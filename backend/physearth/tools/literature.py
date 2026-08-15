"""Reading the corpus: bundled papers, method notes, figures, and live ingestion."""

import base64
import mimetypes
import os
import re
from pathlib import Path

from physearth import config, registry, research
from physearth.corpus import knowledge, live, model_guidelines
from physearth.harness import untrusted
from physearth.ingest import discover, fulltext, http, pdf
from physearth.tools.common import _fail, _ledger, _offline_note, _ok
from physearth.tools.figures import (
    _extract_vector_figure_observations,
    _figure_id_key,
    _paper_figure,
    _trusted_asset_bytes,
)

OUTPUT_BUDGET_CHARS = 16000


def list_literature(query="", scenario="", kind="paper", _session=None):
    wanted = None if kind == "any" else (kind or "paper")
    hits = live.search(_session, query, scenario, wanted)
    total = len(live.catalogue(_session, wanted))
    if not hits:
        return _fail(
            "Nothing matches query=%r scenario=%r kind=%r. There are %d items of that kind; "
            "call with no arguments to see all of them." % (query, scenario, kind, total)
        )
    return _ok(
        "%d of %d item(s) match." % (len(hits), total),
        {"papers": hits, "sources": sorted({h["source"] for h in hits})},
    )


def read_literature(slug, section_id=None, _session=None):
    item = live.card(_session, slug)
    if not item:
        known = sorted(set(knowledge.slugs(kind=None)) | set(live.corpus(_session)))
        return _fail("Unknown slug %r. Available slugs: %s." % (slug, ", ".join(known)))
    source = live.source_of(_session, slug)
    if section_id in (None, ""):
        return _ok(
            "Section index for %s (%s). Call again with a section_id to read one."
            % (slug, source),
            {
                "slug": slug,
                "title": item["title"],
                "doi": item.get("doi", ""),
                "license": item.get("license", ""),
                "source": source,
                "sections": live.section_index(_session, slug),
            },
        )
    opened = live.wrapped_section(_session, slug, section_id, OUTPUT_BUDGET_CHARS)
    if opened is None:
        available = ", ".join(s["id"] for s in live.section_index(_session, slug) or ())
        return _fail(
            "Section %r not found in %s. Available section ids: %s." % (section_id, slug, available)
        )
    section = opened["section"]
    result = _ok(
        "%s section %s: %s (%d chars%s, %s)"
        % (
            slug,
            section["section_id"],
            section["title"],
            len(opened["text"]),
            ", truncated" if opened["truncated"] else "",
            opened["source"],
        ),
        {
            "slug": slug,
            "section_id": section["section_id"],
            "title": section["title"],
            "doi": item.get("doi", ""),
            "citation_key": section["citation_key"],
            "source": opened["source"],
            "text": opened["text"],
            "external_source_findings": opened["findings"],
        },
        citations=[section["citation_key"]],
    )
    if _session is not None:
        _session.setdefault("sections_read", set()).add(section["citation_key"])
    _ledger(
        _session,
        "section",
        {
            "reference": section["citation_key"],
            "paper": slug,
            "section_id": section["section_id"],
            "title": section.get("title", ""),
            "source": opened["source"],
            "doi": item.get("doi", ""),
        },
    )
    return result


def read_research_guideline(topic="planning", _session=None):
    topic = str(topic or "planning").strip().lower()
    slug = "research-planning" if topic in ("planning", "research", "") else topic
    result = read_literature(slug, "00", _session=_session)
    if result["status"] == "success":
        if _session is not None:
            _session.setdefault("research_guidelines_read", set()).add(slug)
            _session.setdefault("skills_read", set()).add(slug)
        result["summary"] = "Research guideline %s is open and must govern the plan." % slug
        result.setdefault("data", {})["guideline_id"] = slug
    return result


def read_model_instruction(model, section=None, _session=None, _switches=None):
    entry = registry.get(str(model or "").strip(), _session)
    if entry is None:
        return _fail("Unknown model %r. Call list_models first." % model)
    instruction = model_guidelines.read(entry.name, entry.card, _session)
    if instruction is None:
        return {
            "status": "needs_input",
            "summary": "Model %s has no registered instruction. Register a user guideline before planning with it." % entry.name,
            "data": {"model": entry.name, "error_code": "model_instruction_missing"},
            "citations": [], "qc": None, "ui": None,
            "error": "model instruction missing",
        }
    text = instruction["text"]
    if section:
        wanted = str(section).strip().lower()
        chunks = re.split(r"(?m)^#{1,6}\s+", text)
        selected = [chunk for chunk in chunks if chunk.lower().startswith(wanted)]
        if selected:
            text = selected[0]
    if _session is not None:
        _session.setdefault("model_instructions_read", set()).add(
            "%s@%s" % (entry.name, instruction["version"])
        )
        _session.setdefault("guidelines_read", set()).add(
            "%s@%s" % (entry.name, instruction["version"])
        )
    result = _ok(
        "Read model instruction %s v%s." % (entry.name, instruction["version"]),
        {
            "model": entry.name,
            "version": instruction["version"],
            "instruction_id": instruction["instruction_id"],
            "source": instruction["source"],
            "text": untrusted.wrap(
                text,
                "model-guideline:%s@%s" % (entry.name, instruction["version"]),
                "registered model instruction",
            ),
            "external_source_findings": untrusted.scan(text),
            "sha256": instruction["sha256"],
            "citation_key": "model-guideline:%s@%s" % (entry.name, instruction["version"]),
        },
    )
    _ledger(
        _session,
        "model_instruction",
        {
            "model": entry.name,
            "version": instruction["version"],
            "reference": "model-guideline:%s@%s" % (entry.name, instruction["version"]),
            "source": instruction.get("source", "model guideline"),
            "instruction_id": instruction.get("instruction_id", entry.name),
        },
    )
    return result


def research_capability_check(
    action="check",
    question="",
    reference_models=None,
    requested_outputs=None,
    local_models=None,
    targets=None,
    _session=None,
):
    if _session is None:
        return _fail("research_capability_check requires a session.")
    report = research.capability_check(
        _session,
        question=question,
        reference_models=reference_models,
        requested_outputs=requested_outputs,
        local_models=local_models,
        targets=targets,
        decision=action,
    )
    if report.get("status") == "error":
        return _fail(
            report.get("message") or "Capability review could not be created.",
            report,
        )
    supported = report.get("supported") or []
    unavailable = report.get("unavailable") or []
    not_comparable = report.get("not_comparable") or []
    resource_gaps = report.get("resource_gaps") or []
    supported_text = "; ".join(
        "%s@%s (%s)" % (
            item.get("model"), item.get("version"),
            ", ".join(item.get("outputs") or ()) or "outputs not declared",
        )
        for item in supported
    ) or "none"
    unavailable_text = "; ".join(
        "%s: %s" % (item.get("model"), item.get("reason"))
        for item in unavailable
    ) or "none"
    incomparable_text = "; ".join(
        "%s is not an equivalent implementation of %s" % (
            item.get("local_model"), item.get("reference_model")
        )
        for item in not_comparable
    ) or "none"
    if resource_gaps:
        return {
            "status": "needs_input",
            "summary": "Complete the capability checkpoint resources before planning: %s."
            % "; ".join(
                "%s requires %s" % (item.get("model"), item.get("resource"))
                for item in resource_gaps
            ),
            "data": {
                "error_code": "capability_resources_required",
                "capability_review": report,
                "required_resources": resource_gaps,
                "repair": "Call list_models and read_model_instruction for every local model, then run the capability check again.",
            },
            "citations": [], "qc": None, "ui": None,
            "error": "capability resources required",
        }
    summary = (
        "Capability check\n\nSupported: %s\n\nUnavailable: %s\n\n"
        "Not comparable: %s"
        % (supported_text, unavailable_text, incomparable_text)
    )
    if report.get("status") == "waiting_user":
        summary += (
            "\n\nExact reproduction is not possible with the currently registered models. "
            "Would you like me to generate a partial plan using only the supported components?"
        )
        return {
            "status": "needs_input",
            "summary": summary,
            "data": {
                "error_code": "capability_review_required",
                "capability_review": report,
                "source": "session.capability_review",
                "expected": "explicit user confirmation for partial scope",
                "repair": "Ask the user whether to generate a plan for supported components.",
                "blocking": True,
            },
            "citations": [], "qc": None, "ui": None,
            "error": "capability review requires user confirmation",
        }
    if report.get("status") == "rejected":
        return {
            "status": "needs_input",
            "summary": "Capability review rejected. No partial research plan was created.",
            "data": {"capability_review": report},
            "citations": [], "qc": None, "ui": None,
            "error": "partial research scope rejected",
        }
    return _ok(summary + "\n\nThe capability checkpoint is complete; a research plan may now be proposed.", {
        "capability_review": report,
    })


def read_paper_figure(paper, figure_id, _session=None):
    item = live.card(_session, str(paper or "").strip())
    if not item:
        return _fail("Unknown paper %r." % paper)
    figure = _paper_figure(item, figure_id)
    resolved_figure_id = str(figure.get("id")) if figure else _figure_id_key(figure_id)
    if figure is None:
        _ledger(
            _session,
            "figure",
            {
                "reference": "%s#%s" % (paper, resolved_figure_id),
                "paper": paper,
                "figure_id": resolved_figure_id,
                "caption": "",
                "source": "paper artifact",
                "asset_available": False,
            },
        )
        return _fail("Paper %s has no extracted figure %s." % (paper, resolved_figure_id))
    citation_key = "%s#fig-%s" % (paper, resolved_figure_id)
    payload = dict(figure)
    payload.pop("asset_bytes", None)
    payload["citation_key"] = citation_key
    if _session is not None:
        _session.setdefault("paper_figures_read", set()).add("%s#%s" % (paper, resolved_figure_id))
    result = _ok(
        "Source-paper figure %s is available. It is not model output and has not been digitized." % resolved_figure_id,
        {"paper": paper, "figure": payload, "citation_key": citation_key},
    )
    _ledger(
        _session,
        "figure",
        {
            "reference": citation_key.replace("#fig-", "#"),
            "paper": paper,
            "figure_id": resolved_figure_id,
            "caption": payload.get("caption", ""),
            "source": payload.get("source_uri") or payload.get("source_url") or "paper artifact",
            "asset_available": bool(
                payload.get("asset_uri") or payload.get("asset_path")
                or payload.get("source_uri") or payload.get("asset_bytes")
            ),
        },
    )
    return result


def inspect_paper_figure(paper, figure_id, focus="", _session=None):
    """Inspect a source figure without silently turning pixels into data.

    The current provider can opt into a bounded multimodal payload with
    ``PHYSEARTH_LLM_VISION=1``. Without it, the tool still records the asset, caption,
    dimensions and provenance, and explicitly reports that qualitative visual review is
    unavailable rather than inventing axes or trends.
    """
    item = live.card(_session, str(paper or "").strip())
    if not item:
        return _fail("Unknown paper %r." % paper)
    figure = _paper_figure(item, figure_id)
    resolved_figure_id = str(figure.get("id")) if figure else _figure_id_key(figure_id)
    reference = "%s#fig-%s" % (paper, resolved_figure_id)
    if figure is None:
        _ledger(
            _session,
            "figure_inspection",
            {
                "reference": reference.replace("#fig-", "#"),
                "paper": paper,
                "figure_id": resolved_figure_id,
                "asset_available": False,
                "analysis_status": "unavailable",
                "availability_reason": "figure asset was not extracted from the paper",
            },
        )
        return _fail(
            "Cannot inspect paper %s figure %s: no extracted source asset is available." %
            (paper, resolved_figure_id)
        )

    payload = dict(figure)
    raw = payload.get("asset_bytes")
    asset_path = payload.get("asset_path") or payload.get("asset_uri")
    if raw is None:
        raw, asset_path = _trusted_asset_bytes(item, asset_path)
    original_raw, original_asset_path = _trusted_asset_bytes(
        item, payload.get("original_asset_path")
    )
    vector_observations = _extract_vector_figure_observations(original_raw)

    asset_available = bool(raw)
    asset_format = str(payload.get("asset_format") or Path(str(asset_path or "")).suffix.lstrip("."))
    width = height = None
    if raw:
        try:
            from io import BytesIO

            from PIL import Image

            with Image.open(BytesIO(raw)) as image:
                width, height = image.size
                asset_format = image.format.lower() if image.format else asset_format
        except (ImportError, OSError, ValueError):
            pass

    caption = str(payload.get("caption") or "").strip()
    analysis_status = (
        "vision_payload_ready"
        if asset_available and _vision_enabled()
        else "text_extracted"
        if asset_available and vector_observations.get("axes") or vector_observations.get("legend")
        else "metadata_only"
        if asset_available
        else "unavailable"
    )
    availability_reason = ""
    if not asset_available:
        availability_reason = "paper artifact contains metadata but no extracted image asset"
    elif analysis_status == "vision_payload_ready":
        availability_reason = (
            "source image attached to the next multimodal model request; vector labels were "
            "also extracted when a publisher PDF was available"
        )
    elif analysis_status == "text_extracted":
        availability_reason = (
            "axis and legend text were extracted from the publisher figure PDF; qualitative "
            "line trends still require visual review"
        )
    else:
        availability_reason = (
            "the configured language-model endpoint has no enabled multimodal image path; "
            "the source image is retained but no vector labels were available"
        )
    visual = {
        "axes": vector_observations.get("axes") or [],
        "legend": vector_observations.get("legend") or [],
        "panels": vector_observations.get("panels"),
        "visible_trends": [],
        "annotations": [],
        "focus": str(focus or "").strip(),
    }
    for key in ("x_ticks", "y_ticks", "panel_detection", "source", "text"):
        if vector_observations.get(key):
            visual[key] = vector_observations[key]
    if caption:
        visual["caption_context"] = caption
    if width and height:
        visual["dimensions_px"] = {"width": width, "height": height}

    image_data_url = None
    if asset_available and _vision_enabled() and len(raw) <= 2_000_000:
        mime = mimetypes.guess_type("figure.%s" % (asset_format or "png"))[0] or "image/png"
        image_data_url = "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))

    data = {
        "paper": paper,
        "figure_id": resolved_figure_id,
        "citation_key": reference,
        "caption": caption,
        "source_page": payload.get("page"),
        "source": payload.get("source_uri") or payload.get("source_url") or "paper artifact",
        "asset_available": asset_available,
        "asset_format": asset_format or None,
        "asset_path": asset_path,
        "original_asset_path": original_asset_path,
        "analysis_status": analysis_status,
        "availability_reason": availability_reason,
        "visual_observations": visual,
        "numeric_digitization": "not performed",
    }
    if image_data_url:
        data["image_data_url"] = image_data_url
    _ledger(
        _session,
        "figure_inspection",
        {
            "reference": reference,
            "paper": paper,
            "figure_id": resolved_figure_id,
            "caption": caption,
            "source": data["source"],
            "asset_available": asset_available,
            "analysis_status": analysis_status,
            "availability_reason": availability_reason,
            "visual_observations": visual,
            "numeric_digitization": "not performed",
        },
    )
    if _session is not None:
        _session.setdefault("paper_figures_inspected", set()).add("%s#%s" % (paper, resolved_figure_id))
    if image_data_url:
        inspection_note = (
            "The source image is attached for visual review; extracted axes and legend text "
            "are included as an audit aid."
        )
    elif analysis_status == "text_extracted":
        inspection_note = (
            "Axes and legend text were extracted from the source figure PDF; line trends "
            "still require a vision-capable model."
        )
    elif not asset_available:
        inspection_note = "No source image asset is available."
    else:
        inspection_note = "Only metadata/caption are available; visual review is unavailable."
    summary = "Inspected source-paper figure %s. %s Numeric curve digitization was not performed." % (
        resolved_figure_id,
        inspection_note,
    )
    return _ok(summary, data, citations=[reference])


def _vision_enabled():
    return str(config.get("PHYSEARTH_LLM_VISION") or os.environ.get("PHYSEARTH_LLM_VISION", "1")).strip().lower() in {
        "1", "true", "yes", "on"
    }


def discover_literature(query, from_year=None, limit=6, _session=None):
    if not http.online():
        return _offline_note("searching the open-access literature")
    try:
        candidates, elapsed = discover.search(
            query,
            from_year,
            limit,
            held_slugs=set(knowledge.slugs()) | set(live.corpus(_session)),
            held_dois=live.held_dois(_session),
        )
    except http.Upstream as exc:
        return _fail(
            "The literature index did not answer (%s). This is an upstream fault, not an "
            "empty result: there may well be relevant papers and this deployment could not "
            "reach the service that lists them. Say so, and work from the bundled corpus."
            % exc
        )
    if not candidates:
        return _ok(
            "OpenAlex returned no open-access paper for %r. The service answered normally, "
            "so this is a genuine absence, not a fault." % query,
            {"query": query, "candidates": [], "topics": []},
        )
    live.remember_abstracts(_session, candidates)
    ready = [
        c for c in candidates if c["full_text"] == "available" and not c["already_held"]
    ]
    return _ok(
        "%d open-access candidate(s) for %r, %d whose full text is reachable from here. "
        "These are abstracts and metadata; nothing here is full text."
        % (len(candidates), query, len(ready)),
        {
            "query": query,
            "candidates": candidates,
            "topics": discover.topics(candidates),
            "elapsed_s": elapsed,
            "note": (
                "full_text says what ingest_paper can do with each one: available means the "
                "text is at an address derivable from the DOI, lookup_required means it may "
                "be held by Europe PMC and the only way to know is to try, unavailable means "
                "it is not reachable from here and stays at abstract level. Cite any of these "
                "as [abs:doi], and only for what a study did or was about; for a number, "
                "ingest the paper and cite the section you read."
            ),
        },
    )


def ingest_paper(doi="", file_path=None, _session=None, _persist=True):
    if _session is None:
        return _fail("ingest_paper needs a conversation to put the paper into.")
    if file_path:
        try:
            record = pdf.parse(file_path)
            card = live.add(_session, record, persist=_persist)
        except (ValueError, RuntimeError, OSError) as exc:
            return _fail("The uploaded paper could not be ingested: %s" % exc)
        return _ok(
            "Stored uploaded PDF %s as %s: %d page section(s), %d extracted figure(s)."
            % (
                record.get("filename") or "paper.pdf",
                card["slug"],
                len(card["sections"]),
                len(card.get("figures") or []),
            ),
            {
                "slug": card["slug"],
                "doi": "",
                "title": card["title"],
                "license": card["license"],
                "fetched_from": "pdf_upload",
                "figures": card.get("figures") or [],
                "tables": card.get("tables") or [],
                "artifact": card.get("artifact"),
                "sections": live.section_index(_session, card["slug"]),
            },
        )
    doi = fulltext.normalise(doi)
    if not doi:
        return _fail("ingest_paper requires a DOI or an uploaded PDF.")
    if not http.online():
        return _offline_note("taking in a paper by DOI")
    doi = fulltext.normalise(doi)
    for slug, item in live.corpus(_session).items():
        if item["doi"] == doi:
            return _ok(
                "%s is already in this conversation as %s." % (doi, slug),
                {"slug": slug, "doi": doi, "sections": live.section_index(_session, slug)},
            )
    for slug in knowledge.slugs():
        if (knowledge.card(slug).get("doi") or "").lower() == doi:
            return _ok(
                "%s ships with this deployment as %s; read it directly." % (doi, slug),
                {"slug": slug, "doi": doi, "sections": knowledge.section_index(slug)},
            )
    hint = (live.abstracts(_session).get(doi) or {}).get("license", "")
    try:
        record = fulltext.fetch(doi, hint)
    except ValueError as exc:
        return _fail(str(exc))
    except LookupError as exc:
        return _fail(
            "%s. The paper may still exist and be open access; what is missing is a route to "
            "its full text from here. Keep it at abstract level and cite it as [abs:%s]."
            % (exc, doi)
        )
    except http.Upstream as exc:
        return _fail(
            "The full text of %s could not be fetched (%s). This is an upstream fault, not a "
            "missing paper. Say so rather than reporting that the paper was not found." % (doi, exc)
        )
    try:
        card = live.add(_session, record, persist=_persist)
    except ValueError as exc:
        return _fail(str(exc))
    return _ok(
        "Took in %s as %s: %d section(s) from %s, licensed %s. Read a section with "
        "read_literature and cite it as [%s#id]."
        % (doi, card["slug"], len(card["sections"]), record["source"], card["license"], card["slug"]),
        {
            "slug": card["slug"],
            "doi": doi,
            "title": card["title"],
            "license": card["license"],
            "figures": card.get("figures") or [],
            "tables": card.get("tables") or [],
            "artifact": card.get("artifact"),
            "fetched_from": record["source"],
            "sections": live.section_index(_session, card["slug"]),
        },
    )

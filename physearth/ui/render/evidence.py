"""The evidence panel: what was read, run, queried, and what was refused."""

from physearth import knowledge, reference
from physearth import live as literature
from physearth.models import registry
from physearth.ui.render.text import SECTION_PREVIEW_CHARS, _e, _svg


def _agreement_row(values):
    """Statistics under the chart they came from, never floating free of it."""
    stats = "".join(
        "<span class='stat'><b>%s</b>%s%s</span>"
        % (_e(name), _e(values[name]), _e(" " + values["unit"] if name != "r" else ""))
        for name in ("bias", "rmse", "mae", "r")
        if values.get(name) is not None
    )
    return (
        "<div class='fig-stats'>%s<span class='fig-stats__note'>%s against %s over %d "
        "overlapping point(s), %g to %g</span></div>"
        % (
            stats,
            _e(values.get("of", "")),
            _e(values.get("against", "")),
            values.get("n_points", 0),
            (values.get("overlap") or [0, 0])[0],
            (values.get("overlap") or [0, 0])[1],
        )
    )


def _comparison_table(rows):
    if not rows:
        return ""
    body = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (
            _e(row.get("quantity", "")),
            _e(row.get("of", "")),
            _e(row.get("against", "")),
            _e(row.get("bias", "")),
            _e(row.get("rmse", "")),
            _e(row.get("mae", "")),
        )
        for row in rows
    )
    return (
        "<div class='fig-comparisons'><b>Pairwise diagnostics</b>"
        "<table><thead><tr><th>quantity</th><th>series</th><th>baseline</th>"
        "<th>bias</th><th>RMSE</th><th>MAE</th></tr></thead><tbody>%s</tbody></table></div>"
        % body
    )


def _figure_card(figure, index):
    sources = figure.get("provenance") or ["model_run"]
    preview = bool(figure.get("preview"))
    ribbon = (
        "fig-ribbon--preview"
        if preview
        else "fig-ribbon--measured"
        if "measured" in sources
        else "fig-ribbon--computed"
    )
    label = (
        "pseudo-data preview"
        if preview
        else " + ".join("model run" if s == "model_run" else s for s in sources)
    )
    figure_number = figure.get("figure_number") or index
    if not preview:
        label = "Figure %d · %s" % (figure_number, label)
    legend = "".join(
        "<span class='badge badge--%s'>%s</span> %s "
        % (
            "ok" if item["source"] == "measured" else "model",
            "measured" if item["source"] == "measured" else "model run",
            _e(
                "%s, %s%s"
                % (
                    item["label"],
                    item["origin"],
                    "" if preview else ", %d points" % item["n_points"],
                )
            ),
        )
        for item in figure.get("series") or []
    )
    agreement = _agreement_row(figure["agreement"]) if figure.get("agreement") else ""
    comparisons = _comparison_table(figure.get("comparisons") or [])
    quality = figure.get("quality_review") or {}
    quality_html = ""
    if not preview and quality.get("reviewed"):
        quality_html = (
            "<div class='fig-quality %s'><b>Figure QA:</b> %s%s</div>"
            % (
                "is-passed" if quality.get("passed") else "is-failed",
                "passed" if quality.get("passed") else "failed",
                " · automatically redrawn for clarity" if quality.get("redrawn") else "",
            )
        )
    return (
        "<div class='fig-card%s' data-anchor='fig-%d'>"
        "<div class='fig-ribbon %s'>%s<span class='handle'>%s</span></div>"
        "<div class='fig-body'><img alt='%s' src='%s'>%s%s%s"
        "<div class='fig-cap'>%s</div></div></div>"
        % (
            " fig-card--preview" if preview else "",
            index,
            ribbon,
            _e(label),
            _e((figure.get("series") or [{}])[0].get("handle", "")),
            _e(figure.get("title") or "chart"),
            _e(figure.get("image_url") or figure.get("png", "")),
            agreement,
            comparisons,
            quality_html,
            legend or _e(figure.get("title") or ""),
        )
    )


SOURCE_BADGE = {
    "bundled": ("badge--src", "bundled"),
    "session": ("badge--model", "fetched in this conversation"),
    "skill": ("badge--mono", "method note"),
}


def _section_card(session, key):
    slug, _, section_id = key.partition("#")
    card = literature.card(session, slug)
    section = literature.read_section(session, slug, section_id) if card else None
    if not section:
        return ""
    origin = literature.source_of(session, slug)
    badge_class, badge_text = SOURCE_BADGE.get(origin, ("badge--src", origin or "source"))
    doi = card.get("doi", "")
    text = " ".join(section["text"].replace("#", " ").split())
    if len(text) > SECTION_PREVIEW_CHARS:
        body = (
            "%s<details class='disclosure' data-key='sec-%s'><summary>rest of the section, "
            "%d more characters</summary><div class='ev-card__text'>%s</div></details>"
        ) % (
            _e(text[:SECTION_PREVIEW_CHARS] + "..."),
            _e(key),
            len(text) - SECTION_PREVIEW_CHARS,
            _e(text[SECTION_PREVIEW_CHARS:]),
        )
    else:
        body = _e(text)
    return (
        "<div class='ev-card' data-anchor='sec-%s'>"
        "<div class='ev-card__head'><span class='badge badge--mono'>%s</span>"
        "<span class='ev-card__title'>%s</span>"
        "<span class='badge %s' style='margin-left:auto'>%s</span></div>"
        "<div class='ev-card__text'>%s</div>"
        "<div class='ev-card__foot'><span class='badge badge--src'>%s</span>"
        "<span>%s (%s)</span>%s</div></div>"
        % (
            _e(key),
            _e(key),
            _e(section["title"]),
            badge_class,
            _e(badge_text),
            body,
            _e(card.get("license", "")),
            _e(card.get("title", slug)),
            _e(card.get("year", "")),
            "<a href='https://doi.org/%s' target='_blank' rel='noopener'>doi.org/%s</a>"
            % (_e(doi), _e(doi))
            if doi
            else "",
        )
    )


def _abstract_card(doi, item):
    """Abstract level. Deliberately drawn as a thinner thing than a section card."""
    return (
        "<div class='ev-card ev-card--abs' data-anchor='abs-%s'>"
        "<div class='ev-card__head'><span class='badge badge--warn'>abstract only</span>"
        "<span class='ev-card__title'>%s</span></div>"
        "<div class='ev-card__text'>%s</div>"
        "<div class='ev-card__foot'><span class='badge badge--src'>%s</span>"
        "<span>%s &middot; %s</span>"
        "<a href='https://doi.org/%s' target='_blank' rel='noopener'>doi.org/%s</a></div>"
        "<div class='pane-note' style='margin:8px 0 0'>Not read. This can support what the "
        "study was about, never a value in kelvin, decibels or volumetric soil moisture.</div>"
        "</div>"
        % (
            _e(doi),
            _e(item.get("title") or doi),
            _e(item.get("abstract") or "No abstract was returned for this record."),
            _e(item.get("license") or "licence not stated"),
            _e(item.get("authors") or "unknown authors"),
            _e(item.get("year") or ""),
            _e(doi),
            _e(doi),
        )
    )


def _dataset_card(slug):
    card = reference.card(slug)
    if not card:
        return ""
    item = reference.provenance(slug)
    indices, _ = reference.query(slug)
    summary = reference.summarise(slug, indices)
    rows = "".join(
        "<tr><td class='name'>%s</td><td>%s</td><td class='num'>%s</td>"
        "<td><span class='badge badge--ok'>%s</span></td></tr>"
        % (
            _e(name),
            _e(spec.get("unit", "")),
            _e(
                "%s to %s" % (spec["min"], spec["max"])
                if "min" in spec
                else "%d value%s" % (spec.get("unique", 0), "" if spec.get("unique") == 1 else "s")
            ),
            _e(card["columns"][name]["source"]),
        )
        for name, spec in summary.items()
    )
    return (
        "<div class='ev-card' data-anchor='data-%s'>"
        "<div class='ev-card__head'><span class='badge badge--mono'>data:%s</span>"
        "<span class='ev-card__title'>%s</span></div>"
        "<table class='table'><thead><tr><th>column</th><th>unit</th><th>range</th>"
        "<th>source</th></tr></thead><tbody>%s</tbody></table>"
        "<div class='ev-card__foot'><span class='badge badge--src'>%s</span>"
        "<span>%d rows</span>"
        "<a href='https://doi.org/%s' target='_blank' rel='noopener'>doi.org/%s</a>"
        "</div></div>"
        % (
            _e(slug),
            _e(slug),
            _e(card["title"]),
            rows,
            _e(item["license"]),
            len(indices),
            _e(item["paper_doi"]),
            _e(item["paper_doi"]),
        )
    )


def _corpus_card(entry):
    card = knowledge.card(entry["slug"])
    doi = card.get("doi", "")
    sections = knowledge.section_index(entry["slug"]) or []
    return (
        "<div class='ev-card'><div class='ev-card__head'>"
        "<span class='badge badge--mono'>%s</span>"
        "<span class='ev-card__title'>%s</span></div>"
        "<div class='ev-card__text'>%s</div>"
        "<div class='ev-card__foot'><span class='badge badge--src'>%s</span>"
        "<span>%s &middot; %d sections</span>"
        "<a href='https://doi.org/%s' target='_blank' rel='noopener'>doi.org/%s</a>"
        "</div></div>"
        % (
            _e(entry["slug"]),
            _e(entry["title"]),
            _e(entry["description"]),
            _e(entry["license"]),
            _e(entry["year"]),
            len(sections),
            _e(doi),
            _e(doi),
        )
    )


def _model_card(row):
    entry = registry.get(row["name"])
    card = entry.card if entry else {}
    tier = "<span class='badge badge--%s' style='margin-left:auto'>%s</span>" % (
        "ok" if row["runnable"] else "mute",
        _e(row["tier"]),
    )
    profile = card.get("resource_profile") or {}
    rows = [
        ("outputs", ", ".join(row["outputs"])),
        ("parameters", "%d declared" % len(card.get("parameters") or {})),
        ("licence", card.get("license", "")),
        ("typical run", profile.get("typical_runtime", "")),
    ]
    info = "".join(
        "<div class='info-row'><span class='k'>%s</span><span class='v'>%s</span></div>"
        % (_e(k), _e(v))
        for k, v in rows
        if v
    )
    citation = card.get("citation", "")
    return (
        "<div class='model-card' data-anchor='model-%s'>"
        "<div class='model-card__head'><span class='model-card__name'>%s</span>"
        "<span class='model-card__ver'>%s</span>%s</div>"
        "<div class='model-card__desc'>%s</div>"
        "<div class='info-card'>%s</div>"
        "<div class='ev-card__foot'><span>%s</span><span>%s</span></div></div>"
        % (
            _e(row["name"]),
            _e(row["name"]),
            _e(row["version"]),
            tier,
            _e(row["description"]),
            info,
            _e(row["source"]),
            _e(citation),
        )
    )


def _rejected_card(item):
    return (
        "<div class='model-card model-card--local'><div class='model-card__head'>"
        "<span class='model-card__name'>%s</span>"
        "<span class='badge badge--mute' style='margin-left:auto'>rejected</span></div>"
        "<div class='model-card__desc'>%s</div></div>"
        % (_e(item["directory"].rsplit("\\", 1)[-1].rsplit("/", 1)[-1]), _e(item["reason"]))
    )


def evidence(session=None, figures=None, sections=None, datasets=None):
    """Everything the conversation holds. Defaults come from the session, so a figure
    drawn in the first question is still on screen during the third."""
    session = session or {}
    figures = list(session.get("figures") or [] if figures is None else figures)
    sections = sorted(session.get("sections_read") or () if sections is None else sections)
    datasets = sorted(session.get("datasets_read") or () if datasets is None else datasets)

    if figures:
        figures_pane = "".join(_figure_card(fig, n) for n, fig in enumerate(figures, 1))
    else:
        figures_pane = (
            "<div class='pane-empty'><div class='pane-empty__title'>No chart yet</div>"
            "<div class='pane-empty__hint'>Ask for a plot. The arrays go from the result store "
            "straight to the renderer, so the numbers never pass through the language "
            "model.</div></div>"
        )

    abstracts = literature.abstracts(session)
    read = "".join(_section_card(session, key) for key in sections)
    read += "".join(_dataset_card(slug) for slug in datasets)
    read += "".join(_abstract_card(doi, abstracts[doi]) for doi in sorted(abstracts))
    if not read:
        read = (
            "<div class='pane-empty'><div class='pane-empty__title'>Nothing opened yet</div>"
            "<div class='pane-empty__hint'>Whatever the agent reads appears here in full, with "
            "its licence and a link to the paper. Switch to the whole corpus to browse all of "
            "it.</div></div>"
        )
    corpus = "".join(_corpus_card(entry) for entry in knowledge.catalogue())

    opened = len(sections) + len(datasets)
    sources_pane = (
        "<input class='scope-input' type='radio' name='pe-scope' id='pe-scope-read' checked>"
        "<input class='scope-input' type='radio' name='pe-scope' id='pe-scope-all'>"
        "<div class='scope'><label for='pe-scope-read'>Opened here (%d)</label>"
        "<label for='pe-scope-all'>Whole corpus (%d)</label></div>"
        "<div class='scope-body'><div class='scope-pane'>%s</div>"
        "<div class='scope-pane'>%s</div></div>"
        "<div class='pane-note'>Every full card in the first list is a section the agent "
        "actually opened, whether it shipped with the system or was fetched during this "
        "conversation. A marker that does not resolve to one of them is refused before the "
        "answer reaches you. The thin cards marked <b>abstract only</b> are papers the agent "
        "has seen listed and has not read; they cannot support a number.</div>"
        % (opened + len(abstracts), len(knowledge.slugs()), read, corpus)
    )

    rows = registry.summary()
    models_pane = "".join(_model_card(row) for row in rows)
    models_pane += "".join(_rejected_card(item) for item in registry.rejected())
    models_pane += (
        "<div class='pane-note'>%d models, one tool. Registering another is a model card plus "
        "one <span class='mono'>run(spec)</span> function, and it inherits every check on this "
        "page without touching the harness. "
        "<a href='https://github.com/zjuiEMLab/PhysEarth-Agent#adding-your-own-model' "
        "target='_blank' rel='noopener'>Read the tutorial</a>.</div>" % len(rows)
    )

    def tab(index, key, icon, name, count):
        return (
            "<label class='tab' for='pe-tab-%s'>%s<span class='tab-name'>%s</span>"
            "<span class='tab-count'>%d</span></label>" % (key, _svg(icon, "tab-icon"), name, count)
        )

    return (
        "<div class='tabset'>"
        "<input class='tab-input' type='radio' name='pe-evtab' id='pe-tab-figures' checked>"
        "<input class='tab-input' type='radio' name='pe-evtab' id='pe-tab-sources'>"
        "<input class='tab-input' type='radio' name='pe-evtab' id='pe-tab-models'>"
        "<div class='tabbar'>%s%s%s</div>"
        "<div class='tab-panes'>"
        "<div class='tab-pane'><div class='pane-scroll'>%s</div></div>"
        "<div class='tab-pane'><div class='pane-scroll'>%s</div></div>"
        "<div class='tab-pane'><div class='pane-scroll'>%s</div></div>"
        "</div></div>"
        % (
            tab(1, "figures", "figure", "Figures", len(figures)),
            tab(2, "sources", "sources", "Sources", len(sections) + len(datasets)),
            tab(3, "models", "models", "Models", len(rows)),
            figures_pane,
            sources_pane,
            models_pane,
        )
    )

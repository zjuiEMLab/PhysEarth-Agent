"""A plan approved by typing, the pages a finished study leaves behind, and the time it took."""

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from apps.studio import studio
from apps.studio import views as render
from apps.studio.views import exports
from apps.studio.views.text import _paragraphs
from physearth import agent, artifacts, research, session
from physearth.agent.completion import _Completion
from tests.test_research import _proposal


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSEARTH_STATE_DIR", str(tmp_path))
    return tmp_path


def _box():
    box = session.new_session("m")
    _proposal(box)
    return box


# ------------------------------------------------------------ typed review commands


@pytest.mark.parametrize("text", ["approve", "Approve.", "  APPROVE and run  ", "lgtm", "批准"])
def test_a_one_word_approval_is_recognised_in_plan_review(text):
    assert research.chat_command(_box(), text) == "approve"


@pytest.mark.parametrize(
    "text",
    [
        "approve, but change the density range to 10-300",
        "I don't approve",
        "can you approve this for me?",
        "yes",
    ],
)
def test_anything_more_than_the_command_is_a_change_not_an_approval(text):
    assert research.chat_command(_box(), text) is None


def test_commands_only_exist_while_a_plan_is_under_review():
    assert research.chat_command(session.new_session("m"), "approve") is None
    box = _box()
    box["research"]["phase"] = "approved"
    assert research.chat_command(box, "approve") is None


def test_typed_approval_reaches_the_same_gate_as_the_button():
    box = _box()
    research.apply_chat_command(box, research.chat_command(box, "approve"))
    assert research.allow_model(box)
    assert box["research"]["selected_charts"] == ["density_curve"]


def test_typed_preview_approves_for_a_layout_preview_only():
    box = _box()
    research.apply_chat_command(box, "preview")
    assert box["research"]["phase"] == "pseudo_preview"
    assert not research.allow_model(box)
    assert "approve" in research.review_guidance(box["research"])


def _drive(monkeypatch, box, text):
    """Run one Studio turn with the agent replaced, and say what the agent was asked."""
    asked = []

    def fake_stream(question, seen, model_id, sess):
        asked.append(question)
        state = agent.new_state(model_id, sess)
        state["phase"] = "done"
        yield "done", [], state

    monkeypatch.setattr(studio.agent, "stream", fake_stream)
    frames = list(studio.respond(text, [], box, "m"))
    return asked, frames[-1]


def test_studio_runs_the_approved_plan_and_shows_the_persons_own_words(state, monkeypatch):
    box = _box()
    asked, frame = _drive(monkeypatch, box, "approve")
    # The plan itself reaches the agent from the loop (see the brief test below).
    assert asked == [studio.EXECUTION_COMMAND]
    turns = frame[8]
    assert turns[-1]["question"] == "approve"
    assert research.allow_model(box)


def test_studio_passes_a_qualified_approval_to_the_agent_as_a_revision(state, monkeypatch):
    box = _box()
    asked, _ = _drive(monkeypatch, box, "approve, but drop the optional chart")
    assert asked == ["approve, but drop the optional chart"]
    assert not research.allow_model(box)


def test_a_preview_command_is_answered_without_a_model_call(state, monkeypatch):
    box = _box()
    asked, frame = _drive(monkeypatch, box, "preview")
    assert asked == []
    assert box["research"]["phase"] == "pseudo_preview"
    assert "pseudo-data" in frame[8][-1]["answer"]


def test_the_research_card_has_no_buttons_and_links_the_plan_page(state):
    box = _box()
    card = studio._research_card(box)
    assert "Open the plan" in card and "Download (HTML)" in card and "<code>approve</code>" in card
    page = Path(box["research"]["plan_export"]["path"])
    assert page.is_file() and "How to approve or change this plan" in page.read_text()
    css = Path("apps/studio/static/ui.css").read_text()
    assert ":has(.approve.approve--research) > .approve__row" in css


# -------------------------------------------------------------- report and scripts

REPORT = """# Reproduction of Figure 3

## Research result and conclusion

The curves converge below **20 kg m-3** [paper#08].

They diverge above it.

## Supporting results

| Quantity | Value |
|---|---|
| bias | 0.1 |
"""


def test_key_findings_are_the_reports_first_section():
    findings = exports.key_findings(REPORT)
    assert findings.startswith("The curves converge") and "They diverge" in findings
    assert "Supporting results" not in findings


def test_markdown_tables_render_as_tables():
    html = _paragraphs("| a | b |\n|---|---|\n| 1 | **2** |")
    assert "<table class='md-table'>" in html and "<b>2</b>" in html


def _finished(box, tmp_path):
    """A completed study with one real figure whose one run was persisted."""
    from physearth.registry import loader

    spec = {
        "electromagnetic_model": "iba", "microstructure_model": "exponential",
        "output": "coefficients", "frequency_ghz": 37.0, "angle_deg": 55.0,
        "thickness_m": 1.0, "density_kg_m3": 300.0, "temperature_k": 265.0,
        "corr_length_m": 0.0001, "radius_m": 0.0001, "stickiness": 0.2, "dort_streams": 8,
        "sweep_parameter": "density_kg_m3", "sweep_start": 10.0, "sweep_stop": 500.0,
        "sweep_points": 4,
    }
    entry = loader.get("smrt")
    if not entry or not entry.runnable:
        pytest.skip("smrt is not runnable here")
    result = entry.run(spec)
    artifacts.persist_run(box["id"], box["id"], "res_test000001", {
        "handle": "res_test000001", "model": "smrt", "version": entry.card["version"],
        "spec": spec, "axis": result["axis"], "series": result["series"], "units": {},
    })
    image = tmp_path / "figure.png"
    image.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00"
        b"\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    box["figures"] = [{
        "figure_number": 1, "title": "Figure 1. ks vs density", "x_label": "Density",
        "y_label": "ks", "kind": "line", "image_path": str(image),
        "series": [{"label": "IBA", "handle": "res_test000001", "x": "density_kg_m3",
                    "y": "ks_per_m", "origin": "smrt@1.5.1", "n_points": 4}],
    }]
    box["research"]["phase"] = "completed"


def test_a_finished_study_publishes_its_report_and_offers_scripts(state, monkeypatch):
    box = _box()
    _finished(box, state)
    turn = studio._publish_report(box, REPORT, "m", {"question": "q", "answer": REPORT})
    assert turn["answer"] == REPORT  # what later turns send to the model is unchanged
    assert turn["display"].startswith("## Key findings") and "generate scripts" in turn["display"]
    page = Path(box["research"]["report_export"]["path"]).read_text()
    assert "data:image/png;base64," in page and "<table class='md-table'>" in page
    assert box["research"]["scripts_offered"]
    shown = render.history([turn], session=box)
    assert "Download report (HTML)" in shown and "Supporting results" not in shown


def test_scripts_are_written_from_the_recorded_runs_and_redraw_them(state):
    box = _box()
    _finished(box, state)
    bundle = research.script_bundle(box)
    assert bundle["figures"] == 1 and not bundle["missing"]
    names = zipfile.ZipFile(bundle["path"]).namelist()
    assert any(n.endswith("reproduce_figure_01.py") for n in names)
    assert any(n.endswith("data/res_test000001.json") for n in names)
    script = Path(bundle["files"][0])
    assert '"electromagnetic_model": "iba"' in script.read_text()
    out = state / "redrawn.png"
    subprocess.run(
        [sys.executable, str(script), "--recorded", "--out", str(out)], check=True,
        capture_output=True, timeout=120,
    )
    assert out.stat().st_size > 1000


def test_only_an_answer_to_the_offer_generates_scripts():
    box = _box()
    assert not studio._wants_scripts(box, "yes")
    box["research"]["scripts_offered"] = True
    assert studio._wants_scripts(box, "generate scripts")
    assert studio._wants_scripts(box, "yes please")
    assert studio._wants_scripts(box, "Can you generate the scripts for the figures?")
    assert not studio._wants_scripts(box, "no scripts, thanks")
    assert not studio._wants_scripts(box, "Why do the curves diverge above 20 kg m-3?")


# ------------------------------------------------------------------ trace and time


def test_an_unlisted_event_kind_reads_as_words_that_can_wrap():
    card = render.trace([{"kind": "some_new_event_kind", "detail": "x"}], agent.new_state())
    assert "SOME NEW EVENT KIND" in card
    card = render.trace(
        [{"kind": "research_mode_selected", "rule": "agent_preflight_reproduction", "detail": "x"}],
        agent.new_state(),
    )
    assert "RESEARCH MODE" in card and "RESEARCH_MODE_SELECTED" not in card


def test_the_trace_shows_where_the_time_went():
    box = session.new_session("m")
    box["turn_clock"] = {"started_at": 1000.0, "finished_at": 1318.0}
    box["timing_totals"] = {"wall_s": 900.0}
    state = agent.new_state("m", box)
    events = [
        {"kind": "model_call", "elapsed_s": 100.0, "first_token_s": 80.0, "completion_tokens": 10},
        {"kind": "tool_call", "elapsed_s": 2.5, "summary": "ran"},
    ]
    html = render.trace_metrics(state, events, False)
    assert "5m 18s" in html and "1m 40s" in html and "1m 20s" in html and "15m 00s" in html
    assert "5m 18s" in render.trace(events, state, running=False)
    live = render.trace(events, state, running=True)
    assert "data-clock-since='1000.000'" in live


class _Delta:
    def __init__(self, reasoning=None, content=None):
        self.reasoning = reasoning
        self.content = content
        self.tool_calls = None


class _Chunk:
    def __init__(self, delta):
        self.choices = [type("C", (), {"delta": delta, "finish_reason": None})()]
        self.usage = None


def test_openrouter_reasoning_is_counted_and_first_token_means_the_answer():
    completion = _Completion()
    completion.feed(_Chunk(_Delta(reasoning="thinking about it")))
    assert completion.reasoning == len("thinking about it")
    assert completion.first_token_s is None
    completion.feed(_Chunk(_Delta(content="Answer.")))
    assert completion.first_token_s is not None
    assert not completion.empty()


def test_reasoning_effort_is_only_sent_when_configured(monkeypatch):
    from physearth.agent import loop

    monkeypatch.delenv("PHYSEARTH_LLM_REASONING_EFFORT", raising=False)
    assert loop._reasoning_effort() is None
    monkeypatch.setenv("PHYSEARTH_LLM_REASONING_EFFORT", "low")
    monkeypatch.setenv("PHYSEARTH_LLM_API_BASE", "https://openrouter.ai/api/v1/")
    assert loop._reasoning_effort() == {"reasoning": {"effort": "low"}}
    json.dumps(loop._reasoning_effort())


# ---------------------------------------------------------- a plan a person can read


@pytest.mark.parametrize(
    "name, unit, expected",
    [
        ("frequency_ghz", "GHz", "frequency (frequency_ghz)"),
        ("temperature_k", "K", "temperature (temperature_k)"),
        ("ks_per_m", "m-1", "ks (ks_per_m)"),
        ("coefficient_c", "none", "coefficient c (coefficient_c)"),
        ("stickiness", "none", "stickiness"),
    ],
)
def test_a_parameter_is_named_without_its_unit(name, unit, expected):
    assert research.sheet.named(name, {"unit": unit}) == expected


def test_a_value_carries_its_declared_unit():
    assert research.sheet.with_unit(37.0, "GHz") == "37 GHz"
    assert research.sheet.with_unit(55.0, "degree") == "55°"
    assert research.sheet.with_unit("iba", "none") == "iba"


def test_a_revision_reads_as_sentences_not_values(state):
    box = _box()
    result = research.revise(
        box, {"runs": [{"id": "smrt_density", "parameters": {"frequency_ghz": 19.0, "sweep_stop": 300}}]},
    )
    text = result["summary"]
    assert "frequency (frequency_ghz), run smrt_density: 37 GHz → 19 GHz" in text
    assert "10 to 500 kg m-3 (12 points) → 10 to 300 kg m-3 (12 points)" in text
    assert "{" not in text and "[" not in text


def test_the_protocol_is_given_only_when_asked(state, monkeypatch):
    box = _box()
    page = exports.plan_document(box)
    assert "plan_version:" not in page
    asked, frame = _drive(monkeypatch, box, "protocol")
    assert asked == []
    links = frame[8][-1]["links"]
    assert links and links[0]["download"].endswith(".yaml")
    assert Path(links[0]["url"].split("=", 1)[1]).read_text().strip()


def _fake_extract(statements):
    def extract(session, slug, sections):
        return statements, {"elapsed_s": 0.0}
    return extract


def test_a_paper_is_read_once_and_kept_as_grounded_statements(state):
    from physearth.corpus import digest

    box = session.new_session("m")
    items = [
        {"section": "08", "kind": "result", "statement": "The sparse medium approximation is valid only for very low densities in the range 10–20 kgm-3."},
        {"section": "08", "kind": "result", "statement": "It is valid up to 999 kg m-3."},  # not in the section
        {"section": "99", "kind": "result", "statement": "No such section."},
    ]
    record, cached = digest.digest(box, "smrt-v1", extract=_fake_extract(items))
    assert not cached and record["dropped"] == 2
    assert [i["ref"] for i in record["items"]] == ["smrt-v1#08"]
    called = []
    again, cached = digest.digest(box, "smrt-v1", extract=lambda *a: called.append(1))
    assert cached and not called and again is record


def test_the_digest_tool_opens_every_section_for_citation_and_sections_stay_readable(state, monkeypatch):
    from physearth import tools
    from physearth.corpus import digest

    box = session.new_session("m")
    monkeypatch.setattr(digest, "_extract", _fake_extract([
        {"section": "08", "kind": "result", "statement": "Valid only for 10–20 kgm-3."},
    ]))
    result = tools.call("read_paper_digest", {"slug": "smrt-v1"}, session=box)
    assert result["status"] == "success" and "[smrt-v1#08]" in result["data"]["text"]
    assert "smrt-v1#08" in box["sections_read"] and "smrt-v1#01" in box["sections_read"]
    assert any(e.get("via") == "digest" for e in box["evidence_ledger"])
    # A section can still be opened for a detail check, before or after approval.
    research.apply_chat_command(_box_with(box), "approve")
    detail = tools.call("read_literature", {"slug": "smrt-v1", "section_id": "08"}, session=box)
    assert detail["status"] == "success"


def _box_with(box):
    _proposal(box)
    return box


def test_the_brief_carries_the_paper_and_the_layout(state):
    box = _box()
    box["paper_digests"] = {"smrt-v1": {"items": [
        {"ref": "smrt-v1#08", "kind": "result", "statement": "Valid only for 10–20 kgm-3."},
    ]}}
    box["research"]["plan"]["literature_evidence"] = [
        {"evidence_ref": "smrt-v1#08", "purpose": "result", "finding": "valid only for 10-20 kg m-3"},
    ]
    brief = research.execution_brief(box)
    assert "[smrt-v1#08] valid only for 10-20 kg m-3" in brief
    assert "[smrt-v1#08] (result) Valid only for 10–20 kgm-3." in brief
    assert "Figure-led report" in brief
    assert "frequency = 37 GHz" in brief or "frequency" in brief
    assert "read_research_guideline" in brief
    assert "What the paper states" in exports.plan_document(box)



def test_figure_led_is_the_default_and_imrad_is_for_a_manuscript(monkeypatch):
    from physearth.research import templates

    monkeypatch.delenv("PHYSEARTH_REPORT_TEMPLATE", raising=False)
    project = {"plan": {"reproduction_targets": [{"source_id": "paper#fig03"}]}}
    assert templates.choose(project) == "figure-led"
    project["plan"]["reproduction_targets"] += [{"source_id": "paper#fig04"}, {"source_id": "paper#fig05"}]
    assert templates.choose(project) == "imrad"
    project["report_template"] = "ledger"
    assert templates.choose(project) == "ledger"


def test_an_approved_plan_reaches_the_agent_once_whoever_approved_it(state, monkeypatch):
    from tests.test_approval import _Chunk, _Delta, _fake_client

    box = _box()
    research.apply_chat_command(box, "approve")
    client, sent = _fake_client([[_Chunk(_Delta(content="Report."))], [_Chunk(_Delta(content="Again."))]])
    monkeypatch.setattr(agent.completion, "_client", lambda: client)
    agent.run("Execute the approved plan.", session=box)
    assert any("Basis of the report" in str(m.get("content")) for m in sent[0])
    agent.run("Anything else?", session=box)
    assert not any("Basis of the report" in str(m.get("content")) for m in sent[-1][-3:])


def test_the_report_radar_plots_the_judges_eight_criteria():
    import yaml
    from apps.studio.views import evaluation

    dimensions = yaml.safe_load(Path("evaluation/standards/report_judge.yaml").read_text())["dimensions"]
    assert [key for key, _l, _d in evaluation.Q1_REPORT_AXES] == list(dimensions)


def _checked(reference, outputs):
    from physearth import tools

    box = session.new_session("m")
    tools.call("list_models", {"model": "smrt"}, session=box)
    tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    result = tools.call("research_capability_check", {
        "action": "check", "question": "Reproduce Figure 3", "local_models": ["smrt"],
        "targets": [{"id": "fig03", "label": "Fig. 3", "reference_models": [reference],
                     "requested_outputs": outputs}],
    }, session=box)
    return result, box["capability_review"]


def test_a_versioned_name_of_a_registered_model_is_that_model_with_a_version_note():
    result, review = _checked(
        "SMRT v1.0 (paper implementation of the same six combinations)", ["ks_per_m"]
    )
    assert review["status"] == "ready" and not review["unavailable"] and not review["not_comparable"]
    assert "source describes version 1.0 and the registry runs 1.5.1" in result["summary"]


def test_a_different_model_with_a_version_is_still_unavailable():
    _result, review = _checked("DMRT-ML v3", ["ks_per_m"])
    assert [item["model"] for item in review["unavailable"]] == ["DMRT-ML v3"]


def test_the_plotted_axis_and_a_phrased_output_are_not_missing_outputs():
    _result, review = _checked("SMRT", ["density_kg_m3", "ks_per_m vs density_kg_m3 over 0-100 kg m-3"])
    assert review["unavailable_outputs"] == [] and review["status"] == "ready"
    _result, review = _checked("SMRT", ["brightness_noise_k"])
    assert review["unavailable_outputs"] == ["brightness_noise_k"]

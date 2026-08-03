import re

from physearth import agent, knowledge
from physearth.ui import render, theme


def test_answer_text_is_escaped_before_anything_else():
    out = render.answer_html("<script>alert(1)</script> and <img onerror=x>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "onerror" not in out or "&lt;img" in out


def test_markers_become_chips_that_name_their_evidence():
    out = render.answer_html("a [smrt-v1#12] b [model:smrt@1.5.1] c [data:tvc-backscatter]")
    assert "data-jump='sec-smrt-v1#12'" in out
    assert "data-jump='model-smrt'" in out
    assert "data-jump='data-tvc-backscatter'" in out
    assert out.count("class='cite") == 3


def test_a_blocked_call_names_the_rule_and_the_offending_value():
    event = {
        "kind": "harness_block",
        "at": "00:00:00",
        "rule": "physical_domain",
        "tool": "run_model",
        "detail": "density_kg_m3 = 2000.0 is outside the physical range",
        "problems": ["density_kg_m3 = 2000.0 is outside the physical range 50.0 to 917.0"],
        "intervention": 1,
    }
    out = render.trace([event], agent.new_state())
    assert "step-card--block" in out
    assert "physical_domain" in out
    assert "2000.0" in out
    assert "BLOCKED" in out


def test_the_trace_shows_a_running_card_only_while_the_turn_is_live():
    state = agent.new_state()
    state["phase"] = "calling_model"
    assert "step-card--thinking" in render.trace([], state, running=True)
    assert "step-card--thinking" not in render.trace([], state, running=False)


def test_a_figure_declares_where_its_numbers_came_from():
    figure = {
        "png": "data:image/png;base64,AAAA",
        "title": "t",
        "kind": "line",
        "provenance": ["measured", "model_run"],
        "series": [
            {"label": "a", "source": "measured", "origin": "tvc", "n_points": 3, "handle": "h"},
            {"label": "b", "source": "model_run", "origin": "smrt@1", "n_points": 3, "handle": "h"},
        ],
    }
    out = render.evidence({}, [figure], set(), set())
    assert "fig-ribbon--measured" in out
    assert "measured" in out and "model run" in out


def test_every_bundled_paper_is_browsable_with_its_licence_and_doi():
    out = render.evidence({}, [], set(), set())
    for entry in knowledge.catalogue():
        assert entry["slug"] in out
        assert entry["license"] in out
    assert out.count("doi.org/10.5194") >= len(knowledge.slugs())


def test_history_collapses_each_past_exchange():
    turns = [
        {
            "index": 1,
            "question": "q one",
            "answer": "a one",
            "events": [{"kind": "harness_block"}],
            "state": {"model_runs": 1, "sections_read": ["smrt-v1#01"]},
        }
    ]
    out = render.history(turns)
    assert out.count("<details class='exchange'") == 1
    assert "data-key='turn-1'" in out
    assert "1 blocked" in out


def test_the_model_switcher_marks_the_running_model():
    out = render.hero("deepseek-ai/DeepSeek-V4-Flash")
    assert "data-model='deepseek-ai/DeepSeek-V4-Flash'" in out
    assert re.search(r"data-model='deepseek-ai/DeepSeek-V4-Flash' class='is-active'", out)
    assert out.count("data-model=") == len(agent.CATALOGUE)


def test_an_unknown_model_falls_back_to_the_default():
    assert agent.resolve_model("evil/model") == agent.default_model()
    assert agent.resolve_model("ZhipuAI/GLM-4.7-Flash") == "ZhipuAI/GLM-4.7-Flash"


def test_the_stylesheet_carries_the_fonts_and_neutralises_gradio():
    css = theme.css()
    assert "@font-face" in css
    assert "Anthropic Serif" in css
    assert "display: contents !important" in css
    assert "#pe-app" in css
    assert theme.js().strip().endswith("peBoot();")

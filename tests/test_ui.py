import re

from physearth import agent, budget, knowledge
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


def test_the_session_shows_every_turn_until_it_is_cleared():
    turns = [
        {"index": 1, "question": "q one", "answer": "a one", "events": [], "state": {}},
        {"index": 2, "question": "q two", "answer": "a two", "events": [], "state": {}},
    ]
    out = render.history(turns)
    assert out.count("msg--user") == 2
    assert out.count("msg--agent") == 2
    assert "q one" in out and "a two" in out
    assert render.history([]).count("msg--") == 0


def test_the_model_switcher_marks_the_running_model():
    second = agent.CATALOGUE[1]["id"]
    out = render.hero(second)
    assert "data-model='%s'" % second in out
    assert re.search(r"data-model='%s' class='is-active'" % re.escape(second), out)
    assert out.count("data-model=") == len(agent.CATALOGUE)


def test_an_unknown_model_falls_back_to_the_default():
    assert agent.resolve_model("evil/model") == agent.default_model()
    for item in agent.CATALOGUE:
        assert agent.resolve_model(item["id"]) == item["id"]


def test_the_stylesheet_carries_the_fonts_and_neutralises_gradio():
    css = theme.css()
    assert "@font-face" in css
    assert "Anthropic Serif" in css
    assert "display: contents !important" in css
    assert "#pe-app" in css
    assert theme.js().strip().endswith("peBoot();")


def test_the_quota_message_names_the_model_and_the_alternatives():
    event = {
        "kind": "harness_stop",
        "at": "00:00:00",
        "rule": "quota",
        "reason": "rate limited (HTTP 429)",
        "model": "Qwen/Qwen3.5-122B-A10B",
        "upstream": "You have exceeded today's quota for model Qwen/Qwen3.5-122B-A10B",
    }
    out = render.trace([event], agent.new_state())
    assert "what the endpoint said" in out
    assert "exceeded today" in out
    assert "Qwen/Qwen3.5-122B-A10B" in out


def test_a_spent_daily_quota_is_not_retried():
    class Spent(Exception):
        status_code = 429
        body = {"message": "You have exceeded today's quota for model X, try again tomorrow"}

    class Busy(Exception):
        status_code = 429
        body = {"message": "Too many requests, slow down"}

    assert agent._dead_for_today(Spent()) == "quota"
    assert agent._dead_for_today(Busy()) == ""
    assert agent._fault(Spent()) == "rate limited (HTTP 429)"


def test_clearing_the_session_resets_the_panels_but_not_the_shared_quota():
    import app

    used_before = budget.used()
    hero, head, history, live, trace, evidence, approve, turns, session, box = app.reset(
        agent.default_model()
    )
    assert turns == [] and box == ""
    assert "hidden" in approve
    assert session["turns"] == 0 and not session["sections_read"]
    assert "msg--" not in history and "msg--" not in live
    assert "Nothing has run yet" in trace
    assert "No chart yet" in evidence
    assert "%d / %d" % used_before in trace


def test_the_opening_hint_belongs_to_the_empty_session_only():
    assert "pane-empty" in render.history([])
    assert "pane-empty" not in render.live("", "")
    turns = [{"index": 1, "question": "q", "answer": "a", "events": [], "state": {}}]
    assert "pane-empty" not in render.history(turns)
    assert "pane-empty" not in render.live("", "")


def test_a_withdrawn_model_is_not_retried_either():
    class Gone(Exception):
        status_code = 400
        body = {"message": "Model id : x/y , has no provider supported"}

    class Other(Exception):
        status_code = 400
        body = {"message": "unsupported parameter"}

    assert agent._dead_for_today(Gone()) == "withdrawn"
    assert agent._dead_for_today(Other()) == ""


def test_a_turn_that_died_upstream_is_marked_and_kept_out_of_the_context():
    import app

    fault = [{"kind": "harness_stop", "rule": "quota", "reason": "rate limited"}]
    good = [{"kind": "harness_pass", "rule": "citation_integrity", "markers": []}]
    assert app._faulted(fault) and not app._faulted(good)

    turns = [
        app._archive(1, {}, fault, "q one", "The free daily quota is used up."),
        app._archive(2, {}, good, "q two", "A real answer."),
    ]
    seen = [
        {"role": role, "content": content}
        for t in turns
        if not t.get("faulted")
        for role, content in (("user", t["question"]), ("assistant", t["answer"]))
    ]
    assert [m["content"] for m in seen] == ["q two", "A real answer."]

    out = render.history(turns)
    assert out.count("msg--fault") == 1
    assert "not an answer" in out


def test_clearing_the_session_does_not_disarm_the_approval_gate():
    """The gate is off in the library and switched on per interface session. Clearing the
    conversation makes a new one, and a gate that quietly stopped applying after the
    visitor pressed Clear would be worse than having none."""
    import app
    from physearth import approval

    first = app._session(None, agent.default_model())
    assert approval.required(first)

    session = app.reset(agent.default_model())[8]
    assert approval.required(session)
    assert app._session(session, agent.default_model()) is session
    assert approval.required(session)


def test_the_evidence_panel_is_cheap_enough_to_redraw():
    """It is rendered on every stream yield, so a linear scan of a 23658-row table inside
    it once cost thirty seconds a chunk."""
    import time

    from physearth import reference

    started = time.perf_counter()
    render._dataset_card("tvc-backscatter")
    assert time.perf_counter() - started < 2.0

    indices, _ = reference.query("tvc-backscatter")
    summary = reference.summarise("tvc-backscatter", indices)
    assert summary["band"]["values"] == ["C", "Ku", "X"]
    assert summary["sigma0_db"]["min"] < summary["sigma0_db"]["max"]
    assert len(reference.columns("tvc-backscatter", indices)["sigma0_db"]) == len(indices)


def test_a_marker_is_escaped_once_and_only_once():
    out = render.answer_html("see [abs:10.1175/1520-0442(2003)016<0100:X>2.0.CO;2] for that")
    assert "&amp;amp;" not in out
    assert "&amp;lt;" not in out
    assert "&lt;0100:X&gt;" in out


def test_the_switcher_never_shows_nothing_selected():
    out = render.hero("someone/else")
    assert out.count("is-active") == 1
    assert "data-model='%s' class='is-active'" % agent.default_model() in out


def test_only_one_route_reaches_the_agent():
    """Two bindings would let a stray submit start a second run against one session."""
    import app

    handlers = [
        dep for dep in app.demo.fns.values()
        if getattr(dep, "name", None) == "respond" or getattr(getattr(dep, "fn", None), "__name__", "") == "respond"
    ]
    assert len(handlers) == 1


def test_a_windowed_rate_limit_is_waited_out_not_reported_as_a_fault():
    """Three fault classes that look alike and must not be treated alike: a limit that
    clears by waiting, a quota that will not clear until tomorrow, and a model the
    endpoint no longer serves."""

    class Rpm(Exception):
        status_code = 429
        body = {"message": "request limited RPM reached, current: 11, limit: 10"}

    class Spent(Exception):
        status_code = 429
        body = {"message": "You have exceeded today's quota for model X"}

    class Gone(Exception):
        status_code = 400
        body = {"message": "Model id : x/y , has no provider supported"}

    assert agent._rate_limited(Rpm()) and agent._dead_for_today(Rpm()) == ""
    assert not agent._rate_limited(Spent()) and agent._dead_for_today(Spent()) == "quota"
    assert not agent._rate_limited(Gone()) and agent._dead_for_today(Gone()) == "withdrawn"

    # The wait has to outlast the window it is counted over, or retrying cannot help.
    span = sum(agent.RATE_LIMIT_BACKOFF_S * i for i in range(1, agent.RATE_LIMIT_RETRIES + 1))
    assert span >= 60.0

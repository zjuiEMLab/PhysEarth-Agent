"""One agent reads the research plan before a person does."""

import json
from pathlib import Path

import pytest
from test_approval import _Chunk, _Delta, _fake_client

from physearth import session
from physearth.agent import completion, loop, plan_review

ROOT = Path(__file__).resolve().parent.parent
RECORD = (
    ROOT / "evaluation" / "results" / "competition" / "batch-2026-10-06"
    / "q1-sparse-medium__p1-reproduction-first__full__openai-gpt-5.6-luna__r1.json"
)


def test_a_clean_review_and_one_that_asks_for_changes_are_both_read():
    ok = plan_review.parse('{"verdict": "ok", "issues": []}')
    assert ok == {"verdict": "ok", "issues": []}
    revise = plan_review.parse(
        'Here you go: {"verdict": "revise", "issues": [{"kind": "extra", '
        '"what": "chart c2 is a zoom the paper does not show", "fix": "drop c2"}]}'
    )
    assert revise["verdict"] == "revise"
    assert revise["issues"] == [
        {"kind": "extra", "what": "chart c2 is a zoom the paper does not show", "fix": "drop c2"}
    ]


def test_a_reply_that_is_not_a_review_is_ignored():
    for text in ("", "looks fine", '{"verdict": "maybe"}', "{not json}"):
        assert plan_review.parse(text) is None, text


def test_revise_without_an_issue_is_not_a_request_for_changes():
    assert plan_review.parse('{"verdict": "revise", "issues": []}')["verdict"] == "ok"


def test_at_most_four_issues_with_a_known_kind():
    issues = [{"kind": "extra", "what": "x%d" % n, "fix": "y"} for n in range(9)]
    issues.append({"kind": "weird", "what": "odd", "fix": ""})
    found = plan_review.parse(json.dumps({"verdict": "revise", "issues": issues}))
    assert len(found["issues"]) == 4
    odd = plan_review.parse(json.dumps({"verdict": "revise", "issues": [{"kind": "weird", "what": "w"}]}))
    assert odd["issues"][0]["kind"] == "question"


def test_the_feedback_tells_the_agent_what_to_do_with_it():
    text = plan_review.feedback({"verdict": "revise", "issues": [
        {"kind": "extra", "what": "chart c2 is a zoom", "fix": "drop it"}]})
    assert "[extra] chart c2 is a zoom -> drop it" in text
    assert "revise_plan" in text and "disagree" in text


def test_the_review_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("PHYSEARTH_PLAN_REVIEW", "off")
    assert not plan_review.enabled()
    monkeypatch.setenv("PHYSEARTH_PLAN_REVIEW", "on")
    assert plan_review.enabled()


@pytest.mark.skipif(not RECORD.is_file(), reason="the recorded Q1 run is not present")
def test_the_brief_carries_the_question_the_runs_and_the_charts():
    project = json.loads(RECORD.read_text())["research"]
    box = session.new_session("m")
    box["research"] = project
    text = plan_review.brief(box)
    assert "Question:" in text and "Reproduce Figure 3" in text
    assert "r_rayleigh_ind" in text and "Chart fig03_reproduction" in text
    assert len(text) <= plan_review.BRIEF_CHARS


def test_a_review_that_cannot_be_made_never_holds_the_plan_back(monkeypatch):
    def broken():
        raise RuntimeError("no endpoint")

    monkeypatch.setattr(completion, "_client", broken)
    assert loop._review_plan(session.new_session("m"), "m") is None


def test_a_review_call_returns_what_the_model_said(monkeypatch):
    reply = '{"verdict": "revise", "issues": [{"kind": "missing", "what": "no H curve", "fix": "add tb_h"}]}'
    client, sent = _fake_client([[_Chunk(_Delta(content=reply))]])
    monkeypatch.setattr(completion, "_client", lambda: client)
    found = loop._review_plan(session.new_session("m"), "m")
    assert found["verdict"] == "revise" and found["issues"][0]["kind"] == "missing"
    assert sent[0][0]["content"] == plan_review.PROMPT


def test_a_figures_caption_reaches_the_digest_verbatim(monkeypatch):
    from physearth.corpus import digest as paper_digest

    card = {"figures": [{"id": "fig04", "title": "Comparison with other reference models",
                         "caption": "The snowpack is semi-infinite with temperature 265 K."}]}
    monkeypatch.setattr(paper_digest.live, "card", lambda session, slug: card)
    found = paper_digest.captions({}, "smrt-v1")
    assert found == [{
        "ref": "smrt-v1#fig04", "section": "fig04", "kind": "figure",
        "statement": "Caption of Comparison with other reference models: The snowpack is "
                     "semi-infinite with temperature 265 K.",
    }]


def test_the_reviewer_sees_captions_and_conditions_before_other_statements():
    box = session.new_session("m")
    box["research"] = {"plan": {"question": "q"}}
    box["paper_digests"] = {"smrt-v1": {"items": [
        {"ref": "smrt-v1#09", "kind": "result", "statement": "A result."},
        {"ref": "smrt-v1#fig04", "kind": "figure", "statement": "Caption: temperature 265 K."},
    ]}}
    text = plan_review.brief(box)
    assert text.index("temperature 265 K") < text.index("A result.")
    assert "caption's" in plan_review.PROMPT


def test_the_reviewer_is_shown_the_figures_the_plan_reproduces(monkeypatch):
    from physearth.tools import literature

    box = {"research": {"plan": {"reproduction_targets": [
        {"source_id": "smrt-v1#fig06"}, {"source_id": "smrt-v1#fig06"}, {"source_id": "no-hash"},
    ]}}}
    assert plan_review.figure_refs(box) == ["smrt-v1#fig06"]
    monkeypatch.setenv("PHYSEARTH_LLM_VISION", "0")
    monkeypatch.setattr(literature.config, "get", lambda key, default=None: "0" if key == "PHYSEARTH_LLM_VISION" else default)
    assert literature.source_figure_images(box, ["smrt-v1#fig06"]) == []


def test_the_bundled_figure_reaches_the_reviewer_as_an_image():
    from physearth.tools import literature

    found = literature.source_figure_images(session.new_session("m"), ["smrt-v1#fig06"])
    assert found and found[0][0] == "smrt-v1#fig06" and found[0][1].startswith("data:image/png;base64,")


def test_a_review_written_after_prose_is_still_read():
    """A reviewer that narrates first has still reviewed the plan.

    The reply is read by matching braces, so prose of its own around the answer -- including
    prose with braces in it, which used to swallow the answer into one unparseable span --
    does not turn a review into "could not be made".
    """
    raw = (
        "Based on the review of the plan {c_fig03} against the paper:\n\n"
        "1. FIGURES: the plan draws the comparison.\n"
        "2. CONDITIONS: the radius looks right.\n\n"
        '{"verdict": "revise", "issues": [{"kind": "extra", '
        '"what": "run r_zoom is a zoom the paper does not show", "fix": "drop it"}]}'
    )
    found = plan_review.parse(raw)
    assert found["verdict"] == "revise"
    assert found["issues"][0]["kind"] == "extra"

    nested = plan_review.parse(
        'Here: {"verdict": "ok", "issues": [], "notes": {"drawn": ["c_fig03"]}}'
    )
    assert nested == {"verdict": "ok", "issues": []}
    # A reply that stops mid-object has no review in it, and is not guessed at.
    assert plan_review.parse('{"verdict": "revise", "issues": [{"kind": "extr') is None


def _client(reply, finish_reason="stop", reject_json_mode=False, calls=None):
    """A client that answers with `reply` and records what it was asked for."""
    calls = calls if calls is not None else []

    def create(**kwargs):
        calls.append(kwargs)
        if reject_json_mode and "response_format" in kwargs:
            raise TypeError("unexpected keyword argument 'response_format'")
        return [_Chunk(_Delta(content=reply), finish_reason=finish_reason)]

    return type("C", (), {"chat": type("Chat", (), {
        "completions": type("Completions", (), {"create": staticmethod(create)})()})()})(), calls


def test_the_reviewer_asks_the_endpoint_for_json(monkeypatch):
    """The format is asked for in the request, not only in the prompt."""
    client, calls = _client('{"verdict": "ok", "issues": []}')
    monkeypatch.setattr(completion, "_client", lambda: client)
    box = session.new_session("m")

    found = loop._review_plan(box, "m")

    assert found == {"verdict": "ok", "issues": []}
    assert len(calls) == 1 and calls[0]["response_format"] == {"type": "json_object"}


def test_an_endpoint_without_json_mode_still_reviews_the_plan(monkeypatch):
    client, calls = _client(
        'Review follows.\n{"verdict": "ok", "issues": []}', reject_json_mode=True
    )
    monkeypatch.setattr(completion, "_client", lambda: client)
    box = session.new_session("m")

    found = loop._review_plan(box, "m")

    assert found == {"verdict": "ok", "issues": []}
    assert len(calls) == 2 and "response_format" not in calls[1]
    assert "plan_review_note" not in box


def test_an_unreadable_review_says_what_was_wrong_with_it(monkeypatch):
    """The note is what the person reads in the trace, so it names the failure."""
    prose = "Based on the review of the research plan against the paper: 1. FIGURES: it draws one chart."
    for reply, finish, expected in (
        (prose, "stop", "answered in prose instead of the JSON"),
        (prose, "length", "cut off at the token budget"),
    ):
        client, _calls = _client(reply, finish_reason=finish)
        monkeypatch.setattr(completion, "_client", lambda: client)
        box = session.new_session("m")
        assert loop._review_plan(box, "m") is None
        assert expected in box["plan_review_note"]

"""A research report is published without the narration of the tool rounds before it."""

from physearth.agent.messages import published

NARRATION = ["Executing the approved runs now.", "Rendering the selected charts."]
REPORT = "## Answer\n" + "The six formulations agree at low density and separate above it. " * 20


def test_a_report_is_published_alone_once_the_plan_is_approved():
    for phase in ("approved", "completed"):
        session = {"research": {"phase": phase}}
        assert published(NARRATION, REPORT, session) == REPORT.strip()


def test_everything_the_model_said_is_kept_before_the_plan_is_approved():
    session = {"research": {"phase": "plan_review"}}
    text = published(NARRATION, REPORT, session)
    assert text.startswith("Executing the approved runs now.") and REPORT.strip() in text


def test_a_short_closing_message_does_not_replace_the_turn():
    session = {"research": {"phase": "approved"}}
    text = published(NARRATION, "Done.", session)
    assert "Executing the approved runs now." in text and text.endswith("Done.")


def test_an_ordinary_answer_is_unchanged():
    assert published(["First."], "Second.", {}) == published(["First."], "Second.")

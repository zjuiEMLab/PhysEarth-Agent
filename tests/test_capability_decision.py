"""A partial-scope decision is made once.

The capability check is recomputed whenever the agent calls it, and it used to reset
`user_decision` every time. So the user confirmed a partial scope, the agent checked
again before proposing, the confirmation was gone, and research_plan was refused with a
request for the same decision that had just been given.
"""

from physearth import session as session_state
from physearth.research import capability


def _confirmed_session():
    box = session_state.new_session("m")
    capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    capability.capability_check(box, decision="confirm_partial")
    return box


def test_the_first_check_asks():
    box = session_state.new_session("m")
    report = capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    assert report["status"] == "waiting_user"
    assert report["user_decision"] is None


def test_a_confirmed_decision_survives_the_next_check():
    box = _confirmed_session()
    again = capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    assert again["status"] == "confirmed", "the user was asked to decide twice"
    assert again["user_decision"] == "partial"


def test_the_session_keeps_the_confirmation():
    """research_plan reads it off the session, so that is what has to hold it."""
    box = _confirmed_session()
    capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    assert (box.get("capability_review") or {}).get("status") == "confirmed"


def test_a_wider_scope_asks_again():
    """The decision covers what was shown. Something newly unavailable is a new question."""
    box = _confirmed_session()
    wider = capability.capability_check(
        box,
        question="Reproduce SMRT figure 4",
        reference_models=["SMRT", "MEMLS", "DMRT-ML"],
    )
    assert wider["status"] == "waiting_user"
    assert wider["user_decision"] is None


def test_a_narrower_scope_still_stands():
    box = _confirmed_session()
    narrower = capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT"]
    )
    assert narrower["status"] in ("confirmed", "ready", "waiting_resources")
    assert narrower["status"] != "waiting_user"


def test_a_rejection_is_not_treated_as_a_confirmation():
    box = session_state.new_session("m")
    capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    capability.capability_check(box, decision="reject")
    again = capability.capability_check(
        box, question="Reproduce SMRT figure 4", reference_models=["SMRT", "MEMLS"]
    )
    assert again["status"] == "waiting_user"
    assert again["user_decision"] is None

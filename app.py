import gradio as gr

from physearth import agent, approval, config, diagnostics
from physearth.ui import render, theme

config.load_dotenv()

# Collected here, at import, so no visitor ever waits for five network probes on the
# request path. Every later reader, including the evidence panel, shares this one result.
_REPORT = diagnostics.report()
print(diagnostics.render(_REPORT), flush=True)


def _new_session(model_id):
    """Every session the interface makes, and the only place the gate is switched on.

    The gate is off in the library, because a script and the evaluation suite have nobody
    to ask. It has to be turned on for each session this interface creates, not only the
    first: clearing the conversation makes a new one, and a gate that silently stopped
    applying after the visitor pressed Clear would be worse than no gate at all.
    """
    session = agent.new_session(model_id)
    approval.set_mode(session, approval.ASK)
    return session


def _session(box, model_id):
    """One session per visitor, held in gr.State. Nothing about it is module level."""
    if isinstance(box, dict) and box.get("id"):
        return box
    return _new_session(model_id)


FAULT_RULES = ("upstream", "quota", "withdrawn", "global_budget")


def _evidence_key(session):
    """What the evidence panel is showing, cheaply. Anything else is not worth a redraw."""
    return (
        len(session.get("figures") or ()),
        len(session.get("sections_read") or ()),
        len(session.get("datasets_read") or ()),
        len(session.get("abstracts") or ()),
        len(session.get("corpus") or ()),
    )


def _faulted(events):
    """True when the turn ended on an upstream fault rather than on an answer."""
    return any(
        event["kind"] == "harness_stop" and event.get("rule") in FAULT_RULES for event in events
    )


def _archive(turn, state, events, question, answer):
    """A turn keeps its own trace, so an old exchange can be reopened with its evidence."""
    return {
        "index": turn,
        "question": question,
        "answer": answer,
        "events": events,
        "faulted": _faulted(events),
        "state": {
            "model_runs": state.get("model_runs", 0),
            "model_calls": state.get("model_calls", 0),
            "tool_calls": state.get("tool_calls", 0),
            "interventions": state.get("interventions", 0),
        },
    }


def respond(question, turns, box, model_id):
    question = (question or "").strip()
    turns = list(turns or [])
    session = _session(box, model_id)
    if not question:
        yield (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            turns,
            session,
            "",
        )
        return

    index = len(turns) + 1
    # A turn that died upstream produced no answer, only an apology. Replaying it as an
    # assistant message would teach the model that such text is a valid reply.
    seen = [
        {"role": role, "content": content}
        for t in turns
        if not t.get("faulted")
        for role, content in (("user", t["question"]), ("assistant", t["answer"]))
    ]

    yield (
        render.hero(model_id, running=True, status="Running"),
        render.conversation_head(index),
        render.history(turns, pending=True),
        render.live(question, "", running=True),
        render.trace([], agent.new_state(model_id, session), running=True),
        render.evidence(session),
        render.approval_bar(session),
        turns,
        session,
        "",
    )

    answer, events, state = "", [], agent.new_state(model_id, session)
    evidence_key = _evidence_key(session)
    try:
        for answer, events, state in agent.stream(question, seen, model_id, session):
            running = state.get("phase") != "done"
            # The evidence panel is the most expensive thing on the page and the only one
            # holding scroll position, an open tab and decoded figure images. Pushing it
            # unchanged on every chunk would reset all three many times a turn, so it goes
            # out only when the evidence itself moved.
            key = _evidence_key(session)
            changed = key != evidence_key
            evidence_key = key
            yield (
                gr.update(),
                gr.update(),
                gr.update(),
                render.live(question, answer, running=running),
                render.trace(events, state, running=running),
                render.evidence(session) if changed else gr.update(),
                render.approval_bar(session),
                gr.update(),
                session,
                gr.update(),
            )
    except Exception as exc:
        answer = "The run failed: %s: %s" % (type(exc).__name__, exc)
        events = events or []
        state = state or agent.new_state(model_id, session)

    turns = turns + [_archive(index, state, events, question, answer)]
    yield (
        render.hero(model_id, running=False, status="Idle - %d events last run" % len(events)),
        render.conversation_head(len(turns)),
        render.history(turns),
        render.live("", ""),
        render.trace(events, state, running=False),
        render.evidence(session),
        render.approval_bar(session),
        turns,
        session,
        # The box was emptied on the first yield, when this question was consumed. Whatever
        # is in it now is the next question, typed while this one ran, and is not ours to clear.
        gr.update(),
    )


def reset(model_id):
    """Clearing the conversation drops the evidence and the session budget with it. The
    hourly deployment quota is shared across visitors and deliberately survives."""
    session = _new_session(model_id)
    return (
        render.hero(model_id, running=False, status="Idle"),
        render.conversation_head(0),
        render.history([]),
        render.live("", ""),
        render.trace([], agent.new_state(model_id, session), running=False),
        render.evidence(session),
        render.approval_bar(session),
        [],
        session,
        "",
    )


with gr.Blocks(title="PhysEarth-Agent", fill_height=True) as demo:
    turns_state = gr.State([])
    session_box = gr.State(None)

    with gr.Column(elem_id="pe-app"):
        hero = gr.HTML(render.hero(), elem_classes=["pe-slot"])

        with gr.Row(elem_classes=["stage"]):
            with gr.Column(elem_classes=["pe-panel", "pe-panel--chat"]):
                head_slot = gr.HTML(render.conversation_head(0), elem_classes=["pe-slot"])
                with gr.Column(elem_id="pe-chat-scroll"):
                    history_slot = gr.HTML(render.history([]), elem_classes=["pe-slot"])
                    live_slot = gr.HTML(render.live("", ""), elem_classes=["pe-slot"])
                with gr.Row(elem_classes=["composer__box"]):
                    question = gr.Textbox(
                        elem_id="pe-input",
                        show_label=False,
                        container=False,
                        lines=3,
                        placeholder=render.PLACEHOLDER,
                    )
                    clear = gr.Button("Clear the session", elem_id="pe-clear")
                    send = gr.Button("Send", variant="primary", elem_id="pe-send")

            with gr.Column(elem_classes=["pe-panel", "pe-panel--trace"]):
                trace_slot = gr.HTML(
                    render.trace([], agent.new_state()), elem_classes=["pe-slot"]
                )
                with gr.Column(elem_id="pe-approve"):
                    approval_slot = gr.HTML(
                        render.approval_bar(None), elem_classes=["pe-slot"]
                    )
                    with gr.Row(elem_classes=["approve__row"]):
                        approve = gr.Button("Run it", variant="primary", elem_id="pe-approve-yes")
                        approve_all = gr.Button("Run it and stop asking", elem_id="pe-approve-all")
                        decline = gr.Button("Decline", elem_id="pe-approve-no")

            with gr.Column(elem_classes=["pe-panel", "pe-panel--evid"]):
                evidence_slot = gr.HTML(
                    render.evidence({}, [], set(), set()), elem_classes=["pe-slot"]
                )

        model_bridge = gr.Textbox(
            value=agent.default_model(), elem_id="pe-model-bridge", show_label=False,
            container=False,
        )

    outputs = [
        hero,
        head_slot,
        history_slot,
        live_slot,
        trace_slot,
        evidence_slot,
        approval_slot,
        turns_state,
        session_box,
        question,
    ]
    inputs = [question, turns_state, session_box, model_bridge]
    # Only one way in. ui.js owns the Enter key and clicks Send, so a second submit
    # binding here would be a second route to the same generator: two runs against one
    # session dict, interleaving their trace and evidence writes and spending the budget
    # twice.
    send.click(respond, inputs, outputs)
    clear.click(reset, [model_bridge], outputs)

    # These three must be able to run while `respond` is blocked inside the gate waiting
    # for them, so they are exempt from the queue's concurrency limit. Without that the
    # click would sit behind the very generator it is meant to release.
    for button, decision in (
        (approve, "approve"),
        (approve_all, approval.ALWAYS),
        (decline, "reject"),
    ):
        button.click(
            lambda box, verdict=decision: (
                approval.decide(box, verdict),
                render.approval_bar(box),
            )[1],
            [session_box],
            [approval_slot],
            concurrency_limit=None,
            queue=False,
        )

demo.queue(default_concurrency_limit=4)

if __name__ == "__main__":
    demo.launch(
        server_name=config.get("PHYSEARTH_HOST"),
        server_port=int(config.get("PHYSEARTH_PORT")),
        css=theme.css(),
        js=theme.js(),
        head=theme.head(),
    )

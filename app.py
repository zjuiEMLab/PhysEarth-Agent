import gradio as gr

from physearth import agent, approval, config, diagnostics, evals, research
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
    session["research_required"] = True
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
        int(session.get("evidence_revision", 0)),
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
        render.trace([], agent.new_state(model_id, session), running=True, include_footer=False),
        render.trace_metrics(agent.new_state(model_id, session)),
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
                render.trace(events, state, running=running, include_footer=False),
                render.trace_metrics(state),
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
        render.trace(events, state, running=False, include_footer=False),
        render.trace_metrics(state),
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
        render.trace([], agent.new_state(model_id, session), running=False, include_footer=False),
        render.trace_metrics(agent.new_state(model_id, session)),
        render.evidence(session),
        render.approval_bar(session),
        [],
        session,
        "",
    )


def review_click(box, action):
    """Advance a human gate and request an agent continuation only after final approval."""
    session = box if isinstance(box, dict) else None
    command = ""
    if session and session.get("research"):
        phase_before = session["research"].get("phase")
        research.review_action(session, action)
        if research.allow_model(session):
            # Formal execution approval is the run approval. Do not ask a second time.
            approval.set_mode(session, approval.ALWAYS)
        if (
            action == "primary"
            and phase_before == "chart_selected"
            and research.allow_model(session)
        ):
            command = (
                "I approve formal execution of the reviewed research plan. Continue now: "
                "run the registered physical model, create the selected plot from its actual "
                "outputs, check the result, and only then report the interpretation and conclusion."
            )
    else:
        decision = {"primary": "approve", "secondary": approval.ALWAYS, "pause": "reject"}[action]
        approval.decide(session, decision)
    return render.approval_bar(session), session, command


def resume_after_review(command, turns, box, model_id):
    """A distinct, approval-only route; normal questions still have one Send binding."""
    yield from respond(command, turns, box, model_id)


def select_chart_click(box, chart_id):
    """Record an explicit human chart click without asking the LLM to infer an ID."""
    session = box if isinstance(box, dict) else None
    chart_id = str(chart_id or "").strip()
    if session and session.get("research") and chart_id:
        research.choose_chart(session, chart_id)
    return render.approval_bar(session), session, ""


with gr.Blocks(title="PhysEarth-Agent", fill_height=True) as demo:
    turns_state = gr.State([])
    session_box = gr.State(None)
    evaluation_cases = evals.demo_cases()
    demo_buttons = []

    with gr.Column(elem_id="pe-app"):
        hero = gr.HTML(render.hero(), elem_classes=["pe-slot"])

        with gr.Tabs(selected="evaluation", elem_id="pe-main-tabs") as main_tabs:
            with gr.Tab("Evaluation", id="evaluation", elem_id="pe-evaluation-tab"):
                with gr.Column(elem_id="pe-evaluation-page"):
                    gr.HTML(evals.dashboard(), elem_classes=["pe-eval-slot"])
                    gr.HTML(
                        "<div class='eval-dashboard'><section "
                        "class='eval-section eval-section--demos'>"
                        "<div class='eval-section__head'><div><span class='eval-index'>02</span>"
                        "<h2>Run a representative case</h2></div><p>Each button loads the "
                        "exact evaluation prompt into the agent. Review it, then press Send.</p>"
                        "</div></section></div>",
                        elem_classes=["pe-eval-slot"],
                    )
                    with gr.Row(elem_classes=["eval-demo-grid"]):
                        for case in evaluation_cases:
                            with gr.Column(elem_classes=["eval-demo-cell"]):
                                gr.HTML(evals.demo_card(case), elem_classes=["pe-eval-slot"])
                                button = gr.Button(
                                    "Try in Live Agent",
                                    elem_classes=["eval-demo-button"],
                                )
                                demo_buttons.append((button, case["question"]))
                    gr.HTML(evals.score_summary(), elem_classes=["pe-eval-slot"])
                    gr.HTML(evals.score_details(), elem_classes=["pe-eval-slot"])

            with gr.Tab("Live Agent", id="agent", elem_id="pe-agent-tab"):
                with gr.Row(elem_classes=["stage"]):
                    with gr.Column(
                        elem_id="pe-panel-chat",
                        elem_classes=["pe-panel", "pe-panel--chat"],
                    ):
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

                    with gr.Column(
                        elem_id="pe-panel-trace",
                        elem_classes=["pe-panel", "pe-panel--trace"],
                    ):
                        with gr.Column(elem_id="pe-trace-stream"):
                            trace_slot = gr.HTML(
                                render.trace([], agent.new_state(), include_footer=False),
                                elem_classes=["pe-slot"],
                            )
                            with gr.Column(elem_id="pe-approve"):
                                approval_slot = gr.HTML(
                                    render.approval_bar(None), elem_classes=["pe-slot"]
                                )
                                with gr.Row(elem_classes=["approve__row"]):
                                    approve = gr.Button(
                                        "Approve / Continue",
                                        variant="primary",
                                        elem_id="pe-approve-yes",
                                    )
                                    approve_all = gr.Button(
                                        "Revise / Regenerate", elem_id="pe-approve-all"
                                    )
                                    decline = gr.Button("Pause", elem_id="pe-approve-no")
                        trace_metrics_slot = gr.HTML(
                            render.trace_metrics(agent.new_state()), elem_classes=["pe-slot"]
                        )

                    with gr.Column(
                        elem_id="pe-panel-evid",
                        elem_classes=["pe-panel", "pe-panel--evid"],
                    ):
                        evidence_slot = gr.HTML(
                            render.evidence({}, [], set(), set()), elem_classes=["pe-slot"]
                        )

        model_bridge = gr.Textbox(
            value=agent.default_model(), elem_id="pe-model-bridge", show_label=False,
            container=False,
        )
        review_command = gr.Textbox(
            value="", elem_id="pe-review-command", show_label=False,
            container=False, visible=False,
        )
        chart_bridge = gr.Textbox(
            value="", elem_id="pe-chart-bridge", show_label=False, container=False,
        )
        chart_submit = gr.Button("Select chart", elem_id="pe-chart-submit")

    outputs = [
        hero,
        head_slot,
        history_slot,
        live_slot,
        trace_slot,
        trace_metrics_slot,
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
    for button, demo_question in demo_buttons:
        button.click(
            lambda text=demo_question: (text, gr.Tabs(selected="agent")),
            inputs=None,
            outputs=[question, main_tabs],
            queue=False,
        )
    chart_submit.click(
        select_chart_click,
        [session_box, chart_bridge],
        [approval_slot, session_box, chart_bridge],
        concurrency_limit=None,
        queue=False,
    )

    # These three must be able to run while `respond` is blocked inside the gate waiting
    # for them, so they are exempt from the queue's concurrency limit. Without that the
    # click would sit behind the very generator it is meant to release.
    for button, decision in (
        (approve, "primary"),
        (approve_all, "secondary"),
        (decline, "pause"),
    ):
        review_event = button.click(
            lambda box, verdict=decision: review_click(box, verdict),
            [session_box],
            [approval_slot, session_box, review_command],
            concurrency_limit=None,
            queue=False,
        )
        # The earlier review phases only mutate their explicit gate. Formal execution
        # approval also resumes the same agent, so the button results in a real model run
        # and selected plot instead of merely changing a state label.
        if decision == "primary":
            review_event.then(
                resume_after_review,
                [review_command, turns_state, session_box, model_bridge],
                outputs,
            )

demo.queue(default_concurrency_limit=4)

if __name__ == "__main__":
    demo.launch(
        server_name=config.get("PHYSEARTH_HOST"),
        server_port=int(config.get("PHYSEARTH_PORT")),
        css=theme.css(),
        js=theme.js(),
        head=theme.head(),
        allowed_paths=[str(config.state_dir().resolve())],
    )

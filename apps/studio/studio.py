import json
import os
import time
import urllib.request
from pathlib import Path

import gradio as gr

from apps.studio import theme
from apps.studio import views as render
from apps.studio.views import evaluation as evals
from apps.studio.views import exports
from apps.studio.views.trace import turn_timing
from physearth.api import (
    agent,
    approval,
    audit,
    config,
    diagnostics,
    evaluation,
    research,
)

config.load_dotenv()
audit.configure()
audit.runtime("service_initializing", state_dir=str(config.state_dir().resolve()))

# Collected here, at import, so no visitor ever waits for five network probes on the
# request path. Every later reader, including the evidence panel, shares this one result.
_REPORT = diagnostics.report()
print(diagnostics.render(_REPORT), flush=True)


def _new_session(model_id):
    """Create a normal Q&A session; the agent opts into research when needed.

    The research gate is enabled dynamically when the model deliberately calls
    ``research_plan``. This keeps ordinary questions out of the plan-review workflow
    while preserving the human approval gates for executable research.
    """
    session = agent.new_session(model_id)
    approval.set_mode(session, approval.ASK)
    session["research_required"] = False
    audit.bind(session)
    audit.emit("session_created", session=session, research_required=False)
    return session


def _session(box, model_id):
    """One session per visitor, held in gr.State. Nothing about it is module level."""
    if isinstance(box, dict) and box.get("id"):
        return box
    return _new_session(model_id)


def start_guided_demo(question, model_id, demo_id="smrt-q1-guided"):
    """Start the guided demo without injecting evaluation data into the agent session."""
    session = _new_session(model_id)
    session["research_required"] = True
    context = session.setdefault("research_context", {})
    context["question"] = question
    audit.emit(
        "guided_demo_started",
        session=session,
        demo_id=demo_id,
        context_source="evaluation_only",
    )
    return (
        render.hero(model_id, running=False, status="Guided reproduction ready"),
        render.conversation_head(0, session=session),
        render.history([], session=session),
        render.live("", ""),
        render.trace([], agent.new_state(model_id, session), running=False, include_footer=False),
        render.trace_metrics(agent.new_state(model_id, session)),
        render.evidence(session),
        render.research_context(session),
        [],
        session,
        question,
        gr.Tabs(selected="agent"),
    )


def start_basic_case(question, case_id, model_id):
    """Initialize a basic-case session before the question is sent.

    The old button only copied text into the composer. That meant the first run created a
    fresh session at send time and the UI had no reliable place to show the run approval
    card. Initializing here preserves the normal ASK gate and makes the case behave like a
    real Live Agent session without injecting evaluation YAML into the model context.
    """
    session = _new_session(model_id)
    session["evaluation_case"] = str(case_id or "")
    audit.emit(
        "basic_case_started",
        session=session,
        case_id=str(case_id or ""),
        approval_mode=approval.ASK,
    )
    return (
        render.hero(model_id, running=False, status="Basic case ready · review required"),
        render.conversation_head(0, session=session),
        render.history([], session=session),
        render.live("", ""),
        render.trace([], agent.new_state(model_id, session), running=False, include_footer=False),
        render.trace_metrics(agent.new_state(model_id, session)),
        render.evidence(session),
        render.research_context(session),
        [],
        session,
        question,
        gr.Tabs(selected="agent"),
    )


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


def _trace_key(events, state, running):
    """What the run trace is showing. Events are append-only, so the count is enough."""
    return (len(events), bool(running), state.get("phase"))


def _unmirrored_events(events, mirrored):
    """Trace events not yet copied into the session log, identified by object.

    The trace is not purely append-only: tool_start and approval_wait are appended, shown
    once, then popped. A high-water index cannot survive that, because the pop and the
    next append happen between two yields and leave the list the same length -- so the
    replacement event inherits an index already counted as mirrored and is dropped. That
    is why a tool outcome never reached the session trace. Matching on identity is exact
    regardless of how the list is edited.
    """
    seen = {id(event) for event in mirrored}
    return [event for event in events if id(event) not in seen]


def _metrics_key(state):
    """The counters under the trace, and nothing else on the page moves them."""
    session = state.get("session") or {}
    return (
        state.get("model_calls"),
        state.get("tool_calls"),
        state.get("model_runs"),
        state.get("rejected_calls"),
        state.get("qc_failures"),
        state.get("boundary_flags"),
        state.get("interventions"),
        state.get("prompt_tokens"),
        state.get("completion_tokens"),
        session.get("model_calls"),
        session.get("tool_calls"),
        session.get("turns"),
    )


def _head_key(events, state, session):
    """The conversation head and the research card, which both follow the phase."""
    research = session.get("research") or {}
    capability = session.get("capability_review") or {}
    return (
        len(events),
        state.get("phase"),
        research.get("phase"),
        research.get("version"),
        capability.get("status"),
        bool(session.get("research_required")),
        session.get("evidence_revision"),
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


# The continuation an approval starts. The person approved; this tells the agent what the
# approval covers. It is never shown as their message.
EXECUTION_COMMAND = (
    "I approve formal execution of the reviewed research plan. Continue now: "
    "run the registered physical model, create the selected plot from its actual "
    "outputs, check the result, and only then report the interpretation and conclusion."
)

_SCRIPT_REPLIES = frozenset({
    "yes", "y", "yes please", "sure", "ok", "okay", "generate", "generate scripts",
    "generate the scripts", "generate script", "scripts", "the scripts", "download scripts",
    "是", "要", "需要", "好", "好的", "生成", "生成脚本", "需要脚本",
})


def _research_card(session):
    """The review card, with the current plan written out as a page beside it first."""
    if isinstance(session, dict) and (session.get("research") or {}).get("plan"):
        exports.ensure_plan_export(session)
    return render.research_context(session)


_PROTOCOL_WORDS = frozenset({
    "protocol", "the protocol", "show protocol", "show the protocol", "protocol yaml",
    "generated protocol", "download protocol", "download the protocol", "协议", "方案文件",
})


def _wants_protocol(session, text):
    """The generated protocol file is only produced when someone asks for it by name."""
    if not ((session or {}).get("research") or {}).get("plan"):
        return False
    return " ".join(str(text or "").lower().split()).strip(" .!?。！？") in _PROTOCOL_WORDS


def _protocol_reply(session):
    url, name = exports.write_protocol(session)
    if not url:
        return "There is no research plan in this session to write a protocol from.", []
    version = int((session.get("research") or {}).get("plan_version") or 1)
    return (
        "Here is the protocol generated from plan v%03d. It is the plan in machine-readable "
        "form, for records and reruns; to change the plan, describe the change here." % version,
        [{"label": "Download protocol (%s)" % name, "url": url, "download": name}],
    )


def _wants_scripts(session, text):
    """Whether this message accepts the offer of figure scripts made after the report."""
    project = (session or {}).get("research") or {}
    if not project.get("scripts_offered"):
        return False
    words = " ".join(str(text or "").lower().split()).strip(" .!。！")
    if words in _SCRIPT_REPLIES:
        return True
    if len(words) > 80 or any(no in words.split() for no in ("no", "not", "don't", "dont")):
        return False
    return ("script" in words or "代码" in words or "脚本" in words) and any(
        verb in words for verb in (
            "generate", "yes", "download", "give", "want", "need", "create", "write", "please",
            "生成", "下载", "需要",
        )
    )


def _scripts_reply(session):
    bundle = research.script_bundle(session)
    if not bundle.get("path"):
        return (
            "There are no model-generated figures in this session to write scripts for.",
            [],
        )
    text = (
        "The scripts are ready: one Python file per figure, the recorded run data in data/, "
        "and a README. Each script holds the exact specification of every run behind its "
        "figure.\n\n"
        "- `python reproduce_figure_01.py --recorded` redraws the figure from the recorded "
        "arrays (needs matplotlib).\n"
        "- `python reproduce_figure_01.py` re-runs each model through its registered adapter "
        "first (needs this repository installed)."
    )
    if bundle.get("missing"):
        text += (
            "\n\n%d run record(s) could not be found, so their curves are left out: %s."
            % (len(bundle["missing"]), ", ".join(bundle["missing"]))
        )
    name = Path(bundle["path"]).name
    links = [{"label": "Download scripts (%s)" % name, "url": exports.file_url(bundle["path"]), "download": name}]
    return text, links


def _start_clock(session):
    session["turn_clock"] = {"started_at": time.time(), "finished_at": None}


def _stop_clock(session, events):
    clock = session.get("turn_clock") or {}
    started = clock.get("started_at") or time.time()
    clock["finished_at"] = time.time()
    session["turn_clock"] = clock
    timing = turn_timing(events)
    totals = session.setdefault(
        "timing_totals", {"wall_s": 0.0, "model_s": 0.0, "tool_s": 0.0, "first_token_s": 0.0}
    )
    totals["wall_s"] = float(totals.get("wall_s") or 0) + clock["finished_at"] - started
    for key in ("model_s", "tool_s", "first_token_s"):
        totals[key] = float(totals.get(key) or 0) + timing[key]
    return clock["finished_at"] - started


def _publish_report(session, answer, model_id, turn):
    """A finished study: the full report becomes a page, and the chat keeps its findings."""
    project = (session or {}).get("research") or {}
    if project.get("phase") != "completed" or not str(answer or "").strip():
        return turn
    if (project.get("report_export") or {}).get("version") == project.get("plan_version"):
        return turn
    totals = session.get("timing_totals") or {}
    url = exports.write_report(
        session, answer, model_id,
        timing=render.trace_seconds(totals.get("wall_s")) if totals.get("wall_s") else None,
    )
    if not url:
        return turn
    name = Path(project["report_export"]["path"]).name
    display = (
        "## Key findings\n\n%s\n\nThe full report -- every section, the figures, and the "
        "runs behind them -- is on its own page, linked below." % exports.key_findings(answer)
    )
    links = [
        {"label": "Open the full report", "url": url, "download": ""},
        {"label": "Download report (HTML)", "url": url, "download": name},
    ]
    if research.scripts.has_figures(session):
        project["scripts_offered"] = True
        display += (
            "\n\nWould you like the Python scripts that reproduce these figures? Reply "
            "**generate scripts** and they will be written from the recorded runs, ready to "
            "download."
        )
    turn = dict(turn)
    turn["display"] = display
    turn["links"] = links
    return turn


def _final_frame(model_id, session, turns, events, state, live_html=None):
    return (
        render.hero(model_id, running=False, status="Idle - %d events last run" % len(events)),
        render.conversation_head(len(turns), session=session, events=events, state=state),
        render.history(turns, session=session),
        live_html if live_html is not None else render.live("", ""),
        render.trace(events, state, running=False, include_footer=False),
        render.trace_metrics(state, events, False),
        render.evidence(session),
        _research_card(session),
        turns,
        session,
        gr.update(),
    )


def _local_turn(question, turns, session, model_id, index, reply, links=None):
    """A turn the interface answers itself: a review command, or the scripts it offered.

    No model call. The exchange is still archived, so the next real turn sees it.
    """
    _start_clock(session)
    state = agent.new_state(model_id, session)
    state["phase"] = "done"
    _stop_clock(session, [])
    turn = _archive(index, state, [], question, reply)
    if links:
        turn["links"] = links
    turns = list(turns) + [turn]
    audit.emit(
        "ui_turn_finished", session=session, ui_turn=index, answer=reply, event_count=0,
        final_agent_event=None, state_phase="done", counters={}, local=True,
    )
    yield _final_frame(model_id, session, turns, [], state)


def respond(question, turns, box, model_id, preserve_conversation=False):
    question = (question or "").strip()
    turns = list(turns or [])
    session = _session(box, model_id)
    audit.bind(session, ui_turn=len(turns) + 1)
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
    audit.emit(
        "ui_turn_submitted",
        session=session,
        ui_turn=index,
        question=question,
        archived_turns=len(turns),
    )
    # A typed review command is decided here, from the person's own words, before any
    # model sees the message. The model can describe a plan; only this can approve one.
    agent_question = question
    command = None if preserve_conversation else research.chat_command(session, question)
    if command:
        phase_before = (session.get("research") or {}).get("phase")
        result = research.apply_chat_command(session, command)
        audit.emit(
            "human_research_review",
            session=session,
            action="chat:%s" % command,
            phase_before=phase_before,
            phase_after=(session.get("research") or {}).get("phase"),
            result_status=(result or {}).get("status"),
            result_summary=(result or {}).get("summary"),
        )
        project = session.get("research") or {}
        if research.allow_model(session) and not project.get("execution_resume_sent"):
            project["execution_resume_sent"] = True
            approval.set_mode(session, approval.ALWAYS)
            agent_question = EXECUTION_COMMAND
        else:
            reply = (
                research.review_guidance(project)
                if project.get("phase") != phase_before
                else (result or {}).get("summary") or research.review_guidance(project)
            )
            yield from _local_turn(question, turns, session, model_id, index, reply)
            return
    elif not preserve_conversation and _wants_protocol(session, question):
        reply, links = _protocol_reply(session)
        yield from _local_turn(question, turns, session, model_id, index, reply, links)
        return
    elif not preserve_conversation and _wants_scripts(session, question):
        reply, links = _scripts_reply(session)
        yield from _local_turn(question, turns, session, model_id, index, reply, links)
        return

    _start_clock(session)
    # A turn that died upstream produced no answer, only an apology. Replaying it as an
    # assistant message would teach the model that such text is a valid reply.
    seen = [
        {"role": role, "content": content}
        for t in turns
        if not t.get("faulted")
        for role, content in (("user", t["question"]), ("assistant", t["answer"]))
    ]

    if preserve_conversation:
        # The approval click already removed the research plan card. Do not repaint the
        # transcript or its scroll position just because the approved physical run starts.
        yield (
            render.hero(model_id, running=True, status="Running"),
            gr.update(),
            gr.update(),
            render.live_result("", running=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            session,
            gr.update(),
        )
    else:
        yield (
            render.hero(model_id, running=True, status="Running"),
            render.conversation_head(index, session=session),
            render.history(turns, pending=True, session=session),
            render.live(question, "", running=True),
            render.trace([], agent.new_state(model_id, session), running=True, include_footer=False),
            render.trace_metrics(agent.new_state(model_id, session), [], True),
            render.evidence(session),
            _research_card(session),
            turns,
            session,
            "",
        )

    answer, events, state = "", [], agent.new_state(model_id, session)
    evidence_key = _evidence_key(session)
    # Gradio replaces the complete subtree of every HTML output it receives.  A model token
    # changes Conversation, while a tool lifecycle event changes Trace; sending both trees on
    # every frame made unchanged content disappear and reappear dozens of times per second.
    # Remember the authoritative HTML already on screen and update each panel independently.
    live_html = (
        render.live_result("", running=True)
        if preserve_conversation
        else render.live(question, "", running=True)
    )
    trace_html = render.trace(
        [], agent.new_state(model_id, session), running=True, include_footer=False
    )
    metrics_html = render.trace_metrics(agent.new_state(model_id, session), [], True)
    approval_html = _research_card(session)
    head_html = render.conversation_head(index, session=session, events=events, state=state)
    # Only the Conversation changes on a content token. The trace, the metrics, the head
    # and the research card change on a checkpoint -- an event appended, a counter moved,
    # a phase changed -- which happens tens of times a turn rather than thousands. They
    # were being rebuilt and string-compared on every token anyway, at a few hundred
    # milliseconds a turn and growing with the length of the trace. These keys are the
    # same idea as _evidence_key above, applied to the rest of the page.
    trace_key = _trace_key(events, state, True)
    metrics_key = (_metrics_key(state), 0, True)
    head_key = _head_key(events, state, session)
    logged_agent_events = []
    try:
        for answer, events, state in agent.stream(agent_question, seen, model_id, session):
            # Gradio may resume a streaming generator in a fresh context, so ContextVar
            # bindings made inside agent.stream are not guaranteed to reach every event.
            # Mirror each newly visible trace event with an explicit session reference.
            for event in _unmirrored_events(events, logged_agent_events):
                logged_agent_events.append(event)
                audit.emit(
                    "agent_trace_event",
                    session=session,
                    ui_turn=index,
                    trace_index=len(logged_agent_events),
                    agent_event=event,
                )
            running = state.get("phase") != "done"
            # The evidence panel is the most expensive thing on the page and the only one
            # holding scroll position, an open tab and decoded figure images. Pushing it
            # unchanged on every chunk would reset all three many times a turn, so it goes
            # out only when the evidence itself moved.
            key = _evidence_key(session)
            changed = key != evidence_key
            evidence_key = key
            next_live = (
                render.live_result(answer, running=running)
                if preserve_conversation
                else render.live(question, answer, running=running)
            )
            live_update = next_live if next_live != live_html else gr.update()
            live_html = next_live

            # Each panel below is rebuilt only when its own key moves. The string compare
            # that follows still decides whether the frame is pushed, so what reaches the
            # browser is unchanged; what is saved is rendering a trace that nobody asked
            # for, once per token.
            trace_update = gr.update()
            next_trace_key = _trace_key(events, state, running)
            if next_trace_key != trace_key:
                trace_key = next_trace_key
                next_trace = render.trace(
                    events, state, running=running, include_footer=False
                )
                if next_trace != trace_html:
                    trace_update = next_trace
                    trace_html = next_trace

            metrics_update = gr.update()
            next_metrics_key = (_metrics_key(state), len(events), running)
            if next_metrics_key != metrics_key:
                metrics_key = next_metrics_key
                next_metrics = render.trace_metrics(state, events, running)
                if next_metrics != metrics_html:
                    metrics_update = next_metrics
                    metrics_html = next_metrics

            head_update = approval_update = gr.update()
            next_head_key = _head_key(events, state, session)
            if next_head_key != head_key:
                head_key = next_head_key
                next_head = render.conversation_head(
                    index, session=session, events=events, state=state
                )
                if next_head != head_html:
                    head_update = next_head
                    head_html = next_head
                # A card that ends the turn waits for the final frame, which also carries
                # the archived turn its continuation is appended to.
                next_approval = _research_card(session) if running else approval_html
                if next_approval != approval_html:
                    approval_update = next_approval
                    approval_html = next_approval
            yield (
                gr.update(),
                head_update,
                gr.update(),
                live_update,
                trace_update,
                metrics_update,
                render.evidence(session) if changed else gr.update(),
                approval_update,
                gr.update(),
                session,
                gr.update(),
            )
    except Exception as exc:
        answer = "The run failed: %s: %s" % (type(exc).__name__, exc)
        events = events or []
        state = state or agent.new_state(model_id, session)
        failure = {
            "kind": "harness_stop",
            "at": time.strftime("%H:%M:%S"),
            "rule": "unhandled_exception",
            "reason": answer,
        }
        events.append(failure)
        audit.exception("ui_turn_exception", exc, session=session, ui_turn=index)

    if preserve_conversation and turns:
        # Keep the approval continuation in the existing assistant turn. This gives the
        # next normal question the final report without creating a visible synthetic user
        # message such as “I approve formal execution ...”.
        previous = dict(turns[-1])
        previous["answer"] = (previous.get("answer", "") + "\n\n" + answer).strip()
        previous["events"] = list(previous.get("events") or []) + list(events)
        previous["faulted"] = previous.get("faulted", False) or _faulted(events)
        turns = turns[:-1] + [previous]
    else:
        turns = turns + [_archive(index, state, events, question, answer)]
    _stop_clock(session, events)
    if turns and not preserve_conversation:
        turns = turns[:-1] + [_publish_report(session, answer, model_id, turns[-1])]
    audit.emit(
        "ui_turn_finished",
        session=session,
        ui_turn=index,
        answer=answer,
        event_count=len(events),
        final_agent_event=(events[-1] if events else None),
        state_phase=state.get("phase"),
        counters={
            "model_calls": state.get("model_calls", 0),
            "tool_calls": state.get("tool_calls", 0),
            "model_runs": state.get("model_runs", 0),
            "interventions": state.get("interventions", 0),
        },
    )
    frame = list(_final_frame(model_id, session, turns, events, state))
    if preserve_conversation:
        frame[2] = gr.update()
        frame[3] = render.live_result(answer, running=False)
    # The box was emptied on the first yield, when this question was consumed. Whatever
    # is in it now is the next question, typed while this one ran, and is not ours to
    # clear -- _final_frame leaves it alone.
    yield tuple(frame)


def reset(model_id):
    """Clearing the conversation drops the evidence and the session budget with it. The
    hourly deployment quota is shared across visitors and deliberately survives."""
    session = _new_session(model_id)
    audit.emit("ui_session_reset", session=session)
    return (
        render.hero(model_id, running=False, status="Idle"),
        render.conversation_head(0, session=session),
        render.history([], session=session),
        render.live("", ""),
        render.trace([], agent.new_state(model_id, session), running=False, include_footer=False),
        render.trace_metrics(agent.new_state(model_id, session)),
        render.evidence(session),
        _research_card(session),
        [],
        session,
        "",
    )


def stop_click(box):
    """Ask the running turn to end. The agent loop reads the flag between chunks, tool
    calls and rate-limit waits, so the turn finishes through its normal path and is
    archived with what it had, instead of being torn down mid-yield."""
    if isinstance(box, dict):
        box["stop_requested"] = True
        audit.emit("ui_stop_requested", session=box)


def review_click(box, action):
    """Advance a human gate and request an agent continuation only after final approval."""
    session = box if isinstance(box, dict) else None
    command = ""
    if session and session.get("research"):
        phase_before = session["research"].get("phase")
        result = research.review_action(session, action)
        # One plan approval should lead directly to the display-only preview.  The
        # physical model remains blocked; the user gets one later figure-confirmation
        # click before formal execution.
        if (
            action == "primary"
            and phase_before == "plan_review"
            and session["research"].get("phase") == "plan_approved"
        ):
            result = research.pseudo_preview(session)
        audit.bind(session)
        audit.emit(
            "human_research_review",
            session=session,
            action=action,
            phase_before=phase_before,
            phase_after=session["research"].get("phase"),
            result_status=(result or {}).get("status"),
            result_summary=(result or {}).get("summary"),
        )
        if research.allow_model(session):
            # Formal execution approval is the run approval. Do not ask a second time.
            approval.set_mode(session, approval.ALWAYS)
        if (
            (
                action in ("primary", "satisfied_figures")
                and phase_before in ("pseudo_preview", "chart_selected")
                or action == "satisfied_figures" and phase_before == "plan_review"
            )
            and research.allow_model(session)
        ):
            # The phase transition is idempotent, but the continuation is a one-shot
            # capability.  This guard covers a second browser click before Gradio has
            # repainted the button.
            if not session["research"].get("execution_resume_sent"):
                session["research"]["execution_resume_sent"] = True
                command = EXECUTION_COMMAND
    else:
        # A ``run_model`` request paused its turn. The first verdict on it starts the
        # continuation, which is appended to the paused turn; a second click finds the
        # request already decided and starts nothing.
        decision = {"primary": "approve", "satisfied_figures": "reject"}[action]
        waiting = approval.pending(session) if session else None
        if waiting and approval.decide(session, decision):
            described = waiting["description"]
            verb = "Approved" if decision == "approve" else "Declined"
            command = f"{verb} the run of {described['model']} as {described['shape']}."
    # Review actions can create or remove pseudo figures.  Refresh evidence in the same
    # click response; waiting for a later agent stream left the Figures badge at zero and
    # made a valid preview look empty to the user.
    return _research_card(session), render.evidence(session), session, command


def resume_after_review(command, turns, box, model_id):
    """A distinct, approval-only route; normal questions still have one Send binding."""
    if not str(command or "").strip():
        # The primary button is shared by plan approval and final execution approval.  For
        # the earlier plan phases there is no agent continuation to run, but Gradio still
        # invokes this chained callback with the full Live Agent output list.  Returning no
        # frame lets Gradio treat missing values as a refresh/reset.  Emit explicit no-op
        # updates instead, so review_click's research-context update is the only visible
        # change and the conversation remains mounted.
        yield tuple(gr.update() for _ in range(11))
        return
    yield from respond(command, turns, box, model_id, preserve_conversation=True)


def select_chart_click(box, chart_id):
    """Record an explicit human chart click without asking the LLM to infer an ID."""
    session = box if isinstance(box, dict) else None
    chart_id = str(chart_id or "").strip()
    if session and session.get("research") and chart_id:
        result = research.choose_chart(session, chart_id)
        audit.bind(session)
        audit.emit(
            "human_chart_selected",
            session=session,
            chart_id=chart_id,
            result_status=result.get("status"),
            result_summary=result.get("summary"),
        )
    # Selecting the final package clears pseudo figures, so evidence must be refreshed
    # here as well rather than retaining stale preview cards until formal execution.
    return _research_card(session), render.evidence(session), session, ""


def _evaluation_session(box, model_id):
    if isinstance(box, dict) and box.get("evaluation"):
        if evaluation.expired(box):
            evaluation.clear(box)
            return evaluation.new_session(model_id)
        evaluation.touch(box)
        return box
    return evaluation.new_session(model_id)


def _evaluation_result_html(result):
    result = result or {}
    data = result.get("data") or {}
    detail = ""
    if data:
        detail = "<pre class='eval-temp-detail'>%s</pre>" % render._e(
            json.dumps(data, ensure_ascii=False, indent=2, default=str)
        )
    css = "badge--ok" if result.get("status") == "success" else "badge--warn"
    return "<div class='eval-temp-status'><span class='badge %s'>%s</span>%s</div>" % (
        css,
        render._e(result.get("summary") or result.get("error") or "No result."),
        detail,
    )


def evaluation_inspect(url, ref, box, model_id):
    session = _evaluation_session(box, model_id)
    result = evaluation.inspect_model(session, url, ref)
    return _evaluation_result_html(result), (result.get("data") or {}).get("proposal_id", ""), session


def evaluation_approve(proposal_id, box, model_id):
    session = _evaluation_session(box, model_id)
    result = evaluation.approve_model(session, proposal_id)
    return _evaluation_result_html(result), session


def evaluation_guideline(model, version, content, file_path, box, model_id):
    session = _evaluation_session(box, model_id)
    if file_path:
        try:
            content = Path(file_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return _evaluation_result_html({"status": "terminal_error", "summary": "Guideline upload failed: %s" % exc}), session
    result = evaluation.attach_guideline(session, model, content, version)
    return _evaluation_result_html(result), session


def evaluation_ingest_doi(doi, box, model_id):
    session = _evaluation_session(box, model_id)
    result = evaluation.ingest_doi(session, doi)
    return _evaluation_result_html(result), render.evidence(session), session


def evaluation_ingest_pdf(file_path, box, model_id):
    session = _evaluation_session(box, model_id)
    result = evaluation.ingest_pdf(session, file_path)
    return _evaluation_result_html(result), render.evidence(session), session, None


def evaluation_run(question, model, box, model_id):
    session = _evaluation_session(box, model_id)
    answer, events, state, result = evaluation.run_test(session, question, model or None)
    return (
        render.answer_html(answer),
        render.trace(events, state or agent.new_state(session=session), running=False, include_footer=False),
        render.evidence(session),
        _evaluation_result_html(result),
        session,
    )


def evaluation_clear(box, model_id):
    if isinstance(box, dict):
        evaluation.clear(box)
    session = evaluation.new_session(model_id)
    cleared = "<span class='badge badge--mute'>Temporary Evaluation data cleared.</span>"
    return (
        cleared,
        "",
        cleared,
        "",
        None,
        cleared,
        "",
        render.trace([], agent.new_state(session=session), running=False, include_footer=False),
        render.evidence(session),
        session,
        None,
    )


with gr.Blocks(title="PhysEarth-Agent", fill_height=True) as demo:
    turns_state = gr.State([])
    session_box = gr.State(None)
    evaluation_session_box = gr.State(None)
    basic_evaluation_cases = evals.basic_cases()
    evaluation_cases = evals.demo_cases()
    guided_evaluation_cases = evals.guided_demo_cases()
    demo_buttons = []
    guided_demo_buttons = []

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
                        "<h2>Run a basic case</h2></div><p>Three short checks show direct model "
                        "execution, sensitivity analysis, and evidence-gated scientific "
                        "refusal.</p></div></section></div>",
                        elem_classes=["pe-eval-slot"],
                    )
                    with gr.Row(elem_classes=["eval-demo-grid"]):
                        for case in basic_evaluation_cases:
                            with gr.Column(elem_classes=["eval-demo-cell"]):
                                gr.HTML(evals.demo_card(case), elem_classes=["pe-eval-slot"])
                                button = gr.Button(
                                    "Try in Live Agent",
                                    elem_classes=["eval-demo-button"],
                                )
                                demo_buttons.append((button, case["question"], case["id"]))
                    gr.HTML(
                        "<div class='eval-dashboard'><section "
                        "class='eval-section eval-section--demos'>"
                        "<div class='eval-section__head'><div><span class='eval-index'>03</span>"
                        "<h2>Start a guided paper reproduction</h2></div><p>Begin with a "
                        "paper-grounded SMRT question. The agent will explain the paper, check "
                        "model support, generate a reviewable plan, and wait for your review "
                        "before any physical execution.</p>"
                        "</div></section></div>",
                        elem_classes=["pe-eval-slot"],
                    )
                    with gr.Row(elem_classes=["eval-demo-grid"]):
                        for case in guided_evaluation_cases:
                            with gr.Column(elem_classes=["eval-demo-cell"]):
                                gr.HTML(evals.demo_card(case), elem_classes=["pe-eval-slot"])
                                button = gr.Button(
                                    case.get("button_label", "Start guided reproduction"),
                                    elem_classes=["eval-demo-button"],
                                )
                                guided_demo_buttons.append((button, case["question"], case["id"]))
                    gr.HTML(evals.q1_comparison(), elem_classes=["pe-eval-slot"])
                    gr.HTML(evals.architecture(), elem_classes=["pe-eval-slot"])

            # Keep the temporary model/paper workbench implemented, but hide it until
            # it has been tested end to end.  Its handlers and session cleanup remain
            # available for a later UI release.
            with gr.Tab("Upload & Test", id="upload", elem_id="pe-upload-tab", visible=False):
                with gr.Column(elem_id="pe-upload-page"):
                    gr.HTML(
                        "<section class='upload-hero'><span class='upload-hero__eyebrow'>TEMPORARY WORKSPACE</span>"
                        "<h1>Bring a model or paper into a clean test session.</h1>"
                        "<p>Inspect model code safely, upload a guideline or paper, and run a temporary test. "
                        "Nothing here is added to the Live Agent or persistent project storage.</p></section>",
                        elem_classes=["pe-upload-slot"],
                    )
                    with gr.Row(elem_classes=["upload-grid"]):
                        with gr.Column(elem_classes=["upload-card"]):
                            gr.HTML(
                                "<div class='upload-card__head'><span class='upload-card__number'>01</span>"
                                "<div><h2>Register a model</h2><p>Read-only inspection first; approval is required before testing.</p></div></div>"
                            )
                            with gr.Accordion("Inspect GitHub repository", open=True):
                                with gr.Row(elem_classes=["upload-form-row"]):
                                    evaluation_github_url = gr.Textbox(label="GitHub URL", placeholder="https://github.com/org/model")
                                    evaluation_github_ref = gr.Textbox(label="Ref / commit", value="main")
                                evaluation_inspect_button = gr.Button("Inspect repository", variant="secondary")
                            evaluation_proposal_status = gr.HTML(
                                "<span class='badge badge--mute'>No repository inspected.</span>",
                                elem_classes=["upload-status"],
                            )
                            with gr.Accordion("Attach a model guideline", open=False):
                                with gr.Row(elem_classes=["upload-form-row"]):
                                    evaluation_guideline_model = gr.Textbox(label="Model name")
                                    evaluation_guideline_version = gr.Textbox(label="Version", value="1.0")
                                evaluation_guideline_text = gr.Textbox(
                                    label="Guideline (Markdown)", lines=4, placeholder="Semantics, valid ranges, outputs, and comparison cautions..."
                                )
                                evaluation_guideline_file = gr.File(
                                    label="Or choose a .md/.txt guideline", file_types=[".md", ".txt"], type="filepath"
                                )
                                evaluation_guideline_button = gr.Button("Attach guideline")
                            with gr.Row(elem_classes=["upload-approval-row"]):
                                evaluation_proposal_id = gr.Textbox(label="Proposal ID")
                                evaluation_approve_button = gr.Button("Approve and register", variant="primary")

                        with gr.Column(elem_classes=["upload-card"]):
                            gr.HTML(
                                "<div class='upload-card__head'><span class='upload-card__number'>02</span>"
                                "<div><h2>Ingest a paper</h2><p>Use a DOI or PDF for this temporary evaluation session only.</p></div></div>"
                            )
                            with gr.Row(elem_classes=["upload-form-row"]):
                                evaluation_doi = gr.Textbox(label="Paper DOI", placeholder="10.xxxx/xxxxx")
                                evaluation_doi_button = gr.Button("Ingest DOI", variant="secondary")
                            gr.HTML("<div class='upload-divider'><span>or upload the source file</span></div>")
                            with gr.Row(elem_classes=["upload-form-row"]):
                                evaluation_pdf = gr.File(label="Paper PDF", file_types=[".pdf"], type="filepath")
                                evaluation_pdf_button = gr.Button("Ingest PDF", variant="secondary")
                            evaluation_paper_status = gr.HTML(
                                "<span class='badge badge--mute'>No temporary paper ingested.</span>",
                                elem_classes=["upload-status"],
                            )
                            with gr.Accordion("Temporary paper evidence", open=False):
                                evaluation_evidence = gr.HTML(
                                    render.evidence({}, [], set(), set()), elem_classes=["upload-evidence"]
                                )

                    with gr.Column(elem_classes=["upload-card", "upload-card--test"]):
                        gr.HTML(
                            "<div class='upload-card__head'><span class='upload-card__number'>03</span>"
                            "<div><h2>Run a temporary test</h2><p>Use only the model and paper registered above. Results disappear when the workspace is cleared.</p></div></div>"
                        )
                        with gr.Row(elem_classes=["upload-form-row"]):
                            evaluation_test_model = gr.Textbox(label="Model name", placeholder="smrt")
                            evaluation_test_question = gr.Textbox(label="Test question", lines=2, placeholder="What should this temporary run check?")
                        with gr.Row(elem_classes=["upload-actions"]):
                            evaluation_run_button = gr.Button("Run temporary test", variant="primary")
                            evaluation_clear_button = gr.Button("Clear temporary data")
                        evaluation_test_status = gr.HTML(
                            "<span class='badge badge--mute'>No temporary test run.</span>",
                            elem_classes=["upload-status"],
                        )
                        with gr.Accordion("Test answer and trace", open=True):
                            evaluation_answer = gr.HTML(elem_classes=["upload-output"])
                            evaluation_trace = gr.HTML(elem_classes=["upload-output"])

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
                            # Research review shares the single left-panel scroll surface
                            # with the conversation, so a long plan cannot hide the controls.
                            with gr.Column(elem_id="pe-approve"):
                                research_context_slot = gr.HTML(
                                    render.research_context(None), elem_classes=["pe-slot"]
                                )
                                with gr.Row(elem_classes=["approve__row"]):
                                    approve = gr.Button(
                                        "Approve plan",
                                        variant="primary",
                                        elem_id="pe-approve-yes",
                                    )
                                    satisfied_figures = gr.Button(
                                        "Satisfied with figures", elem_id="pe-approve-all"
                                    )
                        with gr.Row(elem_classes=["composer__box"]):
                            question = gr.Textbox(
                                elem_id="pe-input",
                                show_label=False,
                                container=False,
                                lines=3,
                                placeholder=render.PLACEHOLDER,
                            )
                            stop = gr.Button("Stop the agent", elem_id="pe-stop")
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
        research_context_slot,
        turns_state,
        session_box,
        question,
    ]
    inputs = [question, turns_state, session_box, model_bridge]
    # Only one way in. ui.js owns the Enter key and clicks Send, so a second submit
    # binding here would be a second route to the same generator: two runs against one
    # session dict, interleaving their trace and evidence writes and spending the budget
    # twice.
    send_event = send.click(respond, inputs, outputs)
    active_stream_events = [send_event]
    evaluation_inspect_button.click(
        evaluation_inspect,
        [evaluation_github_url, evaluation_github_ref, evaluation_session_box, model_bridge],
        [evaluation_proposal_status, evaluation_proposal_id, evaluation_session_box],
        queue=False,
    )
    evaluation_approve_button.click(
        evaluation_approve,
        [evaluation_proposal_id, evaluation_session_box, model_bridge],
        [evaluation_proposal_status, evaluation_session_box],
        queue=False,
    )
    evaluation_guideline_button.click(
        evaluation_guideline,
        [evaluation_guideline_model, evaluation_guideline_version, evaluation_guideline_text, evaluation_guideline_file, evaluation_session_box, model_bridge],
        [evaluation_proposal_status, evaluation_session_box],
        queue=False,
    )
    evaluation_doi_button.click(
        evaluation_ingest_doi,
        [evaluation_doi, evaluation_session_box, model_bridge],
        [evaluation_paper_status, evaluation_evidence, evaluation_session_box],
        queue=False,
    )
    evaluation_pdf_button.click(
        evaluation_ingest_pdf,
        [evaluation_pdf, evaluation_session_box, model_bridge],
        [evaluation_paper_status, evaluation_evidence, evaluation_session_box, evaluation_pdf],
        queue=False,
    )
    # An agent turn spends model calls, so it waits in the queue like Send does; outside
    # it, repeated clicks start parallel turns on one session.
    evaluation_run_button.click(
        evaluation_run,
        [evaluation_test_question, evaluation_test_model, evaluation_session_box, model_bridge],
        [evaluation_answer, evaluation_trace, evaluation_evidence, evaluation_test_status, evaluation_session_box],
    )
    evaluation_clear_button.click(
        evaluation_clear,
        [evaluation_session_box, model_bridge],
        [
            evaluation_proposal_status,
            evaluation_proposal_id,
            evaluation_paper_status,
            evaluation_guideline_text,
            evaluation_guideline_file,
            evaluation_test_status,
            evaluation_answer,
            evaluation_trace,
            evaluation_evidence,
            evaluation_session_box,
            evaluation_pdf,
        ],
        queue=False,
    )
    for button, demo_question, demo_id in demo_buttons:
        button.click(
            lambda model_id, text=demo_question, case_id=demo_id: start_basic_case(
                text, case_id, model_id
            ),
            inputs=[model_bridge],
            outputs=outputs + [main_tabs],
            queue=False,
            cancels=active_stream_events,
        )
    for button, demo_question, demo_id in guided_demo_buttons:
        button.click(
            lambda model_id, text=demo_question, case_id=demo_id: start_guided_demo(
                text, model_id, case_id
            ),
            inputs=[model_bridge],
            outputs=outputs + [main_tabs],
            queue=False,
            cancels=active_stream_events,
        )
    chart_submit.click(
        select_chart_click,
        [session_box, chart_bridge],
        [research_context_slot, evidence_slot, session_box, chart_bridge],
        concurrency_limit=None,
        queue=False,
    )

    # These two must be able to run while `respond` is blocked inside the gate waiting
    # for them, so they are exempt from the queue's concurrency limit. Without that the
    # click would sit behind the very generator it is meant to release.
    for button, decision in (
        (approve, "primary"),
        (satisfied_figures, "satisfied_figures"),
    ):
        review_event = button.click(
            lambda box, verdict=decision: review_click(box, verdict),
            [session_box],
            [research_context_slot, evidence_slot, session_box, review_command],
            concurrency_limit=None,
            queue=False,
        )
        # The earlier review phases only mutate their explicit gate. Formal execution
        # approval also resumes the same agent, so the button results in a real model run
        # and selected plot instead of merely changing a state label.
        if decision in ("primary", "satisfied_figures"):
            resume_event = review_event.then(
                resume_after_review,
                [review_command, turns_state, session_box, model_bridge],
                outputs,
            )
            active_stream_events.append(resume_event)

    # Like the review buttons, Stop has to run while `respond` is still streaming.
    stop.click(
        stop_click, [session_box], None, concurrency_limit=None, queue=False,
    )

    # Resetting the panels is not enough while a streamed response is still alive: its
    # next yield can repaint the freshly cleared UI with the old question's trace and
    # figures. Clear cancels both normal Send and the approval-triggered formal execution.
    clear.click(
        reset,
        [model_bridge],
        outputs,
        cancels=active_stream_events,
        concurrency_limit=None,
        queue=False,
    )

demo.queue(default_concurrency_limit=8)


def _bypass_proxy_for_local_server(host):
    """Keep Gradio's local startup checks off externally configured proxies.

    Gradio 6 uses httpx to call ``/gradio_api/startup-events`` after binding the
    server. In development environments with a global HTTP proxy, that request
    can be sent to the proxy instead of this process and return a misleading 503.
    Preserve the proxy for external services while bypassing it for local hosts.

    Only act when the proxy is configured in the environment, because that is the
    only case this guards. ``getproxies`` is ``getproxies_environment() or
    getproxies_macosx_sysconf()``: writing NO_PROXY when no proxy variable is set
    makes the first call truthy and hides a proxy configured in macOS System
    Settings from everything that resolves it that way -- httpx, and so the
    OpenAI client, which then connects direct and raises APIConnectionError on
    every model call.  A system proxy carries its own exception list for
    loopback, so there is nothing for us to add there.
    """
    env_proxies = urllib.request.getproxies_environment()
    if not any(scheme != "no" for scheme in env_proxies):
        return
    local_hosts = ["127.0.0.1", "localhost", "::1"]
    if host and host not in {"0.0.0.0", "::", "localhost"}:
        local_hosts.append(str(host))
    for variable in ("NO_PROXY", "no_proxy"):
        current = [item.strip() for item in os.environ.get(variable, "").split(",") if item.strip()]
        existing = {item.lower() for item in current}
        current.extend(item for item in local_hosts if item.lower() not in existing)
        os.environ[variable] = ",".join(current)


def main():
    """Launch the Studio. Called by the root app.py, which the deployspec names."""
    try:
        _bypass_proxy_for_local_server(config.get("PHYSEARTH_HOST"))
        audit.runtime(
            "service_launch",
            host=config.get("PHYSEARTH_HOST"),
            port=int(config.get("PHYSEARTH_PORT")),
        )
        demo.launch(
            server_name=config.get("PHYSEARTH_HOST"),
            server_port=int(config.get("PHYSEARTH_PORT")),
            # Gradio 6's frontend template expects body_css to be a mapping. Passing
            # the theme at launch time is required in Gradio 6; setting it on Blocks is
            # deprecated and leaves body_css=None on the pre-launch config.
            theme=gr.themes.Default(),
            css=theme.css(),
            js=theme.js(),
            head=theme.head(),
            allowed_paths=[str(config.state_dir().resolve())],
        )
    except Exception as exc:
        audit.exception("service_crash", exc)
        raise


if __name__ == "__main__":
    main()

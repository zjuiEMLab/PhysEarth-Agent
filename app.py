import gradio as gr

from physearth import agent, config, diagnostics
from physearth.ui import render, theme

config.load_dotenv()

_REPORT = diagnostics.collect()
print(diagnostics.render(_REPORT), flush=True)


def _accumulated(turns):
    """Everything the session has read, run and drawn, oldest turn first."""
    figures, sections, datasets = [], set(), set()
    for turn in turns or []:
        figures.extend(turn["state"].get("figures") or [])
        sections |= set(turn["state"].get("sections_read") or ())
        datasets |= set(turn["state"].get("datasets_read") or ())
    return figures, sections, datasets


def _archive(turn, state, events, question, answer):
    """A turn keeps its own trace, so an old exchange can be reopened with its evidence."""
    return {
        "index": turn,
        "question": question,
        "answer": answer,
        "events": events,
        "state": {
            "model_runs": state.get("model_runs", 0),
            "sections_read": sorted(state.get("sections_read") or ()),
            "datasets_read": sorted(state.get("datasets_read") or ()),
            "figures": list(state.get("figures") or []),
            "interventions": state.get("interventions", 0),
        },
    }


def respond(question, turns, model_id):
    question = (question or "").strip()
    turns = list(turns or [])
    if not question:
        yield (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            turns,
            "",
        )
        return

    index = len(turns) + 1
    seen = [
        {"role": role, "content": content}
        for t in turns
        for role, content in (("user", t["question"]), ("assistant", t["answer"]))
    ]
    figures, sections, datasets = _accumulated(turns)

    yield (
        render.hero(model_id, running=True, status="Running"),
        render.conversation_head(index),
        render.history(turns),
        render.live(question, "", running=True),
        render.trace([], agent.new_state(model_id), running=True),
        render.evidence({}, figures, sections, datasets),
        turns,
        "",
    )

    answer, events, state = "", [], agent.new_state(model_id)
    try:
        for answer, events, state in agent.stream(question, seen, model_id):
            running = state.get("phase") != "done"
            yield (
                gr.update(),
                gr.update(),
                gr.update(),
                render.live(question, answer, running=running),
                render.trace(events, state, running=running),
                render.evidence(
                    state,
                    figures + list(state.get("figures") or []),
                    sections | set(state.get("sections_read") or ()),
                    datasets | set(state.get("datasets_read") or ()),
                ),
                gr.update(),
                "",
            )
    except Exception as exc:
        answer = "The run failed: %s: %s" % (type(exc).__name__, exc)
        events = events or []
        state = state or agent.new_state(model_id)

    turns = turns + [_archive(index, state, events, question, answer)]
    figures, sections, datasets = _accumulated(turns)
    yield (
        render.hero(model_id, running=False, status="Idle - %d events last run" % len(events)),
        render.conversation_head(len(turns)),
        render.history(turns),
        render.live("", ""),
        render.trace(events, state, running=False),
        render.evidence(state, figures, sections, datasets),
        turns,
        "",
    )


def reset(model_id):
    return (
        render.hero(model_id, running=False, status="Idle"),
        render.conversation_head(0),
        render.history([]),
        render.live("", ""),
        render.trace([], agent.new_state(model_id), running=False),
        render.evidence({}, [], set(), set()),
        [],
        "",
    )


with gr.Blocks(title="PhysEarth-Agent", fill_height=True) as demo:
    turns_state = gr.State([])

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
                        placeholder="Ask about snow, soil or vegetation microwave modelling",
                    )
                    clear = gr.Button("Clear", elem_id="pe-clear")
                    send = gr.Button("Send", variant="primary", elem_id="pe-send")
                gr.HTML(render.chips(), elem_classes=["pe-slot"])

            with gr.Column(elem_classes=["pe-panel", "pe-panel--trace"]):
                trace_slot = gr.HTML(
                    render.trace([], agent.new_state()), elem_classes=["pe-slot"]
                )

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
        turns_state,
        question,
    ]
    send.click(respond, [question, turns_state, model_bridge], outputs)
    question.submit(respond, [question, turns_state, model_bridge], outputs)
    clear.click(reset, [model_bridge], outputs)

if __name__ == "__main__":
    demo.launch(
        server_name=config.get("PHYSEARTH_HOST"),
        server_port=int(config.get("PHYSEARTH_PORT")),
        css=theme.css(),
        js=theme.js(),
        head=theme.head(),
    )

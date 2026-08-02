import gradio as gr

from physearth import agent, config, diagnostics, knowledge, render, theme

config.load_dotenv()

_REPORT = diagnostics.collect()
print(diagnostics.render(_REPORT), flush=True)

EXAMPLES = [
    "Which microstructure representations does SMRT offer, and which electromagnetic theory does each one work with?",
    "How is the vegetation contribution represented in a tau-omega emission model, and what does omega mean?",
    "What soil roughness and permittivity values were retrieved at Trail Valley Creek, and at which bands?",
    "Compare how MEMLS and SMRT describe snow microstructure. Where do they agree?",
    "Do not use any tools. From your own knowledge, write a full paragraph explaining how snow density affects 37 GHz brightness temperature.",
]


def respond(question, history):
    question = (question or "").strip()
    if not question:
        return history, "", render.EMPTY_TRACE
    try:
        answer, events, state = agent.run(question)
        trace = render.trace(events, state)
        answer = render.annotate_markers(answer)
    except Exception as exc:
        answer = "The run failed: %s: %s" % (type(exc).__name__, exc)
        trace = render.EMPTY_TRACE
    history = (history or []) + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
    return history, "", trace


def corpus_table():
    lines = [
        "| slug | year | scenarios | outputs | sections | license |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in knowledge.catalogue():
        lines.append(
            "| `%s` | %s | %s | %s | %d | %s |"
            % (
                entry["slug"],
                entry["year"],
                ", ".join(entry["scenarios"]),
                ", ".join(entry["outputs"]),
                len(knowledge.section_index(entry["slug"])),
                entry["license"],
            )
        )
    return "\n".join(lines)


with gr.Blocks(title="PhysEarth-Agent") as demo:
    gr.HTML(render.hero(config.get("MODELSCOPE_MODEL")))
    with gr.Row(equal_height=False):
        with gr.Column(scale=5):
            gr.HTML(
                '<div class="pe-panel-title"><span class="t">Conversation</span>'
                '<span class="h">ask about snow, soil or vegetation microwave modelling</span></div>'
            )
            chat = gr.Chatbot(height=430, show_label=False)
            question = gr.Textbox(
                placeholder="Type a question, or pick one below",
                show_label=False,
                lines=2,
                max_lines=6,
            )
            with gr.Row():
                send = gr.Button("Ask", variant="primary", scale=3)
                clear = gr.Button("Clear", variant="secondary", scale=1)
            gr.Examples(examples=EXAMPLES, inputs=question, label="Examples")
        with gr.Column(scale=4):
            gr.HTML(
                '<div class="pe-panel-title"><span class="t">Run trace</span>'
                '<span class="h">what the system did, and what it refused</span></div>'
            )
            trace = gr.HTML(render.EMPTY_TRACE)
    with gr.Accordion("Bundled corpus", open=False):
        gr.Markdown(corpus_table())
    with gr.Accordion("Runtime self-check", open=False):
        gr.Markdown(diagnostics.render(_REPORT))

    send.click(respond, [question, chat], [chat, question, trace])
    question.submit(respond, [question, chat], [chat, question, trace])
    clear.click(lambda: ([], "", render.EMPTY_TRACE), outputs=[chat, question, trace])

if __name__ == "__main__":
    demo.launch(
        server_name=config.get("PHYSEARTH_HOST"),
        server_port=int(config.get("PHYSEARTH_PORT")),
        theme=theme.theme(),
        css=theme.CSS,
    )

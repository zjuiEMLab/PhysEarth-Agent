import gradio as gr

from physearth import __version__, agent, config, diagnostics, knowledge

config.load_dotenv()

_REPORT = diagnostics.collect()
print(diagnostics.render(_REPORT), flush=True)

EXAMPLES = [
    "Which microstructure representations does SMRT offer, and which electromagnetic theory does each one work with?",
    "How is the vegetation contribution represented in a tau-omega emission model, and what does omega mean?",
    "What soil roughness and permittivity values were retrieved at Trail Valley Creek, and at which bands?",
    "Compare how MEMLS and SMRT describe snow microstructure. Where do they agree?",
]

INTRO = """\
# PhysEarth-Agent

An open-source GeoAI agent for physical Earth models. This build answers from a bundled
corpus of %d open-access Copernicus papers on microwave radiative transfer over snow, soil
and vegetation.

Every scientific claim must carry a citation marker that resolves to a section the agent
actually read. The system checks this after the answer is written and sends the answer back
if a marker does not resolve. The run trace on the right shows every model call, every tool
call, and every time the system blocked an answer.
""" % len(knowledge.slugs())


def respond(question, history):
    question = (question or "").strip()
    if not question:
        return history, "", ""
    try:
        answer, events, state = agent.run(question)
        trace = agent.render_trace(events, state)
    except Exception as exc:
        answer = "The run failed: %s: %s" % (type(exc).__name__, exc)
        trace = "No trace: the run did not start."
    history = (history or []) + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
    return history, "", trace


def corpus_table():
    lines = ["| slug | year | scenarios | outputs | license |", "| --- | --- | --- | --- | --- |"]
    for entry in knowledge.catalogue():
        lines.append(
            "| %s | %s | %s | %s | %s |"
            % (
                entry["slug"],
                entry["year"],
                ", ".join(entry["scenarios"]),
                ", ".join(entry["outputs"]),
                entry["license"],
            )
        )
    return "\n".join(lines)


with gr.Blocks(title="PhysEarth-Agent", fill_height=True) as demo:
    gr.Markdown(INTRO)
    with gr.Row():
        with gr.Column(scale=3):
            chat = gr.Chatbot(height=460, label="Conversation")
            question = gr.Textbox(
                placeholder="Ask about snow, soil or vegetation microwave modelling",
                label="Question",
                lines=2,
            )
            with gr.Row():
                send = gr.Button("Send", variant="primary")
                clear = gr.Button("Clear")
            gr.Examples(examples=EXAMPLES, inputs=question, label="Try one")
        with gr.Column(scale=2):
            gr.Markdown("### Run trace")
            trace = gr.Markdown("The run trace appears here.")
    with gr.Accordion("Bundled corpus and environment", open=False):
        gr.Markdown(corpus_table())
        gr.Markdown(diagnostics.render(_REPORT))

    send.click(respond, [question, chat], [chat, question, trace])
    question.submit(respond, [question, chat], [chat, question, trace])
    clear.click(lambda: ([], "", "The run trace appears here."), outputs=[chat, question, trace])

if __name__ == "__main__":
    demo.launch(
        server_name=config.get("PHYSEARTH_HOST"),
        server_port=int(config.get("PHYSEARTH_PORT")),
    )

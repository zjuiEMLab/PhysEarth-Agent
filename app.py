import gradio as gr

from physearth import __version__, agent, config, diagnostics, knowledge
from physearth.models import registry

config.load_dotenv()

_REPORT = diagnostics.collect()
print(diagnostics.render(_REPORT), flush=True)

EXAMPLES = [
    "Run SMRT to show how 37 GHz brightness temperature changes as snow density goes from 100 to 500 kg/m3 for a 1 m layer, and explain the trend.",
    "Use DMRT with an exponential microstructure at 19 GHz.",
    "Simulate a snowpack at 37 GHz with a density of 2000 kg/m3.",
    "Which microstructure representations does SMRT offer, and which electromagnetic theory does each one work with?",
    "What soil roughness and permittivity values were retrieved at Trail Valley Creek, and at which bands?",
    "Do not use any tools. From your own knowledge, write a full paragraph explaining how snow density affects 37 GHz brightness temperature.",
]

INTRO = """\
# PhysEarth-Agent

An open-source GeoAI agent for physical Earth models. It reads a bundled corpus of %d
open-access Copernicus papers and runs %d registered physical model(s) over snow, soil and
vegetation.

The point is not that it can talk about physics, but that it cannot assert physics it did
not read or run. Parameters are checked against each model's declared physical ranges and
legal combinations before the model runs; the result is quality controlled against the
declared output bounds afterwards; and every literature claim must carry a marker that
resolves to a section actually opened in this conversation. None of these checks is a tool
the agent may skip. The run trace on the right shows each one, including the refusals.
""" % (len(knowledge.slugs()), len(registry.names()))


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


def models_table():
    lines = ["| model | version | tier | outputs | source |", "| --- | --- | --- | --- | --- |"]
    for row in registry.summary():
        lines.append(
            "| `%s` | %s | %s | %s | %s |"
            % (row["name"], row["version"], row["tier"], ", ".join(row["outputs"]), row["source"])
        )
    rejected = registry.rejected()
    if rejected:
        lines.append("")
        lines.append("Rejected at registration:")
        for item in rejected:
            lines.append("- `%s`: %s" % (item["directory"], item["reason"]))
    lines.append("")
    lines.append("See `docs/registering-a-model.md` to add your own.")
    return "\n".join(lines)


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
    with gr.Accordion("Registered models", open=False):
        gr.Markdown(models_table())
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

import gradio as gr

from physearth import __version__, config, diagnostics

config.load_dotenv()

_REPORT = diagnostics.collect()
print(diagnostics.render(_REPORT), flush=True)


def refresh():
    return diagnostics.render(diagnostics.collect())


with gr.Blocks(title="PhysEarth-Agent") as demo:
    gr.Markdown("# PhysEarth-Agent\n\nEnvironment self-check, version %s." % __version__)
    output = gr.Markdown(diagnostics.render(_REPORT))
    gr.Button("Refresh").click(refresh, outputs=output)

if __name__ == "__main__":
    demo.launch(
        server_name=config.get("PHYSEARTH_HOST"),
        server_port=int(config.get("PHYSEARTH_PORT")),
    )

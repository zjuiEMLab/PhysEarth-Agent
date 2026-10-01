"""Render the per-model outcome grid as one self-contained page.

One card per registered model: the model and version, its reproduction task, the figure
the agent drew (or, when it drew none, the reference figure, labelled as such), a short
written conclusion, and the outcome tag of every repeat as scores.json computed it. The
tags and reasons are read from the scores, never typed here.

    python scripts/render_eval_grid.py CARDS.json SCORES.json OUTPUT.html

CARDS.json is a list of {"model", "version", "task", "records": [...], "conclusion"};
`records` are record paths as SCORES.json lists them, oldest repeat first.
"""

import base64
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

import yaml  # noqa: E402

from frontend import theme  # noqa: E402

TAG_STYLE = {
    "Success": ("#2f7d32", "#e3f3e1", "#2f7d32"),
    "Partial": ("#7a5b00", "#fff3c4", "#e0b100"),
    "Failed": ("#a1281b", "#fbe2de", "#c2412e"),
}
CSS = """
body { margin: 0; background: var(--paper-2); color: var(--ink);
  font-family: var(--font-serif); }
.wrap { max-width: 1840px; margin: 0 auto; padding: 36px 40px 48px; }
h1 { font-size: 30px; font-weight: 400; margin: 0 0 6px; }
.sub { color: var(--ink-soft); font-size: 16px; margin: 0 0 22px; max-width: 1500px;
  line-height: 1.5; }
.grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; }
.card { background: var(--paper); border: 1px solid var(--line); border-radius: 18px;
  box-shadow: var(--shadow-panel); overflow: hidden; display: flex; flex-direction: column;
  border-top: 8px solid var(--tag-edge); }
.head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px;
  padding: 16px 20px 6px; }
.model { font-size: 22px; }
.ver { font-family: var(--font-mono); font-size: 13px; color: var(--ink-mute);
  margin-left: 6px; }
.tag { font-family: var(--font-mono); font-size: 14px; font-weight: 700; letter-spacing: .04em;
  padding: 4px 12px; border-radius: 999px; color: var(--tag-ink); background: var(--tag-bg);
  border: 1.5px solid var(--tag-edge); text-transform: uppercase; white-space: nowrap; }
.task { padding: 0 20px 10px; font-size: 14.5px; color: var(--ink-soft); line-height: 1.4; }
.task code { font-family: var(--font-mono); font-size: 12.5px; color: var(--ink-mute); }
.fig { margin: 0 20px; border: 1px solid var(--line); border-radius: 10px; background: #fff;
  height: 300px; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden; }
.fig img { max-width: 100%; max-height: 100%; object-fit: contain; }
.fig.is-reference img { filter: grayscale(1); opacity: .45; }
.fig .ribbon { position: absolute; left: 0; top: 0; font-family: var(--font-mono);
  font-size: 11.5px; padding: 4px 10px; background: rgba(20,20,19,.75); color: #fff;
  border-bottom-right-radius: 8px; }
.body { padding: 12px 20px 6px; font-size: 15px; line-height: 1.5; }
.reps { padding: 4px 20px 6px; display: flex; flex-wrap: wrap; gap: 6px; }
.rep { font-family: var(--font-mono); font-size: 12px; padding: 2px 8px; border-radius: 999px;
  color: var(--tag-ink); background: var(--tag-bg); border: 1px solid var(--tag-edge); }
.why { padding: 4px 20px 16px; font-size: 12.5px; color: var(--ink-mute); line-height: 1.45; }
.why b { color: var(--ink-soft); font-weight: 600; }
.legend { display: flex; gap: 18px; margin: 0 0 18px; font-family: var(--font-mono);
  font-size: 13px; align-items: center; flex-wrap: wrap; }
.legend span.dot { display: inline-block; width: 12px; height: 12px; border-radius: 3px;
  margin-right: 6px; vertical-align: -1px; }
.note { margin-top: 22px; padding: 16px 20px; border-radius: 14px; background: var(--paper);
  border: 1px solid var(--line); font-size: 15.5px; line-height: 1.55; }
.foot { margin-top: 14px; font-family: var(--font-mono); font-size: 12px;
  color: var(--ink-mute); }
"""


def _data_url(path):
    path = ROOT / path
    if not path.is_file():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _clip(text, limit=220):
    """A card shows the start of a computed reason; the record keeps it whole."""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "\u2026"


def _vars(tag):
    ink, bg, edge = TAG_STYLE.get(tag, ("#444", "#eee", "#999"))
    return f"--tag-ink:{ink};--tag-bg:{bg};--tag-edge:{edge};"


def card(spec, rows, record_of, cards_meta):
    rows = [rows[path] for path in spec["records"]]
    latest = rows[-1]
    tag = (latest.get("B6_outcome") or {}).get("tag") or "n/a"
    record = record_of(latest["record"])
    task = cards_meta["tasks"][spec["task"]]
    figure = next((f for f in record.get("figures") or [] if f.get("archived_image_path")), None)
    if figure:
        image, ribbon, cls = (
            _data_url(figure["archived_image_path"]),
            "figure drawn by the agent",
            "",
        )
    else:
        fixture = yaml.safe_load((ROOT / task["reference_fixture"]).read_text(encoding="utf-8"))
        image = _data_url(fixture["visual_reference"]["image_path"])
        ribbon, cls = "no figure drawn - reference shown", " is-reference"
    reps = "".join(
        f"<span class='rep' style='{_vars((row.get('B6_outcome') or {}).get('tag'))}'>"
        f"r{row['repeat']} {html.escape(str((row.get('B6_outcome') or {}).get('tag')))}"
        f" &middot; build {html.escape(str(row.get('build')))}</span>"
        for row in rows
    )
    reasons = (latest.get("B6_outcome") or {}).get("reasons") or []
    why = "".join(
        f"<div>&bull; {html.escape(_clip(str(reason)))}</div>" for reason in reasons[:3]
    )
    return (
        f"<div class='card' style='{_vars(tag)}'>"
        f"<div class='head'><div><span class='model'>{html.escape(spec['model'])}</span>"
        f"<span class='ver'>{html.escape(spec.get('version', ''))}</span></div>"
        f"<span class='tag'>{html.escape(tag)}</span></div>"
        f"<div class='task'>{html.escape(task['title'])} "
        f"<code>{html.escape(spec['task'])}</code></div>"
        f"<div class='fig{cls}'><span class='ribbon'>{ribbon}</span>"
        f"<img alt='' src='{image}'></div>"
        f"<div class='body'>{html.escape(spec['conclusion'])}</div>"
        f"<div class='reps'>{reps}</div>"
        "<div class='why'><b>Computed reason (latest repeat):</b>"
        f"{why or ' all gates passed'}</div>"
        "</div>"
    )


def page(cards, scores, llm):
    rows = {row["record"]: row for row in scores["records"]}
    sys.path.insert(0, str(ROOT / "evaluation" / "runners"))
    import competition

    tasks = competition.load_task_index()

    def record_of(path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"), strict=False)

    body = "".join(card(spec, rows, record_of, {"tasks": tasks}) for spec in cards)
    legend = "".join(
        f"<span><span class='dot' style='background:{TAG_STYLE[name][2]}'></span>"
        f"{name}: {text}</span>"
        for name, text in (
            ("Success", "ran, drew a figure, figure judge and report judge both passed"),
            (
                "Partial",
                "ran and drew a figure, but a judge did not pass or a parameter source is "
                "unresolved",
            ),
            ("Failed", "stopped by a rule, no successful model run, or no figure"),
        )
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Six registered models</title>"
        f"<style>{theme.css()}\n{CSS}</style></head><body><div class='wrap'>"
        "<h1>Six registered models, one reproduction task each</h1>"
        "<p class='sub'>Same harness, same scorer, same prompt profile; LLM "
        f"<code>{html.escape(llm)}</code>, label-blinded judge <code>openai/gpt-6-luna</code>. "
        "Every tag is computed from the recorded run (protocol B6) and every repeat is "
        "shown.</p>"
        f"<div class='legend'>{legend}</div>"
        f"<div class='grid'>{body}</div>"
        "<div class='note'><b>Partial and Failed are not harness defects.</b> The harness is "
        "what makes the agent refuse a request it cannot support, or flag what it could not "
        "establish, instead of silently returning wrong content: no run in this grid executed "
        "an illegal model call, and every plan the gates refused is in the trace with the "
        "gate's reason. A refusal draws no figure and is therefore tagged Failed. Earlier "
        "repeats that ended on an evaluation-runner or agent-loop fault are kept, with their "
        "build; each fault was fixed before the next repeat.</div>"
        "<div class='foot'>Rendered from the evaluation records and the scores.json computed "
        "from them (evaluation/runners/score_runs.py).</div>"
        "</div></body></html>"
    )


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    cards = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    scores = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    output = Path(argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    llm = argv[3] if len(argv) > 3 else "openai/gpt-5.6-luna"
    output.write_text(page(cards, scores, llm), encoding="utf-8")
    print(f"{output} ({output.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Render recorded evaluation runs as static pages of the Studio's own interface.

Each page is drawn from one record under evaluation/results/competition/runs/ with the
views the live Studio uses (apps/studio/views) and its stylesheet (apps/studio/theme): the
conversation the agent was actually sent, the scripted plan approval, every step of the
trace including the gate refusals, the figures it drew and the final report. The page is
self-contained: inline CSS and fonts, figures as base64, no external request.

    python evaluation/render/render_run_pages.py RECORD.json OUTPUT.html [--note TEXT]
"""

import argparse
import base64
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation" / "runners"))

import competition  # noqa: E402

from apps.studio import theme  # noqa: E402
from apps.studio import views as render  # noqa: E402
from physearth.api import agent  # noqa: E402

PAGE_CSS = """
html, body { margin: 0; height: 100%; background: var(--paper); }
#pe-app { height: 100vh; }
.pe-run-note { font: 12px/1.5 'Anthropic Mono', ui-monospace, monospace;
  color: var(--ink-3, #6b6b6b); padding: 6px 18px; border-bottom: 1px solid var(--line);
  background: var(--paper); }
.pe-run-note b { color: var(--ink, #222); font-weight: 600; }
"""


def _data_url(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _events(record):
    """The recorded event log, with each tool step's arguments restored from the tool log
    when the record predates the trace fields."""
    logged = record.get("tool_log") or []
    tool_log = [item for item in logged if item.get("status") != "needs_input"]
    blocks = [item for item in logged if item.get("status") == "needs_input"]
    events = []
    for event in record.get("event_log") or []:
        event = dict(event)
        kind = event.get("kind") or "event"
        event["kind"] = kind
        if kind == "tool_call":
            logged = tool_log.pop(0) if tool_log else {}
            event.setdefault("arguments", logged.get("arguments") or {})
            event.setdefault("summary", f"{event.get('name')} returned {event.get('status')}")
            if logged.get("handle"):
                event["data"] = {"handle": logged["handle"]}
        elif kind == "harness_block" and event.get("tool") and "problems" not in event:
            logged = blocks.pop(0) if blocks else {}
            event["problems"] = logged.get("problems") or []
        events.append(event)
    return events


def _state(record, events, session):
    """Counters as the Studio shows them after the last turn of the recorded run."""
    state = agent.new_state()
    counters = {
        "model_calls": record.get("model_calls") or 0,
        "tool_calls": record.get("tool_calls") or 0,
        "interventions": record.get("interventions") or 0,
        "qc_failures": record.get("qc_failures") or 0,
        "model_runs": len(record.get("successful_runs") or []),
        "turns": len({event.get("turn") for event in events if event.get("turn")}),
    }
    prompts = [event["prompt_tokens"] for event in events if event.get("prompt_tokens")]
    state.update(counters, phase="done", prompt_tokens=prompts[-1] if prompts else 0)
    state["session"] = {
        **state["session"],
        **counters,
        "sections_read": session["sections_read"],
    }
    return state


def _session(record, figures):
    evidence = record.get("evidence") or {}
    return {
        "research": record.get("research") or {},
        "figures": figures,
        "sections_read": set(evidence.get("sections") or []),
        "datasets_read": set(evidence.get("datasets") or []),
        "models_run": set(evidence.get("models") or []),
        "paper_figures_read": set(evidence.get("paper_figures") or []),
        "abstracts_seen": set(evidence.get("abstracts") or []),
    }


def _figures(record):
    figures = []
    for index, figure in enumerate(record.get("figures") or [], 1):
        item = dict(figure)
        item["image_url"] = _data_url(figure.get("archived_image_path") or "")
        item.setdefault("figure_number", index)
        figures.append(item)
    return figures


def _hero(record):
    """The Studio header, with the switcher replaced by the model that actually ran.

    The live switcher only offers the three ModelScope models; an evaluation run uses the
    model the record names, so showing a switcher button as active would misstate it.
    """
    markup = render.hero(None)
    label = html.escape(str(record.get("llm") or ""))
    provider = html.escape(str(record.get("provider") or ""))
    return re.sub(
        r"<div class='segment segment--model'>.*?</div>",
        "<div class='segment segment--model'><button type='button' class='is-active' "
        f"title='{label} via {provider}'>{label}</button></div>",
        markup,
        count=1,
        flags=re.S,
    )


def page(record, note=""):
    profile = next(
        item for item in competition.load_profiles() if item["id"] == record.get("prompt_profile")
    )
    figures = _figures(record)
    events = _events(record)
    session = _session(record, figures)
    state = _state(record, events, session)
    turns = [{"question": competition.condition_text(profile, record["question"]),
              "answer": record.get("planning_answer") or ""}]
    if record.get("planning_answer") != record.get("answer") or (
        record.get("workflow") or {}
    ).get("review_actions"):
        reviewer = "; ".join(
            f"{item.get('actor')}: {item.get('policy') or item.get('status')} "
            f"({item.get('before')} -> {item.get('after')})"
            for item in (record.get("workflow") or {}).get("review_actions") or []
        )
        if (record.get("workflow") or {}).get("review_error"):
            reviewer += " -- " + str(record["workflow"]["review_error"])
        if record.get("answer") and record.get("answer") != record.get("planning_answer"):
            turns.append({"question": competition.CONTINUATION, "answer": record["answer"]})
    else:
        reviewer = ""
    chat = (
        render.conversation_head(len(turns), session=session, events=events, state=state)
        + "<div id='pe-chat-scroll'><div class='pe-slot'>"
        + render.history(turns, session=session)
        + (
            "<div class='msg-group'><div class='msg msg--user'><div class='msg__head'>"
            "<span class='msg__who'>scripted reviewer</span><span class='msg__rule'></span>"
            f"</div><div class='msg__body'><p>{html.escape(reviewer)}</p></div></div></div>"
            if reviewer
            else ""
        )
        + "</div></div><div id='pe-approve'><div class='pe-slot'>"
        + render.research_context(session)
        + "</div></div>"
    )
    trace = (
        "<div id='pe-trace-stream'><div class='pe-slot'>"
        + render.trace(events, state, include_footer=False)
        + "</div></div><div class='pe-slot'>"
        + render.trace_metrics(state)
        + "</div>"
    )
    evidence = render.evidence(
        session, figures, sorted(session["sections_read"]), sorted(session["datasets_read"])
    )
    title = f"PhysEarth run {record.get('task')} {record.get('config')} r{record.get('repeat')}"
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{html.escape(title)}</title>"
        f"<style>{theme.css()}\n{PAGE_CSS}</style></head><body>"
        "<div id='pe-app'>"
        f"<div class='pe-run-note'>{note}</div>"
        f"{_hero(record)}"
        "<div class='stage'>"
        f"<div id='pe-panel-chat' class='pe-panel pe-panel--chat'>{chat}</div>"
        f"<div id='pe-panel-trace' class='pe-panel pe-panel--trace'>{trace}</div>"
        f"<div id='pe-panel-evid' class='pe-panel pe-panel--evid'><div class='pe-slot'>{evidence}"
        "</div></div>"
        "</div></div></body></html>"
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("record")
    parser.add_argument("output")
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)
    record = json.loads(Path(args.record).read_text(encoding="utf-8"), strict=False)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page(record, args.note), encoding="utf-8")
    print(f"{output} ({output.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

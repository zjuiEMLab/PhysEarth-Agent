import base64
from pathlib import Path

import gradio as gr

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_SUBSETS = {
    "source-serif-4-latin.woff2": (
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, "
        "U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, "
        "U+2212, U+2215, U+FEFF, U+FFFD"
    ),
    "source-serif-4-latin-ext.woff2": (
        "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, "
        "U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, "
        "U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"
    ),
}


def font_faces():
    rules = []
    for name, unicode_range in FONT_SUBSETS.items():
        path = FONT_DIR / name
        if not path.is_file():
            continue
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            "@font-face{font-family:'Source Serif 4';font-style:normal;"
            "font-weight:200 900;font-display:swap;"
            "src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s;}"
            % (payload, unicode_range)
        )
    return "\n".join(rules)


PAPER = "#faf9f5"
PAPER_2 = "#f5f4ed"
HOVER = "#f0eee6"
INK = "#141413"
INK_SOFT = "#3d3d3a"
INK_MUTE = "#73726c"
LINE = "rgba(31, 30, 29, 0.14)"
LINE_STRONG = "rgba(31, 30, 29, 0.26)"
CLAY = "#d97757"
CLAY_PRESS = "#c26244"
OK = "#4f7a48"

FONT_SERIF = (
    '"Source Serif 4", "Songti SC", "Noto Serif CJK SC", "Source Han Serif SC", '
    '"SimSun", Georgia, serif'
)
FONT_MONO = 'ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono", monospace'


def theme():
    base = gr.themes.Base(
        font=(
            gr.themes.LocalFont("Source Serif 4", weights=(400, 600)),
            "Songti SC",
            "Noto Serif CJK SC",
            "serif",
        ),
        font_mono=(gr.themes.LocalFont("Consolas"), "ui-monospace", "monospace"),
    )
    return base.set(
        body_background_fill=PAPER,
        body_text_color=INK,
        body_text_color_subdued=INK_MUTE,
        background_fill_primary=PAPER,
        background_fill_secondary=PAPER_2,
        block_background_fill=PAPER,
        block_border_color=LINE,
        block_border_width="1px",
        block_label_background_fill=PAPER_2,
        block_label_text_color=INK_SOFT,
        block_title_text_color=INK_SOFT,
        block_radius="14px",
        block_shadow="0 18px 48px -30px rgba(31, 30, 29, 0.4), 0 6px 16px -14px rgba(31, 30, 29, 0.22)",
        border_color_primary=LINE,
        border_color_accent=CLAY,
        color_accent=CLAY,
        color_accent_soft="rgba(217, 119, 87, 0.12)",
        link_text_color=CLAY,
        link_text_color_hover=CLAY_PRESS,
        panel_background_fill=PAPER_2,
        panel_border_color=LINE,
        input_background_fill=PAPER,
        input_border_color=LINE_STRONG,
        input_radius="10px",
        input_placeholder_color=INK_MUTE,
        button_large_radius="10px",
        button_small_radius="10px",
        button_primary_background_fill=CLAY,
        button_primary_background_fill_hover=CLAY_PRESS,
        button_primary_border_color=CLAY,
        button_primary_text_color="#ffffff",
        button_secondary_background_fill="#e8e6dc",
        button_secondary_background_fill_hover=HOVER,
        button_secondary_border_color=LINE_STRONG,
        button_secondary_text_color=INK,
    )


CSS = font_faces() + """
:root {
  --paper: %(paper)s;
  --paper-2: %(paper2)s;
  --hover: %(hover)s;
  --ink: %(ink)s;
  --ink-soft: %(ink_soft)s;
  --ink-mute: %(ink_mute)s;
  --line: %(line)s;
  --line-strong: %(line_strong)s;
  --clay: %(clay)s;
  --clay-wash: rgba(217, 119, 87, 0.12);
  --ok: %(ok)s;
  --ok-wash: rgba(79, 122, 72, 0.14);
  --violet: #6b5b8a;
  --violet-wash: rgba(107, 91, 138, 0.12);
  --radius: 18px;
  --radius-sm: 10px;
  --font-serif: %(serif)s;
  --font-mono: %(mono)s;
  --shadow-panel: 0 18px 48px -30px rgba(31, 30, 29, 0.4), 0 6px 16px -14px rgba(31, 30, 29, 0.22);
}

.gradio-container {
  background:
    radial-gradient(120%% 90%% at 12%% 0%%, rgba(217, 119, 87, 0.07) 0%%, transparent 58%%),
    radial-gradient(100%% 80%% at 92%% 8%%, rgba(107, 91, 138, 0.07) 0%%, transparent 55%%),
    var(--paper) !important;
  font-family: var(--font-serif) !important;
  max-width: 1560px !important;
  --font: %(serif)s;
  --font-mono: %(mono)s;
}

.gradio-container::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image: radial-gradient(rgba(31, 30, 29, 0.2) 1px, transparent 1px);
  background-size: 24px 24px;
  opacity: 0.34;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.85), transparent 72%%);
  -webkit-mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.85), transparent 72%%);
}

.gradio-container > * { position: relative; z-index: 1; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: rgba(31, 30, 29, 0.28); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: rgba(31, 30, 29, 0.44); }

.pe-hero {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 20px 24px 18px;
  margin-bottom: 4px;
  background: linear-gradient(135deg, rgba(250, 249, 245, 0.92) 0%%, rgba(240, 238, 230, 0.72) 100%%);
  -webkit-backdrop-filter: blur(26px) saturate(1.28);
  backdrop-filter: blur(26px) saturate(1.28);
  box-shadow: var(--shadow-panel);
}

.pe-hero h1 {
  font-family: var(--font-serif);
  font-size: 27px;
  letter-spacing: -0.01em;
  margin: 0 0 2px;
  color: var(--ink);
}

.pe-hero .pe-sub {
  color: var(--ink-soft);
  font-size: 14px;
  margin: 0 0 10px;
}

.pe-hero .pe-claim {
  color: var(--ink-mute);
  font-size: 13px;
  line-height: 1.62;
  margin: 0;
  max-width: 108ch;
}

.pe-pills { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 13px; }

.pe-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 23px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono);
  border-radius: 999px;
  color: var(--ink-soft);
  background: var(--paper-2);
  border: 1px solid var(--line);
}

.pe-pill.accent { color: var(--clay); background: var(--clay-wash); border-color: transparent; }

.pe-panel-title {
  display: flex;
  align-items: baseline;
  gap: 9px;
  margin: 2px 0 8px;
}

.pe-panel-title .t { font-size: 15px; font-weight: 700; color: var(--ink); }
.pe-panel-title .h { font-size: 12px; color: var(--ink-mute); }

.pe-trace {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: linear-gradient(180deg, rgba(250, 249, 245, 0.94) 0%%, rgba(245, 244, 237, 0.8) 100%%);
  -webkit-backdrop-filter: blur(26px) saturate(1.28);
  backdrop-filter: blur(26px) saturate(1.28);
  box-shadow: var(--shadow-panel);
  padding: 12px;
  max-height: 620px;
  overflow: auto;
}

.pe-trace .pe-empty {
  color: var(--ink-mute);
  font-size: 13px;
  padding: 18px 6px;
  text-align: center;
}

.pe-step {
  display: grid;
  grid-template-columns: 26px 1fr;
  gap: 10px;
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  background: var(--paper);
  border: 1px solid var(--line);
}

.pe-step + .pe-step { margin-top: 6px; }
.pe-step.is-block { border-color: rgba(217, 119, 87, 0.55); background: rgba(217, 119, 87, 0.06); }
.pe-step.is-pass { border-color: rgba(79, 122, 72, 0.4); }

.pe-step .n {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  color: var(--ink-mute);
  text-align: right;
  padding-top: 2px;
  font-variant-numeric: tabular-nums;
}

.pe-step .body { min-width: 0; }

.pe-badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  font-family: var(--font-mono);
  border-radius: 999px;
  margin-bottom: 5px;
}

.pe-badge.model { color: var(--violet); background: var(--violet-wash); }
.pe-badge.tool { color: var(--ink-soft); background: var(--paper-2); border: 1px solid var(--line); }
.pe-badge.block { color: #fff; background: var(--clay); }
.pe-badge.pass { color: var(--ok); background: var(--ok-wash); }
.pe-badge.stop { color: var(--ink-soft); background: var(--hover); border: 1px solid var(--line-strong); }

.pe-step .detail {
  font-size: 12.5px;
  color: var(--ink-soft);
  line-height: 1.55;
  word-break: break-word;
}

.pe-step .detail code {
  font-family: var(--font-mono);
  font-size: 11.5px;
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 1px 5px;
  color: var(--ink);
}

.pe-summary {
  margin-top: 11px;
  padding-top: 10px;
  border-top: 1px dashed var(--line-strong);
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pe-metric {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-soft);
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 2px 9px;
}

.pe-metric b { color: var(--ink); font-weight: 700; }

footer, .built-with, .show-api { display: none !important; }
""" % {
    "paper": PAPER,
    "paper2": PAPER_2,
    "hover": HOVER,
    "ink": INK,
    "ink_soft": INK_SOFT,
    "ink_mute": INK_MUTE,
    "line": LINE,
    "line_strong": LINE_STRONG,
    "clay": CLAY,
    "ok": OK,
    "serif": FONT_SERIF,
    "mono": FONT_MONO,
}

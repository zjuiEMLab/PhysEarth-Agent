"""Single source of truth for the architecture-comparison slide.

Coordinates are pixels of the reference image (1906 x 1116). index.html and build_pptx.py both
render these elements as native shapes and text, so the slide stays editable in both.
"""
W, H = 1906, 1116
INK, MUTE, ORG, ORG_T = "222B27", "5B625E", "E07B57", "C4532F"
PEACH, BLUE, BLUE_L = "FFEEE2", "E8F0FA", "9DB7D9"

E = []


def box(x, y, w, h, fill, line, lw=2, r=14):
    E.append(dict(k="box", x=x, y=y, w=w, h=h, fill=fill, line=line, lw=lw, r=r))


def text(x, y, w, h, t, size, font="sans", bold=False, color=INK, align="l", anchor="t"):
    E.append(dict(k="text", x=x, y=y, w=w, h=h, t=t, size=size, font=font, bold=bold, color=color,
                  align=align, anchor=anchor))


def circle(x, y, d, fill, line=None):
    E.append(dict(k="circle", x=x, y=y, w=d, h=d, fill=fill, line=line))


# header
text(65, 14, 900, 30, "ARCHITECTURE COMPARISON", 21, "mono", True, ORG_T)
text(65, 48, 1500, 72, "From a plausible answer to a reproducible result.", 58, "serif", True)
text(65, 118, 1500, 34, "The LLM proposes actions; the harness controls what may run, what counts as evidence, "
                        "and what may be claimed.", 24, "sans", False, MUTE)

# left: typical approach
box(55, 190, 593, 755, "EDEAE5", "D6D0C6", 2, 26)
text(89, 220, 500, 28, "TYPICAL APPROACH", 20, "mono", True, MUTE)
text(89, 252, 540, 54, "LLM + RAG + model code", 40, "serif", True)
text(89, 304, 540, 30, "A short answer-generation pipeline", 21, "sans", False, MUTE)
for y, t in [(365, "Research question"), (472, "Retrieve documents (RAG)"), (579, "LLM writes / calls model code"),
             (686, "Narrative answer + plot")]:
    box(99, y, 505, 80, "FFFFFF", "E3DDD3", 2, 14)
    text(99, y, 505, 80, t, 26, "sans", True, INK, "c", "m")
for y in (447, 554):
    box(349, y, 4, 20, "9AA09C", "9AA09C", 0, 1)
text(331, 654, 40, 30, "▼", 22, "sans", False, "9AA09C", "c")
box(99, 800, 505, 111, "FFF1E5", "F0B48F", 2, 14)
text(123, 816, 460, 28, "COMMON FAILURE MODES", 21, "mono", True, ORG_T)
text(123, 850, 470, 60, "Ad-hoc parameters · no approval · weak provenance\n"
                        "Plausible-looking output can outrun its evidence", 20, "sans", False, MUTE)

# divider
box(690, 205, 2, 720, "FFFFFF", "D9D3C9", 0, 1)
circle(658, 529, 66, "FAF7F2", ORG)
text(658, 529, 66, 66, "VS", 21, "mono", True, ORG_T, "c", "m")

# right: PhysEarth
box(735, 190, 1128, 755, "FFFFFF", ORG, 3, 26)
text(774, 220, 500, 28, "PHYSEARTH-AGENT", 21, "mono", True, ORG_T)
text(774, 252, 1060, 54, "LLM inside a scientific research harness", 40, "serif", True)
text(774, 304, 600, 30, "A controlled, reviewable and recoverable experiment pipeline", 21, "sans", False, MUTE)
box(1397, 306, 18, 18, BLUE, BLUE_L, 2, 4)
text(1426, 304, 160, 24, "SHARED CORE", 17, "mono", True, "4C6A91")
box(1590, 306, 18, 18, PEACH, ORG, 2, 4)
text(1620, 304, 220, 24, "HARNESS-ADDED", 17, "mono", True, ORG_T)

box(773, 355, 1052, 76, PEACH, ORG, 2, 14)
text(803, 366, 900, 26, "ADDED · EVIDENCE BOUNDARY", 21, "mono", True, ORG_T)
text(803, 396, 1000, 28, "Bundled papers + section-level citations · online literature · model cards · "
                         "measured datasets", 20, "sans", False, MUTE)

flow = [(774, 173, "Question +\nevidence", "", True), (976, 199, "Research plan", "pseudo-preview\nhuman approval", False),
        (1203, 199, "Registered\nphysical model", "validated inputs", False),
        (1431, 174, "Result +\nFigure QA", "auto-redraw", False),
        (1633, 192, "Cited report", "claims bound to\nruns + sources", False)]
for x, w, t, sub, shared in flow:
    box(x, 474, w, 110, BLUE if shared else PEACH, BLUE_L if shared else ORG, 2, 14)
    if sub:
        text(x, 484, w, 56, t, 24, "sans", True, INK, "c", "m")
        text(x, 538, w, 44, sub, 18, "sans", False, MUTE, "c", "t")
    else:
        text(x, 474, w, 110, t, 25, "sans", True, INK, "c", "m")
for x1, x2 in [(947, 976), (1175, 1203), (1402, 1431)]:
    box(x1, 526, x2 - x1, 5, ORG, ORG, 0, 1)
text(1596, 507, 44, 40, "▶", 30, "sans", False, ORG, "c")

box(773, 634, 1052, 201, PEACH, ORG, 2, 14)
text(803, 652, 980, 26, "WHAT PHYSEARTH ADDS · HARNESS CONTROL PLANE", 21, "mono", True, ORG_T)
chips = [["Workflow + recovery", "Human approval gates", "Physical validation", "Model registry"],
         ["Result store + replay", "Figure quality review", "Citation integrity", "Audit trace + memory"]]
for r, row in enumerate(chips):
    for c, t in enumerate(row):
        x, y = 803 + c * 253, 696 + r * 68
        box(x, y, 234, 53, "FFFFFF", "E3DDD3", 2, 10)
        text(x, y, 234, 53, t, 19, "sans", True, INK, "c", "m")
text(774, 858, 1050, 30, "LLM: proposes and interprets" + "\u00a0" * 6 + "HARNESS: authorizes, validates, records and recovers",
     19, "mono", False, MUTE)

# bottom callouts
box(55, 980, 885, 102, "EAF4EC", "8DBB98", 2, 22)
circle(80, 1007, 48, "4C8A5E")
text(80, 1007, 48, 48, "1", 26, "sans", True, "FFFFFF", "c", "m")
text(148, 992, 780, 40, "Process-driven reproduction", 31, "serif", True, "20402B")
text(148, 1034, 790, 30, "Reviewable plans → repeatable model runs → checked figures → recoverable execution",
     20, "sans", False, MUTE)
box(968, 980, 895, 102, "EFEBF8", "B3A7DA", 2, 22)
circle(993, 1007, 48, "6A55AE")
text(993, 1007, 48, 48, "2", 26, "sans", True, "FFFFFF", "c", "m")
text(1061, 992, 780, 40, "Evidence-constrained trust", 31, "serif", True, "372B66")
text(1061, 1034, 790, 30, "Every conclusion is traceable to literature, model declarations and actual outputs",
     21, "sans", False, MUTE)


def to_html():
    fonts = {"sans": "var(--sans)", "serif": "var(--serif)", "mono": "var(--mono)"}
    out = []
    for e in E:
        pos = f"left:{e['x']}px;top:{e['y']}px;width:{e['w']}px;height:{e['h']}px;"
        if e["k"] in ("box", "circle"):
            rad = "50%" if e["k"] == "circle" else f"{e.get('r', 0)}px"
            ln = f"border:{e.get('lw', 2)}px solid #{e['line']};" if e.get("line") and e.get("lw", 2) else ""
            out.append(f'<div class="a" style="{pos}background:#{e["fill"]};{ln}border-radius:{rad}"></div>')
        else:
            al = {"l": "left", "c": "center", "r": "right"}[e["align"]]
            jc = {"t": "flex-start", "m": "center"}[e["anchor"]]
            ta = {"l": "flex-start", "c": "center", "r": "flex-end"}[e["align"]]
            out.append(
                f'<div class="a at" style="{pos}font-size:{e["size"]}px;font-family:{fonts[e["font"]]};'
                f'font-weight:{700 if e["bold"] else 400};color:#{e["color"]};text-align:{al};'
                f'justify-content:{jc};align-items:{ta};'
                f'{"letter-spacing:.08em;" if e["font"] == "mono" else ""}">{e["t"]}</div>')
    return "\n".join(out)

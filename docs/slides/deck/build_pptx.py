"""Build PhysEarth-Trust-Protocol.pptx from the same content as index.html.

Speaker notes are read from the NOTES object in index.html (via node). Run:
    python3 build_pptx.py
"""
import json
import subprocess
from pathlib import Path

from arch_spec import E as ARCH
from arch_spec import H as AH
from arch_spec import W as AW
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).parent
NODE = (
    "const h=require('fs').readFileSync(process.argv[1],'utf8');"
    "const N=eval('('+h.match(/const NOTES = (\\{[\\s\\S]*?\\n\\});/)[1]+')');"
    "console.log(JSON.stringify(N))"
)
NOTES = json.loads(subprocess.check_output(["node", "-e", NODE, str(HERE / "index.html")]))

IKB = "C4532F"  # accent (burnt orange, matches the architecture slide)
SANS, MONO, SERIF = "Arial", "Courier New", "Georgia"
TH = {
    "light": dict(bg="F8F6F2", fg="222B27", mute="5B625E", line="E3DDD3", fill="FFFFFF", kick=IKB),
    "dark": dict(bg="26211D", fg="F8F6F2", mute="B5ACA2", line="4A423B", fill="332D28", kick="F0A98A"),
    "accent": dict(bg=IKB, fg="FFFFFF", mute="F3D5C8", line="D98B6F", fill="D2694A", kick="FFFFFF"),
}
LM = 0.75
CW = 13.333 - 2 * LM

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
count = [0]


def rgb(h):
    return RGBColor.from_string(h)


def T(s, content, x, y, w, h, size=14, color="0A0A0A", bold=False, italic=False, font=SANS,
      align="l", anchor="t"):
    """Text box. content: str, or list of (text, {opts}) runs; '\n' starts a new paragraph."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    if font == SANS and size >= 36 and not bold:
        font, bold = SERIF, True
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE}[anchor]
    runs = [(content, {})] if isinstance(content, str) else content
    p = tf.paragraphs[0]
    p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
    for text, o in runs:
        parts = text.split("\n")
        for i, part in enumerate(parts):
            if i:
                p = tf.add_paragraph()
                p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            r = p.add_run()
            r.text = part
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic)
            f.color.rgb = rgb(o.get("color", color))
    return tb


def rect(s, x, y, w, h, fill, line=None, r=0.12):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = min(0.5, r / max(0.01, min(w, h)))
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(fill)
    if line:
        sh.line.color.rgb = rgb(line)
        sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def hline(s, x, y, w, color, pt=0.75):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(pt)


def seg(s, x1, y1, x2, y2, color, pt=1.5):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(pt)


ACC_ITALIC = {"222B27": IKB, "FAFAF8": "F0A98A", "F8F6F2": "F0A98A"}


def italic_runs(title, size, color):
    a, _, b = title.partition("|")
    out = [(a, dict(size=size, color=color, font=SERIF, bold=True))]
    if b:
        out.append((b, dict(size=size, color=ACC_ITALIC.get(color, color), italic=True, font=SERIF, bold=True)))
    return out


class S:
    def __init__(self, sid, theme, left, right, chrome=True):
        self.s = prs.slides.add_slide(BLANK)
        self.t = TH[theme]
        self.theme = theme
        count[0] += 1
        bg = self.s.background.fill
        bg.solid()
        bg.fore_color.rgb = rgb(self.t["bg"])
        if chrome:
            T(self.s, left.upper(), LM, 0.38, 6, 0.3, size=10, color=self.t["mute"], font=MONO)
            T(self.s, f"{right}  ·  {count[0]} / 21".upper(), 6.5, 0.38, CW - 5.75, 0.3, size=10,
              color=self.t["mute"], font=MONO, align="r")
        n = NOTES.get(sid)
        if n:
            self.s.notes_slide.notes_text_frame.text = f"Plan: {n['m']} min\n- " + "\n- ".join(n["t"])

    def head(self, kick, title, size=38, y=0.8):
        if kick:
            T(self.s, kick.upper(), LM, y, CW, 0.3, size=12, bold=True, color=self.t["kick"], font=MONO)
        T(self.s, italic_runs(title, size, self.t["fg"]), LM, y + 0.35, CW, 0.9)

    def trust(self, on):
        dark = self.theme == "dark"
        for i, l in enumerate("ABC"):
            x = 13.333 - LM - 1.2 + i * 0.42
            hit = l in on
            fill = ("F0A98A" if dark else IKB) if hit else self.t["bg"]
            rect(self.s, x, 7.0, 0.36, 0.3, fill, fill if hit else self.t["line"])
            T(self.s, l, x, 7.0, 0.36, 0.3, size=10, bold=True, font=MONO, align="c", anchor="m",
              color=("26211D" if dark else "FFFFFF") if hit else self.t["mute"])

    def foot(self, text):
        T(self.s, text, LM, 7.0, 10.6, 0.3, size=10, color=self.t["mute"], font=MONO)

    def card(self, x, y, w, h, kind=""):
        fill = {"acc": IKB, "ink": "26211D"}.get(kind, self.t["fill"])
        rect(self.s, x, y, w, h, fill, None if kind else self.t["line"], 0.16)
        return ("FFFFFF", "C8C8C6") if kind in ("acc", "ink") else (self.t["fg"], self.t["mute"])

    def rows(self, items, x, y, w, rh, size=15, line=None, fg=None):
        line = line or self.t["line"]
        fg = fg or self.t["fg"]
        for i, it in enumerate(items):
            hline(self.s, x, y + i * rh, w, line)
            T(self.s, it, x, y + i * rh + 0.06, w, rh - 0.1, size=size, color=fg, anchor="m")
        hline(self.s, x, y + len(items) * rh, w, line)

    def table(self, x, y, colw, header, body, size=12, rh=0.6):
        xs = [x + sum(colw[:i]) for i in range(len(colw))]
        for i, h in enumerate(header):
            T(self.s, h.upper(), xs[i], y, colw[i] - 0.15, 0.3, size=10, bold=True, color=self.t["mute"],
              font=MONO)
        hline(self.s, x, y + 0.33, sum(colw), self.t["fg"], 1.5)
        for r, row in enumerate(body):
            top = y + 0.33 + r * rh
            for i, c in enumerate(row):
                T(self.s, c, xs[i], top + 0.04, colw[i] - 0.2, rh - 0.08, size=size, bold=(i == 0),
                  color=self.t["fg"], anchor="m")
            hline(self.s, x, top + rh, sum(colw), self.t["line"])


def tag(t):
    return f"[{t.upper()}]"


# 1 COVER
s = S("cover", "accent", "PhysEarth-Agent", "Open Source GeoAI Practice · IEEE AP-GARSS 2026")
T(s.s, "TRUST PROTOCOL FOR PHYSICAL-MODEL AGENTS", LM, 1.9, CW, 0.3, size=13, bold=True, color="FFFFFF", font=MONO)
T(s.s, [("Can you trust a run of a ", dict(size=54)), ("physical model?", dict(size=54, italic=True))],
  LM, 2.35, 10.5, 2.1, color="FFFFFF")
T(s.s, "An agent for physics-based Earth models, and the protocol that scores whether its runs can be trusted. "
       "Demonstrated end to end on SMRT, a snow microwave model.", LM, 4.9, 9.5, 1.2, size=18, color="F3D5C8")
s.foot("Open source · deploys as a ModelScope Studio app · 12 min + 3 min Q&A")

# 2 PROBLEM
s = S("problem", "dark", "01 · The problem", "Why trust is the question")
T(s.s, italic_runs("Physical models fail |silently.", 44, "FAFAF8"), LM, 1.5, 6.9, 1.9)
T(s.s, "Ask for snow denser than ice and the model still returns a smooth, plausible curve. "
       "Nothing crashes, nothing warns.", LM, 3.6, 6.6, 1.4, size=20)
T(s.s, "So the question is not whether an agent can call a model. It is whether its run can be trusted.",
  LM, 5.2, 6.6, 1.2, size=20, color=s.t["mute"])
for i, (k, d) in enumerate([("40%", "accuracy of code agents on UnivEARTH"),
                            (">44%", "of generated code does not even run")]):
    y = 1.6 + i * 2.3
    hline(s.s, 8.3, y, 4.3, "FAFAF8", 1.5)
    T(s.s, k, 8.3, y + 0.15, 4.3, 1.2, size=66, color="FFFFFF")
    T(s.s, d, 8.3, y + 1.4, 4.3, 0.6, size=14, color=s.t["mute"])
s.foot('UnivEARTH · "Towards LLM Agents for Earth Observation", ICML 2025 (arXiv 2504.12110)')

# 3 LANDSCAPE
s = S("landscape", "light", "02 · Goal and contribution", "Three kinds of GeoAI agent")
s.head("Where PhysEarth sits", "Perceive, code, or |operate a model.")
cs = [("PERCEPTION AGENTS", "RS-Agent · ThinkGeo",
       "Call trained networks, e.g. SAR to flood extent. The model is learned from data.",
       "Trust gap: a black box with no declared physics.", ""),
      ("CODE AGENTS", "GeoAgent · EE Genie",
       "Write and run code for each task. Flexible, but brittle and silent when wrong.",
       "Trust gap: library defaults, out-of-range values, overstated accuracy.", ""),
      ("PHYSICAL-MODEL AGENT", "PhysEarth-Agent",
       "Runs registered radiative-transfer, hydrology and land-surface models that encode processes. "
       "Ranges and legal settings are declared, not guessed.", "Trust by construction, then by score.", "acc")]
w = (CW - 0.6) / 3
for i, (a, b, c, d, k) in enumerate(cs):
    x = LM + i * (w + 0.3)
    fg, mute = s.card(x, 2.2, w, 3.5, k)
    T(s.s, a, x + 0.3, 2.45, w - 0.6, 0.3, size=10, color=mute, font=MONO)
    T(s.s, b, x + 0.3, 2.8, w - 0.6, 0.5, size=20, bold=True, color=fg)
    T(s.s, c, x + 0.3, 3.4, w - 0.6, 1.5, size=14, color=fg)
    T(s.s, d, x + 0.3, 4.95, w - 0.6, 0.6, size=12, color=mute)
T(s.s, [("Goal 1 ", dict(bold=True)), ("· reproduce published model experiments", {})], LM, 6.1, 5.8, 0.5, size=16)
T(s.s, [("Goal 2 ", dict(bold=True)), ("· run new experiments you can trust", {})], 6.9, 6.1, 5.8, 0.5, size=16)
s.trust("")

# 5 TRUST MAP
s = S("trust-map", "dark", "03 · The key delivery", "How can we trust the model?")
s.head("One model, three protocols", "Trust is a protocol, |not a claim.")
cs = [("A", "Register & guard", "Is the model what its card says, and does the system enforce it?",
       "Card valid · adapter equals the authors' code · illegal calls refused · human approval",
       tag("Done") + "  20/20 checks, 0 LLM calls"),
      ("B", "Reproduce", "Does the run match the paper, and does it name what it assumed?",
       "Execution · figure judge · numeric error · provenance · report judge · vs baselines",
       tag("Done") + " " + tag("numeric 1 wk")),
      ("C", "Afford", "What does a trusted run cost in time, tokens and effort?",
       "Minutes · tokens · LLM calls · approvals · user experience",
       tag("Done") + " time, tokens  " + tag("UX later"))]
for i, (a, b, c, d, e) in enumerate(cs):
    x = LM + i * (w + 0.3)
    s.card(x, 2.2, w, 3.7)
    T(s.s, a, x + 0.3, 2.3, 1, 1, size=54, color="FFFFFF")
    T(s.s, b, x + 0.3, 3.35, w - 0.6, 0.4, size=18, bold=True, color="FAFAF8")
    T(s.s, c, x + 0.3, 3.8, w - 0.6, 0.9, size=13, color="FAFAF8")
    T(s.s, d, x + 0.3, 4.65, w - 0.6, 0.7, size=11, color=s.t["mute"])
    T(s.s, e, x + 0.3, 5.45, w - 0.6, 0.35, size=10, bold=True, font=MONO, color="FAFAF8")
T(s.s, "We do not ask you to trust the LLM. We ask you to read the gates and recompute the scores.",
  LM, 6.2, CW, 0.5, size=18, color="FAFAF8")
s.trust("ABC")

# 6 PHILOSOPHIES
s = S("philosophies", "light", "04 · Problem-solving philosophies", "Rules behind every step")
s.head("Why the protocol can be believed", "Four rules, |each a trust mechanism.")
cs = [("01 · A", "Declare, don't code",
       "A model's capability lives in its card: ranges, legal pairs, output bounds. Not in code the LLM writes."),
      ("02 · A B", "Plan before compute",
       "A human approves the whole experiment before anything runs. Unstated values are labelled, not hidden."),
      ("03 · A B", "Verify in code",
       "Gates before the run, after it and at the answer, plus an external rubric. No self-scoring."),
      ("04 · B C", "Persist evidence",
       "Sections read, result handles and provenance carry across turns, so claims stay traceable.")]
w4 = (CW - 0.9) / 4
for i, (a, b, c) in enumerate(cs):
    x = LM + i * (w4 + 0.3)
    s.card(x, 2.2, w4, 3.6)
    T(s.s, a, x + 0.25, 2.4, w4 - 0.5, 0.3, size=10, color=s.t["mute"], font=MONO)
    T(s.s, b, x + 0.25, 2.8, w4 - 0.5, 0.7, size=17, bold=True)
    T(s.s, c, x + 0.25, 3.6, w4 - 0.5, 2.0, size=13)
T(s.s, [("EE Genie", dict(bold=True)), (" makes the LLM a better programmer. ", {}), ("PhysEarth", dict(bold=True)),
        (" makes it a checked operator of trusted models.", {})], LM, 6.15, CW, 0.6, size=16)
s.trust("ABC")

# 7 FLOW
s = S("flow", "light", "05 · Logic flow", "Steps 0 to 4")
s.head("What happens to one query", "Register, plan, |check, report, improve.")
st = [("0", "Register", "Model card + adapter; paper by DOI or file, licence-gated.", tag("Done") + " " + tag("progress UI later")),
      ("1", "Read & plan", "Opens sections and the figure's axes and legend; each parameter's source is labelled.",
       tag("Done") + " figures: SMRT paper only"),
      ("2", "Check, approve, run", "Range and pairing validation, human approval, output QC, results as handles.", tag("Done")),
      ("3", "Report & score", "Chart from a spec beside the paper's figure; citation gate; declared outcome; rubric.", tag("Done in part")),
      ("4", "Improve", "Failure, fix the general mechanism, regression test, human approval, re-score.", tag("As practice"))]
w5 = CW / 5
hline(s.s, LM, 2.3, CW, s.t["fg"], 1.5)
for i, (a, b, c, d) in enumerate(st):
    x = LM + i * w5
    T(s.s, a, x, 2.4, w5 - 0.2, 1, size=48)
    T(s.s, b, x, 3.5, w5 - 0.2, 0.4, size=14, bold=True)
    T(s.s, c, x, 3.95, w5 - 0.3, 1.6, size=12)
    T(s.s, d, x, 5.5, w5 - 0.3, 0.6, size=9, bold=True, font=MONO)
T(s.s, "Step 4 is human-gated, so it is not recursive self-improvement. The rule: never write the answer into "
       "the task, the card or the prompt.", LM, 6.3, 11, 0.5, size=13, color=s.t["mute"])
s.trust("AB")

# 8 LOOP
s = S("loop", "dark", "05 · Logic flow", "The agent loop, gates drawn in")
s.head("Gates are code, not prompt", "Four gates the agent |cannot skip.")
ns = [("Read", "paper sections, figures", 0), ("Plan", "runs and charts, capability check", 0),
      ("Validate", "ranges, legal pairs", 1), ("Approve", "a human, never the agent", 1),
      ("Run", "adapter; the LLM gets a handle", 0), ("QC", "declared output bounds", 1),
      ("Plot", "declarative spec over handles", 0), ("Cite", "every marker must resolve", 1)]
for i, (a, b, g) in enumerate(ns):
    x = LM + (i % 4) * (w4 + 0.3)
    y = 2.3 + (i // 4) * 1.7
    rect(s.s, x, y, w4, 1.4, "F8F6F2" if g else s.t["fill"], "F8F6F2" if g else s.t["line"])
    T(s.s, str(i + 1), x + w4 - 0.5, y + 0.12, 0.3, 0.3, size=10, font=MONO, align="r",
      color="6B6B68" if g else s.t["mute"])
    T(s.s, a, x + 0.25, y + 0.3, w4 - 0.5, 0.45, size=20, bold=True, color="222B27" if g else "FAF7F2")
    T(s.s, b, x + 0.25, y + 0.85, w4 - 0.5, 0.45, size=12, color="5B625E" if g else s.t["mute"])
T(s.s, "21 tools. Ablation switches remove a gate from a YAML file, never from a prompt, so the same gate can "
       "be switched off to measure what it buys.", LM, 5.9, 11, 0.6, size=13, color=s.t["mute"])
s.foot("backend/physearth/harness/ · tools/ · research/")
s.trust("A")

# ARCHITECTURE (native shapes from arch_spec.py, so every box and label is editable)
s = S("architecture", "light", "", "", chrome=False)
sx, sy = 13.333 / AW, 7.5 / AH
FONTS = {"sans": SANS, "serif": SERIF, "mono": MONO}
for e in ARCH:
    x, y, w, h = e["x"] * sx, e["y"] * sy, e["w"] * sx, e["h"] * sy
    if e["k"] in ("box", "circle"):
        shp = s.s.shapes.add_shape(MSO_SHAPE.OVAL if e["k"] == "circle" else MSO_SHAPE.ROUNDED_RECTANGLE,
                                   Inches(x), Inches(y), Inches(w), Inches(h))
        if e["k"] == "box":
            shp.adjustments[0] = min(0.5, e.get("r", 0) * sx / max(0.01, min(w, h)))
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(e["fill"])
        if e.get("line") and e.get("lw", 2):
            shp.line.color.rgb = rgb(e["line"])
            shp.line.width = Pt(max(0.75, e.get("lw", 2) * 0.5))
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False
    else:
        T(s.s, e["t"], x, y, w, h, size=max(9.5, round(e["size"] * 0.49 * 2) / 2), color=e["color"],
          bold=e["bold"], font=FONTS[e["font"]], align=e["align"], anchor=e["anchor"])
T(s.s, f"{count[0]} / 21", 12.2, 0.15, 0.9, 0.25, size=10, color=s.t["mute"], font=MONO, align="r")

# 9 PROTOCOL A
s = S("protocol-a", "light", "06 · Protocol A", "SMRT demo · step 1 of 3")
s.head("A · Register & guard", "Register SMRT. |What proves it worked?", 34)
T(s.s, "YOU HAND IN", LM, 2.2, 3, 0.3, size=10, color=s.t["mute"], font=MONO)
for i, (a, b) in enumerate([("model_card.yaml", "parameter ranges, legal pairs, output bounds"),
                            ("adapter.py", "run(spec) around the upstream package")]):
    y = 2.55 + i * 1.05
    s.card(LM, y, 3.2, 0.9)
    T(s.s, a, LM + 0.2, y + 0.12, 2.8, 0.35, size=13, bold=True, font=MONO)
    T(s.s, b, LM + 0.2, y + 0.5, 2.8, 0.35, size=11, color=s.t["mute"])
T(s.s, "Check: python -m physearth.registry.check\nLoad: PHYSEARTH_MODEL_PATH", LM, 4.7, 3.4, 0.6, size=9,
  color=s.t["mute"], font=MONO)
T(s.s, "20/20", LM, 5.4, 3.4, 0.9, size=54, color=IKB)
T(s.s, "checks pass · 0 LLM calls · deterministic", LM, 6.3, 3.4, 0.4, size=11, color=s.t["mute"])
s.table(4.5, 2.2, [1.2, 2.2, 4.9], ["Eval", "Question", "Evidence it shows"], [
    ["A1 Card", "Is the declaration legal?",
     "7/7: six registered cards pass; one deliberately broken card is rejected before registration"],
    ["A2 Adapter", "Does it compute what the authors' code computes?",
     "9 tasks, 38 checks; SMRT matches upstream to nine decimals; closed-form identities hold for tau-omega and water cloud"],
    ["A3 Guards", "Does the system enforce the card?",
     "4/4: a run succeeds, an identical replay hashes the same, an out-of-range call is refused before it runs, a run is blocked until a human approves"],
    ["Probe", "Does the agent respect it?",
     "Density 2000 kg/m3 is declined, citing the card's 917 kg/m3 bound, instead of returning a curve"]], 12, 1.0)
s.foot("Fixtures: models/examples/toy_model · tasks evaluation/tasks/tier0 · " + tag("Done"))
s.trust("A")

# 10 PROTOCOL B
s = S("protocol-b", "light", "07 · Protocol B", "SMRT demo · step 2 of 3")
s.head("B · Reproduce", "Reproduce Figure 3. |What approves it?", 34)
s.table(LM, 2.1, [2.2, 3.0, 4.9, 1.9], ["Score", "Question it answers", "How it is scored", "Status"], [
    ["Execution rate", "Did the run finish?", "Completed vs stopped by a stop rule", tag("Done")],
    ["Figure: visual judge", "Same curves, order, grouping as the paper?",
     "Label-blinded judge, four dimensions scored 0-2; pass needs line count and patterns at 2", tag("Done")],
    ["Figure: numeric error", "How far from the authors' own code?",
     "Normalised RMSE on the notebook grid, as the agent chose and with the notebook's settings", tag("1 wk")],
    ["Provenance", "Which values were assumed?",
     "Each parameter labelled; labels cross-checked against defaults the system recorded",
     tag("labels") + " " + tag("check 1 wk")],
    ["Report judge", "Is the write-up true and calibrated?",
     "Rubric dimensions 0-2; factuality must be 2; outcome declared as reproduced, partial, not identifiable or failed",
     tag("Done")],
    ["Safety", "Illegal calls executed? False premise caught?",
     "Recomputed from the card, whether or not a gate was on", tag("Done")]], 11, 0.64)
T(s.s, "Every metric is recomputed from the recorded run, never from what the harness decided at the time. "
       "ThinkGeo and Earth-Bench score tool choice and final answer; this adds configuration fidelity and "
       "parameter provenance.", LM, 6.35, 10.5, 0.6, size=12, color=s.t["mute"])
s.trust("B")

# 11 COMPARE
s = S("compare", "light", "07 · Protocol B", "Compared with whom?")
s.head("B · Baselines", "Same task, same scorer, |different operator.", 32)
s.table(LM, 2.2, [2.4, 3.6, 4.0, 2.0], ["Comparator", "What changes", "What it tells you", "Status"], [
    ["Direct LLM", "Same Qwen and tools, harness switched off", "What the gates buy on one model", tag("re-run 1 wk")],
    ["Other LLMs", "DeepSeek, GLM, GPT-5.5 with the harness", "Whether the checks depend on a strong model", tag("1 wk")],
    ["Claude Code, Codex", "Raw coding agent on the same question, then with our plugin",
     "Flexibility versus silent failure; what the plugin adds", tag("Later")]], 12, 0.72)
for i, (a, b, c) in enumerate([
        ("EARLIER BUILD · 48-RUN ABLATION", "0% vs 17%", "illegal calls executed, with the harness vs without"),
        ("EARLIER BUILD · 48-RUN ABLATION", "100% vs 67%", "citations that resolve, with vs without"),
        ("FAIRNESS RULE", "", "Compare only identical task, prompt profile and build. Old records stay for audit and are never pooled.")]):
    x = LM + i * (w + 0.3)
    s.card(x, 4.8, w, 1.9)
    T(s.s, a, x + 0.25, 4.95, w - 0.5, 0.3, size=9, color=s.t["mute"], font=MONO)
    if b:
        T(s.s, b, x + 0.25, 5.3, w - 0.5, 0.7, size=32)
        T(s.s, c, x + 0.25, 6.1, w - 0.5, 0.5, size=11)
    else:
        T(s.s, c, x + 0.25, 5.3, w - 0.5, 1.3, size=14)
s.foot("Earlier-build numbers: records no longer in the tree; re-run pending")
s.trust("BC")

# 12 PROTOCOL C
s = S("protocol-c", "light", "08 · Protocol C", "SMRT demo · step 3 of 3")
s.head("C · Afford", "What does a trusted run |cost?")
w3 = (CW - 0.8) / 3
for i, (a, b, c) in enumerate([("4-5", "minutes per run", "Q1, harness on, qwen-plus"),
                               ("0.7M", "tokens per run", "0.65-0.74M, full pipeline"),
                               ("27", "LLM calls per run", "26-28 observed")]):
    x = LM + i * (w3 + 0.4)
    hline(s.s, x, 2.3, w3, s.t["fg"], 1.5)
    T(s.s, a, x, 2.4, w3, 1.3, size=72)
    T(s.s, b, x, 3.8, w3, 0.4, size=18, bold=True)
    T(s.s, c, x, 4.2, w3, 0.4, size=12, color=s.t["mute"])
T(s.s, "MEASURED  " + tag("Done"), LM, 5.0, 5.5, 0.3, size=10, color=s.t["mute"], font=MONO)
s.rows(["Wall-clock time, LLM calls, tokens per run", "Per-turn and per-session budgets",
        "Prompt grows from about 14k to 39k tokens"], LM, 5.35, 5.6, 0.45, 12)
T(s.s, "USER EXPERIENCE  " + tag("Later"), 6.9, 5.0, 5.5, 0.3, size=10, color=s.t["mute"], font=MONO)
s.rows(["Time to first figure, approvals needed, plan edits made", "One human review per LLM and prompt",
        "Baseline cost to be re-measured"], 6.9, 5.35, 5.7, 0.45, 12)
s.trust("C")

# 13 RESULTS FIGURE
s = S("results-figure", "light", "09 · Results", "SMRT Figure 3 · Q1")
s.head("B · The reproduction", "Same six curves, |same grouping.")
s.s.shapes.add_picture(str(HERE / "images/paper_fig3.png"), Inches(LM), Inches(2.2), width=Inches(3.75))
T(s.s, "PAPER · PICARD ET AL. 2018 · CC BY 4.0", LM, 5.1, 3.8, 0.3, size=9, color=s.t["mute"], font=MONO)
s.s.shapes.add_picture(str(HERE / "images/agent_fig3.png"), Inches(4.75), Inches(2.2), width=Inches(4.6))
T(s.s, "AGENT · QWEN-PLUS, RUN 1 · DRAWN FROM A SPEC", 4.75, 4.85, 4.6, 0.3, size=9, color=s.t["mute"], font=MONO)
for i, (a, b) in enumerate([("3/3", "runs produced the figure"), ("8/8", "visual judge, each run"),
                            ("4/6", "curves within 3-4% of the authors' notebook")]):
    y = 2.2 + i * 1.3
    hline(s.s, 9.9, y, 2.7, s.t["fg"], 1.5)
    T(s.s, a, 9.9, y + 0.08, 2.7, 0.7, size=40)
    T(s.s, b, 9.9, y + 0.8, 2.7, 0.45, size=11, color=s.t["mute"])
T(s.s, "Not pixel-identical, and not meant to be: the judge ignores style. The two sticky curves are about 12% "
       "off because the paper never states stickiness.", LM, 6.3, 8.5, 0.6, size=12, color=s.t["mute"])
s.trust("B")

# 14 RESULTS SPLIT
s = S("results-split", "light", "09 · Results", "Success, partial, failed")
s.head("B · What we can and cannot claim", "Success, partial, |and what failed.")
cs = [("SUCCESS", ["Fig. 3 figure in 3/3 runs", "Visual judge 8, 8, 8",
                   "Refuses density above ice and an illegal model pairing"], ""),
      ("PARTIAL", ["Numbers: 4/6 curves within 3-4%; sticky pair about 12% off",
                   "Reports scored 6, 6, 5 of 10, pass mark 8", "Weak factuality in the write-up"], ""),
      ("FAILED, AND LEARNED", ["Direct-LLM baseline stopped after one page: fixed, with a test",
                               "Stickiness was an unlabelled default in 3/3 runs",
                               "Fig. 6 needs MEMLS; PROSAIL inversion unsupported"], "ink")]
for i, (a, items, k) in enumerate(cs):
    x = LM + i * (w + 0.3)
    fg, mute = s.card(x, 2.2, w, 3.7, k)
    T(s.s, a, x + 0.3, 2.4, w - 0.6, 0.3, size=11, bold=True, color=fg, font=MONO)
    s.rows(items, x + 0.3, 2.9, w - 0.6, 0.95, 14, line="555555" if k else s.t["line"], fg=fg)
T(s.s, "Pilot: Q1 only, qwen-plus, judge claude-opus-5, three repeats. Main experiment with the direct LLM, "
       "robustness across LLMs, and Fig. 4a/4b are next week's runs " + tag("1 wk"), LM, 6.2, 11, 0.6, size=12,
  color=s.t["mute"])
s.trust("BC")

# 15 DEMO
s = S("demo", "dark", "10 · Live demo (video)", "One server, three hosts")
rect(s.s, LM, 1.2, 7.6, 4.275, "332D28", s.t["line"])
T(s.s, "INSERT THE DEMO RECORDING HERE\n(Insert > Video, or play deck/media/demo.mp4)", LM, 3.0, 7.6, 0.8, size=12,
  color=s.t["mute"], font=MONO, align="c")
T(s.s, "THREE BEATS, ABOUT 2 MIN", 8.9, 1.2, 4, 0.3, size=12, bold=True, font=MONO, color="FAFAF8")
for i, (a, b) in enumerate([
        ("1 · Studio", "Register toy_model, an out-of-range call is refused with the card's reason, then a cited run."),
        ("2 · Claude Code plugin", "Ask Q1. The approval gate holds, then a figure and a cited answer."),
        ("3 · Codex, DeepSeek Harness", "A 10-second cut of the same tools: one server, three hosts.")]):
    y = 1.7 + i * 1.5
    hline(s.s, 8.9, y, 3.7, "FAFAF8", 1)
    T(s.s, a, 8.9, y + 0.12, 3.7, 0.4, size=16, bold=True, color="FAFAF8")
    T(s.s, b, 8.9, y + 0.55, 3.7, 0.9, size=12, color=s.t["mute"])
s.trust("AB")

# 16 DELIVERABLES
s = S("deliverables", "light", "11 · Deliverables", "What you can take and run")
T(s.s, "DELIVERABLES", LM, 0.9, 5, 0.3, size=12, bold=True, color=IKB, font=MONO)
T(s.s, italic_runs("Five things, |open source.", 34, s.t["fg"]), LM, 1.25, 5.5, 1.2)
s.rows(["The agent and Studio (ModelScope)", "The registration contract",
        "The evaluation protocol: tasks, judge standards", "The test suite", "Host plugins " + tag("1 wk")],
       LM, 2.6, 5.0, 0.72, 14)
T(s.s, "ONE MCP SERVER · THREE HOSTS  " + tag("1 wk") + "  (static; the HTML deck animates it)", 6.4, 1.0, 6.3, 0.3,
  size=9, color=s.t["mute"], font=MONO)
rect(s.s, 6.4, 3.0, 2.3, 1.9, "26211D")
T(s.s, "MCP SERVER", 6.6, 3.15, 2, 0.3, size=9, color="C8C8C6", font=MONO)
T(s.s, "physearth tools", 6.6, 3.5, 1.95, 0.7, size=16, bold=True, color="FFFFFF")
T(s.s, "register · plan · validate · run · verify", 6.6, 4.2, 1.95, 0.6, size=10, color="C8C8C6")
for name, plug, ty in [("Claude Code", "plugin/claude-geoai", 1.5), ("Codex", "plugin/codex-geoai", 3.45),
                       ("DeepSeek Harness", "plugin/dsh-geoai", 5.4)]:
    seg(s.s, 8.7, 3.95, 9.8, ty + 0.5, IKB, 1.5)
    rect(s.s, 9.8, ty, 2.8, 1.0, IKB)
    T(s.s, name, 10.0, ty + 0.12, 2.5, 0.4, size=15, bold=True, color="FFFFFF")
    T(s.s, plug, 10.0, ty + 0.58, 2.5, 0.3, size=9, color="F3D5C8", font=MONO)
s.trust("ABC")

# 17 NEXT + VISION
s = S("next-vision", "light", "12 · Next and vision", "From plugging in models to plugging in theories")
T(s.s, "NEXT", LM, 0.9, 4, 0.3, size=12, bold=True, color=IKB, font=MONO)
s.rows(["Numeric-claim gate: every number tied to a stored result", "Numeric score against the authors' notebook",
        "Provenance cross-check against recorded defaults", "Laptop install",
        "New cases: TVC, FAO-56, pywatershed, PROSAIL inversion",
        "Full land surface models · comparison with coding agents"], LM, 1.4, 5.3, 0.82, 13)
s.card(6.5, 0.9, 6.1, 5.8, "ink")
T(s.s, "VISION", 6.9, 1.2, 4, 0.3, size=10, color="C8C8C6", font=MONO)
T(s.s, italic_runs("Plug in |theories, not only models.", 30, "FFFFFF"), 6.9, 1.6, 5.3, 1.5)
T(s.s, "Today humans register models and the agent configures and runs them. Next the agent may write or revise "
       "physics code, such as a MEMLS adapter or a revised snow-density scheme, but only through the same contract:",
  6.9, 3.2, 5.3, 1.6, size=13, color="E0E0DE")
T(s.s, "card · conservation and reference checks · regression test · human approval", 6.9, 4.7, 5.3, 0.6, size=10,
  color="E0E0DE", font=MONO)
T(s.s, "\"Declare, don't code\" becomes \"code only through the contract.\"", 6.9, 5.5, 5.3, 0.9, size=17,
  color="FFFFFF")
s.trust("ABC")

# 18 CLOSING
s = S("closing", "accent", "13 · Close", "How can we trust the model?")
T(s.s, italic_runs("Trust, |scored.", 54, "FFFFFF"), LM, 2.6, 5.9, 1.6)
for i, (l, txt) in enumerate([("A", "· The model is what its card says.  " + tag("20/20")),
                              ("B", "· The run matches the paper and names its assumptions.  " + tag("figure") + " " + tag("numeric 1 wk")),
                              ("C", "· The cost is known.  " + tag("time, tokens"))]):
    y = 2.3 + i * 0.95
    hline(s.s, 6.9, y, 5.7, s.t["line"])
    T(s.s, [(l + " ", dict(bold=True)), (txt, {})], 6.9, y + 0.08, 5.7, 0.8, size=14, color="FFFFFF", anchor="m")
hline(s.s, 6.9, 2.3 + 3 * 0.95, 5.7, s.t["line"])
T(s.s, "Read the gates. Recompute the scores. Register your own model and test it the same way.", 6.9, 5.4, 5.7, 1.0,
  size=16, color="F3D5C8")
s.trust("ABC")

# 19 Q&A
s = S("qa", "dark", "Q&A · 3 min", "PhysEarth-Agent")
T(s.s, "Questions", LM, 1.8, 8, 1.5, size=66, color="FAFAF8")
s.rows(["Why not Claude Code or Codex?", "What if the paper does not state a parameter?",
        "How do I add my own model or paper?"], LM, 3.6, 9, 0.8, 20)

# 20 BACKUP TASKS
s = S("backup-tasks", "light", "Backup", "Which tasks the agent can run")
s.head("First pass from task text and registered coverage", "Can run, can't run, |to confirm.", 32)
s.table(LM, 2.2, [3.7, 1.9, 6.4], ["Task", "Verdict", "Why"], [
    ["Q1 · SMRT Fig. 3", tag("Can run"), "Run end to end; figure in 3/3 pilot runs"],
    ["Fig. 4a / 4b · SMRT curves", tag("Should run"), "Paper states the configuration; tasks exist; not yet executed"],
    ["Fig. 5 · IBA with sticky spheres", tag("Should run"), "All SMRT pieces registered; not yet executed"],
    ["Fig. 4 comparison models", tag("Cannot"), "DMRT-QMS and DMRT-ML are not registered"],
    ["Fig. 6 · against MEMLS", tag("Cannot"), "Needs MEMLS; SMRT side only"],
    ["PROSAIL hybrid inversion", tag("Cannot"), "PROSAIL is forward-only"],
    ["Trail Valley Creek, model vs measurement", tag("Should run"), "Dataset and SMRT both bundled; not yet scored"],
    ["Q2, Q3, Q4 in the competition spec", tag("Undefined"), "Only Q1 has a task file; Q3 names MEMLS"]], 11, 0.5)
s.foot("Confirm each by running the capability gate (no LLM) over every task file")

# 21 BACKUP RELATED
s = S("backup-related", "light", "Backup", "Related agents")
s.head("", "Related work, |side by side.", 32)
s.table(LM, 1.9, [2.4, 3.0, 3.3, 3.3], ["Agent", "Tools", "Similar to ours", "Lacks"], [
    ["RS-Agent (2406.07089)", "18 specialist RS models", "Solution and knowledge space = method notes and corpus",
     "Pre-run validation, approval, provenance"],
    ["GeoGPT (2307.07930)", "LangChain GIS tool pool", "Predefined tool pool", "Physical models, checks"],
    ["GeoAgent (2410.18792)", "Code interpreter, RAG, MCTS refinement", "RAG, error recovery",
     "Writes code; no physical bounds"],
    ["ThinkGeo (2505.23752)", "Benchmark: 14 tools, 486 tasks", "Step-wise and final-answer scoring",
     "No configuration or provenance scoring"]], 12, 0.85)
s.foot("Also: UnivEARTH 2504.12110 · Earth-Bench 2509.23141 · survey 2601.01891 · Reichstein et al., Nature 2019")

out = HERE / "PhysEarth-Trust-Protocol.pptx"
prs.save(out)
print("wrote", out, count[0], "slides")

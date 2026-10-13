"""One review of a research plan by a second model call, before a person sees it.

The checks that used to refuse a plan counted things. A reviewer reads the plan the way a person
would: does it draw what the paper's figure shows and nothing else, does it answer the question,
are the conditions the paper's, is anything the figure shows missing. It makes one call with
reasoning off, and its answer goes back to the planning agent in the plan's own tool result, so the
agent can revise the plan once before the person reads it, or say why not. The review is one round
per session. If it cannot be made, the plan goes to the person as it is.

Set PHYSEARTH_PLAN_REVIEW=off to skip it, as the tests do.
"""

import json

from physearth import config
from physearth.corpus import digest as paper_digest
from physearth.research import sheet

PROMPT = (
    "You review a research plan for reproducing a published figure, before a person approves it. "
    "Be brief and concrete. Check only these four things.\n"
    "1. FIGURES: the plan draws exactly the figure or panels the paper shows, one chart for each, "
    "with the same quantities on the same axes. A chart, or a run that only feeds one, for a zoom, "
    "a thickness or solver-convergence check, or any other extra view is not part of the "
    "reproduction: report it as extra.\n"
    "2. QUESTION: the plan lets the question be answered from the figure and its runs.\n"
    "3. CONDITIONS: values the paper states (frequency, radius, temperature, ranges, microstructure) "
    "are the ones used. Report a value chosen without a source that the paper does state. When the "
    "text and a figure caption give different values for the same condition, the caption's is the one "
    "the figure was made with: report a plan that uses the text's. A brightness temperature cannot "
    "exceed the snow temperature, so report a temperature below the values the figure plots. A value "
    "from a worked code example in the text is not a figure condition. A value the plan's author "
    "chose is an assumption, never user-specified unless the question states it.\n"
    "4. MISSING: a curve, panel or output the paper's figure shows that the plan lacks.\n"
    "When the paper's figure image is attached, read it: the plan must draw the same curves and "
    "panels, with the same ordering and about the same range on the axes, and a plan that would "
    "plot values far outside the figure's axis range is wrong, whatever its conditions say. Use "
    "the model's own default for a condition the paper does not give, and do not take a test value "
    "from another figure's caption. Do not ask to remove a condition the model needs to run (for "
    "example frequency, thickness or solver settings): ask that its source be labelled honestly.\n"
    'Reply with JSON only: {"verdict": "ok" or "revise", "issues": [{"kind": "extra" or '
    '"question" or "condition" or "missing", "what": "...", "fix": "..."}]}. '
    'Use "ok" with an empty list when there is nothing to fix. At most four issues.'
)

BRIEF_CHARS = 9000


def figure_refs(session):
    """Source figures the plan's targets reproduce, in order, without repeats."""
    plan = (((session or {}).get("research") or {}).get("plan")) or {}
    refs = []
    for target in plan.get("reproduction_targets") or ():
        ref = str((target or {}).get("source_id") or "") if isinstance(target, dict) else ""
        if "#" in ref and ref not in refs:
            refs.append(ref)
    return refs
KINDS = ("extra", "question", "condition", "missing")


def enabled():
    return str(config.get("PHYSEARTH_PLAN_REVIEW") or "on").strip().lower() not in ("off", "0", "no")


def brief(session):
    """The plan, the question and the paper's own statements, compactly."""
    project = (session or {}).get("research") or {}
    plan = project.get("plan") or {}
    lines = ["Question: %s" % (plan.get("question") or project.get("question") or "")]
    for target in plan.get("reproduction_targets") or ():
        if isinstance(target, dict):
            lines.append("Target %s: %s (%s)" % (
                target.get("id"), target.get("target_quantity") or target.get("label") or "",
                target.get("status") or "planned",
            ))
    built = sheet.build(plan)
    for group in built["groups"]:
        lines.append("Runs of %s:" % group["model"])
        lines.append("  same in every run: %s" % "; ".join(
            "%s = %s" % (c["label"], c["shown"]) for c in group["conditions"][:14]
        ))
        for run in group["runs"]:
            varying = ", ".join(
                "%s = %s" % (c["label"], sheet.fmt(run["values"].get(c["name"])))
                for c in group["columns"]
            )
            lines.append("  %s (%s): %s%s" % (
                run["id"], run.get("stage") or "main", varying or run["label"],
                "; " + (run["sweep"] or group["sweep"]) if (run["sweep"] or group["sweep"]) else "",
            ))
    for chart in plan.get("charts") or ():
        if isinstance(chart, dict):
            lines.append("Chart %s%s: %s against %s, runs %s" % (
                chart.get("id"), "" if chart.get("required", True) else " (optional)",
                ", ".join(chart.get("ys") or [chart.get("y") or ""]), chart.get("x"),
                ", ".join(chart.get("runs") or ["all that produce it"]),
            ))
    if plan.get("hypothesis"):
        lines.append("Hypothesis: %s" % plan["hypothesis"])
    # Figure captions and stated conditions first: they hold the values the plan has to match.
    statements = []
    for record in ((session or {}).get("paper_digests") or {}).values():
        for item in record.get("items") or ():
            statements.append((item.get("kind") not in ("figure", "condition"), "[%s] (%s) %s" % (
                item.get("ref"), item.get("kind"), item.get("statement"))))
    statements = [text for _later, text in sorted(statements, key=lambda pair: pair[0])][:45]
    lines.append("What the paper states:")
    lines += ["- " + line for line in statements] or ["- (nothing recorded)"]
    return "\n".join(lines)[:BRIEF_CHARS]


def _json_objects(text):
    """Every brace-balanced JSON object in a reply, in the order they appear.

    The reply is asked for JSON only and a model sometimes answers in prose anyway, with
    the JSON after it, or with braces of its own inside that prose. Matching from the first
    `{` to the last `}` spans all of it and is not JSON, so the review of a plan that had
    been reviewed read back as "could not be made": counting braces finds the object the
    reviewer actually wrote, whatever it wrote around it.
    """
    found = []
    for start, character in enumerate(text):
        if character != "{":
            continue
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        candidate = json.loads(text[start:index + 1])
                    except ValueError:
                        break
                    if isinstance(candidate, dict):
                        found.append(candidate)
                    break
    return found


def unreadable_note(raw, finish_reason=None):
    """Why a reply could not be read, in words the person reading the trace can act on."""
    text = " ".join(str(raw or "").split())
    if finish_reason == "length":
        return "the reviewer's reply was cut off at the token budget: %r" % text[:160]
    return (
        "the reviewer answered in prose instead of the JSON the review is read from: %r"
        % text[:200]
    )


def parse(text):
    """{"verdict", "issues"} from the reviewer's reply, or None when it is not that."""
    for data in _json_objects(str(text or "")):
        verdict = str(data.get("verdict") or "").strip().lower()
        if verdict not in ("ok", "revise"):
            continue
        issues = []
        for item in data.get("issues") or ():
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind") or "").strip().lower()
            issues.append({
                "kind": kind if kind in KINDS else "question",
                "what": str(item.get("what") or "").strip()[:300],
                "fix": str(item.get("fix") or "").strip()[:300],
            })
        issues = [item for item in issues if item["what"]][:4]
        return {"verdict": "revise" if issues and verdict == "revise" else "ok", "issues": issues}
    return None


def feedback(findings):
    """What the planning agent is told, in the plan's tool result."""
    lines = ["- [%s] %s%s" % (item["kind"], item["what"], " -> " + item["fix"] if item["fix"] else "")
             for item in findings["issues"]]
    return (
        "A reviewer read this plan against the paper and the question and asks for these changes:\n%s\n"
        "Apply the ones you agree with in one research_plan(action=revise_plan) that sends only the "
        "affected fields, and remove charts and runs that are not part of what the paper's figure "
        "shows. Label a value you chose yourself model_assumption or paper_inferred, never "
        "user_specified: that is only for a value the person's question gives. If you disagree with "
        "all of them, reply with one sentence and stop." % "\n".join(lines)
    )

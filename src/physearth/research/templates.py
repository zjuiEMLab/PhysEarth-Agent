"""The five report layouts, and which one a study gets.

Written from engineering-school writing guides (MIT 21W.732, Purdue OWL, Georgia Tech ECE,
Swarthmore Engineering, CMU) and kept in step with docs/design/report-templates.html. Every
layout opens with the answer and keeps three sources apart: what the paper states, what the
figures show, and what the runs measured.

The figure-led report is the default. IMRaD is for a full manuscript -- a study that
reproduces several of a paper's figures -- where a single-figure reproduction would only be
stretched to fill its sections.
"""

from physearth import config

DEFAULT = "figure-led"
# A study spanning this many of the paper's figures is a manuscript, not one reproduction.
MANUSCRIPT_FIGURES = 3

TEMPLATES = {
    "figure-led": {
        "title": "Figure-led report",
        "outline": (
            "## Research result and conclusion -- answer the question in two or three "
            "sentences, in its own terms and units, then one outcome word: reproduced, "
            "partial, not identifiable or failed.",
            "## The plan in brief -- one paragraph: model and version, what was held fixed and "
            "where each value came from, what was swept, how many runs.",
            "## Figure N: <title> -- one block per figure: a caption naming what is plotted and "
            "its conditions; what the figure shows (count, order, convergence, divergence, "
            "crossings); what the recorded results measured (statistics a tool computed, "
            "otherwise N/A); and what this figure answers.",
            "## Against the paper -- each relevant statement the paper makes, cited, beside what "
            "the figures and results show: agree, differ, or not comparable.",
            "## Assumed parameters -- every value the paper did not give, the value used and why.",
            "## Limitations -- two to four that would change the answer.",
        ),
    },
    "brief": {
        "title": "Answer-first brief",
        "outline": (
            "## Research result and conclusion -- the answer and outcome in one paragraph.",
            "## Why -- three bullets, each a figure observation backed by a recorded result.",
            "## How it was obtained -- two sentences on the plan.",
            "## Assumed parameters -- one line each.",
            "## Limitations -- what would change the answer.",
        ),
    },
    "imrad": {
        "title": "IMRaD manuscript",
        "outline": (
            "## Abstract -- objective, method, key results and the answer, under 150 words.",
            "## Introduction -- the question, what the paper states, the hypothesis.",
            "## Methods -- the plan: models and versions, conditions with sources, runs, figures.",
            "## Results -- per figure, what it shows and what the runs measured, without "
            "interpretation.",
            "## Discussion -- the answer, comparison with the paper, outcome, limitations.",
            "## Assumed parameters",
            "## Conclusion -- two sentences.",
        ),
    },
    "ledger": {
        "title": "Claim-evidence ledger",
        "outline": (
            "## Research result and conclusion -- the answer and outcome in one sentence.",
            "## Claims -- a table: claim | evidence (figure, recorded result or paper "
            "statement) | marker | supported, partly supported, not supported or not "
            "identifiable.",
            "## Against the paper -- each paper statement: agree, differ or not comparable.",
            "## Assumed parameters -- input, value, provenance, effect if wrong.",
            "## Limitations -- what would change the verdict.",
        ),
    },
    "memo": {
        "title": "Memo with technical appendix",
        "outline": (
            "## Research result and conclusion -- a one-page memo: purpose, answer, outcome, "
            "confidence, any decision the reader must make.",
            "## Appendix A: conditions and sources",
            "## Appendix B: runs",
            "## Appendix C: figures with captions and recorded statistics",
            "## Appendix D: assumed parameters",
        ),
    },
}


def _source_figures(plan):
    return {
        str(target.get("source_id"))
        for target in (plan or {}).get("reproduction_targets") or ()
        if isinstance(target, dict) and target.get("source_id")
        and str(target.get("source_type") or "result") in ("result", "figure")
    }


def choose(project):
    """The layout for a study: an explicit choice, else by its size, else figure-led."""
    project = project or {}
    chosen = str(project.get("report_template") or config.get("PHYSEARTH_REPORT_TEMPLATE") or "").strip().lower()
    if chosen in TEMPLATES:
        return chosen
    if len(_source_figures(project.get("plan"))) >= MANUSCRIPT_FIGURES:
        return "imrad"
    return DEFAULT


def instructions(project):
    """The chosen layout as the lines the report brief hands the agent."""
    name = choose(project)
    template = TEMPLATES[name]
    return "Write the report as a %s, in this order:\n%s" % (
        template["title"], "\n".join("  " + line for line in template["outline"]),
    )

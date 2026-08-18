"""Ablation switches.

An ablation has to be reproducible by anyone who checks this repository out, so it
cannot be a code edit. It also must not be reachable by the model: these values arrive
as an argument from the process that started the run, never from a prompt and never
from a tool call. `app.py` never passes them, so the deployed application always runs
with everything on and its behaviour is byte identical to the unswitched code.

harness      physical domain validation before a model call, and the evidence and
             citation gates on the final answer
literature   the bundled corpus: both literature tools and the catalogue in the prompt
capability   the declared parameter ranges, enums and legal combinations, in the prompt
             and in what list_models returns
figures      the figure layer of the corpus: the tools that open and inspect a source
             figure, and the figure list a section read returns. With it off the paper
             is text only, which is what a reader has without the plates -- a caption
             says what a figure is about, the figure says what is on it.
"""

PAPER_ACCESS = ("structured_figures", "structured_text", "raw_pdf")
EXECUTION_ACCESS = ("harnessed_smrt", "raw_smrt")
BOOLEAN_SWITCHES = ("harness", "literature", "capability", "figures")

ALL_ON = {
    "harness": True,
    "literature": True,
    "capability": True,
    "figures": True,
    "paper_access": "structured_figures",
    "execution_access": "harnessed_smrt",
}


def resolve(switches=None):
    if switches is None:
        return dict(ALL_ON)
    merged = dict(ALL_ON)
    explicit = set(switches)
    for name, value in switches.items():
        if name not in merged:
            raise ValueError(f"unknown switch {name!r}; known switches: {', '.join(ALL_ON)}")
        if name in BOOLEAN_SWITCHES:
            merged[name] = bool(value)
        elif name == "paper_access":
            if value not in PAPER_ACCESS:
                raise ValueError(
                    f"paper_access {value!r} must be one of {', '.join(PAPER_ACCESS)}"
                )
            merged[name] = value
        elif name == "execution_access":
            if value not in EXECUTION_ACCESS:
                raise ValueError(
                    f"execution_access {value!r} must be one of {', '.join(EXECUTION_ACCESS)}"
                )
            merged[name] = value

    # Preserve the old figures ablation as an alias for structured text. Explicit access
    # modes win, so evaluation records describe the information boundary directly.
    if "paper_access" not in explicit and not merged["figures"]:
        merged["paper_access"] = "structured_text"
    if merged["paper_access"] == "structured_text":
        merged["figures"] = False
    elif merged["paper_access"] == "raw_pdf":
        merged.update(literature=False, capability=False, figures=False)
    if merged["execution_access"] == "raw_smrt":
        merged["capability"] = False
    return merged


def label(switches):
    flags = resolve(switches)
    if flags["paper_access"] == "raw_pdf" and flags["execution_access"] == "raw_smrt":
        return "raw-baseline"
    if flags["paper_access"] == "structured_text":
        return "text-only"
    off = sorted(name for name in BOOLEAN_SWITCHES if not flags[name])
    return "full" if not off else "no-" + "+".join(off)

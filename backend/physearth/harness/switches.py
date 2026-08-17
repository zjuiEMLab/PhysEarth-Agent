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

ALL_ON = {"harness": True, "literature": True, "capability": True, "figures": True}


def resolve(switches=None):
    if switches is None:
        return dict(ALL_ON)
    merged = dict(ALL_ON)
    for name, value in switches.items():
        if name not in merged:
            raise ValueError("unknown switch %r; known switches: %s" % (name, ", ".join(ALL_ON)))
        merged[name] = bool(value)
    return merged


def label(switches):
    off = sorted(name for name, on in resolve(switches).items() if not on)
    return "full" if not off else "no-" + "+".join(off)

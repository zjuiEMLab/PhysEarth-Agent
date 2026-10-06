"""Run one turn from the command line, with no interface and no browser.

    python -m physearth.agent "reproduce figure 4 of the SMRT paper"

The same loop the Studio drives, so a run that misbehaves in the interface can be
reproduced here and read as plain text. Approval-gated model runs still stop and wait:
this is not a way around the gate, only a way to see it without a browser.
"""

import argparse
import sys

from physearth.agent.catalogue import default_model, new_session
from physearth.agent.loop import stream


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m physearth.agent")
    parser.add_argument("question")
    parser.add_argument("--model", default=None, help="language model id; default %s" % "from .env")
    parser.add_argument("--trace", action="store_true", help="print each event as it happens")
    args = parser.parse_args(argv)

    session = new_session(args.model or default_model())
    answer, events, state = "", [], None
    seen = 0
    for answer, events, state in stream(args.question, session=session):
        if args.trace:
            for event in events[seen:]:
                print("  [%s] %s" % (event.get("at", ""), event.get("kind", "")), file=sys.stderr)
            seen = len(events)

    print(answer)
    if state:
        print(
            "\n-- %s model calls, %s tool calls, %s model runs"
            % (
                state.get("model_calls", 0),
                state.get("tool_calls", 0),
                state.get("model_runs", 0),
            ),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

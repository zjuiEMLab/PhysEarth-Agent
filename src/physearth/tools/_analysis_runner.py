"""The child side of run_analysis_script. Run as a script, never imported.

Everything that reaches the registered models goes back over a pipe to the parent, which
runs it through the same validation, quality control and result store as any other run. This
process holds the user-approved script and nothing else of the engine.

Protocol, one JSON object per line. The child writes on the real stdout and the parent
answers on stdin; the script's own prints are captured and returned at the end.
"""

import io
import json
import os
import sys
import traceback

MAX_CAPTURE = 8000


def _default(value):
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    raise TypeError("%s is not JSON serialisable" % type(value).__name__)


class _Capture(io.TextIOBase):
    def __init__(self):
        self.parts, self.size = [], 0

    def write(self, text):
        if self.size < MAX_CAPTURE:
            self.parts.append(text[: MAX_CAPTURE - self.size])
            self.size += len(text)
        return len(text)

    def value(self):
        return "".join(self.parts)


def _block_network():
    """Best effort only: stops an accidental connection, not a determined one."""
    import socket

    def refuse(*args, **kwargs):
        raise OSError("network access is not allowed in an analysis script")

    socket.socket.connect = refuse
    socket.socket.connect_ex = refuse
    socket.getaddrinfo = refuse


def main():
    script_path, site = sys.argv[1], sys.argv[2]
    proto, stdin = sys.stdout, sys.stdin
    if site and os.path.isdir(site):
        sys.path.insert(0, site)
    capture = _Capture()

    def send(message):
        proto.write(json.dumps(message, default=_default) + "\n")
        proto.flush()

    def call(message):
        send(message)
        line = stdin.readline()
        if not line:
            raise SystemExit(3)
        return json.loads(line)

    def run_model(model, **parameters):
        """Run a registered model. Returns {"series": {output: [values]}, "axis": ..., "units": ...}.

        A single point has no axis and one value per output, so `reply["outputs"]["tb_v"]` is a
        number. A sweep has `reply["axis"]["values"]` and `reply["series"]["tb_v"]` lists.
        """
        reply = call({"op": "run", "model": model, "parameters": parameters})
        if not reply.get("ok"):
            raise RuntimeError(reply.get("error") or "the model run failed")
        return reply

    def save_series(name, x, series, x_name="x", units=None, note=""):
        """Keep a result: x values and one list per named series. Charts and the report use it."""
        reply = call({
            "op": "save", "name": str(name), "x_name": str(x_name), "x": x,
            "series": series, "units": units or {}, "note": str(note),
        })
        if not reply.get("ok"):
            raise RuntimeError(reply.get("error") or "the result was not saved")
        return reply["handle"]

    _block_network()
    with open(script_path, encoding="utf-8") as handle:
        source = handle.read()
    namespace = {"__name__": "__main__", "run_model": run_model, "save_series": save_series}
    sys.stdout = sys.stderr = capture
    try:
        exec(compile(source, "<analysis script>", "exec"), namespace)
        failure = ""
    except SystemExit:
        failure = ""
    except BaseException:
        failure = traceback.format_exc()[-3000:]
    sys.stdout = proto
    send({"op": "done", "error": failure, "stdout": capture.value()})


if __name__ == "__main__":
    main()

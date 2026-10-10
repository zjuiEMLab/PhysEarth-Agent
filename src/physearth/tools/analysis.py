"""run_analysis_script: the agent writes the analysis around a registered model, a person approves it.

A model run maps inputs to outputs. Solving for an input, fitting, interpolating or integrating
over runs is code, and the language model knows how to write it. What it must not do is compute
the physics itself, run unseen code, or install anything on its own authority. So:

* the script runs in a separate process, and every model run it makes goes back to this process,
  through the same validation, quality control and result store as any other run;
* a person reads the code first. The approval is recorded by the interface against the code's
  hash, and the tool refuses any code whose hash was not approved;
* the script may import whatever it needs. A package that is not installed is named in the
  approval request, and it is installed only if the person approves, into a folder of its own;
* time, model runs, output size and the environment the script sees are bounded.

This is a process boundary with resource limits, not a security boundary. It suits a person
running their own copy and reading the code; a shared deployment needs a container as well.
"""

import ast
import hashlib
import importlib.util
import json
import os
import queue
import re
import resource
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from physearth import config
from physearth.harness import results
from physearth.tools.common import _fail, _ledger, _ok

MAX_CODE_CHARS = 20000
MAX_SECONDS = 300.0
MAX_MODEL_RUNS = 2000
MAX_SAVED_SERIES = 20
MAX_SERIES_POINTS = 5000
MAX_SAVED_RESULTS = 30
MAX_SCRIPTS_PER_CHOICE = 4
INSTALL_SECONDS = 300
_REQUIREMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]*(\[[A-Za-z0-9,._\-]+\])?([<>=!~]=?[A-Za-z0-9.*+!\-]+(,[<>=!~]=?[A-Za-z0-9.*+!\-]+)*)?$")
_RUNNER = Path(__file__).with_name("_analysis_runner.py")
_SECRET = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", re.IGNORECASE)


def over_budget(session):
    """True when this choice of a script has used up its scripts.

    Each script is read by a person, and a model that is allowed to keep refining will. The
    count starts at zero when the person picks the script option.
    """
    session = session or {}
    used = len(session.get("analysis_runs") or ()) - int(session.get("script_budget_from") or 0)
    return used >= MAX_SCRIPTS_PER_CHOICE


def code_hash(code):
    return hashlib.sha256(str(code or "").encode("utf-8")).hexdigest()


def _site_dir(session):
    return config.state_dir() / "analysis" / str((session or {}).get("id") or "shared") / "site"


def imported_modules(code):
    """Top-level module names a script imports, or a syntax problem."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [], "the script has a syntax error: %s (line %s)" % (exc.msg, exc.lineno)
    found = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for name in names:
            top = name.split(".")[0]
            if top not in found:
                found.append(top)
    return found, ""


def _available(module, site=None):
    if module in sys.stdlib_module_names or module in sys.builtin_module_names:
        return True
    try:
        if importlib.util.find_spec(module) is not None:
            return True
    except (ImportError, ValueError):
        pass
    return bool(site and site.is_dir() and ((site / module).exists() or (site / (module + ".py")).exists()))


def inspect_code(code, requirements=None, session=None):
    """What a person is asked to approve: the imports, which are missing, what would be installed."""
    modules, problem = imported_modules(code)
    site = _site_dir(session)
    missing = [name for name in modules if not _available(name, site)]
    requested = [str(item).strip() for item in (requirements or ()) if str(item).strip()]
    bad = [item for item in requested if not _REQUIREMENT.match(item)]
    return {
        "imports": modules,
        "missing": missing,
        "requirements": [item for item in requested if item not in bad],
        "rejected_requirements": bad,
        "problem": problem,
        "lines": len(str(code or "").splitlines()),
        "sha256": code_hash(code),
    }


def _installer(requirements, target):
    uv = shutil.which("uv")
    if uv:
        return [uv, "pip", "install", "--python", sys.executable, "--target", str(target), *requirements]
    return [sys.executable, "-m", "pip", "install", "--target", str(target), *requirements]


def _install(requirements, target):
    """Install approved packages into the session's own folder. Returns (ok, message)."""
    target.mkdir(parents=True, exist_ok=True)
    try:
        done = subprocess.run(
            _installer(requirements, target), capture_output=True, text=True,
            timeout=INSTALL_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, "%s: %s" % (type(exc).__name__, exc)
    return done.returncode == 0, (done.stderr or done.stdout or "")[-1500:]


def _limits():
    resource.setrlimit(resource.RLIMIT_CPU, (int(MAX_SECONDS) + 30, int(MAX_SECONDS) + 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (50_000_000, 50_000_000))


def _environment(workdir):
    env = {key: value for key, value in os.environ.items() if not _SECRET.search(key)}
    env.update({"HOME": str(workdir), "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
    return env


def _jsonable_series(series):
    clean = {}
    for key, values in (series or {}).items():
        clean[str(key)] = list(values)[:MAX_SERIES_POINTS]
    return clean


def _model_reply(handle_result, owner):
    """What the script receives for a run: the stored arrays, not a preview."""
    if handle_result.get("status") != "success":
        data = handle_result.get("data") or {}
        problems = [str(item) for item in data.get("problems") or ()]
        message = handle_result.get("summary") or handle_result.get("error") or "the run was refused"
        return {
            "ok": False,
            # The script sees only this text when it raises, so the reasons go in it.
            "error": message + (" Problems: " + " | ".join(problems) if problems else ""),
            "problems": problems,
        }
    handle = handle_result["data"]["handle"]
    payload = results.get(handle, owner) or {}
    series = _jsonable_series(payload.get("series"))
    axis = payload.get("axis")
    return {
        "ok": True,
        "handle": handle,
        "axis": axis,
        "series": series,
        "outputs": {key: values[0] for key, values in series.items() if axis is None and values},
        "units": payload.get("units") or {},
        "qc_passed": bool((handle_result.get("qc") or {}).get("passed", True)),
        "invalid_points": (payload.get("diagnostics") or {}).get("invalid_points") or [],
    }


def run_analysis_script(code, requirements=None, purpose="", _owner=None, _switches=None, _session=None):
    from physearth.tools import runs

    code = str(code or "")
    if over_budget(_session):
        return {
            "status": "needs_input",
            "summary": (
                "No more scripts: %d have run for this request. Write the report now from the "
                "results you have, say what is still uncertain, and do not ask for another script."
                % MAX_SCRIPTS_PER_CHOICE
            ),
            "data": {"error_code": "script_budget_used"},
            "citations": [], "qc": None, "ui": None,
            "error": "script budget used",
        }
    if not code.strip():
        return _fail("run_analysis_script needs a non-empty Python script in `code`.")
    if len(code) > MAX_CODE_CHARS:
        return _fail("The script is %d characters; the limit is %d. Split it." % (len(code), MAX_CODE_CHARS))
    report = inspect_code(code, requirements, _session)
    if report["problem"]:
        return _fail(report["problem"], {"error_code": "script_syntax"})
    digest = report["sha256"]
    if digest not in ((_session or {}).get("approved_scripts") or ()):
        return {
            "status": "needs_input",
            "summary": (
                "This script has not been approved by a person. Scripts run only after a person "
                "has read the code and approved it in the interface; in a session with no one "
                "to ask, none runs."
            ),
            "data": {"error_code": "script_approval_required", "sha256": digest},
            "citations": [], "qc": None, "ui": None,
            "error": "script approval required",
        }
    if report["rejected_requirements"]:
        return _fail(
            "Not a plain package requirement: %s. Give package names such as 'scipy' or "
            "'scikit-learn>=1.3', never a URL, a path or a pip option." % ", ".join(report["rejected_requirements"]),
            {"error_code": "script_requirement_rejected"},
        )

    site = _site_dir(_session)
    installed = []
    if report["missing"]:
        approved = report["requirements"]
        if not approved:
            return _fail(
                "The script imports %s, which is not installed, and no `requirements` were given. "
                "Pass the package names to install, for example requirements=['scikit-learn'], "
                "and a person will be asked to approve them." % ", ".join(report["missing"]),
                {"error_code": "script_package_missing", "missing": report["missing"]},
            )
        ok, message = _install(approved, site)
        if not ok:
            return _fail("Installing %s failed: %s" % (", ".join(approved), message),
                         {"error_code": "script_install_failed"})
        installed = approved
        still = [name for name in report["missing"] if not _available(name, site)]
        if still:
            return _fail(
                "After installing %s the script's import of %s still does not resolve. The import "
                "name and the package name can differ; correct `requirements`." % (", ".join(approved), ", ".join(still)),
                {"error_code": "script_package_missing", "missing": still},
            )

    workdir = Path(tempfile.mkdtemp(prefix="physearth-analysis-"))
    script = workdir / "script.py"
    script.write_text(code, encoding="utf-8")
    started = time.monotonic()
    process = subprocess.Popen(
        [sys.executable, "-I", str(_RUNNER), str(script), str(site if site.is_dir() else "")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=workdir, env=_environment(workdir), text=True, preexec_fn=_limits,
    )
    lines = queue.Queue()

    def pump():
        for line in process.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()

    model_runs, saved, handles, finish = 0, [], [], {}
    models_used = []
    failure = ""
    try:
        while True:
            if (_session or {}).get("stop_requested"):
                failure = "stopped at your request"
                break
            if time.monotonic() - started > MAX_SECONDS:
                failure = "the script ran past the %d second limit" % MAX_SECONDS
                break
            try:
                line = lines.get(timeout=0.25)
            except queue.Empty:
                continue
            if line is None:
                failure = failure or ("" if finish else "the script ended without finishing")
                break
            try:
                message = json.loads(line)
            except ValueError:
                continue
            op = message.get("op")
            if op == "done":
                finish = message
                break
            if op == "run":
                model_runs += 1
                if model_runs > MAX_MODEL_RUNS:
                    failure = "the script made more than %d model runs" % MAX_MODEL_RUNS
                    break
                outcome = runs.run_model(
                    message.get("model"), message.get("parameters") or {},
                    _owner=_owner, _switches=_switches, _session=_session, _via_script=True,
                )
                reply = _model_reply(outcome, _owner)
                if reply.get("ok"):
                    key = "%s@%s" % (outcome["data"].get("model"), outcome["data"].get("version"))
                    if key not in models_used:
                        models_used.append(key)
            elif op == "save":
                reply = _save(message, digest, saved, handles, _owner)
            else:
                reply = {"ok": False, "error": "unknown request %r" % op}
            try:
                process.stdin.write(json.dumps(reply) + "\n")
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                failure = "the script ended while a request was pending"
                break
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        shutil.rmtree(workdir, ignore_errors=True)

    elapsed = round(time.monotonic() - started, 2)
    error = failure or finish.get("error") or ""
    record = {
        "sha256": digest, "purpose": str(purpose or "")[:300], "code": code,
        "model_runs": model_runs, "saved": [item["name"] for item in saved],
        "installed": installed, "elapsed_s": elapsed, "error": error,
    }
    if _session is not None:
        _session.setdefault("analysis_runs", []).append(record)
        _ledger(_session, "analysis_script", {
            "reference": "script:%s" % digest[:12], "purpose": record["purpose"],
            "model_runs": model_runs, "saved": record["saved"], "error": error,
        })
    data = {
        "sha256": digest, "model_runs": model_runs, "elapsed_s": elapsed,
        "saved_results": saved, "installed": installed, "models_run": models_used,
        "stdout": finish.get("stdout", ""),
    }
    if error:
        data["error_code"] = "script_failed"
        data["traceback"] = error
        return _fail("The script failed after %d model run(s): %s" % (model_runs, error.strip().splitlines()[-1] if error.strip() else error), data)
    summary = "The script made %d model run(s) in %.1fs and saved %d result(s)%s." % (
        model_runs, elapsed, len(saved), (": " + ", ".join("%s (%s)" % (i["name"], i["handle"]) for i in saved)) if saved else "")
    return _ok(summary, data)


def _save(message, digest, saved, handles, owner):
    if len(saved) >= MAX_SAVED_RESULTS:
        return {"ok": False, "error": "at most %d results can be saved per script" % MAX_SAVED_RESULTS}
    series = message.get("series")
    if not isinstance(series, dict) or not series or len(series) > MAX_SAVED_SERIES:
        return {"ok": False, "error": "series must be a dict of 1 to %d named lists" % MAX_SAVED_SERIES}
    x = list(message.get("x") or [])
    lengths = {len(list(values)) for values in series.values()}
    if len(lengths) != 1 or (x and len(x) not in lengths):
        return {"ok": False, "error": "x and every series must have the same length"}
    if max(lengths | {len(x)}) > MAX_SERIES_POINTS:
        return {"ok": False, "error": "at most %d points per series" % MAX_SERIES_POINTS}
    name = str(message.get("name") or "result")[:80]
    try:
        clean = {str(key): [float(v) for v in values] for key, values in series.items()}
        axis = {"name": str(message.get("x_name") or "x"), "values": [float(v) for v in x]} if x else None
    except (TypeError, ValueError):
        return {"ok": False, "error": "x and series values must be numbers"}
    handle = results.put(
        {
            "model": "analysis_script", "version": digest[:12],
            "spec": {"script_sha256": digest, "name": name, "note": str(message.get("note") or "")[:300]},
            "axis": axis, "series": clean, "points": [],
            "units": {str(k): str(v) for k, v in (message.get("units") or {}).items()},
            "diagnostics": {}, "source": "analysis_script",
        },
        owner,
    )
    saved.append({"name": name, "handle": handle, "points": max(lengths)})
    handles.append(handle)
    return {"ok": True, "handle": handle}

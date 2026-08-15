import concurrent.futures
import json
import os
import platform
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from importlib import metadata

from physearth import config

_PACKAGES = ["gradio", "smrt", "numpy", "scipy", "pandas", "xarray", "numba"]
_PROBES = [
    (
        "llm-api",
        config.llm_api_base().rstrip("/") + "/models",
        {"Authorization": "Bearer %s" % config.llm_api_key()},
    ),
    ("openalex", "https://api.openalex.org/works?per-page=1&select=id", {}),
    ("europepmc", "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=test&format=json&pageSize=1", {}),
    ("copernicus", "https://tc.copernicus.org/articles/18/3971/2024/tc-18-3971-2024.xml", {}),
    ("zenodo", "https://zenodo.org/api/records/12750470", {}),
]


def runtime_info():
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "cwd": os.getcwd(),
        "hostname": socket.gethostname(),
    }


def package_versions():
    out = {}
    for name in _PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = "not installed"
    return out


_BOOT_RECORD = None


def boot_record():
    global _BOOT_RECORD
    if _BOOT_RECORD is not None:
        return dict(_BOOT_RECORD, checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))

    path = config.state_dir() / "boot_marker.json"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    previous = None
    count = 0
    if path.is_file():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
            count = int(previous.get("boot_count", 0))
        except (ValueError, OSError):
            previous = None
    record = {
        "boot_count": count + 1,
        "this_boot": now,
        "previous_boot": (previous or {}).get("this_boot"),
        "pid": os.getpid(),
    }
    try:
        path.write_text(json.dumps(record), encoding="utf-8")
        record["writable"] = True
    except OSError as exc:
        record["writable"] = False
        record["error"] = str(exc)
    record["path"] = str(path.resolve())
    _BOOT_RECORD = record
    return dict(record, checked_at=now)


def network_probes(timeout=6.0):
    """Probe all dependencies concurrently so diagnostics cannot stall UI startup.

    Five sequential six-second timeouts made a degraded network hold the whole product
    page for half a minute or longer. Each request keeps its own timeout, while this
    coordinator returns a complete, ordered status table after one timeout window.
    """
    ctx = ssl.create_default_context()

    def probe(item):
        name, url, extra_headers = item
        started = time.perf_counter()
        entry = {"name": name, "url": url}
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "physearth-diagnostics", **extra_headers},
            )
            with urllib.request.urlopen(request, timeout=timeout, context=ctx) as response:
                response.read(256)
                entry["status"] = response.status
                entry["ok"] = True
        except urllib.error.HTTPError as exc:
            entry["status"] = exc.code
            entry["ok"] = exc.code < 500
        except Exception as exc:
            entry["status"] = type(exc).__name__
            entry["ok"] = False
        entry["elapsed_s"] = round(time.perf_counter() - started, 3)
        return entry

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(_PROBES))
    futures = {executor.submit(probe, item): item for item in _PROBES}
    completed = {}
    try:
        for future in concurrent.futures.as_completed(futures, timeout=timeout + 1.0):
            result = future.result()
            completed[result["name"]] = result
    except concurrent.futures.TimeoutError:
        pass
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
    for name, url, _headers in _PROBES:
        completed.setdefault(
            name,
            {"name": name, "url": url, "status": "Timeout", "ok": False, "elapsed_s": timeout},
        )
    return [completed[name] for name, _url, _headers in _PROBES]


def smrt_warmup():
    entry = {"available": False}
    try:
        from physearth.models.bundled.smrt.adapter import _ensure_smrt_importable

        _ensure_smrt_importable()
        from smrt import make_model, make_snowpack, sensor_list
    except Exception as exc:
        entry["error"] = "%s: %s" % (type(exc).__name__, exc)
        return entry
    try:
        snowpack = make_snowpack(
            thickness=[10.0],
            microstructure_model="exponential",
            density=[300.0],
            temperature=[265.0],
            corr_length=[0.15e-3],
        )
        model = make_model("iba", "dort")
        sensor = sensor_list.passive(37e9, 55.0)
        started = time.perf_counter()
        cold = model.run(sensor, snowpack)
        cold_elapsed = time.perf_counter() - started
        started = time.perf_counter()
        model.run(sensor, snowpack)
        warm_elapsed = time.perf_counter() - started
        entry.update(
            available=True,
            tb_v=round(float(cold.TbV()), 3),
            tb_h=round(float(cold.TbH()), 3),
            cold_call_s=round(cold_elapsed, 3),
            warm_call_s=round(warm_elapsed, 4),
        )
    except Exception as exc:
        entry["error"] = "%s: %s" % (type(exc).__name__, exc)
    return entry


def model_registry_report():
    """Which models registered, and why each rejection was rejected."""
    from physearth import registry

    return {
        "registered": [
            {"name": row["name"], "version": row["version"], "runnable": row["runnable"]}
            for row in registry.summary()
        ],
        "rejected": registry.rejected(),
    }


_REPORT = None


def report():
    """The startup self-check, collected once per process.

    It costs five network probes with a six second timeout each, so anything that renders
    it on a request path must not be the thing that collects it. The application collects
    it at import, before the first visitor arrives, and every later reader gets this.
    """
    global _REPORT
    if _REPORT is None:
        _REPORT = collect()
    return _REPORT


def collect():
    from physearth.ingest import http

    return {
        "runtime": runtime_info(),
        "packages": package_versions(),
        "boot": boot_record(),
        "network": network_probes(),
        "smrt": smrt_warmup(),
        "models": model_registry_report(),
        "online": http.online(),
        "token_present": config.has_token(),
    }


def _table(rows):
    return "\n".join("| %s | %s |" % (k, v) for k, v in rows)


def render(report):
    runtime = report["runtime"]
    boot = report["boot"]
    smrt = report["smrt"]
    lines = []

    lines.append("## Runtime")
    lines.append("| key | value |")
    lines.append("| --- | --- |")
    lines.append(_table(runtime.items()))

    lines.append("\n## Packages")
    lines.append("| package | version |")
    lines.append("| --- | --- |")
    lines.append(_table(report["packages"].items()))

    lines.append("\n## Filesystem persistence")
    lines.append("| key | value |")
    lines.append("| --- | --- |")
    lines.append(_table(boot.items()))
    if boot.get("boot_count", 0) > 1:
        lines.append(
            "\nThis process is boot number %s written to this state directory, so the directory "
            "survived at least one process restart. The counter increments once per process; "
            "refreshing this page does not change it." % boot["boot_count"]
        )
    else:
        lines.append(
            "\nFirst recorded boot for this state directory. Refreshing this page will not "
            "change the counter; only a new process will."
        )

    lines.append("\n## Network")
    lines.append("| target | status | elapsed s |")
    lines.append("| --- | --- | --- |")
    for probe in report["network"]:
        lines.append("| %s | %s | %s |" % (probe["name"], probe["status"], probe["elapsed_s"]))

    lines.append("\n## SMRT warm-up")
    lines.append("| key | value |")
    lines.append("| --- | --- |")
    lines.append(_table(smrt.items()))

    lines.append("\n## Model registry")
    models = report.get("models") or {}
    for row in models.get("registered") or []:
        lines.append("| %s | v%s | runnable %s |" % (row["name"], row["version"], row["runnable"]))
    for row in models.get("rejected") or []:
        lines.append("| REJECTED | %s | %s |" % (row["directory"], row["reason"]))
    if not models.get("rejected"):
        lines.append("No model was rejected.")

    lines.append("\n## Credentials")
    lines.append("Token present: %s" % report["token_present"])
    lines.append("Online literature layer: %s" % report.get("online"))
    return "\n".join(lines)

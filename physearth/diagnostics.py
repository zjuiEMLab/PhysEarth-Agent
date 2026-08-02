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
    ("api-inference", config.get("MODELSCOPE_API_BASE") + "/models"),
    ("zenodo", "https://zenodo.org/api/records/12750470"),
    ("modelscope-www", "https://www.modelscope.cn/api/v1/competitions/263/detail"),
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


def boot_record():
    path = config.state_dir() / "boot_marker.json"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    previous = None
    count = 0
    if path.is_file():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
            count = int(previous.get("count", 0))
        except (ValueError, OSError):
            previous = None
    record = {"count": count + 1, "last_boot": now, "previous_boot": (previous or {}).get("last_boot")}
    try:
        path.write_text(json.dumps(record), encoding="utf-8")
        record["writable"] = True
    except OSError as exc:
        record["writable"] = False
        record["error"] = str(exc)
    record["path"] = str(path.resolve())
    return record


def network_probes(timeout=6.0):
    ctx = ssl.create_default_context()
    results = []
    for name, url in _PROBES:
        started = time.perf_counter()
        entry = {"name": name, "url": url}
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "physearth-diagnostics"})
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
        results.append(entry)
    return results


def smrt_warmup():
    entry = {"available": False}
    try:
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


def collect():
    return {
        "runtime": runtime_info(),
        "packages": package_versions(),
        "boot": boot_record(),
        "network": network_probes(),
        "smrt": smrt_warmup(),
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
    if boot.get("count", 0) > 1:
        lines.append("\nState survived at least one restart.")
    else:
        lines.append("\nFirst recorded boot for this state directory.")

    lines.append("\n## Network")
    lines.append("| target | status | elapsed s |")
    lines.append("| --- | --- | --- |")
    for probe in report["network"]:
        lines.append("| %s | %s | %s |" % (probe["name"], probe["status"], probe["elapsed_s"]))

    lines.append("\n## SMRT warm-up")
    lines.append("| key | value |")
    lines.append("| --- | --- |")
    lines.append(_table(smrt.items()))

    lines.append("\n## Credentials")
    lines.append("Token present: %s" % report["token_present"])
    return "\n".join(lines)

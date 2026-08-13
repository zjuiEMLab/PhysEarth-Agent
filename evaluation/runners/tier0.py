"""Tier 0: does the bundled model still compute what it computed before?

This runner never touches a language model, so it costs nothing to re-run and is the
regression net under everything else. Three kinds of check, declared per task:

  upstream          call the upstream package directly with its own documented recipe
                    and require the adapter to agree
  identities        re-derive a closed-form relation and require the model to satisfy it
  monotonic         require a declared sweep to move in the declared direction

Run it with:  python evaluation/runners/tier0.py
"""

import json
import math
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

from physearth import validation  # noqa: E402
from physearth.models import registry  # noqa: E402

sys.path.insert(0, str(common.ROOT))
from metrics import identities  # noqa: E402

SCHEMA_VERSION = "tier0-adapter-record-v2"
CHECK_FIELDS = (
    "upstream",
    "published",
    "contrast",
    "identities",
    "monotonic",
    "axis_length",
    "monotonic_sweep",
)


def run_model(name, parameters):
    entry = registry.get(name)
    if entry is None:
        raise LookupError("model %r is not registered" % name)
    spec, problems = validation.resolve(entry.card, parameters)
    if problems:
        raise ValueError("the reference configuration is itself illegal: %s" % "; ".join(problems))
    return spec, entry.run(spec)


def upstream_smrt(recipe):
    """Drive the upstream SMRT package directly, the way its own documentation does."""
    from smrt import make_model, make_snowpack, sensor_list

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        snowpack = make_snowpack(**recipe["snowpack"])
        model = make_model(recipe["electromagnetic_model"], "dort")
        sensor = (
            sensor_list.active(recipe["sensor"]["frequency_hz"], recipe["sensor"]["angle_deg"])
            if recipe["sensor"]["mode"] == "active"
            else sensor_list.passive(
                recipe["sensor"]["frequency_hz"], recipe["sensor"]["angle_deg"]
            )
        )
        result = model.run(sensor, snowpack)
    return {name: float(getattr(result, method)()) for name, method in recipe["outputs"].items()}


def check_published(expected, series, label):
    """Compare against a value a paper printed, with the tolerance the task declares."""
    checks = []
    for name, spec in expected.items():
        got = (series.get(name) or [None])[0]
        delta = abs(got - spec["value"]) if got is not None else float("inf")
        checks.append(
            {
                "check": label,
                "output": name,
                "passed": delta <= spec["tolerance"],
                "expected": spec["value"],
                "got": None if got is None else round(got, 6),
                "abs_error": None if got is None else round(delta, 6),
                "tolerance": spec["tolerance"],
                "detail": "%s printed in the paper, %s" % (name, spec.get("unit", "")),
            }
        )
    return checks


def check_upstream(task, series):
    recipe = task["upstream"]
    if recipe["kind"] != "smrt_direct":
        return [{"check": "upstream", "passed": False, "detail": "unknown kind %r" % recipe["kind"]}]
    reference = upstream_smrt(recipe)
    tolerance = float(recipe.get("tolerance", 1.0e-9))
    checks = []
    for name, expected in reference.items():
        got = (series.get(name) or [None])[0]
        delta = abs(got - expected) if got is not None else float("inf")
        checks.append(
            {
                "check": "upstream",
                "output": name,
                "passed": delta <= tolerance,
                "expected": round(expected, 9),
                "got": None if got is None else round(got, 9),
                "abs_error": None if got is None else delta,
                "tolerance": tolerance,
                "detail": "upstream SMRT %s" % name,
            }
        )
    return checks


def check_identities(task, spec, series):
    def rerun(overrides):
        _, result = run_model(task["model"], overrides)
        return result["series"]

    checks = []
    for name in task.get("identities") or []:
        function = identities.REGISTRY.get(name)
        if function is None:
            checks.append({"check": "identity", "name": name, "passed": False, "detail": "unknown"})
            continue
        passed, detail = function(spec, series, rerun)
        checks.append({"check": "identity", "name": name, "passed": passed, "detail": detail})
    return checks


def _direction(values):
    if all(b < a for a, b in zip(values, values[1:], strict=False)):
        return "decreasing"
    if all(b > a for a, b in zip(values, values[1:], strict=False)):
        return "increasing"
    return "not monotonic"


def check_monotonic(task, series, expected, parameter=None):
    checks = []
    for name, wanted in (expected or {}).items():
        values = series.get(name) or []
        got = _direction(values) if len(values) > 1 else "too few points"
        checks.append(
            {
                "check": "monotonic",
                "parameter": parameter,
                "output": name,
                "passed": got == wanted,
                "expected": wanted,
                "got": got,
                "detail": "%d points, %s to %s"
                % (len(values), round(values[0], 4), round(values[-1], 4))
                if values
                else "no values",
            }
        )
    return checks


def _check_id(item):
    kind = item["check"]
    if kind == "identity":
        return "identity:%s" % item["name"]
    if kind == "monotonic":
        return "monotonic:%s:%s:%s" % (
            item.get("parameter"), item["output"], item["expected"]
        )
    if kind == "axis_length":
        return "axis_length:%s:%s" % (item.get("parameter"), item["expected"])
    if kind == "published, contrast":
        return "published_contrast:%s" % item["output"]
    if kind == "published":
        return "published:%s" % item["output"]
    if kind == "upstream":
        return "upstream:%s:%s" % (item.get("oracle_kind", "smrt_direct"), item["output"])
    return kind


def _check_configuration(task):
    return {field: task[field] for field in CHECK_FIELDS if field in task}


def _results_equal(first, second):
    if isinstance(first, dict) and isinstance(second, dict):
        return first.keys() == second.keys() and all(
            _results_equal(first[key], second[key]) for key in first
        )
    if isinstance(first, list) and isinstance(second, list):
        return len(first) == len(second) and all(
            _results_equal(left, right) for left, right in zip(first, second, strict=True)
        )
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        # Compiled scientific kernels can differ by a few ULPs across BLAS/runtime
        # builds.  A 1e-8 absolute/relative tolerance remains far tighter than the
        # model's declared scientific tolerances while keeping replay portable.
        return math.isclose(first, second, rel_tol=1.0e-8, abs_tol=1.0e-8)
    return first == second


def replay_record(record):
    """Re-run the frozen resolved spec and compare its complete arrays with the record."""
    entry = registry.get(record["model"])
    if entry is None:
        return False, "model is no longer registered"
    if entry.card["version"] != record["model_version"]:
        return False, "registered version changed from %s to %s" % (
            record["model_version"], entry.card["version"]
        )
    spec, problems = validation.resolve(entry.card, record["resolved_spec"])
    if problems:
        return False, "; ".join(problems)
    try:
        result = entry.run(spec)
    except Exception as exc:
        return False, "%s: %s" % (type(exc).__name__, exc)
    replayed = {"axis": result.get("axis"), "outputs": result.get("series") or {}}
    wanted = {"axis": record.get("axis"), "outputs": record.get("outputs") or {}}
    return _results_equal(replayed, wanted), (
        "resolved spec reproduces the complete output arrays"
        if _results_equal(replayed, wanted)
        else "replayed arrays differ from the recorded arrays"
    )
def run_task(task):
    if task.get("tier") != 0 or task.get("suite") != "tier0":
        raise ValueError("Tier 0 task %s must declare tier: 0 and suite: tier0" % task.get("id"))
    if not task.get("kind") or not task.get("checks"):
        raise ValueError("Tier 0 task %s must declare kind and checks" % task.get("id"))
    spec, result = run_model(task["model"], task["parameters"])
    series = result["series"]
    checks = []

    if task.get("published"):
        checks.extend(check_published(task["published"], series, "published"))
    if task.get("contrast"):
        block = task["contrast"]
        _, other = run_model(task["model"], dict(task["parameters"], **block["override"]))
        checks.extend(
            check_published(block["published"], other["series"], "published, contrast")
        )
    if task.get("upstream"):
        upstream_checks = check_upstream(task, series)
        for item in upstream_checks:
            item["oracle_kind"] = task["upstream"]["kind"]
        checks.extend(upstream_checks)
    if task.get("identities"):
        checks.extend(check_identities(task, spec, series))
    if task.get("monotonic"):
        checks.extend(
            check_monotonic(
                task,
                series,
                task["monotonic"],
                (spec.get("sweep_parameter") or "none"),
            )
        )
    if task.get("axis_length"):
        axis = (result.get("axis") or {}).get("values") or []
        checks.append(
            {
                "check": "axis_length",
                "parameter": spec.get("sweep_parameter"),
                "passed": len(axis) == task["axis_length"],
                "expected": task["axis_length"],
                "got": len(axis),
                "detail": "sweep axis",
            }
        )
    sweep = task.get("monotonic_sweep")
    if sweep:
        parameters = dict(task["parameters"])
        parameters.update(
            sweep_parameter=sweep["parameter"],
            sweep_start=sweep["start"],
            sweep_stop=sweep["stop"],
            sweep_points=sweep["points"],
        )
        _, swept = run_model(task["model"], parameters)
        checks.extend(check_monotonic(task, swept["series"], sweep["expect"], sweep["parameter"]))

    quality = validation.quality_control(registry.get(task["model"]).card, result)
    checks.append(
        {
            "check": "quality_control",
            "passed": quality["passed"],
            "detail": "%d declared-output checks" % len(quality["checks"]),
        }
    )
    actual_check_ids = [_check_id(item) for item in checks]
    if actual_check_ids != task["checks"]:
        raise ValueError(
            "declared checks do not match executable checks: declared=%s actual=%s"
            % (task["checks"], actual_check_ids)
        )
    entry = registry.get(task["model"])
    record = {
        "tier": 0,
        "suite": "tier0",
        "task_id": task["id"],
        "id": task["id"],
        "model": task["model"],
        "model_version": entry.card["version"],
        "title": task["title"],
        "path": task["_path"],
        "kind": list(task["kind"]),
        "resolved_spec": spec,
        "spec": spec,
        "axis": result.get("axis"),
        "outputs": series,
        "values": {name: values[0] for name, values in series.items()},
        "check_configuration": _check_configuration(task),
        "declared_checks": list(task["checks"]),
        "checks": checks,
        "llm_usage": {"calls": 0, "tokens": None, "cost_usd": None},
    }
    replayable, replay_detail = replay_record(record)
    record["replayable"] = replayable
    record["replay_detail"] = replay_detail
    record["replay_key"] = "%s@%s:%s" % (
        record["model"],
        record["model_version"],
        __import__("hashlib").sha256(
            json.dumps(
                {
                    "spec": spec,
                    "checks": record["check_configuration"],
                },
                sort_keys=True,
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest(),
    )
    record["passed"] = all(c["passed"] for c in checks) and replayable
    return record


def main():
    tasks = common.load_tasks("tier0")
    records = []
    for task in tasks:
        try:
            record = run_task(task)
        except Exception as exc:
            record = {
                "tier": 0,
                "suite": "tier0",
                "task_id": task["id"],
                "id": task["id"],
                "model": task.get("model"),
                "title": task.get("title"),
                "path": task["_path"],
                "checks": [
                    {"check": "ran", "passed": False, "detail": "%s: %s" % (type(exc).__name__, exc)}
                ],
                "replayable": False,
                "llm_usage": {"calls": 0, "tokens": None, "cost_usd": None},
                "passed": False,
            }
        records.append(record)
        total = len(record["checks"])
        failed = sum(1 for c in record["checks"] if not c["passed"])
        print(
            "%-6s %-26s %2d checks, %d failed"
            % ("PASS" if record["passed"] else "FAIL", record["id"], total, failed)
        )
        for check in record["checks"]:
            if not check["passed"]:
                print("       %s" % check)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "tier": 0,
        "suite": "tier0",
        "execution": "deterministic",
        "n_tasks": len(records),
        "n_checks": sum(len(r["checks"]) for r in records),
        "n_passed": sum(1 for r in records if r["passed"]),
        "n_replayable": sum(1 for r in records if r.get("replayable")),
        "llm_usage": {"calls": 0, "tokens": None, "cost_usd": None},
        "records": records,
    }
    path = common.write_json("tier0.json", payload)
    print("\n%d/%d tasks pass, %d checks total -> %s" % (
        payload["n_passed"], payload["n_tasks"], payload["n_checks"], path.name))
    return 0 if payload["n_passed"] == payload["n_tasks"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Check a physics task against what the model actually does, not against what was said.

A physics task (evaluation/tasks/physics/) states expectations a competent answer meets: the
question can be expressed, the configuration has the right sign of response, coupled
quantities are held consistent, the swept range resolves where things change, and the answer
says what matters. Two modes:

    python evaluation/runners/physics_check.py --card
        The card and adapter alone, no language model. Can the question be expressed, and does
        a literal run of it at the task's conditions behave physically? Seconds to run.

    python evaluation/runners/physics_check.py --record evaluation/results/runs/<key>.json
        An agent run recorded by agent_tasks.py. Every successful model call is re-executed
        from its recorded spec, so what is scored is the physics of the configuration the
        agent chose, not the numbers it reported.

Each check is pass, fail or skip; a skip is not a pass. Nothing here knows SMRT beyond the
names in the task file and three spelling patterns for wetness and substrate parameters,
which is what lets the same task score the card before and after it is forged.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

from physearth import registry  # noqa: E402
from physearth.harness import validation  # noqa: E402

TASK = common.TASKS / "physics" / "smrt-wetness-depth.yaml"
WETNESS = re.compile(r"liquid|wetness|lwc", re.IGNORECASE)
SUBSTRATE = re.compile(r"substrate|ground|soil", re.IGNORECASE)
NO_GROUND = (None, "", "none", "vacuum", "transparent")
RUN_TOOLS = ("run_model", "run_models", "run_planned_model", "run_planned_models")


def _check(check_id, status, detail, **evidence):
    return {"id": check_id, "status": status, "detail": detail, **evidence}


def _param(card, pattern):
    return next((name for name in card["parameters"] if pattern.search(name)), None)


def _wetness(spec, name):
    return float(spec.get(name) or 0.0) if name else 0.0


def _execute(entry, arguments):
    """Validate as the harness would and run. Returns (axis values, series, problems)."""
    spec, problems = validation.resolve(entry.card, arguments)
    if problems:
        return None, None, problems
    result = entry.run(spec) or {}
    axis = (result.get("axis") or {}).get("values") or []
    return [float(v) for v in axis], result.get("series") or {}, []


def _trend_problem(axis, values, sign, tolerance):
    pairs = sorted(zip(axis, values, strict=True))
    worst = 0.0
    for (_, left), (_, right) in zip(pairs, pairs[1:], strict=False):
        step = right - left if sign == "nonincreasing" else left - right
        worst = max(worst, step)
    return worst > tolerance, worst


def _distinct(curves, threshold):
    """How many curves differ from every other by more than threshold somewhere."""
    kept = []
    for curve in curves:
        if all(
            max(abs(a - b) for a, b in zip(curve, other, strict=False)) > threshold
            for other in kept
        ):
            kept.append(curve)
    return len(kept)


def check_card(task):
    physics = task["physics"]
    entry = registry.get(task["models"][0])
    card = entry.card
    conditions = dict(physics["conditions"])
    sweep = physics["depth_sweep"]
    checks = []

    wet_name = _param(card, WETNESS)
    checks.append(
        _check(
            "wetness_expressible",
            "pass" if wet_name else "fail",
            "the card exposes %s" % wet_name
            if wet_name
            else "no parameter of %s names liquid water, so the question cannot be asked of it"
            % card["name"],
        )
    )

    ground_name = _param(card, SUBSTRATE)
    ground_default = (
        (card["parameters"].get(ground_name) or {}).get("default") if ground_name else None
    )
    has_ground = ground_name and ground_default not in NO_GROUND
    checks.append(
        _check(
            "ground_substrate_default",
            "pass" if has_ground else "fail",
            "%s defaults to %r" % (ground_name, ground_default)
            if ground_name
            else "the card declares no substrate: snow is simulated over vacuum",
        )
    )

    dry = dict(
        conditions,
        sweep_parameter="thickness_m",
        sweep_start=sweep["start"],
        sweep_stop=sweep["stop"],
        sweep_points=sweep["points"],
    )
    axis, series, problems = _execute(entry, dry)
    trend = physics["dry_depth_trend"]
    if problems:
        checks.append(
            _check(
                "dry_depth_trend", "fail", "the literal run was refused: %s" % "; ".join(problems)
            )
        )
    else:
        values = series.get(trend["output"]) or []
        wrong, worst = _trend_problem(axis, values, trend["sign"], trend["tolerance_k"])
        checks.append(
            _check(
                "dry_depth_trend",
                "fail" if wrong else "pass",
                "%s from %.1f K to %.1f K over %.2f to %.2f m; expected %s (worst step %+.1f K)"
                % (trend["output"], values[0], values[-1], axis[0], axis[-1], trend["sign"], worst),
                depths=axis,
                values=[round(v, 2) for v in values],
            )
        )

    if not wet_name:
        checks.append(_check("wet_below_melting_refused", "skip", "no wetness parameter to test"))
        checks.append(_check("wet_depth_saturates", "skip", "no wetness parameter to test"))
    else:
        saturation = physics["wet_saturation"]
        cold_wet = dict(conditions, **{wet_name: saturation["volumetric_liquid_water"]})
        _, problems = validation.resolve(card, cold_wet)
        checks.append(
            _check(
                "wet_below_melting_refused",
                "pass" if problems else "fail",
                "refused: %s" % problems[0]
                if problems
                else "wet snow at %s K was accepted; liquid water exists only at the melting point"
                % conditions["temperature_k"],
            )
        )
        wet = dict(
            dry,
            temperature_k=physics["wet_temperature_k"],
            **{wet_name: saturation["volumetric_liquid_water"]},
        )
        axis, series, problems = _execute(entry, wet)
        if problems:
            checks.append(
                _check("wet_depth_saturates", "fail", "refused: %s" % "; ".join(problems))
            )
        else:
            values = series.get(trend["output"]) or []
            spread = max(values) - min(values)
            checks.append(
                _check(
                    "wet_depth_saturates",
                    "pass" if spread <= saturation["max_spread_k"] else "fail",
                    "%s spread %.2f K over depth at %s = %s"
                    % (trend["output"], spread, wet_name, saturation["volumetric_liquid_water"]),
                    values=[round(v, 2) for v in values],
                )
            )
    return checks


def _recorded_specs(record, model):
    specs = []
    for call in record.get("tool_log") or ():
        if call.get("name") not in RUN_TOOLS or call.get("status") != "success":
            continue
        if (call.get("model") or model) != model and not call.get("specs"):
            continue
        for spec in [call.get("spec")] + list(call.get("specs") or ()):
            if isinstance(spec, dict):
                specs.append(spec)
    return specs


def check_record(task, record):
    physics = task["physics"]
    entry = registry.get(task["models"][0])
    card = entry.card
    trend = physics["dry_depth_trend"]
    wet_name = _param(card, WETNESS)
    ground_name = _param(card, SUBSTRATE)
    specs = _recorded_specs(record, card["name"])
    checks = []
    if not specs:
        checks.append(
            _check("model_ran", "fail", "the run made no successful %s call" % card["name"])
        )

    wetness_values = sorted({_wetness(spec, wet_name) for spec in specs})
    checks.append(
        _check(
            "wetness_varied",
            "pass" if len(wetness_values) >= 2 else "fail",
            "liquid water values run: %s"
            % (wetness_values if wet_name else "none; the card has no wetness parameter"),
        )
    )

    # The worst outcome is not a refusal but a substitute: another parameter relabelled as
    # wetness, so the answer reads as if the question had been answered.
    answer = str(record.get("answer") or "").lower()
    claims_wetness = re.search(r"\bwet(ter|ness)?\b", answer) is not None
    proxy = claims_wetness and len(wetness_values) < 2
    checks.append(
        _check(
            "no_wetness_proxy",
            "fail" if proxy else "pass",
            "the answer speaks of wetness but no run varied liquid water"
            if proxy
            else "wetness is either run or not claimed",
        )
    )

    grounded = (
        [spec.get(ground_name) not in NO_GROUND for spec in specs] if ground_name else [False]
    )
    checks.append(
        _check(
            "ground_substrate",
            "pass" if specs and all(grounded) else "fail",
            "%d of %d run(s) put the snow on ground" % (sum(grounded), len(specs))
            if ground_name
            else "every run was snow over vacuum: the card declares no substrate",
        )
    )

    melting = physics["wet_temperature_k"]
    cold = [
        spec
        for spec in specs
        if _wetness(spec, wet_name) > 0 and float(spec.get("temperature_k") or 0) < melting - 0.2
    ]
    wet_runs = [spec for spec in specs if _wetness(spec, wet_name) > 0]
    checks.append(
        _check(
            "wet_at_melting_point",
            "skip" if not wet_runs else ("fail" if cold else "pass"),
            "no wet run"
            if not wet_runs
            else "%d of %d wet run(s) below %s K" % (len(cold), len(wet_runs), melting),
        )
    )

    depth_runs = [spec for spec in specs if spec.get("sweep_parameter") == "thickness_m"]
    curves, wrong = {}, []
    for spec in depth_runs:
        axis, series, problems = _execute(entry, spec)
        if problems:
            continue
        values = series.get(trend["output"]) or []
        curves[json.dumps(spec, sort_keys=True)] = values
        if _wetness(spec, wet_name) == 0:
            bad, worst = _trend_problem(axis, values, trend["sign"], trend["tolerance_k"])
            if bad:
                wrong.append("%.1f K to %.1f K" % (values[0], values[-1]))
    dry_runs = [spec for spec in depth_runs if _wetness(spec, wet_name) == 0]
    checks.append(
        _check(
            "dry_depth_trend",
            "skip" if not dry_runs else ("fail" if wrong else "pass"),
            "no dry depth sweep was run"
            if not dry_runs
            else (
                "%d dry depth sweep(s) rise with depth: %s" % (len(wrong), ", ".join(wrong))
                if wrong
                else "every dry depth sweep is %s" % trend["sign"]
            ),
        )
    )

    count = _distinct([v for v in curves.values() if v], physics["distinct_curve_k"])
    checks.append(
        _check(
            "wet_curves_resolved",
            "pass" if count >= physics["min_distinct_curves"] else "fail",
            "%d depth curve(s), %d distinguishable by more than %s K"
            % (len(curves), count, physics["distinct_curve_k"]),
        )
    )

    for key, words in physics["answer_mentions"].items():
        hit = next((word for word in words if word in answer), None)
        checks.append(
            _check(
                "answer_mentions_%s" % key,
                "pass" if hit else "fail",
                "mentions %r" % hit if hit else "the answer names none of: %s" % ", ".join(words),
            )
        )
    return checks


def _print(title, checks):
    print(title)
    for item in checks:
        print("  %-28s %-5s %s" % (item["id"], item["status"], item["detail"]))
    passed = sum(item["status"] == "pass" for item in checks)
    print("  %d/%d passed" % (passed, len(checks)))
    return passed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--task", default=str(TASK))
    parser.add_argument("--card", action="store_true", help="check the card and adapter alone")
    parser.add_argument("--record", nargs="*", default=[], help="agent run records to score")
    parser.add_argument(
        "--write", default="", help="also write the result under evaluation/results/"
    )
    args = parser.parse_args(argv)
    task = common.load_yaml(args.task)
    entry = registry.get(task["models"][0])
    report = {
        "task": task["id"],
        "model": entry.name,
        "version": entry.card["version"],
        "card": None,
        "records": [],
    }
    if args.card or not args.record:
        report["card"] = check_card(task)
        _print("card %s@%s" % (entry.name, entry.card["version"]), report["card"])
    for path in args.record:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        checks = check_record(task, record)
        report["records"].append(
            {
                "path": str(path),
                "llm": record.get("llm"),
                "config": record.get("config"),
                "checks": checks,
            }
        )
        _print("record %s" % Path(path).name, checks)
    if args.write:
        print("wrote %s" % common.write_json(args.write, report))
    return 0


if __name__ == "__main__":
    sys.exit(main())

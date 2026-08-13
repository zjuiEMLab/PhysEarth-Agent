"""Tier 0-A: exhaustively check every registered model declaration.

This runner is deterministic, performs no network or language-model calls, and mutates no
model registration.  Every numeric range, enum and declared combination is exercised rather
than sampling the first field of each kind.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

from physearth import validation  # noqa: E402
from physearth.models import contract, registry  # noqa: E402

SCHEMA_VERSION = "tier0-registry-contract-v2"


def check(name, passed, detail, **extra):
    return {"check": name, "passed": bool(passed), "detail": detail, **extra}


def _outside(spec, below):
    low, high = spec["minimum"], spec["maximum"]
    step = max(abs(low), abs(high), 1)
    value = low - step if below else high + step
    return int(value) if spec["type"] == "integer" else float(value)


def _valid_candidates(spec):
    if spec.get("enum"):
        return list(spec["enum"])
    if spec["type"] == "boolean":
        return [False, True]
    if spec["type"] in contract.NUMERIC_TYPES:
        values = [spec.get("default"), spec["minimum"], spec["maximum"]]
        return [value for value in values if value is not None]
    return [spec.get("default")] if spec.get("default") is not None else []


def _metadata_check(model):
    card = model.card
    directory = Path(card.get("_dir") or "")
    module_name, separator, attribute = str(card.get("entrypoint") or "").partition(":")
    entrypoint_file = directory / (module_name + ".py")
    complete = bool(
        card.get("name")
        and card.get("version")
        and card.get("tier")
        and separator
        and attribute
        and entrypoint_file.is_file()
    )
    return check(
        "registration_metadata",
        complete,
        "name, version, tier and entrypoint resolve" if complete else "registration metadata incomplete",
        model=card.get("name"),
        version=card.get("version"),
        tier=card.get("tier"),
        entrypoint=card.get("entrypoint"),
    )


def _range_checks(card):
    checks = []
    for field, spec in card["parameters"].items():
        if spec["type"] not in contract.NUMERIC_TYPES:
            continue
        for side, below in (("minimum", True), ("maximum", False)):
            value = _outside(spec, below)
            _, problems = validation.resolve(card, {field: value})
            rejected = any(field in problem and "outside the physical range" in problem for problem in problems)
            checks.append(
                check(
                    "range_guard",
                    rejected,
                    "%s rejects a value beyond its %s" % (field, side),
                    field=field,
                    boundary=side,
                    tested_value=value,
                )
            )
    return checks


def _enum_checks(card):
    checks = []
    for field, spec in card["parameters"].items():
        if not spec.get("enum"):
            continue
        invalid = "__invalid_evaluation_value__"
        _, problems = validation.resolve(card, {field: invalid})
        rejected = any(field in problem and "must be one of" in problem for problem in problems)
        checks.append(
            check(
                "enum_guard",
                rejected,
                "%s rejects an undeclared value" % field,
                field=field,
                tested_value=invalid,
            )
        )
    return checks


def _combination_checks(card):
    checks = []
    for index, rule in enumerate(card.get("combinations") or []):
        arguments = {field: values[0] for field, values in rule["when"].items()}
        tested_field = None
        for field, allowed in rule["allow"].items():
            invalid = next(
                (value for value in _valid_candidates(card["parameters"][field]) if value not in allowed),
                None,
            )
            if invalid is not None:
                arguments[field] = invalid
                tested_field = field
                break
        _, problems = validation.resolve(card, arguments)
        rejected = bool(
            tested_field
            and any(tested_field in problem and "not allowed" in problem for problem in problems)
        )
        checks.append(
            check(
                "combination_guard",
                rejected,
                "combination rule %d rejects a constructed invalid pairing" % (index + 1),
                rule_index=index,
                field=tested_field,
                tested_arguments=arguments,
                reason=rule.get("reason"),
            )
        )
    return checks


def _sweep_checks(card):
    sweep = card["parameters"].get("sweep_parameter")
    if not sweep or not sweep.get("enum"):
        return []
    targets = [name for name in sweep["enum"] if name != "none"]
    target = next(
        (
            name
            for name in targets
            if name in card["parameters"]
            and card["parameters"][name]["type"] in contract.NUMERIC_TYPES
        ),
        None,
    )
    if target is None:
        return [check("sweep_contract", False, "no numeric sweep target is declared")]
    target_spec = card["parameters"][target]
    start, stop = target_spec["minimum"], target_spec["maximum"]
    if start == stop:
        return [check("sweep_contract", False, "%s has no non-zero range" % target, field=target)]

    _, missing = validation.resolve(card, {"sweep_parameter": target})
    _, equal = validation.resolve(
        card,
        {"sweep_parameter": target, "sweep_start": start, "sweep_stop": start},
    )
    _, outside = validation.resolve(
        card,
        {
            "sweep_parameter": target,
            "sweep_start": _outside(target_spec, True),
            "sweep_stop": stop,
        },
    )
    _, valid = validation.resolve(
        card,
        {
            "sweep_parameter": target,
            "sweep_start": start,
            "sweep_stop": stop,
            "sweep_points": 2,
        },
    )
    return [
        check(
            "sweep_requires_bounds",
            any("required when sweep_parameter" in problem for problem in missing),
            "%s sweep requires start and stop" % target,
            field=target,
        ),
        check(
            "sweep_rejects_equal_bounds",
            any("not a sweep" in problem for problem in equal),
            "%s sweep rejects equal bounds" % target,
            field=target,
        ),
        check(
            "sweep_respects_target_range",
            any("outside the physical range" in problem for problem in outside),
            "%s sweep rejects a bound outside the target domain" % target,
            field=target,
        ),
        check(
            "sweep_accepts_valid_range",
            not valid,
            "%s accepts a valid two-point sweep" % target,
            field=target,
        ),
    ]


def inspect_model(model):
    card = model.card
    declaration_problems = contract.validate_card(card)
    resolved, default_problems = validation.resolve(card, {})
    checks = [
        _metadata_check(model),
        check(
            "model_card_schema",
            not declaration_problems,
            "valid" if not declaration_problems else "; ".join(declaration_problems),
        ),
        check(
            "default_configuration",
            not default_problems,
            "all required values resolve" if not default_problems else "; ".join(default_problems),
            resolved_fields=sorted(resolved),
        ),
        *_range_checks(card),
        *_enum_checks(card),
        *_combination_checks(card),
        *_sweep_checks(card),
    ]
    return {
        "tier": 0,
        "model": model.name,
        "name": model.name,
        "model_version": card["version"],
        "version": card["version"],
        "source": model.source,
        "registration_tier": model.tier,
        "runnable": model.runnable,
        "coverage": {
            "numeric_parameters": sum(
                spec["type"] in contract.NUMERIC_TYPES for spec in card["parameters"].values()
            ),
            "enum_parameters": sum(bool(spec.get("enum")) for spec in card["parameters"].values()),
            "combination_rules": len(card.get("combinations") or []),
            "sweep_contract": "sweep_parameter" in card["parameters"],
        },
        "checks": checks,
        "passed": all(item["passed"] for item in checks),
        "llm_usage": {"calls": 0, "tokens": None, "cost_usd": None},
    }


def main():
    registry.reload()
    rejected = registry.rejected()
    records = [inspect_model(model) for model in registry.all_models().values()]
    for record in records:
        failed = sum(not item["passed"] for item in record["checks"])
        print(
            "%-5s %-20s %3d contract checks, %d failed"
            % ("PASS" if record["passed"] else "FAIL", record["model"], len(record["checks"]), failed)
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tier": 0,
        "suite": "registry_contract",
        "execution": "deterministic",
        "n_models": len(records),
        "n_checks": sum(len(record["checks"]) for record in records),
        "n_passed": sum(record["passed"] for record in records),
        "n_checks_passed": sum(
            item["passed"] for record in records for item in record["checks"]
        ),
        "rejected_registrations": rejected,
        "llm_usage": {"calls": 0, "tokens": None, "cost_usd": None},
        "records": records,
    }
    path = common.write_json("registry_contract.json", payload)
    print(
        "%d/%d registered models pass; %d rejected registration(s); %d checks -> %s"
        % (payload["n_passed"], payload["n_models"], len(rejected), payload["n_checks"], path)
    )
    return 0 if payload["n_passed"] == payload["n_models"] and not rejected else 1


if __name__ == "__main__":
    raise SystemExit(main())

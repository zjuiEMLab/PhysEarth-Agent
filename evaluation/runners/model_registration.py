"""Evaluate competition dimension A: physical-model registration integrity.

This runner is deterministic and does not call an LLM.  It checks the declarations that
drive registration, reuses the Tier-0 adapter oracles, and records successful, refused,
approval-blocked and replayed calls through the same tool layer used by the agent.

Run with::

    python evaluation/runners/model_registration.py
"""

import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
import tier0  # noqa: E402
from physearth import (
    registry,  # noqa: E402
    tools,  # noqa: E402
)
from physearth.harness import results  # noqa: E402
from physearth.registry import contract  # noqa: E402

FIXTURE = common.ROOT / "fixtures" / "invalid_model_card.yaml"
OWNER = "evaluation:model-registration"


def _check(check_id, passed, detail, **evidence):
    return {"id": check_id, "passed": bool(passed), "detail": detail, **evidence}


def _stable_payload(payload):
    return {
        key: payload.get(key)
        for key in ("model", "version", "spec", "axis", "series", "points", "units")
    }


def _digest(payload):
    encoded = json.dumps(_stable_payload(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def card_schema_evidence():
    cards = []
    checks = []
    for name, model in registry.all_models().items():
        problems = contract.validate_card(model.card)
        cards.append(
            {
                "name": name,
                "version": model.card["version"],
                "source": model.source,
                "runnable": model.runnable,
                "parameters": len(model.card["parameters"]),
                "outputs": len(model.card["outputs"]),
                "combination_rules": len(model.card.get("combinations") or []),
                "problems": problems,
            }
        )
        checks.append(
            _check(
                "registered-card:%s" % name,
                not problems,
                "%d parameters, %d outputs, %d legal-combination rules"
                % (
                    len(model.card["parameters"]),
                    len(model.card["outputs"]),
                    len(model.card.get("combinations") or []),
                ),
            )
        )

    bad_card = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    bad_problems = contract.validate_card(bad_card)
    checks.append(
        _check(
            "intentionally-bad-card-rejected",
            len(bad_problems) >= 3,
            "%d declaration errors detected before registration" % len(bad_problems),
            problems=bad_problems,
        )
    )
    return {"cards": cards, "invalid_fixture": str(FIXTURE.relative_to(common.REPO)), "checks": checks}


def adapter_truth_evidence():
    records = [tier0.run_task(task) for task in common.load_tasks("tier0")]
    checks = [
        _check(
            "tier0:%s" % record["id"],
            record["passed"],
            "%d deterministic checks" % len(record["checks"]),
            model=record["model"],
            checks=record["checks"],
        )
        for record in records
    ]
    return {
        "tasks": len(records),
        "checks": sum(len(record["checks"]) for record in records),
        "records": records,
        "checks_summary": checks,
    }


def trace_replay_evidence():
    parameters = {
        "frequency_ghz": 1.41,
        "angle_deg": 40.0,
        "soil_moisture": 0.25,
        "bulk_density_g_cm3": 1.3,
        "soil_temperature_k": 293.0,
        "canopy_temperature_k": 293.0,
        "vegetation_optical_depth": 0.3,
        "single_scattering_albedo": 0.05,
        "roughness_h": 0.3,
        "cross_q": 0.0,
    }
    first = tools.run_model("tau_omega", parameters, _owner=OWNER)
    replay = tools.run_model("tau_omega", parameters, _owner=OWNER)
    first_payload = results.get((first.get("data") or {}).get("handle"), OWNER) or {}
    replay_payload = results.get((replay.get("data") or {}).get("handle"), OWNER) or {}
    first_hash = _digest(first_payload) if first_payload else None
    replay_hash = _digest(replay_payload) if replay_payload else None

    refused_parameters = dict(parameters, soil_moisture=1.5)
    refused = tools.run_model("tau_omega", refused_parameters, _owner=OWNER)
    review_session = {
        "research_required": True,
        "research": {"phase": "plan_review"},
    }
    approval_blocked = tools.run_model(
        "tau_omega", parameters, _owner=OWNER, _session=review_session
    )
    checks = [
        _check(
            "successful-call-recorded",
            first.get("status") == "success" and bool(first_payload),
            "registered adapter returned a stored, QC-checked result",
        ),
        _check(
            "deterministic-replay",
            bool(first_hash) and first_hash == replay_hash,
            "stable output SHA-256 %s" % (first_hash or "missing"),
        ),
        _check(
            "illegal-call-refused-before-run",
            refused.get("status") == "needs_input" and not (refused.get("data") or {}).get("handle"),
            (refused.get("error") or refused.get("summary") or "")[:500],
        ),
        _check(
            "human-approval-gate",
            approval_blocked.get("status") == "needs_input"
            and (approval_blocked.get("data") or {}).get("phase") == "plan_review",
            approval_blocked.get("summary") or "",
        ),
    ]
    return {
        "successful": {
            "model": "tau_omega",
            "version": first_payload.get("version"),
            "spec": first_payload.get("spec"),
            "handle": (first.get("data") or {}).get("handle"),
            "qc": first.get("qc"),
            "output_sha256": first_hash,
        },
        "replay": {
            "handle": (replay.get("data") or {}).get("handle"),
            "output_sha256": replay_hash,
            "matches": first_hash == replay_hash,
        },
        "refused": {
            "model": "tau_omega",
            "parameters": refused_parameters,
            "status": refused.get("status"),
            "problems": (refused.get("data") or {}).get("problems") or [],
            "handle": (refused.get("data") or {}).get("handle"),
        },
        "approval_gate": {
            "phase": "plan_review",
            "status": approval_blocked.get("status"),
            "summary": approval_blocked.get("summary"),
        },
        "checks": checks,
    }


def evaluate():
    sections = {
        "A1_model_card_schema": card_schema_evidence(),
        "A2_adapter_truth": adapter_truth_evidence(),
        "A3_trace_replay": trace_replay_evidence(),
    }
    section_checks = {
        "A1_model_card_schema": sections["A1_model_card_schema"]["checks"],
        "A2_adapter_truth": sections["A2_adapter_truth"]["checks_summary"],
        "A3_trace_replay": sections["A3_trace_replay"]["checks"],
    }
    summary = {}
    for name, checks in section_checks.items():
        summary[name] = {
            "passed": sum(1 for check in checks if check["passed"]),
            "total": len(checks),
            "status": "passed" if all(check["passed"] for check in checks) else "failed",
        }
    all_checks = [check for checks in section_checks.values() for check in checks]
    return {
        "suite": "A_model_registration",
        "status": "passed" if all(check["passed"] for check in all_checks) else "failed",
        "summary": summary,
        "n_checks": len(all_checks),
        "n_passed": sum(1 for check in all_checks if check["passed"]),
        **sections,
    }


def main():
    payload = evaluate()
    path = common.write_json("model_registration.json", payload)
    for name, item in payload["summary"].items():
        print("%-24s %s %d/%d" % (name, item["status"].upper(), item["passed"], item["total"]))
    print("%d/%d checks pass -> %s" % (payload["n_passed"], payload["n_checks"], path.name))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())


"""Run one small deterministic example for every registered model.

This is deliberately separate from the contract checker: a model can have a
valid card and adapter while its optional runtime dependency is unavailable on
the current host.  The result is meant for the human-facing dashboard.
"""

import json
from pathlib import Path

from physearth import registry, tools

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "registration_demo.json"


def _value_text(name, summary, units):
    item = summary.get(name, {})
    if not isinstance(item, dict):
        return str(item)
    first = item.get("first")
    last = item.get("last")
    unit = units.get(name) or item.get("unit") or ""
    if first == last:
        value = f"{first:g}" if isinstance(first, float) else str(first)
    else:
        value = "%s → %s" % (first, last)
    return "%s %s" % (value, unit) if unit else value


def _record(row):
    name = row["name"]
    result = tools.call("run_model", {"model": name})
    data = result.get("data") or {}
    summary = data.get("series_summary") or {}
    units = data.get("units") or {}
    passed = result.get("status") == "success"
    output_names = list(summary) or list(row.get("outputs") or [])
    return {
        "model": name,
        "version": data.get("version") or row.get("version"),
        "description": row.get("description", ""),
        "parameters": data.get("spec") or {},
        "output_names": output_names,
        "output_summary": {
            output: _value_text(output, summary, units) for output in output_names
        },
        "status": "passed" if passed else "attention",
        "passed": passed,
        "summary": result.get("summary", ""),
        "error": result.get("error") if not passed else None,
    }


def main():
    rows = registry.summary()
    records = [_record(row) for row in rows]
    payload = {
        "schema_version": "registration-demo-v1",
        "execution": "deterministic",
        "parameters": "registered defaults",
        "n_models": len(records),
        "n_passed": sum(record["passed"] for record in records),
        "records": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "registration demos: %d / %d passed -> %s"
        % (payload["n_passed"], payload["n_models"], OUT)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Rebuild the dimension-D coverage/comparability report from raw run records."""

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

from evaluation.metrics import robustness, score  # noqa: E402


def evaluate():
    design = yaml.safe_load((common.ROOT / "llm_robustness.yaml").read_text(encoding="utf-8"))
    tasks = {
        task["id"]: task
        for suite in ("tier1", "probe")
        for task in common.load_tasks(suite)
    }
    records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((common.RESULTS / "runs").glob("*.json"))
    ]
    scored = [score.score_record(record, tasks[record["task"]]) for record in records]
    return robustness.analyse(records, scored, design)


def main():
    payload = evaluate()
    path = common.write_json("llm_robustness.json", payload)
    coverage = payload["coverage"]
    print("status: %s" % payload["status"])
    print("coverage: %d/%d planned cells" % (coverage["recorded"], coverage["expected"]))
    print("comparable groups: %d" % payload["comparable_groups"])
    print("-> %s" % path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


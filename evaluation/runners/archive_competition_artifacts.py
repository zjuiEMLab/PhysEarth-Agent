"""Backfill scenario-labelled figures and editable reports for stored runs."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import competition  # noqa: E402


def main():
    changed = 0
    for path in sorted(competition.RUNS.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if record.get("task") != "q1-sparse-medium":
            continue
        before = json.dumps(record, sort_keys=True, ensure_ascii=False)
        competition.archive_record_artifacts(record)
        after = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if before == after:
            continue
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        changed += 1
    print(f"archived artifacts for {changed} stored run(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

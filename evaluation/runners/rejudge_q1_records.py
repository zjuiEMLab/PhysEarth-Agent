"""Apply the current visual figure judge to stored Q1 records.

Existing report-judge results are retained by default. Pass ``--rerun-reports`` when the
report judge must also receive the newly stored visual-figure judgement.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

sys.path.insert(0, str(common.ROOT))
from metrics import figure3, judge  # noqa: E402

RUNS = common.RESULTS / "competition" / "runs"
SCORED_RUNS = common.RESULTS / "competition" / "scored_runs.json"


def _read_json(path):
    # Some archived model responses contain literal control characters.  They are
    # still bounded evidence and should not prevent an offline dashboard rebuild.
    return json.loads(path.read_text(encoding="utf-8"), strict=False)


def _usage(*judgements):
    result = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        values = [
            (item.get("usage") or {}).get(name)
            for item in judgements
            if item.get("complete")
        ]
        result[name] = (
            sum(values)
            if values and all(isinstance(value, int) for value in values)
            else None
        )
    return result


def _status(judgement):
    return judgement.get("status") if judgement.get("complete") else "not_scoreable"


def _apply_figure_pass_rule(judgement):
    if not judgement.get("complete") or not isinstance(judgement.get("scores"), dict):
        return judgement
    visual_standard = (judge.standard_figure().get("figure") or {}).get("visual_judge") or {}
    pass_rule = visual_standard.get("pass") or {}
    scores = judgement["scores"]
    passed = bool(
        sum(scores.values()) >= int(pass_rule.get("minimum_total", 6))
        and all(
            scores[name] >= int(minimum)
            for name, minimum in (pass_rule.get("required_scores") or {}).items()
        )
    )
    judgement["passed"] = passed
    judgement["status"] = "pass" if passed else "fail"
    return judgement


def _diagnostic_path(record):
    figure = next(
        (item for item in record.get("figures") or [] if item.get("archived_image_path")),
        {},
    )
    image_path = Path(str(figure.get("archived_image_path") or ""))
    if image_path.name:
        return image_path.with_name(f"{image_path.stem}_shape-diagnostic.png")
    suffix = "full" if record.get("config") == "full" else "baseline"
    name = (
        f"{record.get('task', 'q1')}_{record.get('prompt_profile', 'p1')}_"
        f"{record.get('llm', 'candidate')}_r{record.get('repeat', '?')}_{suffix}"
    )
    return common.RESULTS / "competition" / "figures" / f"{name}_shape-diagnostic.png"


def rejudge(
    path,
    oracle,
    rerun_reports=False,
    rerun_figure=True,
    write_aspect_diagnostic=False,
):
    record = _read_json(path)
    if record.get("task") != "q1-sparse-medium":
        return False
    metrics = record.get("dashboard_metrics") or {}
    figure_score = figure3.score(record, oracle=oracle)
    figure_judgement = (
        judge.judge_figure(
            record,
            candidate_models=(record.get("llm"),),
        )
        if rerun_figure
        else _apply_figure_pass_rule(metrics.get("figure_judgement") or {})
    )
    deterministic = figure3.deterministic_report_checks(
        record, figure_score, figure_judgement
    )
    report_judgement = metrics.get("report_judgement") or {
        "complete": False,
        "passed": False,
        "status": "not_run",
    }
    if rerun_reports:
        task = {"question": record.get("question")}
        report_judgement = judge.judge_report(
            record,
            task,
            figure_score,
            deterministic,
            candidate_models=(record.get("llm"),),
            figure_judgement=figure_judgement,
        )
    figure_status = _status(figure_judgement)
    successful = bool(metrics.get("successful"))
    report_correct = bool(report_judgement.get("passed"))
    metrics.update(
        {
            "evaluation_complete": bool(
                figure_judgement.get("complete") and report_judgement.get("complete")
            ),
            "figure_result_correct": figure_status,
            "report_correct": (
                "not_scoreable"
                if not report_judgement.get("complete")
                else "pass" if report_correct else "fail"
            ),
            "overall_correct": (
                "not_scoreable"
                if figure_status == "not_scoreable" or not report_judgement.get("complete")
                else "pass"
                if successful and figure_status == "pass" and report_correct
                else "fail"
            ),
            "figure_result": figure_score,
            "figure_judgement": figure_judgement,
            "deterministic_report": deterministic,
            "report_judgement": report_judgement,
            "judge_usage": _usage(figure_judgement, report_judgement),
            "figure_judge_usage": figure_judgement.get("usage") or {},
        }
    )
    if write_aspect_diagnostic:
        metrics["aspect_diagnostic"] = figure3.write_aspect_diagnostic(
            record,
            _diagnostic_path(record),
        )
    record["dashboard_metrics"] = metrics
    path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{record.get('config')} r{record.get('repeat')}: "
        f"figure={figure_status} report={metrics['report_correct']}"
    )
    return True


def _update_scored_runs():
    """Refresh raw Q1 records in the durable dashboard source without new judges."""
    if not SCORED_RUNS.is_file():
        return 0
    entries = _read_json(SCORED_RUNS)
    raw_by_key = {}
    for path in sorted(RUNS.glob("*.json")):
        try:
            record = _read_json(path)
        except (OSError, ValueError):
            continue
        if record.get("task") != "q1-sparse-medium":
            continue
        key = (
            record.get("config"),
            record.get("repeat"),
            record.get("llm"),
            record.get("build"),
            record.get("prompt_profile"),
        )
        raw_by_key[key] = record
    changed = 0
    for entry in entries:
        raw = entry.get("raw") or {}
        key = (
            raw.get("config"),
            raw.get("repeat"),
            raw.get("llm"),
            raw.get("build"),
            raw.get("prompt_profile"),
        )
        replacement = raw_by_key.get(key)
        if replacement is not None:
            entry["raw"] = replacement
            changed += 1
    SCORED_RUNS.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerun-reports", action="store_true")
    parser.add_argument(
        "--recompute-figure-status",
        action="store_true",
        help="Reapply the rubric to stored figure scores without another image call.",
    )
    parser.add_argument(
        "--write-aspect-diagnostics",
        action="store_true",
        help="Re-render stored numeric curves with fixture plot geometry.",
    )
    parser.add_argument(
        "--update-scored-runs",
        action="store_true",
        help="Copy updated raw Q1 records into scored_runs.json without new judges.",
    )
    args = parser.parse_args(argv)
    oracle = json.loads(figure3.ORACLE_PATH.read_text(encoding="utf-8"))
    changed = 0
    for path in sorted(RUNS.glob("*.json")):
        if rejudge(
            path,
            oracle,
            args.rerun_reports,
            not args.recompute_figure_status,
            args.write_aspect_diagnostics,
        ):
            changed += 1
    refreshed = _update_scored_runs() if args.update_scored_runs else 0
    print(f"rejudged {changed} Q1 record(s)")
    if args.update_scored_runs:
        print(f"updated {refreshed} durable Q1 score record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

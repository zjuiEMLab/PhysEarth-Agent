"""Warnings and refusals attached to a finished answer."""

import re

from physearth.research.charts import _normal_name


def report_warnings(session, answer):
    """Return advisory report-completeness findings.

    These findings help the model and the reviewer improve a scientific report, but they
    are not evidence failures.  Citation, evidence, abstract-depth and model validation
    remain enforced by ``harness.review_final`` and the research execution gates.
    """
    plan = ((session.get("research") or {}).get("plan") or {})
    gaps = plan.get("capability_gaps") or []
    problems = []
    anomalies = ((session.get("research") or {}).get("scientific_anomalies") or [])
    if anomalies:
        normalized_answer = str(answer or "").lower()
        if not any(
            word in normalized_answer
            for word in (
                "discontinuity", "abrupt jump", "numerical", "validity", "不连续", "突变", "数值", "适用范围"
            )
        ):
            problems.append(
                "Figure QA retained a persistent discontinuity as a qualified diagnostic. "
                "The report must identify it and state that it may be numerical or a model-validity "
                "boundary rather than a verified physical transition."
            )
    formal_figures = [
        figure for figure in session.get("figures") or [] if not figure.get("preview")
    ]
    normalized_report = str(answer or "").strip()
    lowered_report = normalized_report.lower()
    # A workflow-status message is not a scientific report.  Models sometimes stop after
    # QA with "the report can now be delivered"; previously that passed citation checks
    # and marked the project complete despite containing no interpretation or conclusion.
    status_only_phrases = (
        "can now be delivered", "will now be delivered", "ready to deliver",
        "final report can", "final report will", "正式报告现在可以", "可以交付最终",
    )
    conclusion_signals = (
        "therefore", "we conclude", "the results show", "indicates that",
        "supports the hypothesis", "does not support", "conclusion", "结论",
        "因此", "结果表明", "说明了", "支持假设", "不支持",
    )
    if formal_figures and (
        any(phrase in lowered_report for phrase in status_only_phrases)
        or not any(signal in lowered_report for signal in conclusion_signals)
    ):
        problems.append(
            "The response is only a workflow/QA status update, not the final scientific report. "
            "Interpret the plotted trends and comparisons, relate them to the hypothesis and "
            "success criteria, state limitations, and give an explicit scientific conclusion."
        )
    if len(formal_figures) > 1:
        missing_numbers = []
        for index, figure in enumerate(formal_figures, 1):
            number = figure.get("figure_number") or index
            if not re.search(r"(?:figure|fig\.?|图)\s*%d\b" % number, str(answer or ""), re.I):
                missing_numbers.append(str(number))
        if missing_numbers:
            problems.append(
                "The report must explain each formal output by Figure number. Add explicit "
                "interpretation for Figure %s; do not discuss several plots as an unnamed group."
                % ", Figure ".join(missing_numbers)
            )
    if not gaps:
        return " ".join(problems)
    lowered = lowered_report
    names_present = all(_normal_name(name) in _normal_name(answer) for name in gaps)
    limitation_present = any(
        phrase in lowered
        for phrase in ("partial", "not run", "not available", "unavailable", "not registered", "未运行", "不可用", "未注册", "部分复现")
    )
    if not (names_present and limitation_present):
        problems.append(
            "This is only a partial reproduction because these named comparison models are not "
            "registered and were not run: %s. State that limitation explicitly; do not report "
            "cross-model agreement metrics or attribute causal differences to their solvers."
            % ", ".join(gaps)
        )
    return " ".join(problems)


def report_problem(session, answer):
    """Backward-compatible name for callers that still inspect report findings."""
    return report_warnings(session, answer)


def safe_report(session):
    """Deterministic last resort: report only actions recorded in session state."""
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    gaps = plan.get("capability_gaps") or []
    planned = plan.get("runs") or []
    successful = session.get("successful_runs") or []
    completed = []
    for run in planned:
        if any(
            actual.get("model") == run.get("model")
            and all(actual.get("spec", {}).get(key) == value for key, value in run.get("parameters", {}).items())
            for actual in successful
        ):
            completed.append(run.get("label") or run.get("id") or run.get("model"))
    markers = sorted(session.get("models_run") or ())
    model_note = (
        " Registered model evidence: %s." % ", ".join("[model:%s]" % marker for marker in markers)
        if markers
        else ""
    )
    figures = [figure for figure in session.get("figures") or [] if not figure.get("preview")]
    lines = [
        "Evidence-only fallback report",
        "The language-model narrative repeatedly failed evidence validation, so unsupported interpretation has been removed.",
        "Completed approved run(s): %s.%s" % (", ".join(completed) or "none", model_note),
        "Formal figure(s) generated from recorded result handles: %d." % len(figures),
    ]
    if gaps:
        lines.append(
            "This is a partial reproduction. %s %s not registered locally and %s not run; no cross-model agreement metric or solver-causality conclusion is available."
            % (", ".join(gaps), "is" if len(gaps) == 1 else "are", "was" if len(gaps) == 1 else "were")
        )
    else:
        lines.append("No additional scientific interpretation is published by this fallback.")
    return "\n\n".join(lines)

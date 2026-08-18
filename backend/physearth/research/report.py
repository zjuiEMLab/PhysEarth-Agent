"""Warnings, report-generation instructions, and refusals for finished answers."""

import json
import re

from physearth.research.charts import _normal_name


def report_generation_prompt(session):
    """Build the final-report contract from the approved research state.

    The model already has the tool transcript, but a long reproduction can bury the
    provenance ledger among plan repairs and tool output.  Keep this reminder compact,
    state-derived, and free of benchmark-specific model or figure names.
    """
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    mappings = plan.get("parameter_mapping") or []
    if isinstance(mappings, dict):
        mappings = list(mappings.values())
    ledger = []
    for item in mappings:
        if not isinstance(item, dict):
            continue
        value = item.get("mapped_value")
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        ledger.append(
            "- %s = %s; provenance=%s; paper_value=%s; evidence=%s; reason=%s"
            % (
                item.get("model_input") or item.get("paper_concept") or "unnamed input",
                value,
                item.get("provenance_class") or "unknown",
                item.get("paper_value"),
                item.get("evidence_ref") or "none",
                item.get("rationale") or item.get("confidence_basis") or "not recorded",
            )
        )
    if not ledger:
        ledger.append("- No parameter mapping was recorded; state that provenance is unavailable.")

    figures = [figure for figure in session.get("figures") or [] if not figure.get("preview")]
    figure_state = []
    for index, figure in enumerate(figures, 1):
        figure_state.append(
            "- Figure %s: title=%r; x=%r; y=%r; series=%s; render_review=%s"
            % (
                figure.get("figure_number") or index,
                figure.get("title"),
                figure.get("x_label"),
                figure.get("y_label"),
                len(figure.get("series") or []),
                (figure.get("quality_review") or {}).get("passed"),
            )
        )
    if not figure_state:
        figure_state.append("- No formal figure was recorded.")

    gaps = plan.get("capability_gaps") or []
    return "\n".join(
        [
            "READER-FACING REPRODUCTION REPORT (be concise; use the recorded state; do not add new experiments)",
            "1. Start with the research result and conclusion. In the opening one or two "
            "paragraphs, answer the original question from the generated figure first: state "
            "what the image shows about convergence, divergence, ordering, or comparison. "
            "If no generated figure exists, say that immediately and do not invent a visual "
            "conclusion. Put supporting details after this opening answer.",
            "2. Use only reader-facing headings such as Research result and conclusion, "
            "Supporting results, Assumed parameters, and Limitations. Do not expose internal "
            "evaluation instructions or headings such as Language Compliance, rubric, gate, "
            "workflow, prompt, QA, or evaluator. Apply those checks silently while writing "
            "normal research-results and conclusion prose.",
            "3. Choose a calibrated outcome. Manual or LLM visual review is the primary figure "
            "validation: if it confirms the same scientific curves and patterns, the report may "
            "call the qualitative reproduction successful even when deterministic title, caption, "
            "legend, recipe, or numeric checks differ. Treat those differences as diagnostics when "
            "the paper did not specify the parameter. Call the result failed only when the figure "
            "cannot be rendered, required curves are missing, visual review fails, or a required "
            "paper-explicit condition is contradicted. This visual allowance does not waive a "
            "failed model run, missing evidence, an unsupported model/output, or a user-requested "
            "numeric or parameter constraint.",
            "4. The parameter ledger below is authoritative. Copy each provenance class exactly. "
            "Every paper_inferred, model_assumption, backend_default, unknown, or null-paper-value "
            "must appear under a clearly labelled Guessed/assumed parameters subsection. Never "
            "call such a value paper_explicit, and never say that no parameter was guessed when "
            "the ledger contains one.",
            "5. After the opening answer, write separate concise sections for (a) the conclusion supported by the source/generated "
            "image and (b) the conclusion supported by actual result handles/arrays. The image "
            "supports count, axes, units, legend, grouping, ordering, shape, convergence and "
            "visible separation; it does not supply digitized values or prove numerical agreement.",
            "6. Compare those two conclusions in a short table or explicit paragraphs. Identify agreement, "
            "disagreement, and qualifications caused by assumptions, version differences, rendering, "
            "or insufficient checks. A passed manual/visual review establishes qualitative figure "
            "correspondence; a render/metadata check alone only establishes that the chart is usable.",
            "7. Only report numerical comparisons that an actual tool result or recorded calculation "
            "supplied. Do not invent or estimate correlation, RMSE, bias, ratios, percent error, or "
            "validation statistics. If none was supplied, write N/A or not scoreable.",
            "8. Answer the original research question directly in the opening and final conclusion. State the "
            "requested range, threshold, or comparison only when supported by opened paper evidence "
            "or recorded results; otherwise say that the requested quantity is not identifiable.",
            "9. Do not write 'matches exactly', 'no visual discrepancy', or equivalent language "
            "unless an explicit comparison check supports it. Prefer 'same qualitative pattern' and "
            "name the observed differences and their consequences.",
            "10. Preserve any machine-readable provenance/outcome appendix required by the user or "
            "evaluation protocol, filling it only from the recorded run state.",
            "AUTHORITATIVE PARAMETER LEDGER:\n" + "\n".join(ledger),
            "RECORDED FORMAL FIGURES:\n" + "\n".join(figure_state),
            "UNAVAILABLE OR UNRUN COMPARISONS: %s" % (", ".join(map(str, gaps)) or "none recorded"),
        ]
    )


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
        "the figure", "the chart", "the image", "research result", "research conclusion",
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
    mappings = plan.get("parameter_mapping") or []
    if isinstance(mappings, dict):
        mappings = list(mappings.values())
    guessed = [
        item.get("model_input") or item.get("paper_concept") or "an input"
        for item in mappings
        if isinstance(item, dict)
        and item.get("provenance_class") in {"paper_inferred", "model_assumption", "backend_default"}
    ]
    if guessed and not any(
        phrase in lowered_report
        for phrase in (
            "guessed", "assumed parameter", "assumptions", "model_assumption",
            "backend_default", "paper_inferred", "猜测", "假设",
        )
    ):
        problems.append(
            "The report must list the guessed or backend-default parameters explicitly, with "
            "their values, provenance class, and reason; do not present them as paper facts."
        )
    if formal_figures:
        figure_language_present = any(
            phrase in lowered_report
            for phrase in ("the figure shows", "the chart shows", "the image shows", "visible curves")
        )
        if not figure_language_present and not any(
            phrase in lowered_report
            for phrase in ("figure-based", "based on the figure", "visual conclusion", "图形结论")
        ):
            problems.append(
                "The report must give a separate conclusion based on each generated figure, "
                "covering its visible curves, axes, units, legend and qualitative patterns."
            )
        result_language_present = any(
            phrase in lowered_report
            for phrase in ("computed results", "recorded results", "computed values")
        )
        if not result_language_present and not any(
            phrase in lowered_report
            for phrase in ("result-backed", "actual model results", "recorded arrays", "数值结果")
        ):
            problems.append(
                "The report must give a separate conclusion from the actual executed result "
                "arrays and conditions, not only describe the chart."
            )
        if not any(
            phrase in lowered_report
            for phrase in ("agreement", "figure-versus", "figure vs", "compare", "对照", "比较")
        ):
            problems.append(
                "The report must compare the figure-based and result-backed conclusions and "
                "state any disagreement or qualification."
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
        "Research result and conclusion",
        "The recorded evidence is incomplete, so unsupported interpretation is not reported.",
        "Completed run(s): %s.%s" % (", ".join(completed) or "none", model_note),
        "Generated figure(s) from recorded result handles: %d." % len(figures),
    ]
    if gaps:
        lines.append(
            "This is a partial reproduction. %s %s not registered locally and %s not run; no cross-model agreement metric or solver-causality conclusion is available."
            % (", ".join(gaps), "is" if len(gaps) == 1 else "are", "was" if len(gaps) == 1 else "were")
        )
    else:
        lines.append("No additional scientific interpretation is published by this fallback.")
    return "\n\n".join(lines)

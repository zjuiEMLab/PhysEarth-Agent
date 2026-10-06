"""Pages a person keeps: the research plan and the final report, as standalone HTML.

The Conversation panel is narrow and lives as long as the session. A plan someone wants
to read properly, and a report they want to keep or send, are written out as one HTML
file each -- styles inline, figures embedded -- under the session's project directory,
where the Studio serves them. Rendering stays here, beside the rest of the interface;
writing the file is one call into the package's artifact store.
"""

import base64
import re
import time
from pathlib import Path
from urllib.parse import quote

from apps.studio.views.parts import _plan_cell, _plan_table, plan_sheet_html
from apps.studio.views.text import _e, _paragraphs
from physearth.api import agent, artifacts, research

_STYLE = """
:root{--paper:#faf9f5;--card:#ffffff;--ink:#1f1e1d;--soft:#4a4944;--mute:#6b6a65;--line:#e4e1d8;
--clay:#c4623f;--wash:#f6e6dd;--ok:#2f6b3a;--okwash:#e3f0d8}
@media (prefers-color-scheme:dark){:root{--paper:#1c1b19;--card:#252421;--ink:#ecebe6;--soft:#c9c7bf;
--mute:#9a988f;--line:#3a3833;--clay:#e08a63;--wash:#3a2a22;--ok:#9fd3a6;--okwash:#24331f}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 16px 64px}
h1{font:700 26px/1.25 Georgia,"Times New Roman",serif;margin:0 0 6px}
h2{font:700 19px/1.3 Georgia,"Times New Roman",serif;margin:28px 0 10px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:16px;margin:18px 0 8px}
.meta{color:var(--mute);font-size:13px;margin:0 0 18px}
.meta span+span:before{content:" · "}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
.findings{border-color:color-mix(in srgb,var(--clay) 50%,var(--line));background:color-mix(in srgb,var(--wash) 55%,var(--card))}
.label{font:700 11px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.07em;text-transform:uppercase;color:var(--mute);margin:0 0 6px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;vertical-align:top;padding:6px 8px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}
th{color:var(--soft);font-size:12px}
.md-table-wrap,.research-plan-table-wrap,.plan-sheet-table-wrap,.research-preview-wrap{max-width:100%;overflow-x:auto;margin:8px 0}
code,pre,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
pre{white-space:pre-wrap;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;overflow-x:auto}
.cite{display:inline-block;font:600 11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;padding:2px 5px;border-radius:4px;
background:var(--okwash);color:var(--ok);text-decoration:none;white-space:nowrap}
.cite--abs{background:#fbe9c7;color:#7a4a05}
figure{margin:16px 0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
figure img{display:block;max-width:100%;height:auto;margin:0 auto;background:#fff;border-radius:6px}
figcaption{font-size:13px;color:var(--soft);margin-top:8px}
.plan-sheet{display:grid;gap:14px}
.plan-sheet__group{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--card)}
.plan-sheet__title{font-weight:600;margin-bottom:8px}
.plan-sheet__purpose{font-size:13px;color:var(--soft);margin:-4px 0 8px}
.plan-sheet-table td:nth-child(2){white-space:nowrap}
.plan-sheet-table td,.plan-sheet-table th{overflow-wrap:normal;word-break:normal}
.plan-sheet-table th{white-space:nowrap}
.plan-sheet-table td:first-child{min-width:150px}
.plan-sheet__about{font-size:12px;color:var(--mute);line-height:1.35;margin-top:2px}
.plan-sheet__label{font:600 11px/1.2 ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--mute);margin:10px 0 4px}
.plan-sheet__sweep,.plan-sheet__sources{font-size:13px;margin:8px 0 0;display:flex;gap:10px;flex-wrap:wrap}
.plan-sheet__decide{border:1px solid #e0b25c;background:#fbf3df;color:#3d2c08;border-radius:10px;padding:10px 14px}
.plan-sheet__hint{font-size:12px;opacity:.8}
.plan-sheet__stage{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:0 5px}
.src{display:inline-block;font:600 11px/1 ui-monospace,monospace;padding:3px 6px;border-radius:4px;white-space:nowrap}
.src-ref{font:11px ui-monospace,monospace;color:var(--mute)}
.src--extracted{background:#e3f0d8;color:#2f5a12}.src--derived{background:#d9efe9;color:#0b5a47}
.src--user{background:#dce9f8;color:#174a80}.src--default{background:#ebeae4;color:#4a4944}
.src--assumed,.src--mixed{background:#fbe9c7;color:#7a4a05}.src--guessed,.src--unlabelled{background:#f8d9d9;color:#8a2020}
.how ul{margin:6px 0 0;padding-left:20px}
footer{margin-top:40px;color:var(--mute);font-size:12px}
@media print{body{background:#fff}main{max-width:none;padding:0}figure,.card{break-inside:avoid}}
"""


def file_url(path):
    """How the Studio serves a file under its state directory."""
    return "/gradio_api/file=%s" % quote(str(Path(path).resolve()), safe="/")


def _export_dir(session):
    path = artifacts.project_dir(session.get("id") or "shared") / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _page(title, body):
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>%s</title><style>%s</style></head><body><main>%s</main></body></html>"
        % (_e(title), _STYLE, body)
    )


def _title(plan, fallback):
    """The plan's title, unless it is really the whole question restated."""
    title = " ".join(str(plan.get("title") or "").split())
    return title if title and len(title) <= 90 else fallback


def _list(items):
    items = [str(item) for item in items or () if str(item).strip()]
    if not items:
        return "<p class='meta'>none stated</p>"
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % _e(item) for item in items)


# ------------------------------------------------------------------------- plan


def _warning_text(item):
    """One validation warning as a sentence, from whichever of its fields are present."""
    parts = [str(item.get(key)) for key in ("message", "detail") if item.get(key)]
    if not parts:
        field = str(item.get("field") or "").replace("_", " ")
        expected, actual = item.get("expected"), item.get("actual")
        parts.append(
            "%s%s%s" % (
                field or "plan",
                ": paper context %s" % research.sheet.fmt(expected) if expected not in (None, "") else "",
                "; plan has %s" % research.sheet.fmt(actual) if actual not in (None, "") else "",
            )
        )
    return " ".join(parts)


def plan_document(session):
    """The current plan as a page to read, print or send before approving it.

    What a reviewer decides on: the question, the conditions with their sources, the runs,
    the figures, and the assumptions. The machinery behind it -- evidence ledger, raw
    mappings, the protocol file -- stays out; the protocol is one typed word away.
    """
    project = (session or {}).get("research") or {}
    plan = project.get("plan") or {}
    version = int(project.get("plan_version") or 1)
    title = _title(plan, "Research plan")
    chart_rows = [
        [_e(item.get("label") or item.get("id")),
         _e(research.sheet.axis_name(plan, item.get("x")) if item.get("x") else "-"),
         _e("; ".join(research.sheet.axis_name(plan, y) for y in item.get("ys") or [item.get("y")] if y)),
         _e("required" if item.get("required", True) else "optional"),
         _e(item.get("purpose") or "")]
        for item in plan.get("charts") or [] if isinstance(item, dict)
    ]
    target_rows = [
        [_e(item.get("target_quantity") or item.get("id")),
         _e(str(item.get("source_id") or item.get("source_type") or "")),
         _e(item.get("status") or "planned"),
         _e(", ".join(item.get("chart_ids") or []) or "-")]
        for item in plan.get("reproduction_targets") or [] if isinstance(item, dict)
    ]
    warnings = [
        _warning_text(item) for item in plan.get("validation_warnings") or [] if isinstance(item, dict)
    ]
    summary = plan.get("revision_summary") or project.get("revision_summary")
    readable = (summary or {}).get("readable") or []
    body = [
        "<h1>%s</h1>" % _e(title),
        "<p class='meta'><span>Plan v%03d</span><span>%s</span><span>%s</span></p>"
        % (version, _e((project.get("phase") or "plan_review").replace("_", " ")), _e(time.strftime("%Y-%m-%d %H:%M"))),
        "<div class='card how'><div class='label'>How to approve or change this plan</div>"
        "Reply in the PhysEarth Conversation:<ul>"
        "<li><b>approve</b> runs the plan as written and draws its required figures;</li>"
        "<li><b>preview</b> first draws the planned figures from pseudo-data, to check the layout;</li>"
        "<li>anything else is a change, for example <i>change the density range to 10-500 kg/m3</i>. "
        "A new version comes back for review, and nothing runs until you approve.</li></ul></div>",
        "<p><b>Question.</b> %s</p>" % _e(plan.get("question") or project.get("question") or ""),
    ]
    if plan.get("hypothesis"):
        body.append("<p><b>Hypothesis.</b> %s</p>" % _e(plan["hypothesis"]))
    if readable:
        body.append(
            "<div class='card'><div class='label'>What changed from v%03d</div><ul>%s</ul></div>"
            % (
                int(summary.get("from_version") or version - 1),
                "".join(
                    "<li>%s%s</li>" % (
                        {"added": "Added ", "removed": "Removed "}.get(item["kind"], ""), _e(item["text"]),
                    )
                    for item in readable
                ),
            )
        )
    digests = [
        record for record in ((session or {}).get("paper_digests") or {}).values()
        if record.get("items")
    ]
    findings = [
        "<li>%s <span class='cite'>%s</span></li>" % (_e(item["statement"]), _e(item["ref"]))
        for record in digests for item in record["items"]
        if item.get("kind") in ("result", "figure", "limitation")
    ] + [
        "<li>%s <span class='cite'>%s</span></li>" % (_e(item["finding"]), _e(item["evidence_ref"]))
        for item in plan.get("literature_evidence") or ()
        if isinstance(item, dict) and item.get("finding") and item.get("evidence_ref")
    ]
    body.append(
        "<h2>What the paper states</h2>"
        + ("<ul>%s</ul>" % "".join(findings) if findings else
           "<p class='meta'>Nothing from the paper is recorded yet. The report compares against "
           "what is recorded here, so ask for the paper's statements to be added if you need "
           "that comparison.</p>")
    )
    template = research.templates.TEMPLATES[research.templates.choose(project)]
    body.append(
        "<p class='meta'>The report will be written as a <b>%s</b>.</p>" % _e(template["title"])
    )
    body += [
        "<h2>Conditions and runs</h2>",
        plan_sheet_html(plan) or "<p class='meta'>No runs are planned.</p>",
        "<h2>Figures</h2>",
        _plan_table(("Figure", "X axis", "Y axis", "Status", "Purpose"), chart_rows),
    ]
    if target_rows:
        body += [
            "<h2>What is reproduced</h2>",
            _plan_table(("Quantity", "From", "Status", "Figures"), target_rows),
        ]
    body += [
        "<h2>Assumptions, limitations and success criteria</h2>",
        "<h3>Assumptions</h3>%s<h3>Limitations</h3>%s<h3>Success criteria</h3>%s"
        % (_list(plan.get("assumptions")), _list(plan.get("limitations")), _list(plan.get("success_criteria"))),
    ]
    if warnings:
        body += ["<h2>Things to check</h2>", _list(warnings)]
    body.append(
        "<footer>Written by PhysEarth-Agent from plan v%03d. Reply <b>protocol</b> in the "
        "Conversation for the generated protocol file.</footer>" % version
    )
    return _page("%s · plan v%03d" % (title, version), "".join(body))


def write_protocol(session):
    """The generated protocol, written only when someone asks for it. Returns (url, name)."""
    project = (session or {}).get("research") or {}
    if not project.get("plan"):
        return "", ""
    version = int(project.get("plan_version") or 1)
    name = "research-protocol-v%03d.yaml" % version
    try:
        path = _export_dir(session) / name
        path.write_text(research.protocol_yaml(project), encoding="utf-8")
    except (OSError, ValueError):
        return "", ""
    return file_url(path), name


def ensure_plan_export(session):
    """Write the current plan version once and remember where it is. Returns its URL."""
    project = (session or {}).get("research") or {}
    if not project.get("plan"):
        return ""
    version = int(project.get("plan_version") or 1)
    saved = project.get("plan_export") or {}
    if saved.get("version") == version and saved.get("url") and Path(saved.get("path", "")).is_file():
        return saved["url"]
    try:
        path = _export_dir(session) / ("research-plan-v%03d.html" % version)
        path.write_text(plan_document(session), encoding="utf-8")
    except (OSError, ValueError):
        return ""
    project["plan_export"] = {"version": version, "path": str(path), "url": file_url(path)}
    return project["plan_export"]["url"]


# ----------------------------------------------------------------------- report

_HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.M)


def key_findings(report):
    """The report's own first section, which the reporting guideline makes the conclusion.

    Falls back to the first three paragraphs when the report has no section headings.
    """
    text = str(report or "").replace(agent.SEGMENT_BREAK, "\n\n").strip()
    sections = [m for m in _HEADING.finditer(text) if len(m.group(1)) >= 2]
    if sections:
        start = sections[0].end()
        end = sections[1].start() if len(sections) > 1 else len(text)
        body = text[start:end].strip()
        if body:
            return body
    paragraphs = [part for part in re.split(r"\n\s*\n", text) if part.strip() and not part.lstrip().startswith("#")]
    return "\n\n".join(paragraphs[:3])


def _image_data(figure):
    for key in ("artifact_image_path", "image_path"):
        path = Path(str(figure.get(key) or ""))
        if path.is_file():
            try:
                return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
            except OSError:
                continue
    return ""


def _figure_html(figure, number):
    image = _image_data(figure)
    series = figure.get("series") or []
    rows = [
        [_plan_cell(item.get("label")), _plan_cell(item.get("origin") or item.get("source")),
         _plan_cell(item.get("n_points")), "<code>%s</code>" % _e(item.get("handle") or "")]
        for item in series
    ]
    comparisons = [
        [_plan_cell(item.get("of")), _plan_cell(item.get("quantity")), _plan_cell(item.get("bias")),
         _plan_cell(item.get("rmse")), _plan_cell(item.get("r"))]
        for item in figure.get("comparisons") or [] if isinstance(item, dict)
    ]
    return (
        "<figure>%s<figcaption><b>%s</b>%s</figcaption>%s%s</figure>"
        % (
            "<img alt='%s' src='%s'>" % (_e(figure.get("title") or "Figure %d" % number), image) if image else "",
            _e(figure.get("title") or "Figure %d" % number),
            "<br>%s" % _e(figure["subtitle"]) if figure.get("subtitle") else "",
            _plan_table(("Series", "Origin", "Points", "Run"), rows) if rows else "",
            _plan_table(("Compared", "Quantity", "Bias", "RMSE", "r"), comparisons) if comparisons else "",
        )
    )


def report_document(session, report, model_id="", timing=None):
    """The full report with its figures, the plan it ran and how long it took."""
    session = session or {}
    project = session.get("research") or {}
    plan = project.get("plan") or {}
    version = int(project.get("plan_version") or 1)
    title = _title(plan, "Research report")
    figures = [
        f for f in session.get("figures") or []
        if not f.get("preview") and not f.get("research_preview")
    ]
    meta = [
        "Plan v%03d" % version,
        time.strftime("%Y-%m-%d %H:%M"),
    ]
    if model_id:
        meta.append(str(model_id))
    if timing:
        meta.append("agent time %s" % timing)
    body = [
        "<h1>%s</h1>" % _e(title),
        "<p class='meta'>%s</p>" % "".join("<span>%s</span>" % _e(item) for item in meta),
        "<p><b>Question.</b> %s</p>" % _e(plan.get("question") or project.get("question") or ""),
        "<div class='card findings'><div class='label'>Key findings</div>%s</div>"
        % _paragraphs(key_findings(report)),
    ]
    if figures:
        body.append("<h2>Figures</h2>")
        body += [_figure_html(figure, n) for n, figure in enumerate(figures, 1)]
    body += [
        "<h2>Full report</h2>",
        _paragraphs(str(report or "").replace(agent.SEGMENT_BREAK, "\n\n")),
        "<h2>What was run</h2>",
        plan_sheet_html(plan) or "<p class='meta'>No plan recorded.</p>",
        "<footer>Written by PhysEarth-Agent. Markers such as <span class='cite'>paper#08</span> "
        "name the paper section, model run, dataset or method note each statement rests on; "
        "the session's Evidence panel holds them.</footer>",
    ]
    return _page("%s · report" % title, "".join(body))


def write_report(session, report, model_id="", timing=None):
    """Write the report page for the current plan version. Returns its URL, or ""."""
    project = (session or {}).get("research") or {}
    version = int(project.get("plan_version") or 1)
    try:
        path = _export_dir(session) / ("research-report-v%03d.html" % version)
        path.write_text(report_document(session, report, model_id, timing), encoding="utf-8")
    except (OSError, ValueError):
        return ""
    project["report_export"] = {"version": version, "path": str(path), "url": file_url(path)}
    return project["report_export"]["url"]

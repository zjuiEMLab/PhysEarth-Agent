"""Phases, provenance vocabulary, the result shapes, and the protocol document."""

import re

import yaml

PHASES = (
    "plan_review",
    "plan_approved",
    "pseudo_preview",
    "chart_selected",
    "approved",
    "completed",
)

PARAMETER_PROVENANCE = (
    "paper_explicit",
    "paper_inferred",
    "user_specified",
    "model_assumption",
    "backend_default",
)

PARAMETER_CONFIDENCE = ("high", "medium", "low")


def _provenance_confidence(provenance):
    return {
        "paper_explicit": ("high", "explicitly supported by opened paper evidence"),
        "paper_inferred": ("medium", "inferred from opened paper evidence"),
        "user_specified": ("high", "directly specified by the user"),
        "backend_default": ("medium", "provided by the registered model backend, not by the paper"),
        "model_assumption": ("low", "not supported by paper or user evidence; requires review"),
    }.get(
        provenance,
        ("low", "source provenance is incomplete and requires review"),
    )


def _clean_list(values, limit=20):
    if isinstance(values, str):
        # Some OpenAI-compatible providers occasionally serialize an array as a
        # numbered multi-line string.  Treat it as prose/list items instead of
        # iterating over individual characters.
        parts = re.split(r"(?:\r?\n)+|\s*;\s*", values)
        values = [re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", item) for item in parts]
    elif isinstance(values, dict):
        values = list(values.values())
    return [str(value).strip() for value in (values or []) if str(value).strip()][:limit]


def protocol_document(project):
    """Return the generated, session-scoped research protocol for human review.

    This is deliberately derived from the LLM proposal and current plan version.  It is
    not read from the paper corpus and is never used as hidden instruction text.
    """
    plan = project.get("plan") or {}
    return {
        "format": "phys-earth/research-protocol",
        "version": int(project.get("plan_version", 1)),
        "plan_version": int(project.get("plan_version", 1)),
        "phase": project.get("phase", "plan_review"),
        "question": plan.get("question", ""),
        "objective": plan.get("objective", ""),
        "hypothesis": plan.get("hypothesis", ""),
        "paper_evidence": list(plan.get("reference_sections") or []),
        "paper_sections": list(plan.get("reference_paper_sections") or []),
        "literature_evidence": list(plan.get("literature_evidence") or []),
        "reproduction_targets": list(plan.get("reproduction_targets") or []),
        "selected_models": list(plan.get("selected_models") or []),
        "parameter_mapping": list(plan.get("parameter_mapping") or []),
        "parameter_resolution": list(plan.get("parameter_resolution") or []),
        "paper_conditions": dict(plan.get("paper_conditions") or {}),
        "condition_provenance": dict(plan.get("condition_provenance") or {}),
        "parameters": dict(plan.get("parameters") or {}),
        "outputs": list(plan.get("outputs") or []),
        "assumptions": list(plan.get("assumptions") or []),
        "runs": list(plan.get("runs") or []),
        "charts": list(plan.get("charts") or []),
        "derived": list(plan.get("derived") or []),
        "quantities": list(plan.get("quantities") or []),
        "controls": list(plan.get("controls") or []),
        "metrics": list(plan.get("metrics") or []),
        "diagnostics": list(plan.get("diagnostics") or []),
        "success_criteria": list(plan.get("success_criteria") or []),
        "stop_conditions": list(plan.get("stop_conditions") or []),
        "limitations": list(plan.get("limitations") or []),
        "baseline_run_id": plan.get("baseline_run_id", ""),
        "approval_state": project.get("phase", "plan_review"),
        "automatic_repairs": list(plan.get("automatic_repairs") or []),
        "validation_warnings": list(plan.get("validation_warnings") or []),
        "revision_summary": dict(plan.get("revision_summary") or project.get("revision_summary") or {}),
    }


def protocol_yaml(project):
    """Serialize the generated protocol without writing a persistent protocol.yaml."""
    return yaml.safe_dump(
        protocol_document(project),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def _require(session):
    if not session.get("research"):
        raise ValueError("No LLM-authored research proposal exists yet.")
    return session["research"]


def _public(project):
    public = {**project, "plan": {**project["plan"]}, "review_log": list(project["review_log"])}
    public["protocol"] = protocol_document(public)
    public["protocol_yaml"] = protocol_yaml(public)
    return public


def _ok(summary, data):
    return {"status": "success", "summary": summary, "data": data, "citations": [], "qc": None, "ui": None, "error": None}


def _needs(summary, data):
    return {"status": "needs_input", "summary": summary, "data": data, "citations": [], "qc": None, "ui": None, "error": summary}


def _fail(summary, data=None):
    return {"status": "terminal_error", "summary": summary, "data": data or {}, "citations": [], "qc": None, "ui": None, "error": summary}


def status(session):
    project = session.get("research")
    if not project:
        return _needs("No research proposal exists yet. Analyse the question and propose one.", {"phase": "analysis"})
    return _ok("Research project is in phase %s." % project["phase"], _public(project))


ITEM_IDENTITY = {
    "runs": ("id",),
    "charts": ("id",),
    "reproduction_targets": ("id",),
    "parameter_mapping": ("model", "model_input"),
}
# What a list item needs to stand on its own. A list made only of such items is the whole
# list the model means; one that has a partial item is a patch.
ITEM_COMPLETE = {
    "runs": ("model", "parameters"),
    "charts": ("x", ("y", "ys")),
    "reproduction_targets": ("evidence_refs",),
    "parameter_mapping": ("model_input", "provenance_class"),
}


# A field a patch changes takes with it what was derived from the old value: a chart's
# series list and axis titles from its y, its x title from its x.
_DEPENDENT_FIELDS = {"y": ("ys", "y_label"), "x": ("x_label",)}


def _is_complete(item, complete):
    return all(
        any(item.get(name) not in (None, "", [], {}) for name in (
            field if isinstance(field, tuple) else (field,)
        ))
        for field in complete
    )


def merge_items(retained, supplied, keys, complete=(), unaddressed=None):
    """Patch a retained list by item identity when the change is a patch.

    A repair often names only the items it fixes: one run's sweep, one target's source.
    Replacing the whole list with those items dropped every other run or target, and the
    next validation refused the plan for what had been lost. So a list holding a partial
    item is a patch: an item whose identity is retained is updated field by field (a run's
    parameters key by key, None deleting one), a new identity is appended, and
    ``remove: true`` drops one. A list of complete items is what the model means the list
    to be and replaces it -- merging that kept every item the model had deliberately left
    out, and a refused item could then never be removed. A list without identities, or an
    empty one, also replaces.

    A mixed list, and a partly named item, are the two cases that have to be read with care.

    An item that gives only some of its identity still names one row, when only one retained
    row agrees with the parts it does give: a Figure 7 revision sent
    ``{"model_input": "density_kg_m3", "rationale": ...}`` with no ``model``, and every plan
    row carries its model, so the pair could not be matched and the whole list was replaced
    instead -- which discarded the correction and let the metadata rebuild re-derive the row
    it had just been asked to fix, seven times. So a partly named item that agrees with
    exactly one retained row takes that row's name. An item that agrees with none of them,
    or with two of them, addresses nothing: it is handed back through ``unaddressed`` for the
    caller to report, and the retained list is kept. A caller that passes no collector gets
    the old behaviour.
    """
    def identity(item):
        return tuple(str(item.get(key) or "").strip() for key in keys)

    def given(item):
        return tuple(pos for pos, part in enumerate(identity(item)) if part)

    def agrees(item, row):
        """Whether every identity part an item gives matches the retained row's."""
        wanted, have = identity(item), identity(row)
        positions = given(item)
        return bool(positions) and all(wanted[pos] == have[pos] for pos in positions)

    if not supplied or not isinstance(retained, list):
        return supplied
    rows = [row for row in retained if isinstance(row, dict)]
    addressed = []
    unnamed = []
    unmatched = []
    for item in supplied:
        if not isinstance(item, dict) or not given(item):
            unnamed.append(item)
            continue
        if len(given(item)) == len(keys):
            addressed.append(item)
            continue
        names = {identity(row) for row in rows if agrees(item, row)}
        if len(names) == 1:
            # One retained row answers to the parts it gives, so that is the row it means.
            addressed.append({**item, **dict(zip(keys, names.pop()))})
        else:
            # None answers to it, or two do and it does not say which.
            unmatched.append(item)
    if not addressed:
        if unmatched and unaddressed is not None:
            unaddressed.extend(unmatched)
            return retained
        return supplied
    if unnamed or unmatched:
        if unaddressed is None:
            return supplied
        unaddressed.extend(unnamed)
        unaddressed.extend(unmatched)
        supplied = addressed
    if all(_is_complete(item, complete) and "remove" not in item for item in supplied):
        # A short list that names only items already retained is a repair of those items,
        # not a request to delete every other one: a traced run replaced ten parameter
        # mappings with the one it was fixing, and the next refusal was about whichever
        # entry the rebuild put in its place, thirteen times over. Dropping an item takes
        # an explicit {"id": ..., "remove": true}; a list that adds an identity, or names
        # every retained one, is still the whole list.
        known = {identity(item) for item in retained if isinstance(item, dict)}
        names_only_known = all(identity(item) in known for item in supplied)
        if not (names_only_known and len(supplied) < len(known)):
            return supplied
    merged = [dict(item) if isinstance(item, dict) else item for item in retained]
    index = {
        identity(item): position for position, item in enumerate(merged) if isinstance(item, dict)
    }
    removed = set()
    for item in supplied:
        key = identity(item)
        if item.get("remove") is True:
            removed.add(key)
            continue
        update = {name: value for name, value in item.items() if name != "remove"}
        if key not in index:
            index[key] = len(merged)
            merged.append(update)
            continue
        base = dict(merged[index[key]])
        for name, dependents in _DEPENDENT_FIELDS.items():
            if name in update and update[name] != base.get(name):
                for dependent in dependents:
                    if dependent not in update:
                        base.pop(dependent, None)
        if isinstance(base.get("parameters"), dict) and isinstance(update.get("parameters"), dict):
            parameters = {**base["parameters"], **update["parameters"]}
            update["parameters"] = {
                name: value for name, value in parameters.items() if value is not None
            }
        merged[index[key]] = {**base, **update}
    return [
        item for item in merged
        if not (isinstance(item, dict) and identity(item) in removed)
    ]

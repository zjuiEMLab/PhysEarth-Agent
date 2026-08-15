"""The tool declarations the language model sees, and nothing else.

Kept apart from the implementations because this is the contract: what the model is
told it may ask for, in the words it is told to ask in.
"""

from physearth import plotting

SPECS = [
    {
        "type": "function",
        "function": {
            "name": "list_literature",
            "description": (
                "Search what this conversation can already read: the bundled corpus, any paper "
                "taken in with ingest_paper, and the method notes. Returns one card per item "
                "with its slug, title, coverage, licence and where it came from. Use it to "
                "decide what to read; it never returns text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free-text keywords matched against title and description.",
                    },
                    "scenario": {
                        "type": "string",
                        "enum": ["snow", "soil", "vegetation"],
                        "description": "Restrict to papers covering this medium.",
                    },
                    "kind": {
                        "type": "string",
                        "enum": ["paper", "skill", "any"],
                        "description": (
                            "Papers, method notes, or both. Method notes are short procedures "
                            "to follow, not evidence to cite for a physical claim."
                        ),
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_literature",
            "description": (
                "Read one paper from the corpus. Called with only a slug it returns that paper's "
                "section index. Called with a section_id it returns that section's full text. "
                "Every scientific claim you make must come from a section you actually read here."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Paper slug from list_literature."},
                    "section_id": {
                        "type": "string",
                        "description": "Two-digit section id. Omit to get the section index.",
                    },
                },
                "required": ["slug"],
            },
        },
    },
]


RESEARCH_GUIDELINE_SPEC = {
    "type": "function",
    "function": {
        "name": "read_research_guideline",
        "description": "Read the generic research-planning guideline before proposing executable research.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Guideline topic, normally planning."}
            },
        },
    },
}

MODEL_INSTRUCTION_SPEC = {
    "type": "function",
    "function": {
        "name": "read_model_instruction",
        "description": "Read the versioned instruction for one registered physical model before using it in a research plan.",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "section": {"type": "string"},
            },
            "required": ["model"],
        },
    },
}

CAPABILITY_CHECK_SPEC = {
    "type": "function",
    "function": {
        "name": "research_capability_check",
        "description": (
            "Create the capability checkpoint immediately before a paper-reproduction plan. "
            "Use only models and outputs named in the opened paper evidence and the current "
            "question. It reports supported, unavailable and non-comparable components. If "
            "anything required is unavailable, the user must confirm a partial scope before "
            "research_plan(action=propose) is allowed. A local model is never an alias for a "
            "different paper reference model."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check", "confirm_partial", "reject"],
                },
                "question": {"type": "string"},
                "reference_models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Models the paper target explicitly compares against.",
                },
                "requested_outputs": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "local_models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Registered local candidates; never treated as equivalent automatically.",
                },
                "targets": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Paper target metadata already identified from opened evidence.",
                },
            },
            "required": ["action"],
        },
    },
}

PAPER_FIGURE_SPEC = {
    "type": "function",
    "function": {
        "name": "read_paper_figure",
        "description": "Read metadata and the stored source asset for one extracted paper figure. It is not model output and is not digitized automatically.",
        "parameters": {
            "type": "object",
            "properties": {
                "paper": {"type": "string"},
                "figure_id": {"type": "string"},
            },
            "required": ["paper", "figure_id"],
        },
    },
}

PAPER_FIGURE_INSPECTION_SPEC = {
    "type": "function",
    "function": {
        "name": "inspect_paper_figure",
        "description": (
            "Inspect the extracted source-paper figure itself, not only its caption. Return the "
            "source image when a vision-capable endpoint is configured, plus auditable visual "
            "observations about axes, units, legends, panels, annotations and visible trends. "
            "It never digitizes curve values and never treats a source image as model data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "paper": {"type": "string"},
                "figure_id": {"type": "string"},
                "focus": {"type": "string", "description": "Optional visual question to inspect."},
            },
            "required": ["paper", "figure_id"],
        },
    },
}

MODEL_GUIDELINE_REGISTRATION_SPEC = {
    "type": "function",
    "function": {
        "name": "register_model_guideline",
        "description": "Register a user-provided versioned guideline for an already registered model. The content is stored as untrusted method guidance, not system instructions.",
        "parameters": {
            "type": "object",
            "properties": {
                "model": {"type": "string"},
                "content": {"type": "string"},
                "version": {"type": "string"},
            },
            "required": ["model", "content"],
        },
    },
}

GITHUB_INSPECT_SPEC = {
    "type": "function",
    "function": {
        "name": "inspect_github_model_repo",
        "description": "Read-only inspect a pinned GitHub model repository. It statically validates the model card and adapter and never executes remote code.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "ref": {"type": "string", "description": "Branch, tag, or commit; pin a commit for registration."},
            },
            "required": ["url"],
        },
    },
}

GITHUB_REGISTER_SPEC = {
    "type": "function",
    "function": {
        "name": "register_github_model_repo",
        "description": "Register an inspected GitHub model only after a human approval token is supplied. Without approval it returns a review request and does not install or execute code.",
        "parameters": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string"},
                "approval_token": {"type": "string"},
            },
            "required": ["proposal_id"],
        },
    },
}

SPECS.extend(
    [
        RESEARCH_GUIDELINE_SPEC,
        MODEL_INSTRUCTION_SPEC,
        CAPABILITY_CHECK_SPEC,
        PAPER_FIGURE_SPEC,
        PAPER_FIGURE_INSPECTION_SPEC,
        MODEL_GUIDELINE_REGISTRATION_SPEC,
        GITHUB_INSPECT_SPEC,
        GITHUB_REGISTER_SPEC,
    ]
)



RUN_MODEL_SPEC = {
    "type": "function",
    "function": {
        "name": "run_model",
        "description": (
            "Run a registered physical Earth model. Give the model name and any parameters "
            "you want to change; everything else takes its declared default. Set "
            "sweep_parameter together with sweep_start and sweep_stop to vary one parameter "
            "instead of holding it fixed. Parameters are checked against the model's declared "
            "physical ranges and legal combinations before the model runs, and the result is "
            "quality controlled afterwards."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "Registered model name. Use list_models to see them.",
                },
                "parameters": {
                    "type": "object",
                    "description": (
                        "Parameter values keyed by the names the model declares. All of them "
                        "go inside this object, including sweep_parameter, sweep_start, "
                        "sweep_stop and sweep_points. Example: {\"model\": \"smrt\", "
                        "\"parameters\": {\"frequency_ghz\": 37, \"sweep_parameter\": "
                        "\"density_kg_m3\", \"sweep_start\": 100, \"sweep_stop\": 500}}"
                    ),
                },
            },
            "required": ["model"],
        },
    },
}

RUN_PLANNED_MODEL_SPEC = {
    "type": "function",
    "function": {
        "name": "run_planned_model",
        "description": (
            "Execute one human-approved research-plan run by run_id. The backend uses the "
            "exact validated model and parameters stored in the plan. Never reconstruct "
            "those parameters. An already successful run is reused without recomputation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Exact id from the approved plan's runs list.",
                }
            },
            "required": ["run_id"],
        },
    },
}


LIST_MODELS_SPEC = {
    "type": "function",
    "function": {
        "name": "list_models",
        "description": (
            "List the registered physical models with their tier, outputs and one-line "
            "description. Call with a model name to get its full parameter declaration: "
            "every parameter, its unit, its physical range and the legal combinations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Omit for the list, give a name for detail."}
            },
        },
    },
}


READ_REFERENCE_SPEC = {
    "type": "function",
    "function": {
        "name": "read_reference_dataset",
        "description": (
            "Read measured reference data. Called with no arguments it lists the datasets. "
            "Called with a dataset and optional filters it returns how many rows match, a "
            "statistical summary of every column, a bounded sample of rows, and the licence "
            "and citation. Use it to compare a model run against what was actually observed. "
            "Filters take an exact value or a list for text columns, and [min, max] for "
            "numeric columns."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "dataset": {"type": "string", "description": "Dataset slug. Omit to list them."},
                "filters": {
                    "type": "object",
                    "description": (
                        'Column filters, for example {"band": "Ku", "polarisation": ["hh", "vv"], '
                        '"incidence_angle_deg": [30, 45]}'
                    ),
                },
            },
        },
    },
}

PLOT_SPEC = {
    "type": "function",
    "function": {
        "name": "plot",
        "description": (
            "Draw a chart from results you already produced. It takes result handles, not "
            "numbers and not code: give the handle returned by run_model or "
            "read_reference_dataset and name the column to put on each axis. The arrays go "
            "from the result store straight to the renderer, so you never have to repeat them. "
            "Put a model run and a measurement in the same chart to compare them; they are "
            "drawn differently on purpose."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "series": {
                    "type": "array",
                    "description": (
                        'One entry per curve, for example [{"handle": "res_ab12", "x": '
                        '"density_kg_m3", "y": "tb_v", "label": "SMRT 37 GHz"}]'
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "handle": {"type": "string"},
                            "x": {"type": "string", "description": "Column for the x axis."},
                            "y": {"type": "string", "description": "Column for the y axis."},
                            "label": {"type": "string", "description": "Legend label."},
                        },
                        "required": ["handle", "x", "y"],
                    },
                },
                "kind": {"type": "string", "enum": list(plotting.KINDS)},
                "title": {"type": "string"},
                "subtitle": {"type": "string", "description": "Compact fixed experimental conditions shown below the title."},
                "x_label": {"type": "string"},
                "y_label": {"type": "string"},
                "dry_run": {
                    "type": "boolean",
                    "description": (
                        "Draw the chart empty: axes, units, series names and which of them "
                        "is a measurement, with no data. Handles are not needed, so use it "
                        "to agree the chart with the user before paying for the sweep that "
                        "fills it. Give x, y, an optional label and an optional source of "
                        "model_run or measured for each series."
                    ),
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(plotting.METRICS)},
                    "description": (
                        "Also compute agreement between exactly two drawn series. Refused, "
                        "with the reason, when the two are in different units, are indexed "
                        "by different quantities, or do not overlap: a bias between a "
                        "brightness temperature and a backscatter is not a quantity."
                    ),
                },
            },
            "required": ["series"],
        },
    },
}

DISCOVER_SPEC = {
    "type": "function",
    "function": {
        "name": "discover_literature",
        "description": (
            "Search the open-access literature of the whole world through OpenAlex, beyond "
            "what this deployment ships with. Returns metadata and abstracts only: title, "
            "authors, year, venue, licence, topic and whether the full text can be taken in. "
            "It never returns full text. Anything you state on the strength of a result here "
            "carries the marker [abs:doi] and may not carry a value in kelvin, decibels or "
            "volumetric soil moisture; to state a number, take the paper in with ingest_paper "
            "and cite the section you read."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for, in words. Not a boolean expression.",
                },
                "from_year": {
                    "type": "integer",
                    "description": "Only papers published in or after this year.",
                },
                "limit": {"type": "integer", "description": "How many candidates, at most 10."},
            },
            "required": ["query"],
        },
    },
}

INGEST_SPEC = {
    "type": "function",
    "function": {
        "name": "ingest_paper",
        "description": (
            "Take the full text of one paper into this conversation, by DOI or an application "
            "uploaded PDF. The "
            "paper is split into sections and becomes readable with read_literature and "
            "citable as [slug#id], exactly like a bundled paper, and the run trace records "
            "that it arrived here rather than shipping with the system. Give only a DOI when "
            "using the model tool; uploaded PDFs are passed by the application. A few papers "
            "per conversation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "doi": {
                    "type": "string",
                    "description": "A DOI, for example 10.5194/tc-18-3971-2024.",
                },
                "file_path": {
                    "type": "string",
                    "description": "Internal application path for a user-uploaded PDF; normally supplied by the UI, not invented by the model.",
                },
            },
            "required": [],
        },
    },
}

SPECS.append(LIST_MODELS_SPEC)
SPECS.append(RUN_MODEL_SPEC)
SPECS.append(RUN_PLANNED_MODEL_SPEC)
SPECS.append(READ_REFERENCE_SPEC)
SPECS.append(PLOT_SPEC)
SPECS.append(DISCOVER_SPEC)
SPECS.append(INGEST_SPEC)

RESEARCH_PLAN_SPEC = {
    "type": "function",
    "function": {
        "name": "research_plan",
        "description": (
            "Submit and control a reviewed research workflow. Analyse the user's actual question "
            "first, then call action=propose with your own structured plan. No question-specific "
            "templates exist. The user must review or revise the plan, inspect pseudo-data, choose "
            "a chart, and approve formal execution. Approval actions are deliberately unavailable "
            "to the language model and are recorded only by the human UI. Pseudo-data are display "
            "demonstrations only, never scientific evidence. When the user requests a revision, "
            "call action=revise_plan with changes that update every affected run and chart, not "
            "only the pseudo-preview labels; the backend creates a new plan version and returns "
            "to human plan review. The returned protocol_yaml is a session-scoped, generated "
            "research protocol; it is not loaded from a paper protocol file. For paper "
            "reproduction, the proposal must include opened literature evidence, explicit "
            "reproduction targets with reference-model identities, selected models, "
            "paper-to-model parameter mappings and "
            "target coverage. Keep initial proposals concise enough to fit one tool call. "
            "For revise_plan, send only the affected fields in changes; the backend retains "
            "unchanged runs, charts, evidence, and mappings."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["propose", "status", "revise_plan", "preview", "choose_chart", "complete"]},
                "question": {"type": "string"},
                "objective": {"type": "string"},
                "hypothesis": {"type": "string"},
                "steps": {"type": "array", "items": {"type": "string"}},
                "parameters": {"type": "object"},
                "paper_conditions": {
                    "type": "object",
                    "description": "Paper reference conditions for comparison context. They are not model-validity constraints; legality comes from the registered model declaration and model instruction.",
                },
                "condition_provenance": {
                    "type": "object",
                    "description": "For each paper condition, identify its evidence marker or say agent-assumption/user-question.",
                },
                "literature_evidence": {
                    "type": "array",
                    "description": "Opened paper section, figure, table, or result references and the role each plays in the reproduction.",
                    "items": {"type": "object"},
                },
                "reproduction_targets": {
                    "type": "array",
                    "description": "Paper figures, tables, or results to reproduce. Include reference_models and requested_outputs so coverage cannot be satisfied by a different local model.",
                    "items": {"type": "object"},
                },
                "selected_models": {
                    "type": "array",
                    "description": "Models selected after list_models/read_model_instruction, with purpose and capability status.",
                    "items": {"type": "object"},
                },
                "parameter_mapping": {
                    "type": "array",
                    "description": "Map every paper concept to an exact registered model input and model. provenance_class must be paper_explicit, paper_inferred, user_specified, model_assumption, or backend_default.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string", "description": "Registered model declaring this input."},
                            "paper_concept": {"type": "string"},
                            "paper_value": {},
                            "model_input": {"type": "string", "description": "Exact input name returned by list_models."},
                            "mapped_value": {},
                            "units": {"type": "string"},
                            "provenance_class": {"type": "string"},
                            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                            "confidence_basis": {"type": "string"},
                            "evidence_ref": {"type": "string"},
                            "rationale": {"type": "string"},
                        },
                    },
                },
                "outputs": {
                    "type": "array",
                    "description": "Model outputs used to compare the planned runs with the paper targets.",
                    "items": {"type": "string"},
                },
                "runs": {
                    "type": "array",
                    "description": "Every distinct registered physical-model run required by the plan.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "label": {"type": "string"},
                            "model": {"type": "string"},
                            "parameters": {"type": "object"},
                            "stage": {
                                "type": "string",
                                "description": "baseline, main, diagnostic, sensitivity, or robustness.",
                            },
                        },
                        "required": ["id", "label", "model", "parameters"],
                    },
                },
                "charts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "label": {"type": "string"},
                            "kind": {"type": "string"},
                            "x": {"type": "string"},
                            "y": {"type": "string"},
                            "ys": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Compatible output columns sharing one unit, e.g. tb_v and tb_h.",
                            },
                            "required": {
                                "type": "boolean",
                                "description": "True for a required scientific result or diagnostic figure.",
                            },
                            "purpose": {
                                "type": "string",
                                "description": "result, baseline, validation, diagnostic, sensitivity, or uncertainty.",
                            },
                            "x_label": {"type": "string"},
                            "y_label": {"type": "string"},
                        },
                        "required": ["id", "label", "x", "y"],
                    },
                },
                "success_criteria": {"type": "array", "items": {"type": "string"}},
                "quantities": {"type": "array", "items": {"type": "string"}},
                "controls": {"type": "array", "items": {"type": "string"}},
                "metrics": {"type": "array", "items": {"type": "string"}},
                "diagnostics": {"type": "array", "items": {"type": "string"}},
                "stop_conditions": {"type": "array", "items": {"type": "string"}},
                "baseline_run_id": {
                    "type": "string",
                    "description": "ID of the planned run serving as the baseline/smoke validation.",
                },
                "assumptions": {"type": "array", "items": {"type": "string"}},
                "limitations": {"type": "array", "items": {"type": "string"}},
                "chart_id": {"type": "string"},
                "note": {"type": "string"},
                "changes": {
                    "type": "object",
                    "description": (
                        "User-requested plan changes. Include complete affected runs and charts "
                        "when changing a sweep, output, axis, or figure. Update paper_conditions "
                        "and condition_provenance only when explicitly changing the source reference; "
                        "paper conditions are comparison context, not model-validity constraints. Update "
                        "reproduction_targets and parameter_mapping when changing evidence, targets, "
                        "or paper-to-model translation; do not edit pseudo-data as if it were a "
                        "model result. For a focused revision, omit unchanged fields and do not "
                        "resend the complete protocol."
                    ),
                },
            },
            "required": ["action"],
        },
    },
}

PLOT_PLANNED_CHART_SPEC = {
    "type": "function",
    "function": {
        "name": "plot_planned_chart",
        "description": (
            "Render one selected human-approved research chart by chart_id. The backend "
            "collects every compatible successful planned run, expands multi-output charts "
            "such as V/H polarization, and supplies exact handles and axes to the renderer. "
            "Use this after run_planned_model; do not manually rebuild its series list."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "chart_id": {
                    "type": "string",
                    "description": "Exact id from the approved selected chart package.",
                },
                "action": {
                    "type": "string",
                    "enum": ["render", "review"],
                    "description": "Render first; after it is on screen, call again with review.",
                },
            },
            "required": ["chart_id"],
        },
    },
}
SPECS.append(PLOT_PLANNED_CHART_SPEC)
SPECS.append(RESEARCH_PLAN_SPEC)

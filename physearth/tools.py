import time

from physearth import knowledge, validation
from physearth.models import registry

OUTPUT_BUDGET_CHARS = 16000
MAX_RUN_SECONDS = 45.0

SPECS = [
    {
        "type": "function",
        "function": {
            "name": "list_literature",
            "description": (
                "Search the bundled open-access literature corpus. Returns one card per paper "
                "with its slug, title, scenarios, outputs and a one-line description. Use it to "
                "decide which paper to read; it never returns paper text."
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


SPECS.append(LIST_MODELS_SPEC)
SPECS.append(RUN_MODEL_SPEC)


def _ok(summary, data, citations=None, qc=None):
    return {
        "status": "success",
        "summary": summary,
        "data": data,
        "citations": citations or [],
        "qc": qc,
        "error": None,
    }


def _fail(message, data=None):
    return {
        "status": "terminal_error",
        "summary": message,
        "data": data or {},
        "citations": [],
        "qc": None,
        "error": message,
    }


def list_literature(query="", scenario=""):
    hits = knowledge.search(query, scenario)
    if not hits:
        return _fail(
            "No paper matches query=%r scenario=%r. The corpus has %d papers; call with no "
            "arguments to see all of them." % (query, scenario, len(knowledge.slugs()))
        )
    return _ok("%d of %d papers match." % (len(hits), len(knowledge.slugs())), {"papers": hits})


def read_literature(slug, section_id=None):
    item = knowledge.card(slug)
    if not item:
        return _fail(
            "Unknown slug %r. Available slugs: %s." % (slug, ", ".join(knowledge.slugs()))
        )
    if section_id in (None, ""):
        return _ok(
            "Section index for %s. Call again with a section_id to read one." % slug,
            {
                "slug": slug,
                "title": item["title"],
                "doi": item["doi"],
                "license": item["license"],
                "sections": knowledge.section_index(slug),
            },
        )
    section = knowledge.read_section(slug, section_id)
    if not section:
        available = ", ".join(s["id"] for s in knowledge.section_index(slug))
        return _fail(
            "Section %r not found in %s. Available section ids: %s." % (section_id, slug, available)
        )
    text = section["text"]
    truncated = False
    if len(text) > OUTPUT_BUDGET_CHARS:
        text = text[:OUTPUT_BUDGET_CHARS] + "\n\n[truncated at output budget]"
        truncated = True
    return _ok(
        "%s section %s: %s (%d chars%s)"
        % (slug, section["section_id"], section["title"], len(text), ", truncated" if truncated else ""),
        {
            "slug": slug,
            "section_id": section["section_id"],
            "title": section["title"],
            "citation_key": section["citation_key"],
            "text": text,
        },
        citations=[section["citation_key"]],
    )


def list_models(model=None):
    if model in (None, ""):
        rows = registry.summary()
        rejected = registry.rejected()
        return _ok(
            "%d registered model(s), %d rejected." % (len(rows), len(rejected)),
            {"models": rows, "rejected": rejected},
        )
    entry = registry.get(model)
    if entry is None:
        return _fail(
            "Unknown model %r. Registered models: %s." % (model, ", ".join(registry.names()) or "none")
        )
    card = entry.card
    return _ok(
        "Capability declaration for %s v%s." % (card["name"], card["version"]),
        {
            "name": card["name"],
            "version": card["version"],
            "tier": card["tier"],
            "runnable_here": entry.runnable,
            "citation": card["citation"],
            "license": card["license"],
            "parameters": card["parameters"],
            "combinations": card.get("combinations") or [],
            "outputs": card["outputs"],
            "resource_profile": card.get("resource_profile") or {},
        },
    )


def run_model(model, parameters=None, **extra):
    parameters = dict(parameters or {})
    parameters.update(extra)
    entry = registry.get(model)
    if entry is None:
        return _fail(
            "Unknown model %r. Registered models: %s." % (model, ", ".join(registry.names()) or "none")
        )
    if not entry.runnable:
        return _fail(
            "%s is registered but its tier is %r, so it cannot run in this environment. "
            "Deploy it locally to use it." % (model, entry.tier)
        )

    spec, problems = validation.resolve(entry.card, parameters or {})
    if problems:
        return {
            "status": "needs_input",
            "summary": "The call was rejected before running %s: %d problem(s)." % (model, len(problems)),
            "data": {"model": model, "rejected_parameters": parameters or {}, "problems": problems},
            "citations": [],
            "qc": None,
            "error": "; ".join(problems),
        }

    started = time.perf_counter()
    try:
        result = entry.run(spec)
    except Exception as exc:
        return _fail(
            "%s raised %s: %s" % (model, type(exc).__name__, exc),
            {"model": model, "spec": spec},
        )
    elapsed = time.perf_counter() - started

    qc = validation.quality_control(entry.card, result)
    axis = result.get("axis")
    summary = "%s ran in %.2fs: %d point(s)%s. Quality control %s." % (
        model,
        elapsed,
        len(result.get("points") or []),
        " over %s" % axis["name"] if axis else "",
        "passed" if qc["passed"] else "FAILED",
    )
    return _ok(
        summary,
        {
            "model": model,
            "version": entry.card["version"],
            "spec": spec,
            "axis": axis,
            "series": result.get("series"),
            "points": result.get("points"),
            "units": {name: item["unit"] for name, item in entry.card["outputs"].items()},
            "elapsed_s": round(elapsed, 3),
        },
        qc=qc,
    )


DISPATCH = {
    "list_literature": list_literature,
    "read_literature": read_literature,
    "list_models": list_models,
    "run_model": run_model,
}


def call(name, arguments):
    handler = DISPATCH.get(name)
    if handler is None:
        return _fail("Unknown tool %r. Available tools: %s." % (name, ", ".join(DISPATCH)))
    try:
        return handler(**arguments)
    except TypeError as exc:
        return _fail("Bad arguments for %s: %s" % (name, exc))

from physearth import knowledge

OUTPUT_BUDGET_CHARS = 16000

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


def _ok(summary, data, citations=None):
    return {
        "status": "success",
        "summary": summary,
        "data": data,
        "citations": citations or [],
        "qc": None,
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


DISPATCH = {
    "list_literature": list_literature,
    "read_literature": read_literature,
}


def call(name, arguments):
    handler = DISPATCH.get(name)
    if handler is None:
        return _fail("Unknown tool %r. Available tools: %s." % (name, ", ".join(DISPATCH)))
    try:
        return handler(**arguments)
    except TypeError as exc:
        return _fail("Bad arguments for %s: %s" % (name, exc))

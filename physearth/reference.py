import json
import statistics
from pathlib import Path

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "reference"
MAX_SAMPLE_ROWS = 20

_CACHE = None


def _load():
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    datasets = {}
    if REFERENCE_DIR.is_dir():
        for card_path in sorted(REFERENCE_DIR.glob("*/dataset_card.json")):
            card = json.loads(card_path.read_text(encoding="utf-8"))
            card["_dir"] = card_path.parent
            datasets[card["slug"]] = card
    _CACHE = datasets
    return _CACHE


def slugs():
    return list(_load())


def card(slug):
    return _load().get(slug)


def catalogue():
    return [
        {
            "slug": slug,
            "title": item["title"],
            "description": " ".join(item["description"].split()),
            "license": item["license"],
            "columns": sorted(item["columns"]),
        }
        for slug, item in _load().items()
    ]


def catalogue_block():
    return "\n".join(
        "- %s (%s)\n  %s\n  columns: %s"
        % (entry["slug"], entry["license"], entry["description"], ", ".join(entry["columns"]))
        for entry in catalogue()
    )


def _table(slug):
    item = _load()[slug]
    if "_table" not in item:
        item["_table"] = json.loads((item["_dir"] / "data.json").read_text(encoding="utf-8"))
    return item["_table"]


def _column_values(table, name):
    column = table["columns"][name]
    if column["kind"] == "categorical":
        levels = column["levels"]
        return [levels[code] for code in column["codes"]]
    return column["values"]


def query(slug, filters=None):
    """Return (indices, problems). Filters are exact matches or [min, max] for numerics."""
    table = _table(slug)
    columns = table["columns"]
    problems = []
    keep = list(range(table["n_rows"]))

    for name, wanted in (filters or {}).items():
        if name not in columns:
            problems.append(
                "%s is not a column of %s. Columns: %s." % (name, slug, ", ".join(sorted(columns)))
            )
            continue
        values = _column_values(table, name)
        if columns[name]["kind"] == "categorical":
            allowed = wanted if isinstance(wanted, list) else [wanted]
            allowed = [str(v) for v in allowed]
            unknown = [v for v in allowed if v not in columns[name]["levels"]]
            if unknown:
                problems.append(
                    "%s has no value %s. Available: %s."
                    % (name, ", ".join(unknown), ", ".join(map(str, columns[name]["levels"][:12])))
                )
                continue
            keep = [i for i in keep if values[i] in allowed]
        else:
            if not (isinstance(wanted, list) and len(wanted) == 2):
                problems.append("%s is numeric, so give a range as [min, max]." % name)
                continue
            low, high = wanted
            keep = [i for i in keep if low <= values[i] <= high]
    return keep, problems


def summarise(slug, indices):
    table = _table(slug)
    item = _load()[slug]
    summary = {}
    for name, column in table["columns"].items():
        values = [_column_values(table, name)[i] for i in indices]
        entry = {"unit": item["columns"][name]["unit"], "source": item["columns"][name]["source"]}
        if not values:
            entry["note"] = "no rows"
        elif column["kind"] == "categorical":
            unique = sorted(set(values))
            entry["unique"] = len(unique)
            entry["values"] = unique[:12]
        else:
            entry["min"] = round(min(values), 3)
            entry["max"] = round(max(values), 3)
            entry["mean"] = round(statistics.fmean(values), 3)
            if len(values) > 1:
                entry["stdev"] = round(statistics.stdev(values), 3)
        summary[name] = entry
    return summary


def sample(slug, indices, limit=MAX_SAMPLE_ROWS):
    table = _table(slug)
    names = list(table["columns"])
    columns = {name: _column_values(table, name) for name in names}
    step = max(1, len(indices) // limit) if indices else 1
    picked = indices[::step][:limit]
    return [{name: columns[name][i] for name in names} for i in picked]


def columns(slug, indices):
    """Full column arrays for the matching rows, for the plot renderer only."""
    table = _table(slug)
    return {
        name: [_column_values(table, name)[i] for i in indices] for name in table["columns"]
    }


def provenance(slug):
    item = _load()[slug]
    return {
        "license": item["license"],
        "citation": item["citation"],
        "paper_doi": item["paper"],
        "corpus_slug": item.get("corpus_slug"),
        "sources": item["sources"],
        "derivation": item["derivation"],
    }

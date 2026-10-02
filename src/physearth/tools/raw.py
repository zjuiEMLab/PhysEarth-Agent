"""Minimal raw-PDF and upstream-SMRT interfaces for the controlled baseline."""

import base64
import concurrent.futures
import importlib
import importlib.metadata
import math
import sys
from pathlib import Path

from physearth.corpus import knowledge
from physearth.harness import results, untrusted
from physearth.tools.common import _fail, _ledger, _ok

MAX_PAGE_TEXT_CHARS = 16000
MAX_PAGE_IMAGE_BYTES = 2_000_000
MAX_RAW_RUN_SECONDS = 45.0


def _paper_for_doi(doi):
    wanted = str(doi or "").strip().lower()
    for slug in knowledge.slugs():
        card = knowledge.card(slug)
        if str((card or {}).get("doi") or "").strip().lower() == wanted:
            return card
    return None


def read_raw_paper(doi, page, include_image=True, _session=None):
    """Return one uncurated PDF page, never the structured corpus representation."""
    card = _paper_for_doi(doi)
    if card is None:
        return _fail(f"No bundled raw PDF matches DOI {doi!r}.")
    raw_path = card.get("raw_pdf_path")
    path = (Path(card["_dir"]) / str(raw_path or "")).resolve()
    if not raw_path or not path.is_file():
        return _fail("The paper is known, but its publisher PDF is not bundled for raw access.")
    try:
        import fitz
    except ImportError:
        return _fail("Raw PDF reading requires PyMuPDF.")

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        return _fail("page must be a one-based integer.")
    with fitz.open(str(path)) as document:
        if page_number < 1 or page_number > document.page_count:
            return _fail(f"Page {page_number} is outside this {document.page_count}-page PDF.")
        pdf_page = document.load_page(page_number - 1)
        raw_text = (pdf_page.get_text("text") or "").strip()
        truncated = len(raw_text) > MAX_PAGE_TEXT_CHARS
        raw_text = raw_text[:MAX_PAGE_TEXT_CHARS]
        data = {
            "doi": str(doi).strip(),
            "page": page_number,
            "page_count": document.page_count,
            "text": untrusted.wrap(
                raw_text,
                f"raw-pdf:{str(doi).strip()}#page-{page_number}",
                "publisher PDF page text",
            ),
            "text_truncated": truncated,
            "source": card.get("raw_pdf_source_uri") or card.get("url"),
        }
        if include_image:
            # Render the whole page. Nothing detects, crops, captions, or labels figures.
            pixmap = pdf_page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            payload = pixmap.tobytes("png")
            if len(payload) <= MAX_PAGE_IMAGE_BYTES:
                encoded = base64.b64encode(payload).decode("ascii")
                data["image_data_url"] = f"data:image/png;base64,{encoded}"
                data["page_image_attached"] = True
            else:
                data["page_image_attached"] = False
                data["image_note"] = "Rendered page exceeds the bounded vision payload."

    reference = f"{str(doi).strip()}#page-{page_number}"
    if _session is not None:
        _session.setdefault("raw_pdf_pages_read", set()).add(reference)
    _ledger(
        _session,
        "raw_pdf_page",
        {
            "reference": reference,
            "doi": str(doi).strip(),
            "page": page_number,
            "source": data["source"],
            "page_image_attached": data.get("page_image_attached", False),
        },
    )
    attachment = " with its page image" if data.get("page_image_attached") else ""
    return _ok(
        f"Read raw publisher PDF page {page_number} of {data['page_count']}{attachment}.",
        data,
    )


def _finite_number(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _raw_smrt_curve(recipe):
    # SMRT 1.5.1's optional Numba cache cannot load on Python 3.13. Use SMRT's own NumPy
    # fallback during its first import, without involving the registered adapter or card.
    if sys.version_info >= (3, 13) and "smrt.core.lib" not in sys.modules:
        missing = object()
        previous = sys.modules.get("numba", missing)
        sys.modules["numba"] = None
        try:
            importlib.import_module("smrt.core.lib")
        finally:
            if previous is missing:
                sys.modules.pop("numba", None)
            else:
                sys.modules["numba"] = previous
    from smrt import make_snow_layer, sensor_list
    from smrt.core.plugin import import_class

    em_name = str(recipe["electromagnetic_model"]).strip()
    micro_name = str(recipe["microstructure_model"]).strip()
    frequency = _finite_number(recipe["frequency_ghz"], "frequency_ghz")
    radius = _finite_number(recipe["radius_m"], "radius_m")
    densities = [
        _finite_number(value, "densities_kg_m3")
        for value in recipe["densities_kg_m3"]
    ]
    if not densities or len(densities) > 60:
        raise ValueError("densities_kg_m3 must contain between 1 and 60 values")

    sensor = sensor_list.passive(frequency * 1e9, 55)
    values = []
    for density in densities:
        layer_kwargs = {"radius": radius}
        microstructure_parameters = recipe.get("microstructure_parameters") or {}
        if not isinstance(microstructure_parameters, dict):
            raise ValueError("microstructure_parameters must be an object")
        for name, value in microstructure_parameters.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("microstructure parameter names must be non-empty strings")
            layer_kwargs[name] = _finite_number(value, f"microstructure_parameters.{name}")
        # Accept old raw-evaluation records that placed stickiness at the recipe root.
        if "stickiness" in recipe and "stickiness" not in layer_kwargs:
            layer_kwargs["stickiness"] = _finite_number(recipe["stickiness"], "stickiness")
        if "temperature_k" in recipe:
            layer_kwargs["temperature"] = _finite_number(
                recipe["temperature_k"], "temperature_k"
            )
        layer = make_snow_layer(
            _finite_number(recipe.get("thickness_m", 1.0), "thickness_m"),
            micro_name,
            density,
            **layer_kwargs,
        )
        model = import_class("emmodel", em_name)(sensor, layer)
        coefficient = getattr(model, "_ks", None)
        if coefficient is None:
            raise RuntimeError("upstream SMRT model did not expose a scattering coefficient")
        values.append(float(coefficient))
    return {
        "axis": {"name": "density_kg_m3", "values": densities},
        "points": [
            {"index": index, "density_kg_m3": density, "ks_per_m": value}
            for index, (density, value) in enumerate(zip(densities, values, strict=True))
        ],
        "series": {"ks_per_m": values},
    }


def run_raw_smrt(recipe, _owner=None, _session=None):
    """Execute a structurally bounded but scientifically unassisted SMRT recipe."""
    if _session is None or not _session.get("evaluation_batch_approved"):
        return {
            "status": "needs_input",
            "summary": (
                "Raw SMRT execution requires the recorded human approval for this "
                "evaluation batch."
            ),
            "data": {"error_code": "evaluation_batch_approval_required"},
            "citations": [],
            "qc": None,
            "ui": None,
            "error": "evaluation batch approval required",
        }
    if not isinstance(recipe, dict):
        return _fail("recipe must be an object.")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        output = executor.submit(_raw_smrt_curve, dict(recipe)).result(
            timeout=MAX_RAW_RUN_SECONDS
        )
    except concurrent.futures.TimeoutError:
        return _fail("Raw SMRT recipe exceeded the 45 second execution limit.")
    except Exception as exc:
        return _fail(
            f"Upstream SMRT rejected the raw recipe with {type(exc).__name__}: {exc}",
            {"error_type": type(exc).__name__},
        )
    finally:
        executor.shutdown(wait=False)

    version = importlib.metadata.version("smrt")
    units = {"ks_per_m": "m-1"}
    handle = results.put(
        {
            "model": "smrt",
            "version": version,
            "spec": dict(recipe),
            "axis": output["axis"],
            "series": output["series"],
            "points": output["points"],
            "units": units,
            "diagnostics": {"interface": "raw_upstream_smrt"},
        },
        _owner,
    )
    return _ok(
        f"Raw upstream SMRT recipe returned {len(output['points'])} "
        "scattering-coefficient points.",
        {
            "model": "smrt",
            "version": version,
            "spec": dict(recipe),
            "handle": handle,
            "n_points": len(output["points"]),
            "axis": {"name": "density_kg_m3"},
            "series_summary": results.summarise_series(output["series"], units),
            "preview": results.preview(output["points"]),
            "units": units,
            "note": f"Full arrays remain in the result store under {handle}.",
        },
        qc={
            "passed": all(
                math.isfinite(value) and value >= 0
                for value in output["series"]["ks_per_m"]
            ),
            "problems": [],
        },
    )

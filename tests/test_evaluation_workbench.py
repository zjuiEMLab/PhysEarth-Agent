from pathlib import Path

from physearth import evaluation, live, tools
from physearth.models import registry


def test_temporary_evaluation_guideline_is_session_scoped():
    box = evaluation.new_session("llm-test")
    item = evaluation.attach_guideline(
        box,
        "smrt",
        "Use the declared output units and report the tested validity range.",
        "2.0",
    )
    assert item["status"] == "success"
    read = tools.call("read_model_instruction", {"model": "smrt"}, session=box)
    assert read["status"] == "success"
    assert read["data"]["version"] == "2.0"
    evaluation.clear(box)
    assert not box


def test_temporary_model_overlay_can_run_without_global_registration(tmp_path):
    source = Path(__file__).resolve().parent.parent / "examples" / "toy_model"
    copied = tmp_path / "toy_model"
    copied.mkdir()
    for name in ("model_card.yaml", "adapter.py"):
        (copied / name).write_bytes((source / name).read_bytes())
    box = evaluation.new_session("llm-test")
    model = registry.register_session_directory(box, copied)
    assert model.name in registry.names(session=box)
    assert model.name not in registry.names()
    result = tools.call(
        "run_model",
        {"model": model.name, "parameters": {"optical_depth": 1.0}},
        session=box,
    )
    assert result["status"] == "success"
    evaluation.clear(box)
    assert model.name not in registry.names(session=box)


def test_evaluation_paper_ingestion_skips_project_artifacts():
    box = evaluation.new_session("llm-test")
    record = {
        "front": {"title": "Temporary paper", "license": "unknown"},
        "doi": "",
        "source": "pdf_upload",
        "url": "",
        "sections": [("Page 1", "Temporary text")],
        "figures": [],
        "tables": [],
        "filename": "temporary.pdf",
    }
    card = live.add(box, record, persist=False)
    assert "artifact" not in card
    assert card["slug"] in box["corpus"]
    evaluation.clear(box)

"""Archived with evaluation/runners/dashboard.py and registration_demo.py."""

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
EVALUATION = ROOT / "evaluation"
sys.path.insert(0, str(EVALUATION / "runners"))


def _runner(name):
    path = EVALUATION / "runners" / (name + ".py")
    spec = importlib.util.spec_from_file_location("tier0_%s" % name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dashboard_explains_registration_and_holds_paper_reproduction():
    dashboard = _runner("dashboard")
    tier0 = json.loads((EVALUATION / "results" / "tier0.json").read_text(encoding="utf-8"))
    registry = json.loads(
        (EVALUATION / "results" / "registry_contract.json").read_text(encoding="utf-8")
    )
    demo = json.loads(
        (EVALUATION / "results" / "registration_demo.json").read_text(encoding="utf-8")
    )
    page = dashboard.build_html([], tier0, registry, demo=demo)
    assert 'id="registration"' in page
    assert 'id="paper"' in page
    assert "ProSAIL" in page
    assert "pywatershed" in page
    assert "SMRT" in page
    assert "OpenRouter" not in page
    assert "ModelScope" not in page
    assert "usage ledger" not in page.lower()
    assert "smoke" not in page.lower()
    assert "tier 0" not in page.lower()
    assert "tier 1" not in page.lower()
    assert "tier 2" not in page.lower()

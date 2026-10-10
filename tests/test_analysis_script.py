"""run_analysis_script: the agent writes the analysis, a person approves the code."""

import json
import threading
import time

import pytest
from test_approval import _call_chunk, _Chunk, _Delta, _fake_client

from physearth import agent, session, tools
from physearth.harness import approval
from physearth.tools import analysis

ROOT_FINDING = '''
import numpy as np
from scipy.optimize import brentq

def ks(density):
    return run_model("smrt", output="coefficients", density_kg_m3=density,
                     radius_m=1e-4, microstructure_model="independent_sphere",
                     electromagnetic_model="rayleigh")["outputs"]["ks_per_m"]

target = ks(250.0)
found = brentq(lambda d: ks(d) - target, 100.0, 400.0, xtol=1e-3)
save_series("density_that_matches", [1.0], {"density": [found]}, x_name="point")
print("found", round(found, 2))
'''


def _approved(code, box=None):
    box = box or session.new_session("m")
    box.setdefault("approved_scripts", set()).add(analysis.code_hash(code))
    return box


def _run(code, box, **arguments):
    return tools.call(
        "run_analysis_script", {"code": code, "purpose": "test", **arguments},
        owner=box["id"], session=box,
    )


def test_a_script_that_was_not_approved_does_not_run():
    box = session.new_session("m")
    result = _run("print(1)", box)
    assert result["status"] == "needs_input"
    assert result["data"]["error_code"] == "script_approval_required"
    assert not box.get("analysis_runs")


def test_the_model_cannot_approve_its_own_script_through_arguments():
    box = session.new_session("m")
    result = tools.call(
        "run_analysis_script",
        {"code": "print(1)", "purpose": "x", "_session": {"approved_scripts": {analysis.code_hash("print(1)")}}},
        owner=box["id"], session=box,
    )
    assert result["status"] == "needs_input"


def test_an_approved_script_can_solve_for_an_input_through_the_registered_model():
    box = _approved(ROOT_FINDING)
    result = _run(ROOT_FINDING, box)
    assert result["status"] == "success", result
    data = result["data"]
    assert data["model_runs"] > 3
    assert "smrt@" in data["models_run"][0]
    assert "found 250" in data["stdout"] or "found 249" in data["stdout"]
    handle = data["saved_results"][0]["handle"]
    from physearth.harness import results

    stored = results.get(handle, box["id"])
    assert abs(stored["series"]["density"][0] - 250.0) < 1.0
    assert box["analysis_runs"][0]["code"] == ROOT_FINDING


def test_a_change_to_the_code_after_approval_is_not_approved():
    box = _approved("print(1)")
    assert _run("print(2)", box)["status"] == "needs_input"


def test_a_model_the_script_names_that_is_refused_comes_back_as_an_error_it_can_handle():
    code = 'run_model("smrt", density_kg_m3=5000)\\n'.replace("\\n", "\n")
    box = _approved(code)
    result = _run(code, box)
    assert result["status"] == "terminal_error"
    assert result["data"]["error_code"] == "script_failed"


def test_a_syntax_error_is_reported_without_running():
    box = _approved("def (:\n")
    assert _run("def (:\n", box)["data"]["error_code"] == "script_syntax"


def test_a_package_that_is_not_installed_must_be_named():
    code = "import a_package_nobody_has\n"
    result = _run(code, _approved(code))
    assert result["data"]["error_code"] == "script_package_missing"
    assert "requirements" in result["summary"]


def test_a_requirement_that_is_not_a_plain_package_is_refused():
    code = "import a_package_nobody_has\n"
    result = _run(code, _approved(code), requirements=["git+https://example.invalid/x", "--index-url=http://x"])
    assert result["data"]["error_code"] == "script_requirement_rejected"


def test_an_approved_package_is_installed_into_the_session_folder_only(monkeypatch):
    code = "import a_package_nobody_has\n"
    seen = {}

    def fake_install(requirements, target):
        seen["requirements"], seen["target"] = list(requirements), target
        return True, ""

    monkeypatch.setattr(analysis, "_install", fake_install)
    box = _approved(code)
    result = _run(code, box, requirements=["a-package-nobody-has>=1.0"])
    assert seen["requirements"] == ["a-package-nobody-has>=1.0"]
    assert str(box["id"]) in str(seen["target"])
    assert result["data"]["error_code"] == "script_package_missing"  # the fake installed nothing


def test_a_script_that_runs_too_long_is_killed(monkeypatch):
    monkeypatch.setattr(analysis, "MAX_SECONDS", 1.5)
    code = "import time\ntime.sleep(60)\n"
    started = time.monotonic()
    result = _run(code, _approved(code))
    assert result["status"] == "terminal_error"
    assert time.monotonic() - started < 20
    assert "limit" in result["summary"]


def test_a_stop_request_ends_a_running_script():
    code = "import time\ntime.sleep(60)\n"
    box = _approved(code)
    threading.Timer(1.0, lambda: box.__setitem__("stop_requested", True)).start()
    started = time.monotonic()
    result = _run(code, box)
    assert time.monotonic() - started < 15
    assert "stopped" in result["summary"]


def test_network_access_is_refused_to_the_script():
    code = "import socket\ns = socket.socket()\ns.connect(('127.0.0.1', 9))\n"
    result = _run(code, _approved(code))
    assert result["status"] == "terminal_error"
    assert "network" in result["data"]["traceback"]


def test_the_scripts_environment_carries_no_credentials(monkeypatch):
    monkeypatch.setenv("SOME_API_KEY", "secret-value")
    code = "import os\nprint(sorted(k for k in os.environ if 'KEY' in k))\n"
    result = _run(code, _approved(code))
    assert result["status"] == "success"
    assert "SOME_API_KEY" not in result["data"]["stdout"]


def test_the_description_carries_the_code_and_the_missing_packages():
    code = "import a_package_nobody_has\nprint(1)\n"
    described = approval.describe(
        "run_analysis_script",
        {"code": code, "purpose": "find a value", "requirements": ["a-package-nobody-has"]},
        session.new_session("m"),
    )
    assert described["code"] == code
    assert described["inspection"]["missing"] == ["a_package_nobody_has"]
    assert "needing packages" in described["shape"]


def test_the_plugin_does_not_expose_the_script_tool():
    import importlib.util
    import pathlib

    path = pathlib.Path(__file__).resolve().parents[1] / "integrations" / "physearth" / "mcp_server.py"
    spec = importlib.util.spec_from_file_location("physearth_mcp_server_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = {tool["name"] for tool in module._engine_tools()}
    assert "run_analysis_script" not in names and "run_model" in names


def test_the_loop_holds_the_script_for_a_person_and_records_the_approval(monkeypatch):
    code = "print('hello')\n"
    box = session.new_session("m")
    approval.set_mode(box, approval.ASK)
    script = [
        [_call_chunk("run_analysis_script", json.dumps({"code": code, "purpose": "say hello"}))],
        [_Chunk(_Delta(content="done"))],
    ]
    client, _sent = _fake_client(script)
    monkeypatch.setattr(agent.completion, "_client", lambda: client)
    list(agent.stream("say hello with a script", session=box))
    waiting = approval.pending(box)
    assert waiting and waiting["tool"] == "run_analysis_script"
    assert waiting["description"]["code"] == code
    assert not box.get("approved_scripts")  # nothing runs, nothing approved, until a person decides

    assert approval.decide(box, "approve")
    list(agent.stream("Approved the run of an analysis script.", session=box))
    assert analysis.code_hash(code) in box["approved_scripts"]
    assert box["analysis_runs"][0]["sha256"] == analysis.code_hash(code)


def test_a_refused_model_call_tells_the_script_why():
    code = 'run_model("smrt", density_kg_m3=5000)\n'
    result = _run(code, _approved(code))
    assert result["status"] == "terminal_error"
    assert "Problems:" in result["data"]["traceback"] and "density" in result["data"]["traceback"].lower()


def test_a_choice_of_a_script_has_a_limited_number_of_scripts():
    box = session.new_session("m")
    box["script_budget_from"] = 0
    box["analysis_runs"] = [{} for _ in range(analysis.MAX_SCRIPTS_PER_CHOICE)]
    assert analysis.over_budget(box)
    code = "print(1)"
    box.setdefault("approved_scripts", set()).add(analysis.code_hash(code))
    result = tools.call("run_analysis_script", {"code": code, "purpose": "x"}, owner=box["id"], session=box)
    assert result["status"] == "needs_input" and "No more scripts" in result["summary"]
    box["script_budget_from"] = len(box["analysis_runs"])  # a fresh choice resets the count
    assert not analysis.over_budget(box)

"""The shared plugin surface: capabilities, knowledge, prompt stack, one call, one turn."""

import pytest

from integrations.geoai import service


def test_health_reports_the_checkout_capabilities():
    report = service.health()

    assert report["models"] >= 6
    assert report["runnable_models"] >= 6
    assert report["tools"] >= 15
    assert report["knowledge"]["papers"] >= 8
    assert report["knowledge"]["sections"] >= 50
    assert report["knowledge"]["skills"] >= 3
    assert report["knowledge"]["reference_datasets"] >= 1


def test_tools_manifest_is_the_model_facing_catalogue():
    manifest = {item["name"]: item for item in service.tools_manifest()}

    for name in ("list_models", "run_model", "research_plan", "plot", "read_literature"):
        assert name in manifest, name
        assert manifest[name]["description"], name
        assert manifest[name]["parameters"].get("type") == "object", name


def test_models_manifest_carries_the_declaration_a_run_is_validated_against():
    models = {item["name"]: item for item in service.models_manifest()}
    smrt = models["smrt"]

    density = smrt["parameters"]["density_kg_m3"]
    assert density["unit"] == "kg m-3"
    assert density["minimum"] == 1.0 and density["maximum"] == 917.0
    assert "tb_v" in smrt["outputs"]
    assert smrt["outputs"]["tb_v"]["unit"] == "K"
    assert smrt["runnable"] is True
    assert smrt["license"]
    assert len(models) >= 6


def test_knowledge_manifest_addresses_evidence_the_way_citations_do():
    manifest = service.knowledge_manifest()

    smrt = next(item for item in manifest["papers"] if item["slug"] == "smrt-v1")
    assert smrt["sections"], "the bundled SMRT paper must expose its sections"
    assert smrt["citation_key"] == "[smrt-v1#<section>]"
    assert all(item["citation_key"].startswith("[skill:") for item in manifest["skills"])
    assert all(item["citation_key"].startswith("[data:") for item in manifest["reference_datasets"])


def test_prompt_stack_carries_the_evidence_rules_and_the_registry_context():
    stack = service.prompt_stack()

    assert len(stack) > 4000
    lowered = stack.lower()
    assert "citation" in lowered
    assert "smrt" in lowered
    # The registry is rendered into the prompt, so a newly registered model appears here
    # without anyone editing prompt text.
    assert "tau_omega" in lowered or "tau-omega" in lowered


def test_a_host_can_take_the_rules_without_this_agent_identity():
    # A coding-agent host has an identity of its own: injecting "You are PhysEarth, an
    # Earth-science physical-modeling agent" would make its model claim to be this agent while
    # still being asked to do the host's work. The rules are the part that changes behaviour,
    # and the generated context is the part the same session can read through the tools.
    scopes = service.prompt_sections()
    assert set(scopes) == set(service.PROMPT_SCOPES)

    rules = service.prompt_stack(["rules"])
    assert "citation" in rules.lower()
    assert "PhysEarth, an Earth-science" not in rules
    assert "tau_omega" not in rules.lower(), "the registry context is its own scope, not the rules"

    # The default is still everything, in the order the engine's own loop stacks it, so a host
    # that asks for all of it gets byte-identical text to the version before scopes existed.
    assert service.prompt_stack() == "\n\n".join(
        block.strip()
        for scope in service.PROMPT_SCOPES
        for block in scopes[scope]
        if block and block.strip()
    )
    assert len(service.prompt_stack(["identity"])) < len(rules) < len(service.prompt_stack())


def test_an_unknown_prompt_scope_is_an_error_rather_than_an_omission():
    # A silently narrower prompt is the failure this repository treats as the worst kind: it
    # changes answers with nothing in the log.
    with pytest.raises(ValueError) as error:
        service.prompt_stack(["rules", "everything"])
    assert "everything" in str(error.value)
    assert "rules" in str(error.value)


def test_call_runs_a_real_model_and_returns_a_handle():
    created = service.new_session(model="smrt")
    assert created["approval"] == "ask"

    result = service.call(
        "run_model",
        {
            "model": "smrt",
            "parameters": {
                "output": "tb",
                "sweep_parameter": "density_kg_m3",
                "sweep_start": 100,
                "sweep_stop": 300,
                "sweep_points": 3,
            },
        },
        session_id=created["session_id"],
        approve_runs=True,
    )

    assert result["status"] == "success", result
    handle = (result.get("data") or {}).get("handle")
    assert handle, result
    assert (result.get("qc") or {}).get("passed") is True

    seen = service.evidence(created["session_id"])
    assert seen["counts"]["handles"] >= 1
    assert any(item["handle"] == handle for item in seen["handles"])


def test_a_refused_call_comes_back_structured_rather_than_raising():
    created = service.new_session(model="smrt")

    refused = service.call(
        "run_model",
        {"model": "smrt", "parameters": {"density_kg_m3": 2000.0}},
        session_id=created["session_id"],
        approve_runs=True,
    )

    assert refused["status"] in ("terminal_error", "needs_input")
    assert "density" in str(refused).lower()


def test_an_unknown_session_is_named_not_silently_replaced():
    result = service.call("list_models", {}, session_id="ses_does_not_exist")

    assert result["status"] == "terminal_error"
    assert result["error"] == "unknown_session"


def test_ask_without_credentials_refuses_instead_of_inventing_an_answer(monkeypatch):
    monkeypatch.setattr(service.config, "has_token", lambda: False)
    monkeypatch.setattr(service.config, "get", lambda name, default="": default)

    result = service.ask("What is the brightness temperature of snow at 37 GHz?")

    assert result["status"] == "terminal_error"
    assert result["error"] == "no_credentials"


def test_plan_status_explains_the_next_review_action():
    created = service.new_session(model="smrt")
    status = service.plan_status(created["session_id"])

    assert status["status"] == "success"
    assert status["phase"] is None
    assert status["next_action"]

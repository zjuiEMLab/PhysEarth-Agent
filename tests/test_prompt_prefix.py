"""What every request carries, and what is read only when it is needed.

The fixed prefix was about 15,000 tokens on every call, and the six model declarations were
the largest part of it although the plan gate makes the agent call list_models for every
model it plans with anyway. The prompt now names each model; list_models gives the rest.
"""

from physearth import prompt, registry, session, tools
from physearth.corpus import knowledge


def test_the_prompt_names_every_model_without_its_declaration():
    box = session.new_session("m")
    text = prompt.models_section(True, box)
    assert len(text) < 4000
    for name, model in registry.all_models(box).items():
        assert "- %s v%s" % (name, model.card["version"]) in text
        for output in model.card["outputs"]:
            assert output in text
    assert "; default " not in text
    assert "list_models(model=...)" in text


def test_the_declaration_is_one_list_models_call_away():
    box = session.new_session("m")
    result = tools.call("list_models", {"model": "smrt"}, session=box)
    density = result["data"]["parameters"]["density_kg_m3"]
    assert density["minimum"] is not None and density["maximum"] is not None


def test_the_capability_ablation_still_withholds_ranges():
    text = prompt.models_section(False, session.new_session("m"))
    assert "parameters: " in text
    assert "; default " not in text


def test_the_catalogue_keeps_when_to_read_each_source():
    block = knowledge.catalogue_block(compact=True)
    for entry in knowledge.catalogue():
        assert "- %s (" % entry["slug"] in block
    assert len(block) < len(knowledge.catalogue_block())
    assert "Read this" in prompt.catalogue_section()

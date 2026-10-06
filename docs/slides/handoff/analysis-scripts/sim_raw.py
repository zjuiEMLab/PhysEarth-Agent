import json, sys
sys.path.insert(0, ".")
from tests.test_approval import _Chunk, _Delta, _call_chunk, _fake_client
from physearth import agent, session
import yaml
task = yaml.safe_load(open("evaluation/tasks/tier2/smrt-q1-sparse-medium.yaml"))
switches = yaml.safe_load(open("evaluation/configs/no-harness.yaml"))["switches"]
doi = "10.5194/gmd-11-2763-2018"
recipe = lambda em, ms, extra=None: json.dumps({"recipe": {"electromagnetic_model": em, "microstructure_model": ms,
    "frequency_ghz": 37.0, "densities_kg_m3": [1, 25, 50, 75, 96], "radius_m": 1e-4, **({"microstructure_parameters": extra} if extra else {})}})
script = [
    [_call_chunk("read_raw_paper", json.dumps({"doi": doi, "page": 2768, "include_image": True}))],
    [_call_chunk("read_raw_paper", json.dumps({"doi": doi, "page": 8, "include_image": True}))],
    [_Chunk(_Delta(content="I will reproduce Figure 3 by first reading the relevant section..."))],
    [_call_chunk("run_raw_smrt", recipe("rayleigh", "independent_sphere"))],
    [_Chunk(_Delta(content="Here is the answer."))],
    [_call_chunk("plot", "{}")],
    [_Chunk(_Delta(content="Final answer."))],
] + [[_Chunk(_Delta(content="Final answer."))]] * 6
client, sent = _fake_client(script)
agent.completion._client = lambda: client
box = session.new_session("m")
box["research_required"] = False
answer, events, state = agent.run(task["question"], session=box, switches=switches)
print("LLM calls:", len(client.tool_choices))
for i, c in enumerate(client.tool_choices):
    print(i + 1, c if c == "auto" else c["function"]["name"])
for e in events:
    if e.get("kind") in ("tool_call", "raw_workflow_block", "harness_stop", "harness_block", "tool_choice_fallback"):
        print(e.get("kind"), e.get("name") or e.get("tool"), e.get("status"), (e.get("summary") or e.get("detail") or "")[:140])
print("successful_runs:", len(box.get("successful_runs") or []), "pages:", box.get("raw_pdf_pages_read"))

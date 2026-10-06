"""End-to-end raw-baseline dry run: scripted LLM policy, real tools, real SMRT."""
import json, sys, re, pathlib, tempfile
sys.path.insert(0, "."); sys.path.insert(0, "evaluation/runners"); sys.path.insert(0, "evaluation")
from tests.test_approval import _Chunk, _Delta, _call_chunk
import competition, common
from metrics import figure3
from physearth import agent
tmp = pathlib.Path(tempfile.mkdtemp())
REAL_REPO = common.REPO; competition.REPORTS = tmp / "reports"; competition.FIGURES = tmp / "figures"
doi = "10.5194/gmd-11-2763-2018"
dens = [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
cases = [("rayleigh", "independent_sphere", None, "Independent spheres (Rayleigh)"),
         ("iba", "independent_sphere", None, "Independent spheres (IBA)"),
         ("dmrt_qcacp_shortrange", "sticky_hard_spheres", 1000.0, "Non-sticky hard spheres (DMRT QCA-CP)"),
         ("iba", "sticky_hard_spheres", 1000.0, "Non-sticky hard spheres (IBA)"),
         ("dmrt_qcacp_shortrange", "sticky_hard_spheres", 0.15, "Sticky hard spheres (DMRT QCA-CP)"),
         ("iba", "sticky_hard_spheres", 0.15, "Sticky hard spheres (IBA)")]
calls = []
def policy(messages, tool_choice):
    forced = tool_choice if tool_choice == "auto" else tool_choice["function"]["name"]
    calls.append(forced)
    text = json.dumps(messages[-6:])
    handles = re.findall(r"res_[0-9a-f]{12}", json.dumps(messages))
    handles = list(dict.fromkeys(handles))
    pages = sum(1 for m in messages if m.get("role") == "tool" and "raw publisher PDF page" in str(m.get("content")))
    if len(calls) == 1:
        return [_call_chunk("read_raw_paper", json.dumps({"doi": doi, "page": 2768}))]
    if pages == 0:
        return [_call_chunk("read_raw_paper", json.dumps({"doi": doi, "page": 8, "include_image": False}))]
    if len(calls) == 3:
        return [_Chunk(_Delta(content="I will reproduce Figure 3 by first reading the relevant section..."))]
    if len(handles) < 6:
        em, ms, st, _ = cases[len(handles)]
        r = {"electromagnetic_model": em, "microstructure_model": ms, "frequency_ghz": 36.5,
             "densities_kg_m3": dens, "radius_m": 1e-4, "temperature_k": 265.0}
        if st is not None: r["microstructure_parameters"] = {"stickiness": st}
        return [_call_chunk("run_raw_smrt", json.dumps({"recipe": r}))]
    if "plot" not in [c for c in calls[:-1]] and not any("Figure" in str(m.get("content")) and m.get("role") == "tool" for m in messages[-2:]):
        if not any(m.get("role") == "tool" and "plot" in str(m.get("name", "")) for m in messages):
            series = [{"handle": h, "x": "density_kg_m3", "y": "ks_per_m", "label": c[3]} for h, c in zip(handles, cases)]
            return [_call_chunk("plot", json.dumps({"title": "Sparse-medium scattering coefficient comparison",
                "x_label": "Density (kg m-3)", "y_label": "Scattering coefficient (m-1)", "series": series}))]
    return [_Chunk(_Delta(content="Six raw SMRT curves were computed and plotted.\n<parameter_provenance>[]</parameter_provenance>\n<reproduction_outcome>partial</reproduction_outcome>"))]
def create(**kw):
    return policy(kw["messages"], kw.get("tool_choice"))
client = type("C", (), {"chat": type("Chat", (), {"completions": type("X", (), {"create": staticmethod(create)})()})()})()
agent.completion._client = lambda: client
task = competition.load_task_index()["q1-sparse-medium"]
profile = competition.load_profiles(["p1-reproduction-first"])[0]
cfg = [c for c in common.load_configs(["no-harness"])][0]
competition.common.REPO = tmp
record = competition.run_one(task, profile, cfg, "scripted-policy", 1, "sim", batch_approved=True, judge_enabled=False)
print("LLM calls:", len(calls), "forced sequence:", calls)
print("stop_rule:", record.get("stop_rule"), "| tools:", [(t["name"], t["status"]) for t in record["tool_log"]])
print("successful runs:", len(record.get("successful_runs") or []), "| figures:", len(record.get("figures") or []))
competition.common.REPO = REAL_REPO
oracle = figure3.build_oracle()
s = figure3.score(record, oracle)
print("figure status:", s["status"], "| structural:", s.get("structural_passed"))
print("numeric:", [(c["curve"], c.get("normalized_rmse")) for c in s["numeric"]["curves"]])
print("recipe:", [(c["curve"], c.get("experiment_exact"), c.get("axis_exact")) for c in s["recipe"]["curves"]])

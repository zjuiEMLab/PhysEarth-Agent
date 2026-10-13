"""Probe a registered model's physical expectations and record the evidence.

The probe stage of the model registration forge (docs/enhancements/model-registration-forge.md).
It runs the registered adapter, through the same validation the agent's calls go through, over
a grid of regimes, and writes what it finds to evaluation/results/<model>_forge_probe.json:

  grid       every expectation in the card's `physics` section, checked across frequencies,
             grain sizes, microstructures and grounds; for each expectation, how many runs
             it applied to, how many met it, and the cells that did not
  findings   the named findings in model_card.provenance.yaml, each reproduced by one probe,
             so a reviewer can re-run the number a finding quotes

A contradiction in the grid is not a failure of the probe. Some expectations are written to
warn on any departure (TB rising with SWE), and the contradicting cells are then the evidence
for the cases the warning's reason lists. The JSON says which.

    python onboarding/forge_probe.py smrt

Read-only apart from the output file. SMRT only for now: the grid and the findings name SMRT
parameters; a second model needs its own grid.
"""

import argparse
import contextlib
import io
import itertools
import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from physearth import registry  # noqa: E402
from physearth.harness import validation  # noqa: E402

PASSIVE_GHZ = (10.65, 18.7, 37.0, 89.0)
ACTIVE_GHZ = (5.4, 13.5, 17.2)
GRAINS = {
    "exponential": ("corr_length_m", (5e-5, 1e-4, 1.5e-4, 2.5e-4, 4e-4)),
    "sticky_hard_spheres": ("radius_m", (5e-5, 1e-4, 2e-4, 3e-4, 5e-4)),
}
DEPTH = {"sweep_parameter": "thickness_m", "sweep_start": 0.05, "sweep_stop": 2.0, "sweep_points": 8}


class Probe:
    def __init__(self, model):
        self.entry = registry.get(model)
        self.card = self.entry.card

    def run(self, **arguments):
        """Validate and run; return (spec, result, expectation checks, SMRT's printed warnings)."""
        spec, problems = validation.resolve(self.card, arguments)
        if problems:
            raise ValueError("; ".join(problems))
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = self.entry.run(spec)
        checks = validation.expectation_checks(self.card, spec, result)
        # SMRT prints solver diagnostics (DORT eigenvalues) as well as validity warnings; only
        # the warnings say the model left its domain.
        return spec, result, checks, [
            line for line in printed.getvalue().splitlines() if "warning" in line.lower()
        ]


def _cell(spec):
    keys = ("output", "frequency_ghz", "microstructure_model", "corr_length_m", "radius_m",
            "substrate", "volumetric_liquid_water", "temperature_k", "sweep_parameter")
    cell = {key: spec.get(key) for key in keys}
    grain = "radius_m" if spec["microstructure_model"] == "sticky_hard_spheres" else "corr_length_m"
    cell["grain_mm"] = round(spec[grain] * 1e3, 3)
    cell.pop("corr_length_m"), cell.pop("radius_m")
    return cell


def grid(probe):
    """Check every expectation across the regime grid."""
    tally = defaultdict(lambda: {"applied": 0, "met": 0, "not_met": []})
    printed = set()

    def record(spec, result, checks, warned):
        printed.update(warned)
        for check in checks:
            item = tally[check["expectation"]]
            item["applied"] += 1
            if check["passed"]:
                item["met"] += 1
            else:
                series = result["series"][check["output"]]
                item["not_met"].append(dict(_cell(spec), change=round(series[-1] - series[0], 2)))

    for (micro, (grain, values)), substrate in itertools.product(GRAINS.items(), ("rough_soil", "flat_soil")):
        for value, frequency in itertools.product(values, PASSIVE_GHZ):
            base = {"microstructure_model": micro, grain: value, "substrate": substrate}
            record(*probe.run(**base, frequency_ghz=frequency, **DEPTH))
            for wetness in (0.005, 0.02):
                record(*probe.run(**base, frequency_ghz=frequency, temperature_k=273.15,
                                  volumetric_liquid_water=wetness, **DEPTH))
            record(*probe.run(**base, frequency_ghz=frequency, temperature_k=273.15, thickness_m=0.5,
                              sweep_parameter="volumetric_liquid_water", sweep_start=0.0,
                              sweep_stop=0.03, sweep_points=6))
            record(*probe.run(**base, frequency_ghz=frequency, thickness_m=1.0,
                              sweep_parameter="temperature_k", sweep_start=230.0,
                              sweep_stop=273.15, sweep_points=6))
        if substrate != "rough_soil":
            continue  # flat soil returns no ground backscatter; active is probed on the default
        for value, frequency in itertools.product(values, ACTIVE_GHZ):
            base = {"microstructure_model": micro, grain: value, "output": "sigma", "angle_deg": 40.0}
            record(*probe.run(**base, frequency_ghz=frequency, **DEPTH))
            record(*probe.run(**base, frequency_ghz=frequency, temperature_k=273.15, thickness_m=0.5,
                              sweep_parameter="volumetric_liquid_water", sweep_start=0.0,
                              sweep_stop=0.03, sweep_points=6))

    unconditional = {
        item["id"] for item in (probe.card.get("physics") or {}).get("expectations") or []
        if not item.get("when")
    }
    expectations = {}
    for name, item in sorted(tally.items()):
        expectations[name] = {
            "applied": item["applied"],
            "met": item["met"],
            "not_met": len(item["not_met"]),
            "warns_on_any_departure": name in unconditional,
            "cells_not_met": item["not_met"],
        }
    return expectations, sorted(printed)


def findings(probe):
    """Reproduce each named finding of the provenance sidecar with one probe."""
    out = {}

    def change(result, output):
        series = result["series"][output]
        return round(series[-1] - series[0], 2)

    _, r, c, _ = probe.run(microstructure_model="sticky_hard_spheres", radius_m=2e-4, stickiness=0.2,
                           temperature_k=270.0, substrate="none", frequency_ghz=37.0,
                           sweep_parameter="thickness_m", sweep_start=0.1, sweep_stop=2.0, sweep_points=8)
    out["vacuum-substrate"] = {"tb_v_first_last": [round(r["series"]["tb_v"][0], 1), round(r["series"]["tb_v"][-1], 1)],
                               "warned": [x["expectation"] for x in c if not x["passed"]]}

    rows = {}
    for label, args in (("snow 270 K on flat soil at 258.15 K", {"substrate": "flat_soil", "soil_temperature_k": 258.15}),
                        ("snow 270 K on flat soil at snow temperature", {"substrate": "flat_soil"})):
        _, r, _, _ = probe.run(microstructure_model="sticky_hard_spheres", radius_m=2e-4, stickiness=0.2,
                               temperature_k=270.0, frequency_ghz=37.0, **args,
                               sweep_parameter="thickness_m", sweep_start=0.1, sweep_stop=2.0, sweep_points=8)
        rows[label] = change(r, "tb_v")
    out["snow-soil-temperature-inversion"] = {"tb_v_change_K": rows}

    rows = {}
    for grain in (5e-5, 1.5e-4):
        _, r, _, _ = probe.run(corr_length_m=grain, substrate="flat_soil", frequency_ghz=37.0, **DEPTH)
        rows["%.2f mm" % (grain * 1e3)] = change(r, "tb_v")
    out["fine-grain-boundary"] = {"tb_v_change_K_37GHz_flat_soil": rows}

    rows = {}
    for substrate, start in itertools.product(("flat_soil", "rough_soil"), (0.05, 0.2)):
        _, r, _, _ = probe.run(frequency_ghz=37.0, temperature_k=273.15, volumetric_liquid_water=0.005,
                               substrate=substrate, sweep_parameter="thickness_m", sweep_start=start,
                               sweep_stop=2.0, sweep_points=10)
        series = r["series"]["tb_v"]
        rows["%s from %.2f m" % (substrate, start)] = round(max(series) - min(series), 2)
    out["thin-wet-layer"] = {"tb_v_spread_K_at_0.5_percent": rows}

    rows = {}
    for substrate in ("flat_soil", "rough_soil"):
        _, r, c, _ = probe.run(microstructure_model="sticky_hard_spheres", radius_m=2e-4, stickiness=0.2,
                               substrate=substrate, frequency_ghz=37.0, **DEPTH)
        rows[substrate] = {"tb_v": change(r, "tb_v"), "tb_h": change(r, "tb_h"),
                           "warned": [x["expectation"] for x in c if not x["passed"]]}
    out["flat-soil-regime-transfer"] = {"run2_arm_b_replay_37GHz": rows}

    rows = {}
    for wetness in (0.0, 0.08):
        _, _, _, printed = probe.run(output="sigma", angle_deg=40.0, frequency_ghz=17.2,
                                     temperature_k=265.0 if wetness == 0 else 273.15,
                                     volumetric_liquid_water=wetness, **DEPTH)
        rows["%.2f liquid water" % wetness] = len(printed)
    out["iem-validity"] = {"smrt_validity_warnings_at_17.2GHz": rows}

    rows = {}
    for label, args in (("soil follows snow", {}), ("soil fixed at 265 K", {"soil_temperature_k": 265.0})):
        _, r, _, _ = probe.run(radius_m=3e-4, microstructure_model="sticky_hard_spheres", frequency_ghz=18.7,
                               thickness_m=1.0, **args, sweep_parameter="temperature_k",
                               sweep_start=230.0, sweep_stop=273.15, sweep_points=6)
        rows[label] = change(r, "tb_v")
    out["soil-follows-snow-in-temperature-sweep"] = {"tb_v_change_K_18.7GHz": rows}

    out["go-mean-square-slope-convention"] = _go_slope()
    return out


def _go_slope():
    """SMRT's geometrical-optics soil at the mean square slope Montpetit et al. (2024) report."""
    try:
        from smrt import make_model, make_snowpack, make_soil, sensor_list
    except ImportError:
        return {"skipped": "smrt not importable"}
    model = make_model("iba", "dort")
    rows = {}
    for angle in (20, 30, 40):
        soil = make_soil("geometrical_optics_backscatter", complex(4, 0.5), temperature=265.0,
                         mean_square_slope=0.01)
        pack = make_snowpack([1e-4], "exponential", density=300.0, temperature=265.0,
                             corr_length=1e-5, substrate=soil)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rows["%d deg" % angle] = round(float(model.run(sensor_list.active(13.5e9, angle), pack).sigmaVV_dB()), 1)
    return {"sigma_vv_db_bare_soil_mss_0.010_13.5GHz": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("model")
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    probe = Probe(args.model)
    expectations, printed = grid(probe)
    report = {
        "model": args.model,
        "version": probe.card["version"],
        "expectations": expectations,
        "smrt_validity_warnings_in_grid": printed,
        "findings": findings(probe),
    }
    out = Path(args.out or ROOT / "evaluation" / "results" / ("%s_forge_probe.json" % args.model))
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, item in expectations.items():
        print("%-34s applied %4d  met %4d  not met %3d%s" % (
            name, item["applied"], item["met"], item["not_met"],
            "  (warns on any departure)" if item["warns_on_any_departure"] else ""))
    print("SMRT validity warnings during the grid: %d" % len(printed))
    for name, value in report["findings"].items():
        print("finding %-38s %s" % (name, json.dumps(value)))
    print("wrote %s" % out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())

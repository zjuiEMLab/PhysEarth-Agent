"""Audit a registered model card for the gaps a forge registration can leave.

Prototype of the checks the model registration forge should run before a card is proposed
(docs/enhancements/model-registration-forge.md). Each check answers a question the SMRT
registration of 2026-10-12 failed to ask, and which the APGARSS run-2 comparison exposed:

  coverage     Which outputs have no physical expectation at all, and which frequencies do the
               expectations leave unchecked? (H-pol and 19 GHz had none.)
  practice     Does a card default agree with how the model's own repository uses the model?
               (The repository uses rough soils; the card defaults to a flat one.)
  regime       Does a default come from a source whose frequency range covers where the card
               will be used? (The flat soil came from an 89 to 243 GHz study.)
  robustness   Does the sign of a basic trend flip inside a load-bearing parameter's typical
               range, so the default silently picks a side? (TbH against depth flips between
               0.2 and 0.3 mm sphere radius.)

    python onboarding/forge_audit.py smrt --repo ~/Desktop/Git/apgarss-testing/run2-arm-a-plain-smrt/smrt

Read-only: it runs the registered adapter, reads the card, its provenance sidecar, the
literature corpus and an optional checkout of the model's repository.
"""

import argparse
import math
import re
import sys
import warnings
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from physearth import paths, registry  # noqa: E402
from physearth.harness import validation  # noqa: E402

GHZ = re.compile(r"(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*GHz")
SOIL_CALL = re.compile(r"make_soil\(\s*[\"']([a-z_0-9]+)")
CARD_TO_REPO = {"flat_soil": "flat", "rough_soil": "soil_wegmuller", "none": None}
PASSIVE = ("tb_v", "tb_h")
FREQUENCIES = (10.65, 18.7, 37.0, 89.0)


def _finding(check, severity, what, **evidence):
    return {"check": check, "severity": severity, "what": what, **evidence}


def coverage(card):
    expectations = (card.get("physics") or {}).get("expectations") or []
    covered = Counter(item["output"] for item in expectations)
    findings = []
    for group, names in (card.get("output_groups") or {}).items():
        for name in names:
            unit = card["outputs"][name]["unit"]
            if name.startswith("swe") or group == "coefficients" or covered[name]:
                continue
            findings.append(_finding(
                "coverage", "high" if unit in ("K", "dB") else "low",
                "%s (%s) has no physical expectation: a wrong trend in it passes silently" % (name, unit),
            ))
    floors = sorted(
        (item.get("when") or {}).get("frequency_ghz", {}).get("ge", 0.0) for item in expectations
        if item["output"] in PASSIVE and item["input"] in ("thickness_m", "swe_mm")
    )
    default = card["parameters"]["frequency_ghz"]["default"]
    if floors and floors[0] > min(FREQUENCIES):
        findings.append(_finding(
            "coverage", "medium",
            "passive depth trends are only checked from %s GHz; %s GHz and below are never checked "
            "(card default %s GHz)" % (floors[0], ", ".join(str(f) for f in FREQUENCIES if f < floors[0]), default),
        ))
    return findings


def practice(card, repo):
    if not repo:
        return [_finding("practice", "info", "no repository checkout given; skipped")]
    calls = Counter()
    for path in Path(repo).rglob("*"):
        if path.suffix in (".py", ".ipynb", ".rst", ".md") and path.is_file():
            calls.update(SOIL_CALL.findall(path.read_text(encoding="utf-8", errors="ignore")))
    total = sum(calls.values())
    default = card["parameters"].get("substrate", {}).get("default")
    repo_name = CARD_TO_REPO.get(default, default)
    share = calls.get(repo_name, 0) / total if total else 0.0
    findings = []
    if total and share < 0.25:
        findings.append(_finding(
            "practice", "high",
            "card default substrate=%s is %d of %d soil constructions in the repository (%.0f %%); "
            "the repository mostly uses %s"
            % (default, calls.get(repo_name, 0), total, 100 * share,
               ", ".join("%s (%d)" % item for item in calls.most_common(4))),
        ))
    return findings


def regime(card, provenance):
    findings = []
    default = card["parameters"]["frequency_ghz"]["default"]
    for field, entry in (provenance.get("fields") or {}).items():
        if not isinstance(entry, dict):
            continue
        chosen = card["parameters"].get(field, {}).get("default")
        for key, span in entry.items():
            if key == "%s_regime" % chosen and isinstance(span, dict):
                low, high = span["frequency_ghz"]
                if not low <= default <= high:
                    findings.append(_finding(
                        "regime", "high",
                        "default %s=%s is sourced for %s to %s GHz; the card's default frequency %s GHz is outside it"
                        % (field, chosen, low, high, default),
                    ))
        for key, slugs in entry.items():
            if not key.endswith("_corpus") or key[: -len("_corpus")] != chosen:
                continue
            if key.endswith("_regime"):
                continue
            for slug in slugs:
                path = paths.knowledge() / "literature" / slug / "card.yaml"
                if not path.is_file():
                    continue
                description = str(yaml.safe_load(path.read_text(encoding="utf-8")).get("description") or "")
                spans = [(float(a), float(b)) for a, b in GHZ.findall(description)]
                if spans and not any(low <= default <= high for low, high in spans[:1]):
                    findings.append(_finding(
                        "regime", "high",
                        "%s=%s is sourced from %s, which covers %s to %s GHz; the card's default "
                        "frequency is %s GHz, outside the source's regime"
                        % (field, key[: -len("_corpus")], slug, spans[0][0], spans[0][1], default),
                    ))
    return findings


def _trend(entry, card, arguments):
    spec, problems = validation.resolve(card, arguments)
    if problems:
        return None
    result = entry.run(spec)
    return {name: values[-1] - values[0] for name, values in result["series"].items()}


def robustness(entry, card, threshold=0.5):
    """Sign of each passive depth trend across the typical range of each grain parameter."""
    findings = []
    families = {
        "sticky_hard_spheres": "radius_m",
        "exponential": "corr_length_m",
    }
    for micro, grain in families.items():
        span = (card["parameters"][grain].get("typical") or {}).get("range")
        default = card["parameters"][grain]["default"]
        if not span:
            continue
        low, high = span
        values = sorted({default, *[low * (high / low) ** (i / 4) for i in range(5)]})
        for frequency in FREQUENCIES:
            signs = {}
            for value in values:
                change = _trend(entry, card, {
                    "microstructure_model": micro, grain: value, "frequency_ghz": frequency,
                    "sweep_parameter": "thickness_m", "sweep_start": 0.05, "sweep_stop": 2.0,
                    "sweep_points": 6,
                })
                if change:
                    for output in PASSIVE:
                        delta = change[output]
                        signs.setdefault(output, []).append(
                            (value, 0 if abs(delta) < threshold else int(math.copysign(1, delta)), delta)
                        )
            for output, row in signs.items():
                kinds = {sign for _, sign, _ in row if sign}
                # A sign that depends on grain size is physics; what matters is a default that
                # sits next to the flip, where the card's choice silently picks the answer.
                values_only = [v for v, _, _ in row]
                i = values_only.index(default)
                near = {row[j][1] for j in (i - 1, i, i + 1) if 0 <= j < len(row) and row[j][1]}
                if len(kinds) > 1 and len(near) > 1:
                    flip = next(v for (v, s, _), (_, s2, _) in zip(row, row[1:], strict=False) if s != s2)
                    at_default = next(d for v, _, d in row if v == default)
                    findings.append(_finding(
                        "robustness", "high" if output == "tb_h" or frequency in (18.7, 37.0) else "medium",
                        "%s against depth changes sign inside the typical %s range at %s GHz (%s); "
                        "the default %s gives %+.1f K, near the flip above %.3g"
                        % (output, grain, frequency, micro, default, at_default, flip),
                        trend=[(round(v * 1e3, 3), round(d, 1)) for v, _, d in row],
                    ))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("model")
    parser.add_argument("--repo", default="", help="a checkout of the model's own repository")
    args = parser.parse_args(argv)
    warnings.filterwarnings("ignore")
    entry = registry.get(args.model)
    card = entry.card
    sidecar = paths.models() / "bundled" / args.model / "model_card.provenance.yaml"
    provenance = yaml.safe_load(sidecar.read_text(encoding="utf-8")) if sidecar.is_file() else {}
    findings = coverage(card) + practice(card, args.repo) + regime(card, provenance) + robustness(entry, card)
    order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    # A sign flip is mitigated when an unconditional expectation on that output already warns
    # at run time whenever the trend goes the unexpected way.
    guarded = {
        item["output"] for item in (card.get("physics") or {}).get("expectations") or []
        if item["input"] in ("thickness_m", "swe_mm") and not item.get("when")
    }
    for item in findings:
        output = item["what"].split(" ", 1)[0]
        if item["check"] == "robustness" and output in guarded:
            item["severity"] = "info"
            item["what"] += "; mitigated: any rise is warned at run time"
    for item in sorted(findings, key=lambda f: order[f["severity"]]):
        print("[%s] %-10s %s" % (item["severity"], item["check"], item["what"]))
        if item.get("trend"):
            print("             grain (mm) -> change over 0.05-2 m (K): %s" % item["trend"])
    print("%d finding(s)" % len(findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Derive the bundled TVC reference tables from the published Zenodo files.

Put the four downloads in data/downloads/ and run from the repository root:

    python scripts/build_reference.py

Only the derived tables are committed. The raw downloads stay out of the repository.
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "downloads"
OUT = ROOT / "knowledge" / "reference"

SANE_LINEAR = (1e-5, 10.0)

SOURCES = {
    "ku": {
        "file": "UMass_TVC18-19_DB.geojson",
        "doi": "10.5281/zenodo.10794918",
        "instrument": "UMass airborne Ku-band SAR",
        "band": "Ku",
    },
    "x": {
        "file": "TSX_TVC18-19_DB.geojson",
        "doi": "10.5281/zenodo.10794868",
        "instrument": "TerraSAR-X",
        "band": "X",
    },
    "c": {
        "file": "RS2_TVC18-19_DB.geojson",
        "doi": "10.5281/zenodo.10794954",
        "instrument": "Radarsat-2",
        "band": "C",
    },
    "roughness": {
        "file": "SoilRough_ALS2018_TVC18-19.json",
        "doi": "10.5281/zenodo.10794980",
        "instrument": "airborne lidar",
        "band": None,
    },
}

CITATION = (
    "Montpetit, B., King, J., Siqueira, P., Adam, J. M., Toose, P., Derksen, C., and Brady, M. "
    "(2024). TVC Experiment 2018/19 [Dataset]. Zenodo. Published in Montpetit et al., "
    "The Cryosphere, 18, 3857-3874, 2024, https://doi.org/10.5194/tc-18-3857-2024."
)
LICENSE = "Open Government Licence - Canada"


def load(name):
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def to_db(linear):
    if not isinstance(linear, (int, float)):
        return None
    if not SANE_LINEAR[0] < linear < SANE_LINEAR[1]:
        return None
    return round(10.0 * math.log10(linear), 3)


def rows_from_polygon_set(key):
    source = SOURCES[key]
    rows, dropped = [], 0
    for feature in load(source["file"])["features"]:
        p = feature["properties"]
        sigma_db = to_db(p.get("loc_sig0") if p.get("loc_sig0") is not None else p.get("sig0"))
        if sigma_db is None:
            dropped += 1
            continue
        angle = p.get("loc_inc_ang") if p.get("loc_inc_ang") is not None else p.get("inc_ang")
        rows.append(
            {
                "band": source["band"],
                "instrument": source["instrument"],
                "station": p["Station"],
                "date": p["Date"][:10],
                "polarisation": p["pol"],
                "incidence_angle_deg": round(float(angle), 3),
                "sigma0_db": sigma_db,
            }
        )
    return rows, dropped


def rows_from_ku():
    source = SOURCES["ku"]
    rows, dropped = [], 0
    for feature in load(source["file"])["features"]:
        p = feature["properties"]
        angle = p.get("inc_mean")
        for field, polarisation in (("slc0_sig0_filt", "co"), ("slc1_sig0_filt", "cross")):
            sigma_db = to_db(p.get(field))
            if sigma_db is None:
                dropped += 1
                continue
            rows.append(
                {
                    "band": source["band"],
                    "instrument": source["instrument"],
                    "station": p.get("site_id") or p.get("site"),
                    "date": (p.get("radar_ts") or "")[:10],
                    "polarisation": polarisation,
                    "incidence_angle_deg": round(float(angle), 3),
                    "sigma0_db": sigma_db,
                }
            )
    return rows, dropped


def columnar(rows, categorical, numeric):
    table = {"n_rows": len(rows), "columns": {}}
    for name in categorical:
        values = sorted({row[name] for row in rows})
        index = {value: position for position, value in enumerate(values)}
        table["columns"][name] = {
            "kind": "categorical",
            "levels": values,
            "codes": [index[row[name]] for row in rows],
        }
    for name in numeric:
        table["columns"][name] = {"kind": "numeric", "values": [row[name] for row in rows]}
    return table


def build_backscatter():
    rows, dropped = [], 0
    for key in ("c", "x"):
        part, lost = rows_from_polygon_set(key)
        rows.extend(part)
        dropped += lost
    part, lost = rows_from_ku()
    rows.extend(part)
    dropped += lost
    rows.sort(key=lambda r: (r["band"], r["station"], r["date"], r["polarisation"]))

    table = columnar(
        rows,
        categorical=["band", "instrument", "station", "date", "polarisation"],
        numeric=["incidence_angle_deg", "sigma0_db"],
    )
    card = {
        "slug": "tvc-backscatter",
        "title": "Trail Valley Creek 2018/19 measured radar backscatter",
        "description": (
            "Measured backscattering coefficients over a tundra snowpack at Trail Valley "
            "Creek, Northwest Territories, from three instruments covering C, X and Ku band. "
            "Use it to compare a model run against what was actually observed. Every value "
            "is a measurement; nothing in this table came from a model."
        ),
        "license": LICENSE,
        "citation": CITATION,
        "paper": "10.5194/tc-18-3857-2024",
        "corpus_slug": "tvc-ku-swe",
        "sources": [
            {"band": SOURCES[k]["band"], "instrument": SOURCES[k]["instrument"], "doi": SOURCES[k]["doi"]}
            for k in ("c", "x", "ku")
        ],
        "derivation": (
            "Backscatter converted from linear power to decibels. The locally corrected "
            "fields loc_sig0 and loc_inc_ang are preferred where the publisher provides them. "
            "Values outside 1e-5 to 10 in linear power are dropped as uncalibrated; %d of "
            "%d candidate values were dropped. Ku co-polarised and cross-polarised channels "
            "come from slc0_sig0_filt and slc1_sig0_filt." % (dropped, dropped + len(rows))
        ),
        "columns": {
            "band": {"unit": "none", "source": "measurement", "description": "Radar band."},
            "instrument": {"unit": "none", "source": "measurement", "description": "Sensor."},
            "station": {"unit": "none", "source": "measurement", "description": "Ground station identifier."},
            "date": {"unit": "date", "source": "measurement", "description": "Acquisition date."},
            "polarisation": {"unit": "none", "source": "measurement", "description": "Transmit and receive polarisation, or co and cross for Ku."},
            "incidence_angle_deg": {"unit": "degree", "source": "measurement", "description": "Local incidence angle."},
            "sigma0_db": {"unit": "dB", "source": "measurement", "description": "Backscattering coefficient."},
        },
    }
    return card, table


def build_roughness():
    raw = load(SOURCES["roughness"]["file"])
    keys = sorted(raw["Site"], key=lambda k: int(k))
    rows = [
        {
            "station": raw["Site"][k],
            "rms_height_m": round(float(raw["rms"][k]), 6),
            "correlation_length_m": round(float(raw["lc"][k]), 6),
            "mean_square_slope": round(float(raw["mss"][k]), 6),
        }
        for k in keys
    ]
    table = columnar(
        rows,
        categorical=["station"],
        numeric=["rms_height_m", "correlation_length_m", "mean_square_slope"],
    )
    card = {
        "slug": "tvc-soil-roughness",
        "title": "Trail Valley Creek soil roughness from airborne lidar",
        "description": (
            "Per-station soil surface roughness retrieved from 2018 airborne lidar at Trail "
            "Valley Creek. These are the numbers a rough-surface substrate needs, so use them "
            "when driving a model at one of these stations instead of guessing a roughness."
        ),
        "license": LICENSE,
        "citation": CITATION,
        "paper": "10.5194/tc-18-3857-2024",
        "corpus_slug": "tvc-ku-swe",
        "sources": [{"band": None, "instrument": "airborne lidar", "doi": SOURCES["roughness"]["doi"]}],
        "derivation": "Reshaped from the published mapping into rows. Values unchanged.",
        "columns": {
            "station": {"unit": "none", "source": "measurement", "description": "Ground station identifier."},
            "rms_height_m": {"unit": "m", "source": "measurement", "description": "RMS surface height."},
            "correlation_length_m": {"unit": "m", "source": "measurement", "description": "Surface correlation length."},
            "mean_square_slope": {"unit": "none", "source": "measurement", "description": "Mean square slope, the parameter the geometrical optics substrate uses."},
        },
    }
    return card, table


def write(card, table):
    target = OUT / card["slug"]
    target.mkdir(parents=True, exist_ok=True)
    (target / "dataset_card.json").write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (target / "data.json").write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
    size = (target / "data.json").stat().st_size
    print("%-22s %6d rows  %7.1f kB" % (card["slug"], table["n_rows"], size / 1024))


def main():
    missing = [s["file"] for s in SOURCES.values() if not (RAW / s["file"]).is_file()]
    if missing:
        print("missing raw downloads in %s: %s" % (RAW, ", ".join(missing)))
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    write(*build_backscatter())
    write(*build_roughness())
    return 0


if __name__ == "__main__":
    sys.exit(main())

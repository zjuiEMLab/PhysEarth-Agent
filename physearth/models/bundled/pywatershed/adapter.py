"""PRMS over the Sagehen Creek test domain, through pywatershed.

Nothing here imports pywatershed at module level. The registry loads this file on every
host, including the ones where the package cannot be installed, and a top-level import
would turn "registered but not runnable here" into "this model was rejected" -- which is
a much less useful thing to tell somebody.

The domain is the pinned release's own `sagehen_5yr` fixture, so a run is reproducible
from the release alone. It is fetched once into the state directory and checksummed; it is
not redistributed in this repository.
"""

import hashlib
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

RELEASE = "3.0.0"
COMMIT = "41707c16f1fac09e2e4d4ecb9e3bf6bf1948885e"
FIXTURE_URL = (
    "https://github.com/DOI-USGS/pywatershed/archive/%s.zip" % COMMIT
)
FIXTURE_MEMBER = "pywatershed-%s/test_data/sagehen_5yr" % COMMIT
MAX_FIXTURE_BYTES = 400_000_000

# What PRMS calls each quantity, and how to turn it into a basin-mean depth in millimetres.
# PRMS works in inches over hydrologic response units; the agent is told millimetres, and
# the conversion belongs here rather than in anything the agent has to remember.
INCH_TO_MM = 25.4
VARIABLES = {
    "snowpack_water_equivalent": "pkwater_equiv",
    "snowmelt": "snowmelt",
    "surface_runoff": "sroff",
    "soil_zone_flow": "ssres_flow",
    "groundwater_flow": "gwres_flow",
    "precipitation": "hru_ppt",
}

PROCESSES = (
    "PRMSSolarGeometry",
    "PRMSAtmosphere",
    "PRMSCanopy",
    "PRMSSnow",
    "PRMSRunoffNoDprst",
    "PRMSSoilzoneNoDprst",
    "PRMSGroundwaterNoDprst",
)


def _state_dir():
    from physearth import config

    return config.state_dir() / "pywatershed"


def fixture_dir():
    """Where the pinned Sagehen domain lives once it has been fetched."""
    return _state_dir() / ("sagehen_5yr_%s" % COMMIT[:12])


def ensure_fixture(timeout=300.0):
    """Fetch the pinned domain once. Returns the directory, or raises with the reason."""
    target = fixture_dir()
    if (target / "control.test").is_file() or (target / "prcp.nc").is_file():
        return target
    root = _state_dir()
    root.mkdir(parents=True, exist_ok=True)
    archive = root / ("pywatershed-%s.zip" % COMMIT[:12])
    if not archive.is_file():
        request = urllib.request.Request(
            FIXTURE_URL, headers={"User-Agent": "physearth-agent/0.1"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read(MAX_FIXTURE_BYTES + 1)
        if len(payload) > MAX_FIXTURE_BYTES:
            raise RuntimeError(
                "the pywatershed source archive is larger than the %d byte ceiling"
                % MAX_FIXTURE_BYTES
            )
        archive.write_bytes(payload)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()

    staging = root / "staging"
    if staging.exists():
        shutil.rmtree(staging)
    with zipfile.ZipFile(archive) as bundle:
        members = [n for n in bundle.namelist() if n.startswith(FIXTURE_MEMBER)]
        if not members:
            raise RuntimeError(
                "the archive for commit %s does not contain %s" % (COMMIT[:12], FIXTURE_MEMBER)
            )
        bundle.extractall(staging, members=members)
    extracted = staging / FIXTURE_MEMBER
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(extracted), str(target))
    shutil.rmtree(staging, ignore_errors=True)
    (target / "PROVENANCE.txt").write_text(
        "pywatershed %s\ncommit %s\nsource %s\narchive sha256 %s\n"
        % (RELEASE, COMMIT, FIXTURE_URL, digest),
        encoding="utf-8",
    )
    return target


def _require():
    """Import pywatershed here, and turn its absence into a sentence, not a traceback."""
    try:
        import pywatershed
    except ImportError as exc:
        raise RuntimeError(
            "pywatershed is not installed in this environment. It needs numpy 2 and Python "
            "3.12 or 3.13, which is why this deployment registers the model without being "
            "able to run it. Install `pywatershed==%s` on a host that allows numpy 2, or "
            "ask about one of the microwave models instead." % RELEASE
        ) from exc
    return pywatershed


def _water_year_bounds(start, end):
    """A water year runs from 1 October of the previous calendar year to 30 September."""
    return "%d-10-01" % (start - 1), "%d-09-30" % end


def _aggregate(values, dates, how):
    if how == "daily":
        return values, list(range(len(values)))
    buckets = {}
    order = []
    for value, date in zip(values, dates, strict=True):
        if how == "monthly":
            key = (date.year, date.month)
        else:
            key = date.year + (1 if date.month >= 10 else 0)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(value)
    means = [sum(buckets[k]) / len(buckets[k]) for k in order]
    return means, list(range(len(means)))


def run(spec):
    pws = _require()
    import numpy as np

    domain = ensure_fixture()
    variable = VARIABLES[spec["variable"]]
    start, end = _water_year_bounds(spec["water_year_start"], spec["water_year_end"])

    # The no-cascades configuration, which is the process chain this card declares. The
    # fixture starts at the beginning of water year 1981; the run is shortened at the end
    # to the requested year and the earlier days are dropped afterwards, because the
    # forcing has to be walked from its own beginning for the stores to be spun up.
    control = pws.Control.load_prms(
        domain / "sagehen_no_cascades.control", warn_unused_options=False
    )
    control.edit_end_time(np.datetime64(end))
    control.options["input_dir"] = domain
    # PRMS calls this the imbalance behaviour: `error` stops the run when the water budget
    # does not close, `warn` lets it finish so the failure can be looked at.
    control.options["imbalance_behavior"] = (
        "error" if spec.get("budget_check", True) else "warn"
    )
    control.options["calc_method"] = "numpy"
    control.options["verbosity"] = 0

    parameters = pws.parameters.PrmsParameters.load(domain / "myparam.param")
    processes = [getattr(pws, name) for name in PROCESSES]
    model = pws.Model(processes, control=control, parameters=parameters)

    wanted_from = np.datetime64(start)
    collected, dates = [], []
    for _ in range(control.n_times):
        model.advance()
        model.calculate()
        holder = None
        for process in model.processes.values():
            if hasattr(process, variable):
                holder = process
        if holder is None:
            raise RuntimeError(
                "%s is not produced by the Sagehen process chain" % spec["variable"]
            )
        if control.current_time >= wanted_from:
            field = np.asarray(getattr(holder, variable), dtype=float)
            collected.append(float(np.nanmean(field)) * INCH_TO_MM)
            dates.append(control.current_time.astype("datetime64[D]").item())
    model.finalize()

    if not collected:
        raise RuntimeError(
            "no time step of the run fell inside water years %d to %d"
            % (spec["water_year_start"], spec["water_year_end"])
        )
    values, index = _aggregate(collected, dates, spec["aggregation"])
    points = [
        {"index": n, "time_index": float(n), "value": value}
        for n, value in zip(index, values, strict=True)
    ]
    return {
        "axis": {"name": "time_index", "values": [float(n) for n in index]},
        "points": points,
        "series": {"value": values, "time_index": [float(n) for n in index]},
    }


def provenance():
    """What a run of this model rests on, for a run manifest."""
    path = fixture_dir() / "PROVENANCE.txt"
    return {
        "release": RELEASE,
        "commit": COMMIT,
        "domain": "sagehen_5yr",
        "fetched": path.is_file(),
        "manifest": path.read_text(encoding="utf-8") if path.is_file() else "",
        "python": os.environ.get("PYTHON_VERSION", ""),
    }

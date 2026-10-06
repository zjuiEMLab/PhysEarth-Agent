"""Executable oracles that do not call PhysEarth model adapters."""

import importlib
import sys
import warnings


def _ensure_smrt_importable():
    """Use SMRT's NumPy fallback when its optional Numba cache fails on Python 3.13+."""
    loaded = sys.modules.get("smrt.core.lib")
    if loaded is not None and hasattr(loaded, "abs2"):
        return
    if sys.version_info < (3, 13):
        return
    for name in [item for item in sys.modules if item == "smrt" or item.startswith("smrt.")]:
        sys.modules.pop(name, None)
    missing = object()
    previous = sys.modules.get("numba", missing)
    sys.modules["numba"] = None
    try:
        importlib.import_module("smrt.core.lib")
    finally:
        if previous is missing:
            sys.modules.pop("numba", None)
        else:
            sys.modules["numba"] = previous


def upstream_smrt_curve(task):
    """Run the task reference directly through the public upstream SMRT API.

    This is adapter-independent and therefore useful for detecting adapter regressions.
    It is not a digitized paper curve and must not be described as one in reports.
    """
    reference = task.get("reference") or {}
    if reference.get("model") != "smrt":
        return None
    spec = dict(reference.get("parameters") or {})
    swept = spec.get("sweep_parameter")
    if swept in (None, "none"):
        axis_values = [spec.get(swept)] if swept else [0]
    else:
        count = int(spec.get("sweep_points") or 10)
        start, stop = spec["sweep_start"], spec["sweep_stop"]
        step = (stop - start) / (count - 1) if count > 1 else 0.0
        axis_values = [start + index * step for index in range(count)]

    _ensure_smrt_importable()
    from smrt import make_model, make_snowpack, sensor_list

    series = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for value in axis_values:
            values = dict(spec)
            if swept not in (None, "none"):
                values[swept] = value
            snowpack_args = {
                "thickness": [values["thickness_m"]],
                "microstructure_model": values["microstructure_model"],
                "density": [values["density_kg_m3"]],
                "temperature": [values["temperature_k"]],
                "radius": [values["radius_m"]],
            }
            if values["microstructure_model"] == "sticky_hard_spheres":
                snowpack_args["stickiness"] = [values["stickiness"]]
            snowpack = make_snowpack(**snowpack_args)
            model = make_model(
                values["electromagnetic_model"],
                "dort",
                rtsolver_options={"n_max_stream": int(values.get("dort_streams", 32))},
            )
            frequency = values["frequency_ghz"] * 1.0e9
            if values["output"] == "sigma":
                sensor = sensor_list.active(frequency, values["angle_deg"])
                result = model.run(sensor, snowpack)
                point = {
                    "sigma_vv_db": float(result.sigmaVV_dB()),
                    "sigma_hh_db": float(result.sigmaHH_dB()),
                    "sigma_hv_db": float(result.sigmaHV_dB()),
                }
            else:
                sensor = sensor_list.passive(frequency, values["angle_deg"])
                result = model.run(sensor, snowpack)
                point = {"tb_v": float(result.TbV()), "tb_h": float(result.TbH())}
            for name, item in point.items():
                series.setdefault(name, []).append(item)
    return {
        "oracle_type": "upstream_package",
        "package": "smrt",
        "adapter_independent": True,
        "paper_digitization": False,
        "axis": None if swept in (None, "none") else {"name": swept, "values": axis_values},
        "series": series,
    }


def _sweep(axis):
    values = axis.get("values")
    if values:
        return [float(value) for value in values]
    start, stop, count = float(axis["start"]), float(axis["stop"]), int(axis["points"])
    step = (stop - start) / (count - 1) if count > 1 else 0.0
    return [start + index * step for index in range(count)]


def _result(package, version, axis_name, axis_values, series, note):
    return {
        "oracle_type": "upstream_package",
        "package": package,
        "package_version": version,
        "adapter_independent": True,
        "paper_digitization": False,
        "note": note,
        "axis": {"name": axis_name, "values": axis_values},
        "series": series,
    }


def upstream_prosail_series(oracle):
    """PROSPECT-5 + 4SAIL called directly, with the recipe's own leaf angle distribution."""
    import importlib.metadata

    import prosail

    recipe = dict(oracle["recipe"])
    bands = {name: int(nm) for name, nm in oracle["bands_nm"].items()}
    axis_values = _sweep(oracle["axis"])
    series = {name: [] for name in bands}
    for value in axis_values:
        values = dict(recipe, **{oracle["axis"]["upstream_name"]: value})
        args = [values.pop(name) for name in (
            "n", "cab", "car", "cbrown", "cw", "cm", "lai", "lidfa", "hspot", "tts", "tto", "psi"
        )]
        spectrum = prosail.run_prosail(*args, **values)
        for name, nm in bands.items():
            series[name].append(float(spectrum[nm - 400]))
    return _result(
        "prosail", importlib.metadata.version("prosail"), oracle["axis"]["name"], axis_values,
        series, "prosail.run_prosail evaluated directly; not a digitized curve",
    )


def upstream_pyet_series(oracle):
    """Each pyet formulation called directly on a dated daily series."""
    import importlib.metadata
    import math

    import pandas
    import pyet

    recipe = oracle["recipe"]
    day = pandas.Timestamp(2001, 1, 1) + pandas.Timedelta(days=int(recipe["day_of_year"]) - 1)

    def series(value):
        return pandas.Series([float(value)], index=pandas.DatetimeIndex([day]))

    lat = math.radians(float(recipe["latitude_deg"]))
    axis_values = _sweep(oracle["axis"])
    out = {name: [] for name in oracle["methods"]}
    for tmean in axis_values:
        common = {"tmean": series(tmean)}
        extremes = {"tmax": series(recipe["tmax_c"]), "tmin": series(recipe["tmin_c"])}
        for name, method in oracle["methods"].items():
            if method == "pm":
                value = pyet.pm(
                    wind=series(recipe["wind_speed_m_s"]), rn=series(recipe["net_radiation"]),
                    pressure=series(recipe["pressure_kpa"]),
                    rhmax=series(recipe["rh_max_pct"]), rhmin=series(recipe["rh_min_pct"]),
                    **extremes, **common,
                )
            elif method == "penman":
                value = pyet.penman(
                    wind=series(recipe["wind_speed_m_s"]), rn=series(recipe["net_radiation"]),
                    pressure=series(recipe["pressure_kpa"]),
                    rhmax=series(recipe["rh_max_pct"]), rhmin=series(recipe["rh_min_pct"]),
                    **extremes, **common,
                )
            elif method == "priestley_taylor":
                value = pyet.priestley_taylor(
                    rn=series(recipe["net_radiation"]), pressure=series(recipe["pressure_kpa"]),
                    **common,
                )
            elif method == "makkink":
                value = pyet.makkink(
                    rs=series(recipe["solar_radiation"]), pressure=series(recipe["pressure_kpa"]),
                    **common,
                )
            elif method == "hargreaves":
                value = pyet.hargreaves(lat=lat, **extremes, **common)
            elif method == "oudin":
                value = pyet.oudin(lat=lat, **common)
            else:
                raise ValueError(f"unknown pyet method {method}")
            out[name].append(float(value.iloc[0]))
    return _result(
        "pyet", importlib.metadata.version("pyet"), oracle["axis"]["name"], axis_values, out,
        "pyet formulations evaluated directly; not a digitized curve",
    )


def upstream_pywatershed_series(oracle):
    """The release's own Sagehen model YAML, run directly, area-weighted over HRUs."""
    import importlib.metadata
    import tempfile
    from pathlib import Path

    import numpy as np
    import pywatershed
    import yaml
    from pywatershed import Parameters

    domain = _sagehen_domain().resolve()
    recipe = oracle["recipe"]
    wanted = oracle["variables"]
    daily = {name: [] for name in wanted}
    dates = []
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        control = yaml.safe_load((domain / recipe["control_yaml"]).read_text(encoding="utf-8"))
        control.update(
            start_time=recipe["start_time"], end_time=recipe["end_time"],
            input_dir=str(domain), calc_method="numpy", imbalance_behavior="error",
        )
        (scratch / "control.yaml").write_text(yaml.safe_dump(control), encoding="utf-8")
        model_spec = yaml.safe_load((domain / recipe["model_yaml"]).read_text(encoding="utf-8"))
        model_spec["control"] = str(scratch / "control.yaml")
        for key, value in model_spec.items():
            if isinstance(value, str) and value.endswith(".nc"):
                model_spec[key] = str(domain / value)
            elif isinstance(value, dict) and str(value.get("parameters", "")).endswith(".nc"):
                value["parameters"] = str(domain / value["parameters"])
        (scratch / "model.yaml").write_text(yaml.safe_dump(model_spec), encoding="utf-8")
        model = pywatershed.Model.from_yaml(scratch / "model.yaml")
        area = np.asarray(
            Parameters.from_netcdf(domain / "parameters_dis_hru.nc").parameters["hru_area"],
            dtype=float,
        )
        for _ in range(model.control.n_times):
            model.advance()
            model.calculate()
            for name, item in wanted.items():
                field = np.asarray(
                    getattr(model.processes[item["process"]], item["prms_name"]), dtype=float
                )
                daily[name].append(float(np.nansum(field * area) / area.sum()) * 25.4)
            dates.append(model.control.current_time.astype("datetime64[D]").item())
        model.finalize()
    months = []
    for date in dates:
        if (date.year, date.month) not in months:
            months.append((date.year, date.month))
    series = {
        name: [
            float(np.mean([v for v, d in zip(values, dates, strict=True)
                           if (d.year, d.month) == month]))
            for month in months
        ]
        for name, values in daily.items()
    }
    return _result(
        "pywatershed", importlib.metadata.version("pywatershed"), oracle["axis"]["name"],
        [float(index) for index in range(len(months))], series,
        "sagehen_no_cascades model YAML run directly with per-process parameter files; "
        "monthly means of area-weighted daily basin depths",
    )


def _sagehen_domain():
    """The pinned Sagehen domain files. Only the adapter's fetch helper is borrowed; the
    run itself never goes through the adapter."""
    import importlib.util
    from pathlib import Path

    bundled = Path(__file__).resolve().parents[2] / "catalog" / "models" / "bundled"
    path = bundled / "pywatershed" / "adapter.py"
    spec = importlib.util.spec_from_file_location("_pywatershed_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ensure_fixture()


UPSTREAM = {
    "prosail": upstream_prosail_series,
    "pyet": upstream_pyet_series,
    "pywatershed": upstream_pywatershed_series,
}

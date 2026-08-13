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

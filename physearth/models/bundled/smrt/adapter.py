import math
import importlib
import sys
import warnings

MICROSTRUCTURE_ARGS = {
    "exponential": ("corr_length_m", "corr_length"),
    "teubner_strey": ("corr_length_m", "corr_length"),
    "gaussian_random_field": ("corr_length_m", "corr_length"),
    "independent_sphere": ("radius_m", "radius"),
    "sticky_hard_spheres": ("radius_m", "radius"),
}


def _ensure_smrt_importable():
    """Load SMRT without Numba on Python versions where its cached ufunc cannot load.

    SMRT 1.5.1 decorates ``abs2`` with ``cache=True``.  Numba cannot locate that
    installed module under Python 3.13 and raises before a model can run.  SMRT already
    supports a NumPy fallback when Numba is unavailable, so hide Numba only while SMRT's
    optional dependency module is first imported.  Other application code keeps its
    normal Numba module.
    """
    loaded_lib = sys.modules.get("smrt.core.lib")
    if loaded_lib is not None and hasattr(loaded_lib, "abs2"):
        return
    if sys.version_info < (3, 13):
        return
    # A failed eager warm-up can leave partially initialized SMRT modules behind.
    for module_name in [name for name in sys.modules if name == "smrt" or name.startswith("smrt.")]:
        sys.modules.pop(module_name, None)
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


def _snowpack(spec, overrides=None):
    _ensure_smrt_importable()
    from smrt import make_snowpack

    values = dict(spec)
    values.update(overrides or {})
    micro = values["microstructure_model"]
    source_key, target_key = MICROSTRUCTURE_ARGS[micro]
    kwargs = {
        "thickness": [values["thickness_m"]],
        "microstructure_model": micro,
        "density": [values["density_kg_m3"]],
        "temperature": [values["temperature_k"]],
        target_key: [values[source_key]],
    }
    if micro == "sticky_hard_spheres":
        kwargs["stickiness"] = [values["stickiness"]]
    return make_snowpack(**kwargs)


def _sensor(spec, overrides=None):
    _ensure_smrt_importable()
    from smrt import sensor_list

    values = dict(spec)
    values.update(overrides or {})
    frequency = values["frequency_ghz"] * 1e9
    angle = values["angle_deg"]
    if values["output"] == "sigma":
        return sensor_list.active(frequency, angle)
    return sensor_list.passive(frequency, angle)


def _extract(result, output):
    if output == "sigma":
        return {
            "sigma_vv_db": float(result.sigmaVV_dB()),
            "sigma_hh_db": float(result.sigmaHH_dB()),
            "sigma_hv_db": float(result.sigmaHV_dB()),
        }
    return {"tb_v": float(result.TbV()), "tb_h": float(result.TbH())}


def _scalar(value):
    """SMRT returns coefficients as its own matrix type, an array, or a bare float."""
    import numpy as np

    value = value() if callable(value) else value
    value = getattr(value, "values", value)
    return float(np.atleast_1d(np.asarray(value, dtype=complex)).ravel()[0].real)


def _coefficients(spec, overrides=None):
    """The electromagnetic coefficients of the layer, without solving radiative transfer.

    This is what separates a question about the medium from a question about what a
    sensor would see. The scattering and absorption coefficients are properties of the
    snow and the theory alone; brightness temperature is those coefficients after a
    solver has been run over them. Asking for the first should not require paying for,
    or being confounded by, the second.
    """
    _ensure_smrt_importable()
    from smrt.core.plugin import import_class

    values = dict(spec)
    values.update(overrides or {})
    snowpack = _snowpack(values)
    sensor = _sensor(dict(values, output="tb"))
    emmodel = import_class("emmodel", values["electromagnetic_model"])(
        sensor, snowpack.layers[0]
    )
    mu = math.cos(math.radians(values["angle_deg"]))
    ks = _scalar(emmodel.ks(mu))
    ka = _scalar(emmodel.ka)
    total = ks + ka
    return {
        "ks_per_m": ks,
        "ka_per_m": ka,
        "effective_permittivity": _scalar(emmodel.effective_permittivity),
        "single_scattering_albedo": ks / total if total > 0 else 0.0,
    }


def run(spec):
    _ensure_smrt_importable()
    from smrt import make_model

    coefficients_only = spec["output"] == "coefficients"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        def model_for(values):
            return make_model(
                values["electromagnetic_model"],
                "dort",
                rtsolver_options={"n_max_stream": int(round(values["dort_streams"]))},
            )
        swept = spec.get("sweep_parameter") or "none"

        if swept == "none":
            if coefficients_only:
                values = _coefficients(spec)
            else:
                result = model_for(spec).run(_sensor(spec), _snowpack(spec))
                values = _extract(result, spec["output"])
            return {
                "axis": None,
                "points": [{"index": 0, **values}],
                "series": {key: [value] for key, value in values.items()},
            }

        start = spec["sweep_start"]
        stop = spec["sweep_stop"]
        count = int(spec.get("sweep_points") or 10)
        step = (stop - start) / (count - 1) if count > 1 else 0.0
        axis_values = [start + step * i for i in range(count)]

        points = []
        series = {}
        for index, value in enumerate(axis_values):
            override = {swept: value}
            if coefficients_only:
                values = _coefficients(spec, override)
            else:
                values_for_run = dict(spec)
                values_for_run.update(override)
                result = model_for(values_for_run).run(
                    _sensor(spec, override), _snowpack(spec, override)
                )
                values = _extract(result, spec["output"])
            points.append({"index": index, swept: value, **values})
            for key, item in values.items():
                series.setdefault(key, []).append(item)

        return {
            "axis": {"name": swept, "values": axis_values},
            "points": points,
            "series": series,
        }

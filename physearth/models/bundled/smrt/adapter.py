import math
import warnings

MICROSTRUCTURE_ARGS = {
    "exponential": ("corr_length_m", "corr_length"),
    "teubner_strey": ("corr_length_m", "corr_length"),
    "gaussian_random_field": ("corr_length_m", "corr_length"),
    "independent_sphere": ("radius_m", "radius"),
    "sticky_hard_spheres": ("radius_m", "radius"),
}


def _snowpack(spec, overrides=None):
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
    from smrt import make_model

    coefficients_only = spec["output"] == "coefficients"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = None if coefficients_only else make_model(
            spec["electromagnetic_model"], "dort"
        )
        swept = spec.get("sweep_parameter") or "none"

        if swept == "none":
            if coefficients_only:
                values = _coefficients(spec)
            else:
                result = model.run(_sensor(spec), _snowpack(spec))
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
                result = model.run(_sensor(spec, override), _snowpack(spec, override))
                values = _extract(result, spec["output"])
            points.append({"index": index, swept: value, **values})
            for key, item in values.items():
                series.setdefault(key, []).append(item)

        return {
            "axis": {"name": swept, "values": axis_values},
            "points": points,
            "series": series,
        }

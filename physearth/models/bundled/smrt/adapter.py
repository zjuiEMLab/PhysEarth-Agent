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
        }
    return {"tb_v": float(result.TbV()), "tb_h": float(result.TbH())}


def run(spec):
    from smrt import make_model

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = make_model(spec["electromagnetic_model"], "dort")
        swept = spec.get("sweep_parameter") or "none"

        if swept == "none":
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

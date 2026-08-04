"""Reference evapotranspiration, through the pyet package.

Six published formulations of the same quantity, which is the point: they disagree, and
the declaration says which inputs each one is entitled to use. Nothing imports pyet at
module level.
"""

METHODS = ("penman", "pm", "priestley_taylor", "hargreaves", "makkink", "oudin")


def _require():
    try:
        import pandas
        import pyet
    except ImportError as exc:
        raise RuntimeError(
            "the pyet package is not installed in this environment, so reference "
            "evapotranspiration cannot be computed here."
        ) from exc
    return pyet, pandas


def _et0(values):
    pyet, pandas = _require()
    method = values["method"]
    series = lambda x: pandas.Series([float(x)])  # noqa: E731
    latitude = values["latitude_deg"] * 3.141592653589793 / 180.0
    common = {"tmean": series(values["air_temperature_c"])}
    if method == "hargreaves":
        out = pyet.hargreaves(
            tmax=series(values["tmax_c"]), tmin=series(values["tmin_c"]),
            lat=latitude, **common,
        )
    elif method == "oudin":
        out = pyet.oudin(lat=latitude, **common)
    elif method == "makkink":
        out = pyet.makkink(
            rs=series(values["solar_radiation_mj_m2_day"]),
            pressure=series(values["air_pressure_kpa"]), **common,
        )
    elif method == "priestley_taylor":
        out = pyet.priestley_taylor(
            rn=series(values["net_radiation_mj_m2_day"]),
            pressure=series(values["air_pressure_kpa"]), **common,
        )
    else:
        function = pyet.penman if method == "penman" else pyet.pm
        out = function(
            wind=series(values["wind_speed_m_s"]),
            rn=series(values["net_radiation_mj_m2_day"]),
            pressure=series(values["air_pressure_kpa"]),
            rh=series(values["relative_humidity_pct"]),
            **common,
        )
    return {"et0_mm_day": float(out.iloc[0])}


def run(spec):
    swept = spec.get("sweep_parameter") or "none"
    if swept == "none":
        values = _et0(spec)
        return {
            "axis": None,
            "points": [{"index": 0, **values}],
            "series": {key: [value] for key, value in values.items()},
        }
    start, stop = spec["sweep_start"], spec["sweep_stop"]
    count = int(spec.get("sweep_points") or 10)
    step = (stop - start) / (count - 1) if count > 1 else 0.0
    axis_values = [start + step * i for i in range(count)]
    points, series = [], {}
    for index, axis_value in enumerate(axis_values):
        local = dict(spec)
        local[swept] = axis_value
        computed = _et0(local)
        points.append({"index": index, swept: axis_value, **computed})
        for key, value in computed.items():
            series.setdefault(key, []).append(value)
    return {"axis": {"name": swept, "values": axis_values}, "points": points, "series": series}

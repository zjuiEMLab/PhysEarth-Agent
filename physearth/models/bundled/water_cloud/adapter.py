import math

FLOOR_DB = -60.0


def _to_db(linear):
    return 10.0 * math.log10(linear) if linear > 1e-12 else FLOOR_DB


def backscatter(values):
    theta = math.radians(values["angle_deg"])
    cos_theta = math.cos(theta)

    two_way_transmissivity = math.exp(
        -2.0 * values["coefficient_b"] * values["vegetation_water_kg_m2"] / cos_theta
    )

    veg_linear = (
        values["coefficient_a"]
        * values["vegetation_water_kg_m2"]
        * cos_theta
        * (1.0 - two_way_transmissivity)
    )

    soil_db = values["coefficient_c"] + values["coefficient_d"] * values["soil_moisture"]
    soil_linear = 10.0 ** (soil_db / 10.0)

    total_linear = veg_linear + two_way_transmissivity * soil_linear

    return {
        "sigma0_total_db": _to_db(total_linear),
        "sigma0_vegetation_db": _to_db(veg_linear),
        "sigma0_soil_db": soil_db,
        "two_way_transmissivity": two_way_transmissivity,
    }


def run(spec):
    swept = spec.get("sweep_parameter") or "none"
    if swept == "none":
        values = backscatter(spec)
        return {
            "axis": None,
            "points": [{"index": 0, **values}],
            "series": {key: [value] for key, value in values.items()},
        }

    start, stop = spec["sweep_start"], spec["sweep_stop"]
    count = int(spec.get("sweep_points") or 10)
    step = (stop - start) / (count - 1)
    axis_values = [start + step * i for i in range(count)]

    points, series = [], {}
    for index, axis_value in enumerate(axis_values):
        values = dict(spec)
        values[swept] = axis_value
        computed = backscatter(values)
        points.append({"index": index, swept: axis_value, **computed})
        for key, value in computed.items():
            series.setdefault(key, []).append(value)

    return {"axis": {"name": swept, "values": axis_values}, "points": points, "series": series}

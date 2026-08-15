import math


def _transmissivity(optical_depth, angle_deg):
    return math.exp(-optical_depth / math.cos(math.radians(angle_deg)))


def run(spec):
    swept = spec.get("sweep_parameter") or "none"
    if swept == "none":
        value = _transmissivity(spec["optical_depth"], spec["angle_deg"])
        return {
            "axis": None,
            "points": [{"index": 0, "transmissivity": value}],
            "series": {"transmissivity": [value]},
        }

    start, stop = spec["sweep_start"], spec["sweep_stop"]
    count = int(spec.get("sweep_points") or 10)
    step = (stop - start) / (count - 1)
    axis_values = [start + step * i for i in range(count)]

    points, series = [], {"transmissivity": []}
    for index, axis_value in enumerate(axis_values):
        values = dict(spec)
        values[swept] = axis_value
        value = _transmissivity(values["optical_depth"], values["angle_deg"])
        points.append({"index": index, swept: axis_value, "transmissivity": value})
        series["transmissivity"].append(value)

    return {"axis": {"name": swept, "values": axis_values}, "points": points, "series": series}

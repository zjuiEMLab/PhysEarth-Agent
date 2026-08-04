"""PROSPECT + 4SAIL canopy reflectance, through the prosail package.

The optical counterpart of the microwave models: the same vegetated surface, seen by a
different kind of sensor. Nothing here imports prosail at module level, so a host without
it registers the model and reports the absence rather than rejecting the whole card.
"""

BANDS = tuple(range(400, 2501))
INDEX = {wavelength: n for n, wavelength in enumerate(BANDS)}


def _require():
    try:
        import prosail
    except ImportError as exc:
        raise RuntimeError(
            "the prosail package is not installed in this environment, so canopy "
            "reflectance cannot be computed here."
        ) from exc
    return prosail


def _spectrum(values):
    prosail = _require()
    return prosail.run_prosail(
        n=values["leaf_structure"],
        cab=values["chlorophyll_ug_cm2"],
        car=values["carotenoid_ug_cm2"],
        cbrown=values["brown_pigment"],
        cw=values["equivalent_water_thickness_cm"],
        cm=values["dry_matter_g_cm2"],
        lai=values["leaf_area_index"],
        lidfa=values["average_leaf_angle_deg"],
        hspot=values["hot_spot"],
        tts=values["solar_zenith_deg"],
        tto=values["view_zenith_deg"],
        psi=values["relative_azimuth_deg"],
        ant=values["anthocyanin_ug_cm2"],
        rsoil=values["soil_brightness"],
        psoil=values["soil_moisture_fraction"],
        typelidf=2,
    )


def _outputs(values):
    reflectance = _spectrum(values)
    red = float(reflectance[INDEX[670]])
    nir = float(reflectance[INDEX[800]])
    green = float(reflectance[INDEX[550]])
    swir = float(reflectance[INDEX[1600]])
    total = nir + red
    return {
        "reflectance_green": green,
        "reflectance_red": red,
        "reflectance_nir": nir,
        "reflectance_swir": swir,
        "ndvi": (nir - red) / total if total > 0 else 0.0,
    }


def run(spec):
    swept = spec.get("sweep_parameter") or "none"
    if swept == "none":
        values = _outputs(spec)
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
        computed = _outputs(local)
        points.append({"index": index, swept: axis_value, **computed})
        for key, value in computed.items():
            series.setdefault(key, []).append(value)
    return {"axis": {"name": swept, "values": axis_values}, "points": points, "series": series}

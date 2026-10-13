import importlib
import math
import sys
import warnings

# Card parameter -> SMRT argument, per microstructure. Teubner-Strey and the Gaussian
# random field declare repeat_distance as a mandatory argument next to corr_length, so a
# single-argument mapping made every combination using them fail inside SMRT.
MICROSTRUCTURE_ARGS = {
    "exponential": (("corr_length_m", "corr_length"),),
    "teubner_strey": (
        ("corr_length_m", "corr_length"),
        ("repeat_distance_m", "repeat_distance"),
    ),
    "gaussian_random_field": (
        ("corr_length_m", "corr_length"),
        ("repeat_distance_m", "repeat_distance"),
    ),
    "independent_sphere": (("radius_m", "radius"),),
    "sticky_hard_spheres": (("radius_m", "radius"),),
    "non_sticky_hard_spheres": (("radius_m", "radius"),),
}

DORT_DIAGONALIZATION_METHODS = (None, "shur", "shur_forcedtriu")


def _is_dort_diagonalization_error(exc):
    """Whether SMRT explicitly says DORT's eigensolver was numerically unstable."""
    text = str(exc).lower()
    return (
        "diagonalization failed in dort" in text
        or "eigen vectors are complex" in text
        or "almost diagonal matrix" in text
    )


def _emmodel_options(values):
    """SMRT electromagnetic-model options; the dense-snow switch only when asked for."""
    if values.get("dense_snow_correction") == "auto":
        return {"dense_snow_correction": "auto"}
    return {}


def _run_with_dort_recovery(values, sensor, snowpack):
    """Retry numerical diagonalization without changing any physical parameter.

    SMRT itself recommends Schur decomposition for the active-mode failure handled here.
    These fallbacks change only the matrix algorithm.  Physical repairs such as changing
    grain radius or stickiness must go back through human plan review instead.
    """
    from smrt import make_model

    failures = []
    for method in DORT_DIAGONALIZATION_METHODS:
        options = {"n_max_stream": int(round(values["dort_streams"]))}
        if method is not None:
            options["diagonalization_method"] = method
        try:
            model = make_model(
                values["electromagnetic_model"],
                "dort",
                emmodel_options=_emmodel_options(values),
                rtsolver_options=options,
            )
            return model.run(sensor, snowpack), method, failures
        except Exception as exc:
            if not _is_dort_diagonalization_error(exc):
                raise
            failures.append(
                {
                    "method": method or "default",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
    raise RuntimeError(
        "DORT numerical recovery exhausted after default, shur and "
        "shur_forcedtriu diagonalization: %s" % failures[-1]["message"]
    )


def _ensure_numpy_trapezoid_alias():
    """Restore ``numpy.trapz`` for SMRT's Gaussian random field on NumPy 2.

    SMRT 1.5.1 integrates that autocorrelation function with ``np.trapz``, which NumPy 2.0
    removed after renaming it ``np.trapezoid``. The two are the same composite-trapezoid
    integrator with the same signature, so this restores the old name rather than changing
    any numerical behaviour. Without it every Gaussian-random-field combination the model
    card declares legal raises AttributeError inside SMRT.
    """
    import numpy

    if not hasattr(numpy, "trapz") and hasattr(numpy, "trapezoid"):
        numpy.trapz = numpy.trapezoid


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


def _substrate(values):
    """The ground under the snow, or None for snow over nothing.

    rough_soil is the soil of SMRT's own examples and of the seasonal-snow literature: the
    Wegmuller and Matzler (1999) rough-soil reflectivity for emission, and the IEM surface
    scattering of Fung et al. (1992) for backscatter, which Wegmuller's model cannot give. flat_soil is a
    Fresnel (specular) soil, the setup of the 89 to 243 GHz tundra studies. SMRT writes a lossy
    permittivity with a positive imaginary part, so the card's 0.5 is the papers' 4 - 0.5j.
    """
    kind = values.get("substrate", "none")
    if kind not in ("rough_soil", "flat_soil"):
        return None
    from smrt import make_soil

    permittivity = complex(values["soil_permittivity_real"], values["soil_permittivity_imag"])
    temperature = values.get("soil_temperature_k")
    if temperature is None:
        temperature = values["temperature_k"]  # unset: ground at the snow temperature
    if kind == "flat_soil":
        return make_soil("flat", permittivity, temperature=temperature)
    if values.get("output") == "sigma":
        return make_soil(
            "iem_fung92", permittivity, temperature=temperature,
            roughness_rms=values["soil_iem_rms_height_m"],
            corr_length=values["soil_iem_corr_length_m"],
            autocorrelation_function="exponential",
        )
    return make_soil(
        "soil_wegmuller", permittivity, temperature=temperature,
        roughness_rms=values["soil_roughness_rms_m"],
    )


def _swe_mm(values):
    """Snow water equivalent of the layer: kg m-2 of water, which is mm."""
    return values["thickness_m"] * values["density_kg_m3"]


def _snowpack(spec, overrides=None):
    _ensure_smrt_importable()
    _ensure_numpy_trapezoid_alias()
    from smrt import make_snowpack

    values = dict(spec)
    values.update(overrides or {})
    micro = values["microstructure_model"]
    smrt_micro = (
        "sticky_hard_spheres"
        if micro == "non_sticky_hard_spheres"
        else micro
    )
    kwargs = {
        "thickness": [values["thickness_m"]],
        "microstructure_model": smrt_micro,
        "density": [values["density_kg_m3"]],
        "temperature": [values["temperature_k"]],
    }
    for source_key, target_key in MICROSTRUCTURE_ARGS[micro]:
        kwargs[target_key] = [values[source_key]]
    if micro == "sticky_hard_spheres":
        kwargs["stickiness"] = [values["stickiness"]]
    elif micro == "non_sticky_hard_spheres":
        # SMRT represents the non-sticky limit as tau=infinity. Keep the public model
        # name explicit so plans can compare it independently from sticky hard spheres.
        kwargs["stickiness"] = [float("inf")]
    wetness = values.get("volumetric_liquid_water") or 0.0
    if wetness > 0:
        # SMRT switches the scatterers to Bohren-Huffman wet ice when liquid water is set.
        kwargs["volumetric_liquid_water"] = [wetness]
    substrate = _substrate(values)
    if substrate is not None:
        kwargs["substrate"] = substrate
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


def _output_names(output):
    if output == "sigma":
        return ("sigma_vv_db", "sigma_hh_db", "sigma_hv_db")
    return ("tb_v", "tb_h")


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
        sensor, snowpack.layers[0], **_emmodel_options(values)
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


def _unphysical(spec, overrides=None):
    """Why the medium itself is not physical under the chosen theory, or "".

    Short-range DMRT overestimates scattering for large grains or low stickiness until the
    absorption coefficient it derives goes negative and the albedo passes 1 (SMRT says so
    in its own DORT error). SMRT v1.0 failed there; with the numerical fallbacks below
    SMRT 1.5.1 returns a brightness temperature anyway -- 264.7 K at 585 um, which passes
    any range check. The coefficients show it before any solver runs.
    """
    try:
        coefficients = _coefficients(spec, overrides)
    except Exception:  # the solve will raise the real error
        return ""
    ka = coefficients["ka_per_m"]
    albedo = coefficients["single_scattering_albedo"]
    if ka < 0:
        return "negative absorption coefficient (ka = %.3g m-1)" % ka
    if albedo > 1:
        return "single scattering albedo above 1 (%.3f)" % albedo
    return _iem_invalid(dict(spec, **(overrides or {})), coefficients["effective_permittivity"])


def _iem_invalid(values, snow_permittivity):
    """Why the rough-soil backscatter model cannot represent this point, or "".

    SMRT's IEM only prints a warning outside its validity and returns a number anyway. The
    criterion is SMRT's own (iem_fung92.check_validity): k s < 3 and k s k l below the square
    root of the soil-to-snow permittivity ratio, with k the wavenumber in the snow.
    """
    if values.get("output") != "sigma" or values.get("substrate") != "rough_soil":
        return ""
    snow = max(float(snow_permittivity), 1.0)
    soil = abs(complex(values["soil_permittivity_real"], values["soil_permittivity_imag"]))
    k = 2 * math.pi * values["frequency_ghz"] * 1e9 / 299792458.0 * math.sqrt(snow)
    ks = k * values["soil_iem_rms_height_m"]
    kl = k * values["soil_iem_corr_length_m"]
    limit = math.sqrt(soil / snow)
    if ks > 3 or ks * kl > limit:
        return (
            "the rough-soil (IEM) backscatter model is outside its validity at %.4g GHz "
            "(k s k l = %.2f, limit %.2f); use 17.2 GHz or lower, a smoother soil, or "
            "substrate flat_soil" % (values["frequency_ghz"], ks * kl, limit)
        )
    return ""


def _sweep_values(spec):
    """The swept values: evenly spaced, or evenly spaced in log for sweep_scale=log."""
    start, stop = spec["sweep_start"], spec["sweep_stop"]
    count = int(spec.get("sweep_points") or 10)
    if spec.get("sweep_scale") == "log":
        if start <= 0 or stop <= 0:
            raise ValueError(
                "sweep_scale=log needs sweep_start and sweep_stop above zero, got %s and %s"
                % (start, stop)
            )
        if count == 1:
            return [float(start)]
        ratio = (stop / start) ** (1.0 / (count - 1))
        return [start * ratio ** i for i in range(count - 1)] + [float(stop)]
    step = (stop - start) / (count - 1) if count > 1 else 0.0
    return [start + step * i for i in range(count)]


def run(spec):
    _ensure_smrt_importable()

    coefficients_only = spec["output"] == "coefficients"
    invalid = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        swept = spec.get("sweep_parameter") or "none"
        recoveries = []

        if swept == "none":
            reason = "" if coefficients_only else _unphysical(spec)
            if reason:
                invalid.append({"axis": None, "value": None, "reason": reason})
                values = {key: float("nan") for key in _output_names(spec["output"])}
            elif coefficients_only:
                values = _coefficients(spec)
            else:
                result, method, failures = _run_with_dort_recovery(
                    spec, _sensor(spec), _snowpack(spec)
                )
                if method is not None:
                    recoveries.append(
                        {"axis": None, "value": None, "method": method, "attempts": failures}
                    )
                values = _extract(result, spec["output"])
            if not coefficients_only:
                values["swe_mm"] = _swe_mm(spec)
            return {
                "axis": None,
                "points": [{"index": 0, **values}],
                "series": {key: [value] for key, value in values.items()},
                "diagnostics": {"solver_recoveries": recoveries, "invalid_points": invalid},
            }

        axis_values = _sweep_values(spec)

        points = []
        series = {}
        for index, value in enumerate(axis_values):
            override = {swept: value}
            reason = "" if coefficients_only else _unphysical(spec, override)
            if reason:
                invalid.append({"axis": swept, "value": value, "reason": reason})
                values = {key: float("nan") for key in _output_names(spec["output"])}
            elif coefficients_only:
                values = _coefficients(spec, override)
            else:
                values_for_run = dict(spec)
                values_for_run.update(override)
                try:
                    result, method, failures = _run_with_dort_recovery(
                        values_for_run,
                        _sensor(spec, override),
                        _snowpack(spec, override),
                    )
                except RuntimeError as exc:
                    raise RuntimeError(
                        "SMRT sweep failed at %s=%s. %s" % (swept, value, exc)
                    ) from exc
                if method is not None:
                    recoveries.append(
                        {
                            "axis": swept,
                            "value": value,
                            "method": method,
                            "attempts": failures,
                        }
                    )
                values = _extract(result, spec["output"])
            if not coefficients_only:
                values["swe_mm"] = _swe_mm(dict(spec, **override))
            points.append({"index": index, swept: value, **values})
            for key, item in values.items():
                series.setdefault(key, []).append(item)

        return {
            "axis": {"name": swept, "values": axis_values},
            "points": points,
            "series": series,
            "diagnostics": {"solver_recoveries": recoveries, "invalid_points": invalid},
        }

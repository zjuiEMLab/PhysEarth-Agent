import cmath
import math

EPS_ICE_FREE_WATER_INF = 4.9
RHO_SOLID_SOIL = 2.66
EPS_SOLID_SOIL = 4.7
ALPHA = 0.65


def water_permittivity(frequency_ghz, temperature_c):
    """Debye relaxation for free water."""
    eps_s = 88.045 - 0.4147 * temperature_c + 6.295e-4 * temperature_c**2
    relaxation_ns = (1.1109e-1 - 3.824e-3 * temperature_c + 6.938e-5 * temperature_c**2) / (2 * math.pi)
    omega_tau = 2 * math.pi * frequency_ghz * relaxation_ns
    real = EPS_ICE_FREE_WATER_INF + (eps_s - EPS_ICE_FREE_WATER_INF) / (1 + omega_tau**2)
    imag = (eps_s - EPS_ICE_FREE_WATER_INF) * omega_tau / (1 + omega_tau**2)
    return complex(real, imag)


def soil_permittivity(moisture, bulk_density, frequency_ghz, temperature_c):
    """Refractive mixing model of the Dobson family."""
    water = water_permittivity(frequency_ghz, temperature_c)
    mixture = (
        1.0
        + (bulk_density / RHO_SOLID_SOIL) * (EPS_SOLID_SOIL**ALPHA - 1.0)
        + moisture**ALPHA * (water**ALPHA)
        - moisture
    )
    return mixture ** (1.0 / ALPHA)


def fresnel_reflectivity(permittivity, angle_deg):
    theta = math.radians(angle_deg)
    cos_i = math.cos(theta)
    root = cmath.sqrt(permittivity - math.sin(theta) ** 2)
    r_h = (cos_i - root) / (cos_i + root)
    r_v = (permittivity * cos_i - root) / (permittivity * cos_i + root)
    return abs(r_h) ** 2, abs(r_v) ** 2


def rough_reflectivity(r_h, r_v, roughness_h, cross_q, angle_deg):
    theta = math.radians(angle_deg)
    damping = math.exp(-roughness_h * math.cos(theta) ** 2)
    rough_h = ((1.0 - cross_q) * r_h + cross_q * r_v) * damping
    rough_v = ((1.0 - cross_q) * r_v + cross_q * r_h) * damping
    return rough_h, rough_v


def brightness(values):
    permittivity = soil_permittivity(
        values["soil_moisture"],
        values["bulk_density_g_cm3"],
        values["frequency_ghz"],
        values["soil_temperature_k"] - 273.15,
    )
    r_h, r_v = fresnel_reflectivity(permittivity, values["angle_deg"])
    r_h, r_v = rough_reflectivity(r_h, r_v, values["roughness_h"], values["cross_q"], values["angle_deg"])

    theta = math.radians(values["angle_deg"])
    transmissivity = math.exp(-values["vegetation_optical_depth"] / math.cos(theta))
    albedo = values["single_scattering_albedo"]
    soil_t = values["soil_temperature_k"]
    canopy_t = values["canopy_temperature_k"]

    out = {}
    for pol, reflectivity in (("h", r_h), ("v", r_v)):
        emissivity = 1.0 - reflectivity
        soil_term = soil_t * emissivity * transmissivity
        canopy_up = canopy_t * (1.0 - albedo) * (1.0 - transmissivity)
        canopy_down = canopy_up * reflectivity * transmissivity
        out["tb_" + pol] = soil_term + canopy_up + canopy_down
    out["emissivity_h"] = 1.0 - r_h
    out["emissivity_v"] = 1.0 - r_v
    return out


def run(spec):
    swept = spec.get("sweep_parameter") or "none"
    if swept == "none":
        values = brightness(spec)
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
        computed = brightness(values)
        points.append({"index": index, swept: axis_value, **computed})
        for key, value in computed.items():
            series.setdefault(key, []).append(value)

    return {"axis": {"name": swept, "values": axis_values}, "points": points, "series": series}

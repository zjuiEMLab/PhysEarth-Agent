"""Closed-form identities a bundled model must satisfy.

These are the part of Tier 0 that does not depend on how any adapter is written. Each
function re-derives one relation from the published equations and compares it with what
the model returned, so a rewrite of the adapter that changes the physics fails here even
if every pinned number is updated to match.

Each takes (spec, series) and returns (passed, detail). `series` maps an output name to
its list of values, which for a single point is a list of one.
"""

import math

EXACT = 1.0e-12
TIGHT = 1.0e-9


def _first(series, name):
    values = series.get(name)
    return values[0] if values else None


def bare_soil_tb_is_soil_temperature_times_emissivity(spec, series, run):
    """With no canopy, tau-omega collapses to Tb_p = T_soil * e_p at both polarisations.

    The albedo goes to zero with the optical depth because the model card refuses the
    pair otherwise, which is the card doing its job on the evaluation suite as well.
    """
    bare = run(dict(spec, vegetation_optical_depth=0.0, single_scattering_albedo=0.0))
    soil_t = spec["soil_temperature_k"]
    worst, detail = 0.0, []
    for pol in ("v", "h"):
        emissivity = _first(bare, "emissivity_" + pol)
        expected = soil_t * emissivity
        got = _first(bare, "tb_" + pol)
        worst = max(worst, abs(got - expected))
        detail.append("tb_%s %.9f vs T*e %.9f" % (pol, got, expected))
    return worst <= TIGHT, "; ".join(detail)


def emissivity_stays_between_zero_and_one(spec, series, run):
    out = []
    for pol in ("v", "h"):
        value = _first(series, "emissivity_" + pol)
        out.append("emissivity_%s = %.6f" % (pol, value))
        if not 0.0 < value < 1.0:
            return False, "; ".join(out)
    return True, "; ".join(out)


def bare_soil_backscatter_is_the_soil_law(spec, series, run):
    """With no vegetation water the water cloud model is exactly C + D * mv."""
    bare = run(dict(spec, vegetation_water_kg_m2=0.0, coefficient_a=0.0))
    expected = spec["coefficient_c"] + spec["coefficient_d"] * spec["soil_moisture"]
    got = _first(bare, "sigma0_total_db")
    return abs(got - expected) <= EXACT, "total %.12f vs C + D*mv %.12f" % (got, expected)


def transmissivity_is_beer_lambert(spec, series, run):
    expected = math.exp(
        -2.0
        * spec["coefficient_b"]
        * spec["vegetation_water_kg_m2"]
        / math.cos(math.radians(spec["angle_deg"]))
    )
    got = _first(series, "two_way_transmissivity")
    return abs(got - expected) <= EXACT, "gamma2 %.12f vs exp(-2BW/cos) %.12f" % (got, expected)


def total_backscatter_exceeds_neither_component_sum(spec, series, run):
    """The canopy attenuates the soil term, so the total is below the undamped sum."""
    total = 10.0 ** (_first(series, "sigma0_total_db") / 10.0)
    veg = 10.0 ** (_first(series, "sigma0_vegetation_db") / 10.0)
    soil = 10.0 ** (_first(series, "sigma0_soil_db") / 10.0)
    return total <= veg + soil + EXACT, "total %.9f, veg + soil %.9f" % (total, veg + soil)


def albedo_is_scattering_over_extinction(spec, series, run):
    """A definition, not a measurement: the albedo must be ks over ks plus ka."""
    ks = _first(series, "ks_per_m")
    ka = _first(series, "ka_per_m")
    albedo = _first(series, "single_scattering_albedo")
    if ks is None or ka is None or albedo is None:
        return False, "the run did not return the coefficients"
    expected = ks / (ks + ka)
    return abs(albedo - expected) <= TIGHT, "albedo %.9f vs ks/(ks+ka) %.9f" % (albedo, expected)


REGISTRY = {
    name: value
    for name, value in list(globals().items())
    if callable(value) and not name.startswith("_") and name not in ("math",)
}

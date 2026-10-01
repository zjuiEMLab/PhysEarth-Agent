"""Closed-form identities a bundled model must satisfy.

These are the part of Tier 0 that does not depend on how any adapter is written. Each
function re-derives one relation from the published equations and compares it with what
the model returned, so a rewrite of the adapter that changes the physics fails here even
if every pinned number is updated to match.

Each takes (spec, series) and returns (passed, detail). `series` maps an output name to
its list of values, which for a single point is a list of one.
"""

import calendar
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


def near_infrared_exceeds_red_for_a_green_canopy(spec, series, run):
    """The red edge. A green canopy absorbs red and scatters near infrared, and the gap
    between them is what every vegetation index is built on."""
    red = _first(series, "reflectance_red")
    nir = _first(series, "reflectance_nir")
    if red is None or nir is None:
        return False, "the run did not return both bands"
    return nir > red * 3.0, "nir %.4f, red %.4f, ratio %.2f" % (nir, red, nir / red if red else 0)


def _water_year_month_lengths(spec):
    lengths = []
    for year in range(spec["water_year_start"], spec["water_year_end"] + 1):
        february = 29 if calendar.isleap(year) else 28
        lengths += [31, 30, 31, 31, february, 31, 30, 31, 30, 31, 31, 30]
    return lengths


def _means(values, lengths):
    means, at = [], 0
    for n in lengths:
        means.append(sum(values[at:at + n]) / n)
        at += n
    return means


def _mean_agreement(got, expected):
    if len(got) != len(expected):
        return False, f"{len(got)} values for {len(expected)} periods"
    worst = max(abs(a - b) for a, b in zip(got, expected, strict=True))
    scale = max(1.0, max(abs(b) for b in expected))
    return worst <= TIGHT * scale, f"{len(got)} periods, largest difference {worst:.3g} mm"


def monthly_values_are_the_means_of_the_daily_series(spec, series, run):
    """PRMS steps daily; the monthly series is the adapter's own aggregate of it, so each
    value must be the plain mean of that calendar month's daily values."""
    daily = run(dict(spec, aggregation="daily"))["value"]
    lengths = _water_year_month_lengths(spec)
    if len(daily) != sum(lengths):
        return False, f"{len(daily)} daily values for {sum(lengths)} days"
    monthly = run(dict(spec, aggregation="monthly"))["value"]
    return _mean_agreement(monthly, _means(daily, lengths))


def water_year_value_is_the_mean_of_the_daily_series(spec, series, run):
    """A water-year value is the mean of the 365 or 366 daily values from 1 October."""
    daily = run(dict(spec, aggregation="daily"))["value"]
    months = _water_year_month_lengths(spec)
    years = [sum(months[n:n + 12]) for n in range(0, len(months), 12)]
    if len(daily) != sum(years):
        return False, f"{len(daily)} daily values for {sum(years)} days"
    yearly = run(dict(spec, aggregation="water_year"))["value"]
    return _mean_agreement(yearly, _means(daily, years))


def snowmelt_never_exceeds_the_water_that_fell(spec, series, run):
    """Mass conservation: a snowpack cannot release more water than fell on the basin plus
    what it held at the start. The first day's store plus its melt bounds the initial one."""
    daily = dict(spec, aggregation="daily")
    melt = run(dict(daily, variable="snowmelt"))["value"]
    precipitation = run(dict(daily, variable="precipitation"))["value"]
    swe = run(dict(daily, variable="snowpack_water_equivalent"))["value"]
    if not melt or not precipitation or not swe:
        return False, "the runs returned no daily values"
    budget = sum(precipitation) + swe[0] + melt[0]
    return sum(melt) <= budget + TIGHT * max(1.0, budget), (
        f"melt {sum(melt):.3f} mm <= precipitation {sum(precipitation):.3f} mm "
        f"+ initial store {swe[0] + melt[0]:.3f} mm"
    )


REGISTRY = {
    name: value
    for name, value in list(globals().items())
    if callable(value) and not name.startswith("_") and name not in ("calendar", "math")
}

"""U.S. Standard Atmosphere, 1976 (NOAA-S/T 76-1562; NASA-TM-X-74335), -5 to 1000 km.

The equations and constants are the Standard's own, section 1 ("Defining
constants and equations"). The input is geometric altitude Z. Three
formulations meet at the Standard's own boundaries:

**Lower atmosphere, -5 km <= Z <= 80 km: hydrostatic, M = M0.** The
temperature profile is defined in geopotential altitude H (eq. 18,
Gamma = 1 m'/m)::

    H = r0 Z / (r0 + Z),        Z = r0 H / (r0 - H)              (18), (19)

and the two are never treated as equal: at Z = 11 000 m, H = 10 981 m', still
in the first layer. Table 4's layers carry a linear TM (eq. 23). Pressure comes
from (33a) where LM,b is not zero and (33b) where it is, with base pressures
from those same equations at each base. Then T = TM, rho = P M0/(R* TM) (42),
N = N_A P/(R* T) (41), Cs = (gamma R* TM/M0)^1/2 (50) and
mu = beta T^3/2/(T + S) (51). Table I begins at Z = -5 000 m.

**Transition, 80 km < Z < 86 km: hydrostatic, M/M0 from Table 8.** P, rho and
Cs are unchanged in form: they depend on TM only. The mean molecular weight
falls from M0 at 80 km to 28.9522 at 86 km. The Standard defines that fall only
as the arbitrarily assigned ratio M/M0 of Table 8, at 0.5 km geometric
intervals, and gives no formula between them. Here it is interpolated linearly
in Z between the Standard's nodes, which is the only reading that uses no
other data. T = TM M/M0 (eq. 22), and mu uses that corrected T, as section
1.2.4 asks for. The Standard's own printed tables in 80-86 km were computed
without this correction (section 1.2.4), so kinetic T, M, N and mu here differ
from them by up to 0.04 %. P, rho and Cs do not.

**Upper atmosphere, 86 km <= Z <= 1000 km: diffusive, per species.** The
species equations of section 1.3 (:mod:`.ussa1976_upper`). P = N k T (33c),
rho = sum n_i M_i / N_A (42), M = sum n_i M_i / N, and TM = T M0/M. Speed of
sound and dynamic viscosity are not defined above 86 km. The Standard
terminates both there (sections 1.3.10, 1.3.11), so they are absent, with that
reason. At 86 km itself they are given, from eqs. 50 and 51, as the Standard
tabulates them.

Outside -5 000 m to 1 000 000 m a state is refused, never clamped.

**Constants** are the Standard's defining-text values
(:mod:`._ussa1976_constants`): not Table 2's misprints, and not CODATA.
"""

from __future__ import annotations

import bisect
import math
from typing import Final

from rocketforge.core.result import Solution, Status

from . import ussa1976_upper as upper
from ._ussa1976_constants import (
    AVOGADRO,
    BETA,
    G0,
    G0_PRIME,
    GAMMA,
    M0,
    P0,
    R0,
    R_STAR,
    SUTHERLAND_S,
    T0,
)
from .state import AtmosphereState, is_number, refuse

__all__ = [
    "BETA",
    "GAMMA",
    "GEOMETRIC_ALTITUDE_RANGE",
    "LAYERS",
    "LOWER_ATMOSPHERE_TOP",
    "M0",
    "MODEL",
    "MODEL_NAME",
    "MODEL_VERSION",
    "MOLECULAR_WEIGHT_RATIO",
    "P0",
    "R0",
    "R_STAR",
    "SUTHERLAND_S",
    "T0",
    "UPPER_ATMOSPHERE_BASE",
    "geometric_altitude",
    "geopotential_altitude",
    "state",
    "state_at_geopotential",
]

MODEL: Final = "ussa1976"
MODEL_NAME: Final = "U.S. Standard Atmosphere, 1976"
MODEL_VERSION: Final = "1976 (NOAA-S/T 76-1562), -5 km to 1000 km geometric"

#: Table 4: base geopotential height Hb (m') and gradient LM,b (K/m').
LAYERS: Final = ((0.0, -6.5e-3), (11000.0, 0.0), (20000.0, 1.0e-3), (32000.0, 2.8e-3),
                 (47000.0, 0.0), (51000.0, -2.8e-3), (71000.0, -2.0e-3))

#: Table 8, right-hand columns: M/M0 at geometric Z (m), the values "initially
#: selected for intervals of 0.5 geometric kilometres" (section 1.2.4).
MOLECULAR_WEIGHT_RATIO: Final = (
    (80000.0, 1.000000), (80500.0, 0.999996), (81000.0, 0.999989), (81500.0, 0.999971),
    (82000.0, 0.999941), (82500.0, 0.999909), (83000.0, 0.999870), (83500.0, 0.999829),
    (84000.0, 0.999786), (84500.0, 0.999741), (85000.0, 0.999694), (85500.0, 0.999641),
    (86000.0, 0.999579))

LOWER_ATMOSPHERE_TOP: Final = 80000.0         # m: M = M0 at and below
UPPER_ATMOSPHERE_BASE: Final = 86000.0        # m: Z7
#: The supported geometric altitude range, m, inclusive.
GEOMETRIC_ALTITUDE_RANGE: Final = (-5000.0, 1000000.0)

_LOWER = "lower: hydrostatic, M = M0 (Z <= 80 km)"
_TRANSITION = "transition: hydrostatic, M/M0 from Table 8 (80 < Z < 86 km)"
_UPPER = "upper: diffusive, species from eqs. 35-40 (86 <= Z <= 1000 km)"
_NO_COMPOSITION = ("The Standard tabulates composition from 86 km (Table VIII). "
                   "Below, the air is mixed at the Table 3 fractions, which this build "
                   "does not report.")
_NO_SOUND = ("Not defined above 86 km: the Standard's speed of sound (eq. 50) applies "
             "only while sound is a small perturbation, and its tables terminate at "
             "86 km (section 1.3.10).")
_NO_VISCOSITY = ("Not defined above 86 km: eq. 51 fails at very high and very low "
                 "temperatures, and the Standard terminates it at 86 km (section 1.3.11).")


def geopotential_altitude(geometric: float) -> float:
    """H (m') from Z (m), eq. (18)."""
    return R0 * geometric / (R0 + geometric)


def geometric_altitude(geopotential: float) -> float:
    """Z (m) from H (m'), eq. (19)."""
    return R0 * geopotential / (R0 - geopotential)


def _pressure(base_pressure: float, base_temperature: float, gradient: float,
              dh: float) -> float:
    if gradient == 0.0:
        return base_pressure * math.exp(-G0_PRIME * M0 * dh / (R_STAR * base_temperature))
    return base_pressure * (base_temperature / (base_temperature + gradient * dh)) ** (
        G0_PRIME * M0 / (R_STAR * gradient))


def _bases() -> tuple[tuple[float, float, float, float], ...]:
    """(Hb, LM,b, TM,b, Pb) per layer: TM,b from eq. (23), Pb from (33a)/(33b)."""
    bases = []
    temperature, pressure = T0, P0
    for index, (height, gradient) in enumerate(LAYERS):
        bases.append((height, gradient, temperature, pressure))
        if index + 1 < len(LAYERS):
            dh = LAYERS[index + 1][0] - height
            pressure = _pressure(pressure, temperature, gradient, dh)
            temperature = temperature + gradient * dh
    return tuple(bases)


_BASES: Final = _bases()
_H_RANGE: Final = tuple(geopotential_altitude(z) for z in GEOMETRIC_ALTITUDE_RANGE)


def _layer(h: float) -> int:
    index = 0
    for i, (height, *_rest) in enumerate(_BASES):
        if h >= height:
            index = i
    return index


def _hydrostatic(h: float) -> tuple[int, float, float]:
    """(layer, TM, P) at geopotential altitude h, eqs. (23) and (33a/b)."""
    index = _layer(h)
    height, gradient, base_temperature, base_pressure = _BASES[index]
    return (index, base_temperature + gradient * (h - height),
            _pressure(base_pressure, base_temperature, gradient, h - height))


def _ratio(z: float) -> float:
    """M/M0 at 80 km <= z <= 86 km: linear between Table 8's geometric nodes."""
    zs = [node for node, _ in MOLECULAR_WEIGHT_RATIO]
    i = min(max(bisect.bisect_right(zs, z) - 1, 0), len(zs) - 2)
    (z0, r0_), (z1, r1) = MOLECULAR_WEIGHT_RATIO[i], MOLECULAR_WEIGHT_RATIO[i + 1]
    return r0_ + (r1 - r0_) * (z - z0) / (z1 - z0)


def _lower(h: float, z: float, inputs: dict[str, float]) -> AtmosphereState:
    index, temperature, pressure = _hydrostatic(h)                 # T = TM here
    return AtmosphereState(
        model=MODEL, model_name=MODEL_NAME, model_version=MODEL_VERSION,
        pressure=pressure, geometric_altitude=z, geopotential_altitude=h,
        temperature=temperature,
        density=pressure * M0 / (R_STAR * temperature),
        speed_of_sound=math.sqrt(GAMMA * R_STAR * temperature / M0),
        dynamic_viscosity=BETA * temperature ** 1.5 / (temperature + SUTHERLAND_S),
        layer=index, inputs=inputs,
        provenance=(f"{MODEL_NAME}: eqs. (18), (23), (33a/b), (42), (50), (51); "
                    f"layer {index} of Table 4"),
        molecular_scale_temperature=temperature,
        number_density=AVOGADRO * pressure / (R_STAR * temperature),
        mean_molar_mass=M0, regime=_LOWER,
        unavailable={"species_number_densities": _NO_COMPOSITION})


def _transition(h: float, z: float, inputs: dict[str, float]) -> AtmosphereState:
    index, tm, pressure = _hydrostatic(h)
    ratio = _ratio(z)
    temperature = tm * ratio                                        # eq. 22
    return AtmosphereState(
        model=MODEL, model_name=MODEL_NAME, model_version=MODEL_VERSION,
        pressure=pressure, geometric_altitude=z, geopotential_altitude=h,
        temperature=temperature,
        density=pressure * M0 / (R_STAR * tm),                      # eq. 42, exact
        speed_of_sound=math.sqrt(GAMMA * R_STAR * tm / M0),         # eq. 50, exact
        dynamic_viscosity=BETA * temperature ** 1.5 / (temperature + SUTHERLAND_S),
        layer=index, inputs=inputs,
        provenance=(f"{MODEL_NAME}: eqs. (18), (22), (23), (33a/b), (41), (42), (50), "
                    "(51); M/M0 linear between the Table 8 geometric nodes"),
        molecular_scale_temperature=tm,
        number_density=AVOGADRO * pressure / (R_STAR * temperature),   # eq. 41
        mean_molar_mass=M0 * ratio, regime=_TRANSITION,
        unavailable={"species_number_densities": _NO_COMPOSITION})


def _segment(z_km: float) -> int:
    """Table 5's subscript b for the upper temperature segments."""
    return 7 if z_km < 91.0 else 8 if z_km < 110.0 else 9 if z_km < 120.0 else 10


def _upper(z: float, inputs: dict[str, float]) -> AtmosphereState:
    z_km = z / 1000.0
    temperature = upper.temperature(z_km)
    species = upper.species(z_km)
    number = sum(species.values())
    mass = sum(n * upper.MOLAR_MASS[name] for name, n in species.items())
    molar_mass = mass / number
    at_base = z == UPPER_ATMOSPHERE_BASE
    unavailable = {} if at_base else {"speed_of_sound": _NO_SOUND,
                                      "dynamic_viscosity": _NO_VISCOSITY}
    return AtmosphereState(
        model=MODEL, model_name=MODEL_NAME, model_version=MODEL_VERSION,
        pressure=number * upper.BOLTZMANN * temperature,            # eq. 33c
        geometric_altitude=z, geopotential_altitude=geopotential_altitude(z),
        temperature=temperature,
        density=mass / AVOGADRO,                                    # eq. 42
        speed_of_sound=(math.sqrt(GAMMA * R_STAR * temperature / molar_mass)
                        if at_base else None),
        dynamic_viscosity=(BETA * temperature ** 1.5 / (temperature + SUTHERLAND_S)
                           if at_base else None),
        layer=_segment(z_km), inputs=inputs,
        provenance=(f"{MODEL_NAME}: eqs. (25)-(40), (20), (33c), (42); segment "
                    f"{_segment(z_km)} of Table 5; species integrated from Table 9"),
        molecular_scale_temperature=temperature * M0 / molar_mass,
        number_density=number, mean_molar_mass=molar_mass,
        species_number_densities=species, regime=_UPPER, unavailable=unavailable)


def _resolve(z: float, h: float, inputs: dict[str, float]) -> AtmosphereState:
    if z <= LOWER_ATMOSPHERE_TOP:
        return _lower(h, z, inputs)
    if z < UPPER_ATMOSPHERE_BASE:
        return _transition(h, z, inputs)
    return _upper(z, inputs)


def state(geometric: float) -> Solution[AtmosphereState]:
    """The Standard atmosphere at geometric altitude ``geometric`` (m)."""
    low, high = GEOMETRIC_ALTITUDE_RANGE
    if not (is_number(geometric) and math.isfinite(geometric)):
        return refuse("ALTITUDE_INVALID", "The altitude must be a finite number.",
                      "geometric_altitude")
    if not low <= geometric <= high:
        return refuse(
            "ALTITUDE_OUT_OF_RANGE",
            f"{MODEL_NAME} is defined from {low:g} m to {high:g} m geometric altitude; "
            f"{geometric:g} m is outside it. Nothing is extrapolated.",
            "geometric_altitude",
            {"geometric_altitude": float(geometric), "minimum": low, "maximum": high})
    z = float(geometric)
    return Solution(value=_resolve(z, geopotential_altitude(z), {"geometric_altitude": z}),
                    status=Status.OK)


def state_at_geopotential(geopotential: float) -> Solution[AtmosphereState]:
    """The Standard atmosphere at geopotential altitude ``geopotential`` (m').

    Same range as :func:`state`, expressed in H. Above 86 km the Standard is
    defined in Z; H is converted with eq. (19).
    """
    low, high = _H_RANGE
    if not (is_number(geopotential) and math.isfinite(geopotential)):
        return refuse("ALTITUDE_INVALID", "The altitude must be a finite number.",
                      "geopotential_altitude")
    if not low <= geopotential <= high:
        return refuse(
            "ALTITUDE_OUT_OF_RANGE",
            f"{MODEL_NAME} is defined from H = {low:.6g} m' to {high:.6g} m' "
            f"(Z = {GEOMETRIC_ALTITUDE_RANGE[0]:g} m to {GEOMETRIC_ALTITUDE_RANGE[1]:g} m); "
            f"{geopotential:g} m' is outside it.",
            "geopotential_altitude",
            {"geopotential_altitude": float(geopotential), "minimum": low, "maximum": high})
    h = float(geopotential)
    # h is in range, so Z is too; only the inverse's last-bit rounding at the
    # two ends is held to the range here. No input is changed.
    z = min(max(geometric_altitude(h), GEOMETRIC_ALTITUDE_RANGE[0]),
            GEOMETRIC_ALTITUDE_RANGE[1])
    return Solution(value=_resolve(z, h, {"geopotential_altitude": h}), status=Status.OK)

"""NASA CEA's native rocket outputs, kept deliberately outside the domain.

CEA returns c*, Cf and Isp. RocketForge does **not** own those yet, and this
module is how both facts stay true at once.

The boundary, stated plainly:

* :class:`CEARocketOracle` is a **provider-native reference record**. It is not
  a RocketForge physics result, it is not a ``ChamberGas``, and nothing in
  ``physics`` or ``engineering`` consumes it.
* Rocket performance ownership belongs to a future ``engineering.nozzle``
  (ADR-15). When that arrives, Phase 5E will compare RocketForge's own c*, Cf
  and Isp against the values recorded here.
* Because that comparison has to be like-for-like, this record carries the
  **exact conditions** each value was produced under -- chamber pressure, area
  ratio, chemistry mode, freeze station -- rather than the bare numbers.

Nothing in this module is imported by :mod:`~rocketforge.providers.cea.provider`.
It exists for validation, reference-artifact generation and future
cross-checking, and it is reachable only by asking for it explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import ModuleType

import numpy as np

from rocketforge.physics.thermochemistry import ExpansionMode, FreezeLocation

from .errors import translate_cea_exception
from .units import (
    molar_mass_to_si,
    pressure_from_bar,
    pressure_to_bar,
    specific_heat_to_si,
)

__all__ = ["CEARocketOracle", "CEARocketStation", "run_rocket_oracle"]


@dataclass(frozen=True, slots=True)
class CEARocketStation:
    """One station of a CEA rocket solution, in SI.

    Chamber, throat and exit are stations 0, 1 and 2 of an infinite-area
    combustor solve with a single supersonic area ratio.
    """

    temperature: float          # K
    pressure: float             # Pa
    molar_mass: float           # kg/mol
    gamma_s: float              # equilibrium isentropic exponent
    mach: float
    area_ratio: float           # Ae/At at this station


@dataclass(frozen=True, slots=True)
class CEARocketOracle:
    """CEA's native rocket answer, with the conditions that produced it.

    Attributes:
        c_star: Characteristic velocity, m/s. A chamber quantity; CEA reports
            the same value at every station.
        thrust_coefficient: Cf at the exit station, dimensionless.
        specific_impulse: Effective exhaust velocity at the exit, **m/s**.
            Phase 5B-0 established the unit by identity: ``Isp == Cf * c*``
            exactly. Divide by 9.80665 for the value in seconds.
        specific_impulse_vacuum: The vacuum figure, m/s.
        stations: Chamber, throat and exit.
        expansion_mode: Which chemistry assumption produced these numbers.
        freeze_location: Where composition was frozen, or ``None`` for a
            shifting-equilibrium expansion.
        chamber_pressure: Pa, as supplied.
        area_ratio: The supersonic area ratio the exit station was solved at.
        reactant_temperatures: K, per reactant, as supplied.
        of_ratio: Oxidiser mass over fuel mass.
        species_set: The product species the solve was restricted to.

    The conditions are not decoration. An Isp compared against another Isp
    without matching chamber pressure, area ratio, chemistry mode and freeze
    station is a comparison of two different questions.
    """

    c_star: float
    thrust_coefficient: float
    specific_impulse: float
    specific_impulse_vacuum: float
    stations: tuple[CEARocketStation, ...]
    expansion_mode: ExpansionMode
    freeze_location: FreezeLocation | None
    chamber_pressure: float
    area_ratio: float
    reactant_temperatures: tuple[float, ...]
    of_ratio: float
    species_set: tuple[str, ...]

    @property
    def specific_impulse_seconds(self) -> float:
        """Isp expressed in seconds, for comparison with published tables."""
        return self.specific_impulse / 9.80665

    @property
    def chamber(self) -> CEARocketStation:
        return self.stations[0]

    @property
    def exit(self) -> CEARocketStation:
        return self.stations[-1]


#: CEA's ``n_frz`` selects the station at which composition freezes. Station 1
#: is the chamber and station 2 is the throat in an infinite-area-combustor
#: solve. The raw integer never leaves this module: RocketForge's public
#: vocabulary is :class:`FreezeLocation` (5C brief section 196, 207).
_FREEZE_STATION: dict[FreezeLocation, int] = {
    FreezeLocation.CHAMBER: 1,
    FreezeLocation.THROAT: 2,
}


def run_rocket_oracle(
    cea_module: ModuleType,
    *,
    fuel_names: tuple[str, ...],
    oxidiser_names: tuple[str, ...],
    fuel_weights: tuple[float, ...],
    oxidiser_weights: tuple[float, ...],
    reactant_temperatures: tuple[float, ...],
    of_ratio: float,
    chamber_pressure: float,
    area_ratio: float,
    product_species: tuple[str, ...],
    expansion_mode: ExpansionMode = ExpansionMode.EQUILIBRIUM,
) -> CEARocketOracle:
    """Run one native CEA rocket case and record it with its conditions.

    Used by validation and reference-artifact generation. Not part of the
    production chamber path, and not reachable from a ``ChamberGas``.
    """
    names = list(fuel_names) + list(oxidiser_names)
    n_fuel = len(fuel_names)
    fuel_vector = np.array(list(fuel_weights) + [0.0] * len(oxidiser_names),
                           dtype=float)
    oxid_vector = np.array([0.0] * n_fuel + list(oxidiser_weights), dtype=float)

    try:
        reactants = cea_module.Mixture(names)
        products = cea_module.Mixture(list(product_species))
        solver = cea_module.RocketSolver(products, reactants=reactants)
        solution = cea_module.RocketSolution(solver)
        weights = reactants.of_ratio_to_weights(oxid_vector, fuel_vector,
                                                float(of_ratio))
        chamber_enthalpy = reactants.calc_property(
            cea_module.ENTHALPY, weights, list(reactant_temperatures)) / cea_module.R

        options: dict[str, object] = {
            "supar": float(area_ratio),
            "hc": chamber_enthalpy,
        }
        freeze = expansion_mode.freeze_location
        if freeze is not None:
            options["n_frz"] = _FREEZE_STATION[freeze]
        solver.solve(solution, weights, pressure_to_bar(chamber_pressure), **options)
    except Exception as exc:  # noqa: BLE001
        raise translate_cea_exception(exc, "running the rocket oracle case") from exc

    stations = tuple(
        CEARocketStation(
            temperature=float(solution.T[i]),
            pressure=pressure_from_bar(float(solution.P[i])),
            molar_mass=molar_mass_to_si(float(solution.MW[i])),
            gamma_s=float(solution.gamma_s[i]),
            mach=float(solution.Mach[i]),
            area_ratio=float(solution.ae_at[i]),
        )
        for i in range(int(solution.num_pts))
    )

    return CEARocketOracle(
        c_star=float(solution.c_star[0]),
        thrust_coefficient=float(solution.coefficient_of_thrust[-1]),
        specific_impulse=float(solution.Isp[-1]),
        specific_impulse_vacuum=float(solution.Isp_vacuum[-1]),
        stations=stations,
        expansion_mode=expansion_mode,
        freeze_location=freeze,
        chamber_pressure=float(chamber_pressure),
        area_ratio=float(area_ratio),
        reactant_temperatures=tuple(float(t) for t in reactant_temperatures),
        of_ratio=float(of_ratio),
        species_set=tuple(product_species),
    )

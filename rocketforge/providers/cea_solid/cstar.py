"""NASA CEA equilibrium characteristic velocity for a solid formulation.

c* is a chamber-and-throat quantity. It says how effectively the chamber
produces mass flow through a throat of given area at a given pressure; it
involves no nozzle expansion, and it is **not** a motor specific impulse, not a
thrust, and not anything a motor delivers.

**Why this module is separate, and the only place the rocket solver appears.**
CEA reports c* only from ``RocketSolver``, and that solver will happily also
return Isp, thrust coefficient, area ratio and exit Mach number for whatever
exit condition it is handed. None of those are validated for a solid
propellant, and none may leak out. So the solver is confined here, only two
things are read from it -- the chamber temperature, to cross-check against the
HP chamber solve, and ``c_star`` -- and
``tests/test_solid_propellant_architecture.py`` forbids reading anything else.

Three measured facts shape it:

* **c* does not depend on the exit condition.** For Example 5 it is bit-
  identical at pc/pe of 10, 34.47 and 500. An exit ratio has to be passed to
  the solver, so a nominal one is, and nothing at the exit is read.
* **Frozen c* is refused.** For Example 5, freezing from the chamber leaves a
  condensed species more than 50 K outside its temperature range; CEA sets
  ``converged=False`` and ``last_error=8`` -- and still returns 1515.91 m/s.
  There is no frozen option here at all.
* **The rocket solve's chamber is not the HP solve's chamber, bit for bit.**
  They agree to 2.6e-11 in temperature; the rocket solution also stores its
  chamber pressure at float32 width. So the two are cross-checked, and a
  disagreement beyond the stated tolerance refuses c* rather than pairing a
  chamber state with a c* from a different one.

The condensed-phase assumption is part of the answer, not a footnote: CEA's
equilibrium c* treats condensed products as moving and exchanging heat with
the gas with no lag. For an aluminised grain that carries a sixth of the mass
as liquid alumina, that is a real idealisation, and every result states it.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from types import ModuleType

import numpy as np

from rocketforge.physics.solid_propellant import SolidFormulationEquilibriumRequest
from rocketforge.physics.thermochemistry import ChamberGas
from rocketforge.providers.cea.errors import translate_cea_exception
from rocketforge.providers.cea.units import enthalpy_argument

from .provider import _materialise_reactants, build_solid_chamber_input

__all__ = [
    "CSTAR_BASIS",
    "CONDENSED_ASSUMPTION",
    "NOMINAL_PRESSURE_RATIO",
    "CHAMBER_CROSS_CHECK_REL_TOL",
    "SolidCharacteristicVelocity",
    "solve_solid_equilibrium_cstar",
]

#: What was computed, stated once.
CSTAR_BASIS = ("NASA CEA equilibrium characteristic velocity, infinite-area "
               "combustor, equilibrium composition from chamber to throat")

#: The idealisation a condensed-phase c* rests on.
CONDENSED_ASSUMPTION = (
    "Condensed products are treated as in equilibrium with the gas: same "
    "velocity and temperature, no particle lag.")

#: pc/pe handed to the solver because it requires one. c* does not depend on
#: it (measured, and pinned by test); nothing at the exit is read.
NOMINAL_PRESSURE_RATIO = 10.0

#: How closely the rocket solve's chamber must agree with the HP chamber solve.
#: Measured agreement is 2.6e-11 in temperature and 3.1e-08 in pressure (the
#: float32-width chamber pressure); 1e-6 is far above both and far below any
#: physically meaningful difference.
CHAMBER_CROSS_CHECK_REL_TOL = 1e-6


@dataclass(frozen=True, slots=True)
class SolidCharacteristicVelocity:
    """An equilibrium c*, or the reason there is none.

    Exactly one of :attr:`value` and :attr:`refusal` is meaningful. A refused
    c* is never a number: CEA can return a plausible value from a solve it did
    not converge, and that value is not carried here even as a fallback.

    Attributes:
        value: m/s, when every validity check passed; otherwise ``None``.
        refusal: Why there is no value, in words; empty when there is one.
        chamber_temperature_rel_diff: How far the rocket solve's chamber
            temperature sits from the HP chamber solve's, relative.
        condensed_mass_fraction: At the chamber, from the HP chamber state --
            the size of the mass the condensed-phase assumption applies to.
    """

    value: float | None
    refusal: str = ""
    chamber_temperature_rel_diff: float | None = None
    condensed_mass_fraction: float | None = None
    basis: str = CSTAR_BASIS
    condensed_assumption: str = CONDENSED_ASSUMPTION

    @property
    def available(self) -> bool:
        return self.value is not None


def _refused(reason: str, chamber: ChamberGas,
             rel_diff: float | None = None) -> SolidCharacteristicVelocity:
    return SolidCharacteristicVelocity(
        value=None, refusal=reason, chamber_temperature_rel_diff=rel_diff,
        condensed_mass_fraction=chamber.condensed_mass_fraction)


def solve_solid_equilibrium_cstar(
        cea_module: ModuleType,
        request: SolidFormulationEquilibriumRequest,
        chamber: ChamberGas) -> SolidCharacteristicVelocity:
    """Equilibrium c* for the chamber ``chamber`` describes. Never raises for a
    solve that fails -- it returns a refusal saying why.

    ``chamber`` must be the HP chamber state solved from the same ``request``;
    the rocket solve is required to reproduce it before its c* is accepted.
    """
    chamber_input = build_solid_chamber_input(request)
    try:
        reactant_specs = _materialise_reactants(cea_module, chamber_input.formulation)
        reactants = cea_module.Mixture(reactant_specs, ions=chamber_input.include_ions)
        if chamber_input.product_species is None:
            products = cea_module.Mixture(
                reactant_specs, products_from_reactants=True,
                omit=list(chamber_input.omit_species),
                ions=chamber_input.include_ions)
        else:
            products = cea_module.Mixture(
                list(chamber_input.product_species),
                omit=list(chamber_input.omit_species),
                ions=chamber_input.include_ions)
        weights = np.asarray(chamber_input.weights, dtype=float)
        hc = enthalpy_argument(
            float(reactants.calc_property(
                cea_module.ENTHALPY, weights,
                list(chamber_input.reactant_temperatures))),
            cea_module.R)
        solver = cea_module.RocketSolver(products, reactants=reactants)
        solution = cea_module.RocketSolution(solver)
        # Convergence is read from the solution itself -- ``converged`` and
        # ``last_error``, two independent signals -- not from the warning CEA
        # raises. CEA's warning is suppressed rather than recorded: recording
        # a warning raised from CEA's compiled code (``record=True``) leaves
        # 45 extension types uncollectable at interpreter shutdown, measured
        # and reproduced with raw CEA and no RocketForge code; ignoring it
        # does not. The refusal below says what CEA reported instead.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            solver.solve(solution, weights, float(chamber_input.pressure_bar),
                         [NOMINAL_PRESSURE_RATIO], iac=True, hc=hc)
    except Exception as exc:  # noqa: BLE001
        error = translate_cea_exception(exc, "solving the equilibrium c*")
        return _refused(f"NASA CEA could not solve the c* problem: {error}",
                        chamber)

    error_code = int(solution.last_error)
    if not bool(solution.converged) or error_code != 0:
        return _refused(
            f"NASA CEA did not converge the c* solve (converged="
            f"{bool(solution.converged)}, error code {error_code}). It returns "
            "a number regardless; that number is not used.",
            chamber)

    rocket_temperature = float(solution.T[0])
    rel_diff = abs(rocket_temperature - chamber.temperature) / chamber.temperature
    if not rel_diff <= CHAMBER_CROSS_CHECK_REL_TOL:
        return _refused(
            f"The c* solve's chamber temperature ({rocket_temperature!r} K) "
            f"differs from the chamber equilibrium ({chamber.temperature!r} K) "
            f"by {rel_diff:.2e} relative, beyond {CHAMBER_CROSS_CHECK_REL_TOL:g}. "
            "A c* is not paired with a chamber state it was not computed from.",
            chamber, rel_diff)

    value = float(solution.c_star[0])
    if not math.isfinite(value) or value <= 0.0:
        return _refused(f"NASA CEA returned a non-physical c* ({value!r} m/s).",
                        chamber, rel_diff)

    return SolidCharacteristicVelocity(
        value=value, chamber_temperature_rel_diff=rel_diff,
        condensed_mass_fraction=chamber.condensed_mass_fraction)

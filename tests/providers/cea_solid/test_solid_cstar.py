"""NASA CEA equilibrium characteristic velocity for solid formulations.

c* is allowed in this phase; Isp, thrust coefficient, thrust and anything at a
nozzle exit are not. What these tests pin down:

* the value is CEA's own, extracted exactly (bit-identical to a direct solve);
* it does not depend on the exit condition the solver has to be handed;
* frozen c* does not exist here, and a non-converged CEA solve -- which still
  returns a number -- is refused rather than reported;
* a c* is never paired with a chamber state it was not computed from;
* CEA's own solver-path sensitivity is measured, because it bounds how many
  digits of c* mean anything.

Mechanism validation against NASA's printed rocket examples is labelled as
such: Examples 12 and 13 are not solid propellants.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

from rocketforge.physics.solid_propellant import (
    SolidFormulation,
    SolidFormulationEquilibriumRequest,
    SolidIngredient,
)
from rocketforge.physics.thermochemistry import (
    ChemistryMode,
    EquilibriumConstraint,
    ThermochemistryProvenance,
)
from rocketforge.providers.cea import check_availability
from rocketforge.providers.cea.units import pressure_from_bar
from rocketforge.providers.cea_solid import (
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
    solve_solid_chamber,
    solve_solid_equilibrium_cstar,
)
from rocketforge.providers.cea_solid.cstar import (
    CHAMBER_CROSS_CHECK_REL_TOL,
    NOMINAL_PRESSURE_RATIO,
)

_AVAILABILITY = check_availability()
requires_cea = pytest.mark.skipif(
    not _AVAILABILITY.is_usable,
    reason=f"NASA CEA provider unavailable ({_AVAILABILITY.status.value})")

FT_PER_M = 1.0 / 0.3048
PROVENANCE = ThermochemistryProvenance(
    provider_id="nasa-cea", database="thermo.lib",
    chemistry_mode=ChemistryMode.EQUILIBRIUM,
    equilibrium_constraint=EquilibriumConstraint.HP)


@pytest.fixture(scope="module")
def cea_module():
    if not _AVAILABILITY.is_usable:
        pytest.skip("NASA CEA is not installed")
    import cea
    return cea


@pytest.fixture(scope="module")
def example5(cea_module):
    request = SolidFormulationEquilibriumRequest(
        formulation=RP1311_EXAMPLE5,
        chamber_pressure=pressure_from_bar(RP1311_EXAMPLE5_PRESSURES_BAR[0]),
        omit_species=RP1311_EXAMPLE5_OMIT)
    chamber = solve_solid_chamber(cea_module, request, provenance=PROVENANCE)
    return request, chamber


def _direct_example5(cea, pressure_ratio, **solver_options):
    """Example 5's c* from CEA directly, no RocketForge code in the solve."""
    reactants = []
    for item in RP1311_EXAMPLE5.ingredients:
        custom = item.custom
        reactants.append(item.name if custom is None else cea.Reactant(
            name=item.name, formula=dict(custom.formula),
            molecular_weight=custom.molecular_weight,
            enthalpy=custom.heat_of_formation,
            enthalpy_units=custom.heat_of_formation_units,
            temperature=custom.reference_temperature))
    weights = np.asarray(RP1311_EXAMPLE5.mass_fractions)
    reac = cea.Mixture(reactants)
    prod = cea.Mixture(reactants, products_from_reactants=True,
                       omit=list(RP1311_EXAMPLE5_OMIT))
    hc = reac.calc_property(cea.ENTHALPY, weights, [298.15] * 5) / cea.R
    solver = cea.RocketSolver(prod, reactants=reac, **solver_options)
    solution = cea.RocketSolution(solver)
    solver.solve(solution, weights, RP1311_EXAMPLE5_PRESSURES_BAR[0],
                 [pressure_ratio], iac=True, hc=hc)
    return float(solution.c_star[0])


# ===========================================================================
# extraction and invariance
# ===========================================================================


@requires_cea
def test_example5_cstar_is_cea_own_value_bit_for_bit(cea_module, example5):
    request, chamber = example5
    result = solve_solid_equilibrium_cstar(cea_module, request, chamber)
    assert result.available
    assert result.value == _direct_example5(cea_module, NOMINAL_PRESSURE_RATIO)


@requires_cea
@pytest.mark.parametrize("ratio", [10.0, 34.473652, 500.0])
def test_cstar_does_not_depend_on_the_exit_condition(cea_module, ratio):
    """Why a nominal exit ratio is safe: c* is a chamber-and-throat quantity.

    Bit-identical, not merely close. Nothing at the exit is read.
    """
    assert (_direct_example5(cea_module, ratio)
            == _direct_example5(cea_module, NOMINAL_PRESSURE_RATIO))


@requires_cea
def test_the_rocket_chamber_agrees_with_the_hp_chamber(cea_module, example5):
    request, chamber = example5
    result = solve_solid_equilibrium_cstar(cea_module, request, chamber)
    assert result.chamber_temperature_rel_diff < CHAMBER_CROSS_CHECK_REL_TOL
    assert result.condensed_mass_fraction == chamber.condensed_mass_fraction


@requires_cea
def test_cea_solver_path_sensitivity_bounds_the_meaningful_digits(cea_module):
    """The measured reason c* is shown to six significant figures, no more.

    Starting CEA from a different condensed phase (an ``AL2O3(L)`` insert)
    moves Example 5's c* by 3.3e-03 m/s, 2.1e-06 relative, although the
    throat at 2482 K is nowhere near alumina's melting point. That is CEA's
    convergence, not physics. A seventh significant figure would be noise.
    """
    plain = _direct_example5(cea_module, NOMINAL_PRESSURE_RATIO)
    inserted = _direct_example5(cea_module, NOMINAL_PRESSURE_RATIO,
                                insert=["AL2O3(L)"])
    rel = abs(inserted - plain) / plain
    assert 0.0 < rel < 1e-5
    assert f"{plain:.6g}" == f"{inserted:.6g}"      # six figures agree


# ===========================================================================
# refusals -- a refused c* is never a number
# ===========================================================================


class _FreezingCEA:
    """Real CEA, with every rocket solve forced frozen from the chamber.

    A negative control built from the actual failure: for Example 5, CEA's
    frozen solve leaves a condensed species more than 50 K outside its range,
    sets ``converged=False`` and ``last_error=8`` -- and returns 1515.91 m/s
    anyway. The refusal must fire on that, not on a mock.
    """

    def __init__(self, cea):
        self._cea = cea

    def __getattr__(self, name):
        return getattr(self._cea, name)

    def RocketSolver(self, *args, **kwargs):  # noqa: N802 -- mirrors CEA
        return _FrozenSolver(self._cea.RocketSolver(*args, **kwargs))

    def RocketSolution(self, solver):  # noqa: N802
        return self._cea.RocketSolution(solver.real)


class _FrozenSolver:
    def __init__(self, real):
        self.real = real

    def solve(self, *args, **kwargs):
        kwargs["n_frz"] = 1
        return self.real.solve(*args, **kwargs)


@requires_cea
def test_a_non_converged_cea_solve_is_refused_not_reported(cea_module, example5):
    request, chamber = example5
    result = solve_solid_equilibrium_cstar(_FreezingCEA(cea_module), request, chamber)
    assert result.available is False
    assert result.value is None                      # not 1515.91
    assert "did not converge" in result.refusal
    assert "error code 8" in result.refusal


@requires_cea
def test_a_cstar_is_not_paired_with_a_different_chamber(cea_module, example5):
    """Hand it a chamber 0.1 % hotter than the one the request produces."""
    request, chamber = example5
    wrong = dataclasses.replace(chamber, temperature=chamber.temperature * 1.001)
    result = solve_solid_equilibrium_cstar(cea_module, request, wrong)
    assert result.value is None
    assert "differs from the chamber equilibrium" in result.refusal


def test_there_is_no_frozen_option():
    """Section D4: frozen c* is refused for now, so it cannot even be asked for."""
    import inspect

    parameters = inspect.signature(solve_solid_equilibrium_cstar).parameters
    assert set(parameters) == {"cea_module", "request", "chamber"}


# ===========================================================================
# MECHANISM VALIDATION against NASA's printed rocket examples.
# Examples 12 and 13 are not solid propellants and are not counted as such.
# ===========================================================================


def _fractions(weights):
    total = math.fsum(float(w) for w in weights)
    out = [float(w) / total for w in weights]
    out[-1] = 1.0 - math.fsum(out[:-1])
    return out


def _module_cstar(cea, names, weights, pc_bar, products=None):
    formulation = SolidFormulation(
        name="mechanism", ingredients=tuple(
            SolidIngredient(n, f) for n, f in zip(names, _fractions(weights))))
    request = SolidFormulationEquilibriumRequest(
        formulation=formulation, chamber_pressure=pressure_from_bar(pc_bar),
        product_species=products)
    chamber = solve_solid_chamber(cea, request, provenance=PROVENANCE)
    return solve_solid_equilibrium_cstar(cea, request, chamber)


EX12_NAMES = ["CH6N2(L)", "N2O4(L)"]
EX12_PRODUCTS = ("CO", "CO2", "H", "HNO", "HNO2", "HO2", "H2", "H2O", "H2O2",
                 "N", "NO", "NO2", "N2", "N2O", "O", "OH", "O2", "HCO", "NH",
                 "CH4", "NH2", "NH3", "H2O(L)", "C(gr)")
EX13_NAMES = ["N2H4(L)", "Be(a)", "H2O2(L)"]


@requires_cea
def test_example12_cstar_matches_nasa_printed_value(cea_module):
    """NASA prints 1707.92 m/s (``%10.2f``); agreement within its half-unit.

    Example 12 runs frozen from the throat (``n_frz=2``, a 1-based station
    number). c* is fixed at the throat, where the composition is still the
    equilibrium one, so its printed c* *is* an equilibrium c* -- which is why
    it is a valid reference here.
    """
    reac = cea_module.Mixture(EX12_NAMES)
    weights = reac.of_ratio_to_weights(np.array([0.0, 1.0]),
                                       np.array([1.0, 0.0]), 2.5)
    result = _module_cstar(cea_module, EX12_NAMES, weights,
                           cea_module.units.psi_to_bar(1000),
                           products=EX12_PRODUCTS)
    assert result.available
    assert abs(result.value - 1707.92) <= 0.005


@requires_cea
def test_example13_cstar_and_why_it_prints_one_digit_differently(cea_module):
    """NASA prints 6386.75 ft/s. RocketForge gives 6386.7444 -- and the cause
    is measured, not tolerated.

    NASA's run passes a ``BeO(L)`` insert, a starting guess for the condensed
    phase. Its throat sits at exactly 2851.000 K, beryllium oxide's melting
    point, where solid and liquid coexist and the answer depends slightly on
    the phase the solver starts from. Isolated: the exit ratios and the 1e-10
    trace threshold change nothing that prints; the insert alone moves c* by
    8.9e-03 ft/s. So:

    * direct CEA *with* the insert reproduces the printed 6386.75;
    * RocketForge equals direct CEA *without* it, bit for bit;
    * the gap is CEA's initial-phase sensitivity, bounded at 1e-5 relative.
    """
    reac = cea_module.Mixture(EX13_NAMES)
    prod = cea_module.Mixture(EX13_NAMES, products_from_reactants=True)
    nasa_weights = reac.of_ratio_to_weights(
        np.array([0.0, 0.0, 1.0]), np.array([0.8, 0.2, 0.0]), 33.0 / 67.0)
    # The same input RocketForge is given: NASA's proportions as mass
    # fractions. Un-normalised and normalised weights differ at the last
    # binary digit (2.4e-14) in the rocket solve, so "bit for bit" is only a
    # fair claim against the identical vector.
    weights = np.asarray(_fractions(nasa_weights))
    pc = cea_module.units.psi_to_bar(3000)
    hc = reac.calc_property(cea_module.ENTHALPY, weights,
                            np.array([298.15] * 3)) / cea_module.R

    def direct(**options):
        solver = cea_module.RocketSolver(prod, reactants=reac, **options)
        solution = cea_module.RocketSolution(solver)
        solver.solve(solution, weights, pc, [NOMINAL_PRESSURE_RATIO],
                     iac=True, hc=hc)
        return float(solution.c_star[0])

    with_insert = direct(trace=1e-10, insert=["BeO(L)"])
    without_insert = direct()
    ours = _module_cstar(cea_module, EX13_NAMES, weights, pc)

    assert abs(with_insert * FT_PER_M - 6386.75) <= 0.005
    assert ours.value == without_insert
    assert abs(ours.value - with_insert) / with_insert < 1e-5
    assert ours.condensed_mass_fraction > 0.3        # BeO(L), condensed-heavy

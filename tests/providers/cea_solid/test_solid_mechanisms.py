"""Mechanism validation for the solid chamber path.

Everything here is labelled **MECHANISM VALIDATION**, not solid-propellant
benchmark coverage. RP-1311 Examples 12 and 13 are bipropellant/hybrid rocket
problems; they are used only for the specific mechanisms the solid path relies
on, and they do not count as additional solid formulations. The one solid
end-to-end benchmark is Example 5, in ``test_solid_chamber.py``.

Mechanisms checked:

* the explicit-weights solve is **bit-identical** to the frozen O/F path when
  both are given the same reactants, proportions, temperatures and products;
* Example 13 -- multi-reactant weights with a condensed *reactant* ``Be(a)``;
* Example 12 -- an explicit product list with condensed candidates that end
  up absent, and the ``n_frz`` station-index hazard R1.1 will inherit;
* phase classification is by name, independent of product order, and is
  cross-checked against CEA's ``num_condensed``.

The rocket solver appears in this file as an **oracle only**. No production
module calls it, and ``tests/test_solid_propellant_architecture.py`` enforces
that.
"""

from __future__ import annotations

import dataclasses
import math
import random

import pytest

from rocketforge.physics.solid_propellant import SolidFormulation, SolidIngredient
from rocketforge.providers.cea import check_availability
from rocketforge.providers.cea.errors import CEAMappingError
from rocketforge.providers.cea_solid import (
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
    SolidChamberInput,
    build_solid_species_table,
    check_condensed_count,
    solid_phase_of_cea_name,
    solve_solid_chamber_raw,
)

_AVAILABILITY = check_availability()
requires_cea = pytest.mark.skipif(
    not _AVAILABILITY.is_usable,
    reason=f"NASA CEA provider unavailable ({_AVAILABILITY.status.value})")


@pytest.fixture(scope="module")
def cea_module():
    if not _AVAILABILITY.is_usable:
        pytest.skip("NASA CEA is not installed")
    import cea
    return cea


def _as_fractions(weights) -> tuple[float, ...]:
    """Normalise a weight vector, closing the last entry so the sum is exact."""
    total = math.fsum(float(w) for w in weights)
    out = [float(w) / total for w in weights]
    out[-1] = 1.0 - math.fsum(out[:-1])
    return tuple(out)


def _weights_input(names, fractions, temperatures, pressure_bar,
                   product_species=None) -> SolidChamberInput:
    formulation = SolidFormulation(
        name="mechanism probe",
        ingredients=tuple(SolidIngredient(n, f) for n, f in zip(names, fractions)))
    return SolidChamberInput(
        formulation=formulation, weights=tuple(fractions),
        reactant_temperatures=tuple(temperatures), pressure_bar=pressure_bar,
        product_species=product_species)


# ===========================================================================
# the parallel solver path cannot drift from the frozen one
# ===========================================================================


@requires_cea
def test_the_weights_path_is_bit_identical_to_the_frozen_of_path(cea_module):
    """The one piece of solver code the solid path could not share.

    ``mapping.solve_chamber_raw`` derives weights with ``of_ratio_to_weights``
    and is byte-frozen, so the solid path carries its own invocation. Given the
    canonical LOX/LCH4 case expressed as explicit weights -- same reactants,
    same proportions, same temperatures, same product set -- every field of the
    raw result must be identical, not merely close. The frozen path hands CEA
    un-normalised weights (they sum to about 48) and the solid path normalised
    ones; identity here also shows CEA depends only on the proportions.
    """
    import numpy as np

    from rocketforge.physics.thermochemistry import (
        ChamberEquilibriumRequest,
        MixtureRatio,
        Phase,
        PropellantStream,
    )
    from rocketforge.providers.cea import LIQUID_METHANE, LOX
    from rocketforge.providers.cea.mapping import (
        build_chamber_input,
        solve_chamber_raw,
    )

    request = ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_METHANE, 111.643, phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(3.4),
        chamber_pressure=10.0e6)
    frozen_input = build_chamber_input(request)
    frozen = solve_chamber_raw(cea_module, frozen_input)

    weights = cea_module.Mixture(list(frozen_input.reactant_names)).of_ratio_to_weights(
        np.asarray(frozen_input.oxidiser_weights, dtype=float),
        np.asarray(frozen_input.fuel_weights, dtype=float),
        frozen_input.of_ratio)
    solid = solve_solid_chamber_raw(cea_module, _weights_input(
        frozen_input.reactant_names, _as_fractions(weights),
        frozen_input.reactant_temperatures, frozen_input.pressure_bar,
        product_species=frozen_input.product_species))

    for field in dataclasses.fields(frozen):
        assert getattr(solid, field.name) == getattr(frozen, field.name), field.name


# ===========================================================================
# RP-1311 Example 13 -- MECHANISM VALIDATION (not a solid benchmark)
# ===========================================================================

EX13_NAMES = ("N2H4(L)", "Be(a)", "H2O2(L)")


def _ex13_oracle(cea):
    """Example 13 exactly as NASA ships it; chamber station read only."""
    import numpy as np

    reac = cea.Mixture(list(EX13_NAMES))
    prod = cea.Mixture(list(EX13_NAMES), products_from_reactants=True)
    solver = cea.RocketSolver(prod, reactants=reac, trace=1e-10, insert=["BeO(L)"])
    solution = cea.RocketSolution(solver)
    weights = reac.of_ratio_to_weights(
        np.array([0.0, 0.0, 1.0]), np.array([0.8, 0.2, 0.0]), 33.0 / 67.0)
    pc = cea.units.psi_to_bar(3000)
    hc = reac.calc_property(cea.ENTHALPY, weights, np.array([298.15] * 3)) / cea.R
    solver.solve(solution, weights, pc, [3.0, 10.0, 30.0, 300.0], iac=True, hc=hc)
    return weights, pc, solution


@requires_cea
def test_example13_multi_reactant_weights_with_a_condensed_reactant(cea_module):
    """Mechanism: explicit weights over three reactants, one of them ``Be(a)``.

    Compared with the chamber station of NASA's own IAC rocket solution. Not
    bit-identical, for a measured reason: the rocket solution reports its
    chamber pressure at float32 width (206.84271240234375 bar against the
    206.84271879505718 bar requested, 3.1e-08 relative), and it also runs with
    a ``BeO(L)`` insert and a 1e-10 trace threshold that the chamber path does
    not use. Agreement is 4.5e-08 on temperature; the bound is 1e-06.
    """
    weights, pc, oracle = _ex13_oracle(cea_module)
    raw = solve_solid_chamber_raw(cea_module, _weights_input(
        EX13_NAMES, _as_fractions(weights), (298.15,) * 3, pc))

    assert raw.temperature_k == pytest.approx(float(oracle.T[0]), rel=1e-6)
    assert raw.molar_mass_kg_per_kmol == pytest.approx(float(oracle.MW[0]), rel=1e-6)
    assert raw.gamma_s == pytest.approx(float(oracle.gamma_s[0]), rel=1e-6)


@requires_cea
def test_example13_condensed_product_is_found_and_counted(cea_module):
    """Mechanism: a significant condensed *product*, ``BeO(L)``."""
    weights, pc, _ = _ex13_oracle(cea_module)
    raw = solve_solid_chamber_raw(cea_module, _weights_input(
        EX13_NAMES, _as_fractions(weights), (298.15,) * 3, pc))
    species = build_solid_species_table(cea_module, tuple(sorted(raw.mass_fractions)))
    check_condensed_count(species, raw)

    present = {name for name, value in raw.mass_fractions.items()
               if value > 0.0 and species[name].phase.is_condensed}
    assert present == {"BeO(L)"}
    assert raw.mass_fractions["BeO(L)"] > 0.3


# ===========================================================================
# RP-1311 Example 12 -- MECHANISM VALIDATION (not a solid benchmark)
# ===========================================================================

EX12_NAMES = ("CH6N2(L)", "N2O4(L)")
EX12_PRODUCTS = ("CO", "CO2", "H", "HNO", "HNO2", "HO2", "H2", "H2O", "H2O2",
                 "N", "NO", "NO2", "N2", "N2O", "O", "OH", "O2", "HCO", "NH",
                 "CH4", "NH2", "NH3", "H2O(L)", "C(gr)")


def _ex12_oracle(cea, n_frz=None):
    import numpy as np

    reac = cea.Mixture(list(EX12_NAMES))
    solver = cea.RocketSolver(cea.Mixture(list(EX12_PRODUCTS)), reactants=reac)
    solution = cea.RocketSolution(solver)
    weights = reac.of_ratio_to_weights(np.array([0.0, 1.0]), np.array([1.0, 0.0]), 2.5)
    pc = cea.units.psi_to_bar(1000)
    hc = reac.calc_property(cea.ENTHALPY, weights, 298.15) / cea.R
    kwargs = dict(supar=[5.0, 10.0, 25.0, 50.0, 75.0, 100.0, 150.0, 200.0],
                  iac=True, hc=hc)
    if n_frz is not None:
        kwargs["n_frz"] = n_frz
    solver.solve(solution, weights, pc, 68.0457, **kwargs)
    return weights, pc, solution


@requires_cea
def test_example12_explicit_product_list_with_absent_condensed_candidates(cea_module):
    """Mechanism: two condensed candidates, zero present.

    ``H2O(L)`` and ``C(gr)`` are in the explicit product list and CEA counts
    both as condensed candidates; neither forms. The "no condensed species
    present" state must come from the composition, not the counter.
    """
    weights, pc, oracle = _ex12_oracle(cea_module)
    raw = solve_solid_chamber_raw(cea_module, _weights_input(
        EX12_NAMES, _as_fractions(weights), (298.15, 298.15), pc,
        product_species=EX12_PRODUCTS))

    assert raw.temperature_k == pytest.approx(float(oracle.T[0]), rel=1e-6)
    assert raw.num_condensed_candidates == 2
    assert raw.mass_fractions["H2O(L)"] == 0.0
    assert raw.mass_fractions["C(gr)"] == 0.0
    species = build_solid_species_table(cea_module, tuple(sorted(raw.mass_fractions)))
    check_condensed_count(species, raw)


@requires_cea
def test_n_frz_is_a_one_based_station_number(cea_module):
    """The hazard R1.1 inherits, pinned now while it is cheap to pin.

    ``n_frz=2`` in Example 12 means "frozen from the throat". CEA numbers
    stations from 1 (chamber = 1, throat = 2), while the solution arrays are
    0-based (chamber = index 0, throat = index 1). Measured: with ``n_frz=2``
    the chamber and throat are identical to the equilibrium run and only the
    stations after the throat freeze. A performance module that reads the
    index as 0-based would label a frozen-from-throat result as something
    else. R1 calls no rocket solver; this test exists so R1.1 cannot start from
    a wrong assumption.
    """
    _, _, equilibrium = _ex12_oracle(cea_module)
    _, _, frozen = _ex12_oracle(cea_module, n_frz=2)

    assert float(frozen.T[0]) == float(equilibrium.T[0])     # chamber
    assert float(frozen.T[1]) == float(equilibrium.T[1])     # throat
    assert float(frozen.T[-1]) < float(equilibrium.T[-1]) - 100.0


# ===========================================================================
# phase classification: by name, order-independent, cross-checked
# ===========================================================================


@pytest.fixture(scope="module")
def example5_raw(cea_module):
    from rocketforge.physics.solid_propellant import SolidFormulationEquilibriumRequest
    from rocketforge.providers.cea.units import pressure_from_bar
    from rocketforge.providers.cea_solid import build_solid_chamber_input

    request = SolidFormulationEquilibriumRequest(
        formulation=RP1311_EXAMPLE5,
        chamber_pressure=pressure_from_bar(RP1311_EXAMPLE5_PRESSURES_BAR[0]),
        omit_species=RP1311_EXAMPLE5_OMIT)
    return solve_solid_chamber_raw(cea_module, build_solid_chamber_input(request))


@requires_cea
def test_classification_agrees_with_num_condensed(cea_module, example5_raw):
    species = build_solid_species_table(
        cea_module, tuple(sorted(example5_raw.mass_fractions)))
    check_condensed_count(species, example5_raw)
    assert example5_raw.num_condensed_candidates == 44


@requires_cea
def test_classification_does_not_depend_on_product_order(cea_module, example5_raw):
    """Section 18: do not assume condensed products come last.

    For Example 5 they happen to (161 gases, then 44 condensed candidates), but
    that is an observation about one case. Shuffling the order must not change
    which products are condensed.
    """
    names = list(example5_raw.mass_fractions)
    expected = {n for n in names if solid_phase_of_cea_name(n).is_condensed}
    rng = random.Random(20260922)
    for _ in range(5):
        rng.shuffle(names)
        table = build_solid_species_table(cea_module, tuple(names))
        assert {n for n, r in table.items() if r.phase.is_condensed} == expected


@requires_cea
def test_a_misclassified_product_is_refused(cea_module, example5_raw):
    """A negative control: the invariant must be able to fail.

    Put one condensed candidate into the gas phase and the count check must
    refuse the result rather than report it.
    """
    from rocketforge.physics.thermochemistry import Phase

    species = build_solid_species_table(
        cea_module, tuple(sorted(example5_raw.mass_fractions)))
    species["AL2O3(L)"] = dataclasses.replace(species["AL2O3(L)"], phase=Phase.GAS)
    with pytest.raises(CEAMappingError) as excinfo:
        check_condensed_count(species, example5_raw)
    assert "wrong phase" in str(excinfo.value)


def test_phase_suffixes_are_kept_on_the_species_name():
    """Section 19: ``AL2O3(L)`` stays recognisably condensed liquid."""
    from rocketforge.physics.thermochemistry import Phase

    assert solid_phase_of_cea_name("AL2O3(L)") is Phase.LIQUID
    assert solid_phase_of_cea_name("AL2O3(a)") is Phase.SOLID
    assert solid_phase_of_cea_name("AL2O3") is Phase.GAS

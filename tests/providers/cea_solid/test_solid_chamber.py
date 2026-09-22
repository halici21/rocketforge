"""The solid CEA chamber path, against NASA RP-1311 Example 5.

The validation is three-way on purpose. Comparing RocketForge only against the
published table would confound two different questions -- has RocketForge
mis-plumbed CEA, or does this build of CEA differ from the paper? So the
installed library is solved *directly*, with no RocketForge code in the solve,
and that result sits between the two.

These tests need the real library and skip with an explicit reason when it is
absent. A skip is never a pass: the CEA-enabled suite is a separate gate.
"""

from __future__ import annotations

import pytest

from rocketforge.physics.solid_propellant import (
    SolidFormulationEquilibriumRequest,
)
from rocketforge.physics.thermochemistry import (
    ChemistryMode,
    EquilibriumConstraint,
    Phase,
    ThermochemistryProvenance,
)
from rocketforge.providers.cea import check_availability
from rocketforge.providers.cea_solid import (
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
    build_solid_chamber_input,
    solid_phase_of_cea_name,
    solve_solid_chamber,
    solve_solid_chamber_raw,
)
from rocketforge.providers.cea.units import pressure_from_bar

_AVAILABILITY = check_availability()
CEA_PRESENT = _AVAILABILITY.is_usable
requires_cea = pytest.mark.skipif(
    not CEA_PRESENT,
    reason=(f"NASA CEA provider unavailable ({_AVAILABILITY.status.value}): "
            f"{_AVAILABILITY.detail or 'install requirements-thermochemistry.txt'}"),
)

#: The published table, Example 5, first pressure column. Quoted at the width
#: RP-1311 prints, which is what a reader can independently check.
OFFICIAL = {
    "T_K": 2723.021,
    "MW": 22.290,
    "gamma_s": 1.1928,
    "AL2O3(L)_mole_fraction": 0.036724,
}

PRESSURE_PA = pressure_from_bar(RP1311_EXAMPLE5_PRESSURES_BAR[0])


@pytest.fixture(scope="module")
def cea_module():
    if not CEA_PRESENT:
        pytest.skip("NASA CEA is not installed")
    import cea
    return cea


@pytest.fixture
def request_example5() -> SolidFormulationEquilibriumRequest:
    return SolidFormulationEquilibriumRequest(
        formulation=RP1311_EXAMPLE5,
        chamber_pressure=PRESSURE_PA,
        product_species=None,
        omit_species=RP1311_EXAMPLE5_OMIT,
    )


@pytest.fixture
def base_provenance() -> ThermochemistryProvenance:
    return ThermochemistryProvenance(
        provider_id="nasa-cea",
        provider_version="solid-r1",
        database="thermo.lib",
        chemistry_mode=ChemistryMode.EQUILIBRIUM,
        equilibrium_constraint=EquilibriumConstraint.HP,
    )


def solve_directly(cea, request) -> dict:
    """Solve Example 5 with CEA alone, importing nothing from the solid path."""
    import numpy as np

    formulation = request.formulation
    reactants = []
    for item in formulation.ingredients:
        if item.custom is None:
            reactants.append(item.name)
        else:
            reactants.append(cea.Reactant(
                name=item.name,
                formula=dict(item.custom.formula),
                molecular_weight=item.custom.molecular_weight,
                enthalpy=item.custom.enthalpy,
                enthalpy_units=item.custom.enthalpy_units,
                temperature=item.custom.temperature))

    weights = np.asarray(formulation.mass_fractions, dtype=np.float64)
    temps = np.asarray([formulation.initial_temperature] * len(weights),
                       dtype=np.float64)
    reac = cea.Mixture(reactants)
    prod = cea.Mixture(reactants, products_from_reactants=True,
                       omit=list(request.omit_species))
    solver = cea.EqSolver(prod, reactants=reac)
    solution = cea.EqSolution(solver)
    h0 = reac.calc_property(cea.ENTHALPY, weights, temps)
    solver.solve(solution, cea.HP, h0 / cea.R,
                 RP1311_EXAMPLE5_PRESSURES_BAR[0], weights)
    return {
        "T": float(solution.T),
        "MW": float(solution.MW),
        "gamma_s": float(solution.gamma_s),
        "density": float(solution.density),
        "mass_fractions": {str(k): float(v)
                           for k, v in solution.mass_fractions.items()},
        "num_condensed": int(solver.num_condensed),
    }


# ---------------------------------------------------------------------------
# the formulation itself, against the published input
# ---------------------------------------------------------------------------


def test_the_example5_formulation_matches_the_published_input():
    """Section 16: represented exactly as the official example does.

    The binder keeps NASA's own ``CHOS-Binder`` label rather than being
    relabelled HTPB or PBAN, so a reader comparing against the published table
    sees the same identifiers on both sides.
    """
    assert RP1311_EXAMPLE5.names == (
        "NH4CLO4(I)", "CHOS-Binder", "AL(cr)", "MgO(cr)", "H2O(L)")
    assert RP1311_EXAMPLE5.mass_fractions == (0.7206, 0.1858, 0.09, 0.002, 0.0016)
    assert sum(RP1311_EXAMPLE5.mass_fractions) == 1.0
    assert RP1311_EXAMPLE5.initial_temperature == 298.15

    binder = RP1311_EXAMPLE5.ingredients[1].custom
    assert binder is not None
    assert dict(binder.formula) == {
        "C": 1.0, "H": 1.86955, "O": 0.031256, "S": 0.008415}
    assert binder.molecular_weight == 14.6652984484
    assert binder.enthalpy == -2999.082
    assert binder.enthalpy_units == "cal/mol"


def test_the_binder_is_not_relabelled_as_a_real_binder():
    names = " ".join(RP1311_EXAMPLE5.names).upper()
    for invented in ("HTPB", "PBAN", "CTPB", "HTPE"):
        assert invented not in names


def test_building_the_input_needs_no_provider(request_example5):
    """The translation is inspectable without CEA installed."""
    chamber_input = build_solid_chamber_input(request_example5)
    assert chamber_input.weights == RP1311_EXAMPLE5.mass_fractions
    assert chamber_input.reactant_temperatures == (298.15,) * 5
    assert chamber_input.pressure_bar == pytest.approx(
        RP1311_EXAMPLE5_PRESSURES_BAR[0], rel=1e-12)
    assert chamber_input.product_species is None


# ---------------------------------------------------------------------------
# phase classification
# ---------------------------------------------------------------------------


def test_the_roman_numeral_one_suffix_is_classified_as_solid():
    """The frozen classifier knows (II) and (III) but not (I).

    CEA uses those numerals for crystalline polymorphs, so the Example 5
    product set returns ``MgSO4(I)`` beside ``MgSO4(II)`` and ``MgSO4(L)``.
    Defaulting it to gas would put a crystal in the gas phase.
    """
    assert solid_phase_of_cea_name("MgSO4(I)") is Phase.SOLID
    assert solid_phase_of_cea_name("MgSO4(II)") is Phase.SOLID
    assert solid_phase_of_cea_name("MgSO4(L)") is Phase.LIQUID
    assert solid_phase_of_cea_name("CO2") is Phase.GAS


def test_an_unknown_phase_marker_still_raises():
    """The frozen classifier's refusal behaviour must survive the extension."""
    from rocketforge.providers.cea.errors import CEAMappingError
    with pytest.raises(CEAMappingError):
        solid_phase_of_cea_name("MADEUP(zz)")


# ---------------------------------------------------------------------------
# the three-way validation
# ---------------------------------------------------------------------------


@requires_cea
def test_direct_cea_reproduces_the_published_table(cea_module, request_example5):
    """Term one against term two: does this build of CEA match the paper?"""
    direct = solve_directly(cea_module, request_example5)
    assert direct["T"] == pytest.approx(OFFICIAL["T_K"], abs=5e-4)
    assert direct["MW"] == pytest.approx(OFFICIAL["MW"], abs=5e-4)
    assert direct["gamma_s"] == pytest.approx(OFFICIAL["gamma_s"], abs=5e-5)


@requires_cea
def test_rocketforge_reproduces_direct_cea_bit_for_bit(
        cea_module, request_example5, base_provenance):
    """Term two against term three, and the tolerance is exact equality.

    Anything looser would hide a unit conversion applied twice, or a value
    rounded on the way through. The two paths run the same solver on the same
    input, so the only honest expectation is identity.
    """
    direct = solve_directly(cea_module, request_example5)
    gas = solve_solid_chamber(cea_module, request_example5,
                              provenance=base_provenance)

    assert gas.temperature == direct["T"]
    assert gas.gamma == direct["gamma_s"]
    assert gas.molar_mass * 1000.0 == direct["MW"]
    assert gas.density == direct["density"]


@requires_cea
def test_the_chamber_pressure_survives_the_round_trip(
        cea_module, request_example5, base_provenance):
    gas = solve_solid_chamber(cea_module, request_example5,
                              provenance=base_provenance)
    assert gas.pressure == PRESSURE_PA


# ---------------------------------------------------------------------------
# condensed products
# ---------------------------------------------------------------------------


@requires_cea
def test_condensed_mass_comes_from_the_composition_not_the_candidate_count(
        cea_module, request_example5, base_provenance):
    """ADR-28's rule, and this case is its strongest evidence yet.

    CEA reports 44 condensed *candidates* for this grain while exactly one is
    actually present. Reading the counter instead of the composition would
    report 43 phases that are not there.
    """
    direct = solve_directly(cea_module, request_example5)
    gas = solve_solid_chamber(cea_module, request_example5,
                              provenance=base_provenance)

    present = [name for name, value in direct["mass_fractions"].items()
               if value > 0.0 and solid_phase_of_cea_name(name).is_condensed]
    assert present == ["AL2O3(L)"]
    assert direct["num_condensed"] > len(present)
    assert gas.condensed_mass_fraction == pytest.approx(
        direct["mass_fractions"]["AL2O3(L)"], rel=1e-12)


@requires_cea
def test_the_alumina_mole_fraction_matches_the_published_value(
        cea_module, request_example5, base_provenance):
    """The published table prints mole fractions, and 0.036724 is one.

    Recorded explicitly because the corresponding *mass* fraction is 0.168 --
    quoting one where the other belongs would be a factor-of-4.6 error that
    still looks like a plausible alumina loading.
    """
    gas = solve_solid_chamber(cea_module, request_example5,
                              provenance=base_provenance)
    assert gas.composition.fraction_of("AL2O3(L)") == pytest.approx(
        OFFICIAL["AL2O3(L)_mole_fraction"], abs=5e-7)
    assert gas.condensed_mass_fraction == pytest.approx(0.16798697793, rel=1e-9)


# ---------------------------------------------------------------------------
# traceability, given ChamberGas.request cannot hold a solid request
# ---------------------------------------------------------------------------


@requires_cea
def test_the_result_carries_no_request_and_says_so_in_provenance(
        cea_module, request_example5, base_provenance):
    """``ChamberGas.request`` validates ``isinstance(ChamberEquilibriumRequest)``.

    A solid request is not one, so the field is ``None`` and provenance is the
    only record of what went in. A result that cannot say what it was made from
    is not reproducible, so this asserts the record is actually there.
    """
    gas = solve_solid_chamber(cea_module, request_example5,
                              provenance=base_provenance)
    assert gas.request is None

    conditions = dict(gas.provenance.reactant_conditions)
    assert conditions["initial_temperature_k"] == 298.15
    for item in RP1311_EXAMPLE5.ingredients:
        assert conditions[f"mass_fraction:{item.name}"] == item.mass_fraction

    options = dict(gas.provenance.options)
    assert options["solid_formulation"] == "RP-1311 Example 5"
    assert options["solid_formulation_reference"] == "NASA RP-1311 Example 5"
    assert "CHOS-Binder" in options["solid_custom_reactants"]
    assert options["solid_products_from_reactants"] == "True"


@requires_cea
def test_the_provenance_records_the_product_set_actually_considered(
        cea_module, request_example5, base_provenance):
    gas = solve_solid_chamber(cea_module, request_example5,
                              provenance=base_provenance)
    assert "AL2O3(L)" in gas.provenance.species_set
    assert len(gas.provenance.species_set) > 100


# ---------------------------------------------------------------------------
# isolation: a solid solve must not disturb the bipropellant path
# ---------------------------------------------------------------------------


@requires_cea
def test_a_solid_solve_leaves_the_bipropellant_path_bit_identical(
        cea_module, request_example5, base_provenance):
    """A / solid / A. ``cea`` holds process-global state, so this is not moot.

    A single run of A would not catch contamination at all; it is the equality
    of the first and third that carries the claim.
    """
    from rocketforge.physics.thermochemistry import (
        ChamberEquilibriumRequest,
        MixtureRatio,
        PropellantStream,
        to_jsonable,
    )
    from rocketforge.providers.cea import (
        LIQUID_METHANE,
        LOX,
        CEAThermochemistryProvider,
    )

    def canonical():
        return ChamberEquilibriumRequest(
            fuel=PropellantStream(LIQUID_METHANE, 111.643, phase=Phase.LIQUID),
            oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
            oxidiser_fuel_ratio=MixtureRatio(3.4),
            chamber_pressure=10.0e6)

    provider = CEAThermochemistryProvider()
    first = to_jsonable(provider.solve_chamber(canonical()).unwrap())
    solve_solid_chamber(cea_module, request_example5, provenance=base_provenance)
    third = to_jsonable(provider.solve_chamber(canonical()).unwrap())

    assert first == third


@requires_cea
def test_repeating_the_solid_solve_is_deterministic(
        cea_module, request_example5, base_provenance):
    """Custom reactants are materialised per solve, never cached.

    A ``cea.Reactant`` carried across two solves is exactly the leakage that
    makes a second run disagree with the first for no visible reason.
    """
    first = solve_solid_chamber(cea_module, request_example5,
                                provenance=base_provenance)
    second = solve_solid_chamber(cea_module, request_example5,
                                 provenance=base_provenance)
    assert first.temperature == second.temperature
    assert first.molar_mass == second.molar_mass
    assert first.condensed_mass_fraction == second.condensed_mass_fraction

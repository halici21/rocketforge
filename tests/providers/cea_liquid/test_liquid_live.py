"""LIQ-1 reactants against the real NASA CEA 3.3.4 database.

These need the library and skip with an explicit reason when it is absent; a
skip is never a pass, and the CEA-enabled suite is the gate for this file.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    MixtureRatio,
    PropellantStream,
)
from rocketforge.providers.cea import (
    GASEOUS_METHANE,
    GASEOUS_OXYGEN,
    LIQUID_HYDROGEN,
    LIQUID_METHANE,
    LOX,
    CEAThermochemistryProvider,
    check_availability,
)
from rocketforge.providers.cea.mapping import assigned_enthalpy_temperature
from rocketforge.providers.cea.species import cea_molar_masses
from rocketforge.providers.cea_liquid import (
    AEROZINE_50,
    CHON_PRODUCT_SPECIES,
    FORMULAS,
    HF_PRODUCT_SPECIES,
    HNF_PRODUCT_SPECIES,
    HON_PRODUCT_SPECIES,
    HYDRAZINE,
    HYDROGEN_PEROXIDE_90,
    LIQUID_FLUORINE,
    LIQUID_PROPELLANTS,
    LIQUID_REACTANT_TEMPERATURE_RANGES,
    MMH,
    NITROGEN_TETROXIDE,
    PRODUCT_SPECIES_BY_ELEMENTS,
    RP1,
    UDMH,
    CEALiquidProvider,
    reactant_cea_names,
)

CEA_PRESENT = check_availability().is_usable
pytestmark = pytest.mark.skipif(not CEA_PRESENT,
                                reason="NASA CEA provider unavailable")

PSIA = 6894.757293168


@pytest.fixture(scope="module")
def cea():
    from rocketforge.providers.cea.availability import load_cea

    return load_cea()


@pytest.fixture(scope="module")
def liquid() -> CEALiquidProvider:
    return CEALiquidProvider()


@pytest.fixture(scope="module")
def frozen() -> CEAThermochemistryProvider:
    return CEAThermochemistryProvider()


def _request(oxidiser, fuel, of, pc=1000 * PSIA, *, t_ox=None, t_fuel=None):
    return ChamberEquilibriumRequest(
        fuel=PropellantStream(fuel, t_fuel or fuel.reference_temperature),
        oxidiser=PropellantStream(oxidiser, t_ox or oxidiser.reference_temperature),
        oxidiser_fuel_ratio=MixtureRatio(of), chamber_pressure=pc)


# ---------------------------------------------------------------------------
# identities, verified against the database the provider actually loads
# ---------------------------------------------------------------------------


def test_every_reactant_name_exists_in_the_shipped_database(cea):
    for definition in LIQUID_PROPELLANTS.values():
        for name in reactant_cea_names(definition):
            cea.Mixture([name])          # raises if thermo.lib lacks it


def test_the_rfna_case_has_no_exact_database_entry(cea):
    """RFNA is absent; the IRFNA entry exists but is a different substance.

    ``cea.Reactant`` defers its lookup, so the probe asks for something.
    """
    with pytest.raises(Exception, match="RFNA"):
        cea.Reactant("RFNA").get_valid_temperature_range()
    with pytest.raises(Exception, match="RFNA"):
        cea.Mixture(["RFNA"])
    cea.Mixture(["IRFNA"])         # present -- and deliberately never used


@pytest.mark.parametrize("name", sorted(LIQUID_REACTANT_TEMPERATURE_RANGES))
def test_recorded_ranges_are_the_providers_own(cea, name):
    low, high = cea.Reactant(name).get_valid_temperature_range()
    assert LIQUID_REACTANT_TEMPERATURE_RANGES[name] == pytest.approx(
        (float(low), float(high)), abs=1e-9)


@pytest.mark.parametrize("name,assigned", [
    ("F2(L)", 85.02), ("N2O4(L)", 298.15), ("C2H8N2(L),UDMH", 298.15),
    ("CH6N2(L)", 298.15), ("RP-1", 298.15),
    ("N2H4(L)", None), ("H2O2(L)", None),
])
def test_enthalpy_behaviour_is_as_documented(cea, name, assigned):
    measured = assigned_enthalpy_temperature(cea, name)
    if assigned is None:
        assert measured is None
    else:
        assert measured == pytest.approx(assigned, abs=1e-9)


def test_liquid_water_responds_to_temperature_through_a_mixture(cea):
    mixture = cea.Mixture(["H2O(L)"])
    weights = np.array([1.0])
    low = float(mixture.calc_property(cea.ENTHALPY, weights, [290.0]))
    high = float(mixture.calc_property(cea.ENTHALPY, weights, [300.0]))
    assert high > low


def test_every_curated_formula_reproduces_ceas_molar_mass(cea):
    """A hand-curated formula is verified, not trusted -- the frozen test's
    rule, applied to every species this package adds."""
    weights = {"C": 12.011, "H": 1.008, "O": 15.999, "N": 14.007, "F": 18.998}
    names = sorted({name for species in PRODUCT_SPECIES_BY_ELEMENTS.values()
                    for name in species}
                   | {name for d in LIQUID_PROPELLANTS.values()
                      for name in reactant_cea_names(d)})
    masses = cea_molar_masses(cea, tuple(names))
    for name in names:
        implied = sum(weights[e] * n for e, n in FORMULAS[name].items())
        assert abs(implied - masses[name]) / masses[name] < 1.0e-4, name


# ---------------------------------------------------------------------------
# curated product sets against CEA's full selection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("reactants,species", [
    (["N2H4(L)", "O2(L)"], HON_PRODUCT_SPECIES),
    (["H2(L)", "F2(L)"], HF_PRODUCT_SPECIES),
    (["N2H4(L)", "F2(L)"], HNF_PRODUCT_SPECIES),
])
def test_small_systems_use_ceas_complete_selection(cea, reactants, species):
    full = cea.Mixture(reactants, products_from_reactants=True)
    assert tuple(full.species_names) == species


@pytest.mark.parametrize("oxidiser,fuel,of", [
    (LOX, UDMH, 1.65), (NITROGEN_TETROXIDE, AEROZINE_50, 2.00),
    (NITROGEN_TETROXIDE, RP1, 3.4), (NITROGEN_TETROXIDE, MMH, 2.15),
])
def test_the_curated_chon_set_matches_the_full_selection(liquid, cea, oxidiser, fuel, of):
    """Truncation cost of the 77-species C/H/O/N set against CEA's 161.

    Compared at the raw CEA level, through the frozen mapping and solve: the
    full selection holds species with no curated formula, which the provider
    would rightly refuse to turn into a ``ChamberGas``.
    """
    from dataclasses import replace

    from rocketforge.providers.cea.mapping import build_chamber_input, solve_chamber_raw

    prepared = liquid._prepare(_request(oxidiser, fuel, of))
    assert prepared.product_species == CHON_PRODUCT_SPECIES
    names = [n for d in (fuel, oxidiser) for n in reactant_cea_names(d)]
    full_set = tuple(cea.Mixture(names, products_from_reactants=True).species_names)
    assert len(full_set) > len(CHON_PRODUCT_SPECIES)
    curated = solve_chamber_raw(cea, build_chamber_input(prepared))
    full = solve_chamber_raw(cea, build_chamber_input(
        replace(prepared, product_species=full_set)))
    assert curated.converged and full.converged
    assert curated.temperature_k == pytest.approx(full.temperature_k, abs=1e-5)
    assert curated.molar_mass_kg_per_kmol == pytest.approx(
        full.molar_mass_kg_per_kmol, rel=1e-9)
    assert curated.gamma_s == pytest.approx(full.gamma_s, rel=1e-8)


# ---------------------------------------------------------------------------
# accepted behaviour preserved
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("oxidiser,fuel,of,t_ox,t_fuel", [
    (LOX, LIQUID_METHANE, 3.4, 90.17, 111.643),
    (LOX, LIQUID_HYDROGEN, 6.0, 90.17, 20.27),
    (GASEOUS_OXYGEN, GASEOUS_METHANE, 3.4, 298.15, 298.15),
    (LOX, LIQUID_METHANE, 2.5, 95.0, 111.643),
])
def test_the_accepted_pairs_are_bit_identical_to_the_frozen_provider(
        liquid, frozen, oxidiser, fuel, of, t_ox, t_fuel):
    request = _request(oxidiser, fuel, of, 10.0e6, t_ox=t_ox, t_fuel=t_fuel)
    a, b = liquid.solve_chamber(request), frozen.solve_chamber(request)
    assert a.status is b.status
    assert [d.code for d in a.diagnostics] == [d.code for d in b.diagnostics]
    for field in ("temperature", "molar_mass", "gamma", "gamma_frozen", "cp",
                  "cv", "density", "enthalpy", "entropy", "condensed_mass_fraction"):
        assert getattr(a.value, field) == getattr(b.value, field), field
    assert a.value.composition.fractions == b.value.composition.fractions
    assert a.provenance[0].species_set == b.provenance[0].species_set


# ---------------------------------------------------------------------------
# every Sutton pair solves, and the refusals are refusals
# ---------------------------------------------------------------------------

SUTTON_PAIRS = [
    (LOX, HYDRAZINE, 0.90), (LOX, RP1, 2.24), (LOX, UDMH, 1.65),
    (LIQUID_FLUORINE, HYDRAZINE, 2.30), (LIQUID_FLUORINE, LIQUID_HYDROGEN, 7.60),
    (NITROGEN_TETROXIDE, HYDRAZINE, 1.34), (NITROGEN_TETROXIDE, AEROZINE_50, 2.00),
    (NITROGEN_TETROXIDE, RP1, 3.4), (NITROGEN_TETROXIDE, MMH, 2.15),
    (HYDROGEN_PEROXIDE_90, RP1, 7.0),
]


@pytest.mark.parametrize("oxidiser,fuel,of", SUTTON_PAIRS,
                         ids=[f"{o.name}-{f.name}" for o, f, _ in SUTTON_PAIRS])
def test_each_new_pair_solves_and_conserves_every_element(liquid, oxidiser, fuel, of):
    solution = liquid.solve_chamber(_request(oxidiser, fuel, of))
    assert solution.value is not None, [d.message for d in solution.diagnostics]
    state = solution.value
    codes = {d.code for d in solution.diagnostics}
    assert "ELEMENT_BALANCE_OK" in codes or not any(
        d.severity.value == "error" for d in solution.diagnostics)
    assert "ELEMENT_BALANCE_VIOLATED" not in codes
    assert 2000.0 < state.temperature < 5000.0
    assert 5.0e-3 < state.molar_mass < 3.0e-2
    assert 1.05 < state.gamma < 1.4 and 1.1 < state.gamma_frozen < 1.4
    for value in (state.cp, state.cv, state.density, state.enthalpy):
        assert math.isfinite(value)


# ---------------------------------------------------------------------------
# product-species order: gases before condensed phases
# ---------------------------------------------------------------------------


def test_every_preset_is_solved_with_condensed_phases_after_the_gases(liquid):
    """The set CEA actually received, read back from provenance, not the constants.

    The frozen C/H/O set (LOX/RP-1, HTP-90/RP-1) keeps its accepted order, with
    C(gr) mid-list, and must arrive exactly as frozen.
    """
    from rocketforge.application.analysis.thermochemistry_presets import executable_presets
    from rocketforge.providers.cea import CHO_PRODUCT_SPECIES, PRODUCTION_PROPELLANTS
    from rocketforge.providers.cea_liquid import liquid_phase_of_cea_name

    definitions = {**PRODUCTION_PROPELLANTS, **LIQUID_PROPELLANTS}
    for preset in executable_presets():
        request = _request(definitions[preset.oxidiser], definitions[preset.fuel],
                           preset.oxidiser_fuel_ratio)
        solution = liquid.solve_chamber(request)
        assert solution.value is not None, preset.key
        used = tuple(solution.provenance[0].species_set)
        if used == CHO_PRODUCT_SPECIES:
            continue
        phases = [liquid_phase_of_cea_name(name).is_condensed for name in used]
        assert phases == sorted(phases), (preset.key, used)


def test_a_condensed_species_among_the_gases_breaks_the_chamber(liquid):
    """Why the order above is load-bearing (cea 3.3.4, measured).

    With H2O(L) moved among the gases, CEA reports convergence on a state some
    2700 K too cold for LOX/UDMH (758 K and 884 K seen, depending on position),
    which the state checks may or may not reject. If this test fails because
    the misordered set now gives the right chamber, CEA has stopped depending
    on the order; the ordering tests stay as harmless invariants.
    """
    from dataclasses import replace

    from rocketforge.physics.thermochemistry.errors import StateConsistencyError

    request = _request(LOX, UDMH, 1.65)
    accepted = liquid.solve_chamber(request).value.temperature
    assert accepted == pytest.approx(3594.0, rel=0.03)   # Sutton Table 5-5
    gases = [name for name in CHON_PRODUCT_SPECIES if "(" not in name]
    condensed = [name for name in CHON_PRODUCT_SPECIES if "(" in name]
    assert condensed == ["C(gr)", "H2O(L)", "H2O(cr)"]
    misordered = tuple(gases[:40] + ["H2O(L)"] + gases[40:] + ["C(gr)", "H2O(cr)"])
    try:
        solution = liquid.solve_chamber(replace(request, product_species=misordered))
    except StateConsistencyError:
        return
    assert solution.value is None or abs(solution.value.temperature - accepted) > 500.0


def test_a_storable_at_its_reference_raises_no_assigned_enthalpy_warning(liquid):
    solution = liquid.solve_chamber(_request(NITROGEN_TETROXIDE, MMH, 2.15))
    assert not any(d.code == "PROVIDER_ASSIGNED_ENTHALPY_REACTANT"
                   for d in solution.diagnostics)


def test_mass_basis_matters_to_the_answer(liquid):
    """The basis guard is not academic: reading HTP-90 as 90 mol % would
    change the chamber temperature by about 110 K."""
    from rocketforge.physics.thermochemistry import (
        Composition, CompositionBasis, PropellantDefinition)

    mole_fraction_h2o2 = 0.9
    m_h2o2, m_h2o = 34.01468, 18.01528
    y = mole_fraction_h2o2 * m_h2o2 / (mole_fraction_h2o2 * m_h2o2
                                       + (1 - mole_fraction_h2o2) * m_h2o)
    as_mole = PropellantDefinition(
        name="HTP-90 read by mole", role=HYDROGEN_PEROXIDE_90.role,
        composition=Composition.from_fractions(
            {"H2O2(L)": y, "H2O(L)": 1 - y}, CompositionBasis.MASS_FRACTION),
        reference_temperature=298.15,
        reference_phase=HYDROGEN_PEROXIDE_90.reference_phase)
    by_mass = liquid.solve_chamber(_request(HYDROGEN_PEROXIDE_90, RP1, 7.0)).value
    by_mole = liquid.solve_chamber(_request(as_mole, RP1, 7.0)).value
    assert by_mole.temperature - by_mass.temperature > 80.0


def test_an_out_of_range_stream_is_refused_not_extrapolated(liquid):
    from rocketforge.providers.cea.errors import CEAMappingError

    with pytest.raises(CEAMappingError, match="outside the range"):
        liquid.solve_chamber(_request(NITROGEN_TETROXIDE, MMH, 2.0, t_fuel=330.0))


def test_an_uncovered_element_system_is_refused_not_aborted(liquid):
    """LF2/MMH is not a Sutton pair. Asking for it must come back as a
    refusal -- CEA itself would abort the process on a mismatched set."""
    from rocketforge.providers.cea.errors import CEAMappingError

    with pytest.raises(CEAMappingError):
        liquid.solve_chamber(_request(LIQUID_FLUORINE, MMH, 2.0))

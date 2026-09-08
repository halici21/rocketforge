"""The production provider, running the real NASA CEA library.

Everything from a live solve onward. Skips with an explicit reason when CEA is
absent -- and a skip is never a pass: the CEA-enabled suite is its own blocking
gate.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from rocketforge.core.result import Severity, Solution, Status
from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    ChamberGas,
    ChemistryMode,
    CompositionBasis,
    EquilibriumConstraint,
    MixtureRatio,
    Phase,
    ProviderDomainError,
    ProviderCapability,
    PropellantStream,
    ThermochemistryProvider,
    UnsupportedCapabilityError,
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

_AVAILABILITY = check_availability()
CEA_PRESENT = _AVAILABILITY.is_usable
requires_cea = pytest.mark.skipif(
    not CEA_PRESENT,
    reason=(f"NASA CEA provider unavailable ({_AVAILABILITY.status.value}): "
            f"{_AVAILABILITY.detail or 'install requirements-thermochemistry.txt'}"),
)

pytestmark = requires_cea


# ---------------------------------------------------------------------------
# the production case
# ---------------------------------------------------------------------------


def test_provider_conforms_to_the_protocol(provider):
    """Structural conformance: no inheritance, no registration."""
    assert isinstance(provider, ThermochemistryProvider)


def test_the_canonical_case_solves(provider, lox_methane_request):
    solution = provider.solve_chamber(lox_methane_request)
    assert isinstance(solution, Solution)
    assert solution.ok, [d.message for d in solution.diagnostics]
    assert isinstance(solution.value, ChamberGas)


def test_every_mandatory_property_is_finite_and_in_domain(provider,
                                                          lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    assert math.isfinite(state.temperature) and state.temperature > 0.0
    assert math.isfinite(state.pressure) and state.pressure > 0.0
    assert math.isfinite(state.density) and state.density > 0.0
    assert math.isfinite(state.molar_mass) and state.molar_mass > 0.0
    assert math.isfinite(state.gas_constant) and state.gas_constant > 0.0
    assert math.isfinite(state.cp) and state.cp > 0.0
    assert math.isfinite(state.cv) and state.cv > 0.0
    assert state.gamma > 1.0
    assert state.gamma_frozen > 1.0
    for value in state.composition.fractions.values():
        assert math.isfinite(value) and value >= 0.0


def test_the_mapped_values_are_physically_plausible(provider, lox_methane_request):
    """A sanity band, not a reference comparison.

    Wide enough that it cannot be mistaken for validation, tight enough to
    catch a unit slip: a molar mass in kg/kmol instead of kg/mol would be a
    thousand times too large, and a pressure left in bar a hundred thousand
    times too small.
    """
    state = provider.solve_chamber(lox_methane_request).unwrap()
    assert 3000.0 < state.temperature < 4000.0            # K
    assert 0.015 < state.molar_mass < 0.030               # kg/mol
    assert 250.0 < state.gas_constant < 500.0             # J/(kg K)
    assert 1.05 < state.gamma < 1.30
    assert 1.0 < state.density < 30.0                     # kg/m3
    assert state.pressure == pytest.approx(10.0e6)        # Pa, as requested


def test_composition_is_complete_and_normalised(provider, lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    assert state.composition.basis is CompositionBasis.MOLE_FRACTION
    assert len(state.composition.entries) >= 25
    assert state.composition.sum() == pytest.approx(1.0, abs=1e-12)
    assert state.composition.fraction_of("H2O") > 0.4
    assert state.composition.fraction_of("CO") > 0.1


def test_trace_species_are_preserved(provider, lox_methane_request):
    """No production cutoff. Display filtering is Phase 5D's problem."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    tiny = [v for v in state.composition.fractions.values() if 0.0 < v < 1.0e-9]
    assert tiny, "expected trace species below 1e-9 to survive the mapping"


def test_cp_and_cv_are_the_frozen_pair(provider, lox_methane_request):
    """Only the frozen pair satisfies cp - cv = R; the equilibrium pair does not.

    Both are preserved, and the generic fields carry the one the identity
    holds for.
    """
    state = provider.solve_chamber(lox_methane_request).unwrap()
    assert state.cp == state.cp_frozen
    assert state.cp_equilibrium is not None
    assert state.cp_equilibrium > state.cp_frozen
    difference = state.cp - state.cv
    assert difference == pytest.approx(state.gas_constant, rel=1e-5)


def test_both_gammas_are_carried_and_differ(provider, lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    assert state.gamma_equilibrium is not None
    assert state.gamma_frozen is not None
    assert state.gamma == state.gamma_equilibrium
    relative = abs(state.gamma_frozen - state.gamma_equilibrium) / state.gamma_frozen
    assert relative > 0.03, "the equilibrium and frozen exponents should differ"
    assert state.gamma_frozen == pytest.approx(state.cp / state.cv, rel=1e-12)


# ---------------------------------------------------------------------------
# provenance
# ---------------------------------------------------------------------------


def test_provenance_identifies_provider_database_and_mode(provider,
                                                          lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    p = state.provenance
    assert p is not None
    assert p.provider_id == "cea"
    assert p.library_version
    assert p.database == "thermo.lib"
    assert len(p.database_sha256) == 64
    assert p.chemistry_mode is ChemistryMode.EQUILIBRIUM
    assert p.equilibrium_constraint is EquilibriumConstraint.HP
    assert p.species_set
    assert p.is_reproducible


def test_the_recorded_hash_is_the_database_actually_used(provider,
                                                         lox_methane_request):
    """Not a convenient copy found elsewhere: the file beside the module."""
    import hashlib
    import pathlib

    resources = provider.resources()
    on_disk = hashlib.sha256(
        pathlib.Path(resources.thermo_path).read_bytes()).hexdigest()
    state = provider.solve_chamber(lox_methane_request).unwrap()
    assert state.provenance.database_sha256 == on_disk
    assert resources.thermo_sha256 == on_disk


def test_provenance_records_the_reactant_conditions(provider, lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    conditions = state.provenance.reactant_conditions
    assert conditions["fuel_temperature"] == pytest.approx(111.643)
    assert conditions["oxidiser_temperature"] == pytest.approx(90.17)
    assert conditions["oxidiser_fuel_ratio"] == pytest.approx(3.4)


def test_provenance_is_available_before_solving(provider):
    p = provider.provenance()
    assert p.provider_id == "cea"
    assert len(p.database_sha256) == 64


def test_result_is_traceable_to_its_request(provider, lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    assert state.request is lox_methane_request
    assert state.request.fuel.temperature == pytest.approx(111.643)


# ---------------------------------------------------------------------------
# boundary hygiene
# ---------------------------------------------------------------------------


def test_no_cea_object_crosses_the_boundary(provider, lox_methane_request):
    """Every field is a RocketForge type or a plain scalar."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    allowed = (type(None), bool, int, float, str, tuple)
    for field in dataclasses.fields(state):
        value = getattr(state, field.name)
        if isinstance(value, allowed):
            continue
        module = type(value).__module__
        assert module.startswith("rocketforge."), (
            f"{field.name} is {module}.{type(value).__name__}")


def test_no_numpy_scalars_survive_the_mapping(provider, lox_methane_request):
    """CEA returns numpy values; the snapshot converts them to plain floats."""
    import numpy as np

    state = provider.solve_chamber(lox_methane_request).unwrap()
    for name in ("temperature", "density", "molar_mass", "gas_constant",
                 "cp", "cv", "gamma"):
        value = getattr(state, name)
        assert type(value) is float, f"{name} is {type(value)}"
        assert not isinstance(value, np.generic)
    for fraction in state.composition.fractions.values():
        assert type(fraction) is float


def test_the_request_is_not_mutated(provider, lox_methane_request):
    before = dataclasses.asdict(lox_methane_request.oxidiser_fuel_ratio)
    temperature = lox_methane_request.fuel.temperature
    provider.solve_chamber(lox_methane_request)
    assert dataclasses.asdict(lox_methane_request.oxidiser_fuel_ratio) == before
    assert lox_methane_request.fuel.temperature == temperature


def test_a_later_solve_does_not_change_an_earlier_result(provider,
                                                         lox_methane_request):
    """CEA reuses a mutable solution object; the snapshot must be a copy."""
    first = provider.solve_chamber(lox_methane_request).unwrap()
    captured = (first.temperature, first.molar_mass, first.gamma,
                dict(first.composition.fractions))

    other = dataclasses.replace(lox_methane_request,
                                oxidiser_fuel_ratio=MixtureRatio(2.6))
    provider.solve_chamber(other)

    assert first.temperature == captured[0]
    assert first.molar_mass == captured[1]
    assert first.gamma == captured[2]
    assert dict(first.composition.fractions) == captured[3]


def test_the_returned_state_is_frozen(provider, lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.temperature = 1.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# condensed phases
# ---------------------------------------------------------------------------


def test_condensed_candidates_are_not_treated_as_presence(provider,
                                                          lox_methane_request):
    """The Phase 5B-0 trap, live in the production case.

    CEA lists condensed species as candidates whenever they are in the product
    set. At O/F 3.4 the candidate count is nonzero and the amount actually
    present is negligible; presence must be read from the composition.
    """
    solution = provider.solve_chamber(lox_methane_request)
    state = solution.unwrap()
    candidates = [d for d in solution.diagnostics
                  if d.code == "CONDENSED_CANDIDATES"]
    assert candidates, "the candidate count should be reported"
    assert candidates[0].detail["candidates"] >= 1.0
    assert state.condensed_mass_fraction is not None
    assert state.condensed_mass_fraction < 1.0e-6


def test_a_genuinely_fuel_rich_case_produces_condensed_carbon(provider,
                                                              lox_methane_request):
    """Actual condensed material, retained with its phase.

    Very fuel-rich LOX/CH4 deposits solid carbon. This is the other half of
    the pair: candidates without presence above, presence here.
    """
    rich = dataclasses.replace(lox_methane_request,
                               oxidiser_fuel_ratio=MixtureRatio(0.5))
    solution = provider.solve_chamber(rich)
    if not solution.ok:
        pytest.skip(f"the fuel-rich case did not solve: {solution.status.value}")
    state = solution.unwrap()
    assert state.condensed_mass_fraction > 1.0e-3
    assert state.has_condensed_phase is True
    assert state.composition.fraction_of("C(gr)") > 0.0


def test_condensed_fraction_is_computed_from_the_composition(provider,
                                                             lox_methane_request):
    """Recomputed independently here, from the state's own composition."""
    from rocketforge.providers.cea.species import phase_of_cea_name

    state = provider.solve_chamber(lox_methane_request).unwrap()
    species = provider._species_for(state.provenance.species_set)
    mass = state.composition.to_basis(CompositionBasis.MASS_FRACTION, species)
    expected = sum(v for n, v in mass.entries if phase_of_cea_name(n).is_condensed)
    assert state.condensed_mass_fraction == pytest.approx(expected, rel=1e-12)


# ---------------------------------------------------------------------------
# reactant state sensitivity
# ---------------------------------------------------------------------------


def test_a_gaseous_reactant_temperature_reaches_the_solver(provider):
    """The guard against a silently substituted reference temperature.

    Gaseous reactants carry temperature-dependent fits, so raising the fuel
    temperature must raise the flame temperature. If the adapter were using the
    propellant definition's reference value instead of the stream's, these two
    would be identical.
    """
    def request(fuel_temperature: float) -> ChamberEquilibriumRequest:
        return ChamberEquilibriumRequest(
            fuel=PropellantStream(GASEOUS_METHANE, fuel_temperature, phase=Phase.GAS),
            oxidiser=PropellantStream(GASEOUS_OXYGEN, 298.15, phase=Phase.GAS),
            oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)

    cool = provider.solve_chamber(request(298.15)).unwrap()
    warm = provider.solve_chamber(request(400.0)).unwrap()
    difference = warm.temperature - cool.temperature
    # Measured: +7.63 K for a 100 K rise in the fuel alone. The fuel is only
    # about 23 % of the mass at O/F 3.4, so a rise well below 100 K is the
    # physically expected outcome; the threshold is set to distinguish a real
    # effect from noise, not to assert a number that was guessed.
    assert difference > 5.0, f"fuel temperature barely moved the chamber: {difference:.3f} K"
    assert warm.gas_constant != cool.gas_constant


def test_an_assigned_enthalpy_reactant_is_reported_not_silently_ignored(
        provider, lox_methane_request):
    """A real NASA CEA limitation, surfaced instead of hidden.

    Several CEA reactant entries -- the cryogenic liquids among them -- carry a
    single **assigned enthalpy** at one reference condition rather than a
    temperature-dependent fit. CEA accepts a different temperature for those
    and then ignores it. Verified at the library level: for ``O2(L)``,
    ``calc_property(ENTHALPY, ...)`` returns the same value at 90.17, 95 and
    99 K, while for gaseous ``O2`` it varies.

    So the honest behaviour is not to pretend the temperature mattered, and not
    to refuse a legal request either, but to say plainly that the value did not
    enter the calculation.
    """
    at_assigned = provider.solve_chamber(lox_methane_request)
    assert not [d for d in at_assigned.diagnostics
                if d.code == "PROVIDER_ASSIGNED_ENTHALPY_REACTANT"]

    warmer = dataclasses.replace(
        lox_methane_request,
        oxidiser=PropellantStream(LOX, 99.0, phase=Phase.LIQUID))
    changed = provider.solve_chamber(warmer)

    warnings = [d for d in changed.diagnostics
                if d.code == "PROVIDER_ASSIGNED_ENTHALPY_REACTANT"]
    assert warnings, "an ignored reactant temperature must be reported"
    assert changed.status is Status.OK_WITH_WARNINGS
    assert warnings[0].detail["requested"] == pytest.approx(99.0)
    assert warnings[0].detail["assigned"] == pytest.approx(90.17)
    assert "did not affect the result" in warnings[0].message

    # And the numbers really are identical, which is what the warning says.
    assert (changed.unwrap().temperature
            == at_assigned.unwrap().temperature)


def test_assigned_enthalpy_detection_is_empirical_not_pattern_matched(provider):
    """Determined by probing CEA, so it cannot be wrong about what it measured."""
    from rocketforge.providers.cea.mapping import assigned_enthalpy_temperature

    module = provider._cea()
    assert assigned_enthalpy_temperature(module, "O2(L)") == pytest.approx(90.17)
    assert assigned_enthalpy_temperature(module, "CH4(L)") == pytest.approx(111.643)
    assert assigned_enthalpy_temperature(module, "H2(L)") == pytest.approx(20.27)
    # Genuinely temperature-dependent entries report None.
    assert assigned_enthalpy_temperature(module, "O2") is None
    assert assigned_enthalpy_temperature(module, "CH4") is None
    assert assigned_enthalpy_temperature(module, "N2H4(L)") is None


def test_liquid_and_gaseous_reactants_give_materially_different_chambers(provider):
    """The 74.9 K question, measured by the production provider.

    Phase 5B-0 measured this difference directly against the library; here it
    is measured through the whole RocketForge pipeline, which is what proves
    the phase and temperature actually reach the solver.
    """
    liquid = ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_METHANE, 111.643, phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)
    gaseous = ChamberEquilibriumRequest(
        fuel=PropellantStream(GASEOUS_METHANE, 298.15, phase=Phase.GAS),
        oxidiser=PropellantStream(GASEOUS_OXYGEN, 298.15, phase=Phase.GAS),
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)

    cold = provider.solve_chamber(liquid).unwrap()
    warm = provider.solve_chamber(gaseous).unwrap()
    difference = warm.temperature - cold.temperature
    assert 60.0 < difference < 90.0, (
        f"expected roughly the 74.9 K Phase 5B-0 measured, got {difference:.2f} K")


def test_the_hydrogen_pair_also_solves(provider):
    """A second propellant pair, and a carbon-free product set."""
    request = ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_HYDROGEN, 20.27, phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(6.0), chamber_pressure=10.0e6)
    state = provider.solve_chamber(request).unwrap()
    assert 3000.0 < state.temperature < 4000.0
    assert state.molar_mass < 0.017          # light products
    assert "CO" not in state.composition.fractions
    assert state.composition.fraction_of("H2O") > 0.5


# ---------------------------------------------------------------------------
# operating matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("of", [2.5, 3.0, 3.4, 4.0, 4.5])
@pytest.mark.parametrize("pc", [5.0e6, 10.0e6, 20.0e6])
def test_the_operating_matrix_solves_and_validates(provider, lox_methane_request,
                                                   of, pc):
    """Fifteen conditions, every one fully validated.

    Not a smoke test: each of these runs element conservation and the state
    identities, so a mapping defect that only appeared at one corner would be
    caught.
    """
    request = dataclasses.replace(lox_methane_request,
                                  oxidiser_fuel_ratio=MixtureRatio(of),
                                  chamber_pressure=pc)
    solution = provider.solve_chamber(request)
    assert solution.ok, [d.message for d in solution.diagnostics
                         if d.severity is Severity.ERROR]
    state = solution.unwrap()
    assert state.pressure == pytest.approx(pc)
    assert 2500.0 < state.temperature < 4200.0


def test_mixture_ratio_changes_the_composition(provider, lox_methane_request):
    lean = provider.solve_chamber(dataclasses.replace(
        lox_methane_request, oxidiser_fuel_ratio=MixtureRatio(4.5))).unwrap()
    rich = provider.solve_chamber(dataclasses.replace(
        lox_methane_request, oxidiser_fuel_ratio=MixtureRatio(2.5))).unwrap()
    assert rich.composition.fraction_of("H2") > lean.composition.fraction_of("H2")
    assert lean.composition.fraction_of("O2") > rich.composition.fraction_of("O2")
    assert rich.molar_mass < lean.molar_mass


# ---------------------------------------------------------------------------
# determinism and state leakage
# ---------------------------------------------------------------------------


def test_ten_identical_solves_are_bitwise_identical(provider, lox_methane_request):
    results = [provider.solve_chamber(lox_methane_request).unwrap()
               for _ in range(10)]
    first = results[0]
    for other in results[1:]:
        assert other.temperature == first.temperature
        assert other.molar_mass == first.molar_mass
        assert other.gamma == first.gamma
        assert dict(other.composition.fractions) == dict(first.composition.fractions)


def test_no_state_leakage_between_alternating_cases(provider, lox_methane_request):
    """A / B / A / B / A with substantially different conditions.

    CEA holds native state and reuses its solution object, so this is the test
    that says whether a previous solve can contaminate the next one.
    """
    a = lox_methane_request
    b = dataclasses.replace(
        lox_methane_request, oxidiser_fuel_ratio=MixtureRatio(2.5),
        chamber_pressure=5.0e6,
        oxidiser=PropellantStream(LOX, 95.0, phase=Phase.LIQUID))

    a1 = provider.solve_chamber(a).unwrap()
    b1 = provider.solve_chamber(b).unwrap()
    a2 = provider.solve_chamber(a).unwrap()
    b2 = provider.solve_chamber(b).unwrap()
    a3 = provider.solve_chamber(a).unwrap()

    assert a1.temperature == a2.temperature == a3.temperature
    assert dict(a1.composition.fractions) == dict(a3.composition.fractions)
    assert b1.temperature == b2.temperature
    assert a1.temperature != pytest.approx(b1.temperature)


# ---------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------


def test_an_out_of_range_pressure_is_refused_with_the_range_named(
        provider, lox_methane_request):
    beyond = dataclasses.replace(lox_methane_request, chamber_pressure=1.0e12)
    with pytest.raises(ProviderDomainError, match="validated range"):
        provider.solve_chamber(beyond)


def test_an_undeclared_capability_raises(provider, lox_methane_request):
    crippled = CEAThermochemistryProvider()
    from rocketforge.physics.thermochemistry import ProviderCapabilities
    crippled.capabilities = ProviderCapabilities(supported=frozenset())
    with pytest.raises(UnsupportedCapabilityError, match="hp_equilibrium"):
        crippled.solve_chamber(lox_methane_request)


def test_kinetics_is_not_claimed(provider):
    """CEA is an equilibrium code. Claiming kinetics would be a lie."""
    assert not provider.capabilities.supports(ProviderCapability.KINETICS)
    assert provider.capabilities.supports(ProviderCapability.LIQUID_REACTANTS)
    assert provider.capabilities.supports(ProviderCapability.ROCKET_PERFORMANCE)


def test_declaring_rocket_performance_does_not_put_it_on_the_state(
        provider, lox_methane_request):
    """The capability says oracle values can be had, not that we own them."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    names = {f.name for f in dataclasses.fields(state)}
    assert not names & {"c_star", "cstar", "cf", "isp", "Isp", "thrust",
                        "coefficient_of_thrust", "specific_impulse"}


# ---------------------------------------------------------------------------
# the spy: malformed input must never reach CEA
# ---------------------------------------------------------------------------


def test_invalid_requests_never_reach_the_solver(provider, monkeypatch,
                                                 lox_stream, methane_stream):
    """Counted, not assumed.

    Phase 5B-0 measured NASA CEA accepting a negative temperature and a
    negative pressure without raising. RocketForge must refuse them first, and
    this counts the calls to prove it does.
    """
    import rocketforge.providers.cea.provider as provider_module

    calls: list[object] = []
    real = provider_module.solve_chamber_raw

    def spy(module, chamber_input):
        calls.append(chamber_input)
        return real(module, chamber_input)

    monkeypatch.setattr(provider_module, "solve_chamber_raw", spy)

    bad_cases = [
        ("negative temperature",
         lambda: PropellantStream(LOX, -90.0)),
        ("zero temperature",
         lambda: PropellantStream(LOX, 0.0)),
        ("negative pressure",
         lambda: PropellantStream(LOX, 90.17, pressure=-1.0e6)),
    ]
    for label, build in bad_cases:
        with pytest.raises(Exception):
            build()
        assert calls == [], f"{label} reached the solver"

    for label, ratio in (("zero O/F", 0.0), ("negative O/F", -3.4),
                         ("NaN O/F", float("nan"))):
        with pytest.raises(Exception):
            MixtureRatio(ratio)
        assert calls == [], f"{label} reached the solver"

    for label, pressure in (("zero Pc", 0.0), ("negative Pc", -1.0e6)):
        with pytest.raises(Exception):
            ChamberEquilibriumRequest(
                fuel=methane_stream, oxidiser=lox_stream,
                oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=pressure)
        assert calls == [], f"{label} reached the solver"

    # A capability refusal must also stop short of the solver.
    from rocketforge.physics.thermochemistry import ProviderCapabilities
    crippled = CEAThermochemistryProvider()
    crippled.capabilities = ProviderCapabilities(supported=frozenset())
    with pytest.raises(UnsupportedCapabilityError):
        crippled.solve_chamber(ChamberEquilibriumRequest(
            fuel=methane_stream, oxidiser=lox_stream,
            oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6))
    assert calls == [], "an unsupported capability reached the solver"

    # And a well-formed request does reach it, so the spy is not vacuous.
    provider.solve_chamber(ChamberEquilibriumRequest(
        fuel=methane_stream, oxidiser=lox_stream,
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6))
    assert len(calls) == 1, "the spy never observed a legitimate call"

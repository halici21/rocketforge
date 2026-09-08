"""Thermodynamic state contracts and their identity validators.

The mutation proofs are the point of this file. Phase 4G shipped a reference
self-test that mutated a bound method instead of the data, so it detected
"corruption" in unmodified rows and was vacuously green. Every proof here
asserts the fixture **actually changed** before asserting that the validator
notices, so a validator that stopped working could not pass as a placebo.
"""

from __future__ import annotations

import dataclasses

import pytest

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.core.result import Severity
from rocketforge.physics.thermochemistry import (
    ChamberGas,
    ChemistryMode,
    Composition,
    CompositionBasis,
    EquilibriumConstraint,
    GasStation,
    StateConsistencyError,
    ThermochemistryProvenance,
    check_cp_cv_relation,
    check_gamma_definition,
    check_gas_constant,
    check_ideal_gas,
    check_provenance_completeness,
    validate_chamber_gas,
    validate_gas_station,
)

MOLE = CompositionBasis.MOLE_FRACTION

# A self-consistent ideal-gas fixture, built from M and gamma so that every
# identity closes by construction rather than by transcription.
#
# M_BAR is the mean molar mass the `products` composition below actually
# implies, not a round number: 0.25*44.0095 + 0.5*18.01528 + 0.15*28.0101
# + 0.10*2.01588 = 24.413118 g/mol. `test_fixture_molar_mass_matches_the_table`
# keeps the two from drifting apart. An earlier draft used an arbitrary 0.024
# here and the `state M = composition M` validator caught it, which is a small
# piece of evidence that the validator works.
M_BAR = 24.413118e-3                            # kg/mol
R_SPEC = UNIVERSAL_GAS_CONSTANT / M_BAR         # J/(kg K)
GAMMA_FROZEN = 1.2
CV = R_SPEC / (GAMMA_FROZEN - 1.0)
CP = GAMMA_FROZEN * CV
T_CHAMBER = 3500.0
P_CHAMBER = 10.0e6
RHO = P_CHAMBER / (R_SPEC * T_CHAMBER)


def test_fixture_molar_mass_matches_the_table(realistic_table):
    """The hand-written M_BAR must equal what the composition implies."""
    composition = Composition.from_fractions(
        {"CO2": 0.25, "H2O": 0.5, "CO": 0.15, "H2": 0.10}, MOLE)
    assert composition.mean_molar_mass(realistic_table) == pytest.approx(
        M_BAR, rel=1e-14)


@pytest.fixture
def products() -> Composition:
    return Composition.from_fractions(
        {"CO2": 0.25, "H2O": 0.5, "CO": 0.15, "H2": 0.10}, MOLE)


@pytest.fixture
def consistent_chamber(products: Composition) -> ChamberGas:
    return ChamberGas(
        temperature=T_CHAMBER,
        gamma=1.14,                    # an equilibrium exponent, deliberately
        gas_constant=R_SPEC,
        molar_mass=M_BAR,
        composition=products,
        pressure=P_CHAMBER,
        density=RHO,
        cp=CP,
        cv=CV,
        cp_frozen=CP,
        gamma_frozen=GAMMA_FROZEN,
        gamma_equilibrium=1.14,
        provenance=ThermochemistryProvenance(
            provider_id="stub:test", provider_version="0",
            library_version="0", database="synthetic", database_version="1",
            chemistry_mode=ChemistryMode.EQUILIBRIUM,
            equilibrium_constraint=EquilibriumConstraint.HP),
    )


# ---------------------------------------------------------------------------
# domain validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field,bad", [
    ("temperature", 0.0), ("temperature", -1.0), ("temperature", float("nan")),
    ("gas_constant", 0.0), ("gas_constant", -1.0),
    ("molar_mass", 0.0), ("molar_mass", float("inf")),
    ("gamma", 1.0), ("gamma", 0.5),
])
def test_chamber_gas_domain(consistent_chamber, field, bad):
    with pytest.raises(StateConsistencyError):
        dataclasses.replace(consistent_chamber, **{field: bad})


def test_gamma_must_exceed_one(consistent_chamber):
    with pytest.raises(StateConsistencyError, match="must exceed 1"):
        dataclasses.replace(consistent_chamber, gamma=1.0)


def test_condensed_fraction_must_lie_in_the_unit_interval(consistent_chamber):
    with pytest.raises(StateConsistencyError):
        dataclasses.replace(consistent_chamber, condensed_mass_fraction=1.5)
    assert dataclasses.replace(
        consistent_chamber, condensed_mass_fraction=0.0).condensed_mass_fraction == 0.0


def test_state_is_frozen(consistent_chamber):
    with pytest.raises(dataclasses.FrozenInstanceError):
        consistent_chamber.temperature = 1.0  # type: ignore[misc]


def test_chamber_temperature_is_a_stagnation_temperature(consistent_chamber):
    """T0, not a static temperature. One letter's confusion would propagate."""
    assert consistent_chamber.stagnation_temperature == consistent_chamber.temperature


def test_chamber_gas_carries_no_performance_or_geometry(consistent_chamber):
    names = {f.name for f in dataclasses.fields(consistent_chamber)}
    for forbidden in ("c_star", "cstar", "cf", "coefficient_of_thrust", "isp",
                      "Isp", "thrust", "throat_area", "l_star", "chamber_volume",
                      "contraction_ratio", "residence_time"):
        assert forbidden not in names


def test_condensed_unknown_is_not_absent(consistent_chamber):
    """`None` means the provider did not report, which is not "there is none".

    Phase 5B-0 found a provider counter that reports candidate condensed
    species rather than present ones, so "unknown" has to be its own answer.
    """
    unknown = dataclasses.replace(consistent_chamber, condensed_mass_fraction=None)
    assert unknown.has_condensed_phase is None
    absent = dataclasses.replace(consistent_chamber, condensed_mass_fraction=0.0)
    assert absent.has_condensed_phase is False
    present = dataclasses.replace(consistent_chamber, condensed_mass_fraction=0.13)
    assert present.has_condensed_phase is True


def test_mode_must_be_recorded_for_the_handshake(consistent_chamber):
    """Precondition P1: a state that cannot say which gamma it carries."""
    assert consistent_chamber.mode_is_recorded
    without = dataclasses.replace(consistent_chamber, provenance=None)
    assert not without.mode_is_recorded


# ---------------------------------------------------------------------------
# gas station
# ---------------------------------------------------------------------------


def test_frozen_station_composition_none_means_inherited():
    """Documented convention, not missing data (09 section 8)."""
    station = GasStation(pressure=1.0e5, temperature=1500.0, gamma=1.2)
    assert station.composition is None
    assert station.composition_is_inherited


def test_station_area_ratio_is_a_boundary_condition_not_geometry():
    station = GasStation(pressure=1.0e5, temperature=1500.0, gamma=1.2,
                         area_ratio=40.0)
    assert station.area_ratio == 40.0
    names = {f.name for f in dataclasses.fields(station)}
    for forbidden in ("area", "x", "axial_position", "contour", "geometry",
                      "throat_area"):
        assert forbidden not in names


def test_station_area_ratio_below_one_is_refused():
    with pytest.raises(StateConsistencyError, match="at least 1"):
        GasStation(pressure=1.0e5, temperature=1500.0, gamma=1.2, area_ratio=0.5)


def test_station_validation_reports_inherited_composition_as_not_applicable():
    station = GasStation(pressure=1.0e5, temperature=1500.0, gamma=1.2)
    report = validate_gas_station(station)
    skipped = {c.identity for c in report.skipped}
    assert "sum(fractions) = 1" in skipped
    assert report.valid


# ---------------------------------------------------------------------------
# identities on a consistent state
# ---------------------------------------------------------------------------


def test_all_identities_pass_on_a_consistent_state(consistent_chamber,
                                                   realistic_table):
    report = validate_chamber_gas(consistent_chamber, realistic_table,
                                  require_provenance=True)
    assert report.valid, [c.identity for c in report.failures]
    assert report.max_residual < 1.0e-12


def test_a_check_that_could_not_run_is_not_a_check_that_passed(consistent_chamber):
    """Skipped and passed are reported separately, never collapsed."""
    minimal = ChamberGas(temperature=T_CHAMBER, gamma=1.2, gas_constant=R_SPEC,
                         molar_mass=M_BAR, composition=consistent_chamber.composition)
    report = validate_chamber_gas(minimal)
    assert report.valid
    assert report.skipped, "cp/cv and ideal-gas checks have nothing to run on"
    identities = {c.identity for c in report.skipped}
    assert "cp - cv = R" in identities
    assert "p = rho R T" in identities


def test_diagnostics_distinguish_the_three_outcomes(consistent_chamber,
                                                    realistic_table):
    report = validate_chamber_gas(consistent_chamber, realistic_table)
    severities = {d.code: d.severity for d in report.to_diagnostics()}
    assert severities.get("IDENTITY_OK") is Severity.INFO
    broken = dataclasses.replace(consistent_chamber, gas_constant=R_SPEC * 1.1)
    failing = validate_chamber_gas(broken, realistic_table).to_diagnostics()
    assert any(d.code == "IDENTITY_VIOLATED" and d.severity is Severity.ERROR
               for d in failing)


def test_equilibrium_gamma_is_not_required_to_equal_cp_over_cv(consistent_chamber):
    """The two gammas are different quantities and must not be conflated.

    Phase 5B-0 measured gamma_s = 1.1336 against a frozen cp/cv of 1.1985 on
    one real state -- a 5.7 % difference. The validator checks the frozen pair
    only; applying it to the equilibrium exponent would fail a correct provider.
    """
    assert consistent_chamber.gamma_equilibrium != pytest.approx(
        consistent_chamber.cp / consistent_chamber.cv)
    report = validate_chamber_gas(consistent_chamber)
    assert report.valid


# ---------------------------------------------------------------------------
# MUTATION PROOFS
# ---------------------------------------------------------------------------


def test_mutation_proof_gas_constant_vs_molar_mass(consistent_chamber):
    """R = Ru / M. Corrupt R; prove it changed, then that the check fails.

    This is the check that catches an adapter which converts molar mass from
    kg/kmol and forgets to convert R.
    """
    good = check_gas_constant(consistent_chamber.gas_constant,
                              consistent_chamber.molar_mass)
    assert good.passed and good.applicable

    corrupt = dataclasses.replace(consistent_chamber,
                                  gas_constant=consistent_chamber.gas_constant * 1.001)
    assert corrupt.gas_constant != consistent_chamber.gas_constant, "mutation must bite"

    bad = check_gas_constant(corrupt.gas_constant, corrupt.molar_mass)
    assert not bad.passed
    assert bad.residual > good.residual


def test_mutation_proof_molar_mass_side_of_the_same_identity(consistent_chamber):
    """The same identity, corrupted from the other side."""
    corrupt = dataclasses.replace(consistent_chamber, molar_mass=M_BAR * 1000.0)
    assert corrupt.molar_mass != consistent_chamber.molar_mass, "mutation must bite"
    assert not check_gas_constant(corrupt.gas_constant, corrupt.molar_mass).passed


def test_mutation_proof_cp_minus_cv_equals_r(consistent_chamber):
    good = check_cp_cv_relation(consistent_chamber.cp, consistent_chamber.cv,
                                consistent_chamber.gas_constant)
    assert good.passed

    corrupt = dataclasses.replace(consistent_chamber, cv=consistent_chamber.cv * 1.01)
    assert corrupt.cv != consistent_chamber.cv, "mutation must bite"
    assert not check_cp_cv_relation(corrupt.cp, corrupt.cv,
                                    corrupt.gas_constant).passed


def test_mutation_proof_gamma_equals_cp_over_cv(consistent_chamber):
    good = check_gamma_definition(consistent_chamber.gamma_frozen,
                                  consistent_chamber.cp, consistent_chamber.cv)
    assert good.passed

    corrupt = dataclasses.replace(consistent_chamber, gamma_frozen=1.4)
    assert corrupt.gamma_frozen != consistent_chamber.gamma_frozen, "mutation must bite"
    assert not check_gamma_definition(corrupt.gamma_frozen, corrupt.cp,
                                      corrupt.cv).passed


def test_mutation_proof_ideal_gas_law(consistent_chamber):
    """p = rho R T. Corrupt rho; prove it changed, then that the check fails."""
    good = check_ideal_gas(consistent_chamber.pressure, consistent_chamber.density,
                           consistent_chamber.gas_constant,
                           consistent_chamber.temperature)
    assert good.passed
    assert good.residual < 1.0e-12

    corrupt = dataclasses.replace(consistent_chamber,
                                  density=consistent_chamber.density * 1.02)
    assert corrupt.density != consistent_chamber.density, "mutation must bite"

    bad = check_ideal_gas(corrupt.pressure, corrupt.density,
                          corrupt.gas_constant, corrupt.temperature)
    assert not bad.passed
    assert bad.residual == pytest.approx(0.02 / 1.02, rel=1e-6)


def test_mutation_proof_nothing_is_silently_repaired(consistent_chamber):
    """The validator reports; it never adjusts a field to force the identity."""
    corrupt = dataclasses.replace(consistent_chamber,
                                  density=consistent_chamber.density * 2.0)
    before = corrupt.density
    check_ideal_gas(corrupt.pressure, corrupt.density, corrupt.gas_constant,
                    corrupt.temperature)
    assert corrupt.density == before


def test_mutation_proof_state_molar_mass_against_its_composition(
        consistent_chamber, realistic_table):
    """The state's M must match the M its own composition implies."""
    good = validate_chamber_gas(consistent_chamber, realistic_table)
    match = good.by_identity()["state M = composition M"]
    assert match.applicable

    corrupt = dataclasses.replace(consistent_chamber, molar_mass=M_BAR * 1.5,
                                  gas_constant=UNIVERSAL_GAS_CONSTANT / (M_BAR * 1.5))
    assert corrupt.molar_mass != consistent_chamber.molar_mass, "mutation must bite"
    report = validate_chamber_gas(corrupt, realistic_table)
    assert not report.by_identity()["state M = composition M"].passed


# ---------------------------------------------------------------------------
# provenance completeness
# ---------------------------------------------------------------------------


def test_provenance_completeness(consistent_chamber):
    assert check_provenance_completeness(consistent_chamber.provenance).passed
    assert not check_provenance_completeness(None).passed


def test_provenance_without_data_identity_is_not_reproducible():
    thin = ThermochemistryProvenance(provider_id="cea", library_version="3.3.4")
    assert not thin.is_reproducible
    check = check_provenance_completeness(thin)
    assert not check.passed
    assert "database" in check.detail


def test_stub_provenance_is_recognisable():
    """A stub value escaping into an artifact would be a fabricated number."""
    assert ThermochemistryProvenance(provider_id="stub:test").is_stub
    assert not ThermochemistryProvenance(provider_id="cea").is_stub


def test_provenance_has_no_timestamp():
    """Two identical calculations must produce equal provenance."""
    names = {f.name for f in dataclasses.fields(ThermochemistryProvenance)}
    assert not any("time" in n or "date" in n for n in names)
    a = ThermochemistryProvenance(provider_id="cea", library_version="3.3.4",
                                  database_version="1")
    b = ThermochemistryProvenance(provider_id="cea", library_version="3.3.4",
                                  database_version="1")
    assert a == b


def test_provenance_rejects_a_malformed_hash():
    from rocketforge.physics.thermochemistry import ThermochemistryError
    with pytest.raises(ThermochemistryError, match="64 hex characters"):
        ThermochemistryProvenance(provider_id="cea", database_sha256="deadbeef")

"""Can a real provider's output actually map into these contracts?

This is the check Phase 5B spec sections 202-204 ask for, done against the
**recorded output of the real libraries** rather than against a hypothetical.
The numbers come from ``acceptance/phase_5b0/``, captured in Phase 5B-0 by
driving NASA CEA 3.3.4 and Cantera 3.2.0 on a matched common case.

No provider is installed and none is imported. These tests read a JSON artifact
and prove the domain records can carry what it contains, without losing
composition, phase, provenance or units, and without a provider-specific
dumping ground.

If the artifacts are absent the tests skip with a reason, following the SciPy
oracle precedent already in this repository.
"""

from __future__ import annotations

import dataclasses
import json
import math
import pathlib

import pytest

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.physics.thermochemistry import (
    DEFAULT_THERMO_TOLERANCES,
    ChamberGas,
    ChemistryMode,
    Composition,
    CompositionBasis,
    EquilibriumConstraint,
    ProviderCapabilities,
    ProviderCapability,
    ThermochemistryProvenance,
    check_gas_constant,
    validate_chamber_gas,
)

ARTIFACTS = pathlib.Path(__file__).resolve().parents[3] / "acceptance" / "phase_5b0"
MOLE = CompositionBasis.MOLE_FRACTION


def load(name: str) -> dict:
    path = ARTIFACTS / name
    if not path.exists():
        pytest.skip(f"Phase 5B-0 artifact {name} is not present")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def cea_case() -> dict:
    return load("common_case_cea.json")


@pytest.fixture
def cantera_case() -> dict:
    return load("common_case_cantera.json")


def to_chamber_gas(case: dict, provider_id: str) -> ChamberGas:
    """The adapter mapping, written out in full.

    This is what a Phase 5C adapter will do. Doing it here, against real
    recorded output, is how the contract is shown to fit before the adapter is
    written.
    """
    composition = Composition.from_fractions(
        case["X"], MOLE,
        database=case.get("native_units", {}).get("database", "recorded"),
        database_version=case["version"])

    molar_mass_kg_per_mol = float(case["M_kg_per_kmol"]) / 1000.0   # kg/kmol -> kg/mol

    return ChamberGas(
        temperature=float(case["Tc_K"]),
        # The mode-appropriate exponent: this case was solved at equilibrium.
        gamma=float(case["gamma_s_equilibrium"]),
        gas_constant=UNIVERSAL_GAS_CONSTANT / molar_mass_kg_per_mol,
        molar_mass=molar_mass_kg_per_mol,
        composition=composition,
        pressure=float(case["P_Pa"]),
        density=float(case["density_kg_per_m3"]),
        enthalpy=float(case["enthalpy_J_per_kg"]),
        entropy=float(case["entropy_J_per_kgK"]),
        cp=float(case["cp_frozen_J_per_kgK"]),
        cv=float(case["cv_frozen_J_per_kgK"]),
        cp_frozen=float(case["cp_frozen_J_per_kgK"]),
        cp_equilibrium=(None if case.get("cp_equilibrium_J_per_kgK") is None
                        else float(case["cp_equilibrium_J_per_kgK"])),
        gamma_frozen=float(case["gamma_frozen_cp_over_cv"]),
        gamma_equilibrium=float(case["gamma_s_equilibrium"]),
        provenance=ThermochemistryProvenance(
            provider_id=provider_id,
            library_version=str(case["version"]),
            database="recorded in Phase 5B-0",
            database_version=str(case["version"]),
            chemistry_mode=ChemistryMode.EQUILIBRIUM,
            equilibrium_constraint=EquilibriumConstraint.HP,
            species_set=tuple(case["case"]["species"]),
            reactant_conditions={
                "fuel_temperature": float(case["case"]["T_reac_K"]),
                "oxidiser_temperature": float(case["case"]["T_reac_K"]),
                "oxidiser_fuel_ratio": float(case["case"]["of_mass"]),
                "chamber_pressure": float(case["case"]["P_Pa"]),
            }),
    )


# ---------------------------------------------------------------------------
# NASA CEA
# ---------------------------------------------------------------------------


def test_real_cea_output_maps_without_loss(cea_case):
    state = to_chamber_gas(cea_case, "cea")

    assert state.temperature == pytest.approx(3673.6145769925606)
    assert state.molar_mass == pytest.approx(21.464430797386115e-3)
    assert len(state.composition.entries) == 9
    assert state.composition.fraction_of("H2O") == pytest.approx(
        cea_case["X"]["H2O"])
    assert state.mode_is_recorded
    assert state.provenance.species_set == tuple(cea_case["case"]["species"])


def test_both_cea_gammas_survive_the_mapping(cea_case):
    """One field could not carry both. Phase 5B-0 measured them 5.7 % apart."""
    state = to_chamber_gas(cea_case, "cea")
    assert state.gamma_equilibrium == pytest.approx(1.133592184936619)
    assert state.gamma_frozen == pytest.approx(1.1985300382701392)
    relative = abs(state.gamma_frozen - state.gamma_equilibrium) / state.gamma_frozen
    assert relative > 0.05, "the two gammas really are far apart"


def test_both_cea_heat_capacities_survive_the_mapping(cea_case):
    state = to_chamber_gas(cea_case, "cea")
    assert state.cp_frozen == pytest.approx(2338.5140340067032)
    assert state.cp_equilibrium == pytest.approx(7162.420288048198)
    assert state.cp_equilibrium > state.cp_frozen


def test_mapped_cea_state_needs_the_provider_tolerance_not_the_strict_one(cea_case):
    """A real finding, and the reason the tolerance categories are separate.

    CEA computes ``cp - cv`` and ``p = rho R T`` with **its own** universal gas
    constant (8314.51, pre-2019). We recompute R from CODATA. Its state is
    therefore internally consistent on its constants and off ours by ~5.7e-06 --
    far above the strict 1e-9 used for RocketForge's own algebra.

    The strict tolerance is not loosened. An adapter passes the provider
    tolerance instead, and that distinction is exactly what Phase 5B spec
    sections 84 and 164 asked to be kept apart.
    """
    state = to_chamber_gas(cea_case, "cea")

    strict = validate_chamber_gas(state, require_provenance=True)
    failed = {c.identity for c in strict.failures}
    assert failed == {"cp - cv = R", "p = rho R T"}, failed
    assert 1.0e-6 < strict.max_residual < 1.0e-5

    provider_aware = validate_chamber_gas(
        state, require_provenance=True,
        tolerances=dataclasses.replace(
            DEFAULT_THERMO_TOLERANCES,
            state_identity_rel_tol=DEFAULT_THERMO_TOLERANCES.provider_identity_rel_tol))
    assert provider_aware.valid, [c.identity for c in provider_aware.failures]


def test_the_provider_tolerance_still_catches_a_real_error(cea_case):
    """Loose enough for CEA's constant, tight enough to catch a defect.

    A 1 % error in density is three orders of magnitude above the constants
    discrepancy and must still fail.
    """
    state = to_chamber_gas(cea_case, "cea")
    broken = dataclasses.replace(state, density=state.density * 1.01)
    assert broken.density != state.density, "the mutation must bite"
    report = validate_chamber_gas(
        broken,
        tolerances=dataclasses.replace(
            DEFAULT_THERMO_TOLERANCES,
            state_identity_rel_tol=DEFAULT_THERMO_TOLERANCES.provider_identity_rel_tol))
    assert not report.valid
    assert "p = rho R T" in {c.identity for c in report.failures}


def test_the_pre_2019_gas_constant_shows_up_where_expected(cea_case):
    """CEA's Ru is 8314.51; ours is CODATA 8314.46261815324.

    An adapter that recomputed R from CEA's own constant instead of ours would
    differ by about 5.7e-06, which is above `state_identity_rel_tol` of 1e-9.
    This test records that as a fact about CEA rather than adjusting either
    number, and it is why doc 09's originally proposed 1e-8 tolerance for a
    *provider comparison* was too tight.
    """
    ru_cea = float(cea_case["gas_constant_used_by_provider"])       # J/(kmol K)
    ru_ours = UNIVERSAL_GAS_CONSTANT * 1000.0
    relative = abs(ru_cea - ru_ours) / ru_ours
    assert relative == pytest.approx(5.7e-06, rel=0.05)

    molar_mass = float(cea_case["M_kg_per_kmol"]) / 1000.0
    r_from_cea = ru_cea / 1000.0 / molar_mass
    check = check_gas_constant(r_from_cea, molar_mass)
    assert not check.passed, (
        "using CEA's own Ru trips our identity check, which is the honest "
        "outcome: the adapter must recompute R from RocketForge's constant")
    assert check.residual == pytest.approx(relative, rel=0.05)


def test_unit_conversions_are_explicit_at_the_boundary(cea_case):
    """kg/kmol -> kg/mol and bar -> Pa happen once, visibly, in the adapter."""
    assert cea_case["native_units"]["M"] == "kg/kmol"
    assert cea_case["native_units"]["P"] == "bar"
    assert cea_case["native_units"]["cp"] == "kJ/(kg K)"
    state = to_chamber_gas(cea_case, "cea")
    assert 1.0e-3 < state.molar_mass < 1.0e-1          # kg/mol magnitude
    assert state.pressure == pytest.approx(1.0e7)      # Pa, not bar


def test_cea_capabilities_are_expressible(cea_case):
    """Everything Phase 5B-0 found CEA doing has a capability to declare."""
    caps = ProviderCapabilities(
        supported=frozenset({
            ProviderCapability.HP_EQUILIBRIUM,
            ProviderCapability.SP_EQUILIBRIUM,
            ProviderCapability.COMPOSITION,
            ProviderCapability.CONDENSED_PHASES,
            ProviderCapability.CONDENSED_PHASE_REPORTING,
            ProviderCapability.LIQUID_REACTANTS,
            ProviderCapability.CUSTOM_REACTANT_TEMPERATURE,
            ProviderCapability.CUSTOM_REACTANTS,
            ProviderCapability.CUSTOM_SPECIES_SET,
            ProviderCapability.EQUILIBRIUM_EXPANSION,
            ProviderCapability.FROZEN_EXPANSION,
            ProviderCapability.FREEZE_LOCATION_CONTROL,
            ProviderCapability.PRESSURE_RATIO_EXPANSION,
            ProviderCapability.AREA_RATIO_EXPANSION,
            ProviderCapability.NATIVE_EQUILIBRIUM_GAMMA,
            ProviderCapability.ROCKET_PERFORMANCE,
            ProviderCapability.TRANSPORT_PROPERTIES,
            ProviderCapability.IONISED_SPECIES,
        }))
    assert caps.supports(ProviderCapability.LIQUID_REACTANTS)
    assert caps.supports(ProviderCapability.ROCKET_PERFORMANCE)
    assert not caps.supports(ProviderCapability.KINETICS)


# ---------------------------------------------------------------------------
# Cantera
# ---------------------------------------------------------------------------


def test_real_cantera_output_maps_without_loss(cantera_case):
    """The same contract, from a provider with a different shape."""
    state = to_chamber_gas(cantera_case, "cantera")
    assert state.temperature == pytest.approx(3677.007652, rel=1e-9)
    assert len(state.composition.entries) == 9
    assert state.mode_is_recorded


def test_cantera_absent_equilibrium_cp_maps_to_none(cantera_case):
    """A capability gap becomes ``None``, never a fabricated number."""
    assert cantera_case["cp_equilibrium_J_per_kgK"] is None
    state = to_chamber_gas(cantera_case, "cantera")
    assert state.cp_equilibrium is None
    assert state.cp_frozen is not None


def test_cantera_finite_difference_gamma_is_still_a_valid_gamma(cantera_case):
    """Cantera has no native gamma_s; the adapter computes it and says so."""
    assert "gamma_s_note" in cantera_case
    assert "NOT native" in cantera_case["gamma_s_note"]
    state = to_chamber_gas(cantera_case, "cantera")
    assert state.gamma_equilibrium == pytest.approx(1.133472637, rel=1e-8)
    provenance = ThermochemistryProvenance(
        provider_id="cantera", library_version="3.2.0", database_version="x",
        warnings=("gamma_equilibrium is a finite-difference estimate",))
    assert provenance.warnings


def test_mapped_cantera_state_passes_even_the_strict_tolerance(cantera_case):
    """Cantera uses the CODATA constant, so its state closes on ours exactly.

    The contrast with CEA is the evidence that the provider tolerance is about
    a specific provider's constants rather than about sloppiness in general.
    """
    assert float(cantera_case["gas_constant_used_by_provider"]) == pytest.approx(
        UNIVERSAL_GAS_CONSTANT * 1000.0, rel=1e-15)
    state = to_chamber_gas(cantera_case, "cantera")
    report = validate_chamber_gas(state)
    assert report.valid, [c.identity for c in report.failures]
    assert report.max_residual < 1.0e-9


def test_the_contract_is_not_biased_toward_either_provider(cea_case, cantera_case):
    """Both map through the *same* function with no provider branch.

    ``to_chamber_gas`` above contains no ``if provider == ...``. If the domain
    model had been shaped around one library, it would.
    """
    cea = to_chamber_gas(cea_case, "cea")
    cantera = to_chamber_gas(cantera_case, "cantera")
    assert type(cea) is type(cantera)
    assert set(cea.composition.fractions) == set(cantera.composition.fractions)
    assert cea.provenance.provider_id != cantera.provenance.provider_id


def test_two_providers_disagreeing_stay_distinguishable(cea_case, cantera_case):
    """Different databases, so different answers -- and provenance says which.

    Phase 5B-0 measured 9.2e-04 relative on chamber temperature. Neither is
    treated as ground truth; the records simply remain separable.
    """
    cea = to_chamber_gas(cea_case, "cea")
    cantera = to_chamber_gas(cantera_case, "cantera")
    relative = abs(cea.temperature - cantera.temperature) / cea.temperature
    assert relative == pytest.approx(9.2e-04, rel=0.1)
    assert cea != cantera
    assert cea.provenance != cantera.provenance


def test_no_provider_module_is_imported_by_these_tests():
    """The fitness review reads recorded artifacts; it imports no provider.

    Checked **statically, on this module's own imports**, not through
    ``sys.modules``. The module table is process-global: once the Phase 5C
    provider tests have run in the same session, ``cea`` is legitimately
    present, and asserting its absence would be asserting something about the
    rest of the suite rather than about this file.
    """
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert not roots & {"cea", "cantera", "rocketcea"}, roots

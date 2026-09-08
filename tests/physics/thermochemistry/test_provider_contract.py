"""The provider contract, exercised against a deliberately fake provider.

The stub here **does not pretend to solve equilibrium**. It returns a fixed,
obviously fixture-driven state and identifies itself as ``stub:``, so a value
that escaped from it into an artifact would be recognisable rather than
plausible (Phase 5B spec section 119).

The conformance checks are written so that Phase 5C can point them at a real
NASA CEA adapter without rewriting them.
"""

from __future__ import annotations

import dataclasses

import pytest

from rocketforge.core.result import Solution, Status
from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    ChamberGas,
    ChemistryMode,
    Composition,
    CompositionBasis,
    EquilibriumConstraint,
    ExpansionMode,
    MixtureRatio,
    ProviderCapabilities,
    ProviderCapability,
    ProviderDomainError,
    ProviderUnavailableError,
    ThermochemistryProvenance,
    ThermochemistryProvider,
    UnsupportedCapabilityError,
)

MOLE = CompositionBasis.MOLE_FRACTION


# ---------------------------------------------------------------------------
# a fake provider, obviously fake
# ---------------------------------------------------------------------------


class StubProvider:
    """Returns one canned state. Solves nothing.

    Written to conform to :class:`ThermochemistryProvider` structurally, which
    is what the protocol is for: no inheritance, no registration.
    """

    provider_id = "stub:contract-test"
    version = "0.0-fixture"

    def __init__(self, capabilities: ProviderCapabilities | None = None) -> None:
        self.capabilities = capabilities or ProviderCapabilities(
            supported=frozenset({
                ProviderCapability.HP_EQUILIBRIUM,
                ProviderCapability.COMPOSITION,
                ProviderCapability.LIQUID_REACTANTS,
                ProviderCapability.CUSTOM_REACTANT_TEMPERATURE,
            }),
            pressure_range=(1.0e3, 5.0e7),
            mixture_ratio_range=(0.1, 20.0),
        )
        self.calls: list[ChamberEquilibriumRequest] = []

    def provenance(self) -> ThermochemistryProvenance:
        return ThermochemistryProvenance(
            provider_id=self.provider_id,
            provider_version=self.version,
            library_version="none -- fixture",
            database="synthetic fixture",
            database_version="0",
            chemistry_mode=ChemistryMode.EQUILIBRIUM,
            equilibrium_constraint=EquilibriumConstraint.HP,
        )

    def solve_chamber(self, request: ChamberEquilibriumRequest) -> Solution[ChamberGas]:
        self.capabilities.require(ProviderCapability.HP_EQUILIBRIUM,
                                  self.provider_id)
        if not self.capabilities.pressure_is_in_range(request.chamber_pressure):
            raise ProviderDomainError(
                f"chamber pressure {request.chamber_pressure} Pa is outside the "
                f"validated range {self.capabilities.pressure_range}")
        if not self.capabilities.mixture_ratio_is_in_range(request.of_mass):
            raise ProviderDomainError(
                f"O/F {request.of_mass} is outside the validated range "
                f"{self.capabilities.mixture_ratio_range}")
        self.calls.append(request)

        # A canned state. Deliberately not a plausible LOX/CH4 answer.
        composition = Composition.from_fractions({"FIXTURE_A": 0.6,
                                                  "FIXTURE_B": 0.4}, MOLE)
        state = ChamberGas(
            temperature=1234.5, gamma=1.25, gas_constant=300.0,
            molar_mass=8.31446261815324 / 300.0,
            composition=composition,
            pressure=request.chamber_pressure,
            request=request,
            provenance=dataclasses.replace(
                self.provenance(),
                reactant_conditions=request.reactant_conditions),
        )
        return Solution(value=state, status=Status.OK)


class NonConvergingStubProvider(StubProvider):
    """Reports non-convergence rather than raising.

    This is the case a bare return type cannot express, and the reason the
    protocol returns ``Solution``. RocketForge's own policy, from
    ``core/errors.py``: a solver that ran out of iterations "returns its best
    estimate with converged=False and never raises". Phase 5B-0 found NASA CEA
    exposing exactly such a flag.
    """

    provider_id = "stub:non-converging"

    def solve_chamber(self, request: ChamberEquilibriumRequest) -> Solution[ChamberGas]:
        return Solution(value=None, status=Status.NO_SOLUTION)


class UnavailableStubProvider(StubProvider):
    """Raises as an absent library would."""

    provider_id = "stub:unavailable"

    def solve_chamber(self, request: ChamberEquilibriumRequest) -> Solution[ChamberGas]:
        raise ProviderUnavailableError(
            "the fixture library is not installed; guarded imports must catch "
            "ImportError and ValueError alike")


@pytest.fixture
def chamber_request(methane_stream, lox_stream) -> ChamberEquilibriumRequest:
    return ChamberEquilibriumRequest(
        fuel=methane_stream, oxidiser=lox_stream,
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)


# ---------------------------------------------------------------------------
# structural conformance
# ---------------------------------------------------------------------------


def test_stub_conforms_structurally():
    """A Protocol, so conformance needs no inheritance and no registration."""
    assert isinstance(StubProvider(), ThermochemistryProvider)


def test_an_object_missing_the_interface_does_not_conform():
    class NotAProvider:
        provider_id = "nope"

    assert not isinstance(NotAProvider(), ThermochemistryProvider)


def test_provider_exposes_identity_capabilities_and_provenance(chamber_request):
    provider = StubProvider()
    assert provider.provider_id.startswith("stub:")
    assert isinstance(provider.capabilities, ProviderCapabilities)
    assert isinstance(provider.provenance(), ThermochemistryProvenance)


def test_provenance_is_available_before_anything_is_computed():
    """So an interface can show what is installed without solving."""
    provider = StubProvider()
    assert provider.provenance().provider_id == provider.provider_id
    assert provider.calls == []


# ---------------------------------------------------------------------------
# result contract
# ---------------------------------------------------------------------------


def test_solve_returns_an_immutable_rocketforge_state(chamber_request):
    provider = StubProvider()
    solution = provider.solve_chamber(chamber_request)
    assert solution.ok
    state = solution.unwrap()
    assert isinstance(state, ChamberGas)
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.temperature = 1.0  # type: ignore[misc]


def test_result_is_traceable_to_its_request(chamber_request):
    """Streams, actual temperatures, O/F, pressure and constraint, all recoverable."""
    state = StubProvider().solve_chamber(chamber_request).unwrap()
    assert state.request is chamber_request
    assert state.request.of_mass == pytest.approx(3.4)
    assert state.request.fuel.temperature == pytest.approx(111.643)
    assert state.request.oxidiser.temperature == pytest.approx(90.17)
    assert state.provenance.reactant_conditions["oxidiser_temperature"] == pytest.approx(90.17)


def test_result_records_its_chemistry_mode(chamber_request):
    """Without it, the state cannot enter the single-gamma handshake."""
    state = StubProvider().solve_chamber(chamber_request).unwrap()
    assert state.mode_is_recorded
    assert state.provenance.chemistry_mode is ChemistryMode.EQUILIBRIUM


def test_stub_output_is_recognisable_as_a_stub(chamber_request):
    state = StubProvider().solve_chamber(chamber_request).unwrap()
    assert state.provenance.is_stub


def test_no_provider_object_crosses_the_boundary(chamber_request):
    """Every field of the returned state is a RocketForge type or a scalar."""
    state = StubProvider().solve_chamber(chamber_request).unwrap()
    allowed = (type(None), bool, int, float, str, tuple)
    for field in dataclasses.fields(state):
        value = getattr(state, field.name)
        if isinstance(value, allowed):
            continue
        module = type(value).__module__
        assert module.startswith("rocketforge."), (
            f"{field.name} is a {module}.{type(value).__name__}, which is not a "
            "RocketForge domain type")


# ---------------------------------------------------------------------------
# the three failure classes, never conflated
# ---------------------------------------------------------------------------


def test_no_solution_is_reported_not_raised(chamber_request):
    solution = NonConvergingStubProvider().solve_chamber(chamber_request)
    assert not solution.ok
    assert solution.status is Status.NO_SOLUTION
    assert solution.value is None


def test_provider_unavailable_raises(chamber_request):
    with pytest.raises(ProviderUnavailableError):
        UnavailableStubProvider().solve_chamber(chamber_request)


def test_out_of_range_request_raises_a_domain_error_naming_the_range(
        methane_stream, lox_stream):
    provider = StubProvider()
    too_high = ChamberEquilibriumRequest(
        fuel=methane_stream, oxidiser=lox_stream,
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=1.0e9)
    with pytest.raises(ProviderDomainError, match="validated range"):
        provider.solve_chamber(too_high)


def test_malformed_input_never_reaches_the_provider(methane_stream, lox_stream):
    """The request refuses itself, so the provider is never consulted."""
    provider = StubProvider()
    with pytest.raises(Exception):
        ChamberEquilibriumRequest(
            fuel=methane_stream, oxidiser=lox_stream,
            oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=-1.0)
    assert provider.calls == []


# ---------------------------------------------------------------------------
# capabilities
# ---------------------------------------------------------------------------


def test_capabilities_are_declared_not_discovered():
    provider = StubProvider()
    assert provider.capabilities.supports(ProviderCapability.HP_EQUILIBRIUM)
    assert not provider.capabilities.supports(ProviderCapability.ROCKET_PERFORMANCE)


def test_an_undeclared_capability_raises_immediately(chamber_request):
    """It must never partially work and never quietly substitute another."""
    crippled = StubProvider(ProviderCapabilities(supported=frozenset()))
    with pytest.raises(UnsupportedCapabilityError, match="hp_equilibrium"):
        crippled.solve_chamber(chamber_request)


def test_capabilities_let_two_different_providers_be_honest():
    """CEA and Cantera differ sharply, and neither has to lie.

    Phase 5B-0: CEA has liquid reactants, rocket performance, area-ratio
    expansion and a native equilibrium gamma; Cantera has none of those but has
    kinetics.
    """
    cea_like = ProviderCapabilities(supported=frozenset({
        ProviderCapability.HP_EQUILIBRIUM, ProviderCapability.SP_EQUILIBRIUM,
        ProviderCapability.COMPOSITION, ProviderCapability.LIQUID_REACTANTS,
        ProviderCapability.ROCKET_PERFORMANCE,
        ProviderCapability.AREA_RATIO_EXPANSION,
        ProviderCapability.NATIVE_EQUILIBRIUM_GAMMA,
        ProviderCapability.FREEZE_LOCATION_CONTROL,
        ProviderCapability.EQUILIBRIUM_EXPANSION,
        ProviderCapability.FROZEN_EXPANSION,
    }))
    cantera_like = ProviderCapabilities(supported=frozenset({
        ProviderCapability.HP_EQUILIBRIUM, ProviderCapability.SP_EQUILIBRIUM,
        ProviderCapability.COMPOSITION, ProviderCapability.KINETICS,
        ProviderCapability.EQUILIBRIUM_EXPANSION,
        ProviderCapability.TRANSPORT_PROPERTIES,
    }))

    assert cea_like.supports(ProviderCapability.LIQUID_REACTANTS)
    assert not cantera_like.supports(ProviderCapability.LIQUID_REACTANTS)
    assert cea_like.supports(ProviderCapability.ROCKET_PERFORMANCE)
    assert not cantera_like.supports(ProviderCapability.ROCKET_PERFORMANCE)
    assert cantera_like.supports(ProviderCapability.KINETICS)
    assert not cea_like.supports(ProviderCapability.KINETICS)

    assert cea_like.supports_expansion_mode(ExpansionMode.FROZEN_AT_THROAT)
    assert not cantera_like.supports_expansion_mode(ExpansionMode.FROZEN_AT_THROAT)


def test_declaring_rocket_performance_does_not_move_the_physics_boundary():
    """A provider may supply c*; ownership still belongs to engineering.

    The capability says "this provider can give you an oracle value", not
    "relocate the performance physics into thermochemistry".
    """
    caps = ProviderCapabilities(
        supported=frozenset({ProviderCapability.ROCKET_PERFORMANCE}))
    assert caps.supports(ProviderCapability.ROCKET_PERFORMANCE)
    names = {f.name for f in dataclasses.fields(ChamberGas)}
    assert not names & {"c_star", "cf", "isp", "thrust"}


def test_undeclared_range_is_not_a_claim_of_validity():
    caps = ProviderCapabilities(supported=frozenset())
    assert caps.pressure_is_in_range(1.0e12)
    assert caps.mixture_ratio_is_in_range(1000.0)


def test_capabilities_are_frozen_and_typed():
    caps = ProviderCapabilities(supported=frozenset({ProviderCapability.COMPOSITION}))
    with pytest.raises(dataclasses.FrozenInstanceError):
        caps.supported = frozenset()  # type: ignore[misc]
    from rocketforge.physics.thermochemistry import ThermochemistryError
    with pytest.raises(ThermochemistryError):
        ProviderCapabilities(supported=frozenset({"hp_equilibrium"}))  # type: ignore[arg-type]

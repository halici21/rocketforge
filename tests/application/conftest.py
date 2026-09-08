"""Shared fixtures for the application-layer tests.

The interesting one is the stub thermochemistry provider. It exists so that the
*controller* logic -- staleness, filtering, aggregation, failure handling -- can
be tested deterministically and in the base environment, where no chemistry
library is installed.

**A stub proves nothing about chemistry.** Its numbers are made up and its
provenance id starts with ``stub:`` so that no artifact can mistake one for a
result. Everything scientific is checked separately against the real provider,
in the tests marked ``requires_cea``.
"""

from __future__ import annotations

import sys

import pytest
from PySide6.QtGui import QGuiApplication

from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.physics.thermochemistry import (
    ChamberGas,
    ChemistryMode,
    Composition,
    CompositionBasis,
    ElementalComposition,
    EquilibriumConstraint,
    Phase,
    Species,
    ThermochemistryProvenance,
)


@pytest.fixture(scope="session")
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    yield app


# ---------------------------------------------------------------------------
# a deterministic stand-in for a thermochemistry provider
# ---------------------------------------------------------------------------

#: Made-up species, with real formulae so the domain records are well formed.
STUB_SPECIES = {
    "H2O": Species(name="H2O", phase=Phase.GAS, molar_mass=0.018015,
                   formula=ElementalComposition.from_mapping({"H": 2, "O": 1})),
    "CO2": Species(name="CO2", phase=Phase.GAS, molar_mass=0.044009,
                   formula=ElementalComposition.from_mapping({"C": 1, "O": 2})),
    "CO": Species(name="CO", phase=Phase.GAS, molar_mass=0.028010,
                  formula=ElementalComposition.from_mapping({"C": 1, "O": 1})),
    "OH": Species(name="OH", phase=Phase.GAS, molar_mass=0.017007,
                  formula=ElementalComposition.from_mapping({"O": 1, "H": 1})),
    "C(gr)": Species(name="C(gr)", phase=Phase.SOLID, molar_mass=0.012011,
                     formula=ElementalComposition.from_mapping({"C": 1})),
}

#: Chosen to sum to exactly one, with a trace species and a condensed one.
#: The trace row is deliberate: the display-threshold proof needs a row it can
#: hide and then recover with its exact value intact.
STUB_FRACTIONS = {
    "H2O": 0.50,
    "CO2": 0.30,
    "CO": 0.19994999,
    "OH": 5.0e-5,
    "C(gr)": 1.0e-8,
}

#: No condensed species at all, so the condensed mass fraction is exactly zero.
#: This is a genuinely different state from "a tiny amount below the reporting
#: threshold", and the interface says two different things about them.
STUB_FRACTIONS_NO_CONDENSED = {
    "H2O": 0.50,
    "CO2": 0.30,
    "CO": 0.19995,
    "OH": 5.0e-5,
}

#: Solid carbon well above the reporting threshold, the shape of a real
#: fuel-rich case.
STUB_FRACTIONS_CONDENSED = {
    "H2O": 0.40,
    "CO2": 0.25,
    "CO": 0.25,
    "OH": 5.0e-5,
    "C(gr)": 0.09995,
}


class StubProvider:
    """A thermochemistry provider that computes nothing.

    It returns a fixed state whose values move with O/F only enough to make a
    sweep non-degenerate, and it can be told to fail at chosen mixture ratios so
    that failed-point handling can be tested without waiting for a real
    non-convergence.
    """

    provider_id = "stub:phase5d"
    version = "stub"

    #: Which product mixture to return. ``"trace"`` carries a condensed
    #: candidate below the reporting threshold, ``"none"`` carries none at all,
    #: and ``"present"`` carries solid carbon well above it -- the three states
    #: the interface must describe differently.
    MIXTURES = {
        "trace": STUB_FRACTIONS,
        "none": STUB_FRACTIONS_NO_CONDENSED,
        "present": STUB_FRACTIONS_CONDENSED,
    }

    def __init__(self, *, fail_at=(), warn=False, condensed="trace") -> None:
        self.fail_at = tuple(round(float(v), 6) for v in fail_at)
        self.warn = warn
        self.condensed = condensed
        self.calls: list = []

    def species_table(self, names):
        return {name: STUB_SPECIES[name] for name in names if name in STUB_SPECIES}

    def provenance(self, species_set=(), reactant_conditions=None):
        return ThermochemistryProvenance(
            provider_id=self.provider_id,
            provider_version=self.version,
            library_version="0.0-stub",
            database="stub.lib",
            database_version="stub",
            chemistry_mode=ChemistryMode.EQUILIBRIUM,
            equilibrium_constraint=EquilibriumConstraint.HP,
            species_set=tuple(species_set) or tuple(STUB_FRACTIONS),
            reactant_conditions=dict(reactant_conditions or {}),
        )

    def solve_chamber(self, request):
        self.calls.append(request)
        of = round(float(request.of_mass), 6)
        provenance = self.provenance(
            species_set=tuple(self.MIXTURES[self.condensed]),
            reactant_conditions=request.reactant_conditions)

        if of in self.fail_at:
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="PROVIDER_NOT_CONVERGED", severity=Severity.ERROR,
                    message="stub provider was told to fail here",
                    field="converged"),),
                provenance=(provenance,))

        composition = Composition.from_fractions(
            self.MIXTURES[self.condensed], CompositionBasis.MOLE_FRACTION)
        molar_mass = composition.mean_molar_mass(STUB_SPECIES)
        gas_constant = composition.specific_gas_constant(STUB_SPECIES)
        cp = 2000.0 + 10.0 * of
        state = ChamberGas(
            temperature=3000.0 + 100.0 * of,
            gamma=1.20 - 0.01 * of,
            gas_constant=gas_constant,
            molar_mass=molar_mass,
            composition=composition,
            pressure=float(request.chamber_pressure),
            density=7.0,
            cp=cp,
            cv=cp - gas_constant,
            cp_frozen=cp,
            cp_equilibrium=cp * 2.0,
            gamma_frozen=cp / (cp - gas_constant),
            gamma_equilibrium=1.20 - 0.01 * of,
            enthalpy=-1.0e6,
            entropy=12000.0,
            condensed_mass_fraction=composition.condensed_mass_fraction(STUB_SPECIES),
            request=request,
            provenance=provenance,
        )
        diagnostics = ()
        status = Status.OK
        if self.warn:
            diagnostics = (Diagnostic(
                code="PROVIDER_ASSIGNED_ENTHALPY_REACTANT",
                severity=Severity.WARNING,
                message="NASA CEA models reactant 'O2(L)' with an assigned "
                        "enthalpy at 90.17 K.",
                field="reactant_temperature",
                detail={"requested": 95.0, "assigned": 90.17}),)
            status = Status.OK_WITH_WARNINGS
        return Solution(value=state, status=status, diagnostics=diagnostics,
                        provenance=(provenance,))


@pytest.fixture()
def stub_provider_class():
    """The stub class itself, for a test that needs to build several.

    Handed over as a fixture rather than imported: two conftest modules in this
    suite share the name ``conftest``, so ``from conftest import ...`` resolves
    to whichever one pytest imported first and fails depending on what else the
    session collected.
    """
    return StubProvider


@pytest.fixture()
def gateway():
    """The provider gateway, with its cached state restored afterwards.

    Every test that swaps a provider in goes through here, so no test can leak
    a stub into another test's environment.
    """
    from rocketforge.application.analysis import thermochemistry_provider as gw

    saved = (gw._availability, gw._provider, gw._options)
    try:
        yield gw
    finally:
        gw._availability, gw._provider, gw._options = saved


@pytest.fixture()
def stub_gateway(gateway):
    """The gateway wired to a stub provider that always solves."""
    from rocketforge.application.analysis.thermochemistry_provider import (
        ProviderAvailability,
    )

    provider = StubProvider()
    gateway._availability = ProviderAvailability(
        status="available", usable=True, version="stub",
        library_version="0.0-stub")
    gateway._provider = provider
    return provider


@pytest.fixture()
def absent_gateway(gateway):
    """The gateway wired to no provider at all."""
    from rocketforge.application.analysis.thermochemistry_provider import (
        NOT_INSTALLED_REMEDY,
        ProviderAvailability,
    )

    gateway._availability = ProviderAvailability(
        status="not_installed", usable=False,
        detail="the 'cea' distribution is not installed",
        remedy=NOT_INSTALLED_REMEDY)
    gateway._provider = None
    return gateway


@pytest.fixture()
def warning_gateway(gateway):
    """The gateway wired to a stub that reports an assigned-enthalpy warning."""
    from rocketforge.application.analysis.thermochemistry_provider import (
        ProviderAvailability,
    )

    provider = StubProvider(warn=True)
    gateway._availability = ProviderAvailability(
        status="available", usable=True, version="stub",
        library_version="0.0-stub")
    gateway._provider = provider
    return provider


@pytest.fixture()
def failing_gateway(gateway):
    """The gateway wired to a stub that refuses one specific mixture ratio.

    Injecting a failure is the only practical way to test failed-point
    handling: a real provider converges everywhere in the useful range, so
    waiting for a genuine non-convergence would mean never testing the path.
    """
    from rocketforge.application.analysis.thermochemistry_provider import (
        ProviderAvailability,
    )

    provider = StubProvider(fail_at=(3.0,))
    gateway._availability = ProviderAvailability(
        status="available", usable=True, version="stub",
        library_version="0.0-stub")
    gateway._provider = provider
    return provider


@pytest.fixture()
def no_condensed_gateway(gateway):
    """A stub whose products contain no condensed species at all."""
    from rocketforge.application.analysis.thermochemistry_provider import (
        ProviderAvailability,
    )

    provider = StubProvider(condensed="none")
    gateway._availability = ProviderAvailability(
        status="available", usable=True, version="stub",
        library_version="0.0-stub")
    gateway._provider = provider
    return provider


@pytest.fixture()
def condensed_gateway(gateway):
    """A stub carrying solid carbon well above the reporting threshold."""
    from rocketforge.application.analysis.thermochemistry_provider import (
        ProviderAvailability,
    )

    provider = StubProvider(condensed="present")
    gateway._availability = ProviderAvailability(
        status="available", usable=True, version="stub",
        library_version="0.0-stub")
    gateway._provider = provider
    return provider

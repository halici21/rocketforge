"""Provider-independent checks on compositions and thermodynamic states.

These validators **report**; they do not raise. Their job is to measure a
discrepancy, and a caller decides what a discrepancy means. Constructors raise
for malformed input; validators quantify inconsistency in well-formed input.
The two roles are kept apart on purpose.

Every check here is reference-free: it needs no published table and no provider,
only the numbers already in hand. That is what makes them usable as a
conformance suite for a future NASA CEA or Cantera adapter -- an adapter that
scales one field and not another is caught by arithmetic, not by an oracle.

The redundancy in the state records is deliberate and this module is why it
exists. ``ChamberGas`` carries both ``gas_constant`` and ``molar_mass``, whose
relation is fixed; a provider adapter that converts one and forgets the other
is detected immediately (``09`` section 7.2).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.core.result import Diagnostic, Severity

from .composition import (
    Composition,
    ElementalInventoryBasis,
    compare_elemental_inventories,
    elemental_inventory,
    mass_to_mole_fractions,
    mole_to_mass_fractions,
)
from .provenance import ThermochemistryProvenance
from .species import Species
from .states import ChamberGas, GasStation
from .tolerances import DEFAULT_THERMO_TOLERANCES, ThermochemistryTolerances
from .types import CompositionBasis

__all__ = [
    "IdentityCheck",
    "ValidationReport",
    "check_composition_sum",
    "check_composition_round_trip",
    "check_mean_molar_mass_paths",
    "check_gas_constant",
    "check_cp_cv_relation",
    "check_gamma_definition",
    "check_ideal_gas",
    "check_element_balance",
    "check_provenance_completeness",
    "validate_chamber_gas",
    "validate_gas_station",
]


def _relative(left: float, right: float) -> float:
    """Scale-aware relative difference. Never returns a negative zero."""
    difference = abs(left - right)
    scale = max(abs(left), abs(right))
    if scale == 0.0:
        return 0.0
    return difference / scale


@dataclass(frozen=True, slots=True)
class IdentityCheck:
    """The outcome of one identity check.

    Attributes:
        identity: The relation checked, written the way it would be read aloud,
            e.g. ``"R = Ru / M"``.
        passed: Whether ``residual <= tolerance``.
        residual: Relative discrepancy, always non-negative.
        tolerance: The tolerance applied.
        left: The value on the left of the identity, when it is a single number.
        right: The value on the right.
        applicable: ``False`` when the state did not carry the fields this check
            needs. A check that could not run is **not** a check that passed,
            and the two are never collapsed.
        detail: Free text, for the one case where a number is not enough.
    """

    identity: str
    passed: bool
    residual: float
    tolerance: float
    left: float | None = None
    right: float | None = None
    applicable: bool = True
    detail: str = ""

    @classmethod
    def not_applicable(cls, identity: str, reason: str) -> "IdentityCheck":
        """A check that could not run because its inputs were absent."""
        return cls(identity=identity, passed=True, residual=0.0, tolerance=0.0,
                   applicable=False, detail=reason)

    def to_diagnostic(self) -> Diagnostic:
        """This check as a core :class:`Diagnostic`.

        Severity distinguishes the three outcomes rather than flattening them:
        a check that did not run is INFO, a passing check is INFO, a failing one
        is ERROR (Phase 5B spec section 219).
        """
        if not self.applicable:
            return Diagnostic(
                code="IDENTITY_NOT_APPLICABLE", severity=Severity.INFO,
                message=f"{self.identity}: not checked -- {self.detail}",
                field=self.identity)
        if self.passed:
            return Diagnostic(
                code="IDENTITY_OK", severity=Severity.INFO,
                message=f"{self.identity}: residual {self.residual:.3e} "
                        f"within {self.tolerance:.3e}",
                field=self.identity,
                detail={"residual": self.residual, "tolerance": self.tolerance})
        return Diagnostic(
            code="IDENTITY_VIOLATED", severity=Severity.ERROR,
            message=f"{self.identity}: residual {self.residual:.3e} exceeds "
                    f"{self.tolerance:.3e}",
            field=self.identity,
            detail={"residual": self.residual, "tolerance": self.tolerance})


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """The outcome of a group of identity checks."""

    checks: tuple[IdentityCheck, ...]

    @property
    def valid(self) -> bool:
        """Whether every applicable check passed."""
        return all(check.passed for check in self.checks if check.applicable)

    @property
    def failures(self) -> tuple[IdentityCheck, ...]:
        """The checks that ran and failed."""
        return tuple(c for c in self.checks if c.applicable and not c.passed)

    @property
    def skipped(self) -> tuple[IdentityCheck, ...]:
        """The checks that could not run. Reported, never counted as passes."""
        return tuple(c for c in self.checks if not c.applicable)

    @property
    def max_residual(self) -> float:
        """Largest residual among the checks that ran."""
        applicable = [c.residual for c in self.checks if c.applicable]
        return max(applicable) if applicable else 0.0

    def by_identity(self) -> Mapping[str, IdentityCheck]:
        """The checks, keyed by identity name."""
        return MappingProxyType({c.identity: c for c in self.checks})

    def to_diagnostics(self) -> tuple[Diagnostic, ...]:
        """Every check as a core diagnostic, for attaching to a ``Solution``."""
        return tuple(c.to_diagnostic() for c in self.checks)


# ---------------------------------------------------------------------------
# composition checks
# ---------------------------------------------------------------------------


def check_composition_sum(
    composition: Composition,
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> IdentityCheck:
    """Fractions sum to one.

    A well-formed :class:`Composition` satisfies this by construction, so a
    failure here means the record was assembled by something that bypassed the
    constructor -- which is exactly what a mutation test does.
    """
    total = composition.sum()
    residual = abs(total - 1.0)
    return IdentityCheck(
        identity="sum(fractions) = 1",
        passed=residual <= tolerances.composition_sum_tol,
        residual=residual,
        tolerance=tolerances.composition_sum_tol,
        left=total,
        right=1.0,
    )


def check_composition_round_trip(
    composition: Composition,
    species: Mapping[str, Species],
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> IdentityCheck:
    """Converting basis and back returns the original fractions.

    Cheap, and it catches the single most common chemistry bug in engineering
    software: a mole/mass conversion that is inverted, or that divides where it
    should multiply.
    """
    masses = {name: species[name].molar_mass for name in composition.species_names}
    original = dict(composition.fractions)
    if composition.basis is CompositionBasis.MOLE_FRACTION:
        there = mole_to_mass_fractions(original, masses)
        back = mass_to_mole_fractions(there, masses)
    else:
        there = mass_to_mole_fractions(original, masses)
        back = mole_to_mass_fractions(there, masses)
    residual = max((_relative(original[name], back[name]) for name in original),
                   default=0.0)
    return IdentityCheck(
        identity="composition round trip X -> Y -> X",
        passed=residual <= tolerances.identity_rel_tol,
        residual=residual,
        tolerance=tolerances.identity_rel_tol,
    )


def check_mean_molar_mass_paths(
    composition: Composition,
    species: Mapping[str, Species],
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> IdentityCheck:
    """``sum(X_i M_i)`` and ``1 / sum(Y_i / M_i)`` describe the same quantity.

    Two independent routes to the mean molar mass. They agree for a consistent
    mixture and diverge for an inconsistent one, which makes this a useful check
    on a provider that supplies both bases.
    """
    from_mole = composition.to_basis(
        CompositionBasis.MOLE_FRACTION, species).mean_molar_mass(species)
    from_mass = composition.to_basis(
        CompositionBasis.MASS_FRACTION, species).mean_molar_mass(species)
    residual = _relative(from_mole, from_mass)
    return IdentityCheck(
        identity="M from mole basis = M from mass basis",
        passed=residual <= tolerances.identity_rel_tol,
        residual=residual,
        tolerance=tolerances.identity_rel_tol,
        left=from_mole,
        right=from_mass,
    )


# ---------------------------------------------------------------------------
# state identity checks
# ---------------------------------------------------------------------------


def check_gas_constant(
    gas_constant: float | None,
    molar_mass: float | None,
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> IdentityCheck:
    """``R = Ru / M``.

    Storing both R and M is redundant, and the redundancy is the point: a
    provider adapter that scales one and not the other is caught here
    immediately. Uses RocketForge's canonical universal gas constant, which is
    **not** adjusted to match any provider's historical convention -- Phase 5B-0
    measured NASA CEA using a pre-2019 value, and absorbing that belongs to the
    CEA adapter's comparison tolerance, not to this identity.
    """
    identity = "R = Ru / M"
    if gas_constant is None or molar_mass is None:
        return IdentityCheck.not_applicable(
            identity, "state does not carry both R and M")
    expected = UNIVERSAL_GAS_CONSTANT / float(molar_mass)
    residual = _relative(float(gas_constant), expected)
    return IdentityCheck(
        identity=identity,
        passed=residual <= tolerances.state_identity_rel_tol,
        residual=residual,
        tolerance=tolerances.state_identity_rel_tol,
        left=float(gas_constant),
        right=expected,
    )


def check_cp_cv_relation(
    cp: float | None,
    cv: float | None,
    gas_constant: float | None,
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> IdentityCheck:
    """``cp - cv = R`` for an ideal gas.

    Conditional: it holds for the ideal-gas model this package's states
    describe, and it is skipped rather than failed when the fields are absent.
    """
    identity = "cp - cv = R"
    if cp is None or cv is None or gas_constant is None:
        return IdentityCheck.not_applicable(
            identity, "state does not carry cp, cv and R")
    difference = float(cp) - float(cv)
    residual = _relative(difference, float(gas_constant))
    return IdentityCheck(
        identity=identity,
        passed=residual <= tolerances.state_identity_rel_tol,
        residual=residual,
        tolerance=tolerances.state_identity_rel_tol,
        left=difference,
        right=float(gas_constant),
    )


def check_gamma_definition(
    gamma: float | None,
    cp: float | None,
    cv: float | None,
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
    label: str = "gamma",
) -> IdentityCheck:
    """``gamma = cp / cv``.

    **Applies to the frozen gamma only.** The equilibrium isentropic exponent is
    a different quantity and does *not* equal cp/cv: Phase 5B-0 measured
    gamma_s = 1.1336 against a frozen cp/cv of 1.1985 on the same state, a 5.7 %
    difference. Applying this identity to an equilibrium gamma would fail a
    correct provider, so callers pass the frozen pair (``11`` section 4).
    """
    identity = f"{label} = cp / cv"
    if gamma is None or cp is None or cv is None:
        return IdentityCheck.not_applicable(
            identity, "state does not carry gamma, cp and cv")
    ratio = float(cp) / float(cv)
    residual = _relative(float(gamma), ratio)
    return IdentityCheck(
        identity=identity,
        passed=residual <= tolerances.state_identity_rel_tol,
        residual=residual,
        tolerance=tolerances.state_identity_rel_tol,
        left=float(gamma),
        right=ratio,
    )


def check_ideal_gas(
    pressure: float | None,
    density: float | None,
    gas_constant: float | None,
    temperature: float | None,
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> IdentityCheck:
    """``p = rho R T``.

    Reports the discrepancy; it never adjusts a field to force the identity.
    """
    identity = "p = rho R T"
    if None in (pressure, density, gas_constant, temperature):
        return IdentityCheck.not_applicable(
            identity, "state does not carry p, rho, R and T")
    predicted = float(density) * float(gas_constant) * float(temperature)
    residual = _relative(float(pressure), predicted)
    return IdentityCheck(
        identity=identity,
        passed=residual <= tolerances.state_identity_rel_tol,
        residual=residual,
        tolerance=tolerances.state_identity_rel_tol,
        left=float(pressure),
        right=predicted,
    )


def check_element_balance(
    reactants: Composition,
    products: Composition,
    species: Mapping[str, Species],
    *,
    basis: ElementalInventoryBasis = ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> IdentityCheck:
    """Chemistry rearranged atoms without creating or destroying any.

    The most valuable check available to this layer, and the only one that is
    simultaneously provider-independent, propellant-independent and
    reference-free. It catches a mis-parsed formula, a dropped species, an
    inverted mixture ratio and a units slip in the mass basis -- the largest
    class of real defects (``09`` section 3.2).

    Defaults to a **per-kilogram** basis, because that is the basis on which
    reactants and products are genuinely comparable: one mole of reactants does
    not become one mole of products, but one kilogram does stay one kilogram.
    """
    left = elemental_inventory(reactants, species, basis)
    right = elemental_inventory(products, species, basis)
    report = compare_elemental_inventories(left, right, tolerances=tolerances)
    worst = f" (worst element {report.worst_element})" if report.worst_element else ""
    return IdentityCheck(
        identity="element conservation, reactants = products",
        passed=report.balanced,
        residual=report.max_residual,
        tolerance=report.tolerance,
        detail=f"basis {basis.value}{worst}",
    )


def check_provenance_completeness(
    provenance: ThermochemistryProvenance | None,
) -> IdentityCheck:
    """A result identifies its provider *and* the data behind it.

    Not a numerical identity, reported through the same structure so a caller
    handles one kind of thing. A result whose provenance names a provider but
    not its thermodynamic data cannot be reproduced later, because the data can
    change under a version bump (``10`` section 9).
    """
    identity = "provenance identifies provider and data"
    if provenance is None:
        return IdentityCheck(
            identity=identity, passed=False, residual=1.0, tolerance=0.0,
            detail="state carries no provenance at all")
    if not provenance.is_reproducible:
        missing = []
        if not (provenance.library_version.strip() or provenance.provider_version.strip()):
            missing.append("a provider or library version")
        if not (provenance.database_sha256.strip() or provenance.database_version.strip()):
            missing.append("a database version or hash")
        return IdentityCheck(
            identity=identity, passed=False, residual=1.0, tolerance=0.0,
            detail=f"provenance for {provenance.provider_id!r} lacks "
                   + " and ".join(missing))
    return IdentityCheck(identity=identity, passed=True, residual=0.0, tolerance=0.0,
                         detail=f"provider {provenance.provider_id!r}")


# ---------------------------------------------------------------------------
# state-level aggregates
# ---------------------------------------------------------------------------


def validate_chamber_gas(
    state: ChamberGas,
    species: Mapping[str, Species] | None = None,
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
    require_provenance: bool = False,
) -> ValidationReport:
    """Run every applicable identity check on a chamber state.

    ``species`` is optional: without it the composition-based checks are
    reported as not applicable rather than silently skipped.
    """
    checks: list[IdentityCheck] = [
        check_gas_constant(state.gas_constant, state.molar_mass,
                           tolerances=tolerances),
        check_cp_cv_relation(state.cp, state.cv, state.gas_constant,
                             tolerances=tolerances),
        check_gamma_definition(
            state.gamma_frozen, state.cp_frozen or state.cp, state.cv,
            tolerances=tolerances, label="gamma_frozen"),
        check_ideal_gas(state.pressure, state.density, state.gas_constant,
                        state.temperature, tolerances=tolerances),
        check_composition_sum(state.composition, tolerances=tolerances),
    ]
    if species is not None:
        checks.append(check_composition_round_trip(
            state.composition, species, tolerances=tolerances))
        checks.append(check_mean_molar_mass_paths(
            state.composition, species, tolerances=tolerances))
        mixture_mass = state.composition.mean_molar_mass(species)
        checks.append(IdentityCheck(
            identity="state M = composition M",
            passed=_relative(state.molar_mass, mixture_mass)
            <= tolerances.state_identity_rel_tol,
            residual=_relative(state.molar_mass, mixture_mass),
            tolerance=tolerances.state_identity_rel_tol,
            left=state.molar_mass, right=mixture_mass,
        ))
    else:
        checks.append(IdentityCheck.not_applicable(
            "composition round trip X -> Y -> X", "no species table supplied"))
        checks.append(IdentityCheck.not_applicable(
            "M from mole basis = M from mass basis", "no species table supplied"))
        checks.append(IdentityCheck.not_applicable(
            "state M = composition M", "no species table supplied"))
    if require_provenance:
        checks.append(check_provenance_completeness(state.provenance))
    return ValidationReport(checks=tuple(checks))


def validate_gas_station(
    state: GasStation,
    species: Mapping[str, Species] | None = None,
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> ValidationReport:
    """Run every applicable identity check on an expansion station."""
    checks: list[IdentityCheck] = [
        check_gas_constant(state.gas_constant, state.molar_mass,
                           tolerances=tolerances),
        check_cp_cv_relation(state.cp, state.cv, state.gas_constant,
                             tolerances=tolerances),
        check_gamma_definition(
            state.gamma_frozen, state.cp_frozen or state.cp, state.cv,
            tolerances=tolerances, label="gamma_frozen"),
        check_ideal_gas(state.pressure, state.density, state.gas_constant,
                        state.temperature, tolerances=tolerances),
    ]
    if state.composition is not None:
        checks.append(check_composition_sum(state.composition, tolerances=tolerances))
        if species is not None:
            checks.append(check_composition_round_trip(
                state.composition, species, tolerances=tolerances))
    else:
        checks.append(IdentityCheck.not_applicable(
            "sum(fractions) = 1",
            "station composition is inherited from the chamber (frozen flow)"))
    return ValidationReport(checks=tuple(checks))

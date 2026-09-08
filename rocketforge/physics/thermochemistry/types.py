"""Foundational enumerations for the thermochemistry domain.

Every member here is a *decision*, not a convenience: each one exists because
leaving the distinction implicit is a known way to get a plausible wrong
answer. The specifications are ``docs/engineering/09``, ``11`` and ``12``.

Naming note. Phase 5A spells the oxidising role ``OXIDISER`` (``09`` section
4.1), and Phase 5A is authoritative for names, so that spelling is canonical
throughout this package. No ``OXIDIZER`` alias is provided: two spellings for
one concept is exactly the kind of ambiguity this package exists to remove.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "Phase",
    "CompositionBasis",
    "PropellantRole",
    "MixtureRatioBasis",
    "ChemistryMode",
    "ExpansionMode",
    "FreezeLocation",
    "EquilibriumConstraint",
    "GammaStrategy",
]


class Phase(StrEnum):
    """The physical phase of a species or a stream.

    Phase is part of a species' *identity*, not a label attached to it: ``H2O``
    and ``H2O(L)`` have different formation enthalpies, and folding them into
    one record with a phase flag is how the latent heat gets lost
    (``09`` section 2.2).

    There is deliberately **no** ``UNKNOWN`` member. Phase 5A ``09`` section 3.3
    defines exactly these four, and an enum member for "unknown" would be a
    value that silently satisfies a required field. Where a phase genuinely may
    be unknown the field is typed ``Phase | None`` and ``None`` means unknown --
    never ``GAS``. Nothing in this package defaults a phase to ``GAS``.
    """

    GAS = "gas"
    LIQUID = "liquid"
    SOLID = "solid"
    SUPERCRITICAL = "supercritical"
    """A real and common *reactant* condition -- LOX above 5.04 MPa in a
    regeneratively cooled feed system. Naming it is better than misfiling it as
    a liquid. Product species take only GAS, LIQUID or SOLID."""

    @property
    def is_condensed(self) -> bool:
        """True for LIQUID and SOLID.

        SUPERCRITICAL is deliberately excluded: a supercritical fluid is not a
        condensed phase in the two-phase-flow sense that ``11`` section 7 cares
        about, and counting it as one would wrongly refuse valid single-phase
        chamber states.
        """
        return self in (Phase.LIQUID, Phase.SOLID)


class CompositionBasis(StrEnum):
    """Whether a set of fractions is by mole or by mass.

    The basis always travels with the numbers. This is the same discipline that
    keeps Darcy and Fanning friction factors apart in the Fanno module: the
    ambiguity is real, the failure is silent, so the unit is carried rather
    than assumed (``09`` section 4.3).

    Mole fraction is RocketForge's *canonical* stored basis (ADR-18); mass
    fraction is accepted on input and derived on request.
    """

    MOLE_FRACTION = "mole_fraction"
    MASS_FRACTION = "mass_fraction"


class PropellantRole(StrEnum):
    """What part a propellant plays in a combustion request (``09`` s. 4.1)."""

    FUEL = "fuel"
    OXIDISER = "oxidiser"
    MONOPROPELLANT = "monopropellant"
    """Present from the start because hydrazine and hydrogen peroxide are the
    cases where O/F is undefined. A type that cannot express them invites a
    fake mixture ratio to be invented (``09`` section 6.5)."""


class MixtureRatioBasis(StrEnum):
    """The basis an O/F ratio was stated on.

    ``MASS`` is canonical. ``MOLAR`` is accepted on input and converted on
    construction, with the original basis remembered so provenance can say so
    (``09`` section 6.2).
    """

    MASS = "mass"
    MOLAR = "molar"


class ChemistryMode(StrEnum):
    """How chemistry is treated when the chamber state is computed.

    One member, deliberately (``11`` section 2). The chamber is computed at
    equilibrium; there is no "frozen chamber", because freezing requires a
    prior composition to freeze *at*, and upstream of the chamber there are
    only unreacted propellants. The enum exists so provenance always carries a
    chamber mode, and so a future kinetic mode has somewhere to go.
    """

    EQUILIBRIUM = "equilibrium"


class FreezeLocation(StrEnum):
    """Where composition is frozen, when it is frozen.

    Explicit because the freeze point changes what the model means: freezing at
    the chamber and freezing at the throat give materially different exit
    conditions (``11`` section 5.4). A boolean ``frozen=True`` cannot express
    the difference, so this package does not offer one.
    """

    CHAMBER = "chamber"
    THROAT = "throat"


class ExpansionMode(StrEnum):
    """How chemistry is treated during an expansion (``11`` section 2).

    ``EQUILIBRIUM`` and ``FROZEN`` bracket reality: chemistry infinitely fast
    and infinitely slow respectively. Neither is "the" answer, and this package
    offers no interpolation between them -- a blended number would have no
    physical basis (``11`` section 5.5).

    **Frozen composition is not constant gamma.** A frozen mixture still has a
    temperature-dependent cp, so gamma still varies along the expansion. Any
    code that treats ``FROZEN`` as "constant gamma" is wrong
    (``11`` section 5.3).
    """

    EQUILIBRIUM = "equilibrium"
    """Shifting: composition is re-solved at every station."""

    FROZEN = "frozen"
    """Composition fixed at the chamber value."""

    FROZEN_AT_THROAT = "frozen_at_throat"
    """Equilibrium to the throat, frozen thereafter."""

    @property
    def freeze_location(self) -> FreezeLocation | None:
        """Where this mode freezes composition, or None if it never does."""
        if self is ExpansionMode.FROZEN:
            return FreezeLocation.CHAMBER
        if self is ExpansionMode.FROZEN_AT_THROAT:
            return FreezeLocation.THROAT
        return None


class EquilibriumConstraint(StrEnum):
    """The pair of thermodynamic properties held fixed while equilibrating.

    Only the two constraints Phase 5A actually uses are exposed. Providers
    support more -- CEA offers TP, UV, TV and SV -- but exposing every mode a
    library happens to implement would make this enum a description of CEA
    rather than of RocketForge.

    The chamber is an ``HP`` problem and not ``UV`` or ``TP``: a rocket chamber
    is a steady-flow device at a pressure set by the throat, so enthalpy and
    pressure are what is conserved. A constant-volume ``UV`` calculation gives a
    noticeably higher temperature because none of the energy goes into the flow
    work of pushing product out -- correct for a bomb calorimeter, wrong for a
    rocket (``11`` section 3.2).
    """

    HP = "HP"
    """Fixed specific enthalpy and pressure. The chamber problem."""

    SP = "SP"
    """Fixed specific entropy and pressure. The ideal expansion problem
    (``11`` section 5.1)."""


class GammaStrategy(StrEnum):
    """Which single gamma represents a varying-gamma expansion.

    **No member is a default and none is correct** (``12`` section 5). Each is a
    stated approximation with a documented bias, and a strategy the user did not
    choose produces a number the user cannot interpret. Nothing in RocketForge
    may select one of these implicitly.

    This enum is a *data contract* only. Phase 5B implements no gamma reduction
    and no nozzle coupling; the adapter that consumes it belongs to
    ``engineering.chamber`` (``12`` section 8).
    """

    CHAMBER = "chamber"
    """Gamma at the chamber state. Overstates gamma at the exit, so understates
    exit Mach. Best for small expansion ratios."""

    THROAT = "throat"
    """Gamma at the sonic condition. Right for mass flow and c*, which are set
    at the throat; not representative of the diverging section."""

    EXIT = "exit"
    """Gamma at the exit condition. Right for exit-plane conditions; distorts
    the throat, so distorts mass flow."""

    CHAMBER_EXIT_MEAN = "chamber_exit_mean"
    """Arithmetic mean of the endpoints. A crude compromise: the endpoints are
    not where the variation is."""

    EFFECTIVE_ISENTROPIC = "effective_isentropic"
    """Fitted so the single-gamma isentropic relation reproduces the true
    temperature ratio over the actual pressure ratio. The most defensible
    single-gamma choice, and still an approximation -- a fitted exponent that
    matches the endpoints does not match the interior."""

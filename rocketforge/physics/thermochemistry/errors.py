"""Thermochemistry-specific errors.

Deliberately few. ``docs/engineering/09`` section 12 and the project's standing
policy both say the existing hierarchy is reused rather than duplicated, so
these classes derive from :mod:`rocketforge.core.errors` and exist only where
the core hierarchy has no name for what went wrong.

The governing policy is unchanged from Phase 4A:

    Raise for invalid input; report for unattainable physics.

A composition whose fractions do not sum to one is a malformed argument and
raises. A chemistry request that no provider can satisfy is a ``Solution`` with
``NO_SOLUTION`` and a diagnostic -- but nothing in Phase 5B solves chemistry, so
that second case arrives with the providers in Phase 5C.
"""

from __future__ import annotations

from rocketforge.core.errors import DomainError, InputError, RocketForgeError

__all__ = [
    "ThermochemistryError",
    "SpeciesError",
    "UnknownSpeciesError",
    "CompositionError",
    "CompositionBasisError",
    "CompositionSumError",
    "ElementalCompositionError",
    "PropellantError",
    "PropellantRoleError",
    "MixtureRatioError",
    "StateConsistencyError",
    "ProviderError",
    "ProviderUnavailableError",
    "ProviderDomainError",
    "UnsupportedCapabilityError",
]


class ThermochemistryError(RocketForgeError):
    """Base class for every error this package raises deliberately.

    Derives from :class:`~rocketforge.core.errors.RocketForgeError` so that
    ``except RocketForgeError`` still catches the whole project.
    """


# ---------------------------------------------------------------------------
# species
# ---------------------------------------------------------------------------


class SpeciesError(ThermochemistryError, InputError):
    """A species record is malformed."""


class UnknownSpeciesError(SpeciesError):
    """A composition referenced a species name that was not supplied.

    Raised rather than defaulted: a missing species silently treated as absent
    would break element conservation while every fraction still summed to one.
    """


class ElementalCompositionError(SpeciesError):
    """An elemental formula is malformed.

    Raised for a negative atom count, a non-finite count, an empty formula on a
    species that needs one, or an element symbol that is not a plain string.
    Non-integer counts are *not* an error: an empirical surrogate formula such
    as RP-1's is fractional by construction (``09`` section 4.5).
    """


# ---------------------------------------------------------------------------
# composition
# ---------------------------------------------------------------------------


class CompositionError(ThermochemistryError, InputError):
    """A composition is malformed."""


class CompositionBasisError(CompositionError):
    """Two compositions or amounts were combined across different bases.

    A blend whose components mix mole and mass bases has no single meaning, so
    it is refused at construction rather than resolved by guessing
    (``09`` section 4.3).
    """


class CompositionSumError(CompositionError, DomainError):
    """Fractions do not sum to one, beyond the canonicalisation tolerance.

    Refused rather than normalised. Normalising ``{"O2": 0.8, "N2": 0.8}`` into
    a valid composition would silently invent a mixture the caller never
    described. Where relative amounts genuinely are unnormalised, the caller
    says so by supplying *weights* rather than fractions
    (``09`` section 5, ``13`` section 4).
    """


# ---------------------------------------------------------------------------
# propellants
# ---------------------------------------------------------------------------


class PropellantError(ThermochemistryError, InputError):
    """A propellant definition or stream is malformed."""


class PropellantRoleError(PropellantError):
    """A propellant was used in a role it does not declare.

    The concrete case this exists for: building a mixture ratio from two
    streams whose fuel and oxidiser arguments were swapped. A silently
    inverted O/F produces a temperature that is wrong but not absurd, so the
    role is checked rather than inferred from argument order
    (``09`` section 10).
    """


class MixtureRatioError(PropellantError, DomainError):
    """An oxidiser-to-fuel ratio is not a usable positive finite number.

    Zero and infinity are not mixture ratios. ``MR = 0`` means no oxidiser,
    which is a monopropellant or a decomposition problem and has its own
    entry point; it is rejected here rather than computed as a limit
    (``09`` section 6.4).
    """


# ---------------------------------------------------------------------------
# states
# ---------------------------------------------------------------------------


class StateConsistencyError(ThermochemistryError, InputError):
    """A thermodynamic state's fields contradict each other.

    Raised only by constructors that promise internal consistency. The
    *validators* in :mod:`~rocketforge.physics.thermochemistry.validation`
    deliberately do not raise: they report residuals, because their job is to
    measure a discrepancy rather than to refuse one.
    """


# ---------------------------------------------------------------------------
# providers
# ---------------------------------------------------------------------------


class ProviderError(ThermochemistryError):
    """Base class for provider-side failures.

    Kept distinct from :class:`InputError` on purpose. Three outcomes must
    never be conflated (``13`` section 9, and the Phase 5B-0 finding that a
    provider may accept nonsense silently):

    * **malformed input** -- the caller's request is meaningless; an
      ``InputError`` subclass, raised before any provider is consulted;
    * **no solution** -- a well-formed question with no physical answer; a
      ``Solution`` with ``NO_SOLUTION``, not an exception;
    * **provider failure** -- the machinery is missing or broken; this branch.
    """


class ProviderUnavailableError(ProviderError):
    """The requested provider is not installed or cannot initialise.

    Phase 5B-0 established that this is not only an ``ImportError`` case: NASA
    CEA initialises its native library and loads its thermodynamic database at
    *import* time, so a missing data file surfaces as a ``ValueError`` during
    import. Adapters translate both into this class so callers have one thing
    to catch.
    """


class ProviderDomainError(ProviderError, DomainError):
    """A request lies outside the provider's validated range.

    A refusal that names the range, never a silent extrapolation
    (``10`` section 4).
    """


class UnsupportedCapabilityError(ProviderError):
    """A capability the provider does not declare was requested.

    A declared-``False`` capability raises immediately and always; it must
    never partially work, and it must never quietly fall back to a capability
    the provider does have. Silently returning frozen results when equilibrium
    was requested is the worst available failure, because the numbers look
    right and are systematically low (``11`` section 6).
    """

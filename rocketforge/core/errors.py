"""The RocketForge exception hierarchy.

Specified in ``docs/engineering/02_data_model_and_api_contracts.md`` section 5.
Only the classes Phase 4A actually needs are defined; the physics branches
(``DomainError``, ``InvalidGammaError``, ``GeometryError`` and the rest) arrive
with the modules that raise them, so the hierarchy grows one phase at a time
rather than standing here as thirty unused names.

The governing policy, quoted from the specification:

    Raise for invalid input; report for unattainable physics.

A caller who passes a bracket that does not bracket anything made a programming
error and gets an exception. A caller who asks a meaningful engineering
question whose answer is "no such state exists" gets a result object saying so.
A root solver that merely ran out of iterations has *not* failed in that sense:
it returns its best estimate with ``converged=False`` and never raises.

Every class derives from :class:`RocketForgeError`, so ``except
RocketForgeError`` catches everything this package raises deliberately.
"""

from __future__ import annotations

__all__ = [
    "RocketForgeError",
    "InputError",
    "DomainError",
    "AreaRatioError",
    "SubsonicShockError",
    "SubsonicExpansionError",
    "GasModelError",
    "InvalidGammaError",
    "InvalidGasConstantError",
    "MissingGasConstantError",
    "NumericalError",
    "BracketError",
    "NonFiniteEvaluationError",
]


class RocketForgeError(Exception):
    """Base class for every error RocketForge raises deliberately.

    Never raised directly; it exists so that callers can catch the whole
    package with one clause.
    """


class InputError(RocketForgeError):
    """The caller supplied something meaningless.

    Not a physical-domain question and not a numerical failure: an argument
    that cannot be acted on at all, such as a non-finite bracket endpoint, a
    non-positive tolerance, or a maximum iteration count below one.
    """


class DomainError(InputError):
    """An argument lies outside a relation's documented physical domain.

    Raised, never silently corrected: a Mach number of -2 does not become 0 or
    2, and an area ratio of 0.8 does not become 1. The interface may prevent
    such input, but the physics layer is also called from notebooks, scripts
    and future optimisers that have no interface in front of them.
    """


class AreaRatioError(DomainError):
    """An area ratio below unity was supplied to an area-Mach relation.

    A/A* is the ratio of a duct area to the area at which that same flow would
    be sonic, so it cannot be less than one. See
    ``docs/engineering/03_compressible_flow_specification.md`` section 3.4.
    """


class SubsonicShockError(DomainError):
    """A shock relation was asked for a Mach number at or below 1.

    The normal-shock relations are algebraically defined for subsonic upstream
    flow, but the states they describe there decrease entropy, which the second
    law forbids. Refusing is the only honest answer: the equations do not
    complain, so nothing but this check stands between a caller and a
    physically impossible result.
    """


class SubsonicExpansionError(DomainError):
    """A Prandtl-Meyer relation was asked for a Mach number below 1.

    Specified in ``02`` section 6. The Prandtl-Meyer function contains
    ``sqrt(M^2 - 1)`` twice, so below Mach 1 it is not merely unphysical but
    complex-valued: an expansion fan is a supersonic phenomenon and there is
    nothing subsonic for the relation to describe. Kept distinct from
    :class:`SubsonicShockError` because the two say different things about
    what the caller was trying to do.
    """


class GeometryError(InputError):
    """A supplied duct geometry cannot carry the requested solution.

    Raised for a non-monotone abscissa, a non-positive area, a duct with no
    interior throat, or more than one minimum-area station. It is an input
    error rather than a numerical one: nothing about the arithmetic failed,
    the passage described simply is not the passage the solver models. A
    quasi-1D C-D solver with two throats has two candidate sonic points and no
    principled way to choose, so it refuses rather than picking one.
    """


class GasModelError(InputError):
    """The gas model itself is inadmissible."""


class InvalidGammaError(GasModelError):
    """The ratio of specific heats is outside the model's hard domain.

    ``gamma > 1`` is required mathematically; RocketForge narrows that to
    ``1.001 <= gamma <= 3.0`` because below roughly 1.0001 the exponents
    ``gamma/(gamma-1)`` reach 10**4 and overflow float64 for modest Mach
    numbers, producing infinities where the physics is meaningless anyway
    (``03`` section 2.2).
    """


class InvalidGasConstantError(GasModelError):
    """The specific gas constant is not a positive finite number."""


class MissingGasConstantError(GasModelError):
    """A dimensional quantity was requested from a gas with no R.

    The dimensionless half of the compressible module needs only gamma, so a
    gas may legitimately be constructed without a gas constant. Asking such a
    gas for cp, cv or a speed of sound is a programming error, and inventing a
    plausible R would be worse than refusing.
    """


class InconsistentStateError(InputError):
    """A dimensional state was supplied whose p, T and rho disagree.

    For a perfect gas the three are not independent. Accepting a state that
    violates rho = p/(R T) would let a single wrong number propagate through
    every derived quantity while each of them still looked plausible, so the
    constructor refuses it at the point where the caller can still see what
    they typed.
    """


class NumericalError(RocketForgeError):
    """A numerical procedure could not be carried out as requested."""


class BracketError(NumericalError):
    """The supplied interval does not bracket a root.

    Raised when ``f(a)`` and ``f(b)`` share a sign and neither endpoint is
    itself a root. The solver does not widen the interval, search outside it,
    or invent a point: choosing a physically meaningful bracket is the caller's
    responsibility, and in RocketForge that responsibility belongs to the
    physics module which knows the monotone branch it is inverting.
    """


class NonFiniteEvaluationError(NumericalError):
    """The objective function returned NaN or an infinity.

    Iteration stops immediately rather than continuing with a value that makes
    every subsequent comparison meaningless -- NaN compares false against
    everything, so an unchecked NaN silently turns a bracketing method into a
    random walk.

    Note: this class is an addition to the hierarchy printed in Phase 3
    (``02`` section 5), which named ``BracketError`` and ``ConvergenceError``
    under ``NumericalError`` but did not cover a non-finite evaluation. It is
    recorded as ADDITION-4A-01 in
    ``docs/engineering/implementation/PHASE_4A_ROOT_FOUNDATION.md``.
    """

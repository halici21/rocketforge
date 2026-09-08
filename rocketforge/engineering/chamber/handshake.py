"""Reducing a chemically computed chamber state to a single-gamma perfect gas.

This is the adapter `12` section 8 specifies, at the location it specifies. It
is the **only** place in RocketForge where a :class:`ChamberGas` becomes a
:class:`PerfectGas`, and it exists so that the reduction is a visible,
refusable, recorded engineering decision rather than an attribute access.

What crosses::

    ChamberGas.temperature   T0  [K]        --->  stagnation temperature
    ChamberGas.gas_constant  R   [J/(kg K)] --->  PerfectGas.gas_constant
    <chosen gamma>           (section 5)    --->  PerfectGas.gamma

What deliberately does **not** cross: composition and mean molar mass. The
compressible module has no field for them and must not acquire one. They stay
on the ``ChamberGas``, are reported beside the result, and are what a future
equilibrium-expansion path consumes instead (`12` section 3).

**Eight preconditions, every one a refusal with a diagnostic.** They are `12`
section 4 verbatim, and four of them carry real weight rather than hygiene:

* **P1** the state must say which chemistry mode produced its gamma;
* **P6/P7** condensed material refuses the single-phase handshake, and
  "the provider did not say" refuses it too;
* **P8** the gamma strategy is chosen by the caller. There is no default, and
  this module will not invent one.

A single-gamma perfect gas cannot represent a reacting mixture whose gamma
varies along the expansion. Which gamma is kept is an engineering choice with a
documented bias, so the choice is named, recorded and reported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.core.tolerances import DEFAULT_TOLERANCES
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.thermochemistry import (
    ChamberGas,
    GammaStrategy,
)

__all__ = [
    "ChamberGammaBasis",
    "SINGLE_PHASE_CONDENSED_LIMIT",
    "GAS_CONSTANT_IDENTITY_TOLERANCE",
    "ReducedChamberGas",
    "reduce_chamber_gas",
    "gamma_for_strategy",
]

#: The condensed mass fraction at or above which the single-phase handshake is
#: **refused**.
#:
#: Declared here, in the engineering layer, because `11` section 7.3 requires a
#: declared constant, states that it is *not zero*, and points at `13` section 4
#: for the value -- where `13` section 4 turns out to be a tolerance-policy
#: table that never fixes it. So Phase 5E fixes it, with the justification `11`
#: section 7.3 itself supplies:
#:
#:     "trace condensed fractions at the 1e-6 level are numerical noise in a
#:      provider's species list, not a two-phase flow"
#:
#: A condensed phase is not a perfect gas and no choice of gamma makes it one:
#: condensed mass carries momentum but does no pressure work, particles lag the
#: gas in temperature and velocity, and the condensate may itself change phase
#: in the nozzle. None of that is recoverable from a mixture gamma, which is why
#: this is a refusal and not a correction.
#:
#: **This is not the Phase 5D presentation threshold.** It happens to carry the
#: same number because both were argued from the same measurement -- provider
#: species lists carry condensed candidates around 1e-8 -- but they are separate
#: constants in separate layers with separate owners, and an architecture test
#: asserts this package never imports the interface one. One decides whether the
#: physics may run; the other decides which sentence a label says.
SINGLE_PHASE_CONDENSED_LIMIT = 1.0e-6

#: Relative tolerance for the ``R == Ru / M_bar`` identity of precondition P4.
#:
#: 1e-8, from `13` section 4: providers may use a pre-2019 universal gas
#: constant, and NASA CEA does -- 8314.51 against CODATA's 8314.46261815324, a
#: 5.7e-06 difference. RocketForge's own adapter derives R from the CODATA
#: value so the identity closes exactly, but a provider that supplies both
#: independently would not, and this check exists to catch an adapter that
#: scaled one and not the other rather than to police constants vintage.
GAS_CONSTANT_IDENTITY_TOLERANCE = 1.0e-8


class ChamberGammaBasis(StrEnum):
    """*Which* chamber gamma. The second half of the reduction decision.

    ``GammaStrategy`` says **where** along the expansion the single exponent is
    taken from. It does not say which exponent, and a chamber state carries
    two that are not interchangeable:

    ``EQUILIBRIUM``
        gamma_s = -(d ln p / d ln v)_s, the isentropic exponent of an expansion
        whose composition **shifts** to stay in equilibrium. Held constant, it
        reproduces a shifting-equilibrium expansion to first order -- which is
        what it was defined for.

    ``FROZEN``
        cp/cv at **fixed** composition. This is the exponent of a genuinely
        constant-composition isentropic process, which is the process this
        ideal model actually computes.

    Measured on the canonical LOX/CH4 chamber: 1.1326 against 1.1956, 5.6 %
    apart, and worth 2 % of c* and 11 % of Isp. There is no default, for the
    same reason ``GammaStrategy`` has none -- and because a reduction that
    picked one silently would produce a number matching neither reference.

    Choosing ``FROZEN`` makes the model like-for-like with a provider's
    frozen-at-chamber expansion. Choosing ``EQUILIBRIUM`` makes it an
    approximation of the shifting-equilibrium expansion, close at the throat
    and drifting downstream. Both are legitimate; neither is correct; each is
    recorded on the result.
    """

    EQUILIBRIUM = "equilibrium"
    FROZEN = "frozen"


@dataclass(frozen=True, slots=True)
class ReducedChamberGas:
    """A chamber state reduced to the constant-property gas a nozzle model uses.

    Immutable, and it carries the decision as well as the result: the strategy
    that was chosen, the gamma that choice produced, and where that gamma came
    from. A reduced gas that cannot say which reduction made it is a number
    nobody can interpret.

    Attributes:
        gas: The single-gamma :class:`PerfectGas`. This is what the frozen
            compressible module receives.
        stagnation_temperature: T0 [K], the chamber stagnation temperature.
            ``ChamberGas.temperature`` is already T0 -- it comes out of a
            constant-enthalpy problem solved from the reactants' stagnation
            enthalpy -- so no conversion happens here.
        strategy: The :class:`GammaStrategy` the caller chose. Never defaulted.
        basis: Which of the chamber's two gammas that strategy read. Never
            defaulted either: they differ by 5.6 % on a real chamber.
        gamma: The value that strategy produced, repeated from ``gas`` so a
            report does not have to reach through it.
        gamma_source: Which field of the chamber state the gamma was read from,
            in words. The audit trail for "why is gamma 1.1326?".
        gas_constant: R [J/(kg K)], repeated for the same reason.
        chamber_pressure: p_c [Pa] from the originating request, when the state
            recorded one. Optional because a ``ChamberGas`` may be constructed
            without a request in a test fixture.
        condensed_mass_fraction: What was measured, carried through even though
            it passed: a result should be able to say the check ran and what it
            saw.
        source: The ``ChamberGas`` this came from, so the whole chemistry
            provenance stays reachable without being copied.
    """

    gas: PerfectGas
    stagnation_temperature: float
    strategy: GammaStrategy
    basis: ChamberGammaBasis
    gamma: float
    gamma_source: str
    gas_constant: float
    chamber_pressure: float | None = None
    condensed_mass_fraction: float | None = None
    source: ChamberGas | None = field(default=None, repr=False, compare=False)

    @property
    def assumptions(self) -> tuple[str, ...]:
        """What accepting this reduction commits a caller to."""
        return (
            "Constant-property gas: gamma and R are held fixed at the reduced "
            "values for the whole expansion.",
            f"Gamma strategy: {self.strategy.value}, {self.basis.value} basis "
            f"— {self.gamma_source}.",
            "Single phase: condensed products are refused, not averaged in.",
            "The composition and mean molar mass did not cross into the gas "
            "model; they remain on the chamber state.",
        )


def gamma_for_strategy(state: ChamberGas, strategy: GammaStrategy,
                       basis: ChamberGammaBasis) -> tuple[float | None, str]:
    """The gamma a strategy and basis select, and where it came from.

    Returns ``(None, reason)`` when the chamber state alone cannot supply it.
    Two of the five strategies genuinely cannot be evaluated here:

    * ``EXIT`` and ``CHAMBER_EXIT_MEAN`` need an exit condition, which does not
      exist until an expansion has been solved -- and the expansion is what the
      reduced gas is *for*;
    * ``EFFECTIVE_ISENTROPIC`` is fitted over a provider expansion (`12`
      section 5), which Phase 5E does not compute.

    They are refused by name rather than quietly falling back to the chamber
    value, because a strategy the user chose and did not get is worse than one
    they could not have.
    """
    if strategy in (GammaStrategy.CHAMBER, GammaStrategy.THROAT):
        # The chamber and the throat are the same chemical state under a
        # constant-composition model: composition does not shift between them,
        # and the exponent is a property of that composition. Stated rather
        # than assumed, and it is the assumption the reduction makes elsewhere.
        where = ("at the chamber state" if strategy is GammaStrategy.CHAMBER
                 else "at the throat, which shares the chamber's chemical "
                      "state under this model's constant-composition assumption")
        if basis is ChamberGammaBasis.FROZEN:
            gamma = state.gamma_frozen
            if gamma is None:
                return None, (
                    "this provider did not supply a frozen specific-heat ratio, "
                    "so the frozen basis cannot be honoured")
            return gamma, (
                f"ChamberGas.gamma_frozen = cp/cv at fixed composition, {where}")
        gamma = state.gamma_equilibrium
        if gamma is None:
            gamma = state.gamma
        return gamma, (
            f"ChamberGas.gamma_equilibrium, the isentropic exponent "
            f"-(d ln p/d ln v)_s of a shifting-equilibrium expansion, {where}")
    if strategy is GammaStrategy.EXIT:
        return None, (
            "the exit gamma needs an exit condition, and the expansion has not "
            "been solved yet — the reduced gas is what solves it")
    if strategy is GammaStrategy.CHAMBER_EXIT_MEAN:
        return None, (
            "the chamber/exit mean needs an exit gamma, which needs an "
            "expansion that has not been solved yet")
    if strategy is GammaStrategy.EFFECTIVE_ISENTROPIC:
        return None, (
            "the effective isentropic exponent is fitted over a provider "
            "expansion, which this phase does not compute")
    return None, f"unrecognised gamma strategy {strategy!r}"


def reduce_chamber_gas(
    state: ChamberGas,
    strategy: GammaStrategy,
    basis: ChamberGammaBasis,
    *,
    chamber_pressure: float | None = None,
    condensed_limit: float = SINGLE_PHASE_CONDENSED_LIMIT,
) -> Solution[ReducedChamberGas]:
    """Reduce a chamber state to a single-gamma perfect gas, or refuse.

    Returns a ``Solution``. A refusal carries ``NO_SOLUTION`` and a diagnostic
    naming the precondition that failed and the number that failed it -- never a
    corrected value, and never a fallback gamma.

    Args:
        state: The accepted chamber equilibrium state.
        strategy: Where along the expansion the exponent is taken from.
            Mandatory; there is no default.
        basis: Which of the chamber's two gammas that means. Mandatory for the
            same reason, and for a sharper one: they differ by 5.6 % on a real
            chamber and pick out different reference models.
        chamber_pressure: p_c [Pa]. Taken from ``state.request`` or
            ``state.pressure`` when not supplied.
        condensed_limit: The single-phase refusal threshold. Exposed so a test
            can drive both sides of it, not so a caller can widen it.
    """
    diagnostics: list[Diagnostic] = []

    if not isinstance(state, ChamberGas):
        raise TypeError(
            f"reduce_chamber_gas needs a ChamberGas, got {type(state).__name__}")
    if not isinstance(strategy, GammaStrategy):
        # P8, at the type level: a string here would let a typo pick a
        # strategy nobody chose.
        raise TypeError(
            "the gamma strategy must be a GammaStrategy member. There is no "
            "default: each strategy is a stated approximation with a stated "
            f"bias, and {strategy!r} is not one of them.")
    if not isinstance(basis, ChamberGammaBasis):
        raise TypeError(
            "the gamma basis must be a ChamberGammaBasis member. There is no "
            "default: a chamber carries an equilibrium and a frozen exponent "
            "that differ by percent-level amounts, and picking one silently "
            f"would produce a number matching neither reference. Got {basis!r}.")

    # -- P1: the state must say which chemistry produced its gamma ---------
    if not state.mode_is_recorded:
        return _refuse(
            "CHAMBER_MODE_NOT_RECORDED",
            "This chamber state does not record the chemistry mode behind its "
            "gamma, so which gamma it carries is unknown and the single-gamma "
            "reduction cannot be interpreted.",
            field="provenance.chemistry_mode")

    # -- P5, P2, P3: the numbers themselves ---------------------------------
    for name, value in (("chamber stagnation temperature", state.temperature),
                        ("specific gas constant", state.gas_constant)):
        if not math.isfinite(value) or value <= 0.0:
            return _refuse(
                "CHAMBER_STATE_NOT_PHYSICAL",
                f"The chamber {name} is {value!r}, which is not a usable "
                "value for a perfect-gas reduction.",
                field=name)
    if not math.isfinite(state.gamma) or state.gamma <= 1.0:
        return _refuse(
            "CHAMBER_STATE_NOT_PHYSICAL",
            f"The chamber gamma is {state.gamma!r}. A ratio of specific heats "
            "at or below 1 is not physical for a gas.",
            field="gamma")

    # The frozen perfect-gas model declares its own domain, and it is narrower
    # than "above 1": below 1.001 the exponent gamma/(gamma-1) exceeds 1000 and
    # overflows double precision at modest Mach numbers. Checked here so the
    # coupling refuses with a diagnostic rather than letting an exception
    # surface from three layers down.
    gamma_min, gamma_max = DEFAULT_TOLERANCES.gamma_min, DEFAULT_TOLERANCES.gamma_max
    if not gamma_min <= state.gamma <= gamma_max:
        return _refuse(
            "CHAMBER_GAMMA_OUTSIDE_GAS_MODEL",
            f"The chamber gamma is {state.gamma!r}, outside the "
            f"[{gamma_min}, {gamma_max}] range the frozen perfect-gas model "
            "declares. The reduction is refused rather than handing the gas "
            "model a value it does not accept.",
            field="gamma",
            detail={"gamma": float(state.gamma), "minimum": float(gamma_min),
                    "maximum": float(gamma_max)})

    # -- P4: R == Ru / M_bar ------------------------------------------------
    expected_r = UNIVERSAL_GAS_CONSTANT / state.molar_mass
    residual = abs(state.gas_constant - expected_r) / expected_r
    if residual > GAS_CONSTANT_IDENTITY_TOLERANCE:
        return _refuse(
            "CHAMBER_GAS_CONSTANT_INCONSISTENT",
            f"R = {state.gas_constant!r} J/(kg K) does not match Ru / M_bar = "
            f"{expected_r!r} for M_bar = {state.molar_mass!r} kg/mol: relative "
            f"residual {residual:.3e} exceeds "
            f"{GAS_CONSTANT_IDENTITY_TOLERANCE:.0e}. One of the two was scaled "
            "and the other was not.",
            field="gas_constant",
            detail={"residual": residual,
                    "tolerance": GAS_CONSTANT_IDENTITY_TOLERANCE})

    # -- P7 then P6: condensed material ------------------------------------
    condensed = state.condensed_mass_fraction
    if condensed is None:
        return _refuse(
            "CONDENSED_FRACTION_UNKNOWN",
            "The provider did not report a condensed mass fraction. Unknown is "
            "not the same as none, so the single-phase perfect-gas handshake "
            "is refused rather than assuming a gas-only mixture.",
            field="condensed_mass_fraction")
    if condensed >= condensed_limit:
        return _refuse(
            "CONDENSED_PHASE_PRESENT",
            f"The chamber mixture carries a condensed mass fraction of "
            f"{condensed:.6g}, at or above the {condensed_limit:.0e} "
            "single-phase limit. A two-phase flow is not a perfect gas and no "
            "choice of gamma makes it one: the condensed mass carries momentum "
            "but does no pressure work, and particles lag the gas in "
            "temperature and velocity. The reduction is refused rather than "
            "averaging the condensate into a gas.",
            field="condensed_mass_fraction",
            detail={"condensed_mass_fraction": float(condensed),
                    "limit": float(condensed_limit)})
    if condensed > 0.0:
        diagnostics.append(Diagnostic(
            code="CONDENSED_TRACE_ACCEPTED", severity=Severity.INFO,
            message=(f"A condensed mass fraction of {condensed:.3e} is present "
                     f"and below the {condensed_limit:.0e} single-phase limit; "
                     "the reduction treats the mixture as a gas."),
            field="condensed_mass_fraction",
            detail={"condensed_mass_fraction": float(condensed),
                    "limit": float(condensed_limit)}))

    # -- P8: the chosen strategy must be evaluable here ---------------------
    gamma, gamma_source = gamma_for_strategy(state, strategy, basis)
    if gamma is None:
        return _refuse(
            "GAMMA_STRATEGY_UNAVAILABLE",
            f"The {strategy.value!r} strategy on the {basis.value!r} basis "
            f"cannot be evaluated from this chamber state: {gamma_source}. "
            "Choose a reduction this model can honour, rather than receiving "
            "one you did not pick.",
            field="gamma_strategy")

    pressure = chamber_pressure
    if pressure is None:
        request = state.request
        pressure = (float(request.chamber_pressure) if request is not None
                    else state.pressure)

    reduced = ReducedChamberGas(
        gas=PerfectGas(gamma=float(gamma), gas_constant=float(state.gas_constant)),
        stagnation_temperature=float(state.temperature),
        strategy=strategy,
        basis=basis,
        gamma=float(gamma),
        gamma_source=gamma_source,
        gas_constant=float(state.gas_constant),
        chamber_pressure=None if pressure is None else float(pressure),
        condensed_mass_fraction=float(condensed),
        source=state,
    )
    status = Status.OK_WITH_WARNINGS if any(
        d.severity is Severity.WARNING for d in diagnostics) else Status.OK
    return Solution(value=reduced, status=status, diagnostics=tuple(diagnostics))


def _refuse(code: str, message: str, *, field: str,
            detail: dict | None = None) -> Solution[ReducedChamberGas]:
    """A refusal carries no value and names the precondition that failed."""
    return Solution(
        value=None, status=Status.NO_SOLUTION,
        diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                message=message, field=field, detail=detail),))

"""Chamber equilibrium, prepared for display. Qt-free.

The whole scientific chain of the Thermochemistry workspace lives here:

    ChamberCase                     what the user asked for, as data
        -> ChamberEquilibriumRequest    the provider-independent question
        -> ThermochemistryProvider      NASA CEA, behind the gateway
        -> Solution[ChamberGas]         the answer, with diagnostics
        -> ChamberOutcome               an immutable display snapshot

**A ``ChamberOutcome`` is a snapshot, not a view of live state.** It carries the
case that produced it, so a result panel can say what its numbers are for even
after the input form has moved on. Nothing above this module reads the input
fields to label a result.

No equation is implemented here. Mole-to-mass conversion is
``Composition.to_basis``; the mean molar mass, the gas constant and the
condensed fraction are the provider's or the domain's. This module chooses
labels, groups, units and order -- which is presentation, and is the one thing
it is allowed to own.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from dataclasses import field as _dataclass_field
from typing import Any

from .thermochemistry_provider import (
    CHEMISTRY_MODE_LABEL,
    CONSTRAINT_LABEL,
    MODEL_SUMMARY,
    PROVIDER_LABEL,
    availability,
    chamber_provider,
    propellant_named,
)

__all__ = [
    "ChamberCase",
    "ChamberOutcome",
    "ResultRow",
    "SpeciesRow",
    "DiagnosticRow",
    "DEFAULT_CASE",
    "OUTCOME_EMPTY",
    "OUTCOME_OK",
    "OUTCOME_WARNING",
    "OUTCOME_NO_SOLUTION",
    "OUTCOME_UNAVAILABLE",
    "OUTCOME_INVALID_INPUT",
    "OUTCOME_PROVIDER_ERROR",
    "solve_case",
    "result_rows",
    "species_rows",
    "diagnostic_rows",
    "provenance_summary",
    "provenance_details",
    "condensed_summary",
    "CONDENSED_REPORTING_THRESHOLD",
    "CONDENSED_UNKNOWN",
    "CONDENSED_NONE_REPORTED",
    "CONDENSED_BELOW_THRESHOLD",
    "CONDENSED_PRESENT",
    "case_headline",
    "MODEL_SUMMARY",
    "PROVIDER_LABEL",
]

# --- outcome kinds ---------------------------------------------------------
#
# Seven, not one. Phase 5D §25 forbids collapsing everything into "calculation
# failed", and the distinctions are real: a provider that is not installed, a
# request the domain refused, a request outside the provider's validated range,
# a solve that did not converge, and a solve that converged but failed
# RocketForge's own checks are five different situations with five different
# remedies.

OUTCOME_EMPTY = "empty"
OUTCOME_OK = "ok"
OUTCOME_WARNING = "warning"
OUTCOME_NO_SOLUTION = "no_solution"
OUTCOME_UNAVAILABLE = "unavailable"
OUTCOME_INVALID_INPUT = "invalid_input"
OUTCOME_PROVIDER_ERROR = "provider_error"

_STATUS_LABELS = {
    OUTCOME_EMPTY: "No result yet",
    OUTCOME_OK: "Solved",
    OUTCOME_WARNING: "Solved with warnings",
    OUTCOME_NO_SOLUTION: "No solution",
    OUTCOME_UNAVAILABLE: "Provider unavailable",
    OUTCOME_INVALID_INPUT: "Input refused",
    OUTCOME_PROVIDER_ERROR: "Provider refused",
}

_STATUS_TONES = {
    OUTCOME_EMPTY: "neutral",
    OUTCOME_OK: "success",
    OUTCOME_WARNING: "warning",
    OUTCOME_NO_SOLUTION: "error",
    OUTCOME_UNAVAILABLE: "neutral",
    OUTCOME_INVALID_INPUT: "warning",
    OUTCOME_PROVIDER_ERROR: "warning",
}


# ---------------------------------------------------------------------------
# the case
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChamberCase:
    """One operating point, in SI, independent of any provider.

    Reactants are named by their catalogue key rather than held as domain
    objects so that a case is trivially comparable, storable and printable, and
    so nothing above the service layer ever holds a ``PropellantDefinition``.

    Attributes:
        oxidiser_fuel_ratio: O/F **by mass** -- oxidiser mass divided by fuel
            mass. The orientation is in the field name because getting it
            backwards produces a wrong answer that does not look wrong.
        chamber_pressure: Pa.
        fuel_temperature / oxidiser_temperature: K, the **actual** stream
            temperatures, not the definitions' reference values.
    """

    fuel: str
    oxidiser: str
    oxidiser_fuel_ratio: float
    chamber_pressure: float
    fuel_temperature: float
    oxidiser_temperature: float

    def replace(self, **changes: Any) -> "ChamberCase":
        from dataclasses import replace as _replace

        return _replace(self, **changes)


#: The validated demonstration case, from Phase 5C. Reactant temperatures are
#: the production definitions' own reference conditions -- normal boiling
#: points, not a hidden 298 K, which for a cryogenic propellant would be worth
#: tens of kelvin of chamber temperature (Phase 5D §191).
DEFAULT_CASE = ChamberCase(
    fuel="LCH4",
    oxidiser="LOX",
    oxidiser_fuel_ratio=3.4,
    chamber_pressure=10.0e6,
    fuel_temperature=111.643,
    oxidiser_temperature=90.17,
)


# ---------------------------------------------------------------------------
# the outcome
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChamberOutcome:
    """One completed calculation, or one completed refusal.

    Immutable and self-describing. ``case`` is the question this answers, so a
    result header never has to read the live input form -- which is how a
    result gets relabelled with conditions that did not produce it.
    """

    kind: str
    case: ChamberCase | None = None
    state: Any = None
    diagnostics: tuple[Any, ...] = ()
    provenance: Any = None
    message: str = ""
    field: str = ""

    @property
    def ok(self) -> bool:
        """Whether a state is present. True for OK and OK_WITH_WARNINGS."""
        return self.state is not None

    @property
    def status_label(self) -> str:
        return _STATUS_LABELS.get(self.kind, "Unknown")

    @property
    def status_tone(self) -> str:
        return _STATUS_TONES.get(self.kind, "neutral")

    @property
    def has_warnings(self) -> bool:
        return self.kind == OUTCOME_WARNING


EMPTY_OUTCOME = ChamberOutcome(kind=OUTCOME_EMPTY)


# ---------------------------------------------------------------------------
# solving
# ---------------------------------------------------------------------------


def build_request(case: ChamberCase) -> Any:
    """Turn a case into a validated ``ChamberEquilibriumRequest``.

    Raises the domain's own errors for a malformed case. Separated from
    :func:`solve_case` so that request construction can be tested with no
    provider present at all.
    """
    from rocketforge.physics.thermochemistry import (
        ChamberEquilibriumRequest,
        MixtureRatio,
        PropellantStream,
    )

    fuel = propellant_named(case.fuel)
    oxidiser = propellant_named(case.oxidiser)
    if fuel is None or fuel.definition is None:
        raise LookupError(f"no propellant definition named {case.fuel!r}")
    if oxidiser is None or oxidiser.definition is None:
        raise LookupError(f"no propellant definition named {case.oxidiser!r}")

    return ChamberEquilibriumRequest(
        fuel=PropellantStream(fuel.definition, case.fuel_temperature,
                              phase=fuel.definition.reference_phase),
        oxidiser=PropellantStream(oxidiser.definition, case.oxidiser_temperature,
                                  phase=oxidiser.definition.reference_phase),
        oxidiser_fuel_ratio=MixtureRatio(case.oxidiser_fuel_ratio),
        chamber_pressure=case.chamber_pressure,
    )


def solve_case(case: ChamberCase) -> ChamberOutcome:
    """Run one chamber equilibrium and package the answer for display.

    Never raises. Every failure mode the chain can produce is turned into an
    outcome that names what happened:

    * no provider installed              -> ``unavailable``
    * the domain refused the request     -> ``invalid_input``
    * outside the provider's range, or
      unmappable                         -> ``provider_error``
    * CEA did not converge, or converged
      and failed RocketForge's checks    -> ``no_solution``
    * solved                             -> ``ok`` / ``warning``

    The last two share a status only because the *provider* gives them one; the
    diagnostics say which check failed, so "converged but rejected" never
    reaches a user as "chemistry failed".
    """
    from rocketforge.core.errors import DomainError, InputError
    from rocketforge.core.result import Status
    from rocketforge.physics.thermochemistry import ProviderError

    provider = chamber_provider()
    if provider is None:
        state = availability()
        return ChamberOutcome(
            kind=OUTCOME_UNAVAILABLE, case=case,
            message=state.detail or "No thermochemistry provider is installed "
                                    "in this environment.")

    try:
        request = build_request(case)
    except LookupError as exc:
        return ChamberOutcome(kind=OUTCOME_INVALID_INPUT, case=case,
                              message=str(exc), field="propellant")
    except InputError as exc:
        return ChamberOutcome(kind=OUTCOME_INVALID_INPUT, case=case,
                              message=str(exc), field=_field_of(exc))

    try:
        solution = provider.solve_chamber(request)
    except ProviderError as exc:
        return ChamberOutcome(kind=OUTCOME_PROVIDER_ERROR, case=case,
                              message=str(exc), field=_field_of(exc))
    except DomainError as exc:
        return ChamberOutcome(kind=OUTCOME_PROVIDER_ERROR, case=case,
                              message=str(exc), field=_field_of(exc))
    except InputError as exc:
        return ChamberOutcome(kind=OUTCOME_INVALID_INPUT, case=case,
                              message=str(exc), field=_field_of(exc))

    diagnostics = tuple(solution.diagnostics)
    provenance = solution.provenance[0] if solution.provenance else None

    if solution.value is None:
        return ChamberOutcome(
            kind=OUTCOME_NO_SOLUTION, case=case, diagnostics=diagnostics,
            provenance=provenance,
            message=_no_solution_message(diagnostics))

    kind = OUTCOME_WARNING if solution.status is Status.OK_WITH_WARNINGS else OUTCOME_OK
    return ChamberOutcome(
        kind=kind, case=case, state=solution.value, diagnostics=diagnostics,
        provenance=solution.value.provenance or provenance)


def _field_of(exc: BaseException) -> str:
    return str(getattr(exc, "field", "") or "")


def _no_solution_message(diagnostics: tuple[Any, ...]) -> str:
    """Why no state came back, taken from the diagnostics rather than guessed.

    A CEA result that converged and then failed element conservation is a
    scientifically different event from a CEA result that did not converge, and
    this is where that distinction survives into the interface.
    """
    from rocketforge.core.result import Severity

    for diagnostic in diagnostics:
        if diagnostic.severity is Severity.ERROR:
            if diagnostic.code == "PROVIDER_NOT_CONVERGED":
                return ("The provider did not converge for this operating "
                        "point, so no chamber state is reported.")
            return ("The provider converged, but RocketForge rejected the "
                    "result: " + diagnostic.message)
    return "No chamber state was produced for this operating point."


# ---------------------------------------------------------------------------
# primary and advanced readouts
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResultRow:
    """One displayed quantity, still numeric.

    ``value`` is the stored SI number, or ``None`` for a quantity this result
    genuinely does not carry. Formatting happens on the way to the screen and
    never replaces the stored value (Phase 5D §31, §105).
    """

    key: str
    label: str
    unit: str
    value: float | None
    group: str
    qualifier: str = ""
    emphasis: bool = False
    help: str = ""

    @property
    def available(self) -> bool:
        return self.value is not None and math.isfinite(self.value)


#: Group names, in display order.
GROUP_PRIMARY = "Chamber state"
GROUP_MIXTURE = "Mixture"
GROUP_ADVANCED = "Advanced"

_HELP = {
    "temperature": (
        "Ideal adiabatic chamber equilibrium temperature — the predicted "
        "stagnation temperature of the combustion products. It is not a wall "
        "temperature and not a finite-rate combustion prediction."),
    "molar_mass": (
        "Composition-weighted average molar mass of the chamber mixture."),
    "gas_constant": (
        "Specific gas constant of the mixture, R = Ru / M̄, derived from "
        "RocketForge's CODATA universal gas constant."),
    "cp": (
        "Specific heat at constant pressure at frozen composition. This is the "
        "pair that satisfies cp − cv = R; the equilibrium heat capacity is a "
        "different quantity and is listed separately under Advanced."),
    "cv": (
        "Specific heat at constant volume at frozen composition, the partner "
        "of the frozen cp above."),
    "gamma": (
        "Equilibrium isentropic exponent γs = −(∂ln p / ∂ln v)s, as reported "
        "by the provider. It is not cp/cv, and it is not constant through a "
        "nozzle."),
    "gamma_frozen": (
        "Ratio of specific heats at frozen composition, cp_fr / cv_fr. "
        "Measurably different from the isentropic exponent above — Phase 5B-0 "
        "measured 5.7 % on a real LOX/CH₄ chamber."),
    "density": "Mixture density at the chamber stagnation condition.",
    "pressure": "The chamber pressure the equilibrium was solved at.",
    "enthalpy": "Specific enthalpy of the products on the provider's datum.",
    "entropy": "Specific entropy of the products on the provider's datum.",
    "condensed": (
        "Mass fraction of the mixture present as liquid or solid, computed "
        "from the returned composition — not from the provider's count of "
        "candidate condensed species. This is the exact value; the "
        "Composition tab reports it against a display reporting threshold."),
    "of": "Oxidiser mass divided by fuel mass.",
}


def result_rows(outcome: ChamberOutcome) -> tuple[ResultRow, ...]:
    """The chamber state as labelled, grouped, still-numeric rows.

    Empty for any outcome without a state: a refusal shows no numbers.

    **No performance quantity appears here.** There is no c\\*, no Cf, no Isp
    and no thrust, because RocketForge does not own them yet and CEA's native
    values are not RocketForge's answer (Phase 5D §11, §206).
    """
    state = outcome.state
    if state is None:
        return ()

    rows: list[ResultRow] = [
        ResultRow("temperature", "Chamber temperature  T₀", "K",
                  state.temperature, GROUP_PRIMARY,
                  qualifier="Adiabatic · HP equilibrium", emphasis=True,
                  help=_HELP["temperature"]),
        ResultRow("pressure", "Chamber pressure  p_c", "Pa",
                  state.pressure, GROUP_PRIMARY, help=_HELP["pressure"]),
        ResultRow("density", "Density  ρ", "kg/m³",
                  state.density, GROUP_PRIMARY, help=_HELP["density"]),
        ResultRow("molar_mass", "Mean molar mass  M̄", "kg/mol",
                  state.molar_mass, GROUP_PRIMARY, emphasis=True,
                  help=_HELP["molar_mass"]),
        ResultRow("gas_constant", "Specific gas constant  R", "J/(kg·K)",
                  state.gas_constant, GROUP_PRIMARY, help=_HELP["gas_constant"]),
        ResultRow("cp", "Specific heat  c_p", "J/(kg·K)",
                  state.cp, GROUP_PRIMARY, qualifier="frozen", help=_HELP["cp"]),
        ResultRow("cv", "Specific heat  c_v", "J/(kg·K)",
                  state.cv, GROUP_PRIMARY, qualifier="frozen", help=_HELP["cv"]),
        ResultRow("gamma", "Isentropic exponent  γ_s", "",
                  state.gamma, GROUP_PRIMARY, qualifier="equilibrium",
                  emphasis=True, help=_HELP["gamma"]),

        ResultRow("gamma_frozen", "Frozen specific-heat ratio  γ_fr", "",
                  state.gamma_frozen, GROUP_ADVANCED, qualifier="c_p,fr / c_v,fr",
                  help=_HELP["gamma_frozen"]),
        ResultRow("cp_equilibrium", "Equilibrium specific heat  c_p,eq",
                  "J/(kg·K)", state.cp_equilibrium, GROUP_ADVANCED,
                  qualifier="does not satisfy c_p − c_v = R",
                  help="The equilibrium heat capacity, which includes the "
                       "energy absorbed by shifting composition. It is not the "
                       "partner of the c_v above and the two must not be mixed."),
        ResultRow("enthalpy", "Specific enthalpy  h", "J/kg",
                  state.enthalpy, GROUP_ADVANCED, help=_HELP["enthalpy"]),
        ResultRow("entropy", "Specific entropy  s", "J/(kg·K)",
                  state.entropy, GROUP_ADVANCED, help=_HELP["entropy"]),
        ResultRow("speed_of_sound", "Speed of sound  a", "m/s",
                  state.speed_of_sound, GROUP_ADVANCED,
                  help="Provider-supplied; nothing in RocketForge computes it "
                       "from this state."),
        ResultRow("condensed_mass_fraction", "Condensed mass fraction", "",
                  state.condensed_mass_fraction, GROUP_ADVANCED,
                  help=_HELP["condensed"]),
    ]
    return tuple(rows)


# ---------------------------------------------------------------------------
# composition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SpeciesRow:
    """One product species, on both bases, with its phase.

    Both fractions are carried on every row so that changing the displayed
    basis is a presentation switch and never a recalculation, and so that a
    display filter can be applied to one basis without the other going stale.
    """

    name: str
    phase: str
    mole_fraction: float
    mass_fraction: float
    display_name: str = ""

    @property
    def is_condensed(self) -> bool:
        return self.phase in ("liquid", "solid")

    @property
    def label(self) -> str:
        return self.display_name or self.name


def species_table(outcome: ChamberOutcome) -> dict[str, Any]:
    """The provider's ``Species`` records for this result's composition.

    Needed for the mole-to-mass conversion and for phase. Taken from the
    provider that produced the result, so the molar masses are the ones the
    chemistry was solved with, not a second atomic-weight table.
    """
    state = outcome.state
    if state is None:
        return {}
    provider = chamber_provider()
    if provider is None:
        return {}
    return provider.species_table(state.composition.species_names)


def species_rows(outcome: ChamberOutcome) -> tuple[SpeciesRow, ...]:
    """Every species in the result, sorted by mole fraction, descending.

    **Complete.** No threshold is applied here and none may be: a display
    filter is applied later, over these rows, and the underlying result keeps
    every species the provider returned (Phase 5D §3, §47).
    """
    from rocketforge.physics.thermochemistry import CompositionBasis

    state = outcome.state
    if state is None:
        return ()
    species = species_table(outcome)
    if not species:
        return ()

    mole = state.composition.to_basis(CompositionBasis.MOLE_FRACTION, species)
    mass = state.composition.to_basis(CompositionBasis.MASS_FRACTION, species)
    mole_fractions = dict(mole.fractions)
    mass_fractions = dict(mass.fractions)

    rows = [
        SpeciesRow(
            name=name,
            phase=str(species[name].phase.value) if name in species else "",
            mole_fraction=float(mole_fractions.get(name, 0.0)),
            mass_fraction=float(mass_fractions.get(name, 0.0)),
            display_name=getattr(species.get(name), "display_name", "") or "",
        )
        for name in mole_fractions
    ]
    # Descending mole fraction, name as the tie-break so the order is total and
    # therefore reproducible between runs.
    rows.sort(key=lambda row: (-row.mole_fraction, row.name))
    return tuple(rows)


#: The mass fraction at or above which the interface reports condensed
#: products as present.
#:
#: **A reporting threshold, not a physical cutoff.** It changes no composition,
#: deletes no species, alters no ``ChamberGas`` field, touches no element
#: balance and never reaches the provider. It decides one thing: which sentence
#: the interface says. The exact fraction is displayed beside that sentence in
#: every case, so the threshold is never the only number a reader gets.
#:
#: Chosen at 1e-06 because the canonical Phase 5C case sits at 6.24e-08 with
#: condensed *candidates* in the product set, and the genuine solid-carbon case
#: at O/F 0.5 is four orders of magnitude above it.
CONDENSED_REPORTING_THRESHOLD = 1.0e-6

#: The four things the interface can honestly say about condensed products.
#:
#: The middle two used to be one. Reporting a measured 6.24e-08 as "None
#: detected" claims the mixture contains no condensed material, and 6.24e-08 is
#: not zero -- so a fraction below the reporting threshold now says exactly
#: that, and says what the threshold is.
CONDENSED_UNKNOWN = "unknown"
CONDENSED_NONE_REPORTED = "none_reported"
CONDENSED_BELOW_THRESHOLD = "below_threshold"
CONDENSED_PRESENT = "present"


def condensed_summary(outcome: ChamberOutcome,
                      rows: tuple[SpeciesRow, ...] = ()) -> dict[str, Any]:
    """What the result says about condensed products, in four distinct states.

    Reads the state's ``condensed_mass_fraction`` -- which the provider
    computes from the returned composition -- and the species phases. It does
    **not** read any count of candidate condensed species: Phase 5C established
    that the canonical production case reports candidates while the amount
    present is 6.24e-08, and announcing "1 condensed species present" there
    would be false (Phase 5D §4, §51).

    ============================  =========================================
    ``unknown``                   the provider reported no fraction. Unknown
                                  is not the same as none (ADR-28).
    ``none_reported``             the fraction is exactly zero.
    ``below_threshold``           ``0 < fraction <`` the reporting threshold.
                                  Something is there; it is below the level
                                  this interface reports as present.
    ``present``                   ``fraction >=`` the reporting threshold.
    ============================  =========================================

    ``fraction`` and ``threshold`` are returned in every known state, because
    the verdict is a sentence about a number and the number belongs beside it.
    """
    threshold = CONDENSED_REPORTING_THRESHOLD
    state = outcome.state
    if state is None:
        return {"state": CONDENSED_UNKNOWN, "known": False, "present": False,
                "fraction": None, "threshold": threshold, "species": (),
                "headline": "No result yet",
                "detail": "Composition comes from a solved chamber equilibrium."}

    fraction = state.condensed_mass_fraction
    if fraction is None:
        return {"state": CONDENSED_UNKNOWN, "known": False, "present": False,
                "fraction": None, "threshold": threshold, "species": (),
                "headline": "Condensed fraction not reported",
                "detail": "The provider did not report a condensed fraction. "
                          "Unknown is not the same as none."}

    fraction = float(fraction)
    condensed = tuple(row for row in (rows or species_rows(outcome))
                      if row.is_condensed and row.mole_fraction > 0.0)

    if fraction <= 0.0:
        return {"state": CONDENSED_NONE_REPORTED, "known": True,
                "present": False, "fraction": fraction, "threshold": threshold,
                "species": condensed,
                "headline": "No condensed product reported",
                "detail": "Condensed mass fraction 0."}

    if fraction < threshold:
        return {"state": CONDENSED_BELOW_THRESHOLD, "known": True,
                "present": False, "fraction": fraction, "threshold": threshold,
                "species": condensed,
                "headline": "No condensed phase above reporting threshold",
                "detail": (f"Exact condensed mass fraction {fraction:.3e}, "
                           f"below the {threshold:.0e} reporting threshold. "
                           "The amount is not zero; it is below the level "
                           "this workspace reports as present.")}

    return {"state": CONDENSED_PRESENT, "known": True, "present": True,
            "fraction": fraction, "threshold": threshold,
            "species": condensed,
            "headline": "Condensed products present",
            "detail": (f"Total condensed mass fraction {fraction:.6g}, "
                       f"at or above the {threshold:.0e} reporting threshold.")}


# ---------------------------------------------------------------------------
# diagnostics
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DiagnosticRow:
    """One provider or validation message, ready to render.

    ``code`` is the stable machine identifier and is always carried, so an
    interface can key off it instead of matching English, and so a code this
    build does not recognise can still be shown with its own name attached.
    """

    code: str
    severity: str
    title: str
    message: str
    field: str = ""
    detail: dict = _dataclass_field(default_factory=dict)
    known: bool = True


#: Titles for the codes this build knows. The provider's own message is always
#: shown underneath; this is a heading, not a replacement (Phase 5D §182).
_DIAGNOSTIC_TITLES = {
    "PROVIDER_ASSIGNED_ENTHALPY_REACTANT": "Reactant temperature not used by the provider",
    "PROVIDER_NOT_CONVERGED": "Provider did not converge",
    "PROVIDER_COMPOSITION_SUM": "Composition does not sum to one",
    "COMPOSITION_CANONICALISED": "Composition canonicalised",
    "ELEMENT_BALANCE_VIOLATED": "Element conservation failed",
    "IDENTITY_VIOLATED": "State identity failed",
    "IDENTITY_OK": "State identity satisfied",
    "IDENTITY_NOT_APPLICABLE": "State identity not checked",
    "CONDENSED_CANDIDATES": "Condensed species were candidates",
}


def diagnostic_rows(outcome: ChamberOutcome,
                    *, include_info: bool = True) -> tuple[DiagnosticRow, ...]:
    """Provider and validation messages, most severe first.

    An unrecognised code is shown with a neutral title and its own name rather
    than being dropped or crashing the view, so a future backend diagnostic
    reaches the user on the day it is added (Phase 5D §183).
    """
    order = {"error": 0, "warning": 1, "info": 2}
    rows: list[DiagnosticRow] = []
    for diagnostic in outcome.diagnostics:
        severity = str(diagnostic.severity)
        if severity == "info" and not include_info:
            continue
        known = diagnostic.code in _DIAGNOSTIC_TITLES
        rows.append(DiagnosticRow(
            code=diagnostic.code,
            severity=severity,
            title=_DIAGNOSTIC_TITLES.get(diagnostic.code,
                                         f"Provider diagnostic {diagnostic.code}"),
            message=diagnostic.message,
            field=diagnostic.field or "",
            detail={k: float(v) for k, v in (diagnostic.detail or {}).items()},
            known=known,
        ))
    rows.sort(key=lambda row: order.get(row.severity, 3))
    return tuple(rows)


def assigned_enthalpy_notes(outcome: ChamberOutcome) -> tuple[dict, ...]:
    """The assigned-enthalpy warnings, expanded into their own record.

    Blocking for Phase 5D acceptance (§32). The provider states which reactant,
    which temperature was requested and which temperature the model actually
    used; all three are carried through so the interface can show the
    comparison rather than a bare "temperature ignored".
    """
    notes: list[dict] = []
    for diagnostic in outcome.diagnostics:
        if diagnostic.code != "PROVIDER_ASSIGNED_ENTHALPY_REACTANT":
            continue
        detail = diagnostic.detail or {}
        notes.append({
            "reactant": _reactant_from(diagnostic.message),
            "requested": float(detail.get("requested", float("nan"))),
            "assigned": float(detail.get("assigned", float("nan"))),
            "message": diagnostic.message,
        })
    return tuple(notes)


def _reactant_from(message: str) -> str:
    """The provider name the warning is about, from its own message.

    The provider quotes the reactant name; taking it from there keeps one
    source of truth. An unquoted message yields an empty string rather than a
    guess, and the full message is displayed regardless.
    """
    start = message.find("'")
    if start < 0:
        return ""
    end = message.find("'", start + 1)
    return message[start + 1:end] if end > start else ""


# ---------------------------------------------------------------------------
# provenance
# ---------------------------------------------------------------------------


def provenance_summary(outcome: ChamberOutcome) -> dict[str, str]:
    """The compact provenance line: who computed this, in what model."""
    provenance = outcome.provenance
    if provenance is None:
        return {"provider": "", "model": "", "database": "", "sha": ""}
    version = provenance.library_version or provenance.provider_version
    digest = provenance.database_sha256
    return {
        "provider": f"{PROVIDER_LABEL} {version}".strip(),
        "model": MODEL_SUMMARY,
        "database": provenance.database,
        "sha": f"{digest[:8]}…" if digest else "",
    }


def provenance_details(outcome: ChamberOutcome) -> tuple[dict[str, str], ...]:
    """Every provenance fact, as label/value rows.

    Read from the **result's own** provenance record, never from what happens
    to be installed now. A result keeps the identity of the provider that made
    it (Phase 5D §180, §181).
    """
    provenance = outcome.provenance
    if provenance is None:
        return ()

    case = outcome.case
    rows: list[dict[str, str]] = [
        {"label": "Provider", "value": PROVIDER_LABEL},
        {"label": "Provider id", "value": provenance.provider_id},
        {"label": "Adapter version", "value": provenance.provider_version},
        {"label": "Library version", "value": provenance.library_version},
        {"label": "Chemistry mode",
         "value": (provenance.chemistry_mode.value.title()
                   if provenance.chemistry_mode else CHEMISTRY_MODE_LABEL)},
        {"label": "Equilibrium constraint",
         "value": (CONSTRAINT_LABEL if provenance.equilibrium_constraint
                   else "")},
        {"label": "Heat-loss assumption", "value": "Adiabatic"},
        {"label": "Database", "value": provenance.database},
        {"label": "Database SHA-256", "value": provenance.database_sha256},
        {"label": "Product species",
         "value": f"{len(provenance.species_set)} species"},
    ]
    if case is not None:
        fuel = propellant_named(case.fuel)
        oxidiser = propellant_named(case.oxidiser)
        rows.append({"label": "Fuel (provider name)",
                     "value": (fuel.provider_name if fuel else "")})
        rows.append({"label": "Oxidiser (provider name)",
                     "value": (oxidiser.provider_name if oxidiser else "")})
    for key, value in sorted(provenance.options.items()):
        rows.append({"label": f"Option · {key}", "value": str(value)})
    for warning in provenance.warnings:
        rows.append({"label": "Provider note", "value": warning})
    return tuple(row for row in rows if row["value"])


def species_set(outcome: ChamberOutcome) -> tuple[str, ...]:
    """The product species set actually used, from the result's provenance."""
    provenance = outcome.provenance
    return tuple(provenance.species_set) if provenance is not None else ()


# ---------------------------------------------------------------------------
# labels
# ---------------------------------------------------------------------------


def case_headline(case: ChamberCase | None) -> str:
    """The one-line statement of what a result is for.

    Built from the case the result carries, never from the live input form, so
    editing an input cannot relabel an existing result (Phase 5D §133, §134).
    """
    if case is None:
        return ""
    fuel = propellant_named(case.fuel)
    oxidiser = propellant_named(case.oxidiser)
    names = f"{oxidiser.key if oxidiser else case.oxidiser} / " \
            f"{fuel.key if fuel else case.fuel}"
    return (f"{names} · O/F {case.oxidiser_fuel_ratio:g} · "
            f"p_c {case.chamber_pressure / 1.0e5:g} bar")

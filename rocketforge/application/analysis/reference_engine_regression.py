"""DB-4A: whether a shipped reference-engine value could become an executable regression.

``REGRESSION_CANDIDATE`` (the evidence capability) says a configuration's record is
*eligible for review*: admitted, opened, rights-cleared values at one operating
point. This module is that review. It asks, quantity by quantity, whether the
source's number means what RocketForge's model output means, so that a
difference between them could be a verdict on the model.

Read-only and solver-free: it takes a loaded :class:`ReferenceEngineCatalog`,
reads its frozen evidence, and returns plain review records. It never runs a
provider or a physics model, never changes the corpus, and never writes. An
accepted case would still have to be built in the comparison layer
(:mod:`rocketforge.comparison.cases`) with its own provenance; this module only
says whether one may be.

The model it reviews against is RocketForge's ideal rocket performance
(``engineering/nozzle/performance.py``): NASA CEA chamber equilibrium, reduced
to a constant-gamma gas, expanded through a frozen ideal nozzle, with no
efficiency of any kind. Its specific impulse and thrust are **ideal
thrust-chamber** quantities. A source's engine rating is a **delivered**
quantity. The two are not interchangeable, and a difference between them is not
an error.

As it stands the gate cannot return ``HARD_REGRESSION_ELIGIBLE`` or
``VALIDATION_COMPARISON_ELIGIBLE``: a delivered value ends at
``EFFICIENCY_COMPARISON_ONLY`` at best, and an ideal one is blocked until a source
can also record its expansion model and inlet state, which no evidence field can
yet carry. The constants name the vocabulary a future, owner-approved path
would use; adding that path is an owner decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from rocketforge.evidence.engines import Assertion, NumberValue, regression_blockers
from rocketforge.evidence.engines.capabilities import PERFORMANCE_QUANTITIES, Capability, CapabilityStatus
from rocketforge.evidence.engines.vocabulary import (
    Environment,
    IspBasis,
    MixtureRatioBasis,
    MixtureRatioForm,
    PressureBasis,
    PressureStation,
    SubjectKind,
    ValueKind,
)

from .reference_engine_catalog import ReferenceEngineCatalog

__all__ = [
    "RESULTS", "HARD_REGRESSION_ELIGIBLE", "VALIDATION_COMPARISON_ELIGIBLE", "EFFICIENCY_COMPARISON_ONLY",
    "INPUT_ELIGIBLE", "REFERENCE_ONLY", "BLOCKED_MISSING_INPUTS", "BLOCKED_SEMANTICS", "BLOCKED_CONFLICT",
    "BLOCKED_RIGHTS", "BLOCKED_MODEL_CAPABILITY", "MODEL", "MODEL_CHOICES_NOT_FROM_SOURCE", "TOLERANCE_BASES",
    "QuantityReview", "CandidateReview", "regression_candidates", "review_candidate", "review_all",
    "source_semantic", "tolerance_problems",
]

HARD_REGRESSION_ELIGIBLE = "HARD_REGRESSION_ELIGIBLE"
VALIDATION_COMPARISON_ELIGIBLE = "VALIDATION_COMPARISON_ELIGIBLE"
EFFICIENCY_COMPARISON_ONLY = "EFFICIENCY_COMPARISON_ONLY"
INPUT_ELIGIBLE = "INPUT_ELIGIBLE"
REFERENCE_ONLY = "REFERENCE_ONLY"
BLOCKED_MISSING_INPUTS = "BLOCKED_MISSING_INPUTS"
BLOCKED_SEMANTICS = "BLOCKED_SEMANTICS"
BLOCKED_CONFLICT = "BLOCKED_CONFLICT"
BLOCKED_RIGHTS = "BLOCKED_RIGHTS"
BLOCKED_MODEL_CAPABILITY = "BLOCKED_MODEL_CAPABILITY"
RESULTS = (HARD_REGRESSION_ELIGIBLE, VALIDATION_COMPARISON_ELIGIBLE, EFFICIENCY_COMPARISON_ONLY, INPUT_ELIGIBLE,
           REFERENCE_ONLY, BLOCKED_MISSING_INPUTS, BLOCKED_SEMANTICS, BLOCKED_CONFLICT, BLOCKED_RIGHTS,
           BLOCKED_MODEL_CAPABILITY)

#: The model every review is against, as it is.
MODEL = ("RocketForge ideal rocket performance: NASA CEA HP chamber equilibrium, reduced to a constant-gamma gas, "
         "frozen ideal nozzle, no efficiency (rocketforge/engineering/nozzle/performance.py)")

#: Choices the ideal value depends on that no reference-engine source prints. A comparison that had to make
#: them would be choosing the model, not testing it.
MODEL_CHOICES_NOT_FROM_SOURCE = (
    "gamma strategy (chamber or throat)",
    "gamma basis (frozen cp/cv or equilibrium gamma_s)",
    "propellant inlet state of the cryogenic reactants",
)

#: Where a hard-regression tolerance may come from. Never from the difference observed. A value's printed
#: precision alone is a reading bound, not a physical uncertainty, so it is not a basis by itself; the comparison
#: layer's significant-figure rule for thermochemistry printouts is an established validation contract.
#: :func:`tolerance_problems` is a declarative rule: it is the check a future case must pass, and nothing calls
#: it today because no case exists.
TOLERANCE_BASES = ("STATED_UNCERTAINTY", "PROVIDER_NUMERICAL_TOLERANCE", "ESTABLISHED_VALIDATION_CONTRACT")

#: The model's expected outputs and what each means; both are ideal thrust-chamber quantities.
_OUTPUTS = ("thrust", "specific_impulse")
#: The model's inputs a source value may supply.
_INPUTS = ("chamber_pressure", "mixture_ratio", "area_ratio")
#: The value kinds a regression may use, as an input or an expected output: a point value. Stricter than the
#: evidence's operating kinds (which count bounds, averages and approximations): a minimum or maximum guarantee
#: is a bound, an average is not the value at the operating point, an approximation has no precision a tolerance
#: could rest on, and a design value, limit, prediction or target is never a measured or rated output. The
#: evidence vocabulary itself is unchanged.
_POINT_KINDS = frozenset({ValueKind.NOMINAL, ValueKind.RATED, ValueKind.TEST_RESULT})
#: Environments at which the ambient pressure an output depends on is known. ALTITUDE records no ambient
#: pressure, so for a comparison it is as unknown as UNKNOWN.
_KNOWN_ENVIRONMENTS = frozenset({Environment.VACUUM, Environment.SEA_LEVEL})

_DELIVERED = ("the source prints an engine rating or measurement, a delivered quantity; the model's is ideal "
              "thrust-chamber performance with no efficiency, so the two do not mean the same thing")
_NO_EFFICIENCY_CLASS = ("RocketForge's comparison layer has no accepted delivered/ideal efficiency class "
                        "(rocketforge/comparison/cases.py: verdicts only against CEA_DIRECT or NASA_PUBLISHED "
                        "thermochemistry; EXPERIMENT is reserved and draws no verdict); adding one is an owner "
                        "decision")


@dataclass(frozen=True, slots=True)
class QuantityReview:
    """One quantity of one candidate, in one role, with what blocks it.

    Attributes:
        configuration_id: The candidate.
        quantity: ``thrust``, ``specific_impulse``, ``chamber_pressure``, ``mixture_ratio`` or ``area_ratio``.
        role: ``"expected_output"`` (a value a model run would be compared with) or ``"input"`` (a value a
            model run would take). An input is never an expected output, whatever its result.
        assertion_ids: The configuration's shipped assertions for the quantity.
        result: One of :data:`RESULTS`.
        blockers: Why it is not more than ``result``; empty only for an eligible result.
    """

    configuration_id: str
    quantity: str
    role: str
    assertion_ids: tuple[str, ...]
    result: str
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CandidateReview:
    configuration_id: str
    label: str
    quantities: tuple[QuantityReview, ...]

    @property
    def hard_regressions(self) -> tuple[QuantityReview, ...]:
        return tuple(q for q in self.quantities if q.result == HARD_REGRESSION_ELIGIBLE)


def regression_candidates(catalog: ReferenceEngineCatalog) -> tuple[str, ...]:
    """The configurations the evidence capability rates SUPPORTED: eligible for review, nothing more."""
    return tuple(e.configuration_id for e in catalog.entries()
                 if catalog.capability(e.configuration_id, Capability.REGRESSION_CANDIDATE).status
                 is CapabilityStatus.SUPPORTED)


def _own(catalog: ReferenceEngineCatalog, cfg: str, quantity: str) -> tuple[Assertion, ...]:
    """The configuration's own assertions for a quantity: never its variant's or family's."""
    paths = PERFORMANCE_QUANTITIES[quantity]
    return tuple(a for a in catalog.assertions(cfg)
                 if a.field_path in paths and a.subject.kind is not SubjectKind.VARIANT
                 and a.subject.kind is not SubjectKind.FAMILY)


def _evidence_blockers(catalog: ReferenceEngineCatalog, a: Assertion) -> tuple[list[str], list[str], list[str]]:
    """(conflict, rights, semantics) reasons an assertion cannot be relied on at all.

    Every reason the evidence's own :func:`regression_blockers` gives (admission, INFERRED status, source
    access and authority, first statement, schematic provenance, conflicts, rights) is kept, sorted into the
    three groups; the review then adds its own stricter checks. It never relaxes the evidence's.
    """
    conflict, rights, semantics = [], [], []
    for reason in regression_blockers(catalog.corpus, [a.assertion_id]):
        if " conflict " in reason or "not the claim that stands" in reason:
            conflict.append(reason)
        elif "may not ship" in reason or "rights of" in reason:
            rights.append(reason)
        else:
            semantics.append(reason)
    if a.value_kind not in _POINT_KINDS:
        semantics.append(f"{a.assertion_id}: value kind {a.value_kind.value} is not a point value a regression may "
                         "use (a design value, limit, bound, approximation, prediction or target never is)")
    if a.subject.kind in (SubjectKind.VARIANT, SubjectKind.FAMILY):
        semantics.append(f"{a.assertion_id}: stated for the {a.subject.kind.value.lower()}, not the configuration")
    if a.subject.kind in (SubjectKind.PROPULSION_UNIT, SubjectKind.COMPONENT):
        semantics.append(f"{a.assertion_id}: stated for a {a.subject.kind.value.lower().replace('_', ' ')} (a "
                         "cluster or a part), not the single engine the model computes")
    if not isinstance(a.value, NumberValue):
        semantics.append(f"{a.assertion_id}: not a single number")
    return conflict, rights, semantics


def _verdict(conflict, rights, semantics, eligible) -> tuple[str, tuple[str, ...]]:
    if conflict:
        return BLOCKED_CONFLICT, tuple(conflict + rights + semantics)
    if rights:
        return BLOCKED_RIGHTS, tuple(rights + semantics)
    if semantics:
        return BLOCKED_SEMANTICS, tuple(semantics)
    return eligible, ()


def _review_input(catalog: ReferenceEngineCatalog, cfg: str, quantity: str) -> QuantityReview:
    found = _own(catalog, cfg, quantity)
    if not found:
        return QuantityReview(cfg, quantity, "input", (), BLOCKED_MISSING_INPUTS,
                              (f"no {quantity} is recorded for the configuration",))
    conflict, rights, semantics = [], [], []
    for a in found:
        c, r, s = _evidence_blockers(catalog, a)
        conflict += c
        rights += r
        semantics += s
        cond = a.conditions
        if quantity == "chamber_pressure":
            if cond.pressure_station is not PressureStation.NOZZLE_STAGNATION:
                semantics.append(f"{a.assertion_id}: pressure station "
                                 f"{getattr(cond.pressure_station, 'value', 'not recorded')}; the model's chamber "
                                 "pressure is the stagnation pressure entering the nozzle")
            if cond.pressure_basis is not PressureBasis.ABSOLUTE:
                semantics.append(f"{a.assertion_id}: pressure basis "
                                 f"{getattr(cond.pressure_basis, 'value', 'not recorded')}, not absolute")
        if quantity == "mixture_ratio":
            if cond.mixture_ratio_form is not MixtureRatioForm.OXIDIZER_TO_FUEL:
                semantics.append(f"{a.assertion_id}: direction "
                                 f"{getattr(cond.mixture_ratio_form, 'value', 'not printed')}; the model takes O/F")
            if cond.mixture_ratio_basis is not MixtureRatioBasis.THRUST_CHAMBER:
                semantics.append(f"{a.assertion_id}: an {getattr(cond.mixture_ratio_basis, 'value', 'unstated')} "
                                 "mixture ratio; the model takes the thrust chamber's (injector) ratio, and an engine "
                                 "ratio counts any propellant routed around the chamber (gas generator, turbine "
                                 "drive): equating the two would be an engineering inference no source prints")
    result, blockers = _verdict(conflict, rights, semantics, INPUT_ELIGIBLE)
    return QuantityReview(cfg, quantity, "input", tuple(a.assertion_id for a in found), result, blockers)


#: The qualifier a record would carry if its source printed an ideal (theoretical) value. None does today.
_BASIS_QUALIFIER = "performance_basis"
_IDEAL_WORDS = ("ideal", "theoretical")


def source_semantic(a: Assertion) -> str:
    """``"IDEAL"`` only where the record says the source printed an ideal value; otherwise ``"DELIVERED"``.

    An engine's printed thrust or specific impulse is a rating or a measurement of real hardware unless the
    source says it is theoretical. The evidence schema carries that as a qualifier; absent one, the value is
    taken as delivered, which is the conservative reading (it can only block a hard regression).
    """
    for q in a.conditions.qualifiers:
        if q.name == _BASIS_QUALIFIER and q.value.strip().lower() in _IDEAL_WORDS:
            return "IDEAL"
    return "DELIVERED"


def _review_output(catalog: ReferenceEngineCatalog, cfg: str, quantity: str,
                   inputs: dict[str, QuantityReview]) -> QuantityReview:
    found = _own(catalog, cfg, quantity)
    ids = tuple(a.assertion_id for a in found)
    if not found:
        return QuantityReview(cfg, quantity, "expected_output", (), BLOCKED_MISSING_INPUTS,
                              (f"no {quantity} is recorded for the configuration",))
    conflict, rights, semantics, missing = [], [], [], []
    for a in found:
        c, r, s = _evidence_blockers(catalog, a)
        conflict += c
        rights += r
        semantics += s
        cond = a.conditions
        if cond.environment not in _KNOWN_ENVIRONMENTS:
            semantics.append(f"{a.assertion_id}: environment not stated "
                             f"({getattr(cond.environment, 'value', 'not recorded')}, no ambient pressure); "
                             f"the model's {quantity} depends on it")
        if quantity == "specific_impulse" and cond.isp_basis in (None, IspBasis.UNKNOWN):
            semantics.append(f"{a.assertion_id}: engine or thrust-chamber basis not stated; the model's is the "
                             "thrust chamber's")
    missing += [f"input {name}: {inputs[name].result}" for name in _INPUTS
                if inputs[name].result != INPUT_ELIGIBLE]
    if quantity == "thrust":
        missing.append("a thrust needs the engine's size (throat area or mass flow); no source records one")
    choices = "the ideal value also depends on choices no source prints: " + "; ".join(MODEL_CHOICES_NOT_FROM_SOURCE)
    delivered = tuple(f"{a.assertion_id}: {_DELIVERED}" for a in found if source_semantic(a) == "DELIVERED")
    for kind, reasons in ((BLOCKED_CONFLICT, conflict), (BLOCKED_RIGHTS, rights), (BLOCKED_SEMANTICS, semantics),
                          (BLOCKED_MISSING_INPUTS, missing)):
        if reasons:
            rest = [x for x in (*conflict, *rights, *semantics, *missing) if x not in reasons]
            # what would still stand if these were resolved: delivered against ideal is never a hard regression
            return QuantityReview(cfg, quantity, "expected_output", ids, kind, (*reasons, *rest, *delivered))
    if any(source_semantic(a) == "DELIVERED" for a in found):
        # complete and comparable, but delivered against ideal: at most a non-locking efficiency, never an error
        return QuantityReview(cfg, quantity, "expected_output", ids, EFFICIENCY_COMPARISON_ONLY,
                              tuple(f"{a.assertion_id}: {_DELIVERED}" for a in found) + (choices, _NO_EFFICIENCY_CLASS))
    # an ideal source value: a hard regression still needs the model's choices fixed by the source
    return QuantityReview(cfg, quantity, "expected_output", ids, BLOCKED_SEMANTICS,
                          (choices, "an ideal source value must also print its expansion model and inlet state "
                                    "before it can lock the model"))


def review_candidate(catalog: ReferenceEngineCatalog, cfg: str) -> CandidateReview:
    """Every input and expected output of one configuration, reviewed against :data:`MODEL`."""
    inputs = {q: _review_input(catalog, cfg, q) for q in _INPUTS}
    outputs = [_review_output(catalog, cfg, q, inputs) for q in _OUTPUTS]
    return CandidateReview(cfg, catalog.entry(cfg).label, (*outputs, *inputs.values()))


def review_all(catalog: ReferenceEngineCatalog) -> tuple[CandidateReview, ...]:
    """The review of every current regression candidate, and of nothing else."""
    return tuple(review_candidate(catalog, cfg) for cfg in regression_candidates(catalog))


def tolerance_problems(basis: str, *, derived_after_comparison: bool) -> tuple[str, ...]:
    """Why a hard-regression tolerance is not acceptable. Empty means its provenance is admissible.

    A tolerance is fixed from the source or an established contract **before** the model is run; a
    threshold read off the observed difference is never one.
    """
    out = []
    if basis not in TOLERANCE_BASES:
        out.append(f"tolerance basis {basis!r} is not one of {', '.join(TOLERANCE_BASES)}")
    if derived_after_comparison:
        out.append("a tolerance chosen after seeing the model's result fits the result; it tests nothing")
    return tuple(out)

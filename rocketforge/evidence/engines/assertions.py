"""Technical assertions: one thing one source says about one subject.

An :class:`Assertion` is the engine counterpart of
:class:`~rocketforge.evidence.ReportedValue`. It keeps that type's discipline --
the value as printed, the unit as printed, the source, the locator, the
:class:`~rocketforge.evidence.ValueStatus` -- and adds what engine data forced:

* a typed value: a number, a range, an enumeration token, a text statement, or
  an explicit :class:`~rocketforge.evidence.Missing`;
* a subject at the level the source describes, an optional operating point,
  and an epoch;
* a :class:`~.vocabulary.ValueKind`, so a limit is never read as an operating value;
* structured :class:`Conditions` (environment, power level, mixture-ratio
  setting, pressure basis and chamber-pressure station, Isp basis);
* first-stated-by provenance for a value repeated second-hand;
* an optional normalised quantity that sits beside the printed value and never
  replaces it.

Field paths are dotted lowercase names. Four quantities have one canonical
name each, with an optional suffix (``thrust_vac``), and a printed value of them
must state the conditions without which published values are not
interchangeable: ``chamber_pressure`` (pressure basis and measurement station),
``thrust`` (environment; ``thrust_chamber*`` is not thrust), ``specific_impulse``
(environment and Isp basis) and ``mixture_ratio`` (form and basis). Synonyms
that would slip past (``isp``, ``pc``, ``vacuum_thrust``) are refused. "Not
stated by the source" is a value of each condition (``UNKNOWN``), never an
omission; a Missing value prints nothing and carries no obligations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..values import EvidenceError, Missing, ValueStatus
from . import _checks as c
from .identity import SubjectRef
from .vocabulary import (
    Admissibility,
    Environment,
    IspBasis,
    MixtureRatioBasis,
    MixtureRatioForm,
    PressureBasis,
    PressureStation,
    SourceAccess,
    ValueKind,
)

__all__ = [
    "NumberValue", "RangeValue", "EnumValue", "TextValue", "AssertionValue",
    "Setting", "Qualifier", "Conditions", "NormalizedQuantity", "Derivation",
    "Assertion", "FIELD_PATH_PATTERN",
]

#: Dotted lowercase segments: ``performance.chamber_pressure``, ``pumps.hpotp.speed``.
FIELD_PATH_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9][a-z0-9_]*)*$")
_TOKEN = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True, slots=True)
class NumberValue:
    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", c.number(self.value, "number value"))


@dataclass(frozen=True, slots=True)
class RangeValue:
    """A printed range ("67% - 109%"), both ends inclusive as printed."""

    low: float
    high: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "low", c.number(self.low, "range low"))
        object.__setattr__(self, "high", c.number(self.high, "range high"))
        if self.low > self.high:
            raise EvidenceError(f"a range runs low to high, got {self.low} > {self.high}")


@dataclass(frozen=True, slots=True)
class EnumValue:
    """A categorical statement as a token (``TAP_OFF``, ``FUEL_RICH``).

    The token is the claim; its vocabulary for a given field is not fixed by
    this schema, so a token from a source is never forced into a nearby one.
    """

    token: str

    def __post_init__(self) -> None:
        if not isinstance(self.token, str) or not _TOKEN.match(self.token):
            raise EvidenceError(f"an enumeration token is UPPER_SNAKE_CASE, got {self.token!r}")


@dataclass(frozen=True, slots=True)
class TextValue:
    """A statement only words can hold (a flow description, a control law)."""

    text: str

    def __post_init__(self) -> None:
        c.text(self.text, "text value")


#: What an assertion can state.
AssertionValue = NumberValue | RangeValue | EnumValue | TextValue | Missing
_QUANTITIES = (NumberValue, RangeValue)


@dataclass(frozen=True, slots=True)
class Setting:
    """A condition setting as printed: ``109`` ``%`` of ``RPL``; mixture ratio ``5.5`` ``:1``."""

    value: float
    unit: str
    reference: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", c.number(self.value, "setting value"))
        c.text(self.unit, "setting unit")
        c.plain(self.reference, "setting reference")


@dataclass(frozen=True, slots=True)
class Qualifier:
    """A further named condition (``inlet_temperature``: ``-423 F``; ``ground_test``: ``AEDC J-4``)."""

    name: str
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not re.match(r"^[a-z][a-z0-9_]*$", self.name):
            raise EvidenceError(f"a qualifier name is lowercase_snake_case, got {self.name!r}")
        c.text(self.value, f"qualifier {self.name}")


@dataclass(frozen=True, slots=True)
class Conditions:
    """The conditions a value is stated at. ``None`` means "not a condition of this value".

    Where a source can fail to say, the enumerations have ``UNKNOWN``: that
    records the source's silence. ``None`` and ``UNKNOWN`` are different
    statements, and the field-path obligations in this module require the
    latter, not an omission.
    """

    environment: Environment | None = None
    power_level: Setting | None = None
    mixture_ratio: Setting | None = None
    mixture_ratio_form: MixtureRatioForm | None = None
    mixture_ratio_basis: MixtureRatioBasis | None = None
    pressure_basis: PressureBasis | None = None
    pressure_station: PressureStation | None = None
    isp_basis: IspBasis | None = None
    qualifiers: tuple[Qualifier, ...] = ()

    def __post_init__(self) -> None:
        c.optional_member(Environment, self.environment, "environment")
        for name in ("power_level", "mixture_ratio"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, Setting):
                raise EvidenceError(f"{name} must be a Setting or None, got {value!r}")
        c.optional_member(MixtureRatioForm, self.mixture_ratio_form, "mixture_ratio_form")
        c.optional_member(MixtureRatioBasis, self.mixture_ratio_basis, "mixture_ratio_basis")
        c.optional_member(PressureBasis, self.pressure_basis, "pressure_basis")
        c.optional_member(PressureStation, self.pressure_station, "pressure_station")
        c.optional_member(IspBasis, self.isp_basis, "isp_basis")
        c.instances(self.qualifiers, Qualifier, "qualifiers")
        names = [q.name for q in self.qualifiers]
        if len(set(names)) != len(names):
            raise EvidenceError("a qualifier is given twice")
        if self.mixture_ratio is not None and (self.mixture_ratio_form is None
                                               or self.mixture_ratio_basis is None):
            raise EvidenceError(
                "a mixture-ratio setting states which way up it is and which flow it describes "
                "(mixture_ratio_form, mixture_ratio_basis)")


@dataclass(frozen=True, slots=True)
class NormalizedQuantity:
    """An SI rendering of a printed quantity, kept beside it, never in its place."""

    value: NumberValue | RangeValue
    unit: str
    method: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, _QUANTITIES):
            raise EvidenceError("a normalised quantity is a number or a range")
        c.text(self.unit, "normalised unit")
        c.text(self.method, "normalisation method (the conversion used)")


@dataclass(frozen=True, slots=True)
class Derivation:
    """The arithmetic behind a DERIVED value: which assertions, combined how."""

    input_assertion_ids: tuple[str, ...]
    method: str

    def __post_init__(self) -> None:
        c.idents(self.input_assertion_ids, "derivation inputs", allow_empty=False)
        c.text(self.method, "derivation method")


#: Spellings that would hide a quantity from its obligations: ``isp``, ``pc``,
#: ``isp_vac``, ``vacuum_thrust``, ``main_chamber_pressure``. One canonical name
#: per quantity (a suffix after it is fine: ``thrust_vac``) keeps the checks honest.
_SYNONYM = re.compile(
    r"(^|_)(isp|pc|p_c)(_|$)|_thrust$|_specific_impulse$|_chamber_pressure$|_mixture_ratio$")


def _final(field_path: str) -> str:
    return field_path.rsplit(".", 1)[-1]


@dataclass(frozen=True, slots=True)
class Assertion:
    """One statement one source makes about one subject.

    Attributes:
        assertion_id: Stable identifier.
        subject: What the statement is about, at the level the source
            describes. A value printed for a configuration is about the
            configuration.
        field_path: Dotted lowercase name of the quantity or fact.
        value: Number, range, token, text, or Missing.
        value_as_printed: The text as printed ("2,994 psia", "approximately
            30,000 rpm"). Empty only for a Missing value.
        unit_as_printed: The unit as printed, for a number or range; empty
            otherwise.
        normalized: Optional SI rendering of a number or range.
        conditions: :class:`Conditions`.
        operating_point_id: The operating point the value belongs to, if any;
            it must be one of the subject's configuration's points.
        epoch: When the statement applies, if the source says ("SA-503 manual,
            25 Nov 1968").
        value_kind: :class:`~.vocabulary.ValueKind`.
        status: How it entered the record; ``None`` exactly when the value is
            Missing.
        admissibility: Whether it is evidence about the subject.
        source_id: Where it was read.
        locator: Page, table, figure.
        access: The source's access state when the assertion was made; must
            agree with the source.
        first_stated_by: The source that first stated it, when this source
            repeats it second-hand (a placard transcribed in a briefing).
        schematic_id: The schematic a DIGITISED value was read from, if any.
        derivation: The arithmetic, for a DERIVED value.
        note: Anything a reader needs to interpret the statement.
    """

    assertion_id: str
    subject: SubjectRef
    field_path: str
    value: AssertionValue
    value_as_printed: str
    unit_as_printed: str
    conditions: Conditions
    value_kind: ValueKind
    status: ValueStatus | None
    admissibility: Admissibility
    source_id: str
    locator: str
    access: SourceAccess
    operating_point_id: str | None = None
    epoch: str | None = None
    normalized: NormalizedQuantity | None = None
    first_stated_by: str | None = None
    schematic_id: str | None = None
    derivation: Derivation | None = None
    note: str = ""

    def __post_init__(self) -> None:
        c.ident(self.assertion_id, "assertion_id")
        where = self.assertion_id
        if not isinstance(self.subject, SubjectRef):
            raise EvidenceError(f"{where}: subject must be a SubjectRef")
        if not isinstance(self.field_path, str) or not FIELD_PATH_PATTERN.match(self.field_path):
            raise EvidenceError(f"{where}: field_path {self.field_path!r} is not dotted lowercase")
        if not isinstance(self.value, (NumberValue, RangeValue, EnumValue, TextValue, Missing)):
            raise EvidenceError(f"{where}: value must be a number, range, token, text or Missing")
        missing = isinstance(self.value, Missing)
        c.plain(self.value_as_printed, "value_as_printed")
        c.plain(self.unit_as_printed, "unit_as_printed")
        if missing:
            if self.value_as_printed or self.unit_as_printed:
                raise EvidenceError(f"{where}: a Missing value has nothing printed")
            if self.status is not None:
                raise EvidenceError(f"{where}: a Missing value has no value status")
        else:
            c.text(self.value_as_printed, f"{where}: value_as_printed")
            c.member(ValueStatus, self.status, f"{where}: status")
        quantity = isinstance(self.value, _QUANTITIES)
        if quantity and not self.unit_as_printed.strip():
            raise EvidenceError(f"{where}: a number or range carries its printed unit")
        if not quantity and self.unit_as_printed:
            raise EvidenceError(f"{where}: only a number or range has a unit")
        if not isinstance(self.conditions, Conditions):
            raise EvidenceError(f"{where}: conditions must be Conditions")
        c.member(ValueKind, self.value_kind, f"{where}: value_kind")
        c.member(Admissibility, self.admissibility, f"{where}: admissibility")
        if self.admissibility is not Admissibility.ADMITTED and not self.note.strip():
            raise EvidenceError(f"{where}: a rejected assertion says why in its note")
        c.ident(self.source_id, f"{where}: source_id")
        c.text(self.locator, f"{where}: locator")
        c.member(SourceAccess, self.access, f"{where}: access")
        if self.operating_point_id is not None:
            c.ident(self.operating_point_id, f"{where}: operating_point_id")
        if self.epoch is not None:
            c.text(self.epoch, f"{where}: epoch")
        if self.normalized is not None:
            if not isinstance(self.normalized, NormalizedQuantity):
                raise EvidenceError(f"{where}: normalized must be a NormalizedQuantity")
            if not quantity:
                raise EvidenceError(f"{where}: only a number or range can be normalised")
            if type(self.normalized.value) is not type(self.value):
                raise EvidenceError(f"{where}: a normalised value keeps the shape of the printed one")
        if self.first_stated_by is not None:
            c.ident(self.first_stated_by, f"{where}: first_stated_by")
            if self.first_stated_by == self.source_id:
                raise EvidenceError(f"{where}: first_stated_by names another source than source_id")
        if self.schematic_id is not None:
            c.ident(self.schematic_id, f"{where}: schematic_id")
        if self.derivation is not None and not isinstance(self.derivation, Derivation):
            raise EvidenceError(f"{where}: derivation must be a Derivation")
        if (self.status is ValueStatus.DERIVED) != (self.derivation is not None):
            raise EvidenceError(f"{where}: a DERIVED value, and only a derived one, records its derivation")
        if self.derivation is not None and self.assertion_id in self.derivation.input_assertion_ids:
            raise EvidenceError(f"{where}: a value cannot be derived from itself")
        c.plain(self.note, "note")
        self._check_field_obligations()

    def _check_field_obligations(self) -> None:
        final = _final(self.field_path)
        cond = self.conditions
        where = self.assertion_id
        synonym = _SYNONYM.search(final)
        if synonym:
            raise EvidenceError(
                f"{where}: field path ending {final!r} names a quantity with a canonical name; "
                "use chamber_pressure, thrust or specific_impulse (with a suffix after them) so "
                "its conditions are checked")
        if self.is_missing:
            return  # nothing was printed, so there is no printed condition to keep
        thrust = (final == "thrust" or final.startswith("thrust_")) and not final.startswith("thrust_chamber")
        if final == "chamber_pressure" or final.startswith("chamber_pressure_"):
            if cond.pressure_basis is None or cond.pressure_station is None:
                raise EvidenceError(
                    f"{where}: a chamber pressure states its pressure basis and measurement "
                    "station (UNKNOWN when the source does not say)")
        isp = final == "specific_impulse" or final.startswith("specific_impulse_")
        if (thrust or isp) and cond.environment is None:
            raise EvidenceError(
                f"{where}: thrust and specific impulse state the environment "
                "(UNKNOWN when the source does not say)")
        if isp and cond.isp_basis is None:
            raise EvidenceError(f"{where}: a specific impulse states its basis (UNKNOWN allowed)")
        if final == "mixture_ratio" or final.startswith("mixture_ratio_"):
            if cond.mixture_ratio_form is None or cond.mixture_ratio_basis is None:
                raise EvidenceError(
                    f"{where}: a mixture ratio states which way up it is and which flow it describes")

    @property
    def is_quantity(self) -> bool:
        return isinstance(self.value, _QUANTITIES)

    @property
    def is_missing(self) -> bool:
        return isinstance(self.value, Missing)

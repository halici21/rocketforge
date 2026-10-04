"""Burn-rate laws as a source states them.

A :class:`BurnLawReference` is evidence: the piecewise law ``r = a * p^n`` a
source publishes, regime by regime, with each regime's reported pressure
interval, coefficients and units, the test temperature as the source states it,
and the uncertainty it gives or does not give. It is not an internal-ballistics
model and computes nothing: evaluating a law inside its published domain is an
application-layer step with its own refusals, and this package never does it.

What is enforced on construction, because a structure that breaks it is not a
source's law:

* every number is a :class:`~.values.ReportedValue` -- a law with a missing
  coefficient or limit is not a law, and is refused rather than completed;
* each regime's interval is positive and ordered (``p_min < p_max``), and the
  regimes are in ascending pressure order and do not overlap -- adjacent regimes
  may share an endpoint, and a gap between regimes is allowed and stays a gap;
* the interval limits are in the law's pressure unit, ``a`` in its rate unit and
  ``n`` dimensionless (unit ``"1"``), exactly as recorded; nothing is converted;
* the temperature and the uncertainty are explicit data: a reported value, or a
  :class:`~.values.Missing` saying why there is none. "Ambient" is not a number.

Nothing here normalises, fits, smooths, interpolates or extends a law.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .values import Datum, EvidenceError, Missing, ReportedValue

__all__ = ["BURN_LAW_FORM", "BurnLawRegime", "BurnLawReference"]

#: The one law form schema version 2 records: Saint Robert / Vieille.
BURN_LAW_FORM = "r = a * p^n"

#: The unit an exponent is recorded in.
DIMENSIONLESS = "1"


def _text(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{what} must be a non-empty string, got {value!r}")
    return value


def _reported(value: object, what: str) -> ReportedValue:
    if not isinstance(value, ReportedValue):
        raise EvidenceError(
            f"{what} must be a reported value, got {value!r}. A burn-law regime with a "
            "missing limit or coefficient is not a law, and is not completed here.")
    return value


@dataclass(frozen=True, slots=True)
class BurnLawRegime:
    """One pressure regime of a piecewise law, exactly as the source prints it.

    Attributes:
        pressure_min, pressure_max: The regime's published pressure limits.
        a: The coefficient, in the law's rate unit for pressure in its pressure unit.
        n: The pressure exponent; any sign, as printed.
    """

    pressure_min: ReportedValue
    pressure_max: ReportedValue
    a: ReportedValue
    n: ReportedValue

    def __post_init__(self) -> None:
        for name in ("pressure_min", "pressure_max", "a", "n"):
            _reported(getattr(self, name), name)
        if self.pressure_min.unit != self.pressure_max.unit:
            raise EvidenceError(
                f"a regime's limits share one unit, got {self.pressure_min.unit!r} and "
                f"{self.pressure_max.unit!r}")
        if self.pressure_min.value < 0.0:
            raise EvidenceError(f"a pressure limit cannot be negative, got {self.pressure_min.value}")
        if not self.pressure_min.value < self.pressure_max.value:
            raise EvidenceError(
                f"a regime needs p_min < p_max, got {self.pressure_min.value} to "
                f"{self.pressure_max.value}")
        if not self.a.value > 0.0:
            raise EvidenceError(f"the coefficient a must be positive, got {self.a.value}")
        if self.n.unit != DIMENSIONLESS:
            raise EvidenceError(f"the exponent n is dimensionless (unit '1'), got {self.n.unit!r}")

    def reported_values(self) -> Iterator[ReportedValue]:
        yield from (self.pressure_min, self.pressure_max, self.a, self.n)


@dataclass(frozen=True, slots=True)
class BurnLawReference:
    """A published piecewise burn-rate law, ``r = a * p^n`` per regime.

    Attributes:
        law_id: Stable identifier.
        source_ids: The sources the law is taken from.
        propellant_name: What the source calls the propellant.
        form: :data:`BURN_LAW_FORM`; recorded so the file says which law it is.
        pressure_unit: The unit the source gives pressure in (``"MPa"``).
        rate_unit: The unit the source gives the burning rate in (``"mm/s"``).
        regimes: In ascending pressure order, non-overlapping.
        temperature: The test temperature, or Missing -- never a guessed number.
        uncertainty: The law's stated uncertainty, or Missing when none is given.
    """

    law_id: str
    source_ids: tuple[str, ...]
    propellant_name: str
    form: str
    pressure_unit: str
    rate_unit: str
    regimes: tuple[BurnLawRegime, ...]
    temperature: Datum
    uncertainty: Datum

    def __post_init__(self) -> None:
        for name in ("law_id", "propellant_name", "pressure_unit", "rate_unit"):
            _text(getattr(self, name), name)
        if not isinstance(self.source_ids, tuple) or not self.source_ids:
            raise EvidenceError("a burn law names at least one source")
        for sid in self.source_ids:
            _text(sid, "source id")
        if self.form != BURN_LAW_FORM:
            raise EvidenceError(f"the only law form is {BURN_LAW_FORM!r}, got {self.form!r}")
        if not isinstance(self.regimes, tuple) or not self.regimes:
            raise EvidenceError("a burn law needs at least one regime")
        for i, regime in enumerate(self.regimes):
            if not isinstance(regime, BurnLawRegime):
                raise EvidenceError(f"regime {i} must be a BurnLawRegime, got {regime!r}")
            if regime.pressure_min.unit != self.pressure_unit:
                raise EvidenceError(
                    f"regime {i}: limits are in {regime.pressure_min.unit!r}, the law in "
                    f"{self.pressure_unit!r}; nothing is converted")
            if regime.a.unit != self.rate_unit:
                raise EvidenceError(
                    f"regime {i}: a is in {regime.a.unit!r}, the law's rate in "
                    f"{self.rate_unit!r}; nothing is converted")
        for i, (low, high) in enumerate(zip(self.regimes, self.regimes[1:])):
            if high.pressure_min.value < low.pressure_max.value:
                raise EvidenceError(
                    f"regimes {i} and {i + 1} overlap or are out of order: "
                    f"{low.pressure_max.value} > {high.pressure_min.value}")
        for name in ("temperature", "uncertainty"):
            if not isinstance(getattr(self, name), (ReportedValue, Missing)):
                raise EvidenceError(f"{name} must be a ReportedValue or an explicit Missing")

    def reported_values(self) -> Iterator[ReportedValue]:
        for regime in self.regimes:
            yield from regime.reported_values()
        for datum in (self.temperature, self.uncertainty):
            if isinstance(datum, ReportedValue):
                yield datum

"""Evaluating a published burn-rate law inside its published domain, and nowhere else.

A :class:`~rocketforge.evidence.BurnLawReference` is evidence; this is the one
place a law is turned into a number. The rule is the source's, applied as
printed: ``r = a * p^n`` with the ``a`` and ``n`` of the regime that owns the
pressure, in the law's own units. Nothing is converted, fitted, interpolated,
clamped or extended.

Which regime owns a pressure is fixed, so the answer never depends on search
order:

* a regime owns ``p_min <= p < p_max``: where two regimes share an endpoint,
  the upper regime owns it;
* a regime's ``p_max`` that no other regime starts at is its own too -- the
  top of the published domain, or the edge of a gap -- so every published
  endpoint is evaluable, and by exactly one regime;
* anything else -- below the lowest limit, above the highest, inside a gap
  between regimes, not finite -- is refused with :class:`BurnLawDomainError`.

A law with a negative exponent is evaluated as printed; nothing assumes the
rate rises with pressure, within a regime or across regimes. A pressure of zero
under ``n <= 0`` has no finite rate and is refused.

Pure application code: it imports the evidence types and nothing that solves.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.core.errors import InputError
from rocketforge.evidence import BurnLawReference

__all__ = ["BurnLawDomainError", "BurnRate", "owning_regime", "evaluate", "domain_text"]


class BurnLawDomainError(InputError):
    """A pressure the published law does not cover. Refused, never approximated."""


@dataclass(frozen=True, slots=True)
class BurnRate:
    """One evaluation, labelled with everything it rests on.

    Attributes:
        rate: ``a * p^n``, in :attr:`rate_unit`.
        rate_unit: The law's rate unit, as the source prints it.
        pressure: The pressure evaluated, in :attr:`pressure_unit`.
        pressure_unit: The law's pressure unit, as the source prints it.
        regime_index: Which regime's coefficients were used (0-based).
        law_id: The law evaluated.
    """

    rate: float
    rate_unit: str
    pressure: float
    pressure_unit: str
    regime_index: int
    law_id: str


def domain_text(law: BurnLawReference) -> str:
    """The published domain, regime by regime, in the law's pressure unit."""
    return "; ".join(f"[{r.pressure_min.value}, {r.pressure_max.value}]"
                     for r in law.regimes) + f" {law.pressure_unit}"


def owning_regime(law: BurnLawReference, pressure: float) -> int:
    """The index of the regime that owns ``pressure``, or a refusal."""
    p = float(pressure)
    if not math.isfinite(p):
        raise BurnLawDomainError(f"{law.law_id}: pressure must be finite, got {pressure!r}")
    for i, regime in enumerate(law.regimes):
        if regime.pressure_min.value <= p < regime.pressure_max.value:
            return i
    starts = {regime.pressure_min.value for regime in law.regimes}
    for i, regime in enumerate(law.regimes):
        if p == regime.pressure_max.value and p not in starts:
            return i
    raise BurnLawDomainError(
        f"{law.law_id}: {p} {law.pressure_unit} is outside the published domain "
        f"({domain_text(law)}); the law is not extended, clamped or continued")


def evaluate(law: BurnLawReference, pressure: float) -> BurnRate:
    """``r = a * p^n`` for the owning regime, in the law's own units."""
    index = owning_regime(law, pressure)
    regime = law.regimes[index]
    p = float(pressure)
    a, n = regime.a.value, regime.n.value
    if p == 0.0 and n <= 0.0:
        raise BurnLawDomainError(
            f"{law.law_id}: at p = 0 the regime's exponent {n} gives no finite rate")
    return BurnRate(rate=a * p ** n, rate_unit=law.rate_unit, pressure=p,
                    pressure_unit=law.pressure_unit, regime_index=index, law_id=law.law_id)

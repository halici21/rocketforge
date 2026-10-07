"""One propellant branch's feed pressure budget: a ledger, not a feed system.

Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed.:

* section 10.4, Eq. 10-7 (p. 377): the pressure a branch supplies "has to
  equal the chamber pressure p1 modified by all the pressure drops" between it
  and the injector face -- "the pressure losses in the cooling jacket,
  injector, piping, and in the open fuel valve";
* section 11.5, Eqs. 11-6 and 11-7 (p. 423): for a pressurized branch, the
  available pressure must equal ``p1 + dp (piping, valves) + dp_inj +
  dp_j (cooling jacket) + 1/2 rho v^2 (dynamic flow head)``, less the static
  head ``L a rho``; "a good design should provide extra pressure drop margins"
  for calibration.

The ledger lists those terms, each with a status:

* **resolved** -- a stated or computed value, Pa (>= 0);
* **not applicable** -- declared absent by the user (for example, a branch
  that does not cool the chamber). It adds zero, and the declaration is kept;
* **unresolved** -- not known. It is never zero.

Two pressures follow. The **minimum known** pressure is the sum of the
resolved terms: every loss is non-negative, so the true requirement is at
least this. The **required** pressure is the same sum, reported only when no
term is unresolved.

The required pressure is at the branch's own reference point (a pump
discharge or a tank outlet, as the user's terms define), with no static-head
credit: ``L a rho`` depends on the liquid level and the flight acceleration,
which are not known here. Nothing here sizes a pump, a tank or a turbine, or
judges whether a pressure is achievable.

SI: Pa.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "BranchBudget",
    "BudgetTerm",
    "TermStatus",
    "branch_budget",
]


class TermStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_APPLICABLE = "not_applicable"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class BudgetTerm:
    """One ledger line.

    Attributes:
        key / label: Identity and name.
        status: See :class:`TermStatus`.
        value: Pa, only when resolved.
        source: Where a resolved value came from, or who declared it absent.
        reason: Why it is unresolved or not applicable.
    """

    key: str
    label: str
    status: TermStatus
    value: float | None = None
    source: str = ""
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.status, TermStatus):
            raise ValueError("a term's status must be a TermStatus")
        if (self.value is not None) != (self.status is TermStatus.RESOLVED):
            raise ValueError(f"{self.key}: a value exists exactly when the term is resolved")
        if self.value is not None and not (
                isinstance(self.value, (int, float)) and not isinstance(self.value, bool)
                and math.isfinite(self.value) and self.value >= 0.0):
            raise ValueError(f"{self.key}: a resolved term is finite and at or above zero")
        if self.status is not TermStatus.RESOLVED and not self.reason.strip():
            raise ValueError(f"{self.key}: an unresolved or absent term says why")

    @property
    def contribution(self) -> float:
        """Pa this term adds to the known sum: its value, or zero if absent."""
        return self.value if self.value is not None else 0.0


@dataclass(frozen=True, slots=True)
class BranchBudget:
    terms: tuple[BudgetTerm, ...]
    minimum_known_pressure: float
    required_pressure: float | None
    unresolved: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.required_pressure is not None


def branch_budget(terms: Sequence[BudgetTerm]) -> BranchBudget:
    """The ledger's sums. ``required_pressure`` only when nothing is unresolved."""
    terms = tuple(terms)
    keys = [t.key for t in terms]
    if len(set(keys)) != len(keys):
        raise ValueError(f"duplicate ledger terms in {keys}")
    known = math.fsum(t.contribution for t in terms)
    unresolved = tuple(t.key for t in terms if t.status is TermStatus.UNRESOLVED)
    return BranchBudget(terms=terms, minimum_known_pressure=known,
                        required_pressure=None if unresolved else known,
                        unresolved=unresolved)

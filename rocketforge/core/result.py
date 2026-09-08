"""The typed result model shared by every RocketForge solver.

Specified in ``docs/engineering/02_data_model_and_api_contracts.md`` sections
2.2 to 2.4. The governing idea is that a number alone is not a result: a
branched or iterative relation also has to say which branch it returned, how
well it converged, what it assumed, and whether the caller should be worried.
None of that fits in a float, and in a dictionary none of it is typed or
discoverable.

The two-tier rule from ADR-07 decides which functions use this:

* algebraic relations that are total on their domain return the bare number;
* anything branched, iterative or classified returns :class:`Solution`.

Phase 4B implements the parts the isentropic module needs. Serialisation
helpers (``02`` section 7) are not written yet, but the constraint that made
them possible is honoured: every field here is a float, int, str, bool, enum,
None, or a tuple of those.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Generic, Mapping, TypeVar

from .errors import RocketForgeError

__all__ = [
    "Status",
    "Severity",
    "Diagnostic",
    "Convergence",
    "Solution",
    "UnusableSolutionError",
]

T = TypeVar("T")


class Status(StrEnum):
    """How much trust the caller may place in :attr:`Solution.value`."""

    OK = "ok"
    """Converged or exact. The value is usable."""

    OK_WITH_WARNINGS = "warning"
    """Usable, but at least one diagnostic qualifies it."""

    NOT_CONVERGED = "not_converged"
    """The numerical method did not converge. The value is its best iterate."""

    NO_SOLUTION = "no_solution"
    """No solution exists for this input. ``value`` is None.

    This is not an error: asking for an attached shock beyond the maximum
    deflection, or for a Mach number past a thermal choking limit, is a
    meaningful engineering question whose answer is "there is none".
    """


class Severity(StrEnum):
    """How much attention a diagnostic deserves."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One machine-readable remark about a result.

    Diagnostics are data, never printed and never raised through
    ``warnings.warn``: the interface has to be able to render them, a report
    has to be able to list them, and a test has to be able to assert on them.

    Attributes:
        code: Stable, greppable identifier such as ``"NEAR_SONIC"``. Callers
            match on this, never on the message text.
        severity: See :class:`Severity`.
        message: One user-facing sentence.
        field: The input this concerns, where one input is responsible.
        detail: Numbers that make the message concrete, for a UI to format.
    """

    code: str
    severity: Severity
    message: str
    field: str | None = None
    detail: Mapping[str, float] | None = None


@dataclass(frozen=True, slots=True)
class Convergence:
    """What an iterative solver did to reach its answer.

    Populated for every iterative result and ``None`` for every closed-form
    one, so the two can never be confused. Built directly from the root
    solver's ``RootReport``.
    """

    converged: bool
    iterations: int
    residual: float
    tolerance: float
    bracket: tuple[float, float] | None
    method: str

    @classmethod
    def from_report(cls, report: object) -> "Convergence":
        """Build from a root solver's report.

        Takes the report structurally rather than by import: ``core.result``
        describes results and must not depend on any particular solver. Every
        relation that iterates uses this one mapping, so a report field can
        never be transcribed two different ways in two different modules.
        """
        return cls(
            converged=report.converged,
            iterations=report.iterations,
            residual=report.residual,
            tolerance=report.tolerance,
            bracket=report.bracket,
            method=report.method,
        )


class UnusableSolutionError(RocketForgeError):
    """:meth:`Solution.unwrap` was called on a result that is not usable."""


@dataclass(frozen=True, slots=True)
class Solution(Generic[T]):
    """A value together with everything needed to judge it.

    Attributes:
        value: The result, or None when :attr:`status` is
            :attr:`Status.NO_SOLUTION`.
        status: See :class:`Status`.
        diagnostics: Advisories, in the order they were raised.
        provenance: The relations used to produce this value, so a result can
            be traced to the equations behind it.
        convergence: Present for iterative results, None for closed-form ones.
        inputs: The inputs echoed back, for reports and reproducibility.
    """

    value: T | None
    status: Status
    diagnostics: tuple[Diagnostic, ...] = ()
    provenance: tuple[object, ...] = ()
    convergence: Convergence | None = None
    inputs: Mapping[str, float] | None = field(default=None)

    @property
    def ok(self) -> bool:
        """Whether the value may be used."""
        return self.status in (Status.OK, Status.OK_WITH_WARNINGS)

    def unwrap(self) -> T:
        """Return the value, or raise if it is not usable.

        The convenience a script or notebook wants: fail loudly rather than
        quietly propagating a non-converged iterate into a plot.
        """
        if not self.ok or self.value is None:
            raise UnusableSolutionError(
                f"solution is {self.status.value}: "
                + "; ".join(f"[{d.code}] {d.message}" for d in self.diagnostics)
            )
        return self.value

    def with_diagnostics(self, *added: Diagnostic) -> "Solution[T]":
        """A copy carrying additional diagnostics, escalating the status.

        Used to merge advisories that belong to an input -- a gas model outside
        the recommended gamma band, say -- into the result of the relation that
        used it. A warning never downgrades an error, and never upgrades a
        result that has no solution.
        """
        if not added:
            return self
        merged = self.diagnostics + added
        status = self.status
        if status is Status.OK and any(
            d.severity in (Severity.WARNING, Severity.ERROR) for d in added
        ):
            status = Status.OK_WITH_WARNINGS
        return Solution(
            value=self.value,
            status=status,
            diagnostics=merged,
            provenance=self.provenance,
            convergence=self.convergence,
            inputs=self.inputs,
        )

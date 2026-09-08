"""Traceability records for engineering relations.

``docs/engineering/01_engineering_architecture.md`` section 10 requires every
public relation family to be traceable to the equation behind it, the
assumptions that equation carries, and the source it came from, so that a
number displayed in the interface can always be explained.

Two levels, deliberately separated:

* :class:`RelationRef` is the lightweight reference a result carries. It holds
  identifiers and short fields only.
* :class:`EquationRecord` is the full record -- LaTeX, description, variables,
  domain -- and lives once in a per-module registry, looked up by identifier.

Results therefore reference the prose rather than copying it, which is what
stops a hundred results from carrying a hundred drifting copies of the same
assumption list.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["RelationRef", "VariableRef", "EquationRecord"]


@dataclass(frozen=True, slots=True)
class RelationRef:
    """A short, storable reference to one relation.

    Attributes:
        identifier: Stable dotted identifier, versioned, e.g.
            ``"isentropic.area_ratio.v1"``. Callers and stored studies match on
            this.
        name: Human-readable name, e.g. ``"Isentropic area-Mach relation"``.
        model: The physical model this belongs to, e.g.
            ``"perfect_gas_isentropic_v1"``. A change that alters a returned
            number for unchanged inputs requires a new model identifier.
        source: Authoritative source, at chapter or report level.
        assumptions: The conditions under which the relation is valid.
        domain: Human-readable statement of the admissible input range.
    """

    identifier: str
    name: str
    model: str
    source: str
    assumptions: tuple[str, ...]
    domain: str


@dataclass(frozen=True, slots=True)
class VariableRef:
    """One symbol appearing in an equation, and its name in code."""

    symbol: str
    name: str
    unit: str
    code_name: str


@dataclass(frozen=True, slots=True)
class EquationRecord:
    """The full description of one relation, for reference display.

    ``html`` exists alongside ``latex`` because the existing Equation Library
    page renders entity-based HTML; ``latex`` is for export and documentation.
    """

    identifier: str
    name: str
    group: str
    latex: str
    html: str
    description: str
    variables: tuple[VariableRef, ...]
    assumptions: tuple[str, ...]
    domain: str
    source: str
    related: tuple[str, ...] = ()

    def reference(self, model: str) -> RelationRef:
        """The lightweight reference a result should carry for this equation."""
        return RelationRef(
            identifier=self.identifier,
            name=self.name,
            model=model,
            source=self.source,
            assumptions=self.assumptions,
            domain=self.domain,
        )

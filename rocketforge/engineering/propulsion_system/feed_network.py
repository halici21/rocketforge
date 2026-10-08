"""A liquid feed line from tank outlet to injector inlet, as components in series.

Steady, single-phase, incompressible liquid at one density and viscosity,
one mass flow through every component (a series network conserves it). Each
component's static-pressure change, in the flow direction:

* **pipe** -- distributed friction, Darcy-Weisbach with the Darcy friction
  factor of :mod:`rocketforge.engineering.line` (64/Re laminar,
  Colebrook-White turbulent, none in the transition band):
  ``dp = f (L/D) rho v^2 / 2``, ``v = mdot / (rho pi D^2 / 4)``,
  ``Re = rho v D / mu``;
* **local loss** (fitting, bend, entrance), **valve**, **check valve** --
  ``dp = K rho v^2 / 2`` with ``K`` stated and referred to the velocity at the
  stated diameter. Only the resistance coefficient K is accepted: flow
  coefficients (Cv, Kv) come in several unit conventions and are not;
* **filter** and **explicit loss** -- a stated pressure drop;
* **static head** -- ``dp = rho a dz``: ``dz`` is the rise along the flow
  against the stated acceleration ``a`` (positive climbs, a loss; negative
  descends, a gain), Sutton 9th ed. Eqs. 11-6, 11-7's ``L a rho``;
* **velocity head** -- ``dp = rho v^2 / 2`` at the injector-inlet diameter:
  the liquid accelerated from rest in the tank (Sutton Eq. 11-6's dynamic
  flow head). Only as the last component;
* **unresolved** -- a component known to exist with no data. Its drop is
  unresolved, never zero.

The network's total is known only when no component is unresolved; the sum of
the resolved drops is always reported. Nothing is defaulted: no roughness,
K, diameter, length or viscosity.

Not modelled: two-phase flow, cavitation and NPSH, water hammer and
transients, valve dynamics, flexible lines, heat transfer, pumps, cooling
channels, parallel branches.

SI: kg/s, kg/m^3, Pa s, m, Pa, m/s^2.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.engineering.line import relations as line
from rocketforge.engineering.line.friction import colebrook_darcy_friction_factor
from rocketforge.engineering.line.types import FlowRegime, classify

__all__ = [
    "ComponentKind",
    "ComponentResult",
    "FeedBranch",
    "FeedComponent",
    "local_loss",
    "solve_feed_branch",
    "static_head",
]


class ComponentKind(StrEnum):
    PIPE = "pipe"
    LOCAL_LOSS = "local_loss"
    VALVE = "valve"
    CHECK_VALVE = "check_valve"
    FILTER = "filter"
    EXPLICIT_LOSS = "explicit_loss"
    STATIC_HEAD = "static_head"
    VELOCITY_HEAD = "velocity_head"
    UNRESOLVED = "unresolved"

    @property
    def coefficient(self) -> bool:
        return self in (ComponentKind.LOCAL_LOSS, ComponentKind.VALVE, ComponentKind.CHECK_VALVE)


#: Which inputs each kind states.
FIELDS: dict[ComponentKind, tuple[str, ...]] = {
    ComponentKind.PIPE: ("length", "diameter", "roughness"),
    ComponentKind.LOCAL_LOSS: ("loss_coefficient", "diameter"),
    ComponentKind.VALVE: ("loss_coefficient", "diameter"),
    ComponentKind.CHECK_VALVE: ("loss_coefficient", "diameter"),
    ComponentKind.FILTER: ("pressure_drop",),
    ComponentKind.EXPLICIT_LOSS: ("pressure_drop",),
    ComponentKind.STATIC_HEAD: ("rise", "acceleration"),
    ComponentKind.VELOCITY_HEAD: ("diameter",),
    ComponentKind.UNRESOLVED: (),
}
_ALL_FIELDS = ("length", "diameter", "roughness", "loss_coefficient", "pressure_drop", "rise",
               "acceleration")


@dataclass(frozen=True, slots=True)
class FeedComponent:
    """One component, with exactly the inputs its kind states."""

    kind: ComponentKind
    label: str = ""
    length: float | None = None
    diameter: float | None = None
    roughness: float | None = None
    loss_coefficient: float | None = None
    pressure_drop: float | None = None
    rise: float | None = None
    acceleration: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ComponentKind):
            raise ValueError("a component's kind must be a ComponentKind")
        wanted = set(FIELDS[self.kind])
        for name in _ALL_FIELDS:
            value = getattr(self, name)
            if (value is not None) != (name in wanted):
                raise ValueError(f"a {self.kind.value} " + ("states" if name in wanted
                                                            else "does not state") + f" {name}")


def _finite(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _domain(c: FeedComponent) -> str:
    """Why a component's stated inputs are out of their domain, or ''."""
    checks = {"length": lambda v: v > 0.0, "diameter": lambda v: v > 0.0,
              "roughness": lambda v: v >= 0.0, "loss_coefficient": lambda v: v >= 0.0,
              "pressure_drop": lambda v: v >= 0.0, "rise": lambda v: True,
              "acceleration": lambda v: v > 0.0}
    for name in FIELDS[c.kind]:
        value = getattr(c, name)
        if not (_finite(value) and checks[name](value)):
            return f"{name.replace('_', ' ')} of {value!r} is out of its domain"
    return ""


def local_loss(loss_coefficient: float, density: float, velocity: float) -> float:
    """``K rho v^2 / 2``."""
    return loss_coefficient * 0.5 * density * velocity * velocity


def static_head(density: float, acceleration: float, rise: float) -> float:
    """``rho a dz``: positive when the flow climbs against the acceleration."""
    return density * acceleration * rise


@dataclass(frozen=True, slots=True)
class ComponentResult:
    index: int
    kind: ComponentKind
    label: str
    status: str                  # "resolved" | "unresolved"
    pressure_change: float | None    # Pa, the static-pressure drop (negative: a gain)
    velocity: float | None
    reynolds: float | None
    friction_factor: float | None
    regime: str
    continuity_closure: float | None     # rho v A / mdot - 1
    reason: str


@dataclass(frozen=True, slots=True)
class FeedBranch:
    mass_flow: float
    density: float
    viscosity: float | None
    components: tuple[ComponentResult, ...]
    known_drop: float            # sum of the resolved drops
    total_drop: float | None     # only when none is unresolved
    unresolved: tuple[int, ...]
    max_continuity_closure: float


def _refuse(code: str, message: str, field: str) -> Solution:
    return Solution(value=None, status=Status.NO_SOLUTION,
                    diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                            message=message, field=field),))


def _component(i: int, c: FeedComponent, mdot: float, rho: float, mu: float | None
               ) -> ComponentResult:
    def done(dp, v=None, re=None, f=None, regime="", reason="") -> ComponentResult:
        closure = None
        if v is not None:
            closure = rho * v * line.circular_area(c.diameter) / mdot - 1.0
        return ComponentResult(i, c.kind, c.label, "resolved" if dp is not None else
                               "unresolved", dp, v, re, f, regime, closure, reason)

    if c.kind is ComponentKind.UNRESOLVED:
        return done(None, reason="Declared without data; not assumed to be zero.")
    if c.kind in (ComponentKind.FILTER, ComponentKind.EXPLICIT_LOSS):
        return done(float(c.pressure_drop))
    if c.kind is ComponentKind.STATIC_HEAD:
        return done(static_head(rho, c.acceleration, c.rise))
    v = line.mean_velocity(mdot, rho, c.diameter)
    if c.kind.coefficient:
        return done(local_loss(c.loss_coefficient, rho, v), v)
    if c.kind is ComponentKind.VELOCITY_HEAD:
        return done(line.dynamic_pressure(rho, v), v)
    # Pipe.
    if mu is None:
        return done(None, v, reason="No viscosity is stated, so the Reynolds number and the "
                    "friction factor are unknown.")
    re = line.reynolds_number(rho, v, c.diameter, mu)
    regime = classify(re)
    if regime is FlowRegime.TRANSITIONAL:
        return done(None, v, re, regime=regime.value,
                    reason=f"Re = {re:.6g} is in the transition band: no friction factor is "
                           "reported (engineering.line).")
    if regime is FlowRegime.LAMINAR:
        f = line.laminar_darcy_friction_factor(re)
    else:
        try:
            f, report = colebrook_darcy_friction_factor(
                re, line.relative_roughness(c.roughness, c.diameter))
        except Exception as error:  # noqa: BLE001 -- a domain refusal is an answer
            return done(None, v, re, regime=regime.value, reason=str(error))
        if not report.converged:
            return done(None, v, re, regime=regime.value,
                        reason="The Colebrook-White solve did not converge.")
    return done(line.darcy_weisbach_pressure_drop(f, c.length, c.diameter, rho, v), v, re, f,
                regime.value)


def solve_feed_branch(mass_flow: float, density: float, viscosity: float | None,
                      components: Sequence[FeedComponent]) -> Solution[FeedBranch]:
    """Every component's pressure change and the series total."""
    if not (_finite(mass_flow) and mass_flow > 0.0):
        return _refuse("MASS_FLOW_INVALID", "The mass flow must be finite and above zero.",
                       "mass_flow")
    if not (_finite(density) and density > 0.0):
        return _refuse("DENSITY_INVALID", "The liquid density must be finite and above zero.",
                       "density")
    if viscosity is not None and not (_finite(viscosity) and viscosity > 0.0):
        return _refuse("VISCOSITY_INVALID", "The viscosity must be finite and above zero.",
                       "viscosity")
    components = tuple(components)
    if not components:
        return _refuse("NETWORK_EMPTY", "The network has no component: state at least one, "
                       "or an unresolved one.", "components")
    heads = [i for i, c in enumerate(components) if c.kind is ComponentKind.VELOCITY_HEAD]
    if heads and heads != [len(components) - 1]:
        return _refuse("TOPOLOGY_INVALID", "The velocity head is the injector-inlet boundary: "
                       "at most one, and only as the last component.", "components")
    for i, c in enumerate(components):
        why = _domain(c)
        if why:
            return _refuse("COMPONENT_INVALID", f"Component {i + 1} ({c.kind.value}): {why}.",
                           "components")
    mdot, rho = float(mass_flow), float(density)
    results = tuple(_component(i, c, mdot, rho, viscosity) for i, c in enumerate(components))
    unresolved = tuple(r.index for r in results if r.pressure_change is None)
    known = math.fsum(r.pressure_change for r in results if r.pressure_change is not None)
    closures = [abs(r.continuity_closure) for r in results if r.continuity_closure is not None]
    return Solution(value=FeedBranch(
        mass_flow=mdot, density=rho, viscosity=viscosity, components=results,
        known_drop=known, total_drop=None if unresolved else known, unresolved=unresolved,
        max_continuity_closure=max(closures, default=0.0)), status=Status.OK,
        provenance=("engineering.line Darcy friction factor; K ρv²/2; ρ a Δz (Sutton 9th ed. "
                    "Eqs. 11-6, 11-7)",))

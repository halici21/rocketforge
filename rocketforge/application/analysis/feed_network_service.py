"""Liquid propellant feed network (SYS-5): resolve, compute, present. Qt-free.

The inputs are a current SYS-4 pressurization study and the current LIQ-6
injector study on the same sizing::

    SYS-4 pressurization  --(tank pressure: regulated, or blowdown start/end)--> FeedBasis
    LIQ-6 injector        --(mdot, density at the inlet, pressure ledger)
    stated per branch: components in series, density source, viscosity,        FeedDefinition
                       carried/replaced for the dynamic-head and "other" terms
        engineering.propulsion_system.feed_network.solve_feed_branch              once per branch

**Closure, without double counting.** The injector inlet needs the LIQ-6 terms
that lie downstream of it -- chamber pressure, injector drop, cooling-jacket
loss, margin, and the dynamic-head and "other" terms the user carries. The
feed-line and valve terms are the span the network models and are never
counted from LIQ-6. The tank outlet then needs the inlet requirement plus the
network's drop, and each SYS-4 tank pressure is compared with that.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from rocketforge.engine.injector import Branch as InjectorBranch
from rocketforge.engine.injector import InjectorResult
from rocketforge.engine.propulsion_system.feed_network import (
    CARRIED_TERMS,
    CHOSEN_TERMS,
    FEED_BRANCH_QUANTITIES,
    FEED_SCHEMA,
    REPLACED_TERMS,
    ComponentSpec,
    DensitySource,
    FeedBasis,
    FeedBranchBasis,
    FeedBranchDefinition,
    FeedDefinition,
    LedgerTerm,
    TermAssignment,
)
from rocketforge.engine.propulsion_system.records import (
    Branch,
    BranchOutcome,
    LedgerLine,
    StudyResult,
    Upstream,
)
from rocketforge.engine.propulsion_system.records import StudyStatus as S

from . import system_presentation as present

__all__ = [
    "ASSUMPTIONS",
    "COMPONENT_FIELDS",
    "COMPONENT_KINDS",
    "BranchSettings",
    "FeedIssue",
    "build_definition",
    "feed_basis",
    "solve_feed_network",
]

#: The kinds a user can add, with their label and the fields each states.
COMPONENT_KINDS: tuple[tuple[str, str], ...] = (
    ("pipe", "Pipe"), ("local_loss", "Local loss (K)"), ("valve", "Valve (K)"),
    ("check_valve", "Check valve (K)"), ("filter", "Filter (Δp)"),
    ("explicit_loss", "Explicit loss (Δp)"), ("static_head", "Static head"),
    ("velocity_head", "Velocity head at the inlet"), ("unresolved", "Unresolved component"),
)
COMPONENT_FIELDS: dict[str, tuple[str, ...]] = {
    "pipe": ("length", "diameter", "roughness"),
    "local_loss": ("loss_coefficient", "diameter"),
    "valve": ("loss_coefficient", "diameter"),
    "check_valve": ("loss_coefficient", "diameter"),
    "filter": ("pressure_drop",), "explicit_loss": ("pressure_drop",),
    "static_head": ("rise", "acceleration"), "velocity_head": ("diameter",),
    "unresolved": (),
}


@dataclass(frozen=True, slots=True)
class BranchSettings:
    """What the user states for one branch. ``components`` are (kind, values)."""

    density_source: DensitySource | None = None
    density: float | None = None                    # kg/m^3, when stated
    viscosity: float | None = None                  # Pa s
    components: tuple[tuple[str, tuple[tuple[str, float | None], ...]], ...] = ()
    assignments: dict[str, TermAssignment | None] = field(
        default_factory=lambda: {key: None for key in CHOSEN_TERMS})


@dataclass(frozen=True, slots=True)
class FeedIssue:
    code: str
    field: str
    message: str


def _tank_pressures(pressurization: StudyResult, branch: Branch) -> tuple[dict, str]:
    b = pressurization.branch(branch)
    mode = b.labels.get("mode", "")
    if b.value("tank_pressure") is not None:
        return {"regulated": b.value("tank_pressure")}, mode
    if b.value("initial_pressure") is not None and b.value("final_pressure") is not None:
        return {"start": b.value("initial_pressure"), "end": b.value("final_pressure")}, mode
    return {}, mode


def feed_basis(pressurization: StudyResult | None, pressurization_stale: bool,
               injector: InjectorResult | None, injector_stale: bool
               ) -> tuple[FeedBasis | None, tuple[FeedIssue, ...]]:
    """The tank pressures and the injector requirement, current and coherent, or why not."""
    def refuse(code: str, field_name: str, message: str):
        return None, (FeedIssue(code, field_name, message),)

    if pressurization is None:
        return refuse("NO_PRESSURIZATION", "pressurization", "No tank-pressurization study "
                      "has been computed. Compute it on the Tank Pressurization page.")
    if pressurization_stale:
        return refuse("PRESSURIZATION_STALE", "pressurization", "The tank-pressurization "
                      "study is stale. Compute it again.")
    if not pressurization.ok:
        return refuse("PRESSURIZATION_REFUSED", "pressurization",
                      "The tank-pressurization study was refused.")
    if injector is None:
        return refuse("NO_INJECTOR", "injector", "No injector study has been computed. "
                      "Compute it on the Injector & Feed Pressure page.")
    if injector_stale:
        return refuse("INJECTOR_STALE", "injector", "The injector study is stale. Compute it "
                      "again.")
    if not injector.ok:
        return refuse("INJECTOR_REFUSED", "injector", "The injector study was refused.")
    p = pressurization.definition.basis
    if injector.definition.basis.sizing_fingerprint != p.sizing_fingerprint:
        return refuse("INJECTOR_MISMATCH", "injector", "The injector study is for a different "
                      "sizing than the propulsion-system chain. Compute it again.")

    def branch_basis(branch: Branch) -> FeedBranchBasis:
        ib = injector.branch(InjectorBranch(branch.value))
        pressures, mode = _tank_pressures(pressurization, branch)
        return FeedBranchBasis(
            mass_flow=ib.value("mass_flow"), injector_density=ib.value("density"),
            ledger=tuple(LedgerTerm(line.key, line.label, line.status, line.value)
                         for line in ib.ledger),
            tank_pressures=pressures, pressurization_mode=mode)

    return FeedBasis(
        pressurization=Upstream("SYS-4", pressurization.definition.fingerprint,
                                pressurization.status.value),
        injector=Upstream("LIQ-6", injector.definition.fingerprint, injector.status.value),
        sizing_fingerprint=p.sizing_fingerprint, pair_label=p.pair_label,
        oxidiser=p.oxidiser, fuel=p.fuel,
        oxidiser_basis=branch_basis(Branch.OXIDISER),
        fuel_basis=branch_basis(Branch.FUEL)), ()


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _branch_definition(branch: Branch, basis: FeedBasis, s: BranchSettings
                       ) -> tuple[FeedBranchDefinition | None, list[FeedIssue]]:
    name = branch.value
    word = "oxidiser" if branch is Branch.OXIDISER else "fuel"
    issues: list[FeedIssue] = []
    if s.density_source is None:
        issues.append(FeedIssue("DENSITY_SOURCE_UNRESOLVED", f"{name}.density_source",
                                f"State the {word} liquid density source."))
    elif s.density_source is DensitySource.STATED and not (_finite(s.density)
                                                           and s.density > 0.0):
        issues.append(FeedIssue("DENSITY_INVALID" if s.density is not None
                                else "DENSITY_UNRESOLVED", f"{name}.density",
                                f"State the {word} liquid density, above zero."))
    if s.viscosity is not None and not (_finite(s.viscosity) and s.viscosity > 0.0):
        issues.append(FeedIssue("VISCOSITY_INVALID", f"{name}.viscosity",
                                f"The {word} viscosity must be finite and above zero."))
    if not s.components:
        issues.append(FeedIssue("NETWORK_EMPTY", f"{name}.components",
                                f"Add the {word} feed components, from tank outlet to injector "
                                "inlet. An unknown one can be added as unresolved."))
    specs = []
    for i, (kind, values) in enumerate(s.components):
        given = dict(values)
        for field_name in COMPONENT_FIELDS[kind]:
            if given.get(field_name) is None:
                issues.append(FeedIssue("COMPONENT_UNRESOLVED", f"{name}.c{i}.{field_name}",
                                        f"State the {word} component {i + 1}'s "
                                        f"{field_name.replace('_', ' ')}, or make it an "
                                        "unresolved component."))
        specs.append(ComponentSpec(kind, dict(COMPONENT_KINDS)[kind],
                                   **{k: given.get(k) for k in COMPONENT_FIELDS[kind]}))
    if any(k == "pipe" for k, _v in s.components) and s.viscosity is None:
        issues.append(FeedIssue("VISCOSITY_UNRESOLVED", f"{name}.viscosity",
                                f"State the {word} viscosity: a pipe's friction factor needs "
                                "it. None is assumed."))
    for key in CHOSEN_TERMS:
        if s.assignments.get(key) is None:
            issues.append(FeedIssue("ASSIGNMENT_UNRESOLVED", f"{name}.{key}",
                                    f"State whether the {word} LIQ-6 "
                                    f"{key.replace('_', ' ')} term is carried at the injector "
                                    "inlet or replaced by the network. Neither is assumed, so "
                                    "nothing is counted twice."))
    if (s.assignments.get("dynamic_head") is TermAssignment.CARRIED
            and any(k == "velocity_head" for k, _v in s.components)):
        issues.append(FeedIssue("DOUBLE_COUNTED", f"{name}.dynamic_head",
                                f"The {word} dynamic head is carried from LIQ-6 and also "
                                "modelled as a velocity-head component: ρv²/2 would be counted "
                                "twice. Replace the LIQ-6 term or remove the component."))
    if issues:
        return None, issues
    density = (basis.of(branch).injector_density if s.density_source is DensitySource.INJECTOR
               else float(s.density))
    return FeedBranchDefinition(branch, s.density_source, density, s.viscosity, tuple(specs),
                                {k: s.assignments[k] for k in CHOSEN_TERMS}), []


def build_definition(basis: FeedBasis | None, oxidiser: BranchSettings, fuel: BranchSettings
                     ) -> tuple[FeedDefinition | None, tuple[FeedIssue, ...]]:
    if basis is None:
        return None, ()
    ox, ox_issues = _branch_definition(Branch.OXIDISER, basis, oxidiser)
    fu, fu_issues = _branch_definition(Branch.FUEL, basis, fuel)
    if ox is None or fu is None:
        return None, tuple(ox_issues + fu_issues)
    return FeedDefinition(basis, ox, fu), ()


ASSUMPTIONS: tuple[str, ...] = (
    "Steady, single-phase, incompressible liquid at one density and viscosity; one mass "
    "flow through every component in series (continuity checked per component).",
    "Pipes: Darcy-Weisbach with the Darcy friction factor of engineering.line (64/Re "
    "laminar, Colebrook-White turbulent, none reported in the transition band 2300–4000).",
    "Local losses, valves and check valves: Δp = K ρ v²/2 with K stated and referred to the "
    "velocity at the stated diameter. Flow coefficients (Cv, Kv) are not accepted.",
    "Static head: Δp = ρ a Δz, Δz the rise along the flow against the stated acceleration "
    "(Sutton 9th ed. Eqs. 11-6, 11-7). Velocity head: ρ v²/2 at the injector inlet, the "
    "liquid accelerated from rest in the tank.",
    "Without double counting: LIQ-6's feed-line and valve terms are replaced by the network "
    "and not counted. Chamber pressure, injector drop, cooling-jacket loss and margin are "
    "carried at the injector inlet; the dynamic-head and other terms as stated.",
    "The tank outlet's static pressure is the SYS-4 tank pressure; the liquid column in the "
    "tank is credited only through a stated static-head component. Blowdown is checked at "
    "its start and end pressures at the design flow; the flow decay is not modelled.",
    "Not modelled: two-phase flow, cavitation and NPSH, water hammer and transients, valve "
    "dynamics, flexible lines, thermal coupling, pumps, cooling-channel hydraulics, "
    "parallel branches.",
)


def _carried(d: FeedBranchDefinition, b: FeedBranchBasis
             ) -> tuple[list[LedgerLine], float, list[str], dict[str, float]]:
    lines: list[LedgerLine] = []
    unresolved: list[str] = []
    known = 0.0
    liq6: dict[str, float] = {}
    for term in b.ledger:
        assigned = (TermAssignment.CARRIED if term.key in CARRIED_TERMS else
                    TermAssignment.REPLACED if term.key in REPLACED_TERMS else
                    d.assignments[term.key])
        if term.value is not None:
            liq6[term.key] = term.value
        if assigned is TermAssignment.REPLACED:
            was = (f"LIQ-6 stated {term.value / 1e5:.4g} bar" if term.value is not None
                   else f"LIQ-6 had it {term.status.replace('_', ' ')}")
            lines.append(LedgerLine(f"liq6_{term.key}", term.label, "excluded", None, "Pa",
                                    "LIQ-6 ledger", f"Replaced by the network ({was}); "
                                    "not counted here."))
        elif term.status == "resolved":
            known += term.value
            lines.append(LedgerLine(f"liq6_{term.key}", term.label, "resolved", term.value,
                                    "Pa", "LIQ-6 ledger, carried at the injector inlet"))
        elif term.status == "not_applicable":
            lines.append(LedgerLine(f"liq6_{term.key}", term.label, "not_applicable", None,
                                    "Pa", "LIQ-6 ledger", "Declared not applicable in LIQ-6"))
        else:
            unresolved.append(term.label.lower())
            lines.append(LedgerLine(f"liq6_{term.key}", term.label, "unresolved", None, "Pa",
                                    "LIQ-6 ledger", "Unresolved in LIQ-6; not zero"))
    return lines, known, unresolved, liq6


def _component_source(r) -> str:
    parts = []
    if r.velocity is not None:
        parts.append(f"v = {r.velocity:.4g} m/s")
    if r.reynolds is not None:
        parts.append(f"Re = {r.reynolds:.4g}")
    if r.friction_factor is not None:
        parts.append(f"f_D = {r.friction_factor:.5g}")
    if r.regime:
        parts.append(r.regime)
    return ", ".join(parts)


def _solve_branch(d: FeedBranchDefinition, basis: FeedBasis) -> BranchOutcome:
    from rocketforge.engineering.propulsion_system import feed_network as rel

    b = basis.of(d.branch)
    word = d.branch.value.capitalize()
    labels = {"pressurization": b.pressurization_mode or "—",
              "density_source": ("LIQ-6 injector-inlet density"
                                 if d.density_source is DensitySource.INJECTOR else "Stated")}
    components = [rel.FeedComponent(rel.ComponentKind(c.kind), c.label,
                                    **{k: getattr(c, k) for k in COMPONENT_FIELDS[c.kind]})
                  for c in d.components]
    solution = rel.solve_feed_branch(b.mass_flow, d.density, d.viscosity, components)
    if solution.value is None:
        message = f"{word}: {solution.diagnostics[0].message}"
        return BranchOutcome(branch=d.branch, status=S.REFUSED,
                             unresolved={q.key: message for q in FEED_BRANCH_QUANTITIES},
                             labels=labels, message=message)
    net = solution.value
    q = {"mass_flow": b.mass_flow, "density": d.density,
         "component_count": float(len(net.components)),
         "network_known_drop": net.known_drop,
         "max_continuity_closure": net.max_continuity_closure}
    unresolved: dict[str, str] = {}
    if d.viscosity is None:
        unresolved["viscosity"] = "Not stated; no pipe needs it."
    else:
        q["viscosity"] = d.viscosity
    ledger = [LedgerLine(f"c{r.index}", f"{r.index + 1}. {r.label}", r.status,
                         r.pressure_change, "Pa", _component_source(r), r.reason)
              for r in net.components]
    carried, inlet_known, carried_unresolved, liq6 = _carried(d, b)
    ledger += carried
    if net.total_drop is None:
        unresolved["network_drop"] = (f"Waits on {len(net.unresolved)} unresolved "
                                      "component(s).")
    else:
        q["network_drop"] = net.total_drop
    if carried_unresolved:
        unresolved["inlet_required"] = ("Waits on LIQ-6 terms unresolved there: "
                                        + ", ".join(carried_unresolved) + ".")
    else:
        q["inlet_required"] = inlet_known
    tank_required = (None if net.total_drop is None or carried_unresolved
                     else inlet_known + net.total_drop)
    why = unresolved.get("network_drop") or unresolved.get("inlet_required", "")
    if tank_required is None:
        unresolved["tank_required"] = why
    else:
        q["tank_required"] = tank_required
    liq6_required = math.fsum(liq6.values()) if all(
        t.status != "unresolved" for t in b.ledger) else None
    if liq6_required is None:
        unresolved["liq6_required"] = "LIQ-6's own ledger is incomplete."
    else:
        q["liq6_required"] = liq6_required
    margins: list[float] = []
    closures: list[float] = []
    names = {"regulated": "regulated", "start": "start", "end": "end"}
    for key, word_key in names.items():
        pressure_key, margin_key = f"tank_pressure_{word_key}", f"margin_{word_key}"
        if key not in b.tank_pressures:
            unresolved[pressure_key] = unresolved[margin_key] = (
                "Not this branch's pressurization mode." if b.tank_pressures else
                "SYS-4 gives no tank pressure for this branch (intent only).")
            continue
        p_tank = b.tank_pressures[key]
        q[pressure_key] = p_tank
        if tank_required is None:
            unresolved[margin_key] = why
            continue
        margin = p_tank - tank_required
        q[margin_key] = margin
        margins.append(margin)
        closures.append(((p_tank - net.total_drop) - inlet_known - margin) / p_tank)
    if closures:
        q["pressure_closure"] = max(closures, key=abs)
    else:
        unresolved["pressure_closure"] = why or "No tank pressure to close against."
    first = next(iter(b.tank_pressures.values()), None)
    series: list[dict[str, float]] = []
    if first is not None:
        cumulative = 0.0
        for r in net.components:
            if r.pressure_change is None:
                break
            cumulative += r.pressure_change
            series.append({"component": float(r.index + 1), "cumulative": cumulative,
                           "pressure": first - cumulative})
    notes: list[str] = []
    if margins and min(margins) < 0.0:
        labels["feed_check"] = "INSUFFICIENT: the tank pressure is below the requirement"
        notes.append(f"{word}: the tank pressure falls short of the required tank-outlet "
                     f"pressure by {-min(margins) / 1e5:.4g} bar.")
        status = S.WARNING
    elif margins and len(margins) == len(b.tank_pressures):
        labels["feed_check"] = "At or above the required tank-outlet pressure"
        status = S.OK
    else:
        labels["feed_check"] = "UNRESOLVED"
        status = S.INCOMPLETE
    return BranchOutcome(branch=d.branch, status=status, quantities=q, unresolved=unresolved,
                         labels=labels, ledger=tuple(ledger), series=tuple(series),
                         notes=tuple(notes))


def solve_feed_network(definition: FeedDefinition) -> StudyResult:
    """Both branches. Never raises for a stated input."""
    ox = _solve_branch(definition.oxidiser, definition.basis)
    fu = _solve_branch(definition.fuel, definition.basis)
    if not (ox.ok and fu.ok):
        status = S.REFUSED
        message = " ".join(m for m in (ox.message, fu.message) if m)
    else:
        statuses = (ox.status, fu.status)
        status = (S.WARNING if S.WARNING in statuses else
                  S.INCOMPLETE if S.INCOMPLETE in statuses else S.OK)
        message = ""
    return StudyResult(schema=FEED_SCHEMA, definition=definition, status=status, oxidiser=ox,
                       fuel=fu, message=message, assumptions=ASSUMPTIONS,
                       provenance=provenance(definition))


def provenance(definition: FeedDefinition) -> dict[str, str]:
    basis = definition.basis
    return {
        "network": "RocketForge engineering.propulsion_system.feed_network over "
                   "engineering.line (Darcy-Weisbach, Colebrook-White); K ρv²/2; ρ a Δz",
        "pressurization": f"SYS-4 pressurization {basis.pressurization.fingerprint[:12]}",
        "injector": f"LIQ-6 injector {basis.injector.fingerprint[:12]}",
        "sizing": f"LIQ-4 sizing {basis.sizing_fingerprint[:12]}",
    }


DISPLAY: dict[str, tuple[str, float, str]] = {
    "mass_flow": ("kg/s", 1.0, ",.5g"),
    "density": ("kg/m³", 1.0, ",.3f"),
    "viscosity": ("mPa·s", 1.0e3, ",.5g"),
    "component_count": ("", 1.0, ".0f"),
    **{k: ("bar", 1.0e-5, ",.4f") for k in (
        "network_known_drop", "network_drop", "inlet_required", "tank_required",
        "liq6_required", "tank_pressure_regulated", "margin_regulated", "tank_pressure_start",
        "margin_start", "tank_pressure_end", "margin_end")},
    "max_continuity_closure": ("", 1.0, ".1e"),
    "pressure_closure": ("", 1.0, ".1e"),
}

GROUPS = (("flow", "Liquid"), ("network", "Network"), ("closure", "Pressure closure"))
LABELS = (("pressurization", "Pressurization"), ("density_source", "Density"),
          ("feed_check", "Feed check"))
SERIES = (("component", "After component", 1.0, ".0f"),
          ("cumulative", "Cumulative Δp bar", 1.0e-5, ",.4f"),
          ("pressure", "Pressure bar", 1.0e-5, ",.4f"))


def branch_view(outcome: BranchOutcome) -> dict:
    view = {"groups": present.branch_groups(outcome, FEED_BRANCH_QUANTITIES, GROUPS, DISPLAY),
            "labels": present.label_rows(outcome, LABELS),
            "ledger": present.ledger_rows(outcome)}
    if outcome.series:
        view["series"] = present.series_rows(outcome, SERIES)
    return view

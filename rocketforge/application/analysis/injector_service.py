"""Injector hydraulics and feed pressure budget (LIQ-6): resolve, compute, present. Qt-free.

The input is an accepted LIQ-4 sizing, read as LIQ-4 produced it::

    accepted LIQ-4 sizing  --(mdot_o, mdot_f, O/F, p1, T, identity)-->  FlowBasis
    stated per branch: dp_inj, Cd, density or its source, holes, terms   InjectorDefinition
        engineering.injector.orifice_sizing / holes_* / dynamic_head      the relations, once
        engineering.injector.branch_budget                                 the ledger, once

**Nothing is resolved silently.** :func:`flow_basis` refuses a missing, stale,
refused or incomplete sizing. :func:`build_definition` refuses a study until
every hydraulic input of both branches is stated: Cd, density and dp have no
default. Pressure terms may stay unresolved; they then stay unresolved in the
ledger, and the branch has a minimum known pressure but no required pressure.

**Density.** Either stated, or from the validated fluid-property model --
only for a propellant with a validated binding (LOX, LCH4, LH2), at the
stream temperature LIQ-3 evaluated and at the injector inlet pressure,
chamber pressure + dp. The CEA chamber state is never a source of liquid
density. The model is reached only by :func:`solve_injector`, which runs only
on the user's Compute action.

No thermochemistry provider is reached. Nothing here evaluates atomization,
combustion efficiency or combustion stability, or judges a pressure
achievable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from rocketforge.engine.chamber_sizing import SizingResult
from rocketforge.engine.injector import (
    BRANCH_QUANTITIES,
    LOSS_TERMS,
    PAIR_QUANTITIES,
    Branch,
    BranchDefinition,
    BranchResult,
    DensitySource,
    FlowBasis,
    HoleMode,
    InjectorDefinition,
    InjectorResult,
    InjectorStatus,
    LedgerLine,
    LossMode,
    LossSetting,
)
from rocketforge.engineering.propellants import PRODUCTION_FLUID_MAPPING

__all__ = [
    "ASSUMPTIONS",
    "BranchSettings",
    "DISPLAY",
    "InjectorIssue",
    "branch_groups",
    "build_definition",
    "display_value",
    "fluid_model_supported",
    "flow_basis",
    "ledger_rows",
    "pair_rows",
    "provenance",
    "solve_injector",
]


@dataclass(frozen=True, slots=True)
class BranchSettings:
    """What the user states for one branch, SI. Every hydraulic value starts
    unset; every pressure term starts unresolved."""

    pressure_drop: float | None = None              # Pa
    discharge_coefficient: float | None = None
    density_source: DensitySource = DensitySource.STATED
    density: float | None = None                    # kg/m^3
    hole_mode: HoleMode = HoleMode.AREA
    hole_count: float | None = None                 # a whole number, held as typed
    hole_diameter: float | None = None              # m
    loss_modes: dict[str, LossMode] = field(
        default_factory=lambda: {key: LossMode.UNRESOLVED for key, _l, _b in LOSS_TERMS})
    loss_values: dict[str, float | None] = field(
        default_factory=lambda: {key: None for key, _l, _b in LOSS_TERMS})


@dataclass(frozen=True, slots=True)
class InjectorIssue:
    code: str
    field: str
    message: str


# ---------------------------------------------------------------------------
# the flows, from an accepted sizing
# ---------------------------------------------------------------------------


def flow_basis(sizing: SizingResult | None, stale: bool
               ) -> tuple[FlowBasis | None, tuple[InjectorIssue, ...]]:
    """The flows of an accepted, current LIQ-4 sizing, or why there are none."""
    if sizing is None:
        return None, (InjectorIssue("NO_SIZING", "sizing",
                                    "No thrust-chamber sizing has been run. Size one on the "
                                    "Thrust Chamber Sizing page."),)
    if stale:
        return None, (InjectorIssue("SIZING_STALE", "sizing",
                                    "The thrust-chamber sizing is stale: the trade selection "
                                    "or its nozzle changed since it ran. Size again."),)
    if not sizing.ok:
        return None, (InjectorIssue("SIZING_REFUSED", "sizing",
                                    "The thrust-chamber sizing was refused, so there are no "
                                    "propellant flows to inject."),)
    flows = [sizing.value(k) for k in ("mass_flow", "oxidiser_mass_flow", "fuel_mass_flow")]
    if any(v is None for v in flows):
        return None, (InjectorIssue("SIZING_INCOMPLETE", "sizing",
                                    "The thrust-chamber sizing carries no propellant flows."),)
    definition = sizing.definition
    point = definition.point
    return FlowBasis(
        sizing_fingerprint=definition.fingerprint,
        sizing_status=sizing.status.value,
        sizing_provenance=dict(sizing.provenance),
        trade_fingerprint=point.trade_fingerprint,
        pair_key=point.pair_key, pair_label=point.pair_label,
        oxidiser=point.oxidiser, fuel=point.fuel,
        oxidiser_fuel_ratio=point.oxidiser_fuel_ratio,
        chamber_pressure=point.chamber_pressure,
        oxidiser_temperature=point.oxidiser_temperature,
        fuel_temperature=point.fuel_temperature,
        mass_flow=flows[0], oxidiser_mass_flow=flows[1], fuel_mass_flow=flows[2],
        thrust=point.thrust,
    ), ()


#: Propellants with a validated fluid-model binding, read once from the table.
_FLUID_MODEL_PROPELLANTS = frozenset(PRODUCTION_FLUID_MAPPING.bindings)


def fluid_model_supported(propellant: str) -> bool:
    """Whether a validated fluid-model binding exists. A set lookup: it reaches
    no provider and no lower-layer function, so a page may ask while browsing."""
    return propellant in _FLUID_MODEL_PROPELLANTS


# ---------------------------------------------------------------------------
# the definition
# ---------------------------------------------------------------------------


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _branch_definition(branch: Branch, basis: FlowBasis, s: BranchSettings
                       ) -> tuple[BranchDefinition | None, list[InjectorIssue]]:
    name = branch.value
    word = "oxidiser" if branch is Branch.OXIDISER else "fuel"
    issues: list[InjectorIssue] = []

    def need(field_name: str, code: str, value, missing: str, valid, invalid: str) -> None:
        if value is None:
            issues.append(InjectorIssue(f"{code}_UNRESOLVED", f"{name}.{field_name}", missing))
        elif not (_finite(value) and valid(value)):
            issues.append(InjectorIssue(f"{code}_INVALID", f"{name}.{field_name}", invalid))

    need("pressure_drop", "PRESSURE_DROP", s.pressure_drop,
         f"State the {word} injector pressure drop. No default is assumed.",
         lambda v: v > 0.0, f"The {word} injector pressure drop must be finite and above zero.")
    need("discharge_coefficient", "DISCHARGE_COEFFICIENT", s.discharge_coefficient,
         f"State the {word} discharge coefficient Cd. No default is assumed.",
         lambda v: 0.0 < v <= 1.0,
         f"The {word} discharge coefficient must be above 0 and at most 1.")
    if s.density_source is DensitySource.STATED:
        need("density", "DENSITY", s.density,
             f"State the {word} liquid density, or use its validated fluid model.",
             lambda v: v > 0.0, f"The {word} density must be finite and above zero.")
    elif not fluid_model_supported(basis.propellant_of(branch)):
        issues.append(InjectorIssue(
            "DENSITY_MODEL_UNSUPPORTED", f"{name}.density_source",
            f"{basis.propellant_of(branch)} has no validated fluid model; state its density."))
    if s.hole_mode is HoleMode.HOLE_COUNT:
        need("hole_count", "HOLE_COUNT", s.hole_count,
             f"State the {word} hole count.", lambda v: v >= 1.0 and v == int(v),
             f"The {word} hole count must be a whole number of at least 1.")
    elif s.hole_mode is HoleMode.HOLE_DIAMETER:
        need("hole_diameter", "HOLE_DIAMETER", s.hole_diameter,
             f"State the {word} hole diameter.", lambda v: v > 0.0,
             f"The {word} hole diameter must be finite and above zero.")

    for key, label, _basis in LOSS_TERMS:
        mode, value = s.loss_modes[key], s.loss_values.get(key)
        if mode is LossMode.STATED:
            need(key, "TERM", value, f"State the {word} {label.lower()}, or mark it "
                 "unresolved or not applicable.", lambda v: v >= 0.0,
                 f"The {word} {label.lower()} must be finite and at or above zero.")
        elif mode is LossMode.LINE_DIAMETER:
            need(key, "LINE_DIAMETER", value, f"State the {word} feed-line diameter for "
                 "the dynamic head.", lambda v: v > 0.0,
                 f"The {word} feed-line diameter must be finite and above zero.")
    if issues:
        return None, issues
    # Every value-carrying term is now stated and in its domain.
    losses = {key: LossSetting(s.loss_modes[key],
                               float(s.loss_values[key])
                               if s.loss_modes[key] in (LossMode.STATED, LossMode.LINE_DIAMETER)
                               else None)
              for key, _label, _basis in LOSS_TERMS}
    fluid = s.density_source is DensitySource.FLUID_MODEL
    return BranchDefinition(
        branch=branch, pressure_drop=float(s.pressure_drop),
        discharge_coefficient=float(s.discharge_coefficient),
        density_source=s.density_source,
        density=None if fluid else float(s.density),
        density_pressure=basis.chamber_pressure + float(s.pressure_drop) if fluid else None,
        hole_mode=s.hole_mode,
        hole_count=int(s.hole_count) if s.hole_mode is HoleMode.HOLE_COUNT else None,
        hole_diameter=(float(s.hole_diameter) if s.hole_mode is HoleMode.HOLE_DIAMETER
                       else None),
        losses=losses), []


def build_definition(basis: FlowBasis | None, oxidiser: BranchSettings, fuel: BranchSettings
                     ) -> tuple[InjectorDefinition | None, tuple[InjectorIssue, ...]]:
    """The stated study, or ``None`` and every reason it cannot be built."""
    if basis is None:
        return None, ()
    ox, ox_issues = _branch_definition(Branch.OXIDISER, basis, oxidiser)
    fu, fu_issues = _branch_definition(Branch.FUEL, basis, fuel)
    if ox is None or fu is None:
        return None, tuple(ox_issues + fu_issues)
    return InjectorDefinition(basis, ox, fu), ()


# ---------------------------------------------------------------------------
# computing
# ---------------------------------------------------------------------------

ASSUMPTIONS: tuple[str, ...] = (
    "Incompressible liquid through the injector orifices: Q = Cd A √(2Δp/ρ), "
    "ṁ = Cd A √(2ρΔp), v = Cd √(2Δp/ρ) (Sutton 9th ed. §8.1, Eqs. 8-1, 8-2, 8-5).",
    "A is each branch's total geometric orifice area; holes, when split, are equal and round.",
    "Cd, Δp and the density are stated (or the density comes from the validated fluid "
    "model); none is inferred from an element type.",
    "A fluid-model density is evaluated at the stream temperature LIQ-3 used and at the "
    "injector inlet, chamber pressure + Δp. A branch heated before the injector (a "
    "regenerative coolant) is not at that temperature: state its density instead.",
    "The flows, O/F and chamber pressure are LIQ-4's, unchanged. Chamber pressure is the "
    "ideal model's p1; the injector-face-to-nozzle-inlet loss is not modelled.",
    "Pressure ledger after Sutton Eq. 10-7 and Eqs. 11-6, 11-7: chamber pressure plus "
    "every drop between the branch's reference point and the chamber. Static head is not "
    "credited. An unresolved term is never zero.",
    "Δp/p1 is reported because it is stability-relevant; combustion stability is not "
    "evaluated. Atomization and combustion efficiency are not computed.",
)

_NO_HOLES = "Not requested: the total area only."
_NO_LINE = "The dynamic head is not computed from a line diameter."


def _density(branch: BranchDefinition, basis: FlowBasis
             ) -> tuple[float | None, dict[str, str], str]:
    """(density, provenance, refusal message)."""
    if branch.density_source is DensitySource.STATED:
        return branch.density, {"source": "Stated by the user"}, ""
    from rocketforge.core.errors import DomainError
    from rocketforge.engineering.propellants import PRODUCTION_FLUID_MAPPING, stream_density

    from . import fluid_property_provider as gateway

    propellant = basis.propellant_of(branch.branch)
    available = gateway.availability()
    if not available.is_usable:
        return None, {}, (f"No validated fluid model is installed for the {propellant} "
                          f"density. {available.detail} Or state the density.")
    temperature = basis.temperature_of(branch.branch)
    try:
        stream = stream_density(gateway.property_provider(),
                                PRODUCTION_FLUID_MAPPING.require(propellant),
                                temperature, branch.density_pressure)
    except DomainError as error:
        return None, {}, f"{error} State the density instead."
    record = {k: str(v) for k, v in stream.as_mapping().items()}
    record["source"] = (f"{stream.provider_label} {stream.library_version}, "
                        f"{stream.fluid_name} at {stream.temperature:g} K and "
                        f"{stream.pressure:g} Pa ({stream.phase})")
    return stream.density, record, ""


def _ledger(branch: BranchDefinition, basis: FlowBasis, density: float):
    from rocketforge.engineering.injector import (
        BudgetTerm,
        TermStatus,
        branch_budget,
        dynamic_head,
    )

    terms = [
        BudgetTerm("chamber_pressure", "Chamber pressure p1", TermStatus.RESOLVED,
                   basis.chamber_pressure, "LIQ-4 sizing (LIQ-3 operating point)"),
        BudgetTerm("injector_pressure_drop", "Injector pressure drop", TermStatus.RESOLVED,
                   branch.pressure_drop, "Stated; sizes the orifice (Sutton Eq. 8-2)"),
    ]
    line_velocity = None
    for key, label, source in LOSS_TERMS:
        setting = branch.losses[key]
        if setting.mode is LossMode.STATED:
            terms.append(BudgetTerm(key, label, TermStatus.RESOLVED, setting.value,
                                    f"Stated · {source}"))
        elif setting.mode is LossMode.LINE_DIAMETER:
            head = dynamic_head(basis.mass_flow_of(branch.branch), density, setting.value)
            line_velocity = head.value.line_velocity
            terms.append(BudgetTerm(
                key, label, TermStatus.RESOLVED, head.value.dynamic_head,
                f"½ρv², v = ṁ/(ρ πD²/4) at D = {setting.value * 1e3:g} mm · {source}"))
        elif setting.mode is LossMode.NOT_APPLICABLE:
            terms.append(BudgetTerm(key, label, TermStatus.NOT_APPLICABLE,
                                    reason="Declared not applicable to this branch"))
        else:
            terms.append(BudgetTerm(key, label, TermStatus.UNRESOLVED,
                                    reason="Not stated; not assumed to be zero"))
    budget = branch_budget(terms)
    lines = tuple(LedgerLine(t.key, t.label, t.status.value, t.value, t.source, t.reason)
                  for t in budget.terms)
    return budget, lines, line_velocity


def _solve_branch(branch: BranchDefinition, basis: FlowBasis) -> tuple[BranchResult, Any]:
    from rocketforge.engineering.injector import (
        holes_from_count,
        holes_from_diameter,
        orifice_sizing,
    )

    density, density_provenance, refusal = _density(branch, basis)
    if density is None:
        return BranchResult(branch=branch.branch, status=InjectorStatus.REFUSED,
                            unresolved={q.key: refusal for q in BRANCH_QUANTITIES},
                            message=refusal), None
    sizing = orifice_sizing(basis.mass_flow_of(branch.branch), density,
                            branch.pressure_drop, branch.discharge_coefficient)
    if sizing.value is None:
        message = sizing.diagnostics[0].message
        return BranchResult(branch=branch.branch, status=InjectorStatus.REFUSED,
                            unresolved={q.key: message for q in BRANCH_QUANTITIES},
                            message=message), None
    o = sizing.value
    q: dict[str, float] = {
        "mass_flow": o.mass_flow, "density": o.density, "volumetric_flow": o.volumetric_flow,
        "pressure_drop": o.pressure_drop,
        "pressure_drop_ratio": o.pressure_drop / basis.chamber_pressure,
        "discharge_coefficient": o.discharge_coefficient, "flow_area": o.flow_area,
        "effective_area": o.effective_area, "injection_velocity": o.injection_velocity,
        "mass_flow_closure": o.mass_flow_closure, "velocity_closure": o.velocity_closure,
    }
    unresolved: dict[str, str] = {}
    notes: list[str] = []
    status = InjectorStatus.OK
    hole_keys = ("hole_count", "hole_diameter", "hole_area", "whole_hole_count",
                 "whole_hole_flow_area", "whole_hole_pressure_drop", "hole_area_closure")
    if branch.hole_mode is HoleMode.AREA:
        unresolved.update({k: _NO_HOLES for k in hole_keys})
    else:
        split = (holes_from_count(o, branch.hole_count)
                 if branch.hole_mode is HoleMode.HOLE_COUNT
                 else holes_from_diameter(o, branch.hole_diameter))
        if split.value is None:
            message = split.diagnostics[0].message
            unresolved.update({k: message for k in hole_keys})
        else:
            h = split.value
            q.update({"hole_count": h.hole_count, "hole_diameter": h.hole_diameter,
                      "hole_area": h.hole_area, "whole_hole_count": float(h.whole_hole_count),
                      "whole_hole_flow_area": h.whole_hole_flow_area,
                      "whole_hole_pressure_drop": h.whole_hole_pressure_drop,
                      "hole_area_closure": h.hole_area_closure})
            for d in split.diagnostics:
                notes.append(f"{branch.branch.value.capitalize()}: {d.message}")
                status = InjectorStatus.WARNING
    budget, lines, line_velocity = _ledger(branch, basis, density)
    q["minimum_known_pressure"] = budget.minimum_known_pressure
    if budget.required_pressure is not None:
        q["required_pressure"] = budget.required_pressure
    else:
        labels = [line.label.lower() for line in lines if line.status == "unresolved"]
        unresolved["required_pressure"] = ("Not complete: unresolved " + ", ".join(labels)
                                           + ". The requirement is at least the minimum "
                                           "known pressure.")
    if line_velocity is None:
        unresolved["line_velocity"] = _NO_LINE
    else:
        q["line_velocity"] = line_velocity
    return BranchResult(branch=branch.branch, status=status, quantities=q,
                        unresolved=unresolved, ledger=lines,
                        density_provenance=density_provenance, notes=tuple(notes)), o


def solve_injector(definition: InjectorDefinition) -> InjectorResult:
    """Compute both branches and the pair's closures. Never raises."""
    basis = definition.basis
    ox, ox_sizing = _solve_branch(definition.oxidiser, basis)
    fu, fu_sizing = _solve_branch(definition.fuel, basis)
    pair: dict[str, float] = {}
    pair_unresolved: dict[str, str] = {}
    if ox_sizing is None or fu_sizing is None:
        status = InjectorStatus.REFUSED
        message = " ".join(m for m in (ox.message, fu.message) if m)
        pair_unresolved = {p.key: "A branch was refused." for p in PAIR_QUANTITIES}
    else:
        # Eq. 8-2 forward, from each branch's own sized orifice (Eq. 8-3 for O/F).
        flows = [s.discharge_coefficient * s.flow_area * math.sqrt(2.0 * s.density
                                                                    * s.pressure_drop)
                 for s in (ox_sizing, fu_sizing)]
        total = flows[0] + flows[1]
        ratio = flows[0] / flows[1]
        pair = {"total_mass_flow": total, "oxidiser_fuel_ratio": ratio,
                "oxidiser_fuel_ratio_closure": ratio / basis.oxidiser_fuel_ratio - 1.0,
                "total_mass_flow_closure": total / basis.mass_flow - 1.0}
        status = (InjectorStatus.WARNING
                  if InjectorStatus.WARNING in (ox.status, fu.status) else InjectorStatus.OK)
        message = ""
    return InjectorResult(definition=definition, status=status, oxidiser=ox, fuel=fu,
                          pair=pair, pair_unresolved=pair_unresolved, message=message,
                          assumptions=ASSUMPTIONS, provenance=provenance(definition))


def provenance(definition: InjectorDefinition) -> dict[str, str]:
    basis = definition.basis
    return {
        "hydraulics": "RocketForge engineering.injector: incompressible orifice, "
                      "Sutton & Biblarz 9th ed. §8.1, Eqs. 8-1, 8-2, 8-3, 8-5",
        "budget": "RocketForge engineering.injector: branch ledger after Sutton §10.4 "
                  "Eq. 10-7 and §11.5 Eqs. 11-6, 11-7",
        "sizing": f"LIQ-4 sizing {basis.sizing_fingerprint[:12]}, {basis.pair_key}",
        "trade": f"LIQ-3 trade {basis.trade_fingerprint[:12]}",
        "sizing_chamber": basis.sizing_provenance.get("chamber", ""),
    }


# ---------------------------------------------------------------------------
# presentation
# ---------------------------------------------------------------------------

#: Display unit, scale and format per quantity. Conversion happens here only.
DISPLAY: dict[str, tuple[str, float, str]] = {
    "mass_flow": ("kg/s", 1.0, ",.5g"),
    "density": ("kg/m³", 1.0, ",.2f"),
    "volumetric_flow": ("L/s", 1.0e3, ",.4f"),
    "pressure_drop": ("bar", 1.0e-5, ",.4f"),
    "pressure_drop_ratio": ("%", 100.0, ".2f"),
    "discharge_coefficient": ("", 1.0, ".4g"),
    "flow_area": ("mm²", 1.0e6, ",.4f"),
    "effective_area": ("mm²", 1.0e6, ",.4f"),
    "injection_velocity": ("m/s", 1.0, ",.3f"),
    "hole_count": ("", 1.0, ",.6g"),
    "hole_diameter": ("mm", 1.0e3, ",.4f"),
    "hole_area": ("mm²", 1.0e6, ",.5f"),
    "whole_hole_count": ("", 1.0, ",.0f"),
    "whole_hole_flow_area": ("mm²", 1.0e6, ",.4f"),
    "whole_hole_pressure_drop": ("bar", 1.0e-5, ",.4f"),
    "line_velocity": ("m/s", 1.0, ",.3f"),
    "minimum_known_pressure": ("bar", 1.0e-5, ",.4f"),
    "required_pressure": ("bar", 1.0e-5, ",.4f"),
    "mass_flow_closure": ("", 1.0, ".1e"),
    "velocity_closure": ("", 1.0, ".1e"),
    "hole_area_closure": ("", 1.0, ".1e"),
    "total_mass_flow": ("kg/s", 1.0, ",.5g"),
    "oxidiser_fuel_ratio": ("", 1.0, ".6g"),
    "oxidiser_fuel_ratio_closure": ("", 1.0, ".1e"),
    "total_mass_flow_closure": ("", 1.0, ".1e"),
}

GROUPS: tuple[tuple[str, str], ...] = (
    ("flow", "Flow"),
    ("orifice", "Orifice"),
    ("holes", "Holes"),
    ("budget", "Pressure budget"),
    ("closure", "Closure"),
)

LEDGER_UNIT = ("bar", 1.0e-5, ",.4f")


def display_value(key: str, value: float | None) -> str:
    if value is None:
        return "—"
    _unit, scale, spec = DISPLAY[key]
    return format(value * scale, spec)


def branch_groups(result: BranchResult) -> list[dict[str, Any]]:
    """Every branch quantity, grouped for display, with unit, note and reason."""
    groups = []
    for key, title in GROUPS:
        rows = [{"key": q.key, "label": q.label, "unit": DISPLAY[q.key][0], "note": q.note,
                 "value": display_value(q.key, result.value(q.key)),
                 "reason": result.unresolved.get(q.key, "")}
                for q in BRANCH_QUANTITIES if q.group == key]
        groups.append({"key": key, "title": title, "rows": rows})
    return groups


def ledger_rows(result: BranchResult) -> list[dict[str, str]]:
    unit, scale, spec = LEDGER_UNIT
    words = {"resolved": "", "not_applicable": "not applicable", "unresolved": "UNRESOLVED"}
    return [{"key": line.key, "label": line.label, "status": line.status,
             "value": format(line.value * scale, spec) if line.value is not None
             else words[line.status],
             "unit": unit if line.value is not None else "",
             "source": line.source, "reason": line.reason}
            for line in result.ledger]


def pair_rows(result: InjectorResult) -> list[dict[str, str]]:
    return [{"key": q.key, "label": q.label, "unit": DISPLAY[q.key][0], "note": q.note,
             "value": display_value(q.key, result.pair.get(q.key)),
             "reason": result.pair_unresolved.get(q.key, "")}
            for q in PAIR_QUANTITIES]

"""Propellant inventory (SYS-1): resolve, compute, present. Qt-free.

The inputs are an accepted LIQ-4 sizing and the LIQ-3 trade it extends, read
as they were produced::

    accepted LIQ-4 sizing  --(mdot_o, mdot_f, O/F, identity)-->        InventoryBasis
    its LIQ-3 trade        --(the LIQ-2 requirement snapshot: burn time)
    stated per branch: residual (eta or mass), reserve, allowances,    InventoryDefinition
                       boil-off
        engineering.propulsion_system.inventory.branch_inventory         once per branch

**Nothing is resolved silently.** :func:`inventory_basis` refuses a missing,
stale, refused or incomplete sizing, a trade that is not the one the sizing
extends, and a requirement with no burn time. Every budget term starts
unresolved; an unresolved term keeps the loaded mass unresolved, and the
minimum known load is given instead.

Only the thrust-chamber flows exist upstream. No gas generator, tank
pressurization bleed or auxiliary flow is added, because no cycle is
modelled, and none is double counted later.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from rocketforge.engine.chamber_sizing import SizingResult
from rocketforge.engine.propellant_trade import TradeResult
from rocketforge.engine.propulsion_system.inventory import (
    ALLOWANCE_TERMS,
    INVENTORY_BRANCH_QUANTITIES,
    INVENTORY_SCHEMA,
    INVENTORY_TOTALS,
    InventoryBasis,
    InventoryBranchDefinition,
    InventoryDefinition,
    ReserveMode,
    ResidualMode,
    TermMode,
    TermSetting,
)
from rocketforge.engine.propulsion_system.records import (
    Branch,
    BranchOutcome,
    LedgerLine,
    StudyResult,
    StudyStatus,
    Upstream,
)

from . import system_presentation as present

__all__ = [
    "ASSUMPTIONS",
    "DISPLAY",
    "GROUPS",
    "BranchSettings",
    "InventoryIssue",
    "build_definition",
    "inventory_basis",
    "provenance",
    "solve_inventory",
]


@dataclass(frozen=True, slots=True)
class BranchSettings:
    """What the user states for one branch, SI. Everything starts unresolved."""

    residual_mode: ResidualMode = ResidualMode.UNRESOLVED
    expulsion_efficiency: float | None = None
    tank_residual_mode: TermMode = TermMode.UNRESOLVED
    tank_residual: float | None = None               # kg
    trapped_line_mode: TermMode = TermMode.UNRESOLVED
    trapped_line: float | None = None                # kg
    reserve_mode: ReserveMode = ReserveMode.UNRESOLVED
    reserve_value: float | None = None               # kg, or a fraction
    allowance_modes: dict[str, TermMode] = field(
        default_factory=lambda: {key: TermMode.UNRESOLVED for key, _l, _b in ALLOWANCE_TERMS})
    allowance_values: dict[str, float | None] = field(
        default_factory=lambda: {key: None for key, _l, _b in ALLOWANCE_TERMS})
    boiloff_mode: TermMode = TermMode.UNRESOLVED
    boiloff: float | None = None                     # kg


@dataclass(frozen=True, slots=True)
class InventoryIssue:
    code: str
    field: str
    message: str


# ---------------------------------------------------------------------------
# the basis, from an accepted sizing and its trade
# ---------------------------------------------------------------------------


def inventory_basis(sizing: SizingResult | None, sizing_stale: bool,
                    trade: TradeResult | None, trade_stale: bool
                    ) -> tuple[InventoryBasis | None, tuple[InventoryIssue, ...]]:
    """The flows and burn time of an accepted, current sizing, or why not."""
    def refuse(code: str, message: str):
        return None, (InventoryIssue(code, "sizing", message),)

    if sizing is None:
        return refuse("NO_SIZING", "No thrust-chamber sizing has been run. Size one on the "
                      "Thrust Chamber Sizing page.")
    if sizing_stale:
        return refuse("SIZING_STALE", "The thrust-chamber sizing is stale: the trade "
                      "selection or its nozzle changed since it ran. Size again.")
    if not sizing.ok:
        return refuse("SIZING_REFUSED", "The thrust-chamber sizing was refused, so there are "
                      "no propellant flows to budget.")
    flows = [sizing.value(k) for k in ("mass_flow", "oxidiser_mass_flow", "fuel_mass_flow")]
    if any(v is None for v in flows):
        return refuse("SIZING_INCOMPLETE", "The thrust-chamber sizing carries no propellant "
                      "flows.")
    point = sizing.definition.point
    if trade is None or trade_stale or trade.definition.fingerprint != point.trade_fingerprint:
        return refuse("TRADE_MISMATCH", "The propellant trade is not the one this sizing "
                      "extends, or it is stale, so the requirement's burn time cannot be "
                      "read. Run the trade and the sizing again.")
    requirement = trade.definition.requirement
    if requirement.fingerprint != point.requirement_fingerprint:
        return refuse("REQUIREMENT_MISMATCH", "The trade's requirement is not the one the "
                      "sizing answered. Run the sizing again.")
    burn_time = requirement.burn_time
    if burn_time is None or not (math.isfinite(burn_time) and burn_time > 0.0):
        return refuse("BURN_TIME_UNRESOLVED", "The engine requirement states no burn time. "
                      "State it on the Engine Requirement page; none is assumed.")
    return InventoryBasis(
        sizing=Upstream("LIQ-4", sizing.definition.fingerprint, sizing.status.value),
        trade_fingerprint=point.trade_fingerprint,
        requirement_fingerprint=point.requirement_fingerprint,
        pair_key=point.pair_key, pair_label=point.pair_label,
        oxidiser=point.oxidiser, fuel=point.fuel,
        oxidiser_fuel_ratio=point.oxidiser_fuel_ratio,
        chamber_pressure=point.chamber_pressure,
        oxidiser_temperature=point.oxidiser_temperature,
        fuel_temperature=point.fuel_temperature,
        mass_flow=flows[0], oxidiser_mass_flow=flows[1], fuel_mass_flow=flows[2],
        burn_time=float(burn_time),
    ), ()


# ---------------------------------------------------------------------------
# the definition
# ---------------------------------------------------------------------------


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _branch_definition(branch: Branch, s: BranchSettings
                       ) -> tuple[InventoryBranchDefinition | None, list[InventoryIssue]]:
    name = branch.value
    word = "oxidiser" if branch is Branch.OXIDISER else "fuel"
    issues: list[InventoryIssue] = []

    def need(field_name: str, code: str, value, missing: str, valid, invalid: str) -> None:
        if value is None:
            issues.append(InventoryIssue(f"{code}_UNRESOLVED", f"{name}.{field_name}", missing))
        elif not (_finite(value) and valid(value)):
            issues.append(InventoryIssue(f"{code}_INVALID", f"{name}.{field_name}", invalid))

    def term(field_name: str, label: str, mode: TermMode, value) -> TermSetting:
        if mode is TermMode.STATED:
            need(field_name, "TERM", value, f"State the {word} {label}, or mark it unresolved "
                 "or not applicable.", lambda v: v >= 0.0,
                 f"The {word} {label} must be finite and at or above zero.")
            return TermSetting(mode, float(value)) if _finite(value) and value >= 0.0 \
                else TermSetting()
        return TermSetting(mode)

    if s.residual_mode is ResidualMode.EXPULSION_EFFICIENCY:
        need("expulsion_efficiency", "EXPULSION_EFFICIENCY", s.expulsion_efficiency,
             f"State the {word} expulsion efficiency. None is assumed.",
             lambda v: 0.0 < v <= 1.0,
             f"The {word} expulsion efficiency must be above 0 and at most 1.")
    tank = trapped = TermSetting()
    if s.residual_mode is ResidualMode.RESIDUAL_MASS:
        tank = term("tank_residual", "tank residual", s.tank_residual_mode, s.tank_residual)
        trapped = term("trapped_line", "trapped-line mass", s.trapped_line_mode,
                       s.trapped_line)
    if s.reserve_mode is ReserveMode.STATED_MASS:
        need("reserve", "RESERVE", s.reserve_value, f"State the {word} reserve mass.",
             lambda v: v >= 0.0, f"The {word} reserve must be finite and at or above zero.")
    elif s.reserve_mode is ReserveMode.STATED_FRACTION:
        need("reserve", "RESERVE", s.reserve_value, f"State the {word} reserve fraction.",
             lambda v: v >= 0.0,
             f"The {word} reserve fraction must be finite and at or above zero.")
    allowances = {key: term(key, label.lower(), s.allowance_modes[key],
                            s.allowance_values.get(key))
                  for key, label, _basis in ALLOWANCE_TERMS}
    boiloff = term("boiloff", "boil-off", s.boiloff_mode, s.boiloff)
    if issues:
        return None, issues
    reserve_stated = s.reserve_mode in (ReserveMode.STATED_MASS, ReserveMode.STATED_FRACTION)
    return InventoryBranchDefinition(
        branch=branch, residual_mode=s.residual_mode,
        expulsion_efficiency=(float(s.expulsion_efficiency)
                              if s.residual_mode is ResidualMode.EXPULSION_EFFICIENCY else None),
        tank_residual=tank, trapped_line=trapped,
        reserve_mode=s.reserve_mode,
        reserve_value=float(s.reserve_value) if reserve_stated else None,
        allowances=allowances, boiloff=boiloff), []


def build_definition(basis: InventoryBasis | None, oxidiser: BranchSettings,
                     fuel: BranchSettings
                     ) -> tuple[InventoryDefinition | None, tuple[InventoryIssue, ...]]:
    """The stated inventory, or ``None`` and every reason it cannot be built."""
    if basis is None:
        return None, ()
    ox, ox_issues = _branch_definition(Branch.OXIDISER, oxidiser)
    fu, fu_issues = _branch_definition(Branch.FUEL, fuel)
    if ox is None or fu is None:
        return None, tuple(ox_issues + fu_issues)
    return InventoryDefinition(basis, ox, fu), ()


# ---------------------------------------------------------------------------
# computing
# ---------------------------------------------------------------------------

ASSUMPTIONS: tuple[str, ...] = (
    "Usable propellant is the steady burn's consumption, ṁ × burn time, at the LIQ-4 "
    "flows and the LIQ-2 burn time (Sutton 9th ed. §11.1 item 1, Example 11-1).",
    "Expulsion efficiency, after Sutton §6.2: the propellant that can be expelled divided "
    "by the propellant present. Present = available / η; residual = present − available. "
    "It covers the tank and its piping, so no separate trapped-line mass is added to it.",
    "Available propellant is what must be expellable: usable + start and shutdown "
    "transients + chill-down + other allowances + reserve.",
    "Boil-off evaporates from the tank before the burn: it is loaded, never present for "
    "expulsion, and is not divided by η.",
    "No expulsion efficiency, reserve, trapped-line mass, boil-off, transient or "
    "chill-down mass is assumed. A term not stated stays unresolved and is never zero.",
    "Only the thrust-chamber flows exist upstream: no gas generator, tank-pressurization "
    "bleed, auxiliary thruster or other cycle flow is included or implied.",
    "Masses only: no density, volume, ullage, tank geometry or pressurization.",
)


def _line(key: str, label: str, setting: TermSetting, source: str) -> LedgerLine:
    if setting.mode is TermMode.STATED:
        return LedgerLine(key, label, "resolved", setting.value, "kg", f"Stated · {source}")
    if setting.mode is TermMode.NOT_APPLICABLE:
        return LedgerLine(key, label, "not_applicable", None, "kg", source,
                          "Declared not applicable to this branch")
    return LedgerLine(key, label, "unresolved", None, "kg", source,
                      "Not stated; not assumed to be zero")


def _mass_term(key: str, label: str, setting: TermSetting):
    from rocketforge.engineering.propulsion_system.inventory import MassTerm, TermStatus

    status = {TermMode.STATED: TermStatus.RESOLVED,
              TermMode.NOT_APPLICABLE: TermStatus.NOT_APPLICABLE,
              TermMode.UNRESOLVED: TermStatus.UNRESOLVED}[setting.mode]
    return MassTerm(key, label, status, setting.value)


def _solve_branch(d: InventoryBranchDefinition, basis: InventoryBasis) -> BranchOutcome:
    from rocketforge.engineering.propulsion_system import inventory as rel

    mass_flow = basis.mass_flow_of(d.branch)
    usable = rel.usable_mass(mass_flow, basis.burn_time)
    # The reserve, as a mass: stated, or a stated fraction of the usable mass.
    if d.reserve_mode is ReserveMode.STATED_MASS:
        reserve = TermSetting(TermMode.STATED, d.reserve_value)
        reserve_source = "Stated mass · Sutton §11.1 items 8, 11"
    elif d.reserve_mode is ReserveMode.STATED_FRACTION:
        reserve = TermSetting(TermMode.STATED, d.reserve_value * usable)
        reserve_source = (f"Stated fraction {d.reserve_value:g} × usable · Sutton "
                          "Example 11-1")
    elif d.reserve_mode is ReserveMode.NOT_APPLICABLE:
        reserve, reserve_source = TermSetting(TermMode.NOT_APPLICABLE), "Sutton §11.1"
    else:
        reserve, reserve_source = TermSetting(), "Sutton §11.1"

    allowances = [_mass_term(key, label, d.allowances[key]) for key, label, _b in ALLOWANCE_TERMS]
    allowances.append(_mass_term("reserve_mass", "Reserve", reserve))
    mode = rel.ResidualMode(d.residual_mode.value)
    parts = ([_mass_term("tank_residual", "Tank residual", d.tank_residual),
              _mass_term("trapped_line", "Trapped in lines and valves", d.trapped_line)]
             if d.residual_mode is ResidualMode.RESIDUAL_MASS else [])
    solution = rel.branch_inventory(mass_flow, basis.burn_time, allowances, mode,
                                    d.expulsion_efficiency, parts,
                                    _mass_term("boiloff_mass", "Boil-off", d.boiloff))
    if solution.value is None:
        message = solution.diagnostics[0].message
        return BranchOutcome(branch=d.branch, status=StudyStatus.REFUSED,
                             unresolved={q.key: message for q in INVENTORY_BRANCH_QUANTITIES},
                             message=message)
    inv = solution.value
    q: dict[str, float] = {"mass_flow": mass_flow, "burn_time": basis.burn_time,
                           "usable_mass": usable,
                           "minimum_known_loaded": inv.minimum_known_loaded}
    unresolved: dict[str, str] = {}

    def put(key: str, value: float | None, why: str) -> None:
        if value is None:
            unresolved[key] = why
        else:
            q[key] = value

    not_stated = "Not stated; not assumed to be zero."
    for key, label, _b in ALLOWANCE_TERMS:
        s = d.allowances[key]
        put(key, s.value if s.mode is TermMode.STATED else
            (0.0 if s.mode is TermMode.NOT_APPLICABLE else None), not_stated)
    put("reserve_mass", reserve.value if reserve.mode is TermMode.STATED else
        (0.0 if reserve.mode is TermMode.NOT_APPLICABLE else None), not_stated)
    names = {**{key: label.lower() for key, label, _b in ALLOWANCE_TERMS},
             "reserve_mass": "reserve", "residual": "residual", "boiloff_mass": "boil-off",
             "tank_residual": "tank residual", "trapped_line": "trapped-line mass"}
    waiting = ("Waits on unresolved terms: "
               + ", ".join(names.get(k, k) for k in inv.unresolved) + ".")
    put("available_mass", inv.available, waiting)
    put("expulsion_efficiency", inv.expulsion_efficiency,
        "Not stated, and not derivable while the residual or the available mass is "
        "unresolved." if d.residual_mode is not ResidualMode.EXPULSION_EFFICIENCY else waiting)
    if d.residual_mode is ResidualMode.RESIDUAL_MASS:
        for key, setting in (("tank_residual", d.tank_residual),
                             ("trapped_line", d.trapped_line)):
            put(key, setting.value if setting.mode is TermMode.STATED else
                (0.0 if setting.mode is TermMode.NOT_APPLICABLE else None), not_stated)
    else:
        covered = ("Covered by the expulsion efficiency, which includes the tank and its "
                   "piping (Sutton §6.2)." if d.residual_mode is ResidualMode.EXPULSION_EFFICIENCY
                   else "The residual is unresolved.")
        unresolved["tank_residual"] = covered
        unresolved["trapped_line"] = covered
    put("residual_mass", inv.residual, waiting if inv.unresolved else not_stated)
    put("present_mass", inv.present, waiting)
    put("boiloff_mass", inv.boiloff, not_stated)
    put("loaded_mass", inv.loaded, waiting)
    put("unavailable_fraction", None if inv.residual is None or inv.present is None
        else inv.residual / inv.present, waiting)
    put("balance_closure", inv.balance_closure, waiting)
    put("efficiency_closure", inv.efficiency_closure, waiting)

    ledger = [LedgerLine("usable_mass", "Usable propellant", "resolved", usable, "kg",
                         "ṁ × burn time (LIQ-4 flow, LIQ-2 burn time)")]
    ledger += [_line(key, label, d.allowances[key], basis_text)
               for key, label, basis_text in ALLOWANCE_TERMS]
    ledger.append(_line("reserve_mass", "Reserve", reserve, reserve_source))
    if d.residual_mode is ResidualMode.EXPULSION_EFFICIENCY:
        ledger.append(LedgerLine(
            "residual_mass", "Residual (unavailable)",
            "resolved" if inv.residual is not None else "unresolved", inv.residual, "kg",
            f"Available × (1/η − 1), η = {d.expulsion_efficiency:g} stated · Sutton §6.2",
            "" if inv.residual is not None else "Waits on the unresolved allowances"))
    elif d.residual_mode is ResidualMode.RESIDUAL_MASS:
        ledger.append(_line("tank_residual", "Tank residual", d.tank_residual,
                            "Sutton §6.2, §11.1 item 6"))
        ledger.append(_line("trapped_line", "Trapped in lines and valves", d.trapped_line,
                            "Sutton §6.2, §11.1 item 6"))
    else:
        ledger.append(LedgerLine("residual_mass", "Residual (unavailable)", "unresolved", None,
                                 "kg", "Sutton §6.2",
                                 "Neither an expulsion efficiency nor a residual mass is "
                                 "stated; not assumed to be zero"))
    ledger.append(_line("boiloff_mass", "Boil-off before the burn", d.boiloff,
                        "Sutton §11.1 item 10"))
    status = StudyStatus.OK if inv.loaded is not None else StudyStatus.INCOMPLETE
    return BranchOutcome(branch=d.branch, status=status, quantities=q, unresolved=unresolved,
                         ledger=tuple(ledger),
                         provenance={"flow": "LIQ-4 sizing", "burn_time": "LIQ-2 requirement"})


def solve_inventory(definition: InventoryDefinition) -> StudyResult:
    """Both branches and the totals. Never raises for a stated input."""
    basis = definition.basis
    ox = _solve_branch(definition.oxidiser, basis)
    fu = _solve_branch(definition.fuel, basis)
    totals: dict[str, float] = {}
    missing: dict[str, str] = {}
    if not (ox.ok and fu.ok):
        status = StudyStatus.REFUSED
        message = " ".join(m for m in (ox.message, fu.message) if m)
        missing = {q.key: "A branch was refused." for q in INVENTORY_TOTALS}
    else:
        uo, uf = ox.value("usable_mass"), fu.value("usable_mass")
        totals["usable_total"] = uo + uf
        totals["usable_oxidiser_fuel_ratio"] = uo / uf
        totals["usable_ratio_closure"] = (uo / uf) / basis.oxidiser_fuel_ratio - 1.0
        totals["usable_total_closure"] = (uo + uf) / (basis.mass_flow * basis.burn_time) - 1.0
        totals["minimum_known_loaded_total"] = (ox.value("minimum_known_loaded")
                                                + fu.value("minimum_known_loaded"))
        incomplete = "A branch's load waits on unresolved terms."
        for key, branch_key in (("loaded_total", "loaded_mass"),
                                ("residual_total", "residual_mass")):
            a, b = ox.value(branch_key), fu.value(branch_key)
            if a is None or b is None:
                missing[key] = incomplete
            else:
                totals[key] = a + b
        lo, lf = ox.value("loaded_mass"), fu.value("loaded_mass")
        if lo is None or lf is None:
            missing["loaded_oxidiser_fuel_ratio"] = incomplete
        else:
            totals["loaded_oxidiser_fuel_ratio"] = lo / lf
        status = (StudyStatus.OK if StudyStatus.INCOMPLETE not in (ox.status, fu.status)
                  else StudyStatus.INCOMPLETE)
        message = ""
    return StudyResult(schema=INVENTORY_SCHEMA, definition=definition, status=status,
                       oxidiser=ox, fuel=fu, totals=totals, totals_unresolved=missing,
                       message=message, assumptions=ASSUMPTIONS,
                       provenance=provenance(definition))


def provenance(definition: InventoryDefinition) -> dict[str, str]:
    basis = definition.basis
    return {
        "inventory": "RocketForge engineering.propulsion_system.inventory: Sutton & Biblarz "
                     "9th ed. §6.2 (expulsion efficiency), §11.1 (propellant budget)",
        "sizing": f"LIQ-4 sizing {basis.sizing.fingerprint[:12]}, {basis.pair_key}",
        "trade": f"LIQ-3 trade {basis.trade_fingerprint[:12]}",
        "requirement": f"LIQ-2 requirement {basis.requirement_fingerprint[:12]}, burn time "
                       f"{basis.burn_time:g} s",
    }


# ---------------------------------------------------------------------------
# presentation
# ---------------------------------------------------------------------------

DISPLAY: dict[str, tuple[str, float, str]] = {
    "mass_flow": ("kg/s", 1.0, ",.5g"),
    "burn_time": ("s", 1.0, ",.6g"),
    **{key: ("kg", 1.0, ",.4f") for key in (
        "usable_mass", "start_stop", "chilldown", "other_allowance", "reserve_mass",
        "available_mass", "tank_residual", "trapped_line", "residual_mass", "present_mass",
        "boiloff_mass", "loaded_mass", "minimum_known_loaded", "usable_total", "loaded_total",
        "minimum_known_loaded_total", "residual_total")},
    "expulsion_efficiency": ("%", 100.0, ".4f"),
    "unavailable_fraction": ("%", 100.0, ".4f"),
    "balance_closure": ("", 1.0, ".1e"),
    "efficiency_closure": ("", 1.0, ".1e"),
    "usable_oxidiser_fuel_ratio": ("", 1.0, ".6g"),
    "loaded_oxidiser_fuel_ratio": ("", 1.0, ".6g"),
    "usable_ratio_closure": ("", 1.0, ".1e"),
    "usable_total_closure": ("", 1.0, ".1e"),
}

GROUPS: tuple[tuple[str, str], ...] = (
    ("burn", "Burn"),
    ("budget", "Available"),
    ("residual", "Residual"),
    ("load", "Load"),
    ("closure", "Closure"),
)


def branch_view(outcome: BranchOutcome) -> dict:
    return {"ok": outcome.ok, "message": outcome.message,
            "groups": present.branch_groups(outcome, INVENTORY_BRANCH_QUANTITIES, GROUPS,
                                            DISPLAY),
            "ledger": present.ledger_rows(outcome)}


def total_rows(result: StudyResult) -> list[dict[str, str]]:
    return present.total_rows(result, INVENTORY_TOTALS, DISPLAY)

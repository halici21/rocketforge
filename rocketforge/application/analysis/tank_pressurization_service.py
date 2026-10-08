"""Tank pressurization foundation (SYS-4): resolve, compute, present. Qt-free.

The inputs are a current SYS-3 management study and, when the required tank
pressure is taken from it, the current LIQ-6 injector study on the same
sizing::

    SYS-3 management  --(gas volumes at start and end, expelled volume)-->  PressurizationBasis
    LIQ-6 injector    --(each branch's required upstream pressure, if complete)
    stated per branch: mode, gas constant, exponent, tank and bottle states  PressurizationDefinition
        engineering.propulsion_system.pressurization.regulated_stored_gas      regulated branches
        engineering.propulsion_system.pressurization.blowdown                  blowdown branches

**Nothing is resolved silently.** No gas, gas constant, temperature, pressure
or exponent has a default; isothermal is n = 1, stated. A required pressure
that LIQ-6 cannot give (its ledger is incomplete) stays unresolved, and so do
the margins. Autogenous and warm-gas pressurization are recorded as intent and
computed nowhere.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.engine.injector import Branch as InjectorBranch
from rocketforge.engine.injector import InjectorResult
from rocketforge.engine.propulsion_system.pressurization import (
    PRESSURIZATION_BRANCH_QUANTITIES,
    PRESSURIZATION_SCHEMA,
    PRESSURIZATION_TOTALS,
    BranchGasVolumes,
    PressurantReserve,
    PressurizationBasis,
    PressurizationBranchDefinition,
    PressurizationDefinition,
    PressurizationMode,
    RequiredSource,
    TankGasTemperature,
    UllageSource,
)
from rocketforge.engine.propulsion_system.records import (
    Branch,
    BranchOutcome,
    StudyResult,
    Upstream,
)
from rocketforge.engine.propulsion_system.records import StudyStatus as S

from . import system_presentation as present

__all__ = [
    "ASSUMPTIONS",
    "BranchSettings",
    "PressurizationIssue",
    "build_definition",
    "pressurization_basis",
    "solve_pressurization",
]


@dataclass(frozen=True, slots=True)
class BranchSettings:
    """What the user states for one branch, SI. Nothing has a value to start."""

    mode: PressurizationMode | None = None
    gas_name: str = ""
    gas_constant: float | None = None              # J/(kg K)
    exponent: float | None = None
    required_source: RequiredSource = RequiredSource.UNRESOLVED
    required_pressure: float | None = None         # Pa, when stated
    tank_pressure: float | None = None             # Pa
    tank_gas_temperature_mode: TankGasTemperature | None = None
    tank_gas_temperature: float | None = None      # K
    bottle_initial_pressure: float | None = None   # Pa
    bottle_initial_temperature: float | None = None
    bottle_final_pressure: float | None = None     # Pa
    ullage_source: UllageSource | None = None
    reserve_mode: PressurantReserve = PressurantReserve.UNRESOLVED
    reserve_value: float | None = None             # kg, or a fraction
    initial_pressure: float | None = None          # Pa, blowdown
    initial_temperature: float | None = None       # K, blowdown


@dataclass(frozen=True, slots=True)
class PressurizationIssue:
    code: str
    field: str
    message: str


def pressurization_basis(management: StudyResult | None, stale: bool
                         ) -> tuple[PressurizationBasis | None, tuple[PressurizationIssue, ...]]:
    """The gas volumes of a current SYS-3 study, or why not."""
    def refuse(code: str, message: str):
        return None, (PressurizationIssue(code, "management", message),)

    if management is None:
        return refuse("NO_MANAGEMENT", "No propellant-management study has been computed. "
                      "Compute it on the Propellant Management page.")
    if stale:
        return refuse("MANAGEMENT_STALE", "The propellant-management study is stale: the "
                      "inventory, the tanks or its intent changed. Compute it again.")
    if not management.ok:
        return refuse("MANAGEMENT_REFUSED", "The propellant-management study was refused.")

    def gas(branch: Branch) -> BranchGasVolumes:
        b = management.branch(branch)
        return BranchGasVolumes(b.value("tank_volume"), b.value("gas_volume_start"),
                                b.value("expelled_volume"), b.value("gas_volume_end"),
                                b.value("residual_volume"))

    d = management.definition
    return PressurizationBasis(
        management=Upstream("SYS-3", d.fingerprint, management.status.value),
        sizing_fingerprint=d.basis.sizing_fingerprint, pair_label=d.basis.pair_label,
        oxidiser=d.basis.oxidiser, fuel=d.basis.fuel,
        oxidiser_gas=gas(Branch.OXIDISER), fuel_gas=gas(Branch.FUEL)), ()


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _required(branch: Branch, s: BranchSettings, basis: PressurizationBasis,
              injector: InjectorResult | None, injector_stale: bool, issues: list
              ) -> tuple[float | None, str, Upstream | None]:
    word = "oxidiser" if branch is Branch.OXIDISER else "fuel"
    field = f"{branch.value}.required_pressure"
    if s.required_source is RequiredSource.UNRESOLVED:
        return None, "Not stated; the margin against the feed requirement is unresolved.", None
    if s.required_source is RequiredSource.STATED:
        if s.required_pressure is None:
            issues.append(PressurizationIssue("REQUIRED_PRESSURE_UNRESOLVED", field,
                                              f"State the {word} required tank pressure."))
        elif not (_finite(s.required_pressure) and s.required_pressure > 0.0):
            issues.append(PressurizationIssue("REQUIRED_PRESSURE_INVALID", field,
                                              f"The {word} required tank pressure must be "
                                              "finite and above zero."))
        return s.required_pressure, "", None
    if injector is None:
        issues.append(PressurizationIssue("NO_INJECTOR", field, "No injector study has been "
                                          "computed to take the required pressure from."))
        return None, "", None
    if injector_stale:
        issues.append(PressurizationIssue("INJECTOR_STALE", field, "The injector study is "
                                          "stale. Compute it again, or state the pressure."))
        return None, "", None
    if not injector.ok:
        issues.append(PressurizationIssue("INJECTOR_REFUSED", field,
                                          "The injector study was refused."))
        return None, "", None
    if injector.definition.basis.sizing_fingerprint != basis.sizing_fingerprint:
        issues.append(PressurizationIssue("INJECTOR_MISMATCH", field, "The injector study is "
                                          "for a different sizing than the inventory."))
        return None, "", None
    upstream = Upstream("LIQ-6", injector.definition.fingerprint, injector.status.value)
    b = injector.branch(InjectorBranch(branch.value))
    value = b.value("required_pressure")
    if value is None:
        return None, ("LIQ-6: " + b.unresolved.get("required_pressure", "not complete")), upstream
    return value, "", upstream


def _branch_definition(branch: Branch, basis: PressurizationBasis, s: BranchSettings,
                       injector: InjectorResult | None, injector_stale: bool
                       ) -> tuple[PressurizationBranchDefinition | None, list]:
    name = branch.value
    word = "oxidiser" if branch is Branch.OXIDISER else "fuel"
    issues: list[PressurizationIssue] = []

    def need(field_name: str, code: str, value, missing: str, valid, invalid: str) -> None:
        if value is None:
            issues.append(PressurizationIssue(f"{code}_UNRESOLVED", f"{name}.{field_name}",
                                              missing))
        elif not (_finite(value) and valid(value)):
            issues.append(PressurizationIssue(f"{code}_INVALID", f"{name}.{field_name}",
                                              invalid))

    if s.mode is None:
        issues.append(PressurizationIssue("MODE_UNRESOLVED", f"{name}.mode",
                                          f"State how the {word} tank is pressurized. None is "
                                          "assumed."))
        return None, issues
    required, reason, upstream = _required(branch, s, basis, injector, injector_stale, issues)
    if s.mode.executable:
        if not s.gas_name.strip():
            issues.append(PressurizationIssue("GAS_UNRESOLVED", f"{name}.gas_name",
                                              f"Name the {word} pressurant. None is assumed."))
        need("gas_constant", "GAS_CONSTANT", s.gas_constant,
             f"State the {word} pressurant's gas constant R. None is assumed.",
             lambda v: v > 0.0, f"The {word} gas constant must be above zero.")
        need("exponent", "EXPONENT", s.exponent,
             f"State the {word} expansion exponent n (1 is isothermal).",
             lambda v: v >= 1.0, f"The {word} expansion exponent must be at least 1.")
    positive = (lambda v: v > 0.0)
    if s.mode is PressurizationMode.REGULATED:
        need("tank_pressure", "TANK_PRESSURE", s.tank_pressure,
             f"State the {word} regulated tank pressure.", positive,
             f"The {word} tank pressure must be above zero.")
        need("bottle_initial_pressure", "BOTTLE_PRESSURE", s.bottle_initial_pressure,
             f"State the {word} bottle's initial pressure.", positive,
             f"The {word} bottle pressure must be above zero.")
        need("bottle_initial_temperature", "BOTTLE_TEMPERATURE", s.bottle_initial_temperature,
             f"State the {word} bottle's initial temperature.", positive,
             f"The {word} bottle temperature must be above zero.")
        need("bottle_final_pressure", "BOTTLE_FINAL_PRESSURE", s.bottle_final_pressure,
             f"State the {word} bottle's final pressure (the regulator's lowest inlet "
             "pressure).", positive, f"The {word} bottle's final pressure must be above zero.")
        if s.tank_gas_temperature_mode is None:
            issues.append(PressurizationIssue(
                "TANK_GAS_TEMPERATURE_UNRESOLVED", f"{name}.tank_gas_temperature_mode",
                f"State the {word} tank gas temperature: stated, or one of Sutton's two "
                "conventions. None is assumed."))
        elif s.tank_gas_temperature_mode is TankGasTemperature.STATED:
            need("tank_gas_temperature", "TANK_GAS_TEMPERATURE", s.tank_gas_temperature,
                 f"State the {word} tank gas temperature.", positive,
                 f"The {word} tank gas temperature must be above zero.")
        if s.ullage_source is None:
            issues.append(PressurizationIssue(
                "ULLAGE_SOURCE_UNRESOLVED", f"{name}.ullage_source",
                f"State whether the {word} start ullage is pre-pressurized or filled from the "
                "bottle."))
        if s.reserve_mode in (PressurantReserve.STATED_MASS, PressurantReserve.STATED_FRACTION):
            need("reserve", "RESERVE", s.reserve_value, f"State the {word} pressurant reserve.",
                 lambda v: v >= 0.0, f"The {word} reserve must be at or above zero.")
    elif s.mode is PressurizationMode.BLOWDOWN:
        need("initial_pressure", "INITIAL_PRESSURE", s.initial_pressure,
             f"State the {word} initial tank pressure.", positive,
             f"The {word} initial pressure must be above zero.")
        need("initial_temperature", "INITIAL_TEMPERATURE", s.initial_temperature,
             f"State the {word} initial gas temperature.", positive,
             f"The {word} initial temperature must be above zero.")
    if issues:
        return None, issues
    regulated = s.mode is PressurizationMode.REGULATED
    blowdown = s.mode is PressurizationMode.BLOWDOWN
    stated_reserve = s.reserve_mode in (PressurantReserve.STATED_MASS,
                                        PressurantReserve.STATED_FRACTION)
    intent = {PressurizationMode.AUTOGENOUS_INTENT:
              "Autogenous pressurization (Sutton §6.5 source 4): needs propellant "
              "evaporation and heat-exchanger models, which do not exist yet.",
              PressurizationMode.WARM_GAS_INTENT:
              "Warm-gas or engine-gas pressurization (Sutton §6.5 sources 2, 3): needs "
              "gas-generator or cycle models, which do not exist yet."}.get(s.mode, "")
    return PressurizationBranchDefinition(
        branch=branch, mode=s.mode, gas_name=s.gas_name.strip(),
        gas_constant=float(s.gas_constant) if s.mode.executable else None,
        exponent=float(s.exponent) if s.mode.executable else None,
        required_source=s.required_source, required_pressure=required,
        required_reason=reason, required_upstream=upstream,
        tank_pressure=float(s.tank_pressure) if regulated else None,
        tank_gas_temperature_mode=s.tank_gas_temperature_mode if regulated else None,
        tank_gas_temperature=(float(s.tank_gas_temperature) if regulated
                              and s.tank_gas_temperature_mode is TankGasTemperature.STATED
                              else None),
        bottle_initial_pressure=float(s.bottle_initial_pressure) if regulated else None,
        bottle_initial_temperature=float(s.bottle_initial_temperature) if regulated else None,
        bottle_final_pressure=float(s.bottle_final_pressure) if regulated else None,
        ullage_source=s.ullage_source if regulated else None,
        reserve_mode=s.reserve_mode if regulated else PressurantReserve.NOT_APPLICABLE,
        reserve_value=float(s.reserve_value) if regulated and stated_reserve else None,
        initial_pressure=float(s.initial_pressure) if blowdown else None,
        initial_temperature=float(s.initial_temperature) if blowdown else None,
        intent_note=intent), []


def build_definition(basis: PressurizationBasis | None, oxidiser: BranchSettings,
                     fuel: BranchSettings, injector: InjectorResult | None = None,
                     injector_stale: bool = False
                     ) -> tuple[PressurizationDefinition | None, tuple]:
    if basis is None:
        return None, ()
    ox, ox_issues = _branch_definition(Branch.OXIDISER, basis, oxidiser, injector,
                                       injector_stale)
    fu, fu_issues = _branch_definition(Branch.FUEL, basis, fuel, injector, injector_stale)
    if ox is None or fu is None:
        return None, tuple(ox_issues + fu_issues)
    return PressurizationDefinition(basis, ox, fu), ()


# ---------------------------------------------------------------------------
# computing
# ---------------------------------------------------------------------------

ASSUMPTIONS: tuple[str, ...] = (
    "Perfect gas, Sutton 9th ed. §6.5: pV = mRT; no propellant evaporation, no gas "
    "dissolved in the propellant, no sloshing, no heat transfer to the gas. The results "
    "are Sutton's theoretical (minimum) estimates; real-gas compressibility at high bottle "
    "pressure is not modelled.",
    "Regulated stored gas: Eq. 6-5 with each temperature explicit. mp = pp Vp/(R Tp); "
    "Tg = T0 (pg/p0)^((n−1)/n); V0 = mp R/(p0/T0 − pg/Tg). n = 1 and Tp = T0 is Eq. 6-7; "
    "n = k, pg = pp and Tp = Tg is Example 6-2.",
    "The bottle's final pressure pg is stated and must stay at or above the regulated tank "
    "pressure (Sutton: pg ≥ pp for valve, line and regulator drops). Regulator transients "
    "and pressurant lines are not modelled.",
    "Blowdown: the ullage gas expands as p V^n = const from the start-of-burn gas volume "
    "to the end-of-burn volume (SYS-3): pf = pi (Vi/Vf)^n. The engine's flow decay as the "
    "pressure falls is not modelled; the design flow sets the volumes.",
    "The gas volumes are SYS-3's: expelled = available propellant / ρ, residual held in "
    "the tank. When the bottle also fills the start ullage, that ullage is taken to hold no "
    "pressurant before it; a pre-pressurized ullage is filled from the ground.",
    "The required tank pressure is stated or taken from the LIQ-6 ledger, whose reference "
    "point is the branch's own (here, the tank) as its terms define it. Unresolved stays "
    "unresolved.",
    "Autogenous and warm-gas pressurization are recorded as intent and not computed. No "
    "boil-off, heat-exchanger, warm-gas chemistry, line sizing or bottle structure.",
)

_MODE_WORDS = {PressurizationMode.REGULATED: "Regulated stored gas",
               PressurizationMode.BLOWDOWN: "Blowdown",
               PressurizationMode.AUTOGENOUS_INTENT: "Autogenous (intent only)",
               PressurizationMode.WARM_GAS_INTENT: "Warm / engine gas (intent only)"}


def _expansion(n: float) -> str:
    return "Isothermal, n = 1" if n == 1.0 else f"Polytropic, n = {n:g}"


def _solve_branch(d: PressurizationBranchDefinition, basis: PressurizationBasis
                  ) -> BranchOutcome:
    from rocketforge.engineering.propulsion_system import pressurization as rel

    gas = basis.gas_of(d.branch)
    labels = {"mode": _MODE_WORDS[d.mode],
              "required_source": {RequiredSource.UNRESOLVED: "UNRESOLVED",
                                  RequiredSource.STATED: "Stated",
                                  RequiredSource.INJECTOR: "LIQ-6 injector ledger"}[
                                      d.required_source]}
    q: dict[str, float] = {"gas_volume_start": gas.gas_volume_start,
                           "gas_volume_end": gas.gas_volume_end}
    unresolved: dict[str, str] = {}
    notes: list[str] = []
    word = d.branch.value.capitalize()
    if d.required_pressure is not None:
        q["required_pressure"] = d.required_pressure
    else:
        unresolved["required_pressure"] = d.required_reason

    def refused(message: str) -> BranchOutcome:
        return BranchOutcome(branch=d.branch, status=S.REFUSED,
                             unresolved={x.key: message for x in
                                         PRESSURIZATION_BRANCH_QUANTITIES},
                             labels=labels, message=f"{word}: {message}")

    if not d.mode.executable:
        labels["intent"] = d.intent_note
        for x in PRESSURIZATION_BRANCH_QUANTITIES:
            if x.key not in q and x.key not in unresolved:
                unresolved[x.key] = "Intent recorded only: " + d.intent_note
        return BranchOutcome(branch=d.branch, status=S.INCOMPLETE, quantities=q,
                             unresolved=unresolved, labels=labels)
    labels["gas"] = f"{d.gas_name}, R = {d.gas_constant:g} J/(kg K) (stated)"
    labels["expansion"] = _expansion(d.exponent)
    q["gas_constant"] = d.gas_constant
    q["exponent"] = d.exponent
    margins: list[float] = []
    if d.mode is PressurizationMode.REGULATED:
        fill = gas.expelled_volume + (gas.gas_volume_start
                                      if d.ullage_source is UllageSource.BOTTLE else 0.0)
        tg = rel.polytropic_temperature(d.bottle_initial_temperature,
                                        d.bottle_initial_pressure, d.bottle_final_pressure,
                                        d.exponent)
        tp = {TankGasTemperature.STATED: d.tank_gas_temperature,
              TankGasTemperature.BOTTLE_INITIAL: d.bottle_initial_temperature,
              TankGasTemperature.BOTTLE_FINAL: tg}[d.tank_gas_temperature_mode]
        labels["tank_gas_temperature_basis"] = {
            TankGasTemperature.STATED: "Stated",
            TankGasTemperature.BOTTLE_INITIAL: "Tp = T0 (Sutton Eq. 6-7 convention)",
            TankGasTemperature.BOTTLE_FINAL: "Tp = Tg (Sutton Example 6-2 convention)"}[
                d.tank_gas_temperature_mode]
        solution = rel.regulated_stored_gas(d.tank_pressure, fill, tp,
                                            d.bottle_initial_pressure,
                                            d.bottle_initial_temperature,
                                            d.bottle_final_pressure, d.gas_constant, d.exponent)
        if solution.value is None:
            return refused(solution.diagnostics[0].message)
        g = solution.value
        q.update({"tank_pressure": g.tank_pressure, "fill_volume": g.fill_volume,
                  "tank_gas_temperature": g.tank_gas_temperature,
                  "delivered_mass": g.delivered_mass,
                  "bottle_initial_pressure": g.bottle_initial_pressure,
                  "bottle_initial_temperature": g.bottle_initial_temperature,
                  "bottle_final_pressure": g.bottle_final_pressure,
                  "bottle_final_temperature": g.bottle_final_temperature,
                  "regulator_drop_end": g.regulator_drop_end, "bottle_volume": g.bottle_volume,
                  "initial_mass": g.initial_mass, "bottle_residual_mass": g.residual_mass,
                  "mass_closure": g.mass_closure})
        if d.reserve_mode is PressurantReserve.UNRESOLVED:
            why = "The pressurant reserve is not stated; not assumed to be zero."
            for key in ("reserve_mass", "loaded_pressurant", "bottle_volume_with_reserve"):
                unresolved[key] = why
        else:
            reserve = {PressurantReserve.NOT_APPLICABLE: 0.0,
                       PressurantReserve.STATED_MASS: d.reserve_value,
                       PressurantReserve.STATED_FRACTION:
                       (d.reserve_value or 0.0) * g.initial_mass}[d.reserve_mode]
            q["reserve_mass"] = reserve
            q["loaded_pressurant"] = g.initial_mass + reserve
            # The reserve is stored at the bottle's initial state: V = m R T0 / p0.
            q["bottle_volume_with_reserve"] = (g.bottle_volume + reserve * d.gas_constant
                                               * d.bottle_initial_temperature
                                               / d.bottle_initial_pressure)
        if d.required_pressure is not None:
            q["pressure_margin"] = g.tank_pressure - d.required_pressure
            margins.append(q["pressure_margin"])
        else:
            unresolved["pressure_margin"] = d.required_reason
        blow = ("initial_pressure", "initial_temperature", "gas_mass", "blowdown_ratio",
                "final_pressure", "final_temperature", "margin_start", "margin_end")
        unresolved.update({k: "Blowdown only." for k in blow})
        series: tuple = ()
    else:
        solution = rel.blowdown(d.initial_pressure, d.initial_temperature,
                                gas.gas_volume_start, gas.expelled_volume, d.gas_constant,
                                d.exponent)
        if solution.value is None:
            return refused(solution.diagnostics[0].message)
        b = solution.value
        q.update({"initial_pressure": b.initial_pressure,
                  "initial_temperature": b.initial_temperature, "gas_mass": b.gas_mass,
                  "blowdown_ratio": b.blowdown_ratio, "final_pressure": b.final_pressure,
                  "final_temperature": b.final_temperature, "mass_closure": b.mass_closure})
        if d.required_pressure is not None:
            q["margin_start"] = b.initial_pressure - d.required_pressure
            q["margin_end"] = b.final_pressure - d.required_pressure
            margins += [q["margin_start"], q["margin_end"]]
        else:
            unresolved["margin_start"] = unresolved["margin_end"] = d.required_reason
        regulated_keys = ("tank_pressure", "pressure_margin", "fill_volume",
                          "tank_gas_temperature", "delivered_mass", "bottle_initial_pressure",
                          "bottle_initial_temperature", "bottle_final_pressure",
                          "bottle_final_temperature", "regulator_drop_end", "bottle_volume",
                          "initial_mass", "bottle_residual_mass", "reserve_mass",
                          "loaded_pressurant", "bottle_volume_with_reserve")
        unresolved.update({k: "Regulated stored gas only." for k in regulated_keys})
        series = tuple({"fraction": s.expelled_fraction, "gas_volume": s.gas_volume,
                        "pressure": s.pressure, "temperature": s.temperature}
                       for s in b.evolution)
    if d.required_pressure is None:
        labels["feed_check"] = "UNRESOLVED: no required tank pressure"
        status = S.INCOMPLETE
    elif min(margins) < 0.0:
        labels["feed_check"] = "INSUFFICIENT: below the required tank pressure"
        what = ("the end-of-burn pressure" if d.mode is PressurizationMode.BLOWDOWN
                else "the regulated tank pressure")
        notes.append(f"{word}: {what} is below the required tank pressure by "
                     f"{-min(margins) / 1e5:.4g} bar.")
        status = S.WARNING
    else:
        labels["feed_check"] = "At or above the required tank pressure"
        status = S.OK
    if status is S.OK and any(k in unresolved for k in ("loaded_pressurant",)):
        status = S.INCOMPLETE
    return BranchOutcome(branch=d.branch, status=status, quantities=q, unresolved=unresolved,
                         labels=labels, series=series, notes=tuple(notes))


def solve_pressurization(definition: PressurizationDefinition) -> StudyResult:
    """Both branches and the totals. Never raises for a stated input."""
    ox = _solve_branch(definition.oxidiser, definition.basis)
    fu = _solve_branch(definition.fuel, definition.basis)
    totals: dict[str, float] = {}
    missing: dict[str, str] = {}
    if not (ox.ok and fu.ok):
        status = S.REFUSED
        message = " ".join(m for m in (ox.message, fu.message) if m)
        missing = {x.key: "A branch was refused." for x in PRESSURIZATION_TOTALS}
    else:
        def carried(outcome: BranchOutcome) -> float | None:
            mode = definition.branch(outcome.branch).mode
            return outcome.value("loaded_pressurant" if mode is PressurizationMode.REGULATED
                                 else "gas_mass")

        masses = [carried(ox), carried(fu)]
        if None in masses:
            missing["pressurant_total"] = "A branch's pressurant is unresolved or intent only."
        else:
            totals["pressurant_total"] = masses[0] + masses[1]
        regulated = [o for o in (ox, fu)
                     if definition.branch(o.branch).mode is PressurizationMode.REGULATED]
        volumes = [o.value("bottle_volume_with_reserve") for o in regulated]
        if not regulated:
            missing["bottle_volume_total"] = "No branch is regulated."
        elif None in volumes:
            missing["bottle_volume_total"] = "A bottle's reserve is unresolved."
        else:
            totals["bottle_volume_total"] = math.fsum(volumes)
        statuses = (ox.status, fu.status)
        status = (S.WARNING if S.WARNING in statuses else
                  S.INCOMPLETE if S.INCOMPLETE in statuses else S.OK)
        message = ""
    return StudyResult(schema=PRESSURIZATION_SCHEMA, definition=definition, status=status,
                       oxidiser=ox, fuel=fu, totals=totals, totals_unresolved=missing,
                       message=message, assumptions=ASSUMPTIONS,
                       provenance=provenance(definition))


def provenance(definition: PressurizationDefinition) -> dict[str, str]:
    basis = definition.basis
    out = {
        "pressurization": "RocketForge engineering.propulsion_system.pressurization: Sutton & "
                          "Biblarz 9th ed. §6.4 (Table 6-3), §6.5 (Eqs. 6-5 to 6-7, "
                          "Example 6-2)",
        "management": f"SYS-3 management {basis.management.fingerprint[:12]}",
        "sizing": f"LIQ-4 sizing {basis.sizing_fingerprint[:12]}",
    }
    for d in (definition.oxidiser, definition.fuel):
        if d.required_upstream is not None:
            out[f"{d.branch.value}_required"] = (f"LIQ-6 injector "
                                                 f"{d.required_upstream.fingerprint[:12]}")
    return out


DISPLAY: dict[str, tuple[str, float, str]] = {
    **{k: ("bar", 1.0e-5, ",.4f") for k in (
        "required_pressure", "tank_pressure", "pressure_margin", "bottle_initial_pressure",
        "bottle_final_pressure", "regulator_drop_end", "initial_pressure", "final_pressure",
        "margin_start", "margin_end")},
    **{k: ("K", 1.0, ",.3f") for k in ("tank_gas_temperature", "bottle_initial_temperature",
                                       "bottle_final_temperature", "initial_temperature",
                                       "final_temperature")},
    **{k: ("m³", 1.0, ",.6f") for k in ("gas_volume_start", "gas_volume_end", "fill_volume",
                                        "bottle_volume", "bottle_volume_with_reserve",
                                        "bottle_volume_total")},
    **{k: ("kg", 1.0, ",.5f") for k in ("delivered_mass", "initial_mass",
                                        "bottle_residual_mass", "reserve_mass",
                                        "loaded_pressurant", "gas_mass", "pressurant_total")},
    "gas_constant": ("J/(kg·K)", 1.0, ",.4f"),
    "exponent": ("", 1.0, ".6g"),
    "blowdown_ratio": ("", 1.0, ".6g"),
    "mass_closure": ("", 1.0, ".1e"),
}

GROUPS = (("requirement", "Requirement"), ("gas", "Pressurant"), ("ullage", "Ullage gas"),
          ("regulated", "Regulated stored gas"), ("blowdown", "Blowdown"),
          ("closure", "Closure"))
LABELS = (("mode", "Mode"), ("gas", "Pressurant"), ("expansion", "Expansion"),
          ("tank_gas_temperature_basis", "Tank gas temperature"),
          ("required_source", "Required pressure"), ("feed_check", "Feed check"),
          ("intent", "Intent"))
SERIES = (("fraction", "Expelled %", 100.0, ".0f"), ("gas_volume", "Gas m³", 1.0, ",.5f"),
          ("pressure", "Pressure bar", 1.0e-5, ",.4f"), ("temperature", "T K", 1.0, ",.2f"))


def branch_view(outcome: BranchOutcome) -> dict:
    mode_regulated = "regulated" if "tank_pressure" in outcome.quantities else "blowdown"
    groups = [g for g in present.branch_groups(outcome, PRESSURIZATION_BRANCH_QUANTITIES,
                                               GROUPS, DISPLAY)
              if g["key"] not in ({"blowdown"} if mode_regulated == "regulated"
                                  else {"regulated"})]
    view = {"groups": groups, "labels": present.label_rows(outcome, LABELS)}
    if outcome.series:
        view["series"] = present.series_rows(outcome, SERIES)
    return view


def total_rows(result: StudyResult) -> list[dict[str, str]]:
    return present.total_rows(result, PRESSURIZATION_TOTALS, DISPLAY)

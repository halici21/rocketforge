"""Propellant management foundation (SYS-3): resolve, compute, present. Qt-free.

The inputs are a current, complete SYS-1 inventory and the current SYS-2
tanks computed from it::

    complete SYS-1 inventory  --(loaded, present, available, residual, eta)--> ManagementBasis
    SYS-2 tanks on it          --(V_tank, rho, ullage, fill)
    stated per branch: management mode, acceleration environment,            ManagementDefinition
                       settling intent (and, optionally, its acceleration)
        engineering.propulsion_system.propellant_management.management_state    once per branch
        engineering.propulsion_system.propellant_management.management_volumes  once per branch

**Intent, not proof.** The outlet-availability state is a declaration with its
basis. The expulsion efficiency stays SYS-1's; nothing here assigns one from a
device type. No slosh dynamics, settling time, capillary retention or device
structure is evaluated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.engine.propulsion_system.inventory import ResidualMode
from rocketforge.engine.propulsion_system.management import (
    MANAGEMENT_BRANCH_QUANTITIES,
    MANAGEMENT_SCHEMA,
    BranchStorage,
    Environment,
    ManagementBasis,
    ManagementBranchDefinition,
    ManagementDefinition,
    ManagementMode,
    SettlingIntent,
)
from rocketforge.engine.propulsion_system.records import (
    Branch,
    BranchOutcome,
    StudyResult,
    StudyStatus,
    Upstream,
)

from . import system_presentation as present

__all__ = [
    "ASSUMPTIONS",
    "BranchSettings",
    "ManagementIssue",
    "build_definition",
    "management_basis",
    "solve_management",
]


@dataclass(frozen=True, slots=True)
class BranchSettings:
    """What the user states for one branch. The mode has no default; the
    environment and settling intent start unresolved."""

    mode: ManagementMode | None = None
    environment: Environment = Environment.UNRESOLVED
    settling: SettlingIntent = SettlingIntent.UNRESOLVED
    settling_acceleration: float | None = None       # m/s^2, optional intent


@dataclass(frozen=True, slots=True)
class ManagementIssue:
    code: str
    field: str
    message: str


def _storage(inventory: StudyResult, tanks: StudyResult, branch: Branch) -> BranchStorage:
    i, t = inventory.branch(branch), tanks.branch(branch)
    d = inventory.definition.branch(branch)
    source = ("stated in SYS-1" if d.residual_mode is ResidualMode.EXPULSION_EFFICIENCY
              else "derived in SYS-1 from the stated residual")
    return BranchStorage(
        loaded_mass=i.value("loaded_mass"), present_mass=i.value("present_mass"),
        available_mass=i.value("available_mass"), residual_mass=i.value("residual_mass"),
        boiloff_mass=i.value("boiloff_mass"),
        expulsion_efficiency=i.value("expulsion_efficiency"), expulsion_source=source,
        density=t.value("density"), tank_volume=t.value("tank_volume"),
        liquid_volume=t.value("liquid_volume"), ullage_volume=t.value("ullage_volume"),
        ullage_fraction=t.value("ullage_fraction"), fill_fraction=t.value("fill_fraction"))


def management_basis(inventory: StudyResult | None, inventory_stale: bool,
                     tanks: StudyResult | None, tanks_stale: bool
                     ) -> tuple[ManagementBasis | None, tuple[ManagementIssue, ...]]:
    """The current inventory and the current tanks built on it, or why not."""
    def refuse(code: str, field: str, message: str):
        return None, (ManagementIssue(code, field, message),)

    if inventory is None or not inventory.ok or inventory.status is not StudyStatus.OK:
        return refuse("INVENTORY_INCOMPLETE", "inventory", "A complete propellant inventory "
                      "is needed. Compute it on the Propellant Inventory page.")
    if inventory_stale:
        return refuse("INVENTORY_STALE", "inventory", "The propellant inventory is stale. "
                      "Compute it again, then the tanks.")
    if tanks is None:
        return refuse("NO_TANKS", "tanks", "No tank geometry has been computed. Compute it on "
                      "the Tank Geometry & Packaging page.")
    if tanks_stale:
        return refuse("TANKS_STALE", "tanks", "The tank geometry is stale: the inventory or "
                      "its inputs changed. Compute it again.")
    if not tanks.ok:
        return refuse("TANKS_REFUSED", "tanks", "The tank geometry was refused, so there is "
                      "no tank to manage.")
    if tanks.definition.basis.inventory.fingerprint != inventory.definition.fingerprint:
        return refuse("TANKS_MISMATCH", "tanks", "The tanks were not computed from this "
                      "inventory. Compute them again.")
    basis = inventory.definition.basis
    return ManagementBasis(
        inventory=Upstream("SYS-1", inventory.definition.fingerprint, inventory.status.value),
        tanks=Upstream("SYS-2", tanks.definition.fingerprint, tanks.status.value),
        sizing_fingerprint=basis.sizing.fingerprint,
        pair_label=basis.pair_label, oxidiser=basis.oxidiser, fuel=basis.fuel,
        oxidiser_storage=_storage(inventory, tanks, Branch.OXIDISER),
        fuel_storage=_storage(inventory, tanks, Branch.FUEL)), ()


def _branch_definition(branch: Branch, s: BranchSettings
                       ) -> tuple[ManagementBranchDefinition | None, list[ManagementIssue]]:
    word = "oxidiser" if branch is Branch.OXIDISER else "fuel"
    issues = []
    if s.mode is None:
        issues.append(ManagementIssue("MODE_UNRESOLVED", f"{branch.value}.mode",
                                      f"State how the {word} is kept at the tank outlet. None "
                                      "is assumed."))
    a = s.settling_acceleration
    if a is not None and not (math.isfinite(a) and a > 0.0):
        issues.append(ManagementIssue("SETTLING_ACCELERATION_INVALID",
                                      f"{branch.value}.settling_acceleration",
                                      f"The {word} settling acceleration must be finite and "
                                      "above zero."))
    if issues:
        return None, issues
    return ManagementBranchDefinition(branch, s.mode, s.environment, s.settling, a), []


def build_definition(basis: ManagementBasis | None, oxidiser: BranchSettings,
                     fuel: BranchSettings
                     ) -> tuple[ManagementDefinition | None, tuple[ManagementIssue, ...]]:
    if basis is None:
        return None, ()
    ox, ox_issues = _branch_definition(Branch.OXIDISER, oxidiser)
    fu, fu_issues = _branch_definition(Branch.FUEL, fuel)
    if ox is None or fu is None:
        return None, tuple(ox_issues + fu_issues)
    return ManagementDefinition(basis, ox, fu), ()


ASSUMPTIONS: tuple[str, ...] = (
    "Propellant management after Sutton 9th ed. §6.2: a settled free surface, a "
    "positive-expulsion device (diaphragm, bladder, piston, bellows) or a surface-tension "
    "device keeps liquid at the outlet. The mode is stated; none is assumed.",
    "Outlet availability is a declaration with its basis, never a demonstration. In low "
    "gravity a free surface needs a settling acceleration, and none is assumed.",
    "The expulsion efficiency and residual are SYS-1's. They are never assigned from the "
    "device type: Sutton's Table 6-2 is qualitative and for hydrazine spacecraft tanks.",
    "Volumes: liquid present at the start = (loaded − boil-off) / ρ; expelled = available / ρ; "
    "the residual is held in the tank, so the gas at the end is V_tank − residual / ρ.",
    "Not modelled: slosh dynamics, pendulum or mode models, damping, frequency, control "
    "coupling, free-surface CFD, vortexing, settling time, screen pore or bubble-point sizing, "
    "diaphragm stress or fatigue.",
)

_MODE_WORDS = {ManagementMode.SETTLED: "Settled free surface",
               ManagementMode.DIAPHRAGM: "Diaphragm", ManagementMode.BLADDER: "Bladder",
               ManagementMode.PISTON: "Piston", ManagementMode.BELLOWS: "Bellows",
               ManagementMode.SURFACE_TENSION: "Surface-tension device (PMD)"}
_ENVIRONMENT_WORDS = {Environment.ACCELERATED: "Accelerated throughout",
                      Environment.LOW_GRAVITY: "Low-gravity phases",
                      Environment.UNRESOLVED: "UNRESOLVED"}
_SETTLING_WORDS = {SettlingIntent.REQUIRED: "Settling acceleration required (stated)",
                   SettlingIntent.NOT_REQUIRED: "No settling acceleration (stated)",
                   SettlingIntent.UNRESOLVED: "UNRESOLVED"}
_AVAILABILITY_WORDS = {
    "declared_device": "Declared: positive-expulsion device (not evaluated)",
    "declared_settled": "Declared: settled by the stated acceleration (not evaluated)",
    "requires_settling": "Only while settling acts (not evaluated)",
    "declared_capillary": "Declared: surface-tension retention (not evaluated)",
    "unresolved": "UNRESOLVED",
}


def _solve_branch(d: ManagementBranchDefinition, basis: ManagementBasis) -> BranchOutcome:
    from rocketforge.engineering.propulsion_system import propellant_management as rel

    s = basis.storage_of(d.branch)
    labels = {"management_mode": _MODE_WORDS[d.mode],
              "environment": _ENVIRONMENT_WORDS[d.environment],
              "settling": _SETTLING_WORDS[d.settling],
              "expulsion_source": f"η {s.expulsion_efficiency:.6g}, {s.expulsion_source}"}
    state = rel.management_state(rel.ManagementMode(d.mode.value),
                                 rel.Environment(d.environment.value),
                                 rel.SettlingIntent(d.settling.value))
    if state.value is None:
        message = f"{d.branch.value.capitalize()}: {state.diagnostics[0].message}"
        return BranchOutcome(branch=d.branch, status=StudyStatus.REFUSED,
                             unresolved={q.key: message for q in MANAGEMENT_BRANCH_QUANTITIES},
                             labels=labels, message=message)
    volumes = rel.management_volumes(s.tank_volume, s.density, s.loaded_mass, s.present_mass,
                                     s.available_mass, s.residual_mass)
    if volumes.value is None:
        message = volumes.diagnostics[0].message
        return BranchOutcome(branch=d.branch, status=StudyStatus.REFUSED,
                             unresolved={q.key: message for q in MANAGEMENT_BRANCH_QUANTITIES},
                             labels=labels, message=message)
    v, st = volumes.value, state.value
    labels["outlet_availability"] = _AVAILABILITY_WORDS[st.availability.value]
    labels["availability_basis"] = st.statement
    q = {"tank_volume": s.tank_volume, "density": s.density, "fill_fraction": s.fill_fraction,
         "ullage_fraction": s.ullage_fraction, "ullage_volume": s.ullage_volume,
         "liquid_volume_present": v.liquid_volume_present,
         "gas_volume_start": v.gas_volume_start,
         "ullage_fraction_start": v.ullage_fraction_start,
         "expelled_volume": v.expelled_volume, "gas_volume_end": v.gas_volume_end,
         "ullage_fraction_end": v.ullage_fraction_end,
         "expulsion_efficiency": s.expulsion_efficiency, "residual_mass": s.residual_mass,
         "residual_volume": v.residual_volume,
         "fill_ullage_closure": s.fill_fraction + s.ullage_fraction - 1.0,
         "volume_closure": v.volume_closure,
         "inventory_closure": math.fsum([s.available_mass, s.residual_mass, s.boiloff_mass])
                              / s.loaded_mass - 1.0}
    unresolved = {}
    if d.settling_acceleration is None:
        unresolved["settling_acceleration"] = "Not stated; recorded only when it is."
    else:
        q["settling_acceleration"] = d.settling_acceleration
    unavailable = st.availability is rel.Availability.UNRESOLVED
    notes = tuple(f"{d.branch.value.capitalize()}: {a}" for a in st.advisories)
    return BranchOutcome(branch=d.branch,
                         status=StudyStatus.INCOMPLETE if unavailable else StudyStatus.OK,
                         quantities=q, unresolved=unresolved, labels=labels, notes=notes)


def solve_management(definition: ManagementDefinition) -> StudyResult:
    """Both branches. Never raises for a stated input."""
    ox = _solve_branch(definition.oxidiser, definition.basis)
    fu = _solve_branch(definition.fuel, definition.basis)
    if not (ox.ok and fu.ok):
        status = StudyStatus.REFUSED
        message = " ".join(m for m in (ox.message, fu.message) if m)
    else:
        status = (StudyStatus.INCOMPLETE if StudyStatus.INCOMPLETE in (ox.status, fu.status)
                  else StudyStatus.OK)
        message = ""
    return StudyResult(schema=MANAGEMENT_SCHEMA, definition=definition, status=status,
                       oxidiser=ox, fuel=fu, message=message, assumptions=ASSUMPTIONS,
                       provenance=provenance(definition))


def provenance(definition: ManagementDefinition) -> dict[str, str]:
    basis = definition.basis
    return {
        "management": "RocketForge engineering.propulsion_system.propellant_management: "
                      "Sutton & Biblarz 9th ed. §6.2, Table 6-2 (qualitative, not used "
                      "numerically)",
        "inventory": f"SYS-1 inventory {basis.inventory.fingerprint[:12]}",
        "tanks": f"SYS-2 tanks {basis.tanks.fingerprint[:12]}",
    }


DISPLAY: dict[str, tuple[str, float, str]] = {
    **{k: ("m³", 1.0, ",.6f") for k in ("tank_volume", "ullage_volume", "liquid_volume_present",
                                        "gas_volume_start", "expelled_volume", "gas_volume_end",
                                        "residual_volume")},
    **{k: ("%", 100.0, ".4f") for k in ("fill_fraction", "ullage_fraction",
                                        "ullage_fraction_start", "ullage_fraction_end",
                                        "expulsion_efficiency")},
    "density": ("kg/m³", 1.0, ",.3f"),
    "residual_mass": ("kg", 1.0, ",.4f"),
    "settling_acceleration": ("m/s²", 1.0, ",.4g"),
    "fill_ullage_closure": ("", 1.0, ".1e"),
    "volume_closure": ("", 1.0, ".1e"),
    "inventory_closure": ("", 1.0, ".1e"),
}

GROUPS = (("loading", "At loading"), ("burn", "Through the burn"), ("residual", "Residual"),
          ("intent", "Settling intent"), ("closure", "Closure"))
LABELS = (("management_mode", "Management"), ("environment", "Environment"),
          ("settling", "Settling"), ("outlet_availability", "Outlet coverage"),
          ("availability_basis", "Basis"), ("expulsion_source", "Expulsion efficiency"))


def branch_view(outcome: BranchOutcome) -> dict:
    return {"groups": present.branch_groups(outcome, MANAGEMENT_BRANCH_QUANTITIES, GROUPS,
                                            DISPLAY),
            "labels": present.label_rows(outcome, LABELS)}

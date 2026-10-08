"""Propellant tank geometry and packaging (SYS-2): resolve, compute, present. Qt-free.

The input is an accepted, complete SYS-1 inventory::

    complete SYS-1 inventory  --(loaded mass per branch, identity)-->   TanksBasis
    stated per branch: density or its storage state, ullage, shape,     TankDefinition
                       the dimension that fixes it, optional envelope
        engineering.propulsion_system.tank_geometry.tank_volumes          once per branch
        engineering.propulsion_system.tank_geometry.solve_tank_geometry   once per branch

**Nothing is resolved silently.** :func:`tanks_basis` refuses a missing,
stale, refused or incomplete inventory: a tank holds the loaded mass, and an
unresolved load has no volume. The ullage, the shape, the fixing dimension and
the density have no default.

**Density.** Either stated, or from the validated fluid-property model --
only for a propellant with a validated liquid binding (LOX, LCH4, LH2) and at
a storage temperature and pressure the user states. The LIQ-3 stream
temperature is the injector feed state, not the storage state, and is not
used. The model is reached only by :func:`solve_tanks`, on the user's Compute.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.engine.propulsion_system.records import (
    Branch,
    BranchOutcome,
    StudyResult,
    StudyStatus,
    Upstream,
)
from rocketforge.engine.propulsion_system.tanks import (
    TANK_BRANCH_QUANTITIES,
    TANK_SCHEMA,
    TANK_TOTALS,
    DensitySource,
    SizingMode,
    TankBranchDefinition,
    TankDefinition,
    TanksBasis,
    TankShape,
    UllageMode,
)
from rocketforge.engineering.propellants import PRODUCTION_FLUID_MAPPING

from . import system_presentation as present

__all__ = [
    "ASSUMPTIONS",
    "DISPLAY",
    "BranchSettings",
    "TankIssue",
    "build_definition",
    "fluid_model_supported",
    "solve_tanks",
    "tanks_basis",
]


@dataclass(frozen=True, slots=True)
class BranchSettings:
    """What the user states for one tank, SI. Nothing has a value to start."""

    density_source: DensitySource = DensitySource.STATED
    density: float | None = None                  # kg/m^3
    storage_temperature: float | None = None      # K
    storage_pressure: float | None = None         # Pa
    ullage_mode: UllageMode | None = None
    ullage_value: float | None = None             # fraction, or m^3
    shape: TankShape | None = None
    sizing_mode: SizingMode | None = None         # for a cylinder
    diameter: float | None = None                 # m
    total_length: float | None = None             # m
    dome_ratio: float | None = None
    envelope_diameter: float | None = None        # m, optional
    envelope_length: float | None = None          # m, optional


@dataclass(frozen=True, slots=True)
class TankIssue:
    code: str
    field: str
    message: str


def tanks_basis(inventory: StudyResult | None, stale: bool
                ) -> tuple[TanksBasis | None, tuple[TankIssue, ...]]:
    """The loaded masses of a current, complete inventory, or why not."""
    def refuse(code: str, message: str):
        return None, (TankIssue(code, "inventory", message),)

    if inventory is None:
        return refuse("NO_INVENTORY", "No propellant inventory has been computed. Compute "
                      "one on the Propellant Inventory page.")
    if stale:
        return refuse("INVENTORY_STALE", "The propellant inventory is stale: the sizing, the "
                      "burn time or its budget changed since it was computed. Compute it "
                      "again.")
    if not inventory.ok:
        return refuse("INVENTORY_REFUSED", "The propellant inventory was refused, so there is "
                      "no loaded mass to store.")
    loads = [inventory.oxidiser.value("loaded_mass"), inventory.fuel.value("loaded_mass")]
    if inventory.status is not StudyStatus.OK or any(v is None for v in loads):
        return refuse("INVENTORY_INCOMPLETE", "The propellant inventory's loaded mass waits "
                      "on unresolved terms. Resolve them first: an unknown load has no "
                      "volume.")
    d = inventory.definition
    return TanksBasis(
        inventory=Upstream("SYS-1", d.fingerprint, inventory.status.value),
        sizing_fingerprint=d.basis.sizing.fingerprint, pair_label=d.basis.pair_label,
        oxidiser=d.basis.oxidiser, fuel=d.basis.fuel,
        oxidiser_loaded_mass=loads[0], fuel_loaded_mass=loads[1]), ()


_FLUID_MODEL_PROPELLANTS = frozenset(PRODUCTION_FLUID_MAPPING.bindings)


def fluid_model_supported(propellant: str) -> bool:
    """A set lookup; reaches no provider."""
    return propellant in _FLUID_MODEL_PROPELLANTS


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _branch_definition(branch: Branch, basis: TanksBasis, s: BranchSettings
                       ) -> tuple[TankBranchDefinition | None, list[TankIssue]]:
    name = branch.value
    word = "oxidiser" if branch is Branch.OXIDISER else "fuel"
    issues: list[TankIssue] = []

    def need(field_name: str, code: str, value, missing: str, valid, invalid: str) -> None:
        if value is None:
            issues.append(TankIssue(f"{code}_UNRESOLVED", f"{name}.{field_name}", missing))
        elif not (_finite(value) and valid(value)):
            issues.append(TankIssue(f"{code}_INVALID", f"{name}.{field_name}", invalid))

    fluid = s.density_source is DensitySource.FLUID_MODEL
    if not fluid:
        need("density", "DENSITY", s.density,
             f"State the {word} storage density, or use its validated fluid model.",
             lambda v: v > 0.0, f"The {word} density must be finite and above zero.")
    elif not fluid_model_supported(basis.propellant_of(branch)):
        issues.append(TankIssue("DENSITY_MODEL_UNSUPPORTED", f"{name}.density_source",
                                f"{basis.propellant_of(branch)} has no validated fluid "
                                "model; state its storage density."))
    else:
        need("storage_temperature", "STORAGE_TEMPERATURE", s.storage_temperature,
             f"State the {word} storage temperature for the fluid model.",
             lambda v: v > 0.0, f"The {word} storage temperature must be above zero.")
        need("storage_pressure", "STORAGE_PRESSURE", s.storage_pressure,
             f"State the {word} storage pressure for the fluid model.",
             lambda v: v > 0.0, f"The {word} storage pressure must be above zero.")
    if s.ullage_mode is None:
        issues.append(TankIssue("ULLAGE_UNRESOLVED", f"{name}.ullage_mode",
                                f"State the {word} ullage, as a fraction of the tank or a "
                                "volume. None is assumed."))
    elif s.ullage_mode is UllageMode.FRACTION:
        need("ullage", "ULLAGE", s.ullage_value, f"State the {word} ullage fraction.",
             lambda v: 0.0 <= v < 1.0,
             f"The {word} ullage fraction must be at or above 0 % and below 100 %.")
    else:
        need("ullage", "ULLAGE", s.ullage_value, f"State the {word} ullage volume.",
             lambda v: v >= 0.0, f"The {word} ullage volume must be at or above zero.")
    if s.shape is None:
        issues.append(TankIssue("SHAPE_UNRESOLVED", f"{name}.shape",
                                f"Choose the {word} tank shape. None is chosen for you."))
    elif s.shape is not TankShape.SPHERE:
        if s.sizing_mode not in (SizingMode.STATED_DIAMETER, SizingMode.STATED_LENGTH):
            issues.append(TankIssue("SIZING_MODE_UNRESOLVED", f"{name}.sizing_mode",
                                    f"State whether the {word} tank's diameter or its length "
                                    "is given."))
        elif s.sizing_mode is SizingMode.STATED_DIAMETER:
            need("diameter", "DIAMETER", s.diameter, f"State the {word} tank diameter.",
                 lambda v: v > 0.0, f"The {word} tank diameter must be above zero.")
        else:
            need("total_length", "LENGTH", s.total_length, f"State the {word} tank length.",
                 lambda v: v > 0.0, f"The {word} tank length must be above zero.")
        if s.shape is TankShape.CYLINDER_ELLIPSOIDAL:
            need("dome_ratio", "DOME_RATIO", s.dome_ratio,
                 f"State the {word} dome height-to-radius ratio k.",
                 lambda v: 0.0 < v <= 1.0,
                 f"The {word} dome ratio k must be above 0 and at most 1.")
    for field_name, value in (("envelope_diameter", s.envelope_diameter),
                              ("envelope_length", s.envelope_length)):
        if value is not None and not (_finite(value) and value > 0.0):
            issues.append(TankIssue("ENVELOPE_INVALID", f"{name}.{field_name}",
                                    f"The {word} envelope must be finite and above zero."))
    if issues:
        return None, issues
    sphere = s.shape is TankShape.SPHERE
    mode = SizingMode.VOLUME if sphere else s.sizing_mode
    return TankBranchDefinition(
        branch=branch, density_source=s.density_source,
        density=None if fluid else float(s.density),
        storage_temperature=float(s.storage_temperature) if fluid else None,
        storage_pressure=float(s.storage_pressure) if fluid else None,
        ullage_mode=s.ullage_mode, ullage_value=float(s.ullage_value), shape=s.shape,
        sizing_mode=mode,
        diameter=float(s.diameter) if mode is SizingMode.STATED_DIAMETER else None,
        total_length=float(s.total_length) if mode is SizingMode.STATED_LENGTH else None,
        dome_ratio=float(s.dome_ratio) if s.shape is TankShape.CYLINDER_ELLIPSOIDAL else None,
        envelope_diameter=None if s.envelope_diameter is None else float(s.envelope_diameter),
        envelope_length=None if s.envelope_length is None else float(s.envelope_length)), []


def build_definition(basis: TanksBasis | None, oxidiser: BranchSettings, fuel: BranchSettings
                     ) -> tuple[TankDefinition | None, tuple[TankIssue, ...]]:
    if basis is None:
        return None, ()
    ox, ox_issues = _branch_definition(Branch.OXIDISER, basis, oxidiser)
    fu, fu_issues = _branch_definition(Branch.FUEL, basis, fuel)
    if ox is None or fu is None:
        return None, tuple(ox_issues + fu_issues)
    return TankDefinition(basis, ox, fu), ()


# ---------------------------------------------------------------------------
# computing
# ---------------------------------------------------------------------------

ASSUMPTIONS: tuple[str, ...] = (
    "Each tank holds its branch's SYS-1 loaded mass as liquid at one storage density: "
    "V_liquid = m / ρ. No thermal stratification, no density change during storage.",
    "Ullage, after Sutton 9th ed. §6.2, is the gas volume above the liquid. It is stated as "
    "a fraction u of the tank, V_tank = V_liquid / (1 − u), or as a volume, "
    "V_tank = V_liquid + V_u. None is assumed.",
    "Internal geometry only: a sphere, or a cylinder with two equal domes, each half a "
    "spheroid of height k R (k = 1 hemispherical; 0 < k < 1 ellipsoidal).",
    "The shape and the dimension that fixes it are stated. No shape, diameter or optimum is "
    "chosen, and a geometry that cannot hold the volume is refused.",
    "No wall thickness, stress, MEOP, tank mass, insulation, common bulkhead, boil-off, "
    "pressurization, slosh or propellant-management device.",
)


def _density(d: TankBranchDefinition, basis: TanksBasis) -> tuple[float | None, dict, str]:
    if d.density_source is DensitySource.STATED:
        return d.density, {"source": "Stated by the user"}, ""
    from rocketforge.core.errors import DomainError
    from rocketforge.engineering.propellants import stream_density

    from . import fluid_property_provider as gateway

    propellant = basis.propellant_of(d.branch)
    available = gateway.availability()
    if not available.is_usable:
        return None, {}, (f"No validated fluid model is installed for the {propellant} "
                          f"density. {available.detail} Or state the density.")
    try:
        stream = stream_density(gateway.property_provider(),
                                PRODUCTION_FLUID_MAPPING.require(propellant),
                                d.storage_temperature, d.storage_pressure)
    except DomainError as error:
        return None, {}, f"{error} State the density instead."
    record = {k: str(v) for k, v in stream.as_mapping().items()}
    record["source"] = (f"{stream.provider_label} {stream.library_version}, "
                        f"{stream.fluid_name} at {stream.temperature:g} K and "
                        f"{stream.pressure:g} Pa ({stream.phase})")
    return stream.density, record, ""


_SHAPE_WORDS = {TankShape.SPHERE: "Sphere",
                TankShape.CYLINDER_HEMISPHERICAL: "Cylinder, hemispherical domes",
                TankShape.CYLINDER_ELLIPSOIDAL: "Cylinder, ellipsoidal domes"}


def _solve_branch(d: TankBranchDefinition, basis: TanksBasis) -> BranchOutcome:
    from rocketforge.engineering.propulsion_system import tank_geometry as rel

    def refused(message: str) -> BranchOutcome:
        return BranchOutcome(branch=d.branch, status=StudyStatus.REFUSED,
                             unresolved={q.key: message for q in TANK_BRANCH_QUANTITIES},
                             message=message)

    density, density_provenance, refusal = _density(d, basis)
    if density is None:
        return refused(refusal)
    fraction = d.ullage_mode is UllageMode.FRACTION
    volumes = rel.tank_volumes(basis.loaded_mass_of(d.branch), density,
                               ullage_fraction=d.ullage_value if fraction else None,
                               ullage_volume=None if fraction else d.ullage_value)
    if volumes.value is None:
        return refused(volumes.diagnostics[0].message)
    v = volumes.value
    geometry = rel.solve_tank_geometry(
        v.tank_volume, rel.TankShape(d.shape.value), rel.SizingMode(d.sizing_mode.value),
        diameter=d.diameter, total_length=d.total_length,
        dome_ratio=(1.0 if d.shape is TankShape.CYLINDER_HEMISPHERICAL else d.dome_ratio),
        envelope_diameter=d.envelope_diameter, envelope_length=d.envelope_length)
    if geometry.value is None:
        return refused(f"{d.branch.value.capitalize()} tank: "
                       f"{geometry.diagnostics[0].message}")
    g = geometry.value
    q = {"liquid_mass": v.liquid_mass, "density": v.density, "liquid_volume": v.liquid_volume,
         "ullage_fraction": v.ullage_fraction, "ullage_volume": v.ullage_volume,
         "tank_volume": v.tank_volume, "fill_fraction": v.fill_fraction,
         "diameter": g.diameter, "total_length": g.total_length,
         "surface_area": g.surface_area, "geometric_volume": g.geometric_volume,
         "volume_closure": g.volume_closure, "mass_closure": v.mass_closure,
         "ullage_closure": v.ullage_closure}
    unresolved: dict[str, str] = {}
    if g.barrel_length is None:
        sphere = "A sphere has no barrel and no domes."
        unresolved.update({k: sphere for k in ("barrel_length", "dome_ratio", "dome_height",
                                               "dome_volume")})
    else:
        q.update({"barrel_length": g.barrel_length, "dome_ratio": g.dome_ratio,
                  "dome_height": g.dome_height, "dome_volume": g.dome_volume})
    return BranchOutcome(
        branch=d.branch, status=StudyStatus.OK, quantities=q, unresolved=unresolved,
        labels={"shape": _SHAPE_WORDS[d.shape],
                "density_source": density_provenance.get("source", "")},
        provenance=density_provenance)


def solve_tanks(definition: TankDefinition) -> StudyResult:
    """Both tanks and the totals. Never raises for a stated input."""
    ox = _solve_branch(definition.oxidiser, definition.basis)
    fu = _solve_branch(definition.fuel, definition.basis)
    totals: dict[str, float] = {}
    missing: dict[str, str] = {}
    if not (ox.ok and fu.ok):
        status = StudyStatus.REFUSED
        message = " ".join(m for m in (ox.message, fu.message) if m)
        missing = {q.key: "A tank was refused." for q in TANK_TOTALS}
    else:
        for key, branch_key in (("tank_volume_total", "tank_volume"),
                                ("liquid_volume_total", "liquid_volume"),
                                ("ullage_volume_total", "ullage_volume"),
                                ("surface_area_total", "surface_area")):
            totals[key] = ox.value(branch_key) + fu.value(branch_key)
        status, message = StudyStatus.OK, ""
    return StudyResult(schema=TANK_SCHEMA, definition=definition, status=status, oxidiser=ox,
                       fuel=fu, totals=totals, totals_unresolved=missing, message=message,
                       assumptions=ASSUMPTIONS, provenance=provenance(definition))


def provenance(definition: TankDefinition) -> dict[str, str]:
    basis = definition.basis
    return {
        "geometry": "RocketForge engineering.propulsion_system.tank_geometry: Sutton & "
                    "Biblarz 9th ed. §6.2; analytic sphere, cylinder and half-spheroid",
        "inventory": f"SYS-1 inventory {basis.inventory.fingerprint[:12]}",
        "sizing": f"LIQ-4 sizing {basis.sizing_fingerprint[:12]}, {basis.pair_label}",
    }


# ---------------------------------------------------------------------------
# presentation
# ---------------------------------------------------------------------------

DISPLAY: dict[str, tuple[str, float, str]] = {
    "liquid_mass": ("kg", 1.0, ",.4f"),
    "density": ("kg/m³", 1.0, ",.3f"),
    "liquid_volume": ("m³", 1.0, ",.6f"),
    "ullage_fraction": ("%", 100.0, ".4f"),
    "ullage_volume": ("m³", 1.0, ",.6f"),
    "tank_volume": ("m³", 1.0, ",.6f"),
    "fill_fraction": ("%", 100.0, ".4f"),
    "diameter": ("m", 1.0, ",.5f"),
    "barrel_length": ("m", 1.0, ",.5f"),
    "dome_ratio": ("", 1.0, ".6g"),
    "dome_height": ("m", 1.0, ",.5f"),
    "dome_volume": ("m³", 1.0, ",.6f"),
    "total_length": ("m", 1.0, ",.5f"),
    "surface_area": ("m²", 1.0, ",.5f"),
    "geometric_volume": ("m³", 1.0, ",.6f"),
    "volume_closure": ("", 1.0, ".1e"),
    "mass_closure": ("", 1.0, ".1e"),
    "ullage_closure": ("", 1.0, ".1e"),
    "tank_volume_total": ("m³", 1.0, ",.6f"),
    "liquid_volume_total": ("m³", 1.0, ",.6f"),
    "ullage_volume_total": ("m³", 1.0, ",.6f"),
    "surface_area_total": ("m²", 1.0, ",.5f"),
}

GROUPS = (("volume", "Volume"), ("geometry", "Geometry"), ("closure", "Closure"))
LABELS = (("shape", "Shape"), ("density_source", "Density"))


def branch_view(outcome: BranchOutcome) -> dict:
    return {"groups": present.branch_groups(outcome, TANK_BRANCH_QUANTITIES, GROUPS, DISPLAY),
            "labels": present.label_rows(outcome, LABELS)}


def total_rows(result: StudyResult) -> list[dict[str, str]]:
    return present.total_rows(result, TANK_TOTALS, DISPLAY)

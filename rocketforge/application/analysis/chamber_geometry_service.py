"""Combustion-chamber geometry (LIQ-5): resolve, compute, present. Qt-free.

The input is an accepted LIQ-4 sizing, read as LIQ-4 produced it::

    accepted LIQ-4 sizing  --(At, Dt, identity)-->  ThroatBasis
    stated L*, Ac/At, half-angle                    GeometryDefinition
        engineering.chamber_geometry.cylindrical_conical_chamber   the relations, once
        Dc, closures                                       presentation of the result

**Nothing is resolved silently.** :func:`throat_basis` refuses a missing,
stale, refused or incomplete sizing. :func:`build_definition` refuses a
geometry until L*, the contraction ratio and the half-angle are all stated:
none has a default, and no optimum is looked for.

No provider is reached. The geometry is algebra on the sizing's throat, and it
runs only when :func:`solve_geometry` is called.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from rocketforge.engine.chamber_geometry import (
    GEOMETRY_QUANTITIES,
    GeometryDefinition,
    GeometryResult,
    GeometryStatus,
    ThroatBasis,
)
from rocketforge.engine.chamber_sizing import SizingResult

__all__ = [
    "DISPLAY",
    "GROUPS",
    "GeometryIssue",
    "GeometrySettings",
    "build_definition",
    "display_value",
    "profile",
    "provenance",
    "quantity_groups",
    "solve_geometry",
    "throat_basis",
]


@dataclass(frozen=True, slots=True)
class GeometrySettings:
    """What the user states. Every value starts unset; none has a default."""

    characteristic_length: float | None = None       # m
    contraction_ratio: float | None = None
    converging_half_angle_deg: float | None = None   # degrees


@dataclass(frozen=True, slots=True)
class GeometryIssue:
    code: str
    field: str
    message: str


def throat_basis(sizing: SizingResult | None, stale: bool
                 ) -> tuple[ThroatBasis | None, tuple[GeometryIssue, ...]]:
    """The throat of an accepted LIQ-4 sizing, or why there is none."""
    if sizing is None:
        return None, (GeometryIssue("NO_SIZING", "sizing",
                                    "No thrust-chamber sizing has been run. Size one on the "
                                    "Thrust Chamber Sizing page."),)
    if stale:
        return None, (GeometryIssue("SIZING_STALE", "sizing",
                                    "The thrust-chamber sizing is stale: the trade selection "
                                    "or its nozzle changed since it ran. Size again."),)
    if not sizing.ok:
        return None, (GeometryIssue("SIZING_REFUSED", "sizing",
                                    "The thrust-chamber sizing was refused, so there is no "
                                    "throat to extend."),)
    area, diameter = sizing.value("throat_area"), sizing.value("throat_diameter")
    if area is None or diameter is None:
        return None, (GeometryIssue("SIZING_INCOMPLETE", "sizing",
                                    "The thrust-chamber sizing carries no throat."),)
    definition = sizing.definition
    point = definition.point
    return ThroatBasis(
        sizing_fingerprint=definition.fingerprint,
        sizing_status=sizing.status.value,
        sizing_provenance=dict(sizing.provenance),
        trade_fingerprint=point.trade_fingerprint,
        pair_key=point.pair_key, pair_label=point.pair_label,
        chamber_pressure=point.chamber_pressure, thrust=point.thrust,
        area_ratio=definition.area_ratio,
        throat_area=area, throat_diameter=diameter,
    ), ()


_STATED = (
    ("characteristic_length", "CHARACTERISTIC_LENGTH",
     "State the characteristic length L*. No default or typical value is assumed.",
     "L* must be finite and above zero.",
     lambda v: v > 0.0),
    ("contraction_ratio", "CONTRACTION_RATIO",
     "State the contraction ratio Ac/At. No default is assumed.",
     "Ac/At must be finite and above 1: the chamber must be wider than the throat.",
     lambda v: v > 1.0),
    ("converging_half_angle_deg", "CONVERGING_HALF_ANGLE",
     "State the converging half-angle. No default is assumed.",
     "The converging half-angle must be above 0 and below 90 degrees.",
     lambda v: 0.0 < v < 90.0),
)


def build_definition(basis: ThroatBasis | None, settings: GeometrySettings
                     ) -> tuple[GeometryDefinition | None, tuple[GeometryIssue, ...]]:
    """The stated geometry, or ``None`` and every reason it cannot be built."""
    if basis is None:
        return None, ()
    issues: list[GeometryIssue] = []
    for name, code, missing, invalid, valid in _STATED:
        value = getattr(settings, name)
        if value is None:
            issues.append(GeometryIssue(f"{code}_UNRESOLVED", name, missing))
        elif not (math.isfinite(value) and valid(value)):
            issues.append(GeometryIssue(f"{code}_INVALID", name, invalid))
    if issues:
        return None, tuple(issues)
    # Degrees as stated on the page; radians from here down (``01`` section 8).
    return GeometryDefinition(basis, float(settings.characteristic_length),
                              float(settings.contraction_ratio),
                              math.radians(settings.converging_half_angle_deg)), ()


# ---------------------------------------------------------------------------
# computing
# ---------------------------------------------------------------------------

ASSUMPTIONS: tuple[str, ...] = (
    "Flat injector face, cylindrical chamber, straight conical convergent to the throat "
    "(Sutton §8.2).",
    "Corner radii at the chamber-convergent and convergent-throat junctions neglected "
    "(Sutton §8.2).",
    "Chamber volume Vc is from the injector face to the throat, cylinder and convergent "
    "included; L* = Vc / At (Sutton Eq. 8-9).",
    "Converging volume is the exact conical frustum, (pi/3) L (Rc² + Rc Rt + Rt²): "
    "Sutton Eq. 8-8 with its factor 1/3.",
    "Circular sections. The throat is LIQ-4's, unchanged.",
    "L* fixes a volume only. It does not establish combustion completeness or stability.",
)


def solve_geometry(definition: GeometryDefinition) -> GeometryResult:
    """Compute the chamber. Never raises; a refusal comes back as a result."""
    from rocketforge.core.result import Status
    from rocketforge.engineering.chamber_geometry import cylindrical_conical_chamber

    solution = cylindrical_conical_chamber(
        definition.basis.throat_area, definition.characteristic_length,
        definition.contraction_ratio, definition.converging_half_angle)
    notes = tuple(dict.fromkeys(d.message for d in solution.diagnostics
                                if str(d.severity) in ("warning", "info")))
    g = solution.value
    if g is None:
        error = next((d for d in solution.diagnostics if str(d.severity) == "error"), None)
        message = _refusal_text(error)
        return GeometryResult(
            definition=definition, status=GeometryStatus.REFUSED,
            unresolved={q.key: message for q in GEOMETRY_QUANTITIES},
            message=message, notes=notes, assumptions=ASSUMPTIONS,
            provenance=provenance(definition))
    quantities = {
        "throat_area": definition.basis.throat_area,
        "throat_diameter": definition.basis.throat_diameter,
        "characteristic_length": g.characteristic_length,
        "contraction_ratio": g.contraction_ratio,
        "converging_half_angle": g.converging_half_angle,
        "chamber_volume": g.chamber_volume,
        "chamber_area": g.chamber_area,
        "chamber_diameter": 2.0 * g.chamber_radius,
        "converging_length": g.converging_length,
        "converging_volume": g.converging_volume,
        "converging_volume_fraction": g.converging_volume / g.chamber_volume,
        "cylinder_length": g.cylinder_length,
        "cylinder_volume": g.cylinder_volume,
        "injector_to_throat_length": g.injector_to_throat_length,
        "characteristic_length_closure": g.characteristic_length_closure,
        "contraction_closure": g.contraction_closure,
    }
    return GeometryResult(
        definition=definition,
        status=(GeometryStatus.WARNING if solution.status is Status.OK_WITH_WARNINGS
                else GeometryStatus.OK),
        quantities=quantities, notes=notes, assumptions=ASSUMPTIONS,
        provenance=provenance(definition))


def _refusal_text(error) -> str:
    """The relation's refusal, with its numbers restated in the page's units."""
    if error is None:
        return "The geometry was refused."
    detail = error.detail or {}
    if error.code == "CONVERGING_SECTION_EXCEEDS_CHAMBER_VOLUME" and detail:
        return (f"The converging section alone needs "
                f"{display_value('converging_volume', detail['converging_volume'])} cm³, "
                f"but L* · At allows "
                f"{display_value('chamber_volume', detail['chamber_volume'])} cm³. At this "
                "contraction ratio and half-angle the smallest L* that leaves a cylinder is "
                f"{detail['minimum_characteristic_length']:.4f} m. No input is changed to "
                "make the geometry fit.")
    return str(error.message)


def provenance(definition: GeometryDefinition) -> dict[str, str]:
    """Which relations produced the numbers, and the sizing they extend."""
    basis = definition.basis
    return {
        "geometry": "RocketForge engineering.chamber_geometry: cylinder + conical frustum, "
                    "corner radii neglected",
        "source": "Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., §8.2, "
                  "Eqs. 8-8 (frustum 1/3 restored) and 8-9",
        "sizing": f"LIQ-4 sizing {basis.sizing_fingerprint[:12]}, {basis.pair_key}, "
                  f"Ae/At {basis.area_ratio:g}",
        "trade": f"LIQ-3 trade {basis.trade_fingerprint[:12]}",
        "sizing_chamber": basis.sizing_provenance.get("chamber", ""),
    }


# ---------------------------------------------------------------------------
# presentation
# ---------------------------------------------------------------------------

#: Display unit, scale and format per quantity. Conversion happens here only.
DISPLAY: dict[str, tuple[str, float, str]] = {
    "throat_area": ("cm²", 1.0e4, ",.3f"),
    "throat_diameter": ("mm", 1.0e3, ",.2f"),
    "characteristic_length": ("m", 1.0, ",.4f"),
    "contraction_ratio": ("", 1.0, ".6g"),
    "converging_half_angle": ("°", 180.0 / math.pi, ".6g"),
    "chamber_volume": ("cm³", 1.0e6, ",.1f"),
    "chamber_area": ("cm²", 1.0e4, ",.2f"),
    "chamber_diameter": ("mm", 1.0e3, ",.2f"),
    "converging_length": ("mm", 1.0e3, ",.2f"),
    "converging_volume": ("cm³", 1.0e6, ",.1f"),
    "converging_volume_fraction": ("%", 100.0, ".2f"),
    "cylinder_length": ("mm", 1.0e3, ",.2f"),
    "cylinder_volume": ("cm³", 1.0e6, ",.1f"),
    "injector_to_throat_length": ("mm", 1.0e3, ",.2f"),
    "characteristic_length_closure": ("", 1.0, ".1e"),
    "contraction_closure": ("", 1.0, ".1e"),
}

GROUPS: tuple[tuple[str, str], ...] = (
    ("inputs", "Throat and stated inputs"),
    ("chamber", "Chamber"),
    ("converging", "Converging section"),
    ("lengths", "Cylinder and overall length"),
    ("closure", "Closure"),
)


def display_value(key: str, value: float | None) -> str:
    if value is None:
        return "—"
    _unit, scale, spec = DISPLAY[key]
    return format(value * scale, spec)


def quantity_groups(result: GeometryResult) -> list[dict[str, Any]]:
    """Every quantity, grouped for display, with its unit, note and reason."""
    groups = []
    for key, title in GROUPS:
        rows = [{"key": q.key, "label": q.label, "unit": DISPLAY[q.key][0],
                 "note": q.note, "value": display_value(q.key, result.value(q.key)),
                 "reason": result.unresolved.get(q.key, "")}
                for q in GEOMETRY_QUANTITIES if q.group == key]
        groups.append({"key": key, "title": title, "rows": rows})
    return groups


def profile(result: GeometryResult) -> list[dict[str, float]]:
    """The wall contour, injector face to throat, in mm: (axial x, radius r).

    Drawn from the result's own numbers; nothing is recomputed. Empty for a
    refusal.
    """
    if not result.ok:
        return []
    q = result.quantities
    rc, rt = q["chamber_diameter"] / 2.0e-3, q["throat_diameter"] / 2.0e-3
    cylinder, total = q["cylinder_length"] * 1.0e3, q["injector_to_throat_length"] * 1.0e3
    return [{"x": 0.0, "r": 0.0}, {"x": 0.0, "r": rc}, {"x": cylinder, "r": rc},
            {"x": total, "r": rt}]

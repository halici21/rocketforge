# SYS-2 — Propellant tank geometry and packaging

SYS-2 answers, for each propellant branch: *what tank volume and internal
dimensions are needed to store this load?* It takes a complete SYS-1
inventory's loaded masses. With a stated storage density, ullage, shape and
fixing dimension, it gives the liquid, ullage and tank volumes and the
internal geometry.

It covers internal geometry only. It has no wall thickness, stress, MEOP,
tank mass, insulation, common bulkhead, boil-off, pressurization, slosh or
propellant-management device.

## Where it lives

| Part | Location |
| --- | --- |
| Volume and geometry relations | `rocketforge/engineering/propulsion_system/tank_geometry.py` |
| Basis, definition, quantities | `rocketforge/engine/propulsion_system/tanks.py` |
| Resolution, density source, computation | `rocketforge/application/analysis/propellant_tanks_service.py` |
| QML singleton `PropellantTanks` | `rocketforge/application/analysis/propellant_tanks_controller.py` |
| Page | `ui/pages/TankGeometryPage.qml` (Propulsion System family) |

## Sources

Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., §6.2, pp. 196–197:

- "Any gas volume above the propellant in sealed tanks is called the
  ullage." Sutton quotes 3–10 % of tank volume as usual. SYS-2 neither uses
  nor checks that range.
- The "optimum shape for propellant tanks ... is spherical", and larger
  tanks are "Most ... cylindrical with half ellipses at the ends".

The volume and area relations are exact analytic geometry. They are tested
against independent calculations: numerical surface integration for the
dome area, and hand values.

## Inputs

**From SYS-1, verbatim.** The loaded mass of each branch and the inventory's
identity. `tanks_basis()` refuses these states:

| SYS-1 state | Code |
| --- | --- |
| none | `NO_INVENTORY` |
| stale | `INVENTORY_STALE` |
| refused | `INVENTORY_REFUSED` |
| loaded mass unresolved | `INVENTORY_INCOMPLETE` |

**Stated per tank.** None has a default.

| Input | Domain |
| --- | --- |
| Storage density | stated, > 0; or the validated fluid model (LOX, LCH4, LH2) at a **stated** storage temperature and pressure, liquid phase only |
| Ullage | a fraction of the tank, 0 ≤ u < 1; or a volume, ≥ 0 |
| Shape | sphere · cylinder + hemispherical domes · cylinder + ellipsoidal domes |
| Fixing dimension | sphere: none, the volume fixes it · cylinder: the diameter, or the total length |
| Dome ratio k = h/R | ellipsoidal only: 0 < k ≤ 1 (k = 1 is a hemisphere) |
| Envelope | optional maximum diameter and length |

The LIQ-3 stream temperature is the injector feed state, not the storage
state. It is never used for the storage density.

## Relations

    V_liquid = m / ρ
    V_tank   = V_liquid / (1 − u)          or  V_liquid + V_ullage
    fill     = V_liquid / V_tank

    sphere:     V = 4/3 π R³,                A = 4 π R²
    capsule:    V = π R² L + 2 · 2/3 π R² h,  h = k R
                A = 2 π R L + 2 A_dome
    A_dome (half spheroid, e = √(1 − k²)) = π R² + π h² artanh(e)/e   (→ 2πR² as k → 1)

**Fixing a capsule.** There are two ways, and both are well posed.

- **Diameter stated.** The barrel length is
  L = (V − 2 V_dome)/(π R²). If the domes alone exceed V, the request is
  refused with `DIAMETER_TOO_LARGE`. L = 0 is accepted exactly.
- **Total length L_t stated.** V(R) = π R² L_t − 2/3 π k R³ rises
  monotonically on 0 < R ≤ L_t/(2k). Its largest value is π L_t³/(6 k²),
  two domes with no barrel. A larger V is refused with `LENGTH_TOO_SHORT`.
  Otherwise the one root is found by RocketForge's bracketed Brent solver.

**Envelopes.** A result outside a stated envelope is refused
(`ENVELOPE_*_EXCEEDED`). Nothing is stretched, and no shape or diameter is
chosen.

## Closures

- Mass: ρ V_liquid / m − 1.
- Ullage: (V_liquid + V_ullage)/V_tank − 1.
- Geometric: the volume recomputed from the dimensions, divided by V_tank,
  minus 1.

## Verified

- **Sphere.** Volume and area by hand.
- **Hemispherical capsule.** A 2 m diameter holding 10 m³ needs a barrel of
  1.8497655 m.
- **Ellipsoidal dome.** Area matches numerical surface integration to
  2 × 10⁻⁹ for k = 0.3–1.0. The k = 1/√2 closed form matches by hand.
- **Boundaries.** Zero barrel at both boundaries, and an envelope met exactly
  is accepted.
- **Grid.** 240 cases (mass × density × ullage × shape and mode). Every
  closure is ≤ 2 × 10⁻¹⁴.
- **Refusals.** Impossible packaging, NaN, infinite and out-of-domain
  geometry.
- **Records.** Stale-inventory refusal, and JSON round-trip with a
  fingerprint check.

## Not in SYS-2

Wall thickness, stress and MEOP sizing, tank dry mass, common bulkheads,
insulation, boil-off, pressurization (SYS-4), slosh, and PMD or diaphragm
design (SYS-3 states management intent only). Toroidal and conformal tanks
are also excluded.

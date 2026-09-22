# Solid propellant — missing data record

What RocketForge does **not** have, stated so nobody fills it in by accident.
Nothing on this page has a value, and nothing on it is a preset. Where a value
is missing, the ingredient or case it belongs to does not exist in the product.

Solid Propellant Thermochemistry Phase 1, 2026-09-22.

## Binders

A custom reactant needs exactly four things (`CustomReactant`,
`rocketforge/physics/solid_propellant/formulation.py`):

| Field | Required | Notes |
| --- | --- | --- |
| chemical formula | yes | element → atoms per formula unit; fractional counts are normal for a polymer |
| heat of formation, with units | yes | standard-datum enthalpy at the reference temperature |
| reference temperature | yes | CEA holds the reactant at this enthalpy whatever grain temperature is requested |
| source | yes | the citation the three values above come from |
| molecular weight | no | used when the source states it (recorded "provided"), otherwise derived by CEA from the formula (recorded "derived") |

| Binder | Status | What is missing |
| --- | --- | --- |
| HTPB | **MISSING — not provided** | no independently sourced formula + heat of formation + reference temperature accepted for this project |
| PBAN | **MISSING — not provided** | the same |
| GAP | **MISSING — not provided** | the same |
| NASA RP-1311 Example 5 `CHOS-Binder` | available | the only custom reactant carried; formula, heat of formation, reference temperature and molecular weight are all stated in NASA's example, and it is never relabelled as any real binder |

Why no preset: HTPB, PBAN and GAP are polymers whose formula and heat of
formation vary with manufacturer, lot and cure. Published values differ from
one source to the next, and none has been chosen and accepted for this
project. A preset would pick one silently and present it as *the* binder.
A user who has a sourced definition can build the reactant; one who does not
will find no default to lean on.

**Measured consequence of the molecular-weight choice**: for NASA's binder,
letting CEA derive the molecular weight instead of using the stated one moves
Example 5's chamber temperature by −0.0287 K (−1.05e−05 relative). That is
enough to miss the published 2723.021 K, which is why the reference case keeps
the stated value.

## Ingredients absent from this `thermo.lib`

Probed with `cea.Mixture`, so the list reflects the installed database, not an
assumption:

| Species | Status |
| --- | --- |
| `KNO3(cr)` | absent — potassium-nitrate grains (e.g. KNDX, KNSU) cannot be posed to this provider |
| `KCLO4(cr)` | absent |

## Benchmarks

| Benchmark | Status |
| --- | --- |
| Solid end-to-end chamber benchmark | **one**: NASA RP-1311 Example 5 |
| Simple non-metalised solid benchmark | **missing** — none found with complete, reproducible CEA inputs |
| Solid nozzle-expansion benchmark | **missing** — needed before any solid Isp, C_f or expansion output |
| Published solid c\* | **missing** — the solid c\* is validated against direct CEA only; NASA's printed c\* values (Examples 12, 13) are rocket problems, not solids |
| PROPEP runs | **none present** — the import path exists (`case_from_mapping`), no data has been supplied |
| EXPLO5 runs | **none present** — the same |
| Experimental data | **none present** — the source kind exists; no measurement has been supplied |

PROPEP and EXPLO5 results, when supplied, are compared as **independent codes**:
differences are reported, no verdict is drawn and no code is ranked.

## Elemental formulas of CEA products

For Example 5, 182 of the 205 products have no elemental formula in
RocketForge. CEA's Python API exposes an element *count* but not per-species
composition, the installed `thermo.lib` is a binary file, and NASA's
`thermo.inp` source text is not shipped with the package. Parsing formulas out
of names such as `AL(OH)2CL` would be guessing, so the formula is left empty,
which the `Species` contract defines as "elemental content not available". The
consequence: no element balance can be computed for a solid result. If NASA's
`thermo.inp` is supplied, formulas could be taken from it with provenance.

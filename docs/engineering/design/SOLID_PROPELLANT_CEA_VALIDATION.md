# Solid propellant CEA validation — NASA RP-1311 Example 5

What was checked, against what, and what the differences actually are.

## Why three terms and not two

| Term | What it is |
| --- | --- |
| **official** | NASA's shipped `cea/samples/rp1311/example5.py`, run unmodified, at the precision it prints. Written verbatim to `acceptance/solid_propellant_r1/rp1311_example5_official_output.txt` by `example5_species_validation.py` (that directory is gitignored; the committed record of the printed values is the generated `rocketforge/comparison/rp1311.py`). The RP-1311 printed table itself was not available offline in this workspace; the shipped example is NASA's own executable reproduction of it, and that limit is stated rather than papered over. |
| **direct CEA** | What the installed `cea` 3.3.4 returns, full precision, solved with no RocketForge code in the solve. |
| **RocketForge** | What `rocketforge.providers.cea_solid.solve_solid_chamber` returns. |

Comparing only the first and last would confound two different questions: has
RocketForge mis-plumbed CEA, or does this build of CEA differ from the paper?
The middle term separates them, and it is the reason the tables below have two
difference columns rather than one.

The scripts are `experiments/solid_propellant_r1/example5_direct.py` and
`example5_rocketforge.py`; the recorded output is `example5_threeway.json`.

## The case

NASA RP-1311 Example 5, first pressure column: **34.473652 bar** (500 psia,
printed as 34.023 atm in the source table).

| Ingredient | Mass fraction |
| --- | --- |
| `NH4CLO4(I)` | 0.7206 |
| `CHOS-Binder` | 0.1858 |
| `AL(cr)` | 0.09 |
| `MgO(cr)` | 0.002 |
| `H2O(L)` | 0.0016 |
| **Total** | **1.0 exactly** |

All reactants at 298.15 K. Products derived from the reactants
(`products_from_reactants=True`) with the published 114-entry omit list.

The binder is NASA's own custom reactant, carried verbatim rather than
relabelled as HTPB or PBAN: formula C 1.0 / H 1.86955 / O 0.031256 / S 0.008415,
molecular weight 14.6652984484, assigned enthalpy −2999.082 cal/mol at 298.15 K.

## Result

| Quantity | Official | Direct CEA | RocketForge | Official → direct | Direct → RocketForge |
| --- | --- | --- | --- | --- | --- |
| T, K | 2723.021 | 2723.0209993067942 | 2723.0209993067942 | −6.93e−07 (−2.6e−10 rel) | **0** |
| MW | 22.290 | 22.290074372803055 | 22.290074372803055 | +7.44e−05 (+3.3e−06 rel) | **0** |
| γ_s | 1.1928 | 1.1928007719171934 | 1.1928007719171934 | +7.72e−07 (+6.5e−07 rel) | **0** |
| ρ, g/cc | 3.523e−03 | 3.5233876650271126e−03 | 3.5233876650271126e−03 | +3.88e−07 (+1.1e−04 rel) | **0** |

**RocketForge reproduces direct CEA exactly — bit for bit, on every field.**
The tolerance in that test is exact equality, not a relative bound: the two
paths run the same solver on the same input, so anything looser would hide a
unit conversion applied twice or a value rounded in transit.

Every official-versus-direct difference is smaller than the published
rounding. The largest relative difference, 1.1e−04 on density, is a
consequence of the source printing four significant figures (3.523e−03):
the full-precision value rounds to exactly what is printed.

A second, independent confirmation: the source's second pressure column,
17.236826 bar, is published as 2706.562 K, and the same path returns
2706.5620087988027 K.

## Condensed products, and a correction worth recording

| Quantity | Value |
| --- | --- |
| `AL2O3(L)` **mole** fraction | 0.036724020599401566 (official: 0.036724) |
| `AL2O3(L)` **mass** fraction | 0.16798697793216655 |
| Reported condensed mass fraction | 0.16798697793216655 |
| Condensed candidates reported by the solver | 44 |
| Condensed species actually present | **1** |

**0.036724 is a mole fraction.** RP-1311 prints mole fractions, and the
corresponding mass fraction is 0.168 — quoting one where the other belongs is a
factor-of-4.6 error that still looks like a plausible alumina loading. Both are
recorded here so the distinction cannot be lost.

The candidate count is the strongest evidence yet for ADR-28's rule that
condensed mass is computed from the **returned composition**, never from CEA's
`num_condensed` counter. That counter reports 44 for this grain; 43 of them are
present at exactly zero. Reading the counter would report 43 phases that are
not there.

## Determinism: a solid solve must not disturb the bipropellant path

`cea` holds process-global state, so this is not a rhetorical question. The
check is A / solid / A:

```
A  digest               : 2ae9f38f36292b4a02b8a8bea97f531c0933ed5233d6cb3b2940a52cf5100854
A' digest (after solid) : 2ae9f38f36292b4a02b8a8bea97f531c0933ed5233d6cb3b2940a52cf5100854
opening baseline digest : 2ae9f38f36292b4a02b8a8bea97f531c0933ed5233d6cb3b2940a52cf5100854
```

The canonical LOX/LCH4 case (O/F 3.4, 10 MPa, Tc 3598.2854205339845 K) is
**bit identical** before and after a solid solve, and both match the digest
recorded in `acceptance/solid_propellant_r1/opening_baseline.json` before any
of this work began.

A single run of A would not catch contamination at all — it is the equality of
the first and third that carries the claim. The check also runs its own
negative control: perturbing the third result by 1e−09 K must change the
digest, and does.

## What this validates, and what it does not

**Validated:** the chamber equilibrium state of a solid formulation —
temperature, molar mass, isentropic exponent, density, gas composition,
condensed-phase identity and mass, and provenance.

**Not validated, because not implemented:** c\*, C_f, I_sp, equilibrium or
frozen expansion, burn rate, grain geometry, erosive burning, and motor
performance of any kind. Solid reference performance is deferred to R1.1;
`cea.RocketSolver` is not called anywhere in R1, and a test enforces that.

## Benchmark taxonomy

Two classes, kept apart on purpose. Counting the second as the first would
inflate what this work has actually validated.

### Class A — solid end-to-end benchmark

**NASA RP-1311 Example 5**, and in this workspace it is the only one.

Validates: multi-component formulation, mass-fraction reactant semantics, a
custom reactant, a metal ingredient, significant condensed products, chamber
thermochemistry, and a formulation with no O/F at all.

### Class B — mechanism benchmarks

RP-1311 Examples 12 and 13. Both are bipropellant/hybrid **rocket** problems,
not solid propellants. They are used only for mechanisms the solid chamber path
relies on, and they are **not** additional solid formulations.

| Example | Mechanism validated | Result |
| --- | --- | --- |
| **13** | multi-reactant explicit weights with a condensed *reactant* (`Be(a)`) | chamber T/MW/γ agree with NASA's own chamber station to 4.5e−08 |
| **13** | condensed *product* parsing at scale | `BeO(L)` found, mass fraction 0.358, count invariant holds (12 = 12) |
| **12** | explicit product list whose condensed candidates do not form | `H2O(L)` and `C(gr)` both at exactly 0.0, 2 candidates, invariant holds |
| **12** | `n_frz` station-index semantics | see the hazard note below |

Example 13 is not bit-identical for a measured reason: its rocket solution
reports the chamber pressure at float32 width — 206.84271240234375 bar against
the 206.84271879505718 bar requested, 3.1e−08 relative — and it also runs with
a `BeO(L)` insert and a 1e−10 trace threshold the chamber path does not use.

The rocket solver appears in these tests as an **oracle only**. No production
module calls it, and `tests/test_solid_propellant_architecture.py` enforces it.

## The parallel solver path cannot drift

The solid path carries its own solver invocation, because
`mapping.solve_chamber_raw` derives weights from an O/F and is byte-frozen.
Given the canonical LOX/LCH4 case expressed as explicit weights — same
reactants, proportions, temperatures and product set — **every field of the raw
result is identical**, not merely close. The frozen path hands CEA
un-normalised weights (summing to ~48) and the solid path normalised ones, so
this also shows CEA depends only on the proportions.

## Major products, three ways

Mole fractions at 34.473652 bar. "Official" is the printed column, at
`%10.5g`; direct CEA is full precision.

| Species | Official | Direct CEA | Official → direct (rel) | Direct → RocketForge |
| --- | --- | --- | --- | --- |
| H2 | 0.3215 | 0.32149623835141183 | −1.17e−05 | **0** |
| CO | 0.26455 | 0.26455225426942081 | +8.52e−06 | **0** |
| H2O | 0.14651 | 0.14650505886146292 | −3.37e−05 | **0** |
| HCL | 0.13187 | 0.13186857719022166 | −1.08e−05 | **0** |
| N2 | 0.068332 | 0.068332333895080061 | +4.89e−06 | **0** |
| CO2 | 0.017784 | 0.017783779362474404 | −1.24e−05 | **0** |
| AL2O3(L) | 0.036724 | 0.036724020599401566 | +5.61e−07 | **0** |

Every official-versus-direct difference is within the rounding of a
five-significant-figure printout; the largest, H2O at 3.4e−05, is at the
half-unit of that print. RocketForge matches direct CEA exactly on every
species. HCl at 13 % is the signature of an ammonium-perchlorate grain, and CO
exceeding CO2 by 15× is what an oxygen-poor aluminised propellant should give.

`M, (1/n)` is also compared (23.139863185079239 against a printed 23.140) and
is carried by the provider, though RocketForge reports `MW`.

## The `n_frz` hazard, recorded before R1.1 can trip on it

R1 calls no rocket solver, so nothing here depends on this. (Phase 1 added the
equilibrium c\*, which is fixed at the throat and so is unaffected; the hazard
still belongs to any future expansion work.) It is pinned now
because it is cheap to pin and expensive to discover later.

`n_frz=2` in Example 12 means "frozen from the throat". CEA numbers stations
from **1** — chamber = 1, throat = 2 — while the solution arrays are 0-based,
so the throat is index 1. Measured: with `n_frz=2` the chamber *and* throat are
identical to the equilibrium run, and only the stations after the throat
freeze. Last station: 1124.90 K equilibrium against 637.72 K frozen.

A performance module that read the index as 0-based would mislabel a
frozen-from-throat result. `tests/providers/cea_solid/test_solid_mechanisms.py`
holds this to it.

## Accepted limitations

Stated, not hidden. None of these blocks R1; all of them bound it.

- **One qualifying end-to-end solid benchmark**, RP-1311 Example 5.
- **No simple non-metalised solid benchmark.** Still open, and not invented to
  fill the gap. Independently: this `thermo.lib` does not contain `KNO3(cr)` or
  `KCLO4(cr)`, so the common sugar-propellant cases could not be posed to this
  provider even if their thermochemistry were fully published.
- **No solid nozzle-expansion or reference-performance benchmark**, and so no
  production solid performance output, no internal ballistics and no delivered
  motor performance.
- **The RP-1311 printed table** was not consulted directly; NASA's shipped
  executable example stands in for it, at its printed precision.

### Nakka and PROPEP

Nakka's KNDX and KNSU cases remain useful for conceptual interpretation and
future educational comparison. They are **not** numerical CEA benchmarks here,
for two reasons that are each sufficient: their product tables are PROPEP
output rather than CEA output, and the custom-reactant thermochemistry needed
to reconstruct the reactants exactly is not published with them.

**PROPEP output is not NASA CEA oracle output.** The two identities stay
distinct, and no Nakka number is used to validate anything in this work.

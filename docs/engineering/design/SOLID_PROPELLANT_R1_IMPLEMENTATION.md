# Solid Propellant Thermochemistry R1 — implementation

What was built, what it refuses to do, and the three things that turned out
differently from the design.

Companion documents: `SOLID_PROPELLANT_R1_ARCHITECTURE.md` (the design and the
frozen-contract analysis) and `SOLID_PROPELLANT_CEA_VALIDATION.md` (the
numbers).

## Scope

R1 was narrowed at the Phase-A gate to:

```
FORMULATION -> CEA HP CHAMBER EQUILIBRIUM -> CHAMBER THERMOCHEMISTRY
            -> GAS + CONDENSED PRODUCTS -> PROVENANCE
```

Solid reference performance — c\*, C_f, I_sp, equilibrium and frozen
expansion — is **deferred to R1.1**. It is not implemented, not exposed, and
not stubbed: there is no disabled panel and no "coming soon" control, because a
greyed-out affordance is a promise the build cannot keep.

## What was added

| Layer | Package | Contents |
| --- | --- | --- |
| Domain | `rocketforge/physics/solid_propellant/` | `CustomReactant`, `SolidIngredient`, `SolidFormulation`, `SolidFormulationEquilibriumRequest` |
| Provider | `rocketforge/providers/cea_solid/` | the solve path, the species table, the RP-1311 Example 5 reference case |
| Application | `thermochemistry_solid_service.py` | `SolidCase`, the ingredient catalogue, `solve_solid_case`, conditions and headline |
| Gateway | `thermochemistry_provider.py` | the solid functions — the one door to the provider |
| UI | `ThermoCalculator.qml`, `ThermoChamberSchematic.qml` | propellant selector, formulation editor, single-stream schematic |
| Guard | `performance_service.py` | refuses a solid chamber before the ideal-rocket model sees it |

Nothing inside `rocketforge/physics/thermochemistry/` or
`rocketforge/providers/cea/` was modified. Both freeze manifests still match.

## Three things the design got wrong

Recorded because each was caught by something, and what caught it is the
transferable part.

### 1. `to_chamber_gas` is not reusable — caught by executing it

The design concluded it was, having counted `request.` attribute accesses
inside it and found exactly one (`chamber_pressure`). But it also passes
`request=request` into `ChamberGas`, whose `__post_init__` validates that field
with `isinstance(..., ChamberEquilibriumRequest)`. The coupling was not an
attribute read at all; it was an `isinstance` check one call deeper, in a
different frozen file.

Running it settled it in one line:

```
request=<duck-typed solid request> -> StateConsistencyError
request=None                       -> OK
```

So the solid path assembles its own `ChamberGas` with `request=None`, and the
formulation lives in provenance — which is the field the frozen domain already
designates for reactant input state.

### 2. New files inside a frozen package are also forbidden — caught by the suite

The design read `test_the_recorded_digest_is_independently_reproducible`, which
walks the manifest's file list, and concluded that *adding* a module inside a
frozen package was permitted. It is not:
`test_each_manifest_covers_its_whole_package` `rglob`s each package root and
requires the manifest to equal what is on disk.

The suite rejected the first attempt, naming only the thermochemistry
violation because the assertion fires on the first failing manifest and stops —
the two modules added under `rocketforge/providers/cea/` were the same
violation, unreported only because the test had already halted.

Both moved to sibling packages, which turned out to be the better layout
anyway: each gets a real `__init__.py` and callers import from the package root
instead of reaching into a submodule.

### 3. The curated species table cannot describe a solid's products

`rocketforge/providers/cea/species.py` curates 33 C/H/O species and refuses any
name without an elemental formula. An aluminised perchlorate grain returns
**205** products spanning Al, Cl, N, Mg and S, so the frozen builder refuses the
entire result.

`build_solid_species_table` takes molar mass from CEA itself and phase from the
name suffix — both real — and supplies an elemental formula only for the 23
species that are curated, leaving it empty for the rest. Empty is the field's
own way of saying the content is unavailable, and it genuinely is: CEA's Python
API exposes `num_elements` as a count and no per-species composition. The
alternative would be parsing formulas out of names like `AL(OH)2CL` and
`CHCO,ketyl`, which is guessing. The documented consequence is that these
species cannot take part in an element balance; R1 performs none.

One related gap: the frozen phase classifier maps `(II)` and `(III)` to solid
but not `(I)`, and the Example 5 product set contains `MgSO4(I)` beside
`MgSO4(II)` and `MgSO4(L)`. `solid_phase_of_cea_name` adds that one suffix and
defers to the frozen classifier for everything else, including its refusal
behaviour for markers neither table knows.

## A leak the brief predicted, found by trying it

Section 9 asks that the R1 result model not make it easy to feed a condensed
solid case into the gas-only performance model. Rocket Performance takes its
chamber from the Thermochemistry controller's `chamber_outcome()`, so the
question was whether a solid outcome could reach it. It could.

The frozen reduction already refuses Example 5 — a 0.168 condensed mass
fraction is above its single-phase limit, and it says so well. But a
**non-metalised** grain carries no condensed mass at all. Built through the
editor this brief asks for, it passed straight through and returned `ok` with a
full ideal-rocket result: an unvalidated solid performance claim, which is
exactly what section 7 forbids.

`solve_performance` now refuses a solid chamber explicitly, before the
reduction, and says why. The refusal is tested with a grain that has no
condensed products, because the condensed gate would have hidden a regression
otherwise.

## The defect that only a screenshot found

Every service-level test passed while the solid workspace rendered an **empty
condition rail**. The controller property `resultConditions` read `case.fuel`,
which a solid case does not have; the binding raised, Qt logged a metacall
warning, and the rail rendered nothing.

A QML binding that raises does not crash anything — it just draws nothing. That
is exactly how this project once shipped an empty result rail that a 5688-field
parity check reported as clean.

`tests/application/test_thermochemistry_solid_controller.py` now reads every
property a binding reads, in both modes, and requires none to raise. Reverting
the fix fails five of those tests, including the one written for it.

A second defect, visible only in the image: the chamber schematic still drew an
`OXIDIZER` inlet and a `FUEL · O/F` inlet for a solid grain — a feed topology
the propellant does not have, with a dangling ratio label. It now draws one
`GRAIN` stream on the axis, and no O/F anywhere. That fix then had to be
applied twice: the schematic is instantiated once for the solved state and once
for the empty state, and the second instance kept drawing two streams until a
later capture showed it.

A third, found the same way: at a grain temperature of 320 K the formulation
still carried the tag **"Reference / validation case"**. The composition was
still NASA's, but nobody published a result at that operating point. The tag
now appears only when the grain *and* the operating point are the published
ones; a published composition elsewhere says so instead.

## What the interface does and does not claim

- The propellant selector switches between Bipropellant and Solid. Switching
  **clears the result**: a result belongs to the mode that produced it.
- Ingredients can be **added and removed**. The catalogue offers only what this
  build can model: library species probed present in the installed `thermo.lib`,
  and custom reactants with a sourced definition — one, NASA's binder. No
  generic HTPB or PBAN preset, because no exact CEA representation of either
  has been independently sourced.
- An added ingredient arrives at **0 %**, so the total never moves by itself,
  and removing one does not rescale the rest.
- Each row states where its thermochemistry comes from (`thermo.lib · solid`,
  `custom · assigned enthalpy`) and the temperature CEA is given for it.
- The formulation editor shows mass **percent**, because that is what a
  propellant chemist writes. The division by 100 happens once, at the
  controller boundary; no percent reaches a solver.
- **Total mass** is always visible. A grain that does not close at 100 % is
  refused, never normalised — in words as well as colour.
- Editing one fraction does not rescale the others.
- RP-1311 Example 5 is labelled `Reference case · NASA RP-1311 Example 5`. A
  validation case and a design starting point are different things.
- Every solid result carries: *"Equilibrium chamber state only. Burn rate,
  grain geometry, erosive burning and motor performance are not modelled."*
- There is no O/F row, because CEA reports `o/f = 0.000` for a solid and the
  absence of a ratio is the honest representation.
- A grain temperature the binder cannot follow is **reported, not absorbed**.
  Measured: CEA returns the same enthalpy for the custom binder at 250, 298.15
  and 320 K, because its enthalpy is assigned at one temperature. A 320 K grain
  is therefore solved with the binder at 298.15 K, and the result says so —
  through the same warning the bipropellant path raises for a cryogen, with the
  requested and used temperatures side by side.
- Editing after a solve leaves the result on screen, dimmed and labelled with
  the case that produced it, and marks it stale. The condition rail keeps
  showing the solved composition while the form shows the edit.

## Verification

| Check | Result |
| --- | --- |
| Direct CEA reproduces RP-1311 Example 5 | PASS |
| RocketForge reproduces direct CEA | PASS — bit for bit, scalars and species |
| Major gas products vs the published column | PASS — all within printed rounding |
| Custom binder carried verbatim, and actually consumed | PASS — perturbing its enthalpy by −6000 cal/mol moves Tc by −136 K |
| Condensed parsed from composition, not the counter | PASS — 44 candidates, 1 present |
| Classification agrees with `num_condensed` | PASS — and refuses when it does not |
| Classification independent of product order | PASS — shuffled 5× |
| Explicit-weights path vs the frozen O/F path | PASS — every raw field identical |
| Mechanism: Example 13 condensed reactant/product | PASS — 4.5e−08 |
| Mechanism: Example 12 absent condensed candidates | PASS |
| `n_frz` station semantics pinned for R1.1 | PASS |
| Bipropellant A / solid / A determinism | PASS — identical digests |
| Canonical bipropellant unchanged from the opening baseline | PASS |
| Rocket Performance refuses a solid chamber | PASS — including a non-metalised one |
| Both freeze manifests | PASS — 0 mismatches |
| Full suite, `.venv-cea` | 7199 passed, 2 skipped |
| Full suite, base `.venv` | 6997 passed, 201 skipped |
| Qt warnings during capture | 0 |

Captures: `acceptance/solid_propellant_r1/captures/` — ten images at 1920×1080
and 1366×768, dark and light, covering unsolved, solved, composition, stale,
unbalanced, refused, assigned-enthalpy warning, an added ingredient, and the
bipropellant workspace for comparison.

Archived for reproduction, in `acceptance/solid_propellant_r1/`:
`rp1311_example5_input.json` (the exact direct-CEA input),
`rp1311_example5_official_output.txt` (NASA's example, stdout verbatim),
`example5_validation.json` (every difference) and `opening_baseline.json` (the
pre-work bipropellant digest).

## Accepted limitations

Carried from the validation document, and not hidden: one qualifying
end-to-end solid benchmark; no non-metalised solid benchmark (and no `KNO3` or
`KCLO4` in this `thermo.lib` to pose one to); no solid expansion benchmark, so
no production solid performance, no internal ballistics, no delivered motor
performance; and the RP-1311 printed table stood in for by NASA's shipped
executable example.

## Deferred milestones — documented, not started

### Solid Propellant Performance R1.1

**Entry gate.** At least one authoritative, reproducible solid case carrying
*all* of: complete formulation; complete custom-reactant thermochemistry;
initial reactant state; chamber pressure; nozzle expansion condition;
equilibrium/frozen specification; and published or direct CEA performance
output. Preferably more than one independent case before production acceptance.

Then it may implement and validate CEA reference c\*, C_f, c_eff and I_sp,
equilibrium and frozen expansion, the RocketForge-versus-CEA comparison, and
condensed-phase performance eligibility.

Two things are already in place for it: the solid path yields a standard
`ChamberGas`, so a performance module can consume it without revisiting
anything here; and `n_frz`'s 1-based station numbering is pinned by test.

### Solid Motor / Internal Ballistics

Further out, and needs burn-rate law, grain geometry, burning-area history
`Ab(t)`, `Kn`, chamber-pressure equilibrium and its time evolution, nozzle mass
flow, and thrust history.

Neither milestone starts automatically.

## Acceptance questions

1. **Can RocketForge represent a multi-component solid-propellant formulation
   without bipropellant O/F semantics?** — **YES.** `SolidFormulation` carries
   ingredients and mass fractions; weights go to CEA directly. No synthetic
   O/F, no fuel/oxidiser split, no fake pair. A test asserts the solid request
   is not a `ChamberEquilibriumRequest` and has no `fuel`, `oxidiser` or
   `oxidiser_fuel_ratio` attribute, and another asserts no solid module names
   `MixtureRatio`, `PropellantStream` or `of_ratio_to_weights`.

2. **Does RocketForge reproduce NASA RP-1311 Example 5 chamber equilibrium
   through the production CEA provider?** — **YES.** 2723.0209993067942 K,
   MW 22.290074372803055, γ_s 1.1928007719171934: identical to direct CEA bit
   for bit, and within printed rounding of the published column. The second
   published pressure reproduces too (2706.5620087988027 K against 2706.562).

3. **Are custom reactants represented from explicit provenance-backed CEA
   data?** — **YES.** NASA's `CHOS-Binder` verbatim — formula, molecular
   weight, −2999.082 cal/mol at 298.15 K — never relabelled HTPB or PBAN.
   `source` is a required field, recorded in provenance with the full
   definition. Perturbing its enthalpy moves Tc by 136 K, so it is demonstrably
   consumed rather than passed and ignored.

4. **Are gas and condensed products separated correctly?** — **YES.** By phase
   suffix, order-independently (shuffle-tested), cross-checked against
   `num_condensed` on every solve, and refused on mismatch. `AL2O3(L)` at mole
   0.036724020599401566 / mass 0.16798697793216655, the single condensed
   species present out of 44 candidates.

5. **Does the UI represent significant condensed products without treating them
   as errors?** — **YES.** "Condensed products present", a `CONDENSED`
   annotation and a `liquid` phase column in the product table, the exact
   fraction and the reporting threshold. No error styling; the states stay the
   accepted four.

6. **Does formulation editing preserve stale-vs-solved semantics?** — **YES.**
   Editing after a solve keeps the result, marks it stale in words and badge,
   and the condition rail still shows the solved 72.060 % while the form shows
   73.060 %. Captured and tested.

7. **Are all pre-existing bipropellant outputs unchanged?** — **YES.** The
   canonical LOX/LCH4 digest matches the pre-work baseline exactly, and the
   full suites pass in both environments.

8. **Does A / solid / A provider execution remain deterministic?** — **YES.**
   Bit-identical digests before and after a solid solve, with a negative
   control proving a 1e−09 K change would be caught.

9. **Does the UI state that motor performance and internal ballistics are not
   part of R1?** — **YES.** Every solid result carries "Chamber
   thermochemistry only. Motor/internal-ballistics and delivered performance
   are not modelled.", and Rocket Performance refuses a solid chamber in words.

10. **Is this a scientifically valid foundation for a future solid-performance
    or internal-ballistics program?** — **YES.** It produces a standard
    `ChamberGas` through the frozen converters, reproduces a published case
    exactly, keeps condensed phase a first-class state rather than averaging it
    into the gas, records provenance sufficient to reproduce a result, and
    refuses rather than estimating at every boundary it cannot cross. The one
    caveat R1.1 must respect is already pinned by test: `n_frz` is a 1-based
    station number.

**Verdict: SOLID PROPELLANT THERMOCHEMISTRY R1 — ACCEPTED**, meaning
formulation plus chamber CEA thermochemistry plus gas/condensed products, and
nothing beyond it.

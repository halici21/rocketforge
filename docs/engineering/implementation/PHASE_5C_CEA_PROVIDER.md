# Phase 5C — NASA CEA v3 Production Thermochemistry Provider

The first phase in which a real external chemical-equilibrium solver becomes
part of RocketForge, and the first in which the question is not "can we make
CEA run" but "can we integrate CEA without surrendering RocketForge's
architecture to it".

**Date:** 2026-09-04.
**Type:** production implementation. 11 provider modules, 145 new tests, one
new optional dependency profile, one production packaging change.

---

## Verdict

**READY FOR PHASE 5D**

---

## 1. Baseline

| Gate | Result |
| --- | --- |
| Base opening (`.venv`) | 5542 passed, 1 skipped, pytest exit 0, 54.83 s |
| Frozen Compressible, opening | 22 files byte-identical |
| Base closing | **5609 passed, 79 skipped**, exit 0, 52.05 s |
| CEA-enabled closing | **5690 passed, 1 skipped**, exit 0, 48.11 s |
| CEA-enabled repeat | 5690 passed, 1 skipped, exit 0 — identical |
| Frozen Compressible, closing | **22 files byte-identical**, digest unchanged |

---

## 2. Environments

| | Path | Provider |
| --- | --- | --- |
| Base | `.venv` | **none** — proves optionality on every run |
| Provider-enabled | `.venv-cea` | cea 3.3.4; the official build is made here |
| Cantera oracle | Phase 5B-0 temp env | cantera 3.2.0, deliberately **not** in the build env |

Both use CPython 3.13.2. Nothing was downgraded to make a provider work.

---

## 3. Files

### Created — production

`rocketforge/providers/cea/` (11 modules, 2198 lines): `__init__.py`,
`availability.py`, `errors.py`, `mapping.py`, `naming.py`, `oracle.py`,
`propellants.py`, `provider.py`, `resources.py`, `species.py`, `units.py`.

`rocketforge/application/selftest.py` (138 lines) — the non-user-facing
diagnostic that makes the packaged provider checkable.

`requirements-thermochemistry.txt` — `cea==3.3.4`, pinned exactly.

### Created — tests

`tests/providers/cea/` (8 files, 2357 lines, **145 tests**): `conftest.py`,
`test_cea_mapping.py` (33), `test_cea_provider_live.py` (49),
`test_cea_architecture.py` (18), `test_cea_validation.py` (15),
`test_cea_availability.py` (14), `test_cea_references.py` (10),
`test_cea_cantera_oracle.py` (6).

### Modified

| File | Change |
| --- | --- |
| `rocketforge/physics/thermochemistry/tolerances.py` | added `provider_element_balance_rel_tol` — see §7 |
| `main.py` | dispatches `--selftest-thermochemistry` before the interface starts |
| `packaging/RocketForge.spec` | collects CEA data and binaries when present |
| `build_exe.bat` | prefers `.venv-cea` for the official build |

**No other production file changed.** No QML changed. `requirements.txt`
unchanged.

---

## 4. Architecture

```
    core
      |
    physics.thermochemistry          provider-independent contracts
      ^
      | implements the protocol
      |
    providers.cea                    the NASA CEA adapter
      |
      v
    Solution[ChamberGas]             immutable, provider-independent

    (future)  engineering.nozzle     owns c*, Cf, Isp, thrust
```

The pipeline, and the order is the point:

```
validated request -> provider-specific mapping -> CEA solve
    -> raw snapshot -> unit conversion -> ChamberGas
    -> scientific post-validation -> Solution[ChamberGas]
```

A result CEA reports as converged is still **rejected** if it fails element
conservation. "The solver converged" and "the answer conserves atoms" are
different claims, and only the second is checkable here.

---

## 5. What the integration actually found

Five findings, each measured rather than assumed. The last two changed the
implementation.

### 5.1 CEA ignores the temperature of assigned-enthalpy reactants

**The most significant finding of the phase.** Verified at the library level,
with no RocketForge code in the path:

```
Mixture(['CH4','O2'])       T=[298.15, 298.15] -> H = -1056854.44
                            T=[350.00, 298.15] -> H = -1029844.11   varies
Mixture(['CH4(L)','O2(L)']) T=[111.643, 90.17] -> H = -1577584.52
                            T=[111.643, 95.00] -> H = -1577584.52   identical
                            T=[111.643, 99.00] -> H = -1577584.52   identical
```

Several CEA reactant entries — the cryogenic liquids among them — carry a
single **assigned enthalpy** at one reference condition rather than a
temperature-dependent fit. A caller who sets liquid oxygen to 95 K silently
receives the 90.17 K answer.

Found because a test written to catch a substituted reference temperature
failed for the opposite reason: the adapter *was* passing the stream
temperature, and CEA was ignoring it.

The adapter is correct and does not pass the silence on. It emits
`PROVIDER_ASSIGNED_ENTHALPY_REACTANT` (WARNING) naming both temperatures and
returns `OK_WITH_WARNINGS`. Detection is **empirical** — the enthalpy is
evaluated at two temperatures inside the reactant's declared range — so it
cannot be wrong about a reactant it has measured:

| Assigned | | Temperature-dependent |
| --- | --- | --- |
| `O2(L)` 90.17 K | | `O2` |
| `CH4(L)` 111.643 K | | `CH4` |
| `H2(L)` 20.27 K | | `N2H4(L)` |
| `RP-1` 298.15 K | | |

Gaseous reactants do respond, and the whole pipeline proves it: raising gaseous
methane from 298.15 K to 400 K moves the chamber by **+7.63 K**.

### 5.2 CEA exposes no per-species elemental composition

`Mixture` offers only names and counts; `EqSolver` only counts;
`Reactant.formula` is `None` for library species. Element conservation —
which Phase 5B makes blocking — therefore needs formulae from elsewhere.

It does, however, expose its **own molar masses**, through
`moles_to_weights` on a unit vector (H₂O 18.015280, CO₂ 44.009500, …). Taking
molar masses from CEA removes the atomic-weight-vintage mismatch from every
balance; only the formulae, unambiguous integers, are curated, and a test
checks them against CEA's masses.

### 5.3 The product species set is a modelling decision, and it was measured

`products_from_reactants` yields **124 species** for LOX/CH₄, down to 1e-36,
with names like `CH3C(CH3)2CH3` and `(HCOOH)2` that no safe parser handles.
Measured cost of a curated 28-species set instead: **ΔTc = 0.0005 K,
Δγ/γ = 1.0e-06** — an order of magnitude *below* CEA's own gas-constant
discrepancy of 5.7e-06. The set used is recorded in provenance.

### 5.4 The condensed-candidate trap is live in the production case

`num_condensed` counts candidates in the product *list*, not species present.
The canonical LOX/CH₄ case reports candidates while the mass fraction actually
present is 6.2e-08. Presence is computed from the composition. Both halves are
tested: candidates without presence at O/F 3.4, genuine solid carbon at O/F 0.5.

### 5.5 CEA's name limit is exactly 15 characters

Measured: 16 and longer are rejected with `CEA_INVALID_SIZE` before any lookup;
15 and shorter reach it. `HCHO,formaldehy` is exactly 15 and works. Isolated in
`naming.py`; the domain model is unconstrained.

---

## 6. Units

Every conversion has one owner. All were established by identity, not by
reading a label — the table is in `CEA_PROVIDER_CONTRACT.md` §4 and in
`acceptance/phase_5c/cea_unit_mapping.csv`.

The subtle one: the HP constraint is handed to CEA as **H/R**, in kelvin, and
both operands come from CEA. RocketForge's CODATA constant is deliberately
**not** substituted there; doing so would inject a 5.7e-06 inconsistency into
the solver's own input, which is worse than the known difference in the
reported properties.

---

## 7. `PHASE_5B_CONTRACT_CORRECTION` — provider element-balance tolerance

Phase 5B set `element_balance_rel_tol = 1e-8`, justified from a **single**
Phase 5B-0 sample that closed to 1.04e-09.

Phase 5C measured the real spread of CEA's own convergence residual across
**52 converged solves** (O/F 1.5–7.5, Pc 1–20 MPa), computed from CEA's own
molar masses and mass fractions with no RocketForge conversion in the path:

* worst scale-aware residual **1.864e-08**, at O/F 2.5 / 5 MPa
* worst per-element residual **5.888e-08**
* best 8.6e-11, at oxidiser-rich conditions

Larger at fuel-rich conditions where dissociation is strongest — a
solver-convergence signature, not a mapping defect. `sum(X)` and `sum(Y)` are
machine-perfect, so nothing is truncated. Two of fifteen matrix cases were
being rejected by the strict tolerance.

**Correction:** `provider_element_balance_rel_tol = 1e-6`, a new named category
parallel to `provider_identity_rel_tol`. It clears the measured worst case by
~50× while remaining four orders of magnitude tighter than any real chemistry
error. **The strict 1e-8 is unchanged** for RocketForge's own algebra.

Proved to still bite: a dropped product species, an inverted O/F, a doubled
species molar mass and an altered formula all fail at the *provider* tolerance
by residuals above 1e-2 — four orders of magnitude clear of the relaxation.

---

## 8. Validation

### Mutation proofs, at the provider tolerances

| Mutation | Caught by |
| --- | --- |
| density ×1.01 | `p = ρRT` |
| cv ×1.01 | `cp − cv = R` |
| R ×1.01 | `R = Ru/M` |
| γ_frozen ×1.01 | `γ = cp/cv` |
| M ×1000, R unchanged | `R = Ru/M` |
| M ×1000 **and** R ÷1000 | `state M = composition M` — the identities alone cannot, and the test says so |
| dropped product species | element conservation, residual > 1e-2 |
| inverted O/F | element conservation |
| species molar mass ×2 | element conservation |
| CO₂ declared as CO₃ | element conservation, names O as worst |
| converged result with a corrupted composition | rejected as `NO_SOLUTION` with `ELEMENT_BALANCE_VIOLATED` |

Every proof asserts the fixture **actually changed** before asserting detection.

### Malformed input never reaches CEA

A spy counts calls to the solver and asserts **zero** for negative temperature,
zero temperature, negative pressure, zero/negative/NaN O/F, zero and negative
chamber pressure, and an unsupported capability — then asserts it *does* see a
legitimate call, so it cannot pass vacuously.

### Reference levels, never merged

Level A adapter regression, Level B external published NASA CEA case, Level C
Cantera. Results in `acceptance/phase_5c/ACCEPTANCE_MANIFEST.md`; every Level B
value falls inside its source's rounding box, and those boxes were derived from
printed precision before the comparison ran.

---

## 9. Packaging

The official desktop build is made from `.venv-cea` and bundles the provider.
The spec collects CEA's data and binaries **conditionally**, so a build
environment without the library still produces a working executable.

| | |
| --- | --- |
| Bundle | 203.7 MB, 2091 files (+11.8 MB, +19 vs Phase 4G) |
| Launch | PASS |
| **Frozen provider solve** | **PASS** — real HP equilibrium from the bundled `thermo.lib` |
| Bundled database hash | matches the build input |
| **Source ↔ frozen parity** | **bitwise identical**, max \|ΔX\| = 0.0 |
| Cantera / RocketCEA / CoolProp / tests | absent |

The frozen solve is genuine execution, not an inference from file presence:
`RocketForge.exe --selftest-thermochemistry` loads the native library, reads
the bundled database, solves, and prints the result with its provenance.

A normal launch never imports CEA — the self-test module's provider imports are
function-local, checked statically.

---

## 10. Boundaries held

| | |
| --- | --- |
| RocketForge c\*, Cf, Isp, thrust | **not implemented** |
| CEA's native c\*, Cf, Isp | preserved in `oracle.py` with full conditions, for Phase 5E |
| `ChamberGas` performance fields | none, asserted on the real dataclass |
| `n_frz`, `iac` in the domain | none; `FreezeLocation` is the vocabulary |
| CEA objects in public results | none; every field walked and checked |
| `physics.thermochemistry` → CEA | none |
| Compressible v1.0 | byte-identical |
| Text parsing of CEA output | none; no regex, no subprocess, no input deck |
| Threading | none — 5B-0 measured 0.85× at four threads |
| Silent provider fallback | none |

---

## 11. Open issues

None blocking.

Two things a later phase should decide rather than inherit silently:

1. **Blend component names.** A blend's component keys are used directly as CEA
   names, because `PropellantDefinition` carries one provider name per
   substance. Extending it to per-component mapping is a domain change and was
   not made for an adapter's convenience.
2. **Bundle contents.** `collect_data_files("cea")` brings in `cea/bin/cea.exe`
   (2.7 MB) and a second copy of `thermo.lib` under `share/`, neither of which
   the provider uses. Harmless, and trimming them is a packaging refinement
   with a small risk of removing something the library expects.

---

## 12. Recommended Phase 5D

**Thermochemistry Calculator + Composition Explorer + Provider/Provenance
Display + Reference Comparison + Basic O/F Scientific Sweep.**

The provider is ready for it: results are immutable, fully provenanced, cheap
enough for interactive sweeps (0.57 ms/point), and honest about what they
assume. `15_thermochemistry_ui_integration_contracts.md` already specifies what
the interface must show and must never imply — mode and provider labelling on
every number, "adiabatic" on every flame temperature, the empty state when no
provider is installed, and results cleared on a provider change.

Phase 5D should show Tc, M̄, R, cp, cv, γ, ρ and composition. It should **not**
show c\*, Cf or Isp: those remain unowned until Phase 5E.

The basic O/F sweep in 5D is a thermochemistry visualisation, **not** the
generic Phase 5F trade-study engine.

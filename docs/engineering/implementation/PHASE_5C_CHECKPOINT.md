# Phase 5C — Execution Checkpoint

**LIVE continuation artifact. Not the final report.** The final report is
`PHASE_5C_CEA_PROVIDER.md`.

---

## Status

```
PHASE                 = 5C  (NASA CEA v3 production thermochemistry provider)
CURRENT_SEGMENT       = COMPLETE
LAST_COMPLETED_STEP   = 73
NEXT_STEP             = none -- Phase 5C is finished
NEXT_ACTION           = none. Phase 5D is the thermochemistry interface; see
                        PHASE_5C_CEA_PROVIDER.md section 12.
BASE_TEST_RESULT      = 5609 passed, 79 skipped, exit 0, 52.05 s
CEA_TEST_RESULT       = 5690 passed, 1 skipped, exit 0, 48.11 s
                        (repeat: 5690 passed, 1 skipped, identical)
CURRENT_FAILING       = none
PROVIDER_VALIDATION   = element balance + state identities + composition sum on
                        every solve; 15/15 matrix; Level A/B/C references green
FROZEN_MANIFEST       = PASS (22 files byte-identical, opening and closing)
PACKAGING_STATE       = PASS -- 203.7 MB / 2091 files, CEA bundled, Cantera
                        absent, frozen provider solves, source/frozen bitwise
                        identical
BLOCKERS              = none
VERDICT               = READY FOR PHASE 5D
CONTINUATION_COMMAND  = CONTINUE PHASE 5C FROM CHECKPOINT
```

---

## Baseline

| Gate | Result |
| --- | --- |
| Base opening regression (`.venv`) | **5542 passed, 1 skipped**, pytest exit 0, 54.83 s |
| Frozen manifest, opening | **PASS** — 22 files byte-identical |
| Digest | `8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` |

---

## Environments

| Environment | Path | Python | Provider |
| --- | --- | --- | --- |
| Base | `.venv` | 3.13.2 | **no CEA** — proves optionality |
| Provider-enabled | `.venv-cea` | 3.13.2 | cea 3.3.4, PySide6 6.10.2, numpy 2.5.2, pytest 9.1.1, scipy 1.18.1 |
| Cantera oracle | `%TEMP%\rocketforge_phase5b0_cantera` | 3.13.2 | cantera 3.2.0 (from Phase 5B-0) |

Verified CEA identity in `.venv-cea`:

```
cea package 3.3.4        cea lib 3.3.4 (3,3,4)        cea.R = 8314.51
data/thermo.lib  612751 bytes  sha256 8e5df1cca92d4a48663d1ee5a1372e65...
data/trans.lib    35108 bytes  sha256 c203d9330746405e1b57008cd6973547...
is_initialized after import: True   <-- import loads the native lib and database
```

The `thermo.lib` hash matches the value Phase 5B-0 recorded, so the provider is
being built against the same database the reference evidence came from.

---

## Segment A findings — decisions these settle

### D1. Package location

`rocketforge/providers/cea/`, following Phase 5A `08` §7's planned layout
(`providers/{cantera,cea,tabulated}/`) rather than the deeper
`providers/thermochemistry/cea/` the brief sketched. The existing architecture
checker derives the layer from `parts[1]`, so both work; Phase 5A wins.

### D2. Dependency profile

`requirements-thermochemistry.txt` with `cea==3.3.4`, exactly pinned.
`requirements.txt` **unchanged**. Rationale is written into the file itself.

### D3. CEA exposes no per-species elemental formulas

Probed and confirmed: `Mixture` offers only `species_names`/`num_species`;
`EqSolver` offers only counts; `Reactant.formula` is `None` for library species
(it is populated only for caller-defined custom reactants). There is no
element-composition accessor in the public API.

Consequence: element conservation — which Phase 5B makes a blocking check —
needs formulas from somewhere else.

### D4. Product species set: curated, not auto-selected. **Measured, not assumed.**

`products_from_reactants=True` for CH4(L)/O2(L) yields **124 species**,
including exotics down to 1e-36 and names such as `C2H2,acetylene`,
`HCHO,formaldehy`, `CH3C(CH3)2CH3`, `(HCOOH)2`, `HO(CO)2OH`. Deriving formulas
from those names needs a parser handling parentheses and comma suffixes —
exactly the fragile universal parser Phase 5B `09` §2.3 and the 5C brief §66
both warn against.

Measured cost of curating instead, LOX/CH4 at O/F 3.4, Pc 100 bar, reactants at
their normal boiling points:

| Product set | Tc [K] | M [kg/kmol] | γ_s | ΔTc | ΔM/M | Δγ/γ |
| --- | --- | --- | --- | --- | --- | --- |
| auto, 124 species | 3598.2855 | 21.77009 | 1.13259 | — | — | — |
| curated 12 | 3598.3332 | 21.76947 | 1.13265 | +0.048 K | −2.9e-05 | +5.1e-05 |
| **curated 27** | **3598.2860** | **21.77008** | **1.13259** | **+0.0005 K** | **−5.8e-07** | **+1.0e-06** |

The 27-species curated set reproduces the full-species answer to about 1e-06 —
an order of magnitude **below** CEA's own pre-2019 gas-constant discrepancy of
5.7e-06, which is already the floor on any provider identity check. So the
curated set costs less than a difference the architecture already tolerates and
documents.

**Decision:** the curated CHO product set is the production default; the exact
set is recorded in provenance (`species_set`); the measured cost above is
documented; a caller may override via `request.product_species`; any species
that cannot be mapped produces an explicit diagnostic and never a silent drop.

### D5. Condensed-candidate trap reproduces in the production case

The same solve reports `num_condensed = 3` (candidates `C(gr)`, `H2O(L)`,
`H2O(cr)`) with **all three at exactly zero**. This is the Phase 5B-0 finding,
live and reproducible in exactly the case Phase 5C ships — an ideal regression
fixture for the "candidate list is not actual presence" rule (ADR-28).

### D6. R is derived from RocketForge's CODATA constant

CEA returns `M`, not `R`. R is therefore derived, and it is derived with
`core.constants.UNIVERSAL_GAS_CONSTANT`, so `R = Ru/M` closes exactly. The
consequence — `cp − cv = R` and `p = ρRT` then miss by ~5.7e-06 because CEA
computed those on its own Ru = 8314.51 — is absorbed by Phase 5B's
`provider_identity_rel_tol = 1e-5`, exactly as that category was designed and
tested for. CEA's own Ru is recorded in provenance options for traceability.

### D7. cp/cv are the frozen pair

CEA exposes `cp_fr`/`cv_fr` and `cp_eq`/`cv_eq`. Only the frozen pair satisfies
`cp − cv = R` (measured: 7.162 − 6.066 = 1.097 kJ/(kg·K) for the equilibrium
pair against R = 0.387). So `ChamberGas.cp`/`cv` carry the frozen pair,
`cp_frozen`/`cp_equilibrium` carry both, `gamma_frozen = cp_fr/cv_fr`, and
`gamma`/`gamma_equilibrium` carry CEA's `gamma_s` isentropic exponent.

### D8. Native units, confirmed

pressure **bar**, cp/cv **kJ/(kg·K)**, enthalpy **kJ/kg**, entropy
**kJ/(kg·K)**, molar mass **kg/kmol**, density **kg/m³**, temperature **K**.

---

## Files created

* `requirements-thermochemistry.txt`
* `docs/engineering/implementation/PHASE_5C_CHECKPOINT.md` (this file)

## Files modified

(none yet)

---

## Step log

| Step | Description | Status |
| --- | --- | --- |
| 1 | Read Phase 5A / 5B-0 / 5B documentation | **done** |
| 2 | Inspect actual Phase 5B public contracts | **done** |
| 3 | Base opening regression | **done** — 5542/1/exit 0 |
| 4 | Verify frozen manifest | **done** — PASS |
| 5 | Create this checkpoint | **done** |
| 6 | Provider-enabled CPython 3.13.2 environment | **done** — `.venv-cea` |
| 7 | Optional dependency profile | **done** |
| 8 | Install NASA CEA | **done** — 3.3.4 |
| 9 | Verify CEA version / native / data identity | **done** |
| 10 | Inspect provider and packaging conventions | **done** |
| 11-73 | provider, mapping, validation, references, oracle, benchmarks, packaging, docs | **done** |

---

## Blockers

None.


---

## Segment B-F findings

### D9. NASA CEA ignores the temperature of assigned-enthalpy reactants

**The most significant scientific finding of the phase.** Verified at the raw
library level, with no RocketForge code in the path:

```
Mixture(['CH4','O2'])         T=[298.15, 298.15] -> H = -1056854.44
                              T=[350.00, 298.15] -> H = -1029844.11   varies
Mixture(['CH4(L)','O2(L)'])   T=[111.643, 90.17] -> H = -1577584.52
                              T=[111.643, 95.00] -> H = -1577584.52   identical
                              T=[111.643, 99.00] -> H = -1577584.52   identical
```

Several CEA reactant entries -- the cryogenic liquids among them -- carry a
single **assigned enthalpy** at one reference condition rather than a
temperature-dependent fit. CEA accepts a different temperature for those and
then ignores it. A caller who sets liquid oxygen to 95 K silently receives the
90.17 K answer.

The adapter is correct: it does pass the actual stream temperature, and CEA
does receive it. But RocketForge must not pass the silence on, so the provider
now emits `PROVIDER_ASSIGNED_ENTHALPY_REACTANT` (WARNING) naming the requested
and the assigned temperature, and the solve returns `OK_WITH_WARNINGS`. The
request is honoured, the answer is usable, and the caller is told the value
they set did not enter the calculation.

Detection is **empirical**, not pattern-matched: the enthalpy is evaluated at
two temperatures inside the reactant's declared range and compared. Measured:

| reactant | assigned T | | reactant | assigned T |
| --- | --- | --- | --- | --- |
| `O2(L)` | 90.17 K | | `O2` | none -- responds |
| `CH4(L)` | 111.643 K | | `CH4` | none -- responds |
| `H2(L)` | 20.27 K | | `N2H4(L)` | none -- responds |
| `RP-1` | 298.15 K | | | |

Gaseous reactants do respond, and the pipeline proves it: raising gaseous
methane from 298.15 K to 400 K moves the chamber by **+7.63 K**.

### D10. PHASE_5B_CONTRACT_CORRECTION -- provider element-balance tolerance

Phase 5B set `element_balance_rel_tol = 1e-8`, justified from a **single**
Phase 5B-0 sample that closed to 1.04e-09. Phase 5C measured the real spread of
CEA's own convergence residual across **52 converged solves** (O/F 1.5-7.5,
Pc 1-20 MPa) using CEA's own molar masses and mass fractions, with no
RocketForge conversion in the path:

* worst scale-aware residual **1.864e-08**, at O/F 2.5 / 5 MPa
* worst per-element residual **5.888e-08**
* best 8.6e-11, at oxidiser-rich conditions

Larger at fuel-rich conditions where dissociation is strongest, which is a
solver-convergence signature rather than a mapping defect. `sum(X)` and
`sum(Y)` are machine-perfect (0.9999999999999999), so nothing is being
truncated.

Two of fifteen matrix cases were therefore rejected as `no_solution` by the
strict tolerance. **Correction:** added
`provider_element_balance_rel_tol = 1e-6` -- a new named category, parallel to
`provider_identity_rel_tol`, clearing the measured worst case by ~50x while
staying four orders of magnitude tighter than any real chemistry error. The
strict 1e-8 is **unchanged** for RocketForge's own algebra.

### D11. CEA name limit is exactly 15 characters

Measured, not read: names of 16+ are rejected with `CEA_INVALID_SIZE` before
any database lookup; 15 and shorter reach the lookup. `HCHO,formaldehy` is
exactly 15 and works. Isolated entirely in `naming.py`.

### D12. CEA exposes its own per-species molar masses

`Mixture.moles_to_weights` with a unit vector returns the molar mass CEA's
database uses (H2O 18.015280, CO2 44.009500, ...). Taking molar masses from CEA
rather than from a shipped periodic table removes the atomic-weight-vintage
mismatch from the element balance entirely. Only the elemental *formulae* are
curated, and those are unambiguous integers.

---

## Files created (running list)

Production, `rocketforge/providers/cea/`: `__init__.py`, `availability.py`,
`errors.py`, `mapping.py`, `naming.py`, `oracle.py`, `propellants.py`,
`provider.py`, `resources.py`, `species.py`, `units.py`.

Other: `requirements-thermochemistry.txt`.

Tests, `tests/providers/cea/`: `conftest.py`, `test_cea_availability.py`,
`test_cea_mapping.py`, `test_cea_provider_live.py`.

## Files modified

* `rocketforge/physics/thermochemistry/tolerances.py` -- added
  `provider_element_balance_rel_tol` (see D10). This is the only change to a
  Phase 5B production file.


---

## Closing record

| Gate | Result |
| --- | --- |
| Base opening | 5542 passed, 1 skipped, exit 0 |
| Base closing | **5609 passed, 79 skipped**, exit 0 |
| CEA-enabled closing | **5690 passed, 1 skipped**, exit 0 |
| CEA-enabled repeat | identical |
| New Phase 5C tests | **145** |
| Architecture | 41 + 18 + 18, all green |
| Frozen manifest | 22 files byte-identical |
| Base `.venv` | provider-free |
| `requirements.txt` | unchanged |
| QML | unchanged |
| Executable | builds, launches, frozen provider solves, bitwise parity |

**Status: COMPLETE.** Final report: `PHASE_5C_CEA_PROVIDER.md`. Provider
contract: `../CEA_PROVIDER_CONTRACT.md`. Acceptance:
`../../../acceptance/phase_5c/ACCEPTANCE_MANIFEST.md`.

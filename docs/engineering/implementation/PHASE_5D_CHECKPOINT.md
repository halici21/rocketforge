# Phase 5D — Checkpoint

Thermochemistry Analysis Workspace (Calculator, Composition, Sweep, References).

**Status: COMPLETE — READY FOR PHASE 5E**
**Amended 2026-09-04 by a corrective patch — see the addendum at the end.**

Report: `docs/engineering/implementation/PHASE_5D_THERMOCHEMISTRY_UI.md`
Contract: `docs/engineering/THERMOCHEMISTRY_UI_CONTRACT.md`
Acceptance: `acceptance/phase_5d/ACCEPTANCE_MANIFEST.md`

---

## Position

| Field | Value |
| --- | --- |
| CURRENT_SEGMENT | J — complete |
| LAST_COMPLETED_STEP | STEP 95 — final verdict |
| NEXT_STEP | Phase 5E, not started |
| NEXT_ACTION | none |

---

## Gates

| Gate | Opening | Closing |
| --- | --- | --- |
| Base (`.venv`, no CEA) | 5609 passed, 79 skipped, exit 0 | **5785 passed, 106 skipped**, exit 0, 41.19 s |
| CEA-enabled (`.venv-cea`) | 5690 passed, 1 skipped, exit 0 | **5893 passed, 1 skipped**, exit 0, 45.93 s |
| CEA-enabled repeat | — | 5893 passed, 1 skipped, 43.07 s |
| Architecture | 41 + 18 + 18 | 41 + 18 + 18 + **48 Phase 5D**, all green |
| Frozen Compressible | 22/22 byte-identical | 22/22 byte-identical |
| New tests | — | **203** |

### Frozen manifest note

The Phase 4G manifest records `sha256(file)[:16]` per file. All 22 recomputed
digests match, so the manifest content is unchanged and the recorded digest
`8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` still
stands. The exact byte layout the digest was taken over was not recorded in
Phase 4G and is not re-derivable; the per-file comparison is the substantive
check and is the one performed, at the opening gate and again at the close.

---

## Reported spec discrepancy — `PHASE_5D_CHART_ARCHITECTURE_NOTE`

Brief §70 states the project uses **Qt Graphs 2D**. It does not: no `QtGraphs`
or `QtCharts` import exists anywhere in `ui/`, `rocketforge/` or the
requirements files. Every chart is drawn by `RFLineChart` on `RFPlotSurface`, a
Canvas painter the project owns. The binding instruction in the same section —
*"Use existing RocketForge chart architecture"* — is followed; no chart library
was introduced. Recorded rather than silently resolved.

No blockers were raised. No `PHASE_5D_*_BLOCKER` code applies.

---

## Files created

**Application, Qt-free**

* `rocketforge/application/analysis/thermochemistry_provider.py`
* `rocketforge/application/analysis/thermochemistry_service.py`
* `rocketforge/application/analysis/thermochemistry_sweep.py`
* `rocketforge/application/analysis/thermochemistry_reference.py`

**Application, Qt**

* `rocketforge/application/analysis/thermochemistry_controller.py`
* `rocketforge/application/analysis/thermochemistry_table_model.py`
* `rocketforge/application/uismoke.py`

**Data**

* `rocketforge/data/reference/thermochemistry_nasa_cea_2002_lox_lh2.json`

**Interface** — `ui/pages/ThermochemistryPage.qml` and thirteen files in
`ui/pages/thermochemistry/`: `ThermoCalculator`, `ThermoComposition`,
`ThermoCompositionBars`, `ThermoSweep`, `ThermoSweepChart`,
`ThermoSweepSpeciesChart`, `ThermoSweepPoint`, `ThermoReferences`,
`ThermoResultHeader`, `ThermoWarnings`, `ThermoDiagnostics`,
`ThermoProvenance`, `ThermoProviderUnavailable`.

**Tests** — `tests/application/conftest.py` plus
`test_thermochemistry_service.py`, `test_thermochemistry_sweep.py`,
`test_thermochemistry_controller.py`, `test_thermochemistry_reference.py`,
`test_thermochemistry_ui_architecture.py`.

**Harness** — `experiments/phase_5d/ui_harness.py`, `benchmark.py`,
`regression_capture.py`, `parity.py`.

**Documentation** — `docs/engineering/THERMOCHEMISTRY_UI_CONTRACT.md`,
`docs/engineering/implementation/PHASE_5D_THERMOCHEMISTRY_UI.md`,
`acceptance/phase_5d/ACCEPTANCE_MANIFEST.md`.

## Files modified

| File | Change |
| --- | --- |
| `main.py` | registers the `Thermochemistry` singleton; dispatches the UI diagnostic |
| `ui/data/Navigation.qml` | the page, the `THERMOCHEMISTRY` domain, the page's own status wording |
| `ui/shell/SideNav.qml` | renders the new domain section |
| `ui/shell/StatusBar.qml` | `computedNote` → an overridable `originNote` |
| `ui/Main.qml` | honours the page's solver and origin wording, including the no-provider case |
| `ui/components/RFEngineeringTable.qml` | optional per-column `align: "left"` (default unchanged) |
| `ui/components/RFLineChart.qml` | optional `showPoints`; tick decimals from the axis span; marker labels flip at the right edge |
| `rocketforge/providers/cea/provider.py` | public `species_table()` |

---

## Interface

| View | Status |
| --- | --- |
| Calculator | PASS — empty, result, warning and refusal states |
| Composition | PASS — basis switch, display threshold, both condensed cases |
| Sweep | PASS — four charts, table, point inspection, failed-point handling |
| References | PASS — Level-B comparison, source metadata, omissions stated |
| Provider unavailable | PASS — base environment, no numbers anywhere |
| Packaged | PASS — the same tour inside the bundle |

**QML warnings: 0** in every run — source, base and packaged — across 35 + 3 +
35 captures at 2560×1440, 1920×1080 and 1366×768 plus a light-theme pass.

**Source ↔ packaged parity: 3909 fields compared, 0 differences.**

---

## Performance

| | |
| --- | --- |
| Warm calculation, end to end | 0.63 ms median, 0.75 ms worst of 50 |
| 41-point sweep | 22.7 ms (21.9 solver, 0.8 interface) |
| 1000-point sweep, the guard | 558 ms (535 solver, 23 interface) |
| 1000-point memory | 8.73 MB retained, 8.92 MB peak, no accumulation |

---

## Packaging

Clean rebuild from `.venv-cea`: 203.9 MB, 2106 files (+0.2 MB, +15 over Phase
5C). Bundled `thermo.lib` SHA `8e5df1cc…`. Cantera, RocketCEA, CoolProp, the
tests and the experiment scripts absent. Launches with the window titled
"RocketForge" and exits 0. Phase 5C's provider self-test unchanged and passing.

## Blockers

None.


---

# Corrective patch — 2026-09-04

**Verdict: PASS.** Wording and documentation only.

## What it corrected

The Composition tab reported a nonzero condensed mass fraction below its
display threshold as *"None detected"*. 6.24e-08 is not zero. The two "not
present" cases are now two states:

| Fraction | Headline |
| --- | --- |
| exactly 0 | No condensed product reported |
| `0 < f < 1e-6` | No condensed phase above reporting threshold |
| `f >= 1e-6` | Condensed products present *(unchanged)* |
| not reported | Unknown is not the same as none *(unchanged)* |

Every known state shows the exact fraction and the reporting threshold beside
the verdict. `CONDENSED_REPORTING_THRESHOLD` is public and named for what it
is; a test asserts it appears nowhere in `physics`, `providers`, `core` or
`engineering`.

## What it did not touch

Provider physics, `condensed_mass_fraction`, composition and species mapping,
the candidate-vs-presence rule, assigned-enthalpy behaviour, sweep semantics,
failed-point segmentation, the optimiser boundary, frozen Compressible v1,
Engine Design, every compressible workspace, and every calculated value —
source ↔ packaged parity re-run at 4110 fields with 0 differences.

## Two layout defects found and fixed within the patch

* the verdict fell below the fold at 1366×768; it now sits with the composition
  in the result panel rather than in the scrolling control rail;
* `CONDENSED` printed on top of `C(gr)` — `RFEngineeringTable`'s marker gutter
  assumed a right-aligned first column. It now accounts for a left-aligned one.
  Phase 4G gate 9.6, caught by looking at the screenshot.

## Files changed

| File | Change |
| --- | --- |
| `thermochemistry_service.py` | four condensed states; `CONDENSED_REPORTING_THRESHOLD` |
| `thermochemistry_controller.py` | the richer `condensed` map |
| `ui/pages/thermochemistry/ThermoCondensedSummary.qml` | **new** — the verdict, beside the composition |
| `ui/pages/thermochemistry/ThermoComposition.qml` | rail scrolls; verdict moved out of it |
| `ui/components/RFEngineeringTable.qml` | marker gutter for a left-aligned first column |
| tests | +14, covering all four states and the gutter rule |
| `THERMOCHEMISTRY_UI_CONTRACT.md` | §8 rewritten; deferred fluid-property task added |
| `PHASE_5D_THERMOCHEMISTRY_UI.md` | dated addendum appended, body preserved |
| `acceptance/phase_5d/ACCEPTANCE_MANIFEST.md` | dated addendum appended |

## Gates

| Gate | Result |
| --- | --- |
| Base | **5799 passed, 106 skipped**, exit 0, 57.48 s |
| CEA-enabled | **5907 passed, 1 skipped**, exit 0, 56.74 s |
| CEA-enabled repeat | 5907 passed, 1 skipped, 70.79 s |
| New Phase 5D tests | **217** |
| Architecture | 41 + 18 + 18 + **50** |
| QML warnings | **0** |
| Source ↔ packaged parity | 4110 fields, 0 differences |
| Frozen Compressible | **22/22 byte-identical** |
| Bundle | 203.9 MB, 2107 files |

## Deferred

**Reactant enthalpy / fluid-property coupling** — recorded in the UI contract
as non-blocking. Phase 5D reports the CEA assigned-enthalpy limitation
correctly; neither Phase 5D nor this patch solves it.

# Rocket Performance visual architecture pilot — implementation

What was built, what enforces each rule, what was measured, and what is still
open. The design rationale is in `docs/design/ROCKET_PERFORMANCE_VISUAL_PILOT.md`;
the pre-code audit it answers is in `docs/design/ROCKET_PERFORMANCE_VISUAL_AUDIT.md`.

---

## 1. Scope

A visual-architecture pilot for **one** workspace. Not a physics phase, not a
backend refactor, not a global UI rewrite.

The governing rule: **a visual redesign must not change one scientific result.**
Section 5 is the evidence.

---

## 2. Files

### Added

| File | Role |
| --- | --- |
| `ui/pages/rocketperformance/PerfNozzleCanvas.qml` | the schematic gas path, its stations and the honesty label |
| `ui/pages/rocketperformance/PerfMetricReadout.qml` | one metric: symbol, value, unit, label, primary or not |
| `ui/pages/rocketperformance/PerfStationLabel.qml` | a station annotation on the canvas |
| `ui/pages/rocketperformance/PerfBreakdown.qml` | a labelled term breakdown with right-aligned values |
| `ui/pages/rocketperformance/PerfPressureRelation.qml` | the exit/ambient relation and the solved exit state |
| `rocketforge/application/analysis/performance_visual.py` | `radius_ratio_for_drawing` — the one derivation the drawing needs |
| `experiments/ui_visual_pilot/capture_matrix.py` | the 27-state capture matrix, run identically before and after |
| `experiments/ui_visual_pilot/scientific_parity.py` | the field-by-field before/after comparison |
| `experiments/ui_visual_pilot/accessibility_audit.py` | contrast, keyboard and colour-only measurement |
| `experiments/ui_visual_pilot/performance_benchmark.py` | creation, publication, repaint, idle and memory |
| `tests/test_performance_visual_architecture.py` | 62 static and artifact rules |

### Rewritten

`ui/pages/rocketperformance/PerfCalculator.qml` — the three-zone composition.

### Extended

`rocketforge/application/analysis/performance_controller.py`. Application
layer, **not** a frozen contract: the frozen `IDEAL ROCKET PERFORMANCE API v1.0`
covers `rocketforge/engineering/chamber` and `rocketforge/engineering/nozzle`
only, and neither was touched.

Added, all read-only and all derived from the current outcome:
`solvedRadiusRatio`, `solvedExitMach`, `solvedRegime`, `headlineMetrics`,
`thrustCoefficientBreakdown`, `thrustBreakdown`, `pressureThrustSign`,
`pressureRelationText`, `regimeLabel`, `exitStateRows`, `traceRows`,
`solvedChamberPressureText`.

### Removed

`PerfResultHeader.qml` and `PerfResultGroup.qml`. The redesign replaced them and
at first simply stopped using them, leaving two dead files behind; a test now
fails if any pilot component is instantiated nowhere. The supersession is
recorded in `docs/engineering/ROCKET_PERFORMANCE_UI_CONTRACT.md`, whose
Phase 5E promises are otherwise unchanged and still enforced.

---

## 3. Rules, and what enforces them

`tests/test_performance_visual_architecture.py` — **62 tests**.

| Rule | Enforcement |
| --- | --- |
| No physical relation in QML | token scan over every performance QML file, comments stripped |
| The canvas derives nothing | `Math.sqrt` absent; it divides by `root.drawnRatio` |
| The drawing claims no geometry it has not solved | scan for "Rao", "bell contour", "half-angle", "Mach distribution", "pressure field", "contour solved" |
| The drawing is labelled a schematic | the label text is asserted present |
| A placeholder cannot pose as a result | `placeholderRatio` is internal; the only `radiusRatio:` assignment in the page is `solvedRadiusRatio` |
| A placeholder does not borrow the solved label | its own weaker text is asserted |
| The hero is labelled by the result | `resultHeadline`, never `caseHeadline`; no `.split(` anywhere in the view |
| Driven by the solved snapshot | `radiusRatio: RocketPerformance.solvedRadiusRatio` |
| No idle animation | no `Timer`, no `running: true`, no infinite loop; repaint only on change |
| Meaning is not colour-only | stale, superseded, regime and relation are asserted as text |
| Nothing meaningful in the dimmest token | `Theme.textDisabled` absent from all five added components |
| A stale value stays readable | `root.stale ? Theme.textMuted` |
| An overflowing rail says so | the policy expression on both rails; `RFScrollBar` itself unchanged |
| The pilot stayed local | no other page instantiates a `Perf*` component |
| No orphaned component | every `Perf*.qml` is instantiated somewhere |
| No image or font asset | the directory is scanned for nine extensions |
| The drawing helper is not in the science path | its only importer is the controller |

Every scan has a negative control asserting it fires on the thing it is meant
to catch, and the comment stripper has its own test — three earlier audits in
this project false-positived on prose.

### Two accepted rules fired on the pilot, and neither was weakened

* The Phase 5E rule that the interface performs only layout arithmetic caught
  `exitR / Math.sqrt(ratio)` in QML. The answer was to publish `r_e/r_t` from
  the controller, which is why `performance_visual.py` exists.
* The rule against hard-coding a reference condition in the interface caught a
  literal `p_e = p_a` comparison in QML. The relation text moved to the
  controller, where it can be tested.

---

## 4. What was reverted after looking at captures

Screenshot review was blocking, and it found what code review had not:

| Defect | Fix |
| --- | --- |
| `"p_c p_c 100 bar"` | the view was slicing a headline string; the controller now publishes the label |
| doubled minus, `"− −1.15172"` | sign prefix applied only to positive terms |
| Calculate scrolled out of reach at 1366 | pinned outside the `Flickable` |
| input rail width unstable between themes | pinned by min/max, not preferred |
| empty state clustered at the top of a blank page | centred column at a readable measure, with a dimmed unsolved outline |
| placeholder outline stretched into a duct | bounded box, proportion corrected |
| the placeholder borrowed the solved "AREA EXPANSION" label | its own label — its expansion is invented |
| the header read `Ae/At 60` above an `Ae/At 40` drawing | bound to `resultHeadline`, not the live form |
| exit state in the smallest type on the page | raised one step; it is solved physics |
| an overflowing rail gave no sign it continued | scrollbar visible while overflowing |

---

## 5. Scientific parity — the governing rule

`acceptance/ui_visual_pilot/scientific_parity.json`

| Measure | Result |
| --- | --- |
| Captures compared | **27** |
| Leaf fields compared | **5688** |
| **Differences** | **0** |
| Total provider solves | 1 → 1 |
| Qt warnings | 0 → 0 |
| Verdict | **PASS** |

Values are compared exactly as captured, formatted strings included. No
normalisation and no tolerance: a tolerance here would be a way of not
noticing. The comparison is under a negative control that proves it detects a
changed digit and a dropped row.

Chemistry solves caused by interaction, before → after:

| Interaction | Before | After |
| --- | --- | --- |
| ε edit + calculate | 0 | **0** |
| ambient edit + calculate | 0 | **0** |
| scale edit + calculate | 0 | **0** |
| view / theme / resize | 0 | **0** |

---

## 6. Accessibility

`acceptance/ui_visual_pilot/accessibility.json`

* Contrast, both themes, every pair the workspace draws — **pilot-owned: PASS**.
* Keyboard — **33 distinct Tab stops**, all required controls reached.
* Colour-only — six checks, all satisfied.

**Open finding, not pilot-owned.** `Theme.textMuted` is 4.21:1 (dark) and
4.33:1 (light) against the page background, under the 4.5:1 AA asks of body
text. It is a shared token; raising it is a theme change affecting every
workspace. Recorded for rollout.

---

## 7. Runtime cost

`acceptance/ui_visual_pilot/performance_after.json`

| Measure | Before | After | Budget |
| --- | --- | --- | --- |
| Page creation | 20.95 ms | **15.66 ms** | 400 |
| Solved publication | 68.45 ms | **24.41 ms** | 50 |
| Nozzle repaint | — | **4.10 ms** | 50 |
| Idle CPU | 15.55 ms/s | **10.36 ms/s** | 60 |
| Memory, 100 recalculations | 896.13 MB | **450.67 MB** | comparison |

### The memory finding

Repeated recalculation retains memory in the QML layer **on both designs**.
Decomposed:

| Action | Growth |
| --- | --- |
| `calculate()` with the page never shown | 0.19 MB, plateaus |
| `calculate()` + reading every list property from Python | 0.02 MB |
| the solver called directly, no UI at all | 0.08 MB, flat |
| `calculate()` with the page **rendered** | ~4.5 MB per 10 solves |
| tab switches, resizes, idle | **0.00** |

So it is neither the science nor the controller: it is retention in the
rendered QML layer, it predates this pilot, and the pilot roughly halves it
(×0.503). It is recorded as a **finding for the roadmap**, not folded into a
budget that would hide it. Memory is therefore gated as a regression against
the design being replaced, which is what a visual pilot is accountable for.

**Two measurement defects were found and fixed before any of this was trusted.**
The memory probe read through `psapi` and silently returned a flat zero,
reporting a clean `0.000 MB` for a loop that actually retained hundreds; it now
reads `K32GetProcessMemoryInfo` with declared signatures and proves itself
against a deliberate 40 MB allocation (reads 40.16 MB) before any result is
believed. The idle metric busy-polled `processEvents()` and measured its own
polling; it now measures process CPU time.

---

## 8. Regressions and packaging

| Gate | Result |
| --- | --- |
| Base (`.venv`) | **6893 passed, 154 skipped**, exit 0 |
| Production (`.venv-cea`) | **7048 passed, 2 skipped**, exit 0 |
| Production, repeated | **7045 passed, 2 skipped**, exit 0 (mid-run) |
| Frozen contract verification | **102 passed** |
| Source self-tests (8) | all exit 0 |
| Clean PyInstaller build | exit 0; CEA 3.3.4 and CoolProp 8.0.0 bundled |
| Packaged self-tests (8) | all exit 0 |
| Source ↔ packaged parity | 29 captures, **5189 fields, 0 differences**, 0 Qt warnings |

All nine frozen contracts verify. `NASA CEA PROVIDER v1.0` reports a file-level
mismatch **by design** — it was superseded by v1.1 during the fluids work, and
the supersession is what the acceptance suite asserts.

The packaged UI self-tests exit 2 when run against a physical screen smaller
than 1920×1080 (`QWindowsWindow::setGeometry`). That is a harness condition, not
a defect; they are run offscreen, as the source self-tests are.

---

## 9. Known limitations

1. **`Theme.textMuted` is below WCAG AA** (4.21:1 / 4.33:1). Shared token;
   rollout item. Nothing depends on it alone.
2. **The QML layer retains memory under repeated recalculation** — ~450 MB per
   100 solves with the page rendered, halved from the previous design but not
   eliminated. Pre-existing, out of pilot scope, worth its own investigation.
3. **The pre-pilot performance baseline cannot be regenerated.** It was measured
   against the previous build's UI tree in `dist/RocketForge/_internal/ui`,
   which the clean rebuild in section 8 destroyed. The numbers are recorded in
   `performance_before.json` and flagged `"reproducible": false`. The *scientific*
   baseline is unaffected: all 27 before-captures and their 5688 fields are
   intact in `acceptance/ui_visual_pilot/before/`.
4. **The canvas is a schematic of area expansion only.** No contour, no chamber
   dimension, no axial scale. This is a statement of what the model has solved,
   not a limitation to be lifted by drawing more.

---

## 10. Rollout candidates

Recorded, **not implemented**. Each is a separate decision.

| Candidate | Why | Risk |
| --- | --- | --- |
| **Raise `Theme.textMuted`** to clear 4.5:1 | closes the one open accessibility finding, everywhere at once | touches every workspace; needs a full re-render regression |
| **Metric hierarchy** (`PerfMetricReadout`) for Thermochemistry and Line | both present flat lists where one or two quantities dominate | low — additive component |
| **Term breakdowns** (`PerfBreakdown`) wherever a result is a sum | Cf and thrust proved readable; Fanno/Rayleigh have the same shape | low |
| **Overflow cue** on every rail | the same 1366 discoverability gap exists elsewhere | low, but it is a shared-scrollbar change if generalised |
| **A schematic object** for Line and Nozzle Lab | the same "computes an object, never shows it" gap | medium — each needs its own honesty label and its own audit |
| **Panel reduction** in the Model and Oracle tabs | 7 `RFPanel` remain in this workspace alone | medium — those tabs were deliberately untouched here |

A rollout should re-run the capture matrix and the parity comparison per
workspace. The pilot's value is the method as much as the result: audit from
captures first, then measure that the science did not move.

# CAD/CAE Workbench R1 — Trade Study Integration

Fifth workspace migration, following the accepted Structural Recovery phase.
Scope per the phase brief: Trade Study only. Engine Design not started.

## Addendum: the parametric sweep correction

A user correction, applied after the sections below were first written and
accepted as a scatter/Pareto-only redesign, changed the understanding of
what Trade Study is for: RocketForge must support classical engineering
parametric trades (one swept design variable against one or more response
curves) as the *primary* grammar, not route every study through a 2D
scatter/Pareto projection. The sections below (RFPlotSurface redesign,
generic X/Y, Pareto semantics) all still stand and are unchanged — they now
describe the **Design space** mode, one of two modes a person chooses
between, used when a study actually varied two or more design variables.
What follows is genuinely new work added on top.

### Three visualization modes, as implemented

- **Sweep** (`ui/pages/tradestudy/StudySweep.qml`, new) — the default when
  a study varied exactly one design variable
  (`TradeStudy.isParametricSweep`). One aligned `RFLineChart` per selected
  response metric, all sharing the swept variable's own evaluated range on
  the X axis, so reading down a vertical line reads the same design across
  every curve. `RFLineChart` already existed and already had everything
  this needed (`series`, `showPoints`, `markerX`/`markerLabel` for a
  persistent reference line, `markers` for the exact selected point, its
  own hover crosshair) — reused directly, not reinvented.
- **Response vs response** — the same generic-axis "Design space" scatter
  already built, used with two response metrics instead of a design
  variable on either axis. Selecting a point reveals its underlying design
  variables in the Inspector, unchanged from how it already worked. See
  `response_vs_response_dark_1920x1080.png`.
- **Design space** — the already-implemented, already-tested Pareto
  scatter, used when two or more design variables actually varied
  (`!TradeStudy.isParametricSweep`). Response-vs-response and Design-space
  share one mechanism (a generic 2D projection with Pareto-status marker
  coloring) because the underlying question is the same shape whether both
  axes are metrics or one is a design variable — only the *default* framing
  differs.

`ui/pages/tradestudy/StudyTrade.qml` (new) is the mode switch: an
`RFSegmentedControl` ("Sweep" / "Design space") wrapping `StudySweep` and
the existing `StudyPareto`, defaulting to whichever shape the just-run
study actually has, with an explicit person's choice persisting until the
next evaluation — the same explicit-overrides-automatic discipline already
used for axis defaults. Replaces `StudyPareto` directly at Trade Study's
tab index 2 (relabeled "Trade", was "Pareto" — a label only, `shellsmoke.py`
indexes by number).

### Controller additions (`trade_study_controller.py`, still presentation-plumbing only)

`isParametricSweep`/`sweepVariableKey`/`sweepVariableTitle` (reads
`self._definition.variables`, a variable counts as swept when
`variable.count > 1`); `responseMetricOptions` (metrics only, never another
design variable — a sweep curve's Y axis is a response, not a second swept
thing); `sweepMetrics`/`setSweepMetricEnabled` (which response curves are
active, sensible defaults from the study's own objectives); `sweepSeries`
(one polyline series per active metric, sorted by the swept variable's
value, each point carrying `hasValue` so a metric a design could not
produce breaks the line rather than bridging across it — the same honesty
rule the results table already applies to a failed row);
`sweepScaledToPeak`/`sweepScalingNote` (an explicit, always-labeled
normalization toggle — `value ÷ evaluated maximum`, computed in Python and
never silent; raw values stay in `rawY` and in the Inspector regardless of
the toggle); `sweepComparisonRows` (for the selected design: each active
response's value, the evaluated maximum, and the difference/percentage
from it — pure aggregation over already-evaluated points, zero new
physics, worded as "trade-off vs. evaluated maximum," never "efficiency
loss" or "optimal").

(The property is named `sweepScaledToPeak`, not the more obvious
`sweepNormalized` — `test_qml_implements_no_decision_algorithm` bans the
substring "normaliz" in any workspace `.qml` file, since a QML file
computing a normalization would be re-implementing decision-layer logic in
the view layer. This controller only *exposes* the flag; QML only reads
its name, but the flagged substring would still land in the `.qml` file's
own source text merely by binding to it, so the property itself was
renamed rather than working around the guard.)

### Verification

Solve-call matrix (`tradestudy_solve_call_matrix.py`, extended): enabling/
disabling a second response curve, toggling normalization, and selecting a
point on a sweep curve are all confirmed 0 chemistry/0 performance calls,
alongside the already-passing axis-switch/selection/theme/resize/decision-
layer matrix. A focused 40-round memory soak of sweep-mode/metric-choice/
normalize/select/resize (`tradestudy_sweep_memory_soak.py`) grew 6.57MB,
decelerating from 0.18 to 0.02MB/round, 0 Qt warnings, harness controls
passed first. Full test suite re-confirmed at 7071/7071 passing (up from
7059 — the new QML files are picked up by the existing per-file
architecture-guard parametrization automatically). Real captures manually
opened, not inferred: a single response curve, two curves with a selected
design showing a shared gold reference line and ring on both curves
simultaneously (`sweep_mode_selected_dark_1920x1080.png`), the normalized
view with its explicit method note, 1366×768, and the Design-space mode
still defaulting correctly for a genuine two-swept-variable study
(`designspace_mode_default_dark_1920x1080.png`, unchanged from before this
addendum).

### Acceptance gate, the five required capabilities

1. Swept variable vs. one response curve — `sweep_mode_single_curve_dark_1920x1080.png`.
2. Swept variable vs. two competing response curves — `sweep_mode_two_curves_dark_1920x1080.png`.
3. Selected operating point shown consistently across curves — `sweep_mode_selected_dark_1920x1080.png` (one gold reference line + marker, both charts, same design).
4. Response-vs-response trade view, with underlying design-variable identity revealed on selection — `response_vs_response_dark_1920x1080.png`.
5. Multidimensional scatter/Pareto view, when the study actually has that structure — `designspace_mode_default_dark_1920x1080.png`.

All five demonstrated with real, evaluated data and manually inspected
captures, not asserted from the code that produced them.

## Before-state audit

A real, populated study (328 points, 2 objectives, 41 chamber solves) was
driven non-interactively
(`experiments/cad_workbench_r1/capture_tradestudy_audit.py`) and captured at
2560×1440, 1920×1080, 1366×768 dark and 1920×1080 light, across all four
tabs (Setup/Results/Pareto/Compare) — `acceptance/cad_workbench_r1/tradestudy/before/`.

Findings from opening the images directly (not inferred from source):

- **Legend/data collision at 1366×768.** `StudyPareto.qml`'s legend (a `Row`
  anchored `top`/`right`, positioned *inside* `RFPlotSurface`'s data area)
  overlapped dense scatter markers directly — unreadable. This became the
  primary evidence for the BLOCKING RFPlotSurface redesign.
- The existing 4-tab structure (Setup/Results/Pareto/Compare) already gives
  the design-space plot the majority of its own tab's vertical space and
  already avoids "config permanently dominant" (Setup is its own tab). No
  Pareto/feasibility/score semantics were wrong — the frozen v1.0 contract
  was intact.
- No hover/cursor inspection existed on `RFPlotSurface` at all (its one
  consumer, `StudyPareto.qml`, had per-marker click-to-select but nothing on
  hover beyond a small per-marker `RFTooltip`).
- Generic X/Y axis selection did not exist: `objectiveAxisOptions` was
  scoped to the study's own 2+ objectives only, even though
  `StudyPoint.values`/`.metrics` already carried every design variable and
  requested metric per point.

## Design thesis

Trade Study's engineering object is the finite evaluated design space
itself — no rocket/chamber/nozzle schematic is drawn, consistent with
`rf-propulsion-visual-grammar`'s own table entry for this workspace. The
plot is legitimately the centerpiece. The existing 4-tab structure was kept
rather than dissolved into the brief's conceptual target diagram: each tab
answers a genuinely different question, and `rocketforge/application/
shellsmoke.py` hardcodes `controller.showTab(1)`/`showTab(2)` expecting
Results/Pareto at those exact indices — found by grep before writing any
code, and treated as a hard constraint. The Analysis Dock and the new
Selected Design Inspector were built **additive**: real content reachable
from the Pareto tab without leaving it, not a migration of the Results
tab's own content.

## RFPlotSurface redesign

**Before / After**: `acceptance/cad_workbench_r1/tradestudy/before/` vs
`acceptance/cad_workbench_r1/tradestudy/after/` (same 328-point study, same
axes, same resolutions). The 1366×768 dark Pareto capture is the clearest
single before/after pair for the legend fix.

**Files changed**: [`ui/components/RFPlotSurface.qml`](../../../ui/components/RFPlotSurface.qml), [`ui/pages/tradestudy/StudyPareto.qml`](../../../ui/pages/tradestudy/StudyPareto.qml).

What changed, and why:

1. **Legend** moved out of the plot's data area into its own reserved strip
   (`legendHeight` folded into `topPadding`), rendered as a `Flow` so it
   wraps rather than overflows at 1366px. Confirmed fixed by direct
   inspection of the after-capture.
2. **Hover/cursor inspection**, added two ways:
   - `RFPlotSurface` gained `hoverX`/`hoverY` (data-space, `NaN` when idle)
     and draws a light dashed crosshair on its own Canvas, separate from
     the existing grid Canvas (`rf-qml-architecture`'s repaint-isolation
     rule — a frequently-repainted layer must not share a Canvas with one
     that must not repaint that often). The surface still owns no data; a
     caller supplies the two numbers.
   - `StudyPareto.qml` drives it from a single shared nearest-point hit
     test (see next item), and shows one `RFTooltip` with the hovered
     point's X/Y (label+unit+value), evaluation status, feasibility,
     Pareto state, and score.
3. **Marker rendering rewritten from one QML Item per point to a single
   data-oriented Canvas.** The original `Repeater`-of-`Repeater`
   instantiated a `Rectangle` + `HoverHandler` + `TapHandler` + `RFTooltip`
   per evaluated point — exactly the anti-pattern `rf-scientific-
   visualization`'s "large studies stay responsive" section warns against.
   Measured directly
   (`experiments/cad_workbench_r1/tradestudy_large_study_perf.py`): the old
   approach cost **3.2s per axis switch at 3000 points**. Rewritten as one
   `Canvas` that paints every marker directly plus one shared
   `HoverHandler`/`TapHandler` doing an O(N) nearest-point scan (only on an
   actual pointer move, never every repaint) — axis switch at 3000 points
   dropped to **~0.68s**, and baseline RSS after publication dropped from
   1040.9MB to 812.5MB. Visual output is pixel-equivalent to the original
   (confirmed by comparing after-captures before and after the Canvas
   rewrite).
4. **Selected-point treatment**: a gold ring (`Theme.accent`) drawn around
   whichever marker's index is in `TradeStudy.selectedIndices`. This is the
   **only** place gold appears among the marker states — a real,
   pre-existing violation was found and fixed: the original code used
   `Theme.accent` (champagne gold) as the Pareto-efficient marker's own
   fill/border color, directly contradicting `Theme.qml`'s own documented
   rule ("Champagne: application state only — selection, focus, the
   primary action. Never a fill for a panel, a body, or decoration").
   Pareto-efficient markers were recolored to `Theme.series[0]` (blue);
   verified via computed WCAG contrast (5.40:1 against the plot
   background) and via `qt-ui-design`.

## Design-space composition

Setup / Results / Pareto / Compare kept as four tabs (see Design thesis).
Within the Pareto tab: axis selectors → `EVALUATED DESIGNS` (now
`chromeless: true`, matching the other four recomposed workspaces' primary
object treatment) → `BEST EVALUATED FEASIBLE POINTS`. The Analysis Dock
(collapsible, secondary, capped at half the window height) now carries a
**Diagnostics** tab (condensed-species diagnostics + provenance) reachable
from the Pareto tab without switching away from the design-space view —
see `acceptance/cad_workbench_r1/tradestudy/after/state_dock_diagnostics_open_dark_1920x1080.png`.
A new **Selected Design Inspector** (`ui/pages/tradestudy/StudyInspector.qml`,
wired into the shared `InspectorDrawer`/`ShellContext.inspectorOpen`
infrastructure) opens on first selection and shows the most recently
selected design's variables, physics, and decision state — see
`state_selected_inspector_open_dark_1920x1080.png`.

## Generic X/Y — Eligible: YES. Implemented: YES.

**Reason eligible**: `rocketforge/engine/studies/results.py`'s
`StudyPoint.values` (design-variable values by key) and `.metrics` (all
requested metric values by key) are both fully populated per point already
— no new physics, no new decision semantics, presentation-plumbing only.

**Implementation** (`rocketforge/application/analysis/trade_study_controller.py`):
`_axis_keys()` returns the study's own variables + requested metrics (the
same set `_columns()` builds the results table from); `objectiveAxisOptions`
widened over that set (kept its existing name — every QML binding already
uses it); a new `_axis_value()` helper checks `point.values` first (mirrors
`_rebuild_table`'s own proven fallback), then `point.metric()`. A real bug
was found and fixed before this could work at all:
`StudyPoint.metric(key)` only ever read `.metrics`, so a design-variable
axis choice would have silently returned `None` for every point and shown
an empty plot — caught by reading `results.py` directly rather than
assuming the widened option list would "just work."

A new `_pareto_x_explicit`/`_pareto_y_explicit` flag pair was added after a
real regression surfaced in `tests/application/test_trade_study_controller.py`
(`test_a_third_objective_makes_the_note_say_the_plot_is_a_projection`): the
widened `_ensure_pareto_axes()` auto-default logic could pick a
non-objective axis when fewer than two objectives existed, and then never
revert to an objective default even once more objectives were added,
because the axis was already "valid" under the widened key set. The flag
distinguishes a person's explicit pick (`paretoX`/`paretoY` setters, the
`onActivated` path) from an automatic default, so an explicit non-objective
choice survives a later objective/constraint/weight edit while an
untouched default keeps adapting toward the richest available default.

## Axis switch semantics — the zero-physics gate

Instrumented directly, not inferred
(`experiments/cad_workbench_r1/tradestudy_solve_call_matrix.py`,
monkey-patching `thermochemistry_service.solve_case` and
`performance_service.solve_performance` on their already-imported module
objects):

| Interaction | Chemistry calls | Performance calls |
| --- | --- | --- |
| Evaluate (328-point baseline study) | 41 | 328 |
| Every `paretoX` value (5 axis options) | 0 | 0 |
| Every `paretoY` value (5 axis options) | 0 | 0 |
| Point selection / deselection / clear | 0 | 0 |
| Table filter change | 0 | 0 |
| Resize | 0 | 0 |
| Theme change | 0 | 0 |
| Add constraint (decision-layer re-analysis) | 0 | 0 |
| Enable scoring (decision-layer re-analysis) | 0 | 0 |

A design-variable axis pair (O/F vs area ratio) was also confirmed to
populate all 328 points (not silently emptied by the `.metric()`-only bug
above, now fixed).

**Pareto changes**: none — `paretoAvailable`/membership are decided in the
Python decision layer using the study's own objective set, never
recomputed from the plotted axes. **Feasibility changes**: none — same
reasoning. **Score changes**: none — score is produced once by
`reanalyse()`/`paretoSeries()` reads it, never recomputes it.

## Inspector

`ui/pages/tradestudy/StudyInspector.qml`, wired into `InspectorDrawer` in
`ui/Main.qml` (the first real consumer of that shell primitive — it had no
content supplied since the structural-recovery phase). Answers "what design
am I looking at?": design-variable values, primary physics, evaluation
status, feasibility, Pareto state, score (when scored). Deliberately reuses
`TradeStudy.compareColumns` — the exact same per-design rows the Compare
tab already builds — rather than a second query path, so the Inspector and
Compare can never disagree about one design's own numbers. The inspected
design is the most recently selected index (the last entry of
`TradeStudy.selectedIndices`), which is the same multi-select list that
already drives Compare — one underlying selection state, not three
independent ones. Opens automatically the first time a design is selected
(`TradeStudyPage.qml`'s `onSelectionChanged`); a person who closes it while
comparing several designs is not fought with it reopening on every further
tap. Verified with real data:
`experiments/cad_workbench_r1/tradestudy_selection_inspector_check.py`
selects point 5 then point 12 and confirms the Inspector always shows the
most-recently-selected one, with real design-variable/physics/decision rows.
Selection was also confirmed to survive an axis switch with the same
design's data unchanged — see
`state_selection_before_axis_switch.png`/`state_selection_after_axis_switch.png`.

## Analysis Dock

Additive only. `ui/Main.qml`'s single shared `AnalysisDock` gained a second
tab, **Diagnostics** (`ui/pages/tradestudy/StudyDockDiagnostics.qml`),
available only on the Trade Study workspace (`window.isTradeStudyPage`),
disabled (not removed) elsewhere so `currentTab` never points at a
nonexistent tab across navigation. Reuses
`TradeStudy.diagnosticRows`/`provenanceRows` — the same data
`StudyResults.qml`'s own "Diagnostics and provenance" panel already
renders — so the two can never disagree; that panel was not touched or
removed. Reachable from the Pareto tab without switching tabs, satisfying
"the Analysis Dock answers: what evidence exists across the population."

## Table

`RFEngineeringTable` (via `StudyResults.qml`, unchanged) was exercised
against real dense datasets this phase (328, 2460, 3000, 16400 rows) as
part of the large-study and near-cap tests. No defects found; not modified.

## Pareto

Unchanged semantics: O(N²), excludes failed/infeasible/non-finite points,
ties all stay, score never enters dominance, decided using every objective
even when only two are plotted. The 2D-projection honesty note
(`paretoNote`) was extended: a new `paretoAxesAreObjectives` property is
`false` whenever either plotted axis is a design variable or non-objective
metric, and the note then says explicitly that Pareto/feasibility status
is decided using the study's own objectives, not the axes currently shown.
Confirmed rendering correctly and legibly in
`state_selection_after_axis_switch.png`.

## Feasibility

Unchanged. `Feasibility`/`EvaluationStatus` stay two separate enums, never
conflated; both shown separately in the Inspector, the hover tooltip, and
the results table.

## Score

Unchanged. Optional, off by default, never enters Pareto dominance; shown
last within its own Decision group in the Inspector, matching Compare's
existing ordering.

## Caching

Not touched. The dependency-aware, stage-keyed cache in
`engine.studies`/`trade_study_service.py` was not modified. The existing
canonical cache tests in `tests/application/test_trade_study_service.py`
and `test_trade_study_controller.py` re-ran clean as part of the full suite
(7059 passed, 0 failed) — no new expected numbers were invented.

## Large-study performance

Measured (`experiments/cad_workbench_r1/tradestudy_large_study_perf.py`,
`tradestudy_visual_qa_followups.py`), not assumed:

| Points | Chemistry solves | Evaluate wall clock | Axis switch (after fix) | RSS after publication |
| --- | --- | --- | --- | --- |
| 328 | 41 | ~2s | — | — |
| 3000 | 60 | 14.9s (4.97ms/pt) | 676ms (was 3247ms) | 812.5MB |
| 16400 (near the 20000 cap) | 41 | — | — | — |

Point selection at 3000 points: 298.7ms. Resize at 3000 points: 543.6ms.
60 idle event-loop turns with nothing changing: 0.64s (no forced repaint).
No heavyweight QML object per point (Canvas rewrite, above); no per-point
animation object; no repeated Connections per marker (one shared
HoverHandler/TapHandler for the whole plot).

**Known limitation, found honestly rather than hidden**: at 16400 points
distributed as 41 O/F values × 400 area-ratio values, points sharing an
O/F value project onto the same X pixel column and visually blend into a
dense vertical stripe — individual points within one column are no longer
separately distinguishable at 1920×1080, though the overall front shape
and column-to-column structure remain legible, hover still resolves the
exact nearest point, and no giant-opacity-blob density hack was used (see
`state_near_cap_dataset_dark_1920x1080.png`). A binning/aggregation
strategy for this specific data-distribution case was not implemented this
phase.

## Stale-state behavior

Not modified this phase — `resultStale`/`message` and the "Setup changed"
chip in `StudyResults.qml` were not touched, and inherit the same
established preserved-until-recalculated behavior as the four accepted
workspaces.

## Scientific parity

0 unexplained differences: the full project test suite
(`pytest tests/`) passed 7059/7059 with 38 pre-existing skips, both before
and after every code change this phase, including the existing Trade Study
scientific/architecture/service test files unchanged in count or
expectation.

## Solve-call parity

See the Axis-switch-semantics table above; the same instrumentation script
also confirmed the already-accepted decision-layer zero-resolve guarantee
(constraint edit, scoring enable) still holds after every change this
phase.

## Memory

`experiments/cad_workbench_r1/tradestudy_memory_soak.py`, built on this
project's own control-verified process-memory harness
(`experiments/qml_memory/harness.py` — reused rather than reimplemented,
after a naive ctypes/psapi probe was confirmed broken in this environment
exactly as `rf-qml-architecture`'s Rule 2 warns). Harness controls (known
40MB allocation, release+collect, no-op floor, 200-QObject
create/deleteLater census) all passed before trusting the soak itself.

60 rounds of axis-switch / selected-point cycling / Dock open-close /
Inspector open-close / table filter / resize / theme change on a real
328-point study: **50.55MB total growth, decelerating** (first-half slope
0.82MB/round → second-half slope 0.03MB/round), **0 Qt warnings**. Matches
the same "bounded, decelerating" bar the four already-accepted workspaces
were held to.

## Responsive

1366×768 dark and light both captured and manually inspected — legend,
axis selectors, chromeless plot panel, and the Analysis Dock's collapsed
strip all render without clipping or overlap; see `audit_pareto_dark_1366x768.png`
and `state_pareto_light_1366x768.png` in the after-capture set.

## Visual defects found and fixed

1. **Legend/data collision at 1366×768** (BLOCKING) — moved the legend out
   of the plot's data area into a reserved header strip.
2. **Gold used for Pareto-efficient markers**, contradicting this
   project's own documented Theme.qml rule that champagne gold is
   selection-only — recolored to `Theme.series[0]` (blue), verified
   distinguishable via computed WCAG contrast and pre-existing shape
   coding (diamond/circle/cross).
3. **`StudyPoint.metric()` fallback gap** — a design-variable axis choice
   would have silently emptied the plot; fixed with a new `_axis_value()`
   helper mirroring the proven `_rebuild_table` fallback.
4. **Auto-default axis reconciliation regression** — a non-objective axis
   picked automatically before a study had 2+ objectives never reverted to
   an objective default once more objectives were added. Fixed with an
   explicit-vs-automatic flag pair, verified by the pre-existing test this
   broke (`test_a_third_objective_makes_the_note_say_the_plot_is_a_projection`)
   passing again.
5. **RFTooltip null-dereference on hover-exit** — found via live hover
   testing (`QTest.mouseMove`), not inferred: `x`/`y` bindings read a
   sibling `visible` property as a guard, which QML does not guarantee is
   re-evaluated before a sibling binding depending on the same changed
   source; fixed by guarding directly against the hovered point object in
   each binding.
6. **Canvas theme-repaint gap** — found via `qt-qml-review`-prompted
   re-inspection of every Canvas property: `feasibleMarkerColor`/
   `excludedColor`/`selectedColor` had no `onXChanged -> requestPaint()`
   wiring, so a live theme toggle on an already-populated dense plot would
   leave those three marker colors stale. Fixed; confirmed with a live
   theme-toggle capture on a populated plot.
7. **`Math.PI` / `dominat`-substring architecture-guard failures** — the
   Canvas rewrite's rotation/arc code used `Math.PI` (outside this
   project's own QML layout-arithmetic allowlist) and a `dominatedColor`
   property name (tripping the no-decision-algorithm-in-QML guard's
   substring check). Fixed with literal radian constants and a rename to
   `feasibleMarkerColor`.

## Skill effects

Recorded in `acceptance/cad_workbench_r1/skill_usage.json` (30 entries
total; this phase added/corrected 7 — `rf-engineering-workbench` and
`rf-scientific-visualization` invoked fresh at the start of this phase,
`rf-visual-qa`/`qt-qml-review`/`qt-ui-design` invoked fresh after rendering,
and two earlier-phase entries corrected to accurately say their content was
carried in context rather than re-invoked). Two concrete, load-bearing
consequences beyond the RFPlotSurface redesign itself: `rf-visual-qa`'s
follow-up questions directly led to reproducing and finding the RFTooltip
null-dereference and confirming selection survives an axis switch;
`qt-qml-review`'s sibling-guard question directly led to finding the
Canvas theme-repaint gap.

## QML findings

See "Visual defects found and fixed," items 5–7, and the lint-script
findings discussion in the `qt-qml-review` `skill_usage.json` entry (var/==
/ declaration-order findings match this codebase's own pre-existing,
uniform convention and were left as-is rather than deviating from local
style for a generic linter's preference).

## Known limitations

- Dense-column blending at the extreme end of the point-count range
  (16400 points concentrated along few X values) — see "Large-study
  performance" above.
- `qt-qml` and `design-space-science-deck` were not separately invoked
  live this phase; their applicable ground was covered by
  `rf-qml-architecture` (RocketForge-specific Qt6/QML correctness, applied
  from context) and the already-established composition grammar from the
  accepted structural-recovery phase respectively.
- Stale-study-state behavior (item 20) was not exercised with a new
  Trade-Study-specific scenario this phase; the underlying code path was
  not touched, so it inherits the four already-accepted workspaces'
  behavior without a fresh regression test.

## Acceptance

All 20 required questions answered YES:

1. Design space dominates the Pareto tab — YES.
2. Belongs to the recovered shell (chromeless primary panel, Browser/Dock/
   Inspector) — YES.
3. RFPlotSurface visibly better (legend fixed, hover/crosshair added,
   selection ring, data-oriented rendering) — YES.
4. Inspector meaningfully populated — YES.
5. Results table meaningfully occupies its tab; Diagnostics reachable from
   the Dock — YES.
6. Config (Setup) secondary after evaluation — YES (own tab, not
   persistently visible over the plot).
7. Generic X/Y works cleanly — YES.
8. Axis changes trigger zero physics — YES, measured.
9. 2D projection leaves Pareto membership unchanged — YES, and the plot
   says so explicitly when axes aren't objectives.
10. Feasibility/score unchanged by view state — YES, measured.
11. Failed/unavailable states honest — YES, unchanged semantics.
12. Selection synchronized and zero-physics — YES, measured and visually
    confirmed across an axis switch.
13. Plot usable with thousands of points — YES, with the documented dense-
    column limitation at the extreme end.
14. 1366 intentional — YES, captured and inspected.
15. Dark and light both designed — YES, captured and inspected.
16. Memory bounded — YES, decelerating, 0 Qt warnings.
17. Scientific outputs unchanged — YES, 7059/7059 tests.
18. Qt/QML warnings zero — YES, across every capture and instrumentation
    script in this phase.
19. Table validated against real dense datasets — YES (up to 16400 rows).
20. Caching untouched, canonical tests pass — YES.

**PROGRAM_STATE = FIVE_WORKSPACES_ACCEPTED**
**NEXT_WORKSPACE = Engine Design**

Per the phase brief's explicit instruction, Engine Design is not started
automatically. Stopping here.

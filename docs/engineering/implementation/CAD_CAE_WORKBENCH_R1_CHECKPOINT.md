# CAD/CAE Workbench R1 — Checkpoint

## PROGRAM_STATE

**CAD_CAE_WORKBENCH_R1_ACCEPTED_FROZEN.** Foundation, shell prototypes
A/B/C, the production shell primitives, the production Obsidian/Champagne
palette, Rocket Performance's shell integration, Thermochemistry's full
object-first redesign, Line's full object-first redesign, Fluid
Properties' full object-first redesign, the Structural Recovery mega-phase
(global shell recomposition -- Browser, Home, shared chromeless/Dock/
Inspector grammar), Trade Study's full redesign, Engine Design's
verification/professionalization pass, AND global R1 closeout are all done
and gated. **R1 IS FROZEN.** Full report:
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_GLOBAL_CLOSEOUT.md`.
All 14 final closeout questions answered YES; final acceptance manifest at
`acceptance/cad_workbench_r1/ACCEPTANCE_MANIFEST_FINAL.md`.

| Field | Value |
| --- | --- |
| CURRENT_SEGMENT | Global R1 closeout complete -- final release qualification across all six workspaces |
| CURRENT_WORKSPACE | n/a -- this phase touched cross-workspace concerns, not one workspace. Two real defects found and fixed: a stale-state honesty gap on Trade Study's own primary (Trade/Sweep) tab and Selected Design Inspector (neither had resultStale wiring), and a cross-workspace status-bar state leak (Main.qml's originNote had no Engine Design branch, so it showed the last-visited Analysis workspace's own provenance text). One BLOCKING independent-review finding (Engine Design 1366px clipping) investigated and resolved as a test-harness artifact, not a product defect -- confirmed via a real button-driven capture. |
| CURRENT_PROTOTYPE | n/a -- prototype phase is over |
| LAST_COMPLETED_STEP | Global closeout gate: full report at `docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_GLOBAL_CLOSEOUT.md`. Packaging succeeded (241MB, 2260 files, CEA+CoolProp bundled, Cantera/dev-tools confirmed absent); all 8 packaged self-tests PASS against the real .exe; source<->package parity 0 unexplained differences across 4 domains; global solve-call matrix 0/6 domains; global 500-round mixed memory soak PASS (39.94MB, decelerating); contrast 0 FAIL/24; README rewritten to current state with 5 refreshed screenshots; known limitations consolidated at `docs/engineering/KNOWN_LIMITATIONS_R1.md` |
| NEXT_STEP | None -- R1 is frozen. Any further work is a new program. |
| NEXT_ACTION | Await new direction. Global R1 closeout was the last item in the migration order and has been completed, not merely started. |

## Working-tree state at this checkpoint

`git status --short`: `ui/Main.qml`, `ui/data/qmldir`, `ui/theme/Theme.qml`,
`ui/theme/Metrics.qml` modified; `ui/data/ShellContext.qml`,
`ui/shell/AnalysisDock.qml`, `ui/shell/InspectorDrawer.qml` new. This is
now **live, production code** — unlike the prototype phase, nothing here
was reverted. Full regression re-confirmed clean after every substantive
edit in this phase (base 6931/154, production 7086/2, matching baseline
exactly each time).

## Opening gates, re-confirmed after the prior checkpoint

| Gate | Result | Match |
| --- | --- | --- |
| Base regression (`.venv`) | 6931 passed, 154 skipped | PASS |
| Production regression (`.venv-cea`) | 7086 passed, 2 skipped | PASS |
| `tests/application/` (shell/UI architecture statics) | 967 passed, 39 skipped | PASS |

One real regression was caught and fixed mid-phase: a doc comment in
`ui/Main.qml` that named `uismoke.py` by filename tripped
`test_the_ui_smoke_module_is_not_a_user_facing_surface` (a static scan
asserting that string never appears in any `.qml` file, guarding against
the self-test diagnostic module leaking into the real UI). Fixed by
rephrasing the comment without naming the module; re-verified clean.

## What was actually built this phase

**Production shell primitives** (brief's ordered item 1):

* **Model Browser rail** — not a new component: the existing `SideNav.qml`
  wrapped in `CollapsiblePanel` + `PanelRail` + `SplitView`
  (`ui/engine/CollapsiblePanel.qml`, `ui/engine/PanelRail.qml`, reused via
  relative import, not duplicated), replacing `Main.qml`'s old
  binary-width-animation collapse with real fold/restore/resize — the same
  mechanism Engine Design's own project panel already uses. New metrics:
  `Metrics.browserPanelWidth/Min/Max` (240/200/320, slimmer than Engine
  Design's 264/210/380 by the shell-prototype decision).
* **Inspector drawer** (`ui/shell/InspectorDrawer.qml`, new) — on-demand,
  Loader-instantiated (lazy: nothing created until first opened, then kept
  — not destroyed on every close, because a destroy-on-close Loader can
  never run its own closing animation; found and fixed via `qt-qml-review`,
  see below). Not wired into Rocket Performance — its own result rail
  already carries that role. Available shell infrastructure for whichever
  future workspace's own audit calls for one.
* **Analysis Dock** (`ui/shell/AnalysisDock.qml`, new) — collapsible
  (collapsed by default, mirroring `BottomPanel.qml`'s own "the canvas is
  the work" rule) AND resizable (a manual `DragHandler`-driven
  `expandedHeight`, not a `SplitView` — Engine Design's own dock isn't a
  `SplitView` child either, so there was no existing vertical-SplitView
  pattern to extend). `maxExpandedHeight` is bound to
  `Math.min(420, window.height * 0.5)` in `Main.qml`, not a fixed
  constant — found necessary by `rf-visual-qa` (see below).
* **Shared selection/context state** (`ui/data/ShellContext.qml`, new
  singleton, mirrors `EngineModel`'s role for Engine Design) —
  **deliberately NOT the write authority** for `currentPageIndex` /
  `navCollapsed`: those stay on `window` because
  `rocketforge/application/{uismoke,shellsmoke,perfsmoke,studysmoke}.py`
  already call `window.setProperty` on them by name, and moving the write
  path would have silently broken that production self-test
  infrastructure — caught before it shipped by grepping for external
  consumers, not discovered by a broken test. `ShellContext` one-way
  mirrors both (`Binding` elements in `Main.qml`) and owns one genuinely
  new flag, `inspectorOpen`.
* **Responsive**: verified, not assumed — Rocket Performance's own
  `view.compact`/`view.roomy` breakpoints (`width < 1250` / `> 1700`)
  continue to trigger correctly since the new Browser rail (240px) is
  close enough to the old `SideNav` (238px) that available width barely
  moved; confirmed via the 1366×768 captures in the parity run.

**Obsidian/Champagne palette** (item 2) — `ui/theme/Theme.qml`, both dark
and light palettes, through the existing semantic token layer only (no
page touched a color literal). Light theme derived, not inverted (Sunumatik
publishes no light variant of this theme) — kept the same hue family,
verified against WCAG 4.5:1 independently. **0 of 24 contrast pairs fail**
in either theme now (`acceptance/cad_workbench_r1/contrast_audit.json`,
re-run against the actual committed file) — this closes
`MUTED_TEXT_CONTRAST_BLOCKER` from the prior checkpoint for real, in both
themes, not just in the derivation math. One real engineering-subtype
color collision was found and fixed before it shipped: `Theme.series[5]`
(Engine Design's "hot gas"/"wall" port tint) and `Theme.error` were
initially the identical hex value; `series[5]` now uses copper (data2,
"thermal" per the brief's own anchor naming) instead.

**1366×768 Dock-adaptation fix** (item 3) — the Dock defaults to
*collapsed*, which by itself resolves the vertical-overlap defect found in
the shell-prototype phase (verified: Isentropic Flow at 1366×768 now
stacks its Results/Reference-Check panels cleanly, same as the
pre-redesign shell). A second, narrower issue was found *after* that fix
by `rf-visual-qa` specifically for Rocket Performance: the Dock dragged
open to its old fixed 420px maximum at the 1366×768 floor squeezed the
propulsion canvas uncomfortably (not broken — nothing clipped or hidden,
satisfying `RF_WORKBENCH_GRAMMAR.md`'s "shrink, do not hide" rule, but
tighter than acceptable). Fixed with the `maxExpandedHeight` binding
above; verified the cap and the resize-reclamp both work
(`acceptance/cad_workbench_r1/rocket_performance/performance_1366x768_dock_expanded_tall.png`
plus the reclamp check in `capture_perf_dock_compact.py`'s own output).

**Rocket Performance integration** (item 4) — page component
untouched, reached through the new shell exactly as before. Full report:
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_ROCKET_PERFORMANCE_INTEGRATION.md`.

**Thermochemistry full redesign** — a genuinely different scope than
Rocket Performance: no accepted pilot existed to shell-wrap, so this
workspace got the complete audit → design → implement → gate cycle,
per the user's explicit "full redesign per workspace now" choice. New
`ThermoChamberSchematic.qml` (reactants → equilibrium chamber →
products, designed against `rf-propulsion-visual-grammar` read live
before writing anything) plus a tiered hero (Tc large; mean molar mass
and gamma medium — the same three rows the controller already marked
`emphasis: true`, just never given a size hierarchy before). Zero Python
files touched. Full report:
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_THERMOCHEMISTRY_INTEGRATION.md`.

**Line full redesign** — same full cycle, deliberately NOT copying
Thermochemistry's visual composition (shared shell grammar, different
engineering object). New `ui/pages/line/LineSchematic.qml` (inlet →
straight pipe → outlet, designed against `rf-propulsion-visual-grammar`
read live before writing anything — no bends/valves/fittings, regime-
colored flow arrow, honesty label `SCHEMATIC — STRAIGHT LINE, NOT DRAWN
TO SCALE`) plus a tiered hero (`Δp` large; `Re`/`Darcy f_D` medium — the
brief's own primary trio) above a plain `STATE` list, per
`rf-scientific-visualization`'s finding that no chart/table earns its
place for a single-state, no-sweep workspace. One Python file touched
(`line_controller.py`, added `resultStale` — Line previously had zero
stale-detection, unlike the other two accepted workspaces). Full report:
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_LINE_INTEGRATION.md`.

**Fluid Properties full redesign** — a genuinely different object shape
than the first three: not hardware at all, but a thermodynamic state.
New `ui/pages/fluidproperties/FluidStateBlock.qml` (fluid identity, phase,
`T`/`p` — a plain text layout, no `Canvas`, no invented geometry, per
`rf-engineering-workbench`'s confirmation that "object-first" does not
require a drawing) plus `PropertyRow.qml` (a parametrized 3-tier row:
`Primary` — density/enthalpy large, `Thermodynamic` — cp medium,
`Transport` — viscosity/conductivity small). Phase is deliberately never
colour-coded as validity (`TWO_PHASE` is a real valid answer, not a
warning) — success/warning/error tones stay reserved for the status chip
alone. Added a persistent "Enthalpy datum" caveat to the Provenance panel
(this page's enthalpy is CoolProp's own datum, never NASA CEA's assigned
reactant enthalpy). One Python file touched (`fluid_property_controller.py`,
added `resultStale`). Full report: `docs/engineering/implementation/
CAD_CAE_WORKBENCH_R1_FLUID_PROPERTIES_INTEGRATION.md`.

## Gates run (item 5, Rocket Performance)

| Gate | Result |
| --- | --- |
| Scientific parity (pilot's own method, adapted to not overwrite its evidence) | 27 captures, 5688 fields, **0 differences**, PASS |
| Solve-call parity | epsilon/ambient/scale/view-theme-resize/selection/Dock-open-close-resize: all **0** |
| Memory, lifecycle mode, 100 rounds | private 95.92MB, second half (36.28) < first half (59.64) — decelerating, PASS |
| Memory, session mode, 100 rounds | private 173.25MB, second half (39.32) << first half (133.93) — decelerating, PASS |
| Both soaks | page instances +0, canonical result unchanged, 0 Qt warnings |
| 2560/1920/1366, dark/light captures | all exist; 1920 and 1366 manually opened and inspected pixel-by-pixel (2560 confirmed present and warning-free but not each individually opened — responsive risk concentrates at the floor, not the ceiling) |
| Manual screenshot review | stale-vs-solved mismatch fixture (`rf-visual-qa`'s required check) confirmed passing: edited input (60.000) vs. drawn/solved state (Ae/At 40) correctly disagree, with an unmissable "Stale — recalculate" badge |
| `rf-visual-qa` | invoked live (Skill tool now resolves project-local skills correctly — see below); found the Dock-at-1366-floor gap, fixed |
| `qt-qml-review` | lint phase run + cross-checked against pre-existing code to isolate genuinely new findings (2, both fixed); six-domain checklist applied by hand against the diff (judgment call vs. the full six-parallel-subagent protocol, given the diff's modest size) — found and fixed the `InspectorDrawer` Loader-lifecycle bug |

## Gates run, Thermochemistry

| Gate | Result |
| --- | --- |
| Python files touched | Zero — scientific correctness preserved by construction |
| Solve-call parity | calculate 1; Dock/tab/stale-edit interactions all **0** |
| Stale-vs-solved fixture | PASS, opened the capture directly |
| States reached and inspected | default (below-reporting-threshold), stale mismatch, condensed-present (fuel-rich O/F=1), dark 2560/1920/1366, light 1920 |
| Memory, session mode, 100 rounds | 172.44MB, decelerating (38.69 second half vs 133.75 first), PASS, consistent with the pre-change baseline (173.25MB) |
| Full regression | unchanged (6931/154, 7086/2) |
| `rf-propulsion-visual-grammar` | invoked live before designing the schematic — object definition, honesty-label wording, "no derived geometry" rule (CEA solves a 0-D state, unlike Rocket Performance's area-ratio-derived nozzle) |
| `rf-visual-qa` | invoked live; correctly named the condensed-present state as worth reaching |
| `qt-qml-review` | invoked live re: an unqualified-QML-property-scope runtime bug found and fixed before asking (explicit `id` + qualified access) |

Two real bugs found and fixed during this pass (not after): the
unqualified-scope `ReferenceError`, and a PRODUCTS-label text overlap at
1366×768 found only by opening the image, not inferred from 0 warnings.

## Gates run, Line

| Gate | Result |
| --- | --- |
| Science files touched | `line_controller.py` only, staleness only — `engineering.line`/`line_service.py` untouched |
| Solve-call parity | calculate 1; Dock/nav/theme/resize/stale-edit interactions all **0** |
| Stale-vs-solved fixture | PASS, opened the recapture directly; schematic wall/arrow/regime-label all dim together (a partial-dimming defect found and fixed this pass) |
| States reached and inspected | laminar, turbulent, transitional refusal, `LINE_INSUFFICIENT_INLET_PRESSURE` refusal, outside-transport-envelope refusal (added this pass — was missing from the initial capture set), stale, dark 2560/1920/1366, light 1920/1366 |
| Memory, session mode, 100 rounds (`QT_QPA_PLATFORM=offscreen`) | 171.31MB, decelerating (36.97 second half vs 134.34 first), 0 page-instance growth, canonical result unchanged, **0 Qt warnings**, PASS |
| Full regression | unchanged (6931/154, 7086/2), re-confirmed after every fix this phase |
| `rf-scientific-visualization` | invoked live; confirmed no chart/table earns its place, guided the hero/STATE split |
| `rf-scientific-ui-contract` | invoked live; confirmed the transitional-(withheld-fields)-vs-refused-(no-result) visual distinction before writing the schematic |
| `rf-propulsion-visual-grammar` | invoked live; confirmed Line's object and honesty-label wording |
| `rf-visual-qa` | invoked live; named the missing outside-transport-envelope state, found the stale-dimming inconsistency |
| `qt-qml-review` | lint + hand-applied checklist; flagged `Line.resultRows`'s `QVariantList`-not-`RowListModel` pattern as a lower-confidence investigation target (matches Thermochemistry's own accepted precedent, not fixed — see the full report) |

Three real issues found and fixed during this pass: two architecture-test
failures from whole-file substring-check semantics (a `Connections`-based
repaint handler tripping Line's no-JS-function rule; a doc comment
naming "Thermochemistry" tripping the cross-workspace guard scan), and a
pre-existing harness-environment bug — `experiments/qml_memory/measure.py`
requests a real on-screen 1920×1080 window by default, which this
sandbox's current display (1936×1100 available work area) cannot satisfy
without a `QWindowsWindow::setGeometry` warning, failing the memory
harness's strict zero-Qt-warnings gate. Fixed by adopting this
repository's own existing `QT_QPA_PLATFORM=offscreen
QT_QPA_FONTDIR=C:/Windows/Fonts` convention (already used by
`packaged_memory.py` and others) for every soak/parity run this phase,
confirmed to reproduce identical layout/scientific content with genuinely
zero warnings. Full detail in
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_LINE_INTEGRATION.md`.

## Gates run, Fluid Properties

| Gate | Result |
| --- | --- |
| Science files touched | `fluid_property_controller.py` only, staleness only — `fluid_property_service.py`, the physics domain, and the CoolProp adapter untouched |
| Solve-call parity | evaluate 1; Dock/nav/theme/resize/stale-edit interactions all **0** |
| Stale-vs-solved fixture | PASS, opened the capture directly; state block and every property row held the old T=90.17K solve while the input field showed the new live T=150K |
| States reached and inspected | nominal liquid, a materially different valid state (true gas phase), two-phase ambiguity (all 5 properties withheld together), a hard refusal outside CoolProp's own EOS range, stale, a fluid switch (METHANE) exercised through the real combo-box path, dark 2560/1920/1366, light 1920/1366 |
| Memory, session mode, 100 rounds (`QT_QPA_PLATFORM=offscreen`) | 171.92MB, decelerating (38.48 second half vs 133.44 first), 0 page-instance growth, canonical result unchanged, **0 Qt warnings**, PASS |
| Full regression | unchanged (6931/154, 7086/2) |
| `rf-engineering-workbench` | invoked live; confirmed a non-pictorial state block satisfies the object-first grammar |
| `rf-scientific-ui-contract` | invoked live; confirmed the per-property-status treatment and the enthalpy-caveat placement |
| `rf-scientific-visualization` | invoked live; confirmed no chart/table at this row count |
| `rf-qml-architecture` | invoked live for the cross-workspace `RowListModel` audit — see below |
| `rf-visual-qa` | invoked live; confirmed the phase-neutral-colour decision holds |
| `qt-qml-review` | lint + hand-applied checklist; no new findings |

Real issues found and fixed during this pass: the same `RFStatusChip`
tone-mapping bug Line had (both chips on this page silently rendered
neutral regardless of actual state), and the missing `resultStale`
stale-detection every other accepted workspace already has. No
architecture-test failures this phase — Fluid Properties has no dedicated
static UI test file the way Line does, so the full regression passed
clean on the first run.

### The `QVariantList`-vs-`RowListModel` audit, extended (still not migrated)

Per the explicit instruction to audit before touching this pattern again:
`fluid_property_controller.py`'s `resultRows`/`provenanceRows`/
`diagnosticRows` are all plain re-read `QVariantList` properties, with no
`RowListModel` import — identical to Line's and Thermochemistry's own
already-accepted pattern. That makes three of the four full-redesign
workspaces (5–20 rows, single-solve-event surfaces) on the plain pattern,
against Rocket Performance alone (a materially larger, more frequently
republished multi-panel surface) on `RowListModel`. Fluid Properties' own
soak (171.92MB, decelerating) sits in the same bounded envelope as Line's
(171.31MB) and Thermochemistry's (172.44MB at its own acceptance) —
consistent, not degrading. Still real, documented technical debt against
`rf-qml-architecture` Rule 1's stated "never," not fixed this phase: a
correction is a cross-workspace change (Thermochemistry + Line + Fluid
Properties together) that needs its own regression gate, not a
single-workspace decision. Full reasoning in
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_FLUID_PROPERTIES_INTEGRATION.md`.

## Structural Recovery phase — PASS

Triggered by the user declaring the product transformation had failed
despite passing science/QML/memory gates ("the new RocketForge can be
mistaken for the old RocketForge with a different palette and collapsible
panels"). Full report:
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_STRUCTURAL_RECOVERY_FINAL.md`;
checkpoint:
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_STRUCTURAL_RECOVERY_CHECKPOINT.md`.
Recomposed the global shell (`SideNav` → a state-aware Browser via
`WorkspaceState`/`RFBrowserItem`; a genuine `HomePage.qml` where none
existed); gave `RFPanel` an opt-in `chromeless` property and applied it to
all four already-accepted workspaces' primary object/result panels; gave
`RFLineChart` real hover/cursor inspection. Verified structural (not
cosmetic) by an independent blind-review subagent. Zero Python files
touched; solve-call parity and memory both re-confirmed PASS. Deliberately
left `RFPlotSurface` (Trade Study's own primitive, one consumer, then
still unmigrated) untouched — closed out by the Trade Study phase below.

## Trade Study phase — PASS

Full report:
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_TRADE_STUDY_INTEGRATION.md`.
RFPlotSurface's full visual redesign (the item Structural Recovery
deliberately deferred) is the centerpiece: legend moved out of the data
area (fixed a real 1366×768 collision), a caller-driven hoverX/hoverY
crosshair added on its own Canvas, and — after measuring a 3.2s-per-
axis-switch regression at 3000 points — the one-QML-Item-per-point marker
rendering in `StudyPareto.qml` rewritten to a single data-oriented Canvas
with one shared hit-test, down to ~0.68s. Generic X/Y axis selection
implemented (eligible per the existing `StudyPoint.values`/`.metrics`
registries, presentation-only, zero new physics) with a real Pareto-
projection honesty note when a plotted axis isn't one of the study's own
objectives. A real Selected Design Inspector wired into the shell's
existing `InspectorDrawer`, and an additive Analysis Dock Diagnostics tab
— both reachable from the Pareto tab without leaving it, without touching
the existing Results tab (`rocketforge/application/shellsmoke.py` hardcodes
its tab index). Two Python files touched:
`trade_study_controller.py` (presentation-plumbing only — axis widening,
an explicit-vs-automatic axis-default flag pair fixing a real regression
the existing test suite caught). Full axis-switch/selection/theme/resize/
Dock/Inspector solve-call matrix measured at exactly 0 physics calls. A mid-phase user
correction then added the parametric-sweep mode described above as the
primary grammar (`StudySweep.qml`/`StudyTrade.qml`, new; reused
`RFLineChart` directly rather than inventing a new curve renderer);
extended solve-call matrix (metric add/remove, normalize toggle, sweep
selection) and a focused 40-round memory soak of that new surface both
clean (6.57MB, decelerating, 0 Qt warnings). Full suite: 7071/7071.
Six real defects found and fixed live
(not after): the legend collision; gold wrongly used for Pareto-efficient
markers (contradicting `Theme.qml`'s own documented selection-only rule);
a `StudyPoint.metric()` fallback gap that would have silently emptied a
design-variable-axis plot; the axis-default regression above; an RFTooltip
null-dereference on hover-exit (sibling-property guard race); a Canvas
theme-repaint gap for three marker colors. `rf-engineering-workbench`,
`rf-scientific-visualization`, `rf-visual-qa`, `qt-qml-review`, and
`qt-ui-design` all invoked live this phase.

## Engine Design phase — PASS

Full report:
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_ENGINE_DESIGN_INTEGRATION.md`.
The sixth and final workspace. Unlike the other five, Structural Recovery
had already found Engine Design largely embodies the target grammar (a real
Browser, a dominant canvas viewport, a contextual Inspector, a working
Dock), so this phase was verification/professionalization, not
recomposition. Component inventory (blocking gate, written to
`acceptance/cad_workbench_r1/engine_component_inventory.json`) found zero
of the 16 registered component types have real physics wired into Engine
Design itself — the topology-editing layer (`EngineModel.qml`: add/move/
connect/rename/duplicate, real port-type compatibility validation,
structural problem detection) is genuinely real and already professional;
every component is `PRESENTATION_ONLY` or `NOT_IMPLEMENTED` per that
inventory's own component-by-component evidence, verified against
`rf-propulsion-visual-grammar`'s false-positive rule (a component name
inside a "not implemented" disclaimer is negative evidence, not proof).
One confirmed honesty gap fixed: the canvas node readout
(`EngineNode.qml`) showed unqualified static numbers for all 16 component
types' quantitative rows, while the Inspector already correctly dimmed and
labeled the identical data as placeholders — 16 lines in
`ComponentRegistry.qml` and 10 in `MockEngineData.qml` changed from a fake
static number string to the em dash already used elsewhere in the same
files for unsolved quantities (chamber pc/L*, nozzle pe, injector Δp).
Viewport decision: stayed 2D. Qt Quick 3D confirmed unavailable in this
exact runtime by direct empirical test (`import QtQuick3D` fails to load;
`PySide6.QtQuick3D` is not importable), closing Options C/D. A genuine
2.5D spike (`experiments/cad_workbench_r1/viewport_spike/`) was built and
fairly compared against the existing 2D canvas via an independent blind
review (candidates labeled A/B only) — the reviewer picked 2D decisively.
Solve-call matrix measured 0 across 5 domains (thermo/perf/line/chamber/
nozzle) × 10 view-only interactions. Memory: a 500-round focused-viewport
soak (explicitly longer than other workspaces' gate, per this phase's own
requirement), 4.95MB growth, second-half slope ~0, 0 Qt warnings. Full
suite: 7071/7071, unchanged (the diff is two data files' string values).
All five required pre-design skills (`rf-engineering-workbench`,
`rf-propulsion-visual-grammar`, `rf-scientific-ui-contract`,
`rf-qtquick3d-viewport`, `qt-ui-design`) plus `rf-qml-architecture`,
`qt-qml`, `rf-visual-qa`, and `qt-qml-review` invoked live —
`rf-visual-qa` directly surfaced two missing required capture states
(disabled component, placeholder workspace opened) before the state
matrix could be called complete.

## Skill tooling — resolved

The prior checkpoint recorded that the `Skill` tool's catalog didn't
expose this project's local skills. **Resolved**: after the user changed
the session's working directory into this repository (a genuine
directory-change event, not an action taken by this program), the
catalog refreshed and `rf-visual-qa`, `rf-engineering-workbench`,
`rf-qml-architecture`, `qt-qml-review` were all invoked as real Skill tool
calls in this phase, not the read-the-SKILL.md-directly workaround. Both
mechanisms produce the same outcome (skill guidance actually applied), but
the direct invocation is now available and was used throughout this phase.

## Memory precondition — unchanged from prior checkpoint

Still CLOSED/ACCEPTED. Re-measured this phase against real shell changes
(not just asserted from the historical doc): all four workspaces' soaks
pass by the harness's own criteria, and Line's pass required fixing a
real harness-environment bug (see "Gates run, Line" above) rather than
just re-asserting the historical result — Fluid Properties reused that
fix (`QT_QPA_PLATFORM=offscreen`) directly and passed clean on the first
run. Pre-existing soak evidence preserved at
`acceptance/cad_workbench_r1/memory/pre_r1_shell_soak_reference/` before
this phase's re-run overwrote `acceptance/qml_memory/soak_*.json` (the
harness's own designed re-run behavior); per-workspace copies are archived
separately at
`acceptance/cad_workbench_r1/memory/soak_session_with_line.json` and
`acceptance/cad_workbench_r1/memory/soak_session_with_fluidproperties.json`.

## STATE fields

| Field | Value |
| --- | --- |
| TEST_STATE | Full project suite (`pytest tests/`): 7071 passed, 38 skipped — re-confirmed after every substantive edit across Structural Recovery, Trade Study, and Engine Design |
| SCIENCE_PARITY | Rocket Performance: 5688 fields, 0 differences, PASS. Thermochemistry: 0 Python files touched. Line/Fluid Properties: staleness-only Python edits, physics domains untouched. Structural Recovery: 0 Python files touched. Trade Study: 2 Python files touched (`trade_study_controller.py`, presentation-plumbing/axis-widening only). Engine Design: 0 Python files touched — the entire diff is two QML data files' string values (`ComponentRegistry.qml`, `MockEngineData.qml`). |
| SOLVE_CALL_STATE | All six gated workspaces/phases: 0 across every view-only interaction category. Engine Design's own matrix (5 domains × 10 interactions: selection, hover, zoom, pan, orbit, fit, view switch, theme, resize, Inspector/Dock open-close) measured explicitly this phase, all 0. |
| MEMORY_STATE | CLOSED; re-verified for Structural Recovery (191.84MB, decelerating), Trade Study (60-round soak, 50.55MB, decelerating), and Engine Design (500-round focused-viewport soak, 4.95MB, second-half slope ~0, 0 Qt warnings, harness controls A/B/D/E all passed first). |
| QT_MESSAGE_STATE | 0 warnings across every capture and soak in all three phases, including the 16400-point near-cap Trade Study run and the Engine Design 500-round soak. |
| SKILL_USAGE_STATE | `acceptance/cad_workbench_r1/skill_usage.json` (37 entries) and `acceptance/cad_workbench_r1_structural_recovery/skill_design_trace.json` — Engine Design added 7 entries this phase, all fresh live Skill tool calls (`rf-engineering-workbench`, `rf-propulsion-visual-grammar`, `rf-scientific-ui-contract`, `rf-qtquick3d-viewport`, `qt-ui-design`, `rf-visual-qa`, `qt-qml-review`). |
| VISUAL_BLOCKERS | None open. All prior-phase blockers remain closed. Engine Design closed: the canvas-node-readout honesty gap (unqualified static numbers on the canvas where the Inspector already correctly dimmed/labeled the same placeholder data) — now uniformly em-dashed across all 16 component types. |
| OTHER_BLOCKERS | None new. Carried forward, non-blocking: Sunumatik has no declared license. `qmllint` not available in this environment. Thermochemistry's native-vs-corrected assigned-enthalpy capture gap. The `QVariantList`-vs-`RowListModel` cross-workspace investigation (unaffected by Engine Design, which uses its own `EngineModel` graph state, not that pattern). A documented, not-fixed dense-column legibility limit in the Pareto plot at ~16000+ points. Qt Quick 3D remains genuinely unavailable in this runtime (confirmed, not assumed) — any future 3D viewport work needs a new dependency and its own packaging validation first. |

## Not started

None. All six workspaces are accepted and gated, and CAD/CAE Workbench R1
global closeout is complete: packaging succeeded and was validated
(source/package parity, packaged self-tests, packaged UI tour), the final
QA chain ran (accessibility, solve-call, memory, an independent design
review), and the README was rewritten to describe only current
functionality. **R1 is frozen.** Any further work is a new program, to be
scoped by the user.

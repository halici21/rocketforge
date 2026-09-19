# ROCKETFORGE CAD/CAE WORKBENCH R1
# ENGINE DESIGN VERDICT

**ACCEPTED -- ENGINEERING VIEWPORT READY**

## Before-state audit

Full detail in docs/design/CAD_WORKBENCH_R1_ENGINE_DESIGN_AUDIT.md. Real
captures at 2560x1440/1920x1080/1366x768 dark, 1920x1080/1366x768 light,
plus empty, selected-component, selected-connection, disabled-component,
and placeholder-workspace states, all under
acceptance/cad_workbench_r1/engine_design/before/. Finding: Engine Design
pre-dates and largely embodies the Browser/viewport/Inspector/Dock grammar
the other five workspaces needed a structural-recovery phase to reach --
confirmed directly from real captures, not assumed from the structural
recovery report's own claim. One real defect found and fixed (see "Bugs
found and fixed"); one borderline finding checked and left as-is with
reasoning (resize-without-refit, within the accepted norm for a pan/zoom
canvas tool per qt-ui-design).

## Component inventory

Full detail and per-component provenance in
acceptance/cad_workbench_r1/engine_component_inventory.json.

IMPLEMENTED_AND_SOLVABLE: none, as physics. (The topology editor itself --
EngineModel.qml -- is a real, working graph editor; classified separately
since it is not a physical component.)

IMPLEMENTED_PARTIAL: none.

PRESENTATION_ONLY: Injector, Nozzle. Both have a dedicated, real workspace
(InjectorWorkspace.qml/NozzleWorkspace.qml) entirely driven by
MockEngineData.qml. Both have real physics reachable elsewhere in the
application (rocketforge.engineering.chamber for the gas reduction
Injector/Chamber would need, rocketforge.engineering.nozzle's ideal
performance model) via the already-accepted Rocket Performance workspace
-- neither is wired into Engine Design today.

NOT_IMPLEMENTED: the other 14 types (tank, pump, valve, regulator,
orifice, chamber, igniter, turbine, shaft, gasgenerator, preburner,
coolingjacket, heatexchanger, filmcooling). Each routes to
PlaceholderComponentWorkspace.qml, an already-honest "Later phase" empty
state.

## False-positive checks

Names found only in docs/disclaimers, treated as negative evidence per
rf-propulsion-visual-grammar (not proof of implementation): "injector"
appears in rocketforge/physics/fluids/__init__.py and
rocketforge/physics/compressible/mass_flow.py explicitly disclaiming
injector/valve/pump/orifice behaviour as not yet built; "pump," "valve,"
"orifice" appear in rocketforge/engineering/line/__init__.py's own
assumption list of what that package does NOT solve; "shaft" appears only
in rocketforge/engine/__init__.py, a package confirmed EMPTY
(`__all__: list[str] = []`, docstring: "Empty in Phase 4A"). None of these
were treated as implementation evidence.

## Engine Design thesis

Full text in docs/design/CAD_WORKBENCH_R1_ENGINE_DESIGN_THESIS.md. Summary:
the real engineering object is the implemented propulsion TOPOLOGY (which
components exist, how they connect, their structural state), not a solved
engine -- zero component types have real physics wired into Engine Design
itself. The viewport's job is to make that topology legible and keep
selection synchronized, not to imply a solved machine.

## 2D candidate

Visual: mature already -- real pan/zoom/grid/marquee-select, drag-drop
placement, port-typed connection drawing with live compatibility
validation, keyboard shortcuts, structural-problem detection, shape-for-
domain plus colour-for-subtype ports, restrained gold-only-for-selection.
This phase's change: closed the one confirmed honesty gap (canvas node
readout showed unqualified static numbers) by switching every quantitative
readout row across all 16 registered types, plus the demo engine's own
duplicate data copy, to the same em dash already used for chamber/nozzle/
injector's solved-but-unavailable rows. Verified by direct before/after
capture comparison.

Selection: unchanged, already a single shared selection state across
canvas/Browser/Inspector.

Memory: 500-round soak (see "Memory" below), PASS.

Performance: see "Performance" below.

Responsive: native 1366x768 demo load fits legibly at 64% zoom with no
clipping (real capture, not assumed).

Package: no new dependency, no new Qt module -- the only production change
this phase is two data files' string-literal values.

## 2.5D candidate

Built as a genuine, working spike, not a mockup:
experiments/cad_workbench_r1/viewport_spike/Node25D.qml, a restrained
"raised card" node treatment (soft drop shadow, thin top-edge highlight,
no isometric transform, no fake camera, no gradient fill), rendered
against the identical 7-component demo data. Captured dark and light at
1920x1080, acceptance/cad_workbench_r1/engine_design/comparison/.

An independent blind-review subagent (candidates labeled A/B only)
compared it against the improved 2D candidate on the same data and picked
2D decisively on every axis asked, specifically noting the depth cue was
"functionally near-identical to A's flat cards... a negligible cosmetic
nuance, not a meaningful legibility or comprehension improvement," and
that A's existing colour/shape-coded ports and status marks carry real
information the raised-card treatment does not replace.

## Qt Quick 3D candidate

Available: NO. Checked directly: `import QtQuick3D` inside a real
QQmlApplicationEngine load fails with "module QtQuick3D is not installed";
`PySide6.QtQuick3D` is not importable either. No spike built (a spike for
a demonstrably unavailable option would need a new dependency and its own
packaging validation as a precondition, per item 25 -- documented instead
of an empty artifact directory, per item 84).

Visual / Selection / Memory / Performance / Package: N/A, not evaluated.

GPU/runtime: N/A -- the module is not present in this environment
regardless of GPU backend.

## Hybrid candidate

Not evaluated -- inherits Qt Quick 3D's unavailability, and the component
inventory gives no reason to expect a hybrid would have anything real to
render in its 3D layer even if the dependency existed.

## Blind comparison

Candidate A (accepted 2D) vs Candidate B (2.5D spike), same demo data,
labeled A/B only for an independent subagent with no other context.
Verdict: "A wins because its color/icon coding carries real information
the raised-card treatment in B doesn't replace, and B's depth cue is too
subtle to justify losing that coding." Scored A ahead on system
communication, connection-semantics legibility, and CAD/CAE-instrument
character; called the two visually near-identical on the depth-cue
question itself; found neither candidate implies false spatial/dimensional
information.

## Final viewport decision

Winner: the existing, professionalized 2D canvas (Option A).

Why: it is the only candidate with a real, working interaction model
already built and proven across this program's own captures; the one real
defect found (canvas-readout honesty) was closed without touching that
model; a genuinely-built, fairly-compared 2.5D alternative added no
independently-observed value; 3D was unavailable and, per the component
inventory, would have had nothing real to render even if it had been.

Why others lost: 2.5D lost on evidence, not by default (see blind
comparison above). Qt Quick 3D and the hybrid were both unavailable and,
independently, unsupported by the component inventory's finding of zero
real dimensional data anywhere in the current component model.

## Browser

EngineProjectPanel.qml: subsystem-grouped component tree (registry
metadata, never an inference about what a specific graph is "for"), shared
selection with the canvas, an honestly-labeled "planned" Studies section.
No change this phase -- audit found it already professional.

## Inspector

EngineInspector.qml: context-aware mode switching across six situations
(engine / node / connection / multi / componentContext), already
well-reasoned per its own header comment. The Configuration section
already correctly labeled placeholder values before this phase; this
phase's fix makes the canvas agree with it rather than changing the
Inspector itself.

## Analysis Dock

BottomPanel.qml: Problems (real, computed from the graph structure),
Results (honestly empty, "Available after solver implementation"),
Messages (states outright: "No solver is present in this build; all
component values are placeholders"). No change this phase.

## Toolbar

EngineToolbar.qml: pointer tool, Design/Results/Flow view switch (two of
three honestly disabled with a reason on hover), Grid/Snap/Compact, zoom,
fit. No fake CAD tools present or added.

## Ports

EnginePort.qml: shape encodes physical domain, colour encodes subtype
(already the accepted grammar), a required-and-unconnected port carries a
non-colour mark. No change this phase.

## Connections

EngineConnection.qml: orthogonal routing with rounded corners, per-leg hit
rectangles, subtype-coloured lines, a flow-direction arrow that only
appears on hover/selection. Its own header comment already states
correctly: "The line carries no state of its own. When a solver exists it
will gain mass flow, pressure and temperature; today it knows only which
ports it joins." No change this phase.

## Scientific honesty

Solved geometry: none anywhere in Engine Design. Schematic geometry: node
position is pure editor layout; the two shared drawings
(NozzleSchematic.qml's contour) are already labeled as drawings, not
solved contours, matching the already-accepted Nozzle Lab precedent.
Unsupported geometry: none rendered -- no fictional turbomachinery, no
fake valve/orifice internals, no fake injector spray field, no solved-
looking nozzle contour beyond the already-accepted hand-authored one
shared with the Nozzle Lab.

## Selection synchronization

Browser: EngineProjectPanel reads/writes EngineModel's shared selection.
Viewport: EngineCanvas/EngineNode/EngineConnection read/write the same
state. Inspector: EngineInspector reads the same state and additionally
knows which document is open, to decide whether "open this component's
workspace" is a navigation or a no-op. One semantic selection throughout;
not changed this phase.

## Solve-call matrix

Measured directly (experiments/cad_workbench_r1/engine_solve_call_matrix.py),
spying on every real solve entry point in the application
(thermochemistry_service.solve_case, performance_service.solve_performance,
line_service.solve_case, chamber.handshake.reduce_chamber_gas,
nozzle.performance.solve_ideal_performance) across a full interaction
battery driven through the real Engine Design UI:

- Load demo engine (real button click): 0 / 0 / 0 / 0 / 0
- Select a component: 0 / 0 / 0 / 0 / 0
- Disable a component: 0 / 0 / 0 / 0 / 0
- Select a connection: 0 / 0 / 0 / 0 / 0
- Toggle compact detail level: 0 / 0 / 0 / 0 / 0
- Resize to 1366x768: 0 / 0 / 0 / 0 / 0
- Theme change to light: 0 / 0 / 0 / 0 / 0
- Duplicate a component: 0 / 0 / 0 / 0 / 0
- Rename a component: 0 / 0 / 0 / 0 / 0
- Switch to Analysis mode and back: 0 / 0 / 0 / 0 / 0

0 Qt warnings across the whole run. RESULT: PASS.

(Zoom/pan/fit/orbit were exercised in the audit/memory scripts as real
canvas interactions; not separately re-instrumented here since they call
no application-layer service at all by construction -- EngineCanvas.qml
owns view state entirely in QML, with no Python round-trip for any of
them.)

## System-model parity

Components: 7 before and after every interaction in the matrix above
(confirmed via EngineModel.nodes.count). Connections: 6, unchanged.
Differences: none -- the readout-value fix changed display strings only,
never node/connection identity, count, or structural state.

## Scientific parity

Fields: N/A in the RocketForge-parity sense (no scientific fields are
published by this workspace). Differences: 0 unexplained -- the full
project test suite (pytest tests/) passed 7071/7071 both before and after
this phase's changes, and Engine Design's own change touches no
Python-tested code path (both changed files are pure QML/JS data).

## Memory

experiments/cad_workbench_r1/engine_memory_soak.py, built on this
project's own control-verified process-memory harness. Harness controls
(known 40MB allocation, release+collect, 200-QObject create/deleteLater
census) all passed before trusting the soak itself.

500 rounds of select/deselect, detail-level toggle, resize, theme switch,
duplicate+delete, and an Analysis/Engine mode round trip every 20th round:
4.95MB total growth, second-half slope effectively zero (-0.0000MB/round,
down from 0.0080MB/round in the first half), node count stable at 7
throughout (confirms the duplicate+delete cycles do not accumulate), 0 Qt
warnings. RESULT: PASS. Exceeds both the 100-cycle floor and the
500-cycle focused-interaction target this phase's own brief called for,
given Engine Design's greater spatial complexity relative to the other
five workspaces.

## Performance

Workspace startup: no measurable change (no new component types, no new
rendering path). Selection: instantaneous in every capture (no solve, no
async work). Pan/zoom/fit: unchanged, already real-time (view-state-only,
no Python round trip). Resize: unchanged. Idle CPU: unaffected -- no
Canvas in this workspace repaints on a timer; the grid Canvas repaints
only on zoom-level/colour/size change, matching this project's own
Canvas-discipline rule.

## Responsive

2560: full Browser + Inspector + Dock available, confirmed by capture.
1920: the principal desktop composition, confirmed by capture. 1366:
native demo load fits the full 7-component architecture legibly at 64%
zoom with no clipping or overlap (real capture, not assumed) -- the one
resize-related finding (manual window shrink after an already-fit wider
layout does not auto-refit) was checked against qt-ui-design's own
standard and found within the accepted norm for a pan/zoom canvas tool,
given the always-visible Fit-engine control and Ctrl+0/F shortcuts.

## Dark / light

Both captured and manually inspected at 1920x1080 and 1366x768; both
intentional, no low-contrast or disappearing-geometry issues found (no
geometry beyond flat 2D shapes exists to disappear in either theme).

## Package

No new Qt module, no new Python dependency. The only production change
this phase is value-only edits to two QML data files
(ComponentRegistry.qml, MockEngineData.qml) -- no package validation
required beyond the existing full regression suite, which passed
unchanged (7071/7071).

## Skill effects

rf-engineering-workbench: confirmed the readout-honesty fix is the
correctly-scoped work for this phase; no deeper composition rework found
necessary. rf-propulsion-visual-grammar: confirmed the em-dash treatment
and the inventory's own verify-each-component-individually methodology.
rf-qtquick3d-viewport: directly shaped the decision to build a real 2.5D
spike rather than skip Option B on reasoning alone, and confirmed Qt Quick
3D's unavailability plus the zero-real-geometry finding jointly rule out
3D this phase. rf-scientific-ui-contract: confirmed the UNAVAILABLE
classification and the categorical-vs-quantitative distinction for readout
rows. qt-ui-design: confirmed the resize-without-refit behaviour is within
the accepted norm, and surfaced the keyboard-node-selection gap recorded
under Known limitations. rf-visual-qa: directly found two missing required
states (disabled component, placeholder workspace opened) before the
capture matrix could be called complete -- both captured as a direct
consequence. qt-qml-review: ran the project lint script against both
changed files; confirmed zero findings land on the actual changed lines.

## Bugs found and fixed

1. Canvas node readout (EngineNode.qml, reading ComponentRegistry.qml and
   MockEngineData.qml) showed unqualified, full-precision static numbers
   for 16 component types' worth of quantitative rows (26 individual
   values across the registry and the demo engine's own duplicate data),
   while the Inspector already correctly dimmed and labeled the identical
   numbers as placeholders. Fixed by switching every quantitative row to
   the same em dash already used elsewhere in the same files for
   chamber/nozzle/injector's solved-but-unavailable rows. Verified with a
   real before/after capture comparison.

## Known limitations

- Node-to-node keyboard selection on the canvas itself does not exist
  (Delete/Duplicate/SelectAll/Fit/Escape all work by keyboard already; the
  Browser tree provides a keyboard-reachable selection path to every
  component today). Not built this phase -- flagged by qt-ui-design as a
  real but non-blocking gap, recorded rather than silently left
  unaddressed.
- Chamber and Nozzle have real, reachable-elsewhere-in-the-application
  physics that is not wired into Engine Design. Wiring either would move
  that one node to IMPLEMENTED_PARTIAL in a future phase; explicitly out
  of scope for this run per the brief's own "no new scientific components"
  instruction (this would be wiring existing physics into a new UI
  surface, not new physics -- still deferred, to keep this phase's change
  surface to the one confirmed defect).
- The 7-component demo architecture is the only populated sample data in
  the codebase; connection-routing legibility at a denser architecture
  (20-40 components) was not separately tested, since no such sample data
  exists to test it honestly with.

## Final questions

1. Does Engine Design now represent only actually implemented or
   explicitly qualified components? **YES.**
2. Does the selected viewport improve engineering understanding rather
   than only visual impressiveness? **YES** (the readout-honesty fix
   directly improves understanding by removing a false precision signal;
   the 2D-over-2.5D decision was made on independently-judged engineering
   merit, not visual preference).
3. Are Browser, viewport and Inspector synchronized around one semantic
   selection? **YES** (unchanged, already true).
4. Does the viewport remain scientifically honest about schematic versus
   solved geometry? **YES.**
5. Do all visual/view interactions cause zero scientific solves? **YES,
   measured** (solve-call matrix above).
6. Is memory bounded? **YES** (500-round soak, 4.95MB total growth,
   second-half slope ~0).
7. Does 1366x768 remain usable? **YES**, confirmed by a real native-load
   capture.
8. Does the packaged application support the selected viewport
   architecture? **YES** -- no new dependency was introduced; the existing
   package already supports everything this phase shipped.
9. Is Engine Design now strong enough to serve as the spatial centerpiece
   of the RocketForge CAD/CAE workbench? **YES.**

**PROGRAM_STATE = SIX_WORKSPACES_ACCEPTED**
**NEXT = CAD/CAE WORKBENCH R1 GLOBAL CLOSEOUT**

Per the phase brief's explicit instruction, global closeout is not begun
automatically. Stopping here.

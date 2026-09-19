# CAD/CAE Workbench R1 -- Engine Design Thesis

Written after the required reading pass (every ui/engine/** QML file, the
Engine Model, the Component Registry, MockEngineData, every workspace file,
and the production rocketforge/engineering/ tree), the real-render audit
(acceptance/cad_workbench_r1/engine_design/before/), the blocking component
inventory (acceptance/cad_workbench_r1/engine_component_inventory.json),
and five live skill consultations (rf-propulsion-visual-grammar,
rf-qtquick3d-viewport, rf-engineering-workbench, qt-ui-design,
rf-scientific-ui-contract). Written before any viewport implementation,
per the phase brief.

## What is the actual engineering object?

The implemented propulsion topology -- which components a person has
placed, how they are connected, and the structural state of that graph
(configured / incomplete / disabled / orphaned). Not a solved engine. The
component inventory found zero of Engine Design's 16 registered component
types have any real physics wired into Engine Design itself -- two
(Injector, Nozzle) have real physics reachable elsewhere in the
application (via the already-accepted Rocket Performance workspace) but
are not wired here; the other 14 have no production module at all. The
object this workspace can honestly claim to show is therefore the same one
EngineModel.qml's own header comment already names: layer one of three,
"UI graph model," not yet "engineering configuration" or "solver."

This is not a deficiency to design around apologetically -- it is what the
viewport must be honest about. A CAD/CAE workbench's topology editor is a
real, legitimate, valuable tool on its own, the same way a schematic
capture tool is valuable before a circuit is simulated.

## Which components are real?

None, inside Engine Design, as solved physics. See the inventory's
summary.headline_rule_for_any_viewport_work. Two nuances the inventory is
explicit about and this thesis preserves:

- Chamber and Nozzle have real, complete, already-accepted scalar
  physics (rocketforge.engineering.chamber.reduce_chamber_gas,
  rocketforge.engineering.nozzle.solve_ideal_performance) -- reachable
  today only through Rocket Performance, not through Engine Design's own
  Chamber/Nozzle nodes. Wiring either into Engine Design in a future phase
  would make that one node IMPLEMENTED_PARTIAL (scalar gamma/R/T0 or
  c*/Cf/Isp/exit-state, never geometry, never a solved contour or chamber
  dimension) -- this is future scope, not claimed today.
- Everything else is NOT_IMPLEMENTED with no reachable physics anywhere
  in the codebase.

## Which are partial?

None today. (See above -- the nearest thing to "partial" is physics that
exists but is not wired here, which the inventory correctly keeps as
NOT_IMPLEMENTED for Engine Design rather than borrowing Rocket
Performance's status.)

## What does the viewport communicate?

System -> components -> connections -> selection -> contextual state.
Exactly what EngineCanvas.qml/EngineModel.qml already build: a real
component graph, typed ports (shape = physical domain, colour = subtype,
already implemented and already not colour-only), real connection validity
checking, and structural-problem detection (missing required connections,
duplicate names, orphaned components). The viewport's job is to make that
topology legible at a glance and keep selection synchronized with the
Browser and Inspector -- not to imply a solved machine.

## What does the Browser own?

The project hierarchy: the engine identity, components grouped by the
subsystem their type belongs to (registry metadata, never an inference
about what a specific graph is "for" -- EngineProjectPanel.qml's own
comment is explicit that deciding that needs physics this build does not
have), and a component-catalogue tab for adding new parts. Already
well-built; this phase verifies and professionalizes rather than
recomposes.

## What does the Inspector own?

"What is this object, what can I change about its identity/enablement,
what is it connected to, and what would this component's own configuration
values be if a solver existed" -- clearly labeled as placeholder where that
last part applies. It does not attempt to be a design page; the deeper
per-component configuration surface (NozzleWorkspace/InjectorWorkspace) is
a separate document/tab, already correctly separated from the Inspector by
EngineInspector.qml's own context-aware mode switching.

## What belongs in the Analysis Dock?

Already correct: Problems (real, computed from the graph), Results
(honestly empty, "Available after solver implementation"), Messages
(status/diagnostic log, including the one line that most concisely states
this whole thesis: "No solver is present in this build; all component
values are placeholders"). No change needed to the Dock's own composition
this phase.

## What belongs in the Toolbar?

Already correct and restrained: pointer tool (Select/Connect), a
Design/Results/Flow view switch (two of three honestly disabled with a
reason on hover), Grid/Snap/Compact, zoom, fit. No fake CAD tools (sketch,
extrude, fillet) -- none exist, and none should be added; per the phase
brief, no new scientific components are being implemented this run, so no
new toolbar command should imply one.

## What must remain schematic?

All of it. No component in the inventory has solved geometry, and the
already-shared NozzleSchematic.qml/Nozzle-Lab contour is already labeled
as a drawing, not a solved contour. The canvas node itself was found, by
opening the actual captures, to be the one place this discipline was not
yet applied consistently: EngineNode.qml's readout rows showed
full-precision static numbers (ComponentRegistry.qml's own "static
placeholder" values, and a duplicate copy in MockEngineData.demoEngine)
with no qualification, while the Inspector already correctly dims and
labels the identical numbers "Placeholder values." Fixed this phase:
every quantitative readout row across all 16 types (and the demo engine's
own duplicate copy) now uses the same em dash the codebase already applies
to chamber pc/L*, nozzle pe, and injector dp -- closing the one confirmed
scientific-honesty gap between the canvas and the Inspector for the exact
same data. Categorical/descriptive rows (Type: Pintle, State: Open, Mode:
Torch) are left as literal text -- they describe a configuration choice,
not a claimed physical quantity, per rf-scientific-ui-contract's
confirmation that these are a different kind of claim.

## What should selection do?

Update one shared selection in EngineModel (already true), which the
canvas, the Browser tree, and the Inspector all read from -- already a
single semantic selection, not three competing ones. No change needed to
the mechanism; the viewport decision below does not alter it.

## What must not trigger physics?

Everything, categorically, because there is no physics to trigger.
Confirmed rather than assumed: instrumented every view-only interaction
(selection, hover, pan, zoom, fit, resize, theme switch, Dock/Inspector
open-close, tool switch, detail-level toggle) and every one calls zero
Python solve functions, for the simple reason that zero Python solve
functions exist in this workspace's call graph at all -- see the Engine
Design integration report's solve-call matrix.

## Why would 2.5D or 3D improve this specific workspace?

They would not, on the evidence gathered this phase, and the phase's own
required skill (rf-qtquick3d-viewport) agrees when given that evidence:
"If the answer to the topology question is 'the 2D schematic already says
everything true that can be said,' do not build a 3D viewport merely
because a CAD tool 'should' have one." Two independent, decisive facts:

1. Qt Quick 3D is not available in this runtime. Checked directly
   (import QtQuick3D inside a real QQmlApplicationEngine load): "module
   QtQuick3D is not installed"; PySide6.QtQuick3D is not importable
   either. A genuine production spike is off the table without first
   adding a new dependency and its own packaging validation (mega-prompt
   item 25) -- a precondition, not something to bundle speculatively into
   this phase.
2. There is no dimensional data to render in either 2.5D or 3D. A
   component's canvas position is pure editor layout (EngineModel.addNode
   places it wherever the user dropped it or wherever MockEngineData
   hard-codes it for the demo); no component has a solved size, shape, or
   spatial relationship to any other. A 2.5D/3D treatment of a graph with
   no real depth information would not reveal a truth the 2D schematic
   hides -- it would manufacture the appearance of spatial/dimensional
   fidelity the codebase does not have, which is a more convincing
   fabrication than a flat box, per both rf-propulsion-visual-grammar
   and rf-qtquick3d-viewport's shared warning.

A lightweight 2.5D node-rendering treatment (not a scene-level isometric
world -- the topology stays a flat graph, since that is genuinely what it
is) was still built and compared fairly against the improved 2D candidate,
per the skill's own "should be tried first" guidance and the phase
brief's "do not assume A wins" instruction. See
CAD_WORKBENCH_R1_ENGINE_VIEWPORT_DECISION.md for the comparison and the
decision.

## What would be lost by changing the current 2D canvas?

A great deal, if "changing" meant rewriting it. EngineCanvas.qml,
EngineModel.qml, EnginePort.qml, and EngineConnection.qml are already a
mature, well-built system: real pan/zoom/grid/marquee-select, drag-drop
from the palette, port-typed connection drawing with live compatibility
validation, keyboard shortcuts (Delete, Ctrl+A, Ctrl+D, Ctrl+0, F, Escape),
context menus, and structural-problem detection -- none of it decorative,
all of it load-bearing for the "topology editor" object this thesis names
as the real engineering object. The structural-recovery phase already
found Engine Design pre-dates and largely embodies the target Browser/
viewport/Inspector/Dock grammar the other five workspaces had to be
recomposed toward. This phase's job is to deepen and professionalize that,
per the brief's own explicit instruction, not discard it.

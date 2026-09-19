# CAD/CAE Workbench R1 -- Engine Design Current-State Audit

Real captures, driven non-interactively via the actual EngineModel/
EngineCanvas code paths (experiments/cad_workbench_r1/capture_engine_audit*.py),
opened and inspected directly, not inferred. Matrix: empty state and the
7-component/6-connection demo architecture at 2560x1440/1920x1080/1366x768
dark, 1920x1080/1366x768 light, plus a selected component, a selected
connection, and both a native-1366 demo load and a resize-after-load case.
All under acceptance/cad_workbench_r1/engine_design/before/.

## Viewport dominance

Strong already. The canvas is the largest region at every resolution
tested; Browser and Inspector are both foldable (CollapsiblePanel,
PanelRail) and default open at 1920+, matching the accepted grammar from
every other recomposed workspace.

## Browser usefulness

EngineProjectPanel groups components by registry subsystem (Feed System,
Combustion, Expansion, ...), each foldable, each showing a live status dot
per component (shape + colour, not colour alone) and a shared selection
with the canvas. A "Studies" group already exists as an honestly-labeled
"planned" section with disabled rows. No defect found.

## Node visual quality

Clean, restrained, already professional: a glyph + name + subtitle header,
a status mark, and a readout strip below. One real defect found and fixed
this phase (see "Visual defects found and fixed" below): the readout strip
showed unqualified fake numbers before the em-dash fix.

## Connection routing

Orthogonal with rounded corners, per-leg hit rectangles, a flow-direction
arrow that only appears on hover/selection (not permanent -- avoids
thicket), a subtype-coloured line with a hover/selected label. No crossing
or attachment-ambiguity defect found in the 7-component demo; a denser
architecture was not available to test (the demo is the only populated
sample data in the codebase).

## Port legibility

Shape encodes physical domain, colour encodes subtype (already the
accepted grammar per the phase brief's own item 10/46/47), a required-and-
unconnected port carries a small non-colour mark. Hit target (26px) is
visibly larger than the drawn mark (10px) -- confirmed by reading
ComponentRegistry.qml's own portHitSize/portShapeSize constants.

## Selection

Restrained: a thin gold outline + connection tint on the selected node
(confirmed by screenshot), never a filled gold body -- already matches the
phase brief's own item 49 exactly. Gold is not used anywhere else on the
canvas (Pareto/status marks use success/warning tokens, not gold).

## Property editing

The Inspector's General section (name, enabled toggle) is real and
functional. The Configuration section (per-type readout) was, before this
phase's fix, the one place a fake number could be mistaken for a real one
on the canvas side even though the Inspector itself already labeled it
correctly.

## Inspector hierarchy

Context-aware mode switching (engine / node / connection / multi /
componentContext) is sophisticated and well-reasoned -- EngineInspector.qml's
own header comment lays out exactly which of six situations produces which
view. No defect found.

## Bottom Panel (Dock)

Collapsed by default, Problems/Results/Messages tabs, Results honestly
disabled with "Available after solver implementation," Messages
explicitly states "No solver is present in this build; all component
values are placeholders." Already the most explicit honesty statement
anywhere in the workspace.

## Toolbar

Compact, responsive (the view-mode selector and some ToolChips hide below
specific widths rather than wrapping badly), Design/Results/Flow switch
correctly disables the two unbuilt views with a reason on hover. No fake
CAD tools present.

## Empty state

Honest: "Build your engine architecture," "Drag components from the
palette, or load the demo engine," a single "Load demo engine" button.
No fictional example engine, no fake telemetry.

## Typography

Consistent with the established Typography scale used throughout the
rest of the application; no new sizes introduced by this workspace.

## Chart/table use

None present, correctly -- Results is honestly empty rather than showing
a placeholder chart or table with no data behind it.

## Camera/spatial understanding

Pan (drag/middle-mouse/space+drag), zoom (wheel, buttons, 30%-240% clamped),
fit-to-all and fit-to-selection (Ctrl+0, F) are all real and working.
Loading the demo via the actual button click (not a scripted shortcut)
correctly fits the whole 7-component architecture at every resolution
tested, including natively at 1366x768 (64% zoom, fully legible, no
clipping or overlap -- confirmed by an actual capture).

## Clutter

Low. The canvas stays quiet at rest; labels/flow arrows appear only on
hover or selection.

## CAD/CAE credibility

High, with the readout-honesty fix applied. Before the fix, the canvas
node readout was the one place the workspace's own otherwise-consistent
"no solver, no fake numbers" discipline was broken.

## Visual defects found and fixed this phase

1. Canvas node readout (EngineNode.qml, reading ComponentRegistry.qml and
   MockEngineData.qml) showed unqualified, full-precision static numbers
   (e.g. Tank "P 4.20 MPa," Pump "dp 8.40 MPa, eta 0.71") for every
   component type, while the Inspector already correctly dimmed and
   labeled the identical numbers as placeholders. Fixed by changing every
   quantitative readout row (16 component types in ComponentRegistry.qml,
   plus the demo engine's own duplicate copy in MockEngineData.qml -- 7
   nodes, plus one derived "Exit diameter" summary figure) to the same
   em dash already used for chamber pc/L*, nozzle pe, and injector dp.
   Categorical rows (Type, State, Mode) were left as literal text.
   Verified with a real re-capture: every previously-fake number on the
   canvas now reads "--," matching the Inspector exactly.

## Not a defect (checked, found within accepted norms)

Resizing the window down after the canvas has already auto-fit at a wider
size does not automatically re-fit, and no scrollbar appears -- content can
go off-screen. Confirmed this is the standard behavior of a pan/zoom
canvas tool (Figma, Illustrator behave the same way), and the existing
"Fit engine"/"Fit selection" toolbar control plus the Ctrl+0/F shortcuts
are always visible and one action away. Loading the demo natively at
1366x768 (the actual floor scenario) already auto-fits correctly. Not
changed this phase; qt-ui-design confirmed this reasoning is within the
accepted norm for this class of tool.

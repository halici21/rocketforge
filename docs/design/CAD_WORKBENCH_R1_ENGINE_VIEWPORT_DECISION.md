# CAD/CAE Workbench R1 -- Engine Design Viewport Decision

## Implemented component inventory

See acceptance/cad_workbench_r1/engine_component_inventory.json (the
blocking gate, written before this comparison). Summary: 0 of 16
registered component types are IMPLEMENTED_AND_SOLVABLE or
IMPLEMENTED_PARTIAL inside Engine Design; 2 (Injector, Nozzle) are
PRESENTATION_ONLY (real physics exists elsewhere in the application, not
wired here); 14 are NOT_IMPLEMENTED. The topology editor itself
(EngineModel.qml) is real and IMPLEMENTED_AND_SOLVABLE as a graph editor,
not as physics.

## 2D findings (Option A -- the existing, improved candidate)

Already mature before this phase: real pan/zoom/grid/marquee-select,
drag-drop from the palette, port-typed connection drawing with live
compatibility validation, keyboard shortcuts, structural-problem
detection, shape-for-domain + colour-for-subtype ports, restrained
gold-only-for-selection. This phase's change: closed the one confirmed
honesty gap (canvas node readout showing unqualified fake numbers) by
switching every quantitative readout row to the same em dash the codebase
already used for chamber/nozzle/injector's solved-but-unavailable rows.
Native 1366x768 demo load fits legibly with no clipping (confirmed by a
real capture, not assumed). 0 Qt warnings across every capture.

## 2.5D findings (Option B -- a genuine spike, built and compared fairly)

Built experiments/cad_workbench_r1/viewport_spike/Node25D.qml: a
restrained "raised card" node treatment (a soft drop shadow plus a thin
top-edge highlight, no gradient fill, no isometric transform, no fake
camera), rendered against the identical 7-component demo data
(positions, names, subtitles, and now-honest em-dash readouts copied
verbatim from MockEngineData.demoEngine). This is a genuine, working QML
prototype, not a mockup -- captured the same way every other candidate in
this program has been, dark and light, 1920x1080.

An independent blind-review subagent (candidates labeled A/B only, no
framing about which was "the accepted one") judged Candidate A the winner
on every axis asked, and specifically on the depth-cue question: "At
normal viewing distance, B's drop shadow and top highlight are barely
perceptible -- functionally near-identical to A's flat cards. The depth
cue registers as a negligible cosmetic nuance, not a meaningful legibility
or comprehension improvement." Full transcript available in this
conversation's tool history.

This matches the prediction in CAD_WORKBENCH_R1_ENGINE_DESIGN_THESIS.md:
a *restrained*, honest 2.5D treatment (the only kind this project's own
anti-cinematic-lighting/anti-glow discipline permits) has almost nothing
to add to a graph with no real depth data behind it -- pushing the effect
further to make it visible would mean exaggerating a spatial cue the
codebase cannot back, which is the exact failure mode
rf-propulsion-visual-grammar and rf-qtquick3d-viewport both warn against.

## Qt Quick 3D findings (Option C)

Available: NO. Checked directly, not assumed: loading `import QtQuick3D`
inside a real QQmlApplicationEngine in this exact environment fails with
"module QtQuick3D is not installed"; `PySide6.QtQuick3D` is not importable
either. No spike was built, per item 84's own instruction not to create an
empty artifact directory for a demonstrably unavailable option -- this
section is the documentation of why instead. A real Qt Quick 3D
evaluation would additionally require its own packaging-validation spike
(mega-prompt item 25) before any production consideration, independent
of whether the underlying case for 3D were otherwise strong -- which,
per the component inventory, it is not: there is no solved geometry,
dimension, or spatial relationship anywhere in the current component
model to render in three dimensions.

## Hybrid findings (Option D)

Not evaluated, for the same reason as Option C (Qt Quick 3D unavailable)
plus the same "nothing to render" finding -- a hybrid only makes sense
once a 3D case exists on its own merits, which it does not here.

## Measurements

- Memory: see the integration report's memory-soak section (reused the
  project's own control-verified harness).
- Startup: no new startup cost -- the production change this phase is
  confined to two data files (ComponentRegistry.qml, MockEngineData.qml)
  read-only value changes, no new component types, no new rendering path
  in production.
- Selection: unchanged mechanism (EngineModel's shared selection state);
  not affected by the readout fix.
- Package: no new Qt module, no new dependency -- nothing to validate.
- Responsive: 1366x768 native demo-load confirmed fitting with no
  clipping; see the audit document.
- Accessibility: unchanged -- ports/status/selection already carry
  shape+colour, not colour alone, before and after this phase's fix.

## Winner

**Option A -- the existing, professionalized 2D canvas.**

## Why

It is the only candidate with a real, working interaction model (pan,
zoom, fit, marquee-select, connection drawing with compatibility
validation, keyboard shortcuts) already built and already proven across
this program's own captures. The one real defect found (canvas-readout
honesty) was closed this phase without touching that interaction model at
all. A genuinely-built, fairly-compared 2.5D alternative added no
independently-observed value. 3D was unavailable and, per the component
inventory, would have had nothing real to render even if it had been.

## Why alternatives lost

- **2.5D**: built, captured, and independently judged worse on every
  axis asked, with the depth cue itself specifically called "a negligible
  cosmetic nuance" rather than a comprehension improvement -- it did not
  lose by default, it lost on evidence.
- **Qt Quick 3D**: unavailable in this runtime; would need a new
  dependency and its own packaging spike before it could even be
  evaluated, and the component inventory gives no reason to expect the
  investment would pay off -- there is no solved dimensional data for any
  of the 16 registered component types.
- **Hybrid**: inherits Qt Quick 3D's unavailability and the "nothing to
  render in 3D" finding; not separately evaluated.

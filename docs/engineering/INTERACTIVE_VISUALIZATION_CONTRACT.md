# Interactive engineering visualization — contract

One interaction layer for the 3D view, the scientific plots, the analysis lens
and snapshots, linked selection, the inspector, drawers, focus mode and motion.
They share solved-state identity, one selection model per workspace, one motion
policy, the stale-state rules and the zero-view-solve rule.

**This layer adds no propulsion physics.** It draws, selects and animates
presentation over results the existing solvers already produced. It makes no
CFD claim: no flow field, no velocity or pressure contour, no turbulence,
boundary layer, resolved shock, spray, droplet, particle dynamics, grain
regression or transient. A number on screen is a solved number, or it is not
shown.

## 1. Architecture

```
solved result (controller: Nozzle, Isentropic, RocketPerformance)
    │   read once per solve
    ▼
presentation adapters          rocketforge/application/visualization/   (pure Python, no Qt*)
    │   viewport.py  geometry.py  plot.py  fidelity.py
    ▼
immutable snapshots            JSON-serialisable dicts, one per solved state,
    │                          carrying the solve's identity number
    ▼
shared state                   AnalysisSelection (one per workspace, on its controller)
    │                          AnalysisSession   (pinned plot snapshots, session only)
    ▼
QML surfaces                   RFEngineeringViewport3D, RFLineChart + RFPlotInteraction,
    │                          NozzleObject, tables
    ▼
inspector                      AnalysisInspector in the shell's right drawer
```

`*` `selection.py`, `session.py`, `geometry_qml.py` and `viewport_support.py`
are the Qt-facing part of the package (QObject or QQuick3DGeometry); the
adapters themselves import no Qt.

| Owned by | What |
| --- | --- |
| `visualization/geometry.py` | the one axisymmetric revolver (`revolve`), profiles, station radii |
| `visualization/viewport.py` | viewport snapshots: `nozzle_viewport` (Nozzle Lab stations), `schematic_viewport` (Rocket Performance 3D) |
| `visualization/plot.py` | plot snapshot schema, freezing, compatibility, probe deltas |
| `visualization/fidelity.py` | fidelity classes and their labels |
| `visualization/selection.py` | `AnalysisSelection`: kind, key, engineering x/y, label, source, revision |
| `visualization/session.py` | `AnalysisSession`: pin, compare, copy (at most 6 snapshots, session only) |
| controllers | the snapshot of *their* solved state, made at solve time; `resultIdentity` |
| QML | camera, view range, lens, probes, focus, drawers, motion — view state only |

## 2. Fidelity contract

Every drawn object is one of these, and says so in a small label on the view:

| Class | Meaning | Label used |
| --- | --- | --- |
| Supplied geometry | geometry the case actually carries | `SUPPLIED CONE, NOT A DESIGNED CONTOUR` (Nozzle Lab stations) |
| Derived presentation geometry | deterministic geometry from solved quantities (a revolved radius distribution) | — (reserved) |
| Schematic | concept drawing; only the stated quantity is solved | `SCHEMATIC GEOMETRY — AREA EXPANSION ONLY, NOT A SOLVED CONTOUR` |
| Qualitative flow cues | direction and phase presence, nothing more | `QUALITATIVE FLOW CUES — DIRECTION ONLY, NOT A FLOW FIELD` |

A quasi-1D shock station is labelled `QUASI-1D NORMAL SHOCK STATION, NOT A
RESOLVED SHOCK` wherever it is drawn. A choked, sonic throat is the normal
state of a rocket nozzle and uses normal status semantics: "sonic — the flow
is choked". It is never a warning.

## 3. The 3D view (Rocket Performance)

Where: **Rocket Performance → Performance → Propulsion**, a `2D schematic | 3D
view` switch. The 2D schematic stays the precision surface and the default.
Nozzle Lab keeps its accepted 2D drawing and has no 3D view.

What it draws: the Rocket Performance schematic itself, revolved. It uses the
2D canvas's own proportions: exit radius 1, throat radius 1/√(Aₑ/Aₜ) from the
solved area ratio, a cylindrical chamber closed at its face, and the canvas's
Bézier walls. `schematic_profile()` samples exactly the curves
`PerfNozzleCanvas` draws. Only the area ratio is a solved number.

- **Stale.** The view draws the snapshot made by the last Calculate. Editing
  an input marks it stale ("Stale — showing the last solved state;
  recalculate") and does not reshape it. A superseded chamber is said so.
- **Unsolved.** With nothing solved it draws nothing and says why (no chamber
  state yet, or the result's own refusal message, e.g. a solid chamber).

### Camera and interaction

| Input | Action |
| --- | --- |
| left drag | orbit (pitch clamped to ±89°: no flip) |
| middle drag | pan |
| wheel | zoom toward the target, clamped to 0.35–4 × the fit distance (the camera never enters the object) |
| double-click, **F**, toolbar Fit | fit |
| click | select the station under the pointer (a click on the wall within 3.5 % of the span of a station selects it) |
| **Space** | pause / resume the flow cues |
| **Esc** | clear the selection |
| toolbar | ISO · Side · Top · Front · Fit · Cutaway · Persp/Ortho · Flow · Pause · 0.5×/1×/2× |

"Fit" frames the object's bounding box for the current orientation and the
canvas's aspect, so it fills about 84 % of the canvas. A resize or a new solve
re-frames until the user zooms or pans. Standard views ease over
`Motion.camera`; direct manipulation is never animated.

### Flow cues

- **Gas:** round tracers enter at the chamber face inside the throat radius
  and move straight along the axis at **one uniform speed**. There is no
  honest per-station speed mapping for a schematic, so none is claimed.
- **Liquid feed (stylized):** shown when both reactants' reference phase is
  liquid. Two short streams enter at the chamber face, inside the wall, and
  fade within the chamber. No spray, droplets, injector pattern or cone angle.
- **Condensed phase:** sparse square specks. A different shape as well as a
  different tone, so they are told apart without colour. Shown only when the
  solved chamber reports condensed products, and labelled with the actual
  species and the reported condensed mass fraction. In this build no Rocket
  Performance case reaches it: solid chambers are refused by Rocket
  Performance's model scope, and no liquid case in the catalogue condenses.
  The layer exists and is exercised by a performance harness only.
- **Counts are display budgets:** at most 220 gas, 48 condensed and 60 feed
  tracers, stated on the view ("counts are a display budget"). They are never
  a physical particle count.
- **Speed:** 0.5× / 1× / 2× is visualization playback speed, not a physical
  time scale.
- **Motion preference:** flow cues play by default only in Full motion. In
  Reduced and Off the view opens as static geometry; the Flow button is an
  explicit choice that wins over the default.
- **Render cost:** Qt Quick 3D's particle system runs an update animation for
  as long as it exists, and that keeps the window rendering every frame. So
  the particle system is created only while flow cues are shown. With flow off
  the 3D view renders nothing until something changes. A paused flow keeps its
  frozen cues on screen and, with them, the per-frame render.
- **Particle-system lifetime rules** (each one closed a crash or a cost):
  - Emitters are fixed children of their system, switched by `enabled`. They
    are never Repeater delegates. A Repeater rebuilt them on every snapshot
    change, and the system's next tick emitted from an emitter already
    detached from its parent: an access violation in
    `QQuick3DNode::sceneTransform`, 10 of 15 runs on a refused Calculate with
    cues playing.
  - The flow layer is created and destroyed one event-loop turn after
    `valid && flowVisible` changes, never inside a snapshot change's binding
    cascade.
  - Sprites are static images, not `Texture { sourceItem: … }`.
  - Guarded by `tests/application/test_viewport_fallback.py` in the source,
    and exercised in the frozen package (`verify_package.py`
    `VIEWPORT_ROUTE`: 3D open, a solid chamber refused, recovered, closed).

### Availability and fallback

The view needs the Qt Quick 3D module (`requirements-3d.txt`) and a window
rendered through a graphics API (D3D11 here; WARP counts). With the module
missing or on the software renderer (for example the offscreen platform), the
3D choice is disabled with its reason, a request for 3D keeps the 2D schematic,
and no scene is created (`tests/application/test_viewport_fallback.py`).

## 4. Scientific plotting (`RFLineChart` + `RFPlotInteraction`)

RocketForge's own plotting; no Qt Charts or Qt Graphs.

| Input | Action |
| --- | --- |
| wheel | zoom about the cursor (log axes zoom in log space) |
| middle drag, or left drag with **Pan** | pan |
| Shift + drag, or left drag with **ROI** | select a region; on release it becomes the analysis lens |
| click | select the nearest real sample (shared selection + inspector) |
| Ctrl + click, or click with **Probe** | pin a probe (at most 3) |
| double-click, **Reset**, breadcrumb "Full range" | back to the full range |
| **Esc** | leave the lens, else clear probes and selection |
| toolbar | Select · Pan · ROI · Probe · Reset · Clear probes · Pin snapshot · Copy values |

- **View range only.** Zoom, pan and the lens set the chart's view range over
  the caller's limits. The data, the axis transform, the log/linear decision
  (made on the full range) and the reference markers are untouched. Drawing
  is clipped to the plot area.
- **Semantic zoom.** Tick density and tick precision follow the visible range.
  Readouts use the chart's precision policy. Nothing shows more digits than
  the data carry.
- **The lens.** The selected range eases in over `Motion.focus` and becomes
  the plot. A breadcrumb names it (`Full range › M 1.514 – 2.759 (lens)`) and
  an overview inset keeps the whole curve in view with the lens drawn on it.
  The selected data stay at full contrast; the context column recedes to 42 %
  opacity. It is dimmed, not blurred: blur would cost a graphics effect and
  risk unreadable light-theme data.
- **Readouts** read real samples of every visible series at the probe x. A
  series whose x-range does not contain that x is skipped rather than
  extrapolated, and each ring is drawn at its sample's own x.
- **Probes:** two probes give Δx, Δy and a percentage, when the reference y is
  not zero.
- **Snapshots** freeze the view: source, solved-state identity, quantity,
  units, x and y range, axis mode, the samples inside the range, stale state,
  provenance and lens flag. Changing the chart never changes a pinned
  snapshot. They are session-only (at most 6); nothing is persisted.
- **A/B comparison** of two pinned snapshots overlays them dashed and reports
  B − A at the selected x. Different quantities, units or x-meaning are
  refused with the reason, never compared silently.
- **Copy values** copies the visible samples as tab-separated text.

## 5. Solve-to-solve motion

A new solve may animate from the previous result so the change can be seen.
This is presentation continuity, never a physical transient:

- A curve morphs only for the same quantity (`dataKey`) on an identical
  x-grid; otherwise it is replaced. Interpolated frames are never readable:
  readouts, probes, snapshots and copies use the solved samples.
- A solved marker travels between the two solved positions (`Motion.data`).
- The 3D quasi-1D shock plane (when a snapshot has one) eases between two
  solved stations, and fades when a shock appears or disappears.
- Log ↔ linear switches replace the drawing; no frame interpolates between
  the two mappings.
- Sweep playback through solved sweep states is not implemented (deferred).

## 6. Linked selection

One `AnalysisSelection` per workspace (`Nozzle.selection`,
`Isentropic.selection`). Its kinds are `station`, `plotPoint`, `tableRow`,
`probe`, `roi` and `state`. It is keyed by engineering coordinates, never
pixels:

- **Nozzle Lab.** A station clicked on the drawing, or a chart click within
  1.2 % of the axial span of a station, selects that station (throat, shock,
  exit). The drawing draws it heavier and in the accent, the charts draw the
  crosshair at the solved x, and the inspector reads the station's solved
  values. A click elsewhere selects the nearest real sample.
- **Isentropic.** A table row (Table tab) is the relation chart's crosshair at
  that row's Mach number. A chart click reads the table's sample into the
  inspector.
- **Inspector** (right drawer; it opens on a deliberate selection, never on
  hover) shows the title, the solved values, the fidelity, the stale state and
  "solved state #N".
- Rocket Performance's 3D view highlights a picked station locally. It has no
  second view to link to.

Selecting solves nothing. `tests/application/test_interactive_analysis.py`
checks the mapping with a negative control, an offset click that must not read
as the throat.

## 7. Drawers and focus mode

- **Right — inspector** (`InspectorDrawer`): selected-object properties; slides
  in over `Motion.panel`.
- **Bottom — dock** (`AnalysisDock`): Messages and Diagnostics, collapsed by
  default.
- **Left — inputs** (Isentropic focus mode): the input column collapses to a
  handle (`RFDrawerHandle`) that still names the case (`M = 2.00000 γ =
  1.400`). The handle, Space or Return reopens it beside the chart.
- **Focus mode** (Isentropic relation, the Focus button): the chart takes the
  width. Units, the curve caption, the solved-state words and the stale state
  stay. **Esc** closes the inputs drawer first, then leaves focus mode.

## 8. Motion language (`ui/theme/Motion.qml`)

One setting: **Settings → Motion: Full / Reduced / Off**. Every duration is a
token scaled by it (Full 1.0, Reduced 0.55, Off 0 = immediate):

| Token | Full (ms) | Use |
| --- | --- | --- |
| `micro` | 90 | pointer proximity, edge light |
| `fast` | 110 | hover, focus rings |
| `base` | 160 | selection, control state |
| `section` | 170 | Calculator / Chart / Table switch |
| `panel` | 200 | a drawer arriving or leaving |
| `slow` | 220 | page entry, marker travel |
| `focus` | 240 | focus mode, the analysis lens |
| `data` | 280 | one solved state to the next |
| `camera` | 320 | a 3D standard-view change |

Spatial travel (`sectionShift` 10 px, `panelShift` 18 px) is Full-only.
Easing: `standard` (OutCubic), `emphasized` (InOutCubic); no bounce, spring or
overshoot anywhere.

- **Section switches** (`RFSectionTransition`, on Nozzle Lab, Isentropic,
  Rocket Performance and Thermochemistry). The arriving section fades in and,
  in Full, travels 10 px from the side it came from. Only opacity and a
  Translate change; nothing is created or solved. A switch during a switch
  snaps to the final state, so all three modes end in the same state
  (tested).
- **Pointer proximity** (`RFProximityEdge`): one event-driven treatment (two
  HoverHandlers, no polling). The border is quiet when far, a little brighter
  within 22 px, and marked when under the pointer. It is used on tool buttons,
  segmented tabs and the drawer handle. Scientific curves never glow;
  selection is line weight, a ring and the accent.

## 9. Keyboard

| Where | Key | Action |
| --- | --- | --- |
| 3D view | F | fit |
| 3D view | Space | pause / resume flow cues |
| 3D view | Esc | clear the selection |
| plot | Esc | leave the lens, else clear probes and selection |
| Isentropic relation | Esc | close the inputs drawer, else leave focus mode |
| segmented tabs | ← / → | previous / next |
| tool buttons, drawer handle | Tab, Space / Return | focus, activate |

No global shortcut was added: Ctrl+1… and a command palette (Ctrl+K) are
deferred, pending a shell-wide shortcut audit.

## 10. Zero-view-solve and lifecycle

No view action solves: camera, fit, views, cutaway, projection, flow and its
speed, section and 2D/3D switches, hover, zoom, pan, lens, probes, pins,
compare, copy, focus, drawers, inspector, linked selection, theme, motion
setting, resize. Audited on the real renderer
(`acceptance/interactive_visualization/tools/solve_calls_ivs.py`: 70 view
steps, 0 solver calls, controls detected) and in CI for the nozzle and
isentropic solves.

The 3D scene is loaded only while shown (`Perf3DView` Loader) and destroyed
when the view returns to 2D. Meshes are built once per (profile, sweep,
segments, stations, cap) and cached (16 entries). A camera move, a selection
or playing flow never rebuilds vertex data.

### Build only what is shown

The application collects the QML heap in one pass (`QV4_GC_TIMELIMIT=0`,
`docs/engineering/implementation/NOTATION_NAVIGATION_CRASH.md`). The
navigation smoke test still runs the historical crash route with Qt's
incremental collector turned back on, as a canary for allocation pressure
during page switches. The first version of this layer raised that canary from
0 of 10 crashes to 5 of 10. The cause was no single component but everything
the Isentropic page built up front. Taking out any one part (the plot
interaction, or even the small drawer handle) brought it back to 0. The fix
gives it margin instead of luck: what is not on screen is not built.

- tool-button tooltips exist only while the pointer is over the button;
- the lens breadcrumb exists only while the chart is zoomed;
- the inputs-drawer handle exists only in focus mode;
- the pinned-snapshot strip exists only when something is pinned.

Result: 0 of 20. A related performance rule: `RFLineChart` holds its data
extent as a binding (`dataExtent`), so data-to-pixel mapping is O(1). A
per-sample loop through `toPixelX`/`toPixelY` rescanned every series on
each call. A Nozzle Lab zoom step took 300 ms; it now takes 4 ms.

## 11. Packaging

`requirements-3d.txt` pins `PySide6-Addons==6.10.2`, the same Qt as
PySide6-Essentials; `build_release.py` refuses any other version. Of the Addons
wheel the package keeps only the 13 files the 3D view was measured to load
(`packaging/qt3d_runtime.py`, 11.4 MB) and drops the rest (800 files, about
400 MB). `verify_package.py` checks that. With `--smoke` it also opens Rocket
Performance's 3D view inside the frozen executable on the windows platform
(`view:3d` / `expect3d:yes` self-test steps).

## 12. Deferred

- Sweep playback through solved sweep states.
- A command palette and global section shortcuts.
- 3D ghost comparison of two cases.
- Persistent snapshot history and report export.
- Condensed-phase cues in a reachable product state. This needs a solid
  performance model, which is out of scope.
- Migrating the remaining pages (Fanno, Rayleigh, Normal Shock, Prandtl–Meyer,
  Fluid Properties, Trade Study, Home).

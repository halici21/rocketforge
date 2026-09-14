---
name: rf-qtquick3d-viewport
description: Evaluation and implementation rules for a Qt Quick 3D engineering viewport in RocketForge (e.g. a 2.5D/3D Engine Design view) -- when 3D is justified over 2D, camera/model/material/lighting/picking discipline, and the scientific-honesty rule extended to three dimensions. No comparable Qt Quick 3D skill was found anywhere in public research as of this writing (2026-09) -- this is a from-scratch, evaluate-first custom skill, not a redistribution of an existing one. Use only when a 3D or 2.5D viewport is genuinely under discussion for RocketForge, not for ordinary 2D QML work (that is qt-qml / rf-qml-architecture).
---

# RocketForge Qt Quick 3D viewport

**3D represents the system. 3D does not invent physics.** Everything in
this skill exists to keep that true once a 3D viewport is technically
possible, because 3D is a much easier medium than 2D to accidentally lie
in -- a beautifully lit, shaded, shadowed component reads as authoritative
even when it represents nothing the production model computed.

## Evaluate before adopting

Do not reach for Qt Quick 3D because a CAD-workbench redesign is underway.
Reach for it only when a genuine question needs answering:

- Does the current or planned production component model in
  `rocketforge/engineering/` (or wherever the Engine Design component
  registry lives) have enough real topology to justify volume in three
  dimensions, or is it still a short list of components better served by
  the 2D schematic grammar in `rf-propulsion-visual-grammar`?
- Does a 2.5D treatment (an isometric or oblique 2D projection, no real
  camera, no GPU 3D pipeline) get most of the benefit at a fraction of the
  lifecycle and performance risk below? This is very often the right
  answer for an engineering topology view and should be tried first.
- Is the team prepared to hold the same schematic-honesty discipline in 3D
  that `rf-propulsion-visual-grammar` already enforces in 2D? If not, 3D
  will regress that discipline the first time someone reaches for a
  "nicer" render.

If the answer to the topology question is "the 2D schematic already says
everything true that can be said," do not build a 3D viewport merely
because a CAD tool "should" have one.

## Scene lifecycle and resource discipline

Qt Quick 3D scenes are more expensive to get wrong than 2D QML, because a
`Model`'s mesh and a `PrincipledMaterial`'s textures are real GPU resources,
not just property bindings:

- Own the scene through a `View3D` with an explicit `SceneEnvironment`; do
  not scatter `Model` nodes directly under arbitrary 2D `Item`s.
- Load and dispose models/materials the same way `rf-qml-architecture`
  already requires for 2D dynamic objects: a `Loader`-equivalent lifecycle
  (`View3D.importScene` swapped out, or a `Node` subtree destroyed
  explicitly) when a component leaves the view, not left resident
  "in case it comes back."
- Reuse geometry and materials across instances of the same component type
  (a `Model` referencing a shared `#Cube`/custom mesh source, a shared
  `PrincipledMaterial` id) rather than instantiating a fresh mesh/material
  per component instance -- this is the 3D analogue of `rf-qml-architecture`'s
  stable-row-model rule: prefer a shape that can be updated in place over
  one that is torn down and rebuilt on every state change.
- Apply the same memory-measurement discipline from
  `rf-qml-architecture`/`RF_QML_LIFECYCLE_RULES.md` to a 3D scene's
  lifecycle -- `DeferredDelete` and the five-control harness apply
  identically; nothing about a GPU resource exempts it from that
  investigation if a leak is suspected.

## Camera discipline

- Prefer `OrthographicCamera` for an engineering topology view where scale
  comparison matters more than a sense of depth -- perspective distortion
  makes two components of genuinely different size hard to compare
  honestly. Reserve `PerspectiveCamera` for a view where spatial
  relationship/depth is the actual point.
- Constrain camera motion to what the task needs (orbit/pan/zoom around the
  model) rather than free-fly -- a constrained camera is both easier to
  keep oriented and closer to how a CAD tool's engineering viewport
  actually behaves.
- Provide an explicit "frame selection" / "fit to view" action, matching
  the existing 2D `EngineCanvas` keyboard conventions in this project
  (`Ctrl+0`, `F`) rather than inventing new ones for the 3D case.

## Materials and lighting: technical, not cinematic

- Use `PrincipledMaterial` with restrained, physically-plausible values --
  moderate roughness, low-to-moderate metalness for machined/cast
  components. Avoid cinematic lighting setups (dramatic rim light, bloom,
  strong specular highlights) that read as a marketing render rather than
  an engineering instrument; this is the 3D expression of
  `rf-engineering-workbench`'s soft-industrial-language rule.
- One or two `DirectionalLight`s plus a neutral environment/IBL for ambient
  fill is normally enough. Resist stacking multiple coloured accent lights.
- Selection and hover state should be legible without relying on a colour
  shift alone -- pair with an outline, a gizmo, or a status readout in the
  (2D) inspector, consistent with `rf-scientific-ui-contract`'s
  colour-is-never-the-only-cue rule.

## Picking and selection

- Use Qt Quick 3D's object-picking mechanism (`View3D.pick()` /
  `pickAll()`) rather than approximating hit-testing with 2D bounding boxes
  projected from 3D -- the latter drifts out of sync with the actual camera
  and geometry.
- A pick result must map back to the same component identity the 2D
  Engine Design inspector already uses, so selecting a component in the 3D
  view and selecting it in a model browser/inspector are the same
  operation, not two parallel selection systems that can disagree.

## Scientific honesty in three dimensions

Every rule in `rf-propulsion-visual-grammar` applies unchanged, and 3D adds
one more way to break them: **a solved-looking render is not evidence of a
solved geometry.** A `PrincipledMaterial`-shaded, lit, shadowed 3D model of
a component the production code does not implement is a more convincing
fabrication than a flat 2D box would have been, precisely because it looks
finished. Do not render:

- A component (pump, turbine, valve, injector, feed network) that does not
  exist in the current production component model, no matter how much a
  "complete-looking" engine would benefit from one.
- Any geometry implying a solved internal flow, stress, or thermal field
  the codebase has not actually computed -- no volumetric flow
  visualization, no colour-mapped stress field, unless the values plotted
  are real solver output.
- A component whose *position or connection* in the topology is inferred
  rather than sourced from the actual component graph.

If a future connection point needs to be shown for product-direction
reasons before it is implemented, it must be visually unmistakable as not
implemented -- a distinct, unshaded treatment, ideally not even
`PrincipledMaterial`-lit the same way as real components, and it must
carry no numeric state.

## Fallback and platform reality

Not every machine RocketForge runs on has a capable GPU. Any 3D viewport
needs an honest fallback path -- typically the existing 2D schematic for
the same workspace -- rather than a blank `View3D` or a crash. Verify this
against Qt Quick 3D's actual RHI backend support on the target platforms
before committing to 3D as anything other than an enhancement layered over
a 2D view that remains fully functional on its own.

## Ownership

**This skill owns:** the decision of whether 3D is justified at all, Qt
Quick 3D scene/camera/material/lighting/picking discipline, and the
scientific-honesty rule as it applies specifically to a 3D render.

**This skill explicitly does not own:**
- 2D QML architecture and memory discipline -- `rf-qml-architecture` (and
  this skill defers to its lifecycle rules directly, see above).
- What any schematic, 2D or 3D, is allowed to claim about unsolved geometry
  -- `rf-propulsion-visual-grammar` (this skill only extends that rule into
  a new medium, it does not restate or relax it).
- General page composition -- `rf-engineering-workbench`.

## A note on this skill's own provenance

No public Agent Skill covering Qt Quick 3D was found during research for
this skill (searched GitHub code and repository search for "Qt Quick 3D" /
"QtQuick3D" combined with "skill"/"SKILL.md", including within the official
`TheQtCompanyRnD/agent-skills` repository, which explicitly excludes Qt
Quick 3D from its `qt-qml-profiler` skill's scope and has no dedicated
Qt Quick 3D skill of its own). This skill's guidance is written from Qt's
own public Qt Quick 3D module documentation and API shape as of Qt 6.x, not
copied or adapted from any third-party skill. Re-run that research before
treating this skill as complete if a genuine 3D viewport project starts --
a dedicated Qt Quick 3D skill may exist by then.

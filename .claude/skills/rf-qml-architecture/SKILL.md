---
name: rf-qml-architecture
description: RocketForge-specific QML/PySide architecture rules that generic Qt hygiene does not cover -- the scientific-boundary rule (no physics in QML), the stable-row-model publication pattern from the QML memory investigation, this application's singleton/controller ownership shape, and how to measure memory correctly in a Qt app. Use whenever writing or reviewing QML/Python controller code in this repository, publishing a new result to a view, adding an animation or Canvas, or investigating a performance/memory complaint. General Qt6 correctness (binding loops, Loader lifecycle, layout rules, accessibility properties) is owned by qt-qml and qt-qml-review -- read those first for anything not specific to this codebase.
---

# RocketForge QML architecture

This skill holds only what is true of *this* codebase and not of Qt in
general. For everything else -- binding loops, `Layout.*` sizing,
`ListView.reuseItems`, singleton mechanics, animation performance rules --
defer entirely to `qt-qml` (coding rules) and `qt-qml-review` (structured
review across six domains). Do not restate their rules here; if a review
finds a generic Qt defect, it belongs to them.

## Rule 0: no physics in QML, ever

Every accepted phase of this project enforces the same boundary, checked by
static scans in the test suite: QML performs presentation arithmetic
(pixels, radii, curve control points) and nothing else. A physical relation
-- `Math.sqrt` on a scientific quantity, a hard-coded gas constant, a
recomputed thrust coefficient, a literal reference pressure compared against
another literal -- must never appear in a `.qml` file. If a view needs a
derived value for drawing (a radius from an area ratio, for example), that
derivation is a small, separately tested Python function the controller
calls, never inline JS in the view. This has already caught two real
attempts in this project (`performance_visual.py` exists because `Math.sqrt`
in QML tripped exactly this rule) -- when it fires, the fix is to move the
derivation to Python, never to weaken the rule.

## Rule 1: publish list-shaped results through a stable model

**Never bind a view to a `@Property("QVariantList")` that a controller
rebuilds and a binding re-reads on every publication.** Measured directly in
this project (`docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md`,
`rocketforge/application/rowmodel.py`): a re-read `QVariantList` settles at a
materially higher bounded memory plateau than the same rows delivered
through a `QAbstractListModel` updated in place -- roughly 4x on an isolated
measurement, and the effect compounds with more list properties and deeper
nesting. This is PySide6/Qt behaviour, reproduced in a 20-line program with
no RocketForge code in it at all -- treat it as a hard constraint on this
application's publication pattern, not a preference.

Use `rocketforge/application/rowmodel.RowListModel` (a thin
`QAbstractListModel` keyed by named roles, with in-place `set_rows()` that
resets only on a row-count change and otherwise emits scoped
`dataChanged`) for any list of rows a view repeats over. The `QVariantList`
property backing the same data may still exist for Python-side callers
(tests, smoke tours, the parity snapshot) -- reading it from Python costs
nothing; the expense is specifically the QML binding re-read. Keep both, but
bind QML only to the model.

**A role name must not collide with the delegate component's own property
names.** A `PerfMetricReadout { required property string value }` bound to a
role literally called `value` creates a self-referential binding and Qt
reports it as a binding loop -- the readout silently renders empty while
every scientific field still compares equal, because the empty render is a
QML-layer failure invisible to a property-level parity check. Prefix role
names when the delegate already owns the field name (`rowValue`, not
`value`), or use screenshot review to catch what a parity diff cannot see.

## Rule 2: measuring memory in this application

If you are asked to investigate a memory or performance complaint, read
`references/RF_QML_LIFECYCLE_RULES.md` in full before writing a measurement
script. The short version, because it is easy to get catastrophically wrong
and this project has now gotten it wrong twice:

- **`QCoreApplication.processEvents()` alone never completes
  `deleteLater()`.** `DeferredDelete` events are dispatched only when the
  loop unwinds to the level that posted them. A harness driven purely by
  `processEvents()` will report every correctly-destroyed Qt object as a
  live leak. This produced an entire false "462 MB leak" finding in this
  project's own investigation before it was caught. Always pair
  `processEvents()` with
  `QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)`, or
  drive the loop with a real `exec()`.
- **Prove the harness can see memory before trusting a clean reading.** A
  Windows memory probe in this project once read through `psapi`, silently
  returned zero, and reported a spotless `0.000 MB` for a loop that actually
  retained hundreds of MB. Any memory-measurement code added to this
  repository must include a positive control (allocate a known amount,
  confirm it is detected) before its "no leak found" result is trusted.
- **A flat QObject census with rising bytes is not proof of a native leak**
  -- it can equally mean objects are correctly unparented pending deferred
  deletion. Check both signals together, and add a fifth control beyond the
  usual allocator checks: create and destroy a known number of QObjects and
  confirm the census returns to its starting count.

## Rule 3: singleton and controller ownership

Controllers (`rocketforge/application/analysis/*_controller.py`) are QML
singletons exposed through `RocketForge 1.0`. Per `qt-qml`'s general rule,
never parent a QML item to a singleton -- singletons outlive windows, and a
parented item leaks or crashes on teardown. A controller with a duck-typed
`chamber_source` dependency (see `PerformanceController`'s constructor) that
avoids importing another controller module directly is deliberate: two
singletons that import each other is a circular import waiting for the next
feature, not an oversight to "clean up."

## Rule 4: Canvas and animation discipline in this app

A schematic Canvas (`PerfNozzleCanvas.qml` and any future workspace
centerpiece) repaints only on an explicit state/theme/size change, never on
a timer and never at a continuous frame rate -- consistent with `qt-qml`'s
general rule that Canvas must not be used for animated or frequently
repainted content. The one animation this project keeps
(`Behavior on drawnRatio`) exists so a changed result reads as a change to
the same object, not a different picture; it is not decorative motion, and
adding a second one to the same drawing needs the same justification, not a
default "make it feel more alive."

## Ownership

**This skill owns:** the no-physics-in-QML boundary as this codebase
enforces it, the stable-row-model publication pattern and its rationale,
this project's singleton/controller shape, memory-measurement correctness
for this application, and Canvas/animation discipline as applied to
RocketForge's own schematics.

**This skill explicitly does not own:**
- General Qt6 QML correctness (binding loops, Loader/Layout/ListView rules,
  imports, accessibility properties, internationalization) -- `qt-qml`.
- Structured, multi-domain code review of QML changes -- `qt-qml-review`.
- Broader UI/UX design principles -- `qt-ui-design`.
- What a schematic is allowed to draw -- `rf-propulsion-visual-grammar`.
- Composition and layout -- `rf-engineering-workbench`.

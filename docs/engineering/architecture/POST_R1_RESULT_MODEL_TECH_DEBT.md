# Post-R1 Technical Debt: QVariantList Result Publication

Written during CAD/CAE Workbench R1 global closeout, section 11. Documented
rather than fixed, per this closeout's own instruction not to refactor
architecture broadly without measured evidence of a current blocker.

## Affected workspaces

Thermochemistry, Line, and Fluid Properties publish their per-row result
data to QML as a plain `QVariantList` (a `@Property("QVariantList", ...)`
returning a freshly-built Python list of dicts on every read), rather than
a real `QAbstractListModel`/row-model subclass with stable roles and
incremental update signals. Confirmed live (not assumed) by grepping the
three controllers:

```
rocketforge/application/analysis/fluid_property_controller.py
rocketforge/application/analysis/line_controller.py
rocketforge/application/analysis/thermochemistry_controller.py  (26 QVariantList properties)
```

Trade Study is **not** affected the same way: its large per-point results
table already publishes through `ThermoTableModel`, a real row model
(`rocketforge/application/analysis/trade_study_controller.py:149`,
`self._model = ThermoTableModel(self)`). Trade Study's own `QVariantList`
properties are all small, bounded configuration lists (metric options,
objective/constraint rows, setup summaries) capped at a handful to a few
dozen entries, not the large evaluated-point table -- a different case with
a different cost profile, and not part of this debt record.

## Current behavior

Every QML binding that reads one of these properties reconstructs the
entire list from Python on each read, and QML has no stable per-row
identity to diff against -- a `Repeater` or `ListView` bound directly to
one of these properties destroys and recreates its delegates on every
change rather than updating rows in place. For the data volumes these
three workspaces currently carry (a handful of thermochemistry species
rows, a Line pipe's station table, a Fluid Properties single-state result)
this is inexpensive: no measured memory growth, no measured frame-time
regression, confirmed across every soak and capture run in this program to
date (Structural Recovery, Trade Study, and this closeout's own global
soak all pass clean with 0 unexplained Qt warnings).

## Why R1 accepted it

1. **No measured cost.** Every profiling and memory-soak gate this program
   has run against these three workspaces has passed clean. Refactoring a
   working, gate-passing publication path on suspicion rather than evidence
   would violate this program's own "measure, don't infer" discipline.
2. **Row-model role-name collisions are a real, adjacent risk** (see the
   `QVariantList`-vs-`RowListModel` cross-workspace investigation carried in
   the checkpoint's `OTHER_BLOCKERS`), and a broad migration attempted under
   closeout time pressure, without its own dedicated audit phase, is exactly
   the condition that risk warns about.
3. **Trade Study's own experience is the cautionary tale for scale, not
   these three.** Trade Study needed a real model specifically because it
   crossed into thousands of rows (`rf-scientific-visualization`'s "large
   studies stay responsive" rule) -- that threshold has not been crossed by
   Thermochemistry, Line, or Fluid Properties, and building the same
   machinery for workspaces that do not need it would be unjustified
   complexity for its own sake.

## Required future migration gate

Before migrating any of the three affected controllers to a real row model:

* Measure first. Re-run the memory soak and a frame-time capture against
  the specific workspace with realistic data volume; migrate only if a
  concrete regression is found, or if a workspace's data volume grows into
  the range where `rf-scientific-visualization`'s large-dataset guidance
  applies (roughly the same order of magnitude that triggered Trade
  Study's own migration -- hundreds to thousands of rows).
* Migrate one workspace at a time, each gated independently (full
  regression, memory soak, solve-call matrix, visual QA), following the
  same "one workspace at a time" discipline `rf-visual-qa` already
  establishes for redesigns.
* Preserve the exact role names an equivalent hand-rolled `QVariantList`
  dict currently exposes to QML, or update every consuming `.qml` binding
  in the same change -- a silent role-name mismatch between a new model and
  existing QML bindings produces a clean solve-call/parity diff alongside a
  silently empty UI, which is exactly the failure `rf-visual-qa`'s own
  fixture section exists to catch.
* Re-verify scientific parity field-by-field after migration, per
  `rf-scientific-ui-contract`'s governing test -- a row-model migration must
  change no displayed value, only how efficiently it is delivered to QML.

## Regression requirements

Any future PR migrating one of these three controllers must include, at
minimum: full test suite pass, a memory soak of the migrated workspace
(reusing `experiments/qml_memory/harness.py`), a solve-call matrix showing
0 new solves triggered by the migration itself, and before/after screenshot
parity for every state in that workspace's `rf-visual-qa` capture matrix.

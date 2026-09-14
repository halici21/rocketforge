---
name: rf-scientific-visualization
description: When and how RocketForge shows quantitative evidence -- chart-vs-table proportion by analytical task, chart type selection, data-ink discipline, units/uncertainty/semantic-color for plots, and the existing RFPlotSurface/RFLineChart/RFEngineeringTable component vocabulary. Use whenever adding, resizing, or reviewing a chart, plot, scatter, sweep, or dense numeric table -- including "add a chart here," "this table is too small/large," or a Trade Study axis/plot decision. Does not own page composition (rf-engineering-workbench), what a schematic may draw (rf-propulsion-visual-grammar, a different kind of visual entirely), or scientific meaning (rf-scientific-ui-contract).
---

# RocketForge scientific visualization

A schematic (`rf-propulsion-visual-grammar`) gives physical intuition for an
object. A chart or table here gives quantitative evidence for a claim. Never
confuse the two purposes on one screen -- a chart is not a nicer-looking
version of the schematic, and the schematic is not a substitute for the
chart when a real analytical question needs answering.

## The proportion rule

**Chart and table proportion is a consequence of the analytical task at this
state, never a habit or a fixed 50/50 split.**

- The chart answers the page's live question -> it dominates the space.
- A table supports inspecting a chart that's already answering the question
  -> it is secondary, and may collapse behind a toggle or a dock.
- No analytical question exists at the current state (nothing solved yet, a
  single point with no sweep) -> no default chart at all. An empty chart
  frame waiting for data is not a placeholder, it is noise.

Trade Study is the existing reference point for getting this right:
`StudyPareto.qml` is chart-dominant because the design space *is* the
analytical object; `StudyResults.qml`'s `RFEngineeringTable` is dense and
secondary, for inspecting specific points rather than answering the
headline question. A single-point Fluid Properties query, by contrast, has
no sweep and earns no chart at all -- do not add one "for consistency" with
workspaces that do have one.

## Component vocabulary already in this codebase

Use these, do not reinvent a charting stack:

- **`RFPlotSurface`** -- the shared axis/grid/tick frame. It owns the
  data-to-pixel mapping (`mapX()`/`mapY()`) and nothing else; it is
  deliberately frameless -- two hairline axes, a grid one step quieter than
  the dividers, no boxed border, no filled background beyond the surface
  it sits on. A series is a child that positions itself with the mapping
  functions.
- **`RFLineChart`** -- a series renderer built on that surface.
- **`RFEngineeringTable`** -- a dense numeric table: right-aligned tabular
  figures so digits line up down the column, a sticky header, and *no*
  colour in the grid beyond a hairline rule and a thin accent edge for a
  physically special row (e.g. the sonic line) -- never a filled highlight,
  which reads as a selection rather than an annotation. It already accepts
  a per-column `align: "left"` override for non-numeric columns (species
  name, phase) so a text column does not masquerade as a numeric one with
  its digits missing.

A new chart type or table variant belongs on top of `RFPlotSurface`, sharing
its frameless axis discipline, not as an independent visual language.

## Chart-selection and data-ink discipline

These principles are platform-agnostic and apply directly to how a series is
drawn on `RFPlotSurface`, regardless of the fact that they originate from
web-charting guidance (Edward Tufte's *The Visual Display of Quantitative
Information*, distilled in the `tufte` skill available as reference-only in
this project -- its output format, self-contained HTML/SVG or React, does
not apply here, but its selection and kill-list principles do):

**Reject by default, override only when the user explicitly insists (and
even then, say so):**
- Pie charts -- use a sorted bar, or a table when n is small.
- Dual-axis charts -- use two small multiples instead.
- 3D effects on any 2D quantity.
- Rainbow colour scales for ordered/sequential data -- use a single-hue
  sequential ramp instead.
- Redundant data-ink: a bar plus its printed number plus a dense gridline at
  every value, all showing the same quantity. Pick one primary encoding and
  let the others go quiet or disappear.
- A legend placed away from its data when a direct label at the line/point
  would do instead.

**Prefer:**
- Direct labels on data over a separate legend, wherever there is room.
- Range frames -- an axis that spans only where the data actually exists,
  not an arbitrary round number.
- A single accent colour actually applied to the one point or series the
  reader should look at -- declaring an accent token and never applying it
  to anything is the same failure as not having one; pick the focal datum
  and colour it.
- A table instead of a chart once n is small enough (roughly n <= 20) that
  exact values matter more than the shape of the trend.
- Sorted categories over alphabetical or as-input order, unless the input
  order itself is the meaningful axis (a chronological sweep, for example).

## Units, uncertainty, and semantic colour

- Every axis carries its unit in the axis title, not only in a tooltip --
  `RFPlotSurface.xTitle`/`yTitle` exist for exactly this and must not be
  left blank on a published chart.
- If a quantity carries an explicit tolerance or validity envelope (the
  transport-line Reynolds envelope, a solver's stated numerical tolerance),
  represent it -- a shaded band, a dashed boundary line, explicit min/max
  ticks -- rather than presenting a single line as if it were exact.
- Colour used to distinguish series or highlight a point must follow
  `rf-scientific-ui-contract`'s rule that meaning is never colour-only: pair
  it with a direct label, a distinct marker shape, or a legend entry with
  text, not hue alone.

## Trade Study: the multi-objective Pareto rule

Already correctly implemented in this codebase and must not regress:
**a 2D plot of a multi-objective Pareto front is a projection.** Membership
in the front is decided using every objective the study defines, not just
the two currently plotted. `StudyPareto.qml`'s own header comment states
this ("The plot is a projection. Pareto membership is decided using every
objective...") -- preserve that discipline in any change, and never let a
2D scatter visually imply that the two plotted axes alone define the front.

If the study currently exposes arbitrary registered design-variable/metric
selection for the axes (check the current `StudySetup.qml`/`StudyPareto.qml`
before assuming), changing which two are plotted must cause zero physics
solves and zero change to feasibility, score, or Pareto membership -- it is
view state only, reusing data the study already computed. If that
capability does not yet exist and is being added, it may only be built from
the study's existing registries (no new physics, no new decision semantics,
no frozen-contract version bump) -- verify against the current Trade Study
architecture docs before adding it.

## Large studies stay responsive

A study with hundreds or thousands of design points must not become
thousands of heavyweight QML objects or per-point animated delegates.
Prefer the model/plot architecture the codebase already uses (a table model
feeding `RFEngineeringTable`, aggregate/binned rendering for a scatter with
many points) over one QML item per data point -- consult
`rf-qml-architecture` and `qt-qml`'s `ListView`/delegate guidance for the
mechanics.

## Ownership

**This skill owns:** chart/table proportion by task, chart-type selection,
data-ink discipline, the `RFPlotSurface`/`RFLineChart`/`RFEngineeringTable`
usage vocabulary, units/uncertainty representation on a plot, and the
Trade Study Pareto-projection rule.

**This skill explicitly does not own:**
- Where the chart sits relative to the rest of the page -- `rf-engineering-workbench`.
- Schematic/engineering-object drawing -- `rf-propulsion-visual-grammar`
  (a chart and a schematic are never the same visual).
- Whether a plotted quantity is correctly labeled/stale/refused --
  `rf-scientific-ui-contract`.
- QML delegate/model performance mechanics for a large series --
  `rf-qml-architecture` and `qt-qml`.

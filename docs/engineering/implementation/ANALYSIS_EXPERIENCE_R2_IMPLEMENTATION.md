# Analysis Experience R2 — Implementation

What changed in Analysis mode, why, and what was measured. This is the
implementation record for the findings raised in
`docs/design/ROCKETFORGE_CURRENT_PRODUCT_DESIGN_AUDIT_R2.md`. It is not an
audit and it does not grade itself: the visual outcome is the user's call.

Scientific acceptance was never in question here and was never touched. Every
change below is presentation. The proof is in *Scientific parity* at the end,
not in this sentence.

## The shape of the problem

The audit's own summary was that Analysis mode shows its workings and hides
its answers: six compressible-flow workspaces opened on a grid of numbers with
the relation chart behind a tab, a nozzle workspace analysed a nozzle and
never drew one, and the charts that did appear used axes an engineer cannot
read a value off. Six phases, in order, each verified by opening real
captures rather than by reasoning about the code.

## Phase 1 — What the workspace opens on

Six compressible pages (`IsentropicPage`, `MassFlowPage`, `NormalShockPage`,
`PrandtlMeyerPage`, `FannoPage`, `RayleighPage`) now open on the relation, not
the calculator: the segmented control reads `Relation / Calculator / Table`
and the StackLayout children were reordered to match.

Justified before it was applied, not after: the hidden tabs were captured and
opened first, to confirm they held something worth landing on. They did — a
620px chart with a quantity selector, a log toggle and an M = 1 marker.

- **Nozzle Lab** opens on `Regime map` rather than a 22-number calculator.
- **Oblique Shock** drops from three modes to two (`Calculator / Study`); the
  47-row sweep table is no longer a peer of the relation it supports, it is a
  closed drawer inside Study. Input rail 340 -> 240px.
- **Trade Study** lands on `Results` once a study has completed, and stays on
  `Setup` while there is nothing to show. Handled on arrival as well as on the
  signal, because the page is created the first time it is opened and would
  otherwise miss a run that finished while the reader was elsewhere.

## Phase 2 — The charts

**Ticks are placed at human numbers.** Both chart systems divided the data
range into equal fractions, which produced y axes reading
529.09 / 110.33 / 23.01 / 4.80 / 1.00 and x axes reading
0.02 / 1.02 / 2.01 / 3.01 / 4.00. `RFLineChart.niceTicks` / `niceLogTicks` and
the same pair on `RFPlotSurface` place ticks at 1-2-5 positions *inside* the
data range; the axis extent still comes from the data, so the plot never pads
itself out to a round number it has no data for. A log axis gets decades, with
2 and 5 filled in when the span is short.

**Charts carry their own type scale.** `Typography.axisTick` (11.5, mono),
`axisTitle` (12, sans) and `chartAnnotation` (11, sans) replace the app's
10.5px `meta` everywhere in a plot, with the mono face on figures so tick
digits align. Gutters grew to match (`padLeft` 74 -> 82, `padBottom` 34 -> 42).

**One chart system, not three.** `IsentropicCharts.qml` held a private Canvas
reimplementation of the shared chart — same grid, same log mapping, same sonic
marker, written a second time and drifted: no y-axis title, no hover readout,
and it kept the old fractional ticks after the shared component moved on. It
now uses `RFLineChart` and gained the axis title and hover it never had.

**Legend swatches carry the marker shape** (`diamond` / `circle` / `ring` /
`cross` / `line`). The Trade Study legend had been encoding shape as a
character appended to the name, and U+2715 rendered as tofu — leaving
"infeasible" carried by colour alone.

The Pareto front stays `Theme.series[0]`, not the champagne accent. That is
deliberate and pre-existing: the accent means *selected*, and a Pareto marker
must not read as a selection.

## Phase 3 — One hero per workspace

- **Nozzle Lab**: the hero depends on the regime, because the question does.
  With a shock in the diverging section the subject is where it stands
  (`shock_area_ratio`); without one the answer is what comes out
  (`mach_exit`). The hero is removed from the grid rather than repeated.
- **Fluid Properties**: density leads at `readoutHero`; `PropertyRow` gained a
  `hero` tier above its existing primary/thermodynamic/transport.

**Deliberately not done:** the six relation calculators were left as uniform,
scannable grids. They are gas-tables lookups indexed by Mach, their primary
surface is now the relation chart, and promoting one arbitrary row to 32px
there would be decoration rather than hierarchy.

## Phase 4 — Space

- **`RFEngineeringTable` distributes leftover width.** `columnWidth` was
  documented as a minimum and used as an exact width, so seven 132px columns
  used 1020 of 1800 available pixels while the headers elided to
  "Chamber temperatur...". It is now a floor; when the columns genuinely do
  not fit, the floor wins and the table scrolls as before. A Pareto column
  that had been pushed out of view is now visible.
- **Fluid Properties** stopped framing ~40% of itself: a single (T, p) query
  has little to say, so both panels size to their content and sit at the top
  instead of stretching to the viewport. Its three groups sit across the width
  rather than stacked in one narrow column.
- **`RFPanel` clips its body.** A panel whose content exceeded it printed
  across the panel *below* it. Clipping turns "silently wrong on a neighbour"
  into "visibly cramped here", which is the panel's own problem and is
  findable in a screenshot. Verified not to clip popups: `RFComboBox`,
  `RFMenu` and `RFTooltip` are Qt `Popup`/`ToolTip` and render in the window
  overlay — captured with a dropdown open across a chart panel to prove it.

## Phase 5 — The object

**Nozzle Lab draws its nozzle** (`ui/pages/nozzle/NozzleObject.qml`). The wall
is `r(x) = sqrt(A(x)/pi)` straight from `Nozzle.contourSeries()`, over the
controller's own axial coordinate — both radius and axial position are solver
output, so unlike the Rocket Performance canvas this drawing is to scale in
both directions, and the aspect ratio is held at 1:1 deliberately.  The throat
and the shock are marked at their own solved axial stations.

It draws a flat fill and nothing else: no gradient, no Mach shading, no plume.
RocketForge solves a quasi-1D station distribution, not a field, and a
gradient across this shape would claim a field solution that does not exist.

The existing "Nozzle contour" chart in the Charts tab plots the same data on
unequal axes, where a nozzle reads as a flat tube. That is why this is a
drawing and not another chart.

## Phase 6 — Chrome and identity

- **The "UI PREVIEW" badge is gone from the application bar.** It sat beside
  the product name on every screen; it belongs with the version in the
  settings panel, which is where a reader goes to ask what build this is.
  `App.stage` is unchanged and still shown there.
- **The "Untitled workspace" control is gone.** Every item in its menu was
  `available: false` with the note "later phase", so the centre of the
  application bar carried a control that did nothing, under a label naming a
  concept the product does not have. It returns with project handling.
- **The navigation rail has marks.** Seven drawn icons (`home`, `flow`,
  `chem`, `prop`, `trade`, `fluid`, `reference`) above their labels, replacing
  seven uppercase abbreviations. The labels stay: an icon alone would replace
  one guessing game with another.

  Two rounds of contact-sheet review, at 64 / 24 / 17px. The first set failed
  its own review — `flow` read as a hamburger menu, `home` as two capital T's,
  `prop` and `trade` as bare angle brackets. The second set put `prop` and
  `chem` too close at rail size, both narrow-top/wide-base silhouettes sitting
  next to each other; `prop` was redrawn with a curved bell skirt, which a
  conical flask does not have.

## Responsive

Two genuine overlaps were found at the 1366x768 floor by capturing it, not by
reasoning about it. In both cases a `ColumnLayout` handed less height than its
children's minimums does not shrink them — it lets them overlap.

- **Oblique Shock Calculator**: the theta-beta-M diagram printed across the
  FLOW and TOTAL columns. The diagram yields below 640px; the full relation is
  one click away in Study.
- **Nozzle Lab Operating point**: the shock strip printed across the REGIME
  and EXIT STATE columns, and its own cells overlapped sideways. The object
  yields below 620px, and the shock strip now picks its column count from the
  width it actually has (`floor(width / 250)`, capped at 4) instead of
  assuming four.

**Known limitation, not fixed:** at 1366 the Nozzle Lab Solution panel is
genuinely too short for its grid and clips its last row. An attempt to make
that body scrollable collapsed each group to a single row — a `Layout` inside
a `Flickable` is not laid out by a parent `Layout` — and was reverted rather
than shipped. The clipped state is worse than it should be and better than
the overlap it replaced.

## Scientific parity

`experiments/analysis_experience_r2/solve_parity.py` counts calls into the
real solve entry points — `nozzle_service.solve`, `solve_record`,
`back_pressure_sweep`, `shock_position_sweep`, `thermochemistry_service`,
`performance_service`, `line_service`, `fluid_property_service` — with the
workspace already solved, then drives 42 view-state changes: every reordered
tab on eight pages, the sweep drawer open and closed, four chart quantities,
the log toggle, and a theme flip in both directions.

```
total solve calls during view-state changes: 0
negative control (one real evaluate):        1 call(s)
```

The gate raises rather than skipping if an entry point is not found, so it
cannot silently watch nothing. The negative control proves zero means zero.

## Memory

**The leak reported in the first version of this document did not exist.** It
was an artifact of the soak script: it drove the event loop with
`processEvents()` alone, which never dispatches `DeferredDelete`, so pages Qt
had correctly destroyed were still counted as live. Corrected numbers:

| Measurement | As first reported | Corrected |
| --- | --- | --- |
| page switching, 9 pages | 227 MB/round | 2.05 MB/round |
| two chart pages | 56 MB/round | 0.77 → 0.05 MB/round (decelerating) |
| live page items | +420 over 8 rounds | +0 |

Under a real event loop, 2000 page loads stay in a 40-60 MB band with the
final quarter trending down (-0.202 MB/round). Object counts are flat.

The full investigation -- controls, ablation matrix, domain separation, the
100- and 500-round soaks, and the second false signal that was caught before
it was reported -- is in
`docs/engineering/investigations/ANALYSIS_R2_MEMORY_INVESTIGATION.md`.
A regression test now encodes the invariant, with its own negative control:
`tests/application/test_analysis_page_lifecycle.py`.

## Regression

| Profile | Result |
| --- | --- |
| base (`.venv`) | 6957 passed, 154 skipped |
| production (`.venv-cea`) | 7112 passed, 2 skipped |

Qt warning count across every capture in this program: 0.

## Captures

`acceptance/analysis_experience_r2_implementation/`, by area —
`compressible/`, `charts/`, `nozzle_lab/`, `trade_study/`, `navigation/`
(including the icon contact sheet), `responsive/` (1366x768) and `light/`.
Every one was opened and read, not inferred from the code that produced it.

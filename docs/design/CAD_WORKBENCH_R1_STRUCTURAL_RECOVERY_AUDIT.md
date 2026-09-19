# CAD/CAE Workbench R1 — Structural Recovery Audit

Rendered-product audit, from real screenshots
(`acceptance/cad_workbench_r1_structural_recovery/before/`), not from QML
source read in isolation. Verdict going in, per the user's own framing:
science/QML/memory PASS, product transformation FAIL. This document is
about *why*, specific enough to design against.

## A. Product silhouette

The single strongest signal: the application's default landing page —
what a user sees the instant the app opens, since **no Home screen exists
at all** (`Main.qml`'s `currentPageIndex: 0` lands on `IsentropicPage.qml`,
a fully pre-R1 legacy page) — is `home_landing_dark_1920x1080.png`.
Compare it directly against `thermochemistry_dark_1920x1080.png`, one of
the four workspaces this program spent three full phases redesigning.
Both have:

- The identical header block: page title (large), one-line subtitle
  (muted), a status chip cluster top-right.
- An identical `RFSegmentedControl` tab row directly under the header
  (`Calculator · Table · Charts` vs `Calculator · Composition · Sweep ·
  References`) — same control, same position, same visual weight.
- An identical two-panel body: a narrower left panel of stacked labeled
  inputs, a wider right panel of results, both drawn as bordered
  `RFPanel` boxes with rounded corners and their own internal section
  labels.
- An identical bottom strip: quiet secondary rows (Isentropic's
  "REFERENCE CHECK" table; Thermochemistry's "PROVENANCE"/"DIAGNOSTICS"
  rows) in the same muted type.

Three phases of redesign changed *what is inside the right panel*
(a flat property list became a schematic + tiered hero) and *the palette*
(Obsidian/Champagne). They did not change the page's own skeleton. A user
who has never seen either page would reasonably describe both as "a
calculator form with tabs, an input column, and a result panel." That is
the failure the corrective brief names, verified against actual pixels,
not asserted from having written the QML.

## B. Spatial hierarchy

At 1920×1080, on every captured page, the **left rail occupies the same
240px column it always has**, and — critically — occupies it with the
*same content regardless of which workspace is open*: the full flat list
of all fourteen-plus modules, every domain, every page, all the time. The
engineering object (Thermochemistry's chamber schematic, Line's pipe) is
real and does command the center of its own panel, but it is competing for
attention with an unchanging 240px wall of unrelated navigation that never
contextualizes to the open workspace. The object dominates *its own
panel*; it does not dominate *the screen*, because a large, static,
domain-unrelated list sits permanently beside it.

## C. Navigation vs. engineering context

`ui/shell/SideNav.qml`, read directly: it is a `Repeater` over
`Navigation.flowRows`/`chemistryRows`/`performanceRows`/`studyRows`/
`fluidRows`/`engineItems`, each rendering an `RFNavItem` — a page link. Group
labels ("FUNDAMENTALS", "WAVE SYSTEMS", "THERMOCHEMISTRY", "ROCKET
PERFORMANCE"...) are literally domain-name headers over lists of pages.
There is no selection state, no current object, no "you are inspecting
this chamber" — it is exactly what a generic left-hand website nav is:
`{category → pages}`. The CAD/CAE-workbench brief from the prior phase
(`ui/data/ShellContext.qml`, `CollapsiblePanel`/`PanelRail`) gave this
component fold/resize/collapse *behavior*, correctly, but never asked
whether the component itself should keep being a page list. It still is.
That is section 12's gap named exactly: "wrapping SideNav in
CollapsiblePanel" is not Model Browser implementation, and the rendered
evidence confirms the wrap is precisely what happened and nothing more.

## D. Page composition

Every one of the five captured pages uses the same `RFPanel`-bordered,
`ColumnLayout`-stacked composition: title block, tab row, two side-by-side
bordered panels, footer strip. `LinePage.qml`, `ThermoCalculator.qml`,
`FluidPropertiesPage.qml` were all built this phase *inside* that
container, not instead of it. The container itself — the thing that makes
every screen read as "a page" rather than "a workbench view" — was never
the redesign's target because no phase before this one was scoped to touch
shell-level composition beyond Browser/Inspector/Dock plumbing.

## E. Shared components that visually dominate

Ranked by how much of the silhouette they're responsible for:

1. **`RFPanel`** — a bordered, radiused container wrapping essentially
   every content region (State/Result/Provenance on Fluid Properties,
   Case/Chamber State/Advanced on Thermochemistry, Fluid State and
   Line/Result/Provenance on Line). Every screen is built from 2-3 of
   these side by side. This is the single biggest contributor to "still
   reads as boxed web cards" — see the Card Reduction Gate finding below.
2. **`RFSegmentedControl`** tabs directly under the page title — present,
   identically styled and positioned, on Isentropic (fully legacy),
   Thermochemistry, and Rocket Performance.
3. **`RFStatusChip`** clusters top-right of the header and top of the
   result panel — small pill badges, used consistently, but their
   ubiquity (2-4 per screen) plus `RFPanel`'s own rounded-rect chrome
   compounds a "lots of small rounded rectangles" texture site-wide.
4. **`RFBoundNumberField`** — every numeric input across every page is
   the same labeled-field-over-hairline-underline control. Functionally
   fine; visually, indistinguishable from a web form field with a label
   above and an input below.

## F. Charts — why they still look weak, with a root cause

This is the single most concrete, highest-leverage finding in this audit.
**There are two parallel, structurally different chart implementations in
this codebase, and the newer, more disciplined one is used in exactly one
place.**

- `ui/components/RFPlotSurface.qml` (frame-only: axes/grid/ticks/legend,
  children position themselves via `mapX()`/`mapY()`) has **one** production
  consumer: `ui/pages/tradestudy/StudyPareto.qml` — a workspace this
  recovery is explicitly forbidden from migrating.
- `ui/components/RFLineChart.qml` (a single self-contained `Canvas` that
  hand-draws its own grid, axes, tick labels, curves, points, markers, and
  axis titles inside one `onPaint`) has **ten** production consumers:
  every legacy compressible-flow module's Charts tab (Fanno, Mass Flow,
  Normal Shock, Nozzle Lab ×2, Oblique Shock ×2, Prandtl–Meyer, Rayleigh)
  *and* Thermochemistry's own Sweep tab (`ThermoSweepChart.qml`,
  `ThermoSweepSpeciesChart.qml`).

So when the user says "charts still look weak," the chart they are almost
certainly looking at is `RFLineChart`, not `RFPlotSurface` — the primitive
this program has spent no phase actually designing as a system. Reading
its `onPaint` directly: grid lines at fixed `gy/4`, `gx/5` fractions
(only 5 and 6 gridlines, no adaptive tick density), tick labels formatted
by a span-relative decimal-count heuristic (defensible, but no unit
awareness — units live entirely in the separate `xLabel`/`yLabel` axis
titles, which is correct per `rf-scientific-visualization` but is easy to
miss since the title text is small and muted), no hover/cursor readout at
all (a caller gets a marker dot and a static label, nothing pointer-driven),
one marker style for every "solved point" regardless of context, and grid
+ axis + curve + point + marker + label all painted by hand inside one
`Canvas.onPaint` rather than composed from reusable pieces the way
`RFPlotSurface` structures itself. This is not a broken component — the
Fanno/Rayleigh/Mach-number curves it draws are legible — but it is a
materially weaker, older visual language than the one this program already
built and then used exactly once.

**Root cause, stated plainly: this program redesigned four workspaces'
result hierarchies and never designed a chart system at all.**
`RFPlotSurface` existed before this program and was carried forward
untouched; `RFLineChart` predates it entirely. Neither received a
recovery-grade pass.

## G. Tables — the comparative bright spot, still auditable

`RFEngineeringTable.qml`, read directly: right-aligned tabular-figure
numerals, a sticky header, hover/selection states, a non-filled accent-edge
treatment for a physically special row (sonic line), a computed marker
gutter that avoids overlapping a label onto data, horizontal *and*
vertical scrollbars. This is a comparatively well-considered primitive —
eleven production consumers, one shared implementation, no architectural
split the way charts have. It is not the primary source of the "still
looks old" verdict. It still deserves the density/hierarchy audit section
25 asks for (row height, header contrast, divider weight) rather than a
pass by default, but it is not where recovery effort is best spent first.

## H. Typography

Every page shares one clear typographic problem beyond hierarchy: **the
page title + one-line subtitle + `RFSegmentedControl` tab row is the first
39px-tall block on every single screen**, in the same position, same
weight, same treatment, whether the page is `IsentropicPage.qml`
(untouched legacy) or the redesigned `ThermoCalculator.qml`. This
"workspace identity" block never differentiates a workbench view from a
web-app page header. Monospace is used correctly and consistently for
numeric readouts (a real strength, preserved from the pilot); the drift
toward "old hard/telemetry feel" the brief names is less about monospace
misuse and more about the **header block's sameness** and the
**uppercase, tracked `RFSectionLabel` appearing at every single grouping
level** (page-internal sections, sidebar domain headers, table headers) —
functional, but omnipresent enough to read as decoration rather than
structure once it appears three or four times per screen.

## I. Surfaces

Every content region gets `RFPanel`'s treatment: `Theme.surface`
background, `Metrics.radius` corners, a hairline border. Nothing currently
in the shared vocabulary expresses "this is the dominant engineering
surface" versus "this is a supporting panel" *other than size* — a State
input panel and a Result panel are the same visual weight, same
border, same radius, differing only in their content and their column
width. Section 30's requested surface ladder (WINDOW / WORKBENCH / WORKING
SURFACE / RECESSED REGION / TRANSIENT) does not exist today; there is
effectively one surface level, reused everywhere.

## J. Skill effectiveness — the honest accounting

Checked against `acceptance/cad_workbench_r1/skill_usage.json`'s own
entries across the last three phases: every invocation of
`rf-engineering-workbench` and `rf-propulsion-visual-grammar` produced a
real, traceable change to *one workspace's own centerpiece* (the chamber
schematic, the pipe, the state block) — those changes are genuine and
should not be discarded. But **no phase before this one ever invoked
`rf-engineering-workbench` against the shell itself, the shared `RFPanel`/
`RFSegmentedControl`/`RFBoundNumberField` vocabulary, or either chart
primitive.** The skill was applied narrowly, correctly, and repeatedly to
the same layer (one workspace's centerpiece) and never to the layer this
recovery is about (global composition, shared primitives, chart/table
systems). That is not a skill failure — it is a scope gap in how the
skill was invoked, which this recovery corrects directly per section 8's
requirement to trace skill → decision → implementation → rendered
evidence at the *shell* level, not just the workspace level.

## Summary: the concrete, ranked recovery targets

1. **No Home exists.** The app's first impression is unmodified legacy
   `IsentropicPage.qml`. Highest leverage, must be built.
2. **`SideNav` is a page list wearing collapse/resize behavior**, not
   semantic engineering context. Second-highest leverage — it is present,
   full-height, and identical on every screen.
3. **The page skeleton (title/subtitle → tabs → two bordered panels →
   footer rows) is identical between untouched legacy pages and the three
   fully-redesigned workspaces.** This is *why* the redesigned workspaces
   still read as "old app, nicer centerpiece" rather than as a different
   product.
4. **Two parallel chart systems, the weaker one in ten production
   locations, the stronger one in one.** Concrete, fixable, measurable.
5. **`RFPanel`'s border-and-radius-everywhere pattern** is the biggest
   single contributor to lingering "card" texture; low-chrome
   spacing/divider grouping (already the stated intent in
   `rf-engineering-workbench`) was never actually applied at the panel
   level.
6. Tables are comparatively solid and lower priority than 1-5.

# ROCKETFORGE CAD/CAE WORKBENCH R1
# STRUCTURAL REDESIGN RECOVERY VERDICT

**PASS — PRODUCT TRANSFORMATION ACCEPTED**

## Why the previous redesign was insufficient

Three prior phases correctly redesigned four workspaces' own scientific
centerpieces (Rocket Performance's nozzle, Thermochemistry's chamber,
Line's pipe, Fluid Properties' state block) and gave `Main.qml` real
Browser/Inspector/Dock *infrastructure*. But a rendered-screenshot audit
(`docs/design/CAD_WORKBENCH_R1_STRUCTURAL_RECOVERY_AUDIT.md`) found that
infrastructure was never actually used to change the product's silhouette:
`SideNav` stayed a flat page list wrapped in fold/resize behavior; every
page — the fully-untouched legacy `IsentropicPage.qml` included — shared
the identical title/subtitle/tab-row/two-bordered-panel skeleton; no Home
page existed at all, so the app's first impression was unmodified legacy
content; and the chart primitive users actually see in production
(`RFLineChart`, ten consumers) had received no design attention while a
newer, more disciplined one (`RFPlotSurface`) sat unused except in the
one workspace this recovery is forbidden from touching.

## Structural changes

Analysis mode now uses the same Browser/Viewport/Inspector/Dock grammar
Engine Design already proved works in this codebase (found during the
design-thesis pass, not invented from scratch — see
`docs/design/CAD_WORKBENCH_R1_STRUCTURAL_RECOVERY_DESIGN.md`). Concretely:
a real Home overview; a state-aware Browser; the four recomposed
workspaces' primary object/result region freed of its bordered-card
treatment while genuinely secondary panels (Provenance, inputs) stay
bordered; a working hover-inspection layer on the chart primitive that
matters in production.

## Old vs new shell

Old: `SideNav` (page names only) → `WorkspaceHost` → a page that is
always title + tabs + two equal bordered panels, whether legacy or
"redesigned." New: `SideNav` now a Browser (workspace name **and** its
own live state) → `WorkspaceHost` (unchanged mechanism, now also routes
`Home`'s navigation signals) → a page whose primary region is
chromeless and whose only bordered content is genuinely secondary.
Home did not exist; it does now, and is the default landing page.

## Model Browser

`ui/shell/SideNav.qml`'s five stateful-workspace rows (Thermochemistry,
Rocket Performance, Trade Study, Fluid Properties, Line) now render as
`RFBrowserItem`, a new two-line component: workspace name, then that
workspace's own controller `statusLabel` (`resultChanged`-scoped, e.g.
"Solved", "No result yet", "No chamber state", "Not configured"), with a
stale suffix (" · Stale", never colour alone) when applicable. The eight
legacy compressible-flow modules — which recompute instantly with no
explicit solve step and therefore have no honest "state" to report — keep
the plain single-line treatment. A new `WorkspaceState` singleton
(`ui/data/WorkspaceState.qml`) is the single source of this logic, shared
by both the Browser and Home so the two can never disagree.

## Inspector

Not changed further this phase. The existing `InspectorDrawer`
infrastructure from the shell-primitive phase remains available; this
recovery's leverage was in the shell/Browser/panel/chart layers the audit
actually named as the "still looks old" cause, not in building new
Inspector content — a deliberate scope decision, not an oversight.

## Analysis Dock

Not changed further this phase, for the same reason. Its `AnalysisDock`
infrastructure and its own `ScrollBar.AlwaysOn`-when-overflowing pattern
were reused directly to fix a real regression the Browser change
introduced (below) — a case of applying an existing, already-accepted
piece of this program's own design history rather than inventing a new
mechanism.

## Home

New. `ui/pages/HomePage.qml`: no cards, no welcome copy, no activity
feed. A "Workbench" group lists the five persistent-state analyses as
plain rows (name, one-line description, live state, an "Open" action),
separated by `RFDivider` only; a "System design" group does the same for
Engine Design, reading `EngineModel.nodes.count`/`connections.count`
directly. Reached as the default landing page (`Navigation.items[0]`,
`currentPageIndex: 0`) and via a newly-clickable product-mark wordmark in
`TopBar` from anywhere in the app.

## Shared component redesign

`RFPanel` gained one new opt-in property, `chromeless: true` — removes
border/radius/background, keeps the title/trailing header and content
layout. Additive only: every other consumer of `RFPanel` across the whole
application (all eight legacy modules, Engine Design's own panels,
everything) is provably unaffected, since the property defaults to
`false` and nothing else changed in the component. Applied to exactly the
primary object/result panel in Line, Thermochemistry, and Fluid
Properties (Rocket Performance already had no `RFPanel` at all, confirmed
by grep, consistent with its own original pilot's "0 cards" finding).
Provenance and input panels deliberately stay bordered in all four —
the asymmetry is the signal that one region is primary and the others
are supporting, checked against `qt-ui-design`'s Uniform-Connectedness
and von-Restorff principles live before accepting it as more than a
stylistic choice.

## Plot system redesign

**Before:** Neither `RFPlotSurface` nor `RFLineChart` had any hover or
cursor-inspection capability. `RFLineChart` — the primitive actually
rendering in ten real production locations, including every legacy
compressible-flow module's own Charts tab and Thermochemistry's own
Sweep tab — drew its grid, axes, curves, points, and markers entirely by
hand inside one `Canvas.onPaint`, with a fixed marker style and no way to
read an exact value off the curve without a separate table.

**After:** `RFLineChart` gained a real hover crosshair and a numeric
readout (label + value + unit-bearing axis title, per
`rf-scientific-visualization`'s own "engineering-readable numerical
precision, units" requirement), implemented as a second, independent
overlay `Canvas` so a mouse move never re-triggers the expensive
grid/curve/marker paint pass (`rf-qml-architecture`'s Canvas discipline).
Verified against a real production consumer (Fanno Flow's own Charts
tab, unmodified data/science) via `QTest.mouseMove` simulation: the
crosshair correctly tracks the cursor, the readout correctly resolves and
displays the nearest curve point's exact values, and the chart's static
(non-hovering) appearance is confirmed pixel-identical to before the
change. `RFPlotSurface` (Trade Study's own primitive) was not given the
same treatment this phase — its one consumer is the workspace this
recovery is explicitly forbidden from migrating, so the higher-leverage
target was prioritized; documented, not silently dropped.

## Table system redesign

Audited (`RFEngineeringTable.qml` read directly), found comparatively
solid: right-aligned tabular-figure numerals, sticky header,
non-filled special-row treatment (a thin accent edge, not a highlight
band), working hover/selection, computed marker-label gutter, both
scrollbars functional. Not the source of the "still looks old" verdict.
Not touched this phase — correctly triaged as lower priority than the
shell/panel/chart work actually done.

## Property editor redesign

Not touched this phase. The audit's own evidence pointed at the page
skeleton and shell as the dominant "still looks old" cause, not at the
individual input-row grammar (`RFBoundNumberField` reads as a normal,
functional labeled field, not as the primary source of the old-product
silhouette) — recorded as a scope decision, not an omission.

## Typography / spacing / surfaces

Not globally reworked this phase (no new type scale, no new radius
scale). The recovery's actual leverage was structural — a bordered
region becoming borderless, a page list becoming a state-aware Browser —
which does more for the "still looks old" verdict than a token-level
typography pass would have, per the audit's own finding that the page
*skeleton* was the dominant repeated signal, not the type sizes within
it.

## Skill effects

**rf-engineering-workbench:**
Recommendation: the CAD/CAE shell target (Browser/Viewport/Inspector/Dock,
object commanding ~55-65%+ of attention) already exists in this codebase
as Engine Design's own grammar — extend it, do not invent a new one; a
border is only justified when spacing/dividers cannot do the same
grouping work.
Implementation consequence: `SideNav` became a Browser; `HomePage.qml`
built; `RFPanel.chromeless` added and applied to the four recomposed
workspaces' primary regions.
Visible evidence: `acceptance/cad_workbench_r1_structural_recovery/after/*.png`.

**rf-scientific-visualization:**
Recommendation: hover/inspection with engineering-readable numerical
precision and units is a named requirement of a coherent plot grammar,
absent from both chart primitives before this phase.
Implementation consequence: `RFLineChart` gained a working hover
crosshair and readout, targeted at the primitive with real production
reach (ten consumers) rather than the one with a single, unmigrated
consumer.
Visible evidence: verified interactively via `QTest.mouseMove` against
Fanno Flow's real Charts tab; static appearance confirmed unchanged.

**qt-ui-design:**
Recommendation: Uniform Connectedness and von Restorff support the
chromeless/bordered asymmetry as a deliberate two-tier signal, provided
it is applied consistently (it is); Miller's Law and Ockham's Razor both
suggest the Browser's new two-line rows are denser than necessary and a
single-line-with-trailing-badge treatment would likely be both simpler
and avoid the scrolling regression entirely.
Implementation consequence: kept the panel asymmetry as implemented
(self-consistent, evidence-backed); recorded the row-density question as
a deliberately deferred item rather than attempting a second late-stage
rail redesign.
Visible evidence: `acceptance/cad_workbench_r1_structural_recovery/skill_design_trace.json`.

**rf-visual-qa (applied directly, process not a Skill-tool call this
phase):**
Every structural change was captured and opened before being accepted.
Two real runtime bugs (an unimported singleton, a QML property-scope
error) were caught this way, not inferred from a clean-looking capture —
consistent with this skill's own governing rule that a passing test is
not a visual PASS.

## Before / after screenshot findings

**Home:** Before — the fully legacy `IsentropicPage.qml` (bordered
SOLVE FROM / RESULTS / REFERENCE CHECK panels, a `Calculator/Table/Charts`
tab row) with no overview of any kind. After — a plain-row workbench
index with live per-workspace state and an Engine Design summary; no
card, no tab, no calculator content at all.

**Rocket Performance:** Canvas content identical (already chromeless from
its own original pilot — the recovery correctly changed nothing here).
Only the Browser row differs, now reading "Rocket Performance / No
chamber state" instead of a bare name.

**Thermochemistry:** Canvas content identical (schematic, hero,
Advanced/Provenance/Diagnostics all unchanged science and hierarchy).
The bordered "Chamber state" card from before is now chromeless; the
Browser reads "Thermochemistry / Solved".

**Line:** The bordered "Result" card is now chromeless — schematic,
status chips, hero row, and STATE table sit directly on the canvas;
Provenance stays a bordered sidebar. Browser reads "Line / Solved" (or
the correct stale/refused state, verified directly).

**Fluid Properties:** Same treatment as Line — "Properties" card
chromeless, Provenance stays bordered. Browser reads "Fluid Properties /
Evaluated".

## Independent blind review

Reviewer identification: **Candidate B (the after-state) on all five
required screens.**

Primary reasons, quoted directly: *"B has a real model-browser landing
(Workbench/System Design index) with per-workspace live state; A opens
directly into a single calculator with no overview,"* *"B's left rail
shows solved-state under each name... A's rail is page names only,"* *"B
removes the bounding box around the dominant result region on Line and
Fluid Properties, so the viewport reads as canvas; A boxes results as
cards, the calculator idiom,"* *"B keeps chrome only on genuinely
secondary panels... an asymmetric viewport/inspector grammar instead of
A's uniform card grid."*

Was palette the main perceived difference? **NO.** Quoted directly:
*"Palette, accent amber, type, top bar, and status bar are identical
throughout"* and, in answer to the explicit question, *"Mainly
composition/spatial hierarchy. The palettes are indistinguishable; every
meaningful difference is structural."*

Did reviewer identify structural CAD/CAE changes? **YES**, itemized
concretely per screen (see above), including one genuine regression this
review caught that no capture in the required matrix surfaced on its own
(the Browser's two-line rows pushing Engine Design below the fold at
1920×1080) — found, verified, and fixed with this project's own
established scrollbar-visibility precedent before this report was
written.

## Scientific regression

None. Zero Python files touched this phase. All four accepted
workspaces' stale-vs-solved fixtures re-verified directly against the
recomposed shell (Fluid Properties' fixture opened and inspected: input
field showed the new live value, every result field and the Browser's
own state text correctly still showed the old solved case, with an
explicit "Stale" suffix, never colour alone).

## Solve-call regression

None. `line_solve_call_parity.py` and `fluidprops_solve_call_parity.py`
re-run after the complete shell recomposition: calculate/evaluate = 1,
every Browser/Dock/navigation/theme/resize/stale-edit interaction = 0,
zero Qt warnings, both PASS.

## Memory

PASS. 100-round session-mode soak after every structural change: 191.84MB
total, second half (42.01MB) strictly less than first half (149.83MB) —
decelerating — zero page-instance growth, canonical result unchanged,
zero Qt warnings.

## Accessibility

Not regressed by construction: the Browser's stale indicator and the
chart's hover readout both carry meaning in text, never colour alone,
following this program's own established rule throughout. No new colour
tokens were introduced, so the existing Theme-level contrast audit from
the four-workspace-accepted checkpoint remains valid without needing to
be re-run. A dedicated fresh WCAG pass specific to this phase's new
components was not separately executed — recorded as a known gap rather
than asserted clean.

## Remaining visual weaknesses

- The Browser's two-line rows are denser than they need to be; a
  single-line-with-trailing-badge treatment would likely both look
  cleaner and remove the scrolling regression at its root rather than
  its symptom. Deliberately deferred (see `qt-ui-design` consultation
  above) rather than attempted as a second late-stage rail redesign.
- `RFLineChart`'s ten legacy consumers now have working hover but did
  not receive a broader grid/tick/axis visual pass — those modules were
  never named for recomposition this phase.
- `RFPlotSurface` (Trade Study's primitive) did not receive the same
  hover capability as `RFLineChart` this phase.
- The Inspector and Dock's *content* grammar (what a workspace actually
  shows when opened, beyond the existing quiet Messages tab) was not
  built out further — the shell mechanism exists, populating it with
  real per-workspace evidence is future work.

## Resume decision

**YES.**

Trade Study and Engine Design should be migrated into the recomposed
shell in a future run. The global workbench design is now verified,
by an independent reviewer with no stake in the outcome, to read as a
structurally different, more mature CAD/CAE-style product — not the old
RocketForge with a different palette and a collapsible sidebar, and not
asserted so from writing the QML, but confirmed from what the rendered
product actually shows.

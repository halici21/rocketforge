# CAD/CAE Workbench R1 — Structural Recovery Design Thesis

## The decisive finding

Engine Design mode (`ui/engine/EngineWorkspace.qml` and its
`EngineSidebar`/`EngineInspector`/`BottomPanel`) already implements the
exact grammar `RF_WORKBENCH_GRAMMAR.md` §6 describes as the CAD/CAE
target: a semantic Project browser (what exists / what can be added,
switched by segmented control, showing live summaries — "Engine-01 · Gas
generator · LOX/CH4" — not just names), a dominant canvas, a genuinely
contextual Inspector (Architecture/Contents/Performance sections that
change with selection), and a working bottom dock (Problems/Results/
Messages). Captured and inspected directly
(`acceptance/cad_workbench_r1_structural_recovery/before/engine_design_dark_1920x1080.png`):
it looks, immediately, like a different and more serious application than
every Analysis-mode page.

**This recovery's job is not to invent a new shell grammar. It is to
bring Analysis mode up to the grammar Engine Design already proves works
in this codebase**, adapted for the fact that Analysis mode's workspaces
are independent calculators, not nodes in one connected engine graph.

## What the current application visually does wrong

Per the audit (`docs/design/CAD_WORKBENCH_R1_STRUCTURAL_RECOVERY_AUDIT.md`):
no Home; `SideNav` is a page list, not engineering context; every page
(legacy and redesigned alike) shares one skeleton (title/subtitle →
segmented tabs → two bordered `RFPanel`s → footer); two parallel,
inconsistent chart systems with the weaker one in ten production
locations. Full detail there — not restated here.

## What replaces the old page-first composition

**Analysis mode adopts Engine Design's own three-region grammar**, not a
new one:

```
BROWSER  (state-aware engineering context, replaces SideNav's page list)
    |
WORKSPACE  (the object-first content each of the 4 recomposed workspaces
             already builds — schematic/state-block, tiered hero,
             secondary state — now inside a container that reads as a
             workbench view, not a page)
    |
INSPECTOR  (on-demand, contextual — provenance/diagnostics/assumptions
             move here from the bottom-of-panel rows they occupy today)

  +  ANALYSIS DOCK along the bottom (already exists, still real evidence
     space — a workspace's own detail, not its primary result)
```

## What remains persistent vs. contextual

**Persistent** across every Analysis-mode screen: the Browser (content
changes are about state, not identity — closer to Engine Design's
Project panel always being present), the workspace's own object/hero
region container shape, the Analysis Dock frame, the status/provenance
line at the very bottom (`StatusBar`, already shell-global and correctly
so).

**Contextual**, changing per workspace: the object itself (schematic,
state block), the primary-result tier, what the Inspector shows when
opened (a workspace's provenance/diagnostics/assumptions — content that
today sits in a "Provenance" `RFPanel` on every page, competing for the
same visual weight as the primary result, moves here instead so the
primary panel is *only* the object and its hero result).

## What moves to the Analysis Dock

Nothing from the four already-accepted centerpieces moves out of primary
view — Δp/Re/Darcy fD, Tc/Mbar/gamma, rho/h, and Isp/Cf/c* all stay where
`rf-engineering-workbench`'s object-first grammar already puts them, per
the explicit instruction not to re-derive those workspaces' hierarchies.
The Dock's real content going forward is what today has no consistent
home: Thermochemistry's Sweep tab, Line's assumption list (already a
quiet footer, a legitimate Dock citizen), Fluid Properties' diagnostic
rows for the two-phase/refused states, Rocket Performance's Provider
comparison tab. These are genuinely secondary evidence, not primary
results, and today they are jammed into same-weight `RFPanel` siblings
of the primary result — exactly the composition problem the corrective
brief names.

## What becomes the dominant engineering surface

The object + primary-result region, unchanged in *content* from the
four already-accepted centerpieces, but no longer inside a bordered
`RFPanel` competing 1:1 in visual weight with an equally-bordered
"Provenance" panel beside it. Provenance moves to the Inspector (on
demand) or a single quiet trace line (Rocket Performance pilot's own
precedent — "provenance is quietest of all and lives in one line, not a
wall of text," a rule this recovery actually enforces rather than
half-applies).

## How navigation changes

`TopBar`'s Analysis/Engine Design mode switch and theme/nav controls stay
— they are genuinely global app chrome, correctly light already. What
changes is `SideNav`'s content model. It becomes a state-aware Browser:
each domain group still exists (the real domains are real: Compressible
Flow's eight legacy modules, Thermochemistry, Rocket Performance, Trade
Study, Fluid Properties, Line, Engine Design), but each entry gains a
live one-line state summary sourced from that workspace's own controller
— "Thermochemistry — LOX/LCH4 · O/F 3.4 · Solved" instead of bare
"Thermochemistry" — mirroring exactly how `EngineProjectPanel` shows
"Engine-01 / Gas generator · LOX/CH4" under the project name rather than
a bare label. This is the single change that converts the Browser from
"list of pages" to "state of my analyses" without inventing any
capability the app does not have — every summary is formatted from a
`resultChanged`-scoped property the controller already publishes (or a
one-line new property, in the exact spirit of the presentation-plumbing
additions already made for `resultStale`).

## How the Browser differs from navigation

Navigation answers "where can I go." A Browser answers "what is the
state of my work." The distinction is not cosmetic: `EngineSidebar`'s
Project view shows *contents and counts*, not just a route. The Analysis
Browser adopts the same standard — each workspace row shows enough of
its own solved/unsolved/stale state that opening it is confirmation, not
discovery.

## How the Inspector earns its place

Per section 15's own constraint — do not force it into every workspace
permanently — the Inspector opens on demand (already-built
`InspectorDrawer.qml` infrastructure, `ShellContext.inspectorOpen`) and
shows exactly what `EngineInspector`'s own sections model: identity
(which case is this), state (solved/stale/warning), and provenance
(what produced it) — the same three things every one of the four
recomposed workspaces' "Provenance" panels already contain, just moved
off the primary canvas and onto a drawer that does not compete with the
object for space by default.

## How the four accepted workspaces differ while sharing one workbench

Each keeps its own object (nozzle / chamber / pipe / state block) and its
own primary-result tier exactly as accepted. What becomes shared: the
*container* around that object (no longer a bordered `RFPanel` sized
1:1 against a Provenance sibling), the location of secondary/provenance
content (Inspector, not an equal-weight panel), and — where each
workspace has genuine secondary evidence (a sweep, a comparison, a
diagnostic list) — the Dock.

## What shared primitives must change

`RFPanel` (used for the object/result region — moves to a lower-chrome
treatment, border removed where a divider already does the grouping
work, per `rf-engineering-workbench`'s own "ask what a border does that
spacing could not" test); the page-header block (title/subtitle/tabs
triplet — the tab row is retired where a workspace has no genuine
second view, kept only where it does, e.g. Thermochemistry's Sweep,
which becomes a Dock tab instead of a page tab); the chart system
(`RFLineChart` — ten production consumers, the weaker of two parallel
implementations — brought up to `RFPlotSurface`'s frameless discipline
and given real hover/inspection, without touching the physics or the
call sites' data contracts).

## What makes the new visual silhouette unmistakably different

At a glance, a screenshot of any recomposed workspace should show: no
bordered box around the object/result region (spacing and one hairline
divider instead), a Browser row that states the workspace's own current
result rather than only its name, no page-level tab row unless a
genuine second view exists, and a materially lower panel-border count
per screen (Card Reduction Gate, tracked explicitly below).

## How charts change

Converge on one grammar. `RFPlotSurface` gets the redesign work (real
hover/cursor readout with numerical precision, a stronger
selected/current-point treatment using `Theme.accent`, adaptive tick
density rather than a fixed 5/6-line grid) since it is architecturally
the sounder of the two and already has the correct frameless discipline.
`RFLineChart`'s own rendering is brought visually in line with the same
tick/grid/marker treatment (a presentation-only change to its `onPaint`
— no data contract change, so its ten existing call sites need no
changes) rather than migrated wholesale, since rewriting ten legacy
modules' chart wiring is out of this recovery's explicit scope (those
modules were never named for recomposition).

## How tables change

Lower priority per the audit (`RFEngineeringTable` is comparatively
solid, single system, eleven consumers) — a density/contrast pass, not a
rebuild.

## What design patterns are explicitly removed

Page title + bordered content card + form section + result card as the
default template for *every* screen regardless of whether the content
needs a boundary; a segmented tab row on a workspace with only one real
view; a "Provenance" panel sized equally against the primary result;
the assumption that a visual grouping needs a background rectangle
rather than spacing and a divider.

## Sequencing

Home and the Browser semantic upgrade first (highest audit-ranked
leverage, and the Browser change is a prerequisite for every subsequent
workspace recomposition, since all four reuse it). Shared `RFPanel`/
header primitives next. Chart system next (self-contained, testable
against real Trade Study/Thermochemistry sweep data without migrating
either workspace). Recompose the four workspaces into the new grammar
last, since they depend on every layer above.

# Analysis Experience R2 — Navigation

## What was rejected

A permanently visible rail listing every destination in the application:
17 entries at 1920x1080, unchanged whatever the user was doing, including
three routes (Compare, Charts, Gas Properties) that are placeholder
skeletons with no functionality. It was application page navigation, not
an analysis context.

## What replaces it

Two levels, one of which is usually enough.

**The family rail** (64 px, always visible). Seven entries: HOME plus six
analysis families — Compressible Flow, Thermochemistry, Rocket
Performance, Trade Study, Fluids and Feed, Reference. Short uppercase
identifiers here are functioning as compact glyphs in an icon-width
column, which is the one use section 24 of the brief still allows; they
are not section headings.

**The contextual drawer** (176 px, floating). Opens only for a family with
more than one module — in practice Compressible Flow (8 modules, grouped
Fundamentals / Wave systems / Duct flow / Nozzle) and Fluids and Feed
(2 modules). It is a Popup, not a layout participant, so it overlays the
workspace instead of permanently reserving width.

A family with exactly one module — Thermochemistry, Rocket Performance,
Trade Study, Reference — opens that module directly from the rail. There
is no second click into a drawer with one row in it.

## Rules the implementation follows

- The drawer opens **only** from an explicit rail click. An earlier
  revision auto-opened it whenever navigation landed inside a
  drawer-owning family; opening the real capture showed it parked on top
  of the workspace's own input rail every time. Navigation now only ever
  closes it.
- Selecting a module closes the drawer.
- `Navigation.items`, `indexOfKey()` and `pageSource()` are untouched, so
  every existing consumer — Main.qml's page index, WorkspaceState, the
  packaged self-test harnesses — keeps working without modification. The
  families array is additive.

## Placeholder routes

Compare (9), Charts (10) and Gas Properties (12) appear in no family
group and are therefore unreachable from production navigation. Their
QML, their routes and `indexOfKey`/`pageSource` are all unchanged, so a
dev route or test fixture can still open them directly; they are simply
not offered to a user as product features while they remain
`ModulePlaceholderPage` skeletons.

Equation Library is real content, so it stays — under Reference.

## Width

`Metrics.browserPanelWidth` went from 240 to 64, with the resizable range
narrowed to 64–200. The workspace gets that width back on every screen.

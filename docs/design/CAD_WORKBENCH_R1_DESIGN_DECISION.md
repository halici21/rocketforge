# CAD/CAE Workbench R1 — shell prototype decision

All three prototypes are real, working QML — `ui/_prototypes/{ProtoA,ProtoB,
ProtoC,ProtoBrowser,ProtoInspector,ProtoDock}.qml`, temporary, to be deleted
once a winner is picked (brief §27), not left in the app tree. Each loads
the actual application (real `Isentropic` and `RocketPerformance`
controllers, real `Navigation` data), captured headlessly, `0` Qt warnings
across all three. Every prototype uses the **same** palette — the
Obsidian/Champagne values are in `ui/theme/Theme.qml`'s `darkPalette` for
the duration of this comparison (temporary; see the comment marking that
block), so nothing here is biased by one prototype getting better colour
than another.

Evidence: `acceptance/cad_workbench_r1/shell_prototype_{a,b,c}/` — 4
captures each (1920×1080, 1366×768, 2560×1440 default; 1920×1080 navigated
to Rocket Performance), `capture_report.json` per prototype.

## Scope of this comparison

Framed per the current-UI audit's finding and the user's own choice of
framing: **not** "invent a shell," but "how far should Analysis mode's
calculator pages move toward the Model Browser / Viewport / Inspector /
Dock grammar Engine Design already has." Built against one representative
page (Isentropic Flow, the actual default landing page) plus a navigation
check against a second real page (Rocket Performance), not a full 14-page
rebuild — consistent with `rf-visual-qa`'s "one workspace at a time"
discipline; a full per-page rollout is the later migration phase (brief
§86-88), not this one.

## What each prototype actually is

**A — Minimal CAD.** Unmodified current shell (`TopBar` + `SideNav` +
`WorkspaceHost` + `StatusBar`) with only the palette changed. No Browser,
no Inspector, no Dock added. The page is exactly as wide as it is today.

**B — CAE Dense.** `TopBar` + a new grouped Model Browser (`ProtoBrowser`,
`dense: true`, `projectPanelWidth` = 264px — Engine Design's own left-panel
width) driven by the same `Navigation` data `SideNav` already uses, with a
status dot per row reflecting the real `computed` flag + a persistent
contextual `Inspector` on the right (`inspectorWidth` = 324px) showing
live controller state when Isentropic is selected. Center content
compressed to whatever remains — on 1920px that's roughly 1330px, on
1366px roughly 780px.

**C — RocketForge Hybrid.** `TopBar` + a slim collapsible Browser rail
(200px, narrower row metrics, same real data) + the page kept as wide as
prototype A's + a collapsible bottom Analysis Dock (`ProtoDock`,
Provenance/Messages tabs, Provenance showing `Isentropic.assumptions` — the
real physics-registry standing-assumption strings, not invented copy) below
the workspace instead of beside it.

## What the captures actually showed

**1920×1080 and 2560×1440: all three render cleanly**, 0 Qt warnings,
correct real data throughout (B's Inspector genuinely updates from
"Calorically perfect gas / γ 1.400 / Mach 2.0000 / Valid" to "RocketForge
ideal rocket model / Computed by RocketForge from a provider chamber state"
with no Solved State section, correctly, when navigated to Rocket
Performance — the context-sensitivity claim is real, not asserted).

**1366×768: A is clean. B and C are not** — inspected directly, not
inferred:

- **B**: the Reference Check panel's PASS badges and trailing digits are
  cut off at the right edge (`protob_default_1366x768.png`). Root cause:
  compressing the center column to ~780px to make room for both a 264px
  Browser and a 324px Inspector leaves less width than
  `IsentropicCalculator`'s internal Reference Check row layout was ever
  tuned for. This is real evidence, not a hypothetical — B's chrome
  measurably costs horizontal room the existing page content does not yet
  absorb.
- **C**: the Reference Check panel overlaps the Results panel above it
  (`protoc_default_1366x768.png`). Root cause: the fixed-height
  `ProtoDock` (190px) subtracts from the page's *vertical* space without
  the page's own internal layout adapting, so two panels that used to
  stack cleanly (and still do in A) now collide.

Per brief §25, an accessibility/layout blocker like this cannot be waved
through by a prototype "winning" anyway — but the correct reading of this
evidence is narrower than "B and C are broken": **both defects come from
dropping an unmodified page into a differently-shaped box**, which is
exactly what the later per-workspace migration phase exists to fix
properly (adapting the page, not shrinking it blindly). It is real
evidence about *cost*, not a disqualification of either composition — A
pays no such cost because it changes nothing about the page's available
space.

**Solve-call behavior**: none of the three added chrome (`ProtoBrowser`,
`ProtoInspector`, `ProtoDock`) calls any controller method — they only read
existing properties (`Isentropic.gamma`, `.mach`, `.valid`, `.stale`,
`.assumptions`, `.modelName`). No new solve path was introduced by any
prototype. This is a property of what was built, confirmed by reading the
three new files, not separately instrumented with a solve counter — full
solve-call parity instrumentation is scoped to the winning prototype's
real implementation (brief §90).

## Scoring (brief §76)

| Dimension | A — Minimal CAD | B — CAE Dense | C — RocketForge Hybrid |
| --- | --- | --- | --- |
| Visual calm | High — nothing added | Lower — two new persistent panels compete with the object | High |
| CAD/CAE familiarity | Low — no tree/inspector grammar at all | High — closest literal match to Engine Design | Medium — browser present, inspector deliberately deferred to each page's own result rail |
| Engineering/propulsion identity | Unchanged from today | Strongest structurally, but the Inspector's real content (a γ and a Mach number) is currently thin next to its persistent width cost | Medium-high |
| Viewport dominance | Highest — 100% of today's width | Lowest — center column shrinks by ~588px combined at 1080p | High — only a 200px rail taken, recoverable by collapsing it |
| Information density | Lowest | Highest | Medium |
| Chart/table behavior | Unaffected | Unaffected at 1080p; **broken at 1366×768** (measured) | Unaffected at 1080p; **broken at 1366×768** (measured) |
| Model Browser utility | None — no browser exists | High — full real navigation tree, denser rows, status dots | Medium — same tree, slimmer rows, collapsible |
| Inspector utility | None | Real but currently thin (2 fields for Isentropic, 0 for most other modules in this spike) | None by design — deferred to each page's own result rail (the accepted Rocket Performance pilot pattern) |
| Analysis Dock behavior | None | None | Real: Provenance tab shows genuine physics-registry assumption strings; collapses to a 34px strip |
| 1366×768 usability | **Only one that passed unmodified** | **Failed as built** (real defect, explained above, fixable in the workspace-migration phase) | **Failed as built** (real defect, explained above, fixable in the workspace-migration phase) |
| Light theme | Not captured this pass (dark only, see Known limitations) | Not captured this pass | Not captured this pass |
| Accessibility | No new interactive chrome to audit | New Browser rows and Inspector need a keyboard/focus pass before shipping (not yet done) | New Browser rail and Dock tabs need a keyboard/focus pass before shipping (not yet done) |
| Maintainability | Simplest — no new components | Two new components, moderate | Three new components (rail variant, dock, tab state), moderate-high |
| QML lifecycle risk | None — no new bindings | Low — Inspector rebinds cleanly on navigation, confirmed in the Rocket Performance capture | Low — Dock content rebinds on navigation the same way |
| Future scalability (valve/orifice/feed workspaces) | Weak — a flat nav does not scale past ~20 pages any better today than it does now | Strong — the tree already groups by domain and the pattern is proven at 60-row density in Engine Design | Medium-strong — same tree, and the Dock generalizes naturally to per-workspace Trace/Provenance/Diagnostics tabs the way Engine Design's BottomPanel already does |

## Decision

**C — RocketForge Hybrid.**

Reasoning, not just the table: `rf-engineering-workbench`'s own rule is
that a workspace's centerpiece is specific to its own physics and should
not be diluted by chrome uniformity — the accepted Rocket Performance
pilot already proved a three-zone, no-persistent-Inspector composition
satisfies the object-first grammar. B's persistent Inspector duplicates
work that pilot already deliberately avoided, permanently taxes viewport
width to do it, and today has genuinely little to show for it outside
Isentropic (the "Solved State" section is honestly empty for every other
module in this spike, because wiring 13 more controllers into a shared
Inspector is real, later work, not a shell-composition question). C keeps
A's viewport dominance (the audit's top priority per brief §35), adds the
Model Browser's real, measured scalability benefit (the actual reason this
whole program exists — Engine Design already proved the pattern works
at higher density than Analysis mode's own flat list), and keeps the
Inspector question open rather than forcing it — a page may still grow a
contextual Inspector later if a specific workspace's own audit calls for
one, the same way each workspace's centerpiece is decided per-workspace,
not by shell mandate.

The 1366×768 defect is real and must be fixed as part of C's actual
implementation (not waved through) — but it is a *page-adaptation* problem
identical in kind to what the accepted Rocket Performance pilot already
solved once for its own workspace, not evidence against the Browser+Dock
composition itself. A's clean 1366×768 result is a property of changing
nothing, not evidence that C's composition cannot also be made to pass —
that is exactly what the per-workspace migration gate (brief §86-88) exists
to prove workspace by workspace before any of them ship.

## What this decision does NOT settle yet

* Whether any individual workspace's audit later concludes it needs its
  own contextual Inspector after all (per-workspace decision, not
  foreclosed by this one).
* The exact Analysis Dock tab set per workspace beyond Provenance/Messages.
* Light theme for the Obsidian/Champagne palette — not derived or captured
  in this pass; must be a deliberate design (brief's own instruction, not
  an inversion of dark) before any workspace migration captures a light
  state.
* The muted-text contrast blocker found in the current-UI audit is
  **already fixed** in the values used for this comparison (validated in
  `contrast_audit.py`'s derivation) but has not been re-run against the
  *new* palette's own token set with the same script — follow-up item
  before this palette is treated as final.
* Accessibility pass (keyboard/focus) on `ProtoBrowser`'s rail and
  `ProtoDock`'s tabs — not yet done; blocking before real implementation
  per brief §25.

## Known limitations of this comparison pass

* Dark theme only. Light theme intentionally deferred (see above).
* One representative page (Isentropic Flow) plus one navigation check
  (Rocket Performance), not all 14 Analysis pages.
* No memory soak run against the three prototypes specifically (the
  underlying QML memory question is already closed per the checkpoint;
  a targeted 100-cycle navigation soak against C's actual implementation
  belongs to that implementation's own gate, brief §92).
* No 2560×1440 defect inspection beyond confirming captures exist and load
  without warnings — only 1920×1080 and 1366×768 images were manually
  opened and inspected pixel-by-pixel in this pass.

## Next step

Per brief step 27: remove the two rejected prototype paths (A and B's
prototype files) once this decision is reviewed, then implement C for real
against the accepted per-workspace migration order (Rocket Performance
first, brief §86), fixing the 1366×768 page-adaptation defect as part of
that implementation rather than deferring it further.

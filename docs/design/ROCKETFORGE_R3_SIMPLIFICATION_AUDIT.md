# RocketForge R3 — Simplification, Clean Code and Performance Audit

Audit only (Phase 0). No production code, QML, theme, test or packaging file was changed.

- Baseline: `bd55966` (master), branch `claude/r3-simplification`.
- UI evidence: all 30 analysis pages plus Engine Design, captured from the running application
  (offscreen, 1920×1080, dark theme, CEA environment), each opened at full resolution. 0 Qt warnings.
- Code evidence: AST metrics over `rocketforge/`, duplicate-window scans over Python and QML, an
  import-time profile, page-switch timings and a test-duration profile.

Every change proposed below is behaviour-preserving or removes something that is not a feature.
Nothing changes a solved number, a scientific label or an evidence record.

## The one-sentence finding

**The compressible-flow modules are coherent; the ten design-chain pages and three placeholder
pages are where the product feels heavy, and the Python/QML duplication sits almost entirely in
seven sibling compressible-flow modules.**

## Part A — UI/UX

The R2 audit's main finding (the product opened on its worst surfaces) has been addressed: Isentropic,
Mass Flow, Normal Shock, Prandtl–Meyer, Fanno, Rayleigh and Nozzle Lab now open on their visual surface.
What remains is ranked by impact on a first-time user.

| # | Finding | Where | Proposed simplification | Risk |
|---|---|---|---|---|
| U1 | **Three placeholder pages ship in the navigation.** Compare, Charts and Gas Properties show "Module UI will be implemented in a later phase", empty dashed boxes, and a status bar reading "No solver in this build · All values are mock data". | FLOW family, REF family | Remove them from `Navigation.items` (keep the files or delete them, owner's choice). The status bar then never says "mock data" anywhere in a shipped build. | Low; navigation tests and the nav smoke list need their keys removed. |
| U2 | **The design chain is ten separate pages, each opening empty.** Engine Requirement → Propellant Trade → Thrust Chamber Sizing → Chamber Geometry → Injector; Propellant Inventory → Tank Geometry → Propellant Management → Tank Pressurization → Feed Network. Each downstream page opens on "Not computed yet" and an orange sentence naming the upstream page, which is not a link. | ENG, SYS families | (a) Make the upstream sentence a button that navigates there. (b) Add one compact chain strip at the top of every chain page: the steps, each with its state (not run / done / stale), clickable. No page is merged, no solve is automated. | Low for (a); medium for (b) (new shared component, read-only over existing controller state). |
| U3 | **Empty right-hand provenance column.** On the chain pages and Fluid Properties/Line, a 20–25 % wide column says "Shown with a result…" and is otherwise empty until a solve. | 12 pages | Collapse the column while there is no result and let the input card use the width; show it with the result. | Low–medium (layout only; test the 1366×768 layout). |
| U4 | **Wording density.** Most cards carry two or three hedging sentences ("Nothing is computed until you do", "Nothing is solved until you do", "Shown with a result: …"), the header carries two chips that restate the subtitle, and the status bar restates both. | all pages | One empty-state sentence per card; keep the scientific scope chip, drop sentences that only repeat it. Scientific caveats (ideal, no efficiency, not a cycle) stay — those are the product's discipline, not noise. | Low, but text is pinned by tests; each removal is checked against `rf-scientific-ui-contract`. |
| U5 | **Raw SI inputs in pascals.** Fluid Properties takes `300000` Pa and Line `1000000` Pa, while Thermochemistry offers an MPa/bar selector. | Fluid Properties, Line | Reuse the existing pressure-unit selector; storage stays SI. | Low–medium (unit conversion at the input boundary only; parity test on solved values). |
| U6 | **Inconsistent first tab.** Every compressible page opens on Relation except Oblique Shock (Calculator) and Nozzle Lab (Regime map). | FLOW | Decide one rule, or document why these two differ (Oblique Shock has no single relation curve). | Owner decision. |
| U7 | **Two evidence browsers.** "Propulsion Database" (solid-propellant evidence) and "Reference Engines" (liquid engines) are separate REF items with near-identical inspectors (26 shared 10-line blocks). | REF | Keep two pages (different records) but share the inspector component. | Low (code), see C3. |
| U8 | **Home is a bare list.** Eight family names and one-line descriptions on an otherwise empty 1920 px page; "Propulsion System" has no description. | Home | Add the missing description; optionally show each family's last-solved state. | Low. |
| U9 | **First-visit page switch lag.** Fluid Properties ≈ 1.8 s and Thermochemistry ≈ 1.6 s on first visit (provider import), Isentropic ≈ 0.9 s (timings net of the 0.4 s capture settle). | — | Pre-import the providers on a background thread after the window is shown. | Low–medium; measure before/after. |

## Part B — Clean code and duplication

| # | Finding | Evidence | Proposed change | Risk |
|---|---|---|---|---|
| C1 | **Qt property boilerplate in the compressible controllers.** 109 hand-written `_get_x`/`_set_x`/`Property` triples (≈ 11 lines each) across seven controllers; the seven files total 5,037 lines and are the top seven Python files in the duplicate scan. | `fanno_controller.py` 19 setters, `rayleigh` 18, `mass_flow` 17, … | One small helper (`input_property(attr, type, notify, recalc=True)`) in `application/`, applied controller by controller. Public QML names, types and notify signals unchanged. | Medium: verified by the controller tests, `test_line_architecture.py`, the UI/nav smoke and a property-surface snapshot (every name, type and notify before = after). |
| C2 | **QML duplication between sibling Calculator/Table pages.** Isentropic/Normal Shock calculators share 40 ten-line blocks; Isentropic/Normal Shock/Prandtl–Meyer tables 33; Fanno/Rayleigh tables 24; Fanno/PM/Rayleigh calculators 16. | `ui/pages/*` (104 page files, 28,558 lines) | Extract the shared table frame and the shared "solved state" readout block into `ui/components/`. Pages keep their own content. | Medium: pixel/field parity per page (the visual-pilot method). |
| C3 | **Evidence inspectors duplicated.** `EngineInspector.qml` / `EvidenceInspector.qml` share 26 blocks. | `ui/pages/referenceengines`, `propulsionevidence` | One shared inspector component. | Low. |
| C4 | **Dead QML.** `ui/visuals/MockScientificPlot.qml` and `ui/visuals/NozzleVisualization.qml` are referenced by nothing. `MockData` feeds only the placeholder pages and the status bar's mock-data text. | grep over `ui/`, `rocketforge/`, `main.py`, `tests/` | Delete the two files; after U1, reduce `MockData` to what is still read. | Low. |
| C5 | **Long functions are mostly justified.** 31 of 3,774 functions exceed 100 lines; the longest are the smoke runners (`perfsmoke`, `studysmoke`, `uismoke`, `navsmoke`, `shellsmoke`, 160–265 lines of scripted steps) and numerically dense solvers (`brent`, `nozzle.solve`, `reduce_chamber_gas`). | AST scan | Leave the solvers alone (frozen, verified). Split the smoke runners into named steps only if they are touched anyway. | — |
| C6 | **No dead Python modules.** Every module is imported; four are used only by tests by design (DB-4A review gate, solid reports, burn-law evaluation, performance reference). | import scan | None. | — |

## Part C — Performance

| Measure | Value | Note |
|---|---|---|
| `import main` | 0.63 s | numpy 0.11 s, PySide6 0.09 s; nothing to gain. |
| `build_engine()` | 0.70 s | All controllers constructed eagerly. |
| `build_engine()` + `Main.qml` load | 4.07 s | Offscreen; QML compilation dominates. |
| Page switch, first visit | 0.4–1.8 s net | One page at a time through a `Loader`; provider imports dominate the slow ones (U9). |
| Base test suite | ≈ 9.7 min | 9,470 passed, 448 skipped at `bd55966`; slowest tests below. |

Slowest tests (a clean run; the times are the module fixtures that start a real application process):

| Test | Time | What it is |
|---|---|---|
| `test_propulsion_system_runtime.py` fixture | 39 s | one subprocess instrument run for five pages |
| `test_shock_workspaces.py::…automation[normalshock]` | 36 s | subprocess UI walk |
| `test_reference_engines_runtime.py` fixture | 35 s | subprocess instrument run |
| `test_visual_polish.py::test_a_quick_pass_does_not_peek` | 33 s | timed UI pass |
| `test_shell_navigation_smoke.py` (all routes) | ≈ 110 s | one subprocess per route |
| `test_theme_repaint.py` | 28 s | theme switch with repaint |
| eight other `*_runtime.py` fixtures | 10–25 s each | one subprocess each |

About a third of the suite's wall time is these subprocess runs. The other ≈ 9,400 tests take well
under a second each.

Environment note: two runs in this audit failed with a negative subprocess timeout (−3,599 s and
−420 s). The machine slept during the run; `subprocess` measures its timeout on a clock that keeps
counting through sleep, so the child appeared to overrun. Each affected file passes on its own. Long
runs must be made with sleep disabled; this is not a code defect.

Candidate optimisations, each to be measured before and after, never assumed:

- P1 — background pre-import of the CEA and CoolProp providers after first paint (U9).
- P2 — QML cache: confirm the packaged build ships compiled QML (`qmlcachegen`) so the 3.4 s load is
  a source-run cost only; measure the packaged start.
- P3 — test-suite time: the slowest tests are subprocess smoke runs; group them or reuse one
  application process where the test's isolation does not depend on a fresh process.

## Proposed phases

Each phase is one commit series, Base suite green, `git diff --check` clean, and an independent review.

1. **R3-A (low risk, visible):** U1 remove placeholder pages, C4 dead QML, U2(a) upstream links, U8 Home.
2. **R3-B (layout):** U3 collapse empty provenance column, U4 wording pass, U5 pressure units.
3. **R3-C (code):** C1 property helper, controller by controller, with a property-surface snapshot test.
4. **R3-D (QML components):** C2/C3 shared table, readout and inspector components, with per-page parity.
5. **R3-E (performance):** P1–P3, each with before/after numbers.
6. **R3-F (optional):** U2(b) chain strip.

## Owner decisions needed

- U1: delete the placeholder page files, or keep them out of navigation for a later phase?
- U6: one first-tab rule for every compressible page, or keep Oblique Shock and Nozzle Lab as they are?
- U4: approve the wording rule (one empty-state sentence per card; scientific scope chips stay).

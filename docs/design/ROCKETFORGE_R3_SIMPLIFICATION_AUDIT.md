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
| U1 | **Three placeholder pages ship in the page list.** Compare, Charts and Gas Properties show "Module UI will be implemented in a later phase", empty dashed boxes, and a status bar reading "No solver in this build · All values are mock data". (Correction during R3-A: the family rail already omits them; they are reached with the rail's Up/Down keys, which step through every page.) The Equation Library also showed the mock status chips. | `Navigation.items` | Remove them from `Navigation.items` (keep the files or delete them, owner's choice). The status bar then never says "mock data" anywhere in a shipped build. | Low; navigation tests and the nav smoke list need their keys removed. |
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

## R3-A — done

- **U1:** Compare, Charts and Gas Properties and their shared `ModulePlaceholderPage.qml` are deleted
  and gone from `Navigation.items`. The Equation Library, which solves nothing, carries its own
  status-bar notes ("Reference relations") instead of the mock chips. No status bar text says "mock data" any more.
- **Navigation:** family members are named by key and resolved with `Navigation.keys()`, so removing
  a page moved no family. The unread per-domain row lists (`flowRows` … `engineItems`) are deleted.
- **C4:** `MockScientificPlot.qml`, `NozzleVisualization.qml` and `MockLineSeries.qml` (read only by
  the other two) are deleted, so `ui/visuals/` is gone. `MockData.qml` keeps only
  what is still read: the Engine Design nozzle outline and the equation text.
- **U2(a):** a new `RFIssueLine` shows an issue and, when the issue names an unsolved upstream page,
  a quiet "Open <page>" button. It covers the four Liquid Engine pages that have an upstream page (Propellant
  Trade, Thrust Chamber Sizing, Chamber Geometry, Injector, through their own Repeaters) and the five
  Propulsion System pages (through `RFSystemWorkspace`). The map covers a missing, stale, refused or
  mismatched upstream result; in every case the fix is on that page. The map from issue code to page
  is `Navigation.upstreamPageOfIssue`. `tests/application/test_issue_links.py` pins the reviewed map; checks that the
  backend message names the page the map opens; checks that every message that sends the person to
  another page, and every upstream-result code, has a link; and, in the running application, checks
  that each link opens its page, once, and solves nothing. Specs that describe the removed pages are
  history and are not rewritten; the route table in `docs/engineering/07_ui_integration_contracts.md`
  marks them removed.
- **U6:** Oblique Shock opens on Relation (the θ–β–M study), then Calculator, then Table, like every
  other compressible page.
- **U8:** Home describes all eight families.

Noted for R3-B: the status bar's trailing dot always shows in the warning colour, on every page, so it
carries no state.

## R3-B — done

- **U3:** a side panel with nothing to show before a result is hidden until it has something (a
  result, or an advisory), and the input card takes the width. On Thrust Chamber Sizing, Chamber
  Geometry, Injector and the five Propulsion System pages (through `RFSystemWorkspace`) the panel held
  only "Shown with a result: …", and those four sentences, which can no longer be seen, are deleted. On
  Fluid Properties and Line it was an empty titled panel. (The Phase 0 table, row U3, described all of
  them as holding the sentence; only the first group did.) On Fluid Properties a refused outcome's
  diagnostic rows now sit only in the page's empty state, which already shows the same text. Propellant Trade's side panel holds the selection control before a
  result and stays.
- **U4:** "Nothing is computed / solved / evaluated until you do" is deleted from nine empty states;
  each repeated the instruction just before it ("then press Compute"). "Nothing is chosen for you" stays:
  it says that no candidate is picked automatically. Scope chips and model caveats are untouched.
- **Status bar:** the trailing dot, always in the warning colour and so carrying no state, is removed.
- **U5:** Fluid Properties and Line take their pressure in Pa, bar or MPa. One table
  (`application/analysis/pressure_units.py`) now serves these and Thermochemistry. The case keeps
  pascals; `pressureDisplay`/`setPressureDisplay` convert at the boundary, so QML does no arithmetic.
  A unit change re-renders the field only: no evaluation, no staleness
  (`tests/application/test_pressure_units.py`). The default stays Pa. Results keep the service's own
  units. The field's step comes from the unit table, so in Pa it is now 1e5 Pa (it was 1e4 on Fluid
  Properties and 5e4 on Line).
- **Review fix:** a unit switch moved the field's value before its decimals, so 0.35 MPa read "0" and the
  next step wrote a wrong pressure (Thermochemistry had the same defect). `RFBoundNumberField` now
  re-renders, without emitting an edit, whenever its decimals change; a QML-level test switches units
  in both orders and checks the text and that no edit is emitted.
- **Confirmation-review fix:** `RFNumberField.nudge()` wrote a step at the base default of 3 decimals,
  whatever the field showed, so an MPa step landed on a 1 kPa grid. A new `stepDecimals` (default:
  `decimals`, so plain fields are unchanged) is bound to the field's own precision in
  `RFBoundNumberField`; the same test steps 0.4321 MPa to 0.5321. This applies to every bound field: a
  step is now written at the precision the field displays.

## R3-C — done

Correction to C1: the seven controllers hold **103** hand-written setter triples, not 109 (the count
included six setters in other controllers).

- **Helper:** `rocketforge/application/analysis/stored_property.py`, one function. It returns the
  `Property` the hand-written triple built: convert, return if the value is already held, store,
  emit the notify signal, and `_recalculate()` only when asked. It is built at class-definition time,
  with no registry, metaclass or later mutation. Its getter and setter are named after the attribute
  (`get_gamma`) so a traceback says which property it was.
- **Replaced: 73 of 103.** Isentropic 3, Mass Flow 15, Normal Shock 10, Oblique Shock 9,
  Prandtl–Meyer 8, Fanno 14, Rayleigh 14. They come from one script that matched each setter body
  exactly against the accepted shapes. Seven of those shapes cover the inputs and the
  `_set_table_setting` table settings, which turned out to be the same pattern without the
  recalculation; one covers the readout precision (`coerce=clamp_precision`).
- **Kept by hand: 30**, because their setters do something else:
  - the five `mode` setters reset the input to the new mode's default;
  - `tablePrecision` updates the table model;
  - `compareEnabled` refreshes a summary;
  - Oblique Shock's `mach1`, `gamma` and `branch` also emit `curveChanged`;
  - the Prandtl–Meyer expansion inputs recompute the expansion;
  - Fanno's convention converts the friction factor;
  - the segment and heat toggles drop an outcome;
  - Fanno and Rayleigh `precision` emit two signals;
  - Isentropic `inputValue` and `gamma` compare the raw value before converting it. These two stay
    exact rather than being folded in.
- **Cleanup:** `AnalysisBehaviour._set_table_setting` had no caller left and is deleted. The two
  precision setters in the base use the same `clamp_precision`.
- **Proof:**
  - `tests/application/test_compressible_property_surface.py` compares every one of 372 properties
    (name, Qt type, read/write, notify signature or constant, and the uniform flags) and all 155
    signal and slot signatures against a literal captured at 3ec5f0f before any edit.
  - `tests/application/test_stored_property.py` checks the helper alone, and then that each of the
    73 built properties reads its own attribute, leaves its controller's other helper-built
    properties alone, notifies on its own signal, and is silent on a repeat value. Each property's
    `recalculate` choice is pinned by the existing controller tests, not by this file; the review
    checked every one against the pre-refactor setter.
  - Five deliberately broken helpers and one renamed property each fail these tests:
    1. a late-bound attribute;
    2. one shared signal;
    3. a float that becomes a QVariant;
    4. a missing notify signal;
    5. a read-only property.
  - A behaviour trace, kept outside the repo, records every readable value and every signal count
    after each of 289 writes on the seven controllers. It is byte-for-byte identical before and after.
  - The seven pages are pixel-identical before and after.
- **Not changed:** QML, physics, services, providers, tolerances.

## Owner decisions (2026-10-12)

- U1: **remove the placeholder pages from navigation and delete their files.** They stay in git history
  and return only as real modules.
- U6: **one rule for every compressible page**: each opens on its visual relation surface.
- U4: **wording rule approved**: one empty-state sentence per card; sentences that only repeat a chip,
  the subtitle or the status bar go; scientific scope chips and caveats (ideal, no efficiency, not a
  cycle) stay. Each removal is checked against `rf-scientific-ui-contract`.

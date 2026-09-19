# CAD/CAE Workbench R1 — Consolidated Known Limitations

Written at global closeout, section 44. Consolidates every limitation
carried across the six workspace phases and this closeout's own findings
into one place, rather than leaving them scattered across phase reports.
Nothing here is hidden inside an old phase document only.

## Scientific / physics scope

* **Engine Design has zero component physics.** All 16 registered component
  types are `PRESENTATION_ONLY` or `NOT_IMPLEMENTED`
  (`acceptance/cad_workbench_r1/engine_component_inventory.json`). The
  topology-editing layer (`EngineModel.qml`) is real; nothing past it is.
  See the README's own "Known limitations" section for the full detail.
* **No dense 20-40 component topology stress case exists.** The demo engine
  is 7 components. The canvas architecture (registry-driven nodes, orthogonal
  routing) has no known scaling defect, but a genuinely dense topology has
  never been built and captured.
* **Qt Quick 3D is unavailable in this runtime**, confirmed by direct import
  test (`import QtQuick3D` fails; `PySide6.QtQuick3D` is not importable).
  Engine Design's viewport decision (2D, confirmed via a real 2.5D spike and
  independent blind review) is not revisited by this closeout. Any future 3D
  viewport work needs a new dependency and its own packaging validation.
* **Thermochemistry's corrected reactant-enthalpy-coupling mode is a tested
  backend capability with no UI control.** `ReactantEnthalpyPolicy.
  FLUID_SENSIBLE_CORRECTION` is real and tested
  (`tests/providers/cea/test_reactant_enthalpy_coupling.py`), but neither
  `thermochemistry_controller.py` nor `thermochemistry_service.py` exposes
  it — `solve_chamber()` is always called with the default (native) policy.
  Classified `TESTED BACKEND / UI STATE NOT DIRECTLY REACHABLE`, not a
  screenshot gap.
* **Trade Study's dense-column Pareto rendering has a known legibility and
  memory-footprint limit** at very high point counts (documented, not fixed,
  per `rf-scientific-visualization`'s warning against one-QML-Item-per-point
  architectures at scale). Reproduced this closeout at 16,400 points: no
  crash, 0 Qt warnings, RSS plateaus in the low gigabytes rather than
  climbing unbounded, but this is a real cost a redesign would need to
  address before going further past this scale.

## Architecture / technical debt

* **QVariantList result publication** in Thermochemistry, Line, and Fluid
  Properties (not Trade Study, which already uses a real row model for its
  large table). Documented with a required migration gate at
  `docs/engineering/architecture/POST_R1_RESULT_MODEL_TECH_DEBT.md`. No
  measured cost today; not migrated during R1.
* **The Inspector drawer does not participate in main-content layout.** It
  is a floating overlay, not a `SplitView` column — a toolbar element pushed
  to the trailing edge of a workspace's own content width (via a
  `Layout.fillWidth` spacer) can end up geometrically underneath the
  Inspector when it's open. Found and fixed for the two places this
  closeout added or touched such an element (Trade Study's stale-state chip
  in `StudyTrade.qml` and `StudyResults.qml`, both now left-aligned instead
  of trailing) — not audited exhaustively across every other workspace's
  toolbar, since that would be a broad UI audit beyond this closeout's scope.
  Worth a dedicated pass if a future toolbar element is added at the
  trailing edge of any workspace's own RowLayout.

## Product shape (acknowledged, not a defect)

* **Analysis and Engine Design are two separate object models sharing one
  shell**, not one unified engineering object with two views. An
  independent design review (this closeout) noted the seam: Analysis
  workspaces never reference the actual Engine Design project by name.
  This was never in scope for R1's own migration order and is a legitimate
  direction for a future program, not a regression.
* **Fluid Properties has no schematic drawing**, unlike every other
  Analysis workspace. This is consistent with `rf-propulsion-visual-grammar`'s
  own per-workspace object table, which defines Fluid Properties' object as
  "fluid identity + (T, p) -> state -> properties" with no schematic
  entitlement unless the provider returns real sampled phase-boundary data
  (CoolProp does not, by default) — an intentional grammar decision from
  that workspace's own accepted phase, not an oversight found this closeout.
* **The left Browser rail is instantiated differently between Analysis and
  Engine Design modes** (a shared equation-library-style tree vs. Engine
  Design's own subsystem-grouped project tree), because the two modes'
  content is genuinely different in kind. Flagged by the independent design
  review as the weakest shared primitive; acknowledged as a legitimate
  critique of the current product shape rather than a bug.

## Licensing

* **Sunumatik** (`github.com/ayberkdt/sunumatik`), used as a read-only design
  reference for the Obsidian/Champagne palette during Structural Recovery,
  is a public repository with **no declared license** (`license: null` via
  the GitHub API, no `LICENSE` file at the repo root). Only hex values and
  discipline principles were re-typed into RocketForge's own `Theme.qml`;
  no file, script, or asset from that repository was copied into this
  project. Flagged for the maintainer's own judgment, not resolved
  unilaterally — carried forward unchanged from the phase that first found
  it.

## Tooling

* **`qmllint` is not available in this development environment** (confirmed
  absent from PATH and from the Qt host tools directory this session).
  `qt-qml-review`'s Python-only lint script and Phase 1 checklist ran in its
  place throughout the program.

## Non-blocking, pre-existing lint findings

Running the project's own QML linter (`qt-qml-review`'s
`qt_qml_lint.py`) against every file this closeout phase touched or added
surfaces the same categories of style finding (`ORD-1` property ordering,
`IMP-2` versioned imports, `STY-1` missing `id: root`, `JS-1`/`JS-2`
var/loose-equality) that the same linter reports against essentially any
file in this codebase — these are systemic, established authoring
conventions this project has used consistently since before R1 began (for
example, `Layout.*` attached properties placed immediately after a
component's opening brace, ahead of its other properties, is the
codebase's own consistent pattern, not a violation of it), not regressions
introduced by this program. Bulk-reformatting the codebase to match a
generic linter default is a broad refactor explicitly out of scope for a
closeout phase; noted here rather than silently suppressed.

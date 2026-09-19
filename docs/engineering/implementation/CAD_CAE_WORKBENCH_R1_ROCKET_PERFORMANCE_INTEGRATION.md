# CAD/CAE Workbench R1 — Rocket Performance shell integration

Rocket Performance is the first (and, per the migration order, only)
workspace integrated into the new production shell this pass. Its own page
component (`ui/pages/rocketperformance/PerfCalculator.qml`,
`RocketPerformancePage.qml`) was **not modified** — it was reached through
the new shell exactly the way it was reached through the old one
(`Navigation` → `WorkspaceHost` → `Loader`), so "integration" here means
the shell around it changed, not the workspace itself.

## What changed around it

* A slim, collapsible, resizable Model Browser rail (`SideNav`, unmodified,
  now wrapped in `CollapsiblePanel`/`PanelRail`/`SplitView` — reused
  directly from `ui/engine/`, not duplicated) replaces the old fixed-width
  collapse.
* A collapsible, resizable Analysis Dock (`ui/shell/AnalysisDock.qml`, new)
  sits along the bottom, collapsed by default.
* An on-demand Inspector drawer (`ui/shell/InspectorDrawer.qml`, new,
  Loader-instantiated) is available shell infrastructure, not opened by
  this workspace — its own result rail already carries that role (design
  decision, see `CAD_WORKBENCH_R1_DESIGN_DECISION.md`).
* The Obsidian/Champagne palette (`ui/theme/Theme.qml`, both dark and
  light) replaces Graphite/Ember everywhere, through the existing semantic
  token layer — no page touched a color literal.

## Preservation of the accepted pilot — verified, not assumed

Re-ran the pilot's own capture/parity tooling rather than inventing a new
method (`experiments/ui_visual_pilot/capture_matrix.py`, labelled
`after_r1_shell`; comparison script adapted as
`experiments/cad_workbench_r1/rocket_performance_parity.py` so the
original pilot's own `acceptance/ui_visual_pilot/scientific_parity.json`
is never overwritten):

| Check | Result |
| --- | --- |
| Captures | 27 (2560×1440 / 1920×1080 / 1366×768, dark + light, every pilot state: empty, normalized/scaled/ambient vacuum, all three pressure-thrust signs, stale, invalid, model trace) |
| Fields compared | 5688 |
| Differences | **0** |
| Total provider solves | 1 → 1 (unchanged) |
| Chemistry solves per interaction | epsilon 0, ambient 0, scaleValue 0, view/theme/resize 0 — identical to the original pilot's own requirement |
| Qt warnings | 0 → 0 |
| **Verdict** | **PASS** |

Manually opened and inspected (not inferred) `scaled_vacuum_2560x1440.png`
and `stale_1920x1080.png`: Isp-led hierarchy intact (348.658s, largest,
first), c*/Cf/c_eff/thrust all present in the accepted order, the
`SCHEMATIC — AREA EXPANSION ONLY, NOT A SOLVED CONTOUR` honesty label is
present and legible, and the stale-vs-solved mismatch fixture
(`rf-visual-qa`'s own required check) passes: with the live expansion-ratio
field edited to 60.000, the drawn schematic, the exit Mach, and the Isp
hero all still read the *old* solved state (Ae/At 40, Isp 348.658) with an
unmissable "Stale — recalculate" badge next to "Solved" — never silently
recomputed, never silently relabelled.

Light theme (`light_1920x1080.png`) manually inspected: clean, warm, high
contrast throughout; the "Calculate" button in the darkened accent bronze
reads clearly against the pearl-paper surface; no color reads as washed
out or muddy.

## Memory — the accepted trusted harness, re-run

`experiments/qml_memory/soak.py` (the calibrated, positive-controlled
harness `docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md`
establishes as trustworthy), 100 rounds each, against the new shell:

| Mode | Private (100 rounds) | First half | Second half | Page instances | Canonical result | Qt warnings | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lifecycle | 95.92 MB | 59.64 | 36.28 (decelerating) | +0 | unchanged | 0 | **PASS** |
| session (all workspaces) | 173.25 MB | 133.93 | 39.32 (decelerating) | +0 | unchanged | 0 | **PASS** |

Both plateau (second half well under first half), matching the root-cause
doc's own accepted pattern rather than the linear growth that would signal
a real regression. Pre-existing reference captures preserved at
`acceptance/cad_workbench_r1/memory/pre_r1_shell_soak_reference/` before
re-running (the harness's output path is meant to be overwritten on each
re-run; the *original* investigation's closing evidence is kept separately
so it is never lost).

## The one real gap `rf-visual-qa` found, and the fix

The pilot's own capture matrix has no concept of Dock state — it predates
the Dock. Manually captured and inspected Rocket Performance at 1366×768
with the Dock open and dragged toward its maximum
(`acceptance/cad_workbench_r1/rocket_performance/performance_1366x768_dock_expanded_tall.png`):
the propulsion canvas compresses and its "CHAMBER"/"EXIT" labels sit close
to the drawing — tight, but **the schematic stays recognizable and Isp
stays fully legible; nothing is clipped, hidden, or misrepresented**. This
satisfies `RF_WORKBENCH_GRAMMAR.md`'s own responsive rule ("shrink the
object, do not hide it") rather than violating it, but a 420px-tall dock
at this floor was more room than the shell should let a user take by
accident. Fixed at the shell layer: `AnalysisDock.maxExpandedHeight` is no
longer a fixed constant — `ui/Main.qml` binds it to
`Math.min(420, window.height * 0.5)`, so the dock can never claim more
than half the window's vertical space regardless of how far it is
dragged, and a resize while the dock is open re-clamps automatically
(verified: shrinking the window from 768px to 700px tall while the dock
sat at its old 384px maximum correctly re-clamped it to the new 350px
maximum, no manual intervention, no warning).

## Engineering subtype color collision — found and fixed before it shipped

While applying the palette, `Theme.series[5]` (which
`ui/engine/model/ComponentRegistry.qml` maps to Engine Design's "hot gas"
and "wall" port subtypes) and `Theme.error` were initially assigned the
identical hex value (`#C95F6A`, Sunumatik's `data6`) — a direct violation
of the brief's own required check ("is error distinguishable from hot
gas?"). Caught by re-reading `ComponentRegistry.subtypeColor()` before
treating the palette as final, not discovered visually. Fixed:
`series[5]` now uses copper (`#C86A40` dark / `#8A4826` light,
Sunumatik's `data2` — thermal, per the brief's own anchor-color naming),
`Theme.error` keeps the rose. Every other engineering subtype (fuel,
oxidiser, coolant, mixture, exhaust/pressurant, shaft) is unaffected —
`ComponentRegistry.qml` itself was not touched, only the `Theme.series`
values its index lookups resolve against.

## Skill usage

`rf-visual-qa` (via the Skill tool, now available in this session) was
asked directly whether wrapping in a new Browser+Dock introduces a
category of risk the pilot's own matrix can't see — it correctly named
Dock-state-at-the-compact-floor as exactly that gap, which produced the
capture and the fix above. `qt-qml-review`'s structured six-domain
checklist, applied by hand against the actual diff (not spawned as six
parallel agents, given the diff's modest size — judgment call, not a skip):
found one genuine issue outside the earlier lint pass — `InspectorDrawer`'s
`active: root.open` destroyed the drawer's item the instant it closed,
which meant its `Behavior on x` closing-slide animation could never
actually run (nothing left to animate). Fixed: the Loader now uses
`active: root.open || item !== null` — lazy-instantiated on first open,
then kept, the same one-time cost a settings panel or popup pays anywhere
else in Qt. `acceptance/cad_workbench_r1/skill_usage.json` has the full
entries.

## Solve-call parity (brief §90's explicit list, this workspace)

| Interaction | Chemistry re-solves |
| --- | --- |
| epsilon change | 0 |
| ambient change | 0 |
| scale change | 0 |
| selection / Browser open-close | 0 (new chrome only reads existing controller properties) |
| theme change | 0 |
| window resize | 0 |
| Dock open / close / resize | 0 (AnalysisDock has no controller binding at all) |

## Remaining before this workspace is fully "accepted" per the brief's own gate

* `qmllint` (Phase 1b of the qt-qml-review protocol) was not run — not
  found on `PATH` in this environment; the Python lint script (Phase 1)
  and manual structured review (Phase 2, applied by hand) stand in its
  place. Noted as an environment gap, not skipped by choice.
* Full 2560×1440 captures exist but were not each individually opened —
  1920×1080 and 1366×768 were the resolutions manually inspected pixel by
  pixel in this pass, consistent with where responsive risk actually
  concentrates (the floor) and where the accepted pilot's own defects were
  originally found.

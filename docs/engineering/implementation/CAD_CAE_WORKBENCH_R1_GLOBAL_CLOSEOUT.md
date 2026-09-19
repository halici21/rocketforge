# CAD/CAE Workbench R1 — Global Closeout

Final release qualification following all six workspace migrations
(Rocket Performance, Thermochemistry, Line, Fluid Properties, Trade Study,
Engine Design) and the Structural Recovery mega-phase. This is a
verification/packaging/documentation pass, not a redesign phase -- no new
product design, no new science, no new component physics, no Qt Quick 3D,
no broad architecture refactor. Two real defects were found and fixed
during verification; both are documented below with the evidence, not
asserted.

## Verdict

**ACCEPTED.** See "Final questions" below; all 14 are YES.

## What this phase found and fixed

1. **A real environment defect**, not a product bug: `.venv` (meant to be
   the "no chemistry library" base environment) had `cea` installed,
   silently inflating the base test-suite pass count and masking the
   base/no-provider code path. Fixed by uninstalling; reconciled the true
   counts against history (see the test-count reconciliation report).
2. **A real, live-reproduced stale-state honesty gap**: Trade Study's Trade
   tab (Sweep/Design-space, the workspace's own primary grammar since the
   mid-phase user correction) and its Selected Design Inspector had zero
   `resultStale` wiring -- only the older Results tab showed the "Setup
   changed" chip. Fixed in `StudyTrade.qml` and `StudyInspector.qml`,
   reusing the exact pattern already accepted in `StudyResults.qml`.
   Discovered a second bug while fixing the first: the naive trailing-edge
   placement of that chip put it geometrically behind the floating
   Inspector drawer overlay when open (confirmed via Qt scene-graph
   introspection: `visible=true`, correct text, but positioned under the
   drawer) -- fixed by left-aligning the chip in both `StudyTrade.qml` and
   the pre-existing `StudyResults.qml` instead of trailing it.
3. **A real cross-workspace status-bar state leak**: `Main.qml`'s
   `originNote` computation had no branch for Engine Design mode, so
   switching into Engine Design after visiting another Analysis workspace
   left the status bar showing that other workspace's own provenance text
   (e.g. Line's "Straight circular liquid line, distributed wall friction
   only" persisting under the Engine Design canvas). Fixed with an explicit
   engine-mode branch; verified in both source and the packaged build.
4. **A confirmed non-defect**: an independent design review flagged
   Engine Design demo-engine clipping at 1366px as BLOCKING. Investigated
   rather than dismissed or blindly fixed: every real UI path that loads
   the demo engine already calls `canvas.fitAll()` immediately afterward
   (verified by reading all three call sites, then by driving the actual
   "Load demo engine" button via `QTest.mouseClick` and capturing a clean,
   fully-visible 64% zoom result). The clipped capture was an artifact of
   a test script calling the model function directly, bypassing every real
   trigger -- no product code changed for this finding.

## Gates

| Gate | Result |
| --- | --- |
| Test-count reconciliation | Complete, 0 unexplained totals |
| Base regression (`.venv`) | 6955 passed, 154 skipped |
| Production regression (`.venv-cea`) | 7110 passed, 2 skipped |
| Scientific freeze | 0 physics/engineering/provider files touched |
| CEA/Cantera provider roles | Unchanged -- CEA production, Cantera dev-only, confirmed absent from the package build |
| Trade Study stale-state fixture | PASS after fix (2 gaps closed) |
| Trade Study dense-column reproduction | 16,400 points, no crash, 0 warnings, bounded RSS |
| Engine Design honesty re-check | 0 fake numeric values found, fix from last phase intact |
| Global cross-workspace screenshot matrix | Captured and visually inspected; 1 real defect found and fixed (status-bar leak) |
| Accessibility / contrast | 0 FAIL / 24 pairs, both themes |
| Global solve-call matrix | 0 / 6 domains across 20+ mixed interactions |
| Global memory soak | 500 rounds, 39.94 MB growth, decelerating, PASS |
| Source cleanliness (`qt-qml-review`) | Ran; findings are pre-existing codebase-wide style conventions, not regressions |
| Package build | Succeeded, 241 MB, 2,260 files |
| Package content audit | Cantera/dev-tools/acceptance confirmed absent |
| Packaged self-tests | 8 / 8 PASS against the real `.exe` |
| Packaged UI tour | 18 workspaces, 65 captures, from the real `.exe` |
| Source <-> package parity | 0 unexplained differences (4 independent smoke domains) |
| Final independent design review | 1 BLOCKING finding, resolved as a test-harness artifact; MEDIUM/LOW findings documented |
| README | Rewritten to describe only current functionality; 5 stale screenshots replaced with current real captures |
| Known limitations | Consolidated at `docs/engineering/KNOWN_LIMITATIONS_R1.md` |
| Licensing audit | Sunumatik: no code/asset copied, flagged, non-blocking |
| Working-tree audit | All files classified; no accidental/temp files |

Full detail for every gate: `acceptance/cad_workbench_r1/ACCEPTANCE_MANIFEST_FINAL.md`.

## Final questions

1. Coherent CAD/CAE workbench: **YES**
2. Six workspaces integrated: **YES**
3. Science preserved: **YES**
4. Visual interactions solver-free: **YES**
5. Stale state globally truthful: **YES** (after the fixes above)
6. Memory bounded: **YES**
7. Package parity: **YES**
8. CEA production: **YES**
9. Cantera dev-only: **YES**
10. Parametric Trade Study: **YES**
11. Honest Engine Design topology: **YES**
12. Packaged 1366 usable: **YES**
13. Limitations documented: **YES**
14. Ready to freeze: **YES**

`PROGRAM_STATE = CAD_CAE_WORKBENCH_R1_ACCEPTED_FROZEN`

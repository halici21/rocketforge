# Analysis Experience R2 — Checkpoint

## PROGRAM_STATE

**ANALYSIS_EXPERIENCE_R2_VISUALLY_APPROVED · CORRECTNESS GATE PASS.**

Visual approval was given by the user on 2026-09-19, in answer to the
direct question asked at the end of the implementation report. The agent
did not and could not set this.

CAD/CAE Workbench R1 is **not** frozen. Its visual acceptance for Analysis
mode was revoked by the user; its scientific acceptance stands and was not
re-opened by this program.

This checkpoint supersedes the Stage A checkpoint. Stage A's own record is
kept in `ANALYSIS_EXPERIENCE_R2_STAGE_A.md`; the implementation record for
this phase is `ANALYSIS_EXPERIENCE_R2_IMPLEMENTATION.md`.

| Field | Value |
| --- | --- |
| PHASE | Implementation of the R2 audit findings — six phases, run in the mandated order |
| DEFAULT_VIEW_STATE | Inverted. Six compressible pages open on `Relation`; Nozzle Lab on `Regime map`; Oblique Shock reduced to two modes with the sweep table demoted to a closed drawer; Trade Study lands on `Results` once a study completes |
| CHART_SYSTEM_STATE | Rebuilt. Nice-number ticks (linear and log) and a chart-owned type scale (`axisTick`/`axisTitle`/`chartAnnotation`) in both `RFLineChart` and `RFPlotSurface`. `IsentropicCharts`' private Canvas reimplementation removed in favour of the shared component. Legend swatches carry marker shape; a tofu glyph that left "infeasible" as colour-only is gone |
| HIERARCHY_STATE | Nozzle Lab has a regime-dependent hero (`shock_area_ratio` / `mach_exit`); Fluid Properties leads with density via a new `hero` tier on `PropertyRow`. The six relation calculators were deliberately left uniform — they are lookup tables and their primary surface is now the chart |
| SPACE_STATE | `RFEngineeringTable.columnWidth` is a floor rather than an exact width, so headers stop eliding beside unused space; Fluid Properties panels size to content; Home uses two columns above 1400px; `RFPanel` clips its body so a panel can no longer print across its neighbour |
| OBJECT_STATE | `NozzleObject.qml` added. Solved wall `r(x) = sqrt(A(x)/pi)` on the solver's own axial coordinate, 1:1 aspect, throat and shock at solved stations, flat fill. No gradient, no plume, no fabricated field |
| CHROME_STATE | "UI PREVIEW" removed from the application bar (retained in settings); the dead "Untitled workspace" control removed; seven drawn navigation icons added after two failed contact-sheet rounds |
| RESPONSIVE_STATE | Two real 1366x768 overlaps found by capture and fixed by reflow (Oblique Shock diagram, Nozzle Lab object + shock strip). One known limitation remains, recorded below |
| SCIENCE_PARITY | `rocketforge/physics` and `rocketforge/engineering` untouched — 0 files. Base 6955 passed / 154 skipped; production 7110 passed / 2 skipped, both unchanged |
| SOLVE_CALL_STATE | 0 solves across 42 view-state interactions over 8 watched entry points; negative control fires 1. The gate raises if an entry point is missing, so it cannot silently watch nothing |
| MEMORY_STATE | **CLOSED.** No leak in the product. The reported ~28 MB per chart-page destroy reproduces exactly (28.51 MB/load) and only with a soak that never dispatches `DeferredDelete`; with dispatch, −5.38 MB/load and zero object growth. 12 ablation variants all at 0 object growth; 500-round and mixed-session soaks bounded. Covered by `tests/application/test_analysis_page_lifecycle.py` with a negative control. See ANALYSIS_R2_MEMORY_LEAK_CLOSURE.md |
| QT_WARNINGS | 0 across every capture in this program |
| USER_APPROVAL_STATE | **APPROVED** by the user, 2026-09-19 |
| BLOCKERS | None internal |

## Known limitations, stated rather than hidden

- At 1366x768 the Nozzle Lab Solution panel is genuinely too short for its
  grid and clips its last row. A `Flickable` fix collapsed each group to a
  single row — a `Layout` inside a `Flickable` is not laid out by a parent
  `Layout` — and was reverted rather than shipped. The clipped state is worse
  than it should be and better than the overlap it replaced.
- ~~The chart page-destroy memory leak~~ — **closed 2026-09-19**: there was
  no leak. Full closure protocol in ANALYSIS_R2_MEMORY_LEAK_CLOSURE.md.
  The residual 5–42 MB band is allocator high-water, not retention.

## What the approval covers, and what it does not

The user approved the **visual and interaction level** of Analysis mode. That
is the question that was asked and the only thing this records.

It did not, on its own, close the two correctness defects that were open at
that moment: both were stated plainly before the approval was given, and a
visual approval could not have closed either. They were closed afterwards, on
their own evidence, in the correctness closure below — the memory defect by
finding that the product never had one, and the 1366 clip by restructuring the
Solution layout.

It is also not a release freeze.

## Not done, deliberately

- The six relation calculators were not given heroes (see HIERARCHY_STATE).
- `RFPlotSurface` remains a separate component from `RFLineChart`; they now
  share the tick rule and the type scale, which was the drift that mattered.
- The Trade Study summary and diagnostics strips were kept. The audit called
  them summary cards; they carry real, non-duplicated study provenance, and
  removing real provenance to satisfy a no-cards heuristic would be wrong.

## Correctness closure, 2026-09-19

Both open defects were run to ground under a fixed protocol and closed. One
production file changed (`ui/pages/nozzle/NozzleCalculator.qml`), gated
entirely on the pre-existing compact breakpoint. `rocketforge/physics/` and
`rocketforge/engineering/`: 0 files.

Gates: base 6957/154, production 7112/2 (both matching the opening baseline),
0 solves across 46 interactions, 0 field-level scientific differences across
the responsive transition, 0 Qt warnings, 0 binding loops, 7 of 8 screens
pixel-identical to the approved candidate.

Two record corrections are stated in ANALYSIS_R2_FINAL_CORRECTNESS_CLOSURE.md:
the memory defect as originally filed was wrong (including its "pre-existing
at HEAD" claim), and five review captures were stale and have been
regenerated. Historical measurements were not overwritten.

Nothing is committed. HEAD remains 8747846.

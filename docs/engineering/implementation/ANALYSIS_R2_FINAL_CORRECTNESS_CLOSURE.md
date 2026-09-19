# Analysis R2 — final correctness closure

**ANALYSIS R2 CORRECTNESS GATE — PASS**

- Memory leak: **CLOSED**
- Nozzle Lab 1366 Solution clip: **CLOSED**
- User-approved visual design: **PRESERVED**

Nothing has been committed. HEAD remains `8747846`.

## The two defects

**Memory.** There was no leak. The reported ~28 MB per chart-page destroy
reproduces exactly — 28.51 MB/load — and only with a soak that drove the loop
with `processEvents()` alone, which never dispatches `DeferredDelete`. With
dispatch: −5.38 MB/load and zero object growth. Detail:
`ANALYSIS_R2_MEMORY_LEAK_CLOSURE.md`.

**1366 clip.** Real, reproduced and measured: 209px of content height against
252px of content, clipping seven quantities. Fixed by laying the four result
groups abreast with stacked cells at compact height only. Detail:
`ANALYSIS_R2_NOZZLE_1366_CLOSURE.md`.

## Production change

One file: `ui/pages/nozzle/NozzleCalculator.qml`, entirely gated on the
pre-existing `page.compact`. `ui/components/RFLineChart.qml` was temporarily
patched for three ablation arms and restored byte-identically (sha256 prefix
`44f006155a45` before and after). No other production file was touched.

`rocketforge/physics/` and `rocketforge/engineering/`: **0 files**.

## Gates

| Gate | Result |
| --- | --- |
| Base tests | 6957 passed, 154 skipped — matches opening baseline |
| Production tests | 7112 passed, 2 skipped — matches opening baseline |
| Solve-call parity | 0 solves / 46 interactions, negative control 1 |
| Scientific parity | 0 field differences across the resize, all 6 workspaces |
| Visual parity | 7 of 8 screens pixel-identical; the 8th differs by 4 px beyond one level |
| Qt/QML warnings | 0 across 180 navigation events with theme + resize |
| Binding loops | 0 across 78 breakpoint crossings |
| Memory, 500 rounds | bounded, final-quarter slope negative, zero object growth |

## Two corrections to the record

**The memory defect as originally filed was wrong**, including the claim that
it was pre-existing at HEAD — that measurement used the same broken method on
an older tree. The earlier investigation document is kept unaltered; this
closure adds the evidence it lacked rather than rewriting it.

**Five of the twelve review captures were stale.** Images 05, 07, 09, 10 and
11 were never refreshed when the set was regenerated, so they showed earlier
states than the tree they represented — old fractional axis ticks, old
truncated table headers. Every one showed a **worse** state than the product
actually has. All have been regenerated. This corrects a record that
disagreed with the product; it does not change what was approved.

## Remaining limitations

- Allocator high-water of 5–42 MB across heavy navigation. Bounded, returns,
  ~15 MB reclaimable on request. Not "fixed" because it is not a defect.
- Soaks run offscreen; GPU texture residency is not exercised and no claim is
  made about it.
- The Oblique Shock Calculator capture differs from its approved baseline by
  29,485 pixels of which **4** exceed one level out of 255 (max delta 2).
  That is rasterisation and colour-animation settling noise. Called out rather
  than rounded to zero.

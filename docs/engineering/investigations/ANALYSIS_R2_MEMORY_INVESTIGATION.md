# Analysis R2 — chart-page memory investigation

## Verdict

**MEMORY LEAK CLOSED — ANALYSIS R2 LIFECYCLE GATE PASS**

There was no leak in the product. The reported retention was an artifact of
the soak script that measured it, and that script was mine.

The correction is not "the numbers were noisy". The numbers were real
measurements of a real thing — they were measurements of objects Qt had
already condemned and which the harness was preventing from dying. Under a
real event loop the same navigation is bounded: over 2000 page loads, memory
oscillates in a 40–60 MB band and the final quarter trends *down*.

## Reproduction

The filed defect reproduces exactly, and only, with the original method:

| Soak method | Slope | Live item growth |
| --- | --- | --- |
| `processEvents()` only, as filed | **59.6 MB/round** | **+420** |
| identical, plus `DeferredDelete` dispatched | **−2.4 MB/round** | **+0** |

Same tree, same navigation, same meter, 8 rounds over two chart pages. The
only difference is whether deferred deletions are allowed to complete.

## Harness controls

Run before anything was concluded. All five pass
(`experiments/qml_memory/harness.run_calibration`):

| Control | Result |
| --- | --- |
| A — known allocation | saw 40.2 MB of 40 · PASS |
| B — released allocation | retained 1.0 MB · PASS |
| C — intentional leak with a known slope | PASS |
| D — no-op noise floor | 0.0000 MB/round, peak-to-peak 0.0000 |
| E — object lifecycle | 200 objects alive before dispatch, **0 after** · PASS |

Control E is the one that names the defect outright: 200 QObjects that had
been `deleteLater()`-ed were still alive until `DeferredDelete` was dispatched.
That is the whole mechanism, demonstrated on objects the harness owns.

## Root cause

`QCoreApplication.processEvents()` does not deliver `DeferredDelete`. Qt holds
those events until the event loop unwinds to the level that posted them. A
scripted soak built from `processEvents()` never unwinds, so `deleteLater()`
never completes, and every page the application correctly destroyed was still
in the object tree to be counted — along with its Canvas backing stores, which
is why the per-load figure was large enough to look alarming.

The affected objects were therefore **not retained by the product at all**:
not by `Loader`, not by `Connections`, not by a model, not by a JS closure,
not by scenegraph or Canvas resources. They were pending deletion.

`experiments/qml_memory/harness.settle()` already documented this trap in its
own docstring, including a previous 2.9 GB false reading from the same cause.
The soak did not use it — it defined its own `settle()`. This investigation
reproduced a mistake the project had already made once and written down.

## Domain separation

100 rounds x 5 pages under a real event loop, sampling each domain
(`memory/step4_domains.json`):

| Domain | Behaviour |
| --- | --- |
| QObject lifetime (census) | Flat. 148 → 148 live items |
| Private/working set | Decelerating: first half +0.598, second half **−0.045** MB/round |
| QML/JS heap | 15.1 MB returned on `collectGarbage()` — reclaimable, therefore not leaked |
| Component cache | 0.1 MB on `trimComponentCache()` |
| Python heap | Grew with the instrument only (below) |
| PySide wrappers | Grew with the instrument only (below) |
| DeferredDelete backlog | 0 under a real loop |
| Allocator high-water | This is what the residual is |

### The second false signal, caught before it was reported

Step 4 showed PySide QObject wrappers growing linearly, 42 → 29,726. That
looked like a second leak. It was the measurement again: `census()` calls
`findChildren(QObject)`, which *creates* a Python wrapper for every object it
returns. Three arms, identical navigation, differing only in measurement
(`memory/step5_wrapper_origin.json`):

| Arm | Wrapper growth |
| --- | --- |
| A — no census taken | 42 → 42 · **+0** |
| B — census each sample | +97,658 |
| C — census, then drop refs and `gc.collect()` | +98,970 |

Arm A settles it. The product creates no wrappers; the instrument did.

## Ablation matrix

20 rounds per arm, each in its own process, real event loop, no census
(`memory/step6_ablation.json`). Arms marked *patched* temporarily edited
`RFLineChart.qml`; it was restored and verified by checksum
(`44f006155a45` before and after).

| Arm | Slope | Second half |
| --- | --- | --- |
| full chart pages (isentropic + fanno) | 0.748 | **−0.625** |
| chart removed (non-chart pages) | 0.065 | −0.013 |
| page kept alive (same page re-selected) | 0.000 | 0.000 |
| Nozzle Lab (NozzleObject canvas) | 1.136 | 0.553 |
| Trade Study (RFPlotSurface) | 0.959 | 0.582 |
| Oblique Shock (two charts) | 0.207 | −0.264 |
| theme flip only | 0.053 | 0.066 |
| resize only | 0.000 | 0.000 |
| *patched* — hover/crosshair disabled | 0.562 | 1.791 |
| *patched* — annotations disabled | 2.279 | 0.984 |
| *patched* — Canvas paint disabled | 0.837 | 0.182 |

The patched arms are the informative ones: **disabling chart features does not
reduce growth, and in two cases increases it.** Nothing is attributable to any
feature, which is the signature of allocator variance rather than a leak.

## Long soaks

**100 rounds x 5 pages** (500 page loads): peak 29.8 MB, first-half slope
+0.598, second-half **−0.045** MB/round, live items flat, 15.1 MB reclaimable.

**500 rounds x 4 pages** (2000 page loads), `memory/step7_soak500.json`:

| | |
| --- | --- |
| peak growth | 59.6 MB |
| final growth | 39.4 MB |
| overall slope | 0.048 MB/round |
| quarter slopes | −0.009, +0.018, +0.215, **−0.202** |
| final-quarter slope | −0.202 MB/round |
| verdict | **BOUNDED** |

Memory oscillates in a band and returns. At the originally reported 28 MB per
chart-page destroy, 2000 page loads would have retained about 56 GB.

## The fix

The product needed no change; no product file was modified by this
investigation (one was temporarily patched for ablation and restored
byte-identically). The fix is in the layer that produced the false result and
would have produced it again:

1. **`tests/application/test_analysis_page_lifecycle.py`** (new). Asserts that
   repeated navigation through four chart workspaces accumulates no live page
   items. It carries its own negative control: a second test asserts that
   without `DeferredDelete` dispatch the retention *is* visible, so the first
   test can never pass vacuously by counting nothing. Runs in the base
   environment; +2 tests on both profiles.
2. **`experiments/analysis_experience_r2/chart_memory_soak.py`** now calls
   `harness.settle`, and judges on deceleration over 40 rounds rather than a
   fixed slope over 12 — the criterion the 500-round evidence supports.
   Corrected result: first half 0.774, second half 0.046 MB/round · PASS.
3. **`soak_bisect.py` / `soak_pagekind.py`** are marked SUPERSEDED in their
   docstrings, with their own false numbers named, and their `settle` fixed so
   a re-run cannot repeat the error. Re-run bisect: page switching
   **227 → 2.05 MB/round**.

## Before and after

| Measurement | As filed | Corrected |
| --- | --- | --- |
| page switching, 9 pages | 227 MB/round | 2.05 MB/round |
| two chart pages | 56 MB/round | first half 0.77 → second half 0.05 |
| 12-round soak growth | 2782.6 MB | 26.6 MB over 40 rounds |
| live page items | +420 over 8 rounds | +0 |
| "pre-existing at HEAD 8747846" | 171 MB/round | same artifact, same method |

The HEAD baseline that made this look pre-existing used the same broken
`settle()`. It was not evidence of a long-standing defect; it was the same
measurement error applied to an older tree.

## Visual parity

No production content changed. Evidence rather than assertion:

- Every file under `ui/`, `rocketforge/`, `main.py` and `packaging/` predates
  the start of this investigation, except `RFLineChart.qml`, which was
  patched for three ablation arms and restored — checksum `44f006155a45`
  before and after.
- Capture is deterministic: two captures of the same page from the same tree
  differ by **0 pixels**, so the comparison method itself is sound.

One correction belongs here. Comparing fresh captures against the
`user_review/` set showed differences of 0.38–2.77%. Those are not
regressions: that review set had been assembled by copying captures taken at
*different points* during the implementation program, so several predated the
Phase 2 tick redesign and the Phase 6 chrome changes. The stale images showed
an **earlier**, worse state than the tree they were meant to represent — for
example the Nozzle Lab regime-map chart still carrying the old
`1.98 / 1.74 / 1.50` axis.

`user_review/` has been regenerated from the current tree so the record and
the product agree. This was a bookkeeping fault in how the review set was
assembled, and it is stated here rather than quietly fixed.

## Scientific and solve-call parity

| Gate | Result |
| --- | --- |
| `rocketforge/physics`, `rocketforge/engineering` | 0 files touched |
| Solve calls during 42 view-state interactions | **0**, negative control 1 |
| Base profile | 6957 passed, 154 skipped (+2 new lifecycle tests) |
| Production profile | 7112 passed, 2 skipped (+2) |
| Qt warnings across all captures | 0 |

## Remaining limitations

- **Allocator high-water is real and unaddressed**, because it is not a
  defect: the process holds a 40–60 MB band across heavy navigation and
  returns to it rather than climbing. ~15 MB of that is QML JS heap the engine
  hands back on request. Nothing here forces a collection to make a number
  look better.
- **The 1366x768 Nozzle Lab Solution-panel clip is untouched**, per the brief.
  It shares no mechanism with this investigation: it is a layout-minimum
  problem, not a lifecycle one.
- **These runs are offscreen.** The scenegraph uses the software/offscreen
  path, so GPU texture residency is not exercised. The object-lifetime and
  allocator conclusions do not depend on the backend, but a GPU-resident
  texture leak would not be visible here and is not claimed to be absent.

# Analysis R2 — memory leak closure

**Verdict: MEMORY LEAK CLOSED.** There was no leak in the product. The
reported retention was produced by the script that measured it.

This supersedes nothing: the earlier investigation record
(`docs/engineering/investigations/ANALYSIS_R2_MEMORY_INVESTIGATION.md`)
and its measurements are kept as written. This document is the closure run
against the brief's protocol, with the evidence the first pass did not
gather — per-class object counts, ownership audits, a full ablation matrix,
and mixed-session soaks.

## Reproduction

The prior claim — ~28 MB retained per chart-page destroy — reproduces
**exactly**, and only with the original method. Same tree, same pages, same
meter, 10 rounds over two chart pages; the arms differ only in whether
`DeferredDelete` is dispatched.

| | processEvents only (as filed) | + DeferredDelete |
| --- | --- | --- |
| per page load | **28.51 MB** | −5.38 MB |
| slope | 58.6 MB/round | −1.77 MB/round |
| workspace pages | **+20** | 0 |
| RFLineChart | **+20** | 0 |
| Canvas | **+40** | 0 |
| HoverHandler | **+210** | 0 |
| Connections | **+60** | 0 |
| total QObjects | **+21,510** | 0 |

Twenty page loads, twenty retained pages. Nothing was being freed because
nothing was being *allowed* to free.

## Harness validation (gate, run first)

| Control | Expects | Observed | Pass |
| --- | --- | --- | --- |
| A known allocation | growth | 40.238 of 40 MB | yes |
| B released allocation | stabilises | 1.008 MB retained | yes |
| C intentional retention | its own slope | 8.048 against 8.0 | yes |
| D no-op | no false growth | 0.0000 MB/round | yes |
| E object lifecycle | destroyed objects die | 200 alive → **0** after dispatch | yes |

Control C is why a negative result means anything: the harness detects a real
8 MB/round leak at 8.048 MB/round. Control E names the mechanism outright.

## Root cause

`processEvents()` does not deliver `DeferredDelete`. Qt holds those events
until the event loop unwinds to the level that posted them; a scripted soak
never unwinds, so `deleteLater()` never completes and every correctly-destroyed
page remains countable — with its Canvas backing stores, which is what made
the per-load figure large enough to alarm.

`experiments/qml_memory/harness.settle()` documented this trap in its own
docstring, including a previous 2.9 GB false reading from the same cause. The
soak defined its own `settle()` instead of importing it.

## What was ruled out, by measurement

| Candidate | Evidence it is not the cause |
| --- | --- |
| Loader not destroying pages | `shiboken6.isValid()` is **False** for all four chart pages after navigating away |
| Singletons retaining visuals | WorkspaceState/ShellContext/Navigation hold **0** child QObjects; Theme holds 2, neither visual |
| Python holding QML wrappers | with no census taken, wrapper count is **42 → 42** over 200 page loads |
| Hover Canvas | disabling it: 56.11 → 56.13 MB/round |
| Canvas paint content | short-circuiting `onPaint`: 56 → 47, so the paint is ~9 MB and existence is the rest |
| `renderTarget` | `Canvas.Image`: 56.04, unchanged |
| Connections lifetime | live `Connections` growth over 200 page loads: **0** |

## Ablation matrix

Twelve variants, each in its own process, real event loop, correct dispatch.
Full table in `acceptance/analysis_r2_closure/memory/ablation_matrix.md`.

**Every variant returned `obj_items +0`.** Memory growth ranged 0.9–30.2 MB
with late slopes from −0.63 to +2.50 and no attribution to any feature:
disabling annotations (22.8 MB), hover (20.1) or Canvas paint (25.5) did not
reduce it below the unpatched A0 (25.6). The one arm that did drop — A2,
dataset emptied, 0.9 MB — is the arm that removes the data the chart holds
*while alive*. That is a working set, not retention.

## Acceptance soaks

Real Qt event loop (`QTimer` inside `app.exec()`); no manual `processEvents`,
no hand dispatch, no forced collection between rounds.

| Profile | Page loads | Peak | Final | 1st half | 2nd half | Object growth |
| --- | --- | --- | --- | --- | --- | --- |
| focused 100 | 200 | 37.6 MB | 19.6 MB | +0.362 | **−0.048** | none |
| focused 500 | 1000 | 41.7 MB | 28.3 MB | +0.004 | **+0.026** | none |
| mixed session 100 | 800 | 16.7 MB | 5.2 MB | +0.016 | **+0.010** | none |

The mixed session covers all eight Analysis workspaces with tab changes, chart
hover, theme cycling and 1366/1920 resize cycling.

Object counts are taken parked on a fixed chart-free page. Comparing a
baseline census taken on one page with a final taken on another measures which
page is resident, not what leaked — that confound produced a spurious "+1
page" reading before it was removed.

## The fix

The product needed none. The fix is in the layer that produced the false
result and would have produced it again:

- **`tests/application/test_analysis_page_lifecycle.py`** — asserts navigation
  accumulates no page instances, with a **negative control** asserting the
  retention *is* visible without dispatch, so the first test can never pass
  by counting nothing. +2 tests on both profiles.
- **`chart_memory_soak.py`** now uses `harness.settle` and judges on
  deceleration over 40 rounds: 0.774 → 0.046 MB/round. Was 231 MB/round.
- **`soak_bisect.py` / `soak_pagekind.py`** marked SUPERSEDED with their own
  false numbers named. Re-run bisect: page switching **227 → 2.05 MB/round**.

## Remaining, and deliberately not "fixed"

A 5–42 MB allocator high-water band that rises and falls with how much chart
data is alive, ~15 MB of it QML JS heap the engine returns on request. It is
bounded and it comes back down. Forcing a collection to flatten the graph
would be cosmetic, and is explicitly out of bounds.

Soaks run offscreen, so GPU texture residency is not exercised. The
object-lifetime and allocator conclusions do not depend on the backend, but a
GPU-resident texture leak would not be visible here and is not claimed absent.

# Trade Study — UI contract

Phase 5F. What the workspace promises, and what enforces each promise.

---

## Shape

Fourth analysis domain, its own sidebar section, one page with four views of
one study.

| View | Question |
| --- | --- |
| **Setup** | What is fixed, what varies, what is reported, wanted, required — and what will it cost? |
| **Results** | Every evaluated point, with its raw physics intact. |
| **Pareto** | Where is the trade-off, and which designs are not beaten outright? |
| **Compare** | These few designs, side by side. |

The views share the controller's single current study, so switching never
re-evaluates and two views cannot disagree.

### Files

| File | Role |
| --- | --- |
| `ui/pages/TradeStudyPage.qml` | header, view selector, stack |
| `ui/pages/tradestudy/StudySetup.qml` | baseline, variables, outputs, objectives, constraints, scoring, run |
| `ui/pages/tradestudy/StudyVariableRow.qml` | one design variable and what varying it costs |
| `ui/pages/tradestudy/StudyResults.qml` | the table, summary, diagnostics, provenance |
| `ui/pages/tradestudy/StudyPareto.qml` | the scatter, axis selectors, best-evaluated points |
| `ui/pages/tradestudy/StudyCompare.qml` | up to four designs, raw physics above the score |

Built from the existing component kit. The **only** change to a shared
component is an added `activated(int index)` signal on `RFComboBox` — purely
additive, no property, default or painted part touched, and needed because a
selector bound to a backend property cannot write back from
`onCurrentIndexChanged` without looping through its own binding.

---

## The rules, and what enforces them

### The workload is previewed before anything runs

The most important line on the Setup page:

> 410 design points · 41 unique chamber solves · 410 performance evaluations.
> The nozzle-stage variables add no chamber solves, so 369 chemistry solves are
> avoided.

It updates as a range is edited, **without running anything** — computed from
variable cardinalities. A user who can see that 410 points cost 41 chamber
solves learns the dependency planner; one who only meets a progress bar will
build the study that costs 410.

Each variable row carries its own `effect` line and a stage chip, so the
expensive variables are identifiable at a glance.

### No equations, no constants, no decision algorithms in QML

`Math` is restricted to `max/min/floor/ceil/round/abs`; a scan bans `8314`,
`9.80665`, `101325` and the rest; a third bans a weighted sum or a limit
comparison. A fourth bans `dominat`, `normaliz`, `weightedsum` — after blanking
string literals, because "Feasible, dominated" is a legend entry and naming a
verdict the engine reached is the opposite of computing one. Each has a
negative control that fires on a real leak and stays silent on the label.

### No chamber case, no study

The workspace says where to set one. Run Study is disabled, and nothing is
invented in its place.

### Every refusal is explained where it happened

An invalid definition shows its message beside the Run button, before any
chemistry runs: too large, an ineffective variable, a metric that needs an
engine size, an objective without a weight.

### The table keeps every point

Successful, infeasible and failed rows are all present by default. A filter
hides rows; it never removes them, and the underlying result keeps all of them
however the view is set. A design space with holes in it is information — the
holes are where the model stops working, and a table that dropped those rows
would imply the space is continuous.

A failed row shows an em dash for the metrics it could not produce, never a
zero. Status and feasibility are **separate columns**, because they answer
different questions.

### Execution is serial and chunked

Eight points per event-loop turn on a zero-interval `QTimer`. No thread pool,
no concurrent provider call — a test bans `QThread`, `QThreadPool`,
`ThreadPoolExecutor`, `ProcessPoolExecutor`, `multiprocessing` and `QRunnable`
from the controller. Phase 5B-0 measured CEA threading and found no gain;
trading a proven property for an unproven one to move a progress bar would be a
poor bargain.

Progress reports real work — "300 of 410 points · 41 of 41 chamber solves" —
not a synthesised percentage.

### A cancelled study shows no front, no ranking and no score

The evaluated points are kept and shown, and the status says why:

> The study was cancelled. The points below were evaluated; no front, ranking
> or score is shown, because they would describe a design space that was only
> partly explored.

### A decision edit re-analyses; it never re-solves

Changing an objective direction, adding an objective, adding a constraint or
moving a weight calls `reanalyse` on the raw result that already exists.
Measured through the Qt surface: **0** provider calls for each.

### Scoring is off by default

Never enabled by a study happening to have two objectives. When on, the panel
shows the normalisation method, the weights as typed, the effective normalised
weights, and:

> Min–max normalisation over the feasible evaluated points of this study. A
> score is therefore relative to this population: the same design scores
> differently in a study with a different range. It never changes a raw value,
> a feasibility verdict or Pareto membership.

### The Pareto plot says what it is and what it is not

Three series distinguished by **marker shape as well as colour** — a diamond
for efficient, an open circle for feasible-and-dominated, a cross for
infeasible-or-failed — with a legend naming each.

Two notes a reader would otherwise get wrong:

> Each marker is one evaluated design, not a point on a continuous curve — the
> front is a sample of the grid that was run.

and, when there are more than two objectives:

> Pareto membership was decided using all 3 objectives; this plot shows Isp and
> chamber temperature, so a marker may look dominated here while being
> efficient in the full objective set.

No spline, no polynomial, no surrogate. The axis selectors are bound to the
axes they control, so a control cannot show one metric while the plot draws
another.

### "Best evaluated", never "optimum"

> One per objective, over the points this study actually evaluated. A finite
> sampled grid cannot establish a global optimum, and nothing here searches for
> one.

A wording audit bans *global optimum*, *globally optimal*, *the optimal
design*, *optimum design* and *guaranteed optimum* — skipping any occurrence
preceded by a negation, because this workspace's honest sentences contain the
banned phrases inside the disclaimers that rule them out. The negative control
fires on the claim and stays silent on the disclaimer.

A wording audit also runs over **every published controller property** after a
live study, not only over the QML.

### Compare shows the physics above the score

Four designs at most. Rows are grouped design variables → physics →
constraints → decision, and the weighted score is the last row of the last
group. A score summarises the numbers above it, and a reader must be able to
see them before being asked to trust it.

Violated constraints are listed with the value that violated them — "3610
violates <= 3500" is actionable; "infeasible" is not.

### Selection is decision support, not an action

Marking a design for comparison changes nothing outside this workspace. There
is no "apply to Engine Design", no geometry write-back and no edit to the
upstream cases.

---

## The packaged diagnostic

```
RocketForge.exe --selftest-trade-study <directory>
```

Loads the real QML, drives the real controllers through the same slots the
controls call, writes one JSON report and 14 PNG captures, exits. **No
synthetic desktop input** — a test bans `QTest`, `sendEvent`, `pyautogui` and
the rest.

It also **counts provider calls**, which is the one thing a screenshot cannot
show: a frozen build that solved chemistry once per design point instead of
once per chemistry state would look identical in every capture.

### Results

| | Source | Packaged |
| --- | --- | --- |
| Captures | 14 | 14 |
| Qt messages | **0** | **0** |
| Design points | 164 | 164 |
| Chamber solves | **41** (expected 41) | **41** |
| Solves added by objective / constraint / weight edits | **0 / 0 / 0** | **0 / 0 / 0** |
| Resolutions | 2560×1440, 1920×1080, 1366×768, + light theme | same |

**Parity: 6936 fields compared, 0 differing, 0 present in only one build.**

At 1366×768 the variables, the workload line and Run Study are all reachable;
Run Study is pinned outside the scroll region and is never clipped.

---

## Defects found and fixed during this phase

**Three QML binding loops.** A selector whose `currentIndex` was bound to a
controller property and which wrote back from `onCurrentIndexChanged` looped
through its own binding — 2 warnings per affected control. Comparing values
first did not help, because Qt reports the loop on the binding rather than on
the value. Fixed by writing back from `activated`, which fires only on a person
choosing an item; `RFComboBox` had to forward the signal, which it now does.

**The Pareto axis selectors were unbound.** Both combo boxes read "Specific
impulse" while the plot was drawn against chamber temperature. Caught by
reading the 1920×1080 capture, not by a test.

**The axis titles showed raw metric keys** rather than labels and units.

**A Phase 5D architecture rule needed the third analysis domain.** The
exclusion list names the analysis workspaces explicitly — the rescoping Phase
5E introduced for exactly this reason — so adding `tradestudy` was a
one-line change with a companion test that still refuses any widening beyond
named domains. The rule's force on the 30+ compressible pages is unchanged.

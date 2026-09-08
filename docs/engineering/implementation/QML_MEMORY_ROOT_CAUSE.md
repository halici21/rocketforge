# Rendered-QML memory retention — root cause

**The reported defect was a measurement artifact. There is no unbounded
rendered-QML memory retention in RocketForge.**

This document is written in the order the evidence arrived, including the part
that was wrong, because the correction is the finding. Evidence in
`acceptance/qml_memory/`.

---

## 1. What was reported

The accepted visual pilot recorded **~451 MB retained per 100 recalculations**
with the Rocket Performance page rendered, against ~896 MB for the design it
replaced. This program was commissioned to find and fix the cause.

## 2. What the first measurements said

A fresh harness — calibrated against a known 40 MB allocation, a released
allocation, an 8 MB/round intentional leak and a no-op noise floor, all passing
— reproduced something that looked exactly like a leak:

| Recalculations | Private bytes |
| --- | --- |
| 10 | 7.52 MB |
| 510 | 233.85 MB |
| 1000 | **462.59 MB** |

Linear, first half 230.02 MB, second half 232.57 MB, no plateau. It reproduced
on the real Windows platform as well as offscreen (4.818 vs 4.717 MB/round), so
it was not a test-rig artifact of the offscreen QPA plugin. Neither `gc.collect()`
(0%) nor `QQmlEngine.collectGarbage()` (8%) reclaimed it. The QObject census
was flat at **+0**, so it was not a live-object leak in the visual tree.

Payload isolation pointed at one thing: a page bound to a single
`@Property("QVariantList")` grew even when only its `.length` was read, and the
cost scaled with the number and nesting of list properties. A twenty-line
reproducer containing no RocketForge code appeared to confirm it at framework
level: 26.71 MB per 1000 publications of six two-field rows.

## 3. What was actually wrong

**`QCoreApplication.processEvents()` does not dispatch `DeferredDelete`
events.** Those are delivered when the event loop unwinds to the `exec()` level
that posted them. Every harness here — and the visual pilot's benchmark before
them — drove the application with `processEvents()` alone, so **no
`deleteLater()` ever completed**. Qt was destroying objects correctly and the
destruction never ran.

It was caught by a different symptom. A page-lifecycle soak reported that
navigating to a workspace and back added one live page instance every time,
never released: `PerfCalculator` 1 → 9 over eight round-trips, and a mixed
multi-workspace session appeared to retain **2.9 GB**. A leak that large and
that simple would not have survived the application's existing test suites, so
the harness was suspected before the product.

Adding one call changed everything:

```python
app.processEvents()
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
```

| Measurement | processEvents only | with deferred deletion |
| --- | --- | --- |
| `PerfCalculator` after 8 navigations | 1 → **9** | 1 → **1** |
| page instances, lifecycle soak (40 rounds) | **+80** | **+0** |
| page instances, session soak (40 rounds) | **+80** | **+0** |
| session soak total | **2878 MB** | 121 MB, decelerating |

The object census stayed flat throughout the recalculation runs because Qt
unparents an item before scheduling its deletion: the objects were no longer
children of the window, so the census could not see them, while their memory
was still committed. A flat census and rising bytes looked like proof of a
native-conversion leak. It was one artifact producing both readings.

## 4. Corrected measurements

Same workload, same harness, deferred deletion dispatched. `baseline` is the
accepted pilot's QML, preserved in
`acceptance/ui_rollout/baseline_snapshot/source/ui`.

| Tree | 1000 recalculations | Slope | First half | Second half |
| --- | --- | --- | --- | --- |
| baseline (as accepted) | **5.66 MB** | 0.002 | 5.66 | **−0.00** |
| current (after this program's change) | **1.61 MB** | 0.001 | 1.61 | **0.00** |

Both plateau. The reported 462 MB does not exist, and neither did the 451 MB or
the 896 MB: the pilot's benchmark had the same omission.

The framework reproducer, corrected:

| Publisher | 1000 publications | Slope |
| --- | --- | --- |
| scalar properties | 0.00 MB | 0.0000 |
| `QAbstractListModel` in place | 0.21 MB | −0.0003 |
| `@Property("QVariantList")` | **1.01 MB** | 0.0102 |

1.01 MB, not 26.71 MB — a 26× overstatement.

## 5. What remains true

Publishing through a re-read `QVariantList` really is more expensive than a
stable model. It is a **higher bounded plateau**, not a leak. Measured on an
isolated page over 800 recalculations:

| Bound to | Total | First half | Second half |
| --- | --- | --- | --- |
| nothing | 3.87 MB | 3.87 | **0.00** |
| five `QVariantList` properties | **16.70 MB** | 19.74 | **−3.04** |
| a stable row model | 4.04 MB | 3.92 | 0.12 |

Every configuration levels off. The list pattern simply settles ~13 MB higher.

## 6. A second finding, and its correction

The object census showed **+142 `QQuickColorAnimation` objects** after ten theme
switches, first written up as a live-object leak. It is not one: the count is
+142 after 10 rounds, +142 after 30, and +142 after 60. Components instantiated
lazily when the light theme is first applied, then kept. Bounded, no action.

An object count taken at a single scale cannot tell accumulation from
instantiation. Two more scales can.

## 7. One finding that is still open

A mixed multi-workspace session — navigating seven workspaces and recalculating
in each — grows about **0.78 MB per round after warm-up** and had not levelled
off at 90 rounds. Page instances are +0 and the object census falls slightly, so
it is not page or object accumulation.

Pure navigation between two workspaces, by contrast, does plateau: 400
round-trips settle at ~20 MB with the second half contributing 23% of the first.

So something in the wider session retains that two-page navigation does not.
This is orders of magnitude smaller than the defect this program set out to
find, it is not what Gate A was scoped to, and its root cause is **not
established**. Recorded as open.

## 8. The change that was made, and why it was kept

Rows are now published through a stable `QAbstractListModel`
(`rocketforge/application/rowmodel.py`) rather than as `QVariantList`
properties a binding re-reads. Twelve list properties across the Rocket
Performance workspace were converted; the QVariantList properties remain for
Python callers — tests, smoke tours, the parity snapshot — where a read costs
nothing.

It was designed as a fix for a leak that turned out not to exist. It is kept
because it is independently justified:

* the plateau falls **5.66 MB → 1.61 MB** for 1000 recalculations, 3.5×;
* delegates are reused rather than destroyed and rebuilt on every publication;
* it is the pattern Gate B needs if the visual language is rolled out to five
  more workspaces, each publishing its own rows.

It is **not** a leak fix, and this document does not claim it as one.

## 9. What was rejected

* `gc.collect()` per solve — reclaimed 0%.
* `QQmlEngine.collectGarbage()` per solve — reclaimed 8%, and changes when
  memory is reclaimed rather than whether it is retained.
* Page reload, engine rebuild, process restart.

None was adopted, and none would have helped: there was nothing to reclaim.

## 10. What this cost, and the lesson

Three harness defects were found in this program, two of them by this program
in its own instruments:

1. The visual pilot's memory probe read through `psapi`, returned a flat zero,
   and reported a clean `0.000 MB` for a loop retaining hundreds of MB.
2. That same benchmark leaked seven page instances from its page-creation
   measurement into its memory measurement, inflating the figure ~10×.
3. Every harness, including this program's, drove Qt with `processEvents()` and
   never let `deleteLater()` complete — which is what produced the entire
   reported defect.

The calibration controls caught none of these, because all four measure the
*allocator*, not the *event loop*. A memory harness for a Qt application needs
a fifth control: **create and destroy a known number of QObjects and assert the
census returns to where it started.**

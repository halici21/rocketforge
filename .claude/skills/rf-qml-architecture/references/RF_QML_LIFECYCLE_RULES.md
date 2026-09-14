# RF QML lifecycle rules

The full protocol for measuring memory and object lifecycle correctly in
this PySide6/QML application, distilled from
`docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md` and the harness
in `experiments/qml_memory/`. Read this before writing any new measurement
script, and before trusting the output of an existing one you did not just
verify.

## Why this document exists

This project's own QML memory investigation produced, in order:

1. A memory probe that read Windows process counters through `psapi`,
   silently returned zero on this machine, and reported a clean `0.000 MB`
   for a loop that was actually retaining hundreds of megabytes.
2. A benchmark that leaked seven extra page instances from its own
   page-creation measurement into its memory measurement, inflating a
   reported figure roughly tenfold.
3. A harness -- built specifically to fix the first two mistakes, with four
   passing allocator controls -- that still reported a ~462 MB "leak" which
   turned out not to exist, because none of its four controls tested
   whether Qt object destruction was actually completing.

The lesson is not "be more careful." It is that a memory harness for a Qt
application needs a control the allocator-focused controls cannot provide:
proof that scheduled object destruction actually ran before any byte count
is trusted.

## The `DeferredDelete` trap, precisely

`QObject.deleteLater()` posts a `DeferredDelete` event. That event is
dispatched when the event loop unwinds to the level of the `exec()` (or
equivalent) call that is currently running -- **not** by
`QCoreApplication.processEvents()`, which processes the regular event queue
but does not drain deferred deletions posted at a level it did not itself
open.

A harness -- or a smoke-test tour, or a benchmark -- that drives Qt only
with `processEvents()` in a loop will therefore see every `deleteLater()`'d
object as permanently alive: unparented (Qt detaches an object from its
parent before scheduling deletion), so an object census may even read as
flat while memory keeps climbing, which looks exactly like a leak with no
object-count evidence to contradict it.

**The fix, in every script that turns the event loop for measurement
purposes:**

```python
from PySide6.QtCore import QCoreApplication, QEvent

def settle(app, rounds: int = 8) -> None:
    for _ in range(rounds):
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
```

`rocketforge`'s own smoke tours (`perfsmoke.py`, `shellsmoke.py`,
`studysmoke.py`, `uismoke.py`) were retrofitted with this exact pattern
after the investigation found they had the same gap -- their reported
packaged-memory peak fell by roughly 1 GB on one tour purely from letting
deletions complete. Any new tour or smoke script must include it from the
start.

## The five controls a memory harness needs

Four are the obvious ones -- but all four passed while control five was
silently broken, which is why five is not optional:

1. **Known allocation.** Retain a known amount of memory (e.g. 40 MB) and
   confirm the probe detects at least ~80% of it.
2. **Released allocation.** Allocate, release, collect. Confirm retained
   growth stays well under the allocated amount -- some retained arena
   space from the allocator is expected and not itself evidence of a leak.
3. **Known leak slope.** Retain a fixed amount per round across several
   rounds and confirm the measured slope matches the known rate within a
   reasonable tolerance.
4. **No-op noise floor.** Turn the event loop with nothing published and
   record the noise floor -- no later claim may rest on a difference
   smaller than this.
5. **Object lifecycle.** Create and `deleteLater()` a known number of
   `QObject`s, dispatch `DeferredDelete`, and confirm the live count returns
   to exactly zero. This is the control that would have caught the false
   462 MB finding immediately -- it directly tests the mechanism the other
   four cannot see.

If control 5 fails (or is skipped), do not trust any "no leak" conclusion
from controls 1-4, no matter how clean they look.

## Two independent memory metrics, and what each one hides

- **Private bytes** (`PROCESS_MEMORY_COUNTERS_EX.PrivateUsage` on Windows) --
  committed private memory, not shared, not trimmed by working-set
  pressure. Use this as the primary signal.
- **Working set** -- pages currently resident. The OS can trim this under
  memory pressure for reasons that have nothing to do with the program being
  measured, so a falling working set is not by itself evidence that nothing
  was retained.

`tracemalloc` (Python's own allocator tracker) **does not observe Qt/native
allocations at all**. A flat `tracemalloc` reading is never evidence that
native (Qt/QML/C++) memory is flat -- it can only speak to Python-side
allocations.

## Windows API pitfall: the pseudo-handle truncation

`ctypes.windll.kernel32.GetCurrentProcess()` returns a pseudo-handle that,
without an explicit `restype = ctypes.c_void_p` declaration, `ctypes`
truncates to 32 bits on a 64-bit process -- the subsequent
`K32GetProcessMemoryInfo` call then fails with `ERROR_INVALID_HANDLE` (error
code 6). Always declare full signatures:

```python
import ctypes

_K32 = ctypes.WinDLL("kernel32", use_last_error=True)
_K32.GetCurrentProcess.restype = ctypes.c_void_p
_K32.GetCurrentProcess.argtypes = []
_K32.K32GetProcessMemoryInfo.restype = ctypes.c_int
_K32.K32GetProcessMemoryInfo.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(_CountersEx), ctypes.c_uint32,
]
```

## Warm-up vs. a real trend

The first tens to low-hundreds of publications on a page can legitimately
populate caches once. That is not the same defect as unbounded linear
growth. Always measure across enough rounds to see whether growth
decelerates (a plateau -- fine) or stays linear (a real defect), and record
the first-half/second-half split explicitly rather than a single before/after
delta -- a plateauing series and a linear one can produce an identical total
at one sample point and only the shape over time tells them apart.

## Pre-registering the acceptance criterion

Decide the pass/fail threshold for a memory investigation *before* looking
at the candidate fix's result, using the measured no-op noise floor and the
originally observed (corrected) defect rate as inputs. Choosing a threshold
after seeing the number invites picking whatever the fix happened to
produce. See `acceptance/qml_memory/acceptance_criterion.json` in this
repository for the actual registered criterion from the investigation that
produced this document, as a template for the shape such a criterion should
take (a slope bound, a bounded-total bound, a sublinearity check, and a
no-masking rule ruling out `gc.collect()`/engine-GC/page-reload as
substitutes for a real fix).

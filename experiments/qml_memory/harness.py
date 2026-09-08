"""Process memory measurement, and the controls that make it trustworthy.

A memory harness is only evidence if it has been shown to detect memory. The
previous one in this project read through `psapi`, silently returned a flat
zero, and reported a clean `0.000 MB` for a loop that actually retained
hundreds of megabytes. Nothing here is believed until the controls below pass.

Two independent process-level observations are recorded, because they fail
differently:

  * **working set** -- pages currently resident. Falls when the OS trims under
    pressure, so it can hide retention and can also drop for reasons that have
    nothing to do with the program.
  * **private bytes** (`PrivateUsage`) -- committed private memory, not shared
    and not trimmed by working-set pressure. This is the primary signal for
    "did the process commit memory it never gave back".

Python-tracked allocations are recorded separately where useful. **tracemalloc
does not observe Qt/native allocations**: a flat tracemalloc says nothing about
the scenegraph, the JS heap or C++ objects, and must never be reported as
evidence that native memory is flat.
"""
from __future__ import annotations

import ctypes
import gc
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "acceptance" / "qml_memory"
MB = 1024 * 1024


class _CountersEx(ctypes.Structure):
    """PROCESS_MEMORY_COUNTERS_EX."""

    _fields_ = [("cb", ctypes.c_uint32),
                ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t)]


_K32 = ctypes.WinDLL("kernel32", use_last_error=True)
# Without declared signatures ctypes truncates the GetCurrentProcess
# pseudo-handle to 32 bits and the call fails with ERROR_INVALID_HANDLE.
_K32.GetCurrentProcess.restype = ctypes.c_void_p
_K32.GetCurrentProcess.argtypes = []
_K32.K32GetProcessMemoryInfo.restype = ctypes.c_int
_K32.K32GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,
                                         ctypes.POINTER(_CountersEx),
                                         ctypes.c_uint32]


def settle(app, rounds: int = 8) -> None:
    """Turn the event loop, INCLUDING deferred deletions.

    QCoreApplication.processEvents() does not dispatch DeferredDelete events --
    those are delivered when the loop unwinds to the exec() level that posted
    them. A harness built only on processEvents() therefore never lets
    deleteLater() complete, and every object Qt has correctly scheduled for
    destruction looks like a leak. That is exactly what happened here: pages
    appeared to accumulate one per navigation and a mixed session appeared to
    retain 2.9 GB, all of it an artifact of this omission.
    """
    from PySide6.QtCore import QCoreApplication, QEvent

    for _ in range(rounds):
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def memory() -> dict[str, float]:
    """Working set and private bytes, in MB. Raises rather than returning 0."""
    counters = _CountersEx()
    counters.cb = ctypes.sizeof(_CountersEx)
    if not _K32.K32GetProcessMemoryInfo(_K32.GetCurrentProcess(),
                                        ctypes.byref(counters), counters.cb):
        raise OSError("K32GetProcessMemoryInfo failed: "
                      f"{ctypes.get_last_error()}")
    return {"working_set_mb": counters.WorkingSetSize / MB,
            "private_mb": counters.PrivateUsage / MB}


def delta(before: dict[str, float], after: dict[str, float]
          ) -> dict[str, float]:
    return {key: round(after[key] - before[key], 3) for key in before}


def slope_mb_per_round(series: list[float]) -> float:
    """Least-squares slope, so a trend is a number rather than an impression."""
    n = len(series)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2.0
    mean_y = sum(series) / n
    num = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(series))
    den = sum((i - mean_x) ** 2 for i in range(n))
    return num / den if den else 0.0


# ---------------------------------------------------------------------------
# controls
# ---------------------------------------------------------------------------

def control_a_known_allocation(mb: int = 40) -> dict:
    """A deliberately retained allocation the measurement must see."""
    gc.collect()
    before = memory()
    ballast = [bytearray(MB) for _ in range(mb)]
    for block in ballast:
        block[0] = 1                     # touch each page so it is resident
    after = memory()
    seen = delta(before, after)
    del ballast
    gc.collect()
    released = delta(after, memory())
    return {"allocated_mb": mb, "seen": seen, "after_release": released,
            "pass": seen["private_mb"] >= mb * 0.8}


def control_b_released_allocation(mb: int = 40) -> dict:
    """Allocate, drop the references, collect. Retention must not be reported."""
    gc.collect()
    before = memory()
    for _ in range(3):
        scratch = [bytearray(MB) for _ in range(mb)]
        for block in scratch:
            block[0] = 1
        del scratch
        gc.collect()
    after = memory()
    kept = delta(before, after)
    # Python may keep freed arenas committed, so this is bounded, not zero.
    return {"cycles": 3, "each_mb": mb, "retained": kept,
            "pass": kept["private_mb"] < mb * 0.5}


def control_c_intentional_leak(rounds: int = 6, mb: int = 8) -> dict:
    """A real leak with a known slope. The harness must produce that slope."""
    gc.collect()
    keep: list[bytearray] = []
    base = memory()
    series = []
    for _ in range(rounds):
        for _ in range(mb):
            block = bytearray(MB)
            block[0] = 1
            keep.append(block)
        series.append(delta(base, memory())["private_mb"])
    measured = slope_mb_per_round(series)
    del keep
    gc.collect()
    return {"rounds": rounds, "leaked_per_round_mb": mb, "series": series,
            "measured_slope_mb_per_round": round(measured, 3),
            "pass": abs(measured - mb) <= mb * 0.35}


def control_d_no_op_noise(app=None, rounds: int = 20,
                          iterations: int = 50) -> dict:
    """The floor: event-loop turns with nothing published.

    Anything at or below this is indistinguishable from doing nothing, and no
    acceptance claim may rest on a difference smaller than it.
    """
    gc.collect()
    base = memory()
    series = []
    from PySide6.QtCore import QCoreApplication, QEvent

    for _ in range(rounds):
        for _ in range(iterations):
            if app is not None:
                app.processEvents()
                QCoreApplication.sendPostedEvents(None,
                                                  QEvent.Type.DeferredDelete)
        series.append(delta(base, memory())["private_mb"])
    return {"rounds": rounds, "iterations_per_round": iterations,
            "series": series,
            "total_mb": series[-1] if series else 0.0,
            "slope_mb_per_round": round(slope_mb_per_round(series), 4),
            "peak_to_peak_mb": round(max(series) - min(series), 4)
            if series else 0.0}


def control_e_object_lifecycle(app) -> dict:
    """Create and destroy known QObjects; the census must return to zero.

    The four controls above all measure the allocator, and all four passed
    while the harness was silently failing to complete a single deleteLater().
    That omission produced this program's entire reported defect. This control
    is the one that catches it: it asks whether objects the harness destroys
    actually die.
    """
    from PySide6.QtCore import QObject

    if app is None:
        return {"skipped": "needs a QApplication", "pass": True}

    parent = QObject()
    before = len(parent.findChildren(QObject))
    for _ in range(200):
        child = QObject(parent)
        child.deleteLater()
    without_dispatch = len(parent.findChildren(QObject)) - before
    settle(app, 8)
    with_dispatch = len(parent.findChildren(QObject)) - before
    return {"created_and_deleted": 200,
            "alive_before_dispatch": without_dispatch,
            "alive_after_dispatch": with_dispatch,
            "pass": with_dispatch == 0,
            "note": "alive_before_dispatch shows what processEvents() alone "
                    "leaves behind; it is not a defect, it is the reason this "
                    "control exists"}


def run_calibration(app=None) -> dict:
    a = control_a_known_allocation()
    b = control_b_released_allocation()
    c = control_c_intentional_leak()
    d = control_d_no_op_noise(app)
    e = control_e_object_lifecycle(app)
    report = {
        "purpose": "prove the measurement detects memory before it is used to "
                   "claim there is none",
        "control_a_known_allocation": a,
        "control_b_released_allocation": b,
        "control_c_intentional_leak": c,
        "control_d_no_op_noise": d,
        "control_e_object_lifecycle": e,
        "metrics": ["private_mb (PrivateUsage)",
                    "working_set_mb (WorkingSetSize)"],
        "tracemalloc_note": "tracemalloc does not observe Qt/native "
                            "allocations; a flat tracemalloc is not evidence "
                            "that native memory is flat",
    }
    report["verdict"] = ("PASS" if a["pass"] and b["pass"] and c["pass"]
                         and e["pass"] else "FAIL")
    return report


def main() -> int:
    from PySide6.QtCore import QCoreApplication

    OUT.mkdir(parents=True, exist_ok=True)
    app = QCoreApplication.instance() or QCoreApplication(sys.argv[:1])
    report = run_calibration(app)
    (OUT / "harness_calibration.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "no_op_noise.json").write_text(
        json.dumps(report["control_d_no_op_noise"], indent=2),
        encoding="utf-8")

    a = report["control_a_known_allocation"]
    b = report["control_b_released_allocation"]
    c = report["control_c_intentional_leak"]
    d = report["control_d_no_op_noise"]
    print(f"A known 40 MB      seen private {a['seen']['private_mb']:.2f} MB, "
          f"ws {a['seen']['working_set_mb']:.2f} MB -> "
          f"{'ok' if a['pass'] else 'FAIL'}")
    print(f"B released         retained private "
          f"{b['retained']['private_mb']:.2f} MB -> "
          f"{'ok' if b['pass'] else 'FAIL'}")
    print(f"C leak 8 MB/round  measured "
          f"{c['measured_slope_mb_per_round']:.2f} MB/round -> "
          f"{'ok' if c['pass'] else 'FAIL'}")
    print(f"D no-op noise      total {d['total_mb']:.3f} MB, slope "
          f"{d['slope_mb_per_round']:.4f} MB/round, p2p "
          f"{d['peak_to_peak_mb']:.4f} MB")
    e = report["control_e_object_lifecycle"]
    if "skipped" in e:
        print(f"E object lifecycle  skipped ({e['skipped']})")
    else:
        print(f"E object lifecycle  {e['alive_before_dispatch']} alive without "
              f"dispatch, {e['alive_after_dispatch']} with -> "
              f"{'ok' if e['pass'] else 'FAIL'}")
    print(report["verdict"])
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

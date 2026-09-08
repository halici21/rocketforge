"""What the visual pilot costs at runtime.

A schematic canvas, a metric hierarchy and two breakdowns replaced a flat list
of rows. That is more to lay out and something to paint, so the question is
whether the workspace still opens, publishes and sits still as cheaply as it
did.

    python experiments/ui_visual_pilot/performance_benchmark.py <before|after>

"before" runs the same measurements against the PRE-PILOT interface preserved
in dist/RocketForge/_internal/ui, so the memory figure has something to be
compared with instead of an invented ceiling.

Five measurements:

  1. PAGE CREATION -- building the workspace from its QML component.
  2. SOLVED PUBLICATION -- calculate() to every readout property being
     readable, which is what a user waits for.
  3. NOZZLE REPAINT -- a changed expansion ratio, drawn.
  4. IDLE -- event-loop work with nothing happening. A canvas that animates
     when it should be still would show here.
  5. MEMORY -- resident set across repeated solve/redraw rounds, to catch a
     canvas or a model that accumulates.

Budgets are deliberate and stated with each result. They are not tuned to
whatever the run produced: a number over budget is printed as OVER and the exit
status is non-zero.

MEMORY IS JUDGED AS A COMPARISON, NOT AGAINST A NUMBER. Repeated recalculation
retains memory in the QML layer on BOTH designs -- measured here at 60.1 MB per
60 solves before the pilot and 28.9 MB after, under an identical script. That
is a pre-existing characteristic of the interface layer and not something this
pilot introduced or is scoped to fix; it is recorded as a finding. What the
pilot is accountable for is not making it worse, so the gate is a regression
gate against the before tree, and the absolute figure is reported beside it.
"""
from __future__ import annotations

import ctypes
import gc
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "ui_visual_pilot"

LABEL = sys.argv[1] if len(sys.argv) > 1 else "after"
#: the pre-pilot interface, as shipped by the last build before the redesign
UI_TREE = ((ROOT / "ui") if LABEL == "after"
           else ROOT / "dist" / "RocketForge" / "_internal" / "ui")

BUDGET = {
    "page_creation_ms": 400.0,
    "solved_publication_ms": 50.0,
    "nozzle_repaint_ms": 50.0,
    "idle_ms_per_second": 60.0,
}

#: memory is a regression gate: the pilot may not retain more than the design
#: it replaced, measured by this same script against that design's own tree.
MEMORY_REGRESSION_ALLOWANCE = 1.10


class _Counters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


_K32 = ctypes.WinDLL("kernel32", use_last_error=True)
# Without explicit signatures ctypes returns the GetCurrentProcess pseudo-handle
# as a 32-bit int and truncates it, and the call fails with ERROR_INVALID_HANDLE.
_K32.GetCurrentProcess.restype = ctypes.c_void_p
_K32.GetCurrentProcess.argtypes = []
_K32.K32GetProcessMemoryInfo.restype = ctypes.c_int
_K32.K32GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,
                                         ctypes.POINTER(_Counters),
                                         ctypes.c_uint32]


def rss_mb() -> float:
    """Resident set in MB.

    psutil is not a dependency of this project, so this reads the working set
    straight from Windows. The entry point is K32GetProcessMemoryInfo in
    kernel32 -- the psapi.dll export answers on some systems and not on this
    one, where it silently returned zero and made a leak check that could not
    have detected 40 MB report a clean 0.000. The return value is checked, and
    self_check() below proves the reading moves.
    """
    counters = _Counters()
    counters.cb = ctypes.sizeof(_Counters)
    ok = _K32.K32GetProcessMemoryInfo(_K32.GetCurrentProcess(),
                                      ctypes.byref(counters), counters.cb)
    if not ok:
        raise OSError("K32GetProcessMemoryInfo failed: "
                      f"{ctypes.get_last_error()}")
    return counters.WorkingSetSize / (1024 * 1024)


def self_check() -> float:
    """Prove the probe can see memory before trusting it to say there is none."""
    before = rss_mb()
    ballast = [bytearray(1024 * 1024) for _ in range(40)]
    for block in ballast:
        block[0] = 1          # touch each page so it is resident
    seen = rss_mb() - before
    del ballast
    gc.collect()
    return seen


def main() -> int:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    ui_dir = UI_TREE
    engine.addImportPath(str(ui_dir))
    engine.load(QUrl.fromLocalFile(str(ui_dir / "Main.qml")))
    roots = engine.rootObjects()
    if not roots:
        print("qml load failed")
        return 1
    window = roots[0]
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject {\n'
        b'  property var perf: RocketPerformance\n'
        b'  property var thermo: Thermochemistry\n'
        b'  property int idx: Navigation.indexOfKey("performance")\n}',
        QUrl.fromLocalFile(str(ui_dir / "_bench.qml")))
    holder = probe.create()
    if holder is None:
        print("probe failed:", probe.errorString())
        return 1
    controller = holder.property("perf")
    thermo = holder.property("thermo")
    window.setProperty("currentPageIndex", int(holder.property("idx")))

    def settle(rounds: int = 8) -> None:
        for _ in range(rounds):
            app.processEvents()

    if not thermo.property("providerAvailable"):
        print("no chemistry provider; benchmark needs a solved chamber")
        return 1
    thermo.resetInputs()
    thermo.calculate()
    settle()
    controller.resetInputs()
    controller.calculate()
    controller.showTab(0)
    settle(12)

    results: dict = {}

    # ---- 1. page creation -------------------------------------------------
    page_url = QUrl.fromLocalFile(str(ui_dir / "pages"
                                      / "RocketPerformancePage.qml"))
    component = QQmlComponent(engine, page_url)
    if component.isError():
        print("page component:", component.errorString())
        return 1
    samples = []
    for _ in range(7):
        gc.collect()
        start = time.perf_counter()
        instance = component.create()
        settle(4)
        samples.append((time.perf_counter() - start) * 1000.0)
        if instance is not None:
            instance.deleteLater()
        settle(2)
    results["page_creation_ms"] = round(min(samples), 2)
    results["page_creation_samples_ms"] = [round(s, 2) for s in samples]

    # ---- 2. solved publication -------------------------------------------
    READOUTS = ("headlineMetrics", "thrustCoefficientBreakdown",
                "thrustBreakdown", "exitStateRows", "traceRows",
                "solvedRadiusRatio", "pressureRelationText", "regimeLabel",
                "resultHeadline", "solvedChamberPressureText")
    samples = []
    for index in range(12):
        controller.setProperty("areaRatio", 30.0 + index)
        start = time.perf_counter()
        controller.calculate()
        for name in READOUTS:
            controller.property(name)
        samples.append((time.perf_counter() - start) * 1000.0)
        settle(2)
    results["solved_publication_ms"] = round(min(samples), 3)
    results["solved_publication_worst_ms"] = round(max(samples), 3)

    # ---- 3. nozzle repaint ------------------------------------------------
    samples = []
    for index in range(12):
        controller.setProperty("areaRatio", 20.0 + index * 5)
        controller.calculate()
        start = time.perf_counter()
        settle(10)          # let the canvas take its repaint
        samples.append((time.perf_counter() - start) * 1000.0)
    results["nozzle_repaint_ms"] = round(min(samples), 2)
    results["nozzle_repaint_worst_ms"] = round(max(samples), 2)

    # ---- 4. idle ----------------------------------------------------------
    controller.resetInputs()
    controller.calculate()
    settle(12)
    # CPU time, not a busy-poll fraction. The first version of this called
    # processEvents() in a tight loop and measured how long its own polling
    # took, which is a measurement of the harness rather than of the workspace.
    cpu_before = time.process_time()
    wall_before = time.perf_counter()
    deadline = wall_before + 3.0
    while time.perf_counter() < deadline:
        app.processEvents()
        time.sleep(0.02)
    wall = time.perf_counter() - wall_before
    cpu = time.process_time() - cpu_before
    results["idle_ms_per_second"] = round(cpu / wall * 1000.0, 2)
    results["idle_window_s"] = round(wall, 2)

    # ---- 5. memory --------------------------------------------------------
    gc.collect()
    settle(10)
    detected = self_check()
    settle(6)
    gc.collect()
    before = rss_mb()
    trace = []
    for round_index in range(10):
        for index in range(10):
            controller.setProperty("areaRatio", 10.0 + index * 7)
            controller.setProperty("ambientMode",
                                   "vacuum" if index % 2 else "sea_level")
            controller.calculate()
        controller.showTab(1)
        controller.showTab(2)
        controller.showTab(0)
        window.setProperty("themeMode", "light")
        window.setProperty("themeMode", "dark")
        settle(6)
        trace.append(round(rss_mb() - before, 3))
    gc.collect()
    settle(10)
    results["memory_growth_mb"] = round(rss_mb() - before, 3)
    results["memory_trace_mb"] = trace
    results["memory_monotonic"] = all(b >= a for a, b in zip(trace, trace[1:]))
    results["memory_probe_saw_mb"] = round(detected, 2)

    over = {name: results[name] for name, budget in BUDGET.items()
            if results[name] > budget}
    # A leak check that cannot see memory is not a leak check.
    if detected < 20.0:
        over["memory_probe_blind"] = round(detected, 2)

    report = {"purpose": "what the visual pilot costs at runtime",
              "ui_tree": str(UI_TREE.relative_to(ROOT).as_posix()),
              "label": LABEL, "budgets": BUDGET, "results": results}

    # memory: a regression gate against the design this one replaced
    baseline_path = OUT / "performance_before.json"
    if LABEL == "after" and baseline_path.is_file():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        was = baseline["results"]["memory_growth_mb"]
        now = results["memory_growth_mb"]
        allowed = was * MEMORY_REGRESSION_ALLOWANCE
        report["memory_regression"] = {
            "before_mb": was, "after_mb": now,
            "allowance": MEMORY_REGRESSION_ALLOWANCE,
            "allowed_mb": round(allowed, 2),
            "ratio": round(now / was, 3) if was else None,
            "pass": now <= allowed,
            "note": "Repeated recalculation retains memory in the QML layer on "
                    "both designs. It is pre-existing, it is not what this "
                    "pilot changed, and it is recorded as a finding rather "
                    "than folded into a budget that would hide it.",
        }
        if not report["memory_regression"]["pass"]:
            over["memory_growth_mb"] = now

    report["over_budget"] = over
    report["verdict"] = "PASS" if not over else "FAIL"
    (OUT / f"performance_{LABEL}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print(f"[{LABEL}] {UI_TREE}")
    for name, budget in BUDGET.items():
        value = results[name]
        mark = "OVER" if value > budget else "ok  "
        print(f"  {mark} {name:24s} {value:>10.3f}  (budget {budget})")
    print(f"       {'memory_growth_mb':24s} "
          f"{results['memory_growth_mb']:>10.3f}  (compared, not budgeted)")
    if "memory_regression" in report:
        m = report["memory_regression"]
        print(f"  {'ok  ' if m['pass'] else 'OVER'} memory vs the design it "
              f"replaced: {m['after_mb']} MB vs {m['before_mb']} MB "
              f"(x{m['ratio']})")
    print(f"  memory probe saw a deliberate 40 MB as {detected:.2f} MB")
    print(f"  memory trace (MB): {trace}")
    print(f"  memory monotonic:  {results['memory_monotonic']}")
    print(report["verdict"])
    return 0 if not over else 1


if __name__ == "__main__":
    sys.exit(main())

"""Reproduce the rendered-QML retention and say what is accumulating.

Bytes alone cannot distinguish a live-object leak from an allocator high-water
mark, so every round records three things together: process memory (private
bytes and working set), a census of live QObjects by class beneath the window,
and Python's own allocation total.

    python experiments/qml_memory/measure.py [--rounds N] [--per-round N]
                                             [--variant NAME] [--out FILE]

Variants are runtime ablations of the *accepted* page -- nothing in production
QML is edited to run them.
"""
from __future__ import annotations

import argparse
import collections
import gc
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))

from harness import (memory, delta, slope_mb_per_round,
                     control_d_no_op_noise, settle as _settle)

OUT = ROOT / "acceptance" / "qml_memory"


#: the accepted pilot's QML, preserved before this program changed anything
BASELINE_UI = (ROOT / "acceptance" / "ui_rollout" / "baseline_snapshot"
               / "source" / "ui")


def build(width: int = 1920, height: int = 1080, ui_tree=None):
    """A loaded application on the Rocket Performance workspace."""
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    messages: list[dict] = []
    kinds = {QtMsgType.QtDebugMsg: "debug", QtMsgType.QtInfoMsg: "info",
             QtMsgType.QtWarningMsg: "warning",
             QtMsgType.QtCriticalMsg: "critical",
             QtMsgType.QtFatalMsg: "fatal"}

    def handler(kind, context, message):
        messages.append({"kind": kinds.get(kind, str(kind)),
                         "message": message})

    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    ui = ui_tree or app_main.UI_DIR
    engine.addImportPath(str(ui))
    engine.load(QUrl.fromLocalFile(str(ui / "Main.qml")))
    roots = engine.rootObjects()
    if not roots:
        raise SystemExit("qml load failed")
    window = roots[0]
    window.setProperty("width", width)
    window.setProperty("height", height)

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject {\n'
        b'  property var perf: RocketPerformance\n'
        b'  property var thermo: Thermochemistry\n'
        b'  property int perfIdx: Navigation.indexOfKey("performance")\n'
        b'  property int otherIdx: Navigation.indexOfKey("isentropic")\n}',
        QUrl.fromLocalFile(str(ui / "_mem.qml")))
    holder = probe.create()
    if holder is None:
        raise SystemExit(f"probe failed: {probe.errorString()}")
    # `probe` must outlive this function: when the component is collected it
    # takes its instance with it and every later property read raises
    # "Internal C++ object already deleted".
    return app, engine, window, holder, messages, probe


def census(window) -> dict:
    """Live QObjects beneath the window, counted by class."""
    from PySide6.QtCore import QObject

    children = window.findChildren(QObject)
    names = collections.Counter()
    for child in children:
        name = child.metaObject().className()
        name = name.split("_QMLTYPE_")[0].split("_QML_")[0]
        names[name] += 1
    return {"total": len(children), "by_class": dict(names)}


def census_delta(before: dict, after: dict, top: int = 20) -> dict:
    keys = set(before["by_class"]) | set(after["by_class"])
    moved = {k: after["by_class"].get(k, 0) - before["by_class"].get(k, 0)
             for k in keys}
    moved = {k: v for k, v in moved.items() if v}
    ranked = sorted(moved.items(), key=lambda kv: -abs(kv[1]))[:top]
    return {"total": after["total"] - before["total"], "by_class": dict(ranked)}


# --- runtime ablations of the accepted page --------------------------------

def find_by_class(window, suffix: str) -> list:
    from PySide6.QtCore import QObject

    hits = []
    for child in window.findChildren(QObject):
        name = child.metaObject().className()
        if name.split("_QMLTYPE_")[0].split("_QML_")[0].endswith(suffix):
            hits.append(child)
    return hits


VARIANTS = {
    "v0_full": "the accepted pilot, unmodified",
    "v1_no_hero": "the schematic canvas hidden",
    "v2_static_hero": "hero visible, its ratio animation disabled",
    "v3_no_animation": "every Behavior/animation on the page disabled",
    "v4_no_result_rail": "the readout rail hidden",
    "v5_no_trace": "the model trace hidden",
    "v6_no_input_rail": "the input rail hidden",
    "v9_page_no_publication": "page rendered, no recalculation published",
    "v10_no_page": "controller publishes, page never shown",
}


def apply_variant(window, holder, name: str) -> dict:
    """Hide or disable parts of the real page. Returns what was affected."""
    from PySide6.QtCore import QObject

    touched: dict[str, int] = {}

    def hide(suffix: str) -> int:
        items = find_by_class(window, suffix)
        for item in items:
            item.setProperty("visible", False)
        return len(items)

    if name == "v1_no_hero":
        touched["PerfNozzleCanvas hidden"] = hide("PerfNozzleCanvas")
    elif name == "v2_static_hero":
        for item in find_by_class(window, "PerfNozzleCanvas"):
            for child in item.findChildren(QObject):
                cls = child.metaObject().className()
                if "Behavior" in cls or "Animation" in cls:
                    child.setProperty("enabled", False)
                    touched["hero animations disabled"] = \
                        touched.get("hero animations disabled", 0) + 1
    elif name == "v3_no_animation":
        for child in window.findChildren(QObject):
            cls = child.metaObject().className()
            if "Behavior" in cls or "Animation" in cls:
                child.setProperty("enabled", False)
                touched["animations disabled"] = \
                    touched.get("animations disabled", 0) + 1
    elif name == "v4_no_result_rail":
        touched["PerfMetricReadout hidden"] = hide("PerfMetricReadout")
        touched["PerfBreakdown hidden"] = hide("PerfBreakdown")
    elif name == "v5_no_trace":
        touched["PerfPressureRelation hidden"] = hide("PerfPressureRelation")
    elif name == "v6_no_input_rail":
        touched["RFSelect hidden"] = hide("RFSelect")
    elif name == "v10_no_page":
        window.setProperty("currentPageIndex", int(holder.property("otherIdx")))
        touched["navigated away"] = 1
    return touched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--per-round", type=int, default=10)
    parser.add_argument("--variant", default="v0_full")
    parser.add_argument("--out", default=None)
    parser.add_argument("--ui", choices=("current", "baseline"),
                        default="current",
                        help="which QML tree to measure")
    parser.add_argument("--tabs", action="store_true",
                        help="switch Performance/Model/Oracle each round")
    parser.add_argument("--theme", action="store_true",
                        help="switch light/dark each round")
    parser.add_argument("--ambient", action="store_true",
                        help="alternate ambient mode with each recalculation")
    parser.add_argument("--gc-each-round", action="store_true")
    parser.add_argument("--qml-gc-each-round", action="store_true")
    args = parser.parse_args()

    app, engine, window, holder, messages, _probe = build(
        ui_tree=BASELINE_UI if args.ui == "baseline" else None)
    controller = holder.property("perf")
    thermo = holder.property("thermo")

    def settle(n: int = 8) -> None:
        _settle(app, n)

    if not thermo.property("providerAvailable"):
        print("no chemistry provider")
        return 1
    thermo.resetInputs()
    thermo.calculate()
    settle()

    window.setProperty("currentPageIndex", int(holder.property("perfIdx")))
    controller.resetInputs()
    controller.calculate()
    controller.showTab(0)
    settle(16)

    touched = apply_variant(window, holder, args.variant)
    settle(10)

    # a Qt-app noise floor, not the bare-Python one
    noise = control_d_no_op_noise(app, rounds=6, iterations=50)

    gc.collect()
    settle(10)
    base_mem = memory()
    base_census = census(window)
    series: list[dict] = []
    start = time.perf_counter()

    for index in range(args.rounds):
        if args.variant != "v9_page_no_publication":
            for step in range(args.per_round):
                controller.setProperty("areaRatio", 10.0 + (step % 12) * 7)
                if args.ambient:
                    controller.setProperty(
                        "ambientMode", "vacuum" if step % 2 else "sea_level")
                controller.calculate()
        if args.tabs:
            controller.showTab(1)
            controller.showTab(2)
            controller.showTab(0)
        if args.theme:
            window.setProperty("themeMode", "light")
            window.setProperty("themeMode", "dark")
        settle(6)
        if args.gc_each_round:
            gc.collect()
        if args.qml_gc_each_round:
            engine.collectGarbage()
        now = memory()
        series.append({"round": index + 1,
                       "recalculations": (index + 1) * args.per_round,
                       **delta(base_mem, now),
                       "objects": census(window)["total"] - base_census["total"]})

    final_census = census(window)
    elapsed = time.perf_counter() - start
    private = [row["private_mb"] for row in series]
    working = [row["working_set_mb"] for row in series]
    half = len(private) // 2

    report = {
        "ui_tree": args.ui,
        "variant": args.variant,
        "variant_description": VARIANTS.get(args.variant, "custom"),
        "variant_touched": touched,
        "rounds": args.rounds,
        "per_round": args.per_round,
        "recalculations": args.rounds * args.per_round,
        "workload": {"tabs": args.tabs, "theme": args.theme,
                     "ambient": args.ambient},
        "gc_each_round": args.gc_each_round,
        "qml_gc_each_round": args.qml_gc_each_round,
        "qt_noise_floor": noise,
        "series": series,
        "private_total_mb": private[-1] if private else 0.0,
        "working_total_mb": working[-1] if working else 0.0,
        "private_slope_mb_per_round": round(slope_mb_per_round(private), 4),
        "first_half_mb": round(private[half - 1], 3) if half else 0.0,
        "second_half_mb": round(private[-1] - private[half - 1], 3)
        if half else 0.0,
        "object_delta": census_delta(base_census, final_census),
        "elapsed_s": round(elapsed, 2),
        "qt_warnings": [m for m in messages
                        if m["kind"] in ("warning", "critical", "fatal")],
    }

    name = args.out or f"variant_{args.variant}.json"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[{args.variant}] {report['recalculations']} recalculations "
          f"in {elapsed:.1f}s")
    print(f"  private  {report['private_total_mb']:8.2f} MB   slope "
          f"{report['private_slope_mb_per_round']:7.3f} MB/round")
    print(f"  working  {report['working_total_mb']:8.2f} MB")
    print(f"  halves   {report['first_half_mb']:.2f} then "
          f"{report['second_half_mb']:.2f} MB")
    print(f"  objects  {report['object_delta']['total']:+d}")
    for cls, n in list(report["object_delta"]["by_class"].items())[:10]:
        print(f"      {n:+6d}  {cls}")
    print(f"  qt noise floor {noise['total_mb']:.3f} MB over "
          f"{noise['rounds']} rounds")
    if report["qt_warnings"]:
        print(f"  QT WARNINGS: {len(report['qt_warnings'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

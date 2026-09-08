"""Longevity soaks: page lifecycle, and a mixed multi-workspace session.

Repeated recalculation on one page is only one way an application accumulates.
These two ask the other questions:

  lifecycle   open the workspace, work in it, leave, come back -- many times.
              A page that is rebuilt rather than reused, or whose old instance
              is never released, shows up as page-object growth.

  session     move through every workspace repeatedly, solving in each, then
              return to Rocket Performance and check the canonical result is
              still the same numbers.

    python experiments/qml_memory/soak.py --mode lifecycle|session
"""
from __future__ import annotations

import argparse
import gc
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))

from harness import memory, delta, slope_mb_per_round
from harness import settle as _settle
from measure import build, census

OUT = ROOT / "acceptance" / "qml_memory"

WORKSPACES = ("performance", "thermochemistry", "fluidproperties", "line",
              "tradestudy", "enginedesign", "isentropic", "nozzlelab")


def page_instances(window) -> int:
    """How many Rocket Performance pages are alive under the window."""
    from PySide6.QtCore import QObject

    count = 0
    for child in window.findChildren(QObject):
        name = child.metaObject().className()
        name = name.split("_QMLTYPE_")[0].split("_QML_")[0]
        if name in ("PerfCalculator", "RocketPerformancePage"):
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("lifecycle", "session"),
                        required=True)
    parser.add_argument("--rounds", type=int, default=40)
    args = parser.parse_args()

    app, engine, window, holder, messages, _probe = build()
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

    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent

    nav = QQmlComponent(engine)
    nav.setData(
        b'import QtQuick\nimport "data"\nQtObject {\n'
        + b"".join(f'  property int i_{name}: '
                   f'Navigation.indexOfKey("{name}")\n'.encode()
                   for name in WORKSPACES)
        + b'}',
        QUrl.fromLocalFile(str(ROOT / "ui" / "_nav.qml")))
    holder2 = nav.create()
    if holder2 is None:
        print("nav probe failed:", nav.errorString())
        return 1
    indices = {name: int(holder2.property(f"i_{name}"))
               for name in WORKSPACES}
    indices = {name: index for name, index in indices.items() if index >= 0}
    perf_index = indices.get("performance", 0)

    window.setProperty("currentPageIndex", perf_index)
    controller.resetInputs()
    controller.calculate()
    controller.showTab(0)
    settle(16)

    canonical = {
        "isp": controller.property("resultHeadline"),
        "trace": [dict(row) for row in (controller.property("traceRows") or [])],
        "headline": [dict(row) for row
                     in (controller.property("headlineMetrics") or [])],
    }

    gc.collect()
    settle(10)
    base = memory()
    base_objects = census(window)["total"]
    base_pages = page_instances(window)
    series = []
    pages = []

    other = [index for name, index in indices.items()
             if name != "performance"] or [perf_index]

    for round_index in range(args.rounds):
        if args.mode == "lifecycle":
            window.setProperty("currentPageIndex", other[0])
            settle(4)
            window.setProperty("currentPageIndex", perf_index)
            settle(4)
            for step in range(5):
                controller.setProperty("areaRatio", 12.0 + step * 9)
                controller.calculate()
            settle(4)
        else:
            for index in other:
                window.setProperty("currentPageIndex", index)
                settle(3)
            window.setProperty("currentPageIndex", perf_index)
            for step in range(5):
                controller.setProperty("areaRatio", 12.0 + step * 9)
                controller.calculate()
            settle(4)
        series.append(delta(base, memory())["private_mb"])
        pages.append(page_instances(window) - base_pages)

    # back to the canonical case: the numbers must be the ones we started with
    controller.resetInputs()
    controller.calculate()
    settle(10)
    final = {
        "isp": controller.property("resultHeadline"),
        "trace": [dict(row) for row in (controller.property("traceRows") or [])],
        "headline": [dict(row) for row
                     in (controller.property("headlineMetrics") or [])],
    }
    identical = final == canonical

    half = len(series) // 2
    report = {
        "mode": args.mode,
        "rounds": args.rounds,
        "private_total_mb": round(series[-1], 3) if series else 0.0,
        "slope_mb_per_round": round(slope_mb_per_round(series), 4),
        "first_half_mb": round(series[half - 1], 3) if half else 0.0,
        "second_half_mb": round(series[-1] - series[half - 1], 3)
        if half else 0.0,
        "series": series,
        "page_instance_delta": pages[-1] if pages else 0,
        "page_instance_series": pages,
        "object_delta": census(window)["total"] - base_objects,
        "canonical_result_unchanged": identical,
        "qt_warnings": [m for m in messages
                        if m["kind"] in ("warning", "critical", "fatal")],
    }
    report["verdict"] = ("PASS" if identical
                         and report["second_half_mb"] <= max(
                             report["first_half_mb"], 1.0)
                         and report["page_instance_delta"] == 0
                         and not report["qt_warnings"] else "FAIL")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"soak_{args.mode}.json").write_text(json.dumps(report, indent=2),
                                                encoding="utf-8")
    print(f"[{args.mode}] {args.rounds} rounds")
    print(f"  private {report['private_total_mb']:8.2f} MB   slope "
          f"{report['slope_mb_per_round']:7.4f}")
    print(f"  halves  {report['first_half_mb']:.2f} then "
          f"{report['second_half_mb']:.2f} MB")
    print(f"  page instances {report['page_instance_delta']:+d}   objects "
          f"{report['object_delta']:+d}")
    print(f"  canonical result unchanged: "
          f"{report['canonical_result_unchanged']}")
    print(f"  qt warnings: {len(report['qt_warnings'])}")
    print(report["verdict"])
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

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

**Every route must resolve, and the report says which ones were visited.** An
earlier version named the workspaces ``"thermochemistry"`` and
``"enginedesign"``. Neither is a navigation key -- Thermochemistry is
``"thermochem"`` and Engine Design is an application mode, not a page -- and
unresolved keys were silently dropped, so the "session" soak never entered
either workspace while reporting PASS. Now an unresolved key stops the soak,
each visit is confirmed by finding the page actually shown, and the report
carries ``visited_routes`` and ``missing_routes``.
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

#: The analysis pages, by their navigation key. Rocket Performance first: it is
#: the page whose result must survive the session unchanged.
PAGES = ("performance", "thermochem", "fluidproperties", "line",
         "tradestudy", "isentropic", "nozzlelab")

#: Engine Design is entered through the application mode, not a page index.
ENGINE_DESIGN = "engine-design"

#: The solid grain the session solves: the published RP-1311 example.
SOLID_FORMULATION = "rp1311-example5"

#: What each mode must visit. The Thermochemistry entries are the parts of that
#: workspace a visit has to exercise, not only its page load.
REQUIRED_ROUTES = {
    "lifecycle": ("performance", "thermochem"),
    "session": PAGES + (ENGINE_DESIGN,
                        "thermochem:bipropellant", "thermochem:composition",
                        "thermochem:solid", "thermochem:solid-cstar"),
}


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


def shown(window, type_name: str) -> bool:
    """Whether a visible item of that QML type is in the window."""
    from PySide6.QtQuick import QQuickItem

    for item in window.findChildren(QQuickItem):
        name = item.metaObject().className()
        if (name.split("_QMLTYPE_")[0].split("_QML_")[0] == type_name
                and item.isVisible()):
            return True
    return False


def section_page(obj, depth: int = 0):
    """The current page's own item: the one with a ``section`` property."""
    if obj is None or depth > 14:
        return None
    if obj.metaObject().indexOfProperty("section") >= 0:
        return obj
    for child in obj.children():
        found = section_page(child, depth + 1)
        if found is not None:
            return found
    return None


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
                   f'Navigation.indexOfKey("{name}")\n'
                   f'  property string p_{name}: '
                   f'Navigation.indexOfKey("{name}") < 0 ? "" : '
                   f'Navigation.items[Navigation.indexOfKey("{name}")].page\n'
                   .encode()
                   for name in PAGES)
        + b'}',
        QUrl.fromLocalFile(str(ROOT / "ui" / "_nav.qml")))
    holder2 = nav.create()
    if holder2 is None:
        print("nav probe failed:", nav.errorString())
        return 1
    indices = {name: int(holder2.property(f"i_{name}")) for name in PAGES}
    unresolved = [name for name, index in indices.items() if index < 0]
    if unresolved:
        # Never drop a route: a soak that skips a workspace and still says
        # PASS is how Thermochemistry went unvisited.
        print(f"FAIL: unresolved navigation keys {unresolved}")
        return 1
    page_types = {name: pathlib.Path(str(holder2.property(f"p_{name}"))).stem
                  for name in PAGES}
    perf_index = indices["performance"]

    visits: dict[str, int] = {}

    def record(route: str) -> None:
        visits[route] = visits.get(route, 0) + 1

    def visit(name: str, rounds: int = 3) -> None:
        """Show a page and confirm it is the page on screen."""
        window.setProperty("currentPageIndex", indices[name])
        settle(rounds)
        if not shown(window, page_types[name]):
            raise SystemExit(f"FAIL: {name} ({page_types[name]}) is not shown")
        record(name)

    def set_section(route: str, section: int) -> None:
        page = section_page(window)
        if page is None:
            raise SystemExit(f"FAIL: no sectioned page for {route}")
        page.setProperty("section", section)
        settle(3)
        record(route)

    def solve_thermochemistry(kind: str) -> None:
        thermo.setProperty("formulationKind", kind)
        if kind == "solid":
            thermo.loadSolidFormulation(SOLID_FORMULATION)
        else:
            thermo.resetInputs()
        thermo.calculate()
        settle(3)
        if (thermo.property("formulationKind") != kind
                or not thermo.property("hasResult")):
            raise SystemExit(f"FAIL: no {kind} Thermochemistry result: "
                             f"{thermo.property('statusMessage')}")
        record(f"thermochem:{kind}")

    def chemistry_tour() -> None:
        """Bipropellant and solid, each on the calculator and the species."""
        visit("thermochem")
        set_section("thermochem:calculator", 0)
        solve_thermochemistry("bipropellant")
        set_section("thermochem:composition", 1)
        set_section("thermochem:calculator", 0)
        solve_thermochemistry("solid")
        if thermo.property("solidCStarShown"):
            record("thermochem:solid-cstar")
        set_section("thermochem:composition", 1)
        set_section("thermochem:calculator", 0)
        # Leave the chamber as it was, so Rocket Performance's canonical case
        # is still the one it started from.
        solve_thermochemistry("bipropellant")

    def engine_design() -> None:
        window.setProperty("appMode", "engine")
        settle(3)
        if not shown(window, "EngineWorkspace"):
            raise SystemExit("FAIL: Engine Design is not shown")
        record(ENGINE_DESIGN)
        window.setProperty("appMode", "analysis")
        settle(3)
        if shown(window, "EngineWorkspace"):
            raise SystemExit("FAIL: Engine Design is still shown in analysis")

    def thermo_snapshot() -> dict:
        return {"headline": thermo.property("resultHeadline"),
                "rows": [dict(row) for row
                         in (thermo.property("resultRows") or [])]}

    thermo_canonical = thermo_snapshot()

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

    others = [name for name in PAGES if name != "performance"]

    for round_index in range(args.rounds):
        if args.mode == "lifecycle":
            visit(others[0], 4)
            visit("performance", 4)
            for step in range(5):
                controller.setProperty("areaRatio", 12.0 + step * 9)
                controller.calculate()
            settle(4)
        else:
            for name in others:
                if name == "thermochem":
                    chemistry_tour()
                else:
                    visit(name)
            engine_design()
            visit("performance")
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
    thermo_identical = thermo_snapshot() == thermo_canonical

    required = REQUIRED_ROUTES[args.mode]
    missing = [route for route in required if route not in visits]

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
        "thermochemistry_result_unchanged": thermo_identical,
        "required_routes": list(required),
        "visited_routes": sorted(visits),
        "route_visits": dict(sorted(visits.items())),
        "missing_routes": missing,
        "qt_warnings": [m for m in messages
                        if m["kind"] in ("warning", "critical", "fatal")],
    }
    report["verdict"] = ("PASS" if identical and thermo_identical
                         and not missing
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
    print(f"  thermochemistry result unchanged: {thermo_identical}")
    print(f"  visited: {', '.join(report['visited_routes'])}")
    print(f"  missing: {', '.join(missing) or 'none'}")
    print(f"  qt warnings: {len(report['qt_warnings'])}")
    print(report["verdict"])
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

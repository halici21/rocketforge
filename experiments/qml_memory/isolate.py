"""Binary-search the publication path with a minimal page.

The feature ablation showed that hiding any individual part of the Rocket
Performance page changes nothing: the growth needs the page shown and a result
published, but is not attributable to the hero, the rails, the trace or the
animations. So the question is not *which component* but *which kind of
published value*.

This builds a minimal QML page that binds to exactly one chosen set of
controller properties and nothing else, then drives the same recalculation
workload. Production QML is not touched.

    python experiments/qml_memory/isolate.py --binding LIST [--rounds N]
    python experiments/qml_memory/isolate.py --all
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

# Each case is a fragment of QML placed inside one Item, binding only to what
# it names. "none" is the control: a rendered page that reads nothing.
CASES: dict[str, str] = {
    "none": "",
    "scalar_real": '''
        Text { text: "" + RocketPerformance.solvedRadiusRatio }
    ''',
    "scalar_bool": '''
        Text { text: RocketPerformance.resultStale ? "s" : "f" }
    ''',
    "string": '''
        Text { text: RocketPerformance.resultHeadline }
    ''',
    "string_many": '''
        Column {
            Text { text: RocketPerformance.resultHeadline }
            Text { text: RocketPerformance.pressureRelationText }
            Text { text: RocketPerformance.regimeLabel }
            Text { text: RocketPerformance.statusLabel }
            Text { text: RocketPerformance.message }
            Text { text: RocketPerformance.solvedChamberPressureText }
        }
    ''',
    # a list-valued property read, but never expanded into delegates
    "list_read_only": '''
        Text { text: "" + RocketPerformance.headlineMetrics.length }
    ''',
    "list_read_only_all": '''
        Text {
            text: "" + RocketPerformance.headlineMetrics.length
                     + RocketPerformance.thrustCoefficientBreakdown.length
                     + RocketPerformance.thrustBreakdown.length
                     + RocketPerformance.exitStateRows.length
                     + RocketPerformance.traceRows.length
        }
    ''',
    # the same list, expanded through a Repeater into real delegates
    "list_repeater": '''
        Column {
            Repeater {
                model: RocketPerformance.headlineMetrics
                delegate: Text {
                    required property var modelData
                    text: modelData.value + " " + modelData.unit
                }
            }
        }
    ''',
    "list_repeater_all": '''
        Column {
            Repeater {
                model: RocketPerformance.headlineMetrics
                delegate: Text {
                    required property var modelData
                    text: modelData.value + " " + modelData.unit
                }
            }
            Repeater {
                model: RocketPerformance.thrustCoefficientBreakdown
                delegate: Text {
                    required property var modelData
                    text: modelData.value
                }
            }
            Repeater {
                model: RocketPerformance.exitStateRows
                delegate: Text {
                    required property var modelData
                    text: modelData.value
                }
            }
            Repeater {
                model: RocketPerformance.traceRows
                delegate: Text {
                    required property var modelData
                    text: modelData.value
                }
            }
        }
    ''',
    # the legacy grouped structure, a list of dicts each holding a list
    "nested_result_groups": '''
        Column {
            Repeater {
                model: RocketPerformance.resultGroups
                delegate: Column {
                    required property var modelData
                    Repeater {
                        model: modelData.rows
                        delegate: Text {
                            required property var modelData
                            text: modelData.value
                        }
                    }
                }
            }
        }
    ''',
}

# Candidate fixes, measured before any of them is adopted.
FIX_CASES = {
    # the same rows, delivered by a QAbstractListModel updated in place
    "fix_stable_model": '''
        Column {
            Repeater {
                model: HeadlineModel
                delegate: Text {
                    required property string value
                    required property string unit
                    text: value + " " + unit
                }
            }
        }
    ''',
    # the same rows, but the property hands back an identical cached object
    # when nothing changed -- tests whether the cost is the conversion or the
    # rebuilding
    "fix_cached_list": '''
        Column {
            Repeater {
                model: CachedRows.rows
                delegate: Text {
                    required property var modelData
                    text: modelData.value + " " + modelData.unit
                }
            }
        }
    ''',
}
CASES.update(FIX_CASES)


PAGE = '''import QtQuick
import RocketForge 1.0

Item {{
    width: 1200
    height: 800
    {body}
}}
'''


def install_fix_helpers(engine, controller, name: str):
    """A stable model and a caching adapter, for the candidate-fix cases."""
    from PySide6.QtCore import (QAbstractListModel, QByteArray, QModelIndex,
                                QObject, Qt, Property, Signal)

    kept = []

    class HeadlineModel(QAbstractListModel):
        ValueRole = Qt.ItemDataRole.UserRole + 1
        UnitRole = Qt.ItemDataRole.UserRole + 2

        def __init__(self, source):
            super().__init__()
            self._source = source
            self._rows: list[dict] = []
            source.resultChanged.connect(self.refresh)
            self.refresh()

        def roleNames(self):
            return {self.ValueRole: QByteArray(b"value"),
                    self.UnitRole: QByteArray(b"unit")}

        def rowCount(self, parent=QModelIndex()):
            return 0 if parent.isValid() else len(self._rows)

        def data(self, index, role=Qt.ItemDataRole.DisplayRole):
            if not index.isValid() or not 0 <= index.row() < len(self._rows):
                return None
            row = self._rows[index.row()]
            if role == self.ValueRole:
                return str(row.get("value", ""))
            if role == self.UnitRole:
                return str(row.get("unit", ""))
            return None

        def refresh(self):
            incoming = list(self._source.headlineMetrics or [])
            # update in place; only signal a structural change when the row
            # count actually moves
            if len(incoming) != len(self._rows):
                self.beginResetModel()
                self._rows = incoming
                self.endResetModel()
                return
            self._rows = incoming
            if self._rows:
                self.dataChanged.emit(self.index(0, 0),
                                      self.index(len(self._rows) - 1, 0),
                                      [self.ValueRole, self.UnitRole])

    class CachedRows(QObject):
        rowsChanged = Signal()

        def __init__(self, source):
            super().__init__()
            self._source = source
            self._cache: list = []
            self._signature = None
            source.resultChanged.connect(self._refresh)
            self._refresh()

        def _refresh(self):
            incoming = list(self._source.headlineMetrics or [])
            signature = repr(incoming)
            if signature == self._signature:
                return               # identical content: publish nothing
            self._signature = signature
            self._cache = incoming
            self.rowsChanged.emit()

        @Property("QVariantList", notify=rowsChanged)
        def rows(self):
            return self._cache

    if name == "fix_stable_model":
        model = HeadlineModel(controller)
        kept.append(model)
        engine.rootContext().setContextProperty("HeadlineModel", model)
    elif name == "fix_cached_list":
        cached = CachedRows(controller)
        kept.append(cached)
        engine.rootContext().setContextProperty("CachedRows", cached)
    return kept


def run_case(name: str, rounds: int, per_round: int) -> dict:
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent

    app, engine, window, holder, messages, _probe = build()
    controller = holder.property("perf")
    thermo = holder.property("thermo")

    def settle(n: int = 8) -> None:
        _settle(app, n)

    if not thermo.property("providerAvailable"):
        raise SystemExit("no chemistry provider")
    thermo.resetInputs()
    thermo.calculate()
    settle()
    controller.resetInputs()
    controller.calculate()
    settle(8)

    # helpers for the candidate-fix cases, registered before the page loads
    helpers = install_fix_helpers(engine, controller, name)

    # a bare page, parented into the live window so it renders
    component = QQmlComponent(engine)
    component.setData(PAGE.format(body=CASES[name]).encode(),
                      QUrl.fromLocalFile(str(ROOT / "ui" / "_isolate.qml")))
    if component.isError():
        raise SystemExit(f"{name}: {component.errorString()}")
    item = component.create()
    if item is None:
        raise SystemExit(f"{name}: create failed")
    item.setParent(window)
    item.setProperty("parent", window)
    settle(12)

    gc.collect()
    settle(10)
    base = memory()
    base_objects = census(window)["total"]
    series = []
    for _ in range(rounds):
        for step in range(per_round):
            controller.setProperty("areaRatio", 10.0 + (step % 12) * 7)
            controller.calculate()
        settle(6)
        series.append(delta(base, memory())["private_mb"])
    objects = census(window)["total"] - base_objects

    return {"case": name, "rounds": rounds, "per_round": per_round,
            "recalculations": rounds * per_round,
            "private_total_mb": round(series[-1], 3) if series else 0.0,
            "slope_mb_per_round": round(slope_mb_per_round(series), 4),
            "series": series, "object_delta": objects,
            "qt_warnings": len([m for m in messages
                                if m["kind"] in ("warning", "critical",
                                                 "fatal")])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binding", default=None, choices=sorted(CASES))
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--per-round", type=int, default=10)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if not args.all and args.binding is None:
        parser.error("pass --binding NAME or --all")

    # One case per process: a QQmlEngine cannot be torn down and rebuilt
    # cleanly in-process, and sharing one would let an earlier case's
    # allocations contaminate the next.
    name = args.binding
    result = run_case(name, args.rounds, args.per_round)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"isolate_{name}.json").write_text(json.dumps(result, indent=2),
                                              encoding="utf-8")
    print(f"{name:24s} {result['private_total_mb']:8.2f} MB   slope "
          f"{result['slope_mb_per_round']:7.3f} MB/round   objects "
          f"{result['object_delta']:+d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

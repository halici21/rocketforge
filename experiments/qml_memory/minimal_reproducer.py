"""A framework-level reproducer, with no RocketForge code in it at all.

If repeatedly publishing a QVariantList property to a QML binding retains
memory in a program this small, the behaviour belongs to PySide6/Qt and not to
RocketForge, and the application's job is to choose a publication pattern that
does not trigger it.

Three publishers, identical data, identical update rate:

  list    a @Property("QVariantList") rebuilt and re-read on every change
  model   a QAbstractListModel updated in place
  scalar  plain string properties

    python experiments/qml_memory/minimal_reproducer.py [--rounds N]

Nothing here imports rocketforge. The only dependency is PySide6.
"""
from __future__ import annotations

import argparse
import ctypes
import gc
import json
import pathlib
import sys

MB = 1024 * 1024
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "acceptance" / "qml_memory"


class _CountersEx(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
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
_K32.GetCurrentProcess.restype = ctypes.c_void_p
_K32.GetCurrentProcess.argtypes = []
_K32.K32GetProcessMemoryInfo.restype = ctypes.c_int
_K32.K32GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,
                                         ctypes.POINTER(_CountersEx),
                                         ctypes.c_uint32]


def private_mb() -> float:
    c = _CountersEx()
    c.cb = ctypes.sizeof(_CountersEx)
    if not _K32.K32GetProcessMemoryInfo(_K32.GetCurrentProcess(),
                                        ctypes.byref(c), c.cb):
        raise OSError(ctypes.get_last_error())
    return c.PrivateUsage / MB


def slope(series: list[float]) -> float:
    n = len(series)
    if n < 2:
        return 0.0
    mx = (n - 1) / 2.0
    my = sum(series) / n
    num = sum((i - mx) * (y - my) for i, y in enumerate(series))
    den = sum((i - mx) ** 2 for i in range(n))
    return num / den if den else 0.0


PAGES = {
    "list": '''import QtQuick
Item {
    width: 900; height: 600
    Column {
        Repeater {
            model: Source.rows
            delegate: Text {
                required property var modelData
                text: modelData.label + " " + modelData.value
            }
        }
    }
}
''',
    "model": '''import QtQuick
Item {
    width: 900; height: 600
    Column {
        Repeater {
            model: Source
            delegate: Text {
                required property string label
                required property string value
                text: label + " " + value
            }
        }
    }
}
''',
    "scalar": '''import QtQuick
Item {
    width: 900; height: 600
    Column {
        Text { text: Source.v0 }
        Text { text: Source.v1 }
        Text { text: Source.v2 }
        Text { text: Source.v3 }
        Text { text: Source.v4 }
        Text { text: Source.v5 }
    }
}
''',
}

ROWS = 6


def make_source(kind: str):
    from PySide6.QtCore import (QAbstractListModel, QByteArray, QModelIndex,
                                QObject, Property, Qt, Signal)

    if kind == "list":
        class Source(QObject):
            changed = Signal()

            def __init__(self):
                super().__init__()
                self._n = 0

            @Property("QVariantList", notify=changed)
            def rows(self):
                return [{"label": f"row {i}", "value": f"{self._n + i}.12345"}
                        for i in range(ROWS)]

            def publish(self, n):
                self._n = n
                self.changed.emit()

        return Source()

    if kind == "model":
        class Source(QAbstractListModel):
            LabelRole = Qt.ItemDataRole.UserRole + 1
            ValueRole = Qt.ItemDataRole.UserRole + 2

            def __init__(self):
                super().__init__()
                self._rows = [{"label": f"row {i}", "value": "0"}
                              for i in range(ROWS)]

            def roleNames(self):
                return {self.LabelRole: QByteArray(b"label"),
                        self.ValueRole: QByteArray(b"value")}

            def rowCount(self, parent=QModelIndex()):
                return 0 if parent.isValid() else len(self._rows)

            def data(self, index, role=Qt.ItemDataRole.DisplayRole):
                if not index.isValid():
                    return None
                row = self._rows[index.row()]
                if role == self.LabelRole:
                    return row["label"]
                if role == self.ValueRole:
                    return row["value"]
                return None

            def publish(self, n):
                for i, row in enumerate(self._rows):
                    row["value"] = f"{n + i}.12345"
                self.dataChanged.emit(self.index(0, 0),
                                      self.index(len(self._rows) - 1, 0),
                                      [self.ValueRole])

        return Source()

    class Source(QObject):
        changed = Signal()

        def __init__(self):
            super().__init__()
            self._values = ["0"] * ROWS

        def publish(self, n):
            self._values = [f"{n + i}.12345" for i in range(ROWS)]
            self.changed.emit()

    for i in range(ROWS):
        def getter(self, _i=i):
            return self._values[_i]
        setattr(Source, f"v{i}",
                Property(str, getter, notify=Source.changed))
    return Source()


def run(kind: str, rounds: int, per_round: int) -> dict:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine = QQmlApplicationEngine()
    source = make_source(kind)
    engine.rootContext().setContextProperty("Source", source)

    component = QQmlComponent(engine)
    component.setData(PAGES[kind].encode(),
                      QUrl.fromLocalFile(str(ROOT / "_min.qml")))
    if component.isError():
        raise SystemExit(f"{kind}: {component.errorString()}")
    item = component.create()
    if item is None:
        raise SystemExit(f"{kind}: create failed")

    def settle(n=6):
        # DeferredDelete must be dispatched explicitly: processEvents() alone
        # never completes deleteLater(), which makes correctly-destroyed
        # objects look retained.
        from PySide6.QtCore import QCoreApplication, QEvent

        for _ in range(n):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    settle(12)
    gc.collect()
    settle(8)
    base = private_mb()
    series = []
    counter = 0
    for _ in range(rounds):
        for _ in range(per_round):
            counter += 1
            source.publish(counter)
        settle(4)
        series.append(round(private_mb() - base, 3))

    return {"publisher": kind, "rows": ROWS,
            "publications": rounds * per_round,
            "private_total_mb": series[-1] if series else 0.0,
            "slope_mb_per_round": round(slope(series), 4),
            "series": series}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=sorted(PAGES), required=True)
    parser.add_argument("--rounds", type=int, default=40)
    parser.add_argument("--per-round", type=int, default=25)
    args = parser.parse_args()

    result = run(args.kind, args.rounds, args.per_round)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"minimal_{args.kind}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(f"{args.kind:8s} {result['publications']:5d} publications  "
          f"{result['private_total_mb']:8.2f} MB  slope "
          f"{result['slope_mb_per_round']:7.4f} MB/round")
    return 0


if __name__ == "__main__":
    sys.exit(main())

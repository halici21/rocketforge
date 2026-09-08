"""The workspaces Phase 5D did not touch, captured so "unchanged" is checkable.

Phase 5D adds a domain to the navigator and one line to the status bar, both of
which are shell files every page renders through. That is exactly the kind of
change that can degrade a page nobody was looking at, so the compressible
workspaces and the Engine Design canvas are rendered and kept alongside the new
ones.

Drives the existing controllers directly. No synthetic desktop input.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

import main as bootstrap  # noqa: E402

MESSAGES: list[dict] = []
_KINDS = {QtMsgType.QtDebugMsg: "debug", QtMsgType.QtInfoMsg: "info",
          QtMsgType.QtWarningMsg: "warning", QtMsgType.QtCriticalMsg: "critical",
          QtMsgType.QtFatalMsg: "fatal"}


def _handler(kind, context, message):
    MESSAGES.append({"kind": _KINDS.get(kind, str(kind)), "message": message})


#: One page from each compressible family, plus the second working mode.
PAGES = ["isentropic", "massflow", "normalshock", "obliqueshock",
         "prandtlmeyer", "fanno", "rayleigh", "nozzlelab"]


def main(outdir: Path) -> int:
    outdir.mkdir(parents=True, exist_ok=True)
    qInstallMessageHandler(_handler)

    bootstrap.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _environment = bootstrap.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(bootstrap.UI_DIR / "Main.qml")))
    roots = engine.rootObjects()
    if not roots:
        print("Main.qml did not load", file=sys.stderr)
        return 1
    window = roots[0]
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)

    from PySide6.QtQml import QQmlComponent

    def index_of(key: str) -> int:
        component = QQmlComponent(engine)
        component.setData(
            b'import QtQuick\nimport "data"\n'
            b'QtObject { property int idx: Navigation.indexOfKey("' + key.encode()
            + b'") }',
            QUrl.fromLocalFile(str(bootstrap.UI_DIR / "_probe.qml")))
        probe = component.create()
        return int(probe.property("idx"))

    def settle(rounds=6):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(0.05)
            app.processEvents()

    captured = []
    for key in PAGES:
        window.setProperty("appMode", "analysis")
        window.setProperty("currentPageIndex", index_of(key))
        settle()
        image = window.grabWindow()
        path = outdir / f"regression_{key}.png"
        image.save(str(path))
        captured.append(path.name)

    window.setProperty("appMode", "engine")
    settle()
    image = window.grabWindow()
    path = outdir / "regression_engine_design.png"
    image.save(str(path))
    captured.append(path.name)

    warnings = [m for m in MESSAGES
                if m["kind"] in ("warning", "critical", "fatal")]
    report = {"captures": captured, "messages": MESSAGES,
              "warning_count": len(warnings)}
    (outdir / "existing_ui_regression.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(f"captured {len(captured)} existing workspaces, "
          f"{len(MESSAGES)} Qt messages ({len(warnings)} warning or worse)")
    for entry in warnings[:20]:
        print("  ", entry["kind"], entry["message"])
    return 0 if not warnings else 2


if __name__ == "__main__":
    target = (Path(sys.argv[1]) if len(sys.argv) > 1
              else ROOT / "acceptance" / "phase_5d" / "regression")
    sys.exit(main(target))

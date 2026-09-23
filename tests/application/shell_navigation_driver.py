"""Drive the real application shell through a navigation route. Not a test.

Run as a separate process by ``test_shell_navigation_smoke.py``, so that a
crash or a hang ends this process and not the test session. The route engine is
the application's own (``rocketforge.application.navsmoke``), the same one a
packaged build runs under ``--selftest-navigation``: navigation is driven by a
QTimer inside ``app.exec()``, with no ``processEvents()`` pumping and no forced
``DeferredDelete`` -- the conditions under which a Nozzle Lab ->
Thermochemistry switch once crashed in Qt6Qml. This file adds only what a
packaged build must never carry: the injected failures the negative controls
need.

usage: shell_navigation_driver.py <route> [--step-ms MS] [--inject warning|crash|hang]

The route syntax is documented in rocketforge/application/navsmoke.py.

Prints ``STEP n spec`` per step and ``RESULT <json>`` at the end.
"""
from __future__ import annotations

import faulthandler
import json
import os
import pathlib
import sys

faulthandler.enable()
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

args = sys.argv[1:]
ROUTE = [step for step in args[0].split(",") if step]
STEP_MS = int(args[args.index("--step-ms") + 1]) if "--step-ms" in args else 600
INJECT = args[args.index("--inject") + 1] if "--inject" in args else ""

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if sys.platform == "win32":
    # The offscreen platform looks for fonts beside Qt, finds none, and says
    # so on every run; point it at the system fonts the real platform uses.
    os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlComponent  # noqa: E402

import main as app_main  # noqa: E402
from rocketforge.application.navsmoke import Route  # noqa: E402

warnings: list[str] = []


def _on_message(kind, _context, message):
    if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        warnings.append(str(message))


qInstallMessageHandler(_on_message)
app_main.configure_application()
app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
engine, _env = app_main.build_engine(app)
engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
if not engine.rootObjects():
    print("RESULT " + json.dumps({"status": "load-failed", "warnings": warnings}), flush=True)
    sys.exit(3)
window = engine.rootObjects()[0]
window.setProperty("width", 1920)
window.setProperty("height", 1080)
window.setProperty("appMode", "analysis")

try:
    route = Route(engine, window, app_main.UI_DIR, ROUTE)
except ValueError as error:
    raise SystemExit(str(error))

_keep: list = []


def _inject(index):
    """Negative controls: prove the test can see each failure it guards against."""
    if index != 1 or not INJECT:
        return
    if INJECT == "warning":
        broken = QQmlComponent(engine)
        broken.setData(b"import QtQuick\nItem { Component.onCompleted: undefinedThing.call() }",
                       QUrl.fromLocalFile(str(app_main.UI_DIR / "_shell_navigation_broken.qml")))
        _keep.append(broken.create())
    elif INJECT == "crash":
        # A real native fault, like the Qt6Qml one. Not ctypes: on Windows it
        # catches the access violation and raises OSError instead.
        faulthandler._read_null()
    elif INJECT == "hang":
        import time
        time.sleep(3600)


result = route.run(app, STEP_MS, warnings, before_step=_inject,
                   on_step=lambda n, spec: print(f"STEP {n} {spec}", flush=True))
print("RESULT " + json.dumps(result), flush=True)
sys.exit(0 if result["status"] == "ok" else 4)

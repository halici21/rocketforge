"""Where 3D cannot render, Rocket Performance stays 2D and says why.

Qt Quick 3D is an optional profile (requirements-3d.txt), and even where it is
installed it needs a hardware or WARP graphics path: Qt Quick's software
renderer -- the offscreen platform here -- cannot run it, and a View3D made
there only warns and draws nothing. So the 3D choice must be disabled with its
reason, a request for 3D must leave the 2D schematic in place, and no 3D scene
may be created at all. Checked on the real application scene, offscreen, in
both environments: without the module (base) and with it (the reason then
names the renderer).

The scene runs in a fresh process (this file, run as a script), as in
test_nozzle_view_refresh.py.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    from PySide6.QtCore import (QCoreApplication, QEvent, QObject, QtMsgType, QUrl,
                                qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _context, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg,
                                       QtMsgType.QtFatalMsg) else None)
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    if not engine.rootObjects():
        return {"loaded": False, "warnings": warnings}
    window = engine.rootObjects()[0]
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "analysis")
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport "data" as Data\n'
                  b'QtObject { property var nav: Data.Navigation }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_viewport_fallback.qml")))
    nav = probe.create().property("nav")

    def settle():
        for _ in range(8):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()

    def classes(prefix):
        return [o for o in window.findChildren(QObject)
                if o.metaObject().className().startswith(prefix)]

    window.setProperty("currentPageIndex", nav.indexOfKey("performance"))
    settle()
    switch = window.findChild(QObject, "performanceViewSwitch")
    calc = classes("PerfCalculator")
    if switch is None or not calc:
        return {"loaded": True, "found": False, "warnings": warnings}
    calc = calc[0]
    before = {"available": switch.property("threeDAvailable"),
              "reason": switch.property("unavailableReason"),
              "show3D": switch.property("show3D")}
    calc.setProperty("objectView", "3d")         # a request for 3D, as the switch makes it
    settle()
    canvases = classes("PerfNozzleCanvas")
    return {
        "loaded": True, "found": True, "before": before,
        "requested": calc.property("objectView"),
        "show3D": switch.property("show3D"),
        "viewport": window.findChild(QObject, "performanceViewport3D") is not None,
        "view3d": len(classes("QQuick3DViewport")),
        "canvas_visible": bool(canvases) and bool(canvases[0].property("visible")),
        "warnings": warnings,
    }


def test_the_performance_view_stays_2d_and_says_why_where_3d_cannot_render():
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    assert completed.returncode == 0, completed.stderr[-2000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    result = json.loads(lines[-1][len("RESULT "):])
    assert result["loaded"], f"the application scene did not load: {result['warnings']}"
    assert result["found"], "the Rocket Performance view switch was not found"

    assert result["before"]["available"] is False
    if importlib.util.find_spec("PySide6.QtQuick3D") is None:
        assert "Qt Quick 3D module" in result["before"]["reason"]
    else:
        assert "software renderer" in result["before"]["reason"]
    # asked for 3D: the request is kept, the view is not
    assert result["requested"] == "3d"
    assert result["show3D"] is False
    assert result["viewport"] is False and result["view3d"] == 0
    assert result["canvas_visible"] is True
    assert result["warnings"] == [], result["warnings"]



def _route(route: str) -> dict:
    driver = PROJECT_ROOT / "tests" / "application" / "shell_navigation_driver.py"
    completed = subprocess.run(
        [sys.executable, str(driver), route, "--step-ms", "250"], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    return json.loads(lines[-1][len("RESULT "):])


def test_the_packaged_self_test_steps_open_the_view_switch_and_see_no_scene_offscreen():
    """The view:/expect3d: route steps verify_package runs inside the package.

    Offscreen there is no 3D: asking for it fails the step and says why (the
    control), the 2D view is reported with no scene, and a page without a
    switch fails rather than passing vacuously.
    """
    ok = _route("page:performance,view:2d,expect3d:no")
    assert ok["status"] == "ok" and ok["warnings"] == [], ok
    refused = _route("page:performance,view:3d")
    assert refused["status"] == "step-failed" and "unavailable" in refused["error"], refused
    missing = _route("page:home,view:3d")
    assert missing["status"] == "step-failed" and "no 2D / 3D view switch" in missing["error"]
    wrong = _route("page:performance,expect3d:yes")
    assert wrong["status"] == "step-failed" and "expected one" in wrong["error"], wrong


def test_particle_emitters_are_fixed_children_of_their_system():
    """A particle emitter must never be a Repeater delegate.

    The liquid-feed emitters were once Repeater3D delegates rebuilt on every
    snapshot change. The particle system's next tick then emitted from an
    emitter already detached from its parent -- an access violation in
    QQuick3DNode::sceneTransform, reproduced 10 times in 15 on a refused
    Calculate with the flow cues playing. Offscreen CI cannot render Qt Quick
    3D, so the shape that crashed is held here in the source; the crash route
    itself runs inside the package (verify_package.py VIEWPORT_ROUTE).
    """
    import re

    source = (PROJECT_ROOT / "ui" / "components" / "viewport" / "RFEngineeringViewport3D.qml")
    text = re.sub(r"//[^\n]*", "", source.read_text(encoding="utf-8"))
    assert "ParticleEmitter3D" in text
    assert not re.search(r"delegate\s*:\s*ParticleEmitter3D", text)
    # every emitter sits inside the one ParticleSystem3D, which the flow
    # layer's Loader3D creates and destroys as a whole
    system_at = text.index("ParticleSystem3D {")
    assert all(match.start() > system_at for match in re.finditer(r"ParticleEmitter3D\s*\{", text))
    assert "Loader3D" in text and "active: root.flowLayer" in text


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive()), flush=True)

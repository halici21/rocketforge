"""Visual polish closure: the plot peek, the shock plane, the Isentropic drawer.

* **Plot peek** (rendered, real pointer events, offscreen): a harness of four
  tiles with `RFPlotPeek`. A quick pass does not peek; a dwell lifts the
  tile's own content onto the stage at a materially larger size (width and
  height checked -- an outline or an opacity change alone fails the test);
  the neighbours recede and the peeked plot stays at full opacity; leaving
  hands the content back to its tile; a press suppresses the peek; Focus
  from the peek closes it and asks for focus; Full, Reduced and Off reach
  the same final state; Plot hover preview Off never peeks; repeated peeks
  build no new objects.
* **Isentropic input drawer** (the real application scene, offscreen):
  closed by default over a valid solved state, open when there is no valid
  result, an explicit open or close wins across later solves and edits,
  the page's lifecycle resets it, and no drawer action solves.
* **Nozzle shock plane**: the 3D view's viewport is re-published on every
  solve (a shock-free solve removes the plane and its ring), and the plane
  stays a faint, theme-aware pane whose accent lives on its perimeter.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import time

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

HARNESS = b'''
import QtQuick
import QtQuick.Layouts
import "theme"
import "components"

Item {
    id: stageRoot
    width: 1200; height: 800
    property alias group: peekGroup
    property var focusCount: 0
    QtObject { id: peekGroup; property Item current: null }
    GridLayout {
        id: areaGrid
        objectName: "area"
        anchors.fill: parent
        anchors.margins: 40
        columns: 2
        rowSpacing: 20; columnSpacing: 20
        Repeater {
            model: 4
            delegate: Item {
                id: tile
                required property int index
                objectName: "tile" + index
                Layout.fillWidth: true
                Layout.fillHeight: true
                opacity: peek.receded ? 0.45 : 1
                Rectangle {
                    id: tileContent
                    objectName: "content" + tile.index
                    anchors.fill: parent
                    color: "#223344"
                    property var series: [{ x: 1, y: 2 }, { x: 2, y: 3 }]
                }
                RFPlotPeek {
                    id: peek
                    objectName: "peek" + tile.index
                    group: peekGroup
                    content: tileContent
                    stage: stageRoot
                    area: areaGrid
                    onFocusRequested: stageRoot.focusCount += 1
                }
            }
        }
    }
}
'''


def _peek_drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    from PySide6.QtCore import (QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt, QtMsgType,
                                QUrl, qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest

    import main as app_main

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _c, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine = QQmlEngine()
    # the harness sits (virtually) in ui/, so "theme" and "components" resolve
    harness_url = QUrl.fromLocalFile(str(app_main.UI_DIR / "_peek_harness.qml"))
    comp = QQmlComponent(engine)
    comp.setData(HARNESS, harness_url)
    root = comp.create()
    if root is None:
        return {"loaded": False, "errors": [e.toString() for e in comp.errors()], "warnings": warnings}
    view = QQuickWindow()
    view.resize(1200, 800)
    root.setParentItem(view.contentItem())
    view.show()

    def settle(seconds=0.3):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def visual(item):
        out, stack = [], [item]
        while stack:
            node = stack.pop()
            for child in node.childItems():
                out.append(child)
                stack.append(child)
        return out

    def named(name):
        for o in visual(root):
            if o.objectName() == name:
                return o
        return None

    def centre(item):
        p = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        return QPoint(int(p.x()), int(p.y()))

    def park():
        QTest.mouseMove(view, QPoint(5, 5)); settle(0.3)

    def frames():
        return [o for o in visual(root) if o.objectName() == "plotPeekFrame"]

    motion = None
    for o in visual(root):
        pass
    # the Motion singleton, through a tiny probe in the same engine
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport "theme"\nQtObject { property var motion: Motion }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_peek_probe.qml")))
    motion = probe.create().property("motion")

    settle(0.6)
    out: dict = {"loaded": True}
    t0, t1 = named("tile0"), named("tile1")
    p0 = named("peek0")
    c0 = named("content0")
    series_before = json.dumps(c0.property("series").toVariant() if hasattr(c0.property("series"), "toVariant") else c0.property("series"))

    def peek_state():
        fr = [f for f in frames() if f.property("visible")]
        f = fr[0] if fr else None
        return {"peeking": bool(p0.property("peeking")),
                "frame": None if f is None else [f.width(), f.height()],
                "tile": [t0.width(), t0.height()],
                "content_in_frame": f is not None and c0.parentItem() is not None and c0.parentItem().parentItem() == f,
                "content_in_tile": c0.parentItem() == t0,
                "neighbours": [round(named(f"tile{i}").property("opacity"), 3) for i in (1, 2, 3)],
                "tile_opacity": round(t0.property("opacity"), 3),
                "frame_opacity": None if f is None else round(f.property("opacity"), 3)}

    park()
    QTest.mouseMove(view, centre(t0)); settle(0.12); park()
    out["quick_pass"] = peek_state()
    for mode in ("full", "reduced", "off"):
        motion.setProperty("mode", mode)
        QTest.mouseMove(view, centre(t0)); settle(0.2)
        before_dwell = bool(p0.property("peeking"))
        settle(0.6)
        state = peek_state()
        state["before_dwell"] = before_dwell
        park(); settle(0.3)
        state["after_leave"] = peek_state()
        out[mode] = state
    motion.setProperty("mode", "full")
    # a press suppresses
    QTest.mouseMove(view, centre(t0)); settle(0.1)
    QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, centre(t0)); settle(0.6)
    out["pressed_peeking"] = bool(p0.property("peeking"))
    QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, centre(t0)); park()
    # Focus from the peek
    QTest.mouseMove(view, centre(t0)); settle(0.8)
    f = [x for x in frames() if x.property("visible")]
    btn = [o for o in visual(f[0]) if o.objectName() == "plotPeekFocusButton"][0] if f else None
    if btn is not None:
        QTest.mouseMove(view, centre(btn)); settle(0.2)
        QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, centre(btn)); settle(0.4)
    out["focus"] = {"count": root.property("focusCount"), "peeking": bool(p0.property("peeking")),
                    "content_in_tile": c0.parentItem() == t0}
    park()
    # hover preview off: no peek; the tile's Focus stays reachable
    motion.setProperty("hoverPreview", False)
    QTest.mouseMove(view, centre(t1)); settle(0.8)
    out["preview_off_peeking"] = bool(named("peek1").property("peeking"))
    out["preview_off_focus_button"] = bool([o for o in visual(t1) if o.objectName() == "plotFocusButton"][0].property("visible"))
    motion.setProperty("hoverPreview", True); park()
    # repeated peeks build nothing new
    for k in range(30):
        QTest.mouseMove(view, centre(named(f"tile{k % 4}"))); settle(0.42); park()
    out["repeated"] = {"frames_total": len(frames()),
                       "frames_visible": sum(1 for x in frames() if x.property("visible")),
                       "contents_home": all(named(f"content{i}").parentItem() == named(f"tile{i}") for i in range(4))}
    out["series_unchanged"] = json.dumps(c0.property("series").toVariant() if hasattr(c0.property("series"), "toVariant") else c0.property("series")) == series_before
    out["warnings"] = warnings
    return out


def _app_drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    from PySide6.QtCore import QCoreApplication, QEvent, QObject, QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main
    from rocketforge.application.analysis import isentropic_controller

    solves = {"isentropic": 0}
    original = isentropic_controller.IsentropicController._recalculate

    def counted(self):
        solves["isentropic"] += 1
        return original(self)
    isentropic_controller.IsentropicController._recalculate = counted

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _c, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]
    window.setProperty("width", 1920); window.setProperty("height", 1080)
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as D\n'
                  b'QtObject { property var nav: D.Navigation; property var isentropic: Isentropic }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_visual_polish.qml")))
    holder = probe.create()
    nav, iso = holder.property("nav"), holder.property("isentropic")

    def settle(seconds=0.4):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def page(key, section):
        window.setProperty("currentPageIndex", nav.indexOfKey(key)); settle(0.6)
        for host in window.findChildren(QObject):
            name = host.metaObject().className().split("_QML")[0]
            if name.endswith("Page") and host.metaObject().indexOfProperty("section") >= 0:
                host.setProperty("section", section)
        settle(0.6)

    def drawer():
        found = window.findChildren(QObject, "isentropicInputDrawer")
        return found[0] if found else None

    def call(obj, name, *args):
        from PySide6.QtCore import Q_ARG, QMetaObject
        QMetaObject.invokeMethod(obj, name, *[Q_ARG("QVariant", a) for a in args])

    out: dict = {}
    page("isentropic", 1)
    d = drawer()
    out["A_fresh_valid"] = {"valid": iso.property("valid"), "open": d.property("open"),
                            "summary": d.property("summary")}
    # no valid result: an input out of range (T/T0 > 1)
    iso.setProperty("mode", "T_over_T0"); iso.setProperty("inputValue", 1.5); settle(0.3)
    out["B_invalid"] = {"valid": iso.property("valid"), "open": d.property("open")}
    iso.setMachAndSolve(2.0); settle(0.3)
    out["B_valid_again"] = {"valid": iso.property("valid"), "open": d.property("open")}
    # manual open wins across solves
    before = solves["isentropic"]
    call(d, "setOpenByUser", True); settle(0.3)
    out["drawer_solves_open"] = solves["isentropic"] - before
    iso.setMachAndSolve(3.0); settle(0.3)
    out["C_manual_open_after_solve"] = d.property("open")
    # manual close wins across an edit (even an invalid one) and a solve
    before = solves["isentropic"]
    call(d, "setOpenByUser", False); settle(0.3)
    out["drawer_solves_close"] = solves["isentropic"] - before
    iso.setProperty("mode", "T_over_T0"); iso.setProperty("inputValue", 1.5); settle(0.3)
    out["D_manual_closed_after_invalid_edit"] = {"valid": iso.property("valid"), "open": d.property("open")}
    iso.setMachAndSolve(2.0); settle(0.3)
    out["D_manual_closed_after_solve"] = d.property("open")
    # the page's lifecycle resets the choice
    page("home", 0); page("isentropic", 1)
    d2 = drawer()
    out["E_after_page_reset"] = {"same_instance": d2 is d, "open": d2.property("open"),
                                 "userChosen": d2.property("userChosen")}
    out["warnings"] = warnings
    return out


def _run(mode: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve()), mode], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert completed.returncode == 0, completed.stderr[-3000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    return json.loads(lines[-1][len("RESULT "):])


_CACHE: dict = {}


def peek() -> dict:
    if "peek" not in _CACHE:
        _CACHE["peek"] = _run("peek")
        assert _CACHE["peek"].get("loaded", True), _CACHE["peek"]
    return _CACHE["peek"]


def app() -> dict:
    if "app" not in _CACHE:
        _CACHE["app"] = _run("app")
    return _CACHE["app"]


# ---------------------------------------------------------------- peek

def test_a_quick_pass_does_not_peek():
    r = peek()
    assert r["quick_pass"]["peeking"] is False and r["quick_pass"]["frame"] is None


@pytest.mark.parametrize("mode", ["full", "reduced", "off"])
def test_a_dwell_really_enlarges_the_plot_in_every_motion_mode(mode):
    s = peek()[mode]
    assert s["before_dwell"] is False, "the peek opened before the dwell"
    assert s["peeking"] and s["frame"] is not None
    tile_w, tile_h = s["tile"]
    frame_w, frame_h = s["frame"]
    # materially larger in both directions -- an outline or a fade alone fails
    assert frame_w >= 1.2 * tile_w and frame_h >= 1.2 * tile_h, (s["frame"], s["tile"])
    assert s["content_in_frame"], "the tile's own content was not lifted"
    assert s["neighbours"] == [0.45, 0.45, 0.45]
    assert s["tile_opacity"] == 1.0 and s["frame_opacity"] == 1.0


@pytest.mark.parametrize("mode", ["full", "reduced", "off"])
def test_leaving_closes_the_peek_and_hands_the_content_back(mode):
    after = peek()[mode]["after_leave"]
    assert after["peeking"] is False and after["frame"] is None
    assert after["content_in_tile"] and after["neighbours"] == [1.0, 1.0, 1.0]


def test_a_press_suppresses_the_peek():
    assert peek()["pressed_peeking"] is False


def test_focus_from_the_peek_closes_it_and_asks_for_focus():
    f = peek()["focus"]
    assert f["count"] == 1 and f["peeking"] is False and f["content_in_tile"]


def test_hover_preview_off_never_peeks_but_focus_stays_reachable():
    r = peek()
    assert r["preview_off_peeking"] is False and r["preview_off_focus_button"] is True


def test_repeated_peeks_build_nothing_new_and_change_no_data():
    r = peek()
    assert r["repeated"]["frames_total"] <= 4           # at most one reusable frame per tile
    assert r["repeated"]["frames_visible"] == 0 and r["repeated"]["contents_home"]
    assert r["series_unchanged"]
    assert r["warnings"] == [], r["warnings"]


# ---------------------------------------------------------------- isentropic drawer

def test_a_fresh_valid_solved_calculator_opens_with_its_drawer_closed():
    a = app()["A_fresh_valid"]
    assert a["valid"] and a["open"] is False
    assert "M = 2" in a["summary"] and "γ 1.4" in a["summary"]


def test_no_valid_result_opens_the_drawer_and_a_valid_one_closes_it_again():
    r = app()
    assert r["B_invalid"] == {"valid": False, "open": True}
    assert r["B_valid_again"] == {"valid": True, "open": False}


def test_an_explicit_choice_wins_over_the_default():
    r = app()
    assert r["C_manual_open_after_solve"] is True
    assert r["D_manual_closed_after_invalid_edit"] == {"valid": False, "open": False}
    assert r["D_manual_closed_after_solve"] is False


def test_the_page_lifecycle_resets_the_choice():
    e = app()["E_after_page_reset"]
    assert e["userChosen"] is False and e["open"] is False


def test_drawer_actions_do_not_solve():
    r = app()
    assert r["drawer_solves_open"] == 0 and r["drawer_solves_close"] == 0
    assert r["warnings"] == [], r["warnings"]


# ---------------------------------------------------------------- nozzle shock plane

def test_every_solve_republishes_the_3d_viewport(qt_app):
    from rocketforge.application.analysis.nozzle_controller import NozzleController
    noz = NozzleController()
    noz.backPressureRatio = 0.7
    assert any(s["key"] == "shock" for s in noz.playbackViewport["stations"])
    seen = []
    noz.playbackChanged.connect(lambda: seen.append([s["key"] for s in noz.playbackViewport["stations"]]))
    noz.backPressureRatio = 0.3                       # overexpanded: no internal shock
    assert seen, "a solve did not re-publish the viewport the 3D view draws"
    assert seen[-1] == ["throat", "exit"] and noz.hasShock is False


def test_the_shock_plane_is_a_faint_theme_aware_pane_not_an_opaque_disk():
    source = (PROJECT_ROOT / "ui" / "components" / "viewport" / "RFEngineeringViewport3D.qml").read_text(encoding="utf-8")
    block = source[source.index('objectName: "station:shock-plane"'):]
    block = block[:block.index("materials: PrincipledMaterial")+400]
    fill = re.search(r"fillOpacity:\s*\(Theme\.isDark \? ([0-9.]+) : ([0-9.]+)\)\s*\+\s*\(stationSelected \? ([0-9.]+) : 0\)", block)
    assert fill, "the plane's fill must be the theme-aware fillOpacity"
    dark, light, selected = (float(v) for v in fill.groups())
    assert max(dark, light) + selected <= 0.25, "the shock plane reads as a disk again"
    assert "opacity: shockPlane.fillOpacity" in block
    # gone when there is no shock: not visible, not pickable
    assert "visible: opacity > 0 && (root.shock !== null" in block
    assert "pickable: root.shock !== null" in block


def _route_steps():
    from rocketforge.application.navsmoke import Route
    return Route._step


def test_the_package_proof_steps_refuse_a_malformed_argument():
    """expectshock / expectfocus take yes or no, like expect3d."""
    from types import SimpleNamespace
    step = _route_steps()
    fake = SimpleNamespace(window=None, thermo=None, perf=None, nozzle=None)
    for spec in ("expectshock:maybe", "expectfocus:1"):
        with pytest.raises(ValueError):
            step(fake, spec)
    for spec in ("expectshock:yes", "expectfocus:no", "sweep", "peekfocus", "backpressure:0.7"):
        assert callable(step(fake, spec))


def test_the_package_proof_route_reaches_focus_through_a_real_peek():
    """The Sweep leg of the package proof, from source and under a real event
    loop: a solved sweep, a real peek, Focus open -- and without the peek the
    same expectation fails, so the step can see a missing overlay."""
    from rocketforge.application.analysis import thermochemistry_provider as gateway
    if not gateway.availability().usable:
        pytest.skip("the sweep needs the NASA CEA provider")
    sys.path.insert(0, str(PROJECT_ROOT / "tests" / "application"))
    from test_shell_navigation_smoke import run_route
    route = "solve,page:thermochem,section:2,sweep,peekfocus,expectfocus:yes"
    result = run_route(route, timeout=180)
    assert result["status"] == "ok", result
    assert result["steps"] == route.count(",") + 1
    assert result["warnings"] == []
    control = run_route("solve,page:thermochem,section:2,sweep,expectfocus:yes", timeout=180)
    assert control["status"] == "failed" and "Focus overlay" in control.get("error", ""), control


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "peek"
    print("RESULT " + json.dumps(_peek_drive() if mode == "peek" else _app_drive(), default=str))

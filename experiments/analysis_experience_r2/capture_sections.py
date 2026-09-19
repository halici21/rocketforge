"""Capture a specific tab/section of an analysis page."""
from __future__ import annotations
import json, pathlib, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BASE = ROOT / "acceptance" / "analysis_experience_r2_implementation"


def find_with_property(obj, name, depth=0):
    """Depth-first search for a QObject carrying a QML property `name`."""
    if obj is None or depth > 14:
        return None
    try:
        idx = obj.metaObject().indexOfProperty(name)
    except Exception:
        idx = -1
    if idx >= 0 and obj.metaObject().property(idx).isWritable():
        return obj
    for child in obj.children():
        hit = find_with_property(child, name, depth + 1)
        if hit is not None:
            return hit
    return None


def main(cfg):
    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow  # noqa: F401
    from PySide6.QtQml import QQmlComponent
    import main as app_main

    msgs = []
    qInstallMessageHandler(lambda k, c, m: msgs.append(str(m))
                           if k in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=12):
        for _ in range(rounds):
            app.processEvents(); time.sleep(0.02); app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
        b'QtObject { property var nav: Data.Navigation; property var obliqueC: ObliqueShock }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe2.qml")))
    holder = probe.create()
    nav = holder.property("nav")

    window.setProperty("width", cfg.get("w", 1920))
    window.setProperty("height", cfg.get("h", 1080))
    window.setProperty("themeMode", cfg.get("theme", "dark"))
    window.setProperty("appMode", "analysis")
    settle()

    holder.property("obliqueC").setDeflectionAndSolve(10.0)
    settle()

    out = BASE / cfg["outdir"]; out.mkdir(parents=True, exist_ok=True)
    for shot in cfg["shots"]:
        window.setProperty("currentPageIndex", nav.indexOfKey(shot["key"]))
        settle()
        page = find_with_property(window, "section")
        if page is None:
            print("!! no page with `section` for", shot["key"]); continue
        page.setProperty("section", shot["section"])
        settle()
        for prop, val in shot.get("set", {}).items():
            target = find_with_property(window, prop)
            if target is None:
                print("!! no object with", prop); continue
            target.setProperty(prop, val)
            settle()
        name = shot.get("name", f'{shot["key"]}_s{shot["section"]}')
        window.grabWindow().save(str(out / f'{name}_{cfg.get("theme","dark")}.png'))
        print("captured", name)

    print(f"{len(msgs)} Qt warnings")
    for m in msgs[:8]:
        print("  ", m)


if __name__ == "__main__":
    main(json.loads(sys.argv[1]))

"""Capture the Reference Engines workspace (DB-3A) for visual QA.

    python experiments/db3a_reference_engines/capture.py <out_dir> [config ...]

Drives the real shell offscreen: for each representative configuration, each
of 2560x1440, 1920x1080 and 1366x768, light and dark, it saves the top of the
record and the record scrolled to its topology panel, plus a few inspector and
data-drawer states. Captures go to <out_dir>, which should be outside the
repository (screenshots are never committed). Prints any Qt warning.
"""
from __future__ import annotations

import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if sys.platform == "win32":
    os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

RESOLUTIONS = ((2560, 1440), (1920, 1080), (1366, 768))
CONFIGS = ("CFG-J2-230K", "CFG-F1", "CFG-H1-188K-SA10", "CFG-LMDE-FINAL", "CFG-J2S", "CFG-IPD",
           "CFG-RD-170", "CFG-RS-68A", "CFG-LR87-AJ-11-T3E", "CFG-RL10B-2-DIV")


def main() -> int:
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "acceptance" / "db3a"
    configs = tuple(sys.argv[2:]) or CONFIGS
    out.mkdir(parents=True, exist_ok=True)

    from PySide6.QtCore import QCoreApplication, QEvent, QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _c, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as D\n'
                  b'QtObject { property var nav: D.Navigation; property var re: ReferenceEngines;'
                  b' property var shell: D.ShellContext }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_db3a_capture.qml")))
    holder = probe.create()
    nav, rex, shell = (holder.property(n) for n in ("nav", "re", "shell"))

    def settle(seconds=0.35):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def items():
        found, stack = [], [window.contentItem()]
        while stack:
            node = stack.pop()
            for child in node.childItems():
                found.append(child)
                stack.append(child)
        return found

    def named(name):
        return next((i for i in items() if i.objectName() == name), None)

    def shot(name):
        settle(0.25)
        window.grabWindow().save(str(out / f"{name}.png"))

    window.setProperty("currentPageIndex", nav.indexOfKey("engines"))
    settle(0.8)
    for theme in ("light", "dark"):
        window.setProperty("themeMode", theme)
        for w, h in RESOLUTIONS:
            window.setProperty("width", w); window.setProperty("height", h)
            settle(0.4)
            for cfg in configs:
                rex.selectConfiguration(cfg)
                shell.setProperty("inspectorOpen", False)
                settle()
                tag = f"{cfg}_{w}_{theme}"
                shot(tag + "_top")
                scroll, topo = named("engineRecordScroll"), named("engineTopology")
                if scroll is not None and topo is not None:
                    y = topo.mapToItem(scroll.property("contentItem"), 0, 0).y()
                    room = scroll.property("contentHeight") - scroll.property("height")
                    scroll.setProperty("contentY", max(0.0, min(y - 8, room)))
                    shot(tag + "_topology")
                    scroll.setProperty("contentY", 0.0)
            # inspector and drawer states on two records
            rex.selectConfiguration("CFG-RD-170"); settle()
            node = next((i for i in items() if i.objectName().startswith("node_")), None)
            if node is not None:
                rex.inspectNode(node.objectName()[len("node_"):])
            shell.setProperty("inspectorOpen", True)
            scroll, topo = named("engineRecordScroll"), named("engineTopology")
            y = topo.mapToItem(scroll.property("contentItem"), 0, 0).y()
            scroll.setProperty("contentY", max(0.0, min(y - 8, scroll.property("contentHeight")
                                                     - scroll.property("height"))))
            shot(f"inspector_node_RD170_{w}_{theme}")
            scroll.setProperty("contentY", 0.0)
            rex.selectConfiguration("CFG-RS25-BLOCK-II"); settle()
            pc = [r for r in rex.property("facts").rows() if r["field"] == "performance.chamber_pressure"]
            if pc:
                rex.inspectAssertion(pc[0]["assertionId"])
            shot(f"inspector_assertion_RS25_{w}_{theme}")
            rex.selectConfiguration("CFG-F1"); settle()
            rex.inspectSource(rex.property("sources").rows()[0]["sourceId"])
            drawer = named("engineDataDrawer")
            drawer.setProperty("open", True); settle(0.5)
            shot(f"drawer_source_F1_{w}_{theme}")
            drawer.setProperty("open", False)
            shell.setProperty("inspectorOpen", False)
            rex.setSearch("zz no such engine"); settle()
            shot(f"no_match_{w}_{theme}")
            rex.clearFilters(); settle()
    print("captures:", len(list(out.glob("*.png"))), "->", out)
    print("warnings:", warnings)
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())

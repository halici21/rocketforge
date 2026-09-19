"""Capture Fluid Properties' required state matrix: nominal liquid, a
materially different valid state (gas phase), two-phase ambiguity (every
property withheld together), a hard refusal outside CoolProp's own EOS
range, and the stale-input fixture, plus the responsive matrix.

Run under QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=C:/Windows/Fonts (see
CAD_CAE_WORKBENCH_R1_LINE_INTEGRATION.md for why -- a real on-screen window
at 1920x1080 can trip a QWindowsWindow::setGeometry warning on a
display-constrained host, unrelated to this workspace's own code).
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "fluidproperties"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    messages = []
    kinds = {QtMsgType.QtDebugMsg: "debug", QtMsgType.QtInfoMsg: "info",
             QtMsgType.QtWarningMsg: "warning",
             QtMsgType.QtCriticalMsg: "critical", QtMsgType.QtFatalMsg: "fatal"}

    def handler(kind, context, message):
        messages.append((kinds.get(kind, str(kind)), message))

    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=6, pause=0.05):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject { property var fp: FluidProperties\n'
        b'  property int idx: Navigation.indexOfKey("fluidproperties") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    fp = holder.property("fp")
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()

    def reset_defaults():
        fp.setFluid("OXYGEN")
        fp.setTemperature(90.17)
        fp.setPressure(300000.0)

    def solve_and_capture(name, note):
        fp.calculate()
        settle()
        window.grabWindow().save(str(OUT / f"{name}.png"))
        print(f"[{name}] {note}: hasResult={fp.property('hasResult')} "
              f"phase={fp.property('phase')!r} "
              f"statusLabel={fp.property('statusLabel')!r} "
              f"message={fp.property('message')!r}")

    # ---- nominal liquid -----------------------------------------------------
    reset_defaults()
    solve_and_capture("state_liquid", "nominal liquid")

    # ---- a materially different valid state: true gas phase -----------------
    reset_defaults()
    fp.setTemperature(100.0)
    fp.setPressure(50000.0)
    solve_and_capture("state_gas", "gas phase")

    # ---- two-phase ambiguity: every property withheld together --------------
    reset_defaults()
    fp.setTemperature(90.17)
    fp.setPressure(101136.47191150107)
    solve_and_capture("state_two_phase", "two-phase (saturation line)")

    # ---- refused: outside CoolProp's own declared EOS range ------------------
    reset_defaults()
    fp.setTemperature(40.0)
    solve_and_capture("state_refused", "outside CoolProp's EOS range")

    # ---- stale-input fixture: solve liquid, then edit T without
    # recalculating -- expect input field = new T, result still shows the
    # OLD solved T=90.17 case, with a stale indication visible.
    reset_defaults()
    fp.calculate()
    settle()
    fp.setTemperature(150.0)
    settle()
    window.grabWindow().save(str(OUT / "state_stale.png"))
    print(f"[state_stale] input T={fp.property('temperature')} "
          f"hasResult={fp.property('hasResult')} "
          f"resultStale={fp.property('resultStale')} "
          f"(result should still reflect T=90.17)")

    # ---- responsive: nominal liquid at all three resolutions, dark ----------
    reset_defaults()
    fp.calculate()
    settle()
    for width, height in ((2560, 1440), (1920, 1080), (1366, 768)):
        window.setProperty("width", width)
        window.setProperty("height", height)
        settle()
        window.grabWindow().save(str(OUT / f"responsive_dark_{width}x{height}.png"))

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "light")
    settle()
    window.grabWindow().save(str(OUT / "responsive_light_1920x1080.png"))
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    settle()
    window.grabWindow().save(str(OUT / "responsive_light_1366x768.png"))
    window.setProperty("themeMode", "dark")

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"\n{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

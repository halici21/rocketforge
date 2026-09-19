"""Capture Line's required state matrix: laminar, turbulent, transitional
refusal, insufficient-inlet-pressure refusal, stale-input fixture."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "line"
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
        b'QtObject { property var line: Line\n'
        b'  property int idx: Navigation.indexOfKey("line") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    line = holder.property("line")
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()

    def reset_defaults():
        line.setMassFlow(2.0)
        line.setLength(5.0)
        line.setInnerDiameter(0.02)
        line.setPressure(1.0e6)

    def solve_and_capture(name, note):
        line.calculate()
        settle()
        window.grabWindow().save(str(OUT / f"{name}.png"))
        print(f"[{name}] {note}: hasResult={line.property('hasResult')} "
              f"regime={line.property('flowRegime')!r} "
              f"statusLabel={line.property('statusLabel')!r} "
              f"message={line.property('message')!r}")

    # ---- laminar ----------------------------------------------------------
    reset_defaults()
    line.setMassFlow(0.001)
    solve_and_capture("state_laminar", "laminar")

    # ---- turbulent (default) ----------------------------------------------
    reset_defaults()
    solve_and_capture("state_turbulent", "turbulent")

    # ---- transitional refusal ----------------------------------------------
    reset_defaults()
    line.setMassFlow(0.0057)
    solve_and_capture("state_transitional", "transitional")

    # ---- insufficient inlet pressure ---------------------------------------
    reset_defaults()
    line.setLength(500.0)
    solve_and_capture("state_insufficient_pressure", "insufficient pressure")

    # ---- outside validated transport envelope -------------------------------
    # Same fluid (methane), same temperature, but a pressure above its
    # recorded viscosity envelope (5-30 bar) while still well inside the
    # provider's own equation-of-state range (up to 1e9 Pa) -- the provider
    # still answers (density, phase all solve), so this is a distinct kind
    # from a hard refusal: hasResult stays false, but the reason is "not
    # claimed here", not "could not be solved".
    reset_defaults()
    line.setPressure(4.0e6)
    solve_and_capture("state_outside_transport_envelope", "outside transport envelope")

    # ---- stale-input fixture: solve laminar (D=0.02), then edit D without
    # recalculating -- expect input field = new D, result still shows the
    # OLD solved D=0.02 case, with a stale indication visible.
    reset_defaults()
    line.setMassFlow(0.001)
    line.calculate()
    settle()
    line.setInnerDiameter(0.04)
    settle()
    window.grabWindow().save(str(OUT / "state_stale.png"))
    print(f"[state_stale] input D={line.property('innerDiameter')} "
          f"hasResult={line.property('hasResult')} "
          f"(result should still reflect D=0.02)")

    # ---- responsive: laminar case at all three resolutions, dark ----------
    reset_defaults()
    line.setMassFlow(0.001)
    line.calculate()
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

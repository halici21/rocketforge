"""A page switched to a theme looks like a page opened in it.

RFLineChart once kept the previous theme's pixels when the theme changed on
an open page: its Canvas repaints only when asked, and nothing asked. This
opens Canvas-drawn views (Nozzle Lab regime map and charts, the Isentropic
relation, the Rocket Performance canvas), switches the theme with the page
open in both directions, and compares each capture with the same page opened
fresh in that theme. Every pair must match to within text antialiasing.

A negative control runs in the same process: the Nozzle Lab chart canvases
are frozen (their signals blocked, so paint() never runs) before a switch,
and that capture must then differ. Without it a comparison that saw nothing
would pass.

Like test_nozzle_view_refresh.py, the scene runs in a fresh process: this
file, run as a script.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: (page key, section, name)
VIEWS = [
    ("nozzlelab", 0, "nozzle_regimes"),
    ("nozzlelab", 3, "nozzle_charts"),
    ("isentropic", 0, "isentropic_relation"),
    ("performance", 0, "performance"),
]

#: A channel difference at or above this (out of 255) is visible. Glyph
#: antialiasing differs by 1-2 between two renders of the same text.
PERCEPTIBLE = 8


def _drive(out: pathlib.Path) -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    from PySide6.QtCore import QObject, QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication, QImage

    import main as app_main
    from rocketforge.application.navsmoke import Route

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _context, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg,
                                       QtMsgType.QtFatalMsg) else None)
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    roots = engine.rootObjects()
    if not roots:
        return {"loaded": False, "warnings": warnings}
    window = roots[0]
    window.setProperty("width", 1600)
    window.setProperty("height", 900)
    window.setProperty("appMode", "analysis")

    specs = []
    for page, section, name in VIEWS:
        specs += ["page:home", "theme:dark", f"page:{page}", f"section:{section}",
                  f"capture:{name}__dark_fresh",
                  "theme:light", f"capture:{name}__light_switched",
                  "theme:dark", f"capture:{name}__dark_switched",
                  "page:home", "theme:light", f"page:{page}", f"section:{section}",
                  f"capture:{name}__light_fresh"]
    # the control: Nozzle Lab charts open in dark, frozen, switched to light
    specs += ["page:home", "theme:dark", "page:nozzlelab", "section:3", "page:home"]
    freeze_at = len(specs) - 1
    specs += ["theme:light", "capture:control__light_switched", "theme:dark"]
    frozen = []

    def freeze_charts():
        for item in window.findChildren(QObject):
            if not item.metaObject().className().startswith("QQuickCanvasItem") or not item.property("visible"):
                continue
            owner = item.parent()
            while owner is not None and not owner.metaObject().className().startswith("RFLineChart"):
                owner = owner.parent()
            if owner is not None:
                item.blockSignals(True)
                frozen.append(item)

    route = Route(engine, window, app_main.UI_DIR, specs, capture_dir=out)
    route.steps[freeze_at] = ("freeze chart canvases", freeze_charts)
    result = route.run(app, 300, warnings)

    def perceptible(a, b):
        first = QImage(str(out / f"{a}.png")).convertToFormat(QImage.Format.Format_RGB32)
        second = QImage(str(out / f"{b}.png")).convertToFormat(QImage.Format.Format_RGB32)
        if first.size() != second.size():
            return -1
        width, stride = first.width(), first.bytesPerLine()
        pa, pb = bytes(first.constBits()), bytes(second.constBits())
        count = 0
        for y in range(first.height()):
            ra = pa[y * stride:y * stride + 4 * width]
            rb = pb[y * stride:y * stride + 4 * width]
            if ra == rb:
                continue
            count += sum(1 for x in range(0, 4 * width, 4)
                         if max(abs(ra[x] - rb[x]), abs(ra[x + 1] - rb[x + 1]),
                                abs(ra[x + 2] - rb[x + 2])) >= PERCEPTIBLE)
        return count

    pairs = {name: {"to_light": perceptible(f"{name}__light_switched", f"{name}__light_fresh"),
                    "to_dark": perceptible(f"{name}__dark_switched", f"{name}__dark_fresh")}
             for _page, _section, name in VIEWS}
    control = perceptible("control__light_switched", "nozzle_charts__light_fresh")
    return {"loaded": True, "status": result.get("status"), "error": result.get("error"),
            "pairs": pairs, "control": control, "frozen": len(frozen), "warnings": warnings}


def test_an_open_page_repaints_when_the_theme_changes(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve()), str(tmp_path)],
        cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert completed.returncode == 0, completed.stderr[-2000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    result = json.loads(lines[-1][len("RESULT "):])
    assert result["loaded"], f"the application scene did not load: {result['warnings']}"
    assert result["status"] == "ok", result
    assert result["warnings"] == [], result["warnings"]
    stale = {name: pair for name, pair in result["pairs"].items()
             if pair["to_light"] != 0 or pair["to_dark"] != 0}
    assert stale == {}, stale
    # the comparison can see a canvas that did not repaint
    assert result["frozen"] > 0
    assert result["control"] > 1000, result["control"]


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(pathlib.Path(sys.argv[1]))), flush=True)

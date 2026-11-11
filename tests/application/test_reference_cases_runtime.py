"""Reference Cases (DB-4C display) in the running application: real QML, computing only on Run.

A subprocess starts the real shell (``main.configure_application`` and
``main.build_engine``, as the product does) with the DB-4C runner wrapped in a
counter before the controller is built. Then: open the page, choose every
point, switch theme and window size, leave and return -- **zero** runs; then,
where NASA CEA is installed, press the real Run button -- **one** run, every
point computed. Without CEA the Run button is disabled and the printed values
are still on the page.

The same run checks that the page prints no Qt/QML warning, never applies a
judging word to a row, and does not accumulate page instances.
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
#: Words the page may never apply to a row (display review §2). The step notes' "not an error" and "never a
#: RocketForge defect" are checked separately: they say what a difference is not.
JUDGING = ("pass", "passed", "fail", "failed", "agree", "agrees", "validated", "verified", "accuracy",
           "efficiency", "score", "better", "worse")


def _drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

    from rocketforge.application.analysis import reference_ideal_case as ideal

    runs: list[int] = []
    original = ideal.run_ideal_cases

    def counted(*args, **kwargs):
        runs.append(1)
        return original(*args, **kwargs)

    ideal.run_ideal_cases = counted

    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QtMsgType, QUrl, qInstallMessageHandler
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
    window.setProperty("width", 1920); window.setProperty("height", 1080)
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as D\n'
                  b'QtObject { property var nav: D.Navigation; property var rc: ReferenceCases }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_reference_cases_runtime.qml")))
    holder = probe.create()
    nav, rc = holder.property("nav"), holder.property("rc")

    def settle(seconds=0.3):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def items(root=None):
        out, stack = [], [root or window.contentItem()]
        while stack:
            node = stack.pop()
            for child in node.childItems():
                out.append(child)
                stack.append(child)
        return out

    def named(name):
        found = [i for i in items() if i.objectName() == name]
        return found[0] if found else None

    def page_texts():
        roots = [i for i in items() if i.metaObject().className().startswith("ReferenceCasesPage")]
        return [str(i.property("text")) for r in roots for i in items(r) if i.property("text")]

    out: dict = {}
    index = nav.indexOfKey("referencecases")
    out["nav_index"] = index
    window.setProperty("currentPageIndex", index); settle(0.8)

    # 1. browsing computes nothing
    out["title"] = named("referenceCasesTitle").property("text")
    out["class_line"] = named("referenceCasesClass").property("text")
    out["summary_before"] = named("referenceCasesRunSummary").property("text")
    titles = []
    for point in range(4):
        rc.select(point); settle(0.2)
        titles.append(named("referenceCasesTitle").property("text"))
    out["titles"] = titles
    texts = page_texts()
    out["not_run_shown"] = sum(1 for t in texts if t == "not run")
    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    for w, h in ((1366, 768), (2560, 1440), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.3)
    counts = []
    for _ in range(3):
        window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
        window.setProperty("currentPageIndex", index); settle(0.5)
        counts.append(sum(1 for i in items() if i.objectName() == "referenceCasesRun"))
    out["page_instances"] = counts
    out["runs_while_browsing"] = len(runs)

    # 2. the real Run button
    button = named("referenceCasesRun")
    out["provider_usable"] = bool(rc.property("providerUsable"))
    out["run_enabled"] = bool(button.property("enabled"))
    if out["provider_usable"]:
        QMetaObject.invokeMethod(button, "clicked"); settle(0.8)
        out["runs_after_click"] = len(runs)
        out["summary_after"] = named("referenceCasesRunSummary").property("text")
        states = []
        for point in range(4):
            rc.select(point); settle(0.2)
            states.append(named("referenceCasesPointState").property("text"))
        out["point_states"] = states
        texts = page_texts()
    out["joined"] = " ".join(texts)
    out["warnings"] = warnings
    return out


def _run() -> dict:
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert completed.returncode == 0, completed.stderr[-3000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    return json.loads(lines[-1][len("RESULT "):])


@pytest.fixture(scope="module")
def run():
    return _run()


def test_the_page_is_in_the_reference_family_and_opens(run):
    assert run["nav_index"] >= 0
    assert run["title"] == "SSME current design at 109%, 1985 TDK printout, first solution"
    assert run["class_line"] == "Independent code: compared, never judged"
    assert run["titles"][3].startswith("Rocketdyne prototype Advanced Space Engine")


def test_browsing_computes_nothing_and_shows_not_run(run):
    assert run["runs_while_browsing"] == 0
    assert run["summary_before"].startswith("Not run.")
    assert run["not_run_shown"] >= 6, "step A's computed and difference cells read 'not run' before a run"


def test_run_is_one_explicit_action(run):
    assert run["run_enabled"] == run["provider_usable"]
    if run["provider_usable"]:
        assert run["runs_after_click"] == 1
        assert run["summary_after"].startswith("Last run: 4 computed of 4 points")
        assert run["point_states"] == ["Computed"] * 4


def test_no_row_is_judged(run):
    lowered = run["joined"].lower()
    for word in JUDGING:
        assert re.search(rf"\b{word}\b", lowered) is None, word


def test_no_warning_and_no_accumulating_pages(run):
    assert run["warnings"] == [], run["warnings"]
    assert run["page_instances"] == [1, 1, 1]


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)

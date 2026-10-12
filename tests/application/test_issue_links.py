"""R3-A: an issue that names an unsolved upstream page links to it, and the link only navigates.

Two layers:

1. **static** -- `Navigation.upstreamPageOfIssue` (QML) and the services' issue messages
   (Python) name the same page. Every mapped code's messages name the mapped page, and every
   issue message that sends the person to another page has its code mapped.
2. **running application** -- in a subprocess, with every service entry point counted: on
   each chain page the link shows once, names the page, opens it, and solves nothing.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import re
import subprocess
import sys
import time

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
NAVIGATION = PROJECT_ROOT / "ui" / "data" / "Navigation.qml"
SERVICES = PROJECT_ROOT / "rocketforge" / "application" / "analysis"
#: With nothing solved, the page each chain page is blocked on.
UPSTREAM = {"propellanttrade": "requirement", "chambersizing": "propellanttrade",
            "chambergeometry": "chambersizing", "injector": "chambersizing",
            "propellantinventory": "chambersizing", "tankgeometry": "propellantinventory",
            "propellantmanagement": "propellantinventory", "tankpressurization": "propellantmanagement",
            "feednetwork": "tankpressurization"}
CHAIN = tuple(UPSTREAM)
#: How the services' messages name each upstream page's study in prose, when they do not
#: give its page title ("The propellant inventory is stale.", "Run the sizing again.",
#: "The selected candidate did not solve in the trade.").
STUDY = {"requirement": ("engine requirement",),
         "propellanttrade": ("propellant trade", "the trade", "selected candidate"),
         "chambersizing": ("thrust-chamber sizing", "the sizing"),
         "injector": ("injector study",),
         "propellantinventory": ("propellant inventory",),
         "tankgeometry": ("tank geometry", "the tanks"),
         "propellantmanagement": ("propellant-management study",),
         "tankpressurization": ("tank-pressurization study",)}
#: The reviewed map, issue code -> the page where the fix is (R3-A review, 2026-10-12). Every
#: service message for each code was read. Navigation.qml must equal this, so a remapped code
#: fails here rather than relying on wording alone.
REVIEWED = {
    "REQUIREMENT_INCOMPLETE": "requirement", "BURN_TIME_UNRESOLVED": "requirement",
    "NO_TRADE": "propellanttrade", "TRADE_STALE": "propellanttrade", "TRADE_MISMATCH": "propellanttrade",
    "NO_SELECTION": "propellanttrade", "SELECTION_FAILED": "propellanttrade",
    "SELECTION_INCOMPLETE": "propellanttrade",
    "NO_SIZING": "chambersizing", "SIZING_STALE": "chambersizing", "SIZING_REFUSED": "chambersizing",
    "SIZING_INCOMPLETE": "chambersizing", "REQUIREMENT_MISMATCH": "chambersizing",
    "NO_INJECTOR": "injector", "INJECTOR_STALE": "injector", "INJECTOR_REFUSED": "injector",
    "INJECTOR_MISMATCH": "injector",
    "NO_INVENTORY": "propellantinventory", "INVENTORY_INCOMPLETE": "propellantinventory",
    "INVENTORY_STALE": "propellantinventory", "INVENTORY_REFUSED": "propellantinventory",
    "NO_TANKS": "tankgeometry", "TANKS_STALE": "tankgeometry", "TANKS_REFUSED": "tankgeometry",
    "TANKS_MISMATCH": "tankgeometry",
    "NO_MANAGEMENT": "propellantmanagement", "MANAGEMENT_STALE": "propellantmanagement",
    "MANAGEMENT_REFUSED": "propellantmanagement",
    "NO_PRESSURIZATION": "tankpressurization", "PRESSURIZATION_STALE": "tankpressurization",
    "PRESSURIZATION_REFUSED": "tankpressurization",
}
#: A code shaped like an upstream result: missing (NO_X), or X stale, refused, mismatched,
#: incomplete or failed, for any X. A new one must be reviewed into the map or listed here.
UPSTREAM_CODE = re.compile(r"^NO_[A-Z]+$|^[A-Z]+_(STALE|REFUSED|MISMATCH|INCOMPLETE|FAILED)$")
#: Codes of that shape that are about the page itself, not an upstream page.
NOT_UPSTREAM = {"NO_CANDIDATES"}      # the trade's own catalogue has no executable pair


def _navigation():
    text = NAVIGATION.read_text(encoding="utf-8")
    labels = dict(re.findall(r'key: "(\w+)",\s*label: "([^"]+)"', text))
    block = text[text.index("upstreamPageOfIssue: ({"):]
    block = block[:block.index("})")]
    mapping = dict(re.findall(r'"([A-Z_]+)": "(\w+)"', block))
    return labels, mapping


def _issue_messages():
    """(file, code, flattened message source) for every issue call in the services."""
    out = []
    for path in sorted(SERVICES.glob("*_service.py")):
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call):
                continue
            codes = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if not codes or not re.fullmatch(r"[A-Z][A-Z_]{3,}", codes[0]):
                continue
            segment = ast.get_source_segment(source, node) or ""
            out.append((path.name, codes[0], re.sub(r'"\s*\n\s*f?"', "", segment)))
    return out


def _names_page(message: str, label: str) -> bool:
    return f"on the {label} page" in message or f"{label}: " in message


def test_every_mapped_code_points_at_a_real_page():
    labels, mapping = _navigation()
    assert mapping, "the upstream map is empty"
    for code, key in mapping.items():
        assert key in labels, (code, key)


def test_the_backend_message_names_the_page_the_link_opens():
    labels, mapping = _navigation()
    seen = set()
    for name, code, message in _issue_messages():
        if code in mapping:
            seen.add(code)
            # The page by title ("on the Propellant Inventory page"), or the study it computes.
            key = mapping[code]
            text = message[message.index(code) + len(code):].lower()
            assert _names_page(message, labels[key]) or any(n in text for n in STUDY[key]), \
                (name, code, message)
    assert seen == set(mapping), set(mapping) - seen     # no stale code in the map


def test_the_map_is_the_reviewed_one():
    _, mapping = _navigation()
    assert mapping == REVIEWED


def test_every_upstream_result_code_has_a_link():
    """Missing, stale, refused or mismatched upstream results: the fix is on that page."""
    _, mapping = _navigation()
    upstream = {code for _, code, _ in _issue_messages() if UPSTREAM_CODE.match(code)} - NOT_UPSTREAM
    assert upstream and upstream <= set(mapping), upstream - set(mapping)


def test_every_message_that_sends_the_person_elsewhere_has_a_link():
    labels, mapping = _navigation()
    for name, code, message in _issue_messages():
        for key, label in labels.items():
            if key not in ("home",) and _names_page(message, label):
                assert mapping.get(code) == key, (name, code, label)


# ---------------------------------------------------------------- running application


def _drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    import functools
    import importlib
    import inspect
    import pkgutil

    import rocketforge

    for info in pkgutil.walk_packages(rocketforge.__path__, "rocketforge."):
        try:
            importlib.import_module(info.name)
        except Exception:
            pass

    service_module = re.compile(r"^rocketforge\.application\.analysis\.\w+_service$")
    entry = re.compile(r"^(solve|generate|run|evaluate|compute|calculate|reanalyse)")
    calls: dict[str, int] = {}

    def wrap(original, key):
        @functools.wraps(original)
        def counted(*args, **kwargs):
            calls[key] = calls.get(key, 0) + 1
            return original(*args, **kwargs)
        return counted

    wrappers: dict[int, object] = {}
    for name, module in list(sys.modules.items()):
        if module is None or not service_module.match(name):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and value.__module__ == name and entry.search(attr):
                wrappers[id(value)] = wrap(value, f"{name}.{attr}")
    for name, module in list(sys.modules.items()):
        if module is None or not (name.startswith("rocketforge") or name == "main"):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and id(value) in wrappers:
                setattr(module, attr, wrappers[id(value)])

    from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt, QtMsgType, QUrl
    from PySide6.QtCore import qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtTest import QTest

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
                  b'QtObject { property var nav: D.Navigation; property var iso: Isentropic }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_issue_links_runtime.qml")))
    holder = probe.create()
    nav, iso = holder.property("nav"), holder.property("iso")

    def settle(seconds=0.3):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def items():
        out, stack = [], [window.contentItem()]
        while stack:
            node = stack.pop()
            for child in node.childItems():
                out.append(child)
                stack.append(child)
        return out

    def total():
        return sum(calls.values())

    out: dict = {"wrapped": len(wrappers)}
    before = total()
    iso.setProperty("inputValue", 2.5); settle(0.2)
    out["positive_control_calls"] = total() - before

    keys = [nav.property("items").toVariant()[i]["key"]
            for i in range(len(nav.property("items").toVariant()))]
    pages = {}
    for key in CHAIN:
        window.setProperty("currentPageIndex", nav.indexOfKey(key)); settle(0.8)
        links = [i for i in items() if i.objectName() == "issueLink" and i.property("visible")]
        page = {"links": [i.property("text") for i in links]}
        if links:
            start = total()
            centre = links[0].mapToScene(QPointF(links[0].width() / 2, links[0].height() / 2)).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, centre)
            settle(0.6)
            page["opened"] = keys[window.property("currentPageIndex")]
            page["calls"] = total() - start
        pages[key] = page
    out["pages"] = pages
    out["labels"] = {k: nav.property("items").toVariant()[nav.indexOfKey(k)]["label"] for k in keys}
    out["mapping"] = nav.property("upstreamPageOfIssue").toVariant()
    out["warnings"] = warnings
    return out


def _run() -> dict:
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=400)
    assert completed.returncode == 0, completed.stderr[-3000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    return json.loads(lines[-1][len("RESULT "):])


@pytest.fixture(scope="module")
def run():
    return _run()


def test_the_instrument_is_live(run):
    assert run["wrapped"] > 20 and run["positive_control_calls"] > 0


@pytest.mark.parametrize("key", CHAIN)
def test_each_chain_page_links_once_to_its_upstream_page_and_solves_nothing(run, key):
    page = run["pages"][key]
    # with nothing solved upstream, every chain page is blocked on exactly one upstream page
    assert len(page["links"]) == 1, page
    assert page["opened"] == UPSTREAM[key]
    assert page["links"] == ["Open " + run["labels"][UPSTREAM[key]]]
    assert page["calls"] == 0                         # navigation only


def test_no_qml_warning(run):
    assert run["warnings"] == [], run["warnings"]


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)

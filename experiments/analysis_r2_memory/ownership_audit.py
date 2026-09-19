"""Sections 13-16: does anything actually retain a page after destruction?

The census answers "is it still in the tree". This answers the stronger
question: is the C++ object gone, and if not, who is holding it. shiboken6
reports whether the underlying C++ object still exists behind a Python
wrapper, which is exactly the distinction between "destroyed" and "orphaned
but alive".
"""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import shiboken6
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent
from rig import build, navigation, settle, census, ROOT
import main as app_main

OUT = ROOT / "acceptance" / "analysis_r2_closure" / "memory"
CHART_PAGES = ["isentropic", "fanno", "nozzlelab", "obliqueshock"]


def page_item(window):
    """The item the WorkspaceHost Loader currently holds."""
    for child in window.findChildren(QObject):
        if "QQuickLoader" in child.metaObject().className():
            item = child.property("item")
            if item is not None and item.metaObject().className().endswith(
                    tuple(["_QMLTYPE_%d" % i for i in range(0)]) or ("",)):
                pass
            if item is not None:
                return child, item
    return None, None


def main() -> int:
    app, engine, window = build()
    nav = navigation(engine)

    findings = {}

    # ---- 15. Loader audit: is the page actually destroyed? -------------
    observed = []
    for key in CHART_PAGES:
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle(app, 6)
        loader, item = page_item(window)
        if item is None:
            continue
        cls = item.metaObject().className()
        # Move away, then ask whether the C++ object behind the wrapper is gone.
        window.setProperty("currentPageIndex", nav.indexOfKey("equations"))
        settle(app, 10)
        gc.collect()
        alive = shiboken6.isValid(item)
        observed.append({"page": key, "class": cls,
                         "cpp_object_alive_after_navigating_away": alive})
        print("  %-14s %-34s destroyed=%s" % (key, cls, not alive))

    findings["loader_audit"] = {
        "question": "does changing Loader.source destroy the previous item",
        "pages": observed,
        "all_destroyed": all(not o["cpp_object_alive_after_navigating_away"]
                             for o in observed),
    }

    # Loader configuration, read off the live object.
    loader, _ = page_item(window)
    if loader is not None:
        findings["loader_config"] = {
            k: str(loader.property(k))
            for k in ("active", "asynchronous", "visible")
        }

    # ---- 14. Singleton audit -------------------------------------------
    # Do the long-lived singletons hold visual objects from destroyed pages?
    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
        b'import "theme"\n'
        b'QtObject {\n'
        b'  property var workspaceState: Data.WorkspaceState\n'
        b'  property var shellContext: Data.ShellContext\n'
        b'  property var theme: Theme\n'
        b'  property var navigation: Data.Navigation\n}',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_singleton_probe.qml")))
    holder = probe.create()
    singles = {}
    for name in ("workspaceState", "shellContext", "theme", "navigation"):
        obj = holder.property(name)
        if obj is None:
            singles[name] = {"error": "not resolvable"}
            continue
        kids = obj.findChildren(QObject)
        visual = [k.metaObject().className() for k in kids
                  if "QQuickItem" in k.metaObject().className()
                  or "Canvas" in k.metaObject().className()]
        singles[name] = {"child_qobjects": len(kids),
                         "visual_children_retained": len(visual),
                         "classes": sorted(set(visual))[:5]}
        print("  singleton %-16s children=%-4d visual=%d"
              % (name, len(kids), len(visual)))
    findings["singleton_audit"] = {
        "question": "do long-lived singletons retain page/chart Items",
        "singletons": singles,
        "any_visual_retention": any(
            v.get("visual_children_retained", 0) for v in singles.values()),
    }

    # ---- 13. Python -> QML reference audit ------------------------------
    gc.collect()
    live_wrappers = [o for o in gc.get_objects() if isinstance(o, QObject)]
    stale = [o for o in live_wrappers if not shiboken6.isValid(o)]
    quick = [o for o in live_wrappers
             if shiboken6.isValid(o)
             and ("QQuickItem" in o.metaObject().className()
                  or "Canvas" in o.metaObject().className())]
    findings["python_reference_audit"] = {
        "question": "does Python hold QQuickItem/page wrappers after destruction",
        "live_python_qobject_wrappers": len(live_wrappers),
        "wrappers_whose_cpp_object_is_gone": len(stale),
        "wrappers_holding_live_visual_items": len(quick),
        "note": ("wrappers for still-live items are expected while the scene "
                 "exists; the defect shape would be wrappers accumulating for "
                 "items of destroyed pages"),
    }
    print("  python wrappers: %d live, %d stale, %d visual"
          % (len(live_wrappers), len(stale), len(quick)))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ownership_audit.json").write_text(
        json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    print()
    print("pages destroyed on navigation :", findings["loader_audit"]["all_destroyed"])
    print("singletons retain visuals     :", findings["singleton_audit"]["any_visual_retention"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""The package carries Qt Quick 3D and nothing else from PySide6-Addons.

The trim is a pure function of a PyInstaller TOC and the set of files the
Addons wheel owns, so it is checked here on made-up files: a required file
survives, every other Addons file goes, and a file from anywhere else --
including an Essentials file with a similar name -- is never touched. The
package-side check is shown to catch both a missing required file and a
stray Addons file.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("qt3d_runtime",
                                                  ROOT / "packaging" / "qt3d_runtime.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    return path.resolve()


def test_the_trim_keeps_qt_quick_3d_and_drops_the_rest_of_the_addons_wheel(tmp_path):
    q = _module()
    wheel = tmp_path / "site" / "PySide6"
    required = _touch(wheel / "Qt6Quick3D.dll")
    plugin = _touch(wheel / "qml" / "QtQuick3D" / "qquick3dplugin.dll")
    webengine = _touch(wheel / "Qt6WebEngineCore.dll")
    physics = _touch(wheel / "qml" / "QtQuick3D" / "Physics" / "qmldir")
    essentials = _touch(wheel / "Qt6Quick.dll")               # not the Addons wheel's
    owned = {required, plugin, webengine, physics}
    toc = [("PySide6/Qt6Quick3D.dll", str(required), "BINARY"),
           ("PySide6/qml/QtQuick3D/qquick3dplugin.dll", str(plugin), "BINARY"),
           ("PySide6/Qt6WebEngineCore.dll", str(webengine), "BINARY"),
           ("PySide6/qml/QtQuick3D/Physics/qmldir", str(physics), "DATA"),
           ("PySide6/Qt6Quick.dll", str(essentials), "BINARY"),
           ("rocketforge/data/reference/table.json", str(tmp_path / "t.json"), "DATA")]
    kept = [dest for dest, _source, _code in q.trim(toc, owned)]
    assert kept == ["PySide6/Qt6Quick3D.dll", "PySide6/qml/QtQuick3D/qquick3dplugin.dll",
                    "PySide6/Qt6Quick.dll", "rocketforge/data/reference/table.json"]


def test_the_required_list_is_what_the_3d_view_was_measured_to_load():
    q = _module()
    names = {name.lower() for name in q.REQUIRED_FILES}
    for loaded in ("Qt6Quick3D.dll", "Qt6Quick3DParticles.dll", "Qt6Quick3DRuntimeRender.dll",
                   "Qt6Quick3DUtils.dll", "Qt6ShaderTools.dll", "QtQuick3D.pyd",
                   "qml/QtQuick3D/qquick3dplugin.dll",
                   "qml/QtQuick3D/Particles3D/qtquick3dparticles3dplugin.dll"):
        assert loaded.lower() in names
    # the plugins' own registration data travels with them
    assert "qml/quicktest/qmldir" not in names
    assert {"qml/qtquick3d/qmldir", "qml/qtquick3d/particles3d/qmldir"} <= names


def test_the_package_check_sees_a_missing_file_and_a_stray_one(tmp_path):
    q = _module()
    internal = tmp_path / "_internal"
    root = internal / "PySide6"
    for name in q.REQUIRED_FILES:
        _touch(root / name)
    owned = {name.lower(): root / name for name in q.REQUIRED_FILES}
    owned["qt6webenginecore.dll"] = tmp_path / "wheel" / "Qt6WebEngineCore.dll"
    assert q.check_package(internal, owned) == []
    (root / "Qt6ShaderTools.dll").unlink()                      # control: missing
    assert any("Qt6ShaderTools.dll is missing" in f for f in q.check_package(internal, owned))
    _touch(root / "Qt6ShaderTools.dll")
    _touch(root / "Qt6WebEngineCore.dll")                       # control: stray
    assert any("were packaged" in f for f in q.check_package(internal, owned))


def test_without_the_addons_wheel_there_is_nothing_to_check(tmp_path):
    assert _module().check_package(tmp_path, {}) == []

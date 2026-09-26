"""The part of PySide6-Addons the package carries: Qt Quick 3D, and nothing else.

The 3D view (requirements-3d.txt) needs Qt Quick 3D, which ships in the
PySide6-Addons wheel together with some 400 MB of other Qt modules the product
never loads -- WebEngine, Multimedia, Charts, Graphs, Location, the rest of the
Qt Quick 3D family (Physics, Xr, Helpers, AssetUtils, SpatialAudio). With the
wheel installed, PyInstaller's PySide6 hooks collect far more than is used.

So the package keeps exactly the Addons files the running 3D view loads, and
drops every other file the Addons wheel owns. The list is not a guess: it is
the set of modules the real window loaded under the windows platform with the
3D view open, every standard view, both projections, cutaway, flow and a theme
switch exercised (acceptance/interactive_visualization/tools/
addons_usage_probe.py), plus the QML metadata those two plugins are
registered by. packaging/verify_package.py checks the result, and the smoke
run opens the 3D view inside the package.

Ownership is read from the wheel's own RECORD, so a file that the Essentials
wheel provides is never touched, whatever its name.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath

ADDONS_DISTRIBUTION = "PySide6_Addons"

#: Addons files the 3D view needs, relative to the PySide6 package directory.
REQUIRED_FILES = (
    "Qt6Quick3D.dll",
    "Qt6Quick3DParticles.dll",
    "Qt6Quick3DRuntimeRender.dll",
    "Qt6Quick3DUtils.dll",
    "Qt6ShaderTools.dll",          # runtime shader generation for the materials
    "QtQuick3D.pyd",               # QQuick3DGeometry, for the revolved meshes
    "qml/QtQuick3D/qquick3dplugin.dll",
    "qml/QtQuick3D/qmldir",
    "qml/QtQuick3D/Quick3D.qmltypes",
    "qml/QtQuick3D/LightmapperOutputWindow.qml",   # declared by the qmldir
    "qml/QtQuick3D/Particles3D/qtquick3dparticles3dplugin.dll",
    "qml/QtQuick3D/Particles3D/qmldir",
    "qml/QtQuick3D/Particles3D/plugins.qmltypes",
)

_REQUIRED = frozenset(name.lower() for name in REQUIRED_FILES)


def addons_files() -> dict[str, Path]:
    """Every file the Addons wheel installed, by its path under PySide6/ (lower case).

    Empty when the wheel is not installed: then there is nothing to trim, and
    the package is built without the 3D view (which then says why).
    """
    try:
        from importlib.metadata import PackageNotFoundError, distribution
        dist = distribution(ADDONS_DISTRIBUTION)
    except PackageNotFoundError:
        return {}
    owned = {}
    for entry in dist.files or ():
        parts = PurePosixPath(str(entry).replace("\\", "/")).parts
        if parts and parts[0] == "PySide6":
            owned["/".join(parts[1:]).lower()] = Path(entry.locate()).resolve()
    return owned


def is_required(relative: str) -> bool:
    """Whether an Addons file, by its path under PySide6/, is one the 3D view needs."""
    return relative.replace("\\", "/").lower() in _REQUIRED


def trim(toc, owned_sources: set[Path]):
    """``toc`` without the Addons files the product does not load.

    ``toc`` is a PyInstaller TOC of (destination, source, typecode). An entry
    is dropped when its source file is owned by the Addons wheel and its
    destination is not one of REQUIRED_FILES.
    """
    kept = []
    for dest, source, typecode in toc:
        if source and Path(source).resolve() in owned_sources:
            relative = dest.replace("\\", "/")
            if relative.lower().startswith("pyside6/"):
                relative = relative[len("pyside6/"):]
            if not is_required(relative):
                continue
        kept.append((dest, source, typecode))
    return kept


def check_package(internal: Path, owned: dict[str, Path]) -> list[str]:
    """Package-side check: the required files are there, no other Addons file is."""
    if not owned:
        return []
    root = internal / "PySide6"
    failures = [f"3d runtime: {name} is missing from the package"
                for name in REQUIRED_FILES if not (root / name).is_file()]
    extra = sorted(str(path.relative_to(root)).replace("\\", "/")
                   for path in root.rglob("*") if path.is_file()
                   and str(path.relative_to(root)).replace("\\", "/").lower() in owned
                   and not is_required(str(path.relative_to(root))))
    if extra:
        failures.append(f"3d runtime: {len(extra)} Addons files the product does not load "
                        f"were packaged, e.g. {extra[:5]}")
    return failures

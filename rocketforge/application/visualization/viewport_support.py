"""Whether this process can show a 3D view, and why not when it cannot.

Two independent conditions, both required:

* the Qt Quick 3D module is installed (``PySide6.QtQuick3D``, shipped in the
  optional ``requirements-3d.txt`` profile);
* the window renders through a 3D graphics API (QRhi). Qt Quick's software
  renderer -- the ``offscreen`` platform, or a machine with no usable GPU
  path -- cannot run Qt Quick 3D at all, and the view says so.

The first is known here, at start-up; the second only once a window exists,
so the QML host checks ``GraphicsInfo.api`` before it instantiates a scene.
Without either, the 2D engineering view is the view, with a one-line reason.
"""
from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal

__all__ = ["Viewport3DSupport", "register_viewport_types", "QML_URI_3D"]

QML_URI_3D = "RocketForge.Viewport3D"

_REGISTERED = {"done": False, "ok": False, "reason": ""}


def register_viewport_types() -> tuple[bool, str]:
    """Register the Qt Quick 3D types once per process; (available, reason)."""
    if _REGISTERED["done"]:
        return _REGISTERED["ok"], _REGISTERED["reason"]
    _REGISTERED["done"] = True
    try:
        from PySide6.QtQml import qmlRegisterType

        from .geometry_qml import RFRevolvedGeometry, RFRingGeometry
    except ImportError:
        _REGISTERED["reason"] = ("The 3D view needs the Qt Quick 3D module, which is not "
                                 "installed (requirements-3d.txt).")
        return False, _REGISTERED["reason"]
    qmlRegisterType(RFRevolvedGeometry, QML_URI_3D, 1, 0, "RFRevolvedGeometry")
    qmlRegisterType(RFRingGeometry, QML_URI_3D, 1, 0, "RFRingGeometry")
    _REGISTERED["ok"] = True
    return True, ""


class Viewport3DSupport(QObject):
    """Exposed to QML as ``Viewport3D``: the module half of the answer."""

    changed = Signal()

    def __init__(self, available: bool, reason: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._available = bool(available)
        self._reason = str(reason)

    @Property(bool, notify=changed)
    def moduleAvailable(self) -> bool:
        return self._available

    @Property(str, notify=changed)
    def moduleReason(self) -> str:
        return self._reason

    @Property(str, constant=True)
    def rendererReason(self) -> str:
        return ("The 3D view needs a hardware or WARP graphics path; this window "
                "renders with Qt Quick's software renderer.")

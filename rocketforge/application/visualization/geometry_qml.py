"""The revolved surface as a Qt Quick 3D geometry.

Imported only when ``PySide6.QtQuick3D`` is installed (``viewport_support``
decides); nothing else in the application depends on this module.

The buffers are built once per (profile, sweep, segments) and cached, so a
camera move, a selection or a playing flow layer never rebuilds a mesh: those
change camera and node transforms, not vertex data.
"""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import Property, QByteArray, Signal
from PySide6.QtGui import QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry

from .geometry import DEFAULT_SEGMENTS, GeometryError, Mesh, profile_from_radius, revolve, ring

__all__ = ["RFRevolvedGeometry", "RFRingGeometry", "mesh_cache_info"]

_CACHE: dict[tuple, Mesh] = {}
_CACHE_LIMIT = 16
_BUILDS = {"count": 0}


def mesh_cache_info() -> dict:
    """How many meshes were built and how many are held (for the lifecycle gate)."""
    return {"built": _BUILDS["count"], "cached": len(_CACHE)}


def _mesh(xs: tuple, rs: tuple, sweep: float, segments: int, keep: tuple,
          cap_start: bool = False) -> Mesh:
    key = (xs, rs, float(sweep), int(segments), keep, bool(cap_start))
    mesh = _CACHE.get(key)
    if mesh is None:
        mesh = revolve(profile_from_radius(xs, rs), segments, sweep, keep, bool(cap_start))
        _BUILDS["count"] += 1
        _CACHE[key] = mesh
        while len(_CACHE) > _CACHE_LIMIT:
            _CACHE.pop(next(iter(_CACHE)))
    return mesh


class RFRevolvedGeometry(QQuick3DGeometry):
    """A surface of revolution about +x from ``profile`` = {x: [...], r: [...]}."""

    profileChanged = Signal()
    sweepChanged = Signal()
    segmentsChanged = Signal()
    keepChanged = Signal()
    capStartChanged = Signal()
    errorChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._profile: dict = {}
        self._sweep = 360.0
        self._segments = DEFAULT_SEGMENTS
        self._keep: list = []
        self._cap_start = False
        self._error = ""
        self._built_key = None

    # ---- properties ----------------------------------------------------
    def _get_profile(self):
        return self._profile

    def _set_profile(self, value) -> None:
        value = dict(value or {})
        if value == self._profile:
            return
        self._profile = value
        self._rebuild()
        self.profileChanged.emit()

    profile = Property("QVariantMap", _get_profile, _set_profile, notify=profileChanged)

    def _get_sweep(self) -> float:
        return self._sweep

    def _set_sweep(self, value: float) -> None:
        value = float(value)
        if value == self._sweep:
            return
        self._sweep = value
        self._rebuild()
        self.sweepChanged.emit()

    sweep = Property(float, _get_sweep, _set_sweep, notify=sweepChanged)

    def _get_segments(self) -> int:
        return self._segments

    def _set_segments(self, value: int) -> None:
        value = int(value)
        if value == self._segments:
            return
        self._segments = value
        self._rebuild()
        self.segmentsChanged.emit()

    segments = Property(int, _get_segments, _set_segments, notify=segmentsChanged)

    def _get_keep(self):
        return self._keep

    def _set_keep(self, value) -> None:
        value = [float(v) for v in (value or [])]
        if value == self._keep:
            return
        self._keep = value
        self._rebuild()
        self.keepChanged.emit()

    keep = Property("QVariantList", _get_keep, _set_keep, notify=keepChanged)

    def _get_cap_start(self) -> bool:
        return self._cap_start

    def _set_cap_start(self, value: bool) -> None:
        value = bool(value)
        if value == self._cap_start:
            return
        self._cap_start = value
        self._rebuild()
        self.capStartChanged.emit()

    # A flat disc closing the first station (a chamber's face).
    capStart = Property(bool, _get_cap_start, _set_cap_start, notify=capStartChanged)

    def _get_error(self) -> str:
        return self._error

    error = Property(str, _get_error, notify=errorChanged)

    # ---- buffers ---------------------------------------------------------
    def _rebuild(self) -> None:
        xs = tuple(float(v) for v in self._profile.get("x", []))
        rs = tuple(float(v) for v in self._profile.get("r", []))
        key = (xs, rs, self._sweep, self._segments, tuple(self._keep), self._cap_start)
        if key == self._built_key:
            return
        self.clear()
        self._built_key = key
        if len(xs) < 2:
            self._set_error("")
            self.update()
            return
        try:
            mesh = _mesh(xs, rs, self._sweep, self._segments, tuple(self._keep),
                         self._cap_start)
        except GeometryError as error:
            self._set_error(str(error))
            self.update()
            return
        positions = np.asarray(mesh.positions, dtype=np.float32).reshape(-1, 3)
        normals = np.asarray(mesh.normals, dtype=np.float32).reshape(-1, 3)
        interleaved = np.hstack([positions, normals]).astype(np.float32)
        self.setVertexData(QByteArray(interleaved.tobytes()))
        self.setStride(24)
        self.setIndexData(QByteArray(np.asarray(mesh.indices, dtype=np.uint32).tobytes()))
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)
        self.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic, 0,
                          QQuick3DGeometry.Attribute.F32Type)
        self.addAttribute(QQuick3DGeometry.Attribute.NormalSemantic, 12,
                          QQuick3DGeometry.Attribute.F32Type)
        self.addAttribute(QQuick3DGeometry.Attribute.IndexSemantic, 0,
                          QQuick3DGeometry.Attribute.U32Type)
        self.setBounds(QVector3D(*mesh.bounds_min), QVector3D(*mesh.bounds_max))
        self._set_error("")
        self.update()

    def _set_error(self, text: str) -> None:
        if text != self._error:
            self._error = text
            self.errorChanged.emit()


def _upload(geometry: QQuick3DGeometry, mesh: Mesh) -> None:
    positions = np.asarray(mesh.positions, dtype=np.float32).reshape(-1, 3)
    normals = np.asarray(mesh.normals, dtype=np.float32).reshape(-1, 3)
    geometry.setVertexData(QByteArray(np.hstack([positions, normals]).astype(np.float32).tobytes()))
    geometry.setStride(24)
    geometry.setIndexData(QByteArray(np.asarray(mesh.indices, dtype=np.uint32).tobytes()))
    geometry.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)
    geometry.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic, 0,
                          QQuick3DGeometry.Attribute.F32Type)
    geometry.addAttribute(QQuick3DGeometry.Attribute.NormalSemantic, 12,
                          QQuick3DGeometry.Attribute.F32Type)
    geometry.addAttribute(QQuick3DGeometry.Attribute.IndexSemantic, 0,
                          QQuick3DGeometry.Attribute.U32Type)
    geometry.setBounds(QVector3D(*mesh.bounds_min), QVector3D(*mesh.bounds_max))


class RFRingGeometry(QQuick3DGeometry):
    """A station ring: a thin torus of ``radius`` with line weight ``tube``."""

    shapeChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._radius = 1.0
        self._tube = 0.02
        self._built = None
        self._rebuild()

    def _get_radius(self) -> float:
        return self._radius

    def _set_radius(self, value: float) -> None:
        if float(value) != self._radius:
            self._radius = float(value)
            self._rebuild()
            self.shapeChanged.emit()

    radius = Property(float, _get_radius, _set_radius, notify=shapeChanged)

    def _get_tube(self) -> float:
        return self._tube

    def _set_tube(self, value: float) -> None:
        if float(value) != self._tube:
            self._tube = float(value)
            self._rebuild()
            self.shapeChanged.emit()

    tube = Property(float, _get_tube, _set_tube, notify=shapeChanged)

    def _rebuild(self) -> None:
        key = (self._radius, self._tube)
        if key == self._built:
            return
        self._built = key
        self.clear()
        if self._radius > 0.0 and self._tube > 0.0:
            cache_key = ("ring", self._radius, self._tube)
            mesh = _CACHE.get(cache_key)
            if mesh is None:
                mesh = ring(self._radius, self._tube, 64, 8)
                _BUILDS["count"] += 1
                _CACHE[cache_key] = mesh
                while len(_CACHE) > _CACHE_LIMIT:
                    _CACHE.pop(next(iter(_CACHE)))
            _upload(self, mesh)
        self.update()

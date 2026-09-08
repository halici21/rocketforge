"""Render the RocketForge product mark to a multi-size Windows .ico.

The mark is the one the application already draws in its own title bar
(RFIcon "nozzle", in the ember accent) - the icon is that shape on the dark
graphite surface, not a new piece of branding.
"""
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (QGuiApplication, QImage, QPainter, QPainterPath,
                           QPen, QColor, QBrush)

OUT = Path(sys.argv[1])
app = QGuiApplication(sys.argv[:1])

GRAPHITE = QColor("#191C21")
EMBER = QColor("#D97F45")

def render(size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)

    # Rounded graphite tile, so the mark has the same ground as the app.
    radius = size * 0.22
    tile = QPainterPath()
    tile.addRoundedRect(0.0, 0.0, float(size), float(size), radius, radius)
    p.fillPath(tile, QBrush(GRAPHITE))

    # The mark, drawn on the same 16-unit grid RFIcon uses.
    k = size / 16.0
    pen = QPen(EMBER)
    pen.setWidthF(max(1.0, 1.6 * k * 0.92))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)

    path = QPainterPath()
    path.moveTo(2.0 * k, 2.6 * k)
    path.lineTo(6.4 * k, 8.0 * k)
    path.lineTo(2.0 * k, 13.4 * k)
    path.moveTo(14.0 * k, 3.4 * k)
    path.lineTo(9.6 * k, 8.0 * k)
    path.lineTo(14.0 * k, 12.6 * k)

    # Inset the 16-unit drawing so it does not touch the tile edge.
    p.save()
    p.translate(size * 0.11, size * 0.11)
    p.scale(0.78, 0.78)
    p.drawPath(path)
    p.restore()
    p.end()
    return img

sizes = [16, 24, 32, 48, 64, 128, 256]
images = [render(s) for s in sizes]

# QImage cannot write multi-image .ico, so write the frames with QIcon through
# a QImageWriter-backed pixmap set is not available either; build the ICO by
# hand from PNG frames, which is a format Windows accepts.
import struct, io as _io
from PySide6.QtCore import QBuffer, QByteArray

frames = []
for img in images:
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QBuffer.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    frames.append(bytes(ba.data()))

header = struct.pack("<HHH", 0, 1, len(frames))
offset = 6 + 16 * len(frames)
entries, blobs = b"", b""
for size, blob in zip(sizes, frames):
    w = 0 if size >= 256 else size
    h = 0 if size >= 256 else size
    entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(blob), offset)
    blobs += blob
    offset += len(blob)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(header + entries + blobs)
print("wrote %s (%d bytes, %d frames)" % (OUT, OUT.stat().st_size, len(frames)))

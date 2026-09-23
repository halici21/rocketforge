"""RocketForge product mark -- Analysis Experience R2 brand pass.

Draws the mark once, in one place, and emits every asset from it:

    assets/branding/rocketforge_mark.svg      vector master
    assets/branding/rocketforge_icon_1024.png large raster
    assets/branding/rocketforge.ico           multi-size Windows icon
    assets/branding/contact_sheet_dark.png    16..256 on dark
    assets/branding/contact_sheet_light.png   16..256 on light

The mark is a converging-diverging nozzle in cross-section: two mirrored
contour strokes with a throat, on an obsidian tile, in champagne. No text,
no flame, no gradient, no cartoon rocket -- the geometry alone carries
"propulsion" and the drawing convention carries "engineering". Below 32 px
the centre axis and its ticks are dropped and the contour is thickened, so
the silhouette stays legible rather than dissolving into grey.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, Qt
from PySide6.QtGui import (QBrush, QColor, QGuiApplication, QImage, QPainter,
                           QPainterPath, QPen)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "branding"

# Obsidian / Champagne -- the accepted production identity (ui/theme/Theme.qml).
OBSIDIAN = QColor("#0F1013")
CHAMPAGNE = QColor("#D3B26A")
AXIS = QColor("#7A6A45")
LIGHT_GROUND = QColor("#F3EEE3")


def nozzle_silhouette(k: float) -> QPainterPath:
    """The mark: one closed, filled bell-nozzle silhouette on a 16-unit grid.

    A first pass drew this as two mirrored contour strokes plus a centre
    axis. Rendered and inspected at 16-32 px on the contact sheet, that
    version read as a letterform rather than a nozzle and dissolved into
    grey below 32 px -- so the geometry was simplified rather than the
    illustration downscaled harder: no axis, no ticks, no open strokes,
    just the silhouette, which survives to 16 px as a recognisable
    chamber-throat-bell shape.
    """
    p = QPainterPath()
    # chamber, across the top
    p.moveTo(5.1 * k, 2.6 * k)
    p.lineTo(10.9 * k, 2.6 * k)
    # right wall: a short convergence to the throat at 6.6, then a long bell
    p.cubicTo(10.9 * k, 4.6 * k, 9.45 * k, 5.2 * k, 9.45 * k, 6.6 * k)
    p.cubicTo(9.45 * k, 10.0 * k, 11.9 * k, 11.3 * k, 13.4 * k, 13.7 * k)
    # bell lip, across the bottom
    p.lineTo(2.6 * k, 13.7 * k)
    # left wall: bell lip -> throat -> chamber
    p.cubicTo(4.1 * k, 11.3 * k, 6.55 * k, 10.0 * k, 6.55 * k, 6.6 * k)
    p.cubicTo(6.55 * k, 5.2 * k, 5.1 * k, 4.6 * k, 5.1 * k, 2.6 * k)
    p.closeSubpath()
    return p


def render(size: int, ground: QColor | None = OBSIDIAN) -> QImage:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)

    if ground is not None:
        radius = size * 0.22
        tile = QPainterPath()
        tile.addRoundedRect(0.0, 0.0, float(size), float(size), radius, radius)
        p.fillPath(tile, QBrush(ground))

    k = size / 16.0

    p.save()
    # Inset so the drawing never touches the tile edge.
    p.translate(size * 0.09, size * 0.09)
    p.scale(0.82, 0.82)

    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(CHAMPAGNE))
    p.drawPath(nozzle_silhouette(k))

    p.restore()
    p.end()
    return img


SVG_MASTER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <title>RocketForge</title>
  <rect x="0" y="0" width="256" height="256" rx="56" ry="56" fill="#0F1013"/>
  <g transform="translate(23.04,23.04) scale(0.82)">
    <path fill="#D3B26A" d="
      M 81.6 41.6
      L 174.4 41.6
      C 174.4 73.6 151.2 83.2 151.2 105.6
      C 151.2 160 190.4 180.8 214.4 219.2
      L 41.6 219.2
      C 65.6 180.8 104.8 160 104.8 105.6
      C 104.8 83.2 81.6 73.6 81.6 41.6
      Z"/>
  </g>
</svg>
"""


def write_ico(path: Path, sizes: list[int]) -> None:
    frames = []
    for size in sizes:
        img = render(size)
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
    path.write_bytes(header + entries + blobs)


def contact_sheet(path: Path, ground: QColor) -> None:
    """16..256 side by side, for the small-size legibility review."""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    pad = 24
    width = pad + sum(s + pad for s in sizes)
    height = 256 + pad * 2
    sheet = QImage(width, height, QImage.Format_ARGB32)
    sheet.fill(ground)
    p = QPainter(sheet)
    p.setRenderHint(QPainter.Antialiasing, True)
    x = pad
    for s in sizes:
        img = render(s)
        p.drawImage(x, pad + (256 - s) // 2, img)
        x += s + pad
    p.end()
    sheet.save(str(path))


#: The Windows icon sizes: 16-256, every size the shell asks for.
ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]


def write_icons() -> list[Path]:
    """The two .ico files, which are generated rather than tracked.

    ``assets/branding/rocketforge.ico`` is the window and taskbar icon;
    ``packaging/RocketForge.ico`` is the executable's shell icon. Both are the
    same frames, drawn from the code above -- so the canonical build
    (``packaging/build_release.py``) regenerates them from the commit it
    packages, and a fresh clone gets exactly the accepted icon.
    """
    targets = [OUT_DIR / "rocketforge.ico", ROOT / "packaging" / "RocketForge.ico"]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        write_ico(target, ICON_SIZES)
    return targets


def main() -> int:
    app = QGuiApplication(sys.argv[:1])  # noqa: F841 -- needed for QImage/QPainter
    if "--icons-only" in sys.argv:
        for target in write_icons():
            print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    (OUT_DIR / "rocketforge_mark.svg").write_text(SVG_MASTER, encoding="utf-8")
    render(1024).save(str(OUT_DIR / "rocketforge_icon_1024.png"))
    write_icons()
    contact_sheet(OUT_DIR / "contact_sheet_dark.png", QColor("#101216"))
    contact_sheet(OUT_DIR / "contact_sheet_light.png", LIGHT_GROUND)

    for name in ("rocketforge_mark.svg", "rocketforge_icon_1024.png",
                 "rocketforge.ico", "contact_sheet_dark.png",
                 "contact_sheet_light.png"):
        f = OUT_DIR / name
        print(f"wrote {f.relative_to(ROOT)} ({f.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

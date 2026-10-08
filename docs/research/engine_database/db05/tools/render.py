import os
import fitz, sys
sid, pages = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 110
d = fitz.open(os.path.join(os.environ.get("DB05_CACHE", "cache"), f"{sid}.pdf"))
for p in pages.split(','):
    pg = d[int(p)-1]
    clip = None
    if len(sys.argv) > 4:  # x0,y0,x1,y1 fractions
        r = pg.rect; f = [float(v) for v in sys.argv[4].split(',')]
        clip = fitz.Rect(r.x0+f[0]*r.width, r.y0+f[1]*r.height, r.x0+f[2]*r.width, r.y0+f[3]*r.height)
    pix = pg.get_pixmap(dpi=dpi, clip=clip)
    out = f"img/{sid}_p{p}" + ("_crop" if clip else "") + ".png"
    pix.save(out); print(out, pix.width, pix.height)

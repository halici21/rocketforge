import os
import fitz, sys
from PIL import Image
sid, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); cols = 4
d = fitz.open(os.path.join(os.environ.get("DB05_CACHE", "cache"), f"{sid}.pdf")); ims = []
for i in range(a, min(b, d.page_count) + 1):
    pix = d[i-1].get_pixmap(dpi=40); im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    im.thumbnail((330, 330)); ims.append((i, im))
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols*340, rows*350), "white")
from PIL import ImageDraw
dr = ImageDraw.Draw(sheet)
for k, (i, im) in enumerate(ims):
    x, y = (k % cols)*340, (k // cols)*350
    sheet.paste(im, (x+5, y+15)); dr.text((x+5, y+1), f"p{i}", fill="red")
sheet.save(f"img/sheet_{sid}_{a}-{b}.png"); print(sheet.size)

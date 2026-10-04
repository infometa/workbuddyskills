#!/usr/bin/env python
"""批量资产联络图（§2f/规则：不抽样，逐格看完再列返工清单）。
CHAR/CROWD 3列、PROP 4列、SC 1列，每格左上角烤编号。
"""
import glob
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "qc")
FONT = "/System/Library/Fonts/Helvetica.ttc"

GROUPS = {
    "CHAR": ("CHAR-*.png", "CROWD-*.png", 4, 420),
    "PROP": ("PROP-*.png", None, 4, 460),
    "SC": ("SC-*.png", None, 1, 900),
}


def build(name, pats, cols, cell):
    files = []
    for p in pats:
        if p:
            files += sorted(glob.glob(os.path.join(ROOT, "assets", p)))
    if not files:
        print(f"跳过 {name}: 无文件")
        return
    rows = (len(files) + cols - 1) // cols
    try:
        fnt = ImageFont.truetype(FONT, 26)
    except Exception:  # noqa: BLE001
        fnt = ImageFont.load_default()
    grid = Image.new("RGB", (cols * cell, rows * cell), (26, 26, 28))
    d = ImageDraw.Draw(grid)
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        im.thumbnail((cell - 8, cell - 8))
        x = (i % cols) * cell + (cell - im.width) // 2
        y = (i // cols) * cell + (cell - im.height) // 2
        grid.paste(im, (x, y))
        label = os.path.basename(f).replace(".png", "")
        d.rectangle([(i % cols) * cell, (i // cols) * cell, (i % cols) * cell + 16 * len(label) + 20, (i // cols) * cell + 38],
                    fill=(0, 0, 0))
        d.text(((i % cols) * cell + 10, (i // cols) * cell + 6), label, font=fnt, fill=(255, 235, 120))
    out = os.path.join(OUT, f"SHEET_{name}.png")
    grid.save(out)
    print(f"{out}  ({len(files)} 张)")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n, (p1, p2, c, cell) in GROUPS.items():
        build(n, [p1, p2], c, cell)

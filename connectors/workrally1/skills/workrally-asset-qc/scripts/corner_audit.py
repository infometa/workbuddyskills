#!/usr/bin/env python
"""四角 100% 原尺寸裁切目检拼版（§2f）。
用法: corner_audit.py <图片路径> [<图片路径> ...]
输出: qc/CORNER_<文件名>.png  （四角横排，左上/右上/左下/右下）
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

C = 640
ORDER = ["TL", "TR", "BL", "BR"]


def corners(src, outdir="qc"):
    os.makedirs(outdir, exist_ok=True)
    img = Image.open(src).convert("RGB")
    W, H = img.size
    c = min(C, W // 2, H // 2)
    boxes = {
        "TL": (0, 0, c, c),
        "TR": (W - c, 0, W, c),
        "BL": (0, H - c, c, H),
        "BR": (W - c, H - c, W, H),
    }
    tiles = []
    for k in ORDER:
        t = img.crop(boxes[k]).copy()
        d = ImageDraw.Draw(t)
        try:
            f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
        except Exception:
            f = ImageFont.load_default()
        d.rectangle([0, 0, 118, 46], fill=(0, 0, 0))
        d.text((10, 6), k, font=f, fill=(255, 255, 255))
        tiles.append(t)
    grid = Image.new("RGB", (sum(t.width for t in tiles), max(t.height for t in tiles)), (20, 20, 20))
    x = 0
    for t in tiles:
        grid.paste(t, (x, 0))
        x += t.width
    name = os.path.splitext(os.path.basename(src))[0]
    out = os.path.join(outdir, f"CORNER_{name}.png")
    grid.save(out)
    print(f"{out}  ({W}x{H} -> 四角 {c}px 原尺寸)")
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        corners(p)

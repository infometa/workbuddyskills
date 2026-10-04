#!/usr/bin/env python
"""跨资产同角位拼墙：把全部资产的同一个角按网格排开，用于横向比对图库水印 / 伪文字 / 徽标。

用法:
    corner_wall.py <图片路径> [...]  [--cols 6] [--corner 640] [--outdir qc]

产出:
    qc/CORNERWALL_TL.png
    qc/CORNERWALL_TR.png
    qc/CORNERWALL_BL.png
    qc/CORNERWALL_BR.png

每张墙 = 全部资产的同一个角落，网格排列，每格左上角烧文件名标签。
同角位横比时，被单独看某一角落容易漏掉的水印/徽标会立刻显形。
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

CORNERS = ["TL", "TR", "BL", "BR"]


def corner_box(W, H, k, c):
    c = min(c, W // 2, H // 2)
    return {
        "TL": (0, 0, c, c),
        "TR": (W - c, 0, W, c),
        "BL": (0, H - c, c, H),
        "BR": (W - c, H - c, W, H),
    }[k]


def font(sz):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--corner", type=int, default=640, help="每格裁切边长（原尺寸像素）")
    ap.add_argument("--outdir", default="qc")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    cells = {}  # corner -> list of (tile, label)

    for p in a.images:
        name = os.path.splitext(os.path.basename(p))[0]
        im = Image.open(p).convert("RGB")
        W, H = im.size
        for k in CORNERS:
            t = im.crop(corner_box(W, H, k, a.corner)).copy()
            cells.setdefault(k, []).append((t, name))

    f = font(20)
    LBL = 24      # 标签条高度，紧贴所属图块下沿（0 间距）
    ROWGAP = 26   # 行与行之间的间距，明显大于 0，避免标签归属歧义
    for k in CORNERS:
        items = cells.get(k)
        if not items:
            continue
        cw = max(t.width for t, _ in items)
        ch = max(t.height for t, _ in items)
        pad = 6
        rows = (len(items) + a.cols - 1) // a.cols
        Wt = a.cols * (cw + pad) + pad
        Ht = rows * (ch + LBL + ROWGAP) + pad
        wall = Image.new("RGB", (Wt, Ht), (20, 20, 20))
        d = ImageDraw.Draw(wall)
        for i, (t, label) in enumerate(items):
            r, cidx = divmod(i, a.cols)
            x = pad + cidx * (cw + pad)
            y = pad + r * (ch + LBL + ROWGAP)
            wall.paste(t, (x, y))
            # 标签条紧贴图块下沿，与下一行留有明显间距 → 归属无歧义
            d.rectangle([x, y + ch, x + cw, y + ch + LBL], fill=(0, 0, 0))
            d.text((x + 4, y + ch + 2), label, font=f, fill=(255, 220, 80))
        out = os.path.join(a.outdir, f"CORNERWALL_{k}.png")
        wall.save(out)
        print(f"{out}  ({Wt}x{Ht}, {len(items)} 张)")


if __name__ == "__main__":
    main()

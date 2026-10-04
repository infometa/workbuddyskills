#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《呼噜噜的夏日》字幕图层渲染
本机 ffmpeg 8.1.2 无 ass/subtitles/drawtext 滤镜 → 用 PIL 渲染透明图层 PNG，再由 ffmpeg overlay
规格对齐 §6a-2：中上英下 / 底部居中 / 白字细黑描边
输出：04_字幕/_overlay/cue_XXX.png（2206×946 RGBA 全画布透明底）
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

# 项目根目录：优先取环境变量 PROJ，否则用下面的默认值（按本机实际项目路径修改）
PROJ = os.environ.get("PROJ") or os.path.expanduser("~/WorkBuddy/<你的项目目录>")
WD = os.path.join(PROJ, "99_工作底稿")
OUT = os.path.join(PROJ, "04_字幕", "_overlay")
os.makedirs(OUT, exist_ok=True)

W, H = 2206, 946
CN_FONT = "/System/Library/Fonts/STHeiti Medium.ttc"
EN_FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
CN_SIZE, EN_SIZE = 58, 34
CN_STROKE, EN_STROKE = 3, 2
CN_BOTTOM = H - 96          # 中文行基线底（对齐 ASS MarginV 96）
EN_BOTTOM = H - 52          # 英文行底部（对齐 ASS MarginV 52）

cn_font = ImageFont.truetype(CN_FONT, CN_SIZE, index=1)
en_font = ImageFont.truetype(EN_FONT, EN_SIZE, index=0)

subs = json.load(open(os.path.join(WD, "subs.json")))

def draw_center(dr, text, font, stroke, bottom_y, fill=(255, 255, 255, 255)):
    bbox = dr.textbbox((0, 0), text, font=font, stroke_width=stroke)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (W - w) // 2 - bbox[0]
    y = bottom_y - h - bbox[1]
    dr.text((x, y), text, font=font, fill=fill,
            stroke_width=stroke, stroke_fill=(0, 0, 0, 235))

made = []
for i, s in enumerate(subs):
    key = s["key"]
    cn, en = s.get("cn", ""), s.get("en", "")
    if not cn and not en:
        continue
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    if cn:
        draw_center(dr, cn, cn_font, CN_STROKE, CN_BOTTOM)
    if en:
        draw_center(dr, en, en_font, EN_STROKE, EN_BOTTOM)
    p = os.path.join(OUT, f"cue_{i:03d}.png")
    img.save(p, optimize=True)
    made.append((i, key, round(s["start"], 2), round(s["end"], 2)))

print(f"生成 {len(made)} 张字幕图层 PNG → {OUT}")
for m in made[:6]:
    print("  ", m)
print("   ...")
for m in made[-3:]:
    print("  ", m)

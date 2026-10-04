#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕图层视频 + 成片合板
思路：本机 ffmpeg 无字幕滤镜 → 已由 gen_sub_overlay.py 渲染 66 张透明 PNG；
本脚本用 image2 + concat 生成「字幕图层视频」（cue 段与透明间隙交替），再对成片做**一次** overlay。
用法：python gen_sub_layer.py [--dry]
"""
import json, os, subprocess, sys

# 项目根目录：优先取环境变量 PROJ，否则用下面的默认值（按本机实际项目路径修改）
PROJ = os.environ.get("PROJ") or os.path.expanduser("~/WorkBuddy/<你的项目目录>")
WD = os.path.join(PROJ, "99_工作底稿")
OV = os.path.join(PROJ, "04_字幕", "_overlay")
FIN = os.path.join(PROJ, "05_成片")
W, H, FPS = 2206, 946, 24
TOTAL = 600.861

# 全透明垫片
from PIL import Image
blank = os.path.join(OV, "transparent.png")
if not os.path.exists(blank):
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)

subs = json.load(open(os.path.join(WD, "subs.json")))
segs = []
cursor = 0.0
for i, s in enumerate(subs):
    st, en = float(s["start"]), min(float(s["end"]), TOTAL)
    if st >= TOTAL:
        continue
    if st > cursor + 0.02:
        segs.append((blank, st - cursor))
        cursor = st
    if en <= cursor + 0.02:
        continue
    st2 = max(st, cursor)
    segs.append((os.path.join(OV, f"cue_{i:03d}.png"), en - st2))
    cursor = en
if cursor < TOTAL - 0.02:
    segs.append((blank, TOTAL - cursor))

print(f"图层段数：{len(segs)}（cue {sum(1 for p,_ in segs if p != blank)} + 间隙 {sum(1 for p,_ in segs if p == blank)}）")

ins, fc, labels = [], [], []
for k, (path, dur) in enumerate(segs):
    ins += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", path]
    # 注意：-i base 是输入 0，图层段依次是输入 1..N，故此处用 k+1
    fc.append(f"[{k + 1}:v]format=rgba,setpts=PTS-STARTPTS[s{k}]")
    labels.append(f"[s{k}]")
fc.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[layer]")

base = os.path.join(FIN, "呼噜噜的夏日_成片_无字幕.mp4")
out = os.path.join(FIN, "呼噜噜的夏日_成片_双语字幕.mp4")

tlimit = TOTAL
for a in sys.argv:
    if a.startswith("--tlimit="):
        tlimit = float(a.split("=")[1])
        out = os.path.join(WD, "textcheck", "TEST_字幕合板.mp4")
        os.makedirs(os.path.dirname(out), exist_ok=True)

cmd = ["ffmpeg", "-y", "-v", "error", "-i", base] + ins + [
    "-filter_complex", ";".join(fc) + ";[0:v][layer]overlay=0:0:format=auto,format=yuv420p[vout]",
    "-map", "[vout]", "-map", "0:a:0",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "copy", "-movflags", "+faststart",
    "-t", f"{tlimit:.3f}", out,
]

if "--dry" in sys.argv:
    print("inputs:", len(ins) // 6, " filter len:", len(cmd[cmd.index("-filter_complex") + 1]))
    sys.exit(0)

print("开始合板（libx264 crf18 · 600s · 2206×946）...", flush=True)
r = subprocess.run(cmd)
print("rc =", r.returncode)
if r.returncode == 0:
    print("✅", out, os.path.getsize(out) / 1e6, "MB")

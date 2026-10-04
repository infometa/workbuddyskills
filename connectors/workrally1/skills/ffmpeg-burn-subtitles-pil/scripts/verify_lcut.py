#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L-cut 跨单元对白接续验证（信号级）
对每条跨单元对白：取目标单元混音首段音频，与源对白文件「应播区段」做归一化互相关。
期望：峰值出现在 lag≈0（±1 帧内），系数显著高于旁瓣。
"""
import json, os, subprocess, sys
import numpy as np

# 项目根目录：优先取环境变量 PROJ，否则用下面的默认值（按本机实际项目路径修改）
PROJ = os.environ.get("PROJ") or os.path.expanduser("~/WorkBuddy/<你的项目目录>")
WD = os.path.join(PROJ, "99_工作底稿")
VO = os.path.join(PROJ, "03_声音", "对白")
FIN = os.path.join(PROJ, "05_成片")
SR = 48000
U = 30.0417


def dec(path, start=0.0, dur=None, ar=SR):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.4f}"]
    if dur:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-i", path, "-vn", "-ac", "1", "-ar", str(ar), "-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)


def ncc(a, b, max_lag_s=0.4):
    """归一化互相关，返回 (best_lag_s, peak)"""
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    m = int(max_lag_s * SR)
    best, bl = -2.0, 0
    for lag in range(-m, m + 1):
        if lag >= 0:
            x, y = a[:n - lag], b[lag:n]
        else:
            x, y = a[-lag:n], b[:n + lag]
        if len(x) < SR * 0.4:
            continue
        d = np.linalg.norm(x) * np.linalg.norm(y)
        if d < 1e-9:
            continue
        c = float(np.dot(x, y) / d)
        if c > best:
            best, bl = c, lag
    return bl / SR, best


subs = json.load(open(os.path.join(WD, "subs.json")))
def unit_of(t):
    return int(t // U) + 1

cross = []
for r in subs:
    u1, u2 = unit_of(float(r["start"])), unit_of(float(r["end"]) - 0.001)
    if u1 != u2:
        cross.append((r, u1, u2))

print(f"跨单元对白 {len(cross)} 条 · 信号级接续验证\n")
print(f"{'对白':<24}{'单元':<10}{'期望lag':>9}{'实测lag':>9}{'NCC':>8}  判定")
print("-" * 72)

allok = True
for r, u1, u2 in cross:
    key = r["key"]
    u0 = (u2 - 1) * U                    # 目标单元起点（全片秒）
    offset = u0 - float(r["start"])      # 源文件内应播起点
    dur = float(r["end"]) - u0
    src = os.path.join(VO, key + ".mp3")
    if not os.path.exists(src):
        print(f"{key:<24}源文件缺失"); allok = False; continue
    seg = dec(src, start=max(0.0, offset), dur=dur)
    mixp = os.path.join(FIN, f"U{u2:02d}_mix.mp4")
    mix = dec(mixp, start=0.0, dur=dur)
    n = min(len(seg), len(mix))
    if n < SR * 0.20:
        print(f"{key:<24}样本不足 ({n})"); allok = False; continue
    lag, peak = ncc(seg, mix)
    ok = abs(lag) <= 0.05 and peak >= 0.30
    allok &= ok
    print(f"{key:<24}{f'U{u1:02d}→U{u2:02d}':<10}{'0.000':>9}{lag:>9.3f}{peak:>8.3f}  {'✅' if ok else '⚠️'}")

print("-" * 72)
print("总体：", "✅ 全部接续正确" if allok else "⚠️ 存在偏差，需人工复核")

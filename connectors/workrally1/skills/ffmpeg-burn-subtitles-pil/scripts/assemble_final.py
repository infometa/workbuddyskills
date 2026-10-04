#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整交付版装配：片头板 → 正片（双语字幕）→ 片尾板
三段统一为 2206×946 / 24fps / h264 yuv420p / AAC 48kHz 立体声，再无损 concat。
用法：python assemble_final.py [--intro=6] [--outro=8] [--dry]
"""
import os, subprocess, sys, json

# 项目根目录：优先取环境变量 PROJ，否则用下面的默认值（按本机实际项目路径修改）
PROJ = os.environ.get("PROJ") or os.path.expanduser("~/WorkBuddy/<你的项目目录>")
PKG = os.path.join(PROJ, "04_包装")
FIN = os.path.join(PROJ, "05_成片")
WD = os.path.join(PROJ, "99_工作底稿")
TMP = os.path.join(WD, "_assemble")
os.makedirs(TMP, exist_ok=True)

W, H, FPS = 2206, 946, 24
SR = 48000

INTRO = os.path.join(PKG, "P01_片头板_成品.png")
OUTRO = os.path.join(PKG, "P02_片尾板_成品.png")
MAIN = os.path.join(FIN, "呼噜噜的夏日_成片_双语字幕.mp4")
OUT = os.path.join(FIN, "呼噜噜的夏日_完整交付版.mp4")

intro_d, outro_d = 6.0, 8.0
for a in sys.argv:
    if a.startswith("--intro="):
        intro_d = float(a.split("=")[1])
    if a.startswith("--outro="):
        outro_d = float(a.split("=")[1])


def build_card(src, dur, dst, fi=1.0, fo=0.8, zoom=0.0):
    """静态图 → 指定时长视频（含淡入淡出 + 静音轨）。zoom>0 时加极缓推镜。"""
    vf = [f"scale={W}:{H}:force_original_aspect_ratio=decrease",
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black"]
    if zoom > 0:
        # 极缓推镜：以 2*zoom 的采样率做 zoompan，24fps
        vf = [f"scale={int(W*2)}:{int(H*2)}:force_original_aspect_ratio=decrease",
              f"pad={int(W*2)}:{int(H*2)}:(ow-iw)/2:(oh-ih)/2:color=black",
              f"zoompan=z='min(zoom+{zoom},1.3)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}"]
    vf += [f"fade=t=in:st=0:d={fi}", f"fade=t=out:st={dur - fo:.3f}:d={fo}", "format=yuv420p"]
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", src,
           "-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"anullsrc=r={SR}:cl=stereo",
           "-vf", ",".join(vf),
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2",
           "-movflags", "+faststart", "-t", f"{dur:.3f}", dst]
    if "--dry" in sys.argv:
        print("CARD", os.path.basename(dst), "vf=", ",".join(vf))
        return True
    r = subprocess.run(cmd)
    ok = r.returncode == 0 and os.path.exists(dst)
    print(("✅" if ok else "❌"), os.path.basename(dst),
          (f"{os.path.getsize(dst)/1e6:.1f} MB" if ok else ""))
    return ok


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
                        "-of", "json", p], capture_output=True, text=True)
    return json.loads(r.stdout)


print("① 生成片头板片段 ...")
i_ok = build_card(INTRO, intro_d, os.path.join(TMP, "00_intro.mp4"), zoom=0.0006)
print("② 生成片尾板片段 ...")
o_ok = build_card(OUTRO, outro_d, os.path.join(TMP, "99_outro.mp4"), zoom=0.0006)

if not (i_ok and o_ok):
    print("❌ 片段生成失败"); sys.exit(1)

# ③ 统一拼接
parts = [os.path.join(TMP, "00_intro.mp4"), MAIN, os.path.join(TMP, "99_outro.mp4")]
lst = os.path.join(TMP, "concat_final.txt")
with open(lst, "w") as f:
    for p in parts:
        f.write(f"file '{p}'\n")

if "--dry" in sys.argv:
    for p in parts:
        print("PRT", os.path.basename(p), json.dumps(probe(p), ensure_ascii=False)[:260])
    sys.exit(0)

print("③ 无损拼接 ...")
r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", "-movflags", "+faststart", OUT])
print("rc =", r.returncode)
if r.returncode == 0:
    d = probe(OUT)
    print("✅", OUT)
    print("   ", json.dumps(d, ensure_ascii=False))

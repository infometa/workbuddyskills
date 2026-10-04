#!/usr/bin/env python3
"""
med-podcast-generator — 播客音频合成脚本
将播客脚本 JSON 合成为 m4a 音频（macOS say + afconvert + Python wave 拼接）。

依赖：macOS 原生 say / afconvert，Python 标准库 wave（无需 ffmpeg/联网）。
输入 JSON 格式：
{
  "title": "节目标题",
  "mode": "solo" | "dialogue",
  "voice": "Ting-Ting",            # solo 模式默认 voice，或每段单独指定
  "segments": [
    {"speaker": "host",  "voice": "Eddy",      "text": "..."},
    {"speaker": "guest", "voice": "Ting-Ting", "text": "..."}
  ]
}
"""
import argparse
import json
import os
import sys
import subprocess
import tempfile
import wave
import shutil


def say_to_aiff(text, voice, out_aiff):
    """调用 macOS say 生成 AIFF 语音片段。"""
    subprocess.run(["say", "-v", voice, "-o", out_aiff, text], check=True)


def aiff_to_wav(aiff, wav):
    """afconvert 将 AIFF-C 转线性 PCM WAV（标准格式，Python wave 可读取）。"""
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", aiff, wav], check=True)


def make_silence(channels, sampwidth, framerate, seconds=0.3):
    """生成指定时长的静音帧，用于段落间自然停顿。"""
    n_frames = int(framerate * seconds)
    return b"\x00" * (n_frames * channels * sampwidth)


def merge_wavs(wavs, out_wav, silence_sec=0.3):
    """拼接多个 WAV，每段间插入静音停顿。"""
    with wave.open(wavs[0], "rb") as w0:
        params = (w0.getnchannels(), w0.getsampwidth(), w0.getframerate())
    with wave.open(out_wav, "wb") as out:
        out.setnchannels(params[0])
        out.setsampwidth(params[1])
        out.setframerate(params[2])
        for w in wavs:
            with wave.open(w, "rb") as wi:
                out.writeframes(wi.readframes(wi.getnframes()))
            out.writeframes(make_silence(params[0], params[1], params[2], silence_sec))


def wav_to_m4a(wav, m4a):
    """afconvert 将 WAV 压成 AAC m4a。"""
    subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", wav, m4a], check=True)


def write_script_md(data, out_md):
    """保存播客脚本文本，便于对照/字幕。"""
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(f"# {data.get('title', '播客脚本')}\n\n")
        f.write(f"> 模式：{data.get('mode', 'solo')}\n\n---\n\n")
        for seg in data.get("segments", []):
            speaker = seg.get("speaker", "host")
            text = seg.get("text", "")
            f.write(f"**{speaker}**：{text}\n\n")


def main():
    ap = argparse.ArgumentParser(description="医学播客音频合成器")
    ap.add_argument("--input", required=True, help="播客脚本 JSON 路径")
    ap.add_argument("--output", required=True, help="输出 m4a 路径")
    ap.add_argument("--script-out", default=None, help="可选：脚本 md 输出路径")
    ap.add_argument("--silence", type=float, default=0.3, help="段落间停顿秒数（默认 0.3）")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    default_voice = data.get("voice", "Ting-Ting")
    segments = data.get("segments", [])
    if not segments:
        print("ERROR: segments 为空", file=sys.stderr)
        sys.exit(1)

    tmp = tempfile.mkdtemp()
    wavs = []
    try:
        for i, seg in enumerate(segments):
            voice = seg.get("voice") or default_voice
            text = seg.get("text", "").strip()
            if not text:
                continue
            aiff = os.path.join(tmp, f"seg_{i}.aiff")
            wav = os.path.join(tmp, f"seg_{i}.wav")
            print(f"[TTS] seg{i} voice={voice} chars={len(text)}")
            say_to_aiff(text, voice, aiff)
            aiff_to_wav(aiff, wav)
            wavs.append(wav)

        if not wavs:
            print("ERROR: 没有生成任何音频段", file=sys.stderr)
            sys.exit(1)

        merged = os.path.join(tmp, "merged.wav")
        merge_wavs(wavs, merged, silence_sec=args.silence)
        wav_to_m4a(merged, args.output)
        print(f"[OK] 音频 -> {args.output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    script_out = args.script_out or (os.path.splitext(args.output)[0] + "_script.md")
    write_script_md(data, script_out)
    print(f"[OK] 脚本 -> {script_out}")


if __name__ == "__main__":
    main()

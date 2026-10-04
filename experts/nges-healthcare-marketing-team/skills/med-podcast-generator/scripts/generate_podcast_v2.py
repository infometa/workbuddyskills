#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
med-podcast-generator v2 — 医学播客音频合成（edge-tts 真人级神经网络音色）

相比 v1（macOS say）的升级：
  - 音色：微软神经网络真人级音色（Yunxi/Xiaoxiao/Yunyang 等），生动自然
  - 格式：直接输出 mp3（不再受 macOS 无 mp3 编码器限制）
  - 发音：内置医学英文缩写发音修正（字母间加空格，确保逐字母清晰朗读）
  - 表现力：支持 rate / volume / pitch 精调，主持人与嘉宾差异化语速

依赖：edge-tts（pip install edge-tts -i https://mirrors.cloud.tencent.com/pypi/simple/）
需联网（微软 TTS 服务）。若离线，回退用 v1 的 generate_podcast.py。

用法：
  python3 generate_podcast_v2.py --input script.json --output out.mp3
"""

import argparse
import asyncio
import json
import os
import re
import sys
import tempfile

try:
    import edge_tts
except ImportError:
    sys.exit("[ERR] 缺少 edge-tts。安装：pip install edge-tts "
             "-i https://mirrors.cloud.tencent.com/pypi/simple/")


# ---------------------------------------------------------------------------
# 医学英文缩写发音修正
# ---------------------------------------------------------------------------
# 原理：edge-tts 对连写的英文缩写（如 EGFR）常整体误读或读成单词。
# 在字母间插入空格可强制逐字母朗读（实测：EGFR-TKI 原样 6.4s vs 空格分隔 7.6s，
# 后者字母清晰）。注意 edge-tts 不支持 SSML（say-as 标签会被转义为文本）。
#
# ALWAYS_SPLIT：需逐字母朗读的纯缩写
# KEEP_AS_WORD：本身是可读单词/习惯读法，保持原样
# ---------------------------------------------------------------------------

ALWAYS_SPLIT = [
    # 组合缩写（必须排在单个缩写之前整体匹配，否则连字符会残留）
    "EGFR-TKI", "ALK-TKI", "ROS1-TKI", "MET-TKI", "RET-TKI", "BTK-TKI",
    "PD-L1", "PD-1", "CTLA-4", "CAR-T", "IL-6", "HER2-ADC",
    # 靶点 / 基因
    "EGFR", "TKI", "ALK", "ROS1", "KRAS", "BRAF", "MET", "RET", "HER2",
    "NTRK", "VEGF", "VEGFR", "TMB", "MSI",
    # 疾病 / 分型
    "NSCLC", "SCLC", "RSV", "COPD", "ARDS", "AECOPD",
    # 疗效 / 终点指标
    "ORR", "PFS", "OS", "DCR", "DOR", "TTP", "DFS", "EFS", "RFS",
    "CR", "PR", "SD", "PD", "AE", "SAE", "TRAE", "irAE",
    # 检测 / 技术
    "NGS", "PCR", "ctDNA", "IHC", "FISH", "CT", "MRI", "PET", "ECOG",
    # 机构 / 指南
    "CSCO", "NCCN", "ESMO", "ASCO", "WCLC", "AACR", "FDA", "NMPA", "EMA",
    "WHO", "GCP", "CDE",
    # 其他常见
    "ICU", "QoL", "BMI", "LDH", "CEA", "AFP", "HBV", "HCV", "HIV",
    "mAb", "ADC", "BiTE", "IgG", "TNF",
]

KEEP_AS_WORD = {
    "MELODY", "HARMONIE", "MEDLEY", "FLAURA", "AURA", "ADAURA",
    "CheckMate", "KEYNOTE", "IMpower", "MARIPOSA", "PAPILLON",
}


def _split_letters(token: str) -> str:
    """把缩写拆成空格分隔的字母序列。

    统一转大写（避免 QoL 里小写 o 被含糊处理），连字符替换为空格
    （连字符若紧贴字母易造成连读，如 "E G F R-T K I"）。

    EGFR      -> "E G F R"
    EGFR-TKI  -> "E G F R T K I"
    PD-L1     -> "P D L 1"
    ROS1      -> "R O S 1"
    QoL       -> "Q O L"
    """
    chars = [ch.upper() for ch in token if ch != "-"]
    return " ".join(chars)


def fix_pronunciation(text: str, extra_split=None, extra_keep=None) -> str:
    """对文本中的医学英文缩写做发音修正。

    只处理词边界完整匹配的缩写，避免破坏正常中英文。
    """
    keep = set(KEEP_AS_WORD)
    if extra_keep:
        keep |= set(extra_keep)

    terms = list(ALWAYS_SPLIT)
    if extra_split:
        terms = list(extra_split) + terms
    # 长词优先，避免 PD 抢先匹配掉 PD-L1
    terms.sort(key=len, reverse=True)

    for term in terms:
        if term in keep:
            continue
        # 词边界：前后不能紧跟字母/数字（允许中文、标点、空白、行首行尾）
        pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
        text = re.sub(pattern, _split_letters(term), text)

    # 合并多余空格（中文间不留双空格）
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


# ---------------------------------------------------------------------------
# 音色预设
# ---------------------------------------------------------------------------
# 说明（edge-tts zh-CN 可用音色）：
#   zh-CN-YunxiNeural     男 Lively/Sunshine   —— 主持人首选，活泼有亲和力
#   zh-CN-YunyangNeural   男 Professional      —— 专家/教授首选，沉稳可靠
#   zh-CN-XiaoxiaoNeural  女 Warm              —— 主持人/旁白，温暖自然
#   zh-CN-XiaoyiNeural    女 Lively            —— 活泼女声
#   zh-CN-YunjianNeural   男 Passion           —— 激情解说
#   zh-CN-YunxiaNeural    男 Cute              —— 年轻男声
# ---------------------------------------------------------------------------

VOICE_PRESETS = {
    "host":   {"voice": "zh-CN-YunxiNeural",    "rate": "+6%",  "pitch": "+2Hz"},
    "guest":  {"voice": "zh-CN-YunyangNeural",  "rate": "-4%",  "pitch": "+0Hz"},
    "solo":   {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+2%",  "pitch": "+0Hz"},
}

# 兼容 v1 的 macOS say 音色名 -> edge-tts 音色映射
LEGACY_VOICE_MAP = {
    "Eddy": "zh-CN-YunxiNeural",
    "Ting-Ting": "zh-CN-XiaoxiaoNeural",
    "Tingting": "zh-CN-XiaoxiaoNeural",
    "Meijia": "zh-CN-XiaoyiNeural",
    "Mei-Jia": "zh-CN-XiaoyiNeural",
    "Flo": "zh-CN-XiaoyiNeural",
    "Grandpa": "zh-CN-YunyangNeural",
    "Grandma": "zh-CN-XiaoxiaoNeural",
    "Reed": "zh-CN-YunjianNeural",
    "Rocko": "zh-CN-YunxiaNeural",
}


def resolve_voice(seg: dict, mode: str) -> dict:
    """决定某段使用的音色与参数。优先级：段内显式 > 预设 > 兜底。"""
    speaker = (seg.get("speaker") or "host").lower()

    if mode == "solo":
        base = dict(VOICE_PRESETS["solo"])
    else:
        base = dict(VOICE_PRESETS.get(speaker, VOICE_PRESETS["host"]))

    v = seg.get("voice")
    if v:
        # 兼容旧的 say 音色名
        base["voice"] = LEGACY_VOICE_MAP.get(v, v)

    for k in ("rate", "volume", "pitch"):
        if seg.get(k):
            base[k] = seg[k]
    return base


# ---------------------------------------------------------------------------
# 音频合成
# ---------------------------------------------------------------------------

async def synth_segment(text: str, opts: dict, out_path: str):
    kwargs = {"voice": opts["voice"]}
    for k in ("rate", "volume", "pitch"):
        if opts.get(k):
            kwargs[k] = opts[k]
    comm = edge_tts.Communicate(text, **kwargs)
    await comm.save(out_path)


def concat_mp3(parts, out_path, gap_ms=320):
    """拼接多个 mp3。

    关键：edge-tts 输出的已是标准 MPEG Layer-3 音频，mp3 帧格式支持直接
    字节流顺序拼接，无需解码重编码——既保住真 mp3 格式，也零质量损失。
    （注意：afconvert 只能解码 mp3、不能编码，Apple 未授权 LAME；
    若走 WAV 中转会被迫降级成 m4a/AAC。）

    段间停顿：脚本中每段以句号结尾，edge-tts 自带尾部静音，
    实测衔接自然；如需更长停顿，在脚本文本末尾加「。」或用 ffmpeg 精调。
    """
    if not parts:
        raise RuntimeError("没有可拼接的音频段")

    # 确保输出为 .mp3
    if not out_path.lower().endswith(".mp3"):
        out_path = os.path.splitext(out_path)[0] + ".mp3"

    with open(out_path, "wb") as out:
        for p in parts:
            with open(p, "rb") as f:
                out.write(f.read())

    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError("mp3 拼接失败")
    return out_path


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

async def run(cfg: dict, out_path: str, no_fix: bool = False):
    mode = cfg.get("mode", "solo")
    segments = cfg.get("segments") or []
    if not segments:
        sys.exit("[ERR] segments 为空")

    extra_split = cfg.get("extra_split_terms")
    extra_keep = cfg.get("keep_as_word_terms")

    tmpdir = tempfile.mkdtemp(prefix="podcast_seg_")
    parts, script_lines = [], []

    for i, seg in enumerate(segments):
        raw = (seg.get("text") or "").strip()
        if not raw:
            continue
        spoken = raw if no_fix else fix_pronunciation(raw, extra_split, extra_keep)
        opts = resolve_voice(seg, mode)

        p = os.path.join(tmpdir, f"seg{i:03d}.mp3")
        await synth_segment(spoken, opts, p)
        if not os.path.exists(p):
            sys.exit(f"[ERR] 第 {i} 段合成失败")
        parts.append(p)

        who = seg.get("speaker_name") or (
            "主持人" if (seg.get("speaker") or "host").lower() == "host" else "嘉宾")
        print(f"[TTS] seg{i} {opts['voice']} rate={opts.get('rate','0%')} chars={len(raw)}")
        script_lines.append(f"**{who}**：{raw}\n")

    final = concat_mp3(parts, out_path) if len(parts) > 1 else _single(parts[0], out_path)

    # 脚本文本
    base = os.path.splitext(final)[0]
    md = base + "_script.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# {cfg.get('title', '医学播客')}\n\n")
        f.write(f"- 形式：{'双人对话' if mode == 'dialogue' else '单人讲解'}\n")
        f.write(f"- 引擎：edge-tts（微软神经网络音色）\n\n---\n\n")
        f.write("\n".join(script_lines))

    print(f"[OK] 音频 -> {final}")
    print(f"[OK] 脚本 -> {md}")
    return final


def _single(part, out_path):
    """单段：edge-tts 输出已是标准 mp3，直接复制即可。"""
    import shutil
    if not out_path.lower().endswith(".mp3"):
        out_path = os.path.splitext(out_path)[0] + ".mp3"
    shutil.copy(part, out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="医学播客音频合成 v2（edge-tts）")
    ap.add_argument("--input", required=True, help="脚本 JSON 路径")
    ap.add_argument("--output", required=True, help="输出音频路径（建议 .mp3）")
    ap.add_argument("--no-fix", action="store_true",
                    help="禁用英文缩写发音自动修正")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印发音修正后的文本，不合成")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        cfg = json.load(f)

    if args.dry_run:
        for i, seg in enumerate(cfg.get("segments", [])):
            raw = (seg.get("text") or "").strip()
            print(f"--- seg{i} ---")
            print(fix_pronunciation(raw) if not args.no_fix else raw)
        return

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    asyncio.run(run(cfg, args.output, args.no_fix))


if __name__ == "__main__":
    main()

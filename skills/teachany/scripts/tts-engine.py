#!/usr/bin/env python3
"""
TeachAny TTS 多引擎抽象层（v7.9.5 新增）

================================================================
解决根因：Edge TTS 依赖的微软 wss://speech.platform.bing.com 在国内
443 端口经常被防火墙拦截或丢包，导致 edge-tts 命令"成功"返回但写出
0 字节 mp3，脚本误以为成功 → L3 TTS 大量交付失败。
================================================================

发布级引擎（v7.12.1 起强制）：
  L0  edge-tts            ：高质量 Neural TTS，发布唯一合格来源
  L1  edge-tts (代理重试) ：通过 HTTP_PROXY / HTTPS_PROXY 重试，仍属 Neural TTS

已禁用低质量回退：macOS say / pyttsx3 / silent.mp3 不再作为发布音频兜底。
如果 Edge TTS 不可用，构建必须失败，而不是交付低质量音频或浏览器 Web Speech。

调用方式（CLI）：
    python3 scripts/tts-engine.py --text "你好" --voice zh-CN-XiaoxiaoNeural --output /tmp/test.mp3

调用方式（Python）：
    from tts_engine import synthesize
    ok, engine = synthesize(text="你好", voice="zh-CN-XiaoxiaoNeural", output="/tmp/test.mp3")

返回值：
    ok=True        音频已生成且大小>=200B
    engine='edge-tts' / 'edge-tts-proxy'
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MIN_VALID_SIZE = 200  # bytes; 0 字节 / 几十字节都视为失败
EDGE_TIMEOUT = 18     # 单次 edge-tts 调用超时（秒），过短会在慢网误杀，过长会拖慢 fallback
EDGE_PROXY_TIMEOUT = 12  # 代理重试超时（更短，因为本地代理可能根本不存在）
RETRY = 1             # edge-tts 直连重试次数（1 次足够，继续失败应快速进入 fallback）

# ============== voice 映射（Edge → macOS say）==============
SAY_VOICE_MAP = {
    "zh-CN-XiaoxiaoNeural":  "Tingting",   # 普通话女声
    "zh-CN-YunxiNeural":     "Sinji",
    "zh-CN-YunyangNeural":   "Tingting",
    "zh-CN-XiaoyiNeural":    "Tingting",
    "en-US-AriaNeural":      "Samantha",
    "en-US-EmmaNeural":      "Samantha",
    "en-US-GuyNeural":       "Alex",
    "en-US-JennyNeural":     "Samantha",
    "en-US-AnaNeural":       "Samantha",
    "en-GB-SoniaNeural":     "Daniel",
    # default fallback by language prefix
    "_zh_default": "Tingting",
    "_en_default": "Samantha",
}

# ============== voice 映射（Edge → pyttsx3）==============
PYTTSX3_VOICE_HINT = {
    "zh": ["Tingting", "Sinji", "zh", "chinese"],
    "en": ["Samantha", "Alex", "en", "english"],
}


def _file_ok(path: str | Path) -> bool:
    p = Path(path)
    return p.exists() and p.stat().st_size >= MIN_VALID_SIZE


def _try_edge_tts(text: str, voice: str, output: str,
                   env: dict | None = None, timeout: int = EDGE_TIMEOUT) -> bool:
    """调用 edge-tts 生成音频。**关键**：必须验证文件大小，0 字节视为失败。"""
    if not shutil.which("edge-tts"):
        return False
    cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", output]
    try:
        # 删除旧文件，避免误判
        if os.path.exists(output):
            os.remove(output)
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout, env=env)
        if result.returncode != 0:
            return False
        return _file_ok(output)
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def _tcp_connect_ok(host: str, port: int, timeout: float = 1.0) -> bool:
    """快速 TCP 连通性探测，避免把时间浪费在不存在的本地代理上。"""
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def _try_macos_say(text: str, voice: str, output: str) -> bool:
    """macOS 系统 say 命令 + ffmpeg 转 mp3。仅 macOS 可用。"""
    if sys.platform != "darwin":
        return False
    if not shutil.which("say") or not shutil.which("ffmpeg"):
        return False
    # 选择 say 的 voice
    say_voice = SAY_VOICE_MAP.get(voice)
    if not say_voice:
        # 按语言前缀回退
        if voice.startswith(("zh-", "zh_")):
            say_voice = SAY_VOICE_MAP["_zh_default"]
        elif voice.startswith(("en-", "en_")):
            say_voice = SAY_VOICE_MAP["_en_default"]
        else:
            say_voice = SAY_VOICE_MAP["_en_default"]

    try:
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
            aiff_path = tmp.name
        # say 生成 aiff
        r1 = subprocess.run(
            ["say", "-v", say_voice, "-o", aiff_path, text],
            capture_output=True, text=True, timeout=60
        )
        if r1.returncode != 0 or not os.path.exists(aiff_path):
            return False
        # ffmpeg 转 mp3
        if os.path.exists(output):
            os.remove(output)
        r2 = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", aiff_path,
             "-codec:a", "libmp3lame", "-qscale:a", "4", output],
            capture_output=True, text=True, timeout=30
        )
        try:
            os.remove(aiff_path)
        except OSError:
            pass
        return _file_ok(output)
    except Exception:
        return False


def _try_pyttsx3(text: str, voice: str, output: str) -> bool:
    """pyttsx3 跨平台离线 TTS。需要 ffmpeg 转 mp3。"""
    try:
        import pyttsx3  # type: ignore
    except ImportError:
        return False
    if not shutil.which("ffmpeg"):
        return False

    lang_prefix = "zh" if voice.startswith(("zh-", "zh_")) else "en"
    hints = PYTTSX3_VOICE_HINT[lang_prefix]

    try:
        engine = pyttsx3.init()
        # 选择最匹配的 voice
        voices = engine.getProperty("voices")
        chosen = None
        for v in voices:
            name_lower = (v.name or "").lower()
            for h in hints:
                if h.lower() in name_lower or h.lower() in (v.id or "").lower():
                    chosen = v.id
                    break
            if chosen:
                break
        if chosen:
            engine.setProperty("voice", chosen)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        engine.save_to_file(text, wav_path)
        engine.runAndWait()
        if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
            return False
        # 转 mp3
        if os.path.exists(output):
            os.remove(output)
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path,
             "-codec:a", "libmp3lame", "-qscale:a", "4", output],
            capture_output=True, text=True, timeout=30
        )
        try:
            os.remove(wav_path)
        except OSError:
            pass
        return _file_ok(output)
    except Exception:
        return False


def _generate_silent(output: str, duration: float = 1.0) -> bool:
    """最后的兜底：生成 N 秒静音 mp3。前端 teachany-tts-narrator.js 会用 Web Speech 朗读。"""
    if not shutil.which("ffmpeg"):
        return False
    try:
        if os.path.exists(output):
            os.remove(output)
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "lavfi", "-i", f"anullsrc=r=22050:cl=mono",
             "-t", str(duration), "-q:a", "9", output],
            capture_output=True, text=True, timeout=15
        )
        return _file_ok(output)
    except Exception:
        return False


def synthesize(text: str, voice: str, output: str,
               allow_silent_fallback: bool = True,
               verbose: bool = False) -> tuple[bool, str]:
    """
    生成 TTS 音频，按引擎优先级自动回退。

    返回：(ok, engine_used)
      ok=True 当且仅当输出文件存在且 size >= MIN_VALID_SIZE。
    """
    os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)

    # ---- L0: edge-tts 直连 ----
    for attempt in range(RETRY + 1):
        if _try_edge_tts(text, voice, output):
            if verbose:
                print(f"  ✅ edge-tts 直连成功（尝试 #{attempt+1}）")
            return True, "edge-tts"
        if verbose:
            print(f"  ⚠️ edge-tts 直连失败（尝试 #{attempt+1}）")

    # ---- L1: edge-tts via 系统代理（HTTP_PROXY / HTTPS_PROXY） ----
    # 如果用户已设置代理环境变量，前一步就用了；否则尝试常见本地代理
    # 关键：先 TCP 探测代理是否存在，避免在不存在的代理上浪费 18 秒超时
    proxy_candidates = []
    if not os.environ.get("HTTPS_PROXY") and not os.environ.get("https_proxy"):
        for proxy_url, host, port in [
            ("http://127.0.0.1:7890", "127.0.0.1", 7890),
            ("http://127.0.0.1:1087", "127.0.0.1", 1087),
            ("http://127.0.0.1:8080", "127.0.0.1", 8080),
        ]:
            if _tcp_connect_ok(host, port, timeout=0.5):
                proxy_candidates.append(proxy_url)
            elif verbose:
                print(f"  ⏭️ 跳过代理 {proxy_url}（端口未开放）")
    for proxy in proxy_candidates:
        env = os.environ.copy()
        env["HTTPS_PROXY"] = proxy
        env["HTTP_PROXY"] = proxy
        if _try_edge_tts(text, voice, output, env=env, timeout=EDGE_PROXY_TIMEOUT):
            if verbose:
                print(f"  ✅ edge-tts 通过代理 {proxy} 成功")
            return True, f"edge-tts-proxy({proxy})"

    # v7.12.1: 发布音频必须是 Edge Neural TTS。
    # 明确禁止 macOS say / pyttsx3 / silent.mp3 / Web Speech 作为“完成”的兜底，
    # 避免低质量音频进入课件。Edge 不通就失败，让构建者修网络/代理。
    if verbose:
        print("  ❌ Edge Neural TTS 不可用：已禁用 macOS say / pyttsx3 / silent / Web Speech 低质量回退")
    return False, "edge-neural-required"


def probe_edge_tts() -> tuple[bool, str]:
    """实测 wss 连通性：生成一个 1 秒探针音频。返回 (是否通畅, 详情)。"""
    if not shutil.which("edge-tts"):
        return False, "edge-tts 命令不可用"
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        probe_path = tmp.name
    try:
        ok = _try_edge_tts("测试", "zh-CN-XiaoxiaoNeural", probe_path)
        if ok:
            return True, "wss 连通，能生成有效 mp3"
        # 区分两种失败：文件存在但 0 字节 vs 命令完全失败
        if os.path.exists(probe_path):
            size = os.path.getsize(probe_path)
            return False, f"wss 不通：edge-tts 写出 {size} 字节（应 ≥{MIN_VALID_SIZE} 字节）"
        return False, "edge-tts 调用超时或异常"
    finally:
        try:
            os.remove(probe_path)
        except OSError:
            pass


def main():
    p = argparse.ArgumentParser(description="TeachAny 多引擎 TTS")
    p.add_argument("--text", required=False, help="要朗读的文本")
    p.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="Edge TTS voice 名")
    p.add_argument("--output", required=False, help="输出 mp3 路径")
    p.add_argument("--probe", action="store_true", help="只做 edge-tts wss 连通性探针")
    p.add_argument("--no-silent-fallback", action="store_true",
                   help="兼容旧参数；v7.12.1 起静音/低质量回退已永久禁用")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    if args.probe:
        ok, msg = probe_edge_tts()
        print(("✅" if ok else "❌"), msg)
        sys.exit(0 if ok else 1)

    if not args.text or not args.output:
        p.error("--text 和 --output 必填（除非用 --probe）")

    ok, engine = synthesize(
        args.text, args.voice, args.output,
        allow_silent_fallback=not args.no_silent_fallback,
        verbose=args.verbose
    )
    if ok:
        size = os.path.getsize(args.output)
        print(f"✅ 已生成 {args.output}（{size} 字节，引擎={engine}）")
        sys.exit(0)
    print(f"❌ Edge Neural TTS 失败；低质量回退已禁用")
    sys.exit(2)


if __name__ == "__main__":
    main()

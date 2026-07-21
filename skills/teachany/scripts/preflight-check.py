#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TeachAny · preflight-check.py (v5.34.11, 2026-04-20)

===========================================================================
目的
===========================================================================
在 AI 开始生成课件（Phase 1）之前，**强制自检并尽量自愈**课件生产所需的
全部工具链。面向国产模型（DeepSeek / Qwen / GLM / Kimi 等）常见的坏习惯：
    • 看到"edge-tts 没装"就默默跳过 L3 语音
    • 看到"Node 没装"就默默跳过 L2 Remotion
    • 看到"image_gen 不可用"就把插图全换成 emoji
    • 看到"cwebp 没装"就提交原图导致课件体积炸
    • 看到"Leaflet 地图加载失败"就把整个地图 section 删掉

本脚本一次性做三件事：
    1. 检测环境（Python / Node / npm / ffmpeg / cwebp / ImageMagick /
       edge-tts / python-pptx / Pillow / BeautifulSoup4 / requests 等）
    2. 缺什么自动装什么（优先 pip/brew/apt/winget；装不了给出一行修复命令）
    3. 发一份 "capability report"：告诉 AI 哪些层（L1/L2/L3/L5）可以做、
       哪些必须降级、哪些必须 hard fail

===========================================================================
退出码
===========================================================================
0  = 全部能力就位，AI 可以正常走完五层（L1→L5）
10 = 部分能力缺失但已自动安装，AI 可继续；报告写入 .teachany-preflight.json
20 = 核心能力缺失（Python < 3.8 / 连基础 pip 都不能用），AI 必须停止
30 = AI 可用的非交互工具（image_gen）探针失败——AI 必须停止并报告用户

===========================================================================
用法
===========================================================================
    python3 scripts/preflight-check.py              # 全量自检 + 自愈
    python3 scripts/preflight-check.py --dry-run    # 只检测，不安装
    python3 scripts/preflight-check.py --quick      # 跳过 Node/Remotion（纯 L1+L3 场景）
    python3 scripts/preflight-check.py --json       # 只输出 JSON 报告（AI 读取用）
    python3 scripts/preflight-check.py --require-image-gen   # 强制 AI 必须能生图

AI 调用约定（在 Phase 0 开头）：
    result = subprocess.run(
        ['python3', 'scripts/preflight-check.py', '--json'],
        capture_output=True, text=True,
    )
    capability = json.loads(result.stdout)
    if capability['exit_code'] in (20, 30):
        raise RuntimeError("工具链不就位，不能继续 Phase 1")
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ==========================================================
# 输出工具
# ==========================================================
USE_COLOR = sys.stdout.isatty() and os.environ.get('NO_COLOR', '') == ''

class C:
    if USE_COLOR:
        G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; B = "\033[94m"
        BOLD = "\033[1m"; DIM = "\033[2m"; END = "\033[0m"
    else:
        G = Y = R = B = BOLD = DIM = END = ""


def log(msg, level="info"):
    if ARGS.json_only:
        return
    prefix = {
        "info":  f"{C.B}ℹ️ {C.END}",
        "ok":    f"{C.G}✅{C.END}",
        "warn":  f"{C.Y}⚠️ {C.END}",
        "err":   f"{C.R}❌{C.END}",
        "head":  f"\n{C.BOLD}{C.B}━━━{C.END}",
    }[level]
    print(f"{prefix} {msg}", flush=True)


def head(msg):
    log(msg, "head")


# ==========================================================
# 工具函数
# ==========================================================
def which(cmd):
    return shutil.which(cmd)


def run(cmd, check=False, capture=True, timeout=120):
    try:
        result = subprocess.run(
            cmd, shell=isinstance(cmd, str),
            capture_output=capture, text=True,
            check=check, timeout=timeout,
        )
        return result
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        class R:
            returncode = 1
            stdout = getattr(e, 'stdout', '') or ''
            stderr = getattr(e, 'stderr', str(e)) or str(e)
        return R()


def detect_os():
    sys_name = platform.system()
    if sys_name == "Darwin":
        return "macos"
    if sys_name == "Linux":
        # 细分 debian/alpine/other
        if Path('/etc/debian_version').exists():
            return "debian"
        if Path('/etc/alpine-release').exists():
            return "alpine"
        return "linux"
    if sys_name == "Windows":
        return "windows"
    return "unknown"


def pip_install(pkg, upgrade=False):
    """尝试 pip install，成功返回 True"""
    cmd = [sys.executable, "-m", "pip", "install",
           "--user", "--quiet", "--disable-pip-version-check"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.append(pkg)
    r = run(cmd, timeout=180)
    return r.returncode == 0


def brew_install(pkg):
    if not which("brew"):
        return False
    r = run(["brew", "install", pkg], timeout=300)
    return r.returncode == 0


def apt_install(pkg):
    if not which("apt-get"):
        return False
    # 不交互
    env = os.environ.copy()
    env['DEBIAN_FRONTEND'] = 'noninteractive'
    r = subprocess.run(
        ["sudo", "-n", "apt-get", "install", "-y", pkg],
        env=env, capture_output=True, text=True, timeout=300,
    )
    return r.returncode == 0


def npm_global_install(pkg):
    if not which("npm"):
        return False
    r = run(["npm", "install", "-g", pkg], timeout=300)
    return r.returncode == 0


# ==========================================================
# 检测规则（每项都可自愈）
# ==========================================================
REPORT = {
    "version": "v5.34.11",
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "os": detect_os(),
    "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "checks": {},   # name -> {status, installed_now, version, hint}
    "capabilities": {
        "L1_html":       False,  # 基础 HTML 课件（总是 True）
        "L2_remotion":   False,  # Remotion mp4 教学动画
        "L3_tts":        False,  # edge-tts 语音（命令可用）
        "L3_tts_wss":    False,  # edge-tts wss 实际连通（v7.9.5 新增，区分"装好了"vs"能生成"）
        "L3_tts_engine": "none", # 实际可用引擎: edge-tts / macos-say / pyttsx3 / silent
        "L4_pack":       False,  # .teachany 打包
        "L5_pptx":       False,  # PPTX 导出
        "image_gen":     False,  # AI 生图（由上层 IDE 提供，探针校验）
        "webp_compress": False,  # cwebp 压图
        "map_rendering": False,  # Leaflet 地图基线（检查 CDN 可达）
    },
    "must_stop": False,          # True 时 AI 必须停止
    "must_stop_reason": "",
    "exit_code": 0,
}


def record(name, status, **kwargs):
    REPORT["checks"][name] = dict(status=status, **kwargs)


# ==========================================================
# 逐项检查
# ==========================================================
def check_python():
    head("Python 运行时")
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 8):
        log(f"Python {major}.{minor} 版本过低（需要 ≥ 3.8）", "err")
        record("python", "fail", version=f"{major}.{minor}",
               hint="升级 Python 到 3.8+（推荐 3.11）")
        REPORT["must_stop"] = True
        REPORT["must_stop_reason"] = "Python < 3.8"
        return False
    log(f"Python {major}.{minor}.{sys.version_info.micro} OK", "ok")
    record("python", "ok", version=f"{major}.{minor}.{sys.version_info.micro}")
    REPORT["capabilities"]["L1_html"] = True
    return True


def check_pip():
    head("pip 包管理器")
    r = run([sys.executable, "-m", "pip", "--version"])
    if r.returncode != 0:
        log("pip 不可用，AI 无法继续（缺 pip 装不了任何 Python 依赖）", "err")
        record("pip", "fail", hint="python3 -m ensurepip --upgrade")
        REPORT["must_stop"] = True
        REPORT["must_stop_reason"] = "pip 不可用"
        return False
    log("pip OK", "ok")
    record("pip", "ok", version=r.stdout.strip().split()[1] if r.stdout else "?")
    return True


def check_python_packages():
    head("Python 依赖包")
    required = {
        "requests":       ("requests",          "requests"),
        "Pillow":         ("PIL",               "Pillow"),
        "beautifulsoup4": ("bs4",               "beautifulsoup4"),
        "python-pptx":    ("pptx",              "python-pptx"),
        "edge-tts":       ("edge_tts",          "edge-tts"),
        "pyyaml":         ("yaml",              "pyyaml"),
    }
    for label, (import_name, pip_name) in required.items():
        try:
            __import__(import_name)
            log(f"{label} OK", "ok")
            record(f"pip:{label}", "ok")
        except ImportError:
            log(f"{label} 缺失，尝试 pip 自动安装...", "warn")
            if ARGS.dry_run:
                log(f"[dry-run] 跳过安装 {label}", "info")
                record(f"pip:{label}", "missing",
                       hint=f"pip install {pip_name}")
                continue
            if pip_install(pip_name):
                log(f"{label} 安装成功", "ok")
                record(f"pip:{label}", "installed_now",
                       hint=f"pip install {pip_name}")
            else:
                log(f"{label} 安装失败", "err")
                record(f"pip:{label}", "fail",
                       hint=f"pip install --user {pip_name} （请手动处理网络/权限）")


def check_edge_tts():
    """
    v7.9.5 增强：除了"命令是否可用"，还实测 wss 连通性。
    根因：Edge TTS 依赖的 wss://speech.platform.bing.com 在国内 443 端口
    经常被防火墙拦截，导致 edge-tts "成功"返回但写出 0 字节 mp3。
    """
    head("edge-tts（L3 语音基线）")
    cmd_available = False
    invocation = None

    if which("edge-tts"):
        r = run(["edge-tts", "--version"], timeout=30)
        log(f"edge-tts 命令可用（{r.stdout.strip()})", "ok")
        REPORT["capabilities"]["L3_tts"] = True
        record("edge-tts", "ok", version=r.stdout.strip())
        cmd_available = True
        invocation = "edge-tts"
    else:
        # 退而求其次，通过 python -m
        r = run([sys.executable, "-m", "edge_tts", "--version"], timeout=30)
        if r.returncode == 0:
            log(f"edge-tts 模块可用（python -m edge_tts）", "ok")
            REPORT["capabilities"]["L3_tts"] = True
            record("edge-tts", "ok", version="module mode", invocation="python -m edge_tts")
            cmd_available = True
            invocation = sys.executable + " -m edge_tts"

    if not cmd_available:
        # 都没有 → 安装
        if ARGS.dry_run:
            log("edge-tts 缺失（dry-run 跳过安装）", "warn")
            record("edge-tts", "missing", hint="pip install edge-tts")
            return False
        log("edge-tts 缺失，pip 自动安装...", "warn")
        if pip_install("edge-tts"):
            log("edge-tts 安装成功", "ok")
            REPORT["capabilities"]["L3_tts"] = True
            record("edge-tts", "installed_now", hint="pip install edge-tts")
            cmd_available = True
            invocation = "edge-tts"
        else:
            log("edge-tts 安装失败——L3 语音将降级为 macOS say / pyttsx3 / 静音占位", "err")
            record("edge-tts", "fail",
                   hint="pip install --user edge-tts；若仍失败检查网络/代理")

    # ============== v7.9.5 新增：wss 实测探针 ==============
    # 即便 edge-tts 命令可用，也要实测 wss 连通性
    # 失败时不阻断 L3，而是触发引擎回退
    log("正在探测 Edge-TTS wss 连通性（实测生成 1 秒探针）...", "info")
    try:
        # 调用 tts-engine.py 的 probe 模式
        tts_engine_script = SCRIPT_DIR / "tts-engine.py" if "SCRIPT_DIR" in globals() else None
        if tts_engine_script is None:
            tts_engine_script = Path(__file__).parent / "tts-engine.py"

        if tts_engine_script.exists():
            r = run([sys.executable, str(tts_engine_script), "--probe"], timeout=40)
            if r.returncode == 0:
                log("✅ wss 连通，将使用 edge-tts（最佳音质）", "ok")
                REPORT["capabilities"]["L3_tts_wss"] = True
                REPORT["capabilities"]["L3_tts_engine"] = "edge-tts"
                record("edge-tts-wss", "ok",
                       hint="wss://speech.platform.bing.com 实测可达")
            else:
                log("⚠️ wss 不通（防火墙拦截或网络问题），将自动回退引擎", "warn")
                REPORT["capabilities"]["L3_tts_wss"] = False
                # 探测可用的回退引擎
                fallback = _detect_tts_fallback()
                REPORT["capabilities"]["L3_tts_engine"] = fallback
                if fallback == "macos-say":
                    log("✅ macOS say 离线 TTS 可用，将作为 edge-tts 替代", "ok")
                elif fallback == "pyttsx3":
                    log("✅ pyttsx3 跨平台离线 TTS 可用", "ok")
                elif fallback == "silent":
                    log("⚠️ 无离线 TTS 引擎可用，将生成静音占位 mp3 +"
                        " 前端 teachany-tts-narrator.js 用 Web Speech 朗读", "warn")
                record("edge-tts-wss", "fail",
                       hint=f"wss 被防火墙/网络拦截，已切换到 {fallback} 引擎；"
                            f"用户如需 edge-tts 高质量音质，请配置 HTTPS_PROXY 重跑")
        else:
            log("tts-engine.py 不存在，跳过 wss 探针", "warn")
    except Exception as e:
        log(f"wss 探针执行异常：{e}", "warn")

    return cmd_available


def _detect_tts_fallback():
    """探测可用的离线 TTS 引擎，返回 'macos-say' / 'pyttsx3' / 'silent' / 'none'。"""
    # macOS say 优先（音质好且默认安装）
    if sys.platform == "darwin" and which("say") and which("ffmpeg"):
        return "macos-say"
    # pyttsx3 跨平台
    try:
        import pyttsx3  # noqa
        if which("ffmpeg"):
            return "pyttsx3"
    except ImportError:
        pass
    # 最后回退：能生成静音
    if which("ffmpeg"):
        return "silent"
    return "none"


def check_node_remotion():
    head("Node.js + Remotion（L2 视频基线）")
    if ARGS.quick:
        log("--quick 模式：跳过 Node/Remotion 检查", "warn")
        record("node", "skipped_quick")
        return False
    node = which("node")
    if not node:
        log("Node.js 未安装，L2 教学动画无法生成", "err")
        record("node", "missing",
               hint="安装 Node.js 20 LTS：访问 https://nodejs.org/ 或使用 nvm")
        _suggest_node_install()
        return False
    # 版本
    r = run(["node", "--version"], timeout=30)
    ver = r.stdout.strip().lstrip('v') if r.returncode == 0 else "?"
    major_ver = 0
    try:
        major_ver = int(ver.split('.')[0])
    except Exception:
        pass
    if major_ver < 18:
        log(f"Node.js {ver} 过低（Remotion 要求 ≥ 18）", "err")
        record("node", "fail", version=ver,
               hint="升级到 Node 20 LTS")
        return False
    log(f"Node.js v{ver} OK", "ok")
    record("node", "ok", version=ver)
    # ffmpeg（Remotion 渲染必需）
    if not which("ffmpeg"):
        log("ffmpeg 缺失（Remotion 渲染需要）", "warn")
        record("ffmpeg", "missing")
        if not ARGS.dry_run:
            _install_ffmpeg()
    else:
        log("ffmpeg OK", "ok")
        record("ffmpeg", "ok")
    # 中文字体（L2 字幕渲染必需，见硬规则 #27）
    _check_cjk_fonts()
    # 如果 ffmpeg 就位，宣布 L2 能力可用
    if which("ffmpeg") and major_ver >= 18:
        REPORT["capabilities"]["L2_remotion"] = True
    return True


def _suggest_node_install():
    os_name = REPORT["os"]
    hints = {
        "macos":  "brew install node@20 && brew link --overwrite node@20",
        "debian": "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs",
        "linux":  "使用 nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && nvm install 20",
        "windows": "winget install OpenJS.NodeJS.LTS",
    }
    hint = hints.get(os_name, "访问 https://nodejs.org/ 下载安装包")
    log(f"Node 安装建议：{hint}", "info")
    record("node_install_hint", "info", hint=hint)


def _install_ffmpeg():
    os_name = REPORT["os"]
    log("尝试自动安装 ffmpeg...", "info")
    if os_name == "macos" and brew_install("ffmpeg"):
        log("ffmpeg 安装成功", "ok")
        record("ffmpeg", "installed_now")
        return
    if os_name == "debian" and apt_install("ffmpeg"):
        log("ffmpeg 安装成功", "ok")
        record("ffmpeg", "installed_now")
        return
    log("ffmpeg 自动安装失败", "warn")
    record("ffmpeg", "fail",
           hint={
               "macos":  "brew install ffmpeg",
               "debian": "sudo apt install -y ffmpeg",
               "windows": "winget install Gyan.FFmpeg",
           }.get(os_name, "请参照 https://ffmpeg.org/download.html"))


def _check_cjk_fonts():
    # macOS 默认自带，Linux 需要 fonts-noto-cjk
    os_name = REPORT["os"]
    if os_name == "macos":
        log("macOS 自带 PingFang SC/Heiti SC，CJK 字体 OK", "ok")
        record("cjk_fonts", "ok")
        return
    if os_name == "debian":
        r = run("fc-list | grep -iE 'noto.*cjk|source.*han' | head -3")
        if r.stdout.strip():
            log("Noto CJK 字体已安装", "ok")
            record("cjk_fonts", "ok")
            return
        log("Noto CJK 字体缺失（L2 字幕将乱码），尝试 apt 安装...", "warn")
        if not ARGS.dry_run and apt_install("fonts-noto-cjk"):
            log("Noto CJK 安装成功", "ok")
            record("cjk_fonts", "installed_now")
            return
        record("cjk_fonts", "fail",
               hint="sudo apt install -y fonts-noto-cjk")
        return
    record("cjk_fonts", "unknown",
           hint="请确保系统有中文字体，否则 Remotion 视频会乱码")


def check_webp():
    head("cwebp（WebP 图片压缩）")
    if which("cwebp"):
        log("cwebp OK", "ok")
        record("cwebp", "ok")
        REPORT["capabilities"]["webp_compress"] = True
        return
    log("cwebp 缺失，尝试自动安装...", "warn")
    if ARGS.dry_run:
        record("cwebp", "missing", hint="brew install webp / apt install webp")
        return
    os_name = REPORT["os"]
    installed = False
    if os_name == "macos":
        installed = brew_install("webp")
    elif os_name == "debian":
        installed = apt_install("webp")
    if installed:
        log("cwebp 安装成功", "ok")
        record("cwebp", "installed_now")
        REPORT["capabilities"]["webp_compress"] = True
        return
    # 退路：Pillow 也能压 WebP，确认可用
    try:
        from PIL import Image
        log("cwebp 不可用，但 Pillow 能用作后备压缩（性能略差）", "warn")
        record("cwebp", "fallback_pillow")
        REPORT["capabilities"]["webp_compress"] = True
        return
    except Exception:
        log("cwebp + Pillow 都不可用，WebP 压缩将被禁用（课件 > 5MB 无法提交）", "err")
        record("cwebp", "fail",
               hint={
                   "macos":  "brew install webp",
                   "debian": "sudo apt install -y webp",
                   "windows": "winget install Google.WebP",
               }.get(os_name, "https://developers.google.com/speed/webp/download"))


def check_map_cdn():
    head("地图底图 CDN 连通性（Leaflet 基线）")
    # 硬规则 #35：必须使用 XYZ 瓦片；检测 CartoDB + ArcGIS + OpenStreetMap 可达性
    urls = {
        "cartodb-dark":     "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/0/0/0.png",
        "arcgis-hillshade": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/0/0/0",
        "jsdelivr":         "https://cdn.jsdelivr.net/gh/weponusa/teachany@main/README.md",
    }
    ok_count = 0
    for name, url in urls.items():
        try:
            import urllib.request
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "TeachAny-Preflight/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    log(f"{name}  200 OK", "ok")
                    record(f"cdn:{name}", "ok", url=url)
                    ok_count += 1
                else:
                    log(f"{name}  {resp.status}", "warn")
                    record(f"cdn:{name}", f"http_{resp.status}", url=url)
        except Exception as e:
            log(f"{name} 连通失败：{type(e).__name__}", "warn")
            record(f"cdn:{name}", "unreachable", url=url, error=str(e)[:100])
    if ok_count >= 2:
        REPORT["capabilities"]["map_rendering"] = True
        log(f"地图底图可用（{ok_count}/3 CDN 连通）", "ok")
    else:
        log(f"地图底图不可达（仅 {ok_count}/3 CDN 通），地理/历史课件需考虑用户 VPN 或切换镜像", "warn")


def check_image_gen():
    head("AI 生图（image_gen 工具）")
    # image_gen 是 IDE 侧工具，Python 脚本无法直接调用；
    # 我们用一个"配置文件"约定来强制 AI 自己填写探针结果
    probe_file = Path(".teachany-image-gen-probe.json")
    if probe_file.exists():
        try:
            probe = json.loads(probe_file.read_text())
            if probe.get("last_success_at"):
                age_hours = (time.time() - probe.get("last_success_unix", 0)) / 3600
                if age_hours < 24:
                    log(f"image_gen 探针 {age_hours:.1f}h 内最近一次成功", "ok")
                    record("image_gen", "ok", last_success=probe["last_success_at"])
                    REPORT["capabilities"]["image_gen"] = True
                    return
        except Exception:
            pass
    log("未找到有效的 image_gen 探针结果（24h 内）", "warn")
    log("AI 在 Phase 0.5 完成后必须：", "info")
    log("  1. 调用 image_gen 生成一张最小探针图（prompt='test pixel art 8x8'）", "info")
    log("  2. 确认返回路径存在且 size > 0", "info")
    log("  3. 写入 .teachany-image-gen-probe.json：", "info")
    log('     {"last_success_at":"YYYY-MM-DD...","last_success_unix":1234567890}', "info")
    log("  4. 如果 image_gen 调用失败 3 次——硬规则 #34 允许降级为占位符，但必须在 Gate 声明", "info")
    record("image_gen", "probe_required",
           hint="AI 必须在 Phase 0.5 后跑一次 image_gen 探针并写 .teachany-image-gen-probe.json")
    if ARGS.require_image_gen:
        REPORT["must_stop"] = True
        REPORT["must_stop_reason"] = "--require-image-gen 强制要求 image_gen 可用，但未检测到探针"


def check_git_hooks():
    head("Git hooks（禁直推护栏）")
    hook = Path(".git/hooks/pre-push")
    target = Path("scripts/pre-push.sh")
    if not target.exists():
        log("scripts/pre-push.sh 缺失", "warn")
        record("pre_push_hook", "missing")
        return
    if not hook.exists():
        log("pre-push hook 未安装，尝试自动安装...", "warn")
        if not ARGS.dry_run:
            os.makedirs(".git/hooks", exist_ok=True)
            try:
                os.symlink("../../scripts/pre-push.sh", hook)
                os.chmod(target, 0o755)
                log("pre-push hook 已安装", "ok")
                record("pre_push_hook", "installed_now")
                return
            except Exception as e:
                log(f"安装失败: {e}", "err")
                record("pre_push_hook", "fail", error=str(e))
                return
        record("pre_push_hook", "missing",
               hint="ln -sf ../../scripts/pre-push.sh .git/hooks/pre-push && chmod +x scripts/pre-push.sh")
        return
    if hook.is_symlink() and str(hook.resolve()).endswith("pre-push.sh"):
        log("pre-push hook OK", "ok")
        record("pre_push_hook", "ok")
    else:
        log("pre-push hook 存在但不是标准软链（可能被旧版覆盖）", "warn")
        record("pre_push_hook", "non_standard",
               hint="rm .git/hooks/pre-push && ln -sf ../../scripts/pre-push.sh .git/hooks/pre-push")


def check_l4_pack():
    head("L4 课件打包（pack-courseware.cjs）")
    pack = Path("scripts/pack-courseware.cjs")
    if pack.exists() and which("node"):
        log("L4 打包脚本 + Node 就位", "ok")
        record("l4_pack", "ok")
        REPORT["capabilities"]["L4_pack"] = True
    elif pack.exists():
        log("L4 打包脚本存在但 Node 缺失——用户课件不能打成 .teachany 包", "warn")
        record("l4_pack", "fail", hint="安装 Node.js")
    else:
        log("pack-courseware.cjs 缺失（仓库不完整？）", "warn")
        record("l4_pack", "missing")


def check_l5_pptx():
    head("L5 PPTX 导出")
    try:
        import pptx   # noqa: F401
        log("python-pptx OK（L5 PPTX 可导出）", "ok")
        record("l5_pptx", "ok")
        REPORT["capabilities"]["L5_pptx"] = True
    except ImportError:
        log("python-pptx 缺失，L5 PPTX 不可用（仅 output_formats 含 pptx 时影响）", "warn")
        record("l5_pptx", "missing", hint="pip install python-pptx")


# ==========================================================
# 主流程
# ==========================================================
def compute_exit_code():
    # 20 / 30 已在检测中直接设置 must_stop
    if REPORT["must_stop"]:
        if "image_gen" in REPORT["must_stop_reason"]:
            REPORT["exit_code"] = 30
        else:
            REPORT["exit_code"] = 20
        return

    # 是否有"安装过的新东西"
    installed_any = any(c.get("status") == "installed_now"
                        for c in REPORT["checks"].values())
    if installed_any:
        REPORT["exit_code"] = 10
    else:
        REPORT["exit_code"] = 0


def write_report():
    Path(".teachany-preflight.json").write_text(
        json.dumps(REPORT, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def human_summary():
    if ARGS.json_only:
        return
    head("工具链自检总结")
    caps = REPORT["capabilities"]
    rows = [
        ("L1 HTML 课件",     caps["L1_html"]),
        ("L2 Remotion 视频", caps["L2_remotion"]),
        ("L3 edge-tts 语音", caps["L3_tts"]),
        ("L4 课件打包",      caps["L4_pack"]),
        ("L5 PPTX 导出",     caps["L5_pptx"]),
        ("图片生成 image_gen", caps["image_gen"]),
        ("WebP 压缩",        caps["webp_compress"]),
        ("地图 CDN",         caps["map_rendering"]),
    ]
    for name, ok in rows:
        mark = f"{C.G}✓ 可用{C.END}" if ok else f"{C.Y}✗ 不可用/待 AI 探针{C.END}"
        print(f"  {name:<20s}  {mark}")
    print()
    if REPORT["must_stop"]:
        print(f"{C.R}{C.BOLD}🛑 AI 必须停止：{REPORT['must_stop_reason']}{C.END}")
    elif REPORT["exit_code"] == 10:
        print(f"{C.Y}{C.BOLD}⚠️  检测中已自动安装若干依赖，详情见 .teachany-preflight.json{C.END}")
    else:
        print(f"{C.G}{C.BOLD}🎉 全部就位，可以进入 Phase 1{C.END}")
    print()


def main():
    check_python()    # 硬闸门
    if REPORT["must_stop"]:
        compute_exit_code(); write_report(); return
    check_pip()
    if REPORT["must_stop"]:
        compute_exit_code(); write_report(); return

    check_python_packages()
    check_edge_tts()
    check_node_remotion()
    check_webp()
    check_l4_pack()
    check_l5_pptx()
    check_map_cdn()
    check_image_gen()
    check_git_hooks()

    compute_exit_code()
    write_report()
    human_summary()

    if ARGS.json_only:
        print(json.dumps(REPORT, ensure_ascii=False, indent=2))

    sys.exit(REPORT["exit_code"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TeachAny preflight tool check")
    parser.add_argument("--dry-run", action="store_true",
                        help="只检测，不安装任何依赖")
    parser.add_argument("--quick", action="store_true",
                        help="跳过 Node/Remotion 相关检查（纯 L1+L3 快速场景）")
    parser.add_argument("--json", dest="json_only", action="store_true",
                        help="只输出 JSON 报告到 stdout（AI 读取用）")
    parser.add_argument("--require-image-gen", action="store_true",
                        help="强制 image_gen 探针必须存在，否则 exit 30")
    ARGS = parser.parse_args()
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TME 音乐人平台登录（有头 Playwright 扫码/账号登录）

用法:
    python3 login.py                 # 有头 Chromium 打开登录页，等用户登录成功
    python3 login.py --headful       # 同上（显式）
    python3 login.py --timeout 300   # 自定义等待超时（秒），默认 300s

成功后落盘:
    ~/.tme-login/storage_state.json  —— Playwright 完整存档（含 cookies + localStorage）
~/.tme-login/token.json          —— tmeHeaderToken 快照，供本 skill 内部脚本直接读取

退出码:
    0 登录成功并落盘
    1 登录失败 / 超时 / Playwright 未安装
"""
import argparse
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

TARGET_URL = "https://y.tencentmusic.com"
TOKEN_KEY = "tmeHeaderToken"

CACHE_DIR = Path.home() / ".tme-login"
STATE_FILE = CACHE_DIR / "storage_state.json"
TOKEN_FILE = CACHE_DIR / "token.json"

# 默认 5 分钟，给用户足够时间完成扫码/输入密码/二次验证
DEFAULT_TIMEOUT_SEC = 300
# 检测到 token 后的"稳定等待"——避免登录过程中拿到中间态 token
STABLE_CHECK_INTERVAL_MS = 1500


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _auto_install_playwright() -> bool:
    """自动安装 Playwright 依赖（pip install playwright + playwright install chromium）

    返回 True 表示安装成功，False 表示安装失败。
    """
    _eprint("")
    _eprint("🔧 未检测到 Playwright，开始自动安装依赖...")
    _eprint(f"   解释器: {sys.executable}")

    # Step 1: pip install playwright
    _eprint("   ▶ Step 1/2: pip install playwright")
    try:
        ret = subprocess.run(
            [sys.executable, "-m", "pip", "install", "playwright"],
            check=False,
        )
        if ret.returncode != 0:
            _eprint("❌ pip install playwright 失败")
            _eprint("   请手动执行：")
            _eprint(f"   {sys.executable} -m pip install playwright")
            _eprint(f"   {sys.executable} -m playwright install chromium")
            return False
    except Exception as e:
        _eprint(f"❌ pip install playwright 异常: {e}")
        return False

    # Step 2: playwright install chromium
    _eprint("   ▶ Step 2/2: playwright install chromium（约 150MB，耐心等待）")
    try:
        ret = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False,
        )
        if ret.returncode != 0:
            _eprint("❌ playwright install chromium 失败")
            _eprint("   请手动执行：")
            _eprint(f"   {sys.executable} -m playwright install chromium")
            return False
    except Exception as e:
        _eprint(f"❌ playwright install chromium 异常: {e}")
        return False

    _eprint("✅ Playwright 依赖安装完成")
    return True


def _detect_screen_size(default_w: int = 1920, default_h: int = 1080) -> tuple:
    """检测主屏幕分辨率（像素），多级回退：
       1) macOS: 调 AppKit（若装了 pyobjc）
       2) 跨平台: tkinter（Python 标准库，大部分环境都带）
       3) 跨平台: screeninfo（若装了）
       4) 兜底: 默认 1920x1080
       返回 (width, height)
    """
    # 1) macOS 优先用 AppKit（最准，不会漏算 menu bar / dock）
    if sys.platform == "darwin":
        try:
            from AppKit import NSScreen  # type: ignore
            frame = NSScreen.mainScreen().frame()
            w = int(frame.size.width)
            h = int(frame.size.height)
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass

    # 2) 跨平台 tkinter
    try:
        import tkinter  # 标准库
        root = tkinter.Tk()
        root.withdraw()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass

    # 3) screeninfo（如果装了）
    try:
        from screeninfo import get_monitors  # type: ignore
        monitors = get_monitors()
        if monitors:
            m = monitors[0]
            if m.width > 0 and m.height > 0:
                return m.width, m.height
    except Exception:
        pass

    # 4) 兜底
    return default_w, default_h


def _ensure_playwright():
    """检测 Playwright 是否可用，缺依赖时自动安装（含 chromium），再次校验"""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError:
        pass

    # 自动安装
    if not _auto_install_playwright():
        _eprint("")
        _eprint("❌ 自动安装 Playwright 失败，请手动执行：")
        _eprint(f"   {sys.executable} -m pip install playwright")
        _eprint(f"   {sys.executable} -m playwright install chromium")
        _eprint("")
        return False

    # 重新尝试 import（清掉可能的负缓存）
    for mod_name in list(sys.modules.keys()):
        if mod_name == "playwright" or mod_name.startswith("playwright."):
            del sys.modules[mod_name]
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError as e:
        _eprint(f"❌ 安装后仍无法 import playwright: {e}")
        _eprint("   可能的原因：当前 Python 解释器与 pip 安装目标不一致")
        _eprint(f"   当前解释器: {sys.executable}")
        return False


def _save_cache(token: str, storage_state: dict) -> None:
    """把 storage_state + token 快照落盘，权限 0600"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. storage_state.json（Playwright 下次加载用）
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(storage_state, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(STATE_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass

    # 2. token.json（下游 skill 约定的读取位置）
    token_payload = {
        "token": token,
        "savedAt": int(time.time()),
        "baseUrl": TARGET_URL,
    }
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(token_payload, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass

    _eprint(f"💾 storage_state 已保存到 {STATE_FILE}")
    _eprint(f"💾 token.json    已保存到 {TOKEN_FILE}")


def _poll_token(page, timeout_sec: int) -> str:
    """在已打开的 page 上轮询 localStorage.tmeHeaderToken，直到拿到稳定值或超时"""
    deadline = time.time() + timeout_sec
    last_tick = 0

    while time.time() < deadline:
        try:
            token = page.evaluate(
                f"() => window.localStorage.getItem('{TOKEN_KEY}')"
            )
        except Exception:
            # 页面可能正在跳转，稍等
            token = None

        if token and isinstance(token, str) and token.strip():
            token = token.strip()
            # 简单稳定性确认：等 1.5s 再读一次，若一致即稳定
            page.wait_for_timeout(STABLE_CHECK_INTERVAL_MS)
            try:
                token2 = page.evaluate(
                    f"() => window.localStorage.getItem('{TOKEN_KEY}')"
                )
            except Exception:
                token2 = None
            if token2 and token2.strip() == token:
                return token
            # 不稳定则继续等

        # 每 10s 提示一次剩余时间
        remaining = int(deadline - time.time())
        if remaining > 0 and remaining // 10 != last_tick // 10:
            _eprint(f"   ⏳ 等待登录中，剩余 {remaining}s（请在浏览器完成扫码/登录）")
        last_tick = remaining

        page.wait_for_timeout(1000)

    return ""


def run_login(timeout_sec: int) -> int:
    if not _ensure_playwright():
        return 1

    from playwright.sync_api import sync_playwright

    _eprint("🔑 正在启动 Chromium（有头模式）...")
    _eprint(f"   目标页面: {TARGET_URL}")
    _eprint(f"   超时时间: {timeout_sec}s")
    _eprint("   请在弹出的浏览器窗口中完成扫码或账号登录")
    _eprint("")

    # 如果之前已有 storage_state，加载一下作为起点（用户可能只是刷新登录态）
    state_kwarg = {}
    if STATE_FILE.exists():
        try:
            state_kwarg["storage_state"] = str(STATE_FILE)
            _eprint(f"ℹ️ 已加载现有 storage_state 作为起点: {STATE_FILE}")
        except Exception:
            state_kwarg = {}

    # 动态获取屏幕分辨率，用于显式指定 Chromium 窗口尺寸
    # macOS 上 --start-maximized 常被忽略，必须用 --window-size 显式指定
    screen_w, screen_h = _detect_screen_size()
    _eprint(f"🖥  检测到屏幕尺寸: {screen_w}x{screen_h}，将以此尺寸打开窗口")

    with sync_playwright() as p:
        # --no-sandbox: 兼容部分容器/CI 环境
        # --start-maximized: Linux/Windows 下启动即最大化（macOS 会忽略，需配合 window-size）
        # --window-position=0,0 + --window-size=W,H: 显式把窗口固定到全屏尺寸，兼容 macOS
        # --force-device-scale-factor=1: 强制页面缩放为 100%，避免高 DPI 屏显示比例异常
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--start-maximized",
                "--window-position=0,0",
                f"--window-size={screen_w},{screen_h}",
                "--force-device-scale-factor=1",
            ],
        )
        try:
            # no_viewport=True: 让页面视口跟随窗口实际大小，而不是默认的 1280x720
            # 否则即便窗口最大化，页面内容仍会被强制缩放到 1280x720
            context = browser.new_context(no_viewport=True, **state_kwarg)
            page = context.new_page()

            # 通过 CDP 主动把窗口 bounds 设为整个屏幕，兜底 macOS 下 args 不生效的情况
            try:
                cdp = context.new_cdp_session(page)
                window_info = cdp.send("Browser.getWindowForTarget")
                cdp.send("Browser.setWindowBounds", {
                    "windowId": window_info["windowId"],
                    "bounds": {
                        "left": 0,
                        "top": 0,
                        "width": screen_w,
                        "height": screen_h,
                        "windowState": "normal",
                    },
                })
            except Exception as e:
                _eprint(f"ℹ️ CDP 设置窗口尺寸失败（忽略，窗口可能已最大化）: {e}")

            try:
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30_000)
            except Exception as e:
                _eprint(f"⚠️ 页面加载异常（继续等待）: {e}")

            token = _poll_token(page, timeout_sec)

            if not token:
                _eprint("")
                _eprint(f"⏱ 已超过 {timeout_sec}s 仍未检测到 tmeHeaderToken")
                _eprint("   请确认：")
                _eprint("   1) 是否在弹出的浏览器中完成了登录")
                _eprint("   2) 登录后页面是否跳到了 y.tencentmusic.com 域下")
                _eprint("   3) 可以尝试在 Console 执行 localStorage.getItem('tmeHeaderToken') 验证")
                return 1

            _eprint("")
            _eprint(f"✅ 登录成功，已捕获 tmeHeaderToken（长度 {len(token)}）")

            # 导出 storage_state
            storage_state = context.storage_state()
            _save_cache(token, storage_state)

            # stdout 输出纯 token，方便 shell 捕获: TOKEN=$(python3 login.py)
            print(token)
            return 0
        finally:
            try:
                browser.close()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="TME 音乐人平台登录（有头 Playwright 扫码/账号登录）"
    )
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT_SEC,
        help=f"等待登录超时（秒），默认 {DEFAULT_TIMEOUT_SEC}"
    )
    parser.add_argument(
        "--headful", action="store_true",
        help="有头模式（默认即为有头，此参数仅作显式声明）"
    )
    args = parser.parse_args()

    return run_login(args.timeout)


if __name__ == "__main__":
    sys.exit(main())

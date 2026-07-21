#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Playwright storage_state 中读取 tmeHeaderToken（跨平台）

设计说明：
  本脚本不再依赖用户真实浏览器（AppleScript / LevelDB 都已移除），
  而是通过 Playwright 无头 Chromium 加载 ~/.tme-login/storage_state.json，
  访问 y.tencentmusic.com，读取 localStorage 中的 tmeHeaderToken。

  storage_state.json 由 login.py 生成，tmeHeaderToken 生命周期约 30 天，
  过期或首次使用时，需要用户先跑 `python3 login.py` 做一次扫码登录。

输出协议（stdout）：
  - 成功：一行 JSON
      {"status":"ok","token":"xxx","browser":"playwright"}
  - 失败：一行 JSON
      {"status":"error","errorCode":"NO_STATE|PLAYWRIGHT_MISSING|NO_TOKEN_KEY|UNKNOWN",
       "errorMsg":"...", "browser":"playwright|null",
       "hint":"人类可读的提示"}

退出码：
  - 成功：0
  - 失败：1
"""
import json
import os
import subprocess
import sys
from pathlib import Path

TARGET_URL = "https://y.tencentmusic.com"
TOKEN_KEY = "tmeHeaderToken"

CACHE_DIR = Path.home() / ".tme-login"
STATE_FILE = CACHE_DIR / "storage_state.json"

# Playwright 内部操作超时（毫秒）
PAGE_LOAD_TIMEOUT_MS = 20_000


def _build_result(**kwargs) -> dict:
    return kwargs


def _err(code: str, msg: str, hint: str) -> dict:
    return {
        "status": "error",
        "browser": "playwright",
        "errorCode": code,
        "errorMsg": msg,
        "hint": hint,
    }


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _auto_install_playwright() -> bool:
    """自动安装 Playwright 依赖（pip install playwright + playwright install chromium）

    注意：本脚本的 stdout 是严格的协议 JSON，不能被污染，
    因此子进程的 stdout 必须重定向到 stderr。
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
            stdout=sys.stderr,  # 避免污染本脚本 stdout
            stderr=sys.stderr,
        )
        if ret.returncode != 0:
            _eprint("❌ pip install playwright 失败")
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
            stdout=sys.stderr,
            stderr=sys.stderr,
        )
        if ret.returncode != 0:
            _eprint("❌ playwright install chromium 失败")
            return False
    except Exception as e:
        _eprint(f"❌ playwright install chromium 异常: {e}")
        return False

    _eprint("✅ Playwright 依赖安装完成")
    return True


def _try_import_playwright() -> bool:
    """尝试 import playwright，不可用时自动安装后再试一次"""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError:
        pass

    if not _auto_install_playwright():
        return False

    # 清理可能的负缓存后重试
    for mod_name in list(sys.modules.keys()):
        if mod_name == "playwright" or mod_name.startswith("playwright."):
            del sys.modules[mod_name]
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError as e:
        _eprint(f"❌ 安装后仍无法 import playwright: {e}")
        _eprint(f"   当前解释器: {sys.executable}")
        return False


def get_token_via_playwright() -> dict:
    # 1. storage_state.json 是否存在
    if not STATE_FILE.exists():
        return _err(
            "NO_STATE",
            f"storage_state.json not found at {STATE_FILE}",
            "请先执行扫码登录：python3 scripts/login.py",
        )

    # 2. Playwright 依赖（缺失则自动安装）
    if not _try_import_playwright():
        return {
            "status": "error",
            "browser": None,
            "errorCode": "PLAYWRIGHT_MISSING",
            "errorMsg": "Playwright is not installed and auto-install failed",
            "hint": f"请手动执行：{sys.executable} -m pip install playwright && {sys.executable} -m playwright install chromium",
        }

    from playwright.sync_api import sync_playwright

    # 3. 无头 Chromium + 加载 state + 读 localStorage
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                context = browser.new_context(storage_state=str(STATE_FILE))
                page = context.new_page()
                try:
                    page.goto(
                        TARGET_URL,
                        wait_until="domcontentloaded",
                        timeout=PAGE_LOAD_TIMEOUT_MS,
                    )
                except Exception as e:
                    # 页面加载异常时仍然尝试读取 localStorage
                    # （domcontentloaded 未触发不代表 storage 读不到）
                    pass

                try:
                    token = page.evaluate(
                        f"() => window.localStorage.getItem('{TOKEN_KEY}')"
                    )
                except Exception as e:
                    return _err(
                        "UNKNOWN",
                        f"evaluate failed: {e}",
                        "Playwright 执行 JS 失败，请重试或重新登录",
                    )

                if not token or not isinstance(token, str) or not token.strip():
                    return _err(
                        "NO_TOKEN_KEY",
                        "localStorage.tmeHeaderToken is empty",
                        "storage_state 已失效或登录态已过期，请重新执行：python3 scripts/login.py",
                    )

                return {
                    "status": "ok",
                    "token": token.strip(),
                    "browser": "playwright",
                }
            finally:
                try:
                    browser.close()
                except Exception:
                    pass
    except Exception as e:
        return _err(
            "UNKNOWN",
            f"playwright runtime error: {e}",
            "Playwright 运行失败，请确认 chromium 已安装：playwright install chromium",
        )


def main():
    result = get_token_via_playwright()
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("status") == "ok" else 1)


if __name__ == "__main__":
    main()

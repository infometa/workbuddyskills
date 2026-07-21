#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查登录态并获取 Token（基于 Playwright storage_state）

用法:
    python3 check_login.py             # 默认流程：缓存 → 无头刷新 → 引导登录
    python3 check_login.py --no-login  # 只尝试缓存和无头读取，失败直接退出（不触发有头登录）
    python3 check_login.py --manual    # 直接手动粘贴 Token

流程（token 有效期约 30 天，首次登录后长期无感）：
    1. 读取本地 token.json，非空即复用（秒级返回）
    2. 缓存为空 / 调用方强制刷新 → 用 Playwright 无头 + storage_state 刷新一次 token
    3. storage_state 不存在或已失效 → 自动调起 login.py 做一次有头扫码登录
    4. 以上全部失败 → 提示手动粘贴兜底

输出:
    成功: stdout 输出 Token 本体（单行），exit 0
    失败: exit 1
    所有提示走 stderr，方便 shell 捕获: TOKEN=$(python3 check_login.py)
"""
import argparse
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

CACHE_DIR = Path.home() / ".tme-login"
TOKEN_CACHE_FILE = CACHE_DIR / "token.json"
STATE_FILE = CACHE_DIR / "storage_state.json"

TARGET_URL = "https://y.tencentmusic.com"


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# ---- 本地缓存读写 ----

def load_token_from_cache() -> str:
    try:
        if not TOKEN_CACHE_FILE.exists():
            return ""
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("token") or "").strip()
    except Exception:
        return ""


def save_token_to_cache(token: str) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "token": token,
            "savedAt": int(time.time()),
            "baseUrl": TARGET_URL,
        }
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(TOKEN_CACHE_FILE, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
        _eprint(f"💾 Token 已保存到 {TOKEN_CACHE_FILE}")
    except Exception as e:
        _eprint(f"⚠️ 保存 Token 到本地失败: {e}")


def emit_token(token: str, source: str) -> bool:
    """把 token 输出到 stdout 并写缓存。空 token 返回 False。"""
    if not token or not token.strip():
        return False
    token = token.strip()
    _eprint(f"✅ 已采用 Token（来源：{source}）")
    save_token_to_cache(token)
    print(token)
    return True


# ---- 子脚本调用 ----

def get_token_via_state() -> dict:
    """调用 get_token_from_browser.py（无头 Playwright + storage_state）"""
    py_script = SCRIPT_DIR / "get_token_from_browser.py"
    try:
        result = subprocess.run(
            [sys.executable, str(py_script)],
            capture_output=True, text=True, timeout=60
        )
        out = (result.stdout or "").strip()
        if not out:
            return {"status": "error", "errorCode": "UNKNOWN",
                    "errorMsg": "get_token_from_browser.py no output",
                    "hint": "子脚本无输出"}
        last_line = out.splitlines()[-1].strip()
        try:
            return json.loads(last_line)
        except Exception:
            return {"status": "error", "errorCode": "UNKNOWN",
                    "errorMsg": f"unparsable output: {last_line[:200]}",
                    "hint": "子脚本输出格式异常"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "errorCode": "UNKNOWN",
                "errorMsg": "subprocess timeout",
                "hint": "Playwright 无头读取超时"}
    except Exception as e:
        return {"status": "error", "errorCode": "UNKNOWN",
                "errorMsg": str(e), "hint": "子脚本调用失败"}


def run_interactive_login(timeout: int = 300) -> str:
    """调用 login.py（有头 Playwright 扫码登录），返回 token，失败返回空串"""
    py_script = SCRIPT_DIR / "login.py"
    _eprint("")
    _eprint("🧭 即将打开浏览器完成登录（有头 Chromium）...")
    try:
        # 登录脚本涉及用户交互，不捕获 stderr，让其直接打印
        # stdout 保留以便拿到 token
        result = subprocess.run(
            [sys.executable, str(py_script), "--timeout", str(timeout)],
            capture_output=True, text=True, timeout=timeout + 60
        )
        # login.py 的 stderr 仍然透传给用户看
        if result.stderr:
            sys.stderr.write(result.stderr)
            sys.stderr.flush()
        if result.returncode == 0:
            return (result.stdout or "").strip().splitlines()[-1].strip() if result.stdout else ""
        return ""
    except subprocess.TimeoutExpired:
        _eprint("❌ 登录流程超时")
        return ""
    except Exception as e:
        _eprint(f"❌ 调用 login.py 失败: {e}")
        return ""


# ---- 错误提示 ----

def print_error_guidance(err: dict) -> None:
    code = err.get("errorCode", "UNKNOWN")
    hint = err.get("hint", "")
    msg = err.get("errorMsg", "")
    _eprint("")
    _eprint("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    _eprint(f"❌ Playwright 读取 Token 失败（errorCode={code}）")
    if hint:
        _eprint(f"💡 {hint}")
    if msg:
        _eprint(f"ℹ️ 原始错误: {msg}")
    _eprint("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def prompt_manual_paste() -> str:
    _eprint("")
    _eprint("🧭 手动兜底流程：")
    _eprint("   1) 在浏览器打开 https://y.tencentmusic.com 并完成登录")
    _eprint("   2) 按 F12 / ⌥⌘I 打开开发者工具，切到 Console 面板")
    _eprint("   3) 执行：localStorage.getItem('tmeHeaderToken')")
    _eprint("   4) 复制输出字符串（不含引号）")

    if not sys.stdin.isatty():
        _eprint("")
        _eprint("⚠️ 当前非交互式终端，无法接收粘贴输入。")
        _eprint("   请在终端直接运行：")
        _eprint(f"   python3 {Path(__file__).resolve()} --manual")
        return ""

    _eprint("")
    try:
        print("请将 Token 粘贴到此处并回车（留空则取消）: ",
              end="", file=sys.stderr, flush=True)
        token = sys.stdin.readline().strip()
        if (token.startswith('"') and token.endswith('"')) or \
           (token.startswith("'") and token.endswith("'")):
            token = token[1:-1]
        return token
    except (EOFError, KeyboardInterrupt):
        return ""


# ---- 主流程 ----

def manual_paste_flow() -> int:
    token = prompt_manual_paste()
    if emit_token(token, "手动粘贴"):
        return 0
    _eprint("❌ 手动粘贴的 Token 无效或为空")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="TME 音乐人平台登录态获取")
    parser.add_argument("--no-login", action="store_true",
                        help="只尝试缓存与无头读取，不触发有头登录")
    parser.add_argument("--manual", action="store_true",
                        help="直接走手动粘贴流程")
    parser.add_argument("--force", action="store_true",
                        help="忽略本地 token.json 缓存，强制刷新")
    args = parser.parse_args()

    # --manual 快速通道
    if args.manual:
        return manual_paste_flow()

    # Step 1: 本地 token.json 缓存
    if not args.force:
        cached = load_token_from_cache()
        if cached:
            _eprint("🔍 发现本地缓存 Token，直接复用")
            if emit_token(cached, "本地缓存"):
                return 0
            _eprint("⚠️ 本地缓存 Token 为空，继续刷新")
        else:
            _eprint(f"🔍 未发现本地缓存 Token（{TOKEN_CACHE_FILE}）")
    else:
        _eprint("🔄 --force 指定，跳过本地缓存")

    # Step 2: Playwright 无头 + storage_state 刷新
    if STATE_FILE.exists():
        _eprint("🔄 尝试用 storage_state 无头刷新 Token...")
        result = get_token_via_state()
        if result.get("status") == "ok":
            if emit_token(result.get("token", ""), "playwright-state"):
                return 0
        else:
            print_error_guidance(result)
            # NO_STATE / NO_TOKEN_KEY 说明登录态失效，继续走 login.py
            # PLAYWRIGHT_MISSING 则无法恢复，直接进入手动粘贴
            if result.get("errorCode") == "PLAYWRIGHT_MISSING":
                return manual_paste_flow()
    else:
        _eprint(f"🔍 未发现 storage_state（{STATE_FILE}），需要先登录一次")

    # --no-login: 到此为止，不触发有头登录
    if args.no_login:
        _eprint("ℹ️ --no-login 指定，跳过有头登录，直接走手动粘贴兜底")
        return manual_paste_flow()

    # Step 3: 调用 login.py 引导用户扫码登录
    token = run_interactive_login()
    if emit_token(token, "playwright-login"):
        return 0

    # Step 4: 最后兜底 —— 手动粘贴
    _eprint("")
    _eprint("⚠️ 有头登录未拿到 Token，进入手动粘贴兜底")
    return manual_paste_flow()


if __name__ == "__main__":
    sys.exit(main())
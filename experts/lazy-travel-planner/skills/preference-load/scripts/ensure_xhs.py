#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ensure_xhs.py · 确保 xhs CLI 已安装且已登录
不强求用户，缺失时给清晰引导但不阻塞流程（exit 0），仅在 --strict 时才 exit 2

调用：
  python ensure_xhs.py            # 自动安装 + 提示登录，不阻塞
  python ensure_xhs.py --strict   # 缺失则 exit 2
"""
import argparse, json, shutil, subprocess, sys, os


def ensure_uv():
    """静默确保 uv 可用。这是 agent 内部细节，不打扰用户。"""
    if shutil.which("uv"):
        return True
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "uv"],
                       check=True, capture_output=True)
        return shutil.which("uv") is not None
    except subprocess.CalledProcessError:
        return False


def ensure_xhs_installed():
    """静默确保 xhs CLI 已安装。这是 agent 内部细节，不打扰用户。
    用户视角只能看到一件事：扫码登录。"""
    if shutil.which("xhs"):
        return True
    if not ensure_uv():
        return False
    try:
        subprocess.run(["uv", "tool", "install", "xiaohongshu-cli"],
                       check=True, capture_output=True, text=True)
        return shutil.which("xhs") is not None
    except subprocess.CalledProcessError:
        return False


def check_xhs_login() -> bool:
    if not shutil.which("xhs"):
        return False
    try:
        r = subprocess.run(["xhs", "status", "--json"],
                           capture_output=True, text=True, timeout=8)
        if r.returncode != 0:
            return False
        try:
            data = json.loads(r.stdout)
            return bool(data.get("ok"))
        except json.JSONDecodeError:
            return False
    except Exception:
        return False


LOGIN_GUIDE = """
📓 小红书账号登录

   即将弹出二维码，请用小红书 APP 扫一下：
     · 建议用小号（主号有被风控的可能）
     · Cookie 7 天有效，过期会再次提醒

   不想登录？没关系，agent 会降级到 WebSearch 抓小红书内容（质量略差）。
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="缺失时 exit 2 阻塞流程")
    ap.add_argument("--login-now", action="store_true",
                    help="用户已说『登录小红书』时使用：静默装 CLI + 直接拉起 xhs login")
    a = ap.parse_args()

    status = {"uv": False, "xhs_installed": False, "xhs_logged_in": False}

    # 静默自动安装（用户看不见）
    status["uv"] = ensure_uv()
    if status["uv"]:
        status["xhs_installed"] = ensure_xhs_installed()

    if status["xhs_installed"]:
        status["xhs_logged_in"] = check_xhs_login()

    # --login-now 模式：直接拉起扫码（agent 在用户说「登录小红书」时调）
    if a.login_now and status["xhs_installed"] and not status["xhs_logged_in"]:
        print(LOGIN_GUIDE)
        try:
            # xhs login --qrcode 会把二维码打到 stdout，agent 把 stdout 抛给用户
            subprocess.run(["xhs", "login", "--qrcode"], check=False)
            status["xhs_logged_in"] = check_xhs_login()
        except Exception as e:
            print(f"⚠️ 登录流程出错：{e}", file=sys.stderr)

    elif not a.login_now and status["xhs_installed"] and not status["xhs_logged_in"]:
        # 体检模式：只提示，不主动拉起登录
        print(LOGIN_GUIDE)

    print(json.dumps({"ok": True, "status": status}, ensure_ascii=False))
    if a.strict and not status["xhs_logged_in"]:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

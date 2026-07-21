#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 环境自检脚本

用途：
- 在 agent 调用本 skill 的 Python 脚本前，快速检查当前 Python 是否可用
- 给出明确的升级/安装引导，避免模型直接运行脚本后报错

用法：
    python scripts/check_python_env.py
    python scripts/check_python_env.py --require trag mcp
    python scripts/check_python_env.py --mcp --json
"""

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Dict, List, Any

MIN_VERSION = (3, 10)
MAX_EXCLUSIVE = (3, 14)
DEFAULT_REQUIRED = []
MCP_REQUIRED = ["trag", "mcp"]


def version_tuple_to_str(v):
    return ".".join(str(x) for x in v)


def is_version_ok(info):
    return info["major"] == 3 and MIN_VERSION <= (info["major"], info["minor"]) < MAX_EXCLUSIVE


def get_python_info() -> Dict[str, Any]:
    vi = sys.version_info
    return {
        "executable": sys.executable,
        "version": platform.python_version(),
        "major": vi.major,
        "minor": vi.minor,
        "micro": vi.micro,
        "ok": vi.major == 3 and MIN_VERSION <= (vi.major, vi.minor) < MAX_EXCLUSIVE,
        "required": f">={version_tuple_to_str(MIN_VERSION)}, <{version_tuple_to_str(MAX_EXCLUSIVE)}",
    }


def check_pip() -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        return {
            "ok": proc.returncode == 0,
            "version": proc.stdout.strip() if proc.returncode == 0 else "",
            "error": proc.stderr.strip() if proc.returncode != 0 else "",
        }
    except Exception as e:
        return {"ok": False, "version": "", "error": str(e)}


def check_modules(modules: List[str]) -> Dict[str, Any]:
    out = {}
    for name in modules:
        spec = importlib.util.find_spec(name)
        out[name] = {"ok": spec is not None}
    return out


def find_candidate_python() -> List[Dict[str, Any]]:
    candidates = []
    names = ["python3.11", "python3.10", "python3.12", "python3.13", "python3", "python"]
    seen = set()
    for name in names:
        path = shutil.which(name)
        if not path or path in seen:
            continue
        seen.add(path)
        try:
            proc = subprocess.run(
                [path, "-c", "import sys, platform; print(platform.python_version()); print(sys.executable)"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                lines = proc.stdout.strip().splitlines()
                version = lines[0] if lines else "unknown"
                exe = lines[1] if len(lines) > 1 else path
                parts = version.split(".")
                major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
                minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                candidates.append({
                    "command": name,
                    "path": exe,
                    "version": version,
                    "ok": major == 3 and MIN_VERSION <= (major, minor) < MAX_EXCLUSIVE,
                })
        except Exception:
            pass
    return candidates


def install_hint() -> Dict[str, List[str]]:
    return {
        "windows": [
            "建议安装 Python 3.11（64-bit）：https://www.python.org/downloads/release/python-3119/",
            "安装时务必勾选 'Add python.exe to PATH'",
            "安装后重新打开 WorkBuddy/终端，再运行：python --version",
            "如果 python 指向旧版本，可尝试：py -3.11 --version",
        ],
        "macos": [
            "推荐：brew install python@3.11",
            "安装后运行：python3.11 --version",
        ],
        "linux": [
            "Ubuntu/Debian：sudo apt install python3.11 python3.11-venv python3-pip",
            "Fedora：sudo dnf install python3.11 python3-pip",
        ],
        "skill_setup": [
            "普通外部用户不需要安装 MCP；通用流程动态查询官网公告，个人流程信息引导 join.qq.com 校招官网 offer 鹅智能体",
            "普通脚本如 fetch_recruit_info.py / fetch_recruit_jds.py / resume_checker.py 只要求 Python 3.10+",
            "仅受控内测调试可选 JD MCP 时，依次运行：python scripts/check_python_env.py --mcp --json → bash scripts/install_mcp.sh → python scripts/check_mcp_registration.py",
            "如国产模型看不到 MCP 工具，岗位/JD 请优先使用 fetch_recruit_jds.py 官网脚本兜底",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="检查当前 Python 环境是否满足腾讯校招 skill 的脚本运行要求")
    parser.add_argument("--require", nargs="*", default=DEFAULT_REQUIRED, help="额外检查的 Python 模块，如 trag mcp")
    parser.add_argument("--mcp", action="store_true", help="按可选 JD MCP 要求检查 trag+mcp")
    parser.add_argument("--json", action="store_true", help="只输出 JSON，便于 agent 解析")
    args = parser.parse_args()

    required = MCP_REQUIRED if args.mcp else args.require
    py = get_python_info()
    pip = check_pip()
    modules = check_modules(required)
    candidates = find_candidate_python()

    missing = [name for name, result in modules.items() if not result["ok"]]
    ok = py["ok"] and pip["ok"] and not missing

    result = {
        "success": ok,
        "python": py,
        "pip": pip,
        "modules": modules,
        "missing_modules": missing,
        "candidate_pythons": candidates,
        "message": "Python 环境满足要求" if ok else "Python 环境不满足要求，请按 hints 更新后重试",
        "hints": install_hint(),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not ok:
            print("\n[给同学的简短提示]")
            print("当前 Python 环境可能不足，建议先更新到 Python 3.10~3.13（推荐 3.11）后再继续。")
            print("普通外部用户不需要安装 MCP；通用流程动态查询官网公告，个人流程信息引导 join.qq.com 校招官网 offer 鹅智能体。")
            print("如需受控内测调试可选 JD MCP，请运行：bash scripts/install_mcp.sh，再用 python scripts/check_mcp_registration.py 检查。")
            print("Windows 用户安装 Python 时请勾选 Add python.exe to PATH，安装后重启 WorkBuddy。")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy 可选 JD MCP 注册自检脚本。

只检查本地 MCP 配置是否包含可选 JD MCP 服务，不读取或输出任何 Key。
通用流程/制度类问题不依赖 MCP，优先运行 `scripts/fetch_recruit_info.py flow` 动态查询官网公告；个人流程信息引导 join.qq.com 校招官网 offer 鹅智能体。
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

REQUIRED_SERVERS = {
    "campus-recruit-jd-qa": "可选在招岗位 JD 知识库",
}


def _default_config_path() -> Path:
    return Path.home() / ".codebuddy" / "mcp.json"


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def _check_server(name: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(cfg, dict):
        return {
            "registered": False,
            "ok": False,
            "message": "配置不是对象",
        }

    command = cfg.get("command")
    args = cfg.get("args") or []
    script_path = ""
    if isinstance(args, list) and args:
        script_path = str(args[-1])

    script_exists = bool(script_path and Path(script_path).exists())
    ok = bool(command and isinstance(args, list) and args and script_exists)

    return {
        "registered": True,
        "ok": ok,
        "command_present": bool(command),
        "args_present": isinstance(args, list) and bool(args),
        "script_path": script_path,
        "script_exists": script_exists,
        "message": "注册正常" if ok else "已注册但启动脚本或参数可能异常",
    }


def main() -> int:
    config_path = Path(os.getenv("WORKBUDDY_MCP_CONFIG", str(_default_config_path()))).expanduser()
    result: Dict[str, Any] = {
        "success": False,
        "config_path": str(config_path),
        "config_exists": config_path.exists(),
        "servers": {},
        "missing_servers": [],
        "next_steps": [],
    }

    if not config_path.exists():
        result["next_steps"] = [
            "未找到 MCP 配置文件，请在 skill 根目录运行：bash scripts/install_mcp.sh",
            "安装完成后完全退出并重启 WorkBuddy",
            "如当前模型不支持 MCP，岗位/JD 请优先使用 scripts/fetch_recruit_jds.py 官网脚本兜底",
        ]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    config = _load_json(config_path)
    mcp_servers = config.get("mcpServers") if isinstance(config, dict) else None
    if not isinstance(mcp_servers, dict):
        result["next_steps"] = [
            "mcp.json 中没有 mcpServers 对象，请重新运行：bash scripts/install_mcp.sh",
            "安装完成后完全退出并重启 WorkBuddy",
        ]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    missing = []
    all_ok = True
    for server_name in REQUIRED_SERVERS:
        if server_name not in mcp_servers:
            missing.append(server_name)
            result["servers"][server_name] = {
                "registered": False,
                "ok": False,
                "message": "未注册",
            }
            all_ok = False
        else:
            check = _check_server(server_name, mcp_servers[server_name])
            result["servers"][server_name] = check
            all_ok = all_ok and bool(check.get("ok"))

    result["missing_servers"] = missing
    result["success"] = all_ok

    if all_ok:
        result["next_steps"] = [
            "MCP 注册看起来正常，请完全退出并重启 WorkBuddy",
            "重启后问：技术方向有哪些岗位？用于验证可选 JD MCP",
            "流程/制度类问题不验证 MCP；通用流程动态查询官网公告，个人流程信息引导 join.qq.com 校招官网 offer 鹅智能体",
        ]
    else:
        result["next_steps"] = [
            "请在 skill 根目录重新运行：bash scripts/install_mcp.sh",
            "确认安装过程没有报错，并完全退出重启 WorkBuddy",
            "如果使用的国产模型仍看不到 MCP 工具，请优先使用 scripts/fetch_recruit_jds.py 官网脚本兜底",
        ]

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

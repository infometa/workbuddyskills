#!/usr/bin/env python3
"""
金数据 MCP Skill 安装辅助脚本

这是一个 MCP 类型的 Skill —— 实际能力由远端 MCP Server 提供，
无需在本地安装任何 Python / Node 依赖。

脚本作用：
1. 把 API Key / Secret 编码成 Basic 凭证
2. 打印 / 生成 MCP 连接配置片段，方便粘贴到 AI 客户端

用法：
    python3 setup.py                               # 打印配置说明
    python3 setup.py --encode [KEY SECRET]         # 把 Key/Secret 编成 Basic 凭证（参数可省，回退环境变量）
    python3 setup.py --print-json [KEY SECRET]     # 输出含 Authorization 头的 mcp.json
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys

MCP_NAME = "jinshuju"
MCP_URL = "https://jinshuju.net/mcp"

# 凭据可通过命令行参数或环境变量提供；推荐环境变量方式，避免 secret 进入 shell 历史
ENV_KEY = "JINSHUJU_API_KEY"
ENV_SECRET = "JINSHUJU_API_SECRET"


def resolve_credentials(cli_key: str | None, cli_secret: str | None) -> tuple[str | None, str | None]:
    """优先用命令行参数，缺省回退环境变量。"""
    key = cli_key or os.environ.get(ENV_KEY)
    secret = cli_secret or os.environ.get(ENV_SECRET)
    return key, secret


def encode_basic(api_key: str, api_secret: str) -> str:
    """把 API Key + Secret 拼成 `key:secret` 并 Base64 编码。"""
    raw = f"{api_key}:{api_secret}".encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def build_snippet(credentials: str = "BASE64_ENCODED_CREDENTIALS") -> dict:
    return {
        "mcpServers": {
            MCP_NAME: {
                "url": MCP_URL,
                "headers": {
                    "Authorization": f"Basic {credentials}",
                },
            }
        }
    }


def print_banner() -> None:
    print("=" * 60)
    print("  金数据 MCP Skill · 安装辅助")
    print("=" * 60)


def print_setup_instructions() -> None:
    print_banner()
    print()
    print(f"MCP 地址：{MCP_URL}")
    print()
    print("金数据 MCP 支持两种认证方式，由用户自行选择：")
    print()
    print("─" * 60)
    print(" 方式 A · HTTP Basic（API Key/Secret）")
    print("─" * 60)
    print()
    print("第 1 步：登录金数据后台 →「个人设置 → API / 开发者」，")
    print("         创建并复制 API Key / API Secret。")
    print()
    print("第 2 步：生成 Basic 凭证（推荐环境变量方式，避免凭据进入 shell 历史）：")
    print(f"         export {ENV_KEY}=YOUR_API_KEY")
    print(f"         export {ENV_SECRET}=YOUR_API_SECRET")
    print("         python3 setup.py --encode            # 自动从环境变量读取")
    print("         python3 setup.py --print-json         # 输出可直接粘贴的 mcp.json")
    print()
    print("         （也可直接传参 `python3 setup.py --encode KEY SECRET`，但 secret 会进入 shell 历史；")
    print('         或用 shell：echo -n "YOUR_API_KEY:YOUR_API_SECRET" | base64）')
    print()
    print("第 3 步：在 AI 客户端（Claude Desktop / Cursor / WorkBuddy 等）中添加 MCP 连接器。")
    print()
    print(f"  名称       ：{MCP_NAME}")
    print(f"  地址 (URL) ：{MCP_URL}")
    print(f"  请求头     ：Authorization: Basic BASE64_ENCODED_CREDENTIALS")
    print()
    print("或把以下片段粘贴到客户端的 MCP 配置：")
    print()
    print(json.dumps(build_snippet(), indent=2, ensure_ascii=False))
    print()
    print("─" * 60)
    print(" 方式 B · OAuth 2.0")
    print("─" * 60)
    print()
    print("  1. 打开 AI 客户端的连接器 / Connectors 管理入口")
    print("  2. 选择「添加连接器 (Add custom connector)」")
    print(f"  3. Name = {MCP_NAME}，URL = {MCP_URL}")
    print("  4. 点击 Add，弹出金数据登录页，登录并点「允许」")
    print("  5. 连接器状态变成 ✅ 即完成，无需手动生成凭证")
    print()
    print("─" * 60)
    print()
    print("添加完成后，在对话里发送 '列一下我金数据里的表单' 即可验证。")
    print()
    print("其它命令：")
    print("  python3 setup.py --encode [KEY SECRET]     # 生成 Basic 凭证（参数可省，回退环境变量）")
    print("  python3 setup.py --print-json [KEY SECRET] # 生成可直接粘贴的 mcp.json")


def cmd_encode(api_key: str, api_secret: str) -> int:
    credentials = encode_basic(api_key, api_secret)
    print(credentials)
    return 0


def cmd_print_json(api_key: str | None, api_secret: str | None) -> int:
    if api_key and api_secret:
        credentials = encode_basic(api_key, api_secret)
    else:
        credentials = "BASE64_ENCODED_CREDENTIALS"
    print(json.dumps(build_snippet(credentials), indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="金数据 MCP Skill 安装辅助")
    parser.add_argument("--encode", nargs="*", metavar=("KEY", "SECRET"),
                        help="把 API Key / Secret 编码成 Basic 凭证并输出；"
                             "可省略参数，改由环境变量 " + ENV_KEY + "/" + ENV_SECRET + " 提供（推荐，避免凭据进入 shell 历史）")
    parser.add_argument("--print-json", nargs="*", metavar=("KEY", "SECRET"),
                        help="输出含 Authorization 头的 mcp.json 片段；"
                             "不带参数时优先读环境变量，仍无则保留占位符")
    args = parser.parse_args()

    if args.encode is not None:
        if len(args.encode) == 2:
            cli_key, cli_secret = args.encode
        elif len(args.encode) == 0:
            cli_key, cli_secret = None, None
        else:
            print("--encode 需要 0 个或 2 个参数（KEY SECRET），或省略以从环境变量读取",
                  file=sys.stderr)
            return 2
        key, secret = resolve_credentials(cli_key, cli_secret)
        if not key or not secret:
            print(f"未提供 API Key/Secret：请通过命令行参数或环境变量 "
                  f"{ENV_KEY}/{ENV_SECRET} 提供", file=sys.stderr)
            return 2
        return cmd_encode(key, secret)

    if args.print_json is not None:
        if len(args.print_json) == 2:
            cli_key, cli_secret = args.print_json
        elif len(args.print_json) == 0:
            cli_key, cli_secret = None, None
        else:
            print("--print-json 需要 0 个或 2 个参数（KEY SECRET），或省略以从环境变量读取",
                  file=sys.stderr)
            return 2
        key, secret = resolve_credentials(cli_key, cli_secret)
        return cmd_print_json(key, secret)

    print_setup_instructions()
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""NeoData 金融数据查询客户端（通过代理 API）

Usage:
    python query.py --query "腾讯最新财报"
    python query.py --query "贵州茅台股价" --data-type api
    python query.py --save-token "<token>"

鉴权优先级: --token 参数 > ~/.workbuddy/.neodata_token 缓存文件（12 小时有效期）

环境变量 (可选):
    NEODATA_ENDPOINT - 代理 URL (可选，默认 https://copilot.tencent.com/agenttool/v1/neodata)
"""

import argparse
import json
import os
import stat
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests", file=sys.stderr)
    sys.exit(1)

DEFAULT_ENDPOINT = "https://copilot.tencent.com/agenttool/v1/neodata"
TOKEN_FILE = Path.home() / ".workbuddy" / ".neodata_token"
TOKEN_TTL_SECONDS = 12 * 3600  # 12 小时


def _read_token_file() -> Optional[str]:
    """从缓存文件读取 token，超过 12 小时返回 None"""
    try:
        raw = TOKEN_FILE.read_text().strip()
        if not raw:
            return None

        # 新格式: JSON {"token": "...", "saved_at": 1234567890}
        try:
            data = json.loads(raw)
            saved_at = data.get("saved_at", 0)
            token = data.get("token", "")
            if not token:
                return None
            # 检查是否过期
            if time.time() - saved_at > TOKEN_TTL_SECONDS:
                print("Token 缓存已过期（超过 12 小时），需要重新获取", file=sys.stderr)
                return None
            return token
        except (json.JSONDecodeError, TypeError):
            # 兼容旧格式: 纯文本 token（无时间戳，视为已过期）
            print("Token 缓存为旧格式（无时间戳），需要重新获取", file=sys.stderr)
            return None

    except (FileNotFoundError, PermissionError):
        return None


def _save_token_file(token: str) -> None:
    """将 token 和时间戳写入缓存文件（权限 600）"""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "token": token.strip(),
        "saved_at": int(time.time()),
    }
    TOKEN_FILE.write_text(json.dumps(data))
    TOKEN_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def query_neodata(
    query: str,
    data_type: str = "all",
    token: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> dict:
    url = endpoint or os.getenv("NEODATA_ENDPOINT", DEFAULT_ENDPOINT)
    jwt_token = token or _read_token_file()
    if not jwt_token:
        print("错误: 未找到有效 token。请先运行 --save-token 保存，或使用 --token 参数传入", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}",
    }

    # channel 和 sub_channel 为固定字段，必须显式传入
    payload: dict = {
        "query": query,
        "channel": "neodata",
        "sub_channel": "workbuddy",
    }
    if data_type != "all":
        payload["data_type"] = data_type

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="NeoData 金融数据查询")
    parser.add_argument("--query", "-q", default=None, help="自然语言查询")
    parser.add_argument("--token", "-t", default=None, help="Token（优先级高于缓存文件）")
    parser.add_argument("--data-type", "-d", default="all", choices=["all", "api", "doc"], help="数据类型 (默认: all)")
    parser.add_argument("--save-token", default=None, metavar="TOKEN", help="将 token 保存到缓存文件（12 小时有效期）")

    args = parser.parse_args()

    # --save-token 模式：保存后退出
    if args.save_token:
        _save_token_file(args.save_token)
        print(f"Token 已保存到 {TOKEN_FILE}（有效期 12 小时）")
        return

    if not args.query:
        parser.error("--query 或 --save-token 必须提供其一")

    try:
        result = query_neodata(
            query=args.query,
            data_type=args.data_type,
            token=args.token,
        )
    except requests.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

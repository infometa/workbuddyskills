#!/usr/bin/env python3
"""NeoData 金融数据查询客户端（通过代理 API）

Usage:
    python query.py --query "腾讯最新财报"
    python query.py --query "贵州茅台股价" --data-type api
    python query.py --save-token "<credential>"

凭证优先级: --token 参数 > ~/.workbuddy/.neodata_token 缓存文件（12 小时有效期）

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
AUTH_ERROR_KEYWORDS = ("token", "认证", "鉴权", "凭证", "unauthorized", "forbidden")


def _read_token_file() -> Optional[str]:
    """从缓存文件读取凭证；不可用时输出稳定的 TOKEN_* 标记。"""
    try:
        raw = TOKEN_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        print("TOKEN_MISSING: 未找到本地缓存凭证，需要获取凭证", file=sys.stderr)
        return None
    except PermissionError:
        print("TOKEN_MISSING: 无法读取本地缓存凭证，需要获取凭证", file=sys.stderr)
        return None

    if not raw:
        print("TOKEN_MISSING: 本地缓存凭证为空，需要获取凭证", file=sys.stderr)
        return None

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # 兼容旧格式：纯文本凭证无时间戳，视为过期，避免长期复用未知有效期凭证。
        print("TOKEN_EXPIRED: 本地缓存为旧格式或格式异常，需要重新获取凭证", file=sys.stderr)
        return None

    saved_at = data.get("saved_at", 0)
    credential = data.get("token", "")
    if not credential:
        print("TOKEN_MISSING: 本地缓存缺少凭证内容，需要获取凭证", file=sys.stderr)
        return None

    if time.time() - saved_at > TOKEN_TTL_SECONDS:
        print("TOKEN_EXPIRED: 本地缓存凭证已超过 12 小时，需要重新获取凭证", file=sys.stderr)
        return None

    return credential


def _save_token_file(credential: str) -> None:
    """将凭证和时间戳写入缓存文件（权限 600）。"""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "token": credential.strip(),
        "saved_at": int(time.time()),
    }
    TOKEN_FILE.write_text(json.dumps(data), encoding="utf-8")
    TOKEN_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _looks_like_auth_error(result: dict) -> bool:
    code = str(result.get("code", ""))
    msg = str(result.get("msg", "")).lower()
    return code == "40101" or any(keyword in msg for keyword in AUTH_ERROR_KEYWORDS)


def query_neodata(
    query: str,
    data_type: str = "all",
    token: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> dict:
    url = endpoint or os.getenv("NEODATA_ENDPOINT", DEFAULT_ENDPOINT)
    credential = token or _read_token_file()
    if not credential:
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {credential}",
    }

    # channel 和 sub_channel 为固定字段，必须显式传入。
    payload: dict = {
        "query": query,
        "channel": "neodata",
        "sub_channel": "workbuddy",
    }
    if data_type != "all":
        payload["data_type"] = data_type

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code in (401, 403):
        print(f"AUTH_ERROR: HTTP {resp.status_code}，凭证已失效或无权限", file=sys.stderr)
        sys.exit(2)

    resp.raise_for_status()
    result = resp.json()
    if _looks_like_auth_error(result):
        print("AUTH_ERROR: 服务返回鉴权错误，需要重新获取凭证", file=sys.stderr)
        sys.exit(2)

    return result


def main():
    parser = argparse.ArgumentParser(description="NeoData 金融数据查询")
    parser.add_argument("--query", "-q", default=None, help="自然语言查询")
    parser.add_argument("--token", "-t", default=None, help="凭证（优先级高于缓存文件）")
    parser.add_argument("--data-type", "-d", default="all", choices=["all", "api", "doc"], help="数据类型 (默认: all)")
    parser.add_argument("--save-token", default=None, metavar="CREDENTIAL", help="将凭证保存到缓存文件（12 小时有效期）")

    args = parser.parse_args()

    # --save-token 模式：保存后退出。
    if args.save_token:
        _save_token_file(args.save_token)
        print(f"凭证已保存到 {TOKEN_FILE}（有效期 12 小时）")
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
        print(f"REQUEST_FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"RESPONSE_PARSE_FAILED: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

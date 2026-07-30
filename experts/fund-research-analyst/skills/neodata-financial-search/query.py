#!/usr/bin/env python3
"""NeoData 金融数据查询客户端

Usage:
    python query.py --query "腾讯最新财报"
    python query.py --query "贵州茅台股价" --data-type api
    python query.py --query "黄金价格" --sub-channel my_channel
"""

import argparse
import json
import os
import sys
import uuid

try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests", file=sys.stderr)
    sys.exit(1)

PROXY_PORT = os.getenv("AUTH_GATEWAY_PORT", "19000")
BASE_URL = f"http://localhost:{PROXY_PORT}/proxy/api"
REMOTE_URL = "https://jprx.m.qq.com/aizone/skillserver/v1/proxy/teamrouter_neodata/query"


def query_neodata(
    query: str,
    sub_channel: str = "qclaw",
    data_type: str = "all",
    request_id: str | None = None,
) -> dict:
    url = BASE_URL
    headers = {
        "Content-Type": "application/json",
        "Remote-URL": REMOTE_URL,
    }
    payload = {
        "channel": "neodata",
        "sub_channel": sub_channel,
        "query": query,
        "request_id": request_id or uuid.uuid4().hex,
        "data_type": data_type,
        "se_params": {},
        "extra_params": {},
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="NeoData 金融数据查询")
    parser.add_argument("--query", "-q", required=True, help="自然语言查询")
    parser.add_argument("--sub-channel", "-s", default=os.getenv("NEODATA_SUB_CHANNEL", "qclaw"), help="子渠道 (默认: qclaw)")
    parser.add_argument("--data-type", "-d", default="all", choices=["all", "api", "doc"], help="数据类型")
    parser.add_argument("--request-id", default=None, help="请求ID (默认自动生成)")

    args = parser.parse_args()

    try:
        result = query_neodata(
            query=args.query,
            sub_channel=args.sub_channel,
            data_type=args.data_type,
            request_id=args.request_id,
        )
    except requests.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

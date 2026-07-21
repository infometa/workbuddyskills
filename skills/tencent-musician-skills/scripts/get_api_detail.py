#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取 API 详情
用法: python get_api_detail.py <api_name>
示例: python get_api_detail.py 37109cb7626e421a8329a5333ee05249
"""
import sys
import os
import json
import urllib.request

# 让脚本在任意 CWD 下都能找到同级的 _token.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _token import get_tme_header_token  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <api_name (operatorCode)>", file=sys.stderr)
        sys.exit(1)

    api_name = sys.argv[1]
    base_url = "https://y.tencentmusic.com/openapi"

    # 认证 Token：env → ~/.tme-login/token.json → 调起本 skill 的 check_login.py
    try:
        tme_header_token = get_tme_header_token()
    except RuntimeError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url}/musician/agent/operator/getApiDetail"
    payload = json.dumps({"name": api_name}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("tme-header-token", tme_header_token)

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(json.dumps(result, indent=4, ensure_ascii=False))
    except urllib.error.HTTPError as e:
        print(f"HTTP 错误 {e.code}: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

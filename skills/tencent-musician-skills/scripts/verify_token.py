#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 tme-header-token 是否有效（跨平台）
用法: python verify_token.py <token>
返回: 成功输出用户信息 JSON，失败返回 exit code 1
"""
import sys
import os
import json
import urllib.request


def main():
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <tme-header-token>", file=sys.stderr)
        sys.exit(1)

    token = sys.argv[1]
    base_url = os.environ.get("MUSICIAN_BASE_URL", "https://y.tencentmusic.com")

    url = f"{base_url}/v2/v2/account/userInfo"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Content-Type", "application/json")
    req.add_header("tme-header-token", token)

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # 判断是否有有效的用户信息
        if data.get("ret") == 0 or data.get("code") == 0 or data.get("success") is True:
            print("✅ Token 有效")
            print(json.dumps(data, indent=4, ensure_ascii=False))
            sys.exit(0)
        else:
            print("❌ Token 无效或已过期")
            sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"❌ Token 验证失败，HTTP 错误 {e.code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Token 验证请求失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

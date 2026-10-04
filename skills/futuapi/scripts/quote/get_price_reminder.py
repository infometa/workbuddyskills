#!/usr/bin/env python3
"""
获取到价提醒列表

功能：获取已设置的到价提醒列表
用法：python get_price_reminder.py
      python get_price_reminder.py HK.00700

接口限制：
- 每 30 秒内最多请求 60 次
"""
import argparse
import json
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_quote_context,
    check_ret,
    safe_close,
    is_empty,
    df_to_records,
)


def get_price_reminder(code=None, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        kwargs = {}
        if code:
            kwargs["code"] = code

        ret, data = ctx.get_price_reminder(**kwargs)
        check_ret(ret, data, ctx, "获取到价提醒")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无到价提醒")
            return

        if output_json:
            print(json.dumps({"data": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print("到价提醒列表")
            print("=" * 70)
            print(data.to_string(index=False))
            print("=" * 70)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取到价提醒列表")
    parser.add_argument("code", nargs="?", default=None, help="股票代码（可选），不填返回全部")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_price_reminder(args.code, args.output_json)

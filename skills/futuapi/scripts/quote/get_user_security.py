#!/usr/bin/env python3
"""
获取自选股列表

功能：获取指定分组的自选股列表
用法：python get_user_security.py "我的自选"

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


def get_user_security(group_name, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_user_security(group_name)
        check_ret(ret, data, ctx, "获取自选股列表")

        if is_empty(data):
            if output_json:
                print(json.dumps({"group_name": group_name, "data": []}))
            else:
                print(f"分组 \"{group_name}\" 无自选股")
            return

        if output_json:
            print(json.dumps({"group_name": group_name, "data": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"自选股列表 - {group_name}")
            print("=" * 70)
            cols = [c for c in ['code', 'name', 'lot_size', 'stock_type'] if c in data.columns]
            print(data[cols].to_string(index=False))
            print(f"\n共 {len(data)} 只")
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
    parser = argparse.ArgumentParser(description="获取自选股列表")
    parser.add_argument("group_name", help="自选股分组名称")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_user_security(args.group_name, args.output_json)

#!/usr/bin/env python3
"""
查询订阅状态

功能：查询当前已订阅的股票和数据类型
用法：python query_subscription.py

接口限制：
- 无特殊限频
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
)


def query_subscription(is_all_conn=True, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.query_subscription(is_all_conn=is_all_conn)
        check_ret(ret, data, ctx, "查询订阅")

        # data 结构: {"total_used": int, "remain": int, "own_used": int, "sub_list": {SubType: [code_list]}}
        total_used = data.get("total_used", 0) if isinstance(data, dict) else 0
        remain = data.get("remain", 0) if isinstance(data, dict) else 0
        own_used = data.get("own_used", 0) if isinstance(data, dict) else 0
        sub_list = data.get("sub_list", {}) if isinstance(data, dict) else {}

        sub_result = {}
        if isinstance(sub_list, dict):
            for k, v in sub_list.items():
                key = str(k).split(".")[-1] if hasattr(k, "name") else str(k)
                sub_result[key] = v if isinstance(v, list) else [v]

        if output_json:
            print(json.dumps({
                "total_used": total_used,
                "remain": remain,
                "own_used": own_used,
                "subscriptions": sub_result,
            }, ensure_ascii=False))
        else:
            print("=" * 50)
            print("订阅状态" + (" (所有连接)" if is_all_conn else " (当前连接)"))
            print("=" * 50)
            print(f"  已用额度: {total_used}  剩余: {remain}  当前连接已用: {own_used}")
            if sub_result:
                for k, codes in sub_result.items():
                    print(f"\n  {k}:")
                    for code in codes:
                        print(f"    - {code}")
            else:
                print("\n  暂无订阅")
            print("\n" + "=" * 50)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="查询订阅状态")
    parser.add_argument("--current", action="store_true", help="只查询当前连接的订阅（默认查询所有连接）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    query_subscription(is_all_conn=not args.current, output_json=args.output_json)

#!/usr/bin/env python3
"""
获取经纪队列

功能：获取股票的经纪买卖队列数据
用法：python get_broker_queue.py HK.00700

接口限制：
- 需先订阅 BROKER 类型
- 仅港股支持经纪队列
- 需要 LV2 行情权限
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
    SubType,
)


def get_broker_queue(code, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, msg = ctx.subscribe([code], [SubType.BROKER])
        check_ret(ret, msg, ctx, "订阅经纪队列")

        ret, bid_data, ask_data = ctx.get_broker_queue(code)
        check_ret(ret, bid_data, ctx, "获取经纪队列")

        if output_json:
            print(json.dumps({
                "code": code,
                "bid_broker": df_to_records(bid_data),
                "ask_broker": df_to_records(ask_data),
            }, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"经纪队列 - {code}")
            print("=" * 70)
            print("\n买方经纪:")
            if is_empty(bid_data):
                print("  无数据")
            else:
                print(bid_data.to_string(index=False))
            print("\n卖方经纪:")
            if is_empty(ask_data):
                print("  无数据")
            else:
                print(ask_data.to_string(index=False))
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
    parser = argparse.ArgumentParser(description="获取经纪队列（需 LV2 权限）")
    parser.add_argument("code", help="股票代码，如 HK.00700")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_broker_queue(args.code, args.output_json)

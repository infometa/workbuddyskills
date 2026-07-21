#!/usr/bin/env python3
"""
获取 IPO 列表

功能：获取指定市场的 IPO 信息列表
用法：python get_ipo_list.py HK

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
    Market,
)


def get_ipo_list(market_str, output_json=False):
    ctx = None
    try:
        market_map = {
            "HK": Market.HK,
            "US": Market.US,
            "SH": Market.SH,
            "SZ": Market.SZ,
        }
        market = market_map.get(market_str.upper())
        if market is None:
            raise ValueError(f"不支持的市场: {market_str}，可选: {list(market_map.keys())}")

        ctx = create_quote_context()
        ret, data = ctx.get_ipo_list(market)
        check_ret(ret, data, ctx, "获取 IPO 列表")

        if is_empty(data):
            if output_json:
                print(json.dumps({"market": market_str, "data": []}))
            else:
                print("无 IPO 数据")
            return

        if output_json:
            print(json.dumps({"market": market_str, "data": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"IPO 列表 - {market_str}")
            print("=" * 70)
            print(data.to_string(index=False))
            print(f"\n共 {len(data)} 条记录")
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
    parser = argparse.ArgumentParser(description="获取 IPO 列表")
    parser.add_argument("market", choices=["HK", "US", "SH", "SZ"], help="市场")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_ipo_list(args.market, args.output_json)

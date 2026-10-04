#!/usr/bin/env python3
"""
获取交易日历

功能：获取指定市场的交易日列表
用法：python get_trading_days.py US --start 2024-01-01 --end 2024-01-31

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
    TradeDateMarket,
    Market,
)


def get_trading_days(market_str, start=None, end=None, output_json=False):
    ctx = None
    try:
        # TradeDateMarket 枚举: NONE, HK, US, CN, NT, ST, JP_FUTURE, SG_FUTURE
        # 注意: 没有 SH/SZ，A 股统一用 CN
        if TradeDateMarket is not None:
            market_map = {
                "HK": TradeDateMarket.HK,
                "US": TradeDateMarket.US,
                "CN": TradeDateMarket.CN,
                "NT": TradeDateMarket.NT,
                "ST": TradeDateMarket.ST,
            }
            for name in ["JP_FUTURE", "SG_FUTURE"]:
                if hasattr(TradeDateMarket, name):
                    market_map[name] = getattr(TradeDateMarket, name)
        else:
            market_map = {
                "HK": Market.HK,
                "US": Market.US,
            }
        market = market_map.get(market_str.upper())
        if market is None:
            raise ValueError(f"不支持的市场: {market_str}，可选: {list(market_map.keys())}")

        ctx = create_quote_context()
        kwargs = {"market": market}
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end

        ret, data = ctx.request_trading_days(**kwargs)
        check_ret(ret, data, ctx, "获取交易日历")

        if is_empty(data):
            if output_json:
                print(json.dumps({"market": market_str, "data": []}))
            else:
                print("无交易日数据")
            return

        if output_json:
            # data 可能是 list 或 DataFrame
            if hasattr(data, 'iloc'):
                records = df_to_records(data)
            else:
                records = [str(d) for d in data]
            print(json.dumps({"market": market_str, "data": records}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"交易日历 - {market_str}")
            print("=" * 70)
            if hasattr(data, 'to_string'):
                print(data.to_string(index=False))
            else:
                for d in data:
                    print(f"  {d}")
            print(f"\n共 {len(data)} 个交易日")
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
    parser = argparse.ArgumentParser(description="获取交易日历")
    parser.add_argument("market", choices=["HK", "US", "CN", "NT", "ST", "JP_FUTURE", "SG_FUTURE"], help="市场（HK/US/CN/NT深沪股通/ST港股通）")
    parser.add_argument("--start", default=None, help="起始日期 yyyy-MM-dd")
    parser.add_argument("--end", default=None, help="结束日期 yyyy-MM-dd")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_trading_days(args.market, start=args.start, end=args.end, output_json=args.output_json)

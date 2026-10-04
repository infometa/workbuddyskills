#!/usr/bin/env python3
"""
获取实时报价

功能：获取已订阅股票的实时报价数据
用法：python get_stock_quote.py HK.00700 US.AAPL

接口限制：
- 需先通过 subscribe 接口订阅 QUOTE 类型
- 订阅后内置 3 秒等待逻辑，超过 3 秒返回空数据

返回字段说明：
- last_price: 最新价
- open_price/high_price/low_price/prev_close_price: 开高低昨收
- volume: 成交量
- turnover: 成交额
- amplitude: 振幅（百分比，20 实际对应 20%）
- turnover_rate: 换手率（百分比）
- suspension: True 表示停牌
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


def get_stock_quote(codes, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, msg = ctx.subscribe(codes, [SubType.QUOTE])
        check_ret(ret, msg, ctx, "订阅报价")

        ret, data = ctx.get_stock_quote(codes)
        check_ret(ret, data, ctx, "获取实时报价")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无数据")
            return

        if output_json:
            print(json.dumps({"data": df_to_records(data)}, ensure_ascii=False))
        else:
            cols = [c for c in ['code', 'name', 'last_price', 'open_price', 'high_price',
                                'low_price', 'volume', 'turnover'] if c in data.columns]
            print("=" * 70)
            print("实时报价")
            print("=" * 70)
            print(data[cols].to_string(index=False))
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
    parser = argparse.ArgumentParser(description="获取实时报价（需先订阅）")
    parser.add_argument("codes", nargs="+", help="股票代码，如 HK.00700")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_stock_quote(args.codes, args.output_json)

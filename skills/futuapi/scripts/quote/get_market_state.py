#!/usr/bin/env python3
"""
获取市场状态

功能：查询指定股票所属市场的交易状态（开盘/收盘/盘前盘后等）
用法：python get_market_state.py HK.00700 US.AAPL

接口限制：
- 每 30 秒内最多请求 10 次
- 每次股票代码上限 400 个
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
    safe_get,
    format_enum,
)


def get_market_state(codes, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_market_state(codes)
        check_ret(ret, data, ctx, "获取市场状态")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无数据")
            return

        records = []
        for i in range(len(data)):
            row = data.iloc[i] if hasattr(data, "iloc") else data[i]
            records.append({
                "code": safe_get(row, "code", default="N/A"),
                "stock_name": safe_get(row, "stock_name", default=""),
                "market_state": format_enum(safe_get(row, "market_state", default="")),
            })

        if output_json:
            print(json.dumps({"data": records}, ensure_ascii=False))
        else:
            print("=" * 50)
            print("市场状态")
            print("=" * 50)
            for r in records:
                print(f"  {r['code']:<15} {r['stock_name']:<10} 状态: {r['market_state']}")
            print("=" * 50)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取市场状态")
    parser.add_argument("codes", nargs="+", help="股票代码，如 HK.00700 US.AAPL")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_market_state(args.codes, args.output_json)

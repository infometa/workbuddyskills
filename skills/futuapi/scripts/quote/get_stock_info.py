#!/usr/bin/env python3
"""
获取股票基本信息

功能：获取指定股票的基本信息（名称、每手数量、证券类型、上市日期等）
用法：python get_stock_info.py US.AAPL,HK.00700

接口限制：
- 每 30 秒内最多请求 10 次
- 每次最多返回 200 个

参数说明：
- code_list: 若传入股票列表只返回指定股票信息，不传返回所有

返回字段说明：
- listing_date: 此字段停止维护
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
    safe_float,
    safe_int,
    format_enum,
    df_to_records,
)


def get_stock_info(codes_str, output_json=False):
    codes = [c.strip() for c in codes_str.split(",") if c.strip()]
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_market_snapshot(codes)
        check_ret(ret, data, ctx, "获取股票信息")

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
                "code": safe_get(row, "code", default=""),
                "name": safe_get(row, "name", default=""),
                "lot_size": safe_int(safe_get(row, "lot_size", default=0)),
                "stock_type": format_enum(safe_get(row, "stock_type", "sec_type", default="")),
                "listing_date": safe_get(row, "listing_date", default=""),
                "last_price": safe_float(safe_get(row, "last_price", default=0)),
                "market_val": safe_float(safe_get(row, "market_val", default=0)),
            })

        if output_json:
            print(json.dumps({"data": records}, ensure_ascii=False))
        else:
            print("=" * 70)
            print("股票基本信息")
            print("=" * 70)
            for r in records:
                print(f"\n  {r['code']}  {r['name']}")
                print(f"    每手: {r['lot_size']}  类型: {r['stock_type']}  上市日: {r['listing_date']}")
                print(f"    最新价: {r['last_price']}  市值: {r['market_val']}")
            print("\n" + "=" * 70)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取股票基本信息")
    parser.add_argument("codes", help="股票代码（逗号分隔），如 US.AAPL,HK.00700")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_stock_info(args.codes, args.output_json)

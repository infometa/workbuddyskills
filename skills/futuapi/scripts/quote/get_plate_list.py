#!/usr/bin/env python3
"""
获取板块列表

功能：获取指定市场的板块列表（行业/概念/地区），支持关键词过滤
用法：python get_plate_list.py --market HK --type CONCEPT --keyword 科技

接口限制：
- 每 30 秒内最多请求 10 次

参数说明：
- market: 不区分沪和深，输入沪或深都会返回沪深市场的子板块
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
    Market,
    Plate,
)

MARKET_MAP = {
    "HK": Market.HK,
    "US": Market.US,
    "SH": Market.SH,
    "SZ": Market.SZ,
}

PLATE_CLASS_MAP = {
    "ALL": Plate.ALL,
    "INDUSTRY": Plate.INDUSTRY,
    "REGION": Plate.REGION,
    "CONCEPT": Plate.CONCEPT,
    "OTHER": Plate.OTHER,
}


def get_plate_list(market="HK", plate_type="ALL", keyword=None, limit=50, output_json=False):
    market_enum = MARKET_MAP.get(market.upper(), Market.HK)
    plate_class = PLATE_CLASS_MAP.get(plate_type.upper(), Plate.ALL)

    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_plate_list(market_enum, plate_class)
        check_ret(ret, data, ctx, "获取板块列表")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无数据")
            return

        records = []
        for i in range(len(data)):
            row = data.iloc[i] if hasattr(data, "iloc") else data[i]
            plate_name = safe_get(row, "plate_name", "stock_name", default="")
            plate_code = safe_get(row, "code", default="")

            if keyword and keyword.lower() not in str(plate_name).lower():
                continue

            records.append({
                "code": plate_code,
                "name": plate_name,
            })

            if len(records) >= limit:
                break

        if output_json:
            print(json.dumps({"market": market, "type": plate_type, "data": records}, ensure_ascii=False))
        else:
            print("=" * 50)
            print(f"板块列表: {market} - {plate_type}" + (f" (关键词: {keyword})" if keyword else ""))
            print("=" * 50)
            for r in records:
                print(f"  {r['code']:<20} {r['name']}")
            print(f"\n  共 {len(records)} 个板块")
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
    parser = argparse.ArgumentParser(description="获取板块列表")
    parser.add_argument("--market", choices=["HK", "US", "SH", "SZ"], default="HK", help="市场（默认: HK）")
    parser.add_argument("--type", dest="plate_type", choices=["ALL", "INDUSTRY", "REGION", "CONCEPT", "OTHER"],
                        default="ALL", help="板块类型（默认: ALL）")
    parser.add_argument("--keyword", "-k", default=None, help="关键词过滤板块名称")
    parser.add_argument("--limit", type=int, default=50, help="返回数量限制（默认: 50）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_plate_list(args.market, args.plate_type, args.keyword, args.limit, args.output_json)

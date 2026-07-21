#!/usr/bin/env python3
"""
获取股票所属板块

功能：查询指定股票所属的所有板块
用法：python get_owner_plate.py HK.00700 US.AAPL

接口限制：
- 每 30 秒内最多请求 10 次
- 每次股票代码上限 200 个
- 仅支持正股和指数

返回字段说明：
- plate_type: 行业板块或概念板块
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


def get_owner_plate(codes, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_owner_plate(codes)
        check_ret(ret, data, ctx, "获取所属板块")

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
                "plate_code": safe_get(row, "plate_code", default=""),
                "plate_name": safe_get(row, "plate_name", default=""),
                "plate_type": format_enum(safe_get(row, "plate_type", default="")),
            })

        if output_json:
            print(json.dumps({"data": records}, ensure_ascii=False))
        else:
            print("=" * 60)
            print("股票所属板块")
            print("=" * 60)
            current_code = None
            for r in records:
                if r["code"] != current_code:
                    current_code = r["code"]
                    print(f"\n  {current_code}:")
                print(f"    {r['plate_code']:<15} {r['plate_name']:<20} [{r['plate_type']}]")
            print("\n" + "=" * 60)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取股票所属板块")
    parser.add_argument("codes", nargs="+", help="股票代码，如 HK.00700 US.AAPL")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_owner_plate(args.codes, args.output_json)

#!/usr/bin/env python3
"""
获取板块成分股

功能：获取指定板块的成分股列表，支持板块代码或内置别名
用法：python get_plate_stock.py HK.BK1910
      python get_plate_stock.py hsi
      python get_plate_stock.py --list-aliases

接口限制：
- 每 30 秒内最多请求 10 次

参数说明：
- plate_code: 先通过 get_plate_list 获取板块代码
- ascend: True 升序，False 降序
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
)

# 内置板块别名
PLATE_ALIASES = {
    # 港股指数
    "hsi": ("HK.800000", "恒生指数"),
    "hscei": ("HK.800100", "国企指数"),
    "hstech": ("HK.800700", "恒生科技"),
    # 港股概念
    "hk_ai": ("HK.BK1910", "AI概念"),
    "hk_chip": ("HK.LIST22912", "芯片概念"),
    "hk_ev": ("HK.LIST22910", "新能源车"),
    "hk_bank": ("HK.LIST1239", "内银股"),
    "hk_property": ("HK.LIST1234", "内房股"),
    "hk_biotech": ("HK.LIST22911", "生物医药"),
    "hk_internet": ("HK.LIST22886", "科网股"),
    # 美股科技
    "us_ai": ("US.LIST2136", "AI概念"),
    "us_chip": ("US.LIST20077", "半导体"),
    "us_cloud": ("US.LIST2520", "SaaS概念"),
    "us_cybersecurity": ("US.LIST2570", "网络安全"),
    # 美股热门
    "us_chinese": ("US.LIST2517", "中概股"),
}


def list_aliases():
    """列出所有可用别名"""
    result = {}
    for alias, (code, desc) in PLATE_ALIASES.items():
        result[alias] = {"code": code, "description": desc}
    return result


def get_plate_stock(plate_code_or_alias, limit=30, output_json=False):
    # 解析别名
    if plate_code_or_alias in PLATE_ALIASES:
        plate_code, plate_desc = PLATE_ALIASES[plate_code_or_alias]
    else:
        plate_code = plate_code_or_alias
        plate_desc = plate_code

    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_plate_stock(plate_code)
        check_ret(ret, data, ctx, "获取板块成分股")

        if is_empty(data):
            if output_json:
                print(json.dumps({"plate": plate_code, "data": []}))
            else:
                print("无数据")
            return

        records = []
        n = min(len(data), limit) if limit > 0 else len(data)
        for i in range(n):
            row = data.iloc[i] if hasattr(data, "iloc") else data[i]
            records.append({
                "code": safe_get(row, "code", default=""),
                "name": safe_get(row, "stock_name", default=""),
            })

        if output_json:
            print(json.dumps({"plate": plate_code, "plate_desc": plate_desc, "data": records}, ensure_ascii=False))
        else:
            print("=" * 50)
            print(f"板块成分股: {plate_desc} ({plate_code})")
            print("=" * 50)
            for r in records:
                print(f"  {r['code']:<15} {r['name']}")
            print(f"\n  显示 {len(records)} / {len(data)} 只")
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
    parser = argparse.ArgumentParser(description="获取板块成分股")
    parser.add_argument("plate", nargs="?", default=None, help="板块代码或别名（如 HK.BK1910 或 hsi）")
    parser.add_argument("--list-aliases", action="store_true", help="列出所有支持的别名")
    parser.add_argument("--limit", type=int, default=30, help="返回数量限制（默认: 30）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()

    if args.list_aliases:
        aliases = list_aliases()
        if args.output_json:
            print(json.dumps(aliases, ensure_ascii=False))
        else:
            print("=" * 50)
            print("支持的板块别名")
            print("=" * 50)
            for alias, info in aliases.items():
                print(f"  {alias:<20} {info['code']:<15} {info['description']}")
            print("=" * 50)
    elif args.plate:
        get_plate_stock(args.plate, args.limit, args.output_json)
    else:
        parser.print_help()

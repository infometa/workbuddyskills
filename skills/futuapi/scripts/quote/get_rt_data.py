#!/usr/bin/env python3
"""
获取分时数据

功能：获取指定股票的当日分时（Time-Sharing）数据
用法：python get_rt_data.py HK.00700

接口限制：
- 需先订阅 RT_DATA 类型

返回字段说明：
- time: 格式 yyyy-MM-dd HH:mm:ss，港股/A 股北京时间，美股美东时间
- is_blank: False 正常数据，True 伪造数据（非交易时段填充）
- avg_price: 期权该字段为 N/A
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
    SubType,
    RET_OK,
)


def get_rt_data(code, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, msg = ctx.subscribe([code], [SubType.RT_DATA])
        if ret != RET_OK:
            print(f"订阅失败: {msg}")
            sys.exit(1)

        ret, data = ctx.get_rt_data(code)
        check_ret(ret, data, ctx, "获取分时数据")

        if is_empty(data):
            if output_json:
                print(json.dumps({"code": code, "data": []}))
            else:
                print("无数据")
            return

        records = []
        for i in range(len(data)):
            row = data.iloc[i] if hasattr(data, "iloc") else data[i]
            records.append({
                "time": safe_get(row, "time", default=""),
                "price": safe_float(safe_get(row, "cur_price", default=0)),
                "avg_price": safe_float(safe_get(row, "avg_price", default=0)),
                "volume": safe_int(safe_get(row, "volume", default=0)),
                "turnover": safe_float(safe_get(row, "turnover", default=0)),
            })

        if output_json:
            print(json.dumps({"code": code, "data": records}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"分时数据: {code}")
            print("=" * 70)
            print(f"  {'时间':<20} {'价格':>10} {'均价':>10} {'成交量':>12}")
            print("  " + "-" * 54)
            for r in records:
                print(f"  {r['time']:<20} {r['price']:>10.3f} {r['avg_price']:>10.3f} {r['volume']:>12}")
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
    parser = argparse.ArgumentParser(description="获取分时数据")
    parser.add_argument("code", help="股票代码，如 HK.00700")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_rt_data(args.code, args.output_json)

#!/usr/bin/env python3
"""
获取逐笔成交数据

功能：获取指定股票的最近逐笔成交记录
用法：python get_ticker.py HK.00700 --num 20

接口限制：
- 需先订阅 TICKER 类型
- 最多获取最近 1000 个逐笔
- 港股期权期货在 LV1 权限下，不支持获取逐笔

返回字段说明：
- time: 格式 yyyy-MM-dd HH:mm:ss:xxx，港股/A 股北京时间，美股美东时间
- volume: 单位：股
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


def get_ticker(code, num=20, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, msg = ctx.subscribe([code], [SubType.TICKER])
        if ret != RET_OK:
            print(f"订阅失败: {msg}")
            sys.exit(1)

        ret, data = ctx.get_rt_ticker(code, num=num)
        check_ret(ret, data, ctx, "获取逐笔")

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
                "price": safe_float(safe_get(row, "price", default=0)),
                "volume": safe_int(safe_get(row, "volume", default=0)),
                "turnover": safe_float(safe_get(row, "turnover", default=0)),
                "direction": safe_get(row, "ticker_direction", default=""),
            })

        if output_json:
            print(json.dumps({"code": code, "data": records}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"逐笔成交: {code}（最近 {num} 笔）")
            print("=" * 70)
            print(f"  {'时间':<20} {'价格':>10} {'成交量':>10} {'方向':>8}")
            print("  " + "-" * 50)
            for r in records:
                print(f"  {r['time']:<20} {r['price']:>10.3f} {r['volume']:>10} {r['direction']:>8}")
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
    parser = argparse.ArgumentParser(description="获取逐笔成交数据")
    parser.add_argument("code", help="股票代码，如 HK.00700")
    parser.add_argument("--num", type=int, default=20, help="返回笔数（默认: 20）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_ticker(args.code, args.num, args.output_json)

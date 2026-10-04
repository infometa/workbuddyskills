#!/usr/bin/env python3
"""
获取资金流向

功能：获取指定股票的日内分时资金流向数据
用法：python get_capital_flow.py HK.00700

接口限制：
- 每 30 秒内最多请求 30 次
- 仅支持正股、窝轮和基金
- 历史周期仅提供最近 1 年数据

参数说明：
- start/end: 格式 yyyy-MM-dd，例如 "2017-06-20"

返回字段说明：
- capital_flow_item_time: 格式 yyyy-MM-dd HH:mm:ss，精确到分钟
- main_in_flow: 仅历史周期（日、周、月）有效
- last_valid_time: 仅实时周期有效
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
    df_to_records,
)


def get_capital_flow(code, period_type=None, start=None, end=None, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        kwargs = {}
        if period_type is not None:
            kwargs["period_type"] = period_type
        if start is not None:
            kwargs["start"] = start
        if end is not None:
            kwargs["end"] = end
        ret, data = ctx.get_capital_flow(code, **kwargs)
        check_ret(ret, data, ctx, "获取资金流向")

        if is_empty(data):
            if output_json:
                print(json.dumps({"code": code, "data": []}))
            else:
                print("无数据")
            return

        if output_json:
            records = df_to_records(data, limit=100)
            print(json.dumps({"code": code, "data": records}, ensure_ascii=False))
        else:
            print("=" * 80)
            print(f"资金流向: {code}")
            print("=" * 80)
            cols = ["capital_flow_item_time", "last_valid_time", "in_flow",
                    "super_in_flow", "big_in_flow", "mid_in_flow", "sml_in_flow", "main_in_flow"]
            available = [c for c in cols if c in data.columns]
            if available:
                print(data[available].tail(20).to_string(index=False))
            else:
                print(data.tail(20).to_string(index=False))
            print("=" * 80)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取资金流向")
    parser.add_argument("code", help="股票代码，如 HK.00700")
    parser.add_argument("--period-type", type=int, default=None, help="周期类型（1=日内, 2=日, 3=周, 4=月）")
    parser.add_argument("--start", default=None, help="开始日期，如 2024-01-01")
    parser.add_argument("--end", default=None, help="结束日期，如 2024-12-31")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_capital_flow(args.code, period_type=args.period_type, start=args.start,
                     end=args.end, output_json=args.output_json)

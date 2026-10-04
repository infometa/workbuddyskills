#!/usr/bin/env python3
"""
获取资金分布

功能：获取指定股票的资金分布（特大单/大单/中单/小单的流入流出）
用法：python get_capital_distribution.py HK.00700

接口限制：
- 每 30 秒内最多请求 30 次
- 仅支持正股、窝轮和基金

返回字段说明：
- update_time: 格式 yyyy-MM-dd HH:mm:ss
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
)


def get_capital_distribution(code, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_capital_distribution(code)
        check_ret(ret, data, ctx, "获取资金分布")

        if is_empty(data):
            if output_json:
                print(json.dumps({"code": code, "data": {}}))
            else:
                print("无数据")
            return

        row = data.iloc[0] if hasattr(data, "iloc") else data
        result = {
            "code": code,
            "capital_in_super": safe_float(safe_get(row, "capital_in_super", default=0)),
            "capital_out_super": safe_float(safe_get(row, "capital_out_super", default=0)),
            "capital_in_big": safe_float(safe_get(row, "capital_in_big", default=0)),
            "capital_out_big": safe_float(safe_get(row, "capital_out_big", default=0)),
            "capital_in_mid": safe_float(safe_get(row, "capital_in_mid", default=0)),
            "capital_out_mid": safe_float(safe_get(row, "capital_out_mid", default=0)),
            "capital_in_small": safe_float(safe_get(row, "capital_in_small", default=0)),
            "capital_out_small": safe_float(safe_get(row, "capital_out_small", default=0)),
        }

        if output_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("=" * 60)
            print(f"资金分布: {code}")
            print("=" * 60)
            print(f"  {'类型':<10} {'流入':>15} {'流出':>15} {'净流入':>15}")
            print("  " + "-" * 56)
            for label, in_key, out_key in [
                ("特大单", "capital_in_super", "capital_out_super"),
                ("大单", "capital_in_big", "capital_out_big"),
                ("中单", "capital_in_mid", "capital_out_mid"),
                ("小单", "capital_in_small", "capital_out_small"),
            ]:
                in_val = result[in_key]
                out_val = result[out_key]
                net = in_val - out_val
                print(f"  {label:<10} {in_val:>15.2f} {out_val:>15.2f} {net:>15.2f}")
            print("=" * 60)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取资金分布")
    parser.add_argument("code", help="股票代码，如 HK.00700")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_capital_distribution(args.code, args.output_json)

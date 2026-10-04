#!/usr/bin/env python3
"""
解析期权简写代码并从期权链中匹配富途期权代码

功能：将用户输入的期权描述解析并通过期权链接口查找对应的富途期权代码
用法：python resolve_option_code.py --underlying US.JPM --expiry 2026-03-20 --strike 267.50 --type CALL [--json]

注意：正股代码必须包含市场前缀（如 US.JPM、HK.00700），由调用方根据上下文确定市场。

接口限制：
- 每 30 秒内最多请求 60 次
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
    safe_float,
    df_to_records,
)


def resolve_option_code(underlying, expiry, strike, option_type, output_json=False):
    """
    通过期权链接口查找匹配的期权合约代码

    Args:
        underlying: 正股代码，必须含市场前缀 (如 US.JPM, HK.00700)
        expiry: 到期日 (如 2026-03-20)
        strike: 行权价 (如 267.50)
        option_type: CALL 或 PUT
        output_json: 是否输出 JSON
    """
    if '.' not in underlying:
        msg = f"正股代码 '{underlying}' 缺少市场前缀，请使用完整格式如 US.{underlying.upper()} 或 HK.{underlying}"
        if output_json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(f"错误: {msg}")
        sys.exit(1)

    ctx = None
    try:
        ctx = create_quote_context()

        # 使用到期日作为期权链的时间筛选范围
        ret, data = ctx.get_option_chain(underlying, start=expiry, end=expiry)
        check_ret(ret, data, ctx, "获取期权链")

        if is_empty(data):
            msg = f"未找到 {underlying} 在 {expiry} 的期权链数据"
            if output_json:
                print(json.dumps({"error": msg, "underlying": underlying,
                                  "expiry": expiry, "strike": strike,
                                  "option_type": option_type}, ensure_ascii=False))
            else:
                print(f"错误: {msg}")
            sys.exit(1)

        # 在期权链中匹配：行权价 + 期权类型(CALL/PUT)
        matched = []
        for i in range(len(data)):
            row = data.iloc[i] if hasattr(data, "iloc") else data[i]

            row_strike = safe_float(row.get("strike_price", 0))
            row_type = str(row.get("option_type", "")).upper()
            row_code = str(row.get("code", ""))
            row_name = str(row.get("name", ""))
            row_strike_time = str(row.get("strike_time", ""))
            row_last_price = safe_float(row.get("last_price", 0))

            # 匹配期权类型
            type_match = False
            if option_type == "CALL" and row_type in ("CALL", "涨", "认购"):
                type_match = True
            elif option_type == "PUT" and row_type in ("PUT", "跌", "认沽"):
                type_match = True

            # 匹配行权价（浮点数比较，容差 0.001）
            strike_match = abs(row_strike - strike) < 0.001

            if type_match and strike_match:
                matched.append({
                    "code": row_code,
                    "name": row_name,
                    "strike_price": row_strike,
                    "strike_time": row_strike_time,
                    "option_type": row_type,
                    "last_price": row_last_price,
                })

        if not matched:
            msg = (f"在 {underlying} 的期权链中未找到匹配的合约\n"
                   f"  到期日: {expiry}, 行权价: {strike}, 类型: {option_type}")
            if output_json:
                print(json.dumps({
                    "error": msg,
                    "underlying": underlying,
                    "expiry": expiry,
                    "strike": strike,
                    "option_type": option_type,
                    "available_count": len(data),
                }, ensure_ascii=False))
            else:
                print(f"错误: {msg}")
                # 打印最接近的几个合约帮助用户确认
                _print_nearby(data, strike, option_type)
            sys.exit(1)

        if output_json:
            print(json.dumps({
                "underlying": underlying,
                "expiry": expiry,
                "strike": strike,
                "option_type": option_type,
                "matched": matched,
            }, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"期权代码解析结果")
            print("=" * 70)
            print(f"  正股:     {underlying}")
            print(f"  到期日:   {expiry}")
            print(f"  行权价:   {strike}")
            print(f"  类型:     {option_type}")
            print("-" * 70)
            for m in matched:
                print(f"  期权代码: {m['code']}")
                print(f"  名称:     {m['name']}")
                print(f"  最新价:   {m['last_price']}")
                print()
            print("=" * 70)

        return matched

    except SystemExit:
        raise
    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


def _print_nearby(data, strike, option_type, count=5):
    """匹配失败时，打印行权价最接近的几个合约帮助用户确认"""
    candidates = []
    for i in range(len(data)):
        row = data.iloc[i] if hasattr(data, "iloc") else data[i]
        row_type = str(row.get("option_type", "")).upper()
        type_match = False
        if option_type == "CALL" and row_type in ("CALL", "涨", "认购"):
            type_match = True
        elif option_type == "PUT" and row_type in ("PUT", "跌", "认沽"):
            type_match = True
        if type_match:
            row_strike = safe_float(row.get("strike_price", 0))
            candidates.append({
                "code": str(row.get("code", "")),
                "strike_price": row_strike,
                "diff": abs(row_strike - strike),
            })

    if candidates:
        candidates.sort(key=lambda x: x["diff"])
        print(f"\n最接近的 {option_type} 合约:")
        for c in candidates[:count]:
            print(f"  {c['code']}  行权价: {c['strike_price']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="通过期权链查找富途期权代码",
        epilog="示例: python resolve_option_code.py --underlying US.JPM --expiry 2026-03-20 --strike 267.50 --type CALL",
    )
    parser.add_argument("--underlying", required=True,
                        help="正股代码，必须含市场前缀（如 US.JPM、HK.00700）")
    parser.add_argument("--expiry", required=True,
                        help="到期日 yyyy-MM-dd")
    parser.add_argument("--strike", type=float, required=True,
                        help="行权价")
    parser.add_argument("--type", dest="option_type", required=True,
                        choices=["CALL", "PUT"],
                        help="期权类型")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="输出 JSON 格式")

    args = parser.parse_args()
    resolve_option_code(args.underlying, args.expiry, args.strike, args.option_type, args.output_json)

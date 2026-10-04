#!/usr/bin/env python3
"""
获取融资融券数据

功能：查询指定股票的融资融券比率
用法：python get_margin_ratio.py HK.00700

接口限制：
- 每 30 秒内最多请求 10 次

返回字段说明：
- im_long_ratio: 初始保证金比率（多头）
- im_short_ratio: 初始保证金比率（空头）
- mm_long_ratio: 维持保证金比率（多头）
- mm_short_ratio: 维持保证金比率（空头）
- is_long_permit: 是否允许做多
- is_short_permit: 是否允许做空
"""
import argparse
import json
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_trade_context,
    parse_trd_env,
    parse_security_firm,
    get_default_acc_id,
    get_default_trd_env,
    check_ret,
    safe_close,
    is_empty,
    df_to_records,
)


def get_margin_ratio(codes, acc_id=None, market=None, trd_env=None, security_firm=None, output_json=False):
    acc_id = acc_id or get_default_acc_id()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()

    ctx = None
    try:
        ctx = create_trade_context(market, security_firm=parse_security_firm(security_firm))
        ret, data = ctx.get_margin_ratio(codes)
        check_ret(ret, data, ctx, "获取融资融券数据")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无融资融券数据")
            return

        if output_json:
            print(json.dumps({"data": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print("融资融券数据")
            print("=" * 70)
            print(data.to_string(index=False))
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
    parser = argparse.ArgumentParser(description="获取融资融券数据")
    parser.add_argument("codes", nargs="+", help="股票代码，如 HK.00700")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--market", choices=["US", "HK", "HKCC", "CN", "SG"], default=None, help="交易市场")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_margin_ratio(args.codes, acc_id=args.acc_id, market=args.market,
                     trd_env=args.trd_env, security_firm=args.security_firm, output_json=args.output_json)

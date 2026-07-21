#!/usr/bin/env python3
"""
获取账户现金流水

功能：查询账户的现金出入流水记录
用法：python get_acc_cash_flow.py --start 2024-01-01 --end 2024-01-31

接口限制：
- 每 30 秒内最多请求 10 次

返回字段说明：
- flow_type: 流水类型
- amount: 金额
- currency: 货币
- create_time: 创建时间
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


def get_acc_cash_flow(start=None, end=None, acc_id=None, market=None, trd_env=None, security_firm=None, output_json=False):
    acc_id = acc_id or get_default_acc_id()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()

    ctx = None
    try:
        ctx = create_trade_context(market, security_firm=parse_security_firm(security_firm))
        kwargs = {"trd_env": trd_env, "acc_id": acc_id}
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end

        ret, data = ctx.get_acc_cash_flow(**kwargs)
        check_ret(ret, data, ctx, "获取现金流水")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无现金流水记录")
            return

        if output_json:
            print(json.dumps({"data": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print("账户现金流水")
            print("=" * 70)
            print(data.to_string(index=False))
            print(f"\n共 {len(data)} 条记录")
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
    parser = argparse.ArgumentParser(description="获取账户现金流水")
    parser.add_argument("--start", default=None, help="起始日期 yyyy-MM-dd")
    parser.add_argument("--end", default=None, help="结束日期 yyyy-MM-dd")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--market", choices=["US", "HK", "HKCC", "CN", "SG"], default=None, help="交易市场")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_acc_cash_flow(start=args.start, end=args.end, acc_id=args.acc_id, market=args.market,
                      trd_env=args.trd_env, security_firm=args.security_firm, output_json=args.output_json)

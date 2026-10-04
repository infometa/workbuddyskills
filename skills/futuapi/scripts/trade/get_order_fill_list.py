#!/usr/bin/env python3
"""
获取当日成交列表

功能：查询当前账户今日的成交记录
用法：python get_order_fill_list.py --market HK

接口限制：
- 每 30 秒内最多请求 10 次

返回字段说明：
- deal_id: 成交 ID
- order_id: 对应订单 ID
- code: 股票代码
- trd_side: 交易方向
- price: 成交价格
- qty: 成交数量
- create_time: 成交时间
"""
import argparse
import json
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_trade_context,
    parse_trd_env,
    parse_market,
    parse_security_firm,
    get_default_acc_id,
    get_default_trd_env,
    get_default_market,
    check_ret,
    safe_close,
    is_empty,
    df_to_records,
    format_enum,
)


def get_order_fill_list(acc_id=None, market=None, trd_env=None, security_firm=None, output_json=False):
    acc_id = acc_id or get_default_acc_id()
    trd_market = parse_market(market) if market else get_default_market()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()

    ctx = None
    try:
        ctx = create_trade_context(trd_market, security_firm=parse_security_firm(security_firm))
        ret, data = ctx.deal_list_query(trd_env=trd_env, acc_id=acc_id, refresh_cache=True)
        check_ret(ret, data, ctx, "查询当日成交")

        if is_empty(data):
            if output_json:
                print(json.dumps({"deals": []}))
            else:
                print("=" * 70)
                print(f"当日成交 - 市场: {format_enum(trd_market)}")
                print("=" * 70)
                print("\n  暂无成交记录")
                print("=" * 70)
            return

        if output_json:
            print(json.dumps({"market": format_enum(trd_market), "deals": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"当日成交 - 市场: {format_enum(trd_market)}")
            print("=" * 70)
            print(data.to_string(index=False))
            print(f"\n共 {len(data)} 条成交")
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
    parser = argparse.ArgumentParser(description="获取当日成交列表")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--market", choices=["US", "HK", "HKCC", "CN", "SG"], default=None, help="交易市场")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_order_fill_list(acc_id=args.acc_id, market=args.market, trd_env=args.trd_env,
                        security_firm=args.security_firm, output_json=args.output_json)

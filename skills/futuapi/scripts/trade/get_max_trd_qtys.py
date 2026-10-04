#!/usr/bin/env python3
"""
查询最大可买卖数量

功能：查询指定股票的最大可买卖数量
用法：python get_max_trd_qtys.py HK.00700 --price 400

接口限制：
- 每 30 秒内最多请求 10 次

参数说明：
- price: 目标价格（必填），用于计算可买卖数量
- order_type: 订单类型，默认 NORMAL（普通限价单）
- session: 仅对美股生效，支持 RTH/ETH/OVERNIGHT/ALL
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
    safe_get,
    safe_float,
    safe_int,
    format_enum,
    OrderType,
    Session,
)

# session 仅对美股生效
ORDER_SESSION_MAP = {
    "NONE": Session.NONE,
    "RTH": Session.RTH,
    "ETH": Session.ETH,
    "OVERNIGHT": Session.OVERNIGHT,
    "ALL": Session.ALL,
}


def get_max_trd_qtys(code, price, acc_id=None, market=None, trd_env=None,
                     security_firm=None, session_str="NONE", output_json=False):
    acc_id = acc_id or get_default_acc_id()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()
    session = ORDER_SESSION_MAP.get(session_str.upper(), Session.NONE)

    ctx = None
    try:
        ctx = create_trade_context(market, security_firm=parse_security_firm(security_firm))
        query_kwargs = dict(
            order_type=OrderType.NORMAL,
            code=code,
            price=price,
            trd_env=trd_env,
            acc_id=acc_id,
        )
        if session != Session.NONE:
            query_kwargs["session"] = session
        ret, data = ctx.acctradinginfo_query(**query_kwargs)
        check_ret(ret, data, ctx, "查询最大可买卖数量")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": {}}))
            else:
                print("无数据")
            return

        row = data.iloc[0] if hasattr(data, "iloc") else data[0]
        result = {
            "code": code,
            "price": price,
            "max_cash_buy": safe_int(safe_get(row, "max_cash_buy", default=0)),
            "max_cash_and_margin_buy": safe_int(safe_get(row, "max_cash_and_margin_buy", default=0)),
            "max_position_sell": safe_int(safe_get(row, "max_position_sell", default=0)),
        }

        if output_json:
            print(json.dumps({"data": result}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"最大可买卖数量 - {code} @ {price}")
            print("=" * 70)
            print(f"  最大现金可买: {result['max_cash_buy']}")
            print(f"  最大融资可买: {result['max_cash_and_margin_buy']}")
            print(f"  最大可卖: {result['max_position_sell']}")
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
    parser = argparse.ArgumentParser(description="查询最大可买卖数量")
    parser.add_argument("code", help="股票代码，如 HK.00700")
    parser.add_argument("--price", type=float, required=True, help="目标价格")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--market", choices=["US", "HK", "HKCC", "CN", "SG"], default=None, help="交易市场")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--session", choices=["NONE", "RTH", "ETH", "OVERNIGHT", "ALL"],
                        default="NONE", help="美股交易时段（仅对美股生效）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_max_trd_qtys(args.code, args.price, acc_id=args.acc_id, market=args.market,
                     trd_env=args.trd_env, security_firm=args.security_firm,
                     session_str=args.session, output_json=args.output_json)

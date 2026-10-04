#!/usr/bin/env python3
"""
获取订单列表

功能：查询当前账户的今日订单
用法：python get_orders.py --market HK --trd-env SIMULATE

接口限制：
- 同一账户 ID 每 30 秒最多请求 10 次（仅刷新缓存时受限）

参数说明：
- refresh_cache: True 立即请求服务器（受限频限制），False 使用 OpenD 缓存
- start/end: 格式 YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD HH:MM:SS.MS

返回字段说明：
- qty/dealt_qty: 期权期货单位是"张"
- price: 精确到小数点后 3 位，超出部分四舍五入
- dealt_avg_price: 无精度限制
- create_time/updated_time: 格式 yyyy-MM-dd HH:mm:ss
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
    format_enum,
    safe_get,
    safe_float,
)


def get_orders(acc_id=None, market=None, trd_env=None, security_firm=None, output_json=False):
    acc_id = acc_id or get_default_acc_id()
    trd_market = parse_market(market) if market else get_default_market()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()

    ctx = None
    try:
        ctx = create_trade_context(trd_market, security_firm=parse_security_firm(security_firm))
        ret, data = ctx.order_list_query(trd_env=trd_env, acc_id=acc_id, refresh_cache=True)
        check_ret(ret, data, ctx, "查询订单")

        if is_empty(data):
            if output_json:
                print(json.dumps({"orders": []}))
            else:
                print("=" * 70)
                print(f"订单列表 - 市场: {format_enum(trd_market)}")
                print("=" * 70)
                print("\n  暂无订单")
                print("=" * 70)
            return

        orders = []
        for i in range(len(data)):
            row = data.iloc[i] if hasattr(data, "iloc") else data[i]
            orders.append({
                "order_id": str(safe_get(row, "order_id", "orderID", default="N/A")),
                "code": safe_get(row, "code", default="N/A"),
                "side": format_enum(safe_get(row, "trd_side", "side", default="N/A")),
                "status": format_enum(safe_get(row, "order_status", "status", default="N/A")),
                "qty": safe_float(safe_get(row, "qty", "quantity", default=0)),
                "price": safe_float(safe_get(row, "price", default=0)),
                "dealt_qty": safe_float(safe_get(row, "dealt_qty", default=0)),
                "dealt_avg_price": safe_float(safe_get(row, "dealt_avg_price", default=0)),
            })

        if output_json:
            print(json.dumps({"market": format_enum(trd_market), "orders": orders}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"订单列表 - 市场: {format_enum(trd_market)}")
            print("=" * 70)
            for o in orders:
                print(f"\n  订单 ID: {o['order_id']}")
                print(f"    代码: {o['code']}  方向: {o['side']}  状态: {o['status']}")
                print(f"    委托: {o['qty']} 股 @ {o['price']}  成交: {o['dealt_qty']} 股 @ {o['dealt_avg_price']}")
                print("  " + "-" * 66)
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
    parser = argparse.ArgumentParser(description="获取今日订单列表")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--market", choices=["US", "HK", "HKCC", "CN", "SG"], default=None, help="交易市场")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_orders(acc_id=args.acc_id, market=args.market, trd_env=args.trd_env,
               security_firm=args.security_firm, output_json=args.output_json)

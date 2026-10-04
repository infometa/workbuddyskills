#!/usr/bin/env python3
"""
获取历史订单

功能：查询账户的历史订单记录
用法：python get_history_orders.py --market HK --start 2026-01-01 --end 2026-03-01

接口限制：
- 同一账户 ID 每 30 秒最多请求 10 次

参数说明：
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


def get_history_orders(acc_id=None, market=None, trd_env=None, code=None,
                       start=None, end=None, status_list=None, limit=200,
                       security_firm=None, output_json=False):
    acc_id = acc_id or get_default_acc_id()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()

    ctx = None
    try:
        ctx = create_trade_context(market, security_firm=parse_security_firm(security_firm))
        kwargs = {"trd_env": trd_env, "acc_id": acc_id}
        if code:
            kwargs["code"] = code
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end
        if status_list:
            from futu import OrderStatus
            status_filter = []
            for s in status_list:
                if hasattr(OrderStatus, s.upper()):
                    status_filter.append(getattr(OrderStatus, s.upper()))
            if status_filter:
                kwargs["status_filter_list"] = status_filter

        ret, data = ctx.history_order_list_query(**kwargs)
        check_ret(ret, data, ctx, "查询历史订单")

        if is_empty(data):
            if output_json:
                print(json.dumps({"orders": []}))
            else:
                print("暂无历史订单")
            return

        orders = []
        n = min(len(data), limit)
        for i in range(n):
            row = data.iloc[i] if hasattr(data, "iloc") else data[i]
            orders.append({
                "order_id": str(safe_get(row, "order_id", default="N/A")),
                "code": safe_get(row, "code", default="N/A"),
                "side": format_enum(safe_get(row, "trd_side", default="")),
                "status": format_enum(safe_get(row, "order_status", default="")),
                "qty": safe_float(safe_get(row, "qty", default=0)),
                "price": safe_float(safe_get(row, "price", default=0)),
                "dealt_qty": safe_float(safe_get(row, "dealt_qty", default=0)),
                "create_time": safe_get(row, "create_time", default=""),
                "updated_time": safe_get(row, "updated_time", default=""),
            })

        no_date_filter = not start and not end
        if output_json:
            result = {"count": len(orders), "orders": orders}
            if no_date_filter:
                result["note"] = "默认仅查询最近90天的订单，如需更早的记录请指定 --start/--end"
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("=" * 80)
            print(f"历史订单（共 {len(orders)} 条）")
            if no_date_filter:
                print("提示：默认仅查询最近90天的订单，如需更早的记录请指定 --start/--end")
            print("=" * 80)
            for o in orders:
                print(f"  [{o['create_time']}] {o['order_id']}  {o['code']}  {o['side']}  "
                      f"{o['qty']}股@{o['price']}  成交:{o['dealt_qty']}  {o['status']}")
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
    parser = argparse.ArgumentParser(description="获取历史订单")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--market", choices=["US", "HK", "HKCC", "CN", "SG"], default=None, help="交易市场")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--code", default=None, help="股票代码过滤")
    parser.add_argument("--start", default=None, help="开始日期（YYYY-MM-DD）")
    parser.add_argument("--end", default=None, help="结束日期（YYYY-MM-DD）")
    parser.add_argument("--status", nargs="+", default=None, help="订单状态过滤（如 FILLED_ALL CANCELLED_ALL）")
    parser.add_argument("--limit", type=int, default=200, help="返回数量限制")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_history_orders(acc_id=args.acc_id, market=args.market, trd_env=args.trd_env,
                       code=args.code, start=args.start, end=args.end,
                       status_list=args.status, limit=args.limit,
                       security_firm=args.security_firm, output_json=args.output_json)

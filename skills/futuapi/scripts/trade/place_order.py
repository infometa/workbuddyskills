#!/usr/bin/env python3
"""
下单

功能：在指定账户下单买入或卖出股票
注意：默认使用模拟账户，真实交易需要指定 --trd-env REAL

接口限制：
- 同一账户 ID 每 30 秒最多请求 15 次
- 连续两次下单间隔不可小于 0.02 秒
- 真实账户需先在 OpenD GUI 界面手动解锁交易密码

参数说明：
- price: 市价单/竞价单仍需传参（可传任意值）。精度：期货整数8位小数9位，美股期权小数2位，美股≤$1允许小数4位，其他小数3位超出四舍五入
- qty: 期权期货单位是"张"
- code: 期货主连代码会自动转为实际合约代码
- adjust_limit: 正数向上调整，负数向下调整，如 0.015 表示向上调整幅度不超过 1.5%
- remark: utf8 长度上限 64 字节
- time_in_force: 港股、A 股、环球期货的市价单仅支持当日有效
- fill_outside_rth: 用于港股盘前竞价与美股盘前盘后，盘前盘后时段不支持市价单
- aux_price: 止损/止盈类订单必传
- trail_type/trail_value/trail_spread: 跟踪止损类订单必传
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
    parse_trd_side,
    parse_security_firm,
    get_default_acc_id,
    get_default_trd_env,
    infer_market_from_code,
    check_ret,
    safe_close,
    format_enum,
    safe_get,
    safe_int,
    OrderType,
    Session,
    RET_OK,
    is_empty,
)

# 下单 session 仅对美股生效
ORDER_SESSION_MAP = {
    "NONE": Session.NONE,
    "RTH": Session.RTH,
    "ETH": Session.ETH,
    "OVERNIGHT": Session.OVERNIGHT,
    "ALL": Session.ALL,
}


def _audit_log(entry):
    """追加交易审计日志到 ~/.futu_trade_audit.jsonl"""
    import datetime
    try:
        log_path = _os.path.join(_os.path.expanduser("~"), ".futu_trade_audit.jsonl")
        entry["timestamp"] = datetime.datetime.now().isoformat()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def place_order(code, side, quantity, price=None, order_type="NORMAL",
                acc_id=None, trd_env=None, security_firm=None, output_json=False,
                confirmed=False, fill_outside_rth=False, session_str="NONE"):
    acc_id = acc_id or get_default_acc_id()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()
    trd_side = parse_trd_side(side)

    # 从 --code 前缀自动推导交易市场
    market = infer_market_from_code(code)
    if not market:
        msg = f"无法从代码 '{code}' 推导交易市场，请使用完整格式如 US.AAPL、HK.00700"
        if output_json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(f"错误: {msg}")
        sys.exit(1)

    if str(order_type).upper() == "MARKET":
        order_type_enum = OrderType.MARKET
        price = 0.0
    else:
        order_type_enum = OrderType.NORMAL
        if price is None:
            print("错误: 限价单必须指定 --price")
            sys.exit(1)

    try:
        if quantity is None or int(quantity) <= 0:
            raise ValueError
    except (ValueError, TypeError):
        if output_json:
            print(json.dumps({"error": "数量必须为正整数"}, ensure_ascii=False))
        else:
            print("错误: 数量必须为正整数")
        sys.exit(1)

    # 实盘下单硬约束：必须传 --confirmed 才能真正下单
    if format_enum(trd_env) == "REAL" and not confirmed:
        summary = {
            "action": "place_order_preview",
            "code": code,
            "side": format_enum(trd_side),
            "quantity": quantity,
            "price": price,
            "order_type": str(order_type).upper(),
            "trd_env": "REAL",
            "acc_id": acc_id,
            "message": "实盘下单需要确认。请核实订单信息后，加上 --confirmed 参数重新执行。",
        }
        if output_json:
            print(json.dumps(summary, ensure_ascii=False))
        else:
            print("=" * 60)
            print("实盘下单预览（未执行）")
            print("=" * 60)
            print(f"  代码:     {code}")
            print(f"  方向:     {format_enum(trd_side)}")
            print(f"  数量:     {quantity}")
            print(f"  价格:     {price}")
            print(f"  类型:     {order_type}")
            print(f"  账户:     {acc_id}")
            print("=" * 60)
            print("请确认后加 --confirmed 参数重新执行。")
        sys.exit(2)

    ctx = None
    try:
        ctx = create_trade_context(market, security_firm=parse_security_firm(security_firm))
        # 校验账户角色：MASTER 账户不允许下单
        if acc_id:
            ret, acc_data = ctx.get_acc_list()
            if ret == RET_OK and not is_empty(acc_data):
                for i in range(len(acc_data)):
                    row = acc_data.iloc[i] if hasattr(acc_data, "iloc") else acc_data[i]
                    row_acc_id = safe_int(safe_get(row, "acc_id", default=0))
                    if row_acc_id == safe_int(acc_id):
                        acc_role = format_enum(safe_get(row, "acc_role", default=""))
                        if acc_role.upper() == "MASTER":
                            msg = "主账户（MASTER）不允许下单，请选择非主账户"
                            if output_json:
                                print(json.dumps({"error": msg}, ensure_ascii=False))
                            else:
                                print(f"错误: {msg}")
                            sys.exit(1)
                        break

        session = ORDER_SESSION_MAP.get(session_str.upper(), Session.NONE)
        order_kwargs = dict(
            price=float(price),
            qty=int(quantity),
            code=code,
            trd_side=trd_side,
            order_type=order_type_enum,
            trd_env=trd_env,
            acc_id=acc_id,
        )
        if fill_outside_rth:
            order_kwargs["fill_outside_rth"] = True
        if session != Session.NONE:
            order_kwargs["session"] = session
        ret, data = ctx.place_order(**order_kwargs)
        check_ret(ret, data, ctx, "下单")

        if hasattr(data, "iloc"):
            row = data.iloc[0]
            order_id = safe_get(row, "order_id", "orderID", default=str(data))
        else:
            order_id = str(data)

        result = {
            "order_id": str(order_id),
            "code": code,
            "side": format_enum(trd_side),
            "quantity": quantity,
            "price": price,
            "order_type": str(order_type).upper(),
            "trd_env": format_enum(trd_env),
            "status": "submitted",
        }

        _audit_log({"action": "place_order", "result": "success", **result})

        if output_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("=" * 60)
            print("下单成功")
            print("=" * 60)
            print(f"  订单 ID:  {order_id}")
            print(f"  代码:     {code}")
            print(f"  方向:     {format_enum(trd_side)}")
            print(f"  数量:     {quantity}")
            print(f"  价格:     {price}")
            print(f"  类型:     {order_type}")
            print(f"  环境:     {format_enum(trd_env)}")
            print("=" * 60)

    except Exception as e:
        _audit_log({"action": "place_order", "result": "error", "code": code,
                     "side": side, "quantity": quantity, "price": price, "error": str(e)})
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下单（买入/卖出股票）")
    parser.add_argument("--code", required=True, help="股票代码（如 US.AAPL）")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL"], help="交易方向")
    parser.add_argument("--quantity", type=int, required=True, help="数量")
    parser.add_argument("--price", type=float, default=None, help="价格（限价单必填）")
    parser.add_argument("--order-type", default="NORMAL", choices=["NORMAL", "MARKET"], help="订单类型")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--fill-outside-rth", action="store_true",
                        help="允许盘前盘后成交（美股盘前盘后、港股竞价盘）")
    parser.add_argument("--session", choices=["NONE", "RTH", "ETH", "OVERNIGHT", "ALL"],
                        default="NONE", help="美股交易时段（仅对美股生效）")
    parser.add_argument("--confirmed", action="store_true", help="实盘下单确认标志（不传则只预览不执行）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    place_order(code=args.code, side=args.side, quantity=args.quantity, price=args.price,
                order_type=args.order_type, acc_id=args.acc_id,
                trd_env=args.trd_env, security_firm=args.security_firm,
                output_json=args.output_json, confirmed=args.confirmed,
                fill_outside_rth=args.fill_outside_rth, session_str=args.session)

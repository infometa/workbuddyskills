#!/usr/bin/env python3
"""
改单

功能：修改指定订单的价格和/或数量
用法：python modify_order.py --order-id 12345678 --price 410 --quantity 200
注意：qty 为修改后期望的总数量（非增量）；A 股通市场不支持改单

接口限制：
- 同一账户 ID 每 30 秒最多请求 20 次
- 连续两次间隔不可小于 0.04 秒
- 真实账户需先在 OpenD GUI 界面手动解锁交易密码

参数说明：
- price: 证券账户精确到小数点后 3 位，期货账户精确到小数点后 9 位，超出部分被舍弃
- qty: 修改后期望的总数量（非增量），期权和期货单位是"张"，精确到小数点后 0 位
- adjust_limit: 正数向上调整，负数向下调整，如 0.015 表示幅度不超过 1.5%（期货忽略此参数）
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
    safe_get,
    safe_float,
    format_enum,
    is_empty,
    ModifyOrderOp,
    RET_OK,
)


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


def modify_order(order_id, price=None, quantity=None, adjust_limit=0,
                 acc_id=None, market=None, trd_env=None, security_firm=None, output_json=False):
    acc_id = acc_id or get_default_acc_id()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()

    if price is None and quantity is None:
        msg = "至少需要指定 --price 或 --quantity 之一"
        if output_json:
            print(json.dumps({"error": msg}, ensure_ascii=False))
        else:
            print(f"错误: {msg}")
        sys.exit(1)

    if price is not None:
        try:
            price = float(price)
        except (ValueError, TypeError):
            msg = "价格必须为数字"
            if output_json:
                print(json.dumps({"error": msg}, ensure_ascii=False))
            else:
                print(f"错误: {msg}")
            sys.exit(1)

    if quantity is not None:
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            msg = "数量必须为正整数"
            if output_json:
                print(json.dumps({"error": msg}, ensure_ascii=False))
            else:
                print(f"错误: {msg}")
            sys.exit(1)

    ctx = None
    try:
        ctx = create_trade_context(market, security_firm=parse_security_firm(security_firm))

        # 自动补全：缺失的 price 或 quantity 从原订单获取
        if price is None or quantity is None:
            ret_q, orders = ctx.order_list_query(
                order_id=order_id, trd_env=trd_env, acc_id=acc_id,
            )
            if ret_q == RET_OK and not is_empty(orders):
                orig = orders.iloc[0]
                if price is None:
                    price = float(safe_float(safe_get(orig, "price", default=0)))
                if quantity is None:
                    quantity = int(safe_float(safe_get(orig, "qty", default=0)))

        if price is None or quantity is None:
            msg = "无法从原订单获取价格或数量，请手动指定 --price 和 --quantity"
            if output_json:
                print(json.dumps({"error": msg}, ensure_ascii=False))
            else:
                print(f"错误: {msg}")
            sys.exit(1)

        ret, data = ctx.modify_order(
            modify_order_op=ModifyOrderOp.NORMAL,
            order_id=order_id,
            qty=quantity,
            price=price,
            adjust_limit=adjust_limit,
            trd_env=trd_env,
            acc_id=acc_id,
        )
        check_ret(ret, data, ctx, "改单")

        if hasattr(data, "iloc"):
            row = data.iloc[0]
            result_order_id = safe_get(row, "order_id", default=order_id)
        else:
            result_order_id = order_id

        result = {
            "order_id": str(result_order_id),
            "price": price,
            "quantity": quantity,
            "status": "modified",
        }

        _audit_log({"action": "modify_order", "result": "success", **result})

        if output_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("=" * 50)
            print("改单成功")
            print("=" * 50)
            print(f"  订单 ID: {result_order_id}")
            print(f"  新价格:  {price}")
            print(f"  新数量:  {quantity}")
            print("=" * 50)

    except Exception as e:
        _audit_log({"action": "modify_order", "result": "error", "order_id": order_id,
                     "price": price, "quantity": quantity, "error": str(e)})
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="改单（修改订单价格和数量）")
    parser.add_argument("--order-id", required=True, help="订单 ID")
    parser.add_argument("--price", type=float, default=None, help="修改后的价格（可选，不传则保持原价）")
    parser.add_argument("--quantity", type=int, default=None, help="修改后的总数量（可选，不传则保持原数量）")
    parser.add_argument("--adjust-limit", type=float, default=0, help="价格微调幅度（默认 0）")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--market", choices=["US", "HK", "HKCC", "CN", "SG"], default=None, help="交易市场")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    modify_order(order_id=args.order_id, price=args.price, quantity=args.quantity,
                 adjust_limit=args.adjust_limit, acc_id=args.acc_id, market=args.market,
                 trd_env=args.trd_env, security_firm=args.security_firm, output_json=args.output_json)

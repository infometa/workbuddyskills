#!/usr/bin/env python3
"""
获取持仓与资金

功能：查询账户的资金状况和持仓列表
用法：python get_portfolio.py --market HK --trd-env SIMULATE

接口限制：
- 同一账户 ID 每 30 秒最多请求 10 次（仅刷新缓存时受限）

参数说明：
- currency: 仅期货账户、综合证券账户适用，其它账户类型忽略此参数；返回的资金字段会以此币种换算
- refresh_cache: True 立即请求服务器（受限频限制），False 使用 OpenD 缓存

返回字段说明：
- power（购买力）: 按 50% 融资初始保证金率计算的近似值，建议用 get_max_trd_qtys 获取精确值
- total_assets: 总资产净值 = 证券资产净值 + 基金资产净值 + 债券资产净值
- market_val: 仅证券账户适用
- avl_withdrawal_cash: 仅证券账户适用
- currency: 仅综合证券账户、期货账户适用
- pl_ratio_avg_cost（持仓盈亏比/均价口径）: 百分比字段，20 实际对应 20%，期货不适用
- average_cost: 平均成本价（与 APP 一致），禁止使用 cost_price（摊薄成本）
- unrealized_pl: 未实现盈亏（均价口径），禁止使用 pl_val（摊薄成本口径）
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
    format_enum,
)


def get_portfolio(acc_id=None, market=None, trd_env=None, currency=None, security_firm=None, output_json=False):
    acc_id = acc_id or get_default_acc_id()
    trd_env = parse_trd_env(trd_env) if trd_env else get_default_trd_env()

    ctx = None
    try:
        ctx = create_trade_context(market, security_firm=parse_security_firm(security_firm))
        # 查询资金（refresh_cache=True 避免返回过时缓存数据，尤其模拟盘）
        query_kwargs = dict(trd_env=trd_env, acc_id=acc_id, refresh_cache=True)
        if currency:
            query_kwargs["currency"] = currency
        ret, acc_data = ctx.accinfo_query(**query_kwargs)
        check_ret(ret, acc_data, ctx, "查询账户资金")

        funds = {}
        if not is_empty(acc_data):
            row = acc_data.iloc[0] if hasattr(acc_data, "iloc") else acc_data
            total_assets = safe_float(safe_get(row, "total_assets", default=0))
            initial_margin = safe_float(safe_get(row, "initial_margin", default=0))
            available_funds_raw = safe_get(row, "available_funds", default="N/A")
            available_funds = safe_float(available_funds_raw)
            # available_funds 对部分账户类型返回 N/A，用 total_assets - initial_margin 计算
            # 仅在原始值为 'N/A' 或缺失时进行回退，避免将真实的 0 误识别为缺失
            if str(available_funds_raw) == "N/A" or available_funds_raw in (None, ""):
                available_funds = total_assets - initial_margin if initial_margin > 0 else total_assets
            funds = {
                "currency": safe_get(row, "currency", default="N/A"),
                "total_assets": total_assets,
                "cash": safe_float(safe_get(row, "cash", default=0)),
                "market_val": safe_float(safe_get(row, "market_val", default=0)),
                "long_mv": safe_float(safe_get(row, "long_mv", default=0)),
                "short_mv": safe_float(safe_get(row, "short_mv", default=0)),
                "frozen_cash": safe_float(safe_get(row, "frozen_cash", default=0)),
                "avl_withdrawal_cash": safe_float(safe_get(row, "avl_withdrawal_cash", default=0)),
                "power": safe_float(safe_get(row, "power", "buying_power", default=0)),
                "available_funds": available_funds,
                "initial_margin": initial_margin,
                "maintenance_margin": safe_float(safe_get(row, "maintenance_margin", default=0)),
                "risk_status": safe_get(row, "risk_status", default="N/A"),
                "us_cash": safe_float(safe_get(row, "us_cash", default=0)),
                "ca_cash": safe_float(safe_get(row, "ca_cash", default=0)),
            }

        # 查询持仓（refresh_cache=True 避免返回过时缓存数据）
        ret, pos_data = ctx.position_list_query(trd_env=trd_env, acc_id=acc_id, refresh_cache=True)
        check_ret(ret, pos_data, ctx, "查询持仓")

        positions = []
        if not is_empty(pos_data):
            for i in range(len(pos_data)):
                row = pos_data.iloc[i] if hasattr(pos_data, "iloc") else pos_data[i]
                positions.append({
                    "code": safe_get(row, "code", default=""),
                    "name": safe_get(row, "stock_name", default=""),
                    "qty": safe_float(safe_get(row, "qty", default=0)),
                    "can_sell_qty": safe_float(safe_get(row, "can_sell_qty", default=0)),
                    "average_cost": safe_float(safe_get(row, "average_cost", default=0)),
                    "nominal_price": safe_float(safe_get(row, "nominal_price", default=0)),
                    "market_val": safe_float(safe_get(row, "market_val", default=0)),
                    "unrealized_pl": safe_float(safe_get(row, "unrealized_pl", default=0)),
                    "pl_ratio_avg_cost": safe_float(safe_get(row, "pl_ratio_avg_cost", default=0)),
                    "realized_pl": safe_float(safe_get(row, "realized_pl", default=0)),
                    "today_pl_val": safe_float(safe_get(row, "today_pl_val", default=0)),
                })

        if output_json:
            print(json.dumps({"funds": funds, "positions": positions}, ensure_ascii=False))
        else:
            print("=" * 70)
            ccy_label = f"  货币: {funds.get('currency', 'N/A')}" if funds else ""
            print(f"账户概览 (环境: {format_enum(trd_env)}){ccy_label}")
            print("=" * 70)
            if funds:
                print(f"\n  总资产: {funds['total_assets']:.2f}  现金: {funds['cash']:.2f}  购买力: {funds['power']:.2f}")
                print(f"  持仓市值: {funds['market_val']:.2f}  可用资金: {funds['available_funds']:.2f}  冻结: {funds['frozen_cash']:.2f}")
            print(f"\n  {'持仓列表':=^66}")
            if positions:
                print(f"  {'代码':<12} {'名称':<10} {'数量':>8} {'均价':>10} {'市值':>12} {'盈亏%':>8}")
                print("  " + "-" * 66)
                for p in positions:
                    print(f"  {p['code']:<12} {p['name']:<10} {p['qty']:>8.0f} {p['average_cost']:>10.2f} {p['market_val']:>12.2f} {p['pl_ratio_avg_cost']:>8.2f}%")
            else:
                print("  暂无持仓")
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
    parser = argparse.ArgumentParser(description="获取持仓与资金")
    parser.add_argument("--acc-id", type=int, default=None, help="账户 ID")
    parser.add_argument("--market", choices=["US", "HK", "HKCC", "CN", "SG"], default=None, help="交易市场")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境")
    parser.add_argument("--currency", choices=["HKD", "USD", "CNH", "JPY", "AUD", "CAD", "MYR", "SGD"], default=None,
                        help="货币类型（默认由服务端决定）")
    parser.add_argument("--security-firm",
                        choices=["FUTUSECURITIES", "FUTUINC", "FUTUSG", "FUTUAU", "FUTUCA", "FUTUJP", "FUTUMY"],
                        default=None, help="券商标识")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_portfolio(acc_id=args.acc_id, market=args.market, trd_env=args.trd_env,
                  currency=args.currency, security_firm=args.security_firm, output_json=args.output_json)

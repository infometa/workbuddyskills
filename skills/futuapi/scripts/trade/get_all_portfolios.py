#!/usr/bin/env python3
"""
查询所有账户的资金与持仓

功能：遍历所有交易账户，查询每个账户的资金和持仓信息
用法：python get_all_portfolios.py [--trd-env SIMULATE] [--acc-id 6795352] [--json]

参数说明：
- --trd-env: 交易环境过滤，SIMULATE 或 REAL（默认显示全部）
- --acc-id: 指定账户 ID，只查询该账户
- --json: JSON 格式输出
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
    check_ret,
    safe_close,
    is_empty,
    safe_get,
    safe_float,
    safe_int,
    format_enum,
    _sdk_supports_ai_type,
    RET_OK,
    TrdEnv,
    TrdMarket,
    SecurityFirm,
)


# 所有券商枚举
ALL_FIRMS = [
    SecurityFirm.FUTUSECURITIES,
    SecurityFirm.FUTUINC,
    SecurityFirm.FUTUSG,
    SecurityFirm.FUTUAU,
    SecurityFirm.FUTUCA,
    SecurityFirm.FUTUJP,
    SecurityFirm.FUTUMY,
]


def get_all_accounts(host, port):
    """获取所有账户列表（去重）"""
    from common import get_opend_config, _check_opend_alive, OpenSecTradeContext
    seen = set()
    accounts = []
    for firm in ALL_FIRMS:
        try:
            kwargs = dict(host=host, port=port, filter_trdmarket=TrdMarket.NONE, security_firm=firm)
            if _sdk_supports_ai_type:
                kwargs["ai_type"] = 1
            ctx = OpenSecTradeContext(**kwargs)
            try:
                ret, data = ctx.get_acc_list()
            finally:
                safe_close(ctx)
            if ret == RET_OK and not is_empty(data):
                for i in range(len(data)):
                    row = data.iloc[i]
                    acc_id = safe_int(safe_get(row, "acc_id", default=0))
                    if acc_id and acc_id not in seen:
                        seen.add(acc_id)
                        accounts.append({
                            "acc_id": acc_id,
                            "trd_env": safe_get(row, "trd_env", default="N/A"),
                            "acc_type": safe_get(row, "acc_type", default="N/A"),
                            "trdmarket_auth": safe_get(row, "trdmarket_auth", default=[]),
                        })
        except Exception:
            continue
    return accounts


def query_portfolio(host, port, acc_id, trd_env):
    """查询单个账户的资金与持仓"""
    from common import OpenSecTradeContext
    kwargs = dict(host=host, port=port, filter_trdmarket=TrdMarket.NONE)
    if _sdk_supports_ai_type:
        kwargs["ai_type"] = 1
    ctx = OpenSecTradeContext(**kwargs)
    try:
        # 资金
        ret, acc_data = ctx.accinfo_query(trd_env=trd_env, acc_id=acc_id)
        funds = {}
        if ret == RET_OK and not is_empty(acc_data):
            row = acc_data.iloc[0]
            funds = {
                "total_assets": safe_float(safe_get(row, "total_assets", default=0)),
                "cash": safe_float(safe_get(row, "cash", default=0)),
                "market_val": safe_float(safe_get(row, "market_val", default=0)),
                "us_cash": safe_float(safe_get(row, "us_cash", default=0)),
                "hk_cash": safe_float(safe_get(row, "hk_cash", default=0)),
                "cn_cash": safe_float(safe_get(row, "cn_cash", default=0)),
                "frozen_cash": safe_float(safe_get(row, "frozen_cash", default=0)),
                "power": safe_float(safe_get(row, "power", default=0)),
            }

        # 持仓
        ret, pos_data = ctx.position_list_query(trd_env=trd_env, acc_id=acc_id)
        positions = []
        if ret == RET_OK and not is_empty(pos_data):
            for i in range(len(pos_data)):
                row = pos_data.iloc[i]
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
                })

        return funds, positions
    finally:
        safe_close(ctx)


def main():
    parser = argparse.ArgumentParser(description="查询所有账户的资金与持仓")
    parser.add_argument("--acc-id", type=int, default=None, help="指定账户 ID")
    parser.add_argument("--trd-env", choices=["REAL", "SIMULATE"], default=None, help="交易环境过滤")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()

    from common import get_opend_config, _check_opend_alive
    host, port = get_opend_config()
    _check_opend_alive(host, port)

    # 获取账户列表
    accounts = get_all_accounts(host, port)

    # 过滤
    if args.trd_env:
        accounts = [a for a in accounts if a["trd_env"] == args.trd_env]
    if args.acc_id:
        accounts = [a for a in accounts if a["acc_id"] == args.acc_id]

    if not accounts:
        if args.output_json:
            print(json.dumps({"accounts": []}, ensure_ascii=False))
        else:
            print("未找到匹配的账户")
        return

    results = []
    for acc in accounts:
        acc_id = acc["acc_id"]
        trd_env_str = acc["trd_env"]
        trd_env = TrdEnv.REAL if trd_env_str == "REAL" else TrdEnv.SIMULATE
        funds, positions = query_portfolio(host, port, acc_id, trd_env)
        results.append({
            "acc_id": acc_id,
            "trd_env": trd_env_str,
            "acc_type": acc["acc_type"],
            "trdmarket_auth": acc["trdmarket_auth"],
            "funds": funds,
            "positions": positions,
        })

    if args.output_json:
        print(json.dumps({"accounts": results}, ensure_ascii=False))
    else:
        for r in results:
            env_label = "模拟" if r["trd_env"] == "SIMULATE" else "实盘"
            markets = r["trdmarket_auth"] if isinstance(r["trdmarket_auth"], list) else [r["trdmarket_auth"]]
            market_str = ",".join(str(m) for m in markets)
            print(f"\n{'='*60}")
            print(f"账户 {r['acc_id']} | {env_label} | {r['acc_type']} | 市场: {market_str}")
            print(f"{'='*60}")
            f = r["funds"]
            if f:
                print(f"  总资产: {f['total_assets']:,.2f}  现金: {f['cash']:,.2f}  持仓市值: {f['market_val']:,.2f}")
            if r["positions"]:
                print(f"  {'代码':<25} {'名称':<12} {'数量':>8} {'现价':>10} {'市值':>12} {'盈亏%':>8}")
                print("  " + "-" * 75)
                for p in r["positions"]:
                    print(f"  {p['code']:<25} {p['name']:<12} {p['qty']:>8.0f} {p['nominal_price']:>10.3f} {p['market_val']:>12.2f} {p['pl_ratio_avg_cost']:>8.2f}%")
            else:
                print("  无持仓")


if __name__ == "__main__":
    main()

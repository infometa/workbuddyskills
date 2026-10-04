
#!/usr/bin/env python3
"""
经营分析计算脚本

输入（stdin JSON）：
{
  "c4_supply_raw": [{"name": "...", "amount": 1000000}],
  "c5_customer_raw": [{"name": "...", "amount": 2000000}],
  "c6_tax_raw": {"book_revenue": 10000000, "declared_revenue": 9700000},
  "c7_production_raw": {"production": 120000, "sales": 115000, "avg_inventory": 5000000, "daily_cogs": 50000},
  "c8_cashflow_raw": {"transactions": [{"date": "...", "type": "income|expense", "amount": ..., "counterparty": "..."}]}
}

输出（stdout JSON）：
{
  "c4_supply": {"total": "62.3%", "assessment": "偏高"},
  "c5_customer": {"total": "69.8%", "assessment": "偏高"},
  "c6_tax": {"diffRate": "3.2%", "assessment": "可接受"},
  "c7_production": {"productionSalesRate": "95.8%", "inventoryTurnoverDays": "45"},
  "c8_cashflow": {"metrics": [...], "topCounterparties": [...]}
}
"""

import json
import sys
from collections import defaultdict


def calculate_concentration(items: list) -> dict:
    """计算集中度：前五合计占比 + 评估"""
    if not items:
        return {"total": "0%", "assessment": "数据不足"}

    total_amount = sum(item.get("amount", 0) for item in items)
    if total_amount == 0:
        return {"total": "0%", "assessment": "数据不足"}

    # 按金额排序取前5
    sorted_items = sorted(items, key=lambda x: x.get("amount", 0), reverse=True)[:5]
    top5_amount = sum(item.get("amount", 0) for item in sorted_items)
    ratio = top5_amount / total_amount * 100

    if ratio > 60:
        assessment = "偏高"
    elif ratio >= 40:
        assessment = "适中"
    else:
        assessment = "分散"

    return {"total": f"{ratio:.1f}%", "assessment": assessment}


def calculate_tax_consistency(book_revenue: float, declared_revenue: float) -> dict:
    """计算账税差异率"""
    if book_revenue == 0:
        return {"diffRate": "N/A", "assessment": "数据不足"}

    diff_rate = abs(book_revenue - declared_revenue) / book_revenue * 100

    if diff_rate < 5:
        assessment = "可接受"
    elif diff_rate < 10:
        assessment = "需关注"
    elif diff_rate < 20:
        assessment = "异常"
    else:
        assessment = "严重异常"

    return {"diffRate": f"{diff_rate:.1f}%", "assessment": assessment}


def calculate_production_sales(production: float, sales: float, avg_inventory: float, daily_cogs: float) -> dict:
    """计算产销率和库存周转天数"""
    result = {}

    if production > 0:
        ps_rate = sales / production * 100
        result["productionSalesRate"] = f"{ps_rate:.1f}%"
    else:
        result["productionSalesRate"] = "N/A"

    if daily_cogs > 0:
        turnover_days = avg_inventory / daily_cogs
        result["inventoryTurnoverDays"] = f"{turnover_days:.0f}"
    else:
        result["inventoryTurnoverDays"] = "N/A"

    return result


def calculate_cashflow(transactions: list) -> dict:
    """计算流水统计指标"""
    if not transactions:
        return {"metrics": [], "topCounterparties": []}

    total_income = 0
    total_expense = 0
    income_by_counterparty = defaultdict(float)
    expense_by_counterparty = defaultdict(float)
    monthly_income = defaultdict(float)

    for tx in transactions:
        amount = tx.get("amount", 0)
        tx_type = tx.get("type", "")
        counterparty = tx.get("counterparty", "未知")
        date = tx.get("date", "")
        month = date[:7] if date else "unknown"

        if tx_type == "income":
            total_income += amount
            income_by_counterparty[counterparty] += amount
            monthly_income[month] += amount
        elif tx_type == "expense":
            total_expense += amount
            expense_by_counterparty[counterparty] += amount

    net_flow = total_income - total_expense
    tx_count = len(transactions)

    # 进账集中度（最大进账方占比）
    max_income = max(income_by_counterparty.values()) if income_by_counterparty else 0
    income_concentration = max_income / total_income if total_income > 0 else 0

    # 月度波动率
    if monthly_income:
        values = list(monthly_income.values())
        mean_val = sum(values) / len(values)
        if mean_val > 0:
            variance = sum((v - mean_val) ** 2 for v in values) / len(values)
            monthly_volatility = (variance ** 0.5) / mean_val
        else:
            monthly_volatility = 0
    else:
        monthly_volatility = 0

    # 支出收入比
    expense_income_ratio = total_expense / total_income if total_income > 0 else 0

    metrics = [
        {"label": "总进账", "value": f"{total_income:,.0f} 元"},
        {"label": "总出账", "value": f"{total_expense:,.0f} 元"},
        {"label": "净流量", "value": f"{net_flow:,.0f} 元"},
        {"label": "交易笔数", "value": f"{tx_count} 笔"},
        {"label": "进账集中度", "value": f"{income_concentration:.2f}"},
        {"label": "月度波动率", "value": f"{monthly_volatility:.2f}"},
        {"label": "支出收入比", "value": f"{expense_income_ratio:.2f}"},
    ]

    # TOP5 对手方
    top_income = sorted(income_by_counterparty.items(), key=lambda x: x[1], reverse=True)[:5]
    top_expense = sorted(expense_by_counterparty.items(), key=lambda x: x[1], reverse=True)[:5]

    top_counterparties = []
    for name, amount in top_income:
        top_counterparties.append({"direction": "收款", "name": name, "amount": f"{amount:,.0f} 元"})
    for name, amount in top_expense:
        top_counterparties.append({"direction": "付款", "name": name, "amount": f"{amount:,.0f} 元"})

    return {"metrics": metrics, "topCounterparties": top_counterparties}


def main():
    raw = json.loads(sys.stdin.read())

    result = {}

    # C4 供应集中度
    if raw.get("c4_supply_raw"):
        result["c4_supply"] = calculate_concentration(raw["c4_supply_raw"])

    # C5 客户集中度
    if raw.get("c5_customer_raw"):
        result["c5_customer"] = calculate_concentration(raw["c5_customer_raw"])

    # C6 账税一致
    if raw.get("c6_tax_raw"):
        tax = raw["c6_tax_raw"]
        result["c6_tax"] = calculate_tax_consistency(
            tax.get("book_revenue", 0),
            tax.get("declared_revenue", 0)
        )

    # C7 产销
    if raw.get("c7_production_raw"):
        prod = raw["c7_production_raw"]
        result["c7_production"] = calculate_production_sales(
            prod.get("production", 0),
            prod.get("sales", 0),
            prod.get("avg_inventory", 0),
            prod.get("daily_cogs", 0)
        )

    # C8 流水
    if raw.get("c8_cashflow_raw"):
        result["c8_cashflow"] = calculate_cashflow(
            raw["c8_cashflow_raw"].get("transactions", [])
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

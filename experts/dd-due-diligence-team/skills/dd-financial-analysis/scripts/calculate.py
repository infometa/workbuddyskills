"""对公信贷财务分析的唯一确定性计算引擎。"""

from __future__ import annotations

import copy
import json
import math
import os
import re
import sys
from datetime import date
from typing import Any, Optional


UNIT_FACTORS = {
    '元': 1.0,
    '人民币元': 1.0,
    '千元': 1_000.0,
    '人民币千元': 1_000.0,
    '万元': 10_000.0,
    '人民币万元': 10_000.0,
    '百万元': 1_000_000.0,
    '人民币百万元': 1_000_000.0,
    '亿元': 100_000_000.0,
    '人民币亿元': 100_000_000.0,
}

AMOUNT_TABLE_KEYS = (
    'balance_sheet',
    'opening_balance_sheet',
    'income_statement',
    'cash_flow',
    'financial_supplement',
    'opening_financial_supplement',
    'cross_validation',
)

UNITLESS_SUPPLEMENT_FIELDS = {
    'top_five_receivables_ratio',
    'receivables_over_one_year_ratio',
    'related_party_receivables_ratio',
    'finished_goods_inventory_ratio',
}

STATEMENT_FIELDS: dict[str, tuple[tuple[str, str], ...]] = {
    'balance_sheet': (
        # ── 流动资产（配平校验 BS-02 的被加项，顺序与报表列示一致）──
        ('cash_and_equivalents', '货币资金'),
        # 「以公允价值计量且其变动计入当期损益的金融资产」是旧准则叫法，二者同一项目；
        # 只保留新准则名称「交易性金融资产」，旧称在抽取侧作为其别名命中，避免重复计数
        ('trading_financial_assets', '交易性金融资产'),
        ('derivative_financial_assets', '衍生金融资产'),
        ('notes_receivable', '应收票据'),
        ('accounts_receivable', '应收账款'),
        ('receivables_financing', '应收款项融资'),
        ('prepaid_accounts', '预付款项'),
        ('other_receivables', '其他应收款'),
        ('inventory', '存货'),
        ('contract_assets', '合同资产'),
        ('assets_held_for_sale', '持有待售资产'),
        ('noncurrent_assets_due_within_one_year', '一年内到期的非流动资产'),
        ('other_current_assets', '其他流动资产'),
        ('current_assets', '流动资产合计'),
        # ── 非流动资产（BS-03 的被加项）──
        ('debt_investments', '债权投资'),
        ('other_debt_investments', '其他债权投资'),
        ('available_for_sale_financial_assets', '可供出售金融资产'),
        ('long_term_receivables', '长期应收款'),
        ('long_term_equity_investments', '长期股权投资'),
        ('other_equity_instrument_investments', '其他权益工具投资'),
        ('investment_property', '投资性房地产'),
        ('fixed_assets', '固定资产'),
        ('construction_in_progress', '在建工程'),
        ('productive_biological_assets', '生产性生物资产'),
        ('oil_and_gas_assets', '油气资产'),
        ('right_of_use_assets', '使用权资产'),
        ('intangible_assets', '无形资产'),
        ('development_expenditure', '开发支出'),
        ('goodwill', '商誉'),
        ('long_term_deferred_expenses', '长期待摊费用'),
        ('entrusted_loans', '委托贷款'),
        ('foreclosed_assets', '抵债资产'),
        ('deferred_tax_assets', '递延所得税资产'),
        ('other_non_current_assets', '其他非流动资产'),
        ('non_current_assets', '非流动资产合计'),
        ('total_assets', '资产总计'),
        # ── 流动负债（BS-05 的被加项）──
        ('short_term_borrowings', '短期借款'),
        ('fvtpl_financial_liabilities', '以公允价值计量且其变动计入当期损益的金融负债'),
        ('trading_financial_liabilities', '交易性金融负债'),
        ('derivative_financial_liabilities', '衍生金融负债'),
        ('notes_payable', '应付票据'),
        ('accounts_payable', '应付账款'),
        ('advances_from_customers', '预收账款'),
        ('contract_liabilities', '合同负债'),
        ('guarantee_deposits_received', '存入担保保证金'),
        ('financial_assets_sold_for_repurchase', '卖出回购金融资产款'),
        ('fees_and_commissions_payable', '应付手续费及佣金'),
        ('employee_benefits_payable', '应付职工薪酬'),
        ('taxes_payable', '应交税费'),
        ('guarantee_compensation_reserve', '担保赔偿准备'),
        ('short_term_liability_reserve', '短期责任准备金'),
        ('other_payables', '其他应付款'),
        ('liabilities_held_for_sale', '持有待售负债'),
        ('noncurrent_liabilities_due_within_one_year', '一年内到期的长期负债'),
        ('other_current_liabilities', '其他流动负债'),
        ('current_liabilities', '流动负债合计'),
        # ── 非流动负债（BS-06 的被加项）──
        ('long_term_borrowings', '长期借款'),
        ('bonds_payable', '应付债券'),
        ('lease_liabilities', '租赁负债'),
        ('long_term_payables', '长期应付款'),
        ('long_term_employee_benefits_payable', '长期应付职工薪酬'),
        ('provisions', '预计负债'),
        ('insurance_contract_reserve', '保险合同准备金'),
        ('deferred_income', '递延收益'),
        ('deferred_tax_liabilities', '递延所得税负债'),
        ('other_non_current_liabilities', '其他非流动负债'),
        ('non_current_liabilities', '非流动负债合计'),
        ('total_liabilities', '负债总计'),
        # ── 所有者权益（BS-07 的被加项；库存股为减项）──
        ('paid_in_capital', '实收资本（或股本）'),
        ('other_equity_instruments', '其他权益工具'),
        ('capital_reserve', '资本公积'),
        ('treasury_stock', '减：库存股'),
        ('other_comprehensive_income', '其他综合收益'),
        ('special_reserve', '专项储备'),
        ('surplus_reserve', '盈余公积'),
        ('general_risk_reserve', '一般风险准备'),
        ('retained_earnings', '未分配利润'),
        ('minority_interest', '少数股东权益'),
        ('total_equity', '所有者权益合计'),
        ('total_liabilities_and_equity', '负债和所有者权益总计'),
    ),
    'income_statement': (
        ('revenue', '营业总收入'),
        ('cost_of_revenue', '营业成本'),
        ('tax_surcharge', '税金及附加'),
        ('selling_expense', '销售费用'),
        ('admin_expense', '管理费用'),
        ('rd_expense', '研发费用'),
        ('finance_expense', '财务费用'),
        ('interest_expense', '利息支出'),
        ('interest_income', '利息收入'),
        ('asset_impairment_loss', '资产减值损失'),
        ('credit_impairment_loss', '信用减值损失'),
        ('investment_income', '投资收益'),
        ('fair_value_change_income', '公允价值变动收益'),
        ('asset_disposal_income', '资产处置收益'),
        ('other_income', '其他收益'),
        ('operating_profit', '营业利润'),
        ('non_operating_income', '营业外收入'),
        ('non_operating_expense', '营业外支出'),
        ('total_profit', '利润总额'),
        ('income_tax', '所得税费用'),
        ('net_profit', '净利润'),
    ),
    'cash_flow': (
        # ── 经营活动现金流入（CF-02 的被加项）──
        ('sales_cash_received', '销售商品、提供劳务收到的现金'),
        ('fvtpl_disposal_cash_received', '处置公允价值计量且其变动计入当期损益'),
        ('interest_fee_commission_received', '收取利息、手续费及佣金的现金'),
        ('net_increase_in_borrowing_funds', '拆入资金净增加额'),
        ('net_increase_in_repurchase_funds', '回购业务资金净增加额'),
        ('tax_refunds_received', '收到的税费返还'),
        ('other_operating_cash_received', '收到的其他与经营活动有关的现金'),
        ('operating_cash_inflow', '经营活动现金流入小计'),
        # ── 经营活动现金流出（CF-03 的被加项）──
        ('purchases_cash_paid', '购买商品、接受劳务支付的现金'),
        ('employee_cash_paid', '支付给职工以及为职工支付的现金'),
        ('taxes_cash_paid', '支付的各项税费'),
        ('other_operating_cash_paid', '支付的其他与经营活动有关的现金'),
        ('operating_cash_outflow', '经营活动现金流出小计'),
        ('operating_cash_flow', '经营活动产生的现金流量净额'),
        # ── 投资活动现金流入（CF-05 的被加项）──
        ('investment_recovered', '收回投资收到的现金'),
        ('investment_income_cash_received', '取得投资收益收到的现金'),
        ('subsidiary_acquisition_cash_received', '取得子公司及其他营业单位所收到的现金净额'),
        ('asset_disposal_cash_received', '处置固定资产、无形资产和其他长期资产收回的现金净额'),
        ('subsidiary_disposal_cash_received', '处置子公司及其他营业单位收到的现金净额'),
        ('other_investing_cash_received', '收到的其他与投资活动有关的现金'),
        ('investing_cash_inflow', '投资活动现金流入小计'),
        # ── 投资活动现金流出（CF-06 的被加项）──
        ('capital_expenditure', '购建固定资产、无形资产和其他长期资产支付的现金'),
        ('investments_paid', '投资支付的现金'),
        ('other_investing_cash_paid', '支付的其他与投资活动有关的现金'),
        ('investing_cash_outflow', '投资活动现金流出小计'),
        ('investing_cash_flow', '投资活动产生的现金流量净额'),
        # ── 筹资活动现金流入（CF-08 的被加项）──
        ('capital_contributions_received', '吸收投资收到的现金'),
        ('borrowings_received', '取得借款收到的现金'),
        ('bond_issuance_cash_received', '发行债券收到的现金'),
        ('other_financing_cash_received', '收到其他与筹资活动有关的现金'),
        ('financing_cash_inflow', '筹资活动现金流入小计'),
        # ── 筹资活动现金流出（CF-09 的被加项）──
        ('debt_repaid', '偿还债务支付的现金'),
        ('interest_dividends_paid', '分配股利、利润或偿付利息支付的现金'),
        ('other_financing_cash_paid', '支付的其他与筹资活动有关的现金'),
        ('financing_cash_outflow', '筹资活动现金流出小计'),
        ('financing_cash_flow', '筹资活动产生的现金流量净额'),
        # 汇率影响仍是报表列示项，但按新规则不参与 CF-10 现金净增加额配平
        ('exchange_effect', '汇率变动对现金及现金等价物的影响'),
        ('cash_change', '现金及现金等价物净增加额'),
        ('cash_begin', '期初现金及现金等价物余额'),
        ('cash_end', '期末现金及现金等价物余额'),
    ),
}

FACT_PREFIXES = {
    'balance_sheet': 'bs',
    'income_statement': 'inc',
    'cash_flow': 'cf',
    'financial_supplement': 'sup',
    'cross_validation': 'xv',
}

STANDARD_REPORT_METRIC_KEYS = (
    'debt_ratio', 'current_ratio', 'quick_ratio', 'interest_coverage',
    'operating_cash_ratio', 'total_asset_turnover', 'current_asset_turnover',
    'inventory_turnover', 'receivable_turnover', 'gross_profit_margin',
    'net_profit_margin', 'roa', 'roe', 'revenue_growth', 'net_profit_growth',
)

EQ_TOLERANCE_YUAN = 1.0
PERCENTAGE_FIELDS = UNITLESS_SUPPLEMENT_FIELDS
MISSING_TEXT_SENTINELS = {
    '未明确', '未披露', '文档未披露', '未知', '不详', '待补充', 'n/a', 'na', 'null',
}
STATEMENT_SCOPE_ALIASES = {
    '合并': '合并',
    '合并口径': '合并',
    '合并报表': '合并',
    '母公司': '母公司',
    '母公司口径': '母公司',
    '单体': '单体',
    '单体口径': '单体',
}


def _num(table: dict[str, Any], key: str) -> Optional[float]:
    value = table.get(key) if isinstance(table, dict) else None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _round(value: Optional[float], digits: int = 6) -> Optional[float]:
    return None if value is None else round(value, digits)


def _safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _safe_positive_div(
    numerator: Optional[float], denominator: Optional[float]
) -> Optional[float]:
    """Return a ratio only when the economic denominator is strictly positive."""
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _average(opening: Optional[float], closing: Optional[float]) -> Optional[float]:
    if opening is None or closing is None:
        return None
    return (opening + closing) / 2


def _required_sum(*values: Optional[float]) -> Optional[float]:
    if any(value is None for value in values):
        return None
    return sum(value for value in values if value is not None)


def _difference_rate(reported: Optional[float], reference: Optional[float]) -> Optional[float]:
    if reported is None or reference is None or reference == 0:
        return None
    return (reported - reference) / abs(reference)


def _normalize_note_details(
    details: Any, currency: str, statement_scope: str
) -> dict[str, Any]:
    if details is None:
        return {}
    if not isinstance(details, dict):
        raise ValueError('note_details must be an object')
    normalized: dict[str, Any] = {}
    for fact_key, detail in details.items():
        if not isinstance(fact_key, str) or not fact_key.startswith(('bs_', 'inc_', 'cf_')):
            raise ValueError(f'note_details key must use bs_/inc_/cf_ prefix: {fact_key!r}')
        if not isinstance(detail, dict):
            raise ValueError(f'note_details.{fact_key} must be an object')
        source_unit = detail.get('source_unit')
        if source_unit not in UNIT_FACTORS:
            raise ValueError(f'note_details.{fact_key}.source_unit is required and must be supported')
        if detail.get('currency') != currency:
            raise ValueError(f'note_details.{fact_key}.currency must match the period currency')
        detail_scope = STATEMENT_SCOPE_ALIASES.get(str(detail.get('statement_scope') or '').strip())
        if detail_scope != statement_scope:
            raise ValueError(f'note_details.{fact_key}.statement_scope must match the period scope')
        source_ref = detail.get('source_ref')
        if not source_ref or not isinstance(source_ref, (str, dict)):
            raise ValueError(f'note_details.{fact_key}.source_ref must be non-empty')
        components = detail.get('components')
        if not isinstance(components, list) or not components:
            raise ValueError(f'note_details.{fact_key}.components must be a non-empty array')
        normalized_components: list[dict[str, Any]] = []
        component_names: set[str] = set()
        for index, component in enumerate(components):
            if not isinstance(component, dict):
                raise ValueError(f'note_details.{fact_key}.components[{index}] must be an object')
            name = component.get('name')
            amount = component.get('amount')
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f'note_details.{fact_key}.components[{index}].name is required')
            normalized_name = name.strip()
            if normalized_name in component_names:
                raise ValueError(f'note_details.{fact_key} 存在重复明细名称：{normalized_name}')
            component_names.add(normalized_name)
            if isinstance(amount, bool) or not isinstance(amount, (int, float)):
                raise ValueError(f'note_details.{fact_key}.components[{index}].amount must be numeric')
            if not math.isfinite(float(amount)):
                raise ValueError(f'note_details.{fact_key}.components[{index}].amount must be finite')
            normalized_components.append({
                'name': normalized_name,
                'amount': float(amount) * UNIT_FACTORS[source_unit],
                'unit': '元',
            })
        raw_text = detail.get('raw_text')
        if raw_text is not None and not isinstance(raw_text, str):
            raise ValueError(f'note_details.{fact_key}.raw_text must be a string or null')
        normalized[fact_key] = {
            'source_unit': source_unit,
            'currency': currency,
            'statement_scope': detail_scope,
            'source_ref': copy.deepcopy(source_ref),
            'raw_text': raw_text,
            'components': normalized_components,
        }
    return normalized


def normalize_period(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError('period must be an object')
    source_unit = data.get('source_unit')
    if not isinstance(source_unit, str) or not source_unit.strip():
        raise ValueError('每个期间必须明确 source_unit，禁止默认按元处理')
    if source_unit not in UNIT_FACTORS:
        raise ValueError(f'unsupported source_unit: {source_unit!r}')
    currency = data.get('currency')
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError('每个期间必须明确 currency')
    if currency.strip().upper() != 'CNY':
        raise ValueError('currency 必须明确为 CNY；缺失或其他币种不得直接进入本人民币口径模型')
    statement_scope = data.get('statement_scope')
    if not isinstance(statement_scope, str) or not statement_scope.strip():
        raise ValueError('每个期间必须明确 statement_scope（合并/母公司等）')
    normalized_scope = STATEMENT_SCOPE_ALIASES.get(statement_scope.strip())
    if normalized_scope is None:
        raise ValueError('statement_scope 必须明确为合并、母公司或单体口径')
    period_type = data.get('period_type')
    if period_type not in {'annual', 'interim'}:
        raise ValueError('period_type 必须为 annual 或 interim')
    period_role = data.get('period_role')
    if not isinstance(period_role, str) or not period_role.strip():
        raise ValueError('每个期间必须明确 period_role')
    period_days = data.get('period_days')
    if isinstance(period_days, bool) or not isinstance(period_days, int):
        raise ValueError('每个期间必须提供整数 period_days')
    if not 1 <= period_days <= 366:
        raise ValueError('period_days 必须在 1 至 366 之间')
    period_start_raw = data.get('period_start')
    period_end_raw = data.get('period_end')
    if not isinstance(period_start_raw, str) or not isinstance(period_end_raw, str):
        raise ValueError('每个期间必须提供 ISO 日期 period_start 和 period_end')
    try:
        period_start = date.fromisoformat(period_start_raw)
        period_end = date.fromisoformat(period_end_raw)
    except ValueError as exc:
        raise ValueError('period_start/period_end 必须为合法 YYYY-MM-DD 日期') from exc
    if period_end < period_start:
        raise ValueError('period_end 不得早于 period_start')
    actual_period_days = (period_end - period_start).days + 1
    if period_days != actual_period_days:
        raise ValueError(
            f'period_days 与起止日不一致：应为 {actual_period_days}，实际为 {period_days}'
        )

    table_units = data.get('table_units') or {}
    if not isinstance(table_units, dict):
        raise ValueError('table_units must be an object')
    for table_key, table_unit in table_units.items():
        if table_key not in AMOUNT_TABLE_KEYS:
            raise ValueError(f'unsupported table_units key: {table_key!r}')
        if table_unit not in UNIT_FACTORS:
            raise ValueError(f'unsupported table unit for {table_key}: {table_unit!r}')
    if data.get('cross_validation') and 'cross_validation' not in table_units:
        raise ValueError('提供 cross_validation 时必须明确 table_units.cross_validation')

    normalized = copy.deepcopy(data)
    normalized.pop('comparative_periods', None)
    normalized_units: dict[str, str] = {}
    for table_key in AMOUNT_TABLE_KEYS:
        table = normalized.get(table_key)
        if table is None:
            normalized[table_key] = {}
            continue
        if not isinstance(table, dict):
            raise ValueError(f'{table_key} must be an object')
        table_unit = table_units.get(table_key, source_unit)
        normalized_units[table_key] = table_unit
        factor = UNIT_FACTORS[table_unit]
        for key, value in table.items():
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f'{table_key}.{key} must be a number or null')
            if not math.isfinite(float(value)):
                raise ValueError(f'{table_key}.{key} must be finite')
            if table_key in {'financial_supplement', 'opening_financial_supplement'} and key in PERCENTAGE_FIELDS:
                percentage = float(value)
                if not 0 <= percentage <= 1:
                    raise ValueError(f'{table_key}.{key} 必须使用 0 至 1 的小数比例')
                table[key] = percentage
            else:
                table[key] = float(value) * factor

    normalized['source_unit'] = source_unit
    normalized['currency'] = 'CNY'
    normalized['statement_scope'] = normalized_scope
    normalized['period_role'] = period_role.strip()
    normalized['period_start'] = period_start.isoformat()
    normalized['period_end'] = period_end.isoformat()
    normalized['table_units'] = normalized_units
    normalized['_table_rounding_tolerance_yuan'] = {
        table_key: max(EQ_TOLERANCE_YUAN, UNIT_FACTORS[unit] * 0.02)
        for table_key, unit in normalized_units.items()
    }
    normalized['note_details'] = _normalize_note_details(
        data.get('note_details'), 'CNY', normalized_scope
    )
    statement_units = [
        normalized_units.get(table_key, source_unit)
        for table_key in ('balance_sheet', 'opening_balance_sheet', 'income_statement', 'cash_flow')
    ]
    normalized['_rounding_tolerance_yuan'] = max(
        EQ_TOLERANCE_YUAN,
        max(UNIT_FACTORS[unit] for unit in statement_units) * 0.02,
    )
    normalized['unit'] = '元'
    return normalized


def _metric(
    category: str,
    name_cn: str,
    formula: str,
    value: Optional[float],
    inputs: dict[str, Optional[float]],
    value_type: str = 'ratio',
    note: Optional[str] = None,
) -> dict[str, Any]:
    rounded_inputs = {key: _round(item, 2) for key, item in inputs.items()}
    return {
        'category': category,
        'name_cn': name_cn,
        'formula': formula,
        'value': _round(value, 2 if value_type == 'amount' else 6),
        'value_type': value_type,
        'computable': value is not None,
        'inputs': rounded_inputs,
        'note': note,
        'uncomputable_reason': None if value is not None else '原始字段缺失、分母为零或分母不符合经济有效域',
    }


def compute_metrics(data: dict[str, Any], comparison: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    bs = data.get('balance_sheet') or {}
    opening = data.get('opening_balance_sheet') or {}
    inc = data.get('income_statement') or {}
    cf = data.get('cash_flow') or {}
    supplement = data.get('financial_supplement') or {}
    opening_supplement = data.get('opening_financial_supplement') or {}
    cross = data.get('cross_validation') or {}

    current_assets = _num(bs, 'current_assets')
    inventory = _num(bs, 'inventory')
    prepaid = _num(bs, 'prepaid_accounts')
    cash = _num(bs, 'cash_and_equivalents')
    trading_assets = _num(bs, 'trading_financial_assets')
    current_liabilities = _num(bs, 'current_liabilities')
    total_assets = _num(bs, 'total_assets')
    total_liabilities = _num(bs, 'total_liabilities')
    total_equity = _num(bs, 'total_equity')
    intangible_assets = _num(bs, 'intangible_assets')
    revenue = _num(inc, 'revenue')
    cost = _num(inc, 'cost_of_revenue')
    net_profit = _num(inc, 'net_profit')
    total_profit = _num(inc, 'total_profit')
    interest_expense = _num(inc, 'interest_expense')
    rd_expense = _num(inc, 'rd_expense')
    depreciation_and_amortization = _num(supplement, 'depreciation_and_amortization')
    operating_cash_flow = _num(cf, 'operating_cash_flow')

    avg_receivables = _average(_num(opening, 'accounts_receivable'), _num(bs, 'accounts_receivable'))
    avg_inventory = _average(_num(opening, 'inventory'), inventory)
    avg_current_assets = _average(_num(opening, 'current_assets'), current_assets)
    avg_total_assets = _average(_num(opening, 'total_assets'), total_assets)
    avg_fixed_assets = _average(_num(opening, 'fixed_assets'), _num(bs, 'fixed_assets'))
    avg_equity = _average(_num(opening, 'total_equity'), total_equity)
    avg_payables = _average(_num(opening, 'accounts_payable'), _num(bs, 'accounts_payable'))
    avg_cash = _average(_num(opening, 'cash_and_equivalents'), cash)
    avg_interest_debt = _average(
        _num(opening_supplement, 'interest_bearing_debt'),
        _num(supplement, 'interest_bearing_debt'),
    )

    quick_assets = _required_sum(current_assets, -inventory if inventory is not None else None, -prepaid if prepaid is not None else None)
    cash_assets = _required_sum(cash, trading_assets)
    gross_profit = None if revenue is None or cost is None else revenue - cost
    ebit = None if total_profit is None or interest_expense is None else total_profit + interest_expense
    ebitda = (
        None
        if total_profit is None
        or interest_expense is None
        or depreciation_and_amortization is None
        else total_profit + interest_expense + depreciation_and_amortization
    )
    cost_expenses = _required_sum(
        cost,
        _num(inc, 'selling_expense'),
        _num(inc, 'admin_expense'),
        _num(inc, 'finance_expense'),
    )
    tangible_net_assets = None if total_equity is None or intangible_assets is None else total_equity - intangible_assets

    metrics: dict[str, Any] = {}

    def add(
        key: str,
        category: str,
        name: str,
        formula: str,
        value: Optional[float],
        inputs: dict[str, Optional[float]],
        value_type: str = 'ratio',
        note: Optional[str] = None,
    ) -> None:
        metrics[key] = _metric(category, name, formula, value, inputs, value_type, note)

    gross_profit_margin = _safe_positive_div(gross_profit, revenue)
    prior_inc = (comparison or {}).get('income_statement') or {}
    prior_revenue = _num(prior_inc, 'revenue')
    prior_cost = _num(prior_inc, 'cost_of_revenue')
    prior_gross_profit = None if prior_revenue is None or prior_cost is None else prior_revenue - prior_cost
    prior_gross_profit_margin = _safe_positive_div(prior_gross_profit, prior_revenue)
    gross_profit_margin_change = (
        None
        if gross_profit_margin is None or prior_gross_profit_margin is None
        else gross_profit_margin - prior_gross_profit_margin
    )

    add('gross_profit_margin', '盈利能力', '销售毛利率', '(营业收入-营业成本)/营业收入', gross_profit_margin, {'gross_profit': gross_profit, 'revenue': revenue}, 'percentage')
    add('gross_profit_margin_change', '盈利能力', '销售毛利率变动', '本期销售毛利率-可比期销售毛利率', gross_profit_margin_change, {'current_gross_profit_margin': gross_profit_margin, 'comparison_gross_profit_margin': prior_gross_profit_margin}, 'percentage', '行业正负2个标准差规则应对毛利率变动进行比较')
    add('net_profit_margin', '盈利能力', '销售净利率', '净利润/营业收入', _safe_positive_div(net_profit, revenue), {'net_profit': net_profit, 'revenue': revenue}, 'percentage')
    add('roa', '盈利能力', '总资产收益率（ROA）', '净利润/平均总资产', _safe_positive_div(net_profit, avg_total_assets), {'net_profit': net_profit, 'average_total_assets': avg_total_assets}, 'percentage')
    add('roe', '盈利能力', '净资产收益率（ROE）', '净利润/平均净资产', _safe_positive_div(net_profit, avg_equity), {'net_profit': net_profit, 'average_equity': avg_equity}, 'percentage', '平均净资产非正时不计算')
    add('cost_expense_profit_ratio', '盈利能力', '成本费用利润率', '净利润/(营业成本+销售费用+管理费用+财务费用)', _safe_positive_div(net_profit, cost_expenses), {'net_profit': net_profit, 'cost_expenses': cost_expenses}, 'percentage')

    receivable_turnover = _safe_positive_div(revenue, avg_receivables)
    inventory_turnover = _safe_positive_div(cost, avg_inventory)
    purchases = _num(supplement, 'purchases')
    payables_turnover = _safe_positive_div(purchases, avg_payables)
    period_days = float(data['period_days'])
    receivable_days = _safe_positive_div(period_days, receivable_turnover)
    inventory_days = _safe_positive_div(period_days, inventory_turnover)
    payables_days = _safe_positive_div(period_days, payables_turnover)
    cash_conversion_cycle = None
    if None not in (receivable_days, inventory_days, payables_days):
        cash_conversion_cycle = receivable_days + inventory_days - payables_days

    add('receivable_turnover', '营运能力', '应收账款周转率', '营业收入/平均应收账款', receivable_turnover, {'revenue': revenue, 'average_receivables': avg_receivables}, 'multiple')
    add('receivable_days', '营运能力', '应收账款周转天数（DSO）', '报告期天数/应收账款周转率', receivable_days, {'period_days': period_days, 'receivable_turnover': receivable_turnover}, 'days')
    add('inventory_turnover', '营运能力', '存货周转率', '营业成本/平均存货', inventory_turnover, {'cost_of_revenue': cost, 'average_inventory': avg_inventory}, 'multiple')
    add('inventory_days', '营运能力', '存货周转天数（DIO）', '报告期天数/存货周转率', inventory_days, {'period_days': period_days, 'inventory_turnover': inventory_turnover}, 'days')
    add('current_asset_turnover', '营运能力', '流动资产周转率', '营业收入/平均流动资产', _safe_positive_div(revenue, avg_current_assets), {'revenue': revenue, 'average_current_assets': avg_current_assets}, 'multiple')
    add('total_asset_turnover', '营运能力', '总资产周转率', '营业收入/平均总资产', _safe_positive_div(revenue, avg_total_assets), {'revenue': revenue, 'average_total_assets': avg_total_assets}, 'multiple')
    add('fixed_asset_turnover', '营运能力', '固定资产周转率', '营业收入/平均固定资产', _safe_positive_div(revenue, avg_fixed_assets), {'revenue': revenue, 'average_fixed_assets': avg_fixed_assets}, 'multiple')
    add('payables_days', '营运能力', '应付账款周转天数（DPO）', '报告期天数/(采购额/平均应付账款)', payables_days, {'period_days': period_days, 'purchases': purchases, 'average_payables': avg_payables}, 'days', '采购额缺失时不以营业成本替代')
    add('cash_conversion_cycle', '营运能力', '现金转换周期', 'DSO+DIO-DPO', cash_conversion_cycle, {'receivable_days': receivable_days, 'inventory_days': inventory_days, 'payables_days': payables_days}, 'days')

    add('current_ratio', '偿债能力', '流动比率', '流动资产/流动负债', _safe_positive_div(current_assets, current_liabilities), {'current_assets': current_assets, 'current_liabilities': current_liabilities}, 'multiple')
    add('quick_ratio', '偿债能力', '速动比率', '(流动资产-存货-预付款项)/流动负债', _safe_positive_div(quick_assets, current_liabilities), {'quick_assets': quick_assets, 'current_liabilities': current_liabilities}, 'multiple')
    add('cash_ratio', '偿债能力', '现金比率', '(货币资金+交易性金融资产)/流动负债', _safe_positive_div(cash_assets, current_liabilities), {'cash_assets': cash_assets, 'current_liabilities': current_liabilities}, 'multiple')
    add('working_capital', '偿债能力', '营运资金', '流动资产-流动负债', None if current_assets is None or current_liabilities is None else current_assets - current_liabilities, {'current_assets': current_assets, 'current_liabilities': current_liabilities}, 'amount')
    add('debt_ratio', '偿债能力', '资产负债率', '负债合计/资产总计', _safe_positive_div(total_liabilities, total_assets), {'total_liabilities': total_liabilities, 'total_assets': total_assets}, 'percentage')
    add('debt_to_equity', '偿债能力', '产权比率', '负债合计/所有者权益', _safe_positive_div(total_liabilities, total_equity), {'total_liabilities': total_liabilities, 'total_equity': total_equity}, 'multiple', '所有者权益非正时不计算')
    add('interest_coverage', '偿债能力', '利息保障倍数', '(利润总额+利息支出)/利息支出', _safe_positive_div(ebit, interest_expense), {'ebit': ebit, 'interest_expense': interest_expense}, 'multiple')
    add('ebitda_interest_coverage', '偿债能力', 'EBITDA 利息保障倍数', '(利润总额+利息支出+折旧摊销)/利息支出', _safe_positive_div(ebitda, interest_expense), {'total_profit': total_profit, 'interest_expense': interest_expense, 'depreciation_and_amortization': depreciation_and_amortization}, 'multiple', '仅在折旧摊销和利息支出均有可靠来源时计算')
    add('equity_multiplier', '偿债能力', '权益乘数', '资产总计/所有者权益', _safe_positive_div(total_assets, total_equity), {'total_assets': total_assets, 'total_equity': total_equity}, 'multiple', '所有者权益非正时不计算')
    add('debt_to_tangible_net_assets', '偿债能力', '负债与有形净资产比率', '负债合计/(净资产-无形资产)', _safe_positive_div(total_liabilities, tangible_net_assets), {'total_liabilities': total_liabilities, 'tangible_net_assets': tangible_net_assets}, 'multiple', '有形净资产非正时不计算')

    prior_bs = (comparison or {}).get('balance_sheet') or {}
    prior_net_profit = _num(prior_inc, 'net_profit')
    prior_receivables = _num(prior_bs, 'accounts_receivable')
    prior_assets = _num(prior_bs, 'total_assets')
    prior_equity = _num(prior_bs, 'total_equity')
    add('revenue_growth', '成长能力', '营业收入增长率', '(本期营业收入-上期营业收入)/|上期营业收入|', _difference_rate(revenue, prior_revenue), {'current_revenue': revenue, 'previous_revenue': prior_revenue}, 'percentage')
    add('net_profit_growth', '成长能力', '净利润增长率', '(本期净利润-上期净利润)/|上期净利润|', _difference_rate(net_profit, prior_net_profit), {'current_net_profit': net_profit, 'previous_net_profit': prior_net_profit}, 'percentage', '亏损基期使用绝对值分母以保持改善/恶化方向')
    add('total_asset_growth', '成长能力', '总资产增长率', '(期末总资产-上期总资产)/|上期总资产|', _difference_rate(total_assets, prior_assets), {'current_total_assets': total_assets, 'previous_total_assets': prior_assets}, 'percentage')
    add('capital_accumulation', '成长能力', '资本积累率', '(期末净资产-上期净资产)/|上期净资产|', _difference_rate(total_equity, prior_equity), {'current_equity': total_equity, 'previous_equity': prior_equity}, 'percentage')
    add('accounts_receivable_growth', '成长能力', '应收账款增长率', '(本期应收账款-上期应收账款)/|上期应收账款|', _difference_rate(_num(bs, 'accounts_receivable'), prior_receivables), {'current_receivables': _num(bs, 'accounts_receivable'), 'previous_receivables': prior_receivables}, 'percentage')
    add('rd_expense_ratio', '成长能力', '研发投入占比', '研发费用/营业收入', _safe_positive_div(rd_expense, revenue), {'rd_expense': rd_expense, 'revenue': revenue}, 'percentage')
    revenue_growth_value = metrics['revenue_growth']['value']
    net_profit_growth_value = metrics['net_profit_growth']['value']
    growth_divergence = None
    if revenue_growth_value is not None and revenue_growth_value > 0 and net_profit_growth_value is not None:
        growth_divergence = (net_profit_growth_value - revenue_growth_value) / revenue_growth_value
    add('profit_revenue_growth_divergence', '成长能力', '收入利润增速偏离度', '(净利润增长率-营业收入增长率)/营业收入增长率', growth_divergence, {'net_profit_growth': net_profit_growth_value, 'revenue_growth': revenue_growth_value}, 'percentage', '仅在营业收入增长率为正时计算，避免零或负基数失真')

    sales_cash_received = _num(cf, 'sales_cash_received')
    capital_expenditure = _num(cf, 'capital_expenditure')
    add('operating_cash_ratio', '现金流', '现金流动负债比率', '经营活动现金流量净额/流动负债', _safe_div(operating_cash_flow, current_liabilities), {'operating_cash_flow': operating_cash_flow, 'current_liabilities': current_liabilities}, 'percentage')
    add('cash_to_debt_ratio', '现金流', '经营现金流负债比', '经营活动现金流量净额/负债合计', _safe_div(operating_cash_flow, total_liabilities), {'operating_cash_flow': operating_cash_flow, 'total_liabilities': total_liabilities}, 'percentage')
    add('total_debt_to_operating_cash', '现金流', '全部负债/经营现金流', '负债合计/经营活动现金流量净额', _safe_div(total_liabilities, operating_cash_flow), {'total_liabilities': total_liabilities, 'operating_cash_flow': operating_cash_flow}, 'multiple')
    add('sales_cash_collection_ratio', '现金流', '销售回款率', '销售商品收到的现金/营业收入', _safe_div(sales_cash_received, revenue), {'sales_cash_received': sales_cash_received, 'revenue': revenue}, 'percentage')
    add('free_cash_flow', '现金流', '自由现金流', '经营活动现金流量净额-资本支出', None if operating_cash_flow is None or capital_expenditure is None else operating_cash_flow - capital_expenditure, {'operating_cash_flow': operating_cash_flow, 'capital_expenditure': capital_expenditure}, 'amount')
    add('cash_reserve_ratio', '现金流', '现金储备占资产比', '货币资金/资产总计', _safe_div(cash, total_assets), {'cash_and_equivalents': cash, 'total_assets': total_assets}, 'percentage')
    add('operating_cash_to_assets', '现金流', '经营现金流占资产比', '经营活动现金流量净额/资产总计', _safe_div(operating_cash_flow, total_assets), {'operating_cash_flow': operating_cash_flow, 'total_assets': total_assets}, 'percentage')
    add('cash_profit_ratio', '现金流', '经营现金流净利润比', '经营活动现金流量净额/净利润', _safe_div(operating_cash_flow, net_profit), {'operating_cash_flow': operating_cash_flow, 'net_profit': net_profit}, 'multiple')
    add('operating_cash_flow_amount', '现金流', '经营活动现金流量净额', '现金流量表披露值', operating_cash_flow, {'operating_cash_flow': operating_cash_flow}, 'amount')

    add('receivables_asset_ratio', '资产质量', '应收账款资产占比', '应收账款/资产总计', _safe_div(_num(bs, 'accounts_receivable'), total_assets), {'accounts_receivable': _num(bs, 'accounts_receivable'), 'total_assets': total_assets}, 'percentage')
    add('inventory_asset_ratio', '资产质量', '存货资产占比', '存货/资产总计', _safe_div(inventory, total_assets), {'inventory': inventory, 'total_assets': total_assets}, 'percentage')
    add('prepaid_asset_ratio', '资产质量', '预付款项资产占比', '预付款项/资产总计', _safe_div(prepaid, total_assets), {'prepaid_accounts': prepaid, 'total_assets': total_assets}, 'percentage')
    add('inventory_current_asset_ratio', '资产质量', '存货流动资产占比', '存货/流动资产', _safe_div(inventory, current_assets), {'inventory': inventory, 'current_assets': current_assets}, 'percentage')
    add('current_liability_share', '资产质量', '流动负债占比', '流动负债/负债合计', _safe_div(current_liabilities, total_liabilities), {'current_liabilities': current_liabilities, 'total_liabilities': total_liabilities}, 'percentage')
    add('restricted_cash_ratio', '资产质量', '受限资金占比', '受限资金/货币资金', _safe_div(_num(supplement, 'restricted_cash'), cash), {'restricted_cash': _num(supplement, 'restricted_cash'), 'cash_and_equivalents': cash}, 'percentage')
    add('interest_bearing_debt_ratio', '资产质量', '有息负债资产比', '有息负债/资产总计', _safe_div(_num(supplement, 'interest_bearing_debt'), total_assets), {'interest_bearing_debt': _num(supplement, 'interest_bearing_debt'), 'total_assets': total_assets}, 'percentage')
    add('short_debt_ratio', '资产质量', '一年内到期有息负债占比', '一年内到期有息负债/有息负债', _safe_div(_num(supplement, 'debt_due_within_one_year'), _num(supplement, 'interest_bearing_debt')), {'debt_due_within_one_year': _num(supplement, 'debt_due_within_one_year'), 'interest_bearing_debt': _num(supplement, 'interest_bearing_debt')}, 'percentage')

    adjusted_profit = _num(supplement, 'adjusted_net_profit')
    non_recurring = _num(supplement, 'non_recurring_profit')
    adjusted_profit_disclosed = adjusted_profit is not None
    if not adjusted_profit_disclosed and net_profit is not None and non_recurring is not None:
        adjusted_profit = net_profit - non_recurring
    if adjusted_profit_disclosed:
        add('adjusted_net_profit', '利润质量', '扣除非经常性损益后净利润', '材料披露值', adjusted_profit, {'adjusted_net_profit': adjusted_profit}, 'amount')
    else:
        add('adjusted_net_profit', '利润质量', '扣除非经常性损益后净利润', '净利润-非经常性损益', adjusted_profit, {'net_profit': net_profit, 'non_recurring_profit': non_recurring}, 'amount', '仅在未披露扣非净利润时按两个已披露值计算')
    add('non_recurring_profit_share', '利润质量', '非经常性损益占净利润比', '非经常性损益/|净利润|', _safe_div(non_recurring, abs(net_profit) if net_profit is not None else None), {'non_recurring_profit': non_recurring, 'net_profit_absolute': abs(net_profit) if net_profit is not None else None}, 'percentage')
    add('core_business_profit_share', '利润质量', '主营业务利润贡献度', '主营业务利润/|利润总额|', _safe_div(_num(inc, 'core_business_profit'), abs(total_profit) if total_profit is not None else None), {'core_business_profit': _num(inc, 'core_business_profit'), 'total_profit_absolute': abs(total_profit) if total_profit is not None else None}, 'percentage')
    add('interest_income_yield', '利润质量', '货币资金收益率', '利息收入/平均货币资金', _safe_div(_num(inc, 'interest_income'), avg_cash), {'interest_income': _num(inc, 'interest_income'), 'average_cash': avg_cash}, 'percentage')
    add('financing_cost', '利润质量', '融资成本', '利息支出/平均有息负债', _safe_div(interest_expense, avg_interest_debt), {'interest_expense': interest_expense, 'average_interest_bearing_debt': avg_interest_debt}, 'percentage')
    add('top_five_receivables_ratio', '资产质量', '前五大客户应收占比', '材料披露比例', _num(supplement, 'top_five_receivables_ratio'), {'top_five_receivables_ratio': _num(supplement, 'top_five_receivables_ratio')}, 'percentage')
    add('receivables_over_one_year_ratio', '资产质量', '一年以上应收占比', '材料披露比例', _num(supplement, 'receivables_over_one_year_ratio'), {'receivables_over_one_year_ratio': _num(supplement, 'receivables_over_one_year_ratio')}, 'percentage')

    net_margin = metrics['net_profit_margin']['value']
    asset_turnover = metrics['total_asset_turnover']['value']
    equity_multiplier = metrics['equity_multiplier']['value']
    dupont = None if None in (net_margin, asset_turnover, equity_multiplier) else net_margin * asset_turnover * equity_multiplier
    add('dupont_roe', '盈利能力', '杜邦 ROE', '销售净利率×总资产周转率×权益乘数', dupont, {'net_profit_margin': net_margin, 'total_asset_turnover': asset_turnover, 'equity_multiplier': equity_multiplier}, 'percentage')

    vat_revenue = _num(cross, 'vat_declared_revenue')
    bank_inflows = _num(cross, 'bank_operating_inflows')
    taxable_income = _num(cross, 'taxable_income')
    registry_assets = _num(cross, 'business_registry_assets')
    income_tax_paid = _num(cross, 'income_tax_paid')
    utility_cost = _num(cross, 'utility_cost')
    payroll = _num(cross, 'payroll')
    social_security_base = _num(cross, 'social_security_base')
    add('revenue_vat_difference_rate', '交叉验证', '财务收入与增值税收入差异率', '(财务收入-增值税申报收入)/|增值税申报收入|', _difference_rate(revenue, vat_revenue), {'revenue': revenue, 'vat_declared_revenue': vat_revenue}, 'percentage')
    add('bank_collection_ratio', '交叉验证', '银行流水回款率', '经营性银行进账/营业收入', _safe_div(bank_inflows, revenue), {'bank_operating_inflows': bank_inflows, 'revenue': revenue}, 'percentage')
    add('profit_taxable_difference_rate', '交叉验证', '利润与应纳税所得额差异率', '(利润总额-应纳税所得额)/|应纳税所得额|', _difference_rate(total_profit, taxable_income), {'total_profit': total_profit, 'taxable_income': taxable_income}, 'percentage')
    add('effective_income_tax_rate', '交叉验证', '所得税费用率', '所得税费用/利润总额', _safe_div(_num(inc, 'income_tax'), total_profit), {'income_tax': _num(inc, 'income_tax'), 'total_profit': total_profit}, 'percentage')
    add('tax_paid_to_expense_ratio', '交叉验证', '实缴所得税与所得税费用比', '实缴所得税/所得税费用', _safe_div(income_tax_paid, _num(inc, 'income_tax')), {'income_tax_paid': income_tax_paid, 'income_tax_expense': _num(inc, 'income_tax')}, 'percentage')
    add('cost_utility_ratio', '交叉验证', '营业成本与能耗费用比', '营业成本/水电气费用', _safe_div(cost, utility_cost), {'cost_of_revenue': cost, 'utility_cost': utility_cost}, 'multiple', '需结合多期产量和能耗趋势解释，不设通用阈值')
    add('payroll_social_security_base_difference_rate', '交叉验证', '工资与社保缴费基数差异率', '(工资总额-社保缴费基数)/|社保缴费基数|', _difference_rate(payroll, social_security_base), {'payroll': payroll, 'social_security_base': social_security_base}, 'percentage', '缴费基数不等于实缴金额，需结合人数和法定费率')
    add('asset_registry_difference_rate', '交叉验证', '财务资产与工商年报资产差异率', '(财务资产-工商年报资产)/|工商年报资产|', _difference_rate(total_assets, registry_assets), {'total_assets': total_assets, 'business_registry_assets': registry_assets}, 'percentage')

    return metrics


def statement_facts(data: dict[str, Any]) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    for table_key, prefix in FACT_PREFIXES.items():
        table = data.get(table_key) or {}
        labels = dict(STATEMENT_FIELDS.get(table_key, ()))
        for key, value in table.items():
            number = _num(table, key)
            facts[f'{prefix}_{key}'] = {
                'name_cn': labels.get(key, key),
                'value': _round(number, 2),
                'value_type': 'percentage' if key in UNITLESS_SUPPLEMENT_FIELDS else 'amount',
                'formula': '材料披露值',
                'computable': number is not None,
            }
    return facts


def _is_close(
    left: Optional[float], right: Optional[float], tolerance: float
) -> Optional[bool]:
    if left is None or right is None:
        return None
    return abs(left - right) <= tolerance



# 勾稽规则版本。规则清单（编号体系/公式/容差口径）变更时递增。
#
# v1：C01-C11（精简科目时代，按会计恒等式抽查，容差为报表单位舍入误差）
# v2：《财务三表勾稽配平》全量配平校验 —— BS-01~08 / IS-01~02 / CF-01~11，
#     「合计 = 明细逐项求和」为主，容差 0%。
# 消费方（前端兜底映射、报告表格）按此版本区分存量与新数据。
CONSISTENCY_RULE_VERSION = 2

# 勾稽规则清单（唯一权威声明）。
#
# 每条规则的 left / right 均为「(符号, 字段全路径)」序列，等式成立条件为
# Σleft == Σright。字段全路径必须与 normalized_inputs.source_refs 的 key 完全一致
# （形如 balance_sheet.total_assets），否则消费方按路径查不到字段级出处，
# 会误判为「人工填报 / 无原始材料出处」。新增或调整规则必须只改本表。
#
# severity 分级（决定提交闸门与报告降级，见 analyze 的 summary）：
# - critical：合计/恒等式类（资产总计、负债总计、负债和所有者权益总计、利润总额、
#   净利润、三大活动净额、现金净增加额、期末现金），不平即视为提取错误；
# - warning：「合计 = 明细逐项求和」类，企业常有未列示的明细科目，差异属口径问题。
#
# 容差统一为 0%（`_CONSISTENCY_TOLERANCE_YUAN`），即左右必须严格相等。
CONSISTENCY_RULES: tuple[dict[str, Any], ...] = (
    # ─────────────── 资产负债表 ───────────────
    {
        'id': 'BS-01',
        'name': '资产总计=流动资产合计+非流动资产合计',
        'severity': 'critical',
        'left': (('+', 'balance_sheet.total_assets'),),
        'right': (
            ('+', 'balance_sheet.current_assets'),
            ('+', 'balance_sheet.non_current_assets'),
        ),
    },
    {
        'id': 'BS-02',
        'name': '流动资产合计=各流动资产明细之和',
        'severity': 'warning',
        'left': (('+', 'balance_sheet.current_assets'),),
        'right': tuple(
            ('+', f'balance_sheet.{key}')
            for key in (
                'cash_and_equivalents',
                'trading_financial_assets',
                'derivative_financial_assets',
                'notes_receivable',
                'accounts_receivable',
                'receivables_financing',
                'prepaid_accounts',
                'other_receivables',
                'inventory',
                'contract_assets',
                'assets_held_for_sale',
                'noncurrent_assets_due_within_one_year',
                'other_current_assets',
            )
        ),
    },
    {
        'id': 'BS-03',
        'name': '非流动资产合计=各非流动资产明细之和',
        'severity': 'warning',
        'left': (('+', 'balance_sheet.non_current_assets'),),
        'right': tuple(
            ('+', f'balance_sheet.{key}')
            for key in (
                'debt_investments',
                'other_debt_investments',
                'available_for_sale_financial_assets',
                'long_term_receivables',
                'long_term_equity_investments',
                'other_equity_instrument_investments',
                'investment_property',
                'fixed_assets',
                'construction_in_progress',
                'productive_biological_assets',
                'oil_and_gas_assets',
                'right_of_use_assets',
                'intangible_assets',
                'development_expenditure',
                'goodwill',
                'long_term_deferred_expenses',
                'entrusted_loans',
                'foreclosed_assets',
                'deferred_tax_assets',
                'other_non_current_assets',
            )
        ),
    },
    {
        'id': 'BS-04',
        'name': '负债总计=流动负债合计+非流动负债合计',
        'severity': 'critical',
        'left': (('+', 'balance_sheet.total_liabilities'),),
        'right': (
            ('+', 'balance_sheet.current_liabilities'),
            ('+', 'balance_sheet.non_current_liabilities'),
        ),
    },
    {
        'id': 'BS-05',
        'name': '流动负债合计=各流动负债明细之和',
        'severity': 'warning',
        'left': (('+', 'balance_sheet.current_liabilities'),),
        'right': tuple(
            ('+', f'balance_sheet.{key}')
            for key in (
                'short_term_borrowings',
                'fvtpl_financial_liabilities',
                'trading_financial_liabilities',
                'derivative_financial_liabilities',
                'notes_payable',
                'accounts_payable',
                'advances_from_customers',
                'contract_liabilities',
                'guarantee_deposits_received',
                'financial_assets_sold_for_repurchase',
                'fees_and_commissions_payable',
                'employee_benefits_payable',
                'taxes_payable',
                'guarantee_compensation_reserve',
                'short_term_liability_reserve',
                'other_payables',
                'liabilities_held_for_sale',
                'noncurrent_liabilities_due_within_one_year',
                'other_current_liabilities',
            )
        ),
    },
    {
        'id': 'BS-06',
        'name': '非流动负债合计=各非流动负债明细之和',
        'severity': 'warning',
        'left': (('+', 'balance_sheet.non_current_liabilities'),),
        'right': tuple(
            ('+', f'balance_sheet.{key}')
            for key in (
                'long_term_borrowings',
                'bonds_payable',
                'lease_liabilities',
                'long_term_payables',
                'long_term_employee_benefits_payable',
                'provisions',
                'insurance_contract_reserve',
                'deferred_income',
                'deferred_tax_liabilities',
                'other_non_current_liabilities',
            )
        ),
    },
    {
        'id': 'BS-07',
        'name': '所有者权益合计=各权益明细之和-库存股',
        'severity': 'warning',
        'left': (('+', 'balance_sheet.total_equity'),),
        'right': (
            ('+', 'balance_sheet.paid_in_capital'),
            ('+', 'balance_sheet.other_equity_instruments'),
            ('+', 'balance_sheet.capital_reserve'),
            # 库存股在报表中以「减：」列示，配平时为减项
            ('-', 'balance_sheet.treasury_stock'),
            ('+', 'balance_sheet.other_comprehensive_income'),
            ('+', 'balance_sheet.special_reserve'),
            ('+', 'balance_sheet.surplus_reserve'),
            ('+', 'balance_sheet.general_risk_reserve'),
            ('+', 'balance_sheet.retained_earnings'),
            ('+', 'balance_sheet.minority_interest'),
        ),
    },
    {
        'id': 'BS-08',
        'name': '负债和所有者权益总计=负债总计+所有者权益合计',
        'severity': 'critical',
        'left': (('+', 'balance_sheet.total_liabilities_and_equity'),),
        'right': (
            ('+', 'balance_sheet.total_liabilities'),
            ('+', 'balance_sheet.total_equity'),
        ),
    },
    # ─────────────── 利润表 ───────────────
    {
        'id': 'IS-01',
        'name': '利润总额=营业利润+营业外收入-营业外支出',
        'severity': 'critical',
        'left': (('+', 'income_statement.total_profit'),),
        'right': (
            ('+', 'income_statement.operating_profit'),
            ('+', 'income_statement.non_operating_income'),
            ('-', 'income_statement.non_operating_expense'),
        ),
    },
    {
        'id': 'IS-02',
        'name': '净利润=利润总额-所得税费用',
        'severity': 'critical',
        'left': (('+', 'income_statement.net_profit'),),
        'right': (
            ('+', 'income_statement.total_profit'),
            ('-', 'income_statement.income_tax'),
        ),
    },
    # ─────────────── 现金流量表 ───────────────
    {
        'id': 'CF-01',
        'name': '经营活动产生的现金流量净额=经营活动现金流入小计-流出小计',
        'severity': 'critical',
        'left': (('+', 'cash_flow.operating_cash_flow'),),
        'right': (
            ('+', 'cash_flow.operating_cash_inflow'),
            ('-', 'cash_flow.operating_cash_outflow'),
        ),
    },
    {
        'id': 'CF-02',
        'name': '经营活动现金流入小计=各流入明细之和',
        'severity': 'warning',
        'left': (('+', 'cash_flow.operating_cash_inflow'),),
        'right': tuple(
            ('+', f'cash_flow.{key}')
            for key in (
                'sales_cash_received',
                'fvtpl_disposal_cash_received',
                'interest_fee_commission_received',
                'net_increase_in_borrowing_funds',
                'net_increase_in_repurchase_funds',
                'tax_refunds_received',
                'other_operating_cash_received',
            )
        ),
    },
    {
        'id': 'CF-03',
        'name': '经营活动现金流出小计=各流出明细之和',
        'severity': 'warning',
        'left': (('+', 'cash_flow.operating_cash_outflow'),),
        'right': tuple(
            ('+', f'cash_flow.{key}')
            for key in (
                'purchases_cash_paid',
                'employee_cash_paid',
                'taxes_cash_paid',
                'other_operating_cash_paid',
            )
        ),
    },
    {
        'id': 'CF-04',
        'name': '投资活动产生的现金流量净额=投资活动现金流入小计-流出小计',
        'severity': 'critical',
        'left': (('+', 'cash_flow.investing_cash_flow'),),
        'right': (
            ('+', 'cash_flow.investing_cash_inflow'),
            ('-', 'cash_flow.investing_cash_outflow'),
        ),
    },
    {
        'id': 'CF-05',
        'name': '投资活动现金流入小计=各流入明细之和',
        'severity': 'warning',
        'left': (('+', 'cash_flow.investing_cash_inflow'),),
        'right': tuple(
            ('+', f'cash_flow.{key}')
            for key in (
                'investment_recovered',
                'investment_income_cash_received',
                'subsidiary_acquisition_cash_received',
                'asset_disposal_cash_received',
                'subsidiary_disposal_cash_received',
                'other_investing_cash_received',
            )
        ),
    },
    {
        'id': 'CF-06',
        'name': '投资活动现金流出小计=各流出明细之和',
        'severity': 'warning',
        'left': (('+', 'cash_flow.investing_cash_outflow'),),
        'right': tuple(
            ('+', f'cash_flow.{key}')
            for key in (
                'capital_expenditure',
                'investments_paid',
                'other_investing_cash_paid',
            )
        ),
    },
    {
        'id': 'CF-07',
        'name': '筹资活动产生的现金流量净额=筹资活动现金流入小计-流出小计',
        'severity': 'critical',
        'left': (('+', 'cash_flow.financing_cash_flow'),),
        'right': (
            ('+', 'cash_flow.financing_cash_inflow'),
            ('-', 'cash_flow.financing_cash_outflow'),
        ),
    },
    {
        'id': 'CF-08',
        'name': '筹资活动现金流入小计=各流入明细之和',
        'severity': 'warning',
        'left': (('+', 'cash_flow.financing_cash_inflow'),),
        'right': tuple(
            ('+', f'cash_flow.{key}')
            for key in (
                'capital_contributions_received',
                'borrowings_received',
                'bond_issuance_cash_received',
                'other_financing_cash_received',
            )
        ),
    },
    {
        'id': 'CF-09',
        'name': '筹资活动现金流出小计=各流出明细之和',
        'severity': 'warning',
        'left': (('+', 'cash_flow.financing_cash_outflow'),),
        'right': tuple(
            ('+', f'cash_flow.{key}')
            for key in (
                'debt_repaid',
                'interest_dividends_paid',
                'other_financing_cash_paid',
            )
        ),
    },
    {
        'id': 'CF-10',
        # 按《财务三表勾稽配平》口径，本式不含汇率变动影响
        'name': '现金及现金等价物净增加额=经营+投资+筹资净额',
        'severity': 'critical',
        'left': (('+', 'cash_flow.cash_change'),),
        'right': (
            ('+', 'cash_flow.operating_cash_flow'),
            ('+', 'cash_flow.investing_cash_flow'),
            ('+', 'cash_flow.financing_cash_flow'),
        ),
    },
    {
        'id': 'CF-11',
        'name': '期末现金及现金等价物余额=期初余额+现金及现金等价物净增加额',
        'severity': 'critical',
        'left': (('+', 'cash_flow.cash_end'),),
        'right': (
            ('+', 'cash_flow.cash_begin'),
            ('+', 'cash_flow.cash_change'),
        ),
    },
)

# 容差 0%：左右两侧必须严格相等。
#
# 比较前两侧统一 round 到分（2 位小数），仅为消除单位换算引入的 IEEE754 尾差
# （如 1.1 万元 → 11000.000000000002），不构成任何金额上的容让。
_CONSISTENCY_TOLERANCE_YUAN = 0.0

# 「合计 = 明细逐项求和」类规则：明细科目在报表未列示时按 0 参与求和。
#
# 会计语义：报表未列示该行即无余额（或余额为 0），与「数值缺失待补」不同。
# 写死公式无法穷举所有行业科目（一般企业/金融/担保/保险报表行项差异很大），
# 若按缺失判不可计算，会导致绝大多数企业的求和类勾稽永远停在「缺少输入」。
# 合计/恒等式类规则（critical）不适用——关键合计缺失必须如实判不可计算。
MISSING_AS_ZERO_RULE_IDS = frozenset({
    'BS-02', 'BS-03', 'BS-05', 'BS-06', 'BS-07',
    'CF-02', 'CF-03', 'CF-05', 'CF-06', 'CF-08', 'CF-09',
})
for _rule in CONSISTENCY_RULES:
    _rule['missing_as_zero'] = _rule['id'] in MISSING_AS_ZERO_RULE_IDS

# 每条勾稽等式两侧涉及的字段全路径（含表名前缀），由 CONSISTENCY_RULES 派生。
#
# 「勾稽 → 字段 → 原始材料」溯源链的对外契约，消费方按此定位字段级出处。
CONSISTENCY_FIELDS: dict[str, dict[str, tuple[str, ...]]] = {
    rule['id']: {
        'left': tuple(path for _sign, path in rule['left']),
        'right': tuple(path for _sign, path in rule['right']),
    }
    for rule in CONSISTENCY_RULES
}


def _signed_sum(
    data: dict[str, Any],
    terms: tuple[tuple[str, str], ...],
    missing_as_zero: bool = False,
) -> tuple[Optional[float], list[str]]:
    """按「(符号, 字段全路径)」序列求和，返回 (合计, 缺失字段路径列表)。

    - missing_as_zero=False（合计/恒等式类）：任一项缺失即整体不可计算（合计 None）。
    - missing_as_zero=True（明细求和类）：报表未列示该行即无余额，缺失按 0 参与求和；
      但若**全部**项都缺失，仍返回 None——对全 0 求和只会产生无意义的「不通过」，
      说明材料里根本没有这张明细表。
    """
    total = 0.0
    missing: list[str] = []
    for sign, path in terms:
        table_key, _, field = path.partition('.')
        value = _num(data.get(table_key) or {}, field)
        if value is None:
            missing.append(path)
            continue
        total += value if sign == '+' else -value
    if missing and (not missing_as_zero or len(missing) == len(terms)):
        return None, missing
    return total, missing


def _diagnose_difference(
    diff: float,
    rule: dict[str, Any],
    data: dict[str, Any],
    quantum: float = 0.01,
) -> Optional[dict[str, Any]]:
    """差额反查：配平差额若精确等于某个参与科目金额（或两科目之差），定位疑似漏项。

    纯算术诊断，仅在「不通过」时执行，不改变 passed 判定；比较同样对齐到披露精度。
    """
    terms: list[tuple[str, float]] = []
    for side in ('left', 'right'):
        for sign, path in rule[side]:
            table_key, _, field = path.partition('.')
            value = _num(data.get(table_key) or {}, field)
            if value is not None:
                terms.append((path, _snap(value if sign == '+' else -value, quantum)))
    for path, value in terms:
        if _is_close(value, diff, _CONSISTENCY_TOLERANCE_YUAN):
            return {
                'type': 'single',
                'field': path,
                'hint': '差额恰等于该科目金额，疑似该科目漏算或重复计数',
            }
    for index, (path_a, value_a) in enumerate(terms):
        for path_b, value_b in terms[index + 1:]:
            if _is_close(
                _snap(value_a - value_b, quantum), diff, _CONSISTENCY_TOLERANCE_YUAN
            ):
                return {
                    'type': 'pair',
                    'fields': [path_a, path_b],
                    'hint': '差额恰等于两科目金额之差，疑似其一漏算或符号处理有误',
                }
    return None


def _disclosure_quantum(data: dict[str, Any], table_keys: set[str]) -> float:
    """规则涉及各表的「最小披露步长」（元）——即该表单位下的 1 分。

    报表以「万元」披露到 2 位小数时，最小可读差异是 100 元；比较必须在这个精度上进行。
    IEEE754 双精度在 1e15 量级的 ulp 已达 0.125 元（大于 1 分），若强行按「分」比较，
    数学上相等、仅加法路径不同的两侧会得出 0.1 元的假差异。
    """
    table_units = data.get('table_units') or {}
    fallback = str(data.get('source_unit') or '元')
    factors = [
        UNIT_FACTORS.get(str(table_units.get(key) or fallback), 1.0) for key in table_keys
    ] or [1.0]
    return max(factors) * 0.01


def _snap(value: Optional[float], quantum: float) -> Optional[float]:
    """把金额对齐到披露精度（避免浮点尾数被当成差异）。"""
    if value is None or quantum <= 0:
        return value
    return round(value / quantum) * quantum


def compute_consistency(data: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for rule in CONSISTENCY_RULES:
        left, left_missing = _signed_sum(data, rule['left'], rule['missing_as_zero'])
        right, right_missing = _signed_sum(data, rule['right'], rule['missing_as_zero'])
        tables = {
            path.split('.', 1)[0] for _sign, path in (*rule['left'], *rule['right'])
        }
        quantum = _disclosure_quantum(data, tables)
        # 先对齐到披露精度再比较，容差本身为 0（不含任何会计口径容让）
        left_snapped = _snap(left, quantum)
        right_snapped = _snap(right, quantum)
        passed = _is_close(left_snapped, right_snapped, _CONSISTENCY_TOLERANCE_YUAN)
        declared = CONSISTENCY_FIELDS[rule['id']]
        check = {
            'id': rule['id'],
            'name': rule['name'],
            'severity': rule['severity'],
            # 等式两侧字段全路径，供消费方按字段溯源到原始材料出处
            'fields': {
                'left': list(declared['left']),
                'right': list(declared['right']),
            },
            'computable': passed is not None,
            'passed': passed,
            'detail': {
                'left': _round(left_snapped, 2),
                'right': _round(right_snapped, 2),
                'tolerance_yuan': _CONSISTENCY_TOLERANCE_YUAN,
                # 披露精度步长（元）：万元表 = 100，元表 = 0.01
                'quantum_yuan': quantum,
                # missing_as_zero 规则中按 0 参与求和的字段，供前端提示「N 项未列示按 0」
                'missing': {'left': left_missing, 'right': right_missing},
            },
        }
        if passed is False and left_snapped is not None and right_snapped is not None:
            diagnosis = _diagnose_difference(
                left_snapped - right_snapped, rule, data, quantum
            )
            if diagnosis:
                check['diagnosis'] = diagnosis
        checks.append(check)

    failed = [item for item in checks if item['computable'] and item['passed'] is False]
    critical_failed = [item for item in failed if item['severity'] == 'critical']
    critical_uncomputable = [item for item in checks if item['severity'] == 'critical' and not item['computable']]
    return {
        'rule_version': CONSISTENCY_RULE_VERSION,
        'checks': checks,
        'failed_count': len(failed),
        'critical_failed': bool(critical_failed),
        'critical_uncomputable_count': len(critical_uncomputable),
        'all_computable_checks_passed': not failed and not critical_uncomputable,
    }


def compute_period_links(period_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Check explicitly supplied opening balances against adjacent annual closes."""
    fields = (
        'cash_and_equivalents', 'accounts_receivable', 'inventory', 'current_assets',
        'fixed_assets', 'total_assets', 'accounts_payable', 'current_liabilities',
        'total_liabilities', 'total_equity',
    )
    annual = [item for item in period_results if item.get('period_type') == 'annual']
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = list(zip(annual, annual[1:]))
    current = period_results[-1] if period_results else None
    if current and current.get('period_type') == 'interim' and annual:
        pairs.append((annual[-1], current))

    checks: list[dict[str, Any]] = []
    for previous, following in pairs:
        previous_inputs = previous.get('normalized_inputs') or {}
        following_inputs = following.get('normalized_inputs') or {}
        closing = previous_inputs.get('balance_sheet') or {}
        opening = following_inputs.get('opening_balance_sheet') or {}
        previous_tolerances = previous_inputs.get('_table_rounding_tolerance_yuan') or {}
        following_tolerances = following_inputs.get('_table_rounding_tolerance_yuan') or {}
        tolerance = max(
            float(previous_tolerances.get('balance_sheet') or EQ_TOLERANCE_YUAN),
            float(following_tolerances.get('opening_balance_sheet') or EQ_TOLERANCE_YUAN),
        )
        for field in fields:
            prior_value = _num(closing, field)
            opening_value = _num(opening, field)
            passed = _is_close(prior_value, opening_value, tolerance)
            checks.append({
                'id': f'PL-{previous.get("period_label")}-{following.get("period_label")}-{field}',
                'field': field,
                'from_period': previous.get('period_label'),
                'to_period': following.get('period_label'),
                'computable': passed is not None,
                'passed': passed,
                'severity': 'warning',
                'detail': {
                    'previous_closing': _round(prior_value, 2),
                    'following_opening': _round(opening_value, 2),
                    'tolerance_yuan': tolerance,
                },
            })
    failed = [item for item in checks if item['computable'] and item['passed'] is False]
    return {
        'checks': checks,
        'failed_count': len(failed),
        'uncomputable_count': sum(1 for item in checks if not item['computable']),
    }


def _choose_current_comparison(raw: dict[str, Any], normalized_periods: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    desired = 'prior_year_same_period' if raw.get('period_type') == 'interim' else 'prior_year'
    for period in reversed(normalized_periods):
        if period.get('period_role') == desired:
            return period
    return None


def _period_year(period: dict[str, Any]) -> Optional[int]:
    label = str(period.get('period_label') or '')
    digits = ''.join(character for character in label[:4] if character.isdigit())
    return int(digits) if len(digits) == 4 else None


def _period_coordinates(period: dict[str, Any]) -> tuple[Optional[int], Optional[str]]:
    return _parse_period_text(period.get('period_label'))


def _parse_period_text(value: Any) -> tuple[Optional[int], Optional[str]]:
    label = str(value or '')
    match = re.search(
        r'((?:19|20)\d{2})(?:'
        r'\s*[/.-]\s*(\d{1,2})'
        r'|\s*年\s*(\d{1,2})\s*月'
        r'|\s*[Qq]([1-4])'
        r'|\s*年\s*第?([一二三四])季度)?',
        label,
    )
    if not match:
        return None, None
    year = int(match.group(1))
    if match.group(2) or match.group(3):
        month = int(match.group(2) or match.group(3))
        if not 1 <= month <= 12:
            return year, None
        return year, f'M{month:02d}'
    if match.group(4):
        return year, f'M{int(match.group(4)) * 3:02d}'
    if match.group(5):
        quarter = {'一': 1, '二': 2, '三': 3, '四': 4}[match.group(5)]
        return year, f'M{quarter * 3:02d}'
    return year, None


def _consecutive_annual_values(
    period_results: list[dict[str, Any]], key: str, count: int
) -> Optional[list[float]]:
    annual = [item for item in period_results if item.get('period_type') == 'annual']
    selected = annual[-count:]
    if len(selected) != count:
        return None
    years = [_period_year(item) for item in selected]
    if any(year is None for year in years):
        return None
    if any(right - left != 1 for left, right in zip(years, years[1:])):
        return None
    values = [(item.get('metrics') or {}).get(key, {}).get('value') for item in selected]
    if any(value is None for value in values):
        return None
    return [float(value) for value in values if value is not None]


def compute_rule_signals(period_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current = period_results[-1] if period_results else {}
    current_metrics = current.get('metrics') or {}
    annual_periods = [item for item in period_results if item.get('period_type') == 'annual']
    latest_annual_metrics = (annual_periods[-1].get('metrics') or {}) if annual_periods else {}

    def value(key: str) -> Optional[float]:
        return (current_metrics.get(key) or {}).get('value')

    signals: list[dict[str, Any]] = []

    def add(rule_id: str, name: str, condition: str, triggered: Optional[bool], inputs: dict[str, Any]) -> None:
        signals.append({
            'rule_id': rule_id,
            'name': name,
            'condition': condition,
            'triggered': triggered,
            'inputs': inputs,
            'computable': triggered is not None,
            'note': '机械规则信号，不等同风险评级或事实认定',
        })

    annual_net_margin = _consecutive_annual_values(period_results, 'net_profit_margin', 3)
    annual_gross_margin = _consecutive_annual_values(period_results, 'gross_profit_margin', 3)
    annual_quick = _consecutive_annual_values(period_results, 'quick_ratio', 2)
    annual_cfo = _consecutive_annual_values(period_results, 'operating_cash_flow_amount', 2)
    annual_growth = _consecutive_annual_values(period_results, 'revenue_growth', 2)

    add('BR-P01', '销售净利率连续三年低于5%', '最近3个连续完整年度均<0.05', all(item < 0.05 for item in annual_net_margin) if annual_net_margin else None, {'annual_values': annual_net_margin})
    add('BR-P02', '毛利率低于20%', '当期<0.20', value('gross_profit_margin') < 0.20 if value('gross_profit_margin') is not None else None, {'current': value('gross_profit_margin')})
    add('BR-P03', '毛利率连续下降', '最近3个连续完整年度逐期下降', annual_gross_margin[0] > annual_gross_margin[1] > annual_gross_margin[2] if annual_gross_margin else None, {'annual_values': annual_gross_margin})
    add('BR-S01', '流动比率低于1.5', '当期<1.5', value('current_ratio') < 1.5 if value('current_ratio') is not None else None, {'current': value('current_ratio')})
    add('BR-S02', '速动比率连续两年低于0.8', '最近2个连续完整年度均<0.8', all(item < 0.8 for item in annual_quick) if annual_quick else None, {'annual_values': annual_quick})
    add('BR-C01', '经营现金流连续两年为负', '最近2个连续完整年度均<0', all(item < 0 for item in annual_cfo) if annual_cfo else None, {'annual_values': annual_cfo})
    add('BR-C02', '现金储备占资产低于10%', '当期<0.10', value('cash_reserve_ratio') < 0.10 if value('cash_reserve_ratio') is not None else None, {'current': value('cash_reserve_ratio')})
    annual_receivable_turnover = (latest_annual_metrics.get('receivable_turnover') or {}).get('value')
    annual_receivable_days = (latest_annual_metrics.get('receivable_days') or {}).get('value')
    receivable_efficiency_signal = None
    if annual_receivable_turnover is not None and annual_receivable_days is not None:
        receivable_efficiency_signal = annual_receivable_turnover < 4 or annual_receivable_days > 90
    add('BR-O01', '年度应收周转偏慢', '最近年度周转率<4或DSO>90天', receivable_efficiency_signal, {'latest_annual_turnover': annual_receivable_turnover, 'latest_annual_days': annual_receivable_days})
    add('BR-G01', '营业收入增长率连续两年低于5%', '最近2个连续完整年度均<0.05', all(item < 0.05 for item in annual_growth) if annual_growth else None, {'annual_values': annual_growth})
    add('BR-Q01', '应收账款占总资产高于20%', '当期>0.20', value('receivables_asset_ratio') > 0.20 if value('receivables_asset_ratio') is not None else None, {'current': value('receivables_asset_ratio')})
    inv_ratio, rec_ratio = value('inventory_asset_ratio'), value('receivables_asset_ratio')
    add('BR-Q02', '存货与应收资产占比双高', '存货/资产>0.15且应收/资产>0.05', inv_ratio > 0.15 and rec_ratio > 0.05 if inv_ratio is not None and rec_ratio is not None else None, {'inventory_asset_ratio': inv_ratio, 'receivables_asset_ratio': rec_ratio})
    add('BR-Q03', '预付款项占总资产高于10%', '当期>0.10', value('prepaid_asset_ratio') > 0.10 if value('prepaid_asset_ratio') is not None else None, {'current': value('prepaid_asset_ratio')})
    net_profit = (current.get('facts') or {}).get('inc_net_profit', {}).get('value')
    cfo = value('operating_cash_flow_amount')
    add('BR-Q04', '净利润为正但经营现金流为负', '净利润>0且CFO<0', net_profit > 0 and cfo < 0 if net_profit is not None and cfo is not None else None, {'net_profit': net_profit, 'operating_cash_flow': cfo})
    add('BR-Q05', '前五大客户应收占比高于50%', '当期>0.50', value('top_five_receivables_ratio') > 0.50 if value('top_five_receivables_ratio') is not None else None, {'current': value('top_five_receivables_ratio')})
    add('BR-Q06', '一年以上应收占比达到或高于10%', '当期>=0.10', value('receivables_over_one_year_ratio') >= 0.10 if value('receivables_over_one_year_ratio') is not None else None, {'current': value('receivables_over_one_year_ratio')})
    vat_diff = value('revenue_vat_difference_rate')
    add('BR-X01', '财务收入与增值税收入差异高于20%', '|差异率|>0.20', abs(vat_diff) > 0.20 if vat_diff is not None else None, {'current': vat_diff})
    collection = value('bank_collection_ratio')
    add('BR-X02', '银行流水回款率低于70%', '当期<0.70', collection < 0.70 if collection is not None else None, {'current': collection})
    divergence = value('profit_revenue_growth_divergence')
    add('BR-A01', '收入利润增速偏离度高于30%', '当期>0.30且收入增速为正', divergence > 0.30 if divergence is not None else None, {'current': divergence})
    return signals


def compute_rule_bands(metrics: dict[str, Any], latest_annual_metrics: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """执行 Excel 中的完整分段，不把区间代码升级为语义评级。"""

    def metric_value(key: str) -> Optional[float]:
        return (metrics.get(key) or {}).get('value')

    def band(
        value: Optional[float],
        cuts: list[tuple[float, str]],
        final: str,
        strict_final: bool = True,
    ) -> Optional[str]:
        if value is None:
            return None
        for index, (upper, code) in enumerate(cuts):
            if value < upper:
                return code
            if strict_final and index == len(cuts) - 1 and math.isclose(value, upper, abs_tol=1e-12):
                return 'equal_upper_threshold'
        return final

    annual_receivable_turnover = ((latest_annual_metrics or {}).get('receivable_turnover') or {}).get('value')
    definitions = {
        'net_profit_margin': {
            'value': metric_value('net_profit_margin'),
            'band': band(metric_value('net_profit_margin'), [(0.05, 'below_0_05'), (0.15, 'from_0_05_to_0_15')], 'above_0_15'),
            'thresholds': [0.05, 0.15],
        },
        'gross_profit_margin': {
            'value': metric_value('gross_profit_margin'),
            'band': band(metric_value('gross_profit_margin'), [(0.20, 'below_0_20'), (0.30, 'from_0_20_to_0_30')], 'above_0_30'),
            'thresholds': [0.20, 0.30],
        },
        'current_ratio': {
            'value': metric_value('current_ratio'),
            'band': band(metric_value('current_ratio'), [(1.5, 'below_1_5'), (2.0, 'from_1_5_to_2_0')], 'above_2_0'),
            'thresholds': [1.5, 2.0],
        },
        'quick_ratio': {
            'value': metric_value('quick_ratio'),
            'band': band(metric_value('quick_ratio'), [(0.8, 'below_0_8'), (1.0, 'from_0_8_to_1_0'), (1.5, 'from_1_0_to_1_5')], 'above_1_5'),
            'thresholds': [0.8, 1.0, 1.5],
        },
        'cash_reserve_ratio': {
            'value': metric_value('cash_reserve_ratio'),
            'band': band(metric_value('cash_reserve_ratio'), [(0.10, 'below_0_10'), (0.15, 'from_0_10_to_0_15')], 'above_0_15'),
            'thresholds': [0.10, 0.15],
        },
        'receivable_turnover': {
            'value': annual_receivable_turnover,
            'band': band(annual_receivable_turnover, [(4.0, 'below_4'), (6.0, 'from_4_to_6')], 'at_or_above_6', strict_final=False),
            'thresholds': [4.0, 6.0],
            'basis': 'latest_annual',
        },
        'revenue_growth': {
            'value': metric_value('revenue_growth'),
            'band': band(metric_value('revenue_growth'), [(0.05, 'below_0_05'), (0.10, 'from_0_05_to_0_10'), (0.15, 'from_0_10_to_0_15')], 'above_0_15'),
            'thresholds': [0.05, 0.10, 0.15],
        },
    }
    return definitions


def compute_industry_comparisons(
    metrics: dict[str, Any], benchmark: Any, expected_as_of_year: Optional[int] = None
) -> dict[str, Any]:
    if benchmark is None:
        return {'usable': False, 'reason': '未提供行业基准对象', 'comparisons': {}}
    if not isinstance(benchmark, dict):
        raise ValueError('industry_benchmarks must be an object')
    benchmark_metrics = benchmark.get('metrics') or {}
    if not benchmark_metrics:
        return {'usable': False, 'reason': '未提供行业数值指标', 'comparisons': {}}
    if not isinstance(benchmark_metrics, dict):
        raise ValueError('industry_benchmarks.metrics must be an object')
    for field in ('classification', 'as_of_period'):
        if not isinstance(benchmark.get(field), str) or not benchmark[field].strip():
            raise ValueError(f'industry_benchmarks.{field} 不能为空')
    benchmark_year, _ = _parse_period_text(benchmark.get('as_of_period'))
    if benchmark_year is None:
        raise ValueError('industry_benchmarks.as_of_period 必须包含四位年份')
    if expected_as_of_year is not None and benchmark_year != expected_as_of_year:
        raise ValueError(
            f'industry_benchmarks.as_of_period 必须与最近完整年度 {expected_as_of_year} 一致'
        )
    sources = benchmark.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError('industry_benchmarks.sources 必须是非空数组')
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f'industry_benchmarks.sources[{index}] 必须是对象')
        for field in ('name', 'ref', 'sample'):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f'industry_benchmarks.sources[{index}].{field} 不能为空')

    comparisons: dict[str, Any] = {}
    for key, values in benchmark_metrics.items():
        if key not in metrics:
            raise ValueError(f'unknown industry benchmark metric: {key}')
        enterprise = (metrics.get(key) or {}).get('value')
        value_type = (metrics.get(key) or {}).get('value_type')
        if not isinstance(values, dict) or not values:
            raise ValueError(f'industry benchmark metric {key} must be a non-empty object')
        item = {'enterprise': enterprise, 'benchmarks': {}, 'difference_rates': {}}
        for benchmark_type in (
            'mean', 'median', 'p25', 'p50', 'p75',
            'excellent', 'weak', 'peer', 'std_dev',
        ):
            benchmark_value = values.get(benchmark_type)
            if benchmark_value is None:
                continue
            if isinstance(benchmark_value, bool) or not isinstance(benchmark_value, (int, float)):
                raise ValueError(f'industry benchmark {key}.{benchmark_type} must be numeric')
            benchmark_value = float(benchmark_value)
            if not math.isfinite(benchmark_value):
                raise ValueError(f'industry benchmark {key}.{benchmark_type} must be finite')
            if benchmark_type == 'std_dev' and benchmark_value <= 0:
                raise ValueError(f'industry benchmark {key}.std_dev must be positive')
            if value_type == 'percentage':
                max_abs = 1.0 if key == 'gross_profit_margin' else (
                    2.0 if key == 'gross_profit_margin_change' else 10.0
                )
                if abs(benchmark_value) > max_abs:
                    raise ValueError(
                        f'industry benchmark {key}.{benchmark_type} 比例必须使用小数口径'
                    )
            item['benchmarks'][benchmark_type] = benchmark_value
            item['difference_rates'][benchmark_type] = _round(_difference_rate(enterprise, benchmark_value))
        if not item['benchmarks']:
            raise ValueError(f'industry benchmark metric {key} has no supported values')
        mean = item['benchmarks'].get('mean')
        std_dev = item['benchmarks'].get('std_dev')
        z_score = _safe_div(None if enterprise is None or mean is None else enterprise - mean, std_dev)
        item['z_score'] = _round(z_score)
        item['outside_two_std'] = None if z_score is None else abs(z_score) > 2
        comparisons[key] = item
    return {
        'usable': True,
        'classification': benchmark.get('classification'),
        'as_of_period': benchmark.get('as_of_period'),
        'sources': sources,
        'comparisons': comparisons,
    }


# 变化率阈值（同比绝对变动）：轻度 >=15%，重度 >=30% 或方向逆转。
STATEMENT_CHANGE_THRESHOLD = 0.15
STATEMENT_CHANGE_SEVERE_MULTIPLE = 2.0

# 绝对额门槛（元）：仅当同比变化率过阈值且绝对变动金额过门槛时才计入显著异动，
# 用于过滤“对比期接近 0 导致的夸张比率”。按科目类型分层，取自银行审查经验默认值，
# 可被 data['statement_change_abs_thresholds'] 覆盖（键为科目前缀 bs_/inc_/cf_ 或具体 fact key）。
DEFAULT_STATEMENT_CHANGE_ABS_THRESHOLDS = {
    'bs_': 1_000_000.0,
    'inc_': 1_000_000.0,
    'cf_': 1_000_000.0,
}

# 方向逆转（盈→亏或权益侵蚀）需要重点关注的科目：由正转负即视为方向逆转。
DIRECTION_REVERSAL_KEYS = {
    'inc_net_profit',
    'inc_operating_profit',
    'inc_total_profit',
    'inc_gross_profit',
    'cf_operating_cash_flow',
    'bs_total_equity',
    'bs_retained_earnings',
}


def _resolve_abs_threshold(
    key: str, overrides: dict[str, Any]
) -> float:
    """按 fact key 精确匹配优先，其次按 bs_/inc_/cf_ 前缀匹配绝对额门槛。"""
    if key in overrides:
        return float(overrides[key])
    for prefix in ('bs_', 'inc_', 'cf_'):
        if key.startswith(prefix):
            if prefix in overrides:
                return float(overrides[prefix])
            return DEFAULT_STATEMENT_CHANGE_ABS_THRESHOLDS[prefix]
    return DEFAULT_STATEMENT_CHANGE_ABS_THRESHOLDS['bs_']


def _grade_statement_change(
    key: str,
    yoy_change: Optional[float],
    passes_abs_gate: bool,
    previous: float,
    latest: float,
) -> tuple[bool, str, bool]:
    """返回 (是否显著, 分级severity, 是否方向逆转)。

    分级规则（纵向自身比）：
    - none：未过阈值或未过绝对额门槛。
    - mild：|同比| ∈ [15%, 30%)。
    - severe：|同比| >= 30%，或关注科目由正转负（方向逆转）。
    绝对额门槛作为双重过滤：变化率达标但绝对变动金额不足门槛时降级为 none，不计入显著异动。
    """
    direction_reversed = key in DIRECTION_REVERSAL_KEYS and previous > 0 and latest < 0
    if yoy_change is None:
        return (False, 'none', direction_reversed)
    magnitude = abs(yoy_change)
    # 保持与历史一致：同比阈值使用严格大于（>0.15）。
    if magnitude <= STATEMENT_CHANGE_THRESHOLD and not direction_reversed:
        return (False, 'none', direction_reversed)
    if not passes_abs_gate and not direction_reversed:
        # 变化率达标但绝对额未过门槛：判定为噪声，不计入显著异动。
        return (False, 'none', direction_reversed)
    if direction_reversed or magnitude >= STATEMENT_CHANGE_THRESHOLD * STATEMENT_CHANGE_SEVERE_MULTIPLE:
        return (True, 'severe', direction_reversed)
    return (True, 'mild', direction_reversed)


def compute_statement_changes(
    period_results: list[dict[str, Any]],
    abs_threshold_overrides: Optional[dict[str, Any]] = None,
    industry_comparisons: Optional[dict[str, Any]] = None,
    metrics: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """三个连续完整年度、同比绝对变动>15% 且过绝对额门槛的异动识别，附分级、方向逆转与双判据。"""
    overrides = abs_threshold_overrides or {}
    annual = [item for item in period_results if item.get('period_type') == 'annual'][-3:]
    if len(annual) < 3:
        return {
            'computable': False,
            'reason': '少于三个完整年度',
            'periods': [item.get('period_label') for item in annual],
            'items': {},
            'significant_items': [],
        }
    years = [_period_year(item) for item in annual]
    if any(year is None for year in years) or any(
        right - left != 1 for left, right in zip(years, years[1:])
    ):
        return {
            'computable': False,
            'reason': '三个完整年度不连续',
            'periods': [item.get('period_label') for item in annual],
            'items': {},
            'significant_items': [],
        }

    horizontal_map = _horizontal_deviation_map(industry_comparisons)
    items: dict[str, Any] = {}
    significant: list[dict[str, Any]] = []
    prefixes = ('bs_', 'inc_', 'cf_')
    keys = sorted(
        set.intersection(
            *(set((item.get('facts') or {}).keys()) for item in annual)
        )
    )
    for key in keys:
        if not key.startswith(prefixes):
            continue
        fact_items = [(item.get('facts') or {}).get(key) or {} for item in annual]
        values = [fact.get('value') for fact in fact_items]
        if any(value is None for value in values):
            continue
        oldest, previous, latest = (float(value) for value in values)
        yoy_change = _difference_rate(latest, previous)
        compound_change = None
        if oldest > 0 and latest >= 0:
            compound_change = (latest / oldest) ** (1 / 2) - 1
        abs_change = latest - previous
        abs_threshold = _resolve_abs_threshold(key, overrides)
        passes_abs_gate = abs(abs_change) >= abs_threshold
        significant_change, severity, direction_reversed = _grade_statement_change(
            key, yoy_change, passes_abs_gate, previous, latest
        )
        table = 'balance_sheet' if key.startswith('bs_') else ('income_statement' if key.startswith('inc_') else 'cash_flow')
        horizontal = horizontal_map.get(key)
        dual_trigger = bool(
            significant_change
            and horizontal is not None
            and horizontal.get('outside_two_std') is True
        )
        item = {
            'key': key,
            'name_cn': fact_items[-1].get('name_cn') or key,
            'table': table,
            'periods': [period.get('period_label') for period in annual],
            'values': [_round(value, 2) for value in values],
            'latest': _round(latest, 2),
            'previous': _round(previous, 2),
            'oldest': _round(oldest, 2),
            'yoy_change': _round(yoy_change),
            'compound_change': _round(compound_change),
            'significant': significant_change,
            'abs_change': _round(abs_change, 2),
            'abs_threshold': _round(abs_threshold, 2),
            'passes_abs_gate': passes_abs_gate,
            'direction_reversed': direction_reversed,
            'severity': severity,
            'horizontal': horizontal,
            'dual_trigger': dual_trigger,
        }
        items[key] = item
        if significant_change:
            significant.append(item)
    return {
        'computable': True,
        'reason': None,
        'threshold': STATEMENT_CHANGE_THRESHOLD,
        'severe_threshold': _round(STATEMENT_CHANGE_THRESHOLD * STATEMENT_CHANGE_SEVERE_MULTIPLE),
        'abs_thresholds': {
            key: _round(_resolve_abs_threshold(key, overrides), 2)
            for key in sorted(items)
        },
        'grading_rule': (
            '纵向自身比：|同比|∈[0.15,0.30) 且过绝对额门槛为 mild；'
            '|同比|>=0.30 或关注科目由正转负为 severe；'
            '同时命中同业 outside_two_std 时 dual_trigger=true 视为高风险。'
        ),
        'periods': [item.get('period_label') for item in annual],
        'items': items,
        'significant_items': significant,
        'severe_items': [item for item in significant if item['severity'] == 'severe'],
        'dual_trigger_items': [item for item in significant if item['dual_trigger']],
        'attribution': _compute_change_attribution(annual, items, metrics),
    }


def _horizontal_deviation_map(
    industry_comparisons: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """把行业对标结果映射到相关三表科目，形成横向判据（同业分位/2σ 偏离）。

    仅在有来源的行业基准可用时生效；无基准时返回空 map，横向判据置 None。
    对标以比率指标为主，这里把与科目直接相关的比率偏离挂到对应科目上，供 dual_trigger 使用。
    """
    if not industry_comparisons or not industry_comparisons.get('usable'):
        return {}
    comparisons = industry_comparisons.get('comparisons') or {}
    # 比率指标 → 相关三表科目的映射（用于把横向偏离信号落到科目上）。
    metric_to_fact = {
        'gross_profit_margin': 'inc_revenue',
        'gross_profit_margin_change': 'inc_revenue',
        'net_profit_margin': 'inc_net_profit',
        'roa': 'bs_total_assets',
        'roe': 'bs_total_equity',
        'asset_liability_ratio': 'bs_total_liabilities',
        'receivable_turnover': 'bs_accounts_receivable',
        'inventory_turnover': 'bs_inventory',
        'revenue_growth': 'inc_revenue',
    }
    mapping: dict[str, Any] = {}
    for metric_key, fact_key in metric_to_fact.items():
        comparison = comparisons.get(metric_key)
        if not comparison:
            continue
        entry = {
            'metric_key': metric_key,
            'enterprise': comparison.get('enterprise'),
            'z_score': comparison.get('z_score'),
            'outside_two_std': comparison.get('outside_two_std'),
            'benchmarks': comparison.get('benchmarks'),
            'difference_rates': comparison.get('difference_rates'),
        }
        existing = mapping.get(fact_key)
        # 同一科目命中多个比率时，保留 outside_two_std=True 的强信号。
        if existing is None or (
            entry.get('outside_two_std') is True and existing.get('outside_two_std') is not True
        ):
            mapping[fact_key] = entry
    return mapping


def _compute_change_attribution(
    annual: list[dict[str, Any]],
    items: dict[str, Any],
    metrics: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """异动归因（确定性分解）：杜邦 ROE 三因子 + 利润与经营现金流背离（利润含金量）。

    仅使用已由脚本计算的事实与指标，不做估算；无法计算的分支返回 computable=False。
    """
    metrics = metrics or {}

    def metric_value(key: str) -> Optional[float]:
        return (metrics.get(key) or {}).get('value')

    # 杜邦分解：ROE = 净利率 × 总资产周转率 × 权益乘数。
    net_margin = metric_value('net_profit_margin')
    asset_turnover = metric_value('total_asset_turnover')
    equity_multiplier = metric_value('equity_multiplier')
    dupont_computable = None not in (net_margin, asset_turnover, equity_multiplier)
    dupont = {
        'computable': dupont_computable,
        'formula': 'ROE = 净利率 × 总资产周转率 × 权益乘数',
        'roe': _round(metric_value('roe')),
        'net_profit_margin': _round(net_margin),
        'total_asset_turnover': _round(asset_turnover),
        'equity_multiplier': _round(equity_multiplier),
        'reconstructed_roe': (
            _round(net_margin * asset_turnover * equity_multiplier)
            if dupont_computable else None
        ),
    }

    # 利润—现金流背离：净利润为正而经营现金流大幅低于净利润，触发“利润含金量”归因。
    latest = annual[-1] if annual else {}
    facts = latest.get('facts') or {}
    net_profit = (facts.get('inc_net_profit') or {}).get('value')
    cfo = (facts.get('cf_operating_cash_flow') or {}).get('value')
    cfo_to_net_profit = _safe_div(cfo, net_profit)
    profit_cash_divergence = {
        'computable': net_profit is not None and cfo is not None,
        'net_profit': _round(net_profit, 2),
        'operating_cash_flow': _round(cfo, 2),
        'cfo_to_net_profit': _round(cfo_to_net_profit),
        # 经营现金流/净利润 < 1 表示利润含金量偏低；<0 表示利润未转化为现金。
        'low_earnings_quality': (
            None
            if net_profit is None or cfo is None or net_profit <= 0
            else (cfo_to_net_profit is None or cfo_to_net_profit < 1)
        ),
    }

    return {
        'dupont': dupont,
        'profit_cash_divergence': profit_cash_divergence,
    }


def compute_matched_note_details(
    statement_changes: dict[str, Any], period_results: list[dict[str, Any]]
) -> dict[str, Any]:
    significant_keys = {
        item.get('key') for item in statement_changes.get('significant_items') or []
        if item.get('key')
    }
    annual = [item for item in period_results if item.get('period_type') == 'annual'][-3:]
    matched: dict[str, Any] = {}
    for fact_key in sorted(significant_keys):
        period_records: list[Optional[dict[str, Any]]] = []
        for period in annual:
            normalized_inputs = period.get('normalized_inputs') or {}
            detail = (normalized_inputs.get('note_details') or {}).get(fact_key)
            if not detail:
                period_records.append(None)
                continue
            line_value = ((period.get('facts') or {}).get(fact_key) or {}).get('value')
            components = []
            for component in detail.get('components') or []:
                amount = component.get('amount')
                components.append({
                    'name': component.get('name'),
                    'amount': _round(amount, 2),
                    'share_of_line_item': _round(
                        _safe_div(amount, abs(line_value) if line_value is not None else None)
                    ),
                })
            components_total = sum(
                component.get('amount') for component in detail.get('components') or []
            )
            reconciliation_passed = _is_close(
                components_total,
                line_value,
                max(
                    EQ_TOLERANCE_YUAN,
                    UNIT_FACTORS[detail.get('source_unit')] * 0.02,
                ),
            )
            period_records.append({
                'period_label': period.get('period_label'),
                'line_item_amount': line_value,
                'source_ref': detail.get('source_ref'),
                'raw_text': detail.get('raw_text'),
                'components': components,
                'components_total': _round(components_total, 2),
                'reconciliation_passed': reconciliation_passed,
            })

        periods = [period for period in period_records if period is not None]
        component_changes: list[dict[str, Any]] = []
        if len(period_records) >= 2 and period_records[-2] is not None and period_records[-1] is not None:
            previous, latest = period_records[-2], period_records[-1]
            previous_map = {item['name']: item['amount'] for item in previous['components']}
            latest_map = {item['name']: item['amount'] for item in latest['components']}
            line_change = (
                None
                if previous.get('line_item_amount') is None or latest.get('line_item_amount') is None
                else latest['line_item_amount'] - previous['line_item_amount']
            )
            for name in sorted(set(previous_map) | set(latest_map)):
                previous_amount = previous_map.get(name)
                latest_amount = latest_map.get(name)
                change = (
                    None
                    if previous_amount is None or latest_amount is None
                    else latest_amount - previous_amount
                )
                component_changes.append({
                    'name': name,
                    'previous_amount': _round(previous_amount, 2),
                    'latest_amount': _round(latest_amount, 2),
                    'change_amount': _round(change, 2),
                    'contribution_to_line_item_change': _round(_safe_div(change, line_change)),
                })
        latest_detail_present = bool(period_records and period_records[-1] is not None)
        complete_for_change_analysis = bool(
            len(period_records) >= 2
            and period_records[-2] is not None
            and period_records[-1] is not None
            and period_records[-2].get('reconciliation_passed') is True
            and period_records[-1].get('reconciliation_passed') is True
        )
        matched[fact_key] = {
            'name_cn': (statement_changes.get('items') or {}).get(fact_key, {}).get('name_cn') or fact_key,
            'periods': periods,
            'component_changes': component_changes,
            'matched': latest_detail_present,
            'complete_for_change_analysis': complete_for_change_analysis,
        }
    return {
        'items': matched,
        'significant_key_count': len(significant_keys),
        'matched_key_count': sum(1 for item in matched.values() if item['matched']),
        'missing_keys': [key for key, item in matched.items() if not item['matched']],
        'incomplete_keys': [
            key for key, item in matched.items()
            if item['matched'] and not item['complete_for_change_analysis']
        ],
    }


def _metric_process(metrics: dict[str, Any]) -> dict[str, Any]:
    process: dict[str, Any] = {}
    for key, item in metrics.items():
        values = list(item['inputs'].values())
        substitution = None
        if item['computable']:
            substitution = '；'.join(f'{name}={value}' for name, value in item['inputs'].items())
        process[key] = {
            'name_cn': item['name_cn'],
            'formula': item['formula'],
            'raw_inputs_normalized_to_yuan_or_ratio': item['inputs'],
            'substitution': substitution,
            'result': item['value'],
            'value_type': item['value_type'],
            'computable': item['computable'],
            'uncomputable_reason': item['uncomputable_reason'],
            'note': item.get('note'),
            'input_count': len(values),
        }
    return process


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError('top-level JSON must be an object')
    current = normalize_period(data)
    raw_periods = data.get('comparative_periods') or []
    if not isinstance(raw_periods, list):
        raise ValueError('comparative_periods must be an array')
    normalized_periods = [normalize_period(period) for period in raw_periods]
    if current.get('period_role') != 'current':
        raise ValueError('顶层期间的 period_role 必须为 current')
    comparison_roles = [period.get('period_role') for period in normalized_periods]
    if len(comparison_roles) != len(set(comparison_roles)):
        raise ValueError('comparative_periods.period_role 不得重复')
    allowed_roles = {
        'calculation_base', 'prior_year_3', 'prior_year_2',
        'prior_year', 'prior_year_same_period',
    }
    unknown_roles = sorted(set(comparison_roles) - allowed_roles)
    if unknown_roles:
        raise ValueError('unsupported comparative period roles: ' + ', '.join(unknown_roles))
    for period in normalized_periods:
        role = period.get('period_role')
        expected_type = 'interim' if role == 'prior_year_same_period' else 'annual'
        if period.get('period_type') != expected_type:
            raise ValueError(f'{role} 的 period_type 必须为 {expected_type}')
    for period in [*normalized_periods, current]:
        role = period.get('period_role')
        if not isinstance(period.get('period_label'), str) or not period['period_label'].strip():
            raise ValueError(f'{role} 必须明确 period_label')
        if not isinstance(period.get('fiscal_year'), str) or not period['fiscal_year'].strip():
            raise ValueError(f'{role} 必须明确 fiscal_year')
        label_year, label_marker = _parse_period_text(period['period_label'])
        fiscal_year, fiscal_marker = _parse_period_text(period['fiscal_year'])
        if label_year is None or fiscal_year is None:
            raise ValueError(f'{role} 的 period_label/fiscal_year 必须包含四位年份')
        if label_year != fiscal_year or (
            label_marker is not None
            and fiscal_marker is not None
            and label_marker != fiscal_marker
        ):
            raise ValueError(f'{role} 的 period_label 与 fiscal_year 不一致')
        period_start = date.fromisoformat(period['period_start'])
        period_end = date.fromisoformat(period['period_end'])
        if label_year != period_end.year:
            raise ValueError(f'{role} 的 period_label 年份必须与 period_end 一致')
        if label_marker is not None and label_marker != f'M{period_end.month:02d}':
            raise ValueError(f'{role} 的 period_label 端点必须与 period_end 月份一致')
        if period.get('period_type') == 'interim' and label_marker is None:
            raise ValueError(f'{role} 的中期 period_label 必须明确月份或季度')
        if period.get('period_type') == 'annual':
            if (period_start.month, period_start.day) != (1, 1) or (
                period_end.month, period_end.day
            ) != (12, 31):
                raise ValueError(f'{role} 的完整年度必须覆盖自然年度起止日')
        elif (period_start.month, period_start.day) == (1, 1) and (
            period_end.month, period_end.day
        ) == (12, 31):
            raise ValueError(f'{role} 覆盖完整自然年度时 period_type 必须为 annual')
    company_name = current.get('company_name')
    if not isinstance(company_name, str) or not company_name.strip():
        raise ValueError('顶层期间必须明确 company_name')
    if company_name.strip().lower() in MISSING_TEXT_SENTINELS:
        raise ValueError('company_name 不能使用未披露/未知等占位词')
    for period in normalized_periods:
        if period.get('company_name') != company_name:
            raise ValueError(f'{period.get("period_role")} 的 company_name 与目标企业不一致')

    current_year, current_marker = _period_coordinates(current)
    if current_year is None:
        raise ValueError('当前期间必须能从 period_label 解析年份')
    role_year_offsets = {
        'prior_year': -1,
        'prior_year_2': -2,
        'prior_year_3': -3,
    }
    by_role = {period.get('period_role'): period for period in normalized_periods}
    for role, offset in role_year_offsets.items():
        period = by_role.get(role)
        if period and _period_year(period) != current_year + offset:
            raise ValueError(f'{role} 的年份必须为当前期间年份加 {offset}')
    annual_comparisons = [
        period for period in normalized_periods
        if period.get('period_role') != 'calculation_base'
        and period.get('period_type') == 'annual'
    ]
    calculation_base = by_role.get('calculation_base')
    if calculation_base and annual_comparisons:
        earliest_year = min(_period_year(period) for period in annual_comparisons)
        if _period_year(calculation_base) != earliest_year - 1:
            raise ValueError('calculation_base 必须是最早分析年度的上一完整年度')
    same_period = by_role.get('prior_year_same_period')
    if same_period:
        same_year, same_marker = _period_coordinates(same_period)
        if current.get('period_type') != 'interim':
            raise ValueError('年度当前期不得提供 prior_year_same_period')
        if current_marker is None or same_marker is None:
            raise ValueError('中期及上年同期 period_label 必须明确相同月份或季度')
        if same_year != current_year - 1 or same_marker != current_marker:
            raise ValueError('prior_year_same_period 必须与当前期端点一致且年份相差一年')
        if abs(int(same_period['period_days']) - int(current['period_days'])) > 1:
            raise ValueError('prior_year_same_period 与当前期覆盖天数相差不得超过一天')
        current_start = date.fromisoformat(current['period_start'])
        current_end = date.fromisoformat(current['period_end'])
        same_start = date.fromisoformat(same_period['period_start'])
        same_end = date.fromisoformat(same_period['period_end'])
        if (same_start.month, same_start.day) != (current_start.month, current_start.day) or (
            same_end.month, same_end.day
        ) != (current_end.month, current_end.day):
            raise ValueError('prior_year_same_period 与当前期起止月日必须一致')
    annual_sequence = [
        period for period in [*normalized_periods, current]
        if period.get('period_type') == 'annual'
    ]
    annual_years = [_period_year(period) for period in annual_sequence]
    if any(year is None for year in annual_years):
        raise ValueError('完整年度必须能从 fiscal_year 或 period_label 解析四位年份')
    if any(right <= left for left, right in zip(annual_years, annual_years[1:])):
        raise ValueError('完整年度必须按时间升序排列且不得重复')
    all_periods = [*normalized_periods, current]
    currencies = {period.get('currency') for period in all_periods}
    scopes = {period.get('statement_scope') for period in all_periods}
    if len(currencies) != 1:
        raise ValueError('所有期间必须使用同一 currency，禁止跨币种直接比较')
    if len(scopes) != 1:
        raise ValueError('所有期间必须使用同一 statement_scope，禁止混用合并与母公司口径')
    current_comparison = _choose_current_comparison(data, normalized_periods)

    period_results: list[dict[str, Any]] = []
    previous_annual: Optional[dict[str, Any]] = None
    for period in normalized_periods:
        comparison = previous_annual if period.get('period_type') == 'annual' else None
        metrics = compute_metrics(period, comparison)
        item = {
            'period_label': period.get('period_label') or period.get('fiscal_year') or '未标明',
            'fiscal_year': period.get('fiscal_year'),
            'period_type': period.get('period_type'),
            'period_role': period.get('period_role'),
            'normalized_inputs': period,
            'metrics': metrics,
            'facts': statement_facts(period),
            'consistency': compute_consistency(period),
        }
        period_results.append(item)
        if period.get('period_type') == 'annual':
            previous_annual = period

    metrics = compute_metrics(current, current_comparison)
    current_result = {
        'period_label': current.get('period_label') or current.get('fiscal_year') or '本期',
        'fiscal_year': current.get('fiscal_year'),
        'period_type': current.get('period_type'),
        'period_role': current.get('period_role') or 'current',
        'normalized_inputs': current,
        'metrics': metrics,
        'facts': statement_facts(current),
        'consistency': compute_consistency(current),
    }
    period_results.append(current_result)

    comparison_metrics = compute_metrics(current_comparison) if current_comparison else {}
    comparison_facts = statement_facts(current_comparison) if current_comparison else {}
    trends: dict[str, Any] = {}
    trend_quantities = {**metrics, **current_result['facts']}
    comparison_quantities = {**comparison_metrics, **comparison_facts}
    for key, metric_item in trend_quantities.items():
        current_value = metric_item.get('value')
        previous_value = (comparison_quantities.get(key) or {}).get('value')
        change = None if current_value is None or previous_value is None else current_value - previous_value
        trends[key] = {
            'name_cn': metric_item['name_cn'],
            'value_type': metric_item['value_type'],
            'current': current_value,
            'previous': previous_value,
            'absolute_change': _round(change),
            'relative_change': _round(_safe_div(change, abs(previous_value) if previous_value is not None else None)),
            'direction': '不可比较' if change is None else ('上升' if change > 0 else ('下降' if change < 0 else '持平')),
        }

    consistency = current_result['consistency']
    latest_annual_result = next((item for item in reversed(period_results) if item.get('period_type') == 'annual'), None)
    rule_bands = compute_rule_bands(metrics, (latest_annual_result or {}).get('metrics'))
    industry_comparisons = compute_industry_comparisons(
        metrics,
        data.get('industry_benchmarks'),
        _period_year(latest_annual_result) if latest_annual_result else None,
    )
    rule_signals = compute_rule_signals(period_results)
    margin_change_comparison = (industry_comparisons.get('comparisons') or {}).get('gross_profit_margin_change') or {}
    outside_two_std = margin_change_comparison.get('outside_two_std')
    rule_signals.append({
        'rule_id': 'BR-I01',
        'name': '毛利率变动超出行业均值正负2个标准差',
        'condition': '|企业毛利率变动-行业变动均值|/行业标准差>2',
        'triggered': outside_two_std,
        'inputs': {
            'gross_profit_margin_change': (metrics.get('gross_profit_margin_change') or {}).get('value'),
            'z_score': margin_change_comparison.get('z_score'),
        },
        'computable': outside_two_std is not None,
        'note': '机械规则信号，不等同风险评级或事实认定',
    })
    statement_changes = compute_statement_changes(
        period_results,
        abs_threshold_overrides=data.get('statement_change_abs_thresholds'),
        industry_comparisons=industry_comparisons,
        metrics=metrics,
    )
    matched_note_details = compute_matched_note_details(statement_changes, period_results)
    period_links = compute_period_links(period_results)
    standard_metric_gaps = [
        key for key in STANDARD_REPORT_METRIC_KEYS
        if not (metrics.get(key) or {}).get('computable')
    ]
    critical_uncomputable_ids = [
        item['id'] for item in consistency['checks']
        if item['severity'] == 'critical' and not item['computable']
    ]
    displayed_consistency_critical_failed = any(
        item.get('period_role') != 'calculation_base'
        and (item.get('consistency') or {}).get('critical_failed') is True
        for item in period_results
    )
    ratios = {key: item for key, item in metrics.items() if item['value_type'] != 'amount'}
    calculation_process = {
        'metrics': _metric_process(metrics),
        'trends': trends,
        'rule_signals': rule_signals,
        'rule_bands': rule_bands,
        'industry_comparisons': industry_comparisons,
        'statement_changes': statement_changes,
        'matched_note_details': matched_note_details,
        'period_links': period_links,
        'consistency': consistency,
    }
    return {
        'company_name': current.get('company_name'),
        'fiscal_year': current.get('fiscal_year'),
        'period_label': current_result['period_label'],
        'source_unit': current.get('source_unit'),
        'unit': '元',
        'normalized_inputs': current,
        'metrics': metrics,
        'ratios': ratios,
        'facts': current_result['facts'],
        'trends': trends,
        'period_results': period_results,
        'comparative_periods': period_results[:-1],
        'consistency': consistency,
        'rule_signals': rule_signals,
        'rule_bands': rule_bands,
        'industry_comparisons': industry_comparisons,
        'statement_changes': statement_changes,
        'matched_note_details': matched_note_details,
        'period_links': period_links,
        'calculation_process': calculation_process,
        'summary': {
            'computable_metric_count': sum(1 for item in metrics.values() if item['computable']),
            'metric_count': len(metrics),
            'period_count': len(period_results),
            'triggered_signal_count': sum(1 for item in rule_signals if item['triggered'] is True),
            'consistency_critical_failed': consistency['critical_failed'],
            'must_re_extract': displayed_consistency_critical_failed,
            'standard_metric_gaps': standard_metric_gaps,
            'critical_uncomputable_ids': critical_uncomputable_ids,
            'current_period_calculation_ready': (
                not consistency['critical_failed']
                and not critical_uncomputable_ids
                and not standard_metric_gaps
                and statement_changes['computable']
            ),
        },
    }


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        result = analyze(data)
        process_path = os.environ.get('AIDD_CALCULATION_PATH', '/workspace/work/financial-calculation.json')
        process_dir = os.path.dirname(process_path)
        if process_dir:
            os.makedirs(process_dir, exist_ok=True)
        with open(process_path, 'w', encoding='utf-8') as handle:
            json.dump(result['calculation_process'], handle, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        sys.exit(2)


if __name__ == '__main__':
    main()

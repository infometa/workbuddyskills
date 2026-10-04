"""财务权威表格与事实提供者（供 LLM 自由撰写报告时引用）。

设计意图
--------
本脚本是「确定性的归代码，语义性的归大模型」在报告环节的落地方式：

- **代码负责**：所有金额、比率、天数、倍数、同比、异动、勾稽、对标的**计算与排版**。
  产出可直接粘贴进报告的 Markdown 表格，以及一份「允许引用的数值事实字典」。
- **LLM 负责**：选择章节结构、把表格插入正确位置、撰写解读与结论。
  LLM **不得**自己算数、不得誊抄改写表格中的数字。

与 render.py 的分工
-------------------
render.py 走「受控 narrative + 硬编码 3 章」路线，章节固定、每段限 280 字。
本脚本不产出章节、不限制篇幅，只提供权威素材，章节结构由报告模板（模板库）决定，
成文由 LLM 完成——与 dd-profile-analysis / dd-business-analysis / dd-industry-analysis
的「LLM 自由写完整 Markdown」架构对齐。

用法
----
    # 方式一：从三表输入现算（会调用 calculate.py）
    python3 tables.py --unit 万元 < financial-input-final.json

    # 方式二：直接用已算好的 calculate.py 结果（推荐，避免重复计算）
    python3 tables.py --from-result --unit 万元 < financial-result.json

    # 只要某几张表
    python3 tables.py --from-result --only metrics,balance_sheet < financial-result.json

输出 stdout JSON::

    {
      "ok": true,
      "display_unit": "万元",
      "periods": ["2023年度", "2024年度", "2025年度"],
      "tables": {
        "balance_sheet":        {"title": "...", "markdown": "| 科目 | ... |", "available": true},
        "income_statement":     {...},
        "cash_flow":            {...},
        "metrics":              {...},
        "balance_sheet_changes":{...},
        ...
      },
      "facts": {                        # 允许 LLM 在正文中引用的数值（已格式化 + 原始值）
        "current_ratio": {"name": "流动比率", "display": "1.18", "value": 1.18, ...}
      },
      "consistency": {...},             # 三表配平校验结论（BS-01~08 / IS-01~02 / CF-01~11）
      "signals": [...],                 # 命中的规则信号
      "summary": {...}                  # 可计算性总开关，决定能否出报告
    }

红线：报告正文中出现的任何数字，都必须能在 `tables[*].markdown` 或 `facts` 中找到。
凡是这两处都没有的数字，一律不得写入报告——需要时先补充输入再重跑本脚本。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 复用 render.py 中已经过验证的表格生成与格式化实现，避免出现第二套口径。
from render import (  # noqa: E402
    CROSS_VALIDATION_METRICS,
    DISPLAY_UNIT_FACTORS,
    STANDARD_METRICS,
    _cross_validation_table,
    _format_value,
    _industry_table,
    _metric_table,
    _note_detail_tables,
    _period_headers,
    _select_display_periods,
    _signal_table,
    _statement_change_table,
    _statement_table,
)

STATEMENT_TABLES = (
    ('balance_sheet', '资产负债表'),
    ('income_statement', '利润表'),
    ('cash_flow', '现金流量表'),
)

#: 除 15 项标准指标外，额外开放给正文引用的指标（覆盖模板第四、五、七章的分析需要）
EXTRA_FACT_METRICS = (
    'net_profit_margin',
    'cash_ratio',
    'working_capital',
    'debt_to_equity',
    'equity_multiplier',
    'ebitda_interest_coverage',
    'receivable_days',
    'inventory_days',
    'payables_days',
    'cash_conversion_cycle',
    'dupont_roe',
    'cost_expense_profit_ratio',
    'gross_profit_margin_change',
    'total_asset_growth',
    'capital_accumulation',
    'accounts_receivable_growth',
    'rd_expense_ratio',
    'profit_revenue_growth_divergence',
    'sales_cash_collection_ratio',
    'cash_profit_ratio',
    'cash_to_debt_ratio',
    'total_debt_to_operating_cash',
    'free_cash_flow',
    'operating_cash_flow_amount',
    'operating_cash_to_assets',
    'cash_reserve_ratio',
    'receivables_asset_ratio',
    'inventory_asset_ratio',
    'prepaid_asset_ratio',
    'restricted_cash_ratio',
    'interest_bearing_debt_ratio',
    'short_debt_ratio',
    'current_liability_share',
    *CROSS_VALIDATION_METRICS,
)

ALL_TABLE_KEYS = (
    'balance_sheet',
    'income_statement',
    'cash_flow',
    'balance_sheet_changes',
    'income_statement_changes',
    'cash_flow_changes',
    'balance_sheet_notes',
    'income_statement_notes',
    'cash_flow_notes',
    'metrics',
    'signals',
    'industry',
    'cross_validation',
    'consistency',
)


def _table(title: str, markdown: str, note: str = '') -> dict[str, Any]:
    """统一表格产出结构；markdown 为空表示当期资料不支持该表。"""
    text = (markdown or '').strip()
    return {
        'title': title,
        'markdown': text,
        'available': bool(text),
        'note': note,
    }


SEVERITY_LABELS = {'critical': '关键', 'warning': '提示'}


def _consistency_table(result: dict[str, Any], display_unit: str) -> str:
    """三表勾稽自查表（模板第 3.4 节直接使用）。

    calculate.py 的 consistency.checks 是 list，左右值在 detail 中，
    差异由本函数按 left-right 计算（仍属确定性计算，不经 LLM）。
    """
    checks = (result.get('consistency') or {}).get('checks') or []
    if not isinstance(checks, list) or not checks:
        return ''
    lines = [
        '| 编号 | 校验项 | 左值 | 右值 | 差异 | 重要性 | 结论 |',
        '| --- | --- | ---: | ---: | ---: | :---: | :---: |',
    ]
    for check in checks:
        if not isinstance(check, dict):
            continue
        detail = check.get('detail') or {}
        left = detail.get('left')
        right = detail.get('right')
        difference: Optional[float] = None
        if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(
            right, (int, float)
        ) and not isinstance(right, bool):
            difference = float(left) - float(right)
        passed = check.get('passed')
        if passed is True:
            verdict = '通过'
        elif passed is False:
            verdict = '不通过'
        else:
            verdict = '不可校验'
        severity = str(check.get('severity') or '')
        lines.append(
            f'| {check.get("id") or "—"} | {check.get("name") or "—"} | '
            f'{_format_value(left, "amount", display_unit)} | '
            f'{_format_value(right, "amount", display_unit)} | '
            f'{_format_value(difference, "amount", display_unit)} | '
            f'{SEVERITY_LABELS.get(severity, severity or "—")} | {verdict} |'
        )
    return '\n'.join(lines) if len(lines) > 2 else ''


#: 周转率类指标在 calculate.py 中统一归为 multiple（倍），但财务惯例用「次」。
#: 仅修正 facts 的展示后缀，不改动 calculate.py 的 value_type，避免影响既有表格与后端校验。
TURNOVER_METRICS = {
    'total_asset_turnover',
    'current_asset_turnover',
    'inventory_turnover',
    'receivable_turnover',
    'fixed_asset_turnover',
}

#: 比率类指标（流动比率、速动比率等）习惯上不带单位，去掉自动附加的「倍」。
UNITLESS_RATIO_METRICS = {
    'current_ratio',
    'quick_ratio',
    'cash_ratio',
    'debt_to_equity',
    'equity_multiplier',
}


def _display_for(metric_key: str, raw_display: str) -> str:
    """按指标语义修正展示后缀：周转率用「次」，比率类不带单位。"""
    if metric_key in TURNOVER_METRICS and raw_display.endswith('倍'):
        return raw_display[:-1] + '次'
    if metric_key in UNITLESS_RATIO_METRICS and raw_display.endswith('倍'):
        return raw_display[:-1]
    return raw_display


def _fact_entry(
    metric: dict[str, Any], key: str, display_unit: str
) -> Optional[dict[str, Any]]:
    if not isinstance(metric, dict) or not metric.get('computable'):
        return None
    value_type = metric.get('value_type', 'ratio')
    return {
        'key': key,
        'name': metric.get('name_cn') or key,
        'category': metric.get('category') or '',
        'formula': metric.get('formula') or '',
        'value': metric.get('value'),
        'value_type': value_type,
        # display 已带单位/百分号/倍/次/天，正文应直接引用该字符串，避免二次换算出错
        'display': _display_for(
            key,
            _format_value(metric.get('value'), value_type, display_unit, include_unit=True),
        ),
    }


def _build_facts(
    result: dict[str, Any], periods: list[dict[str, Any]], display_unit: str
) -> dict[str, Any]:
    """汇总允许正文引用的数值事实：当期指标 + 同比 + 三表科目原值。"""
    current = periods[-1] if periods else {}
    metrics = current.get('metrics') or result.get('metrics') or {}
    previous = periods[-2] if len(periods) >= 2 else {}
    previous_metrics = previous.get('metrics') or {}

    wanted = [key for _, key in STANDARD_METRICS] + list(EXTRA_FACT_METRICS)
    facts: dict[str, Any] = {}
    for key in dict.fromkeys(wanted):  # 去重且保序
        entry = _fact_entry(metrics.get(key) or {}, key, display_unit)
        if not entry:
            continue
        prior = _fact_entry(previous_metrics.get(key) or {}, key, display_unit)
        if prior:
            entry['previous_value'] = prior['value']
            entry['previous_display'] = prior['display']
        facts[key] = entry

    # 三表科目原值（bs_/inc_/cf_/sup_/xv_ 前缀），供正文引用具体金额
    for key, fact in (current.get('facts') or result.get('facts') or {}).items():
        entry = _fact_entry(fact if isinstance(fact, dict) else {}, key, display_unit)
        if entry:
            facts.setdefault(key, entry)
    return facts


def build(payload: dict[str, Any], display_unit: str, only: Optional[set[str]]) -> dict[str, Any]:
    if display_unit not in DISPLAY_UNIT_FACTORS:
        raise ValueError(
            f'display_unit 必须是 {"/".join(DISPLAY_UNIT_FACTORS)} 之一，收到：{display_unit}'
        )

    result = payload
    if 'metrics' not in result or 'summary' not in result:
        raise ValueError(
            'stdin 不是 calculate.py 的结果（缺少 metrics/summary）；'
            '若传入的是三表输入，请去掉 --from-result 参数'
        )

    periods = _select_display_periods(result.get('period_results') or [])
    if not periods:
        # 单期材料：把当期结果本身当作唯一展示期
        periods = [result]

    def wanted(key: str) -> bool:
        return only is None or key in only

    tables: dict[str, dict[str, Any]] = {}

    for table_key, table_name in STATEMENT_TABLES:
        if wanted(table_key):
            tables[table_key] = _table(
                f'{table_name}（单位：{display_unit}）',
                _statement_table(periods, table_key, display_unit),
            )
        change_key = f'{table_key}_changes'
        if wanted(change_key):
            tables[change_key] = _table(
                f'{table_name}显著异动（单位：{display_unit}，按变动金额排序取前五）',
                _statement_change_table(result, table_key, display_unit),
                note='无显著异动或缺少可比期间时为空',
            )
        note_key = f'{table_key}_notes'
        if wanted(note_key):
            tables[note_key] = _table(
                f'{table_name}异动科目附注明细（单位：{display_unit}）',
                _note_detail_tables(result, table_key, display_unit),
                note='仅展示已匹配到附注明细的异动科目',
            )

    if wanted('metrics'):
        tables['metrics'] = _table(
            '标准财务指标（15 项）',
            _metric_table(periods, display_unit),
        )
    if wanted('consistency'):
        tables['consistency'] = _table(
            '三表勾稽校验',
            _consistency_table(result, display_unit),
        )
    if wanted('signals'):
        tables['signals'] = _table(
            '命中的财务规则信号',
            _signal_table(result),
            note='机械规则信号，不等于风险认定或评级结论',
        )
    if wanted('industry'):
        tables['industry'] = _table(
            '同业对标',
            _industry_table(result, display_unit),
            note='仅在已确认行业基准（P4）且样本可用时输出',
        )
    if wanted('cross_validation'):
        tables['cross_validation'] = _table(
            '外部交叉验证',
            _cross_validation_table(result, display_unit),
            note='仅展示可计算项；流水/税务等私有材料缺失时为空',
        )

    consistency = result.get('consistency') or {}
    consistency_checks = consistency.get('checks') or []
    failed_ids = [
        str(item.get('id'))
        for item in consistency_checks
        if isinstance(item, dict) and item.get('computable') and item.get('passed') is False
    ]
    uncheckable_ids = [
        str(item.get('id'))
        for item in consistency_checks
        if isinstance(item, dict) and not item.get('computable')
    ]
    signals = [
        {
            'rule_id': item.get('rule_id'),
            'name': item.get('name'),
            'condition': item.get('condition'),
            'severity': item.get('severity'),
        }
        for item in (result.get('rule_signals') or [])
        if isinstance(item, dict) and item.get('triggered') is True
    ]

    return {
        'ok': True,
        'company_name': result.get('company_name'),
        'display_unit': display_unit,
        'source_unit': result.get('source_unit'),
        'periods': _period_headers(periods),
        'tables': tables,
        'facts': _build_facts(result, periods, display_unit),
        'consistency': {
            'all_computable_checks_passed': consistency.get('all_computable_checks_passed'),
            'critical_failed': consistency.get('critical_failed'),
            'failed_count': consistency.get('failed_count'),
            'critical_uncomputable_count': consistency.get('critical_uncomputable_count'),
            'failed_ids': failed_ids,
            'uncheckable_ids': uncheckable_ids,
        },
        'signals': signals,
        'industry_usable': bool((result.get('industry_comparisons') or {}).get('usable')),
        'summary': result.get('summary') or {},
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description='输出财务权威 Markdown 表格与可引用数值事实',
    )
    parser.add_argument(
        '--unit',
        default='万元',
        help=f'展示单位，可选 {"/".join(DISPLAY_UNIT_FACTORS)}（默认万元）',
    )
    parser.add_argument(
        '--from-result',
        action='store_true',
        help='stdin 已是 calculate.py 的结果；缺省则视为三表输入并先调用 calculate',
    )
    parser.add_argument(
        '--only',
        default='',
        help=f'只输出指定表格，逗号分隔。可选：{",".join(ALL_TABLE_KEYS)}',
    )
    args = parser.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({'ok': False, 'error': 'empty stdin'}, ensure_ascii=False))
        sys.exit(2)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                {'ok': False, 'error': f'stdin 不是合法 JSON：第 {exc.lineno} 行：{exc.msg}'},
                ensure_ascii=False,
            )
        )
        sys.exit(2)

    if not isinstance(payload, dict):
        print(json.dumps({'ok': False, 'error': 'top-level JSON must be an object'}, ensure_ascii=False))
        sys.exit(2)

    only: Optional[set[str]] = None
    if args.only.strip():
        only = {item.strip() for item in args.only.split(',') if item.strip()}
        unknown = only - set(ALL_TABLE_KEYS)
        if unknown:
            print(
                json.dumps(
                    {'ok': False, 'error': f'--only 含未知表格：{", ".join(sorted(unknown))}'},
                    ensure_ascii=False,
                )
            )
            sys.exit(2)

    try:
        if not args.from_result:
            from calculate import analyze  # 局部导入：--from-result 时无需重算

            payload = analyze(payload)
        report = build(payload, args.unit, only)
    except (ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False))
        sys.exit(2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

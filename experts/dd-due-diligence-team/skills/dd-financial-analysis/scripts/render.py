"""将权威计算结果与 LLM 定性分析渲染为报告 JSON 和 Word 文档。"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculate import STATEMENT_FIELDS, UNIT_FACTORS, analyze  # noqa: E402


REPORTS_DIR = os.environ.get('AIDD_REPORTS_DIR', '/workspace/reports')
ENGINE = 'dd-financial-analysis/render.py'
POLICY = 'sandbox-only-numeric-computation/v1'
VERSION = '2.5.0'

DISPLAY_UNIT_FACTORS = {
    '元': 1.0,
    '千元': 1_000.0,
    '万元': 10_000.0,
    '百万元': 1_000_000.0,
    '亿元': 100_000_000.0,
}

CORE_NARRATIVE_KEYS = {
    'balance_sheet_analysis',
    'income_statement_analysis',
    'cash_flow_analysis',
    'solvency_analysis',
    'operating_efficiency_analysis',
    'profitability_analysis',
    'growth_analysis',
    'risk_analysis',
    'analysis_summary',
}
CONDITIONAL_NARRATIVE_KEYS = {'industry_comparison', 'cross_validation'}
LEGACY_NARRATIVE_KEYS = {'analysis_basis', 'limitations'}
NARRATIVE_KEYS = CORE_NARRATIVE_KEYS | CONDITIONAL_NARRATIVE_KEYS | LEGACY_NARRATIVE_KEYS
NARRATIVE_MAX_CHARS = 280
SUMMARY_MAX_CHARS = 360
NARRATIVE_MAX_SENTENCES = 4
NARRATIVE_MAX_PLACEHOLDERS = 6
STATEMENT_CHANGE_DISPLAY_LIMIT = 5
SIGNAL_DISPLAY_LIMIT = 5
PROCESS_PROSE_TERMS = (
    '本报告', '本节', '资料不足', '材料不足', '未提供', '缺少', '缺失', '待补',
    '补件', '待核验', '来源定位', '检索过程', '未执行', '无法验证', '无法核验',
    '不作推测', '不构成授信', '详见', '脚本', '模型', 'LLM', 'AI', '占位符',
)
FORMULAIC_PROSE_TERMS = (
    '综上所述', '综合来看', '总体来看', '整体来看', '值得注意的是', '需要指出的是',
    '从上述分析可以看出', '由此可见',
)

RESEARCH_MODES = {'provided-only', 'auto-enrich', 'full-research'}
RESEARCH_STATUSES = {
    'not-run', 'not-needed', 'completed', 'no-usable-result', 'network-unavailable',
}
RESEARCH_SOURCE_TYPES = {
    'official_exchange', 'official_regulator', 'official_government', 'company_ir',
    'industry_association', 'authorized_database', 'research_report', 'media',
}
RESEARCH_EVIDENCE_SCOPES = {'company_fact', 'industry_benchmark', 'context'}
RESEARCH_EVIDENCE_USES = {'numeric', 'narrative', 'lead-only'}
NON_COMPANY_DOC_TYPES = {'public_industry_source', 'public_context'}
NON_COMPANY_SOURCE_UNITS = {'ratio', 'not-applicable'}
NUMERIC_PUBLIC_SOURCE_TYPES = {
    'official_exchange', 'official_regulator', 'official_government', 'company_ir',
    'industry_association', 'authorized_database', 'research_report',
}
SHA256_RE = re.compile(r'^sha256:[a-f0-9]{64}$')
PUBLIC_ENRICHABLE_TABLES = {
    'balance_sheet', 'opening_balance_sheet', 'income_statement', 'cash_flow',
    'financial_supplement', 'opening_financial_supplement',
}
PRIVATE_ONLY_DOC_KEYWORDS = (
    '银行流水', '对账单', '余额证明', '纳税申报', '完税证明', '发票底账',
    '逐户应收', '期后回款', '盘点底稿', '内部台账', '借款合同', '授信方案',
)

STANDARD_METRICS = (
    ('偿债能力', 'debt_ratio'),
    ('偿债能力', 'current_ratio'),
    ('偿债能力', 'quick_ratio'),
    ('偿债能力', 'interest_coverage'),
    ('偿债能力', 'operating_cash_ratio'),
    ('营运能力', 'total_asset_turnover'),
    ('营运能力', 'current_asset_turnover'),
    ('营运能力', 'inventory_turnover'),
    ('营运能力', 'receivable_turnover'),
    ('盈利能力', 'gross_profit_margin'),
    ('盈利能力', 'net_profit_margin'),
    ('盈利能力', 'roa'),
    ('盈利能力', 'roe'),
    ('发展潜力', 'revenue_growth'),
    ('发展潜力', 'net_profit_growth'),
)

REQUIRED_REPORT_FIELDS = {
    'balance_sheet': (
        'cash_and_equivalents', 'prepaid_accounts', 'accounts_receivable',
        'inventory', 'current_assets', 'fixed_assets', 'intangible_assets',
        'non_current_assets', 'total_assets', 'short_term_borrowings',
        'accounts_payable', 'noncurrent_liabilities_due_within_one_year',
        'current_liabilities', 'non_current_liabilities', 'total_liabilities',
        'retained_earnings', 'total_equity',
    ),
    'opening_balance_sheet': (
        'accounts_receivable', 'inventory', 'current_assets', 'fixed_assets',
        'total_assets', 'total_equity',
    ),
    'income_statement': (
        'revenue', 'cost_of_revenue', 'selling_expense', 'admin_expense',
        'finance_expense', 'interest_expense', 'operating_profit', 'total_profit',
        'income_tax', 'net_profit',
    ),
    'cash_flow': (
        'sales_cash_received', 'operating_cash_inflow', 'operating_cash_outflow',
        'operating_cash_flow', 'investing_cash_inflow', 'investing_cash_outflow',
        'investing_cash_flow', 'capital_expenditure', 'financing_cash_inflow',
        'financing_cash_outflow', 'financing_cash_flow', 'exchange_effect',
        'cash_change', 'cash_begin', 'cash_end',
    ),
}

CROSS_VALIDATION_METRICS = (
    'revenue_vat_difference_rate',
    'bank_collection_ratio',
    'profit_taxable_difference_rate',
    'effective_income_tax_rate',
    'tax_paid_to_expense_ratio',
    'cost_utility_ratio',
    'payroll_social_security_base_difference_rate',
    'asset_registry_difference_rate',
)

PLACEHOLDER_RE = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(?::\s*([a-zA-Z0-9_]+)\s*)?\}\}')
BARE_FINANCIAL_RE = re.compile(
    r'[-+]?\d[\d,]*(?:\.\d+)?\s*(?:%|％|元|千元|万元|百万元|亿元|倍|天|次)'
    r'|[-+]?\d[\d,]*\.\d+(?![\w])'
    r'|百分之[零〇一二三四五六七八九十百千万亿两点]+'
    r'|[零〇一二三四五六七八九十两][零〇一二三四五六七八九十百千万亿两点]*'
    r'(?:元|千元|万元|百万元|亿元|倍|天|成|个百分点|年|个月|月|日|季度|期|笔|家|户|项|次(?!性)|个)'
    r'|[零〇一二三四五六七八九十百千万亿两]+分之[零〇一二三四五六七八九十百千万亿两]+'
    r'|[零〇一二三四五六七八九十百千万亿两]+半'
    r'|半(?:年|个月|月|期)|过半|半数|大半|翻倍|双倍|成倍|翻番'
)
ARABIC_NUMBER_RE = re.compile(r'(?<![A-Za-z_])[-+]?\d[\d,]*(?:\.\d+)?')
ALLOWED_DATE_RE = re.compile(
    r'(?<!\d)(?:19|20)\d{2}(?:'
    r'年(?:'
    r'(?:0?[1-9]|1[0-2])月(?:(?:0?[1-9]|[12]\d|3[01])日?)?'
    r'|第?[一二三四]季度|上半年|下半年|度|末)?'
    r'|[/.-](?:0?[1-9]|1[0-2])(?:[/.-](?:0?[1-9]|[12]\d|3[01]))?'
    r'|Q[1-4])(?!\d)',
    re.IGNORECASE,
)
ALLOWED_CHINESE_DATE_RE = re.compile(
    r'[〇零一二三四五六七八九]{4}年(?:'
    r'[一二三四五六七八九十]{1,3}月(?:[一二三四五六七八九十]{1,3}日)?'
    r'|第?[一二三四]季度|上半年|下半年|度|末)?'
)
ALLOWED_SOURCE_ID_RE = re.compile(r'(?:第\s*)?\d+\s*(?:页|号|章|节|附注)')
ALLOWED_FILE_RE = re.compile(r'\S*\d\S*\.(?:pdf|docx?|xlsx?|csv)', re.IGNORECASE)
LIST_MARKER_RE = re.compile(r'(?m)^\s*\d+[.)、]\s*')
LITERAL_UNIT_SUFFIX_RE = re.compile(
    r'^\s*[（(\[]?\s*(?:%|％|(?:人民币\s*)?(?:元|千元|万元|百万元|亿元)|倍|天|次)'
)


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _digest(value: Any) -> str:
    return 'sha256:' + hashlib.sha256(_stable_json(value).encode('utf-8')).hexdigest()


def _mask_allowed_numbers(text: str) -> str:
    masked = ALLOWED_DATE_RE.sub('日期', text)
    masked = ALLOWED_CHINESE_DATE_RE.sub('日期', masked)
    masked = ALLOWED_SOURCE_ID_RE.sub('来源定位', masked)
    masked = ALLOWED_FILE_RE.sub('材料文件', masked)
    return LIST_MARKER_RE.sub('列表项 ', masked)


def _contains_uncontrolled_number(text: str) -> bool:
    masked = _mask_allowed_numbers(text)
    return bool(ARABIC_NUMBER_RE.search(masked) or BARE_FINANCIAL_RE.search(masked))


def _walk_meta_scalars(value: Any, path: str = 'meta') -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, str) or (
        isinstance(value, (int, float)) and not isinstance(value, bool)
    ):
        found.append((path, value))
    elif isinstance(value, dict):
        for key, item in value.items():
            found.extend(_walk_meta_scalars(item, f'{path}.{key}'))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk_meta_scalars(item, f'{path}[{index}]'))
    return found


def _validate_meta_numbers(meta: dict[str, Any]) -> None:
    for path, value in _walk_meta_scalars(meta):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            raise ValueError(f'{path} 含未通过脚本字段/占位符控制的数值')
        text = str(value)
        if path.startswith('meta.credit_context'):
            if _contains_uncontrolled_number(text):
                raise ValueError(f'{path} 含未通过脚本字段/占位符控制的数值')
        elif BARE_FINANCIAL_RE.search(_mask_allowed_numbers(text)):
            raise ValueError(f'{path} 含未通过脚本字段控制的财务数值')


def _has_computable_cross_validation(result: dict[str, Any]) -> bool:
    metrics = result.get('metrics') or {}
    return any((metrics.get(key) or {}).get('computable') for key in CROSS_VALIDATION_METRICS)


def _required_narrative_keys(result: dict[str, Any]) -> set[str]:
    required = set(CORE_NARRATIVE_KEYS)
    if (result.get('industry_comparisons') or {}).get('usable'):
        required.add('industry_comparison')
    if _has_computable_cross_validation(result):
        required.add('cross_validation')
    return required


def _validate_narrative_style(narrative: dict[str, Any]) -> None:
    """把正文限制为简洁结论稿，过程信息由 reviewRegister 统一承载。"""
    errors: list[str] = []
    visible_keys = CORE_NARRATIVE_KEYS | CONDITIONAL_NARRATIVE_KEYS
    for key in sorted(visible_keys):
        value = narrative.get(key)
        if not _nonempty_string(value):
            continue
        text = value.strip()
        limit = SUMMARY_MAX_CHARS if key == 'analysis_summary' else NARRATIVE_MAX_CHARS
        if len(text) > limit:
            errors.append(f'narrative.{key} 超过 {limit} 字符')
        if '\n' in text or text.startswith(('#', '-', '*', '>')) or '|' in text:
            errors.append(f'narrative.{key} 必须是单段正文，不能包含标题、列表或表格')
        sentence_count = len(re.findall(r'[。！？!?]', text))
        if sentence_count > NARRATIVE_MAX_SENTENCES:
            errors.append(
                f'narrative.{key} 超过 {NARRATIVE_MAX_SENTENCES} 句，请只保留判断、关键事实和信贷影响'
            )
        placeholder_count = len(PLACEHOLDER_RE.findall(text))
        if placeholder_count > NARRATIVE_MAX_PLACEHOLDERS:
            errors.append(
                f'narrative.{key} 引用指标过多，请保留不超过 {NARRATIVE_MAX_PLACEHOLDERS} 个决定性数值'
            )
        process_terms = [term for term in PROCESS_PROSE_TERMS if term in text]
        if process_terms:
            errors.append(
                f'narrative.{key} 含过程性表述：{", ".join(process_terms)}；请移入资料与核验事项'
            )
        formulaic_terms = [term for term in FORMULAIC_PROSE_TERMS if term in text]
        if formulaic_terms:
            errors.append(
                f'narrative.{key} 含套话：{", ".join(formulaic_terms)}；请直接陈述结论'
            )
    if errors:
        raise ValueError('；'.join(errors))


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _default_public_research() -> dict[str, Any]:
    return {
        'mode': 'provided-only',
        'status': 'not-run',
        'network_attempted': False,
        'queries': [],
        'sources': [],
        'enrichments': [],
        'conflicts': [],
    }


def _period_by_role(inputs: dict[str, Any], role: str) -> Optional[dict[str, Any]]:
    periods = [*(inputs.get('comparative_periods') or []), inputs]
    matches = [
        period for period in periods
        if isinstance(period, dict) and period.get('period_role') == role
    ]
    if len(matches) > 1:
        raise ValueError(f'period_role {role} 不得重复')
    return matches[0] if matches else None


def _research_target(
    inputs: dict[str, Any], period_role: str, field: str
) -> tuple[Any, Optional[dict[str, Any]], Optional[dict[str, Any]]]:
    """返回目标值、所属期间和字段级来源引用。"""
    parts = field.split('.')
    if period_role == 'industry_benchmark':
        if len(parts) != 4 or parts[:2] != ['industry_benchmarks', 'metrics']:
            raise ValueError(f'公开增强字段路径不受支持：{field}')
        benchmark = inputs.get('industry_benchmarks') or {}
        value = ((benchmark.get('metrics') or {}).get(parts[2]) or {}).get(parts[3])
        return value, None, None

    period = _period_by_role(inputs, period_role)
    if period is None:
        return None, None, None
    if len(parts) != 2:
        raise ValueError(f'公开增强字段路径不受支持：{field}')
    table, key = parts
    if table in PUBLIC_ENRICHABLE_TABLES:
        value = (period.get(table) or {}).get(key)
        ref = (period.get('source_refs') or {}).get(field)
        return value, period, ref
    if table == 'note_details':
        detail = (period.get('note_details') or {}).get(key)
        ref = detail.get('source_ref') if isinstance(detail, dict) else None
        return detail, period, ref
    raise ValueError(f'公开增强字段路径不受支持：{field}')


def _target_has_numeric_data(value: Any) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(math.isfinite(float(value)))
    if isinstance(value, dict):
        components = value.get('components')
        return isinstance(components, list) and any(
            isinstance(item, dict)
            and isinstance(item.get('amount'), (int, float))
            and not isinstance(item.get('amount'), bool)
            and math.isfinite(float(item['amount']))
            for item in components
        )
    return False


def _public_numeric_deltas(
    initial_inputs: dict[str, Any], final_inputs: dict[str, Any]
) -> set[tuple[str, str]]:
    deltas: set[tuple[str, str]] = set()
    final_roles = [
        period.get('period_role')
        for period in [*(final_inputs.get('comparative_periods') or []), final_inputs]
        if isinstance(period, dict) and _nonempty_string(period.get('period_role'))
    ]
    identity_fields = (
        'company_name', 'period_label', 'period_type', 'period_start', 'period_end',
        'period_days', 'statement_scope', 'currency', 'source_unit',
    )
    for role in final_roles:
        final_period = _period_by_role(final_inputs, role)
        initial_period = _period_by_role(initial_inputs, role)
        if final_period is None:
            continue
        if initial_period is not None:
            for field_name in identity_fields:
                if initial_period.get(field_name) != final_period.get(field_name):
                    raise ValueError(f'公开增强不得改写 {role}.{field_name}')
            if _stable_json(initial_period.get('cross_validation') or {}) != _stable_json(
                final_period.get('cross_validation') or {}
            ):
                raise ValueError('公开增强不得改写流水、税务或发票交叉验证字段')
        elif final_period.get('cross_validation'):
            raise ValueError('联网新增期间不得包含流水、税务或发票交叉验证字段')

        for table in PUBLIC_ENRICHABLE_TABLES:
            initial_table = (initial_period or {}).get(table) or {}
            final_table = final_period.get(table) or {}
            for key in set(initial_table) | set(final_table):
                initial_value = initial_table.get(key)
                final_value = final_table.get(key)
                if initial_value == final_value:
                    continue
                if initial_value is not None:
                    raise ValueError(f'公开增强不得覆盖首次输入已有值：{role}.{table}.{key}')
                if final_value is not None:
                    if not _target_has_numeric_data(final_value):
                        raise ValueError(f'公开增强目标不是有限数值：{role}.{table}.{key}')
                    deltas.add((role, f'{table}.{key}'))

        initial_notes = (initial_period or {}).get('note_details') or {}
        final_notes = final_period.get('note_details') or {}
        for key in set(initial_notes) | set(final_notes):
            initial_value = initial_notes.get(key)
            final_value = final_notes.get(key)
            if _stable_json(initial_value) == _stable_json(final_value):
                continue
            if initial_value is not None:
                raise ValueError(f'公开增强不得覆盖首次输入已有值：{role}.note_details.{key}')
            if final_value is not None:
                if not _target_has_numeric_data(final_value):
                    raise ValueError(f'公开增强附注明细没有可计算金额：{role}.note_details.{key}')
                deltas.add((role, f'note_details.{key}'))

    initial_metrics = ((initial_inputs.get('industry_benchmarks') or {}).get('metrics') or {})
    final_metrics = ((final_inputs.get('industry_benchmarks') or {}).get('metrics') or {})
    for metric in set(initial_metrics) | set(final_metrics):
        initial_values = initial_metrics.get(metric) or {}
        final_values = final_metrics.get(metric) or {}
        for benchmark_type in set(initial_values) | set(final_values):
            initial_value = initial_values.get(benchmark_type)
            final_value = final_values.get(benchmark_type)
            if initial_value == final_value:
                continue
            field = f'industry_benchmarks.metrics.{metric}.{benchmark_type}'
            if initial_value is not None:
                raise ValueError(f'公开增强不得覆盖首次输入已有值：{field}')
            if final_value is not None:
                if not _target_has_numeric_data(final_value):
                    raise ValueError(f'公开增强目标不是有限数值：{field}')
                deltas.add(('industry_benchmark', field))
    return deltas


def _validate_public_research(
    inputs: dict[str, Any], initial_inputs: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    raw = inputs.get('public_research')
    if raw is None:
        raise ValueError('最终输入必须显式提供 public_research，不能隐式回退为 provided-only')
    if not isinstance(raw, dict):
        raise ValueError('public_research 必须是对象')
    if 'enriched_fields' in raw:
        raise ValueError('public_research.enriched_fields 已废止，请使用可溯源的 enrichments')

    research = {**_default_public_research(), **raw}
    mode = research.get('mode')
    status = research.get('status')
    attempted = research.get('network_attempted')
    queries = research.get('queries')
    sources = research.get('sources')
    enrichments = research.get('enrichments')
    conflicts = research.get('conflicts')

    if mode not in RESEARCH_MODES:
        raise ValueError('public_research.mode 不受支持')
    if status not in RESEARCH_STATUSES:
        raise ValueError('public_research.status 不受支持')
    if not isinstance(attempted, bool):
        raise ValueError('public_research.network_attempted 必须为布尔值')
    for name, value in (
        ('queries', queries), ('sources', sources),
        ('enrichments', enrichments), ('conflicts', conflicts),
    ):
        if not isinstance(value, list):
            raise ValueError(f'public_research.{name} 必须为数组')

    if mode == 'provided-only':
        if status != 'not-run' or attempted or queries or sources or enrichments or conflicts:
            raise ValueError('provided-only 模式不得记录联网查询、新增来源或增强字段')
    elif status == 'not-run':
        raise ValueError('auto-enrich/full-research 不能使用 not-run 状态')
    if mode in {'auto-enrich', 'full-research'} and not isinstance(initial_inputs, dict):
        raise ValueError('auto-enrich/full-research 渲染必须同时提供 initial_inputs')
    if status == 'not-needed' and (attempted or queries or sources or enrichments or conflicts):
        raise ValueError('not-needed 状态不得包含联网查询或新增来源')
    if status == 'completed' and (not attempted or not queries or not sources):
        raise ValueError('completed 状态必须实际联网、记录查询并至少登记一个合格来源')
    if status == 'no-usable-result' and (not attempted or not queries or sources or enrichments):
        raise ValueError('no-usable-result 必须记录查询且不得登记已采用来源或增强字段')
    if status == 'network-unavailable' and (
        not attempted or sources or enrichments or not _nonempty_string(research.get('failure_reason'))
    ):
        raise ValueError('network-unavailable 状态不得登记已采用来源或增强字段')

    query_ids: set[str] = set()
    query_outcomes: dict[str, str] = {}
    for index, query in enumerate(queries):
        if not isinstance(query, dict):
            raise ValueError(f'public_research.queries[{index}] 必须是对象')
        for field in ('query_id', 'query', 'purpose', 'outcome'):
            if not _nonempty_string(query.get(field)):
                raise ValueError(f'public_research.queries[{index}].{field} 不能为空')
        query_id = query['query_id'].strip()
        if query_id in query_ids:
            raise ValueError(f'public_research.queries[{index}].query_id 不得重复')
        query_ids.add(query_id)
        if query.get('outcome') not in {'accepted', 'rejected', 'no-result'}:
            raise ValueError(f'public_research.queries[{index}].outcome 不受支持')
        query_outcomes[query_id] = query['outcome']
    if status == 'completed' and 'accepted' not in query_outcomes.values():
        raise ValueError('completed 状态至少需要一条 outcome=accepted 的查询')
    if status == 'no-usable-result' and 'accepted' in query_outcomes.values():
        raise ValueError('no-usable-result 不得包含 outcome=accepted 的查询')

    source_ids: set[str] = set()
    source_by_id: dict[str, dict[str, Any]] = {}
    manifest = inputs.get('material_manifest') or []
    forbidden_payload_keys = {'value', 'amount', 'metrics', 'financial_data', 'raw_values'}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f'public_research.sources[{index}] 必须是对象')
        if forbidden_payload_keys & set(source):
            raise ValueError(
                f'public_research.sources[{index}] 只能保存来源元数据，不能保存待计算财务数值'
            )
        required = (
            'source_id', 'query_id', 'source_type', 'evidence_scope', 'evidence_use', 'title',
            'publisher', 'url', 'publication_date', 'retrieved_at', 'period',
            'locator', 'entity_match',
        )
        for field in required:
            if not _nonempty_string(source.get(field)):
                raise ValueError(f'public_research.sources[{index}].{field} 不能为空')
        source_id = source['source_id'].strip()
        if source_id in source_ids:
            raise ValueError(f'public_research.sources[{index}].source_id 不得重复')
        source_ids.add(source_id)
        source_by_id[source_id] = source
        query_id = source['query_id'].strip()
        if query_id not in query_ids or query_outcomes.get(query_id) != 'accepted':
            raise ValueError(f'public_research.sources[{index}].query_id 必须引用 accepted 查询')
        source_type = source.get('source_type')
        evidence_scope = source.get('evidence_scope')
        evidence_use = source.get('evidence_use')
        if source_type not in RESEARCH_SOURCE_TYPES:
            raise ValueError(f'public_research.sources[{index}].source_type 不受支持')
        if evidence_scope not in RESEARCH_EVIDENCE_SCOPES:
            raise ValueError(f'public_research.sources[{index}].evidence_scope 不受支持')
        if evidence_use not in RESEARCH_EVIDENCE_USES:
            raise ValueError(f'public_research.sources[{index}].evidence_use 不受支持')
        if not source['url'].startswith('https://'):
            raise ValueError(f'public_research.sources[{index}].url 必须使用 HTTPS 原始来源')
        if source_type == 'media' and evidence_use != 'lead-only':
            raise ValueError(f'public_research.sources[{index}] 媒体来源只能作为 lead-only')
        if evidence_scope == 'company_fact':
            if source.get('entity_match') != 'confirmed':
                raise ValueError(f'public_research.sources[{index}] 公司事实主体必须已确认')
            if source.get('company_name') != inputs.get('company_name'):
                raise ValueError(f'public_research.sources[{index}].company_name 与目标企业不一致')
            identity = inputs.get('entity_identity')
            if not isinstance(identity, dict) or identity.get('legal_name') != inputs.get('company_name'):
                raise ValueError('公司事实公开来源要求 entity_identity.legal_name 与目标企业一致')
            if initial_inputs is not None and initial_inputs.get('entity_identity') != identity:
                raise ValueError('公司主体标识必须在首次计算前确定，公开增强阶段不得改写')
            identifiers = [
                key for key in ('security_code', 'uscc') if _nonempty_string(identity.get(key))
            ]
            if not identifiers or not any(source.get(key) == identity.get(key) for key in identifiers):
                raise ValueError(
                    f'public_research.sources[{index}] 必须匹配证券代码或统一社会信用代码'
                )
        elif source.get('entity_match') not in {'confirmed', 'not-applicable'}:
            raise ValueError(f'public_research.sources[{index}].entity_match 不受支持')
        if evidence_use == 'numeric':
            if source_type not in NUMERIC_PUBLIC_SOURCE_TYPES or source_type == 'media':
                raise ValueError(f'public_research.sources[{index}] 来源不得用于数值')
            if source_type == 'research_report' and evidence_scope != 'industry_benchmark':
                raise ValueError(f'public_research.sources[{index}] 研究报告只能用于合格行业基准数值')
            if not _nonempty_string(source.get('local_file')):
                raise ValueError(f'public_research.sources[{index}].local_file 不能为空')
            if not SHA256_RE.fullmatch(str(source.get('sha256') or '')):
                raise ValueError(f'public_research.sources[{index}].sha256 格式非法')
            local_file = os.path.abspath(source['local_file'])
            if not os.path.isfile(local_file):
                raise ValueError(f'public_research.sources[{index}].local_file 不存在')
            digest = hashlib.sha256()
            with open(local_file, 'rb') as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                    digest.update(chunk)
            actual_sha256 = 'sha256:' + digest.hexdigest()
            if actual_sha256 != source.get('sha256'):
                raise ValueError(f'public_research.sources[{index}].sha256 与本地文件不一致')
            matching_manifest = [
                item for item in manifest
                if isinstance(item, dict)
                and item.get('source_origin') == 'public-research'
                and item.get('source_id') == source_id
                and item.get('usable') is True
                and item.get('file_name') == os.path.basename(local_file)
                and os.path.abspath(str(item.get('local_file') or '')) == local_file
                and item.get('sha256') == actual_sha256
                and item.get('period') == source.get('period')
                and all(
                    source.get(field_name) is None
                    or item.get(field_name) == source.get(field_name)
                    for field_name in ('statement_scope', 'currency', 'source_unit')
                )
            ]
            if not matching_manifest:
                raise ValueError(
                    f'public_research.sources[{index}] 数值来源必须以同文件、期间和摘要登记到 material_manifest'
                )

    if status == 'completed' and not any(
        source.get('evidence_use') in {'numeric', 'narrative'} for source in sources
    ):
        raise ValueError('completed 状态至少需要一个可用于数值或叙述的合格来源')

    for index, item in enumerate(manifest):
        if not isinstance(item, dict) or item.get('source_origin') != 'public-research':
            continue
        if item.get('source_id') not in source_ids:
            raise ValueError(f'material_manifest[{index}] 引用了未知公开来源')
        doc_type = str(item.get('doc_type') or '')
        if any(keyword in doc_type for keyword in PRIVATE_ONLY_DOC_KEYWORDS):
            raise ValueError(f'material_manifest[{index}] 公开来源不得声明为非公开材料')

    enrichment_keys: set[tuple[str, str]] = set()
    for index, enrichment in enumerate(enrichments):
        if not isinstance(enrichment, dict):
            raise ValueError(f'public_research.enrichments[{index}] 必须是对象')
        for field_name in ('period_role', 'field', 'source_id', 'merge_action'):
            if not _nonempty_string(enrichment.get(field_name)):
                raise ValueError(f'public_research.enrichments[{index}].{field_name} 不能为空')
        if enrichment.get('merge_action') != 'fill-null':
            raise ValueError(f'public_research.enrichments[{index}] 只允许 fill-null')
        key = (enrichment['period_role'], enrichment['field'])
        if key in enrichment_keys:
            raise ValueError(f'public_research.enrichments[{index}] 目标字段不得重复')
        enrichment_keys.add(key)
        source = source_by_id.get(enrichment['source_id'])
        if not source or source.get('evidence_use') != 'numeric':
            raise ValueError(f'public_research.enrichments[{index}] 必须引用 numeric 合格来源')
        value, period, ref = _research_target(inputs, *key)
        if not _target_has_numeric_data(value):
            raise ValueError(f'public_research.enrichments[{index}] 目标字段不存在或无数值')
        initial_value = None
        if initial_inputs is not None:
            initial_value, _, _ = _research_target(initial_inputs, *key)
        if initial_value is not None:
            raise ValueError(f'public_research.enrichments[{index}] 不得覆盖首次输入已有值')

        if enrichment['period_role'] == 'industry_benchmark':
            benchmark = inputs.get('industry_benchmarks') or {}
            if source.get('evidence_scope') != 'industry_benchmark':
                raise ValueError(f'public_research.enrichments[{index}] 行业字段必须引用行业基准来源')
            if source.get('period') != benchmark.get('as_of_period'):
                raise ValueError(f'public_research.enrichments[{index}] 行业来源期间不匹配')
            if not all(_nonempty_string(source.get(name)) for name in ('sample', 'methodology')):
                raise ValueError(f'public_research.enrichments[{index}] 行业来源缺少样本或方法')
            benchmark_source = next(
                (
                    item for item in (benchmark.get('sources') or [])
                    if isinstance(item, dict)
                    and item.get('source_id') == enrichment['source_id']
                    and item.get('source_origin') == 'public-research'
                ),
                None,
            )
            if benchmark_source is None:
                raise ValueError(f'public_research.enrichments[{index}] 未链接行业基准来源')
        else:
            if period is None or source.get('evidence_scope') != 'company_fact':
                raise ValueError(f'public_research.enrichments[{index}] 公司字段缺少目标期间或主体来源')
            if source.get('period') != period.get('period_label'):
                raise ValueError(f'public_research.enrichments[{index}] 来源期间不匹配')
            for field_name in ('statement_scope', 'currency', 'source_unit'):
                if source.get(field_name) != period.get(field_name):
                    raise ValueError(
                        f'public_research.enrichments[{index}] 来源 {field_name} 与目标期间不匹配'
                    )
            if not isinstance(ref, dict):
                raise ValueError(f'public_research.enrichments[{index}] 缺少字段级 source_ref')
            if (
                ref.get('source_id') != enrichment['source_id']
                or ref.get('source_origin') != 'public-research'
            ):
                raise ValueError(f'public_research.enrichments[{index}] source_ref 未链接同一公开来源')

    if initial_inputs is not None:
        numeric_deltas = _public_numeric_deltas(initial_inputs, inputs)
        if numeric_deltas != enrichment_keys:
            missing_links = sorted(numeric_deltas - enrichment_keys)
            stale_links = sorted(enrichment_keys - numeric_deltas)
            details = []
            if missing_links:
                details.append(f'未登记增强字段：{missing_links}')
            if stale_links:
                details.append(f'无实际增量字段：{stale_links}')
            raise ValueError('；'.join(details))

    for index, conflict in enumerate(conflicts):
        if not isinstance(conflict, dict):
            raise ValueError(f'public_research.conflicts[{index}] 必须是对象')
        for field_name in ('period_role', 'field', 'source_id', 'resolution'):
            if not _nonempty_string(conflict.get(field_name)):
                raise ValueError(f'public_research.conflicts[{index}].{field_name} 不能为空')
        if conflict.get('resolution') != 'kept-provided':
            raise ValueError(f'public_research.conflicts[{index}] 必须保留进件值')
        if conflict.get('source_id') not in source_ids:
            raise ValueError(f'public_research.conflicts[{index}] 引用未知公开来源')
        key = (conflict['period_role'], conflict['field'])
        if key in enrichment_keys:
            raise ValueError(f'public_research.conflicts[{index}] 冲突字段不得同时列为增强字段')
        final_value, _, _ = _research_target(inputs, *key)
        if final_value is None:
            raise ValueError(f'public_research.conflicts[{index}] 冲突字段在最终输入中不存在')
        if initial_inputs is not None:
            initial_value, _, _ = _research_target(initial_inputs, *key)
            if initial_value is None or initial_value != final_value:
                raise ValueError(f'public_research.conflicts[{index}] 未证明保留首次输入值')

    return research


def _validate_evidence(inputs: dict[str, Any]) -> None:
    manifest = inputs.get('material_manifest')
    if not isinstance(manifest, list) or not manifest:
        raise ValueError('完整报告必须提供非空 material_manifest')
    usable_sources: dict[tuple[str, str], list[dict[str, Any]]] = {}

    def is_financial_doc_type(doc_type: str) -> bool:
        return (
            '财务报表' in doc_type
            or '审计报告' in doc_type
            or doc_type in {'audit_report', 'financial_statements', 'annual_report'}
        )

    for index, item in enumerate(manifest):
        if not isinstance(item, dict):
            raise ValueError(f'material_manifest[{index}] 必须是对象')
        for field in ('file_name', 'doc_type', 'period', 'statement_scope', 'currency', 'source_unit'):
            if not _nonempty_string(item.get(field)):
                raise ValueError(f'material_manifest[{index}].{field} 不能为空')
        non_company_doc = item.get('doc_type') in NON_COMPANY_DOC_TYPES
        allowed_units = set(UNIT_FACTORS) | (NON_COMPANY_SOURCE_UNITS if non_company_doc else set())
        if item.get('source_unit') not in allowed_units:
            raise ValueError(f'material_manifest[{index}].source_unit 不受支持')
        if not isinstance(item.get('usable'), bool):
            raise ValueError(f'material_manifest[{index}].usable 必须为布尔值')
        if item['usable']:
            if non_company_doc:
                if item.get('currency') != 'not-applicable':
                    raise ValueError(f'material_manifest[{index}].currency 必须为 not-applicable')
                if item.get('statement_scope') != 'not-applicable':
                    raise ValueError(
                        f'material_manifest[{index}].statement_scope 必须为 not-applicable'
                    )
            else:
                if item.get('currency') != inputs.get('currency'):
                    raise ValueError(f'material_manifest[{index}].currency 与报告币种不一致')
                if item.get('statement_scope') != inputs.get('statement_scope'):
                    raise ValueError(f'material_manifest[{index}].statement_scope 与报告口径不一致')
            key = (item['file_name'].strip(), item['period'].strip())
            usable_sources.setdefault(key, []).append(item)
    if not usable_sources:
        raise ValueError('material_manifest 至少需要一份 usable=true 的材料')
    if not any(
        is_financial_doc_type(item['doc_type'])
        for items in usable_sources.values()
        for item in items
    ):
        raise ValueError('material_manifest 至少需要一份可用财务报表或审计报告')

    def validate_ref(
        ref: Any,
        path: str,
        expected_period: str,
        expected_unit: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if not isinstance(ref, dict):
            raise ValueError(f'{path} 必须是包含文件和定位的对象')
        file_name = ref.get('file') or ref.get('file_name')
        if not _nonempty_string(file_name):
            raise ValueError(f'{path} 缺少 file')
        locator_fields = ('page', 'sheet', 'range', 'section', 'ref')
        if not any(
            _nonempty_string(ref.get(field))
            or (
                isinstance(ref.get(field), (int, float))
                and not isinstance(ref.get(field), bool)
            )
            for field in locator_fields
        ):
            raise ValueError(f'{path} 缺少页码、表名、区域、章节或引用定位')
        source_items = usable_sources.get((file_name.strip(), expected_period))
        if not source_items:
            raise ValueError(f'{path} 引用文件未登记对应报告期 {expected_period}')
        if expected_unit is not None and not any(
            item.get('source_unit') == expected_unit for item in source_items
        ):
            raise ValueError(f'{path} 引用文件的单位与结构化输入不一致')
        return source_items

    def validate_refs(
        refs: Any,
        path: str,
        expected_period: str,
        expected_unit: str,
    ) -> None:
        if not isinstance(refs, dict) or not refs:
            raise ValueError(f'{path} 必须是非空对象')
        financial_match = False
        for key, ref in refs.items():
            source_items = validate_ref(ref, f'{path}.{key}', expected_period)
            financial_match = financial_match or any(
                is_financial_doc_type(item['doc_type'])
                and item.get('source_unit') == expected_unit
                for item in source_items
            )
        if not financial_match:
            raise ValueError(f'{path} 必须引用同期间、同单位的财务报表或审计报告')

    validate_refs(
        inputs.get('source_refs'),
        'source_refs',
        str(inputs.get('period_label')),
        str(inputs.get('source_unit')),
    )
    for index, period in enumerate(inputs.get('comparative_periods') or []):
        refs = period.get('source_refs') if isinstance(period, dict) else None
        validate_refs(
            refs,
            f'comparative_periods[{index}].source_refs',
            str(period.get('period_label')),
            str(period.get('source_unit')),
        )
    for index, period in enumerate([*(inputs.get('comparative_periods') or []), inputs]):
        for fact_key, detail in (period.get('note_details') or {}).items():
            validate_ref(
                detail.get('source_ref') if isinstance(detail, dict) else None,
                f'periods[{index}].note_details.{fact_key}.source_ref',
                str(period.get('period_label')),
                str(detail.get('source_unit')) if isinstance(detail, dict) else None,
            )


def _validate_payload_controls(
    inputs: dict[str, Any],
    narrative: dict[str, Any],
    meta: dict[str, Any],
    initial_inputs: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    _validate_meta_numbers(meta)
    public_research = _validate_public_research(inputs, initial_inputs)
    if meta.get('company_name') not in (None, inputs.get('company_name')):
        raise ValueError('meta.company_name 必须与 inputs.company_name 一致')
    context = meta.get('business_context') or {}
    if not isinstance(context, dict):
        raise ValueError('meta.business_context must be an object')
    credit = meta.get('credit_context') or {}
    if not isinstance(credit, dict):
        raise ValueError('meta.credit_context must be an object')
    for field in (
        'industry', 'stage', 'business_model', 'statement_scope',
        'audit_opinion', 'accounting_standard',
    ):
        if context.get(field) is not None and not _nonempty_string(context.get(field)):
            raise ValueError(f'meta.business_context.{field} must be a non-empty string')
    for field in ('purpose', 'repayment_arrangement', 'guarantee_structure'):
        if credit.get(field) is not None and not _nonempty_string(credit.get(field)):
            raise ValueError(f'meta.credit_context.{field} must be a non-empty string')
    if context.get('statement_scope') not in (None, inputs.get('statement_scope')):
        raise ValueError('meta.business_context.statement_scope 必须与 inputs.statement_scope 一致')
    return public_research


def _verified_renderability_issues(
    inputs: dict[str, Any],
    result: dict[str, Any],
    narrative: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    try:
        _validate_evidence(inputs)
    except (ValueError, TypeError) as exc:
        issues.append(str(exc))

    missing_narratives = sorted(
        key for key in _required_narrative_keys(result)
        if not _nonempty_string(narrative.get(key))
    )
    if missing_narratives:
        issues.append('完整报告缺少 narrative：' + ', '.join(missing_narratives))

    periods = result.get('period_results') or []
    roles = {item.get('period_role') for item in periods[:-1]}
    required_roles = {'calculation_base', 'prior_year', 'prior_year_2'}
    if inputs.get('period_type') == 'interim':
        required_roles |= {'prior_year_3', 'prior_year_same_period'}
    missing_roles = sorted(required_roles - roles)
    if missing_roles:
        issues.append('完整报告缺少比较期角色：' + ', '.join(missing_roles))
    annual = [item for item in periods if item.get('period_type') == 'annual']
    if len(annual) < 3:
        issues.append('完整报告至少需要三个完整年度')
    if not (result.get('statement_changes') or {}).get('computable'):
        issues.append('近三个完整年度不连续，无法执行财务科目异动规则')
    if inputs.get('period_type') == 'interim' and not any(
        item.get('period_role') == 'prior_year_same_period' for item in periods[:-1]
    ):
        issues.append('中期完整报告必须提供上年同期')

    displayed_periods = _select_display_periods(periods)
    for period in periods:
        if period.get('period_role') != 'calculation_base':
            continue
        failed_base_critical = [
            item for item in (period.get('consistency') or {}).get('checks') or []
            if item.get('severity') == 'critical'
            and item.get('computable')
            and item.get('passed') is False
        ]
        if failed_base_critical:
            issues.append('calculation_base 存在已计算但未通过的 critical 勾稽')
    standard_keys = [key for _, key in STANDARD_METRICS]
    non_growth_keys = [
        key for key in standard_keys if key not in {'revenue_growth', 'net_profit_growth'}
    ]
    for period in displayed_periods:
        normalized = period.get('normalized_inputs') or {}
        missing_fields = [
            f'{table_key}.{field}'
            for table_key, fields in REQUIRED_REPORT_FIELDS.items()
            for field in fields
            if not isinstance((normalized.get(table_key) or {}).get(field), (int, float))
            or isinstance((normalized.get(table_key) or {}).get(field), bool)
        ]
        if missing_fields:
            issues.append(
                f'{period.get("period_label")} 缺少标准报告必需原始字段：'
                + ', '.join(missing_fields)
            )
        required_metric_keys = (
            non_growth_keys
            if period.get('period_role') == 'prior_year_same_period'
            else standard_keys
        )
        period_metrics = period.get('metrics') or {}
        missing_metrics = [
            key for key in required_metric_keys
            if not (period_metrics.get(key) or {}).get('computable')
        ]
        if missing_metrics:
            issues.append(
                f'{period.get("period_label")} 存在不可计算的标准指标：' + ', '.join(missing_metrics)
            )

    note_match = result.get('matched_note_details') or {}
    note_gaps = [
        *(note_match.get('missing_keys') or []),
        *(note_match.get('incomplete_keys') or []),
    ]
    if note_gaps:
        issues.append('显著异动科目缺少完整的相邻年度附注明细：' + ', '.join(sorted(set(note_gaps))))

    for period in displayed_periods:
        critical = [
            item for item in (period.get('consistency') or {}).get('checks') or []
            if item.get('severity') == 'critical'
        ]
        label = period.get('period_label') or '未标明期间'
        if not critical or any(not item.get('computable') for item in critical):
            issues.append(f'{label} 的 critical 三表勾稽必须全部可计算')
        elif any(item.get('passed') is not True for item in critical):
            issues.append(f'{label} 的 critical 三表勾稽失败；报告只能作为有限材料分析')

    return list(dict.fromkeys(issues))


def _select_display_periods(period_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not period_results:
        return []
    current = period_results[-1]
    prior = [
        item for item in period_results[:-1]
        if item.get('period_role') != 'calculation_base'
    ]
    annual = [item for item in prior if item.get('period_type') == 'annual'][-3:]
    same_period = [item for item in prior if item.get('period_role') == 'prior_year_same_period'][-1:]
    selected = annual + same_period + [current]
    seen: set[int] = set()
    deduplicated: list[dict[str, Any]] = []
    for item in selected:
        marker = id(item)
        if marker not in seen:
            deduplicated.append(item)
            seen.add(marker)
    eligible_count = len(prior) + 1
    if len(deduplicated) < min(5, eligible_count):
        for item in reversed(prior):
            if id(item) not in seen:
                deduplicated.insert(0, item)
                seen.add(id(item))
            if len(deduplicated) >= min(5, eligible_count):
                break
    return deduplicated[-5:]


def _format_value(
    value: Any, value_type: str, display_unit: str, include_unit: bool = False
) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return '—'
    number = float(value)
    if value_type == 'amount':
        formatted = f'{number / DISPLAY_UNIT_FACTORS[display_unit]:,.2f}'
        return f'{formatted}{display_unit}' if include_unit else formatted
    if value_type == 'percentage':
        return f'{number * 100:.2f}%'
    if value_type == 'days':
        return f'{number:.1f}天'
    if value_type == 'multiple':
        return f'{number:.2f}倍' if include_unit else f'{number:.2f}'
    return f'{number:.4f}'


def _quantity(period: dict[str, Any], key: str) -> Optional[dict[str, Any]]:
    return (period.get('metrics') or {}).get(key) or (period.get('facts') or {}).get(key)


def _resolve_narrative(
    text: str,
    result: dict[str, Any],
    periods: list[dict[str, Any]],
    display_unit: str,
    errors: list[str],
) -> str:
    for placeholder in PLACEHOLDER_RE.finditer(text):
        fmt = placeholder.group(2) or 'value'
        if fmt not in {'name', 'formula'} and LITERAL_UNIT_SUFFIX_RE.match(text[placeholder.end():]):
            errors.append('数值占位符后不得硬编码单位；渲染器会按 display_unit 自动附加')
    remainder = PLACEHOLDER_RE.sub('', text)
    if _contains_uncontrolled_number(remainder):
        errors.append('narrative 含未通过占位符引用的数值（仅日期、报告期和来源定位可裸写）')
    if '{{' in remainder or '}}' in remainder:
        errors.append('narrative 含非法或未闭合占位符')

    current_quantities = {**(result.get('metrics') or {}), **(result.get('facts') or {})}

    def replace(match: re.Match[str]) -> str:
        key, fmt = match.group(1), match.group(2) or 'value'
        if fmt.startswith('period_'):
            try:
                index = int(fmt.removeprefix('period_'))
                period = periods[index]
            except (ValueError, IndexError):
                errors.append(f'无效期间占位符：{key}:{fmt}')
                return match.group(0)
            period_item = _quantity(period, key)
            if not period_item:
                return '—'
            return _format_value(
                period_item.get('value'),
                period_item.get('value_type', 'ratio'),
                display_unit,
                include_unit=True,
            )

        item = current_quantities.get(key)
        if not item:
            errors.append(f'未知数值占位符：{key}')
            return match.group(0)
        if fmt in {'value', 'pct'}:
            return _format_value(
                item.get('value'), item.get('value_type', 'ratio'), display_unit, include_unit=True
            )
        if fmt == 'name':
            return str(item.get('name_cn') or key)
        if fmt == 'formula':
            return str(item.get('formula') or '材料披露值')
        if fmt in {'current', 'previous', 'change', 'relative_change', 'direction'}:
            trend = (result.get('trends') or {}).get(key)
            if not trend:
                errors.append(f'指标 {key} 没有同比结果')
                return match.group(0)
            if fmt == 'direction':
                return str(trend.get('direction') or '不可比较')
            source_key = 'absolute_change' if fmt == 'change' else fmt
            value = trend.get(source_key)
            value_type = 'percentage' if fmt == 'relative_change' else trend.get('value_type', item.get('value_type', 'ratio'))
            return _format_value(value, value_type, display_unit, include_unit=True)
        errors.append(f'不支持的占位符格式：{key}:{fmt}')
        return match.group(0)

    return PLACEHOLDER_RE.sub(replace, text)


def _period_headers(periods: list[dict[str, Any]]) -> list[str]:
    return [str(item.get('period_label') or '未标明') for item in periods]


def _statement_table(periods: list[dict[str, Any]], table_key: str, display_unit: str) -> str:
    headers = _period_headers(periods)
    lines = [
        '| 科目名称 | ' + ' | '.join(headers) + ' |',
        '| --- | ' + ' | '.join('---:' for _ in headers) + ' |',
    ]
    for field, name in STATEMENT_FIELDS[table_key]:
        values = []
        for period in periods:
            table = (period.get('normalized_inputs') or {}).get(table_key) or {}
            values.append(_format_value(table.get(field), 'amount', display_unit))
        lines.append(f'| {name} | ' + ' | '.join(values) + ' |')
    return '\n'.join(lines)


def _metric_table(periods: list[dict[str, Any]], display_unit: str) -> str:
    headers = _period_headers(periods)
    lines = [
        '| 指标大类 | 指标名称 | ' + ' | '.join(headers) + ' |',
        '| --- | --- | ' + ' | '.join('---:' for _ in headers) + ' |',
    ]
    current_metrics = (periods[-1].get('metrics') or {}) if periods else {}
    for category, key in STANDARD_METRICS:
        name = (current_metrics.get(key) or {}).get('name_cn') or key
        values = []
        for period in periods:
            item = (period.get('metrics') or {}).get(key) or {}
            values.append(_format_value(item.get('value'), item.get('value_type', 'ratio'), display_unit))
        lines.append(f'| {category} | {name} | ' + ' | '.join(values) + ' |')
    return '\n'.join(lines)


def _signal_table(result: dict[str, Any]) -> str:
    signals = [
        signal for signal in (result.get('rule_signals') or [])
        if signal.get('triggered') is True
    ][:SIGNAL_DISPLAY_LIMIT]
    if not signals:
        return ''
    lines = ['| 规则 | 条件 | 机械结果 |', '| --- | --- | :---: |']
    for signal in signals:
        lines.append(
            f'| {_escape_cell(signal.get("rule_id"))} {_escape_cell(signal.get("name"))} | '
            f'{_escape_cell(signal.get("condition"))} | 命中 |'
        )
    return '\n'.join(lines)


def _industry_table(result: dict[str, Any], display_unit: str) -> str:
    industry = result.get('industry_comparisons') or {}
    if not industry.get('usable'):
        return ''
    lines = [
        '| 指标 | 企业值 | 均值 | 中位数 | 优秀值 | 较弱值 | 同业值 | 相对均值差异 | Z 值 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for key, comparison in (industry.get('comparisons') or {}).items():
        metric = (result.get('metrics') or {}).get(key) or {}
        value_type = metric.get('value_type', 'ratio')
        benchmarks = comparison.get('benchmarks') or {}
        differences = comparison.get('difference_rates') or {}
        lines.append(
            f'| {metric.get("name_cn") or key} | '
            f'{_format_value(comparison.get("enterprise"), value_type, display_unit)} | '
            f'{_format_value(benchmarks.get("mean"), value_type, display_unit)} | '
            f'{_format_value(benchmarks.get("median"), value_type, display_unit)} | '
            f'{_format_value(benchmarks.get("excellent"), value_type, display_unit)} | '
            f'{_format_value(benchmarks.get("weak"), value_type, display_unit)} | '
            f'{_format_value(benchmarks.get("peer"), value_type, display_unit)} | '
            f'{_format_value(differences.get("mean"), "percentage", display_unit)} | '
            f'{_format_value(comparison.get("z_score"), "ratio", display_unit)} |'
        )
    return '\n'.join(lines)


def _display_statement_changes(result: dict[str, Any], table_key: str) -> list[dict[str, Any]]:
    items = [
        item for item in (result.get('statement_changes') or {}).get('significant_items') or []
        if item.get('table') == table_key
    ]

    def change_amount(item: dict[str, Any]) -> float:
        latest = item.get('latest')
        previous = item.get('previous')
        if isinstance(latest, (int, float)) and not isinstance(latest, bool) and isinstance(
            previous, (int, float)
        ) and not isinstance(previous, bool):
            return abs(float(latest) - float(previous))
        return -1.0

    return sorted(
        items,
        key=lambda item: (-change_amount(item), str(item.get('key') or '')),
    )[:STATEMENT_CHANGE_DISPLAY_LIMIT]


def _statement_change_table(
    result: dict[str, Any], table_key: str, display_unit: str
) -> str:
    changes = result.get('statement_changes') or {}
    items = _display_statement_changes(result, table_key)
    if not items:
        return ''
    periods = changes.get('periods') or ['最早年度', '上一年度', '最近年度']
    lines = [
        f'| 科目 | {periods[0]} | {periods[1]} | {periods[2]} | 最近年度同比 | 三年复合变化 |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
    ]
    for item in items:
        values = item.get('values') or [None, None, None]
        lines.append(
            f'| {item.get("name_cn")} | '
            f'{_format_value(values[0], "amount", display_unit)} | '
            f'{_format_value(values[1], "amount", display_unit)} | '
            f'{_format_value(values[2], "amount", display_unit)} | '
            f'{_format_value(item.get("yoy_change"), "percentage", display_unit)} | '
            f'{_format_value(item.get("compound_change"), "percentage", display_unit)} |'
        )
    return '\n'.join(lines)


def _escape_cell(value: Any) -> str:
    if value is None:
        return '—'
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    return text.replace('|', '\\|').replace('\n', ' ')


def _note_detail_tables(
    result: dict[str, Any], table_key: str, display_unit: str
) -> str:
    matched = (result.get('matched_note_details') or {}).get('items') or {}
    relevant_keys = [
        item.get('key') for item in _display_statement_changes(result, table_key)
        if item.get('key')
    ]
    if not relevant_keys:
        return ''
    sections: list[str] = []
    for fact_key in relevant_keys:
        detail = matched.get(fact_key) or {}
        if not detail.get('matched'):
            continue
        periods = detail.get('periods') or []
        latest = periods[-1]
        latest_components = {
            item.get('name'): item for item in latest.get('components') or []
        }
        lines = [
            f'#### {detail.get("name_cn") or fact_key}附注明细',
            '',
            '| 明细项 | 上期金额 | 本期金额 | 变动金额 | 本期科目占比 | 对科目变动贡献 |',
            '| --- | ---: | ---: | ---: | ---: | ---: |',
        ]
        component_changes = detail.get('component_changes') or []
        if component_changes:
            for component in component_changes:
                latest_component = latest_components.get(component.get('name')) or {}
                lines.append(
                    f'| {_escape_cell(component.get("name"))} | '
                    f'{_format_value(component.get("previous_amount"), "amount", display_unit)} | '
                    f'{_format_value(component.get("latest_amount"), "amount", display_unit)} | '
                    f'{_format_value(component.get("change_amount"), "amount", display_unit)} | '
                    f'{_format_value(latest_component.get("share_of_line_item"), "percentage", display_unit)} | '
                    f'{_format_value(component.get("contribution_to_line_item_change"), "percentage", display_unit)} |'
                )
        else:
            for component in latest.get('components') or []:
                lines.append(
                    f'| {_escape_cell(component.get("name"))} | — | '
                    f'{_format_value(component.get("amount"), "amount", display_unit)} | — | '
                    f'{_format_value(component.get("share_of_line_item"), "percentage", display_unit)} | — |'
                )
        sections.append('\n'.join(lines))
    return '\n\n'.join(sections)


def _cross_validation_table(result: dict[str, Any], display_unit: str) -> str:
    metrics = result.get('metrics') or {}
    available = [key for key in CROSS_VALIDATION_METRICS if (metrics.get(key) or {}).get('computable')]
    if not available:
        return ''
    lines = ['| 验证指标 | 计算结果 | 公式 |', '| --- | ---: | --- |']
    for key in available:
        item = metrics.get(key) or {}
        lines.append(
            f'| {_escape_cell(item.get("name_cn") or key)} | '
            f'{_format_value(item.get("value"), item.get("value_type", "ratio"), display_unit)} | '
            f'{_escape_cell(item.get("formula") or "—")} |'
        )
    return '\n'.join(lines)


def _section(title: str, body: Optional[str]) -> str:
    return '' if not body else f'### {title}\n\n{body}'


def _missing_materials(
    inputs: dict[str, Any],
    result: dict[str, Any],
    meta: dict[str, Any],
) -> list[dict[str, str]]:
    manifest = inputs.get('material_manifest') or []
    private_doc_types = ' '.join(
        str(item.get('doc_type') or '').lower()
        for item in manifest
        if isinstance(item, dict)
        and item.get('usable') is not False
        and item.get('source_origin') not in {'public-research', 'existing-public-file'}
    )

    def has_doc(*needles: str) -> bool:
        return any(needle.lower() in private_doc_types for needle in needles)

    def metric_missing(*keys: str) -> bool:
        metrics = result.get('metrics') or {}
        return any(not (metrics.get(key) or {}).get('computable') for key in keys)

    missing: list[dict[str, str]] = []

    def add(category: str, required: str, impact: str) -> None:
        if not any(item['category'] == category for item in missing):
            missing.append({'category': category, 'required': required, 'impact': impact})

    if metric_missing('bank_collection_ratio') or not has_doc('银行流水', '对账单'):
        add(
            '银行流水与资金证明',
            '主要经营账户流水、对账单、余额及受限资金证明',
            '无法核验真实经营回款、可动用资金和资金用途',
        )
    if metric_missing(
        'revenue_vat_difference_rate', 'profit_taxable_difference_rate',
        'tax_paid_to_expense_ratio',
    ) or not has_doc('税', '纳税'):
        add(
            '税务资料',
            '增值税、企业所得税申报表及完税证明',
            '无法用纳税数据交叉验证收入、利润和现金流',
        )
    if not has_doc('发票', '合同', '订单'):
        add(
            '发票与交易链',
            '销进项发票底账及主要合同、订单、出入库、物流和验收资料',
            '无法验证交易真实性、收入截止性和增长原因',
        )
    if metric_missing('top_five_receivables_ratio', 'receivables_over_one_year_ratio'):
        add(
            '应收账款质量',
            '逐户账龄、逾期、客户集中度、关联方及期后回款明细',
            '无法评价集中度、逾期和可回收性',
        )
    if not has_doc('盘点', '存货明细', '库龄'):
        add(
            '存货质量',
            '存货分类、库龄、盘点、跌价及期后销售明细',
            '无法核验存货存在性、计价和变现能力',
        )
    if metric_missing('interest_bearing_debt_ratio', 'short_debt_ratio', 'restricted_cash_ratio'):
        add(
            '债务与受限资产',
            '借款及授信清单、利率、到期日、还款计划、担保和受限资产明细',
            '无法评价期限错配、峰值偿债压力和风险缓释',
        )
    if not (result.get('industry_comparisons') or {}).get('usable'):
        add(
            '行业基准',
            '有年份、样本定义和来源的行业统计及可比企业数据',
            '无法进行数值行业对标',
        )
    credit = meta.get('credit_context') or {}
    if not all(_nonempty_string(credit.get(key)) for key in (
        'purpose', 'repayment_arrangement', 'guarantee_structure',
    )):
        add(
            '授信方案',
            '申请用途、期限、提款与还款安排、担保结构及抵质押资料',
            '无法评价融资需求、授信覆盖和期限匹配',
        )
    note_match = result.get('matched_note_details') or {}
    if (note_match.get('missing_keys') or []) or (note_match.get('incomplete_keys') or []):
        add(
            '重大异动附注',
            '显著异动科目的相邻年度构成、来源定位及可勾稽明细',
            '异动原因只能作为待核验线索，不能认定为已核验事实',
        )
    if (result.get('summary') or {}).get('standard_metric_gaps'):
        add(
            '核心财务字段',
            '不可计算指标对应的原始报表字段、期初余额或上年同期数据',
            '相关指标在报告中显示为不可计算',
        )
    return missing


def _stable_id(prefix: str, value: Any) -> str:
    return f'{prefix}-' + _digest(value).split(':', 1)[1][:12]


def _build_source_index(
    inputs: dict[str, Any], public_research: dict[str, Any]
) -> list[dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    public_by_id = {
        item.get('source_id'): item
        for item in public_research.get('sources') or []
        if isinstance(item, dict) and _nonempty_string(item.get('source_id'))
    }
    for item in inputs.get('material_manifest') or []:
        if not isinstance(item, dict) or item.get('usable') is False:
            continue
        origin = item.get('source_origin') or 'provided'
        source_id = item.get('source_id') or _stable_id('provided', {
            'file_name': item.get('file_name'),
            'period': item.get('period'),
            'doc_type': item.get('doc_type'),
            'origin': origin,
        })
        public = public_by_id.get(item.get('source_id')) or {}
        sources[source_id] = {
            'sourceId': source_id,
            'origin': origin,
            'documentType': item.get('doc_type'),
            'displayName': item.get('file_name'),
            'publisher': public.get('publisher'),
            'url': public.get('url'),
            'period': item.get('period'),
            'locator': public.get('locator'),
            'evidenceUse': public.get('evidence_use') or (
                'numeric' if is_financial_manifest_item(item) else 'narrative'
            ),
        }
    for item in public_research.get('sources') or []:
        if not isinstance(item, dict) or not _nonempty_string(item.get('source_id')):
            continue
        source_id = item['source_id'].strip()
        sources.setdefault(source_id, {
            'sourceId': source_id,
            'origin': 'public-research',
            'documentType': item.get('evidence_scope'),
            'displayName': item.get('title'),
            'publisher': item.get('publisher'),
            'url': item.get('url'),
            'period': item.get('period'),
            'locator': item.get('locator'),
            'evidenceUse': item.get('evidence_use'),
        })
    for item in (inputs.get('industry_benchmarks') or {}).get('sources') or []:
        if not isinstance(item, dict):
            continue
        source_id = item.get('source_id') or _stable_id('industry', {
            'name': item.get('name'), 'ref': item.get('ref'), 'sample': item.get('sample'),
        })
        sources.setdefault(source_id, {
            'sourceId': source_id,
            'origin': item.get('source_origin') or 'provided',
            'documentType': 'industry_benchmark',
            'displayName': item.get('name'),
            'publisher': item.get('name'),
            'url': None,
            'period': (inputs.get('industry_benchmarks') or {}).get('as_of_period'),
            'locator': item.get('ref'),
            'evidenceUse': 'numeric',
        })
    return sorted(sources.values(), key=lambda item: str(item.get('sourceId') or ''))


def is_financial_manifest_item(item: dict[str, Any]) -> bool:
    doc_type = str(item.get('doc_type') or '')
    return (
        '财务报表' in doc_type
        or '审计报告' in doc_type
        or doc_type in {'audit_report', 'financial_statements', 'annual_report'}
    )


def _note_gap_names(result: dict[str, Any]) -> list[str]:
    note_match = result.get('matched_note_details') or {}
    details = note_match.get('items') or {}
    keys = [*(note_match.get('missing_keys') or []), *(note_match.get('incomplete_keys') or [])]
    names: list[str] = []
    for key in keys:
        name = (details.get(key) or {}).get('name_cn') or key
        if name not in names:
            names.append(str(name))
    return names


def _build_review_register(
    inputs: dict[str, Any],
    result: dict[str, Any],
    public_research: dict[str, Any],
    renderability_issues: list[str],
    missing_materials: list[dict[str, str]],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    note_gaps = _note_gap_names(result)
    for item in missing_materials:
        details = note_gaps if item.get('category') == '重大异动附注' else []
        items.append({
            'itemId': _stable_id('gap', item),
            'kind': 'missing-evidence',
            'status': 'open',
            'blocking': 'evidence',
            'audience': 'report',
            'category': item.get('category'),
            'details': details,
            'impact': item.get('impact'),
            'requiredAction': item.get('required'),
            'owner': 'borrower-or-bank',
            'sourceIds': [],
            'decision': {'disposition': 'limited-report'},
        })

    missing_categories = {item.get('category') for item in missing_materials}
    for issue in _human_renderability_items(renderability_issues):
        if (
            ('显著异动科目' in issue and '重大异动附注' in missing_categories)
            or ('核心财务字段' in issue and '核心财务字段' in missing_categories)
        ):
            continue
        items.append({
            'itemId': _stable_id('limit', issue),
            'kind': 'calculation-limit',
            'status': 'open',
            'blocking': 'structure',
            'audience': 'trace-only' if '定性分析' in issue else 'report',
            'category': '数据与计算边界',
            'details': [],
            'impact': issue,
            'requiredAction': '补齐或更正对应基础数据后重新计算',
            'owner': 'analyst',
            'sourceIds': [],
            'decision': {'disposition': 'limited-report'},
        })

    for conflict in public_research.get('conflicts') or []:
        if not isinstance(conflict, dict):
            continue
        source_id = conflict.get('source_id')
        items.append({
            'itemId': _stable_id('conflict', conflict),
            'kind': 'source-conflict',
            'status': 'open',
            'blocking': 'evidence',
            'audience': 'report',
            'category': '来源冲突',
            'details': [f'{conflict.get("period_role")} / {conflict.get("field")}'],
            'impact': '公开来源与进件记录不一致，当前计算保留进件值',
            'requiredAction': conflict.get('resolution') or '核对原始材料并确认最终口径',
            'owner': 'analyst',
            'sourceIds': [source_id] if _nonempty_string(source_id) else [],
            'decision': {'disposition': 'kept-provided-for-calculation'},
        })

    status = public_research.get('status')
    if status in {'no-usable-result', 'network-unavailable'}:
        reason = public_research.get('failure_reason') or (
            '定向检索未取得可采用来源'
            if status == 'no-usable-result' else '联网工具不可用'
        )
        items.append({
            'itemId': _stable_id('research', {'status': status, 'reason': reason}),
            'kind': 'research-decision',
            'status': 'accepted-limitation',
            'blocking': 'advisory',
            'audience': 'trace-only',
            'category': '公开资料检索',
            'details': [],
            'impact': reason,
            'requiredAction': '保留未解决缺口',
            'owner': 'system',
            'sourceIds': [],
            'decision': {'disposition': 'continue-with-provided-materials'},
        })

    return {
        'version': '1.0',
        'sources': _build_source_index(inputs, public_research),
        'items': items,
    }


def _missing_materials_from_register(register: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            'category': str(item.get('category') or ''),
            'required': str(item.get('requiredAction') or ''),
            'impact': str(item.get('impact') or ''),
        }
        for item in register.get('items') or []
        if item.get('kind') == 'missing-evidence' and item.get('status') == 'open'
    ]


def _human_renderability_items(issues: list[str]) -> list[str]:
    summaries: list[str] = []
    for issue in issues:
        if '缺少 narrative' in issue:
            text = '部分定性分析未提供，已使用有限报告默认说明'
        elif '显著异动科目缺少' in issue:
            text = '显著异动科目缺少完整的相邻年度附注明细'
        elif 'material_manifest' in issue or 'source_refs' in issue:
            text = '材料清单或来源定位未达到已核验报告要求'
        elif '标准报告必需原始字段' in issue or '不可计算的标准指标' in issue:
            text = '部分核心财务字段或标准指标不可计算'
        elif 'critical' in issue:
            text = '关键三表勾稽未全部通过或不可计算'
        elif '比较期角色' in issue or '完整年度' in issue or '上年同期' in issue:
            text = '比较期间未达到已核验报告要求'
        else:
            text = issue
        if text not in summaries:
            summaries.append(text)
    return summaries


def build_report(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = payload.get('inputs')
    initial_inputs = payload.get('initial_inputs')
    meta = payload.get('meta') or {}
    narrative = payload.get('narrative') or {}
    if not isinstance(inputs, dict):
        raise ValueError('missing "inputs"')
    if initial_inputs is not None and not isinstance(initial_inputs, dict):
        raise ValueError('"initial_inputs" must be an object')
    if not isinstance(meta, dict) or not isinstance(narrative, dict):
        raise ValueError('"meta" and "narrative" must be objects')
    unknown = sorted(set(narrative) - NARRATIVE_KEYS)
    if unknown:
        raise ValueError(f'unsupported narrative keys: {", ".join(unknown)}')
    _validate_narrative_style(narrative)

    for field in ('report_name', 'company_name', 'display_unit', 'report_mode'):
        if meta.get(field) is not None and not _nonempty_string(meta.get(field)):
            raise ValueError(f'meta.{field} must be a non-empty string')
    display_unit = meta.get('display_unit') or '万元'
    if display_unit not in DISPLAY_UNIT_FACTORS:
        raise ValueError(f'unsupported display_unit: {display_unit!r}')
    report_mode = meta.get('report_mode') or 'auto'
    if report_mode not in {'auto', 'verified', 'limited'}:
        raise ValueError('meta.report_mode must be auto, verified, or limited')

    public_research = _validate_payload_controls(
        inputs, narrative, meta, initial_inputs=initial_inputs
    )
    initial_result = analyze(initial_inputs) if initial_inputs is not None else None
    result = analyze(inputs)
    renderability_issues = _verified_renderability_issues(inputs, result, narrative)
    if report_mode == 'verified' and renderability_issues:
        raise ValueError('；'.join(renderability_issues))
    verified = not renderability_issues and report_mode != 'limited'
    if report_mode == 'limited' and not renderability_issues:
        renderability_issues = ['调用方指定生成有限材料财务分析报告']
    periods = _select_display_periods(result.get('period_results') or [])
    if not periods:
        raise ValueError('没有可渲染的报告期间')

    errors: list[str] = []
    rendered = {
        key: _resolve_narrative(value.strip(), result, periods, display_unit, errors)
        for key, value in narrative.items()
        if isinstance(value, str) and value.strip()
    }
    if errors:
        raise ValueError('; '.join(sorted(set(errors))))
    if not verified:
        defaults = {
            'balance_sheet_analysis': '资产与负债结构按可计算科目呈现，重点关注流动性和债务期限匹配。',
            'income_statement_analysis': '利润结构按主营经营、期间费用和非经常因素分别观察。',
            'cash_flow_analysis': '现金流按经营、投资和筹资活动分别判断其持续性。',
            'solvency_analysis': '偿债判断以账面流动性、杠杆和经营现金流覆盖为主。',
            'operating_efficiency_analysis': '营运判断以应收、存货和经营资金占用为主。',
            'profitability_analysis': '盈利判断兼顾利润水平、现金实现和非经常因素。',
            'growth_analysis': '成长判断以可比期间的收入、利润和资产变化为主。',
            'risk_analysis': '规则信号仅作为风险线索，结合财务表现审慎判断。',
            'analysis_summary': '第一还款来源以主营经营回款为核心，并结合债务安排判断授信匹配。',
        }
        for key, value in defaults.items():
            rendered.setdefault(key, value)

    context = meta.get('business_context') or {}
    credit = meta.get('credit_context') or {}
    company = meta.get('company_name') or result.get('company_name') or '目标企业'
    report_name = meta.get('report_name') or f'{company}财务分析报告'
    base_missing_materials = _missing_materials(inputs, result, meta)
    review_register = _build_review_register(
        inputs, result, public_research, renderability_issues, base_missing_materials
    )
    missing_materials = _missing_materials_from_register(review_register)
    evidence_coverage = 'partial' if any(
        item.get('status') == 'open' and item.get('blocking') == 'evidence'
        for item in review_register.get('items') or []
    ) else 'complete'
    report_status = (
        '已核验标准报告'
        if verified and evidence_coverage == 'complete'
        else '有限材料财务分析报告'
    )
    metadata_pairs = [
        ('企业', company),
        ('报表口径', context.get('statement_scope') or inputs.get('statement_scope')),
        ('审计意见', context.get('audit_opinion')),
        ('行业', context.get('industry')),
        ('企业阶段', context.get('stage')),
        ('业务与结算模式', context.get('business_model')),
        ('会计准则', context.get('accounting_standard')),
        ('授信用途', credit.get('purpose')),
        ('还款安排', credit.get('repayment_arrangement')),
        ('担保结构', credit.get('guarantee_structure')),
        ('展示单位', display_unit),
    ]
    report_metadata = '\n'.join(
        f'- {label}：{value}' for label, value in metadata_pairs if _nonempty_string(value)
    )

    balance_content = '\n\n'.join(filter(None, [
        _statement_table(periods, 'balance_sheet', display_unit),
        _section('显著异动科目', _statement_change_table(result, 'balance_sheet', display_unit)),
        _note_detail_tables(result, 'balance_sheet', display_unit),
        _section('资产负债表科目异动分析', rendered.get('balance_sheet_analysis')),
    ]))
    income_content = '\n\n'.join(filter(None, [
        _statement_table(periods, 'income_statement', display_unit),
        _section('显著异动科目', _statement_change_table(result, 'income_statement', display_unit)),
        _note_detail_tables(result, 'income_statement', display_unit),
        _section('利润表科目异动分析', rendered.get('income_statement_analysis')),
    ]))
    cash_content = '\n\n'.join(filter(None, [
        _statement_table(periods, 'cash_flow', display_unit),
        _section('显著异动科目', _statement_change_table(result, 'cash_flow', display_unit)),
        _note_detail_tables(result, 'cash_flow', display_unit),
        _section('现金流量表科目异动分析', rendered.get('cash_flow_analysis')),
    ]))

    chapter_one = {
        'id': 'financial-statements',
        'title': '1 财务简表',
        'order': 1,
        'content': report_metadata,
        'children': [
            {'id': 'balance-sheet-analysis', 'title': '1.1 资产负债表分析', 'order': 1, 'content': balance_content, 'children': []},
            {'id': 'income-statement-analysis', 'title': '1.2 利润表分析', 'order': 2, 'content': income_content, 'children': []},
            {'id': 'cash-flow-analysis', 'title': '1.3 现金流量表分析', 'order': 3, 'content': cash_content, 'children': []},
        ],
    }
    chapter_two = {
        'id': 'financial-indicators',
        'title': '2 财务指标分析',
        'order': 2,
        'content': _metric_table(periods, display_unit),
        'children': [
            {'id': 'solvency-analysis', 'title': '2.1 偿债能力分析', 'order': 1, 'content': rendered.get('solvency_analysis') or '', 'children': []},
            {'id': 'operating-efficiency-analysis', 'title': '2.2 营运能力分析', 'order': 2, 'content': rendered.get('operating_efficiency_analysis') or '', 'children': []},
            {'id': 'profitability-analysis', 'title': '2.3 盈利能力分析', 'order': 3, 'content': rendered.get('profitability_analysis') or '', 'children': []},
            {'id': 'growth-analysis', 'title': '2.4 成长能力分析', 'order': 4, 'content': rendered.get('growth_analysis') or '', 'children': []},
        ],
    }

    industry_table = _industry_table(result, display_unit)
    signal_table = _signal_table(result)
    cross_validation_table = _cross_validation_table(result, display_unit)
    summary_parts = [_section('综合结论', rendered.get('analysis_summary'))]
    if industry_table:
        summary_parts.extend([
            _section('行业对标', rendered.get('industry_comparison')),
            industry_table,
        ])
    summary_parts.append(_section('财务风险与异常验证', rendered.get('risk_analysis')))
    if signal_table:
        summary_parts.append(signal_table)
    if cross_validation_table:
        summary_parts.extend([
            _section('外部交叉验证', rendered.get('cross_validation')),
            cross_validation_table,
        ])
    chapter_three = {
        'id': 'financial-summary',
        'title': '3 财务分析总结',
        'order': 3,
        'content': '\n\n'.join(part for part in summary_parts if part),
        'children': [],
    }

    chapters = [chapter_one, chapter_two, chapter_three]
    now = datetime.now(timezone.utc)
    initial_snapshot = initial_inputs if initial_inputs is not None else inputs
    initial_calculation = initial_result if initial_result is not None else result
    enrichment_delta = {
        'enrichments': public_research.get('enrichments') or [],
        'conflicts': public_research.get('conflicts') or [],
    }
    run_id = _digest({
        'initial_inputs': initial_snapshot,
        'final_inputs': inputs,
        'public_research': public_research,
    })
    provenance = {
        'artifactKind': 'financial-analysis',
        'engine': ENGINE,
        'policy': POLICY,
        'version': VERSION,
        'verified': verified,
        'reportStatus': (
            'verified' if verified and evidence_coverage == 'complete' else 'limited'
        ),
        'verificationScope': 'deterministic-computation-and-report-structure',
        'evidenceCoverage': evidence_coverage,
        'renderabilityIssues': renderability_issues,
        'inputsDigest': _digest(inputs),
        'initialInputsDigest': _digest(initial_snapshot),
        'finalInputsDigest': _digest(inputs),
        'initialCalculationDigest': _digest(initial_calculation),
        'calculationDigest': _digest(result),
        'enrichmentDeltaDigest': _digest(enrichment_delta),
        'ratiosDigest': _digest(result.get('metrics') or {}),
        'chaptersDigest': _digest(chapters),
        'publicResearchDigest': _digest(public_research),
        'reviewRegisterDigest': _digest(review_register),
        'runId': run_id,
    }
    report = {
        'reportName': report_name,
        'templateId': None,
        'generatedAt': now.isoformat().replace('+00:00', 'Z'),
        'chapters': chapters,
        'missingMaterials': missing_materials,
        'publicResearch': public_research,
        'reviewRegister': review_register,
        '_provenance': provenance,
    }
    if _digest(report['chapters']) != provenance['chaptersDigest']:
        raise RuntimeError('章节指纹自检失败')
    if _digest(report['reviewRegister']) != provenance['reviewRegisterDigest']:
        raise RuntimeError('核验事项指纹自检失败')
    return report, result


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise ValueError('top-level JSON must be an object')
        report, result = build_report(payload)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        path = f'{REPORTS_DIR}/financial-analysis-{stamp}.json'
        docx_path = f'{REPORTS_DIR}/financial-analysis-{stamp}.docx'
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        from word_report import write_word_report
        write_word_report(report, result, docx_path)
        print(json.dumps({
            'ok': True,
            'path': path,
            'docxPath': docx_path,
            'verified': report['_provenance']['verified'],
            'reportStatus': report['_provenance']['reportStatus'],
            'renderabilityIssues': report['_provenance']['renderabilityIssues'],
            'provenance': report['_provenance'],
            'summary': result['summary'],
        }, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as exc:
        print(json.dumps({
            'ok': False,
            'error': f'financial-render.json 不是合法 JSON：第 {exc.lineno} 行第 {exc.colno} 列：{exc.msg}',
        }, ensure_ascii=False))
        sys.exit(2)
    except (ValueError, RuntimeError, TypeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        sys.exit(2)


if __name__ == '__main__':
    main()

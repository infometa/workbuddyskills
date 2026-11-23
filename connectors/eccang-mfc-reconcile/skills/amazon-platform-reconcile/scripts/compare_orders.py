#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""描述及订单维度的纯本地比较；CLI 惰性转发到统一 MCP 流程。

用法（占位符替换为实际绝对路径，保留引号）：
    PowerShell：
    & "<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/compare_orders.py" --csv "<CSV绝对路径>"
    POSIX shell：
    "<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/compare_orders.py" --csv "<CSV绝对路径>"
    Skill 根目录取本次加载的 SKILL.md 所在目录；不切换工作目录，用户的相对路径仍相对于调用位置。
    可选参数及退出状态与 reconcile.py 相同；单独使用 --check-env 仅检查本地环境。
"""

import sys

if __name__ == '__main__' and '--check-env' in sys.argv[1:]:
    sys.dont_write_bytecode = True

from collections import OrderedDict
from decimal import Decimal, ROUND_HALF_UP, localcontext


class ComparisonError(ValueError):
    """明细不能可靠回勾上层汇总，禁止生成确定性定位结论。"""


def sum_amounts(values):
    """按数据精度累加，避免 Decimal 默认精度截断正负抵消记录。"""
    values = list(values)
    if not values:
        return Decimal('0')
    if any(not isinstance(v, Decimal) or not v.is_finite() for v in values):
        raise ComparisonError('下钻金额未可靠解析，不能补零')
    with localcontext() as context:
        context.prec = max(28, max(v.adjusted() for v in values)
                           - min(v.as_tuple().exponent for v in values) + len(str(len(values))) + 4)
        return sum(values, Decimal('0'))


def cents(value):
    with localcontext() as context:
        context.prec = max(28, value.adjusted() + 5)
        return value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def comparison_group(name, remote, type_map, merge_map):
    if remote:
        merges = {type_map.get(src, src): type_map.get(dst, dst) for src, dst in merge_map.items()}
        return merges.get(name, name)
    name = merge_map.get(name, name)
    return type_map.get(name, name)


def difference_scope(csv_summary, finance_summary, differences, type_map, merge_map, skip_types):
    """比较组只作本地索引；发给 MCP 的始终是实际汇总中的原始 type。"""
    csv_groups = {name: comparison_group(name, False, type_map, merge_map)
                  for name, _ in csv_summary if name not in skip_types}
    remote_groups = {name: comparison_group(name, True, type_map, merge_map)
                     for name, _ in finance_summary if name not in skip_types}
    csv_names = {merge_map.get(name, name) for name in csv_groups}
    targets = OrderedDict()
    for difference in differences:
        name = difference['type']
        group = comparison_group(name, name not in csv_names, type_map, merge_map)
        targets.setdefault(group, [])
    for raw_type, group in remote_groups.items():
        if group in targets:
            targets[group].append(raw_type)
    display_names = {}
    for raw_type, group in csv_groups.items():
        display_names.setdefault(group, set()).add(merge_map.get(raw_type, raw_type))
    if any(len(names) > 1 for group, names in display_names.items() if group in targets):
        raise ComparisonError('CSV 多个未合并显示类型映射到同一财务类型，无法按既有汇总可靠定位')
    return targets, csv_groups, remote_groups


def verify_totals(records, expected_summary, label):
    """按原始 type 核验金额；缺失与额外的非零类型均不能当作完整明细。"""
    amounts = OrderedDict()
    for record in records:
        amounts.setdefault(record['type'], []).append(record['total'])
    expected = OrderedDict((name, Decimal(str(value))) for name, value in expected_summary)
    for name in dict.fromkeys([*expected, *amounts]):
        actual = cents(sum_amounts(amounts.get(name, [])))
        if actual != cents(expected.get(name, Decimal('0'))):
            raise ComparisonError(f'{label}按原始 type 回勾失败：{name}，明细 {actual}，汇总 {expected.get(name, 0)}')
        if name not in expected:
            raise ComparisonError(f'{label}出现汇总未返回的原始 type：{name}')


def verify_group_totals(records, summary, groups, label):
    """原始类型回勾后再核验比较组，防止分类型舍入掩盖合并组不一致。"""
    grouped = [{'type': groups[row['type']], 'total': row['total']} for row in records]
    expected = OrderedDict()
    for name, total in summary:
        expected.setdefault(groups[name], []).append(Decimal(str(total)))
    verify_totals(grouped, [(name, sum_amounts(values)) for name, values in expected.items()], label)


def aggregate_dimension(records, groups, dimension):
    buckets = OrderedDict()
    for record in records:
        value = record.get(dimension)
        value = value.strip() if isinstance(value, str) else value
        key = (groups[record['type']], value or None)
        buckets.setdefault(key, []).append(record)
    return buckets


def compare_dimension(csv_records, remote_records, csv_groups, remote_groups, dimension, comparable=True):
    """保留每条来源记录；空键单独成组，description 只规范两端空白。"""
    local = aggregate_dimension(csv_records, csv_groups, dimension) if comparable else OrderedDict()
    remote = aggregate_dimension(remote_records, remote_groups, dimension)
    comparisons = []
    for group, value in dict.fromkeys([*local, *remote]):
        left, right = local.get((group, value), []), remote.get((group, value), [])
        csv_total = cents(sum_amounts(row['total'] for row in left)) if comparable else None
        mcp_total = cents(sum_amounts(row['total'] for row in right))
        if not comparable:
            kind = '不可双边比较'
        elif not left:
            kind = '仅 MCP 有'
        elif not right:
            kind = '仅 CSV 有'
        else:
            kind = '匹配' if csv_total == mcp_total else '金额不同'
        comparisons.append({
            'group': group, dimension: value, 'csv_total': csv_total, 'mcp_total': mcp_total,
            'diff': cents(sum_amounts([csv_total, mcp_total.copy_negate()])) if comparable else None,
            'kind': kind, 'csv_count': len(left) if comparable else None, 'mcp_count': len(right),
            'csv_records': left, 'mcp_records': right,
        })
    return comparisons


def compare_descriptions(csv_records, remote_records, csv_groups, remote_groups, has_description):
    return compare_dimension(csv_records, remote_records, csv_groups, remote_groups,
                             'description', comparable=has_description)


def compare_orders(csv_records, remote_records, csv_groups, remote_groups):
    comparisons = compare_dimension(csv_records, remote_records, csv_groups, remote_groups, 'order_id')
    differences = [row for row in comparisons if row['order_id'] is not None and row['kind'] != '匹配']
    without_order = [row for row in comparisons if row['order_id'] is None]
    return differences, without_order


def main(argv=None):
    # 包导入和直接运行都只使用主脚本的参数、上下文及退出状态。
    if __package__:
        from .reconcile import main as reconcile_main
    else:
        from reconcile import main as reconcile_main
    return reconcile_main(argv)


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    sys.exit(main())

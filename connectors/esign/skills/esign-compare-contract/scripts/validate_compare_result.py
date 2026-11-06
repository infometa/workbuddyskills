#!/usr/bin/env python3
"""Validate schema v2 and render a report. No network or semantic comparison."""
import argparse
from collections import Counter
import copy
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile

CLASSES = {'material': '实质变更', 'non_material': '非实质变更', 'uncertain': '不确定'}
OPERATIONS = {'add': '新增', 'delete': '删除', 'modify': '修改', 'replace': '替换'}


class ValidationError(Exception):
    """An input violates the result contract."""


def fields(value, expected, label):
    if not isinstance(value, dict):
        raise ValidationError(f'{label} 必须是对象')
    if set(value) != set(expected):
        raise ValidationError(f'{label} 字段不符合协议；缺少 {sorted(set(expected)-set(value))}，'
                              f'多余 {sorted(set(value)-set(expected))}')


def string(value, label, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValidationError(f'{label} 必须是{"字符串" if empty else "非空字符串"}')


def strings(value, label):
    if not isinstance(value, list):
        raise ValidationError(f'{label} 必须是字符串数组')
    for item in value:
        string(item, label)


def normalize_newlines(text):
    # Preserve spaces, tabs and line boundaries; they may separate table cells.
    return text.replace('\r\n', '\n').replace('\r', '\n')


def validate(payload, base_text, compare_text):
    fields(payload, ('schema_version', 'files', 'coverage', 'differences'), '结果')
    if payload['schema_version'] != '2.0':
        raise ValidationError('schema_version 必须为 2.0')
    base_normalized, compare_normalized = normalize_newlines(base_text), normalize_newlines(compare_text)
    if not base_normalized.strip() or not compare_normalized.strip():
        raise ValidationError('正文为空：先解决文件读取问题，不生成比对报告')
    fields(payload['files'], ('base', 'compare'), 'files')
    for key, value in payload['files'].items():
        string(value, f'files.{key}')
    coverage = payload['coverage']
    fields(coverage, ('status', 'base_scope', 'compare_scope', 'limitations'), 'coverage')
    if coverage['status'] not in ('complete', 'partial'):
        raise ValidationError('coverage.status 必须是 complete 或 partial')
    string(coverage['base_scope'], 'coverage.base_scope')
    string(coverage['compare_scope'], 'coverage.compare_scope')
    strings(coverage['limitations'], 'coverage.limitations')
    if coverage['status'] == 'partial' and not coverage['limitations']:
        raise ValidationError('部分比对必须填写 coverage.limitations')
    rows = payload['differences']
    if not isinstance(rows, list):
        raise ValidationError('differences 必须为数组')
    ids, fingerprints = set(), set()
    counts = Counter({key: 0 for key in CLASSES})
    for index, row in enumerate(rows):
        label = f'differences[{index}]'
        fields(row, ('id', 'operation', 'classification', 'base_location',
                     'compare_location', 'before', 'after', 'analysis', 'basis', 'questions'), label)
        for key in ('id', 'analysis', 'basis'):
            string(row[key], f'{label}.{key}')
        for key in ('base_location', 'compare_location', 'before', 'after'):
            string(row[key], f'{label}.{key}', empty=True)
        strings(row['questions'], f'{label}.questions')
        category, operation = row['classification'], row['operation']
        if not isinstance(category, str) or category not in CLASSES:
            raise ValidationError(f'{label}.classification 不合法')
        if operation is None:
            if category != 'uncertain':
                raise ValidationError(f'{label}.operation 仅不确定项允许为 null')
        elif not isinstance(operation, str) or operation not in OPERATIONS:
            raise ValidationError(f'{label}.operation 仅允许 add/delete/modify/replace')
        if category == 'uncertain' and not row['questions']:
            raise ValidationError(f'{label}.questions：不确定项必须说明待确认事项')
        before, after = normalize_newlines(row['before']), normalize_newlines(row['after'])
        if (before and not before.strip()) or (after and not after.strip()):
            raise ValidationError(f'{label} 原文不能仅为空白；无证据的一侧应为空字符串')
        if not before and not after:
            raise ValidationError(f'{label} 至少需要一侧已读取的原文证据；整份读取失败不是差异项')
        if operation == 'add' and (before or not after):
            raise ValidationError(f'{label} 新增要求 before 为空、after 非空')
        if operation == 'delete' and (not before or after):
            raise ValidationError(f'{label} 删除要求 before 非空、after 为空')
        if operation in ('modify', 'replace') and (not before or not after):
            raise ValidationError(f'{label} 修改和替换必须有两侧证据')
        for quote, source, location, side in (
            (before, base_normalized, row['base_location'], '基准'),
            (after, compare_normalized, row['compare_location'], '比对'),
        ):
            if quote and quote not in source:
                raise ValidationError(f'{label} 未在{side}正文中找到引用；核对原文，不可补造')
            if quote and not location.strip():
                raise ValidationError(f'{label} {side}原文需要可复核位置')
            if not quote and location.strip():
                raise ValidationError(f'{label} 无{side}原文的一侧位置应为空')
        if row['id'] in ids:
            raise ValidationError(f'{label} id 重复')
        fingerprint = (row['base_location'].strip(), row['compare_location'].strip(), before, after)
        if fingerprint in fingerprints:
            raise ValidationError(f'{label} 同一位置的差异重复')
        ids.add(row['id']); fingerprints.add(fingerprint)
        counts[category] += 1
    if not rows and coverage['status'] == 'complete' and base_normalized != compare_normalized:
        raise ValidationError('两份正文仍有差异，不能提交完整比对且差异列表为空；补齐差异或说明未覆盖范围')
    if coverage['status'] == 'partial':
        result = 'partial'
    elif rows:
        result = 'differences_found'
    else:
        result = 'no_text_changes'
    normalized = copy.deepcopy(payload)
    normalized['overview'] = {'result': result, 'total': len(rows), 'counts': dict(counts)}
    normalized['evidence_check'] = {
        'method': 'newline-normalized-contiguous-substring',
        'base_sha256': hashlib.sha256(base_text.encode('utf-8')).hexdigest(),
        'compare_sha256': hashlib.sha256(compare_text.encode('utf-8')).hexdigest(),
        'note': '仅验证引用在所提供的抽取正文中存在；不证明抽取完整、位置正确或语义判断准确。'
    }
    return normalized


def md(text):
    # Quote untrusted document strings as inert text, including HTML and links.
    escaped = html.escape(text, quote=False)
    return re.sub(r'([\\`*_{}\[\]()#+.!|>\-])', r'\\\1', escaped)


def quote(text):
    return '\n'.join('> ' + md(line) for line in text.splitlines()) if text.strip() else '> （无）'


def render(result):
    coverage, overview = result['coverage'], result['overview']
    rows = result['differences']
    lines = ['# 合同差异比对报告', '',
             f"基准文件：{md(result['files']['base'])}  ",
             f"比对文件：{md(result['files']['compare'])}", '']
    if overview['result'] == 'partial':
        lines += ['**部分内容尚未完成比对，不能据此判断两份文件一致。**', '']
    if coverage['limitations']:
        lines += [f'- {md(item)}' for item in dict.fromkeys(coverage['limitations'])] + ['']
    if overview['result'] == 'no_text_changes':
        lines += ['未发现正文差异。', '']
    if not rows:
        return '\n'.join(lines)

    # The payload is already in contract order. Do not group details by severity.
    lines += ['## 差异明细', '']
    for row in rows:
        operation = OPERATIONS.get(row['operation'], '变化待确认')
        lines += [f"### {md(row['id'])} · {operation}", '']
        for side, label, value in (('base', '基准', row['before']),
                                   ('compare', '比对', row['after'])):
            if value:
                lines += [f"{label}位置：{md(row[side + '_location'])}", '',
                          f'**{label}原文**', '', quote(value), '']
        if row['questions']:
            lines += ['**待确认事项：**', '']
            lines += [f'- {md(q)}' for q in row['questions']] + ['']

    lines += ['## 分类总结', '', f"共记录 {overview['total']} 项变化。", '']
    for category, label in CLASSES.items():
        group = [row for row in rows if row['classification'] == category]
        if group:
            lines += [f'### {label}（{len(group)}项）', '']
            lines += [f"- {md(row['id'])}：{md(row['analysis'])}" for row in group] + ['']
    return '\n'.join(lines)


def no_duplicate_keys(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValidationError(f'JSON 字段重复：{key}')
        data[key] = value
    return data


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.compare-', delete=False) as handle:
            tmp = Path(handle.name)
            handle.write(text)
        os.replace(tmp, path)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-file', required=True, help='Schema v2 model payload JSON')
    parser.add_argument('--base-text-file', required=True, help='Actual extracted base text, UTF-8')
    parser.add_argument('--compare-text-file', required=True, help='Actual extracted comparison text, UTF-8')
    parser.add_argument('--output-json', help='Validated JSON output; omit to use stdout only')
    parser.add_argument('--output-markdown', help='Optional readable Markdown report')
    args = parser.parse_args()
    try:
        inputs = [Path(p).resolve() for p in (args.input_file, args.base_text_file, args.compare_text_file)]
        outputs = [Path(p).resolve() for p in (args.output_json, args.output_markdown) if p]
        if len(set(outputs)) != len(outputs) or any(p in inputs for p in outputs):
            raise ValidationError('输出路径不能相互重合或覆盖输入路径')
        payload = json.loads(inputs[0].read_text(encoding='utf-8-sig'), object_pairs_hook=no_duplicate_keys)
        base = inputs[1].read_text(encoding='utf-8-sig')
        compare = inputs[2].read_text(encoding='utf-8-sig')
        result = validate(payload, base, compare)
        serialized = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        report = render(result)
        if args.output_json:
            atomic_write(Path(args.output_json).resolve(), serialized)
        if args.output_markdown:
            atomic_write(Path(args.output_markdown).resolve(), report)
        print(serialized, end='')
        return 0
    except (ValidationError, OSError, UnicodeError, ValueError) as exc:
        print(f'校验失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""仅校验摘要结构与原文引用并输出内部 JSON；不联网，不验证语义或完整性。"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def fields(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f'{label} 字段不符合协议')


def string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} 必须为非空字符串')


def validate(payload, text):
    if not text.strip():
        raise ValueError('正文为空，不能生成摘要')
    fields(payload, ('schema_version', 'file_name', 'coverage', 'overviewText',
                     'contractTypeText', 'tableRows'), '摘要')
    if payload['schema_version'] != '2.0':
        raise ValueError('schema_version 必须为 2.0')
    for key in ('file_name', 'overviewText', 'contractTypeText'):
        string(payload[key], key)
    coverage = payload['coverage']
    fields(coverage, ('status', 'scope', 'limitations'), 'coverage')
    if coverage['status'] not in ('complete', 'partial'):
        raise ValueError('coverage.status 必须为 complete 或 partial')
    string(coverage['scope'], 'coverage.scope')
    if not isinstance(coverage['limitations'], list):
        raise ValueError('limitations 必须为数组')
    for item in coverage['limitations']:
        string(item, 'limitations')
    if coverage['status'] == 'partial' and not coverage['limitations']:
        raise ValueError('部分摘要必须说明覆盖限制')
    rows = payload['tableRows']
    if not isinstance(rows, list):
        raise ValueError('tableRows 必须为数组')
    seen = set()
    for index, row in enumerate(rows):
        fields(row, ('field', 'summary', 'quotes'), f'tableRows[{index}]')
        string(row['field'], 'field')
        string(row['summary'], 'summary')
        if not isinstance(row['quotes'], list) or not row['quotes']:
            raise ValueError(f'第 {index+1} 行 quotes 必须为非空原文数组')
        for quote in row['quotes']:
            string(quote, 'quotes')
            if quote not in text:
                raise ValueError(f'第 {index+1} 行未命中连续原文，请核对完整条件；不能静默删行')
        if len(set(row['quotes'])) != len(row['quotes']):
            raise ValueError(f'第 {index+1} 行原文依据重复')
        key = (row['field'], row['summary'], tuple(row['quotes']))
        if key in seen:
            raise ValueError(f'第 {index+1} 行重复')
        seen.add(key)
    result = copy.deepcopy(payload)
    result['evidence_check'] = {
        'method': 'exact-contiguous-substring',
        'source_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'note': '仅校验字段引用存在和结构；不证明正文完整、OCR正确、概述与简洁事实准确、证据支持结论或字段归属正确。',
    }
    return result


def no_duplicate_keys(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError(f'JSON 字段重复：{key}')
        data[key] = value
    return data


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.summary-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-file', required=True)
    parser.add_argument('--text-file', required=True)
    parser.add_argument('--output-json', required=True)
    args = parser.parse_args()
    try:
        inputs = [Path(p).resolve() for p in (args.input_file, args.text_file)]
        output = Path(args.output_json).resolve()
        if output in inputs:
            raise ValueError('输出不能覆盖输入')
        payload = json.loads(inputs[0].read_text(encoding='utf-8-sig'), object_pairs_hook=no_duplicate_keys)
        # Preserve source newline characters as evidence, without normalizing content.
        with inputs[1].open(encoding='utf-8-sig', newline='') as handle:
            text = handle.read()
        result = validate(payload, text)
        serialized = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        write_atomic(output, serialized)
        print(serialized, end='')
        return 0
    except (ValueError, OSError, UnicodeError) as error:
        print(f'校验失败：{error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

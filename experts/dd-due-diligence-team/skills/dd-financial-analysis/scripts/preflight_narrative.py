#!/usr/bin/env python3
"""
渲染前叙事预校验脚本（preflight_narrative.py）

在写 financial-render.json 之前，对叙事草稿（narrative）做与 render.py 完全一致的校验，
把"事后纠错"（只能等 render.py 报错才暴露）变成"事前预防"。

校验项（复用 render.py 的规则与正则，保证与最终渲染一致）：
  1. 字段长度：普通字段 ≤280 字符，analysis_summary ≤360 字符
  2. 单段正文：不能包含标题/列表/表格/换行
  3. 句数 ≤4
  4. 数值占位符 ≤6
  5. 禁用词：过程性表述（如"材料不足/待核验/详见/脚本"）+ 套话（如"综上所述"）
  6. 裸数字：仅日期/报告期/来源定位可裸写，其余必须用 {{placeholder}}
  7. 占位符：未知 key / 无效 period_N / 缺同比 / 非法未闭合 / 占位符后硬编码单位

用法：
  # 只校验叙事风格（无需 result，校验项 1-6）
  echo '<narrative-json>' | python3 scripts/preflight_narrative.py

  # 校验叙事 + 占位符有效性（需要 financial-result.json，额外校验第 7 项）
  echo '<narrative-json>' | python3 scripts/preflight_narrative.py --result financial-result.json --periods '["2024","2023","2022"]'

  也可直接传文件路径：
  python3 scripts/preflight_narrative.py narrative.json [--result result.json]

退出码：0=全部通过；1=有校验问题（打印明细）；2=参数/输入错误
"""
import json
import re
import sys
from pathlib import Path

# 复用 render.py 的校验规则与正则（与最终渲染完全一致，避免规则漂移）
from render import (
    CORE_NARRATIVE_KEYS,
    CONDITIONAL_NARRATIVE_KEYS,
    NARRATIVE_MAX_CHARS,
    SUMMARY_MAX_CHARS,
    PLACEHOLDER_RE,
    PROCESS_PROSE_TERMS,
    FORMULAIC_PROSE_TERMS,
    _validate_narrative_style,
    _contains_uncontrolled_number,
    _resolve_narrative,
)


def _nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def collect_style_errors(narrative: dict) -> list[str]:
    """复用 render._validate_narrative_style 的规则，但返回错误列表而非抛错。"""
    errors: list[str] = []
    visible_keys = CORE_NARRATIVE_KEYS | CONDITIONAL_NARRATIVE_KEYS
    for key in sorted(visible_keys):
        value = narrative.get(key)
        if not _nonempty_string(value):
            continue
        text = value.strip()
        limit = SUMMARY_MAX_CHARS if key == 'analysis_summary' else NARRATIVE_MAX_CHARS
        if len(text) > limit:
            errors.append(f'narrative.{key} 超过 {limit} 字符（当前 {len(text)}）')
        if '\n' in text or text.startswith(('#', '-', '*', '>')) or '|' in text:
            errors.append(f'narrative.{key} 必须是单段正文，不能包含标题、列表或表格')
        sentence_count = len(re.findall(r'[。！？!?]', text))
        if sentence_count > 4:
            errors.append(
                f'narrative.{key} 超过 4 句（当前 {sentence_count}），请只保留判断、关键事实和信贷影响'
            )
        placeholder_count = len(PLACEHOLDER_RE.findall(text))
        if placeholder_count > 6:
            errors.append(
                f'narrative.{key} 引用指标过多（当前 {placeholder_count}），请保留不超过 6 个决定性数值'
            )
        # 裸数字：剥离占位符后检查（与 render._resolve_narrative 的终检一致）
        remainder = PLACEHOLDER_RE.sub('', text)
        if _contains_uncontrolled_number(remainder):
            errors.append(
                f'narrative.{key} 含未通过占位符引用的数值（仅日期、报告期和来源定位可裸写）'
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
    return errors


def collect_placeholder_errors(
    narrative: dict, result: dict, periods: list[dict]
) -> list[str]:
    """复用 render._resolve_narrative 解析占位符，收集 key/期间/同比/裸数字/单位错误。"""
    errors: list[str] = []
    visible_keys = CORE_NARRATIVE_KEYS | CONDITIONAL_NARRATIVE_KEYS
    for key in sorted(visible_keys):
        text = narrative.get(key)
        if not _nonempty_string(text):
            continue
        _resolve_narrative(text.strip(), result, periods, '元', errors)
    return errors


def main() -> int:
    args = sys.argv[1:]
    result_path = None
    periods = []

    if '--result' in args:
        idx = args.index('--result')
        if idx + 1 < len(args):
            result_path = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]

    if '--periods' in args:
        idx = args.index('--periods')
        if idx + 1 < len(args):
            try:
                periods = json.loads(args[idx + 1])
            except json.JSONDecodeError:
                print('错误：--periods 应为 JSON 数组，如 ["2024","2023","2022"]', file=sys.stderr)
                return 2
            args = args[:idx] + args[idx + 2 :]

    # 读取 narrative：文件路径或 stdin JSON
    narrative_raw = None
    if args:
        narrative_raw = Path(args[0]).read_text(encoding='utf-8')
    else:
        narrative_raw = sys.stdin.read()
    if not narrative_raw.strip():
        print('错误：请输入 narrative JSON（文件路径或 stdin）', file=sys.stderr)
        return 2
    try:
        narrative = json.loads(narrative_raw)
    except json.JSONDecodeError as exc:
        print(f'错误：narrative 不是合法 JSON：{exc}', file=sys.stderr)
        return 2
    if not isinstance(narrative, dict):
        print('错误：narrative 应为 JSON 对象', file=sys.stderr)
        return 2

    result = None
    if result_path:
        try:
            with open(result_path, encoding='utf-8') as fh:
                result = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f'错误：无法读取 result 文件 {result_path}：{exc}', file=sys.stderr)
            return 2

    errors: list[str] = collect_style_errors(narrative)
    if result is not None:
        period_items = [{'period_label': p} for p in periods] if periods else []
        errors.extend(collect_placeholder_errors(narrative, result, period_items))

    if errors:
        # 去重并保持顺序
        unique = list(dict.fromkeys(errors))
        print(f'❌ narrative 预校验未通过（{len(unique)} 项）：')
        for err in unique:
            print(f'  - {err}')
        print('\n请修正后重新校验，再写入 financial-render.json。')
        return 1

    print('✅ narrative 预校验全部通过，可写入 financial-render.json。')
    return 0


if __name__ == '__main__':
    sys.exit(main())

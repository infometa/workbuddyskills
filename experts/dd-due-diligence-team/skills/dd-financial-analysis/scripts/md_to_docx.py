#!/usr/bin/env python3
"""把定稿的报告 Markdown 渲染成专业排版的 DOCX（独立专项报告流程专用）。

背景：standalone-report 流程只产出 Markdown，此前"生成 DOCX"这一步没有确定性
脚本可用，Agent 往往跳过或失败，导致 save_finance_report 未传 docxCosKey，
前端报告版本显示"该版本无 Word"。

本脚本复用 word_report.py 已有的排版能力（字体/标题层级/表格样式/页眉页脚/
页码），把 Markdown 的标题层级映射为 Word 的 Heading，表格渲染为真正的
Word 表格，不引入任何新的排版实现。

用法：
    python3 <scripts_dir>/md_to_docx.py \
      --md /workspace/reports/财务专项报告.md \
      --out /workspace/reports/财务专项报告.docx \
      --title "XX公司财务分析报告" \
      [--period "2024年度"] [--scope "合并口径"]

输出 JSON（stdout）：
    {"ok": true, "path": "...", "bytes": 123456, "headings": 32, "tables": 12}
    {"ok": false, "error": "..."}

退出码：0 成功；1 失败。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 与 word_report.py 同目录（bootstrap.py 解压后平铺），直接复用其排版函数
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from word_report import (  # type: ignore[import-not-found]
        _add_inline,
        _add_markdown,
        _configure_document,
        _imports,
        _set_run_font,
    )
except ImportError as exc:  # pragma: no cover
    print(
        json.dumps(
            {
                'ok': False,
                'error': (
                    f'无法导入 word_report：{type(exc).__name__}: {exc}；'
                    '请确认已运行 bootstrap.py 且使用其返回的 scripts_dir'
                ),
            },
            ensure_ascii=False,
        )
    )
    sys.exit(1)


H1_RE = re.compile(r'^#\s+(?P<text>.+?)\s*$')
H2_RE = re.compile(r'^##\s+(?P<text>.+?)\s*$')
FENCE_RE = re.compile(r'^\s*```')


def _split_blocks(markdown: str) -> list[dict[str, Any]]:
    """按 H1/H2 把 Markdown 切成块，块内正文交给 word_report._add_markdown 渲染。

    H3/H4、表格、引用、列表等由 _add_markdown 内部处理，此处不重复实现。
    围栏代码块内的 # 不视为标题。
    """
    blocks: list[dict[str, Any]] = []
    current = {'level': 0, 'title': '', 'lines': []}
    in_fence = False

    for raw in markdown.splitlines():
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            current['lines'].append(raw)
            continue
        if in_fence:
            current['lines'].append(raw)
            continue

        h1 = H1_RE.match(raw)
        h2 = H2_RE.match(raw)
        if h1 or h2:
            if current['title'] or current['lines']:
                blocks.append(current)
            current = {
                'level': 1 if h1 else 2,
                'title': (h1 or h2).group('text').strip(),
                'lines': [],
            }
            continue
        current['lines'].append(raw)

    if current['title'] or current['lines']:
        blocks.append(current)
    return blocks


def render(
    md_path: Path,
    out_path: Path,
    *,
    title: str | None,
    period: str | None,
    scope: str | None,
) -> dict[str, Any]:
    markdown = md_path.read_text(encoding='utf-8')
    if not markdown.strip():
        raise ValueError(f'Markdown 内容为空：{md_path}')

    blocks = _split_blocks(markdown)

    # 文档级标题：显式传入优先，否则取首个 H1
    doc_title = title or next((b['title'] for b in blocks if b['level'] == 1), '财务分析报告')

    api = _imports()
    Document = api['Document']
    WD_ALIGN_PARAGRAPH = api['WD_ALIGN_PARAGRAPH']
    Pt = api['Pt']

    doc = Document()
    # 复用 word_report 的页面/字体/样式/页眉页脚配置
    _configure_document(doc, {'reportName': doc_title}, api)

    # ---- 封面 ----
    kicker = doc.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    kicker.paragraph_format.space_before = Pt(54)
    kicker.paragraph_format.space_after = Pt(12)
    _set_run_font(kicker.add_run('对公信贷'), api, size=11, bold=True, color='6B7280')

    cover = doc.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover.paragraph_format.space_after = Pt(22)
    _set_run_font(cover.add_run(doc_title), api, size=24, bold=True, color='203864')

    if period or scope:
        meta = doc.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        parts = []
        if period:
            parts.append(f'报告期：{period}')
        if scope:
            parts.append(f'报表口径：{scope}')
        _set_run_font(meta.add_run('    '.join(parts)), api, size=10.5, color='4B5563')

    generated = doc.add_paragraph()
    generated.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(
        generated.add_run(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}'),
        api,
        size=9,
        color='6B7280',
    )
    doc.add_page_break()

    # ---- 正文 ----
    heading_count = 0
    for index, block in enumerate(blocks):
        # 首个 H1 已用作封面标题时不再重复输出
        if block['level'] == 1 and block['title'] == doc_title and index == 0:
            body = '\n'.join(block['lines']).strip()
            if body:
                _add_markdown(doc, body, api)
            continue

        if block['level'] == 1:
            heading = doc.add_paragraph(style='Heading 1')
            _add_inline(heading, block['title'], api, size=16, color='2E5B88')
            heading_count += 1
        elif block['level'] == 2:
            heading = doc.add_paragraph(style='Heading 2')
            _add_inline(heading, block['title'], api, size=13, color='2E5B88')
            heading_count += 1

        body = '\n'.join(block['lines']).strip()
        if body:
            _add_markdown(doc, body, api)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    if not out_path.is_file() or out_path.stat().st_size == 0:
        raise RuntimeError(f'DOCX 写入失败：{out_path}')

    table_count = sum(
        1
        for line in markdown.splitlines()
        if line.strip().startswith('|') and not line.strip().startswith('|--')
    )
    return {
        'ok': True,
        'path': str(out_path),
        'bytes': out_path.stat().st_size,
        'headings': heading_count,
        'tables': len(doc.tables),
        'md_table_rows': table_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Markdown → 专业排版 DOCX')
    parser.add_argument('--md', required=True, help='定稿 Markdown 路径')
    parser.add_argument('--out', required=True, help='输出 DOCX 路径')
    parser.add_argument('--title', default=None, help='文档标题（默认取首个 H1）')
    parser.add_argument('--period', default=None, help='报告期，如 2024年度')
    parser.add_argument('--scope', default=None, help='报表口径，如 合并口径')
    args = parser.parse_args()

    try:
        result = render(
            Path(args.md),
            Path(args.out),
            title=args.title,
            period=args.period,
            scope=args.scope,
        )
    except Exception as exc:  # noqa: BLE001 — 失败原因需原样回报给 Agent
        print(json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

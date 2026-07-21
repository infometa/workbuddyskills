#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_report.py —— result.json → HTML / Markdown / PDF 一体化报告（v0.3.0）

功能：
  - 读取 result.json（由 SKILL 工作流产出）
  - 根据模式（single / compare）+ 深度档位（skim / guided / deep / compare）自适应渲染
  - 三输出：
      HTML（assets/report-template.html 骨架，单文件可分享）
      Markdown（同源数据，零依赖文本，进 Obsidian/Notion）
      PDF（默认 via weasyprint；未安装则自动降级 HTML+提示浏览器打印）
  - 渲染 v0.2.0 新字段：method_formula（方法公式化）、one_line_plain（大白话）
  - 渲染 v0.3.0 新字段：result.tldr（整份报告核心一句话）+ --format pdf / all

用法：
  python scripts/render_report.py result.json                    # 默认 HTML
  python scripts/render_report.py result.json --format md        # Markdown 单文件
  python scripts/render_report.py result.json --format pdf       # PDF（缺依赖时降级 HTML）
  python scripts/render_report.py result.json --format all       # HTML + MD + PDF 三件齐套
  python scripts/render_report.py result.json --out report.html  # 显式路径
  python scripts/render_report.py result.json --template path    # 自定义 HTML 模板

【PDF 依赖】
  PDF 输出依赖 weasyprint：
    pip install weasyprint
  若未安装，本脚本不会报错，而是：
    - 写出同 stem 的 .html 文件
    - stderr 输出明确指引："请用浏览器打开 X.html 后 ⌘+P 打印为 PDF"
  这样保证用户即便没装 weasyprint 也能拿到可打印的产物，零阻塞。

退出码：
  0  成功（含 PDF 降级到 HTML）
  1  参数 / 文件错误
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Optional

SCRIPT_VERSION = "0.4.0"

DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "report-template.html"


def esc(x: Any) -> str:
    if x is None:
        return "—"
    return html.escape(str(x))


# 模块级开关：若解析层声明 paginated=false（pasted_text 输入），renderer
# 把 page=null 渲染为「粘贴段·未分页」而不是空白。供 render() 注入。
_PAGINATED: bool = True


def fmt_prov(loc: Optional[dict[str, Any]]) -> str:
    if not loc or not isinstance(loc, dict):
        return ""
    page = loc.get("page")
    section = loc.get("section")
    if page is None and not section and not _PAGINATED:
        return "（粘贴段·未分页）"
    if page is None and not section:
        return ""
    parts: list[str] = []
    if page is not None:
        parts.append(f"p.{page}")
    elif not _PAGINATED:
        parts.append("粘贴段")
    if section:
        parts.append(esc(section))
    return "（" + " · ".join(parts) + "）"


# ============================================================
# 渲染：每个 paper 一个卡片组
# ============================================================


def _collapsible_section(title: str, body_html: str, default_open: bool = True) -> str:
    """生成可折叠的 block-header + block-body 结构。"""
    collapsed_cls = "" if default_open else " collapsed"
    hidden_cls = "" if default_open else " hidden"
    return (
        f'<div class="block-header{collapsed_cls}">'
        f'<h3>{esc(title)}</h3>'
        f'<span class="chevron">▼</span>'
        f'</div>'
        f'<div class="block-body{hidden_cls}">'
        f'{body_html}'
        f'</div>'
    )


def render_summary_card(paper: dict[str, Any]) -> str:
    sc = paper.get("summary_card") or {}
    pmap = sc.get("provenance_map") or {}

    def row(label: str, key: str) -> str:
        value = sc.get(key)
        if value is None or value == "":
            return ""
        loc = pmap.get(key) or {}
        if isinstance(value, list):
            # list 字段的 provenance 支持两种 schema：
            #   (A) loc 是单 dict：整组共享一个汇总 prov（放在 ul 后）
            #   (B) loc 是 list of dict：每项配自己的 prov（嵌在 <li> 内）
            if isinstance(loc, list):
                lis = []
                for i, v in enumerate(value):
                    item_loc = loc[i] if i < len(loc) and isinstance(loc[i], dict) else {}
                    item_prov = (
                        f"<span class='prov'>{fmt_prov(item_loc)}</span>"
                        if item_loc else ""
                    )
                    lis.append(f"<li>{esc(v)}{item_prov}</li>")
                items_html = "<ul>" + "".join(lis) + "</ul>"
                prov_html = ""
            else:
                items_html = "<ul>" + "".join(
                    f"<li>{esc(v)}</li>" for v in value
                ) + "</ul>"
                prov_html = (
                    f"<span class='prov'>{fmt_prov(loc)}</span>"
                    if isinstance(loc, dict) and loc else ""
                )
        else:
            items_html = esc(value)
            prov_html = f"<span class='prov'>{fmt_prov(loc)}</span>"
        return (
            f'<div class="field-row">'
            f'<span class="label">{esc(label)}：</span>'
            f"{items_html}{prov_html}"
            f"</div>"
        )

    blocks: list[str] = [
        row("研究问题", "research_question"),
        row("方法", "method"),
        row("数据集", "dataset"),
        row("关键结果", "key_results"),
        row("贡献", "contributions"),
        row("局限", "limitations"),
        _row_method_formula(sc, pmap),
        _row_one_line_plain(sc, pmap),
    ]
    cards = "".join(b for b in blocks if b)
    body = f"<div class='summary-grid'>{cards}</div>"
    return _collapsible_section("摘要卡", body, default_open=True)


def _row_method_formula(sc: dict[str, Any], pmap: dict[str, Any]) -> str:
    """v0.2.0：方法公式化（伪代数式 ≤4 元素，扫一眼抓本质）。"""
    val = sc.get("method_formula")
    if not val:
        return ""
    loc = pmap.get("method_formula") or {}
    pages = loc.get("aggregate_pages") or ([loc["page"]] if loc.get("page") else [])
    section = loc.get("section") or ""
    cite_parts = []
    if pages:
        cite_parts.append("p." + ", p.".join(str(p) for p in pages))
    if section:
        cite_parts.append(esc(section))
    cite = "（" + " · ".join(cite_parts) + "）" if cite_parts else ""
    return (
        f'<div class="field-row formula">'
        f'<span class="label">方法公式：</span>'
        f"<pre>{esc(val)}</pre>"
        f"<span class='prov'>{cite}</span>"
        f"</div>"
    )


def _row_one_line_plain(sc: dict[str, Any], pmap: dict[str, Any]) -> str:
    """v0.2.0：一句话大白话（≤40 字，零术语）。"""
    val = sc.get("one_line_plain")
    if not val:
        return ""
    loc = pmap.get("one_line_plain") or {}
    pages = loc.get("aggregate_pages") or ([loc["page"]] if loc.get("page") else [])
    section = loc.get("section") or ""
    cite_parts = []
    if pages:
        cite_parts.append("p." + ", p.".join(str(p) for p in pages))
    if section:
        cite_parts.append(esc(section))
    cite = "（" + " · ".join(cite_parts) + "）" if cite_parts else ""
    return (
        f'<div class="field-row one-line">'
        f'<span class="label">一句话：</span>'
        f"<span class='text'>{esc(val)}</span>"
        f"<span class='prov'>{cite}</span>"
        f"</div>"
    )


def _prov_inline_item(value: Any, pmap: dict[str, Any], key: str) -> str:
    # key_results 等数组字段支持逐项 provenance
    if key == "key_results":
        idx = None  # 这里简化不做逐项索引注入
    return value


def render_recommended_questions(paper: dict[str, Any]) -> str:
    rq = paper.get("recommended_questions") or []
    if not rq:
        return ""
    lis = "".join(
        f"<li>"
        f"<span class='q-text'>{esc(q.get('q') or q.get('question') or '')}</span>"
        f"<span class='why'>{esc(q.get('why', ''))}</span>"
        f"</li>"
        for q in rq
    )
    body = f"<ul class='question-list'>{lis}</ul>"
    return _collapsible_section("AI 推荐追问", body, default_open=True)


def render_connection_points(paper: dict[str, Any]) -> str:
    cps = paper.get("connection_points")
    if not cps:
        return ""
    cards: list[str] = []
    for cp in cps:
        type_label = esc(cp.get("type", ""))
        insight = esc(cp.get("insight", ""))
        pages = cp.get("evidence_pages") or []
        pages_str = ", ".join(f"p.{p}" for p in pages) if pages else "—"
        score = cp.get("relevance_score")
        score_str = f"{float(score):.2f}" if score is not None else "—"
        cards.append(
            f'<div class="conn-card">'
            f'<span class="type-tag">{type_label}</span>'
            f'<span class="score">relevance {esc(score_str)}</span>'
            f'<div class="insight">{insight}</div>'
            f'<div class="evidence">证据页：{esc(pages_str)}</div>'
            f"</div>"
        )
    body = "".join(cards)
    return _collapsible_section("与你研究方向的关联点", body, default_open=True)


def render_deep_dive(paper: dict[str, Any]) -> str:
    dd = paper.get("deep_dive_answers")
    if not dd:
        return ""
    blocks: list[str] = []
    for item in dd:
        q = esc(item.get("question", ""))
        a = esc(item.get("answer", ""))
        excerpts = item.get("original_excerpts") or []
        exc_html = ""
        for ex in excerpts:
            page = ex.get("page")
            section = ex.get("section") or ""
            text = esc(ex.get("text", ""))
            cite = f"p.{page}" if page is not None else "—"
            if section:
                cite += f" · {esc(section)}"
            exc_html += f'<div class="excerpt">{text}<span class="cite">{cite}</span></div>'
        ca = item.get("critical_analysis") or {}
        ca_html = ""
        if ca:
            for section_key, label, css in [
                ("agree_with", "同意 / 认可", "ca-agree"),
                ("question", "质疑 / 追问", "ca-question"),
                ("complement", "对你方向的补充", "ca-complement"),
            ]:
                items = ca.get(section_key) or []
                if items:
                    lis = "".join(f"<li>{esc(x)}</li>" for x in items)
                    ca_html += f"<div class='{css}'><h4>{label}</h4><ul>{lis}</ul></div>"
        blocks.append(
            f'<div style="border-left:3px solid var(--accent);padding-left:12px;margin:12px 0;">'
            f"<p><strong>Q：{q}</strong></p>"
            f"<p>{a}</p>"
            f"<div><strong>原文片段</strong>{exc_html}</div>"
            f"<div class='ca-block'>{ca_html}</div>"
            f"</div>"
        )
    body = "".join(blocks)
    return _collapsible_section("精读回答", body, default_open=True)


def render_references_html(paper: dict[str, Any]) -> str:
    """v0.4.0 / P0-A：渲染 papers[i].references[] + references_meta。"""
    refs = paper.get("references") or []
    meta = paper.get("references_meta") or {}
    if not refs and not meta.get("extraction_notes"):
        return ""

    parts: list[str] = []
    if not refs:
        notes = meta.get("extraction_notes") or []
        note_html = "".join(f"<li>{esc(n)}</li>" for n in notes)
        parts.append(
            f"<div class='refs-empty'><i>未抽取到 references</i>"
            f"<ul class='refs-notes'>{note_html}</ul></div>"
        )
        return _collapsible_section("参考文献（References）", "".join(parts), default_open=False)

    if meta.get("extracted") is False and meta.get("extraction_notes"):
        notes = meta.get("extraction_notes") or []
        note_html = "".join(f"<li>{esc(n)}</li>" for n in notes)
        parts.append(
            f"<div class='refs-degraded-note'><b>抽取说明：</b>"
            f"<ul class='refs-notes'>{note_html}</ul></div>"
        )

    items: list[str] = []
    for r in refs:
        if not isinstance(r, dict):
            continue
        idx = esc(r.get("idx") or "?")
        raw = esc(r.get("raw") or "")
        page = r.get("page")
        year = r.get("year")
        meta_bits = []
        if page is not None:
            meta_bits.append(f"<span class='prov'>p.{esc(page)}</span>")
        if year is not None:
            meta_bits.append(f"<span class='ref-year'>{esc(year)}</span>")
        meta_html = " ".join(meta_bits)
        items.append(
            f"<li class='ref-item'><b>[{idx}]</b> {raw} {meta_html}</li>"
        )
    parts.append(f"<ol class='refs-list'>{''.join(items)}</ol>")
    return _collapsible_section("参考文献（References）", "".join(parts), default_open=False)


def render_paper_block(paper: dict[str, Any], paper_idx: int = 0) -> str:
    label = esc(paper.get("label") or "")
    title = esc(paper.get("title") or "（未解析标题）")
    authors = paper.get("authors") or []
    year = paper.get("year")
    venue = paper.get("venue")
    sec_id = f"sec-paper-{paper_idx}"

    meta_parts = []
    if authors:
        meta_parts.append(f'<span>👤 {esc(", ".join(authors))}</span>')
    if year:
        meta_parts.append(f'<span>📅 {esc(year)}</span>')
    if venue:
        meta_parts.append(f'<span>📖 {esc(venue)}</span>')
    total_pages = paper.get("total_pages", "?")
    meta_parts.append(f'<span>📄 共 {esc(total_pages)} 页</span>')
    meta_html = (
        f'<div class="paper-meta">{"".join(meta_parts)}</div>'
        if meta_parts else ""
    )

    title_line = f"[{label}] {title}" if label else title

    sections_html = "".join([
        render_summary_card(paper),
        render_recommended_questions(paper),
        render_connection_points(paper),
        render_deep_dive(paper),
        render_references_html(paper),
    ])

    return (
        f'<section class="block" id="{sec_id}">'
        f'<div class="paper-hero">'
        f'<h2>{title_line}</h2>'
        f'{meta_html}'
        f'</div>'
        f'{sections_html}'
        f'</section>'
    )


def render_comparison(comp: dict[str, Any]) -> str:
    if not comp:
        return ""
    labels = comp.get("papers_labels") or []
    dims = comp.get("dimensions") or []
    table = comp.get("table") or []

    # 对比表格
    header_cells = "".join(f"<th>{esc(l)}</th>" for l in labels)
    thead = f"<thead><tr><th>维度</th>{header_cells}</tr></thead>"
    tbody_rows: list[str] = []
    for row in table:
        dim = esc(row.get("dimension", ""))
        rows_data = row.get("rows") or {}
        cells = []
        for l in labels:
            cell = rows_data.get(l, {}) or {}
            content = esc(cell.get("content") or "—")
            prov = fmt_prov(cell.get("provenance") or {})
            cells.append(f'<td>{content}<span class="prov">{prov}</span></td>')
        tbody_rows.append(f"<tr><th>{dim}</th>{''.join(cells)}</tr>")
    tbody = "<tbody>" + "".join(tbody_rows) + "</tbody>"
    table_html = f"<table class='comp-table'>{thead}{tbody}</table>"

    # 差异叙述
    narrative_raw = comp.get("differences_narrative")
    narrative_html = ""
    if isinstance(narrative_raw, str) and narrative_raw.strip():
        paragraphs = [p.strip() for p in narrative_raw.split("\n\n") if p.strip()]
        for p in paragraphs:
            narrative_html += f'<div class="narrative-theme"><div>{esc(p)}</div></div>'
    elif isinstance(narrative_raw, list):
        for t in narrative_raw:
            if not isinstance(t, dict):
                narrative_html += f'<div class="narrative-theme"><div>{esc(str(t))}</div></div>'
                continue
            cites = t.get("cite") or {}
            cite_str = "；".join(
                f"{esc(k)}: " + ",".join(f"p.{p}" for p in v) for k, v in cites.items()
            )
            narrative_html += (
                f'<div class="narrative-theme">'
                f"<span class='theme-name'>{esc(t.get('theme', ''))}</span>"
                f"<div>{esc(t.get('summary', ''))}</div>"
                f"<div style='color:var(--muted);font-size:0.82em;margin-top:6px;'>{cite_str}</div>"
                f"</div>"
            )

    # cross_paper_answer
    cpa = comp.get("cross_paper_answer")
    cpa_html = ""
    if cpa:
        cpa_html = "<h3>跨论文综合回答</h3>"
        cpa_html += f"<div><b>问题：</b>{esc(cpa.get('question', ''))}</div>"
        cpa_html += f"<div style='margin:6px 0 10px;'>{esc(cpa.get('answer', ''))}</div>"
        for lbl, evs in (cpa.get("per_paper_evidence") or {}).items():
            for ex in evs:
                page = ex.get("page")
                cite = f"[{esc(lbl)}] " + (f"p.{page}" if page is not None else "—")
                cpa_html += f'<div class="excerpt">{esc(ex.get("excerpt", ""))}<span class="cite">{cite}</span></div>'

    # key_takeaways
    kt = comp.get("key_takeaways_for_user_direction") or []
    kt_html = ""
    if kt:
        lis = "".join(f"<li>{esc(x)}</li>" for x in kt)
        kt_html = f"<h3>对你研究方向的 Key Takeaways</h3><ul>{lis}</ul>"

    synth_html = render_synthesis_block_html(comp.get("synthesis_block"))

    # 组合各子块
    comparison_body = (
        _collapsible_section("对比表格", table_html, default_open=True)
        + (f'<div class="block-header"><h3 style="color:var(--accent);">差异叙述</h3></div>'
           f'<div class="block-body">{narrative_html}</div>'
           if narrative_html else "")
        + synth_html
        + cpa_html
        + kt_html
    )

    return (
        f'<section class="block" id="sec-comparison">'
        f'<h2>多篇对比</h2>'
        f'<div class="block-inner">{comparison_body}</div>'
        f'</section>'
    )


def render_synthesis_block_html(synth: Optional[dict[str, Any]]) -> str:
    """v0.4.0 / P1-A：synthesis_block 渲染 —— 对比的"画龙点睛"段落。

    缺字段时跳过对应小节（不抛异常），整段都缺时返回空串。
    详细字段契约见 references/comparison-dimensions.md § 八。
    """
    if not synth or not isinstance(synth, dict):
        return ""
    parts: list[str] = []

    lineage = (synth.get("research_lineage") or "").strip()
    if lineage:
        parts.append(
            f'<div class="synth-lineage"><b>研究脉络：</b>{esc(lineage)}</div>'
        )

    evolution = synth.get("method_evolution") or []
    if evolution:
        items: list[str] = []
        for stage in evolution:
            if not isinstance(stage, dict):
                continue
            label = esc(stage.get("label") or "")
            year = stage.get("year")
            year_str = f" · {esc(year)}" if year is not None else ""
            stage_name = esc(stage.get("stage") or "")
            key_move = esc(stage.get("key_move") or "")
            rationale = esc(stage.get("rationale") or "")
            items.append(
                f"<li>"
                f"<span class='synth-stage-head'><b>[{label}] {stage_name}</b>{year_str}</span>"
                f"<div class='synth-key-move'>{key_move}</div>"
                f"<div class='synth-rationale'><i>动机：</i>{rationale}</div>"
                f"</li>"
            )
        if items:
            parts.append(
                f"<div class='synth-section'><b>方法演进</b>"
                f"<ol class='synth-evolution'>{''.join(items)}</ol></div>"
            )

    disagreements = synth.get("key_disagreements") or []
    if disagreements:
        items = []
        for d in disagreements:
            if not isinstance(d, dict):
                continue
            topic = esc(d.get("topic") or "")
            positions = d.get("positions") or {}
            ev_pages = d.get("evidence_pages") or {}
            pos_lines: list[str] = []
            for lbl, pos in positions.items():
                page = ev_pages.get(lbl)
                page_str = f"<span class='prov'>p.{esc(page)}</span>" if page is not None else ""
                pos_lines.append(
                    f"<li><b>[{esc(lbl)}]</b> {esc(pos)}{page_str}</li>"
                )
            items.append(
                f"<div class='synth-disagreement'>"
                f"<div class='synth-topic'>· {topic}</div>"
                f"<ul>{''.join(pos_lines)}</ul></div>"
            )
        if items:
            parts.append(
                f"<div class='synth-section'><b>关键分歧</b>{''.join(items)}</div>"
            )

    consensus = synth.get("consensus") or []
    if consensus:
        lis = "".join(f"<li>{esc(c)}</li>" for c in consensus)
        parts.append(
            f"<div class='synth-section'><b>共识</b><ul class='synth-consensus'>{lis}</ul></div>"
        )

    open_qs = synth.get("open_questions") or []
    if open_qs:
        lis = "".join(f"<li>{esc(q)}</li>" for q in open_qs)
        parts.append(
            f"<div class='synth-section'><b>未解之谜</b><ul class='synth-open'>{lis}</ul></div>"
        )

    if not parts:
        return ""
    return f"<h3>研究脉络与共识</h3><div class='synth-block'>{''.join(parts)}</div>"


def render_provenance_summary_html(result: dict[str, Any]) -> str:
    """v0.4.0：把 Provenance 审计从工程师术语 → 用户视角的"接下来该怎么做"。

    旧版只展示 4 个数字（总 claim / 页码覆盖 / high 置信 / 幻觉风险标记），
    用户根本不懂术语也不知道下一步该做什么。新版三件事：
      ① 顶部一行人话总结（"42 条事实里，3 条已自动验证，25 条需你核对"）
      ② 三档颜色卡片：✅ 可直接引用 / 🟡 数字对但句式改写 / ⚠️ 需翻原文核对
      ③ 底部"建议你做什么" —— 基于数字动态生成具体行动
    """
    prov = result.get("provenance_summary") or {}
    if not prov:
        return ""

    total = prov.get("total_claims") or 0
    ngram = prov.get("ngram_match") or {}
    high = ngram.get("high_confidence", 0) or 0
    medium = ngram.get("medium_confidence", 0) or 0
    low = ngram.get("low_confidence", 0) or 0
    failed = ngram.get("failed", 0) or 0
    hallu = prov.get("hallucination_risk_flags", failed) or 0

    if total == 0 and (high + medium + low + failed) == 0:
        return ""

    high_ratio = (high / total) if total > 0 else 0
    if high_ratio >= 0.6:
        overall = ("ok", "✅ 整体可信",
                   f"机器已自动验证 {high} 条核心事实，可放心引用；少量条目需抽空核对。")
    elif high_ratio >= 0.3 or hallu == 0:
        overall = ("warn", "🟡 中等可信",
                   f"{high} 条已验证 + {medium} 条数字对得上但句式改写；引用前快速核一下。")
    else:
        overall = ("danger", "⚠️ 低可信 · 引用前必须核对",
                   f"机器只能验证 {high} 条，{hallu} 条句式经过改写或跨栏 PDF 提取受限，"
                   f"建议照下方清单逐一翻原文 PDF。")

    overall_class, overall_label, overall_msg = overall

    cards = [
        ("ok", "✅ 可直接引用", high,
         "机器在原文找到原句强匹配（5-gram 命中）"),
        ("warn", "🟡 数字对得上 / 改写", medium + low,
         "数字、专名、术语命中但句式被改写；做引用前核一眼数字"),
        ("danger", "⚠️ 需要你翻原文核对", failed,
         "ngram 一个都没命中；常见于双栏 PDF 跨栏串行 + 中文意译"),
    ]
    cards_html = "".join(
        f'<div class="prov-card prov-{cls}">'
        f'<div class="prov-card-num">{n}</div>'
        f'<div class="prov-card-label">{label}</div>'
        f'<div class="prov-card-help">{help_txt}</div>'
        f'</div>'
        for cls, label, n, help_txt in cards
    )

    advice_bits: list[str] = []
    if failed > 0:
        warnings = result.get("warnings") or []
        has_double_col = any(
            (w.get("code") or "").upper() == "DOUBLE_COLUMN_EXTRACTION"
            for w in warnings
        )
        if has_double_col:
            advice_bits.append(
                "本批次含双栏 ACL/NeurIPS PDF，<b>跨栏文字提取受限</b>会导致 ngram 误判失败 ——"
                " 实际内容多数仍准确，请翻 PDF 原页面快速对照。"
            )
        advice_bits.append(
            f"翻看下方各论文卡片末尾 <b>『精读回答 / 关联点』</b> 段落，每条 claim 都标了 "
            f"<code>p.X · § Section</code>；先核 <b>{min(failed, 5)}</b> 条最关键的（数字 / 论点 / 实验设置）。"
        )
    if low > 0 and failed == 0:
        advice_bits.append(
            f"{low} 条 claim 是中文改写，原文 ngram 不命中很正常；"
            "若你只是要『大致理解』，可不核对；若要直接引用 → 翻 PDF 对照原文。"
        )
    if high == total and total > 0:
        advice_bits.append(
            "全部 claim 都强匹配命中 —— 这份报告可作为引用源使用。"
        )
    if not advice_bits:
        advice_bits.append("没有需要立即核对的 claim。")

    advice_html = "<ol class='prov-advice'>" + "".join(
        f"<li>{a}</li>" for a in advice_bits
    ) + "</ol>"

    cite_cover = prov.get("with_page_citation", total)
    return (
        f'<div class="prov-summary-block prov-overall-{overall_class}">'
        f'<div class="prov-overall">'
        f'<div class="prov-overall-label">{overall_label}</div>'
        f'<div class="prov-overall-msg">{overall_msg}</div>'
        f'</div>'
        f'<div class="prov-cards">{cards_html}</div>'
        f'<div class="prov-meta-row">'
        f'<span>共 <b>{total}</b> 条事实陈述</span>'
        f'<span>· 全部带页码追溯（{cite_cover}/{total}）</span>'
        f'</div>'
        f'<div class="prov-advice-head"><b>📌 接下来你可以：</b></div>'
        f'{advice_html}'
        f'</div>'
    )


def render_tldr_html(result: dict[str, Any]) -> str:
    """v0.3.0：顶层 tldr 字段 → 醒目 banner（黄底）。

    数据来源优先级：
      1. result.tldr（顶层显式字段，整份报告的核心一句话）
      2. 单篇模式 fallback：papers[0].summary_card.one_line_plain
    多篇对比若无显式 tldr，不自动 fallback（差异性结论必须人工写）。
    """
    tldr = (result.get("tldr") or "").strip()
    if not tldr:
        papers = result.get("papers") or []
        comparison = result.get("comparison")
        if not comparison and len(papers) == 1:
            sc = papers[0].get("summary_card") or {}
            tldr = (sc.get("one_line_plain") or "").strip()
    if not tldr:
        return ""
    return (
        f'<div class="tldr-banner">'
        f'<span class="tldr-label">TL;DR</span>'
        f'<span class="tldr-text">{esc(tldr)}</span>'
        f"</div>"
    )


def render_degraded_banner_html(result: dict[str, Any]) -> str:
    """v0.4.0 / P0-B：整篇置信度降级 → 红色 banner（顶部，比 tldr 还醒目）。

    数据来自 `result.meta.confidence_degraded`（由 verify_provenance.py --in-place 写入）。
    缺该字段或 is_degraded=False 时返回空串（保持简洁）。
    """
    meta = result.get("meta") or {}
    cd = meta.get("confidence_degraded") or {}
    if not cd.get("is_degraded"):
        return ""

    reason = cd.get("reason") or "unknown"
    reason_label_map = {
        "claims_removed": "强校验失败已删除 claim",
        "failed_count_exceeds": "失败 claim 数超阈值",
        "high_ratio_below_threshold": "高置信占比不足 60%",
    }
    reason_label = reason_label_map.get(reason, reason)
    stats = cd.get("stats") or {}
    high = stats.get("high", 0)
    total = stats.get("total", 0)
    failed = stats.get("failed", 0)
    high_ratio = cd.get("high_ratio")
    advice = cd.get("advice_zh") or "建议在 deep 模式下重读关键段落，或重新粘贴更长上下文。"

    ratio_part = f"{high_ratio:.0%}" if isinstance(high_ratio, (int, float)) else "—"
    stats_part = (
        f"high={high} · medium={stats.get('medium', 0)} · "
        f"low={stats.get('low', 0)} · failed={failed} · 总计 {total}"
    )

    return (
        f'<div class="degraded-banner" role="alert">'
        f'  <div class="degraded-head">'
        f'    <span class="degraded-icon">!</span>'
        f'    <span class="degraded-title">置信度降级 · {esc(reason_label)}</span>'
        f'  </div>'
        f'  <div class="degraded-stats">高置信占比 <b>{esc(ratio_part)}</b>'
        f'      （{esc(stats_part)}）</div>'
        f'  <div class="degraded-advice">{esc(advice)}</div>'
        f"</div>"
    )


def render_warnings(warnings: list[dict[str, Any]]) -> str:
    if not warnings:
        return ""
    boxes: list[str] = []
    for w in warnings:
        level = w.get("level", "info")
        css = {"error": "err", "warning": "", "info": "info"}.get(level, "info")
        boxes.append(
            f'<div class="warn-box {css}">'
            f'<b>[{esc(level.upper())}] {esc(w.get("code", ""))}</b> — {esc(w.get("message", ""))}'
            + (f" · 论文 {esc(w.get('paper_label'))}" if w.get("paper_label") else "")
            + (f" · 字段 {esc(w.get('affected_field'))}" if w.get("affected_field") else "")
            + "</div>"
        )
    return f"<section class='block'><h2>警告 / 提示</h2>{''.join(boxes)}</section>"


# ============================================================
# 主渲染流程
# ============================================================


def render(result: dict[str, Any], template: str) -> str:
    meta = result.get("meta") or {}
    papers = result.get("papers") or []
    comparison = result.get("comparison")
    warnings = result.get("warnings") or []
    prov_sum = result.get("provenance_summary") or {}

    global _PAGINATED
    _PAGINATED = bool(meta.get("paginated", True))
    for p in papers:
        if p.get("source_type") == "pasted_text" or p.get("paginated") is False:
            _PAGINATED = False
            break

    content_blocks: list[str] = []
    for i, p in enumerate(papers):
        content_blocks.append(render_paper_block(p, paper_idx=i))
    if comparison:
        content_blocks.append(render_comparison(comparison))
    content_html = "\n".join(content_blocks)

    depth_used = meta.get("depth_used") or []
    title = "AI 论文速读报告"
    if len(papers) == 1:
        title += f" · {papers[0].get('title', '')[:60]}"
    elif comparison:
        title += f" · {len(papers)} 篇对比"

    mapping = {
        "TITLE": esc(title),
        "MODE": esc(meta.get("mode") or "single"),
        "DEPTH_USED": esc(" / ".join(depth_used) or "skim"),
        "LANG": esc(meta.get("language") or "zh"),
        "PAPERS_COUNT": esc(len(papers)),
        "GENERATED_AT": esc(meta.get("generated_at") or ""),
        "DEGRADED_BANNER": render_degraded_banner_html(result),
        "TLDR_BLOCK": render_tldr_html(result),
        "CONTENT": content_html,
        "WARNINGS_BLOCK": render_warnings(warnings),
        "PROV_SUMMARY_BLOCK": render_provenance_summary_html(result),
        "SKILL_VERSION": esc(meta.get("skill_version") or SCRIPT_VERSION),
    }

    out = template
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", v)
    return out


# ============================================================
# Markdown 渲染（v0.2.0 新增 · 与 HTML 同源数据，零依赖纯文本）
# ============================================================


def _md_prov(loc: Optional[dict[str, Any]]) -> str:
    """Markdown 版 provenance 标记：(p.3 · §3 Method)"""
    if not loc or not isinstance(loc, dict):
        return ""
    page = loc.get("page")
    pages = loc.get("aggregate_pages") or ([page] if page is not None else [])
    section = loc.get("section")
    parts: list[str] = []
    if pages:
        parts.append("p." + ", p.".join(str(p) for p in pages))
    if section:
        parts.append(str(section))
    return f" _({' · '.join(parts)})_" if parts else ""


def _md_field(label: str, value: Any, loc: Any) -> str:
    """单字段渲染：标量 → 一行；列表 → 多 bullet。

    list 字段的 provenance 兼容两种 schema：
      (A) loc 是单 dict → 整组共享一个汇总 prov（放在 label 行尾）
      (B) loc 是 list of dict → 每项 bullet 后接自己的 prov
    """
    if value is None or value == "":
        return ""
    if isinstance(value, list):
        if isinstance(loc, list):
            items_lines = []
            for i, v in enumerate(value):
                item_loc = loc[i] if i < len(loc) and isinstance(loc[i], dict) else {}
                item_prov = _md_prov(item_loc) if item_loc else ""
                items_lines.append(f"- {v}{item_prov}")
            return f"**{label}**：\n\n" + "\n".join(items_lines) + "\n"
        prov = _md_prov(loc) if isinstance(loc, dict) else ""
        items = "\n".join(f"- {v}" for v in value)
        return f"**{label}**：{prov}\n\n{items}\n"
    prov = _md_prov(loc) if isinstance(loc, dict) else ""
    return f"**{label}**：{value}{prov}\n"


def _render_provenance_summary_md(result: dict[str, Any]) -> str:
    """v0.4.0：Markdown 版"用户视角"Provenance 汇总（同 HTML 数据源）。

    与 render_provenance_summary_html 同口径，文案一致；MD 不用色块，
    用 emoji + 嵌套 bullet 表达三档分级 + 行动建议。
    """
    prov = result.get("provenance_summary") or {}
    if not prov:
        return ""
    total = prov.get("total_claims") or 0
    ngram = prov.get("ngram_match") or {}
    high = ngram.get("high_confidence", 0) or 0
    medium = ngram.get("medium_confidence", 0) or 0
    low = ngram.get("low_confidence", 0) or 0
    failed = ngram.get("failed", 0) or 0
    hallu = prov.get("hallucination_risk_flags", failed) or 0
    if total == 0 and (high + medium + low + failed) == 0:
        return ""

    high_ratio = (high / total) if total > 0 else 0
    if high_ratio >= 0.6:
        head = "## 这份报告靠不靠谱？ ✅ 整体可信\n"
        msg = f"机器已自动验证 {high} 条核心事实，可放心引用；少量条目需抽空核对。\n"
    elif high_ratio >= 0.3 or hallu == 0:
        head = "## 这份报告靠不靠谱？ 🟡 中等可信\n"
        msg = f"{high} 条已验证 + {medium} 条数字对得上但句式改写；引用前快速核一下。\n"
    else:
        head = "## 这份报告靠不靠谱？ ⚠️ 低可信 · 引用前必须核对\n"
        msg = (f"机器只能验证 {high} 条，{hallu} 条句式经过改写或跨栏 PDF 提取受限，"
               "建议照下方清单逐一翻原文 PDF。\n")

    lines: list[str] = [head, msg]
    lines.append(f"- ✅ **可直接引用**：{high} 条 _(机器在原文找到原句强匹配)_")
    lines.append(f"- 🟡 **数字对得上 / 改写**：{medium + low} 条 _(数字、专名命中但句式被改写)_")
    lines.append(f"- ⚠️ **需要你翻原文核对**：{failed} 条 _(ngram 一个都没命中)_")
    lines.append(f"\n_共 **{total}** 条事实陈述 · 全部带页码追溯_\n")

    lines.append("**📌 接下来你可以：**\n")
    advice: list[str] = []
    warnings = result.get("warnings") or []
    has_double_col = any(
        (w.get("code") or "").upper() == "DOUBLE_COLUMN_EXTRACTION"
        for w in warnings
    )
    if failed > 0:
        if has_double_col:
            advice.append(
                "本批次含双栏 ACL/NeurIPS PDF，**跨栏文字提取受限**会导致 ngram 误判失败 ——"
                " 实际内容多数仍准确，请翻 PDF 原页面快速对照。"
            )
        advice.append(
            f"翻看下方各论文卡片末尾 **『精读回答 / 关联点』** 段落，"
            f"每条 claim 都标了 `p.X · § Section`；"
            f"先核 **{min(failed, 5)}** 条最关键的（数字 / 论点 / 实验设置）。"
        )
    if low > 0 and failed == 0:
        advice.append(
            f"{low} 条 claim 是中文改写，原文 ngram 不命中很正常；"
            "若你只是要『大致理解』，可不核对；若要直接引用 → 翻 PDF 对照原文。"
        )
    if high == total and total > 0:
        advice.append("全部 claim 都强匹配命中 —— 这份报告可作为引用源使用。")
    if not advice:
        advice.append("没有需要立即核对的 claim。")
    for i, a in enumerate(advice, 1):
        lines.append(f"{i}. {a}")
    lines.append("")
    return "\n".join(lines)


def render_markdown(result: dict[str, Any]) -> str:
    """渲染 result.json → 单文件 Markdown。

    与 HTML 同源（同一个 result.json），但格式更适合：
      - Cursor / VSCode 直接预览
      - 投递到 Obsidian / Logseq / Notion
      - 进 GitHub README / wiki
      - 与对话内容零格式偏差
    """
    meta = result.get("meta") or {}
    papers = result.get("papers") or []
    comparison = result.get("comparison")
    warnings = result.get("warnings") or []
    prov_sum = result.get("provenance_summary") or {}
    depth_used = meta.get("depth_used") or ["skim"]

    title = "AI 论文速读报告"
    if len(papers) == 1:
        title += f" · {papers[0].get('title', '')[:80]}"
    elif comparison:
        title += f" · {len(papers)} 篇对比"

    lines: list[str] = []
    lines.append(f"# {title}\n")

    meta_bar = [
        f"**模式** `{meta.get('mode') or 'single'}`",
        f"**深度** `{' / '.join(depth_used)}`",
        f"**论文数** {len(papers)}",
        f"**语言** {meta.get('language') or 'zh'}",
        f"**生成于** {meta.get('generated_at') or '—'}",
    ]
    lines.append(" · ".join(meta_bar) + "\n")

    # v0.4.0 / P0-B：整篇置信度降级 banner（在最顶部，比 TLDR 还要醒目）
    cd = meta.get("confidence_degraded") or {}
    if cd.get("is_degraded"):
        reason_label_map = {
            "claims_removed": "强校验失败已删除 claim",
            "failed_count_exceeds": "失败 claim 数超阈值",
            "high_ratio_below_threshold": "高置信占比不足 60%",
        }
        reason_label = reason_label_map.get(cd.get("reason"), cd.get("reason") or "unknown")
        stats = cd.get("stats") or {}
        ratio = cd.get("high_ratio")
        ratio_part = f"{ratio:.0%}" if isinstance(ratio, (int, float)) else "—"
        advice = cd.get("advice_zh") or "建议在 deep 模式下重读关键段落，或重新粘贴更长上下文。"
        lines.append(f"> ⚠️ **置信度降级 · {reason_label}**  ")
        lines.append(
            f"> 高置信占比 **{ratio_part}**（high={stats.get('high', 0)} · "
            f"medium={stats.get('medium', 0)} · low={stats.get('low', 0)} · "
            f"failed={stats.get('failed', 0)} · 总计 {stats.get('total', 0)}）  "
        )
        lines.append(f"> {advice}\n")

    # 顶层 TL;DR（v0.3.0）
    tldr = (result.get("tldr") or "").strip()
    if not tldr and not comparison and len(papers) == 1:
        tldr = ((papers[0].get("summary_card") or {}).get("one_line_plain") or "").strip()
    if tldr:
        lines.append(f"> **TL;DR** — {tldr}\n")

    lines.append("---\n")

    # 每篇 paper
    for p in papers:
        lines.append(_render_paper_md(p))

    # 对比块
    if comparison:
        lines.append(_render_comparison_md(comparison))

    lines.append(_render_provenance_summary_md(result))

    # 警告
    if warnings:
        lines.append("## 警告 / 提示\n")
        for w in warnings:
            level = (w.get("level") or "info").upper()
            code = w.get("code", "")
            msg = w.get("message", "")
            extra = []
            if w.get("paper_label"):
                extra.append(f"论文 {w['paper_label']}")
            if w.get("affected_field"):
                extra.append(f"字段 {w['affected_field']}")
            extra_str = f" · {' · '.join(extra)}" if extra else ""
            lines.append(f"- **[{level}]** `{code}` — {msg}{extra_str}")
        lines.append("")

    lines.append("---\n")
    lines.append(
        f"_由 **paper-quick-reader** v{meta.get('skill_version') or SCRIPT_VERSION} 生成 · "
        f"所有引用均可追溯至原文 page + section_\n"
    )

    return "\n".join(lines)


def _render_paper_md(paper: dict[str, Any]) -> str:
    label = paper.get("label") or ""
    title = paper.get("title") or "（未解析标题）"
    head = f"## [{label}] {title}\n" if label else f"## {title}\n"

    meta_bits = []
    if paper.get("authors"):
        meta_bits.append("**作者** " + ", ".join(paper["authors"]))
    if paper.get("year"):
        meta_bits.append(f"**年份** {paper['year']}")
    if paper.get("venue"):
        meta_bits.append(f"**期刊/会议** {paper['venue']}")
    meta_bits.append(f"**共 {paper.get('total_pages', '?')} 页**")
    head += " · ".join(meta_bits) + "\n\n"

    sc = paper.get("summary_card") or {}
    pmap = sc.get("provenance_map") or {}
    sections: list[str] = []

    sections.append("### 摘要卡\n")
    for label_zh, key in [
        ("研究问题", "research_question"),
        ("方法", "method"),
        ("数据集", "dataset"),
        ("关键结果", "key_results"),
        ("贡献", "contributions"),
        ("局限", "limitations"),
    ]:
        text = _md_field(label_zh, sc.get(key), pmap.get(key))
        if text:
            sections.append(text)

    # v0.2.0 扩展字段
    if sc.get("method_formula"):
        loc = pmap.get("method_formula") or {}
        prov = _md_prov(loc)
        sections.append(f"**方法公式**：{prov}\n\n```\n{sc['method_formula']}\n```\n")
    if sc.get("one_line_plain"):
        loc = pmap.get("one_line_plain") or {}
        prov = _md_prov(loc)
        sections.append(f"> **一句话** — {sc['one_line_plain']}{prov}\n")

    # 推荐追问
    rq = paper.get("recommended_questions") or []
    if rq:
        sections.append("### AI 推荐追问\n")
        for q in rq:
            qtext = q.get("q") or q.get("question") or ""
            why = q.get("why", "")
            sections.append(f"- **{qtext}**")
            if why:
                sections.append(f"  - _{why}_")
        sections.append("")

    # 关联点
    cps = paper.get("connection_points") or []
    if cps:
        sections.append("### 与你研究方向的关联点\n")
        for cp in cps:
            t = cp.get("type", "")
            insight = cp.get("insight", "")
            pages = cp.get("evidence_pages") or []
            score = cp.get("relevance_score")
            score_str = f"{float(score):.2f}" if score is not None else "—"
            pages_str = ", ".join(f"p.{p}" for p in pages) if pages else "—"
            sections.append(f"- **[{t}]** (relevance {score_str}) {insight}")
            sections.append(f"  - 证据页：{pages_str}")
        sections.append("")

    # 精读
    dd = paper.get("deep_dive_answers") or []
    if dd:
        sections.append("### 精读回答\n")
        for item in dd:
            q = item.get("question", "")
            a = item.get("answer", "")
            sections.append(f"#### Q: {q}\n")
            sections.append(f"{a}\n")
            for ex in (item.get("original_excerpts") or []):
                page = ex.get("page")
                section = ex.get("section") or ""
                cite = (f"p.{page}" if page is not None else "—") + (f" · {section}" if section else "")
                sections.append(f"> {ex.get('text', '')}\n>\n> _— {cite}_\n")
            ca = item.get("critical_analysis") or {}
            for ca_key, ca_label in [
                ("agree_with", "同意 / 认可"),
                ("question", "质疑 / 追问"),
                ("complement", "对你方向的补充"),
            ]:
                items = ca.get(ca_key) or []
                if items:
                    sections.append(f"**{ca_label}**：")
                    for x in items:
                        sections.append(f"- {x}")
                    sections.append("")

    refs = paper.get("references") or []
    refs_meta = paper.get("references_meta") or {}
    if refs or refs_meta.get("extraction_notes"):
        sections.append("### 参考文献（References）\n")
        if refs_meta.get("extracted") is False and refs_meta.get("extraction_notes"):
            sections.append("**抽取说明：**")
            for n in (refs_meta.get("extraction_notes") or []):
                sections.append(f"- {n}")
            sections.append("")
        if refs:
            for r in refs:
                if not isinstance(r, dict):
                    continue
                idx = r.get("idx") or "?"
                raw = (r.get("raw") or "").replace("\n", " ")
                page = r.get("page")
                year = r.get("year")
                bits = []
                if page is not None:
                    bits.append(f"p.{page}")
                if year is not None:
                    bits.append(str(year))
                tail = f" _({' · '.join(bits)})_" if bits else ""
                sections.append(f"- **[{idx}]** {raw}{tail}")
            sections.append("")
        elif not (refs_meta.get("extraction_notes")):
            sections.append("_未抽取到 references_\n")

    return head + "\n".join(sections) + "\n---\n"


def _render_comparison_md(comp: dict[str, Any]) -> str:
    out: list[str] = ["## 多篇对比\n"]
    labels = comp.get("papers_labels") or []
    table = comp.get("table") or []

    if labels and table:
        head = "| 维度 | " + " | ".join(labels) + " |"
        sep = "|---" * (1 + len(labels)) + "|"
        out.append(head)
        out.append(sep)
        for row in table:
            dim = row.get("dimension", "")
            rows_data = row.get("rows") or {}
            cells = []
            for l in labels:
                cell = rows_data.get(l, {}) or {}
                content = cell.get("content") or "—"
                content = str(content).replace("|", "\\|").replace("\n", " ")
                prov = _md_prov(cell.get("provenance") or {})
                cells.append(content + prov)
            out.append(f"| **{dim}** | " + " | ".join(cells) + " |")
        out.append("")

    narrative = comp.get("differences_narrative")
    if narrative:
        out.append("### 差异叙述\n")
        if isinstance(narrative, str):
            out.append(narrative + "\n")
        elif isinstance(narrative, list):
            for t in narrative:
                if isinstance(t, dict):
                    out.append(f"**{t.get('theme', '')}** — {t.get('summary', '')}")
                    cites = t.get("cite") or {}
                    if cites:
                        cite_str = "；".join(
                            f"{k}: " + ", ".join(f"p.{p}" for p in v) for k, v in cites.items()
                        )
                        out.append(f"  - _{cite_str}_")
                else:
                    out.append(f"- {t}")
            out.append("")

    cpa = comp.get("cross_paper_answer")
    if cpa:
        out.append("### 跨论文综合回答\n")
        out.append(f"**问题**：{cpa.get('question', '')}\n")
        out.append(f"{cpa.get('answer', '')}\n")
        for lbl, evs in (cpa.get("per_paper_evidence") or {}).items():
            for ex in evs:
                page = ex.get("page")
                cite = (f"p.{page}" if page is not None else "—")
                out.append(f"> [{lbl}] {ex.get('excerpt', '')}\n>\n> _— {cite}_\n")

    kt = comp.get("key_takeaways_for_user_direction") or []
    if kt:
        out.append("### 对你研究方向的 Key Takeaways\n")
        for x in kt:
            out.append(f"- {x}")
        out.append("")

    synth_md = _render_synthesis_block_md(comp.get("synthesis_block"))
    if synth_md:
        out.append(synth_md)

    return "\n".join(out) + "\n---\n"


def _render_synthesis_block_md(synth: Optional[dict[str, Any]]) -> str:
    """v0.4.0 / P1-A：synthesis_block 的 Markdown 渲染。"""
    if not synth or not isinstance(synth, dict):
        return ""
    parts: list[str] = []

    lineage = (synth.get("research_lineage") or "").strip()
    if lineage:
        parts.append(f"### 研究脉络与共识\n")
        parts.append(f"**研究脉络**：{lineage}\n")

    evolution = synth.get("method_evolution") or []
    if evolution:
        if not lineage:
            parts.append("### 研究脉络与共识\n")
        parts.append("**方法演进**：\n")
        for stage in evolution:
            if not isinstance(stage, dict):
                continue
            label = stage.get("label", "")
            year = stage.get("year")
            year_str = f" · {year}" if year is not None else ""
            stage_name = stage.get("stage", "")
            key_move = stage.get("key_move", "")
            rationale = stage.get("rationale", "")
            parts.append(f"1. **[{label}] {stage_name}**{year_str}")
            parts.append(f"   - {key_move}")
            parts.append(f"   - _动机_：{rationale}")
        parts.append("")

    disagreements = synth.get("key_disagreements") or []
    if disagreements:
        if not lineage and not evolution:
            parts.append("### 研究脉络与共识\n")
        parts.append("**关键分歧**：\n")
        for d in disagreements:
            if not isinstance(d, dict):
                continue
            topic = d.get("topic", "")
            parts.append(f"- {topic}")
            positions = d.get("positions") or {}
            ev_pages = d.get("evidence_pages") or {}
            for lbl, pos in positions.items():
                page = ev_pages.get(lbl)
                page_str = f" _(p.{page})_" if page is not None else ""
                parts.append(f"  - **[{lbl}]** {pos}{page_str}")
        parts.append("")

    consensus = synth.get("consensus") or []
    if consensus:
        if not lineage and not evolution and not disagreements:
            parts.append("### 研究脉络与共识\n")
        parts.append("**共识**：\n")
        for c in consensus:
            parts.append(f"- {c}")
        parts.append("")

    open_qs = synth.get("open_questions") or []
    if open_qs:
        if not lineage and not evolution and not disagreements and not consensus:
            parts.append("### 研究脉络与共识\n")
        parts.append("**未解之谜**：\n")
        for q in open_qs:
            parts.append(f"- {q}")
        parts.append("")

    return "\n".join(parts)


# ============================================================
# CLI
# ============================================================


def _html_to_pdf(html_str: str, pdf_path: Path) -> tuple[bool, str]:
    """HTML → PDF。优先 weasyprint；缺依赖时返回 (False, 友好提示) 让上层降级。

    返回值：
      (True,  "")     —— 已成功写入 pdf_path
      (False, msg)    —— 未生成 PDF，msg 为可直接 stderr 给用户的中文降级提示
    """
    try:
        from weasyprint import HTML  # type: ignore
    except ImportError:
        return (
            False,
            "未检测到 weasyprint —— PDF 渲染需要 `pip install weasyprint` "
            "（macOS 还需 brew install pango cairo gdk-pixbuf libffi）。"
            "已自动降级生成同名 .html，请用浏览器打开后按 ⌘+P 打印为 PDF。",
        )
    except Exception as e:  # pragma: no cover - 系统库异常路径
        return (
            False,
            f"weasyprint 加载失败（可能是底层 pango/cairo 系统库缺失）：{e}。"
            "已自动降级生成同名 .html，请用浏览器打开后按 ⌘+P 打印为 PDF。",
        )

    try:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=html_str).write_pdf(str(pdf_path))
        return True, ""
    except Exception as e:  # pragma: no cover - PDF 写入异常
        return (
            False,
            f"weasyprint 渲染 PDF 失败：{e}。"
            "已自动降级生成同名 .html，请用浏览器打开后按 ⌘+P 打印为 PDF。",
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render paper-quick-reader result.json to HTML / Markdown / PDF",
    )
    parser.add_argument("result", help="Path to result.json")
    parser.add_argument(
        "--out", "-o", default=None,
        help="Output path; for multi-format (all / 多个 -f), used as basename "
             "(extension auto). Default: <result_dir>/report.{html|md|pdf}",
    )
    parser.add_argument(
        "--format", "-f", default="html",
        help="Output format: html (default) / md / pdf / all。"
             "支持逗号或空格分隔的多选，如 -f html,md,pdf 等价于 -f all。",
    )
    parser.add_argument(
        "--template", "-t", default=None,
        help="HTML template path (only for html/pdf/all); default: assets/report-template.html",
    )
    args = parser.parse_args(argv)

    result_path = Path(args.result).expanduser().resolve()
    if not result_path.exists():
        _err(f"result.json 不存在: {result_path}")
        return 1
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _err(f"result.json 解析失败: {e}")
        return 1

    formats = _parse_format_arg(args.format)
    if not formats:
        _err(f"无法识别的 --format 取值: {args.format!r}")
        return 1

    out_arg = Path(args.out).expanduser().resolve() if args.out else None
    multi = len(formats) > 1
    written: list[Path] = []

    html_out: Optional[str] = None
    if formats & {"html", "pdf"}:
        tpl_path = Path(args.template).expanduser().resolve() if args.template else DEFAULT_TEMPLATE
        if not tpl_path.exists():
            _err(f"HTML 模板不存在: {tpl_path}")
            return 1
        template = tpl_path.read_text(encoding="utf-8")
        html_out = render(result, template)

    def _path_for(suffix: str, default_name: str) -> Path:
        if out_arg and not multi:
            return out_arg
        if out_arg and multi:
            return out_arg.with_suffix(suffix)
        return result_path.parent / default_name

    if "html" in formats:
        html_path = _path_for(".html", "report.html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        assert html_out is not None
        html_path.write_text(html_out, encoding="utf-8")
        written.append(html_path)

    if "md" in formats:
        md_out = render_markdown(result)
        md_path = _path_for(".md", "report.md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_out, encoding="utf-8")
        written.append(md_path)

    if "pdf" in formats:
        pdf_path = _path_for(".pdf", "report.pdf")
        assert html_out is not None
        ok, msg = _html_to_pdf(html_out, pdf_path)
        if ok:
            written.append(pdf_path)
        else:
            _err(msg)
            fallback = pdf_path.with_suffix(".html")
            if fallback in written:
                # 多选场景下 html 分支已写过；不再重复，避免误导
                _err(f"降级 HTML 复用已有文件: {fallback}")
            else:
                fallback.parent.mkdir(parents=True, exist_ok=True)
                fallback.write_text(html_out, encoding="utf-8")
                _err(f"降级 HTML 已生成: {fallback}")
                written.append(fallback)

    for p in written:
        _err(f"已生成: {p}")
    return 0


def _parse_format_arg(raw: str) -> set[str]:
    """把 --format 取值解析成 {'html','md','pdf'} 子集。

    支持：
      - 单值: html / md / markdown / pdf / all
      - 多值: 逗号或空格分隔，如 'html,pdf' / 'md pdf' / 'html, md, pdf'
      - 'all' 等价于全选
    未知 token 一律忽略；返回空集表示完全无效。
    """
    if not raw:
        return set()
    tokens = [t.strip().lower() for t in raw.replace(",", " ").split() if t.strip()]
    out: set[str] = set()
    for t in tokens:
        if t == "all":
            return {"html", "md", "pdf"}
        if t == "markdown":
            out.add("md")
        elif t in ("html", "md", "pdf"):
            out.add(t)
    return out


def _err(msg: str) -> None:
    sys.stderr.write(f"[render_report] {msg}\n")


if __name__ == "__main__":
    sys.exit(main())

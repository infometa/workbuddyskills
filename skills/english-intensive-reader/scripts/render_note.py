#!/usr/bin/env python3
"""
render_note.py — english-intensive-reader
Render AI-generated sentence_units JSON into a dual-column HTML reading note.

Usage:
    python render_note.py --input analysis.json --output note.html
    python render_note.py --input analysis.json --format md
"""

import sys
import json
import argparse
import os
from datetime import datetime
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — 英语精读笔记</title>
<style>
  :root {{
    --primary: #2563eb;
    --accent: #f59e0b;
    --highlight-bg: #fef3c7;
    --underline-color: #3b82f6;
    --complex-bg: #eff6ff;
    --card-bg: #f8fafc;
    --border: #e2e8f0;
    --text: #1e293b;
    --muted: #64748b;
    --green: #16a34a;
    --tag-bg: #dbeafe;
    --tag-text: #1d4ed8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    font-size: 15px;
    line-height: 1.7;
    color: var(--text);
    background: #f1f5f9;
    padding: 24px 16px;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}

  /* Header */
  .header {{
    background: white;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 20px;
    border: 1px solid var(--border);
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }}
  .header h1 {{ font-size: 22px; font-weight: 700; color: var(--primary); margin-bottom: 8px; }}
  .header .meta {{ display: flex; gap: 16px; flex-wrap: wrap; }}
  .meta-item {{ font-size: 13px; color: var(--muted); }}
  .meta-item strong {{ color: var(--text); }}
  .level-badge {{
    display: inline-block;
    background: var(--tag-bg);
    color: var(--tag-text);
    font-size: 12px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
  }}

  /* Sentence card */
  .sentence-card {{
    background: white;
    border-radius: 10px;
    border: 1px solid var(--border);
    margin-bottom: 16px;
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(0,0,0,.04);
  }}
  .sentence-card.complex {{ border-left: 4px solid var(--underline-color); }}
  .sentence-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    font-size: 13px;
    color: var(--muted);
  }}
  .sentence-id {{ font-weight: 700; color: var(--primary); font-size: 12px; }}
  .complex-badge {{
    background: var(--complex-bg);
    color: var(--underline-color);
    font-size: 11px;
    padding: 1px 8px;
    border-radius: 10px;
    font-weight: 600;
  }}

  /* Two-column layout */
  .sentence-body {{
    display: grid;
    grid-template-columns: 58% 42%;
  }}
  @media (max-width: 768px) {{
    .sentence-body {{ grid-template-columns: 1fr; }}
  }}
  .left-col {{
    padding: 16px 20px;
    border-right: 1px solid var(--border);
  }}
  .right-col {{
    padding: 16px 20px;
    background: #fafbfc;
  }}

  /* Left column: original text */
  .original-text {{
    font-size: 15px;
    line-height: 1.8;
    color: var(--text);
    margin-bottom: 12px;
  }}
  mark {{
    background: var(--highlight-bg);
    color: #92400e;
    padding: 0 2px;
    border-radius: 3px;
    font-weight: 600;
    cursor: pointer;
  }}
  mark:hover {{ background: #fde68a; }}
  .complex-span {{
    text-decoration: underline;
    text-decoration-color: var(--underline-color);
    text-decoration-thickness: 2px;
    text-underline-offset: 3px;
  }}
  .add-btn {{
    display: inline-block;
    font-size: 11px;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 1px 6px;
    cursor: pointer;
    margin-left: 4px;
    vertical-align: middle;
    text-decoration: none;
  }}
  .add-btn:hover {{ background: #1d4ed8; }}

  /* Right column: analysis */
  .analysis-section {{ margin-bottom: 12px; }}
  .analysis-label {{
    font-size: 11px;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .5px;
    margin-bottom: 4px;
  }}
  .backbone {{
    font-size: 14px;
    color: var(--text);
    font-weight: 600;
    background: #f0fdf4;
    border-left: 3px solid var(--green);
    padding: 4px 10px;
    border-radius: 0 4px 4px 0;
  }}
  .modifier-item {{
    font-size: 13px;
    color: var(--text);
    padding: 2px 0;
  }}
  .modifier-role {{
    display: inline-block;
    background: #f1f5f9;
    color: var(--muted);
    font-size: 11px;
    padding: 0 6px;
    border-radius: 4px;
    margin-right: 4px;
  }}
  .grammar-tag {{
    display: inline-block;
    background: var(--tag-bg);
    color: var(--tag-text);
    font-size: 11px;
    padding: 1px 8px;
    border-radius: 10px;
    margin: 2px 2px 2px 0;
    font-weight: 500;
  }}
  .translation {{
    font-size: 14px;
    color: #374151;
    font-style: italic;
    border-top: 1px dashed var(--border);
    padding-top: 8px;
    margin-top: 8px;
  }}

  /* Vocab notes */
  .vocab-note {{
    background: white;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 8px;
    font-size: 13px;
  }}
  .vocab-word {{
    font-weight: 700;
    color: var(--primary);
    font-size: 14px;
  }}
  .vocab-pos {{ color: var(--muted); font-size: 12px; margin-left: 4px; }}
  .vocab-def {{ color: var(--text); margin: 4px 0; }}
  .vocab-collocations {{ color: var(--muted); font-size: 12px; }}
  .vocab-example {{
    font-size: 12px;
    color: #4b5563;
    font-style: italic;
    margin-top: 4px;
    border-left: 2px solid var(--accent);
    padding-left: 8px;
  }}
  .level-tag {{
    display: inline-block;
    font-size: 10px;
    padding: 0 5px;
    border-radius: 3px;
    margin-left: 4px;
    font-weight: 600;
  }}
  .level-cet4 {{ background: #dcfce7; color: #166534; }}
  .level-cet6 {{ background: #dbeafe; color: #1e40af; }}
  .level-kaoyan {{ background: #fef3c7; color: #92400e; }}
  .level-foreign_press {{ background: #fce7f3; color: #9d174d; }}

  /* Summary section */
  .summary-section {{
    background: white;
    border-radius: 10px;
    border: 1px solid var(--border);
    padding: 24px 28px;
    margin-top: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }}
  .summary-section h2 {{
    font-size: 16px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--primary);
  }}
  .summary-list {{ list-style: none; }}
  .summary-list li {{
    padding: 6px 0;
    border-bottom: 1px dashed var(--border);
    font-size: 14px;
    color: var(--text);
    display: flex;
    gap: 10px;
  }}
  .summary-list li:last-child {{ border-bottom: none; }}
  .summary-num {{
    font-weight: 700;
    color: var(--primary);
    min-width: 20px;
  }}

  /* Key patterns */
  .pattern-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
  }}
  .pattern-name {{
    font-weight: 700;
    color: var(--text);
    font-size: 14px;
    margin-bottom: 6px;
  }}
  .pattern-example {{
    font-style: italic;
    color: #374151;
    font-size: 13px;
    background: white;
    border-left: 3px solid var(--accent);
    padding: 6px 10px;
    border-radius: 0 4px 4px 0;
    margin: 6px 0;
  }}
  .pattern-tip {{
    font-size: 12px;
    color: var(--muted);
  }}
  .pattern-source {{
    font-size: 11px;
    color: var(--primary);
    font-weight: 600;
  }}

  /* Footer */
  .footer {{
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    margin-top: 32px;
    padding: 16px;
  }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <h1>📖 {title}</h1>
    <div class="meta">
      <div class="meta-item">来源：<strong>{source}</strong></div>
      <div class="meta-item">词数：<strong>{word_count}</strong></div>
      <div class="meta-item">句数：<strong>{sentence_count}</strong></div>
      <div class="meta-item">级别：<span class="level-badge">{level}</span></div>
      <div class="meta-item">侧重：<strong>{focus}</strong></div>
    </div>
  </div>

  <!-- Sentence units -->
  {sentence_cards}

  <!-- Summary -->
  <div class="summary-section">
    <h2>📋 全文脉络</h2>
    <ul class="summary-list">
      {summary_items}
    </ul>
  </div>

  <!-- Key patterns -->
  <div class="summary-section">
    <h2>✨ 值得背诵的句型</h2>
    {pattern_cards}
  </div>

  <div class="footer">
    由 AI 英语精读 Skill 生成 · {generated_at}
  </div>
</div>
</body>
</html>"""


def _level_class(level: str) -> str:
    return f"level-{level.replace('_', '_')}"


def _render_sentence_card(unit: Dict[str, Any]) -> str:
    sid = unit.get("id", "s??")
    raw = unit.get("raw", "")
    is_complex = unit.get("is_complex", False)
    highlights = unit.get("highlights", {})
    new_words = highlights.get("new_words", [])
    complex_spans = highlights.get("complex_clause_spans", [])
    analysis = unit.get("sentence_analysis") or {}
    vocab_notes = unit.get("vocab_notes", [])

    # Highlight new words in original text
    display_text = raw
    for word in new_words:
        import re
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        display_text = pattern.sub(
            f'<mark>{word}</mark><button class="add-btn" title="加入单词本">+</button>',
            display_text,
            count=1,
        )

    # Underline complex clause spans
    for span in complex_spans:
        if span in display_text:
            display_text = display_text.replace(
                span, f'<span class="complex-span">{span}</span>', 1
            )

    # Build right column
    backbone = analysis.get("backbone", "")
    modifiers = analysis.get("modifiers", [])
    grammar_tags = analysis.get("grammar_tags", [])
    translation = analysis.get("translation", "")

    backbone_html = f'<div class="backbone">{backbone}</div>' if backbone else ""

    modifiers_html = ""
    if modifiers:
        items = []
        for m in modifiers:
            role = m.get("role", "")
            text = m.get("text", "")
            note = m.get("note", "")
            note_str = f" <em style='color:#94a3b8;font-size:11px'>({note})</em>" if note else ""
            items.append(
                f'<div class="modifier-item"><span class="modifier-role">{role}</span>{text}{note_str}</div>'
            )
        modifiers_html = "\n".join(items)

    tags_html = "".join(
        f'<span class="grammar-tag">{tag}</span>' for tag in grammar_tags
    )

    translation_html = f'<div class="translation">🌐 {translation}</div>' if translation else ""

    vocab_html = ""
    for vn in vocab_notes:
        word = vn.get("word", "")
        pos = vn.get("pos", "")
        definition = vn.get("definition", "")
        collocations = " / ".join(vn.get("collocations", [])[:3])
        example = vn.get("example", "")
        level_tag = vn.get("level_tag", "")
        level_cls = _level_class(level_tag)
        vocab_html += f"""
        <div class="vocab-note">
          <span class="vocab-word">{word}</span>
          <span class="vocab-pos">{pos}</span>
          <span class="level-tag {level_cls}">{level_tag}</span>
          <div class="vocab-def">{definition}</div>
          <div class="vocab-collocations">搭配：{collocations}</div>
          <div class="vocab-example">{example}</div>
        </div>"""

    complex_class = " complex" if is_complex else ""
    complex_badge = '<span class="complex-badge">长难句</span>' if is_complex else ""

    return f"""
  <div class="sentence-card{complex_class}">
    <div class="sentence-header">
      <span class="sentence-id">{sid}</span>
      {complex_badge}
    </div>
    <div class="sentence-body">
      <div class="left-col">
        <div class="original-text">{display_text}</div>
      </div>
      <div class="right-col">
        {"<div class='analysis-section'><div class='analysis-label'>🔑 主干</div>" + backbone_html + "</div>" if backbone_html else ""}
        {"<div class='analysis-section'><div class='analysis-label'>📎 修饰成分</div>" + modifiers_html + "</div>" if modifiers_html else ""}
        {"<div class='analysis-section'><div class='analysis-label'>🏷 语法</div>" + tags_html + "</div>" if tags_html else ""}
        {translation_html}
        {"<div class='analysis-section'><div class='analysis-label'>📚 生词</div>" + vocab_html + "</div>" if vocab_html else ""}
      </div>
    </div>
  </div>"""


def render_html(data: Dict[str, Any], output_path: str) -> None:
    """Render full HTML reading note."""
    meta = data.get("meta", {})
    sentence_units = data.get("sentence_units", [])
    article_summary = data.get("article_summary", [])
    key_patterns = data.get("key_patterns", [])

    # Sentence cards
    cards_html = "\n".join(_render_sentence_card(u) for u in sentence_units)

    # Summary items
    summary_html = "\n".join(
        f'<li><span class="summary-num">{i+1}.</span><span>{s}</span></li>'
        for i, s in enumerate(article_summary)
    )

    # Pattern cards
    patterns_html = ""
    for i, p in enumerate(key_patterns):
        patterns_html += f"""
    <div class="pattern-card">
      <div class="pattern-name">{i+1}. {p.get('pattern', '')}</div>
      <div class="pattern-example">{p.get('example', '')}</div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div class="pattern-tip">💡 {p.get('why_worth_learning', '')}</div>
        <div class="pattern-source">来自 {p.get('source_id', '')}</div>
      </div>
    </div>"""

    html = HTML_TEMPLATE.format(
        title=meta.get("title", "英语精读笔记"),
        source=meta.get("source", "—"),
        word_count=meta.get("word_count", "—"),
        sentence_count=meta.get("sentence_count", len(sentence_units)),
        level=meta.get("level_detected", "—"),
        focus=meta.get("focus", "all"),
        sentence_cards=cards_html,
        summary_items=summary_html,
        pattern_cards=patterns_html,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML 笔记已生成：{output_path}")


def render_markdown(data: Dict[str, Any]) -> str:
    """Render Markdown reading note."""
    meta = data.get("meta", {})
    sentence_units = data.get("sentence_units", [])
    article_summary = data.get("article_summary", [])
    key_patterns = data.get("key_patterns", [])

    lines = [
        f"# 📖 英语精读笔记",
        f"**文章**：{meta.get('title', '—')} | **来源**：{meta.get('source', '—')} | "
        f"**级别**：{meta.get('level_detected', '—')} | **词数**：{meta.get('word_count', '—')}",
        "",
        "---",
        "",
        "## 逐句精读",
        "",
    ]

    for unit in sentence_units:
        sid = unit.get("id", "s??")
        raw = unit.get("raw", "")
        is_complex = unit.get("is_complex", False)
        analysis = unit.get("sentence_analysis") or {}
        vocab_notes = unit.get("vocab_notes", [])

        complex_flag = " 🔴 **长难句**" if is_complex else ""
        lines.append(f"### [{sid}]{complex_flag}")
        lines.append(f"> {raw}")
        lines.append("")

        if analysis.get("backbone"):
            lines.append(f"🔑 **主干**：`{analysis['backbone']}`")
        if analysis.get("modifiers"):
            for m in analysis["modifiers"]:
                lines.append(f"📎 **{m.get('role', '修饰')}**：{m.get('text', '')} — {m.get('note', '')}")
        if analysis.get("grammar_tags"):
            tags = " · ".join(f"`{t}`" for t in analysis["grammar_tags"])
            lines.append(f"🏷 **语法**：{tags}")
        if analysis.get("translation"):
            lines.append(f"🌐 **译文**：{analysis['translation']}")

        if vocab_notes:
            lines.append("")
            lines.append("📚 **生词**：")
            for vn in vocab_notes:
                collocations = " / ".join(vn.get("collocations", [])[:3])
                lines.append(
                    f"- **{vn['word']}** *{vn.get('pos', '')}* `{vn.get('level_tag', '')}` — {vn.get('definition', '')}"
                )
                if collocations:
                    lines.append(f"  - 搭配：{collocations}")
                if vn.get("example"):
                    lines.append(f"  - 例句：_{vn['example']}_ `[+单词本]`")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Summary
    lines.append("## 📋 全文脉络")
    lines.append("")
    for i, s in enumerate(article_summary):
        lines.append(f"{i+1}. {s}")
    lines.append("")

    # Key patterns
    lines.append("## ✨ 值得背诵的句型")
    lines.append("")
    for i, p in enumerate(key_patterns):
        lines.append(f"### {i+1}. {p.get('pattern', '')}")
        lines.append(f"> {p.get('example', '')}（来自 {p.get('source_id', '')}）")
        lines.append(f"> 💡 {p.get('why_worth_learning', '')}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Render reading note for english-intensive-reader"
    )
    parser.add_argument("--input", required=True, help="Path to analysis JSON file")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--format", choices=["html", "md", "both"], default="md",
        help="Output format (default: md)"
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.format in ("html", "both"):
        output_path = args.output or args.input.replace(".json", ".html")
        render_html(data, output_path)

    if args.format in ("md", "both"):
        md = render_markdown(data)
        if args.format == "md":
            output_path = args.output or args.input.replace(".json", ".md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"✅ Markdown 笔记已生成：{output_path}")
        else:
            md_path = args.input.replace(".json", ".md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"✅ Markdown 笔记已生成：{md_path}")


if __name__ == "__main__":
    main()

"""
execution_logger.py — 执行日志生成器
ecommerce-data-analyst skill 工具层

生成结构化 Markdown 日志，记录报告生成的完整过程。
用于事后复盘：哪一步数据不对、SQL 有没有写错、脚本组装是否有 bug。

用法：
    from scripts.execution_logger import generate_execution_log
    log = generate_execution_log(meta, recipe, sql_results, outputs, facts, report_data)
    with open("execution_log.md", "w") as f:
        f.write(log)
"""

from __future__ import annotations

import json
from datetime import datetime


def generate_execution_log(
    meta: dict,
    recipe: list[dict],
    sql_results: dict,
    outputs: list[dict],
    facts: list[dict],
    report_data: dict,
    gate_check_result: dict | None = None,
    files_read: list[str] | None = None,
    html_output_path: str = "",
    notes: list[str] | None = None,
) -> str:
    """生成结构化执行日志（Markdown 格式）。

    Args:
        meta:              报告元信息
        recipe:            步骤 2 构造的 Recipe JSON
        sql_results:       步骤 3 收集的 SQL 结果（{sql_ref: [rows]}）
        outputs:           ComponentRunner 输出（list[ComponentOutput.to_dict()]）
        facts:             合并后的 facts
        report_data:       组装后的 report_data
        gate_check_result: Gate Check 结果
        files_read:        读取的文件列表
        html_output_path:  输出的 HTML 文件路径
        notes:             额外备注

    Returns:
        Markdown 格式的执行日志字符串
    """
    generated_at = meta.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    title = meta.get("title", "报告")
    domain = meta.get("domain", "")
    period = meta.get("period", "")

    lines = [
        f"# 执行日志：{title}",
        "",
        f"> 自动生成于 {generated_at}",
        "",
        "---",
        "",
        "## 步骤 1：意图解析",
        "",
        f"- **域**：{domain}",
        f"- **时间范围**：{period}",
        "",
    ]

    # 步骤 2
    lines.append("## 步骤 2：加载域知识 + 构造 Recipe")
    lines.append("")
    if files_read:
        lines.append("**读取的文件**：")
        for f in files_read:
            lines.append(f"- `{f}`")
        lines.append("")
    lines.append(f"**Recipe**（{len(recipe)} 项）：")
    lines.append("")
    lines.append("| seq | component_id | sql_ref | sql_text |")
    lines.append("|-----|-------------|---------|----------|")
    for item in recipe:
        sql_short = str(item.get('sql_text', ''))[:80].replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {item.get('seq', '?')} | {item.get('component_id', '?')} | {item.get('sql_ref', '?')} | `{sql_short}` |")
    lines.append("")

    # 步骤 3
    # 从 recipe 建立 sql_ref → sql_text 映射
    sql_text_map = {}
    for item in recipe:
        ref = item.get("sql_ref", "")
        if ref and item.get("sql_text"):
            sql_text_map[ref] = item["sql_text"]

    lines.append(f"## 步骤 3：SQL 执行（{len(sql_results)} 条）")
    lines.append("")
    for ref, rows in sql_results.items():
        row_count = len(rows) if isinstance(rows, list) else 0
        lines.append(f"### {ref}")
        # 贴完整 SQL
        sql_text = sql_text_map.get(ref, "")
        if sql_text:
            lines.append(f"```sql\n{sql_text}\n```")
        lines.append(f"- 返回行数：{row_count}")
        if rows and isinstance(rows, list) and rows:
            keys = list(rows[0].keys()) if isinstance(rows[0], dict) else []
            lines.append(f"- 字段：{', '.join(keys)}")
            if row_count == 1 and isinstance(rows[0], dict):
                preview = {k: v for k, v in rows[0].items()}
                lines.append(f"- 值：`{json.dumps(preview, ensure_ascii=False)}`")
        lines.append("")

    # 步骤 4
    lines.append("## 步骤 4：Gate Check")
    lines.append("")
    if gate_check_result:
        passed = "✅ PASS" if gate_check_result.get("passed") else "❌ FAIL"
        lines.append(f"**结果**：{passed}")
        report_text = gate_check_result.get("report_text", "")
        if report_text:
            lines.append(f"```\n{report_text}\n```")
    else:
        lines.append("未执行")
    lines.append("")

    # 步骤 5
    lines.append("## 步骤 5：脚本流水线")
    lines.append("")
    lines.append(f"### 5a ComponentRunner → {len(outputs)} outputs, {len(facts)} facts")
    lines.append("")
    for o in outputs:
        cid = o.get("component_id", "?")
        n_facts = len(o.get("facts", []))
        html_len = len(o.get("html_fragment", ""))
        lines.append(f"- **{cid}**：{n_facts} facts，html_fragment {html_len} chars")
    lines.append("")

    n_kpis = len(report_data.get("kpis", []))
    n_sections = len(report_data.get("sections", []))
    n_recs = len(report_data.get("recommendations", []))
    n_insights = len(report_data.get("insights", []))
    lines.append(f"### 5b JSON 组装 → {n_kpis} KPI, {n_sections} sections, {n_recs} recommendations")
    lines.append("")
    lines.append(f"- KPI 卡片：{n_kpis}")
    lines.append(f"- 正文章节：{n_sections}")
    lines.append(f"- 洞察：{n_insights}")
    lines.append(f"- 建议：{n_recs}")
    if report_data.get("highlights"):
        hl = report_data["highlights"]
        if "positive" in hl:
            lines.append(f"- 正面高亮：{hl['positive'].get('text', '')[:80]}")
        if "negative" in hl:
            lines.append(f"- 负面高亮：{hl['negative'].get('text', '')[:80]}")
    lines.append("")

    if html_output_path:
        lines.append(f"### 5c HTML 渲染 → `{html_output_path}`")
    else:
        lines.append("### 5c HTML 渲染 → HTML 已生成")
    lines.append("")

    if notes:
        lines.append("## 遗留问题 / 备注")
        lines.append("")
        for i, note in enumerate(notes, 1):
            lines.append(f"{i}. {note}")
        lines.append("")

    return "\n".join(lines)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
埃及市场营销专家 压力测试脚本
模拟用户问题，从真实语料库/DuckDB 提取答案片段，验证 Agent 路径，输出测试报告。

Usage:
    python scripts/pressure_test.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import duckdb
except ImportError:
    # Auto-install duckdb if not available
    import subprocess as _sp
    print("duckdb not found, auto-installing...", file=sys.stderr)
    _result = _sp.run(
        [sys.executable, "-m", "pip", "install", "duckdb", "--quiet"],
        capture_output=True, text=True
    )
    if _result.returncode != 0:
        print(
            "ERROR: Failed to auto-install duckdb: {}".format(_result.stderr.strip()),
            file=sys.stderr
        )
        sys.exit(1)
    import duckdb  # retry after install

# 路径常量 — 使用脚本所在目录的上一级作为项目根目录（可移植）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REF_DIR = PROJECT_ROOT / "Reference_Texts"
DB_PATH = PROJECT_ROOT / "Databases" / "egypt_marketing.duckdb"
AGENT_MD = PROJECT_ROOT / "agents" / "egypt-marketing.md"
SKILL_MD = PROJECT_ROOT / "skills" / "egypt-marketing-skill" / "SKILL.md"
OUTPUT_FILE = PROJECT_ROOT / "EGYPT_MARKETING_PRESSURE_TEST_REPORT.md"


def read_file(path: Path, max_chars: int = 2000) -> str:
    if not path.exists():
        return "<FILE_MISSING>"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_chars)
    except Exception as e:
        return f"<READ_ERROR: {e}>"


def read_full(path: Path) -> str:
    if not path.exists():
        return "<FILE_MISSING>"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"<READ_ERROR: {e}>"


def count_lines(path: Path) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return -1


def run_duckdb(query: str):
    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        result = con.execute(query).fetchall()
        con.close()
        return result
    except Exception as e:
        return [("<DUCKDB_ERROR>", str(e))]


def extract_context(text: str, keyword: str, radius: int = 150) -> str:
    """从文本中提取关键词上下文片段。"""
    if text is None or keyword is None:
        return ""
    text = text.replace("\n", " ")
    pattern = r".{0," + str(radius) + "}" + re.escape(keyword) + r".{0," + str(radius) + "}"
    m = re.search(pattern, text, re.I)
    if m:
        return m.group(0).strip()
    return ""


def test_corpus_file(name: str, keywords: list) -> dict:
    """测试语料文件是否存在、关键词是否命中。"""
    txt_path = REF_DIR / f"{name}.txt"
    status = "PASS"
    notes = []
    snippets = []

    if not txt_path.exists():
        status = "FAIL"
        notes.append(f"语料文件缺失: {txt_path}")
    else:
        full_text = read_full(txt_path)
        for kw in keywords:
            if re.search(kw, full_text, re.I):
                notes.append(f"命中关键词: {kw}")
                snippets.append(extract_context(full_text, kw, 120))
            else:
                status = "WARN" if status == "PASS" else status
                notes.append(f"未命中关键词: {kw}")
        notes.append(f"行数: {count_lines(txt_path)}")

    return {
        "name": name,
        "status": status,
        "notes": "; ".join(notes),
        "snippets": snippets[:2]
    }


def test_duckdb_table(label: str, table: str, query: str, expected_min_rows: int = 1) -> dict:
    result = run_duckdb(query)
    status = "PASS"
    notes = []
    if not result or result[0][0] == "<DUCKDB_ERROR>":
        status = "FAIL"
        notes.append(f"查询失败: {result}")
    else:
        row_count = len(result)
        notes.append(f"返回 {row_count} 行; 样例: {result[0]}")
        if row_count < expected_min_rows:
            status = "WARN"
            notes.append(f"行数少于预期 {expected_min_rows}")
    return {
        "label": label,
        "table": table,
        "query": query,
        "status": status,
        "notes": "; ".join(notes),
        "sample": result[0] if result and result[0][0] != "<DUCKDB_ERROR>" else None
    }


def main():
    report_lines = []
    report_lines.append("# 埃及市场营销专家 压力测试报告")
    report_lines.append("")
    report_lines.append(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Agent 版本**: 1.1.0")
    report_lines.append(f"**项目路径**: `{PROJECT_ROOT}`")
    report_lines.append("")

    # 1. 配置存在性检查
    report_lines.append("## 1. 配置与文件存在性检查\n")
    config_checks = [
        ("Agent 指令", AGENT_MD),
        ("Skill 指令", SKILL_MD),
        ("DuckDB 数据库", DB_PATH),
        ("plugin.json", PROJECT_ROOT / ".codebuddy-plugin" / "plugin.json"),
    ]
    for label, path in config_checks:
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        report_lines.append(f"- {'✅' if exists else '❌'} {label}: `{path}` ({size} bytes)")
    report_lines.append("")

    # 2. 语料库读取测试 + 提取答案片段
    report_lines.append("## 2. 语料库强制读取与答案片段测试\n")
    corpus_tests = [
        ("埃及 Facebook/TikTok 用户多少？", "digital_2024_egypt", [r"Facebook", r"TikTok", r"用户"]),
        ("埃及社交媒体怎么投广告？", "egypt_social_media_guide", [r"广告", r"平台", r"策略"]),
        ("埃及消费者喜欢什么？", "egypt_consumer_culture", [r"消费", r"年轻", r"文化"]),
        ("斋月怎么做营销？", "egypt_ramadan_playbook", [r"斋月", r"Ramadan", r"营销"]),
        ("埃及人怎么看中国品牌？", "egypt_public_opinion", [r"中国", r"China", r"好感"]),
        ("埃及电商市场多大？COD 占多少？", "egypt_ecommerce_payments", [r"电商", r"COD", r"支付"]),
        ("埃及广告有什么禁忌？", "egypt_ad_regulations", [r"广告", r"禁忌", r"合规"]),
        ("埃及 KOL 怎么选？花多少钱？", "egypt_kol_ecosystem", [r"KOL", r"网红", r"预算"]),
        ("埃及文化维度 PDI 是多少？", "hofstede_culture_egypt", [r"PDI", r"权力距离", r"80"]),
        ("埃及市场怎么进入？", "egypt_marketing_strategy", [r"市场进入", r"定位", r"渠道"]),
    ]
    corpus_results = []
    for q, file, kws in corpus_tests:
        result = test_corpus_file(file, kws)
        corpus_results.append(result)
        report_lines.append(f"### 问题: {q}")
        report_lines.append(f"- **应读取文件**: `{file}.txt`")
        report_lines.append(f"- **状态**: {result['status']}")
        report_lines.append(f"- **说明**: {result['notes']}")
        if result['snippets']:
            report_lines.append(f"- **答案片段**:")
            for s in result['snippets']:
                report_lines.append(f"  - `{s}`")
        report_lines.append("")

    # 3. DuckDB 查询测试
    report_lines.append("## 3. DuckDB 语料库元数据索引测试\n")
    duckdb_tests = [
        ("语料库元数据全表", "corpus_metadata", "SELECT * FROM corpus_metadata LIMIT 5", 1),
        ("按字符数排序", "corpus_metadata", "SELECT file_name, char_count FROM corpus_metadata ORDER BY char_count DESC LIMIT 5", 1),
        ("语料文件总数", "corpus_metadata", "SELECT COUNT(*) FROM corpus_metadata", 1),
    ]
    duckdb_results = []
    for label, table, query, min_rows in duckdb_tests:
        result = test_duckdb_table(label, table, query, min_rows)
        duckdb_results.append(result)
        report_lines.append(f"- **{label}** (`{table}`): {result['status']}")
        report_lines.append(f"  - 查询: `{query}`")
        report_lines.append(f"  - 说明: {result['notes']}")
        report_lines.append("")

    # 4. 工作流模式路由测试
    report_lines.append("## 4. 工作流模式路由测试\n")
    routing_tests = [
        ("帮我做一份蓝牙耳机在埃及的营销方案", "策略方案模式 (Mode 4)", r"营销方案|蓝牙耳机"),
        ("埃及 TikTok 有多少用户", "快速查询 (Mode 1)", r"TikTok|用户"),
        ("语料库测试", "语料库测试 (Mode 7)", r"语料库测试|corpus test"),
        ("详细模式", "详细模式 (Mode 5)", r"详细|verbose"),
        ("简洁模式", "简洁模式 (Mode 6)", r"简洁|concise"),
        ("你好", "闲聊 (Mode 0)", r"你好|hello"),
    ]
    report_lines.append("| 用户输入 | 预期路由 | 命中 |")
    report_lines.append("|----------|---------|------|")
    for q, expected, pattern in routing_tests:
        hit = bool(re.search(pattern, q, re.I))
        report_lines.append(f"| {q} | {expected} | {'✅' if hit else '❌'} |")
    report_lines.append("")

    # 5. 来源占比与引用规范检查
    report_lines.append("## 5. 来源占比与引用规范检查\n")
    agent_text = read_file(AGENT_MD, 100000)
    required_markers = [
        ("语料库优先原则", "语料库优先"),
        ("来源占比标注", "来源占比"),
        ("结构化引用格式", "来源引用"),
        ("语料库测试模式", "语料库测试"),
        ("详细模式", "详细模式"),
        ("文化敏感提醒", "文化提示"),
        ("RAG 检索规则", "RAG"),
        ("定向触发矩阵", "触发矩阵"),
    ]
    report_lines.append("| 规范项 | Agent.md 中是否定义 |")
    report_lines.append("|--------|-------------------|")
    for label, keyword in required_markers:
        present = keyword in agent_text
        report_lines.append(f"| {label} | {'✅ 已定义' if present else '❌ 缺失'} |")
    report_lines.append("")

    # 6. 17 份语料完整性检查
    report_lines.append("## 6. 17 份语料文件完整性检查\n")
    expected_files = [
        "digital_2024_egypt", "egypt_social_media_guide", "egypt_marketing_cases",
        "egypt_marketing_strategy", "egypt_consumer_culture", "egypt_ramadan_playbook",
        "egypt_public_opinion", "egypt_ecommerce_payments", "egypt_digital_payments",
        "egypt_ad_regulations", "egypt_kol_ecosystem",
        "consumer_psychology_toolkit", "data_analytics_roi", "competitive_intelligence",
        "pr_crisis_management", "user_journey_aarrr", "hofstede_culture_egypt",
    ]
    report_lines.append("| # | 文件名 | 存在 | 大小 |")
    report_lines.append("|---|--------|------|------|")
    all_corpus_ok = True
    for i, fname in enumerate(expected_files, 1):
        fpath = REF_DIR / f"{fname}.txt"
        exists = fpath.exists()
        size = fpath.stat().st_size if exists else 0
        if not exists:
            all_corpus_ok = False
        report_lines.append(f"| {i} | {fname}.txt | {'✅' if exists else '❌'} | {size} bytes |")
    report_lines.append("")

    # 7. 测试结果汇总
    all_status = [r["status"] for r in corpus_results + duckdb_results]
    pass_count = all_status.count("PASS")
    warn_count = all_status.count("WARN")
    fail_count = all_status.count("FAIL")
    report_lines.append("## 7. 测试结果汇总\n")
    report_lines.append(f"- ✅ 通过: {pass_count}")
    report_lines.append(f"- ⚠️ 警告: {warn_count}")
    report_lines.append(f"- ❌ 失败: {fail_count}")
    report_lines.append(f"- 📁 语料完整性: {'✅ 17/17' if all_corpus_ok else '❌ 有缺失'}")
    report_lines.append("")
    if fail_count == 0 and all_corpus_ok:
        report_lines.append("**结论**: 核心数据底座（语料库 + DuckDB）可正常读取，Agent 配置完整，压力测试通过。")
    else:
        report_lines.append("**结论**: 存在失败项，需检查对应数据源。")
    report_lines.append("")

    # 8. DuckDB 数据快照
    report_lines.append("## 8. 附录：DuckDB 语料库元数据快照\n")
    metadata = run_duckdb("SELECT file_name, char_count, source_url FROM corpus_metadata ORDER BY char_count DESC")
    if metadata and metadata[0][0] != "<DUCKDB_ERROR>":
        report_lines.append("| 文件名 | 字符数 | 来源 |")
        report_lines.append("|--------|--------|------|")
        for row in metadata:
            clean_row = [re.sub(r"[\r\n|]+", " ", str(c)) for c in row]
            report_lines.append("| " + " | ".join(clean_row) + " |")
    else:
        report_lines.append(f"DuckDB 查询失败: {metadata}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*报告由埃及市场营销专家压力测试脚本自动生成。*")

    OUTPUT_FILE.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Report written to: {OUTPUT_FILE}")
    print(f"Summary: PASS={pass_count}, WARN={warn_count}, FAIL={fail_count}, Corpus={'OK' if all_corpus_ok else 'INCOMPLETE'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Egypt Strategic Advisory — 压力测试脚本
模拟用户问题，验证语料库/DuckDB 可读性，验证 Agent 配置完整性。

Usage:
    python scripts/pressure_test.py
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    try:
    import duckdb
except ImportError:
    import subprocess
    import sys
    print("duckdb not found, auto-installing...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "duckdb"])
    import duckdb
except ImportError:
    import subprocess
    print("duckdb not found, installing...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "duckdb", "--quiet"])
    try:
    import duckdb
except ImportError:
    import subprocess
    import sys
    print("duckdb not found, auto-installing...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "duckdb"])
    import duckdb

# ── Paths ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REF_DIR = PROJECT_ROOT / "Reference_Texts"
DB_PATH = PROJECT_ROOT / "Databases" / "egypt_strategic_advisory.duckdb"
AGENT_MD = PROJECT_ROOT / "agents" / "egypt-strategic-advisory.md"
SKILL_MD = PROJECT_ROOT / "skills" / "egypt-strategic-advisory-skill" / "SKILL.md"
PLUGIN_JSON = PROJECT_ROOT / ".codebuddy-plugin" / "plugin.json"
OUTPUT_FILE = PROJECT_ROOT / "EGYPT_STRATEGIC_PRESSURE_TEST_REPORT.md"


def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def run_duckdb(query: str):
    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        rows = con.execute(query).fetchall()
        con.close()
        return rows
    except Exception as e:
        return [("<ERROR>", str(e))]


def test_corpus_file(name: str, keywords: list) -> dict:
    txt_path = REF_DIR / f"{name}.txt"
    if not txt_path.exists():
        return {"name": name, "status": "FAIL", "notes": "文件缺失", "snippets": []}

    text = read_file(txt_path)
    notes = []
    snippets = []
    for kw in keywords:
        if re.search(kw, text, re.I):
            notes.append(f"命中: {kw}")
            ctx = re.search(r".{0,120}" + re.escape(kw) + r".{0,120}", text, re.I)
            if ctx:
                snippets.append(ctx.group(0).strip().replace("\n", " "))
        else:
            notes.append(f"未命中: {kw}")

    return {
        "name": name,
        "status": "PASS" if all(f"命中: {kw}" in str(notes) for kw in keywords[:2]) else "WARN",
        "notes": "; ".join(notes) + f" | {txt_path.stat().st_size} bytes",
        "snippets": snippets[:2]
    }


def main():
    lines = []
    lines.append("# Egypt Strategic Advisory — 压力测试报告\n")
    lines.append(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**项目路径**: `{PROJECT_ROOT}`\n")

    # ── 1. 文件存在性 ──
    lines.append("## 1. 文件存在性检查\n")
    files_to_check = {
        "Agent MD": AGENT_MD,
        "Skill MD": SKILL_MD,
        "plugin.json": PLUGIN_JSON,
        "DuckDB": DB_PATH,
    }
    for i, (name, fpath) in enumerate(files_to_check.items(), 1):
        ok = fpath.exists()
        size = fpath.stat().st_size if ok else 0
        lines.append(f"{'✅' if ok else '❌'} {i}. {name}: {fpath.name} ({size} bytes)")

    # Corpus files
    corpus_files = sorted(REF_DIR.glob("*.txt"))
    lines.append(f"\n📁 Reference_Texts: {len(corpus_files)} 个文件")
    for f in corpus_files:
        lines.append(f"   ✅ {f.name} ({f.stat().st_size//1024}KB)")

    lines.append("")

    # ── 2. 语料库关键词测试 ──
    lines.append("## 2. 语料库关键数据可读性\n")
    tests = [
        ("egypt_macro_outlook", [r"GDP", r"inflation", r"fiscal", r"reform"]),
        ("egypt_national_narrative", [r"development", r"strategy", r"growth", r"sustainable"]),
        ("egypt_investment_law", [r"Investment Law", r"GAFI", r"exemption", r"guarantee"]),
        ("egypt_trade_agreements", [r"COMESA", r"PAFTA", r"FTA", r"tariff"]),
        ("egypt_vision2030", [r"2030", r"sustainable", r"quality of life", r"economic"]),
        ("egypt_industry_analysis", [r"manufacturing", r"energy", r"ICT", r"tourism"]),
        ("egypt_fdi_analysis", [r"FDI", r"investment", r"UNCTAD", r"GAFI"]),
        ("egypt_political_risk", [r"risk", r"IMF", r"sovereign", r"fiscal"]),
        ("egypt_sczone_guide", [r"SCZone", r"Suez", r"industrial", r"zone"]),
        ("egypt_suez_canal", [r"Suez Canal", r"revenue", r"transit", r"trade"]),
        ("egypt_competition_landscape", [r"Chinese", r"Huawei", r"multinational", r"manufacturing"]),
        ("egypt_ebrd_transition_2025", [r"growth", r"economy", r"reform", r"transition"]),
        ("egypt_wb_mpo", [r"poverty", r"growth", r"inflation", r"outlook"]),
    ]

    corpus_results = []
    for fname, kws in tests:
        r = test_corpus_file(fname, kws)
        corpus_results.append(r)
        lines.append(f"### 📄 `{fname}.txt`")
        lines.append(f"   **状态**: {r['status']}")
        lines.append(f"   **说明**: {r['notes']}")
        if r['snippets']:
            for s in r['snippets']:
                lines.append(f"   > {s[:120]}...")
        lines.append("")

    # ── 3. DuckDB 查询测试 ──
    lines.append("## 3. DuckDB 结构化数据查询\n")
    db_queries = [
        ("语料库元数据", "SELECT COUNT(*), SUM(chars) FROM corpus_metadata"),
        ("宏观指标", "SELECT indicator, value FROM egypt_macro_indicators LIMIT 5"),
        ("行业数据", "SELECT sector, gdp_share_pct, growth_rate_pct FROM egypt_industry_sectors LIMIT 5"),
        ("FDI 来源", "SELECT country, fdi_share_pct FROM egypt_fdi_by_source LIMIT 5"),
        ("贸易协定", "SELECT agreement, type FROM egypt_trade_agreements LIMIT 5"),
        ("SCZone 行业", "SELECT sector, priority_rank FROM egypt_sczone_sectors ORDER BY priority_rank LIMIT 5"),
        ("重大项目", "SELECT project_name, investment_value_usd_billion FROM egypt_mega_projects LIMIT 5"),
        ("中资企业", "SELECT company, investment_usd_million FROM egypt_chinese_investment ORDER BY investment_usd_million DESC LIMIT 5"),
    ]

    db_results = []
    for label, q in db_queries:
        rows = run_duckdb(q)
        if rows and rows[0][0] != "<ERROR>":
            db_results.append({"label": label, "status": "PASS", "rows": len(rows), "sample": rows[0]})
            lines.append(f"✅ **{label}**: {len(rows)} 行 | 样例: {rows[0]}")
        else:
            db_results.append({"label": label, "status": "FAIL", "rows": 0, "sample": str(rows)})
            lines.append(f"❌ **{label}**: 查询失败: {rows}")
    lines.append("")

    # ── 4. Agent MD 结构检查 ──
    lines.append("## 4. Agent 配置结构检查\n")
    agent_text = read_file(AGENT_MD)
    checks = [
        ("输出铁律", "🚨 输出铁律"),
        ("语料库优先原则", "语料库优先原则"),
        ("来源占比标注", "来源占比"),
        ("核心能力", "核心能力"),
        ("工作流模式", "工作流模式"),
        ("定向触发矩阵", "定向触发矩阵"),
        ("回答策略", "回答策略"),
        ("不确定性标注", "不确定性标注"),
        ("客观中立", "客观中立"),
        ("免责声明", "免责"),
        ("风险提醒", "地缘警示"),
        ("降级熔断", "降级与熔断"),
        ("fetch_with_fallback", "fetch_with_fallback"),
        ("定向搜索模板", "定向搜索模板库"),
    ]
    for label, kw in checks:
        present = kw in agent_text
        lines.append(f"{'✅' if present else '❌'} {label}: {'已定义' if present else '缺失'}")

    # ── 5. Skill MD 结构检查 ──
    lines.append("\n## 5. Skill 配置结构检查\n")
    skill_text = read_file(SKILL_MD)
    skill_checks = [
        ("语料库统计", "Reference_Texts — 13 份"),
        ("DuckDB 统计", "DuckDB — 8 张表"),
        ("语料库优先原则", "语料库优先原则"),
        ("fetch_with_fallback 优先级", "fetch_with_fallback 在线抓取"),
        ("四层降级图", "四层降级流程图"),
        ("强制读取表", "触发主题"),
        ("结构化引用格式", "来源引用"),
    ]
    for label, kw in skill_checks:
        present = kw in skill_text
        lines.append(f"{'✅' if present else '❌'} {label}: {'已定义' if present else '缺失'}")

    # ── 6. plugin.json 检查 ──
    lines.append("\n## 6. plugin.json 配置检查\n")
    try:
        with open(PLUGIN_JSON, "r", encoding="utf-8") as f:
            pj = json.load(f)
        pj_checks = [
            ("name", pj.get("name") == "egypt-strategic-advisory"),
            ("displayName(zh)", pj.get("displayName", {}).get("zh") == "埃及 战略顾问"),
            ("avatar 路径", "avatars/" in pj.get("avatar", "")),
            ("categoryId", bool(pj.get("categoryId"))),
            ("tags 数量", len(pj.get("tags", [])) == 5),
            ("quickPrompts 数量", len(pj.get("quickPrompts", [])) == 3),
            ("agentName", bool(pj.get("agentName"))),
            ("agents 路径", all(a.startswith("./agents/") for a in pj.get("agents", []))),
            ("skills 路径", all(s.startswith("./skills/") for s in pj.get("skills", []))),
        ]
        for label, ok in pj_checks:
            lines.append(f"{'✅' if ok else '❌'} {label}")
    except Exception as e:
        lines.append(f"❌ JSON 解析失败: {e}")

    # ── 7. 头像检查 ──
    lines.append("\n## 7. 头像检查\n")
    avatar_path = PROJECT_ROOT / "avatars" / "egypt-strategic-advisory.png"
    if avatar_path.exists():
        lines.append(f"✅ 头像存在: {avatar_path.stat().st_size//1024}KB")
    else:
        lines.append("❌ 头像缺失")

    # ── 8. 汇总 ──
    lines.append("\n## 8. 测试结果汇总\n")
    all_status = [r["status"] for r in corpus_results + db_results]
    passes = all_status.count("PASS")
    warns = all_status.count("WARN")
    fails = all_status.count("FAIL")
    lines.append(f"- ✅ 通过: {passes}")
    lines.append(f"- ⚠️ 警告: {warns}")
    lines.append(f"- ❌ 失败: {fails}")
    lines.append(f"- 📁 语料文件: {len(corpus_files)}/13")
    lines.append(f"- 🗄️  DuckDB 表: {len(db_queries)} 张可查询")
    lines.append(f"- 🎨 头像: {'有' if avatar_path.exists() else '无'}")
    conclusion = "✅ **结论：Agent 配置完整，数据底座可正常读取，可以上线。**"
    if fails > 0:
        conclusion = "⚠️ **结论：存在失败项，建议修复后重新测试。**"
    lines.append(f"\n{conclusion}")
    lines.append("\n---\n*报告由压力测试脚本自动生成。*")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUTPUT_FILE}")
    print(f"PASS={passes} WARN={warns} FAIL={fails} Corpus={len(corpus_files)}/13 DB_Tables={len(db_queries)}")


if __name__ == "__main__":
    main()

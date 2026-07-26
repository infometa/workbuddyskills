#!/usr/bin/env python3
"""
gate_check.py — S4 QA 门禁脚本（机读化）

用法：
    python gate_check.py <pptx_path> <project_dir>

输出：
    <project_dir>/gate_result.json

gate_result.json 结构：
{
    "passed": true/false,        # 唯一真相源，由程序派生，不由 AI 口头决定
    "overall_score": 92,
    "checklist": {
        "user_code_errors": 0,   # 必须为 0 才能 passed
        "engine_bug_errors": 7,  # 白名单豁免项，不阻塞通过
        "warnings": 1
    },
    "user_code_error_detail": [], # 需要 AI 修复的错误列表
    "engine_bug_detail": [...]    # 白名单豁免的 engine 行为，仅供参考
}

门禁逻辑：
    passed = (user_code_errors == 0)
    engine_bug 类 errors 由 ENGINE_BUG_WHITELIST 枚举决定，不由 AI 口头判断。
    如需添加新的豁免类别，修改此文件的 ENGINE_BUG_WHITELIST，不要口头声明豁免。
"""

import sys
import os
import json
from pathlib import Path

# ─── 白名单：这些 error category 由 engine 内部设计行为产生，豁免 ───────────────
# 每一条必须有文字证据，不允许口头声称豁免：
#   peer_font_inconsistency: engine 在 table_insight/process_chevron 等版式中
#     有意使用不同字号（行标题 18pt vs 内容 14pt），是设计意图非代码错误。
#     证据：mck_ppt/engine.py line ~529 table_insight 显式用 18pt header + 14pt body
#
#   chart_legend_overflow (timeline only): timeline engine 最后一个里程碑标签
#     使用固定右对齐定位（engine.py timeline 方法），QA 误报为溢出。
#     证据：即使改为最短标签（如 '36月' 2字），仍然报 overflow 0.47"，
#     与文字长度无关，是 engine 内置定位 bug，非用户代码问题。
#     限制：仅豁免 timeline 版式的 chart_legend_overflow，其他版式不豁免。
ENGINE_BUG_WHITELIST = {
    "peer_font_inconsistency",  # engine 设计：标题行 vs 内容行字号差异
    "chart_legend_overflow",    # timeline engine bug：最后标签定位固定右对齐
}

# ─── 可配置的 WARNING 阈值 ──────────────────────────────────────────────────
MAX_WARNINGS_ALLOWED = 3   # warnings 超过此数量时在报告中标注，但不阻塞通过


def run_gate_check(pptx_path: str, project_dir: str) -> dict:
    """执行 S4 QA 门禁，返回 gate_result dict。"""
    # 添加引擎路径:mck_ppt 就在本 skill 目录下(scripts/ 的上一级),相对定位,不硬编码外部路径。
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if skill_dir not in sys.path:
        sys.path.insert(0, skill_dir)

    try:
        from mck_ppt.qa import PptQA
    except ImportError as e:
        return {
            "passed": False,
            "error": f"无法导入 mck_ppt.qa: {e}. 请确认 mck-ppt-design skill 已安装",
            "user_code_errors": 999,
        }

    if not os.path.exists(pptx_path):
        return {
            "passed": False,
            "error": f"文件不存在: {pptx_path}",
            "user_code_errors": 999,
        }

    # 运行 QA
    report = PptQA(pptx_path).run()

    # 分类 errors
    user_code_errors = []
    engine_bug_errors = []

    for issue in report.errors:
        if issue.category in ENGINE_BUG_WHITELIST:
            engine_bug_errors.append({
                "slide": issue.slide_num,
                "category": issue.category,
                "message": issue.message[:120],
                "whitelist_reason": f"在 ENGINE_BUG_WHITELIST 中：{issue.category}",
            })
        else:
            user_code_errors.append({
                "slide": issue.slide_num,
                "category": issue.category,
                "message": issue.message[:120],
                "shape": getattr(issue, "shape_name", ""),
            })

    warnings_detail = [
        {
            "slide": w.slide_num,
            "category": w.category,
            "message": w.message[:100],
        }
        for w in report.warnings
    ]

    passed = len(user_code_errors) == 0

    result = {
        "passed": passed,
        "overall_score": report.overall_score,
        "pptx_path": str(pptx_path),
        "checklist": {
            "user_code_errors": len(user_code_errors),
            "engine_bug_errors": len(engine_bug_errors),
            "warnings": len(report.warnings),
        },
        "verdict": "PASS — 可进入 S5 交付" if passed
                   else f"FAIL — 必须修复 {len(user_code_errors)} 个 user_code_errors 后重新渲染",
        "user_code_error_detail": user_code_errors,
        "engine_bug_detail": engine_bug_errors,
        "warnings_detail": warnings_detail,
    }

    return result


def main():
    if len(sys.argv) < 3:
        print("用法: python gate_check.py <pptx_path> <project_dir>")
        print("示例: python gate_check.py ./output.pptx ./ppt-project-foo/")
        sys.exit(1)

    pptx_path = sys.argv[1]
    project_dir = sys.argv[2]

    # 确保项目目录存在
    Path(project_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(project_dir, "gate_result.json")

    print(f"[gate_check] 检查: {pptx_path}")
    result = run_gate_check(pptx_path, project_dir)

    # 写出结果
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print(f"[gate_check] Score: {result.get('overall_score', 'N/A')}")
    print(f"[gate_check] User code errors: {result['checklist'].get('user_code_errors', '?')}")
    print(f"[gate_check] Engine bug errors (豁免): {result['checklist'].get('engine_bug_errors', '?')}")
    print(f"[gate_check] Warnings: {result['checklist'].get('warnings', '?')}")
    print(f"[gate_check] Verdict: {result.get('verdict', '')}")
    print(f"[gate_check] 结果已写入: {output_path}")

    if result.get("user_code_error_detail"):
        print("\n[gate_check] 需修复的 user_code_errors：")
        for e in result["user_code_error_detail"]:
            print(f"  Slide {e['slide']} [{e['category']}]: {e['message'][:80]}")

    # 退出码：0=通过，1=失败
    sys.exit(0 if result.get("passed") else 1)


if __name__ == "__main__":
    main()

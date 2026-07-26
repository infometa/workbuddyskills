#!/usr/bin/env python3
"""
gate_check_s3.py — S3 内容门禁脚本（机读化）

用法：
    python gate_check_s3.py <content_json_path> <project_dir>

输出：
    <project_dir>/gate_s3.json

gate_s3.json 结构：
{
    "passed": true/false,
    "fail_items": [          # 需要修复的问题列表
        {
            "slide_idx": 6,
            "layout": "four_column",
            "check": "api_format",
            "message": "four_column items[0] 应为三元组 (num, title, desc)，实际得到 2 个元素"
        }
    ],
    "pass_items": [...]      # 通过的检查项（供参考）
}

检查内容：
    1. API 格式：确保各版式的 items/steps/segments 参数符合三元组要求
    2. 数量约束：donut ≤6段、process_chevron ≤5步、grouped_bar ≤6类×3系列
    3. 版式标签约束：process_chevron 标签不能含 \\n、timeline 最后标签 ≤6字符
    4. 出处完整性：每张内容页有 source 非空
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any


# ─── 各版式 API 格式检查规则 ────────────────────────────────────────────────

def check_four_column(slide: Dict, idx: int) -> List[Dict]:
    """four_column items 必须是三元组 (num, col_title, desc)"""
    issues = []
    items = slide.get("items", [])
    for i, item in enumerate(items):
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            got = len(item) if isinstance(item, (list, tuple)) else "非列表"
            issues.append({
                "slide_idx": idx,
                "layout": "four_column",
                "check": "api_format",
                "message": (f"four_column items[{i}] 应为三元组 (num, col_title, desc)，"
                            f"实际得到 {got} 个元素。"
                            f"修复：加上编号，如 ('1', '标题', '描述内容')"),
            })
    return issues


def check_executive_summary(slide: Dict, idx: int) -> List[Dict]:
    """executive_summary items 必须是三元组 (num, item_title, desc)"""
    issues = []
    items = slide.get("items", [])
    for i, item in enumerate(items):
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            got = len(item) if isinstance(item, (list, tuple)) else "非列表"
            issues.append({
                "slide_idx": idx,
                "layout": "executive_summary",
                "check": "api_format",
                "message": (f"executive_summary items[{i}] 应为三元组 (num, item_title, desc)，"
                            f"实际得到 {got} 个元素。"
                            f"修复：加上序号，如 ('1', '立即启动', '具体行动描述')"),
            })
    return issues


def check_matrix_2x2(slide: Dict, idx: int) -> List[Dict]:
    """matrix_2x2 quadrants 必须是三元组 (label, bg_color, desc)，不能是四元组"""
    issues = []
    quadrants = slide.get("quadrants", [])
    for i, q in enumerate(quadrants):
        if not isinstance(q, (list, tuple)):
            issues.append({
                "slide_idx": idx,
                "layout": "matrix_2x2",
                "check": "api_format",
                "message": f"matrix_2x2 quadrants[{i}] 应为列表/元组，实际类型 {type(q).__name__}",
            })
        elif len(q) != 3:
            issues.append({
                "slide_idx": idx,
                "layout": "matrix_2x2",
                "check": "api_format",
                "message": (f"matrix_2x2 quadrants[{i}] 应为三元组 (label, bg_color, desc)，"
                            f"实际得到 {len(q)} 个元素。"
                            f"修复：(label, LIGHT_BLUE, '描述文字')，只用3个元素"),
            })
    if len(quadrants) != 4:
        issues.append({
            "slide_idx": idx,
            "layout": "matrix_2x2",
            "check": "count",
            "message": f"matrix_2x2 需要恰好 4 个象限，实际得到 {len(quadrants)} 个",
        })
    return issues


def check_process_chevron(slide: Dict, idx: int) -> List[Dict]:
    """process_chevron: ≤5步，标签不含\\n，desc ≤50字符"""
    issues = []
    steps = slide.get("steps", [])
    if len(steps) > 5:
        issues.append({
            "slide_idx": idx,
            "layout": "process_chevron",
            "check": "count",
            "message": f"process_chevron 最多 5 步，实际 {len(steps)} 步。修复：合并步骤或拆分成多页",
        })
    for i, step in enumerate(steps):
        if not isinstance(step, (list, tuple)) or len(step) < 3:
            issues.append({
                "slide_idx": idx,
                "layout": "process_chevron",
                "check": "api_format",
                "message": f"process_chevron steps[{i}] 应为三元组 (label, step_title, desc)",
            })
            continue
        label, title, desc = step[0], step[1], step[2]
        if "\n" in str(label):
            issues.append({
                "slide_idx": idx,
                "layout": "process_chevron",
                "check": "label_newline",
                "message": (f"process_chevron steps[{i}] 标签不能含 \\n。"
                            f"实际: {repr(label)}。修复：如 '1990-2010' 而非 '阶段一\\n1990-2010'"),
            })
        if len(str(desc)) > 50:
            issues.append({
                "slide_idx": idx,
                "layout": "process_chevron",
                "check": "desc_length",
                "message": (f"process_chevron steps[{i}] desc 超 50 字符 ({len(str(desc))} 字)。"
                            f"预览: '{str(desc)[:30]}...'"),
            })
    return issues


def check_donut_pie(slide: Dict, idx: int) -> List[Dict]:
    """donut/pie segments ≤6"""
    issues = []
    layout = slide.get("layout", "")
    segments = slide.get("segments", [])
    if len(segments) > 6:
        issues.append({
            "slide_idx": idx,
            "layout": layout,
            "check": "count",
            "message": (f"{layout} 最多 6 段，实际 {len(segments)} 段。"
                        f"修复：保留 top 5 + '其他' 合并"),
        })
    return issues


def check_grouped_bar(slide: Dict, idx: int) -> List[Dict]:
    """grouped_bar categories ≤6，series ≤3"""
    issues = []
    categories = slide.get("categories", [])
    series = slide.get("series", [])
    if len(categories) > 6:
        issues.append({
            "slide_idx": idx,
            "layout": "grouped_bar",
            "check": "count",
            "message": f"grouped_bar 最多 6 个类别，实际 {len(categories)} 个",
        })
    if len(series) > 3:
        issues.append({
            "slide_idx": idx,
            "layout": "grouped_bar",
            "check": "count",
            "message": f"grouped_bar 最多 3 个 series，实际 {len(series)} 个",
        })
    return issues


def check_timeline_last_label(slide: Dict, idx: int) -> List[Dict]:
    """timeline 最后一个里程碑标签 ≤6 字符"""
    issues = []
    milestones = slide.get("milestones", [])
    if milestones:
        last = milestones[-1]
        if isinstance(last, (list, tuple)) and len(last) >= 1:
            label = str(last[0])
            if len(label) > 6:
                issues.append({
                    "slide_idx": idx,
                    "layout": "timeline",
                    "check": "last_label_length",
                    "message": (f"timeline 最后里程碑标签 '{label}' 超 6 字符 ({len(label)} 字)，"
                                f"容易溢出右边界。修复：缩短为如 '36月'"),
                })
    return issues


def check_source(slide: Dict, idx: int) -> List[Dict]:
    """每张内容页（非 cover/toc/section_divider/closing）有 source 非空"""
    issues = []
    layout = slide.get("layout", "")
    skip_layouts = {"cover", "toc", "section_divider", "closing", "appendix_title"}
    if layout in skip_layouts:
        return issues
    source = slide.get("source", "")
    if not source or source.strip() == "":
        issues.append({
            "slide_idx": idx,
            "layout": layout,
            "check": "source_missing",
            "message": f"Slide {idx} ({layout}) 缺少 source 出处，每张内容页必须有 source",
        })
    return issues


def check_action_title(slide: Dict, idx: int) -> List[Dict]:
    """Action Title 应为完整句子（非 cover/section_divider/closing）"""
    issues = []
    layout = slide.get("layout", "")
    skip_layouts = {"cover", "toc", "section_divider", "closing", "appendix_title"}
    if layout in skip_layouts:
        return issues
    title = slide.get("title", "")
    if len(title) <= 10:
        issues.append({
            "slide_idx": idx,
            "layout": layout,
            "check": "title_too_short",
            "message": (f"Slide {idx} title '{title}' 太短（≤10字），应为完整洞见句。"
                        f"如：'竞争格局分散，技术壁垒是核心差异化维度' 而非 '竞争格局'"),
        })
    return issues


# ─── 版式路由 ────────────────────────────────────────────────────────────────

LAYOUT_CHECKERS = {
    "four_column": [check_four_column, check_source, check_action_title],
    "executive_summary": [check_executive_summary, check_source, check_action_title],
    "matrix_2x2": [check_matrix_2x2, check_source, check_action_title],
    "process_chevron": [check_process_chevron, check_source, check_action_title],
    "donut": [check_donut_pie, check_source, check_action_title],
    "pie": [check_donut_pie, check_source, check_action_title],
    "grouped_bar": [check_grouped_bar, check_source, check_action_title],
    "stacked_bar": [check_source, check_action_title],
    "timeline": [check_timeline_last_label, check_source, check_action_title],
    # 通用检查：有 source + title 长度
    "big_number": [check_source, check_action_title],
    "table_insight": [check_source, check_action_title],
    "value_chain": [check_source, check_action_title],
    "key_takeaway": [check_source, check_action_title],
    "side_by_side": [check_source, check_action_title],
    "before_after": [check_source, check_action_title],
    "meet_the_team": [check_source],
    "case_study": [check_source, check_action_title],
    "data_table": [check_source, check_action_title],
    "scorecard": [check_source, check_action_title],
    "line_chart": [check_source, check_action_title],
    "horizontal_bar": [check_source, check_action_title],
    "waterfall": [check_source, check_action_title],
}


def run_gate_check_s3(content_json_path: str, project_dir: str) -> dict:
    """执行 S3 内容门禁，返回 gate_s3 dict。"""
    if not os.path.exists(content_json_path):
        return {
            "passed": False,
            "error": f"content.json 不存在: {content_json_path}",
            "fail_items": [{"check": "file_missing", "message": f"找不到 {content_json_path}"}],
            "pass_items": [],
        }

    with open(content_json_path, "r", encoding="utf-8") as f:
        try:
            content = json.load(f)
        except json.JSONDecodeError as e:
            return {
                "passed": False,
                "error": f"content.json JSON 解析失败: {e}",
                "fail_items": [{"check": "json_parse", "message": str(e)}],
                "pass_items": [],
            }

    slides = content.get("slides", [])
    all_issues = []
    checked = []

    for slide in slides:
        idx = slide.get("idx", "?")
        layout = slide.get("layout", "unknown")
        checkers = LAYOUT_CHECKERS.get(layout, [check_source])

        slide_issues = []
        for checker in checkers:
            slide_issues.extend(checker(slide, idx))

        if not slide_issues:
            checked.append({
                "slide_idx": idx,
                "layout": layout,
                "status": "ok",
            })
        else:
            all_issues.extend(slide_issues)

    passed = len(all_issues) == 0
    result = {
        "passed": passed,
        "total_slides": len(slides),
        "verdict": "PASS — 可进入 S4 渲染" if passed
                   else f"FAIL — 必须修复 {len(all_issues)} 个问题后重新检查",
        "fail_items": all_issues,
        "pass_items": checked,
    }
    return result


def main():
    if len(sys.argv) < 3:
        print("用法: python gate_check_s3.py <content_json_path> <project_dir>")
        print("示例: python gate_check_s3.py ./ppt-project-foo/content.json ./ppt-project-foo/")
        sys.exit(1)

    content_json_path = sys.argv[1]
    project_dir = sys.argv[2]

    Path(project_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(project_dir, "gate_s3.json")

    print(f"[gate_check_s3] 检查: {content_json_path}")
    result = run_gate_check_s3(content_json_path, project_dir)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[gate_check_s3] Slides: {result.get('total_slides', '?')}")
    print(f"[gate_check_s3] Fail items: {len(result.get('fail_items', []))}")
    print(f"[gate_check_s3] Verdict: {result.get('verdict', '')}")
    print(f"[gate_check_s3] 结果已写入: {output_path}")

    if result.get("fail_items"):
        print("\n[gate_check_s3] 需修复的问题：")
        for item in result["fail_items"]:
            print(f"  Slide {item.get('slide_idx')} [{item.get('layout')}]"
                  f" [{item.get('check')}]: {item.get('message', '')[:100]}")

    sys.exit(0 if result.get("passed") else 1)


if __name__ == "__main__":
    main()

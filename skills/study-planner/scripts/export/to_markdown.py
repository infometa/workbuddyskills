#!/usr/bin/env python3
"""
导出为 Markdown 格式（默认导出格式）
用法：
    python3 to_markdown.py [plan_id]
    python3 to_markdown.py --stdout                  # 直接打印不写文件
    python3 to_markdown.py --output-dir ./reports    # 指定报告输出目录
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _base import find_plan, category_of, resolve_output_dir


def render(plan: dict) -> str:
    meta = plan["meta"]
    lines = []
    lines.append(f"# {meta['title']}\n")
    lines.append(f"> {meta['goal']}\n")
    lines.append(f"- 截止：**{meta['deadline']}**")
    lines.append(f"- 当前水平：{meta.get('current_level', '-')}")
    budget = meta.get("daily_budget", {})
    if budget:
        lines.append(f"- 每日预算：工作日 {budget.get('weekday', 0)} 分钟 / 周末 {budget.get('weekend', 0)} 分钟")
    if meta.get("weak_points"):
        lines.append(f"- 薄弱项：{', '.join(meta['weak_points'])}")
    if meta.get("methodology"):
        lines.append(f"- 方法论：{', '.join(meta['methodology'])}")
    lines.append("")

    # 阶段
    lines.append("## 阶段总览\n")
    lines.append("| 阶段 | 名称 | 时长 | 目标 |")
    lines.append("|-----|-----|------|------|")
    for s in plan.get("stages", []):
        goals = "、".join(s.get("goals", []))
        lines.append(f"| {s['id']} | {s['name']} | {s['duration_days']} 天 | {goals} |")
    lines.append("")

    # 每日任务
    lines.append("## 每日任务\n")
    for d in plan.get("daily_tasks", []):
        lines.append(f"### {d['date']}（{d['stage_id']}）\n")
        lines.append("| 任务 | 类别 | 时长 | 资料 |")
        lines.append("|------|-----|------|------|")
        for t in d["tasks"]:
            checkbox = "[ ] " if t.get("checkable", True) else ""
            lines.append(
                f"| {checkbox}{t['title']} | {category_of(t)} | {t['duration_min']} min | {t.get('resource', '-')} |"
            )
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan_id", nargs="?", default=None)
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="报告输出目录（支持 {plan_id} / {cwd} 占位符）；不传则与 plan.json 同目录",
    )
    args = parser.parse_args()

    plan, plan_dir = find_plan(args.plan_id)
    md = render(plan)

    if args.stdout:
        print(md)
    else:
        out_dir = resolve_output_dir(plan_dir, plan.get("id"), args.output_dir)
        out_file = out_dir / "plan.md"
        out_file.write_text(md, encoding="utf-8")
        print(f"[OK] Markdown 已导出: {out_file}")


if __name__ == "__main__":
    main()

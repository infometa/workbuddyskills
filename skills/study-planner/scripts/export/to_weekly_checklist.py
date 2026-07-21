#!/usr/bin/env python3
"""
生成每周任务清单（weekly-checklist.md）

数据来源：plan.json（schema v1.1）
输出：<output_dir>/weekly-checklist.md（默认 output_dir = plan_dir）

用法：
    python3 to_weekly_checklist.py [plan_id]
    python3 to_weekly_checklist.py [plan_id] --output-dir ./reports
    python3 to_weekly_checklist.py --plan-file ./path/to/plan.json --out ./weekly.md  # 兼容老用法

按 plan.daily_tasks 真实 schema：
    daily_tasks[].date         # YYYY-MM-DD
    daily_tasks[].stage_id     # stage-1 / stage-2 ...
    daily_tasks[].tasks[].title / duration_min / category / checkable
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _base import find_plan, category_of, resolve_output_dir  # noqa: E402


WEEKDAY_CN = ["一", "二", "三", "四", "五", "六", "日"]


def _stage_name(plan: dict, stage_id: str) -> str:
    for s in plan.get("stages", []):
        if s.get("id") == stage_id:
            return s.get("name", stage_id)
    return stage_id


def render_weekly(plan: dict) -> str:
    meta = plan.get("meta", {})
    title = meta.get("title", "学习计划")
    goal = meta.get("goal", "")
    deadline = meta.get("deadline", "-")

    daily_tasks = sorted(plan.get("daily_tasks", []), key=lambda d: d.get("date", ""))
    if not daily_tasks:
        return f"# {title} · 每周任务清单\n\n*暂无任务数据*\n"

    start = datetime.strptime(daily_tasks[0]["date"], "%Y-%m-%d")
    end = datetime.strptime(daily_tasks[-1]["date"], "%Y-%m-%d")
    total_days = (end - start).days + 1
    total_weeks = (total_days + 6) // 7

    lines = []
    lines.append(f"# {title} · 每周任务清单\n")
    if goal:
        lines.append(f"> 🎯 {goal}\n")
    lines.append(f"> 计划 ID：`{plan.get('id', '-')}`")
    lines.append(f"> 时间：{start:%Y-%m-%d} ~ {end:%Y-%m-%d}（共 {total_days} 天，{total_weeks} 周）")
    lines.append(f"> 截止：**{deadline}**")
    # P1-1：截止日 vs 计划末日 留白说明
    cal = (meta.get("_calendar_note") or {})
    if cal.get("tip"):
        lines.append(f"> 📅 {cal['tip']}")
    lines.append("")
    lines.append("---\n")

    by_date = {d["date"]: d for d in daily_tasks}

    for week_num in range(1, total_weeks + 1):
        ws = start + timedelta(days=(week_num - 1) * 7)
        we = min(ws + timedelta(days=6), end)
        lines.append(f"## 📅 第 {week_num} 周（{ws:%Y-%m-%d} ~ {we:%Y-%m-%d}）\n")

        # 每日任务表
        lines.append("| 日期 | 星期 | 阶段 | 今日任务 | 时长 |")
        lines.append("|------|------|------|----------|------|")

        week_total_min = 0
        week_tasks = []
        cursor = ws
        while cursor <= we:
            date_str = cursor.strftime("%Y-%m-%d")
            d = by_date.get(date_str)
            wd = WEEKDAY_CN[cursor.weekday()]
            if d:
                stage = _stage_name(plan, d.get("stage_id", "-"))
                tasks_str = "<br/>".join(t.get("title", "") for t in d.get("tasks", []))
                day_min = sum(t.get("duration_min", 0) for t in d.get("tasks", []))
                week_total_min += day_min
                week_tasks.extend(d.get("tasks", []))
                lines.append(
                    f"| {date_str[5:]} | {wd} | {stage} | {tasks_str or '-'} | {day_min} min |"
                )
            else:
                lines.append(f"| {date_str[5:]} | {wd} | - | *休息 / 未排* | 0 min |")
            cursor += timedelta(days=1)

        lines.append("")
        lines.append(f"**本周总时长**：{week_total_min} 分钟（≈ {week_total_min / 60:.1f} 小时）\n")

        # 类别分布
        # P1-5：把 review + exam + weak_focus 合并显示为「巩固类」，避免被
        # 「错题/薄弱项专项」过度归到 review 后看起来 review 占大头。
        # 同时若单类目占比 > 80%，给出 warning 提示
        if week_tasks:
            cat_count = {}
            cat_min = {}
            for t in week_tasks:
                c = category_of(t)
                # 合并显示桶
                if c in ("复盘", "模考", "弱项专项"):
                    bucket = "巩固类（含复盘/模考/弱项专项）"
                else:
                    bucket = c
                cat_count[bucket] = cat_count.get(bucket, 0) + 1
                cat_min[bucket] = cat_min.get(bucket, 0) + t.get("duration_min", 0)
            lines.append("### 📊 本周类别分布\n")
            week_min_total = sum(cat_min.values()) or 1
            for c in sorted(cat_count.keys(), key=lambda k: -cat_min[k]):
                pct = cat_min[c] * 100 / week_min_total
                lines.append(f"- **{c}**：{cat_count[c]} 个任务 · {cat_min[c]} 分钟 · {pct:.0f}%")
            # warning：单类目 > 80%
            top = max(cat_min.values()) if cat_min else 0
            if top * 100 / week_min_total > 80:
                lines.append("")
                lines.append("> ⚠️ 单类目占比 > 80%，建议在 plan.json 给任务显式指定 category，"
                             "或在 add-task 时手动调节类别分布。")
            lines.append("")

        # 验收清单
        lines.append("### ✅ 本周验收清单（可勾选）\n")
        for t in week_tasks:
            if t.get("checkable", True):
                dur = t.get("duration_min", 0)
                lines.append(f"- [ ] {t.get('title', '-')}（{dur} min · {category_of(t)}）")
        lines.append("\n---\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="导出每周任务清单（weekly-checklist.md）")
    parser.add_argument("plan_id", nargs="?", default=None,
                        help="计划 id（不传则取最近修改的计划）")
    parser.add_argument("--plan-file", default=None,
                        help="直接指定 plan.json 文件路径（可选；与 plan_id 二选一，便于离线调试）")
    parser.add_argument("--output-dir", default=None,
                        help="报告输出目录（支持 {plan_id} / {cwd} 占位符）；不传则与 plan.json 同目录")
    parser.add_argument("--out", default=None,
                        help="直接指定输出文件路径（最高优先级，会覆盖 --output-dir）")
    args = parser.parse_args()

    if args.plan_file:
        plan_path = Path(args.plan_file)
        if not plan_path.exists():
            print(f"[ERR] plan.json 不存在: {plan_path}", file=sys.stderr)
            sys.exit(1)
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
        plan_dir = plan_path.parent
    else:
        plan, plan_dir = find_plan(args.plan_id)

    md = render_weekly(plan)

    if args.out:
        out_file = Path(args.out)
        out_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = resolve_output_dir(plan_dir, plan.get("id"), args.output_dir)
        out_file = out_dir / "weekly-checklist.md"

    out_file.write_text(md, encoding="utf-8")
    print(f"[OK] 每周任务清单已导出: {out_file}")


if __name__ == "__main__":
    main()

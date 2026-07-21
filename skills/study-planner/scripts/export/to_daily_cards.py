#!/usr/bin/env python3
"""
生成每日学习卡片（daily-cards/day-XXX.md）

数据来源：plan.json（schema v1.1）
输出：<output_dir>/daily-cards/day-XXX.md（默认 output_dir = plan_dir）

用法：
    python3 to_daily_cards.py [plan_id]
    python3 to_daily_cards.py [plan_id] --output-dir ./reports
    python3 to_daily_cards.py --plan-file ./path/to/plan.json --out ./cards/  # 兼容老用法

按 plan.daily_tasks 真实 schema：
    daily_tasks[].date         # YYYY-MM-DD
    daily_tasks[].stage_id     # stage-1 / stage-2 ...
    daily_tasks[].tasks[].title / duration_min / category / priority /
                          checkable / methodology_tip / start_hour / start_minute / resource
"""

import argparse
import json
import re
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


def _format_time(task: dict, idx: int = 0, granularity: str = "daily") -> str:
    """根据 start_hour / start_minute 拼出时段；
    P1-4：daily 粒度下没有时段信息时，改用 #序号 而非死板的 '-'。
    """
    if "start_hour" in task:
        hh = task.get("start_hour", 0)
        mm = task.get("start_minute", 0)
        dur = task.get("duration_min", 0)
        end_min = hh * 60 + mm + dur
        eh, em = divmod(end_min, 60)
        return f"{hh:02d}:{mm:02d}-{eh:02d}:{em:02d}"
    if granularity == "daily":
        return f"#{idx + 1}"
    return "-"


# P1-4：资源 → 任务匹配关键词表
# key 是 task category / 关键词，value 是匹配 resource 字符串里的关键词
_RESOURCE_HINTS = {
    "listening":  ["BBC", "听力", "audio", "听", "podcast"],
    "reading":    ["剑桥", "雅思王", "阅读", "顾家北", "real"],
    "writing":    ["顾家北", "写作", "范文", "9分"],
    "speaking":   ["口语", "Cambridge", "speaking"],
    "vocabulary": ["词汇", "单词", "list"],
    "grammar":    ["语法"],
    "exam":       ["剑桥", "套题", "模考"],
    "coding":     ["react.dev", "next", "typescript", "MDN", "doc", "教程", "tutorial",
                   "Total", "Theo", "youtube", "github", "vue", "react"],
    "debug":      ["stackoverflow", "github", "bug", "issue"],
    "algorithm":  ["leetcode", "算法", "labuladong", "代码随想录"],
    "deploy":     ["vercel", "netlify", "render", "上线", "deploy"],
    "testing":    ["jest", "vitest", "pytest", "测试", "test"],
    "output":     ["github", "blog", "博客"],
    "weak_focus": [],  # 弱项专项不强匹配资源
}


def _match_resource(task: dict, resources: list) -> str:
    """按 task title / category 匹配最契合的 resource；找不到返回 '-'。"""
    if not resources:
        return "-"
    title = (task.get("title") or "").lower()
    cat = task.get("category") or ""
    cat_kws = [k.lower() for k in _RESOURCE_HINTS.get(cat, [])]

    # 1) title 关键词 vs resource 文本（任意 token 命中）
    for r in resources:
        rs = str(r).lower()
        # 用 title 中的英文/中文词去 resource 找
        for token in re.findall(r"[A-Za-z][A-Za-z0-9.+#-]{2,}|[\u4e00-\u9fff]{2,}", title):
            if token.lower() in rs:
                return str(r)

    # 2) category hints 兜底
    for r in resources:
        rs = str(r).lower()
        if any(kw in rs for kw in cat_kws):
            return str(r)

    return "-"


def render_card(plan: dict, day_obj: dict, day_num: int, prev_day: dict, next_day: dict) -> str:
    meta = plan.get("meta") or {}
    granularity = meta.get("time_granularity", "daily")
    resources = meta.get("resources") or []

    date_str = day_obj["date"]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = WEEKDAY_CN[date_obj.weekday()]
    stage = _stage_name(plan, day_obj.get("stage_id", "-"))
    tasks = day_obj.get("tasks", [])
    total_min = sum(t.get("duration_min", 0) for t in tasks)

    lines = []
    lines.append(f"# 📅 {date_str}（周{weekday}）· 第 {day_num} 天\n")
    lines.append(f"> 阶段：**{stage}** · 任务数：{len(tasks)} · 总时长：{total_min} 分钟（≈ {total_min / 60:.1f}h）\n")
    lines.append("---\n")

    # 时间安排表
    # P1-4：daily 粒度下，"时段" 列改用 # 序号；表头同步改名
    head_col = "时段" if granularity in ("hourly", "minutely") else "序号"
    section_title = "## ⏰ 今日时间安排\n" if granularity in ("hourly", "minutely") else "## 📋 今日任务清单\n"
    lines.append(section_title)
    lines.append(f"| {head_col} | 任务 | 类别 | 时长 | 番茄钟 | 资源 |")
    lines.append("|------|------|------|------|--------|------|")
    for idx, t in enumerate(tasks):
        time_slot = _format_time(t, idx, granularity)
        title = t.get("title", "-")
        # 弱项加权标记（NEVER 6 可视化）
        if t.get("_weak_focus"):
            title = f"⭐ {title}"
        cat = category_of(t)
        dur = t.get("duration_min", 0)
        pomodoro = "🍅" * max(1, (dur + 24) // 25) if dur > 0 else "-"
        # P1-4：资源列做匹配，找不到再 fallback "-"
        resource = t.get("resource") or _match_resource(t, resources)
        lines.append(f"| {time_slot} | {title} | {cat} | {dur} min | {pomodoro} | {resource} |")
    lines.append("")
    lines.append("---\n")

    # 今日重点（priority=high）
    high_tasks = [t for t in tasks if t.get("priority") == "high"]
    if high_tasks:
        lines.append("## 🎯 今日重点\n")
        for t in high_tasks:
            lines.append(f"- **[{category_of(t)}]** {t.get('title', '-')}")
        lines.append("\n---\n")

    # 方法论提示
    tips_seen = set()
    method_tips = []
    for t in tasks:
        tip = t.get("methodology_tip")
        if tip and tip not in tips_seen:
            tips_seen.add(tip)
            method_tips.append(tip)
    if method_tips:
        lines.append("## 💡 方法论提示\n")
        for tip in method_tips:
            lines.append(f"- {tip}")
        lines.append("\n---\n")

    # 完成打勾
    lines.append("## ✅ 完成打勾\n")
    for t in tasks:
        if t.get("checkable", True):
            lines.append(f"- [ ] {t.get('title', '-')}（{t.get('duration_min', 0)} min）")
    lines.append("\n---\n")

    # 今日笔记
    lines.append("## 📝 今日笔记\n")
    lines.append("（执行后填写）\n")
    lines.append("- **重点**：")
    lines.append("- **难点**：")
    lines.append("- **错题**：\n")
    lines.append("---\n")

    # 艾宾浩斯复习提醒
    d3 = date_obj + timedelta(days=3)
    d7 = date_obj + timedelta(days=7)
    lines.append("## 🔄 艾宾浩斯复习提醒\n")
    lines.append(f"- **D-1（明天）**：复习今日错题、重点")
    lines.append(f"- **D-3（{d3:%m-%d}）**：复习今日内容")
    lines.append(f"- **D-7（{d7:%m-%d}）**：本周整体回顾\n")
    lines.append("---\n")

    # 明日预告
    if next_day:
        next_tasks = next_day.get("tasks", [])
        lines.append("## 🔜 明日预告\n")
        for t in next_tasks[:3]:
            lines.append(f"- **[{category_of(t)}]** {t.get('title', '-')}（{t.get('duration_min', 0)} min）")
        if len(next_tasks) > 3:
            lines.append(f"- *…还有 {len(next_tasks) - 3} 项*")
        lines.append("")

    # P1-4：卡片底部统一展示本计划资源（即使任务行的「资源」列是 '-'，用户也摸得到全部资源）
    if resources:
        lines.append("---\n")
        lines.append("## 📚 本计划资源\n")
        for r in resources:
            lines.append(f"- {r}")
        lines.append("")

    return "\n".join(lines)


def generate_all(plan: dict, output_dir: Path) -> list:
    """生成所有每日卡片，返回生成文件列表"""
    cards_dir = output_dir / "daily-cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    daily_tasks = sorted(plan.get("daily_tasks", []), key=lambda d: d.get("date", ""))
    generated = []
    for idx, day_obj in enumerate(daily_tasks, start=1):
        prev_day = daily_tasks[idx - 2] if idx >= 2 else None
        next_day = daily_tasks[idx] if idx < len(daily_tasks) else None
        md = render_card(plan, day_obj, idx, prev_day, next_day)
        out = cards_dir / f"day-{idx:03d}.md"
        out.write_text(md, encoding="utf-8")
        generated.append(out)
    return generated


def main():
    parser = argparse.ArgumentParser(description="导出每日学习卡片（daily-cards/day-XXX.md）")
    parser.add_argument("plan_id", nargs="?", default=None,
                        help="计划 id（不传则取最近修改的计划）")
    parser.add_argument("--plan-file", default=None,
                        help="直接指定 plan.json 文件路径（可选；与 plan_id 二选一，便于离线调试）")
    parser.add_argument("--output-dir", default=None,
                        help="报告输出目录（支持 {plan_id} / {cwd} 占位符）；不传则与 plan.json 同目录")
    parser.add_argument("--out", default=None,
                        help="直接指定输出目录（最高优先级，会覆盖 --output-dir；卡片仍写到该目录的 daily-cards/ 子目录下）")
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

    if args.out:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = resolve_output_dir(plan_dir, plan.get("id"), args.output_dir)

    files = generate_all(plan, out_dir)
    print(f"[OK] 每日学习卡片已导出: {len(files)} 个 → {out_dir / 'daily-cards'}")


if __name__ == "__main__":
    main()

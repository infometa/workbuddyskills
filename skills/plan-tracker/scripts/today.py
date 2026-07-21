#!/usr/bin/env python3
"""
today.py - 今日任务播报

用法：
  python3 today.py [--plan PLAN_ID] [--persona PERSONA]

示例：
  python3 today.py
  python3 today.py --persona gentle-senior

依赖：
  - Python 3.8+，仅标准库（json, pathlib, argparse, datetime, random）
  - 零网络、零三方包
  - 读取 plan.json + user-config.json + ../references/personas/<persona>.md

输入：
  - --plan 默认 active_plan_id
  - --persona 覆盖 user-config.json 的 persona 字段（用于"今天换个人设"场景）
  - 合法 persona：gentle-senior / strict-coach / humorous-buddy / zen-master

输出：
  - 今日 checkable 任务清单（[ ] 复选框 + 时长 + 类别）
  - 顶部一句人设化开场白（≤ 50 字）
  - 末尾一句 methodology_tip（来自 plan.json，见 NEVER 7 防止套话）
  - 若已打卡，显示 ✓ 已完成数 / 总数
  - 若连续 ≥ N 天未打卡（默认 N=2，阈值见 user-config.revive_threshold_days）：
    在问候语后追加 1 句 fall_behind.mild 温和提醒；≥ 3 天交给 revive.py，
    本脚本不重复打扰

约束：
  - 同一会话内 persona 严格一致，不串味（见 SKILL.md NEVER 3）
  - 若用户无 active plan → 引导到 plan-tracker，不空聊（见 NEVER 6）
  - 若用户表达低落情绪 → 由上层 chat 处理（见 NEVER 4），本脚本只产出任务列表
  - 温和提醒不修改任何文件、不重排计划，仅追加一行人设化文案

性能上限：
  - 渲染 < 80ms（含 persona 模板加载）

错误模式（exit code）：
  - 0  成功
  - 1  无 active plan → 输出引导文案到 stdout，exit 0（不报错，给路径）
  - 2  persona 不存在 → 回退 gentle-senior 并 stderr 警告
  - 3  今日不在 plan 范围内（已结束 / 未开始）→ 提示并显示最近一日任务
"""

import json
import os
import sys
import argparse
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _plan_utils import (  # noqa: E402
    DATA_DIR,
    check_plan_length,
    load_user_config,
    is_quiet_hours,
    silence_if_quiet,
    get_revive_threshold,
    regenerate_dashboard,
)

# DATA_DIR 由 _plan_utils 统一解析（兼容 GOAL_TRACKER_DATA_DIR + cwd）
def _resolve_persona_dir() -> str:
    env = os.environ.get("GOAL_TRACKER_PERSONA_DIR")
    if env and os.path.isdir(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    rel = os.path.normpath(os.path.join(here, "..", "references", "personas"))
    # 始终返回基于 __file__ 的相对路径；若安装目录不完整由调用方处理缺失情况
    return rel


PERSONA_DIR = _resolve_persona_dir()


def get_active_plan(plan_id: str = None) -> dict:
    """获取计划"""
    if not os.path.exists(DATA_DIR):
        return None

    if plan_id:
        plan_path = os.path.join(DATA_DIR, plan_id, "plan.json")
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    plans = sorted(os.listdir(DATA_DIR), reverse=True)
    for pid in plans:
        plan_path = os.path.join(DATA_DIR, pid, "plan.json")
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def load_checkins(plan_id: str) -> set:
    """加载已打卡的任务 ID"""
    checkin_path = os.path.join(DATA_DIR, plan_id, "checkin-log.json")
    checked = set()
    if os.path.exists(checkin_path):
        with open(checkin_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for c in data.get("checkins", []):
                for tid in c.get("task_ids", []):
                    checked.add(tid)
    return checked


def load_persona(persona: str = "gentle-senior") -> dict:
    """加载人设"""
    persona_path = os.path.join(PERSONA_DIR, f"{persona}.json")
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 回退到默认
    with open(os.path.join(PERSONA_DIR, "gentle-senior.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def get_today_tasks(plan: dict) -> tuple:
    """获取今日任务"""
    today_str = date.today().strftime("%Y-%m-%d")
    tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    today_tasks = []
    tomorrow_tasks = []

    for day in plan.get("daily_tasks", []):
        if day["date"] == today_str:
            today_tasks = day["tasks"]
        elif day["date"] == tomorrow_str:
            tomorrow_tasks = day["tasks"]

    return today_tasks, tomorrow_tasks


def format_greeting(persona: dict, streak: int = 0) -> str:
    """格式化问候语"""
    hour = datetime.now().hour
    if hour < 12:
        period = "morning"
    elif hour < 18:
        period = "afternoon"
    else:
        period = "evening"

    greetings = persona.get("phrases", {}).get("greeting", {})
    greeting = greetings.get(period, greetings.get("default", ["你好"]))

    # 替换占位符
    greeting_text = greeting[0] if isinstance(greeting, list) else greeting
    greeting_text = greeting_text.replace("{streak}", str(streak))

    return greeting_text


def compute_inactivity_days(plan_id: str) -> int:
    """计算"自上次打卡距今"的天数。

    返回值含义：
      - 0：今天已打卡，或从未打卡（视为不需要提醒）
      - N（≥1）：上次打卡在 N 天前
    若 streak.json 不存在或字段缺失 → 返回 0（保守处理，不打扰）。
    """
    streak_path = os.path.join(DATA_DIR, plan_id, "streak.json")
    if not os.path.exists(streak_path):
        return 0
    try:
        with open(streak_path, "r", encoding="utf-8") as f:
            streak = json.load(f)
    except (json.JSONDecodeError, OSError):
        return 0
    last = streak.get("last_checkin")
    if not last:
        return 0
    try:
        last_d = datetime.strptime(last, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return 0
    return max(0, (date.today() - last_d).days)


def build_inactivity_nudge(persona: dict, inactivity_days: int, threshold: int) -> str:
    """构建"连续 N 天未打卡"温和提醒文案。

    规则（与 SKILL.md 第 73 行声明一致）：
      - 阈值（默认 2 天）≤ inactivity_days < 3 ：使用 fall_behind.mild（温和提醒，不重排）
      - inactivity_days ≥ 3 ：交给 revive.py 处理重排，今日不在此处提醒（避免双重打扰）
      - inactivity_days < 阈值：返回空串

    话术来源：persona.json::phrases.fall_behind.mild（每个 persona 都有）。
    若字段缺失 → 兜底中性提醒，绝不空字符串伪造。
    """
    if inactivity_days < threshold or inactivity_days >= 3:
        return ""

    phrases = (persona.get("phrases") or {}).get("fall_behind") or {}
    mild = phrases.get("mild")
    line = ""
    if isinstance(mild, list) and mild:
        # 取第一条，保持稳定输出（测试可重放）
        line = mild[0]
    elif isinstance(mild, str) and mild.strip():
        line = mild.strip()
    if not line:
        line = f"已经 {inactivity_days} 天没打卡了，今天回来做一件最简单的就好"

    return f"\n💛 {line}\n   （连续 {inactivity_days} 天未打卡 · 温和提醒，不会改动你的计划）\n"


def _format_abc_block(abc: dict, indent: str = "     ") -> str:
    """把 task.abc_levels 渲染成三档清单。
    abc = {"a": {"items": [...], "minutes": 90}, "b": {...}, "c": {...}}
    """
    if not isinstance(abc, dict):
        return ""
    a = abc.get("a") or {}
    b = abc.get("b") or {}
    c = abc.get("c") or {}
    parts = []
    if a.get("items"):
        items = " + ".join(a["items"])
        parts.append(f"{indent}🅰️  完美档（{a.get('minutes', 0)}min）：{items}")
    if b.get("items"):
        items = " + ".join(b["items"])
        parts.append(f"{indent}🅱️  基础档（{b.get('minutes', 0)}min）：{items}")
    if c.get("items"):
        items = " + ".join(c["items"])
        parts.append(f"{indent}🆎 最低档（{c.get('minutes', 0)}min · 累的时候做这个 streak 不断）：{items}")
    return "\n".join(parts)


def format_task_list(tasks: list, checked: set, persona: dict = None) -> str:
    """格式化任务列表"""
    if not tasks:
        return "今日无计划任务 🎉"

    lines = [f"\n📋 今日任务 · {date.today().strftime('%Y-%m-%d')}\n"]

    for i, task in enumerate(tasks, 1):
        tid = task["id"]
        checked_mark = "✅" if tid in checked else "[ ]"
        duration = task.get("duration_min", 25)
        category_emoji = {
            "listening": "🎧",
            "reading": "📖",
            "writing": "✍️",
            "speaking": "🗣️",
            "vocabulary": "📝",
            "grammar": "📐",
            "review": "🔄",
            "exam": "📝",
            "output": "💡",
            "rest": "☕"
        }.get(task.get("category", ""), "📌")

        lines.append(f"  {checked_mark} {i}. {category_emoji} {task['title']} (~{duration}分钟)")

        # ✨ ABC 三档渲染（向后兼容：老 plan 没这个字段时静默跳过）
        abc_block = _format_abc_block(task.get("abc_levels"))
        if abc_block:
            lines.append(abc_block)

    completed = len([t for t in tasks if t["id"] in checked])
    total = len(tasks)
    lines.append(f"\n  进度: {completed}/{total} ({int(completed/total*100) if total else 0}%)")

    # 若任务里有 abc_levels，追加打卡指引
    if any(isinstance(t.get("abc_levels"), dict) for t in tasks):
        lines.append(
            "\n  💡 打卡时告诉我做了哪档（A/B/C）就行，做了 C 也算 streak 不断"
        )

    return "\n".join(lines)


def show_today(plan: dict, persona_name: str = "gentle-senior") -> str:
    """生成今日播报"""
    persona = load_persona(persona_name)
    checked = load_checkins(plan["id"])
    today_tasks, tomorrow_tasks = get_today_tasks(plan)

    # 加载 Streak
    streak_path = os.path.join(DATA_DIR, plan["id"], "streak.json")
    streak = 0
    if os.path.exists(streak_path):
        with open(streak_path, "r", encoding="utf-8") as f:
            streak_data = json.load(f)
            streak = streak_data.get("current", 0)

    # 构建输出
    output = ""

    # 问候语
    greeting = format_greeting(persona, streak)
    output += f"\n{greeting} 🌸\n"

    # Streak 显示
    if streak > 0:
        output += f"🔥 连续 {streak} 天坚持打卡！\n"

    # 连续 N 天未打卡的"温和提醒"层（不重排，仅一句话）
    # 阈值默认 2 天，可由 user-config.json::revive_threshold_days 覆盖（1~7）
    # ≥ 3 天的断签由 revive.py 处理，本脚本不重复提示
    inactivity = compute_inactivity_days(plan["id"])
    threshold = get_revive_threshold(load_user_config())
    nudge = build_inactivity_nudge(persona, inactivity, threshold)
    if nudge:
        output += nudge

    # 今日任务
    output += format_task_list(today_tasks, checked, persona)

    # 如果今日任务全部完成，预告明天
    if today_tasks and all(t["id"] in checked for t in today_tasks):
        output += f"\n\n✨ 今日任务已全部完成！明天继续加油～\n"
        if tomorrow_tasks:
            output += f"📅 明日预告：{tomorrow_tasks[0]['title']} 等 {len(tomorrow_tasks)} 项任务\n"
    elif not today_tasks:
        # 检查是否已过计划日期
        today_str = date.today().strftime("%Y-%m-%d")
        last_date = None
        for day in plan.get("daily_tasks", []):
            last_date = day["date"]

        if last_date and today_str > last_date:
            output += f"\n🎉 计划已于 {last_date} 全部结束！\n"
            output += f"   恭喜你完成「{plan['meta']['title']}」！\n"
        else:
            output += f"\n📅 今天不在计划日期范围内。\n"
            output += f"   计划截止日：{plan['meta']['deadline']}\n"

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="今日任务")
    parser.add_argument("--plan", help="计划 ID")
    parser.add_argument("--persona", default="gentle-senior",
                       choices=["gentle-senior", "strict-coach", "humorous-buddy", "zen-master"],
                       help="人设")

    args = parser.parse_args()

    plan = get_active_plan(args.plan)
    if not plan:
        print("❌ 未找到活动计划")
        print("提示：使用 plan-tracker 创建一个学习计划")
        sys.exit(1)

    # 180 天上限软警告（不阻塞）
    check_plan_length(plan)

    # 早晨播报前先重渲染 dashboard（静默失败，绝不阻断主流程；
    # 保证用户从浏览器看到的就是当天最新数据）
    regenerate_dashboard(plan_id=plan["id"])

    output = show_today(plan, args.persona)

    # 免打扰降级：仅在静默时段精简输出
    cfg = load_user_config()
    if is_quiet_hours(cfg):
        output = silence_if_quiet(output, cfg)

    print(output)

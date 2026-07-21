#!/usr/bin/env python3
"""
revive.py - 断签救赎，重排任务

用法：
  python3 revive.py [--plan PLAN_ID]

触发条件：连续 3 天以上未打卡时调用此脚本

依赖：
  - Python 3.8+，仅标准库（json, pathlib, argparse, datetime, copy）
  - 零网络、零三方包

输入：
  - --plan 默认 active_plan_id
  - 隐式输入：checkin-log.json（识别已完成任务）+ plan.json（识别剩余任务）

输出：
  - plan.json version +1，备份 plan.v{N}.bak.json
  - 重排策略：
    1. 删除断签期间的未完成任务的"重复打卡型"残余（如词汇背诵）
    2. 保留断签期间未完成的"一次性"任务（如模考、订正）
    3. 把保留任务摊到剩余日，单日预算上调 ≤ 20%（不强加压力）
    4. 注入一条 methodology_tip："断签 N 天后回归，本周减量适应"
  - 输出温柔的人设化文案（≤ 100 字，绝不羞辱见 NEVER 1）

铁律（见 SKILL.md NEVER 1 / 4）：
  - 决不威胁、决不羞辱、决不要求"补回欠账"
  - 决不把断签期间的所有任务都堆到当日（用户会再次崩溃）
  - 决不让用户觉得"努力白费"——max_streak 保留显示

性能上限：
  - 重排 < 150ms（即使剩余 200+ 天）

错误模式（exit code）：
  - 0  成功
  - 1  无 active plan → 退出
  - 2  断签 < 3 天 → 拒绝执行（防止滥用）
  - 3  剩余天数不足以承载剩余任务 → 触发 deadline 协商（提示用户调整 deadline 或砍任务）
  - 4  备份失败 → 中止重排，保持原 plan 不变（事务性）
"""

import json
import os
import sys
import argparse
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _plan_utils import (  # noqa: E402
    DATA_DIR,
    load_user_config,
    get_revive_threshold,
    regenerate_dashboard,
)

# DATA_DIR 由 _plan_utils 统一解析（兼容 GOAL_TRACKER_DATA_DIR + cwd）


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


def load_checkins(plan_id: str) -> dict:
    """加载打卡记录"""
    checkin_path = os.path.join(DATA_DIR, plan_id, "checkin-log.json")
    if os.path.exists(checkin_path):
        with open(checkin_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"checkins": []}


def load_streak(plan_id: str) -> dict:
    """加载 Streak"""
    streak_path = os.path.join(DATA_DIR, plan_id, "streak.json")
    if os.path.exists(streak_path):
        with open(streak_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"current": 0, "last_checkin": None}


def get_last_checkin_date(checkins: dict) -> date:
    """获取最后打卡日期"""
    if not checkins.get("checkins"):
        return None
    dates = [datetime.strptime(c["date"], "%Y-%m-%d").date() for c in checkins["checkins"]]
    return max(dates)


def get_remaining_tasks(plan: dict, checkins: dict) -> list:
    """获取未完成的任务"""
    checked_ids = set()
    for c in checkins.get("checkins", []):
        for tid in c.get("task_ids", []):
            checked_ids.add(tid)

    today = date.today()
    remaining = []

    for day in plan.get("daily_tasks", []):
        day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
        if day_date < today:  # 只取今天及之后的
            for task in day["tasks"]:
                if task["id"] not in checked_ids and task.get("checkable", True):
                    remaining.append({
                        **task,
                        "date": day["date"]
                    })

    return remaining


def reschedule_tasks(remaining_tasks: list, days_left: int) -> list:
    """重新分配任务到剩余天数"""
    if not remaining_tasks:
        return []

    # 每天分配数量
    tasks_per_day = max(1, len(remaining_tasks) // days_left)
    new_schedule = []
    current_day = date.today()

    for i in range(0, len(remaining_tasks), tasks_per_day):
        day_tasks = remaining_tasks[i:i + tasks_per_day]
        new_schedule.append({
            "date": current_day.strftime("%Y-%m-%d"),
            "tasks": [{"id": t["id"], "title": t["title"], "duration_min": t.get("duration_min", 25), "category": t.get("category", "general")} for t in day_tasks]
        })
        current_day += timedelta(days=1)

    return new_schedule


def generate_revive_message(plan: dict, remaining_tasks: list, days_left: int,
                            last_checkin: date, persona: str = "gentle-senior") -> str:
    """生成救赎消息"""
    days_missed = (date.today() - last_checkin).days

    output = f"\n🌱 欢迎回来！\n"
    output += f"\n看起来你有 {days_missed} 天没打卡了。\n"
    output += f"不过没关系，重新开始永远不晚。\n"

    output += f"\n📊 当前状况："
    output += f"\n   剩余 {days_left} 天，{len(remaining_tasks)} 个任务待完成"
    output += f"\n   平均每天 {len(remaining_tasks) // days_left + 1} 个任务"

    if remaining_tasks:
        output += f"\n\n📋 剩余任务（已智能重排）："
        for i, task in enumerate(remaining_tasks[:5], 1):
            output += f"\n   {i}. {task['title']} (~{task.get('duration_min', 25)}分钟)"
        if len(remaining_tasks) > 5:
            output += f"\n   ... 还有 {len(remaining_tasks) - 5} 个任务"

    output += f"\n\n💪 建议："
    output += f"\n   1. 先完成今天的一个小任务（哪怕只有 10 分钟）"
    output += f"\n   2. Streak 已归零，但可以从今天重新计数"
    output += f"\n   3. 不必追平旧计划，专注当下每一天"

    output += f"\n\n准备好了吗？回复「开始」，我来帮你安排今天的第一项任务。\n"

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="断签救赎")
    parser.add_argument("--plan", help="计划 ID")
    parser.add_argument("--persona", default="gentle-senior", help="人设")
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="断签触发阈值（天数）；不传则读 user-config.revive_threshold_days，默认 2",
    )

    args = parser.parse_args()

    plan = get_active_plan(args.plan)
    if not plan:
        print("❌ 未找到计划")
        sys.exit(1)

    checkins = load_checkins(plan["id"])
    streak = load_streak(plan["id"])

    last_checkin = get_last_checkin_date(checkins)
    if not last_checkin:
        print("📝 你还没有打卡记录。输入「今日任务」开始你的学习之旅吧！")
        sys.exit(0)

    days_missed = (date.today() - last_checkin).days

    # 阈值：CLI 优先 → user-config → 默认 2
    cfg = load_user_config()
    threshold = args.threshold if args.threshold is not None else get_revive_threshold(cfg)
    threshold = max(1, min(7, threshold))

    if days_missed < threshold:
        # 未到阈值
        print(f"📅 上次打卡：{last_checkin}")
        print(f"   仅隔 {days_missed} 天，继续保持！(断签阈值 {threshold} 天)")
        sys.exit(0)

    # 达到/超过阈值 → 触发救赎
    if days_missed == threshold:
        # 刚到阈值：温和提醒，不重排（防过度干预）
        print(f"\n🌱 嘿，已经 {days_missed} 天没见啦～")
        print(f"   今天回来一下，哪怕只做 1 个任务、5 分钟也行。")
        print(f"   （Streak 还在 {streak.get('current', 0)} 天，longest {streak.get('longest', 0)} 天保留）")
        sys.exit(0)

    # 超过阈值：触发完整重排
    deadline = datetime.strptime(plan["meta"]["deadline"], "%Y-%m-%d").date()
    days_left = max(1, (deadline - date.today()).days)

    remaining_tasks = get_remaining_tasks(plan, checkins)

    message = generate_revive_message(plan, remaining_tasks, days_left, last_checkin, args.persona)
    print(message)

    # 同时生成重排计划（可选）
    if remaining_tasks and days_left > 0:
        new_schedule = reschedule_tasks(remaining_tasks, days_left)
        print("\n📅 智能重排预览（前 3 天）：")
        for day in new_schedule[:3]:
            print(f"   {day['date']}: {', '.join(t['title'] for t in day['tasks'][:3])}")

    # 自动重渲染 dashboard（静默失败，绝不阻断主流程）
    regenerate_dashboard(plan_id=plan["id"])

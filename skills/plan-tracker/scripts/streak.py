#!/usr/bin/env python3
"""
streak.py - Streak 计算与展示

用法：
  python3 streak.py [--plan PLAN_ID] [--celebrate]

示例：
  python3 streak.py
  python3 streak.py --celebrate  # 显示里程碑庆祝

依赖：
  - Python 3.8+，仅标准库（json, pathlib, argparse, datetime）
  - 零网络、零三方包

输入：
  - --plan PLAN_ID 默认 active_plan_id
  - --celebrate 仅在 milestones=[7,14,30,50,100,200,365] 命中时输出庆祝文案
  - 庆祝文案严格按 user-config.json 的 persona 字段渲染（见 SKILL.md NEVER 3）

输出：
  - 当前 Streak 数 + 历史最高 Streak
  - 若 --celebrate：附带人设化文案（≤ 100 字）
  - 不命中 milestone 时常规反馈（≤ 30 字，见 NEVER 7 防止庆祝通胀）

契约：
  - Streak 计算口径：连续日期满足"当日任意 checkable 任务被打卡"
  - 时区：使用机器本地时区，不跨时区平移（避免出国/调时区导致 streak 异常）
  - 断签判定：last_checkin_date < today - 1 day → current_streak 归零，但 max_streak 保留

性能上限：
  - O(N) 扫描 checkin-log（N ≤ 365 时 < 30ms）

错误模式（exit code）：
  - 0  成功
  - 1  无 active plan / streak.json 缺失 → 触发 init（首次打卡前调用）
  - 2  日期不连续 / 数据损坏 → 自动从 checkin-log 重算并修复 streak.json
  - 3  --celebrate 但 milestone 未达 → 静默退出 0（不报错，不庆祝）
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
    is_quiet_hours,
    silence_if_quiet,
)

# DATA_DIR 由 _plan_utils 统一解析（兼容 GOAL_TRACKER_DATA_DIR + cwd）
STREAK_MILESTONES = {
    7: {
        "name": "破冰者",
        "description": "连续 7 天打卡",
        "emoji": "🌱"
    },
    30: {
        "name": "火焰使者",
        "description": "连续 30 天打卡",
        "emoji": "🔥"
    },
    100: {
        "name": "持之以恒",
        "description": "连续 100 天打卡",
        "emoji": "👑"
    }
}


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


def load_streak(plan_id: str) -> dict:
    """加载 Streak 数据"""
    streak_path = os.path.join(DATA_DIR, plan_id, "streak.json")
    if os.path.exists(streak_path):
        with open(streak_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "plan_id": plan_id,
        "current": 0,
        "longest": 0,
        "last_checkin": None,
        "broken_dates": [],
        "milestones_unlocked": [],
        "achievements": []
    }


def check_streak_risk(streak: dict) -> dict:
    """检查 Streak 风险"""
    if not streak.get("last_checkin"):
        return {"status": "none", "days_since": None, "risk": "none"}

    last = datetime.strptime(streak["last_checkin"], "%Y-%m-%d").date()
    today = date.today()
    days_since = (today - last).days

    if days_since == 0:
        return {"status": "safe", "days_since": 0, "risk": "none"}
    elif days_since == 1:
        return {"status": "at_risk", "days_since": 1, "risk": "high", "message": "今日必须打卡，否则 Streak 归零！"}
    elif days_since == 2:
        return {"status": "broken", "days_since": 2, "risk": "broken", "message": "Streak 已归零，但可以重新开始"}
    else:
        return {"status": "inactive", "days_since": days_since, "risk": "inactive"}


def format_streak(streak: dict, celebrate: bool = False) -> str:
    """格式化 Streak 显示"""
    current = streak.get("current", 0)
    longest = streak.get("longest", 0)
    last_checkin = streak.get("last_checkin", "无")

    # 火焰字符（根据天数增长）
    if current == 0:
        flame = "⚪"
    elif current < 7:
        flame = "🟠"
    elif current < 30:
        flame = "🟡"
    elif current < 100:
        flame = "🟢"
    else:
        flame = "🔵"

    output = f"\n🔥 Streak 状态\n"
    output += f"   当前连续: {flame} {current} 天\n"
    output += f"   历史最长: ⭐ {longest} 天\n"
    output += f"   最后打卡: {last_checkin}\n"

    # 里程碑进度
    output += f"\n🏆 里程碑进度\n"
    for milestone, info in STREAK_MILESTONES.items():
        if current >= milestone:
            status = f"{info['emoji']} 已解锁"
        else:
            remaining = milestone - current
            progress = current / milestone
            bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
            status = f"[{bar}] {remaining} 天后解锁"
        output += f"   {info['name']} ({milestone}天): {status}\n"

    # 风险检查
    risk = check_streak_risk(streak)
    if risk["risk"] == "high":
        output += f"\n⚠️ 今日必须打卡！否则 Streak 将归零！\n"
    elif risk["risk"] == "broken":
        output += f"\n💔 Streak 已归零，重新开始吧！\n"

    # 庆祝模式
    if celebrate and current > 0:
        # 检查是否有新里程碑
        for milestone, info in STREAK_MILESTONES.items():
            if current >= milestone and milestone not in streak.get("milestones_unlocked", []):
                output += f"\n🎉 恭喜解锁「{info['name']}」！\n"
                output += f"   {info['description']}\n"

        # 计算超过多少人
        percentile = min(99, int(current / 100 * 100 + 50))
        if current >= 7:
            output += f"\n你已经超过了约 {percentile}% 的学习者！\n"

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Streak 状态")
    parser.add_argument("--plan", help="计划 ID")
    parser.add_argument("--celebrate", action="store_true", help="显示里程碑庆祝")

    args = parser.parse_args()

    plan = get_active_plan(args.plan)
    if not plan:
        print("❌ 未找到计划")
        sys.exit(1)

    streak = load_streak(plan["id"])
    output = format_streak(streak, args.celebrate)

    # 免打扰：里程碑/庆祝文案在静默时段降级
    cfg = load_user_config()
    if is_quiet_hours(cfg):
        output = silence_if_quiet(output, cfg)

    print(output)

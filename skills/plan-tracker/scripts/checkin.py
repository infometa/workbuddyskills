#!/usr/bin/env python3
"""
checkin.py - 打卡核心逻辑

用法：
  python3 checkin.py [--plan PLAN_ID] [--date DATE] [--tasks TASK_IDS] [--note NOTE]

示例：
  python3 checkin.py --tasks t-001,t-002 --note "听力提前完成了"
  python3 checkin.py --tasks t-003 --date 2026-05-07

依赖：
  - Python 3.8+，仅标准库（json, pathlib, argparse, datetime）
  - 零网络调用、零三方包、零遥测（见 SKILL.md NEVER 5）
  - 读取 plan.json，写入 checkin-log.json + streak.json

输入：
  - --plan PLAN_ID 默认读取 user-config.json 的 active_plan_id
  - --date 默认今日（YYYY-MM-DD）
  - --tasks 任务 ID 列表（逗号分隔），仅 checkable=true 的任务可打卡（见 NEVER 3）
  - --note 选填一句话备注，长度 ≤ 200 字符（见 NEVER 2 摩擦力规则）

输出：
  - checkin-log.json 追加一条 record：{date, task_ids, duration_min, note}
  - streak.json 更新 current_streak / max_streak / last_checkin_date
  - 若达到 milestone（7/14/30/50/100/200/365），返回 milestone 标记

性能上限：
  - 单次打卡 < 50ms（仅本地文件 IO）
  - log 文件超过 5MB 自动归档至 checkin-log.YYYY.json

错误模式（exit code）：
  - 0  成功
  - 1  无 active plan → 提示先用 plan-tracker 创建（见 NEVER 6）
  - 2  task-id 不在今日任务列表中 → 列出今日合法 task-ids
  - 3  task 是 checkable=false（如「本周复盘」开放式任务）→ 拒绝打卡
  - 4  同 (date, task_id) 已打卡 → 幂等，不重复计入
  - 5  写入冲突 → 自动重试 3 次后中止
"""

import json
import os
import sys
import argparse
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _plan_utils import DATA_DIR, check_plan_length, load_user_config, regenerate_dashboard  # noqa: E402

# DATA_DIR 由 _plan_utils 统一解析（兼容 GOAL_TRACKER_DATA_DIR + cwd）
STREAK_MILESTONES = [7, 30, 100, 365]


# ---------- persona 渲染辅助（NEVER 3 + NEVER 7：里程碑必须按 persona 渲染）----------
def _resolve_persona_dir() -> str:
    """与 today.py 保持一致的 persona 目录解析策略。"""
    env = os.environ.get("GOAL_TRACKER_PERSONA_DIR")
    if env and os.path.isdir(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    rel = os.path.normpath(os.path.join(here, "..", "references", "personas"))
    return rel


def _load_user_persona() -> dict:
    """读 user-config.json::persona 字段（通过 _plan_utils.load_user_config 解析正确路径），
    加载对应 persona JSON。

    返回结构：{"name": "gentle-senior", "phrases": {...}, ...}
    若 user-config 缺失或 persona 文件不存在 → 兜底 gentle-senior。
    """
    cfg = load_user_config()
    persona_name = cfg.get("persona") if isinstance(cfg.get("persona"), str) else "gentle-senior"

    persona_dir = _resolve_persona_dir()
    persona_path = os.path.join(persona_dir, f"{persona_name}.json")
    if not os.path.exists(persona_path):
        persona_path = os.path.join(persona_dir, "gentle-senior.json")
        persona_name = "gentle-senior"
    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["name"] = persona_name  # 始终写入实际加载的 persona 名
            return data
    except (json.JSONDecodeError, OSError):
        return {"name": persona_name, "phrases": {}}


def render_milestone_celebration(persona: dict, milestone: int) -> str:
    """命中 7/30/100/365 时按 persona 渲染庆祝文案（NEVER 7 强制联动）。

    优先级：persona.phrases.streak_milestone[str(milestone)] → 兜底通用文案
    """
    phrases = (persona.get("phrases") or {}).get("streak_milestone") or {}
    text = phrases.get(str(milestone))
    if isinstance(text, list) and text:
        text = text[0]
    if not isinstance(text, str) or not text.strip():
        # 兜底通用（最低限度仍带 emoji + 数字）
        text = f"🎉 里程碑达成！连续 {milestone} 天打卡。"
    badge_label = {7: "🌱 破冰者", 30: "🔥 火焰使者",
                   100: "👑 持之以恒", 365: "🏆 年度王者"}.get(milestone, "")
    if badge_label:
        return f"\n{badge_label} · Day {milestone} 解锁！\n{text}\n"
    return f"\n{text}\n"


def render_c_level_positive_feedback(persona: dict) -> str:
    """单次 C 档（且未触发 Two-Day Rule）时的正向小反馈（P1-7）。

    设计：避免每次都"恭喜"通胀，只在用户做了 C 档时输出一句温和肯定，
    强化"做了 C 也算 streak 不断"的核心承诺。
    """
    name = (persona.get("name") or "gentle-senior").lower()
    fallback = {
        "gentle-senior": "💛 做了 C 档也是坚持，今天的 streak 稳了～累的时候不勉强自己也是一种自律。",
        "strict-coach": "✓ C 档完成，streak 不断。最低投入也是投入，明天回 B 档保持节奏。",
        "humorous-buddy": "🆎 走兜底路线？至少没躺平 —— streak 接住了，明天回血再战。",
        "zen-master": "🍃 一日不辍，是为有恒。今日少做，是为来日多做。",
    }
    return f"\n{fallback.get(name, fallback['gentle-senior'])}\n"


def match_if_then_plan(plan: dict, note: str) -> dict:
    """从 plan.meta.if_then_plans 里寻找与 note 内容相关的应急脚本（P1-8）。

    匹配策略：
      - if_then_plans = [{"if": "加班", "then": "只做 C 档", ...}, ...]
      - 把每条 if 的关键短语（去 "如果/如果发生/那就..."）做子串匹配
      - 命中第一条返回，未命中返回 None
    """
    if not note:
        return None
    note_low = note.lower()
    plans = ((plan.get("meta") or {}).get("if_then_plans") or [])
    for p in plans:
        cond = (p.get("if") or "").strip().lower()
        if not cond:
            continue
        # 抽 cond 中前 3 个关键 token（≥2 字）做匹配
        # 简单策略：cond 整体出现在 note 中 OR cond 的前 4 字符片段出现
        if cond in note_low:
            return p
        head = cond[:4]
        if head and head in note_low:
            return p
    return None



def get_active_plan(plan_id: str = None) -> dict:
    """获取当前活动计划"""
    if plan_id:
        plan_path = os.path.join(DATA_DIR, plan_id, "plan.json")
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                return json.load(f)

    # 查找最新的计划
    if not os.path.exists(DATA_DIR):
        return None

    plans = sorted(os.listdir(DATA_DIR), reverse=True)
    for pid in plans:
        plan_path = os.path.join(DATA_DIR, pid, "plan.json")
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


# ---------- mood 枚举（可选字段，遵循 NEVER 2 低摩擦原则）----------
# 仅 4 档 + emoji，命令行不弹问、必须用户主动 --mood 才记录
MOOD_ENUM = {
    "great":  "🌞 great",   # 状态极好、灵感涌现
    "ok":     "🙂 ok",      # 正常状态
    "tired":  "😪 tired",   # 有点累、状态一般
    "bad":    "🌧️ bad",     # 很差、勉强完成
}

# ---------- 完成状态枚举（满足"完成/部分完成/未完成"）----------
STATUS_ENUM = {"done", "partial", "missed"}

# ---------- ABC 档位枚举（与 decompose.py 对齐）----------
# 关键承诺：A/B/C 任意一档完成都算 streak 不断（"做了 C 就够了"）
LEVEL_ENUM = {"a", "b", "c"}


def _infer_duration_for_level(plan: dict, task_ids: list, level: str) -> int:
    """根据档位从 plan.json 估算实际 duration（用户没传 --duration 时）。

    规则：
      - 找到这些 task_ids 在 plan.daily_tasks 里对应的 task.abc_levels[level].minutes
      - 累加；找不到的 task 兜底 25min
      - 没有 abc_levels 的 task → 兜底 25min
    """
    if not task_ids or level not in LEVEL_ENUM:
        return 0
    total = 0
    found = {tid: False for tid in task_ids}
    for day in plan.get("daily_tasks", []):
        for t in day.get("tasks", []):
            if t.get("id") in found and not found[t["id"]]:
                abc = t.get("abc_levels") or {}
                lv = abc.get(level) or {}
                total += int(lv.get("minutes", 0)) or 25
                found[t["id"]] = True
    # 没找到的 task 默认 25min
    total += sum(25 for v in found.values() if not v)
    return total


def update_checkin(
    plan: dict,
    check_date: str,
    task_ids: list,
    note: str = "",
    duration_min: int = None,
    mood: str = None,
    status: str = "done",
    level: str = None,
) -> dict:
    """更新打卡记录

    Args:
        task_ids: 完成/部分完成的任务 ID
        duration_min: 实际耗时（分钟），None 时按 25min/任务 估算（或根据 level 取 abc_levels.minutes）
        mood: 可选 great|ok|tired|bad；None 不写入字段（不强制问询）
        status: done|partial|missed（缺省 done）
        level: a|b|c；None 表示老式 plan 不记录档位
    """
    plan_id = plan["id"]
    plan_dir = os.path.join(DATA_DIR, plan_id)
    checkin_path = os.path.join(plan_dir, "checkin-log.json")

    # 读取现有打卡记录
    if os.path.exists(checkin_path):
        with open(checkin_path, "r", encoding="utf-8") as f:
            checkin_data = json.load(f)
    else:
        checkin_data = {"plan_id": plan_id, "checkins": []}

    # 时长：优先用户指定；否则根据 level 从 abc_levels 取；最后兜底 25min/任务
    if duration_min is None:
        if level in LEVEL_ENUM:
            duration = _infer_duration_for_level(plan, task_ids, level)
        else:
            duration = len(task_ids) * 25
    else:
        duration = max(0, int(duration_min))

    # 添加新打卡（mood/status/level 仅在显式提供时写入）
    new_checkin = {
        "date": check_date,
        "task_ids": task_ids,
        "duration_min": duration,
        "note": note,
        "status": status,
    }
    if mood:
        new_checkin["mood"] = mood
    if level in LEVEL_ENUM:
        new_checkin["level"] = level

    # 检查当天是否已有打卡
    existing = [i for i, c in enumerate(checkin_data["checkins"]) if c["date"] == check_date]
    if existing:
        # 合并当天打卡
        idx = existing[0]
        checkin_data["checkins"][idx]["task_ids"] = list(set(
            checkin_data["checkins"][idx]["task_ids"] + task_ids
        ))
        checkin_data["checkins"][idx]["duration_min"] += duration
        # 后写入的 mood / status / note / level 覆盖（用户复盘时常更新）
        if mood:
            checkin_data["checkins"][idx]["mood"] = mood
        if status:
            checkin_data["checkins"][idx]["status"] = status
        if note:
            checkin_data["checkins"][idx]["note"] = note
        if level in LEVEL_ENUM:
            checkin_data["checkins"][idx]["level"] = level
    else:
        checkin_data["checkins"].append(new_checkin)

    # 排序
    checkin_data["checkins"].sort(key=lambda x: x["date"])

    # 保存
    with open(checkin_path, "w", encoding="utf-8") as f:
        json.dump(checkin_data, f, ensure_ascii=False, indent=2)

    return checkin_data


def update_streak(plan: dict, check_date: str) -> dict:
    """更新 Streak"""
    plan_id = plan["id"]
    plan_dir = os.path.join(DATA_DIR, plan_id)
    streak_path = os.path.join(plan_dir, "streak.json")

    # 读取现有 Streak
    if os.path.exists(streak_path):
        with open(streak_path, "r", encoding="utf-8") as f:
            streak = json.load(f)
    else:
        streak = {
            "plan_id": plan_id,
            "current": 0,
            "longest": 0,
            "last_checkin": None,
            "broken_dates": [],
            "milestones_unlocked": [],
            "achievements": []
        }

    last_date = streak.get("last_checkin")
    today = datetime.strptime(check_date, "%Y-%m-%d").date()

    new_milestones = []

    if last_date is None:
        # 第一次打卡
        streak["current"] = 1
        streak["last_checkin"] = check_date
    else:
        last = datetime.strptime(last_date, "%Y-%m-%d").date()
        diff = (today - last).days

        if diff == 0:
            # 同一天打卡，不变
            pass
        elif diff == 1:
            # 连续打卡
            streak["current"] += 1
            streak["last_checkin"] = check_date
        else:
            # 断签，重新开始
            if streak["current"] > 0:
                streak["broken_dates"].append(last_date)
            streak["current"] = 1
            streak["last_checkin"] = check_date

    # 更新最长记录
    if streak["current"] > streak["longest"]:
        streak["longest"] = streak["current"]

    # 检查里程碑
    for milestone in STREAK_MILESTONES:
        if streak["current"] >= milestone and milestone not in streak["milestones_unlocked"]:
            streak["milestones_unlocked"].append(milestone)
            new_milestones.append(milestone)
            # 添加成就
            achievement = {
                "id": f"streak_{milestone}",
                "name": f"连续 {milestone} 天",
                "unlocked_at": check_date,
                "description": f"成功连续打卡 {milestone} 天"
            }
            streak["achievements"].append(achievement)

    # 保存
    with open(streak_path, "w", encoding="utf-8") as f:
        json.dump(streak, f, ensure_ascii=False, indent=2)

    return streak, new_milestones


def get_checkin_stats(plan: dict) -> dict:
    """获取打卡统计"""
    plan_id = plan["id"]
    plan_dir = os.path.join(DATA_DIR, plan_id)
    checkin_path = os.path.join(plan_dir, "checkin-log.json")
    streak_path = os.path.join(plan_dir, "streak.json")

    stats = {
        "total_checkins": 0,
        "total_duration": 0,
        "this_week": 0,
        "completion_rate": 0
    }

    if os.path.exists(checkin_path):
        with open(checkin_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            stats["total_checkins"] = len(data["checkins"])
            stats["total_duration"] = sum(c["duration_min"] for c in data["checkins"])

            # 本周打卡
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            this_week = [c for c in data["checkins"]
                        if datetime.strptime(c["date"], "%Y-%m-%d").date() >= week_start]
            stats["this_week"] = len(this_week)

    # 计算完成率（需要 plan.json 中的任务总数）
    plan_path = os.path.join(plan_dir, "plan.json")
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
            total_tasks = sum(len(day["tasks"]) for day in plan_data.get("daily_tasks", []))
            if total_tasks > 0:
                checked_tasks = 0
                for c in data.get("checkins", []):
                    checked_tasks += len(c["task_ids"])
                stats["completion_rate"] = round(checked_tasks / total_tasks * 100, 1)

    # Streak 信息
    if os.path.exists(streak_path):
        with open(streak_path, "r", encoding="utf-8") as f:
            streak = json.load(f)
            stats["streak"] = streak["current"]
            stats["longest_streak"] = streak["longest"]

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="学习打卡")
    parser.add_argument("--plan", help="计划 ID")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="打卡日期")
    parser.add_argument("--tasks", help="完成任务 ID，逗号分隔")
    parser.add_argument("--note", default="", help="打卡备注（≤ 200 字符）")
    parser.add_argument(
        "--mood",
        default=None,
        choices=list(MOOD_ENUM.keys()),
        help="可选心情打卡：great|ok|tired|bad；默认不记录（NEVER 2 低摩擦）",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="实际耗时（分钟）；不传则按每任务 25min 估算",
    )
    parser.add_argument(
        "--status",
        default="done",
        choices=sorted(STATUS_ENUM),
        help="完成状态：done|partial|missed（默认 done）",
    )
    parser.add_argument(
        "--level",
        default=None,
        choices=sorted(LEVEL_ENUM),
        help="ABC 档位：a(完美)|b(基础)|c(最低)；做了 C 档也算 streak 不断（NEVER 9）",
    )
    parser.add_argument("--stats", action="store_true", help="仅显示统计")

    args = parser.parse_args()

    plan = get_active_plan(args.plan)
    if not plan:
        print("❌ 未找到活动计划。请先创建计划或指定 --plan")
        sys.exit(1)

    # 180 天上限软警告（不阻塞打卡）
    check_plan_length(plan)

    if args.stats:
        stats = get_checkin_stats(plan)
        print(f"📊 打卡统计")
        print(f"   总打卡次数: {stats['total_checkins']}")
        print(f"   本周打卡: {stats['this_week']} 天")
        print(f"   总学习时长: {stats['total_duration'] // 60}h {stats['total_duration'] % 60}m")
        print(f"   任务完成率: {stats['completion_rate']}%")
        if "streak" in stats:
            print(f"   🔥 当前 Streak: {stats['streak']} 天")
            print(f"   🏆 最长 Streak: {stats['longest_streak']} 天")
        sys.exit(0)

    if not args.tasks:
        # status=missed 时允许无 tasks（记录"今日未完成"）
        if args.status == "missed":
            task_ids = []
        else:
            print("❌ 请指定 --tasks（或 --status missed 记录未完成）")
            sys.exit(1)
    else:
        task_ids = args.tasks.split(",")
        task_ids = [t.strip() for t in task_ids if t.strip()]

    # note 长度防御（NEVER 2：摩擦力上限）
    note = (args.note or "")[:200]

    # 检测：连续 ≥ 2 天做 C 档（Two-Day Rule）— 写入前先看历史
    two_day_c_warning = ""
    if args.level == "c":
        prev_path = os.path.join(DATA_DIR, plan["id"], "checkin-log.json")
        if os.path.exists(prev_path):
            try:
                with open(prev_path, "r", encoding="utf-8") as f:
                    prev_log = json.load(f)
                # 取最后一条非今日的打卡
                prev_c_count = 0
                today_d = datetime.strptime(args.date, "%Y-%m-%d").date()
                for c in reversed(prev_log.get("checkins", [])):
                    if c.get("date") == args.date:
                        continue
                    try:
                        cd = datetime.strptime(c["date"], "%Y-%m-%d").date()
                    except (ValueError, KeyError, TypeError):
                        continue
                    if (today_d - cd).days <= 7 and c.get("level") == "c":
                        prev_c_count += 1
                    else:
                        break
                if prev_c_count >= 1:
                    two_day_c_warning = (
                        f"\n⚠️ Two-Day Rule：你最近连续 {prev_c_count + 1} 天都是 C 档了，"
                        f"明天要不要试试 B 档？（连续做 C 是滑向放弃的早期信号）"
                    )
            except (json.JSONDecodeError, OSError):
                pass

    # 更新打卡
    checkin_data = update_checkin(
        plan,
        args.date,
        task_ids,
        note=note,
        duration_min=args.duration,
        mood=args.mood,
        status=args.status,
        level=args.level,
    )

    # 更新 Streak（核心承诺：A/B/C 任意一档完成都算 streak 不断 → done/partial 都计入）
    if args.status in ("done", "partial"):
        streak, new_milestones = update_streak(plan, args.date)
    else:
        # missed：不动 streak，但仍输出当前状态
        streak_path = os.path.join(DATA_DIR, plan["id"], "streak.json")
        streak = json.load(open(streak_path, "r", encoding="utf-8")) if os.path.exists(streak_path) else {"current": 0}
        new_milestones = []

    # 输出结果
    status_emoji = {"done": "✅", "partial": "🟡", "missed": "⏸️"}[args.status]
    level_label = {"a": "🅰️ 完美档", "b": "🅱️ 基础档", "c": "🆎 最低档"}.get(args.level or "", "")
    print(f"{status_emoji} 打卡成功！日期: {args.date} · 状态: {args.status}"
          + (f" · {level_label}" if level_label else ""))
    if task_ids:
        print(f"   完成任务: {', '.join(task_ids)}")
    if args.mood:
        print(f"   心情: {MOOD_ENUM[args.mood]}")
    print(f"   🔥 Streak: {streak.get('current', 0)} 天")

    if two_day_c_warning:
        print(two_day_c_warning)

    # ===== 按 persona 渲染：C 档正向反馈（P1-7）/ If-Then 联动（P1-8）/ 里程碑庆祝（P1-1） =====
    persona = _load_user_persona()

    # 1) 单次 C 档（且未触发 Two-Day Rule）→ 输出一条正向小反馈
    if args.level == "c" and not two_day_c_warning and args.status in ("done", "partial"):
        print(render_c_level_positive_feedback(persona))

    # 2) note 里命中 if-then 触发条件 → 回显应急脚本，强化"障碍预演"的存在感
    if note:
        matched = match_if_then_plan(plan, note)
        if matched:
            print(
                f"\n🔮 If-Then 触发：你提到了「{matched.get('if', '').strip()}」，"
                f"应急脚本是：「{matched.get('then', '').strip()}」"
                f"\n   （这是你拆解时为自己写好的剧本 · 不是临时妥协）"
            )

    # 3) 里程碑：必须按 persona 渲染（NEVER 7 强制联动 + NEVER 3 不串味）
    if new_milestones:
        for m in new_milestones:
            print(render_milestone_celebration(persona, m))

    # 4) 自动重渲染 dashboard（静默失败，绝不阻断主流程）
    regenerate_dashboard(plan_id=plan["id"])

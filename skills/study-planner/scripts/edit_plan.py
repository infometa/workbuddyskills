#!/usr/bin/env python3
"""
edit_plan.py - 编辑/调整已有学习计划

支持的操作：
  - add-task        在某日新增任务
  - remove-task     删除某任务
  - move-task       把任务移到另一天
  - postpone        整体延后 N 天（含未完成任务）
  - update-meta     修改 meta 字段（goal / deadline / daily_budget 等）
  - shrink          压缩计划（删除已完成日，剩余任务重新分布）
  - extend          延长计划（在末尾追加 N 天 review）
  - show            打印当前计划摘要

每次修改 version 自增 1，原文件备份到 plan.v{N}.bak.json

用法：
  python3 edit_plan.py show <plan-id>
  python3 edit_plan.py add-task <plan-id> --date 2026-04-15 \\
      --title "听力精听 ×2 篇" --duration 50 --category listening
  python3 edit_plan.py remove-task <plan-id> --task-id t-005
  python3 edit_plan.py move-task <plan-id> --task-id t-005 --to-date 2026-04-16
  python3 edit_plan.py postpone <plan-id> --days 3
  python3 edit_plan.py update-meta <plan-id> --field deadline --value 2026-05-01

依赖：
  - Python 3.8+，仅标准库（json, pathlib, argparse, datetime, copy）
  - 零网络调用、零三方包

输入：
  - 子命令 + plan-id（必须存在于 <cwd>/study-planner/study-plans/）
  - 各子命令参数见上文

输出：
  - 修改后的 plan.json（version 自增 +1）
  - 备份 plan.v{N}.bak.json（不限保留份数；用户可手动清理）
  - stdout 打印 diff 摘要（新增/删除/移动几条任务）

性能上限：
  - 单次操作 < 100ms（即使 365 天 / 1000+ 任务）
  - 内存峰值 < 20MB（一次性载入 plan + 写入 backup）

错误模式（exit code）：
  - 0  成功
  - 1  plan-id 不存在 → 列出最近 5 个 plan
  - 2  task-id 不存在 → 提示用 show 子命令查看
  - 3  日期格式错误 / 超出 plan 起止范围 → 提示合法区间
  - 4  postpone 后超过 deadline → 强制提醒用户先 update-meta
  - 5  备份失败 → 中止本次修改，保持原文件不变（事务性）

数据安全：
  - 严禁覆盖式重写（详见 SKILL.md NEVER 5）
  - 所有变更走自增 version + .bak 文件，user_companion 端 Streak 不丢失
"""

import json
import os
import sys
import argparse
import shutil
from datetime import datetime, timedelta


def _resolve_data_dir() -> str:
    """数据目录解析。优先级：STUDY_PLANNER_DATA_DIR env > <cwd>/study-planner/study-plans/"""
    env = os.environ.get("STUDY_PLANNER_DATA_DIR")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.abspath(os.path.join(os.getcwd(), "study-planner", "study-plans"))


DATA_DIR = _resolve_data_dir()

# NEVER 4：单任务时长上限（pomodoro 友好），超过则自动拆分子任务
MAX_TASK_MIN = 45

# 默认 methodology_tip 池，category 没匹配上时兜底，保证 NEVER 7 不出现空字段
DEFAULT_METHOD_TIPS = {
    "listening":  "艾宾浩斯：精听段落第 1/3/7 天各重听一次（不看原文）",
    "reading":    "帕累托：高频题型优先（判断/填空），20% 考点拿 80% 分",
    "writing":    "费曼法：写完读给自己听，能 5 分钟讲明白论点再交卷",
    "speaking":   "费曼法：录音回放，标记卡顿点，用更简单的词替换",
    "vocabulary": "艾宾浩斯：1/3/7/15 天复现 5 次后进入长期记忆",
    "grammar":    "番茄：单次 ≤45min，错题立刻造 3 个新例句",
    "review":     "艾宾浩斯：错题第 1/3/7 天复现，能 1 分钟讲明白才算过",
    "exam":       "限时模考：严格计时，做完立即对答案，错题 24h 内复盘",
    "output":     "费曼法：不写就不算学过——产出可以是文章/代码/讲解视频",
    "rest":       "主动休息：散步/远眺/换脑，禁止刷短视频",
}


def _split_duration(total: int, max_each: int = MAX_TASK_MIN) -> list:
    """把 total 分钟拆成每段 ≤ max_each（NEVER 4）。
    余数 < 5 时合并到上一段，避免出现 1-3 min 的碎片。
    """
    if total <= max_each:
        return [total]
    chunks = []
    remaining = total
    while remaining > max_each:
        chunks.append(max_each)
        remaining -= max_each
    if remaining < 5 and chunks:
        chunks[-1] += remaining
    elif remaining > 0:
        chunks.append(remaining)
    return chunks


def plan_path(plan_id: str) -> str:
    return os.path.join(DATA_DIR, plan_id, "plan.json")


def load_plan(plan_id: str) -> dict:
    p = plan_path(plan_id)
    if not os.path.exists(p):
        raise FileNotFoundError(f"找不到计划: {plan_id}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plan(plan: dict, plan_id: str, backup: bool = True):
    p = plan_path(plan_id)
    if backup and os.path.exists(p):
        bak = os.path.join(DATA_DIR, plan_id, f"plan.v{plan['version']}.bak.json")
        shutil.copy2(p, bak)
    plan["version"] = plan.get("version", 1) + 1
    with open(p, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)


def next_task_id(plan: dict) -> str:
    """生成下一个 t-NNN 编号"""
    max_n = 0
    for daily in plan.get("daily_tasks", []):
        for task in daily.get("tasks", []):
            tid = task.get("id", "")
            if tid.startswith("t-") and tid[2:].isdigit():
                max_n = max(max_n, int(tid[2:]))
    return f"t-{max_n + 1:03d}"


def find_or_create_day(plan: dict, date: str) -> dict:
    """查找日期对应的 daily 块，没有则创建并按日期插入"""
    for daily in plan["daily_tasks"]:
        if daily["date"] == date:
            return daily
    # 推断 stage_id
    stage_id = plan["stages"][0]["id"] if plan.get("stages") else "stage-1"
    new_daily = {"date": date, "stage_id": stage_id, "tasks": []}
    plan["daily_tasks"].append(new_daily)
    plan["daily_tasks"].sort(key=lambda d: d["date"])
    return new_daily


# ──────────────────────────────────────────────
# 操作
# ──────────────────────────────────────────────
def op_show(plan_id: str):
    plan = load_plan(plan_id)
    meta = plan["meta"]
    print(f"\n📋 {meta['title']} ({plan['id']})")
    print(f"   版本：v{plan['version']}    截止：{meta['deadline']}    模板：{meta.get('template_origin', '?')}")
    print(f"   目标：{meta.get('goal', '-')}")
    print(f"   现状：{meta.get('current_level', '-')}")
    print(f"   日预算：工作日 {meta['daily_budget']['weekday']}min / 周末 {meta['daily_budget']['weekend']}min")

    print(f"\n   阶段（{len(plan['stages'])}）：")
    for s in plan["stages"]:
        print(f"     • {s['name']}（{s['duration_days']}天）")

    daily_tasks = plan.get("daily_tasks", [])
    total_tasks = sum(len(d["tasks"]) for d in daily_tasks)
    print(f"\n   任务：{len(daily_tasks)} 个学习日，共 {total_tasks} 个任务")
    if daily_tasks:
        print(f"   最早：{daily_tasks[0]['date']}    最晚：{daily_tasks[-1]['date']}")
    print()


def op_add_task(plan_id: str, date: str, title: str, duration: int,
                category: str, priority: str = "medium",
                resource: str = "", tip: str = ""):
    """新增任务。
    - NEVER 4：duration > MAX_TASK_MIN 时自动拆成多段子任务（part X/Y）
    - 下游打卡硬契约：每个任务必须含 checkable=true
    - NEVER 7：methodology_tip 不能为空，未指定时按 category 补齐
    """
    plan = load_plan(plan_id)
    daily = find_or_create_day(plan, date)

    # 拆分时长
    chunks = _split_duration(duration)
    base_id = next_task_id(plan)
    base_n = int(base_id[2:])
    final_tip = tip or DEFAULT_METHOD_TIPS.get(category, "番茄：专注 ≤45min，结束后强制起身 5 min")

    new_tasks = []
    for j, dur in enumerate(chunks):
        if len(chunks) == 1:
            tid = base_id
            ttitle = title
        else:
            tid = f"t-{base_n:03d}" if j == 0 else f"t-{base_n:03d}-p{j+1}"
            ttitle = f"{title} (part {j+1}/{len(chunks)})"
        task = {
            "id": tid,
            "title": ttitle,
            "duration_min": dur,
            "category": category,
            "priority": priority,
            "checkable": True,            # 下游打卡渲染 [ ] 复选框依赖此字段
            "methodology_tip": final_tip,  # NEVER 7
            "_origin": "custom",           # rebalance 不会改自定义任务时长
        }
        if resource:
            task["resource"] = resource
        daily["tasks"].append(task)
        new_tasks.append(tid)

    save_plan(plan, plan_id)
    if len(chunks) == 1:
        print(f"✅ 已添加任务 {new_tasks[0]} 到 {date}")
    else:
        print(f"✅ 已添加任务 {new_tasks[0]} 到 {date}（按 NEVER 4 自动拆成 {len(chunks)} 段子任务: {', '.join(new_tasks)}）")


def op_remove_task(plan_id: str, task_id: str):
    plan = load_plan(plan_id)
    removed = False
    for daily in plan["daily_tasks"]:
        before = len(daily["tasks"])
        daily["tasks"] = [t for t in daily["tasks"] if t["id"] != task_id]
        if len(daily["tasks"]) < before:
            removed = True
    # 清理空 daily
    plan["daily_tasks"] = [d for d in plan["daily_tasks"] if d["tasks"]]
    if not removed:
        print(f"⚠️  未找到任务 {task_id}")
        return
    save_plan(plan, plan_id)
    print(f"✅ 已删除任务 {task_id}")


def op_move_task(plan_id: str, task_id: str, to_date: str):
    plan = load_plan(plan_id)
    moved_task = None
    for daily in plan["daily_tasks"]:
        for t in daily["tasks"]:
            if t["id"] == task_id:
                moved_task = t
                daily["tasks"].remove(t)
                break
        if moved_task:
            break
    if not moved_task:
        print(f"⚠️  未找到任务 {task_id}")
        return
    plan["daily_tasks"] = [d for d in plan["daily_tasks"] if d["tasks"]]
    target = find_or_create_day(plan, to_date)
    target["tasks"].append(moved_task)
    save_plan(plan, plan_id)
    print(f"✅ 任务 {task_id} 已移到 {to_date}")


def op_postpone(plan_id: str, days: int):
    """整体延后：所有未来日期 +days，deadline +days"""
    plan = load_plan(plan_id)
    today = datetime.now().date()
    for daily in plan["daily_tasks"]:
        d = datetime.strptime(daily["date"], "%Y-%m-%d").date()
        if d >= today:
            daily["date"] = (d + timedelta(days=days)).strftime("%Y-%m-%d")
    old_deadline = datetime.strptime(plan["meta"]["deadline"], "%Y-%m-%d").date()
    plan["meta"]["deadline"] = (old_deadline + timedelta(days=days)).strftime("%Y-%m-%d")
    save_plan(plan, plan_id)
    print(f"✅ 已整体延后 {days} 天，新截止：{plan['meta']['deadline']}")


def op_update_meta(plan_id: str, field: str, value: str):
    plan = load_plan(plan_id)
    # 支持嵌套：daily_budget.weekday
    if "." in field:
        parts = field.split(".")
        cur = plan["meta"]
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        # 数字字段尝试转换
        try:
            cur[parts[-1]] = int(value)
        except ValueError:
            cur[parts[-1]] = value
    else:
        plan["meta"][field] = value
    save_plan(plan, plan_id)
    print(f"✅ meta.{field} 已更新为 {value}")

    # 改了 daily_budget 时，提示用户跑 rebalance（不自动跑——副作用太大，会覆盖用户已手改的任务）
    if field.startswith("daily_budget"):
        print(f"\n⚠️  你修改了 daily_budget，但已有任务的 duration_min 未自动重排。")
        print(f"   如需让未来日期的任务时长贴近新预算，请运行：")
        print(f"     python3 edit_plan.py rebalance {plan_id}")
        print(f"   （rebalance 仅调整骨架任务时长，保留你手动加的自定义任务）")


def _is_skeleton_task(task: dict) -> bool:
    """判断是否为 init 时生成的骨架任务（id 形如 t-NNN 或 t-NNN-pX，且无自定义 resource）。
    rebalance 只动骨架任务，不碰用户后续 add-task 加进来的自定义任务。
    判据：title 不以「自定义:」开头 + category 在标准集合里。
    后续可在 init 时给骨架任务打 _origin: "skeleton" 标记，更精确。
    """
    # 兜底标记法：rebalance 会给重排过的任务打 _rebalanced=true，避免重复影响
    return task.get("_origin", "skeleton") == "skeleton"


def op_rebalance(plan_id: str, dry_run: bool = False):
    """根据当前 meta.daily_budget 重新分配未来日期的骨架任务时长。

    安全策略：
      - 只处理 today 起未来日期（已过去的不动，保持打卡历史一致）
      - 跳过 meta.blocked_weekdays（用户已声明不学的日子保持空）
      - 单任务时长上限 MAX_TASK_MIN（NEVER 4），超过则按 _split_duration 拆成多段
      - 仅按比例缩放骨架任务（_origin=skeleton 或缺省视为骨架），保留用户自定义任务
      - 当用户自定义任务时长已 ≥ 当日预算时，骨架任务全部置为最小 20min（不再压缩到 0）

    Args:
        plan_id: 计划 ID
        dry_run: 仅展示调整范围，不写盘
    """
    plan = load_plan(plan_id)
    today = datetime.now().date()
    budget = plan["meta"].get("daily_budget", {"weekday": 90, "weekend": 180})
    blocked = set(plan["meta"].get("blocked_weekdays", []))

    affected = []     # [(date, old_total, new_total, n_tasks)]
    skipped_blocked = 0
    underfilled = []  # 当 budget > 骨架任务最大容量时（45 * N），提示用户手动加任务

    for daily in plan["daily_tasks"]:
        d = datetime.strptime(daily["date"], "%Y-%m-%d").date()
        if d < today:
            continue
        if d.weekday() in blocked:
            # 屏蔽日：不应有任务，若有（异常状态）也不在 rebalance 处理范围
            if daily.get("tasks"):
                skipped_blocked += 1
            continue

        is_weekend = d.weekday() >= 5
        day_budget = budget.get("weekend" if is_weekend else "weekday", 90)

        skeleton_tasks = [t for t in daily["tasks"] if _is_skeleton_task(t)]
        custom_tasks = [t for t in daily["tasks"] if not _is_skeleton_task(t)]

        if not skeleton_tasks:
            # 全是用户自定义，不动
            continue

        custom_total = sum(t.get("duration_min", 0) for t in custom_tasks)
        old_skel_total = sum(t.get("duration_min", 0) for t in skeleton_tasks)

        # 留给骨架任务的预算（不能 < 20min，避免压缩成无意义碎片）
        skel_budget = max(20 * len(skeleton_tasks), day_budget - custom_total)
        per_skel = max(20, min(MAX_TASK_MIN, skel_budget // len(skeleton_tasks)))

        # NEVER 4 截断检测：单任务被卡到 MAX_TASK_MIN 但实际预算还有富余
        ideal_total_skel = day_budget - custom_total
        actual_total_skel = per_skel * len(skeleton_tasks)
        if ideal_total_skel - actual_total_skel >= 30:  # 至少差 30min 才提示
            underfilled.append((daily["date"], actual_total_skel, ideal_total_skel))

        if old_skel_total == actual_total_skel:
            continue  # 完全没变

        if not dry_run:
            for t in skeleton_tasks:
                t["duration_min"] = per_skel
                # 标记已重排，下次 rebalance 仍可继续处理
                t["_origin"] = "skeleton"

        new_total = actual_total_skel + custom_total
        affected.append((daily["date"], old_skel_total + custom_total, new_total, len(skeleton_tasks)))

    prefix = "📋 [DRY-RUN]" if dry_run else "✅"
    if not affected:
        print(f"{prefix} 无需重排：所有未来日期的骨架任务时长已与 daily_budget 一致。")
        if skipped_blocked:
            print(f"   （另有 {skipped_blocked} 天属屏蔽日，跳过）")
        return

    print(f"{prefix} 已重排 {len(affected)} 天的骨架任务（工作日 {budget.get('weekday')}min / 周末 {budget.get('weekend')}min）：")
    for date, old, new, n in affected[:10]:
        print(f"   • {date}  {old} → {new} min（骨架任务 ×{n}）")
    if len(affected) > 10:
        print(f"   ...（共 {len(affected)} 天，仅展示前 10 条）")
    if skipped_blocked:
        print(f"   ℹ️  跳过 {skipped_blocked} 个屏蔽日上的残留任务（应通过 block-weekday 处理）")

    if underfilled:
        # 单任务被 MAX_TASK_MIN(45) 截断时，提示用户加任务而非加时长
        print(f"\n⚠️  有 {len(underfilled)} 天因单任务上限 {MAX_TASK_MIN}min（NEVER 4）未填满预算，建议 add-task 补足：")
        for date, actual, ideal in underfilled[:3]:
            print(f"   • {date}：实际 {actual}min，预算 {ideal}min（差 {ideal-actual}min）")
        if len(underfilled) > 3:
            print(f"   ...（共 {len(underfilled)} 天）")

    if not dry_run:
        save_plan(plan, plan_id)


def op_extend(plan_id: str, days: int):
    """在 deadline 后追加 N 天 review 缓冲"""
    plan = load_plan(plan_id)
    deadline = datetime.strptime(plan["meta"]["deadline"], "%Y-%m-%d").date()
    last_stage_id = plan["stages"][-1]["id"] if plan["stages"] else "stage-1"
    for i in range(1, days + 1):
        new_date = (deadline + timedelta(days=i)).strftime("%Y-%m-%d")
        plan["daily_tasks"].append({
            "date": new_date,
            "stage_id": last_stage_id,
            "tasks": [{
                "id": next_task_id(plan),
                "title": f"缓冲日 {i}：错题 review + 薄弱补漏",
                "duration_min": 45,
                "category": "review",
                "priority": "medium",
                "checkable": True,
                "methodology_tip": "延期缓冲，主动降负，保持手感（艾宾浩斯：精选 3 道错题深挖根因）"
            }]
        })
    plan["meta"]["deadline"] = (deadline + timedelta(days=days)).strftime("%Y-%m-%d")
    save_plan(plan, plan_id)
    print(f"✅ 已延长 {days} 天 review 缓冲，新截止：{plan['meta']['deadline']}")


# ──────────────────────────────────────────────
# block-weekday：把指定周几的所有未来任务挪到下一个非屏蔽日
# 适用场景：用户说「周三我有课」/「周末不想学」
#
# weekday 取值：0=Mon, 1=Tue, ..., 6=Sun（与 datetime.weekday() 一致）
# 也可以用别名："mon","tue","wed","thu","fri","sat","sun","weekend"
#
# 行为：
#   - 仅处理 today 起未来的日期（已过去的不动，避免破坏打卡历史）
#   - 把目标日的所有任务，按顺序追加到下一个「未被屏蔽」的日子
#   - 如果连续多日都被屏蔽（如同时 block sat+sun），向后顺延找到首个空闲日
#   - 同步更新 meta.blocked_weekdays（持久化用户偏好，下游打卡可读）
# ──────────────────────────────────────────────
_WEEKDAY_ALIAS = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6, "周天": 6,
}


def _parse_weekdays(weekdays_arg: str) -> set:
    """解析 --weekday 参数，支持 '2'、'wed'、'2,5'、'weekend' 等。
    返回 {0..6} 子集。
    """
    result = set()
    for token in str(weekdays_arg).split(","):
        token = token.strip().lower()
        if not token:
            continue
        if token == "weekend":
            result |= {5, 6}
            continue
        if token == "weekday":
            result |= {0, 1, 2, 3, 4}
            continue
        if token in _WEEKDAY_ALIAS:
            result.add(_WEEKDAY_ALIAS[token])
            continue
        try:
            n = int(token)
        except ValueError:
            raise ValueError(f"无法解析 weekday: {token}（用 0-6 或 mon/tue/.../sun/weekend）")
        if not 0 <= n <= 6:
            raise ValueError(f"weekday 必须在 0-6 之间（当前 {n}）")
        result.add(n)
    if not result:
        raise ValueError("未指定任何 weekday")
    return result


def op_block_weekday(plan_id: str, weekdays_arg: str, dry_run: bool = False):
    """把指定周几的未来任务全部挪到下一个非屏蔽日。

    Args:
        plan_id: 计划 ID
        weekdays_arg: '2' / 'wed' / '2,5' / 'weekend' 等
        dry_run: 仅打印影响范围，不写盘
    """
    blocked = _parse_weekdays(weekdays_arg)
    plan = load_plan(plan_id)
    today = datetime.now().date()

    # 1) 收集需要挪走的 daily 块（today 起的未来日期，且 weekday 在 blocked 集合中）
    to_relocate = []  # [(date_obj, daily_block), ...]
    for daily in plan["daily_tasks"]:
        d = datetime.strptime(daily["date"], "%Y-%m-%d").date()
        if d >= today and d.weekday() in blocked and daily.get("tasks"):
            to_relocate.append((d, daily))

    if not to_relocate:
        weekday_names = ",".join(sorted(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][w] for w in blocked))
        print(f"ℹ️  未来日期中没有 {weekday_names} 的待办任务，无需调整")
        return

    # 2) 对每个待挪走的 daily，找到「下一个非屏蔽日」
    deadline = datetime.strptime(plan["meta"]["deadline"], "%Y-%m-%d").date()
    moved_count = 0
    affected_days = []
    for src_date, src_daily in to_relocate:
        # 从 src_date+1 开始找
        target_date = src_date + timedelta(days=1)
        while target_date.weekday() in blocked:
            target_date += timedelta(days=1)
            if target_date > deadline + timedelta(days=30):
                # 防止 7 天全 block 时无限循环（虽然这不合理）
                raise ValueError(f"无法为 {src_date} 找到非屏蔽日（屏蔽天数过多）")

        target_str = target_date.strftime("%Y-%m-%d")
        if dry_run:
            affected_days.append((src_daily["date"], target_str, len(src_daily["tasks"])))
            continue

        # 实际挪动
        target_daily = find_or_create_day(plan, target_str)
        target_daily["tasks"].extend(src_daily["tasks"])
        moved_count += len(src_daily["tasks"])
        affected_days.append((src_daily["date"], target_str, len(src_daily["tasks"])))
        src_daily["tasks"] = []

    # 3) 清理空 daily 块
    plan["daily_tasks"] = [d for d in plan["daily_tasks"] if d.get("tasks")]

    # 4) 持久化用户偏好到 meta（下游打卡后续可读取，避免重新生成时又填回去）
    if not dry_run:
        existing = set(plan["meta"].get("blocked_weekdays", []))
        plan["meta"]["blocked_weekdays"] = sorted(existing | blocked)
        save_plan(plan, plan_id)

    # 5) 输出摘要
    weekday_names = ",".join(sorted(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][w] for w in blocked))
    prefix = "📋 [DRY-RUN]" if dry_run else "✅"
    print(f"{prefix} 已屏蔽 {weekday_names}，影响 {len(affected_days)} 天，{moved_count or sum(c for _,_,c in affected_days)} 个任务被挪动：")
    for src, dst, n in affected_days[:10]:
        print(f"   • {src} → {dst}（{n} 个任务）")
    if len(affected_days) > 10:
        print(f"   ...（共 {len(affected_days)} 天，仅展示前 10 条）")
    if not dry_run:
        print(f"   meta.blocked_weekdays = {plan['meta']['blocked_weekdays']}")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="编辑学习计划")
    sub = parser.add_subparsers(dest="op", required=True)

    sub.add_parser("show").add_argument("plan_id")

    p_add = sub.add_parser("add-task")
    p_add.add_argument("plan_id")
    p_add.add_argument("--date", required=True)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--duration", type=int, required=True)
    p_add.add_argument("--category", required=True,
                       choices=["listening", "reading", "writing", "speaking",
                                "vocabulary", "grammar", "review", "exam", "output", "rest"])
    p_add.add_argument("--priority", default="medium", choices=["high", "medium", "low"])
    p_add.add_argument("--resource", default="")
    p_add.add_argument("--tip", default="")

    p_rm = sub.add_parser("remove-task")
    p_rm.add_argument("plan_id")
    p_rm.add_argument("--task-id", required=True)

    p_mv = sub.add_parser("move-task")
    p_mv.add_argument("plan_id")
    p_mv.add_argument("--task-id", required=True)
    p_mv.add_argument("--to-date", required=True)

    p_pp = sub.add_parser("postpone")
    p_pp.add_argument("plan_id")
    p_pp.add_argument("--days", type=int, required=True)

    p_um = sub.add_parser("update-meta")
    p_um.add_argument("plan_id")
    p_um.add_argument("--field", required=True, help="如 goal / deadline / daily_budget.weekday")
    p_um.add_argument("--value", required=True)

    p_ex = sub.add_parser("extend")
    p_ex.add_argument("plan_id")
    p_ex.add_argument("--days", type=int, required=True)

    p_bw = sub.add_parser("block-weekday",
                          help="把指定周几的未来任务批量挪到下一个非屏蔽日（如『周三有课』『周末不想学』）")
    p_bw.add_argument("plan_id")
    p_bw.add_argument("--weekday", required=True,
                      help="0-6 / mon-sun / weekend / weekday，可逗号分隔，如 '2'、'wed'、'2,5'、'weekend'")
    p_bw.add_argument("--dry-run", action="store_true", help="仅展示影响范围，不写盘")

    p_rb = sub.add_parser("rebalance",
                          help="按当前 meta.daily_budget 重排未来日期的骨架任务时长（保留自定义任务）")
    p_rb.add_argument("plan_id")
    p_rb.add_argument("--dry-run", action="store_true", help="仅展示调整范围，不写盘")

    args = parser.parse_args()

    try:
        if args.op == "show":
            op_show(args.plan_id)
        elif args.op == "add-task":
            op_add_task(args.plan_id, args.date, args.title, args.duration,
                        args.category, args.priority, args.resource, args.tip)
        elif args.op == "remove-task":
            op_remove_task(args.plan_id, args.task_id)
        elif args.op == "move-task":
            op_move_task(args.plan_id, args.task_id, args.to_date)
        elif args.op == "postpone":
            op_postpone(args.plan_id, args.days)
        elif args.op == "update-meta":
            op_update_meta(args.plan_id, args.field, args.value)
        elif args.op == "extend":
            op_extend(args.plan_id, args.days)
        elif args.op == "block-weekday":
            op_block_weekday(args.plan_id, args.weekday, dry_run=args.dry_run)
        elif args.op == "rebalance":
            op_rebalance(args.plan_id, dry_run=args.dry_run)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()

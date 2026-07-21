#!/usr/bin/env python3
"""
stats.py · 学习统计与周报/月报生成

用法：
  python3 stats.py weekly                       # 本周周报
  python3 stats.py monthly                      # 本月月报
  python3 stats.py weekly --plan PLAN_ID
  python3 stats.py weekly --week 2026-05-04     # 指定某周（周一日期）

依赖：
  - Python 3.8+，仅标准库（json, pathlib, argparse, datetime, statistics）
  - 零网络、零三方包

输入：
  - 子命令：weekly / monthly
  - --plan / --week / --month 可选

输出：
  - 周/月报 markdown 文本（≤ 30 行）
  - 必含字段：完成率 + 打卡天数 + 任务分类时长 + 弱日识别 + 改进建议
  - 文案严格按 persona 渲染（见 SKILL.md NEVER 3）

诚实度铁律（见 NEVER 8）：
  - 完成率如实显示百分比（不修饰、不四舍五入到好看数字）
  - 当完成率 < 60% 时，必须给出具体改进建议（不能只说"加油"）
  - 弱日识别：列出未打卡的具体星期几 + 推断原因（工作日 / 周末 / 节假日）
  - 不报喜不报忧——优点和不足同等篇幅

性能上限：
  - 周报 < 60ms / 月报 < 150ms

错误模式（exit code）：
  - 0  成功
  - 1  无 active plan
  - 2  指定周/月不在 plan 范围内 → 提示合法范围
  - 3  数据为空（首周还没打卡）→ 输出"建议下周一再看"，exit 0
"""

import json
import os
import sys
import argparse
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _plan_utils import (  # noqa: E402
    DATA_DIR,
    compute_bottleneck_tasks,
    persist_bottleneck_to_streak,
)

# DATA_DIR 由 _plan_utils 统一解析（兼容 GOAL_TRACKER_DATA_DIR + cwd）

# ---------- mood / 时段配置 ----------
MOOD_LABELS = {
    "great": "🌞 great",
    "ok":    "🙂 ok",
    "tired": "😪 tired",
    "bad":   "🌧️ bad",
}

# 时段划分（按 checkin.date 推断不准；改为按 plan.daily_tasks 内 task.duration 自然落点
# 但若 checkin-log 含 created_at 字段则用之。这里保守地按 weekday 维度即可，时段维度用
# checkin record 的 timeslot 字段（如有），缺失则降级到 weekday 维度）
TIMESLOTS = ["morning", "afternoon", "evening", "night"]
TIMESLOT_LABEL = {
    "morning": "早晨 (06-12)",
    "afternoon": "下午 (12-18)",
    "evening": "晚间 (18-22)",
    "night":   "深夜 (22-06)",
}


def _infer_timeslot_from_record(c: dict) -> str:
    """从 checkin record 中尽力推断时段：
    1) 显式 timeslot 字段
    2) created_at / checked_at HH:MM 字段
    3) None（不计入时段聚合）
    """
    ts = c.get("timeslot")
    if ts in TIMESLOTS:
        return ts
    for ts_key in ("created_at", "checked_at", "time"):
        s = c.get(ts_key)
        if isinstance(s, str):
            # 提取 HH
            for sep in ("T", " "):
                if sep in s:
                    s = s.split(sep, 1)[1]
                    break
            try:
                hour = int(s[:2])
                if 6 <= hour < 12:
                    return "morning"
                if 12 <= hour < 18:
                    return "afternoon"
                if 18 <= hour < 22:
                    return "evening"
                return "night"
            except (ValueError, IndexError):
                pass
    return None


def load_plan_data(plan_id: str = None):
    """加载 plan.json + checkin-log.json + streak.json"""
    if plan_id:
        plan_dir = os.path.join(DATA_DIR, plan_id)
    else:
        if not os.path.exists(DATA_DIR):
            print(f"[ERR] 数据目录不存在：{DATA_DIR}")
            sys.exit(1)
        plans = sorted(
            [p for p in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, p))],
            key=lambda p: os.path.getmtime(os.path.join(DATA_DIR, p, "plan.json"))
            if os.path.exists(os.path.join(DATA_DIR, p, "plan.json"))
            else 0,
            reverse=True,
        )
        if not plans:
            print("[ERR] 没有找到任何学习计划")
            sys.exit(1)
        plan_dir = os.path.join(DATA_DIR, plans[0])

    def safe_load(name, default):
        path = os.path.join(plan_dir, name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default

    plan = safe_load("plan.json", None)
    if plan is None:
        print(f"[ERR] {plan_dir} 中没有 plan.json")
        sys.exit(1)

    checkin = safe_load("checkin-log.json", {"checkins": []})
    streak = safe_load("streak.json", {"current": 0, "longest": 0})
    user_cfg = safe_load("user-config.json", {"persona": "gentle-senior"})

    return plan, checkin, streak, user_cfg, plan_dir


def get_week_range(ref_date: date = None):
    """返回本周一 ~ 本周日的日期范围"""
    today = ref_date or date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_month_range(ref_date: date = None):
    today = ref_date or date.today()
    first = today.replace(day=1)
    if first.month == 12:
        next_month = first.replace(year=first.year + 1, month=1)
    else:
        next_month = first.replace(month=first.month + 1)
    last = next_month - timedelta(days=1)
    return first, last


def build_task_index(plan):
    """task_id → task 的索引"""
    idx = {}
    for d in plan.get("daily_tasks", []):
        for t in d["tasks"]:
            idx[t["id"]] = {**t, "_date": d["date"], "_stage": d["stage_id"]}
    return idx


def date_in_range(d_str: str, start: date, end: date) -> bool:
    try:
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        return start <= d <= end
    except ValueError:
        return False


def render_emoji_bar(value: int, max_val: int, width: int = 20) -> str:
    """渲染 emoji 进度条"""
    if max_val == 0:
        return "░" * width
    filled = int(value / max_val * width)
    return "█" * filled + "░" * (width - filled)


def generate_report(plan, checkin, streak, start: date, end: date, period_name: str):
    task_idx = build_task_index(plan)

    # 范围内打卡
    period_checkins = [
        c for c in checkin.get("checkins", []) if date_in_range(c["date"], start, end)
    ]

    # 应完成 vs 实际完成
    period_planned = [
        d for d in plan.get("daily_tasks", []) if date_in_range(d["date"], start, end)
    ]
    total_planned = sum(len(d["tasks"]) for d in period_planned)
    total_done = sum(len(c.get("task_ids", [])) for c in period_checkins)

    # 总时长
    total_minutes = 0
    category_counter = Counter()
    daily_minutes = defaultdict(int)

    # weekday × timeslot 二维矩阵：weekday(0..6) × timeslot
    # 累积「分钟数」与「任务数」用于诊断
    wd_ts_minutes = defaultdict(lambda: defaultdict(int))   # [weekday][timeslot] -> minutes
    wd_ts_tasks = defaultdict(lambda: defaultdict(int))     # [weekday][timeslot] -> task count

    # mood 分桶
    mood_counter = Counter()
    mood_minutes = defaultdict(int)

    # status 分桶（done / partial / missed）
    status_counter = Counter()

    for c in period_checkins:
        try:
            d_obj = datetime.strptime(c["date"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        wd = d_obj.weekday()
        ts = _infer_timeslot_from_record(c)

        c_total = 0
        for tid in c.get("task_ids", []):
            t = task_idx.get(tid)
            if t:
                dm = t.get("duration_min", 0)
                c_total += dm
                category_counter[t.get("category", "其他")] += 1
        # 若 record 自带 duration_min（用户 --duration），优先用该值（已含 task 估算 + 实际差额）
        rec_dm = c.get("duration_min")
        if isinstance(rec_dm, (int, float)) and rec_dm > 0:
            c_total = int(rec_dm)

        total_minutes += c_total
        daily_minutes[c["date"]] += c_total
        wd_ts_minutes[wd][ts or "_unknown"] += c_total
        wd_ts_tasks[wd][ts or "_unknown"] += len(c.get("task_ids", []))

        # mood / status
        mood = c.get("mood")
        if mood in MOOD_LABELS:
            mood_counter[mood] += 1
            mood_minutes[mood] += c_total
        st = c.get("status")
        if st:
            status_counter[st] += 1

    # 打卡天数
    checkin_days = len(set(c["date"] for c in period_checkins))
    period_days = (end - start).days + 1

    completion_rate = (total_done / total_planned * 100) if total_planned else 0

    # 评级
    if completion_rate >= 90:
        grade, grade_emoji = "卓越", "🏆"
    elif completion_rate >= 70:
        grade, grade_emoji = "优秀", "🌟"
    elif completion_rate >= 50:
        grade, grade_emoji = "及格", "💪"
    elif completion_rate > 0:
        grade, grade_emoji = "落后", "🌧️"
    else:
        grade, grade_emoji = "断档", "💔"

    # ---------- 诊断：找最差 weekday × timeslot ----------
    # 仅当至少 2 天有打卡记录时才输出诊断（避免数据不足误判）
    diag_lines = []
    has_timeslot = any(
        ts != "_unknown"
        for ts_dict in wd_ts_minutes.values()
        for ts in ts_dict
    )

    weekday_label = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    # 收集每个 weekday 上的 level 集合（用于 ABC 三档诊断纠偏，避免"C 档低分"被误判为效率低）
    wd_levels = defaultdict(list)  # weekday -> [level, ...]，level ∈ {"a","b","c",None}
    for c in period_checkins:
        try:
            d_obj = datetime.strptime(c["date"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        wd_levels[d_obj.weekday()].append((c.get("level") or "").lower())

    # 1) 弱日识别（weekday 维度，按完成时长升序）
    daily_minutes_by_wd = defaultdict(int)
    for d_str, mins in daily_minutes.items():
        try:
            wd = datetime.strptime(d_str, "%Y-%m-%d").date().weekday()
            daily_minutes_by_wd[wd] += mins
        except ValueError:
            continue

    if len(daily_minutes_by_wd) >= 2:
        sorted_wd = sorted(daily_minutes_by_wd.items(), key=lambda x: x[1])
        worst_wd, worst_mins = sorted_wd[0]
        best_wd, best_mins = sorted_wd[-1]
        if best_mins > 0 and worst_mins < best_mins * 0.5:
            # ⚠️ ABC 三档纠偏：若 worst_wd 上的打卡全是 C 档，那不是"低效率"，
            # 而是用户主动启用兜底档保住 streak —— 应给正向反馈，不能让 AI 反向建议
            # 用户"把 C 档任务挪到 streak 没断的另一天"（违反 ABC 核心承诺）
            worst_levels = [lv for lv in wd_levels.get(worst_wd, []) if lv]
            all_c_on_worst = bool(worst_levels) and all(lv == "c" for lv in worst_levels)
            if all_c_on_worst:
                diag_lines.append(
                    f"{weekday_label[worst_wd]}用了 C 档兜底（{worst_mins} min），"
                    f"这是 ABC 三档的正确用法 —— 状态不好时启动兜底，streak 不断比满分更重要。"
                    f"不需要把任务挪走。"
                )
            else:
                diag_lines.append(
                    f"{weekday_label[worst_wd]}效率较低（{worst_mins} min），仅 {weekday_label[best_wd]}（{best_mins} min）的 "
                    f"{int(worst_mins/best_mins*100) if best_mins else 0}%；"
                    f"如果不是因为状态低（C 档），可以考虑把该日重负任务挪到 {weekday_label[best_wd]}。"
                )

    # 2) 时段维度（仅在 record 含时间戳时）
    if has_timeslot:
        ts_total = defaultdict(int)
        for ts_dict in wd_ts_minutes.values():
            for ts, mins in ts_dict.items():
                if ts != "_unknown":
                    ts_total[ts] += mins
        if len(ts_total) >= 2:
            sorted_ts = sorted(ts_total.items(), key=lambda x: x[1])
            worst_ts, worst_m = sorted_ts[0]
            best_ts, best_m = sorted_ts[-1]
            if best_m > 0 and worst_m < best_m * 0.5:
                diag_lines.append(
                    f"{TIMESLOT_LABEL[worst_ts]}效率最低（{worst_m} min），不到 {TIMESLOT_LABEL[best_ts]}（{best_m} min）的一半；"
                    f"建议调整到 {TIMESLOT_LABEL[best_ts]}。"
                )

    # 3) mood 与效率关联（如有数据）
    if mood_counter:
        mood_avg = {
            m: (mood_minutes[m] / mood_counter[m]) for m in mood_counter
        }
        if "tired" in mood_avg and "ok" in mood_avg and mood_avg["tired"] < mood_avg["ok"] * 0.7:
            diag_lines.append(
                f"标记 tired 的打卡日均 {mood_avg['tired']:.0f} min，明显低于 ok 状态（{mood_avg['ok']:.0f} min）；"
                f"疲惫日建议直接降量，避免硬撑导致质量下滑。"
            )

    # ---------- 下周预警 ----------
    next_start = end + timedelta(days=1)
    next_end = next_start + timedelta(days=6)
    next_week_planned = [
        d for d in plan.get("daily_tasks", [])
        if date_in_range(d["date"], next_start, next_end)
    ]
    next_week_task_total = sum(len(d["tasks"]) for d in next_week_planned)
    next_week_minute_total = sum(
        t.get("duration_min", 0)
        for d in next_week_planned for t in d["tasks"]
    )

    next_warnings = []
    if next_week_task_total == 0:
        if period_name == "周":
            next_warnings.append("下周计划为空——若 plan 已结束，可考虑 plan-tracker 衍生新计划；若未结束需检查 daily_tasks 是否有缺漏。")
    else:
        # 与本期比较负荷
        cur_minute_total = sum(
            t.get("duration_min", 0)
            for d in period_planned for t in d["tasks"]
        )
        if cur_minute_total > 0:
            ratio = next_week_minute_total / cur_minute_total
            if ratio > 1.3:
                next_warnings.append(
                    f"下周计划负荷比本期高 {int((ratio-1)*100)}%（{next_week_minute_total} min vs {cur_minute_total} min），建议提前规划高效时段。"
                )
            elif ratio < 0.7:
                next_warnings.append(
                    f"下周计划负荷比本期低 {int((1-ratio)*100)}%，是补齐落后任务和深度复盘的好时机。"
                )
        # 完成率与负荷预警
        if completion_rate < 50 and next_week_task_total > 10:
            next_warnings.append(
                f"本期完成率仅 {completion_rate:.0f}% 而下周还有 {next_week_task_total} 个任务待完成，"
                f"强烈建议先用 edit_plan.py rebalance 减量或 postpone 顺延。"
            )

    # 输出
    out = []
    meta = plan["meta"]
    out.append("=" * 60)
    out.append(f"  📊 {period_name}报告 · {meta['title']}")
    out.append(f"     {start.isoformat()}  →  {end.isoformat()}")
    out.append("=" * 60)
    out.append("")

    out.append(f"🎯 总览")
    out.append(f"   评级：{grade_emoji} {grade}（{completion_rate:.0f}%）")
    out.append(f"   完成：{total_done}/{total_planned} 个任务")
    out.append(f"   时长：{total_minutes // 60}h {total_minutes % 60}min")
    out.append(f"   打卡：{checkin_days}/{period_days} 天")
    out.append(f"   连续：🔥 {streak.get('current', 0)} 天（历史最长 {streak.get('longest', 0)} 天）")
    if status_counter:
        st_parts = []
        for k in ("done", "partial", "missed"):
            if status_counter.get(k):
                st_parts.append(f"{k} {status_counter[k]}")
        if st_parts:
            out.append(f"   状态：" + " · ".join(st_parts))
    out.append("")

    # 进度条可视化
    out.append("📈 完成度")
    out.append(f"   [{render_emoji_bar(total_done, total_planned)}] {completion_rate:.0f}%")
    out.append("")

    # 类别分布
    cat_label = {
        "listening": "听力", "reading": "阅读", "writing": "写作", "speaking": "口语",
        "vocabulary": "词汇", "grammar": "语法", "review": "复盘", "exam": "模考",
        "output": "输出", "rest": "休息",
    }
    if category_counter:
        out.append("📚 类别分布")
        max_cat = max(category_counter.values())
        for cat, cnt in category_counter.most_common():
            label = cat_label.get(cat, cat)
            bar = render_emoji_bar(cnt, max_cat, width=15)
            out.append(f"   {label:<6} [{bar}] {cnt}")
        out.append("")

    # mood 分布
    if mood_counter:
        out.append("💭 心情分布")
        max_m = max(mood_counter.values())
        for m, cnt in mood_counter.most_common():
            avg = mood_minutes[m] / cnt if cnt else 0
            bar = render_emoji_bar(cnt, max_m, width=12)
            out.append(f"   {MOOD_LABELS[m]:<10} [{bar}] {cnt} 次 · 均 {avg:.0f} min")
        out.append("")

    # 每日时长热力
    if daily_minutes:
        out.append("⏰ 每日学习时长")
        max_min = max(daily_minutes.values())
        cur = start
        while cur <= end:
            mins = daily_minutes.get(cur.isoformat(), 0)
            bar = render_emoji_bar(mins, max_min, width=20) if max_min > 0 else "░" * 20
            day_label = cur.strftime("%m-%d %a")
            out.append(f"   {day_label}  [{bar}] {mins} min")
            cur += timedelta(days=1)
        out.append("")

    # 瓶颈任务（基于过去 14 天 miss 计数）
    bottlenecks = compute_bottleneck_tasks(plan, checkin, today=end)
    if bottlenecks:
        out.append("🔻 瓶颈任务（连续被跳过）")
        for b in bottlenecks[:3]:
            cat = cat_label.get(b["category"], b["category"])
            out.append(
                f"   · [{cat}] {b['title']} —— miss {b['miss_count']} 次（最近 {b['last_missed']}）"
            )
        out.append("")

    # AI 诊断（weekday × timeslot 效率分析）
    if diag_lines:
        out.append("🔍 AI 诊断")
        for line in diag_lines:
            out.append(f"   · {line}")
        out.append("")

    # 智能洞察（保留原有）
    out.append("💡 洞察")
    if completion_rate >= 90:
        out.append("   · 你这周/月简直是学霸本霸！保持节奏，注意劳逸结合 🌿")
    elif completion_rate >= 70:
        out.append("   · 完成度优秀，可以适度提高难度或增加输出环节")
    elif completion_rate >= 50:
        out.append("   · 还有提升空间，建议聚焦最薄弱的 1-2 项突破")
    elif completion_rate > 0:
        out.append("   · 进度落后，建议：缩减每日任务量 + 提高单任务质量")
    else:
        out.append("   · 本期未打卡，建议执行「断签救赎」重排计划")

    if checkin_days < period_days * 0.6 and checkin_days > 0:
        out.append(f"   · 打卡频率较低（{checkin_days}/{period_days}），建议固定时间段学习")

    if category_counter:
        weakest_cat = min(category_counter.items(), key=lambda x: x[1])
        out.append(f"   · 最少投入：{cat_label.get(weakest_cat[0], weakest_cat[0])} 仅 {weakest_cat[1]} 次，下周可加强")

    out.append("")

    # 下周预警（仅周报输出）
    if period_name == "周" and next_warnings:
        out.append("⚠️ 下周预警")
        for w in next_warnings:
            out.append(f"   · {w}")
        out.append("")

    out.append("=" * 60)

    # 副作用：把 bottleneck_tasks 持久化回 streak.json，下游 agent 可直接读
    try:
        persist_bottleneck_to_streak(plan["id"], bottlenecks)
    except OSError:
        # 不阻塞周报输出
        pass

    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("period", choices=["weekly", "monthly"], help="周报 / 月报")
    parser.add_argument("--plan", default=None, help="指定计划 ID")
    parser.add_argument("--week", default=None, help="指定某周（周内任意日期 YYYY-MM-DD）")
    parser.add_argument("--month", default=None, help="指定某月（月内任意日期 YYYY-MM-DD）")
    parser.add_argument("--save", action="store_true", help="保存为 markdown 文件")
    args = parser.parse_args()

    plan, checkin, streak, _, plan_dir = load_plan_data(args.plan)

    if args.period == "weekly":
        ref = datetime.strptime(args.week, "%Y-%m-%d").date() if args.week else None
        start, end = get_week_range(ref)
        period_name = "周"
    else:
        ref = datetime.strptime(args.month, "%Y-%m-%d").date() if args.month else None
        start, end = get_month_range(ref)
        period_name = "月"

    report = generate_report(plan, checkin, streak, start, end, period_name)
    print(report)

    if args.save:
        from pathlib import Path
        report_dir = Path(plan_dir) / "reports"
        report_dir.mkdir(exist_ok=True)
        fname = f"{args.period}-{start.isoformat()}.md"
        (report_dir / fname).write_text(report, encoding="utf-8")
        print(f"\n[OK] 报告已保存：{report_dir / fname}")


if __name__ == "__main__":
    main()

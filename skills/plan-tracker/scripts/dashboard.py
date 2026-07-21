#!/usr/bin/env python3
"""
dashboard.py · plan-tracker HTML 仪表盘生成器

用法：
  python3 dashboard.py                     # 用 active_plan 生成（默认暗色）
  python3 dashboard.py --plan PLAN_ID      # 指定计划
  python3 dashboard.py --theme light       # 浅色主题
  python3 dashboard.py --open              # 生成后用浏览器打开（macOS/Linux/Windows 自适配）

输出：
  <plan_dir>/dashboard.html                # 单文件，0 外部依赖、0 JS 框架、0 网络请求

设计契约（参考 SKILL.md NEVER 1 / NEVER 5）：
  - 静态快照：每次执行 = 当下数据切片，所有 JSON 只读不写
  - 不含 localStorage / 不含外网 CDN / 不含跨域请求
  - 所有 SVG 内联（热力图为 7×N <rect> 网格）
  - 失败时优雅降级（缺失数据用占位文案，而非崩溃）

依赖：Python 3.8+，仅标准库
"""

import argparse
import html
import json
import os
import sys
import webbrowser
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _plan_utils import (  # noqa: E402
    DATA_DIR,
    compute_bottleneck_tasks,
    resolve_end_date,
    resolve_start_date,
)

# ---------------------------------------------------------------- 主题配色

THEMES = {
    "dark": {
        "bg": "#0f0f1a",
        "card": "#1a1a2e",
        "card2": "#222238",
        "border": "rgba(255,255,255,0.06)",
        "text": "#e0e0e0",
        "text_dim": "#aaa",
        "text_mute": "#666",
        "primary": "#ff6b6b",
        "accent": "#ffa502",
        "success": "#2ed573",
        "warn": "#ffa502",
        "heat": ["#1f1f33", "#3d2a44", "#7d3a52", "#cf4d56", "#ff6b6b"],
    },
    "light": {
        "bg": "#f8f9fc",
        "card": "#ffffff",
        "card2": "#f0f2f8",
        "border": "rgba(0,0,0,0.06)",
        "text": "#1a1a2e",
        "text_dim": "#555",
        "text_mute": "#999",
        "primary": "#e74c3c",
        "accent": "#f39c12",
        "success": "#27ae60",
        "warn": "#f39c12",
        "heat": ["#ebedf0", "#f6c7c7", "#f49494", "#ed6464", "#e74c3c"],
    },
}

# ---------------------------------------------------------------- 数据加载


def load_plan_data(plan_id: str = None):
    """复用 stats.py 同款加载逻辑（简化版）。

    错误处理：以 import 方式被外部调用时不能直接 sys.exit；
    改为抛 RuntimeError，由上层统一兜底。
    """
    if plan_id:
        plan_dir = os.path.join(DATA_DIR, plan_id)
    else:
        if not os.path.exists(DATA_DIR):
            raise RuntimeError(f"数据目录不存在：{DATA_DIR}")
        plans = sorted(
            [p for p in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, p))],
            key=lambda p: os.path.getmtime(os.path.join(DATA_DIR, p, "plan.json"))
            if os.path.exists(os.path.join(DATA_DIR, p, "plan.json"))
            else 0,
            reverse=True,
        )
        if not plans:
            raise RuntimeError("没有找到任何学习计划")
        plan_dir = os.path.join(DATA_DIR, plans[0])

    def safe_load(name, default):
        path = os.path.join(plan_dir, name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return default

    plan = safe_load("plan.json", None)
    if plan is None:
        raise RuntimeError(f"{plan_dir} 中没有 plan.json")

    checkin = safe_load("checkin-log.json", {"checkins": []})
    streak = safe_load("streak.json", {"current": 0, "longest": 0})
    return plan, checkin, streak, plan_dir


# ---------------------------------------------------------------- 计算辅助


def _esc(s) -> str:
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def compute_overview(plan: dict, checkin: dict, streak: dict, today: date):
    start = resolve_start_date(plan)
    end = resolve_end_date(plan, fallback=today)
    total_days = max(1, (end - start).days + 1)
    elapsed_days = max(0, min(total_days, (today - start).days + 1))
    days_left = max(0, (end - today).days)

    # 计划任务总数 / 已打卡完成任务总数
    total_planned = sum(len(d.get("tasks", [])) for d in plan.get("daily_tasks", []))
    done_ids = set()
    for c in checkin.get("checkins", []):
        for tid in c.get("task_ids", []):
            done_ids.add(tid)
    total_done = len(done_ids)

    progress_pct = (total_done / total_planned * 100) if total_planned else 0
    return {
        "start": start,
        "end": end,
        "total_days": total_days,
        "elapsed_days": elapsed_days,
        "days_left": days_left,
        "total_planned": total_planned,
        "total_done": total_done,
        "progress_pct": progress_pct,
    }


def compute_streak_fire(checkin: dict, today: date, start_date: date):
    """从 start_date 到 today 的 Streak 火焰条。"""
    dates_with_checkin = {c["date"] for c in checkin.get("checkins", []) if "date" in c}
    cells = []
    d = start_date
    while d <= today:
        cells.append({
            "date": d.isoformat(),
            "label": d.strftime("%m-%d"),
            "active": d.isoformat() in dates_with_checkin,
            "is_today": d == today,
        })
        d += timedelta(days=1)
    return cells


def compute_heatmap(checkin: dict, plan: dict, today: date):
    """GitHub 风格热力图：从 plan.start_date 到 today（最多回溯 180 天）。
    返回 7×N 矩阵（行=星期，列=周）+ 5 档时长分位映射。
    """
    start = resolve_start_date(plan)
    # 回溯 180 天上限
    earliest = today - timedelta(days=179)
    if start < earliest:
        start = earliest

    # 把 start 对齐到当周周一（让热力图左对齐）
    grid_start = start - timedelta(days=start.weekday())
    grid_end = today

    # 累计每日时长
    daily_minutes = defaultdict(int)
    for c in checkin.get("checkins", []):
        d = c.get("date")
        if not d:
            continue
        # duration_min 缺失时按 task_ids × 25 分钟兜底
        rec_dm = c.get("duration_min")
        if isinstance(rec_dm, (int, float)) and rec_dm > 0:
            daily_minutes[d] += int(rec_dm)
        else:
            daily_minutes[d] += len(c.get("task_ids", [])) * 25

    # 5 档分位（按非 0 时长的最大值切等分）
    nonzero = [v for v in daily_minutes.values() if v > 0]
    max_min = max(nonzero) if nonzero else 0

    def level(mins):
        if mins <= 0:
            return 0
        if max_min == 0:
            return 0
        ratio = mins / max_min
        if ratio < 0.25:
            return 1
        if ratio < 0.5:
            return 2
        if ratio < 0.75:
            return 3
        return 4

    # 拼网格：weeks 列表，每列是 7 天
    weeks = []
    cur = grid_start
    cur_week = []
    while cur <= grid_end:
        in_range = cur >= start and cur <= today
        mins = daily_minutes.get(cur.isoformat(), 0) if in_range else 0
        cur_week.append({
            "date": cur.isoformat(),
            "weekday": cur.weekday(),
            "in_range": in_range,
            "minutes": mins,
            "level": level(mins) if in_range else 0,
            "is_today": cur == today,
        })
        if cur.weekday() == 6:  # 周日 = 一周结束
            weeks.append(cur_week)
            cur_week = []
        cur += timedelta(days=1)
    if cur_week:
        weeks.append(cur_week)

    total_active_days = len(nonzero)
    total_minutes = sum(daily_minutes.values())
    return {
        "weeks": weeks,
        "max_min": max_min,
        "total_active_days": total_active_days,
        "total_minutes": total_minutes,
    }


def compute_milestones(streak: dict, overview: dict):
    """里程碑徽章：3 已解锁档 + 3 进度档。"""
    cur = int(streak.get("current", 0))
    longest = int(streak.get("longest", 0))
    progress_pct = overview["progress_pct"]

    badges = []
    # 7 / 30 / 100 天 streak
    for thr, name, emoji in [(7, "破冰者", "🌱"), (30, "火焰使者", "🔥"), (100, "持之以恒", "👑")]:
        if longest >= thr:
            badges.append({"emoji": emoji, "name": name, "unlocked": True, "label": f"{thr} 日连签"})
        else:
            badges.append({
                "emoji": emoji,
                "name": name,
                "unlocked": False,
                "label": f"{thr} 日连签",
                "progress": min(100, int(cur / thr * 100)),
                "current": cur,
                "target": thr,
            })

    # 计划完成度
    if progress_pct >= 100:
        badges.append({"emoji": "🏁", "name": "终点达成", "unlocked": True, "label": "完成全部计划"})
    else:
        badges.append({
            "emoji": "🏁",
            "name": "终点达成",
            "unlocked": False,
            "label": "完成全部计划",
            "progress": int(progress_pct),
            "current": overview["total_done"],
            "target": overview["total_planned"],
        })
    return badges


def compute_today_tasks(plan: dict, checkin: dict, today: date) -> list:
    """提取今日任务 + 标注是否已打卡。

    返回 list[dict]：
      {
        "id": str,
        "title": str,
        "category": str,
        "checked": bool,         # 今日是否已打卡（含 a/b/c 任意档）
        "checked_level": str,    # 已打卡的档位（A/B/C）或空
        "abc_levels": dict|None, # v2 plan 才有
      }
    """
    today_str = today.isoformat()

    # 今日已打卡的 task_id → level（取最新一次）
    checked_map = {}
    for c in checkin.get("checkins", []):
        if c.get("date") != today_str:
            continue
        lvl = (c.get("level") or "").lower()
        for tid in c.get("task_ids", []):
            checked_map[tid] = lvl

    # 找今日 daily_tasks
    today_tasks_raw = []
    for day in plan.get("daily_tasks", []):
        if day.get("date") == today_str:
            today_tasks_raw = day.get("tasks", []) or []
            break

    rows = []
    for t in today_tasks_raw:
        tid = t.get("id", "")
        rows.append({
            "id": tid,
            "title": t.get("title", "(未命名任务)"),
            "category": t.get("category", ""),
            "minutes": t.get("minutes") or t.get("duration_min") or 0,
            "checked": tid in checked_map,
            "checked_level": checked_map.get(tid, "").upper(),
            "abc_levels": t.get("abc_levels") if isinstance(t.get("abc_levels"), dict) else None,
        })
    return rows


def compute_recent_days(checkin: dict, today: date, window: int = 14):
    """最近 14 天的打卡明细。"""
    by_date = defaultdict(list)
    for c in checkin.get("checkins", []):
        d = c.get("date")
        if d:
            by_date[d].append(c)

    rows = []
    for i in range(window):
        d = today - timedelta(days=i)
        ds = d.isoformat()
        records = by_date.get(ds, [])
        if not records:
            rows.append({
                "date": ds,
                "label": d.strftime("%m-%d %a"),
                "checked": False,
                "summary": "未打卡",
                "level": None,
                "minutes": 0,
                "mood": None,
            })
            continue
        # 合并多次打卡
        total_min = 0
        levels = []
        moods = []
        statuses = []
        notes = []
        for r in records:
            rec_dm = r.get("duration_min")
            if isinstance(rec_dm, (int, float)) and rec_dm > 0:
                total_min += int(rec_dm)
            else:
                total_min += len(r.get("task_ids", [])) * 25
            if r.get("level"):
                levels.append(r["level"])
            if r.get("mood"):
                moods.append(r["mood"])
            if r.get("status"):
                statuses.append(r["status"])
            if r.get("note"):
                notes.append(r["note"])

        level_str = "/".join(sorted(set(levels))).upper() if levels else None
        status = "done"
        if "missed" in statuses and "done" not in statuses and "partial" not in statuses:
            status = "missed"
        elif "partial" in statuses and "done" not in statuses:
            status = "partial"
        rows.append({
            "date": ds,
            "label": d.strftime("%m-%d %a"),
            "checked": True,
            "summary": notes[0] if notes else f"{total_min} 分钟",
            "level": level_str,
            "minutes": total_min,
            "mood": moods[0] if moods else None,
            "status": status,
        })
    return rows


def compute_tag_stats(plan: dict, checkin: dict):
    """高频 category（tag）统计。"""
    task_idx = {}
    for d in plan.get("daily_tasks", []):
        for t in d.get("tasks", []):
            task_idx[t.get("id")] = t

    counter = Counter()
    for c in checkin.get("checkins", []):
        for tid in c.get("task_ids", []):
            t = task_idx.get(tid)
            if t:
                counter[t.get("category", "其他")] += 1

    label_map = {
        "listening": "听力", "reading": "阅读", "writing": "写作", "speaking": "口语",
        "vocabulary": "词汇", "grammar": "语法", "review": "复盘", "exam": "模考",
        "output": "输出", "rest": "休息",
    }
    return [
        {"name": label_map.get(k, k), "count": v}
        for k, v in counter.most_common(8)
    ]


# ---------------------------------------------------------------- 渲染：CSS


def render_css(theme: dict) -> str:
    t = theme
    return f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Roboto, sans-serif;
  background: {t['bg']};
  color: {t['text']};
  min-height: 100vh;
  padding: 24px 16px 40px;
  line-height: 1.5;
}}
.container {{ max-width: 920px; margin: 0 auto; }}
.section {{
  background: {t['card']};
  border-radius: 14px;
  padding: 22px 26px;
  margin-bottom: 18px;
  border: 1px solid {t['border']};
}}
.section h2 {{
  font-size: 15px;
  font-weight: 600;
  color: {t['text_dim']};
  margin-bottom: 14px;
  letter-spacing: 0.3px;
}}
.muted {{ color: {t['text_mute']}; font-size: 12px; }}

/* Header */
.header {{
  text-align: center;
  padding: 30px 24px;
  background: linear-gradient(135deg, {t['card']} 0%, {t['card2']} 100%);
  border-radius: 16px;
  margin-bottom: 18px;
  border: 1px solid {t['border']};
}}
.header h1 {{
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(90deg, {t['primary']}, {t['accent']});
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}}
.header .sub {{ font-size: 13px; color: {t['text_dim']}; margin-bottom: 18px; }}
.header-stats {{
  display: flex;
  justify-content: center;
  gap: 28px;
  flex-wrap: wrap;
}}
.header-stat {{ text-align: center; }}
.header-stat .num {{
  font-size: 30px;
  font-weight: 800;
  color: {t['primary']};
  line-height: 1;
}}
.header-stat .lbl {{ font-size: 12px; color: {t['text_dim']}; margin-top: 6px; }}

/* Progress bar */
.progress-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; }}
.progress-pct {{ color: {t['accent']}; font-weight: 600; }}
.progress-bar {{
  height: 10px;
  background: {t['card2']};
  border-radius: 5px;
  overflow: hidden;
}}
.progress-fill {{
  height: 100%;
  background: linear-gradient(90deg, {t['primary']}, {t['accent']});
  border-radius: 5px;
}}

/* Streak fire */
.fire-row {{ display: flex; gap: 6px; margin: 8px 0 12px; flex-wrap: wrap; }}
.fire-cell {{
  width: 38px; height: 46px;
  border-radius: 8px;
  background: {t['card2']};
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  border: 1px solid {t['border']};
  position: relative;
}}
.fire-cell.active {{
  background: linear-gradient(135deg, {t['primary']}33, {t['accent']}33);
  border-color: {t['primary']}66;
}}
.fire-cell.today {{
  border-color: {t['primary']};
  box-shadow: 0 0 10px {t['primary']}44;
}}
.fire-cell .lbl {{
  position: absolute; bottom: -16px; left: 0; right: 0;
  font-size: 9px; text-align: center; color: {t['text_mute']};
}}
.fire-meta {{ font-size: 13px; color: {t['text_dim']}; margin-top: 22px; }}
.fire-meta .num {{ color: {t['primary']}; font-weight: 700; font-size: 15px; }}

/* Heatmap */
.heatmap-wrap {{ overflow-x: auto; padding-bottom: 6px; }}
.heatmap-svg {{ display: block; }}
.heatmap-legend {{
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: {t['text_mute']};
  margin-top: 10px;
}}
.legend-cell {{ width: 12px; height: 12px; border-radius: 2px; }}
.heatmap-summary {{ font-size: 13px; color: {t['text_dim']}; margin-top: 12px; }}
.heatmap-summary .num {{ color: {t['accent']}; font-weight: 600; }}

/* Milestones */
.badges {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}}
.badge {{
  background: {t['card2']};
  border-radius: 10px;
  padding: 14px 12px;
  text-align: center;
  border: 1px solid {t['border']};
  position: relative;
}}
.badge.unlocked {{
  background: linear-gradient(135deg, {t['success']}22, {t['accent']}22);
  border-color: {t['success']}66;
}}
.badge.unlocked::after {{
  content: "✓";
  position: absolute; top: 6px; right: 8px;
  color: {t['success']}; font-weight: 700; font-size: 14px;
}}
.badge .emoji {{ font-size: 30px; line-height: 1.2; }}
.badge .name {{ font-size: 13px; font-weight: 600; margin-top: 4px; color: {t['text']}; }}
.badge .lbl {{ font-size: 11px; color: {t['text_mute']}; margin-top: 2px; }}
.badge .mini-bar {{
  height: 4px; background: {t['card']}; border-radius: 2px; overflow: hidden;
  margin-top: 8px;
}}
.badge .mini-fill {{
  height: 100%;
  background: linear-gradient(90deg, {t['primary']}, {t['accent']});
}}
.badge.unlocked .name {{ color: {t['success']}; }}

/* Bottleneck & tags */
.bottleneck-list {{ list-style: none; }}
.bottleneck-item {{
  padding: 10px 12px;
  background: {t['card2']};
  border-left: 3px solid {t['warn']};
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 13px;
}}
.bottleneck-item .miss {{ color: {t['warn']}; font-weight: 600; }}

.tag-grid {{
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-top: 10px;
}}
.tag-chip {{
  padding: 6px 12px;
  background: {t['card2']};
  border-radius: 14px;
  font-size: 12px;
  color: {t['text_dim']};
  border: 1px solid {t['border']};
}}
.tag-chip .cnt {{ color: {t['primary']}; font-weight: 700; margin-left: 4px; }}

/* Today tasks (一键复制打卡) */
.today-list {{ list-style: none; }}
.today-row {{
  display: flex; flex-direction: column; gap: 8px;
  padding: 12px 0;
  border-bottom: 1px solid {t['border']};
}}
.today-row:last-child {{ border-bottom: none; }}
.today-head {{
  display: flex; align-items: center; gap: 10px;
  font-size: 14px;
}}
.today-head .title {{ flex: 1; font-weight: 600; color: {t['text']}; }}
.today-head .meta {{ font-size: 11px; color: {t['text_mute']}; }}
.today-head .done {{
  background: {t['success']}22; color: {t['success']};
  padding: 2px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 600;
}}
.today-actions {{ display: flex; gap: 8px; flex-wrap: wrap; padding-left: 4px; }}
.btn-checkin {{
  appearance: none;
  border: 1px solid {t['border']};
  background: {t['card2']};
  color: {t['text']};
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
  min-width: 92px;
}}
.btn-checkin:hover {{ border-color: {t['primary']}66; transform: translateY(-1px); }}
.btn-checkin.lvl-a {{ border-color: {t['success']}66; }}
.btn-checkin.lvl-a:hover {{ background: {t['success']}22; }}
.btn-checkin.lvl-b {{ border-color: {t['accent']}66; }}
.btn-checkin.lvl-b:hover {{ background: {t['accent']}22; }}
.btn-checkin.lvl-c {{ border-color: {t['primary']}66; }}
.btn-checkin.lvl-c:hover {{ background: {t['primary']}22; }}
.btn-checkin.copied {{
  background: {t['success']};
  color: #fff;
  border-color: {t['success']};
}}
.btn-checkin.copied .btn-label::after {{
  content: " ✓ 已复制粘贴回终端";
}}
.today-empty {{
  padding: 24px 8px; text-align: center;
  color: {t['text_dim']}; font-size: 13px; line-height: 1.7;
}}

/* Recent days */
.day-list {{ list-style: none; }}
.day-row {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 4px;
  border-bottom: 1px solid {t['border']};
  font-size: 13px;
}}
.day-row:last-child {{ border-bottom: none; }}
.day-row .left {{ display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }}
.day-row .date {{ color: {t['text_mute']}; font-family: ui-monospace, "SF Mono", monospace; font-size: 12px; min-width: 88px; }}
.day-row .icon {{ font-size: 16px; }}
.day-row .summary {{ color: {t['text_dim']}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.day-row .right {{ display: flex; gap: 8px; flex-shrink: 0; margin-left: 12px; }}
.day-row .lvl {{
  padding: 2px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 600;
}}
.lvl-a {{ background: {t['success']}22; color: {t['success']}; }}
.lvl-b {{ background: {t['accent']}22; color: {t['accent']}; }}
.lvl-c {{ background: {t['primary']}22; color: {t['primary']}; }}
.day-row.missed .icon {{ color: {t['text_mute']}; }}
.day-row.missed .summary {{ color: {t['text_mute']}; }}

/* Footer */
.footer {{
  text-align: center; margin-top: 28px;
  font-size: 11px; color: {t['text_mute']};
}}

@media (max-width: 600px) {{
  body {{ padding: 12px 8px 30px; }}
  .section {{ padding: 16px 14px; }}
  .header {{ padding: 22px 14px; }}
  .header h1 {{ font-size: 22px; }}
  .header-stats {{ gap: 18px; }}
  .header-stat .num {{ font-size: 24px; }}
  .fire-cell {{ width: 30px; height: 38px; font-size: 16px; }}
}}
"""


# ---------------------------------------------------------------- 渲染：HTML 各 section


def render_header(plan: dict, streak: dict, overview: dict, persona_name: str) -> str:
    meta = plan.get("meta") or {}
    title = _esc(meta.get("title", plan.get("id", "学习计划")))
    deadline = _esc(meta.get("deadline", overview["end"].isoformat()))
    cur = int(streak.get("current", 0))
    pct = overview["progress_pct"]

    return f"""
<div class="header">
  <h1>🎯 {title}</h1>
  <div class="sub">目标日期：{deadline} · 当前人设：{_esc(persona_name)}</div>
  <div class="header-stats">
    <div class="header-stat">
      <div class="num">{overview['elapsed_days']}</div>
      <div class="lbl">已学习天数</div>
    </div>
    <div class="header-stat">
      <div class="num">{overview['days_left']}</div>
      <div class="lbl">距 deadline</div>
    </div>
    <div class="header-stat">
      <div class="num">🔥 {cur}</div>
      <div class="lbl">当前 Streak</div>
    </div>
    <div class="header-stat">
      <div class="num">{pct:.0f}%</div>
      <div class="lbl">总体进度</div>
    </div>
  </div>
</div>
<div class="section">
  <div class="progress-row">
    <span>{overview['total_done']} / {overview['total_planned']} 任务</span>
    <span class="progress-pct">{pct:.1f}%</span>
  </div>
  <div class="progress-bar"><div class="progress-fill" style="width: {min(100, pct):.1f}%"></div></div>
</div>
"""


def render_streak_fire(cells: list, streak: dict) -> str:
    cur = int(streak.get("current", 0))
    longest = int(streak.get("longest", 0))

    cell_html = []
    for c in cells:
        cls = ["fire-cell"]
        if c["active"]:
            cls.append("active")
        if c["is_today"]:
            cls.append("today")
        emoji = "🔥" if c["active"] else "·"
        cell_html.append(
            f'<div class="{" ".join(cls)}" title="{c["date"]}">{emoji}<span class="lbl">{c["label"]}</span></div>'
        )

    return f"""
<div class="section">
  <h2>🔥 Streak 火焰（自计划开始）</h2>
  <div class="fire-row">{''.join(cell_html)}</div>
  <div class="fire-meta">
    当前连续 <span class="num">{cur}</span> 天 · 历史最长 <span class="num">{longest}</span> 天
  </div>
</div>
"""


def render_heatmap(hm: dict, theme: dict) -> str:
    """SVG 内联渲染 GitHub 风格热力图。"""
    weeks = hm["weeks"]
    if not weeks:
        return ""

    cell_size = 12
    cell_gap = 3
    label_w = 28
    width = label_w + len(weeks) * (cell_size + cell_gap) + 4
    height = 7 * (cell_size + cell_gap) + 16  # +16 留给月份

    rects = []
    weekday_labels = ["一", "二", "三", "四", "五", "六", "日"]
    # 行标签（周一 / 周三 / 周五）
    for i in (0, 2, 4):
        y = 16 + i * (cell_size + cell_gap) + cell_size - 2
        rects.append(
            f'<text x="0" y="{y}" font-size="10" fill="{theme["text_mute"]}">{weekday_labels[i]}</text>'
        )

    # 月份标签（第一周 + 月份变化时打）
    last_month = None
    for wi, week in enumerate(weeks):
        if not week:
            continue
        # 取该周第一个 in_range 单元
        ref = next((c for c in week if c["in_range"]), week[0])
        try:
            d_obj = datetime.strptime(ref["date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        cur_month = d_obj.month
        if last_month != cur_month and (wi == 0 or d_obj.day <= 7):
            x = label_w + wi * (cell_size + cell_gap)
            rects.append(
                f'<text x="{x}" y="10" font-size="10" fill="{theme["text_mute"]}">{cur_month}月</text>'
            )
            last_month = cur_month

    # 单元格
    for wi, week in enumerate(weeks):
        for day in week:
            x = label_w + wi * (cell_size + cell_gap)
            y = 16 + day["weekday"] * (cell_size + cell_gap)
            if not day["in_range"]:
                color = theme["card2"]
                opacity = "0.4"
            else:
                color = theme["heat"][day["level"]]
                opacity = "1"
            stroke = theme["primary"] if day["is_today"] else "none"
            stroke_w = 1.5 if day["is_today"] else 0
            tip = f'{day["date"]} · {day["minutes"]} 分钟' if day["in_range"] else day["date"]
            rects.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                f'rx="2" ry="2" fill="{color}" opacity="{opacity}" '
                f'stroke="{stroke}" stroke-width="{stroke_w}">'
                f'<title>{tip}</title></rect>'
            )

    # 图例
    legend_cells = "".join(
        f'<span class="legend-cell" style="background:{c}"></span>'
        for c in theme["heat"]
    )

    return f"""
<div class="section">
  <h2>📅 学习热力图</h2>
  <div class="heatmap-wrap">
    <svg class="heatmap-svg" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
      {''.join(rects)}
    </svg>
  </div>
  <div class="heatmap-legend">
    少 {legend_cells} 多
    <span style="margin-left:auto">峰值：{hm['max_min']} 分钟 / 天</span>
  </div>
  <div class="heatmap-summary">
    打卡 <span class="num">{hm['total_active_days']}</span> 天 ·
    总学习时长 <span class="num">{hm['total_minutes'] // 60}h {hm['total_minutes'] % 60}min</span>
  </div>
</div>
"""


def render_milestones(badges: list) -> str:
    items = []
    for b in badges:
        cls = "badge unlocked" if b["unlocked"] else "badge"
        progress_html = ""
        sub = b.get("label", "")
        if not b["unlocked"]:
            pct = b.get("progress", 0)
            progress_html = (
                f'<div class="mini-bar"><div class="mini-fill" style="width:{pct}%"></div></div>'
                f'<div class="lbl">{b.get("current", 0)} / {b.get("target", 0)}</div>'
            )
        else:
            progress_html = f'<div class="lbl">已解锁</div>'
        items.append(f"""
<div class="{cls}">
  <div class="emoji">{_esc(b['emoji'])}</div>
  <div class="name">{_esc(b['name'])}</div>
  <div class="lbl">{_esc(sub)}</div>
  {progress_html}
</div>
""")
    return f"""
<div class="section">
  <h2>🏆 里程碑徽章</h2>
  <div class="badges">{''.join(items)}</div>
</div>
"""


def render_bottleneck_and_tags(bottlenecks: list, tags: list) -> str:
    body = []

    if bottlenecks:
        body.append('<h2 style="margin-bottom: 10px">⚠️ 瓶颈任务（连续 3+ 次未完成）</h2>')
        body.append('<ul class="bottleneck-list">')
        for b in bottlenecks[:3]:
            body.append(
                f'<li class="bottleneck-item">'
                f'<strong>{_esc(b["title"])}</strong> '
                f'<span class="muted">[{_esc(b.get("category", ""))}]</span> · '
                f'<span class="miss">miss {b["miss_count"]} 次</span>'
                f'<span class="muted"> · 最近 {_esc(b.get("last_missed", ""))}</span>'
                f'</li>'
            )
        body.append("</ul>")
    else:
        body.append('<h2>✅ 暂无瓶颈任务</h2>')
        body.append('<div class="muted">最近 14 天内没有连续 3+ 次被跳过的任务，节奏不错。</div>')

    if tags:
        body.append('<h2 style="margin-top: 18px; margin-bottom: 6px">📌 高频标签</h2>')
        body.append('<div class="tag-grid">')
        for t in tags:
            body.append(
                f'<div class="tag-chip">{_esc(t["name"])}<span class="cnt">{t["count"]}</span></div>'
            )
        body.append("</div>")

    return f'<div class="section">{"".join(body)}</div>'


def _build_checkin_cmd(plan_id: str, task_id: str, level: str = None) -> str:
    """拼接打卡命令字符串。

    返回相对路径写法，用户在 plan-tracker skill 目录下可直接粘贴；
    若不在该目录，python3 解释器仍能根据 PYTHONPATH / 用户实际部署路径找到 checkin.py。
    """
    parts = [
        "python3", "scripts/checkin.py",
        "--plan", plan_id,
        "--tasks", task_id,
    ]
    if level:
        parts.extend(["--level", level])
    return " ".join(parts)


def render_today_tasks(today_rows: list, plan_id: str) -> str:
    """今日任务区：ABC 三按钮（v2）/ 单按钮（v1）一键复制打卡命令。"""
    if not today_rows:
        return f"""
<div class="section">
  <h2>📌 今日任务</h2>
  <div class="today-empty">
    今天没有计划任务。<br>
    <span class="muted">可能计划已结束，或今天是休息日 — 哈哈，那就好好休息吧。</span>
  </div>
</div>
"""

    items = []
    for r in today_rows:
        title = _esc(r["title"])
        category = _esc(r["category"]) if r["category"] else ""
        minutes = r["minutes"]
        meta_parts = []
        if category:
            meta_parts.append(category)
        if minutes:
            meta_parts.append(f"{minutes} 分钟")
        meta_html = f'<span class="meta">{" · ".join(meta_parts)}</span>' if meta_parts else ""

        if r["checked"]:
            lvl_str = r["checked_level"] or "✓"
            done_html = f'<span class="done">已打卡 {_esc(lvl_str)}</span>'
            actions = ""
        else:
            done_html = ""
            buttons = []
            if r["abc_levels"]:
                # v2 plan：ABC 三按钮
                for lvl_key, emoji, label in [("a", "🅰️", "A 完美"), ("b", "🅱️", "B 基础"), ("c", "🆎", "C 兜底")]:
                    cmd = _build_checkin_cmd(plan_id, r["id"], lvl_key)
                    cmd_attr = html.escape(json.dumps(cmd), quote=True)
                    buttons.append(
                        f'<button type="button" class="btn-checkin lvl-{lvl_key}" '
                        f'onclick="cbCopy(this, {cmd_attr})">'
                        f'<span class="btn-label">{emoji} {label}</span>'
                        f'</button>'
                    )
            else:
                # v1 plan：单按钮
                cmd = _build_checkin_cmd(plan_id, r["id"])
                cmd_attr = html.escape(json.dumps(cmd), quote=True)
                buttons.append(
                    f'<button type="button" class="btn-checkin" '
                    f'onclick="cbCopy(this, {cmd_attr})">'
                    f'<span class="btn-label">✅ 复制打卡命令</span>'
                    f'</button>'
                )
            actions = f'<div class="today-actions">{"".join(buttons)}</div>'

        items.append(f"""
<li class="today-row">
  <div class="today-head">
    <span class="title">{title}</span>
    {meta_html}
    {done_html}
  </div>
  {actions}
</li>
""")

    return f"""
<div class="section">
  <h2>📌 今日任务（点按钮 → 终端粘贴回车 → 完成打卡）</h2>
  <ul class="today-list">{''.join(items)}</ul>
</div>
"""


def render_recent_days(rows: list) -> str:
    items = []
    for r in rows:
        if not r["checked"]:
            items.append(f"""
<li class="day-row missed">
  <div class="left">
    <span class="date">{_esc(r['label'])}</span>
    <span class="icon">·</span>
    <span class="summary">未打卡</span>
  </div>
</li>
""")
            continue

        icon_map = {"done": "✅", "partial": "🟡", "missed": "❌"}
        icon = icon_map.get(r.get("status", "done"), "✅")

        right_parts = []
        if r.get("level"):
            for lvl in r["level"].split("/"):
                lvl = lvl.strip().lower()
                if lvl:
                    right_parts.append(f'<span class="lvl lvl-{lvl}">{lvl.upper()} 档</span>')
        if r["minutes"]:
            right_parts.append(f'<span class="muted">{r["minutes"]} min</span>')

        items.append(f"""
<li class="day-row">
  <div class="left">
    <span class="date">{_esc(r['label'])}</span>
    <span class="icon">{icon}</span>
    <span class="summary">{_esc(r['summary'])}</span>
  </div>
  <div class="right">{''.join(right_parts)}</div>
</li>
""")

    return f"""
<div class="section">
  <h2>📝 最近 14 天打卡记录</h2>
  <ul class="day-list">{''.join(items)}</ul>
</div>
"""


# ---------------------------------------------------------------- 渲染：组装


def assemble(plan, checkin, streak, theme_name="dark", persona_name="温柔学姐"):
    today = date.today()
    theme = THEMES.get(theme_name, THEMES["dark"])

    overview = compute_overview(plan, checkin, streak, today)
    fire_cells = compute_streak_fire(checkin, today, resolve_start_date(plan))
    heatmap = compute_heatmap(checkin, plan, today)
    badges = compute_milestones(streak, overview)
    bottlenecks = compute_bottleneck_tasks(plan, checkin, today=today)
    tags = compute_tag_stats(plan, checkin)
    today_rows = compute_today_tasks(plan, checkin, today)
    recent = compute_recent_days(checkin, today, window=14)

    title = (plan.get("meta") or {}).get("title", plan.get("id", "学习计划"))
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    plan_id = plan.get("id", "")

    css = render_css(theme)
    body_parts = [
        render_header(plan, streak, overview, persona_name),
        render_today_tasks(today_rows, plan_id),
        render_streak_fire(fire_cells, streak),
        render_heatmap(heatmap, theme),
        render_milestones(badges),
        render_bottleneck_and_tags(bottlenecks, tags),
        render_recent_days(recent),
    ]

    # 极简 clipboard JS：≤30 行，仅做 writeText + 反馈
    clipboard_js = """
function cbCopy(btn, cmd) {
  const ok = function() {
    btn.classList.add('copied');
    setTimeout(function() { btn.classList.remove('copied'); }, 1800);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(cmd).then(ok).catch(function() { fallback(cmd, ok); });
  } else {
    fallback(cmd, ok);
  }
  function fallback(text, cb) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); cb(); } catch (e) { alert('复制失败，请手动复制：\\n' + text); }
    document.body.removeChild(ta);
  }
}
"""

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)} · plan-tracker 仪表盘</title>
<style>{css}</style>
</head>
<body>
<div class="container">
  {''.join(body_parts)}
  <div class="footer">
    plan-tracker dashboard · 生成于 {gen_time} · 数据全本地，无外网请求<br>
    打卡 / 编辑 / 救赎后此页面会自动重渲染，浏览器按 ⌘R / Ctrl+R 即可看到最新数据
  </div>
</div>
<script>{clipboard_js}</script>
</body>
</html>
"""

    insights = []
    cur = int(streak.get("current", 0))
    if cur >= 1:
        for thr, name in [(7, "🌱 破冰者"), (30, "🔥 火焰使者"), (100, "👑 持之以恒")]:
            if cur < thr:
                insights.append(f"连续 {cur} 天打卡，距「{name}」徽章还差 {thr - cur} 天")
                break
    if tags:
        insights.append(f"{tags[0]['name']} 已累计 {tags[0]['count']} 次，是你最稳的项目")
    if bottlenecks:
        b = bottlenecks[0]
        insights.append(f"⚠️ {b['title']} 已被跳过 {b['miss_count']} 次，建议明天补一次")

    return html_doc, insights


# ---------------------------------------------------------------- 对外渲染入口


def render_dashboard(plan_id: str = None, theme: str = "dark", out_path: str = None) -> str:
    """供其它脚本 import 复用的渲染入口。

    返回写入的 dashboard.html 绝对路径。
    失败由调用方 try/except 包住即可（本函数不吞异常）。
    """
    plan, checkin, streak, plan_dir = load_plan_data(plan_id)
    persona_name = _resolve_persona_name(plan_dir)
    if theme not in THEMES:
        theme = "dark"
    html_doc, _insights = assemble(plan, checkin, streak, theme_name=theme, persona_name=persona_name)
    final_path = out_path or os.path.join(plan_dir, "dashboard.html")
    out_dir = os.path.dirname(final_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return final_path


def _resolve_persona_name(plan_dir: str) -> str:
    """从 user-config.json 读 persona，最佳努力。"""
    user_cfg_path = os.path.abspath(os.path.join(os.path.dirname(plan_dir), "..", "user-config.json"))
    if os.path.exists(user_cfg_path):
        try:
            with open(user_cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            persona_map = {
                "gentle-senior": "温柔学姐",
                "strict-coach": "严格教练",
                "humorous-buddy": "幽默损友",
                "zen-master": "佛系导师",
            }
            return persona_map.get(cfg.get("persona", ""), "温柔学姐")
        except (json.JSONDecodeError, OSError):
            pass
    return "温柔学姐"


# ---------------------------------------------------------------- main


def main():
    parser = argparse.ArgumentParser(description="plan-tracker HTML 仪表盘生成器")
    parser.add_argument("--plan", default=None, help="指定计划 ID（默认取最近 plan）")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="配色主题")
    parser.add_argument("--open", action="store_true", help="生成后用浏览器打开")
    parser.add_argument("--out", default=None, help="自定义输出路径（默认 <plan_dir>/dashboard.html）")
    args = parser.parse_args()

    # 允许 PLAN_TRACKER_THEME 环境变量覆盖
    theme = os.environ.get("PLAN_TRACKER_THEME", args.theme)
    if theme not in THEMES:
        theme = "dark"

    plan, checkin, streak, plan_dir = (None, None, None, None)
    try:
        plan, checkin, streak, plan_dir = load_plan_data(args.plan)
    except RuntimeError as e:
        print(f"[ERR] {e}", file=sys.stderr)
        print("提示：先用 plan-tracker 拆解一个目标，或上传 plan.json 到 .plan-tracker/plans/ 下", file=sys.stderr)
        sys.exit(1)
    persona_name = _resolve_persona_name(plan_dir)

    html_doc, insights = assemble(plan, checkin, streak, theme_name=theme, persona_name=persona_name)

    out_path = args.out or os.path.join(plan_dir, "dashboard.html")
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"✅ Dashboard 已生成")
    print(f"📂 路径：{out_path}")
    print(f"🔍 双击文件即可在浏览器打开")
    if insights:
        print()
        print("本期亮点：")
        for line in insights:
            print(f"  · {line}")

    if args.open:
        try:
            webbrowser.open(f"file://{out_path}")
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
plan_view.py · plan-tracker 单计划全景视图（HTML）

用法：
  python3 plan_view.py                      # 用 active_plan 生成（默认暗色）
  python3 plan_view.py --plan PLAN_ID       # 指定计划
  python3 plan_view.py --theme light        # 浅色主题
  python3 plan_view.py --open               # 生成后用浏览器打开

输出：
  <plan_dir>/plan.html                      # 单文件，0 外部依赖、0 JS 框架、0 网络请求

与 dashboard.py 的分工（互补，非替代）：
  - dashboard.py   = 「当下快照」：streak / 热力图 / 最近 14 天 / 瓶颈
  - plan_view.py   = 「计划全景」：目标卡 / SMART / Anti-Goals / If-Then / OKR / 阶段时间线 / ABC 任务清单 / 标签云

设计契约（参考 SKILL.md NEVER 1 / NEVER 5）：
  - 静态快照：每次执行 = 当下数据切片，所有 JSON 只读不写
  - 不含 localStorage / 不含外网 CDN / 不含跨域请求
  - 复用 dashboard.py 的主题（dark / light），保持视觉一致
  - 失败时优雅降级（缺失字段用占位文案，而非崩溃）
  - 兼容 schema v1（缺 abc_levels / anti_goals / if_then_plans / okr_phases）

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
    resolve_end_date,
    resolve_start_date,
)
# 复用 dashboard 的主题字典，保持视觉一致
from dashboard import THEMES  # noqa: E402

# ---------------------------------------------------------------- 数据加载


def load_plan_data(plan_id: str = None):
    """与 dashboard.py 同款加载逻辑，但 checkin / streak 缺失时不报错。"""
    if plan_id:
        plan_dir = os.path.join(DATA_DIR, plan_id)
    else:
        if not os.path.exists(DATA_DIR):
            print(f"[ERR] 数据目录不存在：{DATA_DIR}", file=sys.stderr)
            print("提示：先用 plan-tracker 拆解一个目标，或上传 plan.json 到 .plan-tracker/plans/ 下", file=sys.stderr)
            sys.exit(1)
        plans = sorted(
            [p for p in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, p))],
            key=lambda p: os.path.getmtime(os.path.join(DATA_DIR, p, "plan.json"))
            if os.path.exists(os.path.join(DATA_DIR, p, "plan.json"))
            else 0,
            reverse=True,
        )
        if not plans:
            print("[ERR] 没有找到任何学习计划", file=sys.stderr)
            sys.exit(1)
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
        print(f"[ERR] {plan_dir} 中没有 plan.json", file=sys.stderr)
        sys.exit(1)

    checkin = safe_load("checkin-log.json", {"checkins": []})
    streak = safe_load("streak.json", {"current": 0, "longest": 0})
    return plan, checkin, streak, plan_dir


# ---------------------------------------------------------------- 工具


def _esc(s) -> str:
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def _fmt_date(s):
    """容错日期格式化：YYYY-MM-DD → MM-DD（周X）。"""
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
        wd = "一二三四五六日"[d.weekday()]
        return f"{d.month:02d}-{d.day:02d} 周{wd}"
    except (ValueError, TypeError):
        return s or ""


# ---------------------------------------------------------------- 计算


def compute_overview(plan: dict, checkin: dict, today: date):
    """目标卡所需的核心计数。"""
    start = resolve_start_date(plan)
    end = resolve_end_date(plan, fallback=today)
    total_days = max(1, (end - start).days + 1)
    elapsed_days = max(0, min(total_days, (today - start).days + 1))
    days_left = max(0, (end - today).days)

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
        "done_ids": done_ids,
    }


def compute_stage_progress(plan: dict, today: date, done_ids: set):
    """计算每个 stage / okr_phase 的时间进度 + 任务进度。"""
    meta = plan.get("meta") or {}
    stages = plan.get("stages") or []
    okr_phases = meta.get("okr_phases") or []

    # 用 stage_id → daily_tasks 索引
    stage_task_count = defaultdict(int)
    stage_done_count = defaultdict(int)
    for d in plan.get("daily_tasks", []):
        sid = d.get("stage_id") or "_default"
        for t in d.get("tasks", []):
            stage_task_count[sid] += 1
            if t.get("id") in done_ids:
                stage_done_count[sid] += 1

    rows = []
    # 优先用 stages（结构清晰），用 okr_phases 补全 objective / KR
    okr_by_id = {p.get("phase_id"): p for p in okr_phases if p.get("phase_id")}

    if stages:
        for s in stages:
            sid = s.get("id") or s.get("phase_id") or ""
            try:
                sd = datetime.strptime(s.get("start_date", ""), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                sd = None
            try:
                ed = datetime.strptime(s.get("end_date", ""), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                ed = None

            time_pct = 0
            status = "upcoming"
            if sd and ed:
                if today < sd:
                    status = "upcoming"
                    time_pct = 0
                elif today > ed:
                    status = "done"
                    time_pct = 100
                else:
                    status = "active"
                    span = max(1, (ed - sd).days + 1)
                    time_pct = int((today - sd).days / span * 100)

            planned = stage_task_count.get(sid, 0)
            done = stage_done_count.get(sid, 0)
            task_pct = int(done / planned * 100) if planned else 0

            okr = okr_by_id.get(sid, {})
            rows.append({
                "id": sid,
                "name": s.get("name") or sid or "（未命名阶段）",
                "objective": okr.get("objective") or (s.get("goals") or [None])[0],
                "key_results": okr.get("key_results") or [],
                "start_date": s.get("start_date"),
                "end_date": s.get("end_date"),
                "duration_days": s.get("duration_days"),
                "status": status,
                "time_pct": time_pct,
                "task_planned": planned,
                "task_done": done,
                "task_pct": task_pct,
            })
    elif okr_phases:
        # 无 stages，只有 okr_phases 时也能渲染
        for p in okr_phases:
            sid = p.get("phase_id") or ""
            rng = (p.get("phase_range") or "").split("~")
            sd_s = rng[0].strip() if len(rng) >= 1 else ""
            ed_s = rng[1].strip() if len(rng) >= 2 else ""
            rows.append({
                "id": sid,
                "name": p.get("phase_id") or "（OKR 阶段）",
                "objective": p.get("objective"),
                "key_results": p.get("key_results") or [],
                "start_date": sd_s,
                "end_date": ed_s,
                "duration_days": None,
                "status": "active",
                "time_pct": 0,
                "task_planned": stage_task_count.get(sid, 0),
                "task_done": stage_done_count.get(sid, 0),
                "task_pct": 0,
            })
    return rows


def compute_tag_cloud(plan: dict):
    """从 daily_tasks 统计 category 分布（不依赖 checkin）。"""
    counter = Counter()
    for d in plan.get("daily_tasks", []):
        for t in d.get("tasks", []):
            counter[t.get("category", "其他")] += 1
    label_map = {
        "listening": "听力", "reading": "阅读", "writing": "写作", "speaking": "口语",
        "vocabulary": "词汇", "grammar": "语法", "review": "复盘", "exam": "模考",
        "output": "输出", "rest": "休息",
    }
    return [
        {"name": label_map.get(k, k), "key": k, "count": v}
        for k, v in counter.most_common(12)
    ]


def group_daily_by_stage(plan: dict, done_ids: set, today: date):
    """把 daily_tasks 按 stage_id 分组，附带每个 day 的完成度。"""
    groups = defaultdict(list)
    for d in plan.get("daily_tasks", []):
        sid = d.get("stage_id") or "_default"
        try:
            d_obj = datetime.strptime(d.get("date", ""), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            d_obj = None

        tasks = d.get("tasks") or []
        done_in_day = sum(1 for t in tasks if t.get("id") in done_ids)
        is_today = d_obj == today
        is_past = (d_obj is not None) and d_obj < today

        groups[sid].append({
            "date": d.get("date"),
            "date_obj": d_obj,
            "tasks": tasks,
            "done_in_day": done_in_day,
            "total_in_day": len(tasks),
            "is_today": is_today,
            "is_past": is_past,
        })
    return groups


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
  line-height: 1.55;
}}
.container {{ max-width: 960px; margin: 0 auto; }}
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
.section h2 .hint {{
  font-size: 12px; font-weight: 400; color: {t['text_mute']}; margin-left: 8px;
}}
.muted {{ color: {t['text_mute']}; font-size: 12px; }}

/* Header（目标卡） */
.header {{
  padding: 28px 26px 24px;
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
.header .goal {{
  font-size: 14px; color: {t['text']}; margin-bottom: 16px;
  padding: 10px 12px; background: {t['card2']}; border-radius: 8px;
  border-left: 3px solid {t['accent']};
}}
.header-stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 18px;
  margin-top: 6px;
}}
.header-stat {{ text-align: center; }}
.header-stat .num {{
  font-size: 26px;
  font-weight: 800;
  color: {t['primary']};
  line-height: 1;
}}
.header-stat .lbl {{ font-size: 12px; color: {t['text_dim']}; margin-top: 6px; }}

/* SMART grid */
.smart-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}}
.smart-cell {{
  padding: 10px 12px;
  background: {t['card2']};
  border-radius: 8px;
  border: 1px solid {t['border']};
}}
.smart-cell .lbl {{
  font-size: 11px;
  color: {t['accent']};
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}}
.smart-cell .val {{ font-size: 13px; color: {t['text']}; word-break: break-word; }}

/* Anti / If-Then */
.list-clean {{ list-style: none; }}
.anti-item {{
  padding: 8px 12px;
  background: {t['card2']};
  border-left: 3px solid {t['warn']};
  border-radius: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  color: {t['text']};
}}
.ifthen-item {{
  padding: 10px 12px;
  background: {t['card2']};
  border-radius: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: {t['text']};
  border: 1px solid {t['border']};
}}
.ifthen-item .if {{ color: {t['text_dim']}; }}
.ifthen-item .arrow {{ color: {t['accent']}; margin: 0 8px; font-weight: 700; }}
.ifthen-item .then {{ color: {t['text']}; font-weight: 600; }}
.ifthen-item .kind {{
  display: inline-block; margin-left: 8px;
  padding: 2px 8px; border-radius: 10px;
  font-size: 11px; background: {t['bg']}; color: {t['text_mute']};
}}

/* OKR / Stage timeline */
.timeline {{ display: flex; flex-direction: column; gap: 12px; }}
.stage {{
  padding: 14px 16px;
  background: {t['card2']};
  border-radius: 10px;
  border: 1px solid {t['border']};
  border-left: 4px solid {t['text_mute']};
}}
.stage.active {{ border-left-color: {t['primary']}; }}
.stage.done {{ border-left-color: {t['success']}; opacity: 0.85; }}
.stage.upcoming {{ border-left-color: {t['text_mute']}; }}
.stage-head {{
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 6px;
}}
.stage-name {{ font-size: 15px; font-weight: 700; color: {t['text']}; }}
.stage-status {{
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
  background: {t['bg']}; color: {t['text_mute']};
}}
.stage.active .stage-status {{ color: {t['primary']}; }}
.stage.done .stage-status {{ color: {t['success']}; }}
.stage-objective {{
  font-size: 13px; color: {t['text_dim']}; margin-bottom: 8px;
}}
.stage-dates {{ font-size: 12px; color: {t['text_mute']}; margin-bottom: 8px; }}
.stage-bars {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.stage-bar .label {{ font-size: 11px; color: {t['text_mute']}; margin-bottom: 4px; }}
.stage-bar .label .num {{ color: {t['accent']}; font-weight: 600; margin-left: 4px; }}
.bar {{
  height: 6px; background: {t['bg']}; border-radius: 3px; overflow: hidden;
}}
.bar > .fill {{ height: 100%; background: linear-gradient(90deg, {t['primary']}, {t['accent']}); border-radius: 3px; }}
.bar.success > .fill {{ background: {t['success']}; }}
.kr-list {{ list-style: none; margin-top: 10px; }}
.kr-item {{
  font-size: 12px; color: {t['text_dim']};
  padding: 6px 0;
  border-top: 1px dashed {t['border']};
}}
.kr-item:first-child {{ border-top: none; }}
.kr-item .kr-bar {{ height: 4px; background: {t['bg']}; border-radius: 2px; overflow: hidden; margin-top: 4px; }}
.kr-item .kr-fill {{ height: 100%; background: {t['accent']}; }}

/* Tag cloud */
.tag-grid {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.tag-chip {{
  padding: 6px 12px;
  background: {t['card2']};
  border-radius: 14px;
  font-size: 12px;
  color: {t['text_dim']};
  border: 1px solid {t['border']};
}}
.tag-chip .cnt {{ color: {t['primary']}; font-weight: 700; margin-left: 4px; }}

/* Daily tasks (折叠) */
.day-block {{
  border: 1px solid {t['border']};
  border-radius: 8px;
  margin-bottom: 8px;
  background: {t['card2']};
  overflow: hidden;
}}
.day-block summary {{
  cursor: pointer;
  padding: 10px 14px;
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; color: {t['text']};
  user-select: none;
  list-style: none;
}}
.day-block summary::-webkit-details-marker {{ display: none; }}
.day-block summary::before {{
  content: "▸"; margin-right: 8px; color: {t['text_mute']};
  display: inline-block; transition: transform 0.15s;
  width: 12px;
}}
.day-block[open] summary::before {{ transform: rotate(90deg); }}
.day-block.today {{ border-color: {t['primary']}; box-shadow: 0 0 0 1px {t['primary']}33; }}
.day-summary-meta {{ font-size: 12px; color: {t['text_mute']}; }}
.day-summary-meta .ok {{ color: {t['success']}; font-weight: 600; }}
.day-tasks {{ list-style: none; padding: 4px 14px 12px; }}
.task-row {{
  padding: 10px 0;
  border-top: 1px dashed {t['border']};
  font-size: 13px;
}}
.task-row:first-child {{ border-top: none; }}
.task-head {{ display: flex; justify-content: space-between; gap: 10px; }}
.task-title {{ color: {t['text']}; font-weight: 500; }}
.task-title.done {{ color: {t['success']}; text-decoration: line-through; text-decoration-color: {t['success']}66; }}
.task-meta {{ font-size: 11px; color: {t['text_mute']}; flex-shrink: 0; }}
.task-meta .cat {{ color: {t['accent']}; }}
.abc-row {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;
  margin-top: 8px;
}}
.abc-cell {{
  background: {t['bg']}; border-radius: 6px;
  padding: 6px 8px; font-size: 11px;
  border: 1px solid {t['border']};
}}
.abc-cell .tag {{
  display: inline-block; padding: 1px 6px; border-radius: 8px;
  font-weight: 700; font-size: 10px; margin-right: 4px;
}}
.abc-cell.a .tag {{ background: {t['success']}33; color: {t['success']}; }}
.abc-cell.b .tag {{ background: {t['accent']}33; color: {t['accent']}; }}
.abc-cell.c .tag {{ background: {t['primary']}33; color: {t['primary']}; }}
.abc-cell .items {{ color: {t['text_dim']}; }}
.abc-cell .mins {{ color: {t['text_mute']}; margin-top: 2px; }}

/* Footer */
.footer {{
  text-align: center; margin-top: 28px;
  font-size: 11px; color: {t['text_mute']};
}}

@media (max-width: 600px) {{
  body {{ padding: 12px 8px 30px; }}
  .section {{ padding: 16px 14px; }}
  .header {{ padding: 22px 14px 18px; }}
  .header h1 {{ font-size: 22px; }}
  .header-stat .num {{ font-size: 22px; }}
  .stage-bars {{ grid-template-columns: 1fr; }}
  .abc-row {{ grid-template-columns: 1fr; }}
}}
"""


# ---------------------------------------------------------------- 渲染：各 section


def render_header(plan: dict, overview: dict, persona_name: str) -> str:
    meta = plan.get("meta") or {}
    title = _esc(meta.get("title", plan.get("id", "学习计划")))
    goal = _esc(meta.get("goal", ""))
    deadline = _esc(meta.get("deadline", overview["end"].isoformat()))
    start_date = _esc(meta.get("start_date", overview["start"].isoformat()))
    daily_budget = meta.get("daily_budget") or {}
    weekday_min = daily_budget.get("weekday")
    weekend_min = daily_budget.get("weekend")
    budget_str = (
        f"{weekday_min} / {weekend_min} min" if weekday_min and weekend_min else "—"
    )
    current_level = _esc(meta.get("current_level", "—"))

    goal_block = f'<div class="goal">📋 {goal}</div>' if goal else ""

    return f"""
<div class="header">
  <h1>🎯 {title}</h1>
  <div class="muted" style="margin-bottom: 14px;">
    {start_date} → {deadline} · 当前人设：{_esc(persona_name)}
  </div>
  {goal_block}
  <div class="header-stats">
    <div class="header-stat">
      <div class="num">{overview['days_left']}</div>
      <div class="lbl">距 deadline</div>
    </div>
    <div class="header-stat">
      <div class="num">{overview['elapsed_days']}<span class="muted" style="font-size:14px;font-weight:500"> / {overview['total_days']}</span></div>
      <div class="lbl">已学习 / 总天数</div>
    </div>
    <div class="header-stat">
      <div class="num">{overview['progress_pct']:.0f}%</div>
      <div class="lbl">总体进度</div>
    </div>
    <div class="header-stat">
      <div class="num" style="font-size:18px">{budget_str}</div>
      <div class="lbl">每日 / 周末预算</div>
    </div>
    <div class="header-stat">
      <div class="num" style="font-size:14px;font-weight:600">{current_level}</div>
      <div class="lbl">当前水平</div>
    </div>
  </div>
</div>
"""


def render_smart(plan: dict, overview: dict) -> str:
    meta = plan.get("meta") or {}
    title = meta.get("title", "")
    goal = meta.get("goal", "")
    deadline = meta.get("deadline", overview["end"].isoformat())
    weak = meta.get("weak_points") or []
    resources = meta.get("resources") or []

    cells = [
        ("S · Specific 具体", title or "—"),
        ("M · Measurable 可量化", goal or "—"),
        ("A · Achievable 可达性", meta.get("current_level") or "—"),
        ("R · Relevant 相关性", "、".join(weak) if weak else "—"),
        ("T · Time-bound 截止", deadline),
        ("📚 资源", "、".join(resources) if resources else "—"),
    ]
    cell_html = "".join(
        f'<div class="smart-cell"><div class="lbl">{_esc(lbl)}</div><div class="val">{_esc(val)}</div></div>'
        for lbl, val in cells
    )
    return f"""
<div class="section">
  <h2>📐 SMART 摘要 <span class="hint">拆解时填入的目标契约</span></h2>
  <div class="smart-grid">{cell_html}</div>
</div>
"""


def render_anti_and_ifthen(plan: dict) -> str:
    meta = plan.get("meta") or {}
    anti = meta.get("anti_goals") or []
    ifthen = meta.get("if_then_plans") or []
    if not anti and not ifthen:
        return ""

    blocks = []
    if anti:
        items = "".join(f'<li class="anti-item">🛡️ {_esc(a)}</li>' for a in anti[:10])
        blocks.append(f"""
<div class="section">
  <h2>🛡️ Anti-Goals 反目标护栏 <span class="hint">不愿牺牲的底线（共 {len(anti)} 条）</span></h2>
  <ul class="list-clean">{items}</ul>
</div>
""")

    if ifthen:
        kind_map = {
            "low_energy": "体力不支",
            "fall_behind": "进度落后",
            "over_pressure": "超额预防",
            "external_block": "外部阻碍",
            "general": "通用",
        }
        items = []
        for p in ifthen[:8]:
            iff = _esc(p.get("if", ""))
            then = _esc(p.get("then", ""))
            kind_raw = p.get("trigger_kind", "general")
            kind = kind_map.get(kind_raw, kind_raw)
            items.append(
                f'<div class="ifthen-item">'
                f'<span class="if">如果：{iff}</span>'
                f'<span class="arrow">→</span>'
                f'<span class="then">{then}</span>'
                f'<span class="kind">{_esc(kind)}</span>'
                f'</div>'
            )
        blocks.append(f"""
<div class="section">
  <h2>🔮 If-Then 障碍预演 <span class="hint">预先想好"如果 X 那就 Y"</span></h2>
  {''.join(items)}
</div>
""")
    return "".join(blocks)


def render_stages(stages: list) -> str:
    if not stages:
        return ""
    rows = []
    for s in stages:
        cls = f"stage {s['status']}"
        status_label = {"active": "进行中", "done": "已完成", "upcoming": "未开始"}[s["status"]]
        kr_html = ""
        if s.get("key_results"):
            kr_items = []
            for kr in s["key_results"]:
                target = kr.get("target") or 0
                current = kr.get("current") or 0
                unit = kr.get("unit") or ""
                pct = 0
                try:
                    if target:
                        pct = max(0, min(100, int(current / target * 100)))
                except (TypeError, ZeroDivisionError):
                    pct = 0
                kr_items.append(
                    f'<li class="kr-item">'
                    f'· {_esc(kr.get("kr",""))} '
                    f'<span class="muted">（{current}/{target} {_esc(unit)}）</span>'
                    f'<div class="kr-bar"><div class="kr-fill" style="width:{pct}%"></div></div>'
                    f'</li>'
                )
            kr_html = f'<ul class="kr-list">{"".join(kr_items)}</ul>'

        date_line = ""
        if s.get("start_date") or s.get("end_date"):
            date_line = (
                f'<div class="stage-dates">📅 {_esc(s.get("start_date","?"))} → {_esc(s.get("end_date","?"))}'
                + (f' · 共 {s["duration_days"]} 天' if s.get("duration_days") else '')
                + '</div>'
            )

        objective = s.get("objective")
        obj_line = f'<div class="stage-objective">🎯 {_esc(objective)}</div>' if objective else ""

        rows.append(f"""
<div class="{cls}">
  <div class="stage-head">
    <div class="stage-name">{_esc(s['name'])}</div>
    <span class="stage-status">{status_label}</span>
  </div>
  {obj_line}
  {date_line}
  <div class="stage-bars">
    <div class="stage-bar">
      <div class="label">⏱ 时间进度<span class="num">{s['time_pct']}%</span></div>
      <div class="bar"><div class="fill" style="width:{s['time_pct']}%"></div></div>
    </div>
    <div class="stage-bar">
      <div class="label">✅ 任务完成<span class="num">{s['task_done']}/{s['task_planned']}</span></div>
      <div class="bar success"><div class="fill" style="width:{s['task_pct']}%"></div></div>
    </div>
  </div>
  {kr_html}
</div>
""")

    return f"""
<div class="section">
  <h2>🗺️ 阶段时间线 <span class="hint">按 OKR / stages 拆分</span></h2>
  <div class="timeline">{''.join(rows)}</div>
</div>
"""


def render_tag_cloud(tags: list) -> str:
    if not tags:
        return ""
    chips = "".join(
        f'<div class="tag-chip">{_esc(t["name"])}<span class="cnt">{t["count"]}</span></div>'
        for t in tags
    )
    return f"""
<div class="section">
  <h2>📌 任务标签分布 <span class="hint">来自 plan.daily_tasks 的 category</span></h2>
  <div class="tag-grid">{chips}</div>
</div>
"""


def render_daily_tasks(plan: dict, stage_rows: list, done_ids: set, today: date) -> str:
    """每个 stage 一个折叠区，里面再按日折叠任务详情。"""
    daily_tasks = plan.get("daily_tasks") or []
    if not daily_tasks:
        return ""

    groups = group_daily_by_stage(plan, done_ids, today)

    # stage 顺序：优先用 stage_rows 的顺序，剩余按出现顺序
    stage_order = [s["id"] for s in stage_rows]
    remaining = [sid for sid in groups.keys() if sid not in stage_order]
    ordered = stage_order + remaining

    sections = []
    for sid in ordered:
        days = groups.get(sid)
        if not days:
            continue
        days.sort(key=lambda x: x["date_obj"] or date.max)
        stage_name = next((s["name"] for s in stage_rows if s["id"] == sid), sid or "未分组")

        # stage 汇总
        total = sum(d["total_in_day"] for d in days)
        done = sum(d["done_in_day"] for d in days)
        # 默认折叠：当前 stage 展开，其他折叠
        is_active_stage = any(
            s.get("status") == "active" and s.get("id") == sid for s in stage_rows
        )
        stage_open_attr = " open" if is_active_stage or not stage_rows else ""

        day_blocks = []
        for d in days:
            day_done = d["done_in_day"]
            day_total = d["total_in_day"]
            ok_str = (
                f'<span class="ok">{day_done}/{day_total} 完成</span>'
                if day_done > 0 else f'{day_done}/{day_total}'
            )
            today_cls = " today" if d["is_today"] else ""
            past_cls = " past" if d["is_past"] else ""
            day_open = " open" if d["is_today"] else ""
            label = _fmt_date(d["date"])

            task_items = []
            for t in d["tasks"]:
                tid = t.get("id", "")
                title = _esc(t.get("title", "（无标题）"))
                cat = _esc(t.get("category", ""))
                duration = t.get("duration_min")
                duration_str = f"{duration}min" if duration else ""
                priority = _esc(t.get("priority", ""))
                done_cls = " done" if tid in done_ids else ""

                meta_parts = []
                if cat:
                    meta_parts.append(f'<span class="cat">#{cat}</span>')
                if duration_str:
                    meta_parts.append(duration_str)
                if priority:
                    meta_parts.append(priority)

                # ABC 三档（v2）
                abc = t.get("abc_levels") or {}
                abc_html = ""
                if abc:
                    cells = []
                    for lvl_key, emoji in [("a", "🅰️"), ("b", "🅱️"), ("c", "🆎")]:
                        lvl = abc.get(lvl_key) or {}
                        items = lvl.get("items") or []
                        mins = lvl.get("minutes")
                        if not items and mins is None:
                            continue
                        items_str = "、".join(items) if items else "—"
                        mins_str = f"{mins} min" if mins is not None else ""
                        cells.append(
                            f'<div class="abc-cell {lvl_key}">'
                            f'<span class="tag">{emoji} {lvl_key.upper()}</span>'
                            f'<span class="items">{_esc(items_str)}</span>'
                            f'<div class="mins">{mins_str}</div>'
                            f'</div>'
                        )
                    if cells:
                        abc_html = f'<div class="abc-row">{"".join(cells)}</div>'

                task_items.append(f"""
<li class="task-row{past_cls}">
  <div class="task-head">
    <div class="task-title{done_cls}">{'✅ ' if done_cls else ''}{title}</div>
    <div class="task-meta">{' · '.join(meta_parts)}</div>
  </div>
  {abc_html}
</li>
""")

            day_blocks.append(f"""
<details class="day-block{today_cls}"{day_open}>
  <summary>
    <span>📅 {_esc(label)}{' · 今天' if d['is_today'] else ''}</span>
    <span class="day-summary-meta">{ok_str}</span>
  </summary>
  <ul class="day-tasks">
    {''.join(task_items)}
  </ul>
</details>
""")

        sections.append(f"""
<details class="day-block"{stage_open_attr} style="margin-bottom: 10px;">
  <summary>
    <span><strong>{_esc(stage_name)}</strong>（{len(days)} 天）</span>
    <span class="day-summary-meta">{done}/{total} 任务</span>
  </summary>
  <div style="padding: 4px 14px 12px;">
    {''.join(day_blocks)}
  </div>
</details>
""")

    if not sections:
        return ""
    return f"""
<div class="section">
  <h2>📋 ABC 任务清单 <span class="hint">点击展开每日详情；A/B/C 三档可见</span></h2>
  {''.join(sections)}
</div>
"""


# ---------------------------------------------------------------- 渲染：组装


def assemble(plan, checkin, streak, theme_name="dark", persona_name="温柔学姐"):
    today = date.today()
    theme = THEMES.get(theme_name, THEMES["dark"])

    overview = compute_overview(plan, checkin, today)
    stage_rows = compute_stage_progress(plan, today, overview["done_ids"])
    tags = compute_tag_cloud(plan)

    title = (plan.get("meta") or {}).get("title", plan.get("id", "学习计划"))
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    css = render_css(theme)
    body_parts = [
        render_header(plan, overview, persona_name),
        render_smart(plan, overview),
        render_anti_and_ifthen(plan),
        render_stages(stage_rows),
        render_tag_cloud(tags),
        render_daily_tasks(plan, stage_rows, overview["done_ids"], today),
    ]

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)} · plan-tracker 计划全景</title>
<style>{css}</style>
</head>
<body>
<div class="container">
  {''.join(body_parts)}
  <div class="footer">
    plan-tracker plan view · 生成于 {gen_time} · 数据全本地，无外网请求
  </div>
</div>
</body>
</html>
"""
    return html_doc


# ---------------------------------------------------------------- main


def main():
    parser = argparse.ArgumentParser(description="plan-tracker 单计划全景视图（HTML）")
    parser.add_argument("--plan", default=None, help="指定计划 ID（默认取最近 plan）")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="配色主题")
    parser.add_argument("--open", action="store_true", help="生成后用浏览器打开")
    parser.add_argument("--out", default=None, help="自定义输出路径（默认 <plan_dir>/plan.html）")
    args = parser.parse_args()

    theme = os.environ.get("PLAN_TRACKER_THEME", args.theme)
    if theme not in THEMES:
        theme = "dark"

    plan, checkin, streak, plan_dir = load_plan_data(args.plan)

    # persona 从 user-config.json 读取（best-effort）
    persona_name = "温柔学姐"
    user_cfg_path = os.path.join(os.path.dirname(plan_dir), "..", "user-config.json")
    user_cfg_path = os.path.abspath(user_cfg_path)
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
            persona_name = persona_map.get(cfg.get("persona", ""), persona_name)
        except (json.JSONDecodeError, OSError):
            pass

    html_doc = assemble(plan, checkin, streak, theme_name=theme, persona_name=persona_name)

    out_path = args.out or os.path.join(plan_dir, "plan.html")
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"✅ 计划全景视图已生成")
    print(f"📂 路径：{out_path}")
    print(f"🔍 双击文件即可在浏览器打开")

    if args.open:
        try:
            webbrowser.open(f"file://{out_path}")
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()

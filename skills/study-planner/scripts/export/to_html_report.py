#!/usr/bin/env python3
"""
导出为 HTML 报告（屏幕浏览导向）

设计哲学：
    - to_print.py    = A4 打印版，复选框 / 按周分页 / 高对比度，**贴墙抬头看**
    - to_html_report = 屏幕浏览版，含 SVG 任务类别分布图 + 阶段节奏对照 +
                       "不用 skill vs 用本计划" 对照段，**电脑/手机翻**

    两者刻意区分：打印版是"离线仪式感"，报告版是"上线前预览 / 分享给朋友看"。

输出：
    plan-report.html   单文件 HTML，无外部依赖（CSS / SVG 全内联）

用法：
    python3 to_html_report.py [plan_id]
    python3 to_html_report.py [plan_id] --stdout   # 直接打印不写文件
"""
import sys
import argparse
import html as _html
from collections import Counter, defaultdict
from datetime import date as date_cls
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _base import find_plan, category_of, resolve_output_dir  # noqa: E402

# ============================================================
#                       常量与样式
# ============================================================

# category → (中文标签, 主色, 浅色背景)
CATEGORY_STYLE = {
    "listening":  ("听力", "#3B82F6", "#DBEAFE"),
    "reading":    ("阅读", "#10B981", "#D1FAE5"),
    "writing":    ("写作", "#F59E0B", "#FEF3C7"),
    "speaking":   ("口语", "#EF4444", "#FEE2E2"),
    "vocabulary": ("词汇", "#8B5CF6", "#EDE9FE"),
    "grammar":    ("语法", "#EC4899", "#FCE7F3"),
    "review":     ("复盘", "#6B7280", "#F3F4F6"),
    "exam":       ("模考", "#DC2626", "#FEE2E2"),
    "output":     ("输出", "#0EA5E9", "#E0F2FE"),
    "rest":       ("休息", "#A3A3A3", "#F3F4F6"),
    # —— 编程/技能学习类 ——
    "coding":     ("编码", "#2563EB", "#DBEAFE"),
    "debug":      ("调试", "#F97316", "#FFEDD5"),
    "algorithm":  ("算法", "#7C3AED", "#EDE9FE"),
    "deploy":     ("部署", "#0D9488", "#CCFBF1"),
    "testing":    ("测试", "#16A34A", "#DCFCE7"),
    "weak_focus": ("弱项专项", "#DC2626", "#FEE2E2"),
}
DEFAULT_STYLE = ("其他", "#9CA3AF", "#F3F4F6")

PACE_LABEL = {
    "缓": ("缓", "#10B981", "宽松，可以反复打磨"),
    "正常": ("正常", "#3B82F6", "标准节奏"),
    "紧": ("紧", "#EF4444", "需要每天按时打卡，少踩刹车"),
}

WEEKDAY_CN = ["一", "二", "三", "四", "五", "六", "日"]


def _esc(s):
    return _html.escape(str(s)) if s is not None else ""


def _category_style(cat: str):
    return CATEGORY_STYLE.get(cat, DEFAULT_STYLE)


# ============================================================
#                       数据聚合
# ============================================================

def aggregate(plan: dict) -> dict:
    """把 plan.json 聚合成报告需要的派生数据。"""
    daily = plan.get("daily_tasks", [])
    stages = plan.get("stages", [])

    # 总分钟、总任务数
    total_min = 0
    total_tasks = 0
    cat_minutes = Counter()       # category -> 分钟
    cat_count = Counter()          # category -> 任务数
    stage_minutes = defaultdict(int)
    stage_tasks = defaultdict(int)

    for d in daily:
        for t in d.get("tasks", []):
            mins = int(t.get("duration_min") or 0)
            cat = t.get("category") or "other"
            total_min += mins
            total_tasks += 1
            cat_minutes[cat] += mins
            cat_count[cat] += 1
            stage_minutes[d.get("stage_id")] += mins
            stage_tasks[d.get("stage_id")] += 1

    # 计划天数（去重 date）
    days = len({d.get("date") for d in daily if d.get("date")})

    return {
        "total_min": total_min,
        "total_tasks": total_tasks,
        "days": days,
        "cat_minutes": cat_minutes,
        "cat_count": cat_count,
        "stage_minutes": dict(stage_minutes),
        "stage_tasks": dict(stage_tasks),
    }


# ============================================================
#                       SVG 图表
# ============================================================

def render_bar_chart(cat_minutes: Counter, *, width: int = 560, bar_h: int = 22) -> str:
    """任务类别分钟数横向条形图（SVG，纯内联）。
    选条形图而不是雷达图：条形图对绝对量更直观，且单文件 HTML 更稳。
    """
    items = sorted(cat_minutes.items(), key=lambda kv: -kv[1])
    if not items:
        return '<p class="muted">暂无任务，无法绘图。</p>'

    max_val = max(v for _, v in items) or 1
    label_w = 70
    val_w = 60
    chart_w = width - label_w - val_w - 20
    height = len(items) * (bar_h + 8) + 10

    rows = []
    for i, (cat, mins) in enumerate(items):
        label, color, _ = _category_style(cat)
        y = 5 + i * (bar_h + 8)
        bw = max(2, int(chart_w * mins / max_val))
        hours = mins / 60
        val_text = f"{mins} min"
        if hours >= 1:
            val_text = f"{mins} min · {hours:.1f}h"
        rows.append(
            f'<text x="0" y="{y + bar_h - 6}" font-size="13" fill="#374151">{_esc(label)}</text>'
            f'<rect x="{label_w}" y="{y}" width="{bw}" height="{bar_h}" '
            f'rx="4" fill="{color}" opacity="0.85" />'
            f'<text x="{label_w + bw + 6}" y="{y + bar_h - 6}" '
            f'font-size="12" fill="#6B7280">{val_text}</text>'
        )

    svg = (
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="任务类别分钟数分布">'
        + "".join(rows)
        + "</svg>"
    )
    return svg


def render_pace_strip(stages: list) -> str:
    """阶段节奏对照条：按 duration_days 等比拼接，颜色按 pace 上色。"""
    if not stages:
        return ""
    total_days = sum(int(s.get("duration_days") or 0) for s in stages) or 1
    blocks = []
    for s in stages:
        days = int(s.get("duration_days") or 0)
        if days <= 0:
            continue
        pct = days * 100 / total_days
        pace = (s.get("pace") or "正常").strip()
        label, color, _ = PACE_LABEL.get(pace, PACE_LABEL["正常"])
        title = f"{s.get('name','')} · {days} 天 · 节奏：{label}"
        blocks.append(
            f'<div class="pace-block" style="width:{pct:.2f}%;background:{color};" '
            f'title="{_esc(title)}">'
            f'<span class="pace-name">{_esc(s.get("name",""))}</span>'
            f'<span class="pace-meta">{days}天·{_esc(label)}</span>'
            f'</div>'
        )
    return f'<div class="pace-strip">{"".join(blocks)}</div>'


# ============================================================
#                       HTML 各段
# ============================================================

CSS = """
:root{
  --fg:#111827; --fg2:#374151; --muted:#6B7280; --line:#E5E7EB; --bg:#F9FAFB;
  --card:#FFFFFF; --accent:#2563EB;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--fg);
  font-family: -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",
    "Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  font-size:15px;line-height:1.65;}
.wrap{max-width:880px;margin:0 auto;padding:32px 24px 80px}
h1{font-size:26px;margin:0 0 4px}
h2{font-size:20px;margin:32px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:16px;margin:18px 0 8px}
p{margin:8px 0}
.muted{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:18px 20px;margin:12px 0}
.kv{display:grid;grid-template-columns:auto 1fr;gap:6px 18px;font-size:14px}
.kv dt{color:var(--muted)}
.kv dd{margin:0}
.tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;
  background:#F3F4F6;color:#374151;margin:0 4px 4px 0;border:1px solid var(--line)}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0}
.metric{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:14px 16px;text-align:center}
.metric .num{font-size:24px;font-weight:600;color:var(--accent)}
.metric .lbl{font-size:12px;color:var(--muted);margin-top:2px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#F3F4F6;font-weight:600;color:#374151}
td.right,th.right{text-align:right}
.badge{display:inline-block;padding:1px 8px;border-radius:4px;font-size:12px;
  font-weight:500;margin-right:6px}
.day{margin:14px 0;padding:12px 14px;border:1px solid var(--line);
  border-radius:8px;background:var(--card)}
.day h4{margin:0 0 8px;font-size:14px;color:var(--fg2)}
.day ul{margin:0;padding-left:20px}
.day li{margin:3px 0;font-size:14px}
.pace-strip{display:flex;width:100%;height:56px;border-radius:8px;overflow:hidden;
  border:1px solid var(--line);margin:8px 0}
.pace-block{display:flex;flex-direction:column;justify-content:center;align-items:center;
  color:#fff;font-size:12px;text-align:center;padding:4px 6px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.pace-name{font-weight:600}
.pace-meta{opacity:.85;font-size:11px;margin-top:2px}
.compare{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:8px 0}
.compare .col{padding:14px 16px;border-radius:10px;border:1px solid var(--line);
  background:var(--card)}
.compare h4{margin:0 0 8px;font-size:15px}
.compare .bad{border-left:4px solid #EF4444}
.compare .good{border-left:4px solid #10B981}
.compare ul{margin:6px 0 0 18px;padding:0}
.compare li{margin:4px 0;font-size:13.5px;color:var(--fg2)}
.footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);
  font-size:12px;color:var(--muted);text-align:center}
@media (max-width:640px){
  .metrics{grid-template-columns:repeat(2,1fr)}
  .compare{grid-template-columns:1fr}
}
"""


def render_header(plan: dict) -> str:
    meta = plan.get("meta", {})
    title = _esc(meta.get("title", "学习计划"))
    goal = _esc(meta.get("goal", ""))
    deadline = _esc(meta.get("deadline", "-"))
    cur = _esc(meta.get("current_level", "-"))
    budget = meta.get("daily_budget") or {}
    weak = meta.get("weak_points") or []
    method = meta.get("methodology") or []

    weak_html = "".join(f'<span class="tag">{_esc(w)}</span>' for w in weak) or '<span class="muted">未指定</span>'
    method_html = "".join(f'<span class="tag">{_esc(m)}</span>' for m in method) or '<span class="muted">未指定</span>'

    budget_str = "-"
    if budget:
        budget_str = (f'工作日 {int(budget.get("weekday",0))} 分钟 / '
                      f'周末 {int(budget.get("weekend",0))} 分钟')

    # P1-1：截止日 vs 计划末日 留白说明
    cal = (meta.get("_calendar_note") or {})
    calendar_html = ""
    if cal.get("tip"):
        buf = int(cal.get("buffer_days") or 0)
        color = "#10B981" if buf > 0 else "#6B7280"
        calendar_html = (
            f'<dt>日历</dt>'
            f'<dd style="color:{color}">📅 {_esc(cal["tip"])}</dd>'
        )

    return f"""
    <h1>{title}</h1>
    <p class="muted">{goal}</p>
    <div class="card">
      <dl class="kv">
        <dt>截止</dt><dd><b>{deadline}</b></dd>
        {calendar_html}
        <dt>当前水平</dt><dd>{cur}</dd>
        <dt>每日预算</dt><dd>{_esc(budget_str)}</dd>
        <dt>薄弱项</dt><dd>{weak_html}</dd>
        <dt>方法论</dt><dd>{method_html}</dd>
      </dl>
    </div>
    """


def render_metrics(agg: dict) -> str:
    total_h = agg["total_min"] / 60 if agg["total_min"] else 0
    days = agg["days"] or 1
    avg_min_per_day = agg["total_min"] / days if days else 0
    cat_count = len(agg["cat_minutes"])
    return f"""
    <div class="metrics">
      <div class="metric"><div class="num">{agg["days"]}</div><div class="lbl">总天数</div></div>
      <div class="metric"><div class="num">{agg["total_tasks"]}</div><div class="lbl">总任务数</div></div>
      <div class="metric"><div class="num">{total_h:.1f}h</div><div class="lbl">总学习时长</div></div>
      <div class="metric"><div class="num">{avg_min_per_day:.0f}min</div><div class="lbl">日均时长</div></div>
    </div>
    <p class="muted">任务覆盖 <b>{cat_count}</b> 个类别。</p>
    """


def render_stages(plan: dict, agg: dict) -> str:
    stages = plan.get("stages", [])
    if not stages:
        return ""

    pace_strip = render_pace_strip(stages)
    rows = []
    for s in stages:
        sid = s.get("id", "")
        name = _esc(s.get("name", ""))
        days = int(s.get("duration_days") or 0)
        goals = "、".join(s.get("goals") or [])
        pace = (s.get("pace") or "正常").strip()
        plabel, pcolor, ptip = PACE_LABEL.get(pace, PACE_LABEL["正常"])
        smin = agg["stage_minutes"].get(sid, 0)
        stasks = agg["stage_tasks"].get(sid, 0)
        badge = (f'<span class="badge" style="background:{pcolor};color:#fff" '
                 f'title="{_esc(ptip)}">{_esc(plabel)}</span>')
        rows.append(
            f"<tr><td>{_esc(sid)}</td><td>{name} {badge}</td>"
            f"<td>{days} 天</td>"
            f"<td>{stasks} 个任务 · {smin} 分钟</td>"
            f"<td>{_esc(goals)}</td></tr>"
        )

    return f"""
    <h2>阶段总览</h2>
    {pace_strip}
    <table>
      <thead><tr><th>阶段</th><th>名称 / 节奏</th><th>时长</th><th>容量</th><th>目标</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    """


def render_category_chart(agg: dict) -> str:
    if not agg["cat_minutes"]:
        return ""
    chart = render_bar_chart(agg["cat_minutes"])
    # 同时给一个表格副本（无障碍 + 数字党）
    rows = []
    total = sum(agg["cat_minutes"].values()) or 1
    top_pct = 0.0
    top_cat_label = ""
    for cat, mins in sorted(agg["cat_minutes"].items(), key=lambda kv: -kv[1]):
        label, color, bg = _category_style(cat)
        cnt = agg["cat_count"].get(cat, 0)
        pct = mins * 100 / total
        if pct > top_pct:
            top_pct = pct
            top_cat_label = label
        rows.append(
            f"<tr>"
            f'<td><span class="badge" style="background:{bg};color:{color};border:1px solid {color}33">'
            f'{_esc(label)}</span></td>'
            f'<td class="right">{cnt}</td>'
            f'<td class="right">{mins}</td>'
            f'<td class="right">{pct:.1f}%</td>'
            f"</tr>"
        )

    # P1-5：单类目占比 > 80% 时给出 warning
    warning_html = ""
    if top_pct > 80:
        warning_html = (
            f'<div class="card" style="border-left:4px solid #F59E0B;background:#FFFBEB">'
            f'<b>⚠️ 类别分布过于集中</b>：<b>{_esc(top_cat_label)}</b> 占比 {top_pct:.1f}%。'
            f'通常意味着 _infer_category 兜底过多——建议在 plan.json 给任务显式指定 '
            f'<code>category</code> 字段，或在 add-task 时手动调节类别分布。'
            f'</div>'
        )

    return f"""
    <h2>任务类别分布</h2>
    {warning_html}
    <div class="card">{chart}</div>
    <table>
      <thead><tr><th>类别</th><th class="right">任务数</th>
        <th class="right">分钟</th><th class="right">占比</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    """


def render_daily(plan: dict, *, preview_days: int = 7) -> str:
    """渲染每日任务卡片。

    - 默认显示前 preview_days 天（折叠其余）
    - 生成「展开全部 / 收起」按钮，纯前端交互，无外部依赖
    """
    daily = plan.get("daily_tasks", [])
    if not daily:
        return ""

    total = len(daily)
    # 至少展示1天，最多展示全部
    preview = min(preview_days, total)

    blocks = []
    for i, d in enumerate(daily):
        date_str = d.get("date", "")
        wd = ""
        try:
            y, m, day = [int(x) for x in date_str.split("-")]
            wd = "周" + WEEKDAY_CN[date_cls(y, m, day).weekday()]
        except Exception:
            pass
        items = []
        for t in d.get("tasks", []):
            label, color, bg = _category_style(t.get("category"))
            tip = t.get("methodology_tip") or ""
            tip_html = f' <span class="muted">· {_esc(tip)}</span>' if tip else ""
            items.append(
                f'<li>'
                f'<span class="badge" style="background:{bg};color:{color};'
                f'border:1px solid {color}33">{_esc(label)}</span>'
                f'{_esc(t.get("title",""))} '
                f'<span class="muted">· {int(t.get("duration_min") or 0)} min</span>'
                f'{tip_html}'
                f'</li>'
            )
        # 第 preview 天之后的卡片默认隐藏
        hidden = i >= preview
        style = ' style="display:none;"' if hidden else ""
        blocks.append(
            f'<div class="day" data-day-index="{i}"{style}><h4>{_esc(date_str)} {_esc(wd)} · '
            f'阶段 {_esc(d.get("stage_id",""))}</h4>'
            f'<ul>{"".join(items)}</ul></div>'
        )

    btn_html = ""
    if total > preview:
        btn_html = (
            f'<button id="toggleDaysBtn" onclick="toggleDays()" '
            f'style="margin:12px 0 8px;padding:8px 18px;background:var(--accent,#2563EB);'
            f'color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">'
            f'展开全部 {total} 天 ▼</button>'
        )

    # JS 用 .format 占位符 {0} {1} 避免与 Python f-string 冲突
    return (
        f'<h2>每日任务（共 {total} 天）</h2>\n'
        f'{btn_html}\n'
        + ''.join(blocks)
        + f'\n<script>\n'
        f'  let _daysExpanded = false;\n'
        f'  function toggleDays() {{\n'
        f'    const cards = document.querySelectorAll(".day[data-day-index]");\n'
        f'    const btn = document.getElementById("toggleDaysBtn");\n'
        f'    _daysExpanded = !_daysExpanded;\n'
        f'    cards.forEach(function(c) {{\n'
        f'      const idx = parseInt(c.getAttribute("data-day-index"));\n'
        f'      c.style.display = (idx < {preview} || _daysExpanded) ? "block" : "none";\n'
        f'    }});\n'
        f'    if (btn) {{\n'
        f'      btn.textContent = _daysExpanded\n'
        f'        ? "收起 ▲" : "展开全部 {total} 天 ▼";\n'
        f'    }}\n'
        f'  }}\n'
        f'</script>\n'
    )


def render_compare(plan: dict, agg: dict) -> str:
    """「不用 skill vs 用本计划」对照段。
    生成基于 plan 实际数据，不画大饼。"""
    meta = plan.get("meta", {})
    days = agg["days"]
    total_h = agg["total_min"] / 60
    weak = meta.get("weak_points") or []
    weak_str = "、".join(weak) if weak else "未识别（建议先跑 self_test 自检）"
    return f"""
    <h2>不用 skill vs 用本计划</h2>
    <div class="compare">
      <div class="col bad">
        <h4>不用任何工具</h4>
        <ul>
          <li>"明天就开始"循环：连续 3 天没动手，截止日逼近</li>
          <li>每天临时决定学啥，决策疲劳吃掉一半精力</li>
          <li>薄弱项被反复绕开（不舒服的事会被本能跳过）</li>
          <li>到考前一周才发现整块没碰过，开始裸考焦虑</li>
        </ul>
      </div>
      <div class="col good">
        <h4>用本计划（{days} 天 · {total_h:.1f}h）</h4>
        <ul>
          <li>每天打开就知道今天学什么，决策成本 = 0</li>
          <li>薄弱项（{_esc(weak_str)}）写进每日任务，绕不开</li>
          <li>阶段节奏可视，紧/正常/缓一眼看到，不会临阵踩刹车</li>
        </ul>
      </div>
    </div>
    <p class="muted">本段不是营销话术，是基于你这份计划的实际数据生成的。</p>
    """


# ============================================================
#                       主渲染
# ============================================================

def render_html(plan: dict) -> str:
    agg = aggregate(plan)
    meta = plan.get("meta", {})
    title = _esc(meta.get("title", "学习计划"))

    body = (
        render_header(plan)
        + render_metrics(agg)
        + render_stages(plan, agg)
        + render_category_chart(agg)
        + render_daily(plan)
        + render_compare(plan, agg)
    )

    plan_id = _esc(plan.get("id", ""))
    schema_v = _esc(plan.get("schema_version") or plan.get("version") or "")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 学习计划报告</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{body}
<div class="footer">
  plan_id: {plan_id} · schema: {schema_v} ·
  由 study-planner 生成（report 屏读版） · 打印请用 <code>plan-print.html</code>
</div>
</div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(
        description="导出 HTML 报告（屏幕浏览版，含 SVG 图）"
    )
    parser.add_argument("plan_id", nargs="?", default=None)
    parser.add_argument("--stdout", action="store_true",
                        help="直接打印 HTML 到 stdout，不写文件")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="报告输出目录（支持 {plan_id} / {cwd} 占位符）；不传则与 plan.json 同目录",
    )
    args = parser.parse_args()

    plan, plan_dir = find_plan(args.plan_id)
    html_str = render_html(plan)

    if args.stdout:
        print(html_str)
        return

    out_dir = resolve_output_dir(plan_dir, plan.get("id"), args.output_dir)
    out_file = out_dir / "plan-report.html"
    out_file.write_text(html_str, encoding="utf-8")
    print(f"[OK] HTML 报告已导出: {out_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
导出为打印友好格式（study-planner 唯一保留的非屏读导出）

设计哲学：
    第三方工具（滴答/iCal/Notion/飞书）的入口已被砍掉——多入口 = 心智断裂、
    打印版是唯一的「物理可见、不可关闭、贴墙抬头就看到」的非数字入口，
    用于对抗手机分心 / 仪式感打卡 / 离家出差时的 offline 备份。

输出：
    plan-print.txt   纯文本兜底（等宽字体打印 / 复制粘贴友好）
    plan-print.html  A4 友好排版（每周一页 / ☐ 复选框 / ★ 弱项标记 /
                     category 徽章 / 阶段总览 / 浏览器 ⌘P 直接打印）

用法：
    python3 to_print.py [plan_id]                # 默认两种都生成
    python3 to_print.py [plan_id] --format html  # 仅 HTML
    python3 to_print.py [plan_id] --format txt   # 仅 TXT
    python3 to_print.py [plan_id] --stdout       # 打印到终端（仅 txt 模式）
"""
import sys
import argparse
import html as _html
from datetime import date as date_cls
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _base import find_plan, category_of, resolve_output_dir  # noqa: E402

HR = "=" * 60
SUB_HR = "-" * 60

# category → (中文标签, 徽章色)
CATEGORY_STYLE = {
    "listening": ("听力", "#3B82F6"),
    "reading": ("阅读", "#10B981"),
    "writing": ("写作", "#F59E0B"),
    "speaking": ("口语", "#EF4444"),
    "vocabulary": ("词汇", "#8B5CF6"),
    "grammar": ("语法", "#EC4899"),
    "review": ("复盘", "#6B7280"),
    "exam": ("模考", "#DC2626"),
    "output": ("输出", "#0EA5E9"),
    "rest": ("休息", "#A3A3A3"),
}
DEFAULT_BADGE = ("其他", "#9CA3AF")

WEEKDAY_CN = ["一", "二", "三", "四", "五", "六", "日"]


# ============================================================
#                          TXT 渲染
# ============================================================

def render_txt(plan: dict) -> str:
    meta = plan["meta"]
    weak = set(meta.get("weak_points") or [])
    lines = []

    # 头部
    lines.append(HR)
    lines.append(f"  {meta['title']}")
    lines.append(HR)
    lines.append("")
    lines.append(f"  目标：{meta['goal']}")
    lines.append(f"  截止：{meta['deadline']}")
    lines.append(f"  当前：{meta.get('current_level', '-')}")
    if meta.get("weak_points"):
        lines.append(f"  弱项：{', '.join(meta['weak_points'])}（任务前缀 ★）")
    budget = meta.get("daily_budget") or {}
    if budget:
        lines.append(
            f"  预算：工作日 {budget.get('weekday', '-')}min / 周末 {budget.get('weekend', '-')}min"
        )
    lines.append("")
    lines.append(HR)
    lines.append("")

    # 阶段
    lines.append("  阶段总览")
    lines.append(SUB_HR)
    for s in plan.get("stages", []):
        lines.append(f"  ◆ {s['name']}（{s['duration_days']} 天）")
        for g in s.get("goals", []):
            lines.append(f"      · {g}")
    lines.append("")
    lines.append(HR)
    lines.append("")

    # 每日任务（每天一段，便于撕开/折叠）
    for d in plan.get("daily_tasks", []):
        try:
            wk = WEEKDAY_CN[date_cls.fromisoformat(d["date"]).weekday()]
            date_label = f"{d['date']} 周{wk}"
        except Exception:
            date_label = d["date"]
        lines.append(f"  {date_label}  [{d['stage_id']}]")
        lines.append(SUB_HR)
        if not d.get("tasks"):
            lines.append("    （休息日）")
        for t in d["tasks"]:
            box = "[ ]" if t.get("checkable", True) else "[·]"
            star = "★ " if (t.get("category") in weak or t.get("title", "") in weak) else "  "
            duration = f"({t.get('duration_min', 0)}min)"
            cat = category_of(t)
            lines.append(f"  {box}  {star}{t['title']}  {duration}  [{cat}]")
            if t.get("resource"):
                lines.append(f"           资料：{t['resource']}")
            if t.get("methodology_tip"):
                lines.append(f"           tip：{t['methodology_tip']}")
        lines.append("")

    lines.append(HR)
    lines.append("  打印小贴士：A4 / 字号 12pt / 等宽字体（SF Mono / Menlo）")
    lines.append("  HTML 版（plan-print.html）排版更友好，浏览器 Cmd+P 直接打印")
    lines.append(HR)
    return "\n".join(lines)


# ============================================================
#                          HTML 渲染
# ============================================================

def _badge(cat: str) -> str:
    label, color = CATEGORY_STYLE.get(cat, DEFAULT_BADGE)
    return (
        f'<span class="badge" style="background:{color}">{_html.escape(label)}</span>'
    )


def _is_weak_task(t: dict, weak_set: set) -> bool:
    if not weak_set:
        return False
    if t.get("category") in weak_set:
        return True
    title = t.get("title", "")
    return any(w and w in title for w in weak_set)


def _iso_week_key(d: str) -> str:
    """返回 'YYYY-Www' 格式，用于按周分页"""
    try:
        dt = date_cls.fromisoformat(d)
        y, w, _ = dt.isocalendar()
        return f"{y}-W{w:02d}"
    except Exception:
        return "Unknown"


def render_html(plan: dict) -> str:
    meta = plan["meta"]
    weak_set = set(meta.get("weak_points") or [])
    title = _html.escape(meta["title"])
    goal = _html.escape(meta.get("goal", ""))
    deadline = _html.escape(meta.get("deadline", ""))
    level = _html.escape(meta.get("current_level", "-"))
    budget = meta.get("daily_budget") or {}
    budget_str = (
        f"工作日 {budget.get('weekday', '-')}min / 周末 {budget.get('weekend', '-')}min"
        if budget
        else "-"
    )
    weak_str = "、".join(meta.get("weak_points") or []) or "-"
    methodology = "、".join(meta.get("methodology") or []) or "-"
    template = _html.escape(meta.get("template_origin", "-"))

    # 阶段总览
    stages_html = []
    for s in plan.get("stages", []):
        goals = "".join(f"<li>{_html.escape(g)}</li>" for g in s.get("goals", []))
        stages_html.append(
            f"""
            <div class="stage-card">
              <div class="stage-name">◆ {_html.escape(s.get('name', ''))}
                <span class="stage-days">{s.get('duration_days', 0)} 天</span>
              </div>
              <ul class="stage-goals">{goals}</ul>
            </div>
            """
        )

    # 按周分组
    by_week: dict = {}
    week_order: list = []
    for d in plan.get("daily_tasks", []):
        key = _iso_week_key(d["date"])
        if key not in by_week:
            by_week[key] = []
            week_order.append(key)
        by_week[key].append(d)

    weeks_html = []
    for idx, wk in enumerate(week_order, start=1):
        days = by_week[wk]
        first_date = days[0]["date"]
        last_date = days[-1]["date"]
        # 计算本周总时长 / 任务数
        total_min = 0
        total_tasks = 0
        for d in days:
            for t in d.get("tasks", []):
                if t.get("checkable", True):
                    total_min += t.get("duration_min", 0) or 0
                    total_tasks += 1

        days_html = []
        for d in days:
            try:
                dt = date_cls.fromisoformat(d["date"])
                wk_label = f"周{WEEKDAY_CN[dt.weekday()]}"
            except Exception:
                wk_label = ""
            tasks = d.get("tasks", [])
            if not tasks:
                tasks_html = '<div class="rest-day">休息日</div>'
            else:
                rows = []
                for t in tasks:
                    checkable = t.get("checkable", True)
                    box = "☐" if checkable else "·"
                    weak_cls = " weak" if _is_weak_task(t, weak_set) else ""
                    star = '<span class="star">★</span>' if weak_cls else ""
                    badge = _badge(t.get("category", ""))
                    duration = t.get("duration_min", 0)
                    title_html = _html.escape(t.get("title", ""))
                    resource = t.get("resource")
                    tip = t.get("methodology_tip")
                    extra = []
                    if resource:
                        extra.append(
                            f'<div class="meta-line">📖 {_html.escape(resource)}</div>'
                        )
                    if tip:
                        extra.append(
                            f'<div class="meta-line tip">💡 {_html.escape(tip)}</div>'
                        )
                    extra_html = "".join(extra)
                    rows.append(
                        f"""
                        <div class="task{weak_cls}">
                          <span class="checkbox">{box}</span>
                          <div class="task-body">
                            <div class="task-title">{star}{title_html}
                              {badge}<span class="duration">{duration}min</span>
                            </div>
                            {extra_html}
                          </div>
                        </div>
                        """
                    )
                tasks_html = "".join(rows)

            days_html.append(
                f"""
                <div class="day">
                  <div class="day-header">
                    <span class="day-date">{_html.escape(d['date'])}</span>
                    <span class="day-weekday">{wk_label}</span>
                    <span class="day-stage">{_html.escape(d.get('stage_id', ''))}</span>
                  </div>
                  {tasks_html}
                </div>
                """
            )

        weeks_html.append(
            f"""
            <section class="week-page">
              <header class="week-header">
                <div>
                  <span class="week-idx">第 {idx} 周</span>
                  <span class="week-range">{_html.escape(first_date)} → {_html.escape(last_date)}</span>
                </div>
                <div class="week-stats">
                  本周 {total_tasks} 个可打卡任务 · 共 {total_min} 分钟
                </div>
              </header>
              {''.join(days_html)}
              <footer class="week-footer">
                本周完成度：☐☐☐☐☐☐☐ &nbsp;&nbsp; 备注：__________________________________________
              </footer>
            </section>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title} · 打印版</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  * {{ box-sizing: border-box; }}
  html, body {{
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    color: #1f2937; line-height: 1.55; margin: 0; padding: 0;
    background: #f3f4f6;
  }}
  .container {{ max-width: 780px; margin: 24px auto; padding: 0 16px; }}
  .cover-page, .week-page {{
    background: #fff; padding: 28px 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
    margin-bottom: 24px; border-radius: 6px;
  }}
  /* 印刷模式：每周一页 */
  @media print {{
    body {{ background: #fff; }}
    .container {{ margin: 0; padding: 0; max-width: none; }}
    .cover-page, .week-page {{
      box-shadow: none; border-radius: 0;
      margin: 0; padding: 0; page-break-after: always;
    }}
    .week-page:last-child {{ page-break-after: auto; }}
    .no-print {{ display: none; }}
  }}

  h1 {{ font-size: 24pt; margin: 0 0 8px; color: #111827; }}
  h2 {{ font-size: 14pt; margin: 18px 0 10px; color: #374151;
       border-bottom: 2px solid #e5e7eb; padding-bottom: 4px; }}

  .subtitle {{ color: #6b7280; font-size: 11pt; margin-bottom: 16px; }}

  .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr);
              gap: 8px 24px; font-size: 11pt; margin: 12px 0; }}
  .meta-grid div {{ padding: 6px 0; border-bottom: 1px dashed #e5e7eb; }}
  .meta-grid b {{ color: #4b5563; margin-right: 6px; }}

  .stage-card {{ padding: 10px 14px; margin: 8px 0;
                background: #f9fafb; border-left: 3px solid #6366f1;
                border-radius: 4px; }}
  .stage-name {{ font-weight: 600; font-size: 12pt; }}
  .stage-days {{ font-size: 10pt; color: #6b7280; margin-left: 8px;
                font-weight: normal; }}
  .stage-goals {{ margin: 6px 0 0 16px; padding: 0; font-size: 10.5pt; color: #374151; }}
  .stage-goals li {{ margin: 2px 0; }}

  .week-header {{ display: flex; justify-content: space-between;
                 align-items: baseline; padding-bottom: 10px;
                 border-bottom: 2px solid #111827; margin-bottom: 12px; }}
  .week-idx {{ font-size: 16pt; font-weight: 700; color: #111827;
              margin-right: 12px; }}
  .week-range {{ color: #6b7280; font-size: 11pt; }}
  .week-stats {{ font-size: 10pt; color: #6b7280; }}

  .day {{ margin: 14px 0; padding: 10px 12px;
         background: #fafafa; border-radius: 4px;
         break-inside: avoid; }}
  .day-header {{ display: flex; gap: 10px; align-items: baseline;
                margin-bottom: 8px; padding-bottom: 4px;
                border-bottom: 1px dashed #d1d5db; }}
  .day-date {{ font-size: 12pt; font-weight: 600; color: #111827; }}
  .day-weekday {{ font-size: 10pt; color: #4b5563;
                 background: #e5e7eb; padding: 1px 6px; border-radius: 3px; }}
  .day-stage {{ font-size: 9pt; color: #9ca3af; margin-left: auto; }}

  .task {{ display: flex; gap: 8px; padding: 6px 4px;
          align-items: flex-start; break-inside: avoid; }}
  .task.weak {{ background: #fef3c7; border-radius: 3px; }}
  .checkbox {{ font-size: 16pt; line-height: 1; color: #374151;
              font-family: "Helvetica Neue", sans-serif;
              min-width: 18px; }}
  .task-body {{ flex: 1; }}
  .task-title {{ font-size: 11pt; font-weight: 500; color: #111827;
                display: flex; align-items: center; gap: 6px;
                flex-wrap: wrap; }}
  .star {{ color: #d97706; font-weight: 700; }}
  .badge {{ display: inline-block; padding: 1px 7px; border-radius: 9px;
           color: #fff; font-size: 8.5pt; font-weight: 500; }}
  .duration {{ font-size: 9.5pt; color: #6b7280; }}
  .meta-line {{ font-size: 9.5pt; color: #4b5563; margin-top: 2px;
               padding-left: 26px; }}
  .meta-line.tip {{ color: #7c3aed; font-style: italic; }}

  .rest-day {{ color: #9ca3af; font-style: italic;
              padding: 8px 0; text-align: center; }}

  .week-footer {{ margin-top: 14px; padding-top: 10px;
                 border-top: 1px dashed #d1d5db;
                 font-size: 10pt; color: #6b7280;
                 letter-spacing: 1px; }}

  .legend {{ font-size: 10pt; color: #6b7280; margin-top: 16px;
            padding: 10px 14px; background: #f3f4f6; border-radius: 4px; }}
  .legend code {{ background: #fff; padding: 1px 6px; border-radius: 3px;
                 border: 1px solid #e5e7eb; font-family: SF Mono, Menlo, monospace; }}

  .print-tip {{ position: fixed; top: 12px; right: 12px;
               background: #6366f1; color: #fff; padding: 8px 14px;
               border-radius: 6px; font-size: 11pt;
               box-shadow: 0 2px 8px rgba(0,0,0,.2); cursor: pointer; }}
</style>
</head>
<body>
<div class="no-print print-tip" onclick="window.print()">🖨️ 点此打印（或 Cmd+P）</div>
<div class="container">

  <!-- 封面页 -->
  <section class="cover-page">
    <h1>{title}</h1>
    <div class="subtitle">study-planner · 打印版（贴墙 / 夹书 / 离线打卡）</div>
    <div class="meta-grid">
      <div><b>🎯 目标：</b>{goal}</div>
      <div><b>📅 截止：</b>{deadline}</div>
      <div><b>📊 当前：</b>{level}</div>
      <div><b>⚠️ 弱项：</b>{_html.escape(weak_str)}</div>
      <div><b>⏱️ 预算：</b>{_html.escape(budget_str)}</div>
      <div><b>📐 模板：</b>{template}</div>
      <div style="grid-column: 1 / -1;"><b>🧠 方法论：</b>{_html.escape(methodology)}</div>
    </div>

    <h2>阶段总览</h2>
    {''.join(stages_html)}

    <div class="legend">
      <b>图例：</b>
      <code>☐</code> 待打卡 &nbsp;
      <code>·</code> 不计入打卡（开放式任务） &nbsp;
      <code style="color:#d97706;">★</code> 弱项加权任务（命中 weak_points） &nbsp;
      彩色徽章 = 任务类别（听力/阅读/写作/...）
      <br>
      <b>使用建议：</b>每周撕一页贴书桌，做完一项打 ✓；周末用底部"完成度"圆圈给自己打分，用空白处写复盘备注。
    </div>
  </section>

  {''.join(weeks_html)}

</div>
</body>
</html>
"""


# ============================================================
#                            CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="study-planner 打印版导出器（保留唯一非屏读入口）"
    )
    parser.add_argument("plan_id", nargs="?", default=None)
    parser.add_argument(
        "--format",
        choices=["txt", "html", "both"],
        default="both",
        help="导出格式（默认 both = txt + html）",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="打印 txt 到终端（仅 --format txt 时生效）",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="报告输出目录（支持 {plan_id} / {cwd} 占位符）；不传则与 plan.json 同目录",
    )
    args = parser.parse_args()

    plan, plan_dir = find_plan(args.plan_id)
    out_dir = resolve_output_dir(plan_dir, plan.get("id"), args.output_dir)

    outputs = []

    if args.format in ("txt", "both"):
        text = render_txt(plan)
        if args.stdout and args.format == "txt":
            print(text)
        else:
            f_txt = out_dir / "plan-print.txt"
            f_txt.write_text(text, encoding="utf-8")
            outputs.append(("TXT 纯文本", f_txt))

    if args.format in ("html", "both"):
        html_doc = render_html(plan)
        f_html = out_dir / "plan-print.html"
        f_html.write_text(html_doc, encoding="utf-8")
        outputs.append(("HTML A4 打印版", f_html))

    if not outputs:
        return

    print("[OK] 打印版已导出：")
    for label, path in outputs:
        size_kb = path.stat().st_size / 1024
        print(f"  · {label:<14} {path}  ({size_kb:.1f} KB)")
    print()
    print("打印步骤：")
    print("  · HTML（推荐）：双击 plan-print.html → 浏览器 Cmd+P → A4 / 纵向 / 背景图形开")
    print("  · TXT 兜底   ：等宽字体打印或 cat 到终端复制")
    print("  · 每周一页   ：HTML 版自动按 ISO 周分页，撕下贴书桌即可")


if __name__ == "__main__":
    main()

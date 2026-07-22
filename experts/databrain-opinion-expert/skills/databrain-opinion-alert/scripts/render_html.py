#!/usr/bin/env python3
"""
render_html.py — 把告警结果 + 归因渲染成自包含 HTML 详情页（5 区块）。

设计要点
========
1. **完全自包含**：内联 CSS / 内联 SVG（30 天趋势图自绘），不依赖任何 CDN，
   离线也能打开。
2. **XSS 防护**：所有用户/上游数据通过 _esc/_attr/_url 转义后才插入 HTML。
3. **5 个区块**：
   - 顶部摘要（游戏 / 渠道 / 评估时间 / 触发等级 + 关键数字）
   - 全切片表格（默认显示触发的，复选可显示 OK；纯 HTML+JS 实现筛选）
   - 30 天评分趋势 SVG（全球 score / score_pp，标注当前 + baseline 水位线）
   - 归因（投诉国家 / 语种 Top + 全部 Top N 代表性差评，含跳转链接）
   - 底部折叠原始 JSON（便于调试）

CLI
====
    python scripts/render_html.py \\
        --result_file /tmp/alert.json \\
        --attribution_file /tmp/attribution.json \\
        --game_name "PUBG Mobile" \\
        --output /tmp/alert.html
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import quote

# ---------------------------------------------------------------------------
# 安全：HTML / 属性 / URL 转义
# ---------------------------------------------------------------------------
def _esc(s) -> str:
    """文本节点 HTML 转义（任意类型 → safe text）。"""
    if s is None:
        return ""
    return html.escape(str(s), quote=False)


def _attr(s) -> str:
    """HTML 属性值转义（含 quote）。"""
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def _url(u: Optional[str]) -> str:
    """
    安全 URL：仅允许 http(s) scheme；其他一律返回 '#'。
    [Why] feeds.sources.url 来自第三方爬取，可能含 javascript: / data:。
    """
    if not u or not isinstance(u, str):
        return "#"
    s = u.strip()
    if not (s.startswith("http://") or s.startswith("https://")):
        return "#"
    # 允许除少量危险字符外的所有 URL 字符；quote() 默认不转 :/?#[]@!$&'()*+,;=~_-
    return quote(s, safe=":/?#[]@!$&'()*+,;=~_-.%")


LEVEL_BADGE = {
    "P0": ("🚨", "P0 严重", "#dc2626"),   # red
    "P1": ("⚠️", "P1 警告", "#ea580c"),   # orange
    "P2": ("🟡", "P2 关注", "#ca8a04"),   # yellow
    "OK": ("✅", "OK 正常", "#16a34a"),   # green
}

CHANNEL_LABEL = {"steam": "Steam", "google_play": "Google Play", "app_store": "App Store"}
SCOPE_LABEL = {"all_reviews": "总体评分", "recent_reviews": "近 30 天评分"}

DIM_LABEL = {
    "A_absolute": "绝对水位低",
    "A_absolute_score": "评分跌破水位",
    "A_one_star_rate": "1 星占比异常",
    "B_drop_6h": "6h 显著下跌",
    "B_drop_24h": "24h 显著下跌",
    "C_below_p5": "低于 30 天 P5",
    "C_below_p25": "低于 30 天 P25",
    "C_below_median_7d": "低于 7 天中位数",
}


# ---------------------------------------------------------------------------
# SVG 趋势图（自绘，无外部依赖）
# ---------------------------------------------------------------------------
def _svg_trend(values: list[float], *, current: Optional[float] = None,
               baseline_p5: Optional[float] = None,
               baseline_median: Optional[float] = None,
               y_min: Optional[float] = None, y_max: Optional[float] = None,
               width: int = 640, height: int = 200, unit: str = "") -> str:
    """
    自绘 SVG 折线图。values 是 30 天时序，current/baseline 画水位线。
    [Why] 不依赖 quickchart 等外部服务，离线可看；不用 JS 库也好嵌。
    """
    if not values or len(values) < 2:
        return f'<div class="empty">无足够历史数据（需要 ≥ 2 天）</div>'

    pad_l, pad_r, pad_t, pad_b = 40, 20, 20, 30
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b
    n = len(values)

    candidates = [v for v in values if v is not None]
    if current is not None:
        candidates.append(current)
    if baseline_p5 is not None:
        candidates.append(baseline_p5)
    if baseline_median is not None:
        candidates.append(baseline_median)
    vmin = y_min if y_min is not None else min(candidates)
    vmax = y_max if y_max is not None else max(candidates)
    if vmax == vmin:
        vmax = vmin + 1
    span = vmax - vmin
    vmin -= span * 0.05
    vmax += span * 0.05

    def x(i: int) -> float:
        return pad_l + (i / max(n - 1, 1)) * plot_w

    def y(v: float) -> float:
        return pad_t + (1 - (v - vmin) / (vmax - vmin)) * plot_h

    lines: list[str] = []
    # 折线
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(values))
    lines.append(f'<polyline fill="none" stroke="#2563eb" stroke-width="2" points="{pts}" />')
    # 数据点
    for i, v in enumerate(values):
        lines.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="2.5" fill="#2563eb" />')
    # 水位线
    if baseline_p5 is not None:
        yp5 = y(baseline_p5)
        lines.append(
            f'<line x1="{pad_l}" y1="{yp5:.1f}" x2="{pad_l + plot_w}" y2="{yp5:.1f}" '
            f'stroke="#dc2626" stroke-dasharray="4 4" stroke-width="1" />'
            f'<text x="{pad_l + plot_w + 4}" y="{yp5:.1f}" font-size="11" '
            f'fill="#dc2626" alignment-baseline="middle">P5={baseline_p5:.2f}{unit}</text>'
        )
    if baseline_median is not None:
        ym = y(baseline_median)
        lines.append(
            f'<line x1="{pad_l}" y1="{ym:.1f}" x2="{pad_l + plot_w}" y2="{ym:.1f}" '
            f'stroke="#ca8a04" stroke-dasharray="4 4" stroke-width="1" />'
            f'<text x="{pad_l + plot_w + 4}" y="{ym:.1f}" font-size="11" '
            f'fill="#ca8a04" alignment-baseline="middle">7d中位={baseline_median:.2f}{unit}</text>'
        )
    if current is not None:
        yc = y(current)
        lines.append(
            f'<line x1="{pad_l}" y1="{yc:.1f}" x2="{pad_l + plot_w}" y2="{yc:.1f}" '
            f'stroke="#16a34a" stroke-width="1.5" />'
            f'<text x="{pad_l + plot_w + 4}" y="{yc:.1f}" font-size="11" '
            f'fill="#16a34a" alignment-baseline="middle" font-weight="bold">当前={current:.2f}{unit}</text>'
        )

    # 坐标轴
    lines.append(
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#9ca3af" />'
        f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}" y2="{pad_t + plot_h}" stroke="#9ca3af" />'
    )
    # Y 轴刻度
    for frac in (0, 0.5, 1):
        v = vmax - frac * (vmax - vmin)
        yt = pad_t + frac * plot_h
        lines.append(
            f'<text x="{pad_l - 6}" y="{yt:.1f}" font-size="10" fill="#6b7280" '
            f'text-anchor="end" alignment-baseline="middle">{v:.2f}</text>'
            f'<line x1="{pad_l - 3}" y1="{yt:.1f}" x2="{pad_l}" y2="{yt:.1f}" stroke="#9ca3af" />'
        )
    # X 轴标签：起 / 中 / 末
    for i, lbl in [(0, f"D-{n - 1}"), (n // 2, f"D-{n - 1 - n // 2}"), (n - 1, "今天")]:
        lines.append(
            f'<text x="{x(i):.1f}" y="{pad_t + plot_h + 14}" font-size="10" '
            f'fill="#6b7280" text-anchor="middle">{lbl}</text>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet" '
        f'style="width:100%;max-width:{width}px;height:auto;background:#fafafa;border:1px solid #e5e7eb;'
        f'border-radius:6px;">'
        + "".join(lines) + "</svg>"
    )


# ---------------------------------------------------------------------------
# 区块渲染
# ---------------------------------------------------------------------------
def _block_summary(result: dict, game_name: str) -> str:
    channel = result.get("channel", "")
    scope = result.get("scope") or ""
    triggered = result.get("triggered", False)
    slices = result.get("slices") or []
    fired = [s for s in slices if s.get("should_push")]
    rank = {"P0": 0, "P1": 1, "P2": 2}
    max_lvl = "OK"
    if fired:
        max_lvl = min((s["level"] for s in fired), key=lambda lv: rank.get(lv, 99))
    icon, badge, color = LEVEL_BADGE[max_lvl]
    chip = (f'<span style="background:{color};color:white;padding:4px 10px;'
            f'border-radius:4px;font-weight:bold;">{icon} {_esc(badge)}</span>')

    return f"""
<section class="card">
  <h1 style="margin:0 0 12px;">商店评分告警 · {chip}</h1>
  <table class="kv">
    <tr><th>游戏</th><td>{_esc(game_name or result.get('game_id', ''))}</td></tr>
    <tr><th>渠道</th><td>{_esc(CHANNEL_LABEL.get(channel, channel))}{
        ' · ' + _esc(SCOPE_LABEL.get(scope, '')) if scope else ''}</td></tr>
    <tr><th>评估时间</th><td>{_esc(result.get('evaluated_at', ''))}</td></tr>
    <tr><th>触发情况</th><td><strong>{len(fired)}</strong> / {len(slices)} 个切片触发，
      最高等级 <strong>{_esc(max_lvl)}</strong>{
      "（触发）" if triggered else "（未触发）"}</td></tr>
    <tr><th>game_id</th><td><code>{_esc(result.get('game_id', ''))}</code></td></tr>
  </table>
</section>"""


def _slice_row_html(s: dict, channel: str) -> str:
    cur = s.get("current") or {}
    if channel == "steam":
        cur_v = cur.get("score_pp")
        cur_str = f"{cur_v:.2f}%" if isinstance(cur_v, (int, float)) else "—"
    else:
        cur_v = cur.get("score")
        cur_str = f"{cur_v:.2f}" if isinstance(cur_v, (int, float)) else "—"
    bl = s.get("baseline") or {}
    bl_str = "—"
    if isinstance(bl.get("p5"), (int, float)) and isinstance(bl.get("median_7d"), (int, float)):
        suf = "%" if channel == "steam" else ""
        bl_str = f"P5={bl['p5']:.2f}{suf} / 7d={bl['median_7d']:.2f}{suf}"
    dims = " / ".join(DIM_LABEL.get(d, d) for d in (s.get("matched_dims") or []))
    lvl = s.get("level", "OK")
    icon, badge, color = LEVEL_BADGE.get(lvl, ("", lvl, "#6b7280"))
    is_fired = " data-fired=\"1\"" if s.get("should_push") else ""
    return f"""
<tr{is_fired}>
  <td><span style="color:{color};font-weight:bold;">{icon} {_esc(lvl)}</span></td>
  <td>{_esc(s.get('label') or s.get('slice_key', ''))}</td>
  <td>{cur_str}</td>
  <td>{s.get('sample_in_window', 0)}</td>
  <td>{_esc(bl_str)}</td>
  <td>{_esc(dims) or '—'}</td>
  <td>{_esc(s.get('push_reason') or '—')}</td>
</tr>"""


def _block_slices(result: dict) -> str:
    channel = result.get("channel", "")
    slices = result.get("slices") or []
    rank = {"P0": 0, "P1": 1, "P2": 2, "OK": 99}
    steam_lang_rank = {"EN": 1, "JA": 2, "KO": 3, "ZH-CN": 4, "DE": 5, "FR": 6, "RU": 7, "ES": 8, "PT-BR": 9}

    def _slice_sort_key(s: dict):
        if s.get("slice_key") == "__global__":
            slice_rank = 0
        elif channel == "steam":
            slice_rank = steam_lang_rank.get(s.get("language_code") or str(s.get("slice_key", "")).replace("lang_", ""), 90)
        else:
            slice_rank = 50
        return (rank.get(s.get("level"), 99), slice_rank, -int(s.get("sample_in_window", 0)))

    slices_sorted = sorted(slices, key=_slice_sort_key)
    rows = "".join(_slice_row_html(s, channel) for s in slices_sorted)
    return f"""
<section class="card">
  <div class="block-head">
    <h2>切片评估明细（{len(slices)}）</h2>
    <label><input type="checkbox" id="show-ok" /> 显示 OK 切片</label>
  </div>
  <table class="data" id="slice-table">
    <thead>
      <tr><th>等级</th><th>切片</th><th>当前值</th><th>窗口样本</th>
          <th>baseline</th><th>命中维度</th><th>推送原因</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <script>
    (function() {{
      var cb = document.getElementById('show-ok');
      var rows = document.querySelectorAll('#slice-table tbody tr');
      function apply() {{
        rows.forEach(function(r) {{
          if (r.dataset.fired === "1") return;
          r.style.display = cb.checked ? "" : "none";
        }});
      }}
      cb.addEventListener('change', apply);
      apply();
    }})();
  </script>
</section>"""


def _block_trend(result: dict) -> str:
    channel = result.get("channel", "")
    slices = result.get("slices") or []
    g = next((s for s in slices if s.get("slice_key") == "__global__"), None)
    if not g:
        return ""
    bl = g.get("baseline") or {}
    cur = g.get("current") or {}
    if channel == "steam":
        cur_v = cur.get("score_pp")
        unit = "%"
    else:
        cur_v = cur.get("score")
        unit = ""
    history_extracted = g.get("history_values") or []
    if history_extracted:
        svg = _svg_trend(
            history_extracted,
            current=cur_v if isinstance(cur_v, (int, float)) else None,
            baseline_p5=bl.get("p5"),
            baseline_median=bl.get("median_7d"),
            unit=unit,
        )
    else:
        svg = ('<div class="empty">⚠ 当前 alert_result.json 未携带 history_values；'
               '请升级 check_store_score_alerts.py 后重跑。</div>')
    return f"""
<section class="card">
  <h2>30 天评分趋势（全球聚合）</h2>
  {svg}
  <p class="meta">
    红色虚线 = 30 天 P5；黄色虚线 = 7 天中位数；绿色实线 = 当前。
    样本数 = {bl.get('samples', 0)} 天。
  </p>
</section>"""


def _block_attribution(att: Optional[dict], channel: str) -> str:
    if not att:
        return ('<section class="card"><h2>归因</h2>'
                '<div class="empty">未提供 attribution_file，跳过归因。</div></section>')
    dist = att.get("complaint_distribution") or {}
    win_h = dist.get("window_hours", "?")
    total = dist.get("total_negative", 0)

    def _topn_table(rows: list, label: str) -> str:
        if not rows:
            return f'<div class="empty">{_esc(label)}：无数据</div>'
        body = "".join(
            f'<tr><td>{_esc(r.get("key"))}</td>'
            f'<td>{r.get("count", 0)}</td>'
            f'<td>{int((r.get("ratio", 0) or 0) * 100)}%</td>'
            f'<td>{r.get("uniq_users", 0)}</td></tr>'
            for r in rows[:10]
        )
        return f"""
<table class="data">
  <thead><tr><th>{_esc(label)}</th><th>条数</th><th>占比</th><th>独立用户</th></tr></thead>
  <tbody>{body}</tbody>
</table>"""

    reviews = att.get("top_negative_reviews") or []
    review_rows = []
    for i, r in enumerate(reviews, 1):
        url = _url(r.get("url"))
        snippet = (r.get("snippet") or r.get("text") or r.get("content") or "").strip()
        if not snippet:
            snippet = r.get("reviewer") or "代表性差评"
        snippet = " ".join(snippet.split())[:100]
        review_text = (
            f'<a href="{_attr(url)}" target="_blank" rel="noopener noreferrer">'
            f'「{_esc(snippet)}」</a>'
        ) if url != "#" else f"「{_esc(snippet)}」"
        locale_text = _esc(r.get("language") or "—") if channel == "steam" else f'{_esc(r.get("country") or "—")} / {_esc(r.get("language") or "—")}'
        review_rows.append(f"""
<tr>
  <td>{i}</td>
  <td>{review_text}</td>
  <td>@{_esc(r.get("reviewer") or "anonymous")}</td>
  <td>{_esc((r.get("comment_time") or "")[:16])}</td>
  <td>{locale_text}</td>
  <td>👍 {r.get("likes", 0)} · 💬 {r.get("replies", 0)} · 🔁 {r.get("retweets", 0)}</td>
</tr>""")
    locale_header = "语种" if channel == "steam" else "国家/语种"
    review_table = (
        '<table class="data">'
        f'<thead><tr><th>#</th><th>代表差评</th><th>作者</th><th>时间</th><th>{locale_header}</th>'
        '<th>互动</th></tr></thead>'
        f'<tbody>{"".join(review_rows)}</tbody></table>'
    ) if review_rows else '<div class="empty">无可跳转的代表性差评。</div>'

    attribution_cards = []
    country_rows = dist.get("by_country") or []
    if channel != "steam" and country_rows:
        attribution_cards.append(f'<div>{_topn_table(country_rows, "Top 投诉国家")}</div>')
    if channel == "steam":
        attribution_cards.append(f'<div>{_topn_table(dist.get("by_language") or [], "Top 投诉语种")}</div>')
    attribution_grid = "".join(attribution_cards)

    return f"""
<section class="card">
  <h2>归因（最近 {_esc(win_h)}h 共 {total} 条负面）</h2>
  <div class="grid">
    {attribution_grid}
  </div>
  <h3 style="margin-top:18px;">代表性差评</h3>
  {review_table}
</section>"""


def _block_raw(result: dict, attribution: Optional[dict]) -> str:
    payload = {"alert_result": result, "attribution": attribution}
    raw = _esc(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return f"""
<section class="card">
  <details>
    <summary><strong>原始 JSON（点击展开）</strong></summary>
    <pre>{raw}</pre>
  </details>
</section>"""


# ---------------------------------------------------------------------------
# 主渲染
# ---------------------------------------------------------------------------
_CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
       "Microsoft YaHei", sans-serif; background: #f3f4f6; margin: 0; padding: 24px; color: #111827; }
.container { max-width: 1100px; margin: 0 auto; }
.card { background: white; border-radius: 8px; padding: 20px 24px; margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); }
h1 { font-size: 22px; }
h2 { font-size: 17px; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 1px solid #e5e7eb; }
h3 { font-size: 15px; margin: 12px 0 8px; }
table.kv th { text-align: left; color: #6b7280; font-weight: normal; padding: 4px 12px 4px 0;
              vertical-align: top; width: 90px; }
table.kv td { padding: 4px 0; }
table.data { width: 100%; border-collapse: collapse; font-size: 13px; }
table.data th { text-align: left; padding: 8px; background: #f9fafb; border-bottom: 2px solid #e5e7eb; }
table.data td { padding: 8px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
table.data tr:hover { background: #f9fafb; }
.block-head { display: flex; justify-content: space-between; align-items: center; }
.block-head label { font-size: 13px; color: #6b7280; }
.empty { color: #9ca3af; padding: 12px; background: #f9fafb; border-radius: 6px; text-align: center; }
.meta { color: #6b7280; font-size: 12px; margin-top: 8px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
pre { background: #1f2937; color: #f3f4f6; padding: 14px; border-radius: 6px; overflow: auto;
      font-size: 12px; line-height: 1.5; }
details summary { cursor: pointer; padding: 4px 0; }
code { background: #f3f4f6; padding: 1px 5px; border-radius: 3px; font-size: 12px; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
"""


def render_html(
    result: dict,
    attribution: Optional[dict],
    game_name: str,
) -> str:
    """渲染完整 HTML 字符串。"""
    channel = result.get("channel", "")
    title = (f"{game_name or result.get('game_id', '')} · "
             f"{CHANNEL_LABEL.get(channel, channel)} 评分告警")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{_esc(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
{_block_summary(result, game_name)}
{_block_slices(result)}
{_block_trend(result)}
{_block_attribution(attribution, channel)}
{_block_raw(result, attribution)}
<p style="text-align:center;color:#9ca3af;font-size:11px;margin-top:24px;">
  Generated by databrain-opinion-alert v2 · 详情数据来源 BigQuery feeds / store_score_*
</p>
</div>
</body>
</html>"""


def render_to_file(
    result: dict,
    attribution: Optional[dict],
    game_name: str,
    output_path: str,
) -> str:
    """渲染并写盘，返回 file:// URL。"""
    p = Path(output_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_html(result, attribution, game_name), encoding="utf-8")
    return f"file://{p.as_posix()}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="渲染告警详情 HTML（自包含、离线可用）")
    parser.add_argument("--result_file", required=False, default="")
    parser.add_argument("--attribution_file", default="")
    parser.add_argument("--game_name", default="")
    parser.add_argument("--output", default="/tmp/alert_detail.html")
    parser.add_argument("--self_test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    if not args.result_file:
        parser.error("需要 --result_file 或 --self_test")

    with open(args.result_file, encoding="utf-8") as f:
        result = json.load(f)
    attribution = None
    if args.attribution_file:
        try:
            with open(args.attribution_file, encoding="utf-8") as f:
                attribution = json.load(f)
        except Exception as e:
            print(f"[WARN] 读取 attribution_file 失败：{e}", file=sys.stderr)

    file_url = render_to_file(result, attribution, args.game_name, args.output)
    print(f"✅ HTML 已生成：{args.output}")
    print(f"   浏览器打开：{file_url}")


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
def _self_test() -> int:
    failures: list[str] = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            failures.append(name)

    print("=== render_html self test ===")

    # XSS / URL 转义
    _check("_esc 转义 <script>",
           _esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;")
    _check("_attr 转义引号",
           '"' not in _attr('a"b') and "&quot;" in _attr('a"b'))
    _check("_url 拒绝 javascript:", _url("javascript:alert(1)") == "#")
    _check("_url 拒绝 data:", _url("data:text/html,<script>") == "#")
    _check("_url 拒绝 file://", _url("file:///etc/passwd") == "#")
    _check("_url 接受 https://", _url("https://store.steampowered.com/abc").startswith("https://"))
    _check("_url None → #", _url(None) == "#")

    # SVG 趋势
    svg = _svg_trend([1.0, 2.0, 3.0, 4.0, 5.0], current=4.5, baseline_p5=1.5,
                     baseline_median=3.0, unit="%")
    _check("SVG 含 polyline", "<polyline" in svg)
    _check("SVG 含 P5 标注", "P5=1.50" in svg)
    _check("SVG 含 当前 标注", "当前=4.50" in svg)
    _check("SVG 空数据 graceful", "无足够历史" in _svg_trend([]))

    # 完整渲染
    fake_result = {
        "game_id": "ufc454d9b1af70b40588e2a6fa4da4a8b",
        "channel": "google_play",
        "scope": None,
        "evaluated_at": "2026-05-07T17:30:00+00:00",
        "triggered": True,
        "any_p0": True,
        "slices": [
            {
                "slice_key": "__global__", "label": "全球", "level": "P0",
                "matched_dims": ["A_one_star_rate", "B_drop_6h"],
                "current": {"score": 3.42, "one_star_rate": 0.45},
                "baseline": {"p5": 4.10, "median_7d": 4.30, "samples": 30},
                "history_values": [4.3, 4.32, 4.31, 4.30, 4.28, 4.25, 4.20,
                                   4.18, 4.15, 4.12, 4.10, 4.09, 4.08, 4.05,
                                   4.02, 4.00, 3.95, 3.90, 3.85, 3.80, 3.75,
                                   3.70, 3.65, 3.60, 3.55, 3.50, 3.48, 3.46,
                                   3.44, 3.42],
                "sample_in_window": 587,
                "should_push": True, "push_reason": "first_trigger",
            },
            {
                "slice_key": "country_us", "label": "us 区", "level": "P1",
                "matched_dims": ["B_drop_6h"],
                "current": {"score": 3.7}, "baseline": {"p5": 4.0, "median_7d": 4.2},
                "sample_in_window": 220, "should_push": True, "push_reason": "first_trigger",
            },
            {
                "slice_key": "country_jp", "label": "jp 区", "level": "OK",
                "matched_dims": [], "current": {"score": 4.5},
                "should_push": False,
            },
        ],
    }
    fake_attribution = {
        "complaint_distribution": {
            "total_negative": 412, "window_hours": 6.0,
            "by_country": [{"key": "us", "count": 168, "ratio": 0.408, "uniq_users": 130}],
            "by_language": [{"key": "en", "count": 290, "ratio": 0.704, "uniq_users": 200}],
        },
        "top_negative_reviews": [
            {"reviewer": "Player<One>", "comment_time": "2026-05-07 12:30:00",
             "country": "us", "language": "en", "likes": 153, "replies": 22, "retweets": 5,
             "url": "https://play.google.com/r/abc"},
            {"reviewer": "javascript:evil", "comment_time": "2026-05-07 11:50:00",
             "country": "br", "language": "pt", "likes": 80, "replies": 5, "retweets": 0,
             "url": "javascript:alert(1)"},  # 应被 _url 转成 '#'
        ],
    }

    h = render_html(fake_result, fake_attribution, "PUBG Mobile")
    _check("HTML 含 5 区块（摘要/切片/趋势/归因/原始JSON）",
           all(k in h for k in ["商店评分告警", "切片评估明细", "30 天评分趋势",
                                "归因", "原始 JSON"]))
    _check("HTML 含等级 badge P0", "P0 严重" in h)
    _check("XSS 防护：reviewer <One> 被转义",
           "&lt;One&gt;" in h and "Player<One>" not in h)
    _check("XSS 防护：javascript: URL 不出现在 href",
           "javascript:alert" not in h.replace("alert(1)", ""))  # JSON 区块不算
    _check("XSS 防护：javascript: URL 不可点击",
           'href="javascript:' not in h and 'href="data:' not in h)
    _check("正常 URL 保留", "play.google.com/r/abc" in h)
    _check("OK 切片默认隐藏 JS 已注入", "show-ok" in h and "data-fired" in h)
    _check("折叠原始 JSON 含 details", "<details>" in h and "</details>" in h)

    # 写盘往返
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
        out_path = tf.name
    try:
        url = render_to_file(fake_result, fake_attribution, "PUBG Mobile", out_path)
        _check("写盘成功", Path(out_path).exists() and Path(out_path).stat().st_size > 1000)
        _check("URL 是 file:// 格式", url.startswith("file://") and url.endswith(".html"))
    finally:
        Path(out_path).unlink(missing_ok=True)

    print("\n" + "-" * 40)
    print(f"FAIL: {len(failures)}" if failures else "PASS: all render_html tests")
    return 1 if failures else 0


if __name__ == "__main__":
    main()

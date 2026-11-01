"""经营周报/月报 — 报告插件（capability_id=1）

从 ecommerce_report.py 搬出的 generate_trade_findings()，逻辑完全不变。

JSON 需要:
  - overview / previous_overview
  - daily_summary / previous_daily_summary
  - weekly_trend
  - refund_by_category（可选）
  - finding_narratives（可选，hybrid 模式文案覆盖）
"""

import json
import sys
import os

# 确保父目录在 path 中，以便 import ecommerce_report 的工具函数
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecommerce_report import (
    _sf, _si, _esc, fmt_yuan, fmt_yuan_simple, fmt_num, fmt_pct, fmt_decimal,
    fmt_date_short, _weekday_cn, compute_derived, _color_span, _pct_change,
)


def generate_findings(data: dict) -> list:
    """交易域能力1（日常经营看板）自动生成 5 个标准 findings。"""
    ov = data.get("overview", {})
    prev_ov = data.get("previous_overview", {})
    daily = data.get("daily_summary", [])
    prev_daily = data.get("previous_daily_summary", [])
    weekly = data.get("weekly_trend", [])
    refund_cat = data.get("refund_by_category", [])

    narratives = data.get("finding_narratives", [])
    def _narr(idx):
        return narratives[idx] if idx < len(narratives) else None

    d = compute_derived(ov)
    pd_ = compute_derived(prev_ov) if prev_ov else {}

    findings = []
    chart_counter = [0]

    def _cid(prefix="chart"):
        chart_counter[0] += 1
        return f"{prefix}_{chart_counter[0]}"

    # ────────────────────────────────────────────
    # F1: 逐日 GMV 走势
    # ────────────────────────────────────────────
    if daily:
        peak_day = max(daily, key=lambda r: _sf(r.get("gmv")))
        peak_date = fmt_date_short(peak_day["stat_date"])
        peak_wd = _weekday_cn(peak_day["stat_date"])
        peak_gmv = _sf(peak_day["gmv"])
        total_gmv = _sf(ov.get("gmv"))
        peak_pct = peak_gmv / total_gmv * 100 if total_gmv else 0

        rows = []
        for r in daily:
            dt = fmt_date_short(r["stat_date"])
            wd = f"周{_weekday_cn(r['stat_date'])}"
            gmv_v = fmt_yuan(_sf(r.get("gmv")))
            idx = daily.index(r)
            prev_gmv = _sf(prev_daily[idx].get("gmv")) if idx < len(prev_daily) else 0
            chg = _pct_change(r.get("gmv"), prev_gmv)
            chg_html = _color_span(chg) if chg is not None else "-"
            rows.append([dt, wd, gmv_v,
                         fmt_yuan(prev_gmv) if prev_gmv else "-",
                         chg_html,
                         fmt_num(r.get("pay_uv")),
                         fmt_yuan_simple(d["aov"] if _sf(r.get("pay_uv")) == 0 else _sf(r.get("gmv")) / _sf(r.get("pay_uv")))])

        gmv_chg = _pct_change(ov.get("gmv"), prev_ov.get("gmv"))
        summary = [
            "<strong>合计</strong>", "—",
            f"<strong>{fmt_yuan(total_gmv)}</strong>",
            f"<strong>{fmt_yuan(prev_ov.get('gmv'))}</strong>",
            f"<strong>{_color_span(gmv_chg) if gmv_chg is not None else '-'}</strong>",
            f"<strong>{fmt_num(ov.get('pay_uv'))}</strong>",
            f"<strong>{fmt_yuan_simple(d['aov'])}</strong>",
        ]

        labels = [fmt_date_short(r["stat_date"]) for r in daily]
        cur_gmv = [_sf(r.get("gmv")) for r in daily]
        prev_gmv_list = [_sf(prev_daily[i].get("gmv")) if i < len(prev_daily) else 0 for i in range(len(daily))]
        cur_uv = [_si(r.get("pay_uv")) for r in daily]
        prev_uv = [_si(prev_daily[i].get("pay_uv")) if i < len(prev_daily) else 0 for i in range(len(daily))]

        cid1, cid2 = _cid("gmv_trend"), _cid("uv_trend")
        content = (
            f"<p>本周期内 GMV 走势中，<strong>{peak_date}（周{peak_wd}）为峰值日</strong>，"
            f"GMV {fmt_yuan(peak_gmv)}，占全周 {peak_pct:.1f}%。"
            f"全周 GMV {fmt_yuan(total_gmv)}，"
            f"环比{'增长' if (gmv_chg or 0) > 0 else '下降'} "
            f"<strong>{abs(gmv_chg or 0):.1f}%</strong>。</p>"
        )
        if _narr(0):
            content = _narr(0)

        findings.append({
            "title": f"逐日 GMV 走势：{peak_date}（周{peak_wd}）为峰值，贡献全周 {peak_pct:.0f}%",
            "content_html": content,
            "tables": [{
                "headers": ["日期", "星期", "本周 GMV", "上周 GMV", "环比增速", "支付人数", "客单价"],
                "rows": rows,
                "summary_row": summary,
            }],
            "charts": [
                {"id": cid1, "title": "本周 vs 上周 GMV 日走势", "type": "line", "half_width": True,
                 "data": {"labels": labels, "datasets": [
                     {"label": "本周 GMV", "data": cur_gmv, "color": "#1E40AF", "fill": True, "show_datalabels": True, "datalabel_format": "raw"},
                     {"label": "上周 GMV", "data": prev_gmv_list, "color": "#94A3B8", "dash": True},
                 ]}, "options": {}},
                {"id": cid2, "title": "逐日支付人数对比", "type": "line", "half_width": True,
                 "data": {"labels": labels, "datasets": [
                     {"label": "本周", "data": cur_uv, "color": "#22C55E", "show_datalabels": True, "datalabel_format": "raw"},
                     {"label": "上周", "data": prev_uv, "color": "#94A3B8", "dash": True},
                 ]}, "options": {}},
            ],
        })

    # ────────────────────────────────────────────
    # F2: 增长驱动力拆解
    # ────────────────────────────────────────────
    if prev_ov:
        gmv_c, gmv_p = _sf(ov.get("gmv")), _sf(prev_ov.get("gmv"))
        visit_c = _sf(ov.get("visit_uv"))
        visit_p = _sf(prev_ov.get("visit_uv"))
        pay_uv_c = _sf(ov.get("pay_uv"))
        pay_uv_p = _sf(prev_ov.get("pay_uv"))
        aov_c, aov_p = d.get("aov", 0), pd_.get("aov", 0)
        delta_gmv = gmv_c - gmv_p
        tri_valid = (visit_c > 0 and visit_p > 0)

        if tri_valid:
            cvr_c = pay_uv_c / visit_c if visit_c else 0
            cvr_p = pay_uv_p / visit_p if visit_p else 0
            uv_contrib  = (visit_c - visit_p) * cvr_p * aov_p
            cvr_contrib = (cvr_c - cvr_p)    * visit_p * aov_p
            aov_contrib = (aov_c - aov_p)    * visit_c * cvr_p
            uv_pct  = uv_contrib  / delta_gmv * 100 if delta_gmv else 0
            cvr_pct = cvr_contrib / delta_gmv * 100 if delta_gmv else 0
            aov_pct = aov_contrib / delta_gmv * 100 if delta_gmv else 0

            drivers = [("访问人数", uv_pct), ("转化率", cvr_pct), ("客单价", aov_pct)]
            main_driver, main_pct = max(drivers, key=lambda x: abs(x[1]))

            aov_order_c = d.get("aov_order", 0)
            aov_order_p = pd_.get("aov_order", 0)
            attach_c    = d.get("attach_rate", 0)
            attach_p    = pd_.get("attach_rate", 0)

            def _factor_html(name, contrib, pct, cur_str, prev_str, chg_html, is_main):
                direction = "正向" if contrib >= 0 else "负向"
                main_tag  = " ⚠️ <strong>主因</strong>" if is_main else ""
                return (f"<li><strong>{name} 因子</strong>：{prev_str} → {cur_str}，"
                        f"{direction}贡献 {fmt_yuan(contrib)}（{pct:+.1f}%）{main_tag}</li>")

            uv_chg_html  = _color_span(_pct_change(visit_c, visit_p))
            cvr_chg_html = _color_span((cvr_c - cvr_p) * 100, "{:+.1f}个百分点")
            aov_chg_html = _color_span(_pct_change(aov_c, aov_p))

            content = (
                f"<p>GMV = <strong>访问人数 × 转化率 × 客单价</strong>（三因子框架）。"
                f"将 GMV {'增幅' if delta_gmv >= 0 else '降幅'} {fmt_yuan(abs(delta_gmv))} 拆解：</p><ul>"
                + _factor_html("访问人数",  uv_contrib,  uv_pct,
                               fmt_num(int(visit_c)), fmt_num(int(visit_p)), uv_chg_html,  main_driver == "访问人数")
                + _factor_html("转化率",  cvr_contrib, cvr_pct,
                               fmt_pct(cvr_c * 100),  fmt_pct(cvr_p * 100), cvr_chg_html, main_driver == "转化率")
                + _factor_html("客单价",  aov_contrib, aov_pct,
                               fmt_yuan_simple(aov_c), fmt_yuan_simple(aov_p), aov_chg_html, main_driver == "客单价")
                + f"</ul><p>本周 GMV {'下滑' if delta_gmv < 0 else '增长'}的核心原因是"
                f"<strong>{main_driver}（{main_pct:+.1f}%）</strong>。</p>"
            )
            if _narr(1):
                content = _narr(1)

            cid3 = _cid("waterfall")
            net_gmv_c    = d.get("net_gmv", 0)
            refund_amt_c = _sf(ov.get("refund_amt"))

            wf_vals = [round(gmv_p, 2), round(uv_contrib, 2), round(cvr_contrib, 2),
                       round(aov_contrib, 2), round(gmv_c, 2), -round(refund_amt_c, 2), round(net_gmv_c, 2)]
            wf_colors = [
                '#1E40AF',
                '#22C55E' if uv_contrib  >= 0 else '#EF4444',
                '#22C55E' if cvr_contrib >= 0 else '#EF4444',
                '#22C55E' if aov_contrib >= 0 else '#EF4444',
                '#1E40AF', '#EF4444', '#1E40AF',
            ]

            def _contrib_row(name, cur_val, prev_val, contrib, pct, cur_str, prev_str, chg_html, is_main):
                name_cell = f"<strong>{name}</strong>" if is_main else name
                main_note = "（主因）" if is_main else ""
                return ([name_cell, cur_str, prev_str, chg_html,
                         fmt_yuan(contrib), f"{pct:+.1f}%{main_note}"],
                        ' style="background:#FFF5F5"' if is_main else "")

            rows_raw = [
                _contrib_row("访问人数", visit_c, visit_p, uv_contrib, uv_pct,
                             fmt_num(int(visit_c)), fmt_num(int(visit_p)), uv_chg_html, main_driver == "访问人数"),
                _contrib_row("转化率", cvr_c * 100, cvr_p * 100, cvr_contrib, cvr_pct,
                             fmt_pct(cvr_c * 100), fmt_pct(cvr_p * 100), cvr_chg_html, main_driver == "转化率"),
                _contrib_row("客单价", aov_c, aov_p, aov_contrib, aov_pct,
                             fmt_yuan_simple(aov_c), fmt_yuan_simple(aov_p), aov_chg_html, main_driver == "客单价"),
            ]
            contrib_table_html = '<div class="table-container"><table><thead><tr>'
            for h in ["因子", "本周", "上周", "变动", "贡献金额", "贡献度"]:
                contrib_table_html += f"<th>{_esc(h)}</th>"
            contrib_table_html += "</tr></thead><tbody>"
            for row, row_style in rows_raw:
                contrib_table_html += f"<tr{row_style}>"
                for cell in row:
                    contrib_table_html += f"<td>{cell}</td>"
                contrib_table_html += "</tr>\n"
            summary_cells = ["<strong>GMV 增量合计</strong>", "", "", "",
                             f"<strong>{fmt_yuan(delta_gmv)}</strong>", "<strong>100%</strong>"]
            contrib_table_html += '<tr style="font-weight:700;border-top:2px solid var(--border);background:#F0F3F7">'
            for cell in summary_cells:
                contrib_table_html += f"<td>{cell}</td>"
            contrib_table_html += "</tr></tbody></table></div>"

            findings.append({
                "title": f"增长驱动力拆解：{main_driver}{'下滑' if main_pct < 0 else '增长'}是主因，贡献约 {abs(main_pct):.0f}%",
                "content_html": (content or "") + contrib_table_html,
                "tables": [
                    {"headers": ["效率因子", "本周", "上周", "变动"],
                     "rows": [
                         ["笔单价", fmt_yuan_simple(aov_order_c), fmt_yuan_simple(aov_order_p),
                          _color_span(_pct_change(aov_order_c, aov_order_p))],
                         ["连带率", fmt_decimal(attach_c), fmt_decimal(attach_p),
                          _color_span(_pct_change(attach_c, attach_p))],
                     ]},
                ],
                "charts": [
                    {"id": cid3, "title": "GMV 三因子增长瀑布（UV × 转化率 × 客单价）",
                     "type": "bar", "half_width": False,
                     "data": {
                         "labels": ["上周GMV", "UV贡献", "转化率贡献", "客单价贡献", "本周GMV", "退款侵蚀", "净GMV"],
                         "datasets": [{"label": "金额", "data": wf_vals,
                                       "color": "#1E40AF", "colors": wf_colors, "show_datalabels": True, "datalabel_format": "raw"}]
                     },
                     "options": {
                         "hide_legend": True,
                     }},
                ],
            })

        else:
            # 降级：二因子
            uv_c_2  = pay_uv_c
            uv_p_2  = pay_uv_p
            uv_contrib_2  = (uv_c_2 - uv_p_2) * aov_p if aov_p else 0
            aov_contrib_2 = (aov_c - aov_p) * uv_c_2 if uv_c_2 else 0
            uv_pct_2  = uv_contrib_2  / delta_gmv * 100 if delta_gmv else 0
            aov_pct_2 = aov_contrib_2 / delta_gmv * 100 if delta_gmv else 0
            main_driver_2 = "支付人数增长" if abs(uv_pct_2) > abs(aov_pct_2) else "客单价提升"
            aov_order_c = d.get("aov_order", 0); aov_order_p = pd_.get("aov_order", 0)
            attach_c    = d.get("attach_rate", 0); attach_p   = pd_.get("attach_rate", 0)
            cid3 = _cid("waterfall")
            net_gmv_c = d.get("net_gmv", 0)
            content_2 = (
                f"<p>GMV = 支付人数 × 客单价。将 GMV 增量 {fmt_yuan(delta_gmv)} 拆解为两大因子：</p>"
                f"<ul><li><strong>人数因子</strong>：{fmt_num(uv_p_2)} → {fmt_num(uv_c_2)}，"
                f"贡献 {fmt_yuan(uv_contrib_2)}（{uv_pct_2:.1f}%）</li>"
                f"<li><strong>客单价因子</strong>：{fmt_yuan_simple(aov_p)} → {fmt_yuan_simple(aov_c)}，"
                f"贡献 {fmt_yuan(aov_contrib_2)}（{aov_pct_2:.1f}%）</li></ul>"
                f"<p>增长主要由<strong>{main_driver_2}</strong>驱动。</p>"
            )
            if _narr(1):
                content_2 = _narr(1)
            findings.append({
                "title": f"增长驱动力拆解：{main_driver_2}贡献 {max(abs(uv_pct_2), abs(aov_pct_2)):.0f}%",
                "content_html": content_2,
                "tables": [
                    {"headers": ["因子", "本周", "上周", "变动", "贡献金额", "贡献度"],
                     "rows": [
                         ["支付人数", fmt_num(uv_c_2), fmt_num(uv_p_2),
                          _color_span(_pct_change(uv_c_2, uv_p_2)), fmt_yuan(uv_contrib_2), f"{uv_pct_2:.1f}%"],
                         ["客单价", fmt_yuan_simple(aov_c), fmt_yuan_simple(aov_p),
                          _color_span(_pct_change(aov_c, aov_p)), fmt_yuan(aov_contrib_2), f"{aov_pct_2:.1f}%"],
                     ],
                     "summary_row": ["<strong>GMV 增量合计</strong>", "", "", "",
                                     f"<strong>{fmt_yuan(delta_gmv)}</strong>", "<strong>100%</strong>"]},
                    {"headers": ["效率因子", "本周", "上周", "变动"],
                     "rows": [
                         ["笔单价", fmt_yuan_simple(aov_order_c), fmt_yuan_simple(aov_order_p),
                          _color_span(_pct_change(aov_order_c, aov_order_p))],
                         ["连带率", fmt_decimal(attach_c), fmt_decimal(attach_p),
                          _color_span(_pct_change(attach_c, attach_p))],
                     ]},
                ],
                "charts": [
                    {"id": cid3, "title": "GMV 增长瀑布（增长 + 侵蚀全景）", "type": "bar", "half_width": False,
                     "data": {"labels": ["上周GMV", "人数贡献", "客单价贡献", "本周GMV", "退款侵蚀", "净GMV"],
                              "datasets": [{"label": "金额", "data": [
                                  round(gmv_p, 2), round(uv_contrib_2, 2), round(aov_contrib_2, 2),
                                  round(gmv_c, 2), -round(_sf(ov.get("refund_amt")), 2), round(net_gmv_c, 2)],
                                  "color": "#1E40AF", "show_datalabels": True, "datalabel_format": "raw"}]},
                     "options": {"hide_legend": True}},
                ],
            })

    # ────────────────────────────────────────────
    # F3: 退款多维诊断
    # ────────────────────────────────────────────
    refund_rate_c = d.get("refund_rate", 0)
    refund_rate_p = pd_.get("refund_rate", 0)
    refund_pen_c = d.get("refund_penetration", 0)
    refund_pen_p = pd_.get("refund_penetration", 0)
    refund_per_user_c = d.get("refund_per_user", 0)
    refund_per_user_p = pd_.get("refund_per_user", 0)

    refund_daily_rows = []
    if daily:
        total_refund = _sf(ov.get("refund_amt"))
        for r in daily:
            dt = fmt_date_short(r["stat_date"])
            g = _sf(r.get("gmv"))
            ref = _sf(r.get("refund_amt"))
            day_rate = ref / g * 100 if g else 0
            day_pct = ref / total_refund * 100 if total_refund else 0
            refund_daily_rows.append([
                f"{dt}（周{_weekday_cn(r['stat_date'])}）",
                fmt_yuan(g), fmt_yuan(ref),
                _color_span(day_rate, "{:.1f}%", positive_good=False),
                f"{day_pct:.1f}%",
            ])

    cid4, cid5 = _cid("refund_bar"), _cid("refund_trend")
    content = (
        f"<p>退款率 <strong>{refund_rate_c:.1f}%</strong>（环比 {_sf(refund_rate_p):.1f}%），"
        f"退款渗透率 <strong>{refund_pen_c:.1f}%</strong>，"
        f"退款人均金额 <strong>{fmt_yuan_simple(refund_per_user_c)}</strong>。</p>"
    )
    if refund_rate_c > 100:
        content += "<p>⚠️ 退款金额超过当期 GMV，存在跨周期退款（退还更早周期的订单）。</p>"
    if _narr(2):
        content = _narr(2)

    refund_tbl1 = {
        "headers": ["退款指标", "本周", "上周", "变动"],
        "rows": [
            ["<strong>退款率</strong>", f"<strong>{refund_rate_c:.1f}%</strong>",
             f"{refund_rate_p:.1f}%",
             _color_span(refund_rate_c - refund_rate_p, "{:+.1f}个百分点", positive_good=False)],
            ["<strong>退款渗透率</strong>", f"<strong>{refund_pen_c:.1f}%</strong>",
             f"{refund_pen_p:.1f}%",
             _color_span(refund_pen_c - refund_pen_p, "{:+.1f}个百分点", positive_good=False)],
            ["<strong>退款人均</strong>", f"<strong>{fmt_yuan_simple(refund_per_user_c)}</strong>",
             fmt_yuan_simple(refund_per_user_p),
             _color_span(_pct_change(refund_per_user_c, refund_per_user_p), "{:+.1f}%", positive_good=False)],
            ["退款人数", fmt_num(ov.get("refund_uv")), fmt_num(prev_ov.get("refund_uv")),
             _color_span(_pct_change(ov.get("refund_uv"), prev_ov.get("refund_uv")), "{:+.1f}%", positive_good=False)],
            ["退款金额", fmt_yuan(ov.get("refund_amt")), fmt_yuan(prev_ov.get("refund_amt")),
             _color_span(_pct_change(ov.get("refund_amt"), prev_ov.get("refund_amt")), "{:+.1f}%", positive_good=False)],
        ]}

    tables = [refund_tbl1]
    if refund_daily_rows:
        tables.append({
            "headers": ["日期", "GMV", "退款", "日退款率", "退款占比"],
            "rows": refund_daily_rows,
        })

    charts = []
    if daily:
        charts.append({
            "id": cid4, "title": "逐日 GMV vs 退款金额", "type": "bar", "half_width": True,
            "data": {"labels": [fmt_date_short(r["stat_date"]) for r in daily],
                     "datasets": [
                         {"label": "GMV", "data": [_sf(r.get("gmv")) for r in daily],
                          "color": "#1E40AF", "show_datalabels": True, "datalabel_format": "raw"},
                         {"label": "退款", "data": [_sf(r.get("refund_amt")) for r in daily],
                          "color": "#EF4444", "show_datalabels": True, "datalabel_format": "raw"},
                     ]}, "options": {}})
    if weekly:
        wk_refund_rates = [_sf(w.get("refund_amt")) / _sf(w.get("gmv")) * 100
                           if _sf(w.get("gmv")) else 0 for w in weekly]
        charts.append({
            "id": cid5, "title": f"近 {len(weekly)} 周退款率趋势", "type": "line", "half_width": True,
            "data": {"labels": [w["week_label"] for w in weekly],
                     "datasets": [
                         {"label": "退款率(%)", "data": [round(r, 1) for r in wk_refund_rates],
                          "color": "#EF4444", "fill": True, "show_datalabels": True, "datalabel_format": "raw"},
                     ]}, "options": {"y_format": "percent"}})

    findings.append({
        "title": f"退款多维诊断：退款率 {refund_rate_c:.1f}%，渗透率 {refund_pen_c:.1f}%",
        "content_html": content,
        "tables": tables,
        "charts": charts,
    })

    # ────────────────────────────────────────────
    # F4: 转化漏斗分析
    # ────────────────────────────────────────────
    f4_visit_c  = _si(ov.get("visit_uv"))
    f4_order_c  = _si(ov.get("order_uv"))
    f4_pay_c    = _si(ov.get("pay_uv"))
    f4_visit_p  = _si(prev_ov.get("visit_uv")) if prev_ov else 0
    f4_order_p  = _si(prev_ov.get("order_uv")) if prev_ov else 0
    f4_pay_p    = _si(prev_ov.get("pay_uv"))   if prev_ov else 0

    funnel_valid      = (f4_visit_c > 0 and f4_order_c > 0)
    funnel_prev_valid = (f4_visit_p > 0 and f4_order_p > 0)

    cvr_vo_c = f4_order_c / f4_visit_c * 100 if funnel_valid      else 0
    cvr_vo_p = f4_order_p / f4_visit_p * 100 if funnel_prev_valid else 0
    cvr_op_c = f4_pay_c   / f4_order_c * 100 if f4_order_c        else 0
    cvr_op_p = f4_pay_p   / f4_order_p * 100 if f4_order_p        else 0
    cvr_ov_c = f4_pay_c   / f4_visit_c * 100 if funnel_valid      else 0
    cvr_ov_p = f4_pay_p   / f4_visit_p * 100 if funnel_prev_valid else 0

    f4_lost_1 = f4_visit_c - f4_order_c
    f4_lost_2 = f4_order_c - f4_pay_c
    cvr_vo_pp = cvr_vo_c - cvr_vo_p
    cvr_op_pp = cvr_op_c - cvr_op_p
    visit_chg = _pct_change(f4_visit_c, f4_visit_p) or 0

    order_bar_color = '#EF4444' if cvr_vo_pp < -2 else ('#22C55E' if cvr_vo_pp > 0 else '#F59E0B')

    visit_rate_cls = "good" if visit_chg >= 0 else "bad"
    visit_rate_val = f"{'▲' if visit_chg >= 0 else '▼'} {abs(visit_chg):.1f}%"
    order_rate_cls = "bad" if cvr_vo_pp < -2 else ("good" if cvr_vo_pp > 0 else "")
    order_rate_val = f"{'▼' if cvr_vo_pp < 0 else '▲'} {abs(cvr_vo_pp):.1f}个百分点"
    pay_rate_cls   = "good" if cvr_op_c >= 85 else "bad"
    pay_rate_val   = f"{cvr_op_c:.1f}% {'✅' if cvr_op_c >= 85 else '⚠️'}"
    pay_rate_sub   = f"下单→支付 环比{'↑' if cvr_op_pp > 0 else '↓'}"

    has_prev_visit = f4_visit_p > 0
    if has_prev_visit and cvr_vo_pp < -1:
        diag_html = (
            f'<div class="highlight-negative">'
            f'<div class="highlight-label">断点诊断：访问→下单转化率环比下滑 {abs(cvr_vo_pp):.1f}个百分点</div>'
            f'<div class="highlight-text">本周访问→下单转化率 <strong>{cvr_vo_c:.1f}%</strong>'
            f'（上周 {cvr_vo_p:.1f}%），是本周 GMV 下滑的核心原因。'
            f'建议优化商品详情页吸引力（主图/价格/评价）及搜索推荐入口的商品相关性。</div></div>'
        )
    elif has_prev_visit and cvr_vo_pp > 1:
        diag_html = (
            f'<div class="highlight-positive">'
            f'<div class="highlight-label">转化率提升：访问→下单环比 +{cvr_vo_pp:.1f}个百分点</div>'
            f'<div class="highlight-text">访问→下单转化率 <strong>{cvr_vo_c:.1f}%</strong>'
            f'（上周 {cvr_vo_p:.1f}%），转化效率改善。</div></div>'
        )
    else:
        diag_html = ""

    if funnel_valid:
        funnel_html = f"""\
<div class="funnel-chart">
  <div class="funnel-chart-title">访问漏斗：访问 → 下单 → 支付</div>
  <div class="funnel-step">
    <div class="funnel-step-label">访问人数</div>
    <div class="funnel-bar-wrap">
      <div class="funnel-bar" style="width:100%;background:#1E40AF;">
        <span class="f-num">{fmt_num(f4_visit_c)}</span>
        <span class="f-pct">100%</span>
      </div>
    </div>
    <div class="funnel-step-rate">
      <span class="r-val {visit_rate_cls}">{_esc(visit_rate_val)}</span>
      <span style="font-size:11px;color:var(--text-muted)">访问人数 环比</span>
    </div>
  </div>
  <div class="funnel-arrow-row">
    <div class="arrow-spacer"></div>
    <div class="arrow-body">
      <span class="arrow-icon">↓</span>
      <span style="color:#EF4444;font-weight:600;font-size:12px;">流失 {fmt_num(f4_lost_1)} 人</span>
    </div>
  </div>
  <div class="funnel-step">
    <div class="funnel-step-label">下单人数</div>
    <div class="funnel-bar-wrap">
      <div class="funnel-bar" style="width:{cvr_vo_c:.1f}%;background:{order_bar_color};">
        <span class="f-num">{fmt_num(f4_order_c)}</span>
        <span class="f-pct">{cvr_vo_c:.1f}%</span>
      </div>
    </div>
    <div class="funnel-step-rate">
      <span class="r-val {order_rate_cls}">{_esc(order_rate_val)}</span>
      <span style="font-size:11px;color:var(--text-muted)">访问→下单 环比</span>
    </div>
  </div>
  <div class="funnel-arrow-row">
    <div class="arrow-spacer"></div>
    <div class="arrow-body">
      <span class="arrow-icon">↓</span>
      <span style="color:#94A3B8;font-weight:500;font-size:12px;">流失 {fmt_num(f4_lost_2)} 人</span>
    </div>
  </div>
  <div class="funnel-step">
    <div class="funnel-step-label">支付人数</div>
    <div class="funnel-bar-wrap">
      <div class="funnel-bar" style="width:{cvr_ov_c:.1f}%;background:#22C55E;">
        <span class="f-num">{fmt_num(f4_pay_c)}</span>
        <span class="f-pct">{cvr_ov_c:.1f}%</span>
      </div>
    </div>
    <div class="funnel-step-rate">
      <span class="r-val {pay_rate_cls}">{_esc(pay_rate_val)}</span>
      <span style="font-size:11px;color:var(--text-muted)">{_esc(pay_rate_sub)}</span>
    </div>
  </div>
</div>
{diag_html}"""
    else:
        funnel_html = ""

    cvr_c_dt    = d.get("order_pay_cvr", 0) * 100
    cvr_p_dt    = pd_.get("order_pay_cvr", 0) * 100 if pd_ else 0
    amt_loss_c  = d.get("order_pay_amt_loss", 0) * 100
    amt_loss_p  = pd_.get("order_pay_amt_loss", 0) * 100 if pd_ else 0
    lost_uv_dt  = _si(ov.get("order_uv")) - _si(ov.get("pay_uv"))
    lost_cnt_dt = _si(ov.get("order_cnt")) - _si(ov.get("pay_cnt"))
    lost_amt_dt = _sf(ov.get("order_amt")) - _sf(ov.get("gmv"))

    detail_intro = (
        f'<div class="finding-content" style="margin-top:28px"><p>'
        f"下单→支付细节：下单人数 {fmt_num(ov.get('order_uv'))}，支付人数 {fmt_num(ov.get('pay_uv'))}，"
        f"<strong>下单→支付转化率 {cvr_c_dt:.1f}%</strong>"
        + (f"（上周 {cvr_p_dt:.1f}%，{'✅ 提升' if cvr_c_dt > cvr_p_dt else '⚠️ 下降'}）" if cvr_p_dt else "")
        + f"。下单金额 {fmt_yuan(ov.get('order_amt'))} vs 支付 GMV {fmt_yuan(ov.get('gmv'))}，"
        f"<strong>金额折损率 {amt_loss_c:.1f}%</strong>，每周折损 {fmt_yuan(lost_amt_dt)}。</p></div>"
    )
    if _narr(3):
        detail_intro = _narr(3)

    intro_html = (
        f"<p>本周访问 {fmt_num(f4_visit_c)} 人，最终支付 {fmt_num(f4_pay_c)} 人，"
        f"<strong>整体转化率 {cvr_ov_c:.1f}%</strong>"
        + (f"（上周 {cvr_ov_p:.1f}%，<strong>环比{'下滑' if cvr_ov_c < cvr_ov_p else '提升'} "
           f"{abs(cvr_ov_c - cvr_ov_p):.1f}个百分点</strong>）" if f4_visit_p else "")
        + f"。访问→下单是主要流失环节，下单→支付环节{'✅ 健康' if cvr_op_c >= 85 else '⚠️ 需关注'}（{cvr_op_c:.1f}%）。</p>"
    )

    cid6, cid7 = _cid("cvr_compare"), _cid("cvr_trend")

    findings.append({
        "title": f"转化漏斗分析：整体转化率 {cvr_ov_c:.1f}%"
                 + (f"（环比 {cvr_ov_c - cvr_ov_p:+.1f}个百分点）" if f4_visit_p else ""),
        "content_html": intro_html + funnel_html + detail_intro,
        "tables": [
            {"headers": ["指标", "下单", "支付", "折损", "折损率", "上周折损率"],
             "rows": [
                 ["人数", fmt_num(ov.get("order_uv")), fmt_num(ov.get("pay_uv")),
                  _color_span(-lost_uv_dt, "{:.0f} 人", positive_good=False),
                  _color_span(100 - cvr_c_dt, "{:.1f}%", positive_good=False),
                  f"{100 - cvr_p_dt:.1f}%" if cvr_p_dt else "-"],
                 ["订单数", fmt_num(ov.get("order_cnt")), fmt_num(ov.get("pay_cnt")),
                  _color_span(-lost_cnt_dt, "{:.0f} 单", positive_good=False),
                  _color_span(lost_cnt_dt / _sf(ov.get("order_cnt")) * 100
                              if _sf(ov.get("order_cnt")) else 0, "{:.1f}%", positive_good=False),
                  "-"],
                 ["金额", fmt_yuan(ov.get("order_amt")), fmt_yuan(ov.get("gmv")),
                  _color_span(-lost_amt_dt, "{}".format(fmt_yuan(lost_amt_dt)), positive_good=False),
                  f"<strong>{_color_span(amt_loss_c, '{:.1f}%', positive_good=False)}</strong>",
                  f"{amt_loss_p:.1f}%" if amt_loss_p else "-"],
             ]}],
        "charts": [
            {"id": cid6, "title": "下单 vs 支付对比", "type": "bar", "half_width": True,
             "data": {"labels": ["人数", "订单数"],
                      "datasets": [
                          {"label": "下单", "data": [_si(ov.get("order_uv")), _si(ov.get("order_cnt"))],
                           "color": "#94A3B8", "show_datalabels": True, "datalabel_format": "raw"},
                          {"label": "支付", "data": [_si(ov.get("pay_uv")), _si(ov.get("pay_cnt"))],
                           "color": "#7C3AED", "show_datalabels": True, "datalabel_format": "raw"},
                      ]}, "options": {}},
            *([ {"id": cid7, "title": f"近 {len(weekly)} 周下单→支付转化率", "type": "line", "half_width": True,
                 "data": {"labels": [w["week_label"] for w in weekly],
                          "datasets": [{"label": "转化率(%)",
                                        "data": [round(_sf(w.get("pay_uv")) / _sf(w.get("order_uv")) * 100, 1)
                                                 if _sf(w.get("order_uv")) else 0 for w in weekly],
                                        "color": "#7C3AED", "fill": True,
                                        "show_datalabels": True, "datalabel_format": "raw"}]},
                 "options": {"y_format": "percent"}}
               ] if weekly else []),
        ],
    })

    return findings

"""门店/区域对标 — 报告插件（capability_id=2）

从 ecommerce_report.py 搬出的 generate_store_benchmark_findings()，逻辑完全不变。

JSON 需要:
  - stores[]: 门店明细列表（按 GMV 降序），每项含:
      store_name, gmv, prev_gmv, pay_uv, order_uv, sales_qty, pay_cnt,
      refund_amt, aov(可选), cvr(可选), refund_rate(可选)
  - previous_stores[]: 环比期门店明细（可选，用于环比计算）
  - finding_narratives[]: 4 段分析文案（可选）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecommerce_report import (
    _sf, _si, _esc, fmt_yuan, fmt_yuan_simple, fmt_num, fmt_pct, fmt_decimal,
    _pct_change, _color_span, compute_derived, fmt_change, fmt_date_short,
)


def generate_findings(data: dict) -> list:
    """门店/区域对标自动生成 4 个标准 findings。"""
    stores = data.get("stores", [])
    if not stores:
        return []

    narratives = data.get("finding_narratives", [])
    def _narr(idx):
        return narratives[idx] if idx < len(narratives) else None

    findings = []
    chart_counter = [100]  # 避免和 trade 的 chart id 冲突
    def _cid(prefix="store"):
        chart_counter[0] += 1
        return f"{prefix}_{chart_counter[0]}"

    n_stores = len(stores)

    # 预计算每个门店的衍生指标
    for s in stores:
        g = _sf(s.get("gmv"))
        uv = _sf(s.get("pay_uv"))
        ouv = _sf(s.get("order_uv"))
        ref = _sf(s.get("refund_amt"))
        qty = _sf(s.get("sales_qty"))
        cnt = _sf(s.get("pay_cnt"))
        s["_aov"] = s.get("aov", g / uv if uv else 0)
        s["_cvr"] = s.get("cvr", uv / ouv * 100 if ouv else 0)
        s["_refund_rate"] = s.get("refund_rate", ref / g * 100 if g else 0)
        s["_attach"] = qty / cnt if cnt else 0

    total_gmv = sum(_sf(s.get("gmv")) for s in stores)

    # Top/Bottom 分组
    top3 = stores[:3]
    bottom3 = stores[-3:] if n_stores >= 6 else stores[-1:]
    top3_gmv = sum(_sf(s.get("gmv")) for s in top3)
    top3_pct = top3_gmv / total_gmv * 100 if total_gmv else 0
    bottom3_gmv = sum(_sf(s.get("gmv")) for s in bottom3)
    bottom3_pct = bottom3_gmv / total_gmv * 100 if total_gmv else 0

    best = stores[0]
    worst = stores[-1]
    aov_ratio = _sf(best["_aov"]) / _sf(worst["_aov"]) if _sf(worst["_aov"]) else 0
    gmv_ratio = _sf(best.get("gmv")) / _sf(worst.get("gmv")) if _sf(worst.get("gmv")) else 0

    # HHI 指数
    hhi = sum((_sf(s.get("gmv")) / total_gmv) ** 2 for s in stores) if total_gmv else 0

    # ────────────────────────────────────────────
    # F1: 门店 GMV 排行
    # ────────────────────────────────────────────
    rank_rows = []
    for i, s in enumerate(stores):
        g = _sf(s.get("gmv"))
        pg = _sf(s.get("prev_gmv"))
        chg = _pct_change(g, pg)
        chg_html = _color_span(chg) if chg is not None else "-"
        gmv_pct = g / total_gmv * 100 if total_gmv else 0
        if i == 0:
            rank = "🥇 1"
        elif i == 1:
            rank = "🥈 2"
        elif i == 2:
            rank = "🥉 3"
        else:
            rank = str(i + 1)
        rr = s["_refund_rate"]
        rr_html = f"<span style='color:#EF4444;font-weight:700'>{rr:.1f}%</span>" if rr > 12 else (
            f"<span style='color:#F59E0B'>{rr:.1f}%</span>" if rr > 8 else f"{rr:.1f}%")
        rank_rows.append([rank, _esc(s.get("store_name", "")), fmt_yuan(g), fmt_yuan(pg) if pg else "-",
                          chg_html, fmt_num(s.get("pay_uv")),
                          fmt_yuan_simple(s["_aov"]), f"{s['_cvr']:.1f}%", rr_html])

    total_prev = sum(_sf(s.get("prev_gmv")) for s in stores)
    total_chg = _pct_change(total_gmv, total_prev)
    total_uv = sum(_si(s.get("pay_uv")) for s in stores)
    total_aov = total_gmv / total_uv if total_uv else 0
    rank_summary = ["", "<strong>全网合计</strong>", f"<strong>{fmt_yuan(total_gmv)}</strong>",
                    f"<strong>{fmt_yuan(total_prev)}</strong>",
                    f"<strong>{_color_span(total_chg) if total_chg is not None else '-'}</strong>",
                    f"<strong>{fmt_num(total_uv)}</strong>",
                    f"<strong>{fmt_yuan_simple(total_aov)}</strong>", "", ""]

    cid1 = _cid("rank")
    store_names = [s.get("store_name", "")[:6] for s in stores]
    store_gmv_list = [_sf(s.get("gmv")) for s in stores]
    prev_gmv_list = [_sf(s.get("prev_gmv")) for s in stores]

    content = (
        f"<p>{n_stores} 家门店按 GMV 排行，Top 1 {_esc(best.get('store_name', ''))} GMV {fmt_yuan(best.get('gmv'))}，"
        f"是末位 {_esc(worst.get('store_name', ''))} {fmt_yuan(worst.get('gmv'))} 的 <strong>{gmv_ratio:.1f} 倍</strong>。"
        f"Top 3 合计贡献 <strong>{top3_pct:.0f}%</strong> GMV。</p>"
    )
    if _narr(0):
        content = _narr(0)

    findings.append({
        "title": f"门店 GMV 排行：头尾差距 {gmv_ratio:.0f} 倍，Top 3 贡献 {top3_pct:.0f}%",
        "content_html": content,
        "tables": [{
            "headers": ["排名", "门店名称", "本周 GMV", "上周 GMV", "环比", "支付人数", "客单价", "转化率", "退款率"],
            "rows": rank_rows,
            "summary_row": rank_summary,
        }],
        "charts": [
            {"id": cid1, "title": f"{n_stores} 门店 GMV 排行（本周 vs 上周）", "type": "bar", "half_width": False,
             "data": {"labels": store_names,
                      "datasets": [
                          {"label": "本周 GMV", "data": store_gmv_list, "color": "#1E40AF",
                           "show_datalabels": True, "datalabel_format": "yuan", "datalabel_align": "right"},
                          {"label": "上周 GMV", "data": prev_gmv_list, "color": "#94A3B833"},
                      ]},
             "options": {"index_axis": "y", "y_format": "yuan"}},
        ],
    })

    # ────────────────────────────────────────────
    # F2: GMV 集中度 + 散点图
    # ────────────────────────────────────────────
    mid_stores = stores[3:-3] if n_stores >= 6 else stores[3:]
    mid_pct = 100 - top3_pct - bottom3_pct

    cid2 = _cid("concentration")
    cid3 = _cid("scatter")

    content = (
        f"<p>HHI 集中度指数 <strong>{hhi:.3f}</strong>（{'高集中度' if hhi > 0.15 else '中等' if hhi > 0.10 else '分散'}），"
        f"Top 3 贡献 {top3_pct:.0f}%，中间 {len(mid_stores)} 家贡献 {mid_pct:.0f}%，"
        f"Bottom {len(bottom3)} 家仅贡献 {bottom3_pct:.1f}%。</p>"
    )
    if _narr(1):
        content = _narr(1)

    scatter_data = [{"x": round(s["_aov"], 1), "y": round(s["_cvr"], 1)} for s in stores]

    findings.append({
        "title": f"GMV 集中度 {top3_pct:.0f}%（HHI={hhi:.3f}），头部依赖风险{'显著' if hhi > 0.15 else '可控'}",
        "content_html": content,
        "charts": [
            {"id": cid2, "title": "门店 GMV 占比分布", "type": "doughnut", "half_width": True,
             "data": {"labels": [f"Top 3（{top3_pct:.0f}%）", f"中间 {len(mid_stores)} 家（{mid_pct:.0f}%）",
                                 f"Bottom {len(bottom3)}（{bottom3_pct:.1f}%）"],
                      "datasets": [{"label": "GMV 占比", "data": [round(top3_pct, 1), round(mid_pct, 1), round(bottom3_pct, 1)],
                                    "colors": ["#1E40AF", "#94A3B8", "#EF4444"],
                                    "show_datalabels": True, "datalabel_format": "pct_plain"}]},
             "options": {"cutout": "55%"}},
            {"id": cid3, "title": "门店客单价 vs 转化率散点图", "type": "scatter", "half_width": True,
             "data": {"labels": store_names,
                      "datasets": [{"label": "门店", "data": scatter_data, "color": "#1E40AF", "point_radius": 10}]},
             "options": {"x_title": "客单价（¥）", "y_title": "转化率（%）", "y_format": "percent", "hide_legend": True}},
        ],
    })

    # ────────────────────────────────────────────
    # F3: 标杆 vs 薄弱门店对标（雷达图 + 表格）
    # ────────────────────────────────────────────
    cid4 = _cid("radar")

    def _percentile(vals, v):
        if not vals or max(vals) == min(vals):
            return 50
        return (v - min(vals)) / (max(vals) - min(vals)) * 100

    all_gmv = [_sf(s.get("gmv")) for s in stores]
    all_aov = [s["_aov"] for s in stores]
    all_cvr = [s["_cvr"] for s in stores]
    all_rr = [s["_refund_rate"] for s in stores]
    all_attach = [s["_attach"] for s in stores]

    best_scores = [
        round(_percentile(all_gmv, _sf(best.get("gmv")))),
        round(_percentile(all_aov, best["_aov"])),
        round(_percentile(all_cvr, best["_cvr"])),
        round(100 - _percentile(all_rr, best["_refund_rate"])),
        round(_percentile(all_attach, best["_attach"])),
    ]
    worst_scores = [
        round(_percentile(all_gmv, _sf(worst.get("gmv")))),
        round(_percentile(all_aov, worst["_aov"])),
        round(_percentile(all_cvr, worst["_cvr"])),
        round(100 - _percentile(all_rr, worst["_refund_rate"])),
        round(_percentile(all_attach, worst["_attach"])),
    ]

    pk_rows = [
        ["周 GMV", fmt_yuan(best.get("gmv")), fmt_yuan(worst.get("gmv")),
         f"<span style='color:#EF4444;font-weight:700'>{gmv_ratio:.1f}x</span>", "产出断层"],
        ["支付人数", fmt_num(best.get("pay_uv")), fmt_num(worst.get("pay_uv")),
         f"{_sf(best.get('pay_uv')) / _sf(worst.get('pay_uv')):.1f}x" if _sf(worst.get("pay_uv")) else "-", "客流差距"],
        ["客单价", fmt_yuan_simple(best["_aov"]), fmt_yuan_simple(worst["_aov"]),
         f"<span style='color:#EF4444'>{aov_ratio:.1f}x</span>", "品类结构差异"],
        ["转化率", f"{best['_cvr']:.1f}%", f"{worst['_cvr']:.1f}%",
         f"{best['_cvr'] / worst['_cvr']:.1f}x" if worst["_cvr"] else "-", "运营能力差距"],
        ["退款率", f"{best['_refund_rate']:.1f}%",
         f"<span style='color:#EF4444'>{worst['_refund_rate']:.1f}%</span>",
         f"{worst['_refund_rate'] / best['_refund_rate']:.1f}x" if best["_refund_rate"] else "-", "品控差距"],
        ["连带率", fmt_decimal(best["_attach"]), fmt_decimal(worst["_attach"]),
         f"{best['_attach'] / worst['_attach']:.1f}x" if worst["_attach"] else "-", "搭配购差距"],
    ]

    content = (
        f"<p>将 Top 1 <strong>{_esc(best.get('store_name', ''))}</strong> 与末位 "
        f"<strong>{_esc(worst.get('store_name', ''))}</strong> 逐维度对标。"
        f"客单价差距 {aov_ratio:.1f} 倍，转化率差距 "
        f"{best['_cvr'] / worst['_cvr']:.1f}x。</p>"
        if worst["_cvr"] else ""
    )
    if _narr(2):
        content = _narr(2)

    findings.append({
        "title": f"标杆对标：{best.get('store_name', '')} vs {worst.get('store_name', '')}",
        "content_html": content,
        "tables": [{
            "headers": ["对比维度", f"🏆 {best.get('store_name', '')}", f"⚠️ {worst.get('store_name', '')}",
                        "差距倍数", "诊断结论"],
            "rows": pk_rows,
        }],
        "charts": [
            {"id": cid4, "title": "标杆 vs 薄弱门店核心指标雷达图", "type": "radar", "half_width": False,
             "data": {"labels": ["GMV", "客单价", "转化率", "退款率(反向)", "连带率"],
                      "datasets": [
                          {"label": best.get("store_name", "Top 1"), "data": best_scores, "color": "#1E40AF"},
                          {"label": worst.get("store_name", "Bottom 1"), "data": worst_scores, "color": "#EF4444"},
                      ]},
             "options": {"radar_max": 100}},
        ],
    })

    # ────────────────────────────────────────────
    # F4: 各门店环比增速排行
    # ────────────────────────────────────────────
    growth_data = []
    for s in stores:
        chg = _pct_change(s.get("gmv"), s.get("prev_gmv"))
        growth_data.append({"name": s.get("store_name", ""), "growth": round(chg, 1) if chg is not None else 0})
    growth_data.sort(key=lambda x: x["growth"], reverse=True)

    fastest = growth_data[0] if growth_data else {"name": "", "growth": 0}
    slowest = growth_data[-1] if growth_data else {"name": "", "growth": 0}
    neg_count = sum(1 for g in growth_data if g["growth"] < 0)

    cid5 = _cid("growth")

    content = f"<p>{n_stores} 家门店中，增速最高为 <strong>{fastest['name']}（{fastest['growth']:+.1f}%）</strong>，"
    if neg_count == 0:
        content += "全部正增长。</p>"
    else:
        sn = slowest['name']
        sg = slowest['growth']
        content += f"{neg_count} 家负增长，最低 {sn}（{sg:+.1f}%）。</p>"
    if _narr(3):
        content = _narr(3)

    findings.append({
        "title": f"环比增速：{fastest['name']} 领跑（{fastest['growth']:+.1f}%）"
                 + (f"，{slowest['name']} 垫底（{slowest['growth']:+.1f}%）" if neg_count > 0 else ""),
        "content_html": content,
        "charts": [
            {"id": cid5, "title": "各门店环比增速排行", "type": "bar", "half_width": False,
             "data": {"labels": [g["name"][:6] for g in growth_data],
                      "datasets": [{"label": "环比增速(%)", "data": [g["growth"] for g in growth_data],
                                    "color": "#1E40AF", "show_datalabels": True, "datalabel_format": "percent"}]},
             "options": {"y_format": "percent", "hide_legend": True}},
        ],
    })

    return findings

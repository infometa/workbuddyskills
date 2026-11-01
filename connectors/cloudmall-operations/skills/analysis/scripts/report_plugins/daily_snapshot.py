"""经营日报快照 — 报告插件（capability_id=3）

生成 5 个 findings 章节：
  F1: 转化漏斗分析（访问→浏览→下单→支付）
  F2: 用户结构（新客/老客人数+GMV+客单价）
  F3: 品类表现（GMV排行+CVR+退款率）
  F4: 异常信号汇总（红/橙/绿三级）

注：S1 核心结论概览 和 S3 建议 由 build_html() 通用框架渲染，
    本插件只负责 S2 核心分析发现 的 findings 列表。

JSON 需要（见 schema_examples/cap_3.json）:
  - overview / previous_overview（必填）
  - user_segments / previous_user_segments（推荐）
  - category_stats[]（推荐）
  - finding_narratives[]（可选，hybrid 模式文案覆盖）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecommerce_report import (
    _sf, _si, _esc, fmt_yuan, fmt_yuan_simple, fmt_num, fmt_pct, fmt_decimal,
    _pct_change, _color_span, compute_derived, fmt_change, fmt_date_short,
)


def generate_findings(data: dict) -> list:
    """经营日报快照自动生成 4 个标准 findings。"""
    ov = data.get("overview", {})
    pov = data.get("previous_overview", {})
    us = data.get("user_segments", {})
    pus = data.get("previous_user_segments", {})
    cats = data.get("category_stats", [])
    narratives = data.get("finding_narratives", [])

    def _narr(idx):
        return narratives[idx] if idx < len(narratives) else None

    findings = []
    chart_counter = [200]
    def _cid(prefix="daily"):
        chart_counter[0] += 1
        return f"{prefix}_{chart_counter[0]}"

    # ── 预计算 ──
    visit_uv = _si(ov.get("visit_uv"))
    browse_uv = _si(ov.get("browse_uv"))
    order_uv = _si(ov.get("order_uv"))
    pay_uv = _si(ov.get("pay_uv"))
    gmv = _sf(ov.get("gmv"))

    p_visit_uv = _si(pov.get("visit_uv"))
    p_browse_uv = _si(pov.get("browse_uv"))
    p_order_uv = _si(pov.get("order_uv"))
    p_pay_uv = _si(pov.get("pay_uv"))

    # 漏斗转化率
    cvr_v2b = browse_uv / visit_uv * 100 if visit_uv else 0
    cvr_b2o = order_uv / browse_uv * 100 if browse_uv else 0
    cvr_o2p = pay_uv / order_uv * 100 if order_uv else 0
    cvr_overall = pay_uv / visit_uv * 100 if visit_uv else 0

    p_cvr_v2b = p_browse_uv / p_visit_uv * 100 if p_visit_uv else 0
    p_cvr_b2o = p_order_uv / p_browse_uv * 100 if p_browse_uv else 0
    p_cvr_o2p = p_pay_uv / p_order_uv * 100 if p_order_uv else 0

    # 漏斗各步 width%（相对访问）
    pct_visit = 100
    pct_browse = browse_uv / visit_uv * 100 if visit_uv else 0
    pct_order = order_uv / visit_uv * 100 if visit_uv else 0
    pct_pay = pay_uv / visit_uv * 100 if visit_uv else 0

    # ────────────────────────────────────────────
    # F1: 转化漏斗分析
    # ────────────────────────────────────────────
    lost_o2p = order_uv - pay_uv
    lost_gmv_est = lost_o2p * (gmv / pay_uv) if pay_uv else 0

    # 找断点
    diffs = [
        ("访问→浏览", cvr_v2b - p_cvr_v2b),
        ("浏览→下单", cvr_b2o - p_cvr_b2o),
        ("下单→支付", cvr_o2p - p_cvr_o2p),
    ]
    worst_step = min(diffs, key=lambda x: x[1])
    breakpoint_text = f"{worst_step[0]} {worst_step[1]:+.1f}个百分点" if worst_step[1] < -0.5 else "无明显断点"

    content = (
        f"<p>昨日访问 {fmt_num(visit_uv)} 人，最终支付 {fmt_num(pay_uv)} 人，"
        f"<strong>整体转化率 {cvr_overall:.1f}%</strong>。"
    )
    if worst_step[1] < -0.5:
        content += f"<strong>{worst_step[0]} 是断点（{worst_step[1]:+.1f}个百分点）</strong>，"
        content += f"约 {fmt_num(lost_o2p)} 人下单后未支付，估算流失 {fmt_yuan(lost_gmv_est)}。</p>"
    else:
        content += "各步骤转化率均稳定。</p>"

    if _narr(0):
        content = _narr(0)

    # 漏斗用 funnel 自定义标记，build_html 有专门渲染逻辑
    funnel_steps = [
        {"label": "访问人数", "value": visit_uv, "pct": pct_visit, "color": "#1E40AF",
         "rate_text": f"▲ {_pct_change(visit_uv, p_visit_uv):+.1f}%" if _pct_change(visit_uv, p_visit_uv) is not None else "-",
         "rate_sub": "访问人数 环比",
         "rate_cls": "good" if (_pct_change(visit_uv, p_visit_uv) or 0) >= 0 else "bad"},
        {"label": "浏览人数", "value": browse_uv, "pct": pct_browse, "color": "#0EA5E9",
         "rate_text": f"{cvr_v2b - p_cvr_v2b:+.1f}个百分点 {'✅' if cvr_v2b >= p_cvr_v2b else '⚠️'}",
         "rate_sub": "访问→浏览 环比", "rate_cls": "good" if cvr_v2b >= p_cvr_v2b else "bad",
         "lost": visit_uv - browse_uv},
        {"label": "下单人数", "value": order_uv, "pct": pct_order, "color": "#F59E0B",
         "rate_text": f"{cvr_b2o - p_cvr_b2o:+.1f}个百分点 {'✅' if cvr_b2o >= p_cvr_b2o else '⚠️'}",
         "rate_sub": "浏览→下单 环比", "rate_cls": "good" if cvr_b2o >= p_cvr_b2o else "bad",
         "lost": browse_uv - order_uv},
        {"label": "支付人数", "value": pay_uv, "pct": pct_pay, "color": "#22C55E",
         "rate_text": f"{cvr_o2p:.1f}% {'▼' if cvr_o2p < p_cvr_o2p else '▲'} {cvr_o2p - p_cvr_o2p:+.1f}个百分点",
         "rate_sub": "下单→支付 环比", "rate_cls": "bad" if cvr_o2p < p_cvr_o2p else "good",
         "lost": order_uv - pay_uv, "is_breakpoint": worst_step[1] < -0.5 and worst_step[0] == "下单→支付"},
    ]

    findings.append({
        "title": f"转化漏斗分析：{breakpoint_text}",
        "content_html": content,
        "funnel": funnel_steps,  # 专用字段，build_html 识别后渲染为漏斗图
        "tables": [{
            "headers": ["步骤", "人数", "占访问比", "步骤转化率", "环比变化"],
            "rows": [
                ["访问", fmt_num(visit_uv), "100%", "-", f"{_pct_change(visit_uv, p_visit_uv):+.1f}%" if _pct_change(visit_uv, p_visit_uv) is not None else "-"],
                ["浏览", fmt_num(browse_uv), f"{pct_browse:.1f}%", f"{cvr_v2b:.1f}%", _color_span(cvr_v2b - p_cvr_v2b, unit="pp") if p_cvr_v2b else "-"],
                ["下单", fmt_num(order_uv), f"{pct_order:.1f}%", f"{cvr_b2o:.1f}%", _color_span(cvr_b2o - p_cvr_b2o, unit="pp") if p_cvr_b2o else "-"],
                ["支付", fmt_num(pay_uv), f"{pct_pay:.1f}%", f"{cvr_o2p:.1f}%", _color_span(cvr_o2p - p_cvr_o2p, unit="pp") if p_cvr_o2p else "-"],
            ],
        }],
    })

    # ────────────────────────────────────────────
    # F2: 用户结构
    # ────────────────────────────────────────────
    new_uv = _si(us.get("new_pay_uv"))
    ret_uv = _si(us.get("returning_pay_uv"))
    new_gmv = _sf(us.get("new_gmv"))
    ret_gmv = _sf(us.get("returning_gmv"))
    total_uv_us = new_uv + ret_uv or pay_uv
    total_gmv_us = new_gmv + ret_gmv or gmv

    new_pct = new_uv / total_uv_us * 100 if total_uv_us else 0
    ret_pct = ret_uv / total_uv_us * 100 if total_uv_us else 0
    new_aov = new_gmv / new_uv if new_uv else 0
    ret_aov = ret_gmv / ret_uv if ret_uv else 0
    new_gmv_pct = new_gmv / total_gmv_us * 100 if total_gmv_us else 0
    ret_gmv_pct = ret_gmv / total_gmv_us * 100 if total_gmv_us else 0

    # 环比
    p_new_uv = _si(pus.get("new_pay_uv"))
    p_ret_uv = _si(pus.get("returning_pay_uv"))

    content = (
        f"<p>昨日支付人数 {fmt_num(total_uv_us)} 中，"
        f"<strong>新客 {fmt_num(new_uv)} 人（{new_pct:.1f}%）</strong>、"
        f"<strong>老客 {fmt_num(ret_uv)} 人（{ret_pct:.1f}%）</strong>。"
        f"老客客单价（{fmt_yuan_simple(ret_aov)}）"
        f"{'高出' if ret_aov > new_aov else '低于'}新客（{fmt_yuan_simple(new_aov)}）"
        f"{abs(ret_aov - new_aov) / new_aov * 100:.0f}%。</p>"
        if new_aov else
        f"<p>昨日支付人数 {fmt_num(total_uv_us)}。</p>"
    )
    if _narr(1):
        content = _narr(1)

    cid_user_bar = _cid("user_bar")
    cid_user_pie = _cid("user_pie")

    findings.append({
        "title": f"用户结构：新客 {new_pct:.1f}% / 老客 {ret_pct:.1f}%"
                 + (f"，老客客单价高出 {abs(ret_aov - new_aov) / new_aov * 100:.0f}%" if new_aov and ret_aov > new_aov else ""),
        "content_html": content,
        "charts": [
            {"id": cid_user_bar, "title": "新老客支付人数（昨日 vs 前日）", "type": "bar", "half_width": True,
             "data": {"labels": ["前日", "昨日"],
                      "datasets": [
                          {"label": "新客", "data": [p_new_uv, new_uv], "color": "#3B82F6"},
                          {"label": "老客", "data": [p_ret_uv, ret_uv], "color": "#0F172A"},
                      ]},
             "options": {"stacked": True}},
            {"id": cid_user_pie, "title": "昨日 GMV 新老客贡献占比", "type": "doughnut", "half_width": True,
             "data": {"labels": [f"老客 GMV（{ret_gmv_pct:.1f}%）", f"新客 GMV（{new_gmv_pct:.1f}%）"],
                      "datasets": [{"label": "GMV 占比",
                                    "data": [round(ret_gmv, 0), round(new_gmv, 0)],
                                    "colors": ["#0F172A", "#3B82F6"],
                                    "show_datalabels": True, "datalabel_format": "pct_plain"}]},
             "options": {"cutout": "55%"}},
        ],
        "tables": [{
            "headers": ["用户类型", "支付人数", "人数占比", "环比变化", "客单价", "贡献 GMV", "GMV 占比"],
            "rows": [
                ["新客", fmt_num(new_uv), f"{new_pct:.1f}%",
                 _color_span(_pct_change(new_uv, p_new_uv)) if p_new_uv else "-",
                 fmt_yuan_simple(new_aov), fmt_yuan(new_gmv), f"{new_gmv_pct:.1f}%"],
                ["老客", fmt_num(ret_uv), f"{ret_pct:.1f}%",
                 _color_span(_pct_change(ret_uv, p_ret_uv)) if p_ret_uv else "-",
                 fmt_yuan_simple(ret_aov), fmt_yuan(ret_gmv), f"{ret_gmv_pct:.1f}%"],
            ],
            "summary_row": [
                "<strong>合计</strong>", f"<strong>{fmt_num(total_uv_us)}</strong>", "<strong>100%</strong>",
                f"<strong>{_color_span(_pct_change(total_uv_us, p_new_uv + p_ret_uv)) if (p_new_uv + p_ret_uv) else '-'}</strong>",
                f"<strong>{fmt_yuan_simple(total_gmv_us / total_uv_us if total_uv_us else 0)}</strong>",
                f"<strong>{fmt_yuan(total_gmv_us)}</strong>", "<strong>100%</strong>",
            ],
        }],
    })

    # ────────────────────────────────────────────
    # F3: 品类表现
    # ────────────────────────────────────────────
    if cats:
        total_cat_gmv = sum(_sf(c.get("gmv")) for c in cats)

        cid_cat_bar = _cid("cat_bar")
        cid_cat_pie = _cid("cat_pie")

        cat_names = [c.get("category_name", "")[:6] for c in cats]
        cat_gmv_list = [_sf(c.get("gmv")) for c in cats]
        cat_colors = ["#0F172A", "#1E40AF", "#F59E0B", "#22C55E", "#7C3AED", "#94A3B8",
                      "#06B6D4", "#EF4444", "#D946EF", "#84CC16"]

        # 找退款率最高的品类
        worst_rr_cat = max(cats, key=lambda c: _sf(c.get("refund_rate")), default=None)
        # 找 CVR 最好的品类
        best_cvr_cat = max(cats, key=lambda c: _sf(c.get("cvr")), default=None)

        content = (
            f"<p>昨日共 {len(cats)} 个品类有成交"
        )
        if worst_rr_cat and _sf(worst_rr_cat.get("refund_rate")) > 10:
            content += (
                f"，<strong>{_esc(worst_rr_cat.get('category_name', ''))} 退款率 "
                f"{_sf(worst_rr_cat.get('refund_rate')):.1f}% 严重超红线</strong>"
            )
        content += "。"
        if best_cvr_cat:
            content += f"{_esc(best_cvr_cat.get('category_name', ''))} 转化率 {_sf(best_cvr_cat.get('cvr')):.1f}% 最优。"
        top3_cat_gmv = sum(_sf(c.get("gmv")) for c in cats[:3])
        top3_cat_pct = top3_cat_gmv / total_cat_gmv * 100 if total_cat_gmv else 0
        content += f"前三品类 GMV 集中度 {top3_cat_pct:.1f}%。</p>"

        if _narr(2):
            content = _narr(2)

        # 品类表格
        cat_rows = []
        for c in cats:
            c_gmv = _sf(c.get("gmv"))
            c_prev = _sf(c.get("prev_gmv"))
            c_chg = _pct_change(c_gmv, c_prev)
            c_pct = c_gmv / total_cat_gmv * 100 if total_cat_gmv else 0
            c_cvr = _sf(c.get("cvr"))
            c_rr = _sf(c.get("refund_rate"))

            # 退款率着色
            if c_rr > 10:
                rr_html = f"<span style='color:#EF4444;font-weight:700'>{c_rr:.1f}% 🔴</span>"
                health = "🔴 退款超标"
            elif c_rr > 8:
                rr_html = f"<span style='color:#F59E0B'>{c_rr:.1f}% ⚠️</span>"
                health = "⚠️ 退款偏高"
            else:
                rr_html = f"{c_rr:.1f}%"
                health = "✅ 健康"

            # CVR 着色
            cvr_html = f"<span style='color:#22C55E;font-weight:700'>{c_cvr:.1f}% ★</span>" if best_cvr_cat and c.get("category_name") == best_cvr_cat.get("category_name") else f"{c_cvr:.1f}%"

            cat_rows.append([
                _esc(c.get("category_name", "")),
                fmt_yuan(c_gmv),
                f"{c_pct:.1f}%",
                _color_span(c_chg) if c_chg is not None else "-",
                cvr_html,
                rr_html,
                health,
            ])

        # 合计行
        total_prev_cat = sum(_sf(c.get("prev_gmv")) for c in cats)
        total_chg_cat = _pct_change(total_cat_gmv, total_prev_cat)
        avg_cvr = sum(_sf(c.get("cvr")) for c in cats) / len(cats) if cats else 0
        total_rr = _sf(ov.get("refund_amt", 0)) / gmv * 100 if gmv else 0

        cat_summary = [
            "<strong>合计</strong>", f"<strong>{fmt_yuan(total_cat_gmv)}</strong>",
            "<strong>100%</strong>",
            f"<strong>{_color_span(total_chg_cat) if total_chg_cat is not None else '-'}</strong>",
            f"{avg_cvr:.1f}% 均值", f"{total_rr:.1f}%", "—",
        ]

        findings.append({
            "title": f"品类表现"
                     + (f"：{_esc(worst_rr_cat.get('category_name', ''))} 退款率 {_sf(worst_rr_cat.get('refund_rate')):.1f}%" if worst_rr_cat and _sf(worst_rr_cat.get("refund_rate")) > 10 else ""),
            "content_html": content,
            "charts": [
                {"id": cid_cat_bar, "title": "各品类 GMV（元）", "type": "bar", "half_width": True,
                 "data": {"labels": cat_names,
                          "datasets": [{"label": "GMV（元）", "data": cat_gmv_list,
                                        "colors": cat_colors[:len(cats)]}]},
                 "options": {"index_axis": "y", "hide_legend": True}},
                {"id": cid_cat_pie, "title": "品类 GMV 占比", "type": "doughnut", "half_width": True,
                 "data": {"labels": cat_names,
                          "datasets": [{"label": "GMV 占比", "data": cat_gmv_list,
                                        "colors": cat_colors[:len(cats)],
                                        "show_datalabels": True, "datalabel_format": "pct_plain"}]},
                 "options": {"cutout": "55%"}},
            ],
            "tables": [{
                "headers": ["品类", "GMV", "GMV 占比", "环比（前日）", "转化率 CVR", "退款率", "健康判定"],
                "rows": cat_rows,
                "summary_row": cat_summary,
            }],
        })

    # ────────────────────────────────────────────
    # F4: 异常信号汇总
    # ────────────────────────────────────────────
    signals = []
    refund_rate = _sf(ov.get("refund_amt", 0)) / gmv * 100 if gmv else 0
    prev_refund_rate = _sf(pov.get("refund_amt", 0)) / _sf(pov.get("gmv")) * 100 if _sf(pov.get("gmv")) else 0

    # 退款率检查
    if refund_rate > 10:
        signals.append(("🔴", f"退款率 {refund_rate:.1f}%，严重超红线（>10%）",
                        f"退款率 {refund_rate:.1f}%，较前日{'+' if refund_rate > prev_refund_rate else ''}{refund_rate - prev_refund_rate:.1f}个百分点。"))
    elif refund_rate > 8:
        signals.append(("⚠️", f"退款率 {refund_rate:.1f}%，接近红线（>8%）",
                        f"退款率环比{'上升' if refund_rate > prev_refund_rate else '下降'}{abs(refund_rate - prev_refund_rate):.1f}个百分点。"))

    # 品类级别退款
    if cats:
        for c in cats:
            rr = _sf(c.get("refund_rate"))
            if rr > 10:
                signals.append(("🔴", f"{c.get('category_name', '')} 退款率 {rr:.1f}%，严重超红线",
                                f"GMV {fmt_yuan(c.get('gmv'))} 中约 {fmt_yuan(_sf(c.get('gmv')) * rr / 100)} 将被退款侵蚀。"))

    # 下单→支付转化率
    if cvr_o2p < 85:
        signals.append(("⚠️", f"下单→支付转化率 {cvr_o2p:.1f}%，跌破 85% 警戒线（{cvr_o2p - p_cvr_o2p:+.1f}个百分点）",
                        f"约 {fmt_num(lost_o2p)} 人下单后未支付，估算每日流失约 {fmt_yuan(lost_gmv_est)}。"))

    # 连带率
    derived = compute_derived(ov)
    attach = derived.get("attach_rate", 0)
    if attach < 1.5:
        signals.append(("⚠️", f"连带率 {attach:.2f}，低于 1.5 警戒线",
                        f"每单件数减少直接拉低客单价。若提升至 1.5 可带来日 GMV 增量约 {fmt_yuan(gmv * (1.5 - attach) / attach if attach else 0)}。"))

    if not signals:
        signals.append(("✅", "未检测到异常信号", "各项指标均在健康范围内。"))

    if _narr(3):
        content = _narr(3)
    else:
        alert_cnt = sum(1 for s in signals if s[0] == "🔴")
        warn_cnt = sum(1 for s in signals if s[0] == "⚠️")
        content = f"<p>四角度扫描共发现 <strong>{alert_cnt} 个红色预警、{warn_cnt} 个警示信号</strong>。</p>"

    findings.append({
        "title": "异常信号汇总",
        "content_html": content,
        "signals": signals,  # 专用字段，build_html 识别后渲染为信号列表
    })

    return findings

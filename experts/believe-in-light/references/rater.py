# -*- coding: utf-8 -*-
"""
rater.py — Layer 4 赛道评级（平定级）· 报告渲染

严格对齐设计文档「Layer 4 输出要素」：
  · 最终评级（🟢🟡🔴 + 一句话）
  · 景气度（数值 + 方向 + 各链 chain_net 拆解 → 由多链收敛卡承载）
  · 置信度（档位 + C/R/S 各因子值及理由）
  · 多链收敛卡（每条链净方向与幅度，标注一致/冲突）
  · 自进化状态（权重来源 / 样本数 / 下次校准日）
  · 运行元信息（模式 / 快照时间 / 数据源状态 → 头部徽章）

九宫格（景气度 × 置信度）作为「最终评级」的可视化一并呈现。
[已移除] Δ景气度 / 仓位建议 / 三端信号明细 / 链转变 / 耦合反转 / 锚变化 / 权重Top5
—— 文档输出要素未列这些块，且部分依赖本程序暂无的真实跨期/逐信号数据，
   强行渲染为假精度，违背「不造假」原则。

用法：
  python rater.py --prosperity <json> --out report.html
  python rater.py --self-test
"""
from __future__ import annotations
import json
import argparse
import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 九宫格映射（与设计文档 Layer4 九宫格详图一致）
GRID = {
    ("扩张", "高"): ("🟢", "积极", "三链共振且证据扎实，可积极看待赛道景气度"),
    ("扩张", "中"): ("🟡", "有据", "方向向好但置信一般，需跟踪确认"),
    ("扩张", "低"): ("🔴", "矛盾", "方向虽扩但置信低，信号互相打架，需重审"),
    ("持平", "高"): ("🟡", "平稳", "方向中性但数据可靠，信号状态稳定"),
    ("持平", "中"): ("🟡", "观察", "方向中性，持续观察边际变化"),
    ("持平", "低"): ("🔴", "存疑", "无明确方向且置信低，信号不充分"),
    ("收缩", "高"): ("🔴", "承压", "方向转弱且证据扎实，赛道景气承压"),
    ("收缩", "中"): ("🟡", "偏弱", "方向偏弱，信号尚不充分"),
    ("收缩", "低"): ("🔴", "低迷", "方向弱且置信低，信号全面低迷"),
}


def rate(prosperity_direction: str, confidence_label: str):
    key = (prosperity_direction, confidence_label)
    emoji, label, sentence = GRID.get(key, ("⚪", "未知", "无对应评级"))
    return emoji, label, sentence


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_report(weight_summary, meta, evolution):
    emoji, label, sentence = rate(weight_summary["prosperity_direction"],
                                  weight_summary["confidence_label"])
    return {
        "rating": [emoji, label, sentence],
        "summary": weight_summary,
        "meta": meta,
        "evolution": evolution,
    }


# ---------- 各卡片渲染 ----------
def _pill(text, kind):
    return f'<span class="pill {kind}">{esc(text)}</span>'


def _render_confidence(s):
    return f"""
      <div class="card">
        <h2>置信度（C × R × S）</h2>
        <div class="kv"><span>跨链收敛 C</span><b>{s['confidence_C']}</b></div>
        <div class="kv"><span>可靠度 R（期数→值）</span><b>{s['confidence_R']}</b></div>
        <div class="kv"><span>来源可信度 S</span><b>{s['confidence_S']}</b></div>
        <div class="kv"><span>合计</span><b>{s['confidence_raw']}（{s['confidence_label']}）</b></div>
        <div class="note">C=同向链数/总链数(3，含静默链)；R=累计期数→0.3/0.6/0.9；S=专业1.0/部分0.8/纯网0.6</div>
      </div>"""


def _render_convergence(s):
    rows = ""
    for c in s["convergence_card"]:
        if c["net"] is None:
            rows += f"<tr><td>{c['chain']}</td><td>—</td><td>无信号</td><td>—</td></tr>"
        else:
            ag = "✔ 同向" if c["agree"] else ("✘ 冲突" if c["agree"] is False else "—")
            rows += (f"<tr><td>{c['chain']}</td><td>{c['net']:+.3f}</td>"
                     f"<td>{c['direction']}</td><td>{ag}</td></tr>")
    return f"""
      <div class="card">
        <h2>多链收敛卡</h2>
        <table><tr><th>链</th><th>净方向值</th><th>方向</th><th>与总方向</th></tr>{rows}</table>
        <div class="note">每条链触发的信号中最靠近结局的=后序(计入净方向)；之前的=前序(不计入)。一致→C 高→置信上抬。</div>
      </div>"""


def _render_evolution(evo):
    # 权重来源：程序化生成，杜绝 LLM 自由文本膨胀（一句话、仅说是否校准+低置信主因）
    n_cal = evo.get("calibrated_signals", 0) or 0
    R = evo.get("R")
    if n_cal > 0:
        hit_source = f"已校准（{n_cal} 个信号样本≥3），权重基于真实命中率"
    else:
        hit_source = (f"冷启动默认 0.5（未校准）；叠加期数不足（R={R}），"
                      f"故置信度=低，随真实样本累积自动改善")
    return f"""
      <div class="kv"><span>累计期数(R)</span><b>{evo.get('run_count', '—')}</b></div>
      <div class="kv"><span>R 值</span><b>{R}</b></div>
      <div class="kv"><span>已校准信号</span><b>{n_cal}</b></div>
      <div class="kv"><span>下次校准</span><b>{evo.get('next_calibration') or '—'}</b></div>
      <div class="kv"><span>权重来源</span><b>{hit_source}</b></div>"""


def render_html(report: dict) -> str:
    s = report["summary"]
    meta = report.get("meta") or {}
    evo = report.get("evolution") or {}
    emoji, label, sentence = report["rating"]
    rating_color = {"🟢": "#16a34a", "🟡": "#d97706", "🔴": "#dc2626"}.get(emoji, "#555")

    mode = meta.get("mode", "未知")
    mode_badge = {"专业": ("badge-green", "🟢 专业模式（万得+通达信）"),
                  "部分": ("badge-amber", "🟡 部分模式（缺一项数据源）"),
                  "纯网": ("badge-red", "🔴 纯互联网模式（精度下降）")}.get(mode, ("badge-amber", mode))

    # 最顶部全宽警示横幅（标题之上）— 统一四要素免责声明
    topbanner = """
      <div class="topbanner">
        <div class="banner-title"><span>⚠️</span> 重要警示 <span>⚠️</span></div>
        <ul>
          <li><b>① AI 生成：</b>本报告全部内容由 AI 模型基于公开信息自动整理生成，非人工撰写，不构成任何形式的个人/机构观点。</li>
          <li><b>② 基于公开信息：</b>所有评级、信号、权重均为系统基于互联网/数据源公开信息机械运算的结果，不含未公开数据，精度有限。</li>
          <li><b>③ 不构成投资建议：</b>仅供学习参考与框架验证，不涉及估值（PE/PB/PEG），不能作为买卖决策依据。</li>
          <li><b>④ 不构成个股推荐：</b>本系统为赛道级景气度评级，不针对任何具体个股、标的或证券给出买入/卖出推荐。</li>
          <li><b>用得越久才越准，前期不准。</b>本系统通过自升级机制持续校准信号权重，前几个月权重为默认值、准确率低，随真实样本累积自动改善。</li>
        </ul>
      </div>"""

    # 顶部提醒（数据源 / 模式）
    topalert = f"""
      <div class="topalert">
        <div class="item {'a-blue' if meta.get('mode')=='专业' else 'a-amber' if meta.get('mode')=='部分' else 'a-red'}">
          <span class="ic">{'📡' if meta.get('mode')=='专业' else '⚠️'}</span>
          <div><b>{meta.get('mode', '未知')}数据源：</b>{esc(meta.get('data_source', ''))}</div></div>
      </div>"""

    # 评级推导
    cons = s["confidence_label"]
    derivation = f"""
      <div class="grid cols-2" style="gap:22px">
        <div>
          <h3>① 这个评级是怎么算出来的</h3>
          <table style="margin-bottom:12px"><tbody>
            <tr><td style="background:#f8fafc;font-weight:600;width:96px">第一层</td>
              <td>方向 <b>{s['prosperity_direction']}</b> → 景气度水平
                {_pill('高·扩张' if s['prosperity_signed']>=1.5 else '中' if s['prosperity_signed']>=0.5 else '低', 'neu')}</td></tr>
            <tr><td style="background:#f8fafc;font-weight:600">第二层</td>
              <td>景气度 × 置信度 <b>{cons}</b> → 九宫格 = {_pill(emoji+' '+label, 'neu')}</td></tr>
          </tbody></table>
          <div class="logic-box"><b>因果链角色：</b>每条链触发的信号中最靠近结局的=后序，计入净方向；
            之前的触发信号=前序，不进景气度。三链同向→C高→置信度上抬。</div>
        </div>
        <div>
          <h3>② 九宫格（景气度 × 置信度）</h3>
          {_render_ninegrid(s['prosperity_direction'], cons)}
        </div>
      </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>光模块赛道评级报告</title>
<style>
  :root{{--bg:#eef1f5;--card:#fff;--text:#1f2933;--muted:#6b7785;--border:#e2e8f0;
    --green:#16a34a;--greenbg:#dcfce7;--red:#dc2626;--redbg:#fee2e2;
    --blue:#2563eb;--bluebg:#dbeafe;--amber:#d97706;--amberbg:#fef3c7;--shadow:0 1px 3px rgba(0,0,0,.08)}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
    background:var(--bg);color:var(--text);line-height:1.55;padding:24px}}
  .wrap{{max-width:1080px;margin:0 auto}}
  .header{{background:var(--card);border-radius:12px;padding:20px 24px;box-shadow:var(--shadow);margin-bottom:16px}}
  .header h1{{font-size:20px;font-weight:700;margin-bottom:8px}}
  .meta{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:13px;color:var(--muted)}}
  .badge{{padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600}}
  .badge-red{{background:var(--redbg);color:var(--red)}}
  .badge-amber{{background:var(--amberbg);color:var(--amber)}}
  .badge-green{{background:var(--greenbg);color:var(--green)}}
  .topalert{{display:grid;gap:8px;margin-top:14px}}
  .topalert .item{{display:flex;gap:10px;align-items:flex-start;padding:10px 14px;border-radius:8px;font-size:12.8px;line-height:1.55}}
  .topalert .item .ic{{flex-shrink:0;font-size:15px;line-height:1.2;margin-top:1px}}
  .topalert .a-red{{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}}
  .topalert .a-amber{{background:#fffbeb;border:1px solid #fde68a;color:#92600a}}
  .topalert .a-blue{{background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af}}
  .topalert b{{font-weight:700}}
  .topbanner{{background:#fef2f2;border:2px solid #f87171;color:#7f1d1d;border-radius:10px;
             padding:14px 18px;margin-bottom:14px}}
  .topbanner .banner-title{{font-size:15px;font-weight:700;margin-bottom:8px;
             display:flex;gap:6px;align-items:center}}
  .topbanner ul{{margin:0;padding-left:18px;font-size:12.5px;line-height:1.7}}
  .topbanner li{{margin-bottom:4px}}
  .topbanner b{{font-weight:700}}
  .grid{{display:grid;gap:16px}}
  .cols-3{{grid-template-columns:repeat(3,1fr)}}
  .cols-2{{grid-template-columns:repeat(2,1fr)}}
  @media(max-width:860px){{.cols-3,.cols-2{{grid-template-columns:1fr}}}}
  .card{{background:var(--card);border-radius:12px;padding:18px 20px;box-shadow:var(--shadow)}}
  .card h2{{font-size:15px;font-weight:700;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)}}
  .card h3{{font-size:13.5px;margin:2px 0 10px;color:var(--muted)}}
  .rating-box{{text-align:center;padding:8px 0}}
  .rating-emoji{{font-size:40px;line-height:1}}
  .rating-label{{font-size:18px;font-weight:700;margin-top:6px}}
  .rating-sub{{font-size:13px;color:var(--muted);margin-top:4px}}
  .kv{{display:flex;justify-content:space-between;font-size:13px;padding:5px 0;border-bottom:1px dashed var(--border)}}
  .kv:last-child{{border-bottom:none}}
  .pill{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11.5px;font-weight:600}}
  .pos{{background:var(--greenbg);color:var(--green)}}
  .neg{{background:var(--redbg);color:var(--red)}}
  .neu{{background:var(--bluebg);color:var(--blue)}}
  .placeholder{{background:#f1f5f9;border:1px dashed #cbd5e1;color:#64748b;border-radius:8px;padding:14px;font-size:13px;text-align:center}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px}}
  th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--border)}}
  th{{color:var(--muted);font-weight:600;background:#f8fafc}}
  .disclaimer{{font-size:11.5px;color:var(--muted);line-height:1.7}}
  .logic-box{{font-size:12.5px;color:var(--muted);background:#f8fafc;border-radius:8px;padding:10px 12px;line-height:1.65}}
  .logic-box b{{color:var(--text)}}
  .ninegrid td{{text-align:center;font-weight:700;padding:9px 6px}}
  .ninegrid th{{text-align:center}}
  .ninegrid .hl{{outline:3px solid #1f2933;outline-offset:-3px}}
  .note{{font-size:12px;color:var(--muted);margin-top:8px}}
</style></head>
<body><div class="wrap">

  {topbanner}

  <div class="header">
    <h1>光模块赛道 · 信号监控评级报告</h1>
    <div class="meta">
      <span>快照：{esc(meta.get('run_date', '—'))}</span>
      <span class="badge {mode_badge[0]}">{mode_badge[1]}</span>
      <span class="badge badge-amber">触发信号：{meta.get('triggered_count', 0)} 个</span>
    </div>
    {topalert}
  </div>

  <div class="grid cols-3">
    <div class="card">
      <h2>评级结论（水平）</h2>
      <div class="rating-box">
        <div class="rating-emoji" style="color:{rating_color}">{emoji}</div>
        <div class="rating-label">{label}</div>
        <div class="rating-sub">{sentence}</div>
      </div>
      <div style="margin-top:10px">
        <div class="kv"><span>景气度</span>{_pill(('高·扩张' if s['prosperity_signed']>=1.5 else '中' if s['prosperity_signed']>=0.5 else '低')+' · '+s['prosperity_direction'], 'pos')}</div>
        <div class="kv"><span>置信度</span>{_pill(cons, 'neu')}</div>
        <div class="kv"><span>最终评级</span>{_pill(emoji+' '+label, 'neu')}</div>
      </div>
    </div>

    {_render_confidence(s)}

    {_render_convergence(s)}
  </div>

  <div class="card" style="margin-top:16px">
    <h2>评级推导逻辑 &amp; 九宫格矩阵</h2>
    {derivation}
  </div>

  <div class="card" style="margin-top:16px">
    <h2>自进化状态</h2>
    {_render_evolution(evo)}
  </div>

  <div class="card" style="margin-top:16px">
    <h2>置信度与数据局限</h2>
    <div class="disclaimer">
      • 运行模式：{esc(meta.get('data_source', '未知'))}。<br>
      • 置信度受数据源限制：纯网模式数据精度下降，置信度受限；接入专业数据源后预期上抬。<br>
      • 景气指数阈值（幅度分级）、置信因子映射待「命中率季度回看」后校准。<br>
      • <b>Δ/仓位说明</b>：本程序暂不渲染 Δ景气度（动量）与仓位建议——当前无真实跨期/仓位数据，强行输出为假精度。连续多周真实运行后即可由快照序列恢复期对期对比。
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>免责声明</h2>
    <div class="disclaimer">
      ⚠️ 以上内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。<br><br>
      本系统前六个月权重均为默认值，因果链/权重的方法论仍在演进中。本报告仅供学习参考与框架验证，据此操作风险自负。
    </div>
  </div>

</div></body></html>"""


def _render_ninegrid(direction, conf):
    # 行标签是「景气度水平(高/中/低)」；GRID 以「方向(扩张/持平/收缩)」为键，
    # 故查表前需把水平映射回方向，否则所有格都会命中兜底「承压」。
    LEVEL_TO_DIR = {"高": "扩张", "中": "持平", "低": "收缩"}
    lvl = "高" if direction == "扩张" else "中" if direction == "持平" else "低"
    rows = []
    for lv in ["高", "中", "低"]:
        cells = []
        for cf in ["高", "中", "低"]:
            key = (LEVEL_TO_DIR[lv], cf)
            emoji, txt, _ = GRID.get(key, ("🔴", "承压", ""))
            style = ""
            if lv == lvl and cf == conf:
                style = ' class="hl"'
            color = {"🟢": "var(--greenbg);color:var(--green)",
                     "🟡": "var(--amberbg);color:var(--amber)",
                     "🔴": "var(--redbg);color:var(--red)"}.get(emoji, "")
            cells.append(f'<td{style} style="background:{color}">{emoji} {txt}</td>')
        rows.append(f'<tr><td style="background:#f8fafc;font-weight:700;text-align:left">{lv}</td>{"".join(cells)}</tr>')
    return (f'<table class="ninegrid"><thead><tr><th>景气度＼置信度</th>'
            f'<th>高</th><th>中</th><th>低</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
            f'<div style="font-size:12px;color:var(--muted);margin-top:10px;text-align:center">'
            f'当前位置：<b>{lvl}景气 × {conf}置信</b></div>')


def self_test():
    # 演示值：技术链静默 → 仅供给(+)、需求(+) 两链同向，C=2/3
    demo_summary = {
        "prosperity_signed": 1.6, "by_chain": {"供给": 0.6, "需求": 1.0},
        "prosperity_direction": "扩张",
        "confidence_C": round(2/3, 3), "confidence_R": 0.6, "confidence_S": 1.0,
        "confidence_raw": 0.40, "confidence_label": "中",
        "convergence_card": [
            {"chain": "供给", "net": 0.6, "direction": "扩张", "agree": True},
            {"chain": "需求", "net": 1.0, "direction": "扩张", "agree": True},
            {"chain": "技术", "net": None, "direction": "无信号", "agree": None},
        ],
    }
    meta = {"run_date": "2026-07-11", "mode": "专业", "mode_factor": 1.0,
            "data_source": "万得 ✅ + 通达信 ✅", "triggered_count": 9}
    evo = {"run_count": 11, "R": 0.6, "calibrated_signals": 19,
           "next_calibration": "2026-10-11"}

    rep = build_report(demo_summary, meta, evo)
    html = render_html(rep)
    print("=== 平定级 self-test (文档对齐版) ===")
    assert rep["rating"] == ["🟡", "有据", "方向向好但置信一般，需跟踪确认"]
    # 文档输出要素应有的块
    for must in ["评级推导逻辑", "九宫格", "C × R × S", "多链收敛卡",
                 "自进化状态", "免责声明", "重要警示",
                 "不涉及估值", "用得越久才越准"]:
        assert must in html, f"缺块: {must}"
    # 文档未列的块（不得出现）
    for must_not in ["<h2>Δ景气度（动量）</h2>", "<h2>仓位建议</h2>",
                     "<h2>三端信号明细（本周触发）</h2>", "<h2>链转变（跨期）</h2>",
                     "<h2>耦合反转</h2>", "<h2>锚变化（最早逆转传感器）</h2>",
                     "<h2>权重 Top5（后序信号）</h2>", "加仓/高仓位", "Δ = +0.30"]:
        assert must_not not in html, f"不应出现: {must_not}"
    print(f"评级: {rep['rating'][0]} {rep['rating'][1]}")
    print("[test] ✅ 报告严格对齐文档输出要素；多链收敛卡保留；非文档块已剔除")


def main():
    ap = argparse.ArgumentParser(description="Layer4 赛道评级（平定级）")
    ap.add_argument("--prosperity", required=False, help="Layer3 输出 JSON (含 summary)")
    ap.add_argument("--out", default="report.html", help="输出 HTML 路径")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.prosperity:
        print("错误: 需提供 --prosperity 或 --self-test")
        sys.exit(1)
    with open(args.prosperity, encoding="utf-8") as f:
        w = json.load(f)
    rep = build_report(w["summary"], w.get("meta", {}), w.get("evolution", {}))
    html = render_html(rep)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[rater] 已写 {args.out} → {rep['rating'][0]} {rep['rating'][1]}")


if __name__ == "__main__":
    main()

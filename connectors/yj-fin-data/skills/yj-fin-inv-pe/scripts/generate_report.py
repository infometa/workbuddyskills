#!/usr/bin/env python3
"""
股权投资分析报告生成器（yj-fin-inv-pe · v1.0）

读取经 `scripts/assemble_data.py` 校验归一的报告输入 JSON，生成**单文件自包含 HTML**
股权投资分析报告：五维雷达（技术壁垒/商业化/团队/政策竞争/经营风险）、可比公司市值条图
与乘数柱图、三层估值与敏感度对照、企业画像四列表格、行业八点、风险提示与待核验清单、结论。

设计要点：
  - 图表引擎 ECharts 从同目录 assets/echarts.min.js 读取并**内联**进 HTML；
    运行时零外部请求、客户端离线也能正常渲染。资产缺失/不可读/含 `</script` 字面量时
    **非零退出**并指名字符路径，绝不产出图表静默空白的报告。
  - __ECHARTS_LIB__ 占位标记**最后**一次替换（1MB 源码不会被后续 token 扫到）。
  - stdout 只打产物绝对路径；诊断信息走 stderr。

Usage:
    python3 generate_report.py --data /path/to/{公司}_inv_pe_input.json
    python3 generate_report.py --data /path/to/{公司}_inv_pe_input.json --output-dir /path/to/output/
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import default_skill_output_dir

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ECHARTS_ASSET_PATH = os.path.join(SCRIPT_DIR, "assets", "echarts.min.js")


class AssetError(RuntimeError):
    """内联第三方资源缺失或不可用。"""


def load_echarts_js():
    """读取本地 ECharts 资产，供内联进报告 HTML。

    报告必须自包含，故资产缺失/不可读时**直接失败**（由 main 转成非零退出），
    绝不静默降级成"图表空白"。
    路径相对本脚本自身解析，与 cwd 无关。
    """
    try:
        with open(ECHARTS_ASSET_PATH, "r", encoding="utf-8") as f:
            js = f.read()
    except OSError as e:
        raise AssetError(
            f"内联图表引擎缺失或不可读：{ECHARTS_ASSET_PATH}（{e}）。"
            f"该文件随技能包分发，请从技能包补回后重试。") from e
    # HTML 规范里 script 数据以 `</script`（不区分大小写、后跟空白/`/`/`>`）结束，
    # 故这里按不区分大小写判定，避免大小写变体提前闭合 script 块。
    if re.search(r"</script", js, re.IGNORECASE):
        raise AssetError(
            f"内联图表引擎 {ECHARTS_ASSET_PATH} 含 </script 字面量（不区分大小写），"
            f"内联会提前闭合 script 块并破坏 HTML；请更换资产。")
    return js


def _f(v, nd=2, suffix=""):
    """数值格式化；None → '—'。"""
    if v is None:
        return "—"
    try:
        return f"{float(v):,.{nd}f}{suffix}"
    except (TypeError, ValueError):
        return "—"


def _pct(v):
    return _f(v, 1, "%")


# ============================================================
#  红标（数据语义）—— 唯一解析点在数据**入口**
# ============================================================

RED_MARK_RE = re.compile(r"\[\[红\]\](.*?)\[\[/红\]\]", re.DOTALL)


def _parse_redmark(s):
    """字符串里的 [[红]]…[[/红]] → <span class="hl-red">…</span>（红 #B23A33）。

    幂等：不含标记则原样返回；已解析过的内容再跑一次也不会重复包裹。
    """
    if not isinstance(s, str) or not s:
        return s
    return RED_MARK_RE.sub(r'<span class="hl-red">\1</span>', s)


def _apply_redmark(node):
    """递归整棵数据树解析红标——**红标的唯一解析点**（入口调用一次）。

    为什么放在入口而不是各输出路径：红标标记的是「差异 / 待补充核验」这类
    **数据语义**，不是某一处的排版效果。若交给各输出路径逐条转换，那么每新增
    一条输出路径都要记得补一次转换，漏一处就把未解析的标记原样输出成文本。
    放在入口统一解析后，渲染层接触到的永远是已解析内容，
    **新增任意输出路径都不会漏**。
    """
    if isinstance(node, str):
        return _parse_redmark(node)
    if isinstance(node, list):
        return [_apply_redmark(v) for v in node]
    if isinstance(node, dict):
        return {k: _apply_redmark(v) for k, v in node.items()}
    return node


def _inline_md(t):
    """行内排版符号 → HTML（不包裹段落，也**不处理红标**）。

    红标由入口 `_apply_redmark` 统一解析；这里只管**排版层**的符号约定
    （【小标题】转 run-in 加粗、**粗体**、`行内代码` 转 <code>），
    供 `md_to_html` 的每段与 `_table` 的 txt 列共用。
    """
    if not t:
        return ""
    t = re.sub(r"【(.+?)】", r'<span class="hl">\1</span>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def md_to_html(t):
    """分析文本 → HTML。

    支持：\n\n 分段，段内 \n 转 <br>；逐段套用 `_inline_md`（【】/**/` 排版约定）。
    红标不在这里处理——已在入口由 `_apply_redmark` 解析完毕（幂等，重复调用无害）。
    """
    if not t:
        return ""
    parts = []
    for p in t.split("\n\n"):
        p = p.strip()
        if not p:
            continue
        p = _inline_md(p).replace("\n", "<br>")
        parts.append('<p class="atext">' + p + "</p>")
    return "".join(parts)


# ============================================================
#  HTML 模板（token 替换，避免 f-string 大括号转义）
# ============================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<script>__ECHARTS_LIB__</script>
<style>
:root{
  --page:#1E2430; --paper:#FBFCFE;
  --ink:#1F2937; --ink2:#4B5563; --muted:#8A94A6;
  --rule:#E3E8F0; --rule2:#C7D0DE;
  --accent:#1F5FA8; --accent-deep:#143F72;
  --up:#B23A33; --down:#2E8B57; --warn:#B0820E;
  --serif:"Songti SC","Noto Serif SC","STSong","SimSun",Georgia,serif;
  --sans:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC","Helvetica Neue",Arial,sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:var(--sans);background:var(--page);color:var(--ink);line-height:1.85;font-size:14px;
     font-variant-numeric:tabular-nums}
.sidebar{position:fixed;left:0;top:0;bottom:0;width:212px;background:#161B25;color:#AEB7C7;
         overflow-y:auto;z-index:50;padding:30px 0 36px}
.side-brand{padding:0 20px 18px;border-bottom:1px solid rgba(174,183,199,.20);margin-bottom:14px}
.side-brand .co{font-family:var(--serif);font-size:18px;font-weight:700;color:#F2F6FC;letter-spacing:1px}
.side-brand .code{font-size:11px;letter-spacing:.10em;opacity:.66;margin-top:4px}
.side-brand .ic{font-size:11.5px;color:#7FB0E6;margin-top:10px;line-height:1.6}
.side-nav a{display:block;padding:7px 20px;color:#94A0B4;font-size:12.5px;text-decoration:none;
            border-left:2px solid transparent;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
            transition:color .15s}
.side-nav a:hover{color:#F2F6FC}
.side-nav a.active{color:#F2F6FC;border-left-color:var(--accent);background:rgba(31,95,168,.12)}
.main{margin-left:212px;padding:40px 46px;display:flex;justify-content:center}
.sheet{width:100%;max-width:1080px;background:var(--paper);border:1px solid var(--rule);
       box-shadow:0 2px 18px rgba(22,27,37,.10);padding:54px 62px 44px}
@media (max-width:1080px){.sidebar{display:none}.main{margin-left:0;padding:12px}.sheet{padding:26px 18px}}
/* 窄视口：表格已是滚动容器，这里只收紧内边距与字号，让更多列一屏可见。 */
@media (max-width:640px){
  .sheet{padding:20px 12px}
  .data-table{font-size:12px}
  .data-table th,.data-table td{padding:7px 8px}
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
  .kpi:nth-child(3n){border-right:1px solid var(--rule)}
  .kpi:nth-child(2n){border-right:none}
  .chart{height:300px}
  .chart.sm{height:268px}
}
.kicker{font-size:10.5px;font-weight:600;letter-spacing:.22em;color:var(--accent);text-transform:uppercase}
.masthead{display:flex;justify-content:space-between;align-items:flex-start;gap:28px;flex-wrap:wrap}
.masthead h1{font-family:var(--serif);font-size:28px;font-weight:700;letter-spacing:1.5px;margin-top:8px}
.mast-meta{font-size:12px;color:var(--muted);margin-top:8px;letter-spacing:.02em}
.mast-meta b{color:var(--ink2);font-weight:600}
.ic-box{margin-top:16px;padding:14px 18px;background:#F1F6FC;border-left:3px solid var(--accent);
        border-radius:2px;font-size:13.5px;color:var(--accent-deep);line-height:1.7}
.rule-double{height:6px;border-top:2.5px solid var(--ink);border-bottom:1px solid var(--ink);margin:20px 0 0}
.kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);border-bottom:1px solid var(--rule);margin:18px 0 6px}
.kpi{padding:14px 16px 12px;border-right:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.kpi:nth-child(3n){border-right:none}
.kpi-label{font-size:11px;color:var(--muted);letter-spacing:.06em}
.kpi-value{font-family:var(--serif);font-size:21px;font-weight:700;color:var(--ink);margin-top:3px;letter-spacing:.3px}
.kpi-sub{font-size:11px;color:var(--ink2);margin-top:2px}
.section{padding:38px 0 8px;border-top:1px solid var(--rule)}
.section:first-of-type{border-top:none}
.section h2{font-family:var(--serif);font-size:20px;font-weight:700;letter-spacing:1.2px;margin:6px 0 16px;scroll-margin-top:20px}
.section h3{font-size:13px;font-weight:600;color:var(--ink2);letter-spacing:.05em;margin:20px 0 6px}
.chart{width:100%;height:380px;margin:6px 0 2px}
.chart.sm{height:320px}
.chart-row{display:flex;gap:26px;flex-wrap:wrap;align-items:flex-start}
/* min-width 用 min(360px,100%)：窄视口下 360px 硬下限会把容器顶出屏幕，
   而 flex-wrap 只在**换行后**才解决问题，单列窄于 360px 时仍会横向溢出。 */
.chart-row>div{flex:1;min-width:min(360px,100%)}
.atext{font-size:13.6px;color:#374151;margin:10px 0;text-align:justify}
.hl{font-weight:700;color:var(--accent-deep);margin-right:5px}
.hl-red{font-weight:700;color:var(--up)}
code{font-family:"SFMono-Regular",Consolas,monospace;font-size:12px;background:#EEF2F7;padding:1px 5px;border-radius:3px;color:#27496E}
/* 表格横向兜底：宽表在本层滚动，绝不把文档撑宽。
   这张表**必须存在**——表格输出侧每张表都套了 <div class="tbl-wrap">，
   缺了它包裹层就是空壳，nowrap 的宽表会直接顶破 .sheet 与 body。 */
.tbl-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}
.tbl-wrap::-webkit-scrollbar{height:6px}
.tbl-wrap::-webkit-scrollbar-thumb{background:var(--rule2);border-radius:3px}
.data-table{width:100%;border-collapse:collapse;margin:14px 0;font-size:12.5px}
.data-table th{font-size:11px;font-weight:600;letter-spacing:.05em;color:var(--ink2);
               padding:9px 10px;border-top:1.5px solid var(--ink);border-bottom:1px solid var(--rule2);
               text-align:right;background:none}
.data-table th:first-child{text-align:left}
/* 列分型：数字列 nowrap 保持严格对齐；文本列必须能换行。
   散文列若套用数字列的 nowrap，长文本整格不折行 → 表格无限变宽。 */
.data-table td{padding:7px 10px;border-bottom:1px solid var(--rule);text-align:right;color:#374151}
.data-table td:first-child{text-align:left;color:var(--ink2)}
.data-table th.num,.data-table td.num{white-space:nowrap}
.data-table th.txt,.data-table td.txt{white-space:normal;overflow-wrap:anywhere;word-break:break-word;line-height:1.65}
.data-table tbody tr:last-child td{border-bottom:1px solid var(--rule2)}
.data-table tbody tr:hover{background:rgba(31,95,168,.05)}
/* 表内长散文列移出后的逐条注解：纵向承接，横向零成本 */
.peer-note{font-size:12.2px;color:#374151;line-height:1.75;padding:9px 0 9px 16px;
           border-left:2px solid var(--rule2);margin:9px 0}
.peer-note .pn-name{font-weight:700;color:var(--accent-deep);margin-right:7px}
.peer-note .pn-src{color:var(--muted);font-size:11.2px;margin-left:6px;white-space:nowrap}
.peer-note .pn-tag{font-size:10.5px;color:var(--muted);letter-spacing:.04em;margin-right:6px}
.table-note{font-size:11.5px;color:var(--muted);margin:6px 0 0;line-height:1.7}
/* 评分摘要清单：雷达旁替代宽表 */
.score-list{margin:4px 0 0}
.score-row{display:flex;align-items:baseline;gap:8px;padding:6px 0;border-bottom:1px solid var(--rule)}
.score-row:last-child{border-bottom:none}
.score-row .sr-name{flex:0 0 72px;font-size:12px;font-weight:600;color:var(--ink2)}
.score-row .sr-val{flex:0 0 34px;font-size:12.5px;font-weight:700;color:var(--ink);text-align:right}
.score-row .sr-coef{flex:0 0 52px;font-size:11.5px;text-align:right}
.score-row .sr-basis{flex:1;min-width:0;font-size:11.5px;color:#4B5563;line-height:1.6;overflow-wrap:anywhere}
.sr-up{color:var(--up)}.sr-down{color:var(--down)}.sr-flat{color:var(--muted)}
.kpi-value{overflow-wrap:anywhere}
.atext{overflow-wrap:anywhere}
.card{background:#F7F9FC;border:1px solid var(--rule);border-radius:3px;padding:14px 16px;margin:10px 0}
.card .t{font-size:13px;font-weight:700;color:var(--accent-deep);margin-bottom:4px}
.card .v{font-size:12.5px;color:#374151;line-height:1.7}
.risk-stats{font-size:12.5px;margin-bottom:6px}
.risk-stat{font-weight:600;margin-right:18px}
.rs-high{color:var(--up)}.rs-mid{color:var(--warn)}.rs-low{color:var(--down)}.rs-ok{color:var(--down)}
.risk-item{border-left:2px solid var(--rule2);padding:9px 0 9px 16px;margin:12px 0}
.risk-item .rt{font-weight:650;font-size:13.5px;color:var(--ink)}
.risk-item .rd{color:var(--ink2);font-size:12.5px;line-height:1.8;margin-top:2px}
.rtag{font-size:11px;font-weight:700;letter-spacing:.1em;margin-right:9px}
.pending-item{font-size:12.8px;color:var(--ink2);padding:6px 0 6px 18px;border-left:2px dashed var(--warn);margin:8px 0}
.footer{text-align:center;padding:30px 0 0;color:var(--muted);font-size:11px;letter-spacing:.04em;
        border-top:1px solid var(--rule);margin-top:36px;line-height:1.7}
@media print{
  .sidebar{display:none}.main{margin:0;padding:0}
  .sheet{border:none;box-shadow:none;max-width:none;padding:18px}
  .section{break-inside:avoid}
  body{background:#fff}
}
</style>
</head>
<body>
<nav class="sidebar">
  <div class="side-brand">
    <div class="co">__COMPANY__</div>
    <div class="code">__CODE__ · __STATUS__</div>
    <div class="ic">股权投资分析 · 祜·Care及Gangtise合作股权投研</div>
  </div>
  <div class="side-nav" id="sideNav">
    <a href="#sec1">01 IC 结论与概况</a>
    <a href="#sec2">02 企业基础画像</a>
    <a href="#sec3">03 行业深度分析</a>
    <a href="#sec4">04 可比公司对比</a>
    <a href="#sec5">05 估值测算</a>
    <a href="#sec6">06 风险提示与待核验</a>
    <a href="#sec7">07 投资结论</a>
  </div>
</nav>

<div class="main"><div class="sheet">

  <div class="masthead">
    <div>
      <div class="kicker">Equity Investment Analysis Report</div>
      <h1>__COMPANY__ 股权投资分析报告</h1>
      <div class="mast-meta"><b>__CODE__</b> ｜ 上市状态 <b>__STATUS__</b> ｜ 赛道 <b>__INDUSTRY__</b> ｜ 数据截止 __COLLECT_DATE__ ｜ 报告生成 __GEN_TIME__ ｜ 数据来源：祜·Care及Gangtise合作股权投研</div>
    </div>
  </div>
  <div class="ic-box">__IC_CONCLUSION__</div>
  <div class="rule-double"></div>

  <div class="kpi-grid">__KPI_CARDS__</div>

  <div class="section" id="sec1">
    <div class="kicker">Section 01 · Overview</div>
    <h2>IC 结论与概况</h2>
    __TXT_OVERVIEW__
  </div>

  <div class="section" id="sec2">
    <div class="kicker">Section 02 · Profile</div>
    <h2>企业基础画像</h2>
    <h3>基础信息核对（材料提炼 vs 独立旁证）</h3>
    <div class="tbl-wrap">__BASIC_TABLE__</div>
    <h3>工商与股权</h3>
    __TXT_EQUITY__
    <h3>财务标准化（CAS）</h3>
    __CAS_TABLE__
    __TXT_FINANCE__
    <h3>市场规模（TAM / SAM / SOM）</h3>
    __MARKET_SIZE__
    <h3>核心优势</h3>
    __ADVANTAGES__
  </div>

  <div class="section" id="sec3">
    <div class="kicker">Section 03 · Industry</div>
    <h2>行业深度分析</h2>
    __INDUSTRY_POINTS__
    <div id="c_industry" class="chart sm"></div>
    __TXT_INDUSTRY__
  </div>

  <div class="section" id="sec4">
    <div class="kicker">Section 04 · Comparable</div>
    <h2>可比公司对比</h2>
    <div class="chart-row">
      <div><div id="c_mcap" class="chart sm"></div></div>
      <div><div id="c_multiples" class="chart sm"></div></div>
    </div>
    <h3>可比公司明细</h3>
    <div class="tbl-wrap">__PEERS_TABLE__</div>
    __PEERS_NOTES__
    <h3>乘数统计（剔除极值后）</h3>
    <div class="tbl-wrap">__MULTIPLES_STATS__</div>
  </div>

  <div class="section" id="sec5">
    <div class="kicker">Section 05 · Valuation</div>
    <h2>估值测算</h2>
    <h3>三层估值结构</h3>
    <div class="tbl-wrap">__LAYERS_TABLE__</div>
    __LAYERS_NOTES__
    <div class="chart-row">
      <div><div id="c_radar" class="chart sm"></div></div>
      <div>__FIVEDIM_LIST__</div>
    </div>
    <h3>中性基准与建议可谈区间</h3>
    __VAL_RANGE__
    <h3>敏感度对照（合计系数 ± 滑动）</h3>
    <div class="tbl-wrap">__SENSITIVITY_TABLE__</div>
    <h3>交易结构（中性换算）</h3>
    __DEAL_STRUCT__
  </div>

  <div class="section" id="sec6">
    <div class="kicker">Section 06 · Risk</div>
    <h2>风险提示与待核验清单</h2>
    <div class="risk-stats">__RISK_STATS__</div>
    <div>__RISK_CARDS__</div>
    <h3>待补充核验清单</h3>
    __PENDING_LIST__
  </div>

  <div class="section" id="sec7">
    <div class="kicker">Section 07 · Conclusion</div>
    <h2>投资结论</h2>
    __TXT_CONCLUSION__
  </div>

  <div class="footer">__FOOTER__</div>
</div></div>

<script>
var D = __DATA__;
var PAL = ['#1F5FA8','#2E8B57','#B0820E','#9B59B6','#B23A33','#0E8FA0','#C77D3A'];
var INK = '#1F2937', INK2 = '#4B5563', MUTED = '#8A94A6';
var RULE = '#E7ECF3', RULE2 = '#C7D0DE', PAPER = '#FBFCFE';
var UP = '#B23A33', DOWN = '#2E8B57', WARN = '#B0820E';
var CHARTS = [];
var FONT = '"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif';

function mk(id, opt){
  var el = document.getElementById(id);
  if(!el) return null;
  var c = echarts.init(el);
  var base = {
    color: PAL,
    textStyle: {fontFamily: FONT},
    tooltip: {trigger:'axis', backgroundColor:'rgba(22,27,37,.95)', borderWidth:0,
              textStyle:{color:'#EEF2F8', fontSize:12},
              axisPointer:{type:'shadow', shadowStyle:{color:'rgba(31,95,168,.06)'}}},
    legend: {top:0, left:'center', icon:'circle', itemWidth:8, itemHeight:8,
             itemGap:16, textStyle:{color:INK2, fontSize:11.5}},
    grid: {left:8, right:16, top:42, bottom:8, containLabel:true},
    toolbox: {right:0, top:0, feature:{saveAsImage:{title:'保存图片', pixelRatio:2}},
              iconStyle:{borderColor:RULE2}}
  };
  // 横向条图（市值）共享一套坐标轴约定
  if(opt._horizontal){
    var g = {left:8, right:24, top:30, bottom:8, containLabel:true};
    opt.grid = g;
    delete opt._horizontal;
  }
  c.setOption(Object.assign(base, opt));
  CHARTS.push(c);
  return c;
}
function xa(data, extra){ return Object.assign({type:'category', data:data, axisTick:{show:false},
    axisLine:{lineStyle:{color:RULE2}}, axisLabel:{color:MUTED, fontSize:11}}, extra||{}); }
function ya(name, fmt, extra){ var y = {type:'value', name:name, nameTextStyle:{color:MUTED, fontSize:10.5},
    axisLabel:{color:MUTED, fontSize:11}, splitLine:{lineStyle:{color:RULE}}};
  if(fmt) y.axisLabel.formatter = fmt; return Object.assign(y, extra||{}); }
function bar(name, data, extra){ return Object.assign({name:name, type:'bar', data:data, barMaxWidth:22,
    itemStyle:{borderRadius:[3,3,0,0]}}, extra||{}); }
function pctFmt(p){ return p[0].name + p.map(function(x){
    return '<br>' + x.marker + x.seriesName + ': ' + (x.value==null?'—':x.value); }).join(''); }
function topLabel(arr, suffix){ return {show:true, position:'top', fontSize:10.5, color:INK2,
    formatter:function(p){var v = arr[p.dataIndex]; return v==null ? '' : v + (suffix||'');}}; }

// 04a 可比市值（亿元 · 横向条）
if (D.mcap.length){ mk('c_mcap', { _horizontal:true,
  tooltip:{trigger:'item', formatter:'{b}<br>市值 {c} 亿元', backgroundColor:'rgba(22,27,37,.95)', textStyle:{color:'#EEF2F8'}},
  legend:{show:false},
  xAxis: ya('亿元'),
  yAxis: xa(D.mcap.map(function(x){return x.name;}), {axisLabel:{color:INK2, fontSize:11}}),
  series:[{type:'bar', data:D.mcap.map(function(x){return x.value;}), barMaxWidth:18,
    itemStyle:{color:function(p){return p.dataIndex===D.mcap.length-1 ? '#1F5FA8' : '#9DB8D6';},
      borderRadius:[0,3,3,0]},
    label:{show:true, position:'right', color:MUTED, fontSize:10.5, formatter:'{c} 亿'}}]
}); }

// 04b 可比乘数（PE / PS · 单轴，倍数同级）
if (D.peersMetrics.pe.length){ mk('c_multiples', {
  tooltip:{trigger:'axis', formatter:pctFmt, backgroundColor:'rgba(22,27,37,.95)', textStyle:{color:'#EEF2F8'}},
  legend:{data:['市盈率PE(TTM)','市销率PS(TTM)']},
  xAxis: xa(D.peersMetrics.names),
  yAxis: ya('倍'),
  series: [ bar('市盈率PE(TTM)', D.peersMetrics.pe, {itemStyle:{color:'#1F5FA8', borderRadius:[3,3,0,0]}}),
            bar('市销率PS(TTM)', D.peersMetrics.ps, {itemStyle:{color:'#C77D3A', borderRadius:[3,3,0,0]}}) ]
}); }

// 03 行业指标（可选：规模趋势条）
if (D.industryMetrics.length){ mk('c_industry', {
  tooltip:{trigger:'axis', backgroundColor:'rgba(22,27,37,.95)', textStyle:{color:'#EEF2F8'}},
  legend:{show:false},
  xAxis: xa(D.industryMetrics.map(function(x){return x.name;})),
  yAxis: ya(D.industryUnit || ''),
  series: [ bar('指标', D.industryMetrics.map(function(x){return x.value;}),
             {itemStyle:{color:'#2E8B57', borderRadius:[3,3,0,0]},
              label: topLabel(D.industryMetrics.map(function(x){return x.value;}), '')}) ]
}); }

// 05 五维雷达（0~5 分）
if (D.radar.length){ mk('c_radar', {
  tooltip:{trigger:'item', backgroundColor:'rgba(22,27,37,.95)', textStyle:{color:'#EEF2F8'}},
  legend:{show:false},
  radar:{
    indicator: D.radar.map(function(s){return {name:s.name + '\\n' + s.value.toFixed(1), max:5};}),
    radius:'62%', splitNumber:5,
    axisName:{color:INK2, fontSize:11},
    splitArea:{areaStyle:{color:['#FBFCFE','#F3F7FC','#ECF2F9','#E4ECF5','#DCE6F1']}},
    splitLine:{lineStyle:{color:RULE2}}, axisLine:{lineStyle:{color:RULE2}}
  },
  series:[{type:'radar',
    data:[{value:D.radar.map(function(s){return s.value;}), name:'五维评分'}],
    areaStyle:{color:'rgba(31,95,168,.16)'},
    lineStyle:{color:PAL[0], width:2}, itemStyle:{color:PAL[0]}}]
}); }

window.addEventListener('resize', function(){ CHARTS.forEach(function(c){ c.resize(); }); });
</script>
</body>
</html>"""


# ============================================================
#  数据载荷构造
# ============================================================

def _get(d, *path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def build_payload(data):
    """把归一后的输入 JSON 整理成 JS 数据载荷 D。"""
    # --- 可比市值条图（横向）---
    mcap = []
    for p in data.get("comparable", {}).get("peers", []) or []:
        v = p.get("market_cap")
        if isinstance(v, (int, float)):
            mcap.append({"name": str(p.get("name", "")), "value": round(float(v), 2)})
    tm = _get(data, "comparable", "target_metrics") or {}
    if isinstance(tm.get("market_cap"), (int, float)):
        mcap.append({"name": "标的(本项目)", "value": round(float(tm["market_cap"]), 2)})

    # --- 可比乘数（PE / PS）---
    names, pe_l, ps_l = [], [], []
    for p in data.get("comparable", {}).get("peers", []) or []:
        nm = str(p.get("name", ""))
        pe = p.get("pe")
        ps = p.get("ps")
        if isinstance(pe, (int, float)) or isinstance(ps, (int, float)):
            names.append(nm)
            pe_l.append(round(float(pe), 2) if isinstance(pe, (int, float)) else None)
            ps_l.append(round(float(ps), 2) if isinstance(ps, (int, float)) else None)

    # --- 行业指标条图（可选）---
    ind_metrics = []
    for m in data.get("industry_analysis", {}).get("metrics", []) or []:
        v = m.get("value")
        if isinstance(v, (int, float)):
            ind_metrics.append({"name": str(m.get("name", "")), "value": round(float(v), 2)})

    # --- 五维雷达 ---
    radar = []
    for d in _get(data, "valuation", "five_dims") or []:
        s = d.get("score")
        if isinstance(s, (int, float)):
            radar.append({"name": str(d.get("name", "")), "value": float(s)})

    return {
        "company": data.get("company", ""),
        "mcap": mcap,
        "peersMetrics": {"names": names, "pe": pe_l, "ps": ps_l},
        "industryMetrics": ind_metrics,
        "industryUnit": data.get("industry_analysis", {}).get("unit", ""),
        "radar": radar,
    }


def build_kpi(data):
    """构造 KPI 卡片 HTML（动态：缺值显示 —）。"""
    val = data.get("valuation", {}) or {}
    comp = data.get("comparable", {}) or {}
    risks = data.get("risks", []) or []
    hc = sum(1 for r in risks if r.get("level") == "高")
    mc = sum(1 for r in risks if r.get("level") == "中")
    lc = sum(1 for r in risks if r.get("level") == "低")

    coef_sum = None
    for d in val.get("five_dims", []) or []:
        c = d.get("coef")
        if isinstance(c, (int, float)):
            coef_sum = (coef_sum or 0) + float(c)

    rng = val.get("range")
    rng_txt = (f"{_f(rng[0])} ~ {_f(rng[1])} 亿" if isinstance(rng, list) and len(rng) == 2
               else "—") if rng is not None else "—"

    cards = [
        ("中性基准估值", _f(val.get("neutral_base")) + " 亿", "投前 · 单一结论档"),
        ("建议可谈区间", rng_txt, f"半宽 ±{_pct(val.get('band_half'))}"),
        ("五维合计系数", (f"{coef_sum*100:+.0f}%" if coef_sum is not None else "—"), "风险校准后"),
        ("可比标的", str(len(comp.get("peers", []) or [])), "市场参照 / 上限"),
        ("风险信号", f"高{hc} 中{mc} 低{lc}", "待核验另计" if (data.get("pending")) else "—"),
        ("行业增速", _pct(_get(data, "industry_analysis", "growth")), "近3年 CAGR 口径"),
    ]
    out = ""
    for label, value, sub in cards:
        out += (f'<div class="kpi"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div>'
                f'<div class="kpi-sub">{sub}</div></div>')
    return out


# 允许的列类型（值必须与样式表里的 .num / .txt 真实对应）。
# 声明成模块级常量有两个作用：① 列类型写错（如 "tx"）在生成期即报错，
# 不会静默产出一列没有样式的单元格；② 模板外的静态检查以这份清单为准，
# 机械断言「用到的 class 都有 CSS 规则」——模板外看不到拼接结果，只能以清单为准。
COL_KINDS = ("num", "txt")

# 模板里以 `class="... {var}"` 形式拼接的动态 class 取值。
# 必须显式登记在这里：若改了模板里的动态 class，请同步更新本清单，
# 否则新取值可能漏掉对应的 CSS 规则——模板外看不到拼接结果，只能以这份清单为准。
DYNAMIC_CLASSES = ("sr-up", "sr-down", "sr-flat")


def _col_class(k):
    """列类型 → class 名（字面量内联，便于静态检查）。"""
    if k not in COL_KINDS:
        raise ValueError(f"未知列类型 {k!r}，允许：{COL_KINDS}")
    return "num" if k == "num" else "txt"


def _table(headers, rows, kinds=None):
    """通用表格。

    headers: list[str]；rows: list[list[str]]；kinds: list[str]（长度须同 headers）。

    kinds 逐列声明单元格的**换行行为**，是这份表格布局契约的核心：
      - "num"（默认）：数字/短标签列 → nowrap，保持小数点严格对齐、不被折行破坏；
      - "txt"        ：散文列        → 允许折行 + overflow-wrap:anywhere。

    为什么必须逐列声明：散文列若套用数字列的 nowrap，任何一列的长文本都会
    把整表撑到超出容器、把整页顶出视口。
    默认 "num" 是有意的：漏标只让某列偏窄（可接受），不会让整页横溢出（不可接受）。
    """
    if kinds is None:
        kinds = ["num"] * len(headers)
    if len(kinds) != len(headers):
        raise ValueError(
            f"_table 列类型数（{len(kinds)}）必须与表头数（{len(headers)}）一致")
    th = "".join(f'<th class="{_col_class(k)}">{h}</th>'
                 for h, k in zip(headers, kinds))
    body = ""
    for r in rows:
        tds = ""
        for i, c in enumerate(r):
            # 列类型缺失则按 "num" 兜底（与表头对齐）；只有 "txt" 列做行内排版转换，
            # 避免把纯数字列里偶发的 `**`/`【】` 误当标记（数字列也几乎不会含标记）。
            # 注：红标不在这里处理，入口 `_apply_redmark` 已整树解析。
            kind = kinds[i] if i < len(kinds) else "num"
            content = _inline_md(c) if kind == "txt" else c
            tds += f'<td class="{_col_class(kind)}">{content}</td>'
        body += f"<tr>{tds}</tr>"
    return f'<table class="data-table"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'


def build_sections(data):
    """返回各 __TOKEN__ 的替换文本。"""
    rep = {}
    prof = data.get("profile", {}) or {}
    comp = data.get("comparable", {}) or {}
    val = data.get("valuation", {}) or {}
    ind = data.get("industry_analysis", {}) or {}
    risks = data.get("risks", []) or []

    # IC + 概况
    rep["__IC_CONCLUSION__"] = data.get("ic_conclusion", "（未提供一句话 IC 结论）")
    rep["__TXT_OVERVIEW__"] = md_to_html(data.get("overview", ""))

    # 基础信息四列表格
    basic = prof.get("basic_info", []) or []
    if basic:
        rows = [[str(r[0]), str(r[1]), str(r[2]), str(r[3])] for r in basic]
        rep["__BASIC_TABLE__"] = _table(
            ["基础信息项", "业务材料提炼", "独立提炼 / 旁证", "差异"], rows,
            kinds=["txt", "txt", "txt", "txt"])
    else:
        rep["__BASIC_TABLE__"] = '<p class="atext">未提供基础信息四列表格。</p>'

    # 工商股权
    rep["__TXT_EQUITY__"] = md_to_html(prof.get("equity", "（未提供股权穿透信息；无可靠来源时应在风险处标「待补充核验」）"))

    # CAS 标准化表
    cas = prof.get("cas_standardization", []) or []
    if cas:
        rows = [[str(r[0]), str(r[1]), str(r[2]), str(r[3])] for r in cas]
        rep["__CAS_TABLE__"] = _table(
            ["科目 / 调整项", "原始报表", "标准化后", "调整原因"], rows,
            kinds=["num", "txt", "txt", "txt"])
    else:
        rep["__CAS_TABLE__"] = '<p class="atext">无 CAS 标准化调整项（已上市标的直接采用公告口径；未上市且无规范报表时此处应呈【原始 VS 标准化】对比）。</p>'

    rep["__TXT_FINANCE__"] = md_to_html(prof.get("finance_note", ""))

    # 市场规模 TAM/SAM/SOM
    ms = prof.get("market_size", {}) or {}
    if ms:
        rep["__MARKET_SIZE__"] = (
            '<div class="card"><div class="t">TAM 总量市场</div><div class="v">'
            + (ms.get("tam") or "—") + '</div></div>'
            '<div class="card"><div class="t">SAM 可服务市场</div><div class="v">'
            + (ms.get("sam") or "—") + '</div></div>'
            '<div class="card"><div class="t">SOM 可获取份额</div><div class="v">'
            + (ms.get("som") or "—") + '</div></div>')
    else:
        rep["__MARKET_SIZE__"] = '<p class="atext">未提供 TAM/SAM/SOM 三段市场规模。</p>'

    # 核心优势
    adv = prof.get("advantages", []) or []
    if adv:
        rep["__ADVANTAGES__"] = "".join(
            f'<div class="card"><div class="t">优势 {i+1}</div><div class="v">{md_to_html(a)}</div></div>'
            for i, a in enumerate(adv))
    else:
        rep["__ADVANTAGES__"] = '<p class="atext">未提炼核心优势要点。</p>'

    # 行业八点
    pts = ind.get("points", []) or []
    if pts:
        rep["__INDUSTRY_POINTS__"] = "".join(
            f'<div class="card"><div class="t">{p.get("title", "")}</div>'
            f'<div class="v">{md_to_html(p.get("text", ""))}</div></div>'
            for p in pts)
    else:
        rep["__INDUSTRY_POINTS__"] = '<p class="atext">未提供行业八点分析。</p>'
    rep["__TXT_INDUSTRY__"] = md_to_html(ind.get("note", ""))

    # 可比明细：数值核心留在表内，散文（与标的差异 / 来源）移到表下逐条注解。
    #
    # 为什么拆：横向是稀缺资源（一屏宽度有限），纵向是免费的——把散文塞进横向网格，
    # 结果就是表格无限变宽并把整页顶出视口。移出后表内只剩纯数值列，
    # 差异与来源按「可比对象」逐条落在下方注解里，信息一条不少、且更易读。
    peers = comp.get("peers", []) or []
    if peers:
        rows = []
        for p in peers:
            rows.append([
                str(p.get("name", "")),
                str(p.get("type", "—")),
                _f(p.get("pe")),
                _f(p.get("pb")),
                _f(p.get("ps")),
                _f(p.get("market_cap")),
                _f(p.get("roe"), 1),
                _f(p.get("revenue_growth"), 1),
                _f(p.get("gross_margin"), 1),
                str(p.get("match", "—")),
            ])
        rep["__PEERS_TABLE__"] = _table(
            ["可比对象", "类型", "PE", "PB", "PS", "市值(亿)", "ROE%", "营收增速%", "毛利率%", "匹配度"],
            rows,
            kinds=["num", "num", "num", "num", "num", "num", "num", "num", "num", "num"])

        notes = []
        for p in peers:
            diff = str(p.get("diff", "") or "").strip()
            src = str(p.get("source", "") or "").strip()
            if not diff and not src:
                continue
            src_html = (f'<span class="pn-src">[{src}]</span>'
                        if src and src != "—" else "")
            notes.append(
                f'<div class="peer-note"><span class="pn-name">{p.get("name", "")}</span>'
                f'{md_to_html(diff) if diff and diff != "—" else "—"}{src_html}</div>')
        rep["__PEERS_NOTES__"] = (
            '<h3>可比对象差异与出处</h3>' + "".join(notes) if notes
            else '<p class="atext">未提供可比对象的差异说明与出处。</p>')
    else:
        rep["__PEERS_TABLE__"] = '<p class="atext">未提供可比公司明细（一级/二级均不足时应在正文说明 VC 法兜底）。</p>'
        rep["__PEERS_NOTES__"] = ""

    # 乘数统计
    stats = comp.get("multiples_stats", []) or []
    if stats:
        rows = [[str(s.get("metric", "")), _f(s.get("mean")), _f(s.get("median")),
                 _f(s.get("q1")), _f(s.get("q3"))] for s in stats]
        rep["__MULTIPLES_STATS__"] = _table(
            ["乘数", "均值", "中位数", "下四分位", "上四分位"], rows,
            kinds=["txt", "num", "num", "num", "num"])
    else:
        rep["__MULTIPLES_STATS__"] = '<p class="atext">未提供乘数统计（剔除 ±3×IQR 极值后的四组口径）。</p>'

    # 三层估值表
    layers = val.get("layers", []) or []
    # 三层估值：数值核心留表，「方法/乘数」与「来源」这两段散文移到表下注解。
    # 横向宽度有限，散文列会把整表撑宽——同样移到表下逐条注解，信息不减。
    if layers:
        rows = [[str(l.get("layer", "")), _f(l.get("base")),
                 _f(l.get("applied")), str(l.get("result", ""))]
                for l in layers]
        rep["__LAYERS_TABLE__"] = _table(
            ["估值层级", "基准倍数", "标的对应指标", "结果"], rows,
            kinds=["txt", "num", "num", "num"])

        lnotes = []
        for l in layers:
            method = str(l.get("method", "") or "").strip()
            src = str(l.get("source", "") or "").strip()
            if not method and not src:
                continue
            src_html = f'<span class="pn-src">[{src}]</span>' if src and src != "—" else ""
            lnotes.append(
                f'<div class="peer-note"><span class="pn-name">{l.get("layer", "")}</span>'
                f'{md_to_html(method) if method and method != "—" else "—"}{src_html}</div>')
        rep["__LAYERS_NOTES__"] = (
            '<div class="table-note">方法 / 乘数与出处：</div>' + "".join(lnotes)
            if lnotes else "")
    else:
        rep["__LAYERS_TABLE__"] = '<p class="atext">未提供三层估值结构。</p>'
        rep["__LAYERS_NOTES__"] = ""

    # 五维打分：用竖向评分清单而不是塞进半栏表格——名称/评分/系数固定宽，
    # 打分依据占剩余弹性宽度并自动折行，天然适配任何栏宽。
    fd = val.get("five_dims", []) or []
    if fd:
        rows = []
        for d in fd:
            coef = d.get("coef")
            if isinstance(coef, (int, float)):
                cls = "sr-up" if coef > 0 else ("sr-down" if coef < 0 else "sr-flat")
                coef_txt = f"{float(coef)*100:+.0f}%"
            else:
                cls, coef_txt = "sr-flat", "—"
            ev = str(d.get("evidence", "—") or "—")
            rows.append(
                f'<div class="score-row">'
                f'<span class="sr-name">{d.get("name", "")}</span>'
                f'<span class="sr-val">{_f(d.get("score"), 1)}</span>'
                f'<span class="sr-coef {cls}">{coef_txt}</span>'
                f'<span class="sr-basis">{md_to_html(str(d.get("basis", ""))) or "—"}'
                f'<span class="pn-src">证据强度 {ev}</span></span></div>')
        rep["__FIVEDIM_LIST__"] = ('<div class="table-note">维度 / 评分 / 系数 / 打分依据</div>'
                                   '<div class="score-list">' + "".join(rows) + '</div>')
    else:
        rep["__FIVEDIM_LIST__"] = '<p class="atext">未提供五维打分。</p>'

    # 中性基准与可谈区间
    rng = val.get("range")
    nb = val.get("neutral_base")
    rep["__VAL_RANGE__"] = (
        '<div class="card"><div class="t">中性基准（唯一结论档）</div>'
        f'<div class="v">投前估值 ≈ <b>{_f(nb)} 亿元</b>；建议可谈区间 '
        f'<b>{_f(rng[0]) if isinstance(rng, list) and len(rng)==2 else "—"} ~ '
        f'{_f(rng[1]) if isinstance(rng, list) and len(rng)==2 else "—"} 亿元</b>'
        f'（半宽 ±{_pct(val.get("band_half"))}）。</div></div>'
        if nb is not None else
        '<p class="atext">未提供中性基准估值。</p>')

    # 敏感度对照
    sens = val.get("sensitivity", []) or []
    if sens:
        rows = [[str(s.get("scenario", "")),
                 (f"{float(s['coef'])*100:+.0f}%" if isinstance(s.get("coef"), (int, float)) else "—"),
                 _f(s.get("pre")),
                 (f"{_f(s.get('range_low'))} ~ {_f(s.get('range_high'))}"
                  if s.get("range_low") is not None else "—")]
                for s in sens]
        rep["__SENSITIVITY_TABLE__"] = _table(
            ["情景", "合计系数", "对应投前(亿)", "对应区间(亿)"], rows,
            kinds=["txt", "num", "num", "num"])
    else:
        rep["__SENSITIVITY_TABLE__"] = '<p class="atext">未提供敏感度对照（合计系数 ± 滑动三档）。</p>'

    # 交易结构
    deal = val.get("deal_structure", {}) or {}
    if deal:
        rep["__DEAL_STRUCT__"] = (
            '<div class="card"><div class="v">'
            f'投前 <b>{_f(deal.get("pre"))} 亿</b> ＋ 本轮拟融 <b>{_f(deal.get("round"))} 亿</b>'
            f' ＝ 投后 <b>{_f(deal.get("post"))} 亿</b>；出让比例 ≈ '
            f'<b>{_f(deal.get("stake"), 1)}%</b>。'
            f'{(" " + deal.get("note", "")) if deal.get("note") else ""}</div></div>')
    else:
        rep["__DEAL_STRUCT__"] = '<p class="atext">未提供交易结构换算。</p>'

    # 风险
    lv_color = {"高": "#B23A33", "中": "#B0820E", "低": "#2E8B57"}
    risk_cards = ""
    for r in risks:
        color = lv_color.get(r.get("level"), "#8A94A6")
        risk_cards += (f'<div class="risk-item" style="border-left-color:{color}">'
                       f'<div class="rt"><span class="rtag" style="color:{color}">{r.get("level","")}风险</span>'
                       f'{r.get("title","")}</div><div class="rd">{r.get("desc","")}</div></div>')
    if not risk_cards:
        risk_cards = ('<div class="risk-item" style="border-left-color:#2E8B57">'
                      '<div class="rt"><span class="rtag" style="color:#2E8B57">通过</span>'
                      '未触发量化风险信号</div>'
                      '<div class="rd">仍建议完成工商/司法/实地核查程序。</div></div>')
    hc = sum(1 for r in risks if r.get("level") == "高")
    mc = sum(1 for r in risks if r.get("level") == "中")
    lc = sum(1 for r in risks if r.get("level") == "低")
    risk_stats = ""
    if hc: risk_stats += f'<span class="risk-stat rs-high">高风险 {hc} 项</span>'
    if mc: risk_stats += f'<span class="risk-stat rs-mid">中风险 {mc} 项</span>'
    if lc: risk_stats += f'<span class="risk-stat rs-low">低风险 {lc} 项</span>'
    if not risks: risk_stats = '<span class="risk-stat rs-ok">扫描通过 · 0 项风险信号</span>'
    rep["__RISK_STATS__"] = risk_stats
    rep["__RISK_CARDS__"] = risk_cards

    # 待核验清单
    pending = data.get("pending", []) or []
    if pending:
        rep["__PENDING_LIST__"] = "".join(
            f'<div class="pending-item">{p}</div>' for p in pending)
    else:
        rep["__PENDING_LIST__"] = '<p class="atext">无待补充核验项。</p>'

    # 结论
    rep["__TXT_CONCLUSION__"] = md_to_html(data.get("conclusion", "（未提供投资结论）"))

    return rep


# ============================================================
#  HTML 报告生成
# ============================================================

def generate_html_report(data, output_path, echarts_js=""):
    # 红标唯一解析点：整棵树过一遍，之后的渲染层再也看不到 `[[红]]`。
    # 图表数据仍用**原始树**（见下），避免 HTML 片段被 json.dumps 塞进 <script>
    # 污染图表标签——图表用的是纯数值与公司/维度名，本就不该带红标。
    rendered = _apply_redmark(data)

    company = rendered.get("company", "标的")
    collect_date = rendered.get("collect_date", datetime.now().strftime("%Y-%m-%d"))

    payload = build_payload(data)
    kpi_html = build_kpi(rendered)
    sec = build_sections(rendered)

    replacements = {
        "__TITLE__": f"{company} 股权投资分析",
        "__COMPANY__": company,
        "__CODE__": data.get("security_code") or "—",
        "__STATUS__": data.get("status_note") or ("已上市" if data.get("listed") else "未上市 · BP 口径"),
        "__INDUSTRY__": data.get("industry") or "—",
        "__COLLECT_DATE__": str(collect_date),
        "__GEN_TIME__": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "__KPI_CARDS__": kpi_html,
        "__FOOTER__": ("本报告由祜·Care 与 Gangtise 合作开发，属测试技能，仅供股权投研复盘与尽调参考。"
                       "本报告不构成任何投资建议，据此决策风险自担。如有优化建议或业务咨询，"
                       "请联系 13386019198。"),
        "__DATA__": json.dumps(payload, ensure_ascii=False),
        # 内联图表引擎：必须**最后**一次替换。
        "__ECHARTS_LIB__": echarts_js,
    }
    replacements.update(sec)

    html = HTML_TEMPLATE
    for token, value in replacements.items():
        html = html.replace(token, value)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="生成股权投资分析报告（离线自包含 HTML）")
    parser.add_argument("--data", required=True, help="报告输入 JSON 文件路径（经 assemble_data.py 校验归一）")
    parser.add_argument("--output-dir", default="", help="输出目录；默认 {工作目录}/company_inv_pe")
    parser.add_argument("--company", default="", help="公司名称（覆盖 JSON 中的 company）")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    company = args.company or data.get("company", "标的")

    # 图表引擎先加载：缺失即失败，避免产出"图表静默空白"的报告。
    try:
        echarts_js = load_echarts_js()
    except AssetError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    # 诊断信息走 stderr，stdout 只留产物绝对路径（与 assemble_data.py 一致）。
    fd = (data.get("valuation", {}) or {}).get("five_dims", []) or []
    print(f"报告主体：{company}（{data.get('status_note') or ('已上市' if data.get('listed') else '未上市')}）",
          file=sys.stderr)
    print(f"五维打分：{len(fd)} 项 | 可比标的：{len((data.get('comparable', {}) or {}).get('peers', []) or [])} 家"
          f" | 风险：{len(data.get('risks', []) or [])} 项", file=sys.stderr)

    out_dir = os.path.abspath(args.output_dir or default_skill_output_dir())
    os.makedirs(out_dir, exist_ok=True)

    html_path = os.path.join(out_dir, f"{company}_股权投资分析.html")
    generate_html_report(data, html_path, echarts_js)
    print(html_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

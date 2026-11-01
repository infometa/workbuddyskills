#!/usr/bin/env python3
"""yj-fin-pe-bp-review 报告生成器（v1.0）

读取本技能组装的报告输入 JSON，生成**单文件自包含 HTML**：头部结论 + KPI 概览 +
分模块的分析、表格、要点卡片、图表、风险信号与待补充核验清单，末段落固定声明。

设计要点：
  - 图表引擎 ECharts 从同目录 assets/echarts.min.js 读取并**内联**进 HTML；
    运行时零外部请求、客户端离线也能正常渲染。资产缺失/不可读/含 `</script`
    字面量时**非零退出**并指名字符路径，绝不产出图表静默空白的报告。
  - __ECHARTS_LIB__ 占位标记**最后**一次替换（约 1MB 源码不会被后续 token 扫到）。
  - 内容按「区块（block）」组织：章节由下方 SECTIONS 定义骨架，正文取自输入 JSON
    的 `sections[id].blocks`；block 类型见 render_block 的 dispatch。
  - stdout 只打产物绝对路径；诊断信息走 stderr。

Usage:
    python3 generate_report.py --data /path/to/{名称}_pe_bp_review_input.json
    python3 generate_report.py --data /path/to/input.json --output-dir /path/to/output/
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

# ==== SKILL CONFIG（生成器写入，勿手改：由 scripts/gen_skill_renderers.py 生成） ====
SKILL_NAME = "yj-fin-pe-bp-review"
DOC_KICKER = "Business Plan Review"
SIDEBAR_IC = "BP 评审 · 祜·Care及Gangtise合作股权投研"
TITLE_SUFFIX = "商业计划书评审报告"
FILE_SUFFIX = "BP评审"
SUBDIR = "pe_bp_review"
FOOTER_TEXT = "本报告由祜·Care 与 Gangtise 合作开发，属测试技能，仅供BP 评审复盘与参考。本报告不构成任何投资建议，据此决策风险自担。如有优化建议或业务咨询，请联系 13386019198。"
# 侧栏与章节骨架：(锚点 id, 导航文字, 小节英文 kicker, 中文标题)
SECTIONS = (
    ("sec1", "01 总体判断", "Section 01 · Verdict", "总体判断与项目画像"),
    ("sec2", "02 六维度评分卡", "Section 02 · Scorecard", "六维度评分卡"),
    ("sec3", "03 行业适配", "Section 03 · Industry Fit", "行业适配分析"),
    ("sec4", "04 关键问题清单", "Section 04 · Key Questions", "关键问题清单"),
    ("sec5", "05 投资人视角推演", "Section 05 · Investor View", "投资人视角推演"),
    ("sec6", "06 行动清单与重写建议", "Section 06 · Actions", "行动清单与重写建议"),
)
# ==== END SKILL CONFIG ====


class AssetError(RuntimeError):
    """内联第三方资源缺失或不可用。"""


def load_echarts_js():
    """读取本地 ECharts 资产，供内联进报告 HTML。

    报告必须自包含，故资产缺失/不可读时**直接失败**（由 main 转成非零退出），
    绝不静默降级成"图表空白"。路径相对本脚本自身解析，与 cwd 无关。
    """
    try:
        with open(ECHARTS_ASSET_PATH, "r", encoding="utf-8") as f:
            js = f.read()
    except OSError as e:
        raise AssetError(
            f"内联图表引擎缺失或不可读：{ECHARTS_ASSET_PATH}（{e}）。"
            f"该文件随技能包分发，请从技能包补回后重试。") from e
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
        return str(v)


def _pct(v, suffix="%"):
    return _f(v, 1, suffix)


def _esc(v):
    """把任意值转成可安全嵌入 HTML 文本的字符串（不引入标记）。"""
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, float):
        return _f(v)
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


# ============================================================
#  红标（数据语义）—— 唯一解析点在数据**入口**
# ============================================================

RED_MARK_RE = re.compile(r"\[\[红\]\](.*?)\[\[/红\]\]", re.DOTALL)


def _parse_redmark(s):
    """字符串里的 [[红]]…[[/红]] → <span class="hl-red">…</span>。

    幂等：不含标记则原样返回；已解析过的内容再跑一次也不会重复包裹。
    """
    if not isinstance(s, str) or not s:
        return s
    return RED_MARK_RE.sub(r'<span class="hl-red">\1</span>', s)


def _apply_redmark(node):
    """递归整棵数据树解析红标——**红标的唯一解析点**（入口调用一次）。

    红标标记的是「差异 / 待补充核验」这类**数据语义**，不是某一处的排版效果。
    放在入口统一解析后，渲染层接触到的永远是已解析内容，新增任意输出路径都不会漏。
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

    只管**排版层**符号约定（【小标题】转 run-in 加粗、**粗体**、`行内代码`），
    供 md_to_html 的每段与 _table 的 txt 列共用。
    """
    if not t:
        return ""
    t = re.sub(r"【(.+?)】", r'<span class="hl">\1</span>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def md_to_html(t):
    """分析文本 → HTML：\\n\\n 分段，段内 \\n 转 <br>；逐段套用 _inline_md。"""
    if not t:
        return ""
    parts = []
    for p in str(t).split("\n\n"):
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
.kpi-value{font-family:var(--serif);font-size:21px;font-weight:700;color:var(--ink);margin-top:3px;letter-spacing:.3px;overflow-wrap:anywhere}
.kpi-sub{font-size:11px;color:var(--ink2);margin-top:2px}
.section{padding:38px 0 8px;border-top:1px solid var(--rule)}
.section:first-of-type{border-top:none}
.section h2{font-family:var(--serif);font-size:20px;font-weight:700;letter-spacing:1.2px;margin:6px 0 16px;scroll-margin-top:20px}
.section h3{font-size:13px;font-weight:600;color:var(--ink2);letter-spacing:.05em;margin:20px 0 6px}
.chart{width:100%;height:380px;margin:6px 0 2px}
.chart.sm{height:320px}
.chart-row{display:flex;gap:26px;flex-wrap:wrap;align-items:flex-start}
.chart-row>div{flex:1;min-width:min(360px,100%)}
.atext{font-size:13.6px;color:#374151;margin:10px 0;text-align:justify;overflow-wrap:anywhere}
.hl{font-weight:700;color:var(--accent-deep);margin-right:5px}
.hl-red{font-weight:700;color:var(--up)}
code{font-family:"SFMono-Regular",Consolas,monospace;font-size:12px;background:#EEF2F7;padding:1px 5px;border-radius:3px;color:#27496E}
.tbl-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}
.tbl-wrap::-webkit-scrollbar{height:6px}
.tbl-wrap::-webkit-scrollbar-thumb{background:var(--rule2);border-radius:3px}
.data-table{width:100%;border-collapse:collapse;margin:14px 0;font-size:12.5px}
.data-table th{font-size:11px;font-weight:600;letter-spacing:.05em;color:var(--ink2);
               padding:9px 10px;border-top:1.5px solid var(--ink);border-bottom:1px solid var(--rule2);
               text-align:right;background:none}
.data-table th:first-child{text-align:left}
.data-table td{padding:7px 10px;border-bottom:1px solid var(--rule);text-align:right;color:#374151}
.data-table td:first-child{text-align:left;color:var(--ink2)}
.data-table th.num,.data-table td.num{white-space:nowrap}
.data-table th.txt,.data-table td.txt{white-space:normal;overflow-wrap:anywhere;word-break:break-word;line-height:1.65}
.data-table tbody tr:last-child td{border-bottom:1px solid var(--rule2)}
.data-table tbody tr:hover{background:rgba(31,95,168,.05)}
.peer-note{font-size:12.2px;color:#374151;line-height:1.75;padding:9px 0 9px 16px;
           border-left:2px solid var(--rule2);margin:9px 0}
.peer-note .pn-name{font-weight:700;color:var(--accent-deep);margin-right:7px}
.peer-note .pn-src{color:var(--muted);font-size:11.2px;margin-left:6px;white-space:nowrap}
.peer-note .pn-tag{font-size:10.5px;color:var(--muted);letter-spacing:.04em;margin-right:6px}
.table-note{font-size:11.5px;color:var(--muted);margin:6px 0 0;line-height:1.7}
.score-list{margin:4px 0 0}
.score-row{display:flex;align-items:baseline;gap:8px;padding:6px 0;border-bottom:1px solid var(--rule)}
.score-row:last-child{border-bottom:none}
.score-row .sr-name{flex:0 0 84px;font-size:12px;font-weight:600;color:var(--ink2)}
.score-row .sr-val{flex:0 0 40px;font-size:12.5px;font-weight:700;color:var(--ink);text-align:right}
.score-row .sr-coef{flex:0 0 56px;font-size:11.5px;text-align:right}
.score-row .sr-basis{flex:1;min-width:0;font-size:11.5px;color:#4B5563;line-height:1.6;overflow-wrap:anywhere}
.sr-up{color:var(--up)}.sr-down{color:var(--down)}.sr-flat{color:var(--muted)}
.card{background:#F7F9FC;border:1px solid var(--rule);border-radius:3px;padding:14px 16px;margin:10px 0}
.card .t{font-size:13px;font-weight:700;color:var(--accent-deep);margin-bottom:4px}
.card .v{font-size:12.5px;color:#374151;line-height:1.7}
.kv-table{width:100%;border-collapse:collapse;margin:10px 0;font-size:12.8px}
.kv-table td{padding:8px 12px;border-bottom:1px solid var(--rule);vertical-align:top}
.kv-table td.k{width:180px;color:var(--ink2);font-weight:600;background:#F7F9FC}
.kv-table td.v{color:#374151}
.badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.06em;
       padding:1px 9px;border-radius:10px;margin-right:6px}
.badge-ok{color:#1E6B44;background:#E4F2EA}
.badge-warn{color:#8A6608;background:#F7F0DC}
.badge-bad{color:#8E2A24;background:#F7E4E2}
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
    <div class="ic">__SIDEBAR_IC__</div>
  </div>
  <div class="side-nav" id="sideNav">
    __NAV__
  </div>
</nav>

<div class="main"><div class="sheet">

  <div class="masthead">
    <div>
      <div class="kicker">__DOC_KICKER__</div>
      <h1>__COMPANY__ __TITLE_SUFFIX__</h1>
      <div class="mast-meta">__META_LINE__</div>
    </div>
  </div>
  <div class="ic-box">__IC_CONCLUSION__</div>
  <div class="rule-double"></div>

  __KPI_GRID__

  __SECTIONS_HTML__

  <div class="footer">__FOOTER__</div>
</div></div>

<script>
var D = __DATA__;
var PAL = ['#1F5FA8','#2E8B57','#B0820E','#9B59B6','#B23A33','#0E8FA0','#C77D3A'];
var INK = '#1F2937', INK2 = '#4B5563', MUTED = '#8A94A6';
var RULE = '#E7ECF3', RULE2 = '#C7D0DE';
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
  if(opt._horizontal){
    opt.grid = {left:8, right:24, top:30, bottom:8, containLabel:true};
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
function topLabel(arr, suffix){ return {show:true, position:'top', fontSize:10.5, color:INK2,
    formatter:function(p){var v = arr[p.dataIndex]; return v==null ? '' : v + (suffix||'');}}; }
var TT = {backgroundColor:'rgba(22,27,37,.95)', borderWidth:0, textStyle:{color:'#EEF2F8', fontSize:12}};

function drawChart(spec){
  var id = spec.id, kind = spec.kind || 'bar';
  var cats = spec.categories || [];
  var series = spec.series || [];
  if(kind === 'bar' || kind === 'hbar'){
    var horiz = (kind === 'hbar');
    var names = series.map(function(s){return s.name;});
    var opt = { tooltip: Object.assign({trigger:'axis'}, TT), legend:{data:names}, _horizontal:horiz };
    opt.xAxis = horiz ? ya(spec.unit || '') : xa(cats);
    opt.yAxis = horiz ? xa(cats, {axisLabel:{color:INK2, fontSize:11}}) : ya(spec.unit || '');
    opt.series = series.map(function(s){
      var it = {name:s.name, type:'bar', data:s.data, barMaxWidth:horiz?18:22,
                itemStyle:{borderRadius:horiz?[0,3,3,0]:[3,3,0,0]}};
      if(s.color) it.itemStyle.color = s.color;
      if(s.label) it.label = {show:true, position:horiz?'right':'top', color:MUTED, fontSize:10.5,
                              formatter:'{c}' + (spec.unit||'')};
      return it;
    });
    mk(id, opt);
  } else if(kind === 'line'){
    mk(id, {
      tooltip: Object.assign({trigger:'axis'}, TT), legend:{data:series.map(function(s){return s.name;})},
      xAxis: xa(cats), yAxis: ya(spec.unit || ''),
      series: series.map(function(s){
        return {name:s.name, type:'line', data:s.data, smooth:true, symbolSize:6,
                lineStyle:{width:2}, areaStyle:{opacity:.10}};
      })
    });
  } else if(kind === 'radar'){
    var max = spec.max || 5;
    mk(id, {
      tooltip: Object.assign({trigger:'item'}, TT), legend:{show:false},
      radar:{ indicator: cats.map(function(n,i){
                return {name: n + (spec.values ? '\\n' + spec.values[i] : ''), max: max}; }),
              radius:'62%', splitNumber:5, axisName:{color:INK2, fontSize:11},
              splitArea:{areaStyle:{color:['#FBFCFE','#F3F7FC','#ECF2F9','#E4ECF5','#DCE6F1']}},
              splitLine:{lineStyle:{color:RULE2}}, axisLine:{lineStyle:{color:RULE2}} },
      series:[{type:'radar', data:[{value: spec.values || [], name:'评分'}],
               areaStyle:{color:'rgba(31,95,168,.16)'},
               lineStyle:{color:PAL[0], width:2}, itemStyle:{color:PAL[0]}}]
    });
  } else if(kind === 'gauge'){
    var g = (spec.values && spec.values[0] != null) ? spec.values[0] : 0;
    var gmax = spec.max || 100;
    mk(id, {
      tooltip: Object.assign({trigger:'item'}, TT), legend:{show:false},
      series:[{type:'gauge', min:0, max:gmax, radius:'86%', startAngle:210, endAngle:-30,
               progress:{show:true, width:14, itemStyle:{color:PAL[0]}},
               axisLine:{lineStyle:{width:14, color:[[1, '#E7ECF3']]}},
               axisTick:{show:false}, splitLine:{length:10, lineStyle:{color:RULE2}},
               axisLabel:{color:MUTED, fontSize:10, distance:16},
               pointer:{width:4, itemStyle:{color:INK2}},
               detail:{valueAnimation:true, fontSize:26, color:INK, offsetCenter:[0,'62%'],
                       formatter:'{value}' + (spec.unit||'')},
               data:[{value:g}]}]
    });
  }
}

drawChart.__charts = {};
(D.charts || []).forEach(function(s){ drawChart(s); });
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


# 允许的列类型（值必须与样式表里的 .num / .txt 真实对应）。
COL_KINDS = ("num", "txt")

# 模板里以 `class="... {var}"` 形式拼接的动态 class 取值。
DYNAMIC_CLASSES = ("sr-up", "sr-down", "sr-flat", "badge-ok", "badge-warn", "badge-bad")


def _col_class(k):
    """列类型 → class 名（字面量内联，便于静态检查）。"""
    if k not in COL_KINDS:
        raise ValueError(f"未知列类型 {k!r}，允许：{COL_KINDS}")
    return "num" if k == "num" else "txt"


def _badge_class(level):
    """结论/合规等级 → 徽标 class（值域与 DYNAMIC_CLASSES 对应）。"""
    lv = str(level or "").strip()
    if lv in ("满足", "合规", "可合作", "通过", "达标", "是", "已核实", "完整"):
        return "badge-ok"
    if lv in ("缺口", "谨慎", "待补充核验", "待核实", "部分", "不完整"):
        return "badge-warn"
    if lv in ("不合作", "不满足", "不合规", "红线", "否", "重大"):
        return "badge-bad"
    return "badge-warn"


def _table(headers, rows, kinds=None):
    """通用表格：kinds 逐列声明换行行为（num=nowrap 对齐；txt=允许折行）。"""
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
            kind = kinds[i] if i < len(kinds) else "num"
            content = _inline_md(str(c)) if kind == "txt" else _esc(c)
            tds += f'<td class="{_col_class(kind)}">{content}</td>'
        body += f"<tr>{tds}</tr>"
    return f'<table class="data-table"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'


def render_block(b):
    """把一个 block 渲染成 HTML 片段。未识别类型 → 空串（不产半成品）。"""
    if not isinstance(b, dict):
        return ""
    t = b.get("type")
    if t == "text":
        return md_to_html(b.get("md", ""))
    if t == "h3":
        return f'<h3>{_inline_md(str(b.get("text", "")))}</h3>'
    if t == "table":
        return '<div class="tbl-wrap">' + _table(
            b.get("headers", []), b.get("rows", []), b.get("kinds")) + '</div>'
    if t == "note":
        return f'<p class="table-note">{md_to_html(b.get("md", ""))}</p>'
    if t == "cards":
        out = ""
        for i, c in enumerate(b.get("items", []) or []):
            title = c.get("t", f"要点 {i+1}")
            out += (f'<div class="card"><div class="t">{_inline_md(str(title))}</div>'
                    f'<div class="v">{md_to_html(c.get("v", ""))}</div></div>')
        return out
    if t == "kv":
        rows = "".join(
            f'<tr><td class="k">{_inline_md(str(r[0]))}</td>'
            f'<td class="v">{md_to_html(str(r[1]))}</td></tr>'
            for r in b.get("rows", []) if isinstance(r, (list, tuple)) and len(r) >= 2)
        return f'<table class="kv-table"><tbody>{rows}</tbody></table>'
    if t == "score":
        rows = ""
        for d in b.get("items", []) or []:
            coef = d.get("coef")
            if isinstance(coef, (int, float)):
                cls = "sr-up" if coef > 0 else ("sr-down" if coef < 0 else "sr-flat")
                coef_txt = f"{float(coef)*100:+.0f}%"
            else:
                cls, coef_txt = "sr-flat", "—"
            ev = str(d.get("evidence", "") or "")
            ev_html = f'<span class="pn-src">证据强度 {ev}</span>' if ev else ""
            rows += (f'<div class="score-row">'
                     f'<span class="sr-name">{_esc(d.get("name",""))}</span>'
                     f'<span class="sr-val">{_esc(d.get("score","—"))}</span>'
                     f'<span class="sr-coef {cls}">{coef_txt}</span>'
                     f'<span class="sr-basis">{md_to_html(str(d.get("basis",""))) or "—"}{ev_html}</span>'
                     f'</div>')
        head = '<div class="table-note">维度 / 评分 / 系数 / 依据</div>' if b.get("head", True) else ""
        return head + '<div class="score-list">' + rows + '</div>'
    if t == "risk":
        lv_color = {"高": "#B23A33", "中": "#B0820E", "低": "#2E8B57"}
        out = ""
        for r in b.get("items", []) or []:
            color = lv_color.get(r.get("level"), "#8A94A6")
            out += (f'<div class="risk-item" style="border-left-color:{color}">'
                    f'<div class="rt"><span class="rtag" style="color:{color}">'
                    f'{_esc(r.get("level",""))}风险</span>{_inline_md(str(r.get("title","")))}</div>'
                    f'<div class="rd">{md_to_html(r.get("desc",""))}</div></div>')
        return out
    if t == "pending":
        return "".join(f'<div class="pending-item">{md_to_html(str(p))}</div>'
                       for p in b.get("items", []) or [])
    if t == "badges":
        return "".join(
            f'<span class="badge {_badge_class(x.get("level"))}">{_esc(x.get("level",""))}</span>'
            f'{_inline_md(str(x.get("text","")))}<br>' for x in b.get("items", []) or [])
    if t == "chart":
        return (f'<div id="{b.get("id","")}" class="chart'
                f'{ " sm" if b.get("sm") else "" }"></div>')
    return ""


def build_sections_html(data):
    """按 SECTIONS 骨架渲染各章节；正文取自 data['sections'][id]['blocks']。"""
    by_id = {s.get("id"): s for s in (data.get("sections", []) or [])
             if isinstance(s, dict) and s.get("id")}
    out = []
    for sid, _nav, kicker, title in SECTIONS:
        sec = by_id.get(sid, {})
        blocks = sec.get("blocks", []) or []
        body = "".join(render_block(b) for b in blocks)
        if not body:
            body = '<p class="atext">本节内容未提供。</p>'
        out.append(
            f'<div class="section" id="{sid}">\n'
            f'    <div class="kicker">{kicker}</div>\n'
            f'    <h2>{title}</h2>\n'
            f'    {body}\n'
            f'  </div>')
    return "\n\n  ".join(out)


def build_nav():
    return "\n    ".join(f'<a href="#{sid}">{nav}</a>' for sid, nav, _k, _t in SECTIONS)


def build_kpi(data):
    """KPI 卡片：来自 data['kpi']；缺省不渲染整块网格。"""
    items = data.get("kpi", []) or []
    if not items:
        return ""
    cards = ""
    for it in items:
        cards += (f'<div class="kpi"><div class="kpi-label">{_esc(it.get("label",""))}</div>'
                  f'<div class="kpi-value">{_esc(it.get("value","—"))}</div>'
                  f'<div class="kpi-sub">{_esc(it.get("sub",""))}</div></div>')
    return f'<div class="kpi-grid">{cards}</div>'


def build_payload(data):
    """图表数据载荷：仅取纯数值与标签，避免 HTML 片段污染图表标签。"""
    charts = []
    for s in data.get("charts", []) or []:
        if isinstance(s, dict) and s.get("id"):
            charts.append({
                "id": s.get("id"), "kind": s.get("kind", "bar"),
                "categories": [str(c) for c in (s.get("categories", []) or [])],
                "unit": s.get("unit", ""), "max": s.get("max"),
                "values": s.get("values", []),
                "series": [{"name": str(ser.get("name", "")),
                            "data": ser.get("data", []),
                            "color": ser.get("color"),
                            "label": ser.get("label", False)}
                           for ser in (s.get("series", []) or [])],
            })
    return {"charts": charts}


# ============================================================
#  HTML 报告生成
# ============================================================

def generate_html_report(data, output_path, echarts_js=""):
    # 红标唯一解析点：整棵树过一遍，之后的渲染层再也看不到 `[[红]]`。
    rendered = _apply_redmark(data)

    company = rendered.get("company", "标的")
    collect_date = rendered.get("collect_date", datetime.now().strftime("%Y-%m-%d"))

    meta_line = rendered.get("meta_line")
    if not meta_line:
        meta_line = (f'<b>{_esc(data.get("security_code") or "—")}</b> ｜ '
                     f'基准日 <b>{_esc(collect_date)}</b> ｜ '
                     f'生成 <b>{datetime.now().strftime("%Y-%m-%d %H:%M")}</b> ｜ '
                     f'数据来源：祜·Care及Gangtise合作股权投研')

    replacements = {
        "__TITLE__": f"{company} {TITLE_SUFFIX}",
        "__COMPANY__": _esc(company),
        "__CODE__": _esc(data.get("security_code") or "—"),
        "__STATUS__": _esc(data.get("status_note") or "自查框架"),
        "__SIDEBAR_IC__": SIDEBAR_IC,
        "__DOC_KICKER__": DOC_KICKER,
        "__TITLE_SUFFIX__": TITLE_SUFFIX,
        "__META_LINE__": meta_line,
        "__IC_CONCLUSION__": md_to_html(rendered.get("ic_conclusion", "（未提供一句话结论）")),
        "__KPI_GRID__": build_kpi(rendered),
        "__NAV__": build_nav(),
        "__SECTIONS_HTML__": build_sections_html(rendered),
        "__FOOTER__": FOOTER_TEXT,
        "__DATA__": json.dumps(build_payload(data), ensure_ascii=False),
        # 内联图表引擎：必须**最后**一次替换。
        "__ECHARTS_LIB__": echarts_js,
    }

    html = HTML_TEMPLATE
    for token, value in replacements.items():
        html = html.replace(token, value)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def main():
    parser = argparse.ArgumentParser(description=f"生成{TITLE_SUFFIX}（离线自包含 HTML）")
    parser.add_argument("--data", required=True, help="报告输入 JSON 文件路径")
    parser.add_argument("--output-dir", default="", help=f"输出目录；默认 {{工作目录}}/{SUBDIR}")
    parser.add_argument("--company", default="", help="名称（覆盖 JSON 中的 company 作为文件名）")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    company = args.company or data.get("company", "标的")

    try:
        echarts_js = load_echarts_js()
    except AssetError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    print(f"报告主体：{company}（{data.get('status_note') or '自查框架'}）", file=sys.stderr)

    out_dir = os.path.abspath(args.output_dir or default_skill_output_dir())
    os.makedirs(out_dir, exist_ok=True)

    html_path = os.path.join(out_dir, f"{company}_{FILE_SUFFIX}.html")
    generate_html_report(data, html_path, echarts_js)
    print(html_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

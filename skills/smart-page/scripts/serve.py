#!/usr/bin/env python3
"""
serve.py · tencent-smart-page 四阶段路由服务

阶段链路（state.json.stage 字段驱动）：
    stage=scene_probe          · 场景初筛（agent 预判 + 用户确认/修改 + 自定义场景）
    stage=intent_questionnaire · 细分意图问卷（按 scene 选内置模板，或读 agent 注入的动态问卷）
    stage=template_choice      · 3 套叙事模板卡片（封面缩略 + 长图预览 + AI 帮我选兜底）
    stage=skeleton_loading     · 生成中骨架（agent 写入 skeleton.json，server 渲染思维链）

CLI：
    python3 serve.py start --theme "主题" [--probe-scene proposal] [--probe-reason "..."] [--custom-scenes-file ...]
    python3 serve.py advance <workdir> --to intent_questionnaire [--questionnaire-file ...]
    python3 serve.py advance <workdir> --to template_choice [--top 3]
    python3 serve.py advance <workdir> --to skeleton_loading --skeleton-file <path>
    python3 serve.py stop <workdir>

落盘（位于 workdir 目录下）：
    state.json              · 当前 stage、probe 信息、版本号
    server.pid / server.error · 守护进程 pid 与启动错误
    scene_confirm.json      · scene_probe 用户确认后写入（POST /confirm_scene）
    dyn_questionnaire.json  · advance --to intent_questionnaire --questionnaire-file 时落盘的动态问卷
    answers.json            · 意图问卷答案（POST /submit_intent）
    match_result.json       · advance --to template_choice 时由 match.py 输出
    choice.json             · 用户最终选择（POST /choose）
    skeleton.json           · advance --to skeleton_loading --skeleton-file 时落盘的骨架
"""

import argparse
import html
import json
import os
import signal
import sys
import socket
import subprocess
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import template_source  # noqa: E402

PORT_RANGE = range(17501, 17599)
WORKDIR_MARKER = ".smart-page-workdir"
WORKDIR_MARKER_VALUE = "smart-page-managed-workdir-v1"


def h(value) -> str:
    """统一转义进入 HTML 文本/属性的动态内容。"""
    return html.escape("" if value is None else str(value), quote=True)


def find_port() -> int:
    for port in PORT_RANGE:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("no available port")


def load_index() -> dict:
    return template_source.load_index()


# ============================================================
# 共用：腾讯系设计 Token
# ============================================================

TENCENT_CSS = r"""
  :root{
    --tc-blue:#0052D9;
    --tc-blue-600:#0037A5;
    --tc-blue-50:#EAF1FF;
    --tc-blue-100:#D6E4FF;
    --tc-gold:#FBAE40;
    --tc-ink:#0E1F3A;
    --tc-ink-2:#2E4363;
    --tc-muted:#6A7890;
    --tc-line:#E2E8F3;
    --tc-bg:#F5F7FC;
    --tc-surface:#FFFFFF;
    --tc-danger:#E54D42;
    --tc-success:#00A870;
    --radius-lg:14px;
    --radius-md:10px;
    --radius-sm:7px;
    --shadow-card:0 1px 2px rgba(14,31,58,.04), 0 8px 28px rgba(14,31,58,.08);
    --shadow-pop:0 2px 6px rgba(14,31,58,.06), 0 12px 36px rgba(0,82,217,.14);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{background:var(--tc-bg);color:var(--tc-ink);
    font-family:"PingFang SC","Microsoft YaHei","Helvetica Neue",Helvetica,Arial,sans-serif;
    font-size:14px;line-height:1.6;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  }
  a{color:var(--tc-blue);text-decoration:none}
  button{font-family:inherit;cursor:pointer}
  .wrap{max-width:780px;margin:0 auto;padding:28px 24px 140px}
  .brand{display:flex;align-items:center;gap:10px;margin-bottom:14px}
  .brand-logo{
    width:28px;height:28px;border-radius:8px;
    background:linear-gradient(135deg,var(--tc-blue) 0%, #2B6FF1 60%, var(--tc-gold) 160%);
    display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:14px;
    box-shadow:0 2px 6px rgba(0,82,217,.35);
  }
  .brand-name{font-size:13px;font-weight:600;color:var(--tc-ink-2);letter-spacing:.5px}
  .brand-badge{font-size:11px;color:var(--tc-blue);background:var(--tc-blue-50);
    padding:2px 8px;border-radius:999px;font-weight:600}
  h1{font-size:22px;font-weight:700;color:var(--tc-ink);letter-spacing:-.01em;margin-bottom:6px}
  h1 em{font-style:normal;color:var(--tc-blue);background:linear-gradient(180deg,transparent 62%,rgba(251,174,64,.42) 62%);padding:0 2px}
  .lead{font-size:13px;color:var(--tc-muted);margin-bottom:26px}
  .lead b{color:var(--tc-ink-2);font-weight:600}
  .card{background:var(--tc-surface);border:1px solid var(--tc-line);border-radius:var(--radius-lg);
    padding:18px 20px;box-shadow:var(--shadow-card)}
  .section{margin-bottom:18px}
  .section-label{font-size:14px;font-weight:600;color:var(--tc-ink);margin-bottom:4px;display:flex;align-items:center;gap:8px}
  .section-label::before{content:"";width:3px;height:14px;background:var(--tc-blue);border-radius:2px}
  .section-hint{font-size:12px;color:var(--tc-muted);margin-bottom:12px;padding-left:11px}
  .chip-row{display:flex;flex-wrap:wrap;gap:8px}
  .chip{padding:8px 14px;border-radius:20px;font-size:13px;color:var(--tc-ink-2);
    background:#fff;border:1px solid var(--tc-line);transition:.15s;user-select:none;font-weight:500}
  .chip:hover{border-color:var(--tc-blue);color:var(--tc-blue);background:var(--tc-blue-50)}
  .chip.is-selected{background:var(--tc-blue);color:#fff;border-color:var(--tc-blue);box-shadow:0 4px 12px rgba(0,82,217,.25)}
  .chip--ghost{background:transparent;border-style:dashed;color:var(--tc-muted)}
  .chip--ghost.is-selected{background:var(--tc-ink);border-style:solid;color:#fff;border-color:var(--tc-ink)}
  .chip--tencent{background:linear-gradient(135deg,#F8FAFF 0%,#EEF4FF 100%);color:var(--tc-ink);
    border:1px solid var(--tc-line);box-shadow:none;font-weight:600;position:relative;overflow:visible}
  .chip--tencent::before{content:"🏢 ";}
  .chip--tencent::after{content:"官方";position:absolute;top:-7px;right:-6px;
    font-size:9px;font-weight:700;color:#fff;background:var(--tc-gold);
    padding:1px 5px;border-radius:4px;line-height:1.4;letter-spacing:.3px;
    box-shadow:0 2px 4px rgba(251,174,64,.4)}
  .chip--tencent:hover{background:linear-gradient(135deg,#EEF4FF 0%,#E3ECFF 100%);border-color:var(--tc-blue-100)}
  .chip--tencent.is-selected{background:linear-gradient(90deg,var(--tc-blue) 0%, #2B6FF1 100%);color:#fff;border-color:transparent;
    box-shadow:0 6px 20px rgba(0,82,217,.45)}
  .chip--tencent.is-selected::after{background:#fff;color:var(--tc-blue)}
  textarea{width:100%;min-height:110px;padding:12px 14px;border-radius:var(--radius-md);
    border:1px solid var(--tc-line);background:#fff;font-size:13px;font-family:inherit;
    outline:none;resize:vertical;color:var(--tc-ink);line-height:1.65;transition:.15s}
  textarea:focus{border-color:var(--tc-blue);box-shadow:0 0 0 3px var(--tc-blue-100)}
  .footer{position:fixed;bottom:0;left:0;right:0;padding:14px 24px;background:rgba(255,255,255,.92);
    backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
    border-top:1px solid var(--tc-line);display:flex;justify-content:center;z-index:40}
  .footer-inner{max-width:780px;width:100%;display:flex;justify-content:flex-end;gap:10px}
  .btn{padding:10px 20px;border-radius:var(--radius-md);font-size:13px;font-weight:600;
    border:none;transition:.15s;font-family:inherit;display:inline-flex;align-items:center;gap:6px}
  .btn--primary{background:var(--tc-blue);color:#fff;box-shadow:0 2px 8px rgba(0,82,217,.3)}
  .btn--primary:hover{background:var(--tc-blue-600);box-shadow:0 4px 14px rgba(0,82,217,.4);transform:translateY(-1px)}
  .btn--ghost{background:transparent;color:var(--tc-ink-2);border:1px solid var(--tc-line)}
  .btn--ghost:hover{background:var(--tc-blue-50);color:var(--tc-blue);border-color:var(--tc-blue)}
  .done{display:none;text-align:center;padding:60px 16px}
  .done .check{width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,var(--tc-blue),var(--tc-gold));
    margin:0 auto 14px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:28px;font-weight:800;
    box-shadow:0 8px 24px rgba(0,82,217,.3)}
  .done h3{font-size:18px;margin-bottom:6px;font-weight:700}
  .done p{font-size:13px;color:var(--tc-muted)}
  .done-loader{margin:18px auto 0;display:flex;flex-direction:column;align-items:center;gap:14px}
  .done-dots{display:inline-flex;gap:6px}
  .done-dots span{width:7px;height:7px;border-radius:50%;
    background:linear-gradient(135deg,var(--tc-blue),var(--tc-gold));
    animation:done-dot-bounce 1.2s ease-in-out infinite}
  .done-dots span:nth-child(2){animation-delay:.18s}
  .done-dots span:nth-child(3){animation-delay:.36s}
  @keyframes done-dot-bounce{0%,80%,100%{transform:translateY(0);opacity:.35}40%{transform:translateY(-6px);opacity:1}}
  .done-bar{width:200px;height:3px;background:var(--tc-blue-50);border-radius:3px;overflow:hidden;position:relative}
  .done-bar::after{content:"";position:absolute;top:0;left:0;height:100%;width:40%;
    background:linear-gradient(90deg,transparent,var(--tc-blue),var(--tc-gold),transparent);
    border-radius:3px;animation:done-bar-sweep 1.6s ease-in-out infinite}
  @keyframes done-bar-sweep{0%{left:-40%}100%{left:100%}}
  @media(prefers-reduced-motion:reduce){
    .done-dots span,.done-bar::after{animation:none}
    .done-bar::after{left:0;width:100%;opacity:.6}
  }
  body.finished .section,body.finished .header-block,body.finished .footer,body.finished .cards,body.finished .ai-pick-cta{display:none!important}
  body.finished .done{display:block}
  .timeout{display:none;position:fixed;inset:0;background:#fff;z-index:100;flex-direction:column;
    align-items:center;justify-content:center;text-align:center;padding:24px}
  body.timed-out .timeout{display:flex}body.timed-out .wrap,body.timed-out .footer{display:none}
"""


BRAND_HTML = '<div class="brand"><span class="brand-logo">AI</span><span class="brand-name">AI 原生汇报新范式</span></div>'

STAGE_POLL_JS = r"""
// 修复 bfcache（Safari/Chrome 返回缓存）导致"后退到旧阶段"的问题
window.addEventListener("pageshow", function(e){
  if (e.persisted || (performance.getEntriesByType && performance.getEntriesByType("navigation")[0] && performance.getEntriesByType("navigation")[0].type === "back_forward")) {
    location.reload();
  }
});
async function pollStageAndReload(){
  // 标记当前 stage 正在等待切换（刷新时可恢复 loading 态）
  sessionStorage.setItem("sp_waiting_from", window.CURRENT_STAGE);
  // 提交后等服务端 stage 切换：每 1s 轮询一次 /stage，最长 180s
  for(let i=0;i<180;i++){
    try{
      const r=await fetch("/stage",{cache:"no-store"});
      if(r.ok){const s=await r.json();if(s.stage&&s.stage!==window.CURRENT_STAGE){sessionStorage.removeItem("sp_waiting_from");location.reload();return;}}
    }catch(e){}
    await new Promise(res=>setTimeout(res,1000));
  }
}
// 页面加载时：检测是否处于"已提交等待切换"状态（刷新恢复）
(function(){
  var wf=sessionStorage.getItem("sp_waiting_from");
  if(wf && wf===window.CURRENT_STAGE){
    // 仍在同一 stage，说明 advance 还没完成，恢复 loading 态并继续轮询
    document.body.classList.add("finished");
    pollStageAndReload();
  }
})();
(async function(){
  // 后台心跳：每 3s 探一次 /stage，连不上就显示超时蒙层
  while(true){
    await new Promise(r=>setTimeout(r,3000));
    if(document.body.classList.contains("finished")||document.body.classList.contains("timed-out"))return;
    try{const r=await fetch("/stage",{cache:"no-store"});if(!r.ok)throw 0;}catch(_){document.body.classList.add("timed-out");return;}
  }
})();
"""


# ============================================================
# STAGE 1 · 场景初筛（AI 预判 + 确认）
# ============================================================

SCENE_META = {
    "proposal": {"emoji": "📐", "cn": "向上汇报 / 立项", "tagline": "提案、方案、ROI、资源申请", "has_template": True},
    "sync":     {"emoji": "📊", "cn": "周期同步 / 双周报", "tagline": "周报、OKR、进度、状态更新", "has_template": True},
    "insight":  {"emoji": "📈", "cn": "数据洞察 / 产品分析", "tagline": "KPI、归因、对比、dashboard", "has_template": True},
    "share":    {"emoji": "📖", "cn": "知识传播 / 技术分享", "tagline": "技术分享、长文、培训、杂志", "has_template": True},
}

# 模板库未覆盖、需走 AI 自由生成路径的场景示例（仅作 agent 拼装 custom_scenes 时的参考字典，
# 本文件本身**不直接读取**它；agent 把 custom_scenes 数组通过 --custom-scenes-file 传给 start）
CUSTOM_SCENE_EXAMPLES = {
    "homepage":   {"emoji": "🏠", "cn": "品牌官网 / Landing",  "tagline": "产品首页、品牌介绍"},
    "invitation": {"emoji": "💌", "cn": "邀请函 / 会议邀请",    "tagline": "活动、婚礼、年会"},
    "campaign":   {"emoji": "🎯", "cn": "运营活动页 / H5",      "tagline": "促销、招募、落地页"},
    "prd":        {"emoji": "📝", "cn": "PRD / 需求文档",       "tagline": "产品需求说明书"},
    "brochure":   {"emoji": "📒", "cn": "画册 / 作品集",        "tagline": "设计画册、个人作品" },
    "minutes":    {"emoji": "📋", "cn": "会议纪要 / 复盘",      "tagline": "纪要、复盘文档"},
    "profile":    {"emoji": "👤", "cn": "个人简历 / 介绍页",    "tagline": "简历、自我介绍"},
    "report":     {"emoji": "📑", "cn": "自由网页报告",          "tagline": "其他自定义汇报"},
}


def page_scene_probe(theme: str, probe_scene: str, probe_reason: str, custom_scenes=None) -> str:
    """
    custom_scenes: list of dict({id, emoji, cn, tagline, has_template})，由 agent 根据用户输入动态生成。
      · id 以 "custom:" 开头，如 "custom:invitation"
      · has_template=False 时走自由生成路径（scene_choice=other）
    """
    custom_scenes = custom_scenes or []
    theme_html = h(theme)
    default_scene_js = json.dumps(probe_scene or "sync", ensure_ascii=False)

    # 构造 chips：先列模板覆盖的 4 个场景
    chips = ""
    all_scenes = dict(SCENE_META)
    for sid, meta in SCENE_META.items():
        is_pre = "is-selected" if sid == probe_scene else ""
        chips += f'<button class="chip {is_pre}" data-v="{h(sid)}" data-has-tpl="1">{h(meta["emoji"])} {h(meta["cn"])}</button>'

    # 再追加 agent 动态识别出来的"模板外场景"（走 scene=other 自由生成）
    if custom_scenes:
        chips += '<div style="width:100%;height:0;flex-basis:100%"></div>'
        chips += '<div style="font-size:11px;color:var(--tc-muted);margin:6px 0 2px">模板外场景 · 走 AI 自由生成（四区原则不变）</div>'
        chips += '<div style="width:100%;height:0;flex-basis:100%"></div>'
        for cs in custom_scenes:
            sid = cs.get("id", "custom:other")
            is_pre = "is-selected" if sid == probe_scene else ""
            chips += f'<button class="chip {is_pre}" data-v="{h(sid)}" data-has-tpl="0">{h(cs.get("emoji", "✚"))} {h(cs.get("cn", sid))}</button>'
            all_scenes[sid] = cs

    # 兜底入口：完全自定义
    chips += '<button class="chip chip--ghost" data-v="custom:freeform" data-has-tpl="0">✚ 其他 · 让 AI 自由生成</button>'

    probe_block = ""
    # probe_scene 可能是模板场景或 custom:xxx
    probe_meta = all_scenes.get(probe_scene) or (SCENE_META.get(probe_scene) if probe_scene else None)
    if probe_meta:
        emoji = h(probe_meta.get("emoji", "🤖"))
        cn = h(probe_meta.get("cn", probe_scene))
        reason = h(probe_reason or '已根据关键词匹配，若不准确请手动修正或选"其他·自由生成"。')
        probe_block = f"""
        <div class="ai-probe">
          <div class="ai-probe-head">
            <span class="ai-probe-tag">AI 初筛</span>
            <span class="ai-probe-title">基于你的输入，这看起来像<b>{emoji} {cn}</b></span>
          </div>
          <div class="ai-probe-reason">{reason}</div>
        </div>
        """

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>场景初筛 · {theme_html}</title><style>{TENCENT_CSS}
.ai-probe{{background:linear-gradient(135deg,var(--tc-blue-50) 0%, #fff 100%);border:1px solid var(--tc-blue-100);
  border-radius:var(--radius-lg);padding:14px 18px;margin-bottom:18px}}
.ai-probe-head{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.ai-probe-tag{{font-size:11px;background:var(--tc-blue);color:#fff;padding:2px 8px;border-radius:4px;font-weight:600;letter-spacing:.5px}}
.ai-probe-title{{font-size:14px;color:var(--tc-ink);font-weight:500}}
.ai-probe-title b{{color:var(--tc-blue);font-weight:700}}
.ai-probe-reason{{font-size:12px;color:var(--tc-muted);padding-left:4px}}
</style></head>
<body><div class="wrap">
{BRAND_HTML}
<div class="header-block">
  <h1>关于「<em>{theme_html}</em>」的 <span style="color:var(--tc-blue)">场景初筛</span></h1>
  <div class="lead">先确认大的汇报类型，下一步会根据场景出 <b>专属的细分意图问卷</b></div>
</div>
{probe_block}
<div class="section card" data-field="scene">
  <div class="section-label">这是什么类型的汇报？</div>
  <div class="section-hint">AI 已做初步判断，你可以确认或重选</div>
  <div class="chip-row">{chips}</div>
</div>
<div class="done"><div class="check">✓</div><h3>场景已确认</h3><p>正在为你生成专属细分问卷...</p>
<div class="done-loader"><div class="done-dots"><span></span><span></span><span></span></div><div class="done-bar"></div></div>
</div>
</div>
<div class="footer"><div class="footer-inner">
  <button class="btn btn--primary" id="btn-continue">确认场景 →</button>
</div></div>
<script>
window.CURRENT_STAGE="scene_probe";
const THEME={json.dumps(theme, ensure_ascii=False)};
const DEFAULT_SCENE={default_scene_js};
document.querySelectorAll(".chip[data-v]").forEach(c=>c.addEventListener("click",()=>{{
  c.closest(".section").querySelectorAll(".chip").forEach(x=>x.classList.remove("is-selected"));
  c.classList.add("is-selected");
}}));
document.getElementById("btn-continue").addEventListener("click",async()=>{{
  const sel=document.querySelector(".section[data-field=scene] .chip.is-selected");
  const scene=sel?sel.dataset.v:DEFAULT_SCENE;
  const hasTpl=sel?(sel.dataset.hasTpl==="1"):true;
  const r=await fetch("/confirm_scene",{{method:"POST",headers:{{"Content-Type":"application/json"}},
    body:JSON.stringify({{scene,has_template:hasTpl,theme:THEME}})}});
  if(r.ok){{document.body.classList.add("finished");pollStageAndReload();}}
}});
{STAGE_POLL_JS}
</script></body></html>"""


# ============================================================
# STAGE 2 · 场景相关的细分意图问卷
# ============================================================

# 每场景的细分意图问卷（仅含 sub_intent + audience 两题；
# tone/skin_pref 由全局 TONE_OPTIONS_* 统一渲染，content 是页面底部 textarea）
QUESTIONNAIRES = {
    "proposal": {
        "title": "立项/向上汇报意图补充",
        "hint": "不同类型的向上汇报，匹配的叙事范式完全不同",
        "sub_intent": {
            "label": "这是哪一类向上汇报？",
            "hint": "决定用哪套叙事骨架（金字塔/SCQA/BLM）",
            "options": [
                {"v": "new-project",  "l": "🚀 新立项 / 资源申请", "hint": "金字塔·结论先行"},
                {"v": "pivot",        "l": "🔄 转型 / 推动变革",    "hint": "SCQA·冲突叙事"},
                {"v": "strategy",     "l": "🧭 战略规划 / 3-5 年",  "hint": "BLM·战略模型"},
                {"v": "option-pick",  "l": "⚖️ 方案对比 / 决策支持", "hint": "金字塔·多方案评估"},
            ]
        },
        "audience": {
            "label": "汇报对象是谁？",
            "options": [
                {"v": "leader",     "l": "📈 直属 Leader"},
                {"v": "committee",  "l": "🏛 评审委员会 / 投委会"},
                {"v": "cross-bu",   "l": "🤝 跨 BU / 跨部门"},
            ]
        },
    },
    "sync": {
        "title": "周期同步意图补充",
        "hint": "轻量同步 vs 有复盘感 vs 跨团队对齐，叙事完全不同",
        "sub_intent": {
            "label": "这次同步的性质是？",
            "hint": "决定用 PREP / STAR / OKR",
            "options": [
                {"v": "lightweight",  "l": "⚡ 轻量双周报 / 进展同步", "hint": "PREP·观点回环"},
                {"v": "retro",        "l": "🎬 项目复盘 / 战役收尾", "hint": "STAR·情境行动"},
                {"v": "cross-align",  "l": "🎯 季度 OKR / 跨团对齐", "hint": "OKR·目标对齐"},
                {"v": "monthly",      "l": "🗓 月报 / 阶段总结", "hint": "PREP+KPI"},
            ]
        },
        "audience": {
            "label": "同步给谁？",
            "options": [
                {"v": "team",       "l": "👥 团队内"},
                {"v": "leader",     "l": "📈 向上 Leader"},
                {"v": "cross-team", "l": "🔗 跨团队 / 依赖方"},
            ]
        },
    },
    "insight": {
        "title": "数据洞察意图补充",
        "hint": "概览汇报 vs 深度归因 vs A/B 对比，图表与叙事完全不同",
        "sub_intent": {
            "label": "数据报告的核心诉求？",
            "options": [
                {"v": "kpi-overview", "l": "📊 KPI 大盘概览 / Dashboard", "hint": "金字塔·数据版"},
                {"v": "why-drop",     "l": "🔻 异常波动 / 为什么下跌", "hint": "归因树"},
                {"v": "why-rise",     "l": "🔺 爆发归因 / 上涨拆解", "hint": "归因树"},
                {"v": "ab-compare",   "l": "🆎 A/B 实验 / 同环比", "hint": "对比叙事"},
            ]
        },
        "audience": {
            "label": "读者是？",
            "options": [
                {"v": "pm",         "l": "📦 产品经理"},
                {"v": "leader",     "l": "📈 业务 Leader"},
                {"v": "ops",        "l": "⚙️ 运营 / 数据同事"},
            ]
        },
    },
    "share": {
        "title": "知识传播意图补充",
        "hint": "故事曲线 vs 问答驱动 vs 杂志深读，排版差异巨大",
        "sub_intent": {
            "label": "这是哪一类分享？",
            "options": [
                {"v": "idea-story",   "l": "💡 产品理念 / 技术故事", "hint": "故事曲线"},
                {"v": "training",     "l": "🎓 培训课件 / FAQ", "hint": "问题驱动"},
                {"v": "deep-article", "l": "📖 深度长文 / 杂志特辑", "hint": "杂志深读"},
                {"v": "talk-deck",    "l": "🎤 技术大会 / 公开演讲", "hint": "故事曲线·Hero"},
            ]
        },
        "audience": {
            "label": "读者是？",
            "options": [
                {"v": "engineer",   "l": "👨‍💻 工程师 / 技术同行"},
                {"v": "product",    "l": "📦 产品/设计"},
                {"v": "external",   "l": "🌐 对外 / 社区"},
            ]
        },
    },
}

# tone 选项（所有场景共享，但最后一项始终是"腾讯系"）
TONE_OPTIONS_COMMON = [
    {"v": "precise",       "l": "⚡ 精准克制"},
    {"v": "institutional", "l": "🏛 严谨机构"},
    {"v": "narrative",     "l": "☕ 温暖叙事"},
    {"v": "data",          "l": "📈 数据密集"},
    {"v": "elegant",       "l": "💜 优雅传播"},
]
TONE_OPTIONS_TENCENT = {"v": "tencent", "l": "腾讯系官方", "tencent": True}
TONE_OPTIONS_MAGAZINE = {"v": "magazine", "l": "📕 杂志深读"}


def page_intent_questionnaire(theme: str, scene: str, dyn_questionnaire: dict = None) -> str:
    """
    意图问卷页（4 题：意图场景 / 传播对象 / 设计风格 / 更多补充）。

    dyn_questionnaire: agent 注入的动态问卷 JSON，结构：
      {
        "title": "...",                 # 问卷标题
        "hint":  "...",                 # 副标
        "sub_intent": {                 # 题 1：意图场景（必填）
          "label": "这是哪一类？",
          "hint": "...",
          "options": [{"v":"xxx","l":"🎯 xxx","hint":"..."}]
        },
        "audience": {                   # 题 2：传播对象（必填）
          "label": "给谁看？",
          "options": [{"v":"xxx","l":"xxx"}]
        },
        "tone": {                       # 题 3：设计风格（可选，用 SKIN_LIBRARY + agent 自定义）
          "label": "设计风格",
          "options": [{"v":"xxx","l":"xxx","accent":"#XXX"}],  # accent 可选
          "include_tencent": true       # 是否追加腾讯系官方常驻按钮（默认 true）
        }
      }

    所有题都会自动追加「🎲 让 AI 帮我选」chip。
    """
    # 优先用 agent 注入的动态问卷；否则 fallback 到内置 4 场景模板；再 fallback 到 sync
    if dyn_questionnaire:
        q = dyn_questionnaire
    else:
        q = QUESTIONNAIRES.get(scene, QUESTIONNAIRES.get("sync", {}))
    scene_meta = SCENE_META.get(scene, {})

    sub = q.get("sub_intent") or {"label": "这是哪一类？", "hint": "", "options": []}
    aud = q.get("audience") or {"label": "给谁看？", "hint": "决定信息密度与语气", "options": []}
    tone_cfg = q.get("tone") or {"label": "设计风格", "hint": "", "options": None, "include_tencent": True}

    title = q.get("title") or f"{scene_meta.get('cn', scene)} 意图补充"
    hint_line = q.get("hint") or "回答 4 个问题，帮你匹配最合适的叙事与风格"
    scene_emoji = h(scene_meta.get("emoji", "📌"))
    scene_cn = h(scene_meta.get("cn", scene))
    theme_html = h(theme)
    title_html = h(title)
    hint_html = h(hint_line)

    # === 题 1 · 意图场景 ===
    sub_chips = "".join(
        f'<button class="chip" data-v="{h(o.get("v", ""))}" title="{h(o.get("hint", ""))}">{h(o.get("l", ""))}'
        + (f'<span style="color:var(--tc-muted);font-size:11px;margin-left:6px">· {h(o.get("hint", ""))}</span>' if o.get("hint") else "")
        + '</button>'
        for o in sub.get("options", [])
    )
    sub_chips += '<button class="chip chip--ghost" data-v="dont-care">🎲 让 AI 帮我选</button>'

    # === 题 2 · 传播对象 ===
    aud_chips = "".join(
        f'<button class="chip" data-v="{h(o.get("v", ""))}">{h(o.get("l", ""))}</button>'
        for o in aud.get("options", [])
    )
    aud_chips += '<button class="chip chip--ghost" data-v="dont-care">🎲 让 AI 帮我选</button>'

    # === 题 3 · 设计风格 ===
    # tone_cfg.options 为 None/空 → 用内置 TONE_OPTIONS_COMMON + scene 专属（share 加 magazine）
    # tone_cfg.options 有值 → 用 agent 提供的自定义皮肤（如 "婚礼粉/节日红"）
    if tone_cfg.get("options"):
        # agent 动态注入（用于模板外场景）
        tone_chips = "".join(
            f'<button class="chip" data-v="{h(o.get("v", ""))}"'
            + (f' style="box-shadow:inset 0 0 0 2px {h(o.get("accent"))}"' if o.get("accent") else "")
            + f'>{h(o.get("l", ""))}</button>'
            for o in tone_cfg["options"]
        )
    else:
        tone_list = list(TONE_OPTIONS_COMMON)
        if scene == "share":
            tone_list.append(TONE_OPTIONS_MAGAZINE)
        tone_chips = "".join(
            f'<button class="chip" data-v="{h(o.get("v", ""))}">{h(o.get("l", ""))}</button>' for o in tone_list
        )
    # 腾讯系官方：默认常驻
    if tone_cfg.get("include_tencent", True):
        tone_chips += f'<button class="chip chip--tencent" data-v="tencent">{h(TONE_OPTIONS_TENCENT["l"])}</button>'
    tone_chips += '<button class="chip chip--ghost" data-v="dont-care">🎲 让 AI 帮我选</button>'

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>意图补充 · {theme_html}</title><style>{TENCENT_CSS}
.scene-tag{{display:inline-flex;align-items:center;gap:6px;background:var(--tc-blue-50);
  color:var(--tc-blue);padding:5px 12px;border-radius:999px;font-size:12px;font-weight:600;margin-bottom:10px}}
.narrative-hint{{font-size:11px;color:var(--tc-muted);background:var(--tc-bg);padding:2px 6px;
  border-radius:4px;margin-left:6px}}
</style></head>
<body><div class="wrap">
{BRAND_HTML}
<div class="header-block">
  <div class="scene-tag">{scene_emoji} 场景 · {scene_cn}</div>
  <h1><em>{title_html}</em></h1>
  <div class="lead">{hint_html}</div>
</div>

<div class="section card" data-field="sub_intent">
  <div class="section-label">{h(sub.get('label', '意图场景'))}</div>
  <div class="section-hint">{h(sub.get('hint',''))}</div>
  <div class="chip-row">{sub_chips}</div>
</div>

<div class="section card" data-field="audience">
  <div class="section-label">{h(aud.get('label', '传播对象'))}</div>
  <div class="section-hint">{h(aud.get('hint','决定信息密度与语气'))}</div>
  <div class="chip-row">{aud_chips}</div>
</div>

<div class="section card" data-field="tone">
  <div class="section-label">{h(tone_cfg.get('label', '设计风格'))}</div>
  <div class="section-hint">{h(tone_cfg.get('hint','选「腾讯系官方」会为你匹配腾讯蓝+琥珀金主题 + TencentSans 全字体'))}</div>
  <div class="chip-row">{tone_chips}</div>
</div>

<div class="section card" data-field="content">
  <div class="section-label">更多补充（选填但强烈推荐）</div>
  <div class="section-hint">关键成果 / 数字 / 问题 / 下一步 / 你希望读者记住的一句话</div>
  <textarea id="content-text" placeholder="越具体越好。例：本周推进项目 v1，已完成 A/B/C 三件事，DAU 从 5.2k 涨到 6.8k，下期聚焦付费转化..."></textarea>
</div>

<div class="done"><div class="check">✓</div><h3>意图已记录</h3><p>正在为你匹配 3 套最合适的叙事模板...</p>
<div class="done-loader"><div class="done-dots"><span></span><span></span><span></span></div><div class="done-bar"></div></div>
</div>
</div>
<div class="footer"><div class="footer-inner">
  <button class="btn btn--ghost" id="btn-decide">让 AI 全部替我选</button>
  <button class="btn btn--primary" id="btn-continue">匹配模板 →</button>
</div></div>
<script>
window.CURRENT_STAGE="intent_questionnaire";
const THEME={json.dumps(theme, ensure_ascii=False)};
const SCENE={json.dumps(scene)};
document.querySelectorAll(".chip[data-v]").forEach(c=>c.addEventListener("click",()=>{{
  c.closest(".section").querySelectorAll(".chip").forEach(x=>x.classList.remove("is-selected"));
  c.classList.add("is-selected");
}}));
function collect(decideAll){{
  const ans={{theme:THEME,scene:SCENE}};
  document.querySelectorAll(".section[data-field]").forEach(sec=>{{
    const f=sec.dataset.field;
    if(f==="content"){{ans.content=document.getElementById("content-text").value.trim();return;}}
    const sel=sec.querySelector(".chip.is-selected");
    ans[f]=sel?sel.dataset.v:"";
  }});
  if(decideAll){{ans.auto_pick_narrative=true;}}
  // tone=tencent 时同步 skin_pref
  if(ans.tone==="tencent"){{ans.skin_pref="tencent";}}
  return ans;
}}
async function submit(decideAll){{
  const r=await fetch("/submit_intent",{{method:"POST",headers:{{"Content-Type":"application/json"}},
    body:JSON.stringify(collect(decideAll))}});
  if(r.ok){{document.body.classList.add("finished");pollStageAndReload();}}
}}
document.getElementById("btn-continue").addEventListener("click",()=>submit(false));
document.getElementById("btn-decide").addEventListener("click",()=>submit(true));
{STAGE_POLL_JS}
</script></body></html>"""


# ============================================================
# STAGE 3 · 模板选择（3 套叙事 × 封面 + 预览长图按钮 + mock）
# ============================================================

def page_template_choice(theme: str, match_result: dict) -> str:
    top = match_result.get("top", [])
    scene_name = match_result.get("scene_name", "")
    theme_html = h(theme)
    scene_name_html = h(scene_name)

    cards_json = json.dumps(top, ensure_ascii=False)

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>3 套叙事模板 · {theme_html}</title><style>{TENCENT_CSS}
.cards{{display:flex;flex-direction:column;gap:16px}}
.ncard{{background:#fff;border:2px solid var(--tc-line);border-radius:var(--radius-lg);
  overflow:hidden;transition:.2s;position:relative;box-shadow:var(--shadow-card)}}
.ncard:hover{{border-color:var(--tc-blue);transform:translateY(-2px);box-shadow:var(--shadow-pop)}}
.ncard.is-selected{{border-color:var(--tc-blue);box-shadow:0 0 0 3px var(--tc-blue-100),var(--shadow-pop)}}
.ncard-rank{{position:absolute;top:12px;left:12px;z-index:3;background:linear-gradient(135deg,var(--tc-blue),#2B6FF1);
  color:#fff;font-size:12px;font-weight:700;padding:3px 10px;border-radius:8px;
  box-shadow:0 3px 10px rgba(0,82,217,.4)}}
.ncard-thumb{{height:200px;background:linear-gradient(180deg,#F0F4FC,#FFFFFF);overflow:hidden;position:relative;
  display:flex;align-items:center;justify-content:center}}
.ncard-thumb img{{width:100%;height:100%;object-fit:cover;object-position:top;display:block}}
.ncard-thumb .ph{{color:var(--tc-muted);font-size:13px}}
.ncard-body{{padding:16px 18px 18px}}
.ncard-narr{{display:flex;align-items:baseline;gap:10px;margin-bottom:4px}}
.ncard-name{{font-size:17px;font-weight:700;color:var(--tc-ink)}}
.ncard-id{{font-size:11px;color:var(--tc-muted);font-family:"JetBrains Mono",monospace;
  background:var(--tc-bg);padding:2px 6px;border-radius:4px}}
.ncard-intent{{font-size:13px;color:var(--tc-ink-2);margin-bottom:4px}}
.ncard-mock{{font-size:12px;color:var(--tc-muted);margin-bottom:12px;font-style:italic;line-height:1.55;
  padding:8px 10px;background:var(--tc-bg);border-radius:6px;border-left:3px solid var(--tc-blue-100)}}
.skins-label{{font-size:12px;color:var(--tc-ink-2);font-weight:600;margin-bottom:6px}}
.ncard-skins{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}}
.sopt{{display:flex;align-items:center;gap:6px;padding:6px 10px;border-radius:8px;
  border:1.5px solid var(--tc-line);background:#fff;font-size:12px;color:var(--tc-ink-2);transition:.15s;font-weight:500}}
.sopt:hover{{border-color:var(--tc-blue)}}
.sopt.is-rec{{border-color:var(--tc-gold)}}
.sopt.is-selected{{background:var(--tc-blue);color:#fff;border-color:var(--tc-blue);
  box-shadow:0 4px 12px rgba(0,82,217,.25)}}
.sdot{{width:14px;height:14px;border-radius:4px;flex-shrink:0;border:1px solid rgba(0,0,0,.08)}}
.rec-pill{{font-size:10px;background:var(--tc-gold);color:#fff;padding:1px 5px;border-radius:3px;
  margin-left:3px;font-weight:700;letter-spacing:.5px}}
.actions{{display:flex;gap:10px;flex-wrap:wrap}}
.act-btn{{padding:8px 16px;border-radius:var(--radius-sm);font-size:13px;font-weight:600;
  border:none;transition:.15s;display:inline-flex;align-items:center;gap:5px}}
.act-pick{{background:var(--tc-blue);color:#fff;box-shadow:0 2px 6px rgba(0,82,217,.3)}}
.act-pick:hover{{background:var(--tc-blue-600);box-shadow:0 4px 12px rgba(0,82,217,.4)}}
.act-preview{{background:#fff;color:var(--tc-blue);border:1.5px solid var(--tc-line)}}
.act-preview:hover{{border-color:var(--tc-blue);background:var(--tc-blue-50)}}
/* 长图预览 modal */
.modal{{display:none;position:fixed;inset:0;background:rgba(14,31,58,.85);z-index:80;
  align-items:flex-start;justify-content:center;padding:24px;overflow:auto}}
.modal.is-open{{display:flex}}
.modal-inner{{max-width:820px;width:100%;background:#fff;border-radius:var(--radius-lg);
  overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.4);position:relative}}
.modal-head{{position:sticky;top:0;background:#fff;padding:14px 18px;border-bottom:1px solid var(--tc-line);
  display:flex;justify-content:space-between;align-items:center;z-index:2}}
.modal-title{{font-size:14px;font-weight:700;color:var(--tc-ink)}}
.modal-close{{background:transparent;border:none;font-size:22px;color:var(--tc-muted);line-height:1}}
.modal-body{{padding:0}}
.modal-body img{{width:100%;height:auto;display:block}}
.ai-pick-cta{{margin:16px 0 8px;background:linear-gradient(135deg,var(--tc-blue-50) 0%, #fff 60%);
  border:1px dashed var(--tc-blue-100);border-radius:var(--radius-lg);padding:14px 18px}}
.ai-pick-inner{{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}}
.ai-pick-title{{font-size:14px;font-weight:700;color:var(--tc-ink);margin-bottom:2px}}
.ai-pick-sub{{font-size:12px;color:var(--tc-muted)}}
</style></head>
<body><div class="wrap">
{BRAND_HTML}
<div class="header-block">
  <h1>为你匹配的 <em>3 套叙事模板</em></h1>
  <div class="lead">场景：<b>{scene_name}</b> · 每套叙事的信息结构不同，可查看「预览长图」了解完整排版</div>
</div>
<div class="cards" id="cards"></div>

<!-- AI 帮我选 · 兜底入口 -->
<div class="ai-pick-cta">
  <div class="ai-pick-inner">
    <div class="ai-pick-text">
      <div class="ai-pick-title">🎲 选择困难？让 AI 帮你选最合适的那套</div>
      <div class="ai-pick-sub">AI 会综合你的意图 + 场景 + 内容，自动挑选推荐模板和风格</div>
    </div>
    <button class="btn btn--ghost" id="btn-ai-pick">让 AI 帮我选 →</button>
  </div>
</div>

<div class="done"><div class="check">✓</div><h3>已选定模板和风格</h3><p>正在为你拆解内容骨架...</p>
<div class="done-loader"><div class="done-dots"><span></span><span></span><span></span></div><div class="done-bar"></div></div>
</div>
</div>

<div class="modal" id="modal"><div class="modal-inner">
  <div class="modal-head">
    <div class="modal-title" id="modalTitle">预览</div>
    <button class="modal-close" id="modalClose">×</button>
  </div>
  <div class="modal-body" id="modalBody"></div>
</div></div>

<script>
window.CURRENT_STAGE="template_choice";
const DATA={cards_json};

function h(s){{return String(s ?? "").replace(/[&<>\"']/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}})[c]);}}

// 每个叙事一句"代表性 mock 文案"，用于在卡片下方做"长什么样"的口味提示（手写常量，与 mock-data.js 解耦）
const MOCK_HINTS={{
  "pyramid":"建议立项 AI Page 模板库 v1，6 周内 Beta，Q3 覆盖 5k 司内 DAU。结论先行 + 三支柱 MECE + ROI 可交互。",
  "scqa":"现状：PPT 制作耗时成本高 / 冲突：模板割裂叙事被锁死 / 问题：如何解耦 / 答案：场景×叙事×皮肤三层正交。",
  "blm":"市场洞察 → 战略意图 → 创新焦点 → 关键任务 → 正式组织。适配 3-5 年规划级汇报。",
  "prep":"观点-原因-例证-重申。本期推进情况：闭环交付 12 套模板，人效提升 3.2×。",
  "star":"情境-任务-行动-结果。项目复盘：上线首周 DAU 5.2k，满意度 NPS +38。",
  "okr":"O：打造司内汇报基础设施。KR1 覆盖 4 场景 ✓ / KR2 12 叙事 ✓ / KR3 5k DAU 进行中。",
  "pyramid-data":"一句话结论 + 四象限 KPI + 趋势钻取 + 洞察行动。DAU 5.2k(+38%) / 留存 62%(+11%)。",
  "attribution":"现象：付费率下跌 6pt。假设：渠道×人群×价格。验证：价格页转化率下降主导。行动：A/B 新版价格页。",
  "contrast":"基线 vs 实验：新版落地页 CTR +18%，转化率 +6.2%，留存持平，建议全量。",
  "story-arc":"钩子-张力-高潮-回响。从『PPT 时代』到『HTML 报告时代』的一次产品理念迁移。",
  "qa-driven":"Q1 什么是 AI Page？Q2 和 PPT 区别？Q3 如何接入？… 适合培训、FAQ、答疑。",
  "magazine":"封面-引语-章节-尾声。衬线杂志排版，WebGL 背景，最适合沉淀深度长文。"
}};

function render(){{
  const root=document.getElementById("cards");
  root.innerHTML=DATA.map((t,i)=>{{
    const thumb=t.default_thumbnail?`<img src="${{h(t.default_thumbnail)}}" alt="${{h(t.narrative_name)}}" onerror="this.style.display='none';this.parentElement.innerHTML='<div class=ph>${{h(t.narrative_name)}}</div>'">`:`<div class="ph">${{h(t.narrative_name)}}</div>`;
    const skins=(t.available_skins||[]).map(sid=>{{
      const isRec=sid===t.recommended_skin;
      const accent=(t.skin_accents||{{}})[sid]||"#5E6AD2";
      const label=(t.skin_labels||{{}})[sid]||sid;
      return `<button class="sopt ${{isRec?'is-rec is-selected':''}}" data-skin="${{h(sid)}}" data-narr="${{h(t.narrative)}}">
        <span class="sdot" style="background:${{h(accent)}}"></span>${{h(label)}}
        ${{isRec?'<span class="rec-pill">推荐</span>':''}}
      </button>`;
    }}).join("");
    const mockLine=MOCK_HINTS[t.narrative]||t.intent||"";
    return `<div class="ncard" data-narr="${{h(t.narrative)}}">
      <div class="ncard-rank">TOP ${{i+1}}</div>
      <div class="ncard-thumb">${{thumb}}</div>
      <div class="ncard-body">
        <div class="ncard-narr">
          <div class="ncard-name">${{h(t.narrative_name)}}</div>
          <div class="ncard-id">${{h(t.scene)}}/${{h(t.narrative)}}</div>
        </div>
        <div class="ncard-intent">叙事骨架：${{h(t.intent)}}</div>
        <div class="ncard-mock">📄 示例：${{h(mockLine)}}</div>
        <div class="skins-label">设计风格 ${{(t.available_skins||[]).length}} 套可选</div>
        <div class="ncard-skins" data-narr="${{h(t.narrative)}}">${{skins}}</div>
        <div class="actions">
          <button class="act-btn act-pick" data-act="pick" data-narr="${{h(t.narrative)}}">✓ 选择此叙事</button>
          <button class="act-btn act-preview" data-act="preview" data-narr="${{h(t.narrative)}}">🖼 查看预览长图</button>
        </div>
      </div>
    </div>`;
  }}).join("");
  root.addEventListener("click",onClick);
}}

function onClick(e){{
  const skinBtn=e.target.closest(".sopt");
  if(skinBtn){{
    const narr=skinBtn.dataset.narr;
    document.querySelectorAll(`.sopt[data-narr="${{narr}}"]`).forEach(b=>b.classList.remove("is-selected"));
    skinBtn.classList.add("is-selected");
    // 更新封面图
    const card=skinBtn.closest(".ncard");
    const t=DATA.find(x=>x.narrative===narr);
    const sid=skinBtn.dataset.skin;
    if(t&&t.previews&&t.previews[sid]){{
      const img=card.querySelector(".ncard-thumb img");
      if(img){{img.src=t.previews[sid];}}
    }}
    return;
  }}
  const actBtn=e.target.closest("[data-act]");
  if(!actBtn)return;
  const narr=actBtn.dataset.narr;
  const t=DATA.find(x=>x.narrative===narr);
  const card=actBtn.closest(".ncard");
  const selectedSkin=card.querySelector(".sopt.is-selected");
  const skin=selectedSkin?selectedSkin.dataset.skin:t.recommended_skin;
  if(actBtn.dataset.act==="preview"){{
    openPreview(t,skin);
  }}else if(actBtn.dataset.act==="pick"){{
    submitChoice(t,skin);
  }}
}}

function openPreview(t,skin){{
  const modal=document.getElementById("modal");
  const title=document.getElementById("modalTitle");
  const body=document.getElementById("modalBody");
  title.textContent=`${{t.narrative_name}} · ${{(t.skin_labels||{{}})[skin]||skin}} 完整预览`;
  const full=(t.full_previews||{{}})[skin]||t.default_full_preview;
  if(full){{
    body.innerHTML=`<img src="${{h(full)}}" alt="预览" onerror="this.outerHTML='<div style=padding:40px;text-align:center;color:#6A7890>暂无该皮肤的完整预览，可选其他皮肤</div>'">`;
  }}else{{
    body.innerHTML='<div style="padding:40px;text-align:center;color:#6A7890">暂无完整预览</div>';
  }}
  modal.classList.add("is-open");
}}
document.getElementById("modalClose").addEventListener("click",()=>document.getElementById("modal").classList.remove("is-open"));
document.getElementById("modal").addEventListener("click",(e)=>{{if(e.target.id==="modal")document.getElementById("modal").classList.remove("is-open");}});

async function submitChoice(t,skin){{
  const r=await fetch("/choose",{{method:"POST",headers:{{"Content-Type":"application/json"}},
    body:JSON.stringify({{
      scene:t.scene,scene_name:t.scene_name,
      narrative:t.narrative,narrative_name:t.narrative_name,
      skin,skin_label:(t.skin_labels||{{}})[skin]||skin,
      picked_at:new Date().toISOString()
    }})}});
  if(r.ok){{document.body.classList.add("finished");pollStageAndReload();}}
}}

render();

// AI 帮我选：直接提交 DATA[0] + 其推荐皮肤
document.getElementById("btn-ai-pick").addEventListener("click",()=>{{
  if(!DATA||DATA.length===0)return;
  const t=DATA[0];
  submitChoice(t, t.recommended_skin);
}});

{STAGE_POLL_JS}
</script></body></html>"""


# ============================================================
# STAGE 4 · 生成骨架 Loading（缓解等待焦虑）
# ============================================================

def page_skeleton_loading(theme: str, skeleton: dict, scene: str, narrative: str, skin: str) -> str:
    sections = skeleton.get("sections", [])
    narrative_name = skeleton.get("narrative_name", narrative)
    skin_label = skeleton.get("skin_label", skin)
    theme_html = h(theme)
    narrative_name_html = h(narrative_name)
    skin_label_html = h(skin_label)

    def render_step(i, s):
        status = s.get("status", "pending")  # pending / active / done
        if status not in {"pending", "active", "done"}:
            status = "pending"
        emoji = {"pending": "○", "active": "◐", "done": "●"}[status]
        css_class = f"skl-step skl-{status}"
        bullets = "".join(f'<li>{h(b)}</li>' for b in s.get("bullets", []))
        return f'''
        <div class="{css_class}" data-idx="{i}">
          <div class="skl-head">
            <span class="skl-dot">{emoji}</span>
            <span class="skl-num">{i+1:02d}</span>
            <span class="skl-title">{h(s.get("title", ""))}</span>
            <span class="skl-role">{h(s.get("role", ""))}</span>
          </div>
          {f'<ul class="skl-bul">{bullets}</ul>' if bullets else ''}
        </div>
        '''

    steps_html = "".join(render_step(i, s) for i, s in enumerate(sections))

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>正在生成 · {theme_html}</title><style>{TENCENT_CSS}
.skl-hero{{background:linear-gradient(135deg,var(--tc-blue) 0%, #2B6FF1 45%, var(--tc-gold) 180%);
  color:#fff;border-radius:var(--radius-lg);padding:22px 24px;margin-bottom:22px;position:relative;overflow:hidden}}
.skl-hero::before{{content:"";position:absolute;inset:0;
  background:radial-gradient(600px 400px at 90% -20%,rgba(255,255,255,.18),transparent),
             radial-gradient(500px 300px at -10% 120%,rgba(251,174,64,.25),transparent)}}
.skl-hero > *{{position:relative;z-index:1}}
.skl-tag{{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.18);
  backdrop-filter:blur(8px);padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;margin-bottom:8px}}
.skl-hero h2{{font-size:20px;font-weight:700;margin-bottom:4px}}
.skl-hero .skl-meta{{font-size:12px;opacity:.9}}
.skl-progress{{margin-top:14px;height:4px;background:rgba(255,255,255,.25);border-radius:3px;overflow:hidden}}
.skl-progress-bar{{height:100%;background:linear-gradient(90deg,#fff,var(--tc-gold));
  border-radius:3px;animation:skl-sweep 2.4s ease-in-out infinite;width:30%}}
@keyframes skl-sweep{{0%{{margin-left:-30%}}50%{{margin-left:60%}}100%{{margin-left:-30%}}}}

.skl-chain-label{{font-size:12px;font-weight:600;color:var(--tc-muted);letter-spacing:.5px;
  text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;gap:10px}}
.skl-chain-label::before,.skl-chain-label::after{{content:"";flex:1;height:1px;background:var(--tc-line)}}

.skl-step{{background:#fff;border:1px solid var(--tc-line);border-radius:var(--radius-md);
  padding:14px 16px;margin-bottom:10px;transition:.3s;position:relative}}
.skl-step.skl-done{{opacity:.65}}
.skl-step.skl-active{{border-color:var(--tc-blue);box-shadow:0 0 0 3px var(--tc-blue-100);
  background:linear-gradient(180deg,#fff,var(--tc-blue-50))}}
.skl-head{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.skl-dot{{font-size:14px;color:var(--tc-blue);width:18px;display:inline-block}}
.skl-active .skl-dot{{animation:skl-pulse 1.2s ease-in-out infinite}}
@keyframes skl-pulse{{0%,100%{{opacity:.4}}50%{{opacity:1}}}}
.skl-num{{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--tc-muted);
  background:var(--tc-bg);padding:1px 6px;border-radius:3px;font-weight:700}}
.skl-title{{font-size:14px;font-weight:700;color:var(--tc-ink);flex:1}}
.skl-role{{font-size:11px;color:var(--tc-muted);background:var(--tc-blue-50);padding:2px 8px;border-radius:4px;font-weight:600}}
.skl-bul{{margin-top:6px;padding-left:34px;list-style:none}}
.skl-bul li{{font-size:12px;color:var(--tc-ink-2);line-height:1.8;position:relative;padding-left:12px}}
.skl-bul li::before{{content:"→";position:absolute;left:0;color:var(--tc-blue);font-weight:700}}

.skl-principles{{background:linear-gradient(180deg,var(--tc-bg),#fff);border:1px dashed var(--tc-line);
  border-radius:var(--radius-md);padding:14px 16px;margin-top:22px}}
.skl-principles h4{{font-size:13px;font-weight:700;margin-bottom:8px;color:var(--tc-ink)}}
.skl-principles ul{{list-style:none;padding-left:0}}
.skl-principles li{{font-size:12px;color:var(--tc-ink-2);padding:4px 0;padding-left:18px;position:relative}}
.skl-principles li::before{{content:"◆";position:absolute;left:0;color:var(--tc-gold)}}
</style></head>
<body><div class="wrap">
{BRAND_HTML}
<div class="skl-hero">
  <div class="skl-tag">⚡ Generating · 内容骨架已拆解</div>
  <h2>{theme_html}</h2>
  <div class="skl-meta">叙事：{narrative_name_html} · 皮肤：{skin_label_html} · 正在按骨架填入真实内容…</div>
  <div class="skl-progress"><div class="skl-progress-bar"></div></div>
</div>

<div class="skl-chain-label">思维链 · {len(sections)} 步</div>
{steps_html}

<div class="skl-principles">
  <h4>💎 产品化报告四区（HTML 报告的核心理念）</h4>
  <ul>
    <li><b>Overview</b> · 一句话结论 + KPI 卡片 + 当前假设摘要</li>
    <li><b>Controls</b> · 滑块/开关/下拉，支持「如果参数变了会怎样」</li>
    <li><b>Charts</b> · 趋势/结构/敏感性/明细，承接参数变化</li>
    <li><b>Logic</b> · 假设说明 / 计算口径 / 结论解释</li>
  </ul>
</div>
</div>
<script>window.CURRENT_STAGE="skeleton_loading";{STAGE_POLL_JS}</script>
</body></html>"""


# ============================================================
# HTTP Handler
# ============================================================

class RouterHandler(BaseHTTPRequestHandler):
    workdir: str = ""
    theme: str = ""

    @classmethod
    def _state(cls) -> dict:
        try:
            return json.loads(Path(cls.workdir, "state.json").read_text("utf-8"))
        except Exception:
            return {"stage": "scene_probe"}

    def _hdr(self, status=200, ct="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        # 禁用 HTTP 缓存（bfcache 由前端 pageshow 监听器另行处理）
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()

    def do_OPTIONS(self):
        self._hdr(200)

    def do_GET(self):
        path = unquote(self.path).split("?")[0]
        state = self._state()
        stage = state.get("stage", "scene_probe")

        if path == "/stage":
            self._hdr(ct="application/json")
            self.wfile.write(json.dumps(state).encode())
            return

        if path.startswith("/preview/"):
            # 兼容旧链接：302 重定向到 COS（现在前端已直接使用绝对 URL，这里仅做兜底）
            rel = unquote(path[len("/preview/"):])
            if ".." in rel or rel.startswith("/"):
                self._hdr(403)
                self.wfile.write(b"Forbidden")
                return
            # 若 rel 本身已经是绝对 URL（老行为下被双重拼接），尝试直接解析成目标 URL
            if rel.startswith("http://") or rel.startswith("https://"):
                target = rel
            else:
                target = template_source.cos_url(rel)
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            return

        if path == "/" or path == "":
            if stage == "scene_probe":
                probe_scene = state.get("probe_scene", "")
                probe_reason = state.get("probe_reason", "")
                custom_scenes = state.get("custom_scenes", [])
                html = page_scene_probe(self.theme, probe_scene, probe_reason, custom_scenes)
            elif stage == "intent_questionnaire":
                confirm_path = Path(self.workdir, "scene_confirm.json")
                scene = "sync"
                if confirm_path.is_file():
                    scene = json.loads(confirm_path.read_text("utf-8")).get("scene", "sync")
                # 优先读 agent 注入的动态问卷
                dyn_path = Path(self.workdir, "dyn_questionnaire.json")
                dyn_q = None
                if dyn_path.is_file():
                    try:
                        dyn_q = json.loads(dyn_path.read_text("utf-8"))
                    except Exception:
                        dyn_q = None
                html = page_intent_questionnaire(self.theme, scene, dyn_q)
            elif stage == "template_choice":
                mr_path = Path(self.workdir, "match_result.json")
                match_result = json.loads(mr_path.read_text("utf-8")) if mr_path.is_file() else {}
                html = page_template_choice(self.theme, match_result)
            elif stage == "skeleton_loading":
                sk_path = Path(self.workdir, "skeleton.json")
                skeleton = json.loads(sk_path.read_text("utf-8")) if sk_path.is_file() else {"sections": []}
                choice_path = Path(self.workdir, "choice.json")
                choice = json.loads(choice_path.read_text("utf-8")) if choice_path.is_file() else {}
                html = page_skeleton_loading(
                    self.theme, skeleton,
                    choice.get("scene", ""), choice.get("narrative", ""), choice.get("skin_label", "")
                )
            else:
                html = "<h1>Unknown stage</h1>"
            self._hdr()
            self.wfile.write(html.encode("utf-8"))
            return

        self._hdr(404)
        self.wfile.write(b"Not found")

    def do_POST(self):
        path = unquote(self.path).split("?")[0]
        clen = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(clen).decode("utf-8")
        data = json.loads(body) if body else {}

        if path == "/confirm_scene":
            Path(self.workdir, "scene_confirm.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
            self._hdr(ct="application/json")
            self.wfile.write(b'{"ok":true}')
            return

        if path == "/submit_intent":
            Path(self.workdir, "answers.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
            self._hdr(ct="application/json")
            self.wfile.write(b'{"ok":true}')
            return

        if path == "/choose":
            Path(self.workdir, "choice.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
            self._hdr(ct="application/json")
            self.wfile.write(b'{"ok":true}')
            return

        self._hdr(404)
        self.wfile.write(b"Not found")

    def log_message(self, fmt, *args):
        pass


# ============================================================
# CLI
# ============================================================

def cmd_start(args):
    theme = args.theme
    workdir = tempfile.mkdtemp(prefix="smart-page-")
    port = find_port()

    # 支持 --custom-scenes-file：agent 拼 JSON 数组 [{"id":"custom:invitation","emoji":"💌","cn":"邀请函","tagline":"..."}]
    custom_scenes = []
    if getattr(args, "custom_scenes_file", ""):
        p = Path(args.custom_scenes_file)
        if p.is_file():
            try:
                cs = json.loads(p.read_text("utf-8"))
                if isinstance(cs, list):
                    custom_scenes = cs
            except Exception as e:
                print(f"warn: failed to parse custom_scenes_file: {e}", file=sys.stderr)

    state = {
        "stage": "scene_probe",
        "probe_scene": args.probe_scene or "",
        "probe_reason": args.probe_reason or "",
        "custom_scenes": custom_scenes,
    }
    Path(workdir, WORKDIR_MARKER).write_text(WORKDIR_MARKER_VALUE, "utf-8")
    Path(workdir, "state.json").write_text(json.dumps(state, ensure_ascii=False), "utf-8")

    # 使用 subprocess 启动独立守护子进程（避免 os.fork 兼容性问题）
    import time as _time
    env = os.environ.copy()
    env["_SP_DAEMON"] = "1"
    env["_SP_WORKDIR"] = workdir
    env["_SP_PORT"] = str(port)
    env["_SP_THEME"] = theme

    devnull_f = open(os.devnull, "w")
    proc = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "_daemon"],
        stdout=devnull_f,
        stderr=devnull_f,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    devnull_f.close()

    Path(workdir, "server.pid").write_text(str(proc.pid), "utf-8")

    # 等待子进程就绪（最多 5 秒）
    ready = False
    for _ in range(50):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect(("127.0.0.1", port))
                ready = True
                break
        except (ConnectionRefusedError, OSError):
            pass
        if proc.poll() is not None:
            err_path = Path(workdir, "server.error")
            err_msg = err_path.read_text("utf-8") if err_path.is_file() else "daemon exited unexpectedly"
            print(json.dumps({"ok": False, "error": err_msg, "workdir": workdir}, ensure_ascii=False))
            sys.exit(1)
        _time.sleep(0.1)

    if not ready:
        err_path = Path(workdir, "server.error")
        err_msg = err_path.read_text("utf-8") if err_path.is_file() else "timeout waiting for server"
        print(json.dumps({"ok": False, "error": err_msg, "workdir": workdir}, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps({
        "ok": True, "stage": "scene_probe",
        "url": f"http://127.0.0.1:{port}",
        "workdir": workdir, "pid": proc.pid, "theme": theme,
    }, ensure_ascii=False))
    sys.stdout.flush()


def cmd_advance(args):
    workdir = args.workdir
    state_path = Path(workdir, "state.json")
    state = json.loads(state_path.read_text("utf-8"))
    to = args.to

    if to == "intent_questionnaire":
        # 若 agent 提供了 --questionnaire-file，落盘到 workdir/dyn_questionnaire.json
        qf = getattr(args, "questionnaire_file", "")
        if qf:
            src = Path(qf)
            if src.is_file():
                try:
                    # 解析校验一下
                    parsed = json.loads(src.read_text("utf-8"))
                    Path(workdir, "dyn_questionnaire.json").write_text(
                        json.dumps(parsed, ensure_ascii=False, indent=2), "utf-8"
                    )
                except Exception as e:
                    print(f"warn: questionnaire-file invalid JSON: {e}", file=sys.stderr)
            else:
                print(f"warn: questionnaire-file not found: {qf}", file=sys.stderr)
        state["stage"] = "intent_questionnaire"

    elif to == "template_choice":
        # 调用 match.py
        answers_path = Path(workdir, "answers.json")
        proc = subprocess.run(
            [sys.executable, str(HERE / "match.py"), "--answers", str(answers_path), "--top", str(args.top)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(json.dumps({"ok": False, "error": f"match failed: {proc.stderr}"}))
            sys.exit(1)
        match_result = json.loads(proc.stdout)
        Path(workdir, "match_result.json").write_text(json.dumps(match_result, ensure_ascii=False, indent=2), "utf-8")
        state["stage"] = "template_choice"

    elif to == "skeleton_loading":
        if args.skeleton_file and Path(args.skeleton_file).is_file():
            skeleton = json.loads(Path(args.skeleton_file).read_text("utf-8"))
            Path(workdir, "skeleton.json").write_text(json.dumps(skeleton, ensure_ascii=False, indent=2), "utf-8")
        state["stage"] = "skeleton_loading"

    state["version"] = state.get("version", 1) + 1
    state_path.write_text(json.dumps(state), "utf-8")

    out = {"ok": True, "stage": state["stage"], "workdir": workdir, "version": state["version"]}
    if to == "template_choice":
        out["top"] = json.loads(Path(workdir, "match_result.json").read_text("utf-8")).get("top", [])
    print(json.dumps(out, ensure_ascii=False))


def _is_managed_workdir(workdir: str) -> bool:
    path = Path(workdir)
    marker = path / WORKDIR_MARKER
    try:
        return (
            path.is_dir()
            and path.name.startswith("smart-page-")
            and marker.is_file()
            and marker.read_text("utf-8").strip() == WORKDIR_MARKER_VALUE
        )
    except Exception:
        return False


def cmd_stop(args):
    workdir = args.workdir
    if not _is_managed_workdir(workdir):
        print(json.dumps({
            "ok": False,
            "error": "refuse to delete unmarked workdir",
            "workdir": workdir,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)

    pid_path = Path(workdir, "server.pid")
    if pid_path.is_file():
        try:
            os.kill(int(pid_path.read_text().strip()), signal.SIGTERM)
        except (ProcessLookupError, PermissionError, ValueError):
            pass
    import shutil
    shutil.rmtree(workdir, ignore_errors=True)
    print(json.dumps({"ok": True, "stopped": workdir}, ensure_ascii=False))


def _cmd_daemon():
    """由 cmd_start 通过 subprocess.Popen 调用，运行 HTTP 服务器。"""
    workdir = os.environ["_SP_WORKDIR"]
    port = int(os.environ["_SP_PORT"])
    theme = os.environ["_SP_THEME"]

    RouterHandler.workdir = workdir
    RouterHandler.theme = theme
    try:
        server = HTTPServer(("127.0.0.1", port), RouterHandler)
        Path(workdir, "server.pid").write_text(str(os.getpid()), "utf-8")
        server.serve_forever()
    except Exception as e:
        Path(workdir, "server.error").write_text(str(e), "utf-8")
        sys.exit(1)


def main():
    # 隐式 _daemon 子命令（由 cmd_start 内部通过 subprocess 调用）
    if len(sys.argv) >= 2 and sys.argv[1] == "_daemon":
        _cmd_daemon()
        return

    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("start")
    ps.add_argument("--theme", required=True)
    ps.add_argument("--probe-scene", default="", help="AI 预判的场景 id（4 模板场景之一 或 custom:xxx）")
    ps.add_argument("--probe-reason", default="", help="AI 预判的理由")
    ps.add_argument("--custom-scenes-file", default="",
                    help='JSON 文件路径，内容形如 [{"id":"custom:invitation","emoji":"💌","cn":"邀请函","tagline":"..."}]')

    pa = sub.add_parser("advance")
    pa.add_argument("workdir")
    pa.add_argument("--to", required=True, choices=["intent_questionnaire", "template_choice", "skeleton_loading"])
    pa.add_argument("--top", type=int, default=3)
    pa.add_argument("--skeleton-file", default="", help="skeleton_loading 时的骨架 JSON 文件")
    pa.add_argument("--questionnaire-file", default="",
                    help='intent_questionnaire 时 agent 注入的动态问卷 JSON 路径')

    pt = sub.add_parser("stop")
    pt.add_argument("workdir")

    args = p.parse_args()
    if args.cmd == "start": cmd_start(args)
    elif args.cmd == "advance": cmd_advance(args)
    elif args.cmd == "stop": cmd_stop(args)
    else: p.print_help(); sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_material.py — 把代表名片信息 + 内容数据渲染成手机竖版 HTML 简报单页。

用法：
  python3 render_material.py --content content.json --out 物料_最新研究_20260628.html [--profile ~/.workbuddy/med-rep-profile.json]

content.json 结构（v2，更丰富的简报版式）：
{
  "type": "research",              // greeting | news | research | education
  "column": "最新研究研读",         // 刊头栏目名（可选，按类型有默认）
  "issue": "第 12 期",             // 期号（可选）
  "headline": "度普利尤单抗治疗中重度特应性皮炎研究研读",
  "gen_date": "2026-06-28",        // 生成日期（可选，缺省取今天）
  "fresh_tag": "报告研读",          // 新鲜度后缀词（可选，按类型有默认，如"报告研读"/"热点速递"）
  "recipient": {"dept": "肿瘤科", "name": "张三大夫"},  // 发送对象（可选）→ 刊头显示"致：肿瘤科 张三大夫"
  "lead": "（可选）开场导语，代表对医生说话的口吻，一段话",
  "sections": [                    // 推荐：分板块；每板块多个条目
    {
      "name": "疗效证据",
      "items": [
        {
          "title": "SOLO 长期随访数据",
          "rows": [                // 多行结构化信息，lbl 为标签
            {"lbl": "研究", "val": "一项 3 年长期随访..."},
            {"lbl": "发现", "val": "疾病控制率维持稳定..."},
            {"lbl": "临床意义", "val": "支持长期规范化用药..."}
          ],
          "src": "JAMA Dermatol, 2026"
        }
      ]
    }
  ],
  "items": [...],                  // 兼容旧版：无 sections 时用扁平 items（每项 title/text/src）
  "greeting": { "festival":"端午安康", "lines":["...","..."] },  // type=greeting 专用
  "summary": "本期小结：规范化用药下长期获益证据持续积累。"  // 可选
}
"""
import argparse, base64, datetime, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "templates" / "material_template.html"
GREETING_TEMPLATE = HERE.parent / "templates" / "greeting_template.html"
CARD_TEMPLATE = HERE.parent / "templates" / "card_template.html"
CARD_H_TEMPLATE = HERE.parent / "templates" / "card_h_template.html"
HTML2CANVAS_JS = HERE.parent / "templates" / "html2canvas.min.js"

def load_html2canvas():
    """读取 html2canvas 源码用于内联，确保离线/微信内置浏览器也能导出。"""
    try:
        return HTML2CANVAS_JS.read_text(encoding="utf-8")
    except Exception:
        # 兜底：内联失败则回退 CDN（在线环境仍可用）
        return ('document.write(\'<scr\'+\'ipt src="https://cdn.jsdelivr.net/npm/'
                'html2canvas@1.4.1/dist/html2canvas.min.js"></scr\'+\'ipt>\');')

TYPE_DEFAULTS = {
    "greeting":  {"column": "节日问候", "fresh": "诚挚祝福"},
    "news":      {"column": "行业热点速递", "fresh": "热点速递"},
    "research":  {"column": "最新研究研读", "fresh": "报告研读"},
    "education": {"column": "学术科普", "fresh": "学术科普"},
}

# 节日氛围配色：scene 渐变 a→b + 主题金/亮色。按节日关键词匹配，缺省走通用夜色。
FESTIVAL_THEMES = {
    "生日": {"a": "#b5377e", "b": "#e8769b", "gold": "#FFE08A"},
    "中秋": {"a": "#1a2a52", "b": "#3a4f8a", "gold": "#FFD27A"},
    "春节": {"a": "#7a0e16", "b": "#b81d28", "gold": "#FFD86B"},
    "新年": {"a": "#7a0e16", "b": "#b81d28", "gold": "#FFD86B"},
    "元旦": {"a": "#7a0e16", "b": "#b81d28", "gold": "#FFD86B"},
    "端午": {"a": "#155a4a", "b": "#2e8b6e", "gold": "#E9D58A"},
    "国庆": {"a": "#8a1216", "b": "#c0212a", "gold": "#FFD86B"},
    "教师节": {"a": "#243a78", "b": "#3f63b8", "gold": "#FFD27A"},
    "医师节": {"a": "#143a6b", "b": "#2668EB", "gold": "#9FD0FF"},
    "元宵": {"a": "#7a0e16", "b": "#b81d28", "gold": "#FFD86B"},
    "清明": {"a": "#2e5a4a", "b": "#5a8a78", "gold": "#E9E0C0"},
    "重阳": {"a": "#7a3a12", "b": "#b8702a", "gold": "#FFD27A"},
    "建党": {"a": "#8a1216", "b": "#c41e2a", "gold": "#FFD86B"},
}
DEFAULT_FESTIVAL_THEME = {"a": "#1a2a52", "b": "#3a4f8a", "gold": "#FFD27A"}

# 节日对应的日期显示文本（仅贺卡用）。生日无默认日期（需代表输入或不显示）。
FESTIVAL_DATES = {
    "中秋": "农历八月十五",
    "春节": "农历正月初一",
    "新年": "农历正月初一",
    "元旦": "公历一月一日",
    "端午": "农历五月初五",
    "元宵": "农历正月十五",
    "清明": "四月清明时节",
    "重阳": "农历九月初九",
    "国庆": "十月一日",
    "教师节": "九月十日",
    "医师节": "八月十九日",
    "建党": "七月一日",
}

# 节日装饰 SVG（内联，用于贺卡主视觉区右上角）
FESTIVAL_DECOR_SVG = {
    "中秋": '''<svg class="decor-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <!-- 圆月 -->
  <circle cx="60" cy="42" r="28" fill="url(#moonGrad)" opacity=".95"/>
  <defs><radialGradient id="moonGrad" cx="40%" cy="35%"><stop offset="0%" stop-color="#FFFDE8"/><stop offset="70%" stop-color="#FFD27A"/><stop offset="100%" stop-color="#F5C34B"/></radialGradient></defs>
  <!-- 月亮环形光晕 -->
  <circle cx="60" cy="42" r="32" fill="none" stroke="rgba(255,210,122,.3)" stroke-width="2"/>
  <!-- 玉兔剪影 -->
  <g transform="translate(42,72) scale(.6)" fill="rgba(255,255,255,.85)">
    <ellipse cx="20" cy="22" rx="12" ry="14"/>
    <ellipse cx="20" cy="8" rx="7" ry="9"/>
    <ellipse cx="15" cy="-2" rx="2.5" ry="7" transform="rotate(-15 15 -2)"/>
    <ellipse cx="25" cy="-2" rx="2.5" ry="7" transform="rotate(15 25 -2)"/>
    <circle cx="17" cy="6" r="1.2" fill="#e8769b"/>
    <circle cx="23" cy="6" r="1.2" fill="#e8769b"/>
  </g>
</svg>''',
    "春节": '''<svg class="decor-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <!-- 灯笼 -->
  <g transform="translate(60,10)">
    <rect x="-3" y="0" width="6" height="10" rx="2" fill="#FFD86B"/>
    <ellipse cx="0" cy="40" rx="20" ry="28" fill="#FF3B3B" opacity=".9"/>
    <ellipse cx="0" cy="40" rx="20" ry="28" fill="url(#lanternGrad)"/>
    <rect x="-12" y="12" width="24" height="4" rx="2" fill="#FFD86B"/>
    <rect x="-12" y="64" width="24" height="4" rx="2" fill="#FFD86B"/>
    <rect x="-1" y="20" width="2" height="40" fill="rgba(255,216,107,.5)"/>
    <line x1="0" y1="68" x2="0" y2="82" stroke="#FFD86B" stroke-width="2"/>
    <circle cx="0" cy="84" r="3" fill="#FFD86B"/>
  </g>
  <defs><radialGradient id="lanternGrad" cx="35%" cy="30%"><stop offset="0%" stop-color="rgba(255,255,255,.3)"/><stop offset="100%" stop-color="transparent"/></radialGradient></defs>
  <!-- 烟花点缀 -->
  <g transform="translate(20,85)" fill="none" stroke="#FFD86B" stroke-width="1" opacity=".7">
    <line x1="0" y1="0" x2="-6" y2="-8"/><line x1="0" y1="0" x2="6" y2="-8"/>
    <line x1="0" y1="0" x2="-8" y2="0"/><line x1="0" y1="0" x2="0" y2="-10"/>
    <circle cx="-6" cy="-8" r="1.5" fill="#FFD86B"/><circle cx="6" cy="-8" r="1.5" fill="#FFD86B"/>
  </g>
</svg>''',
    "新年": None,  # 复用春节
    "元旦": None,  # 复用春节
    "端午": '''<svg class="decor-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <!-- 粽子 -->
  <g transform="translate(60,20)">
    <polygon points="0,-5 -22,35 22,35" fill="#4a7a5a" stroke="#2e5a3a" stroke-width="1.5"/>
    <polygon points="0,-5 -22,35 22,35" fill="url(#zongGrad)"/>
    <line x1="-5" y1="-8" x2="0" y2="-5" stroke="#6b8f6b" stroke-width="2"/>
    <line x1="5" y1="-10" x2="0" y2="-5" stroke="#6b8f6b" stroke-width="2"/>
    <line x1="-11" y1="15" x2="11" y2="15" stroke="#E9D58A" stroke-width="2.5"/>
    <line x1="0" y1="0" x2="0" y2="32" stroke="#E9D58A" stroke-width="2.5"/>
  </g>
  <defs><radialGradient id="zongGrad" cx="40%" cy="30%"><stop offset="0%" stop-color="rgba(255,255,255,.15)"/><stop offset="100%" stop-color="transparent"/></radialGradient></defs>
  <!-- 波纹 -->
  <g transform="translate(20,80)" fill="none" stroke="rgba(233,213,138,.4)" stroke-width="1.5">
    <path d="M0,0 Q15,-8 30,0 Q45,8 60,0"/><path d="M5,10 Q20,2 35,10 Q50,18 65,10"/>
  </g>
</svg>''',
    "生日": '''<svg class="decor-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <!-- 蛋糕 -->
  <g transform="translate(60,25)">
    <!-- 底层 -->
    <rect x="-28" y="40" width="56" height="30" rx="6" fill="#F8E0E6"/>
    <rect x="-28" y="40" width="56" height="30" rx="6" fill="url(#cakeGrad)"/>
    <!-- 上层 -->
    <rect x="-20" y="20" width="40" height="24" rx="5" fill="#FFF0F3"/>
    <!-- 奶油滴 -->
    <path d="M-20,20 Q-18,26 -14,20 Q-10,26 -6,20 Q-2,26 2,20 Q6,26 10,20 Q14,26 18,20 Q20,26 20,20" fill="#fff" opacity=".8"/>
    <!-- 蜡烛 -->
    <rect x="-2" y="6" width="4" height="16" rx="1.5" fill="#FFB6C1"/>
    <ellipse cx="0" cy="4" rx="3" ry="4.5" fill="#FFDD44"/>
    <ellipse cx="0" cy="3" rx="1.5" ry="2.5" fill="#FFF8E0"/>
    <!-- 装饰 -->
    <circle cx="-12" cy="52" r="2.5" fill="#FFB6C1"/><circle cx="0" cy="55" r="2" fill="#FFD86B"/>
    <circle cx="12" cy="52" r="2.5" fill="#B6E0FF"/>
  </g>
  <defs><radialGradient id="cakeGrad" cx="50%" cy="30%"><stop offset="0%" stop-color="rgba(255,255,255,.2)"/><stop offset="100%" stop-color="transparent"/></radialGradient></defs>
  <!-- 彩带 -->
  <g fill="none" stroke-width="1.5" opacity=".6">
    <path d="M15,95 Q20,85 25,95 Q30,105 35,95" stroke="#FFB6C1"/>
    <path d="M75,90 Q80,80 85,90 Q90,100 95,90" stroke="#B6E0FF"/>
  </g>
</svg>''',
    "国庆": '''<svg class="decor-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <!-- 五角星 -->
  <g transform="translate(60,45)">
    <polygon points="0,-24 6,-8 24,-8 10,4 16,22 0,12 -16,22 -10,4 -24,-8 -6,-8"
             fill="#FFD86B" opacity=".9"/>
  </g>
  <!-- 烟花 -->
  <g transform="translate(25,80)" fill="none" stroke="#FFD86B" stroke-width="1.2" opacity=".6">
    <line x1="0" y1="0" x2="-8" y2="-10"/><line x1="0" y1="0" x2="8" y2="-10"/>
    <line x1="0" y1="0" x2="-10" y2="2"/><line x1="0" y1="0" x2="10" y2="2"/>
    <line x1="0" y1="0" x2="0" y2="-12"/>
  </g>
  <g transform="translate(95,75)" fill="none" stroke="#FF6B6B" stroke-width="1.2" opacity=".6">
    <line x1="0" y1="0" x2="-6" y2="-8"/><line x1="0" y1="0" x2="6" y2="-8"/>
    <line x1="0" y1="0" x2="-8" y2="3"/><line x1="0" y1="0" x2="8" y2="3"/>
    <line x1="0" y1="0" x2="0" y2="-10"/>
  </g>
</svg>''',
    "建党": '''<svg class="decor-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <!-- 党徽五角星 -->
  <g transform="translate(60,45)">
    <polygon points="0,-26 7,-9 26,-9 11,3 17,22 0,12 -17,22 -11,3 -26,-9 -7,-9"
             fill="#FFD86B" opacity=".9"/>
    <circle cx="0" cy="3" r="6" fill="none" stroke="#FFD86B" stroke-width="1.5" opacity=".7"/>
  </g>
  <!-- 光芒 -->
  <g transform="translate(60,45)" fill="none" stroke="rgba(255,216,107,.4)" stroke-width="1">
    <line x1="0" y1="-30" x2="0" y2="-38"/><line x1="28" y1="-10" x2="34" y2="-14"/>
    <line x1="-28" y1="-10" x2="-34" y2="-14"/><line x1="18" y1="22" x2="22" y2="28"/>
    <line x1="-18" y1="22" x2="-22" y2="28"/>
  </g>
</svg>''',
    "元宵": None,  # 复用春节
    "教师节": '''<svg class="decor-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <!-- 书本 -->
  <g transform="translate(60,50)">
    <path d="M-25,0 Q0,-10 25,0 L25,30 Q0,20 -25,30 Z" fill="rgba(255,255,255,.2)" stroke="rgba(255,255,255,.4)" stroke-width="1.5"/>
    <line x1="0" y1="-5" x2="0" y2="25" stroke="rgba(255,255,255,.3)" stroke-width="1"/>
    <path d="M-15,8 L-5,6" stroke="rgba(255,210,122,.5)" stroke-width="1.5"/>
    <path d="M-15,14 L-5,12" stroke="rgba(255,210,122,.5)" stroke-width="1.5"/>
    <path d="M5,6 L15,8" stroke="rgba(255,210,122,.5)" stroke-width="1.5"/>
  </g>
</svg>''',
    "医师节": '''<svg class="decor-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <!-- 听诊器 -->
  <g transform="translate(60,40)" fill="none" stroke="rgba(159,208,255,.7)" stroke-width="2.5">
    <path d="M-12,-20 C-12,5 -20,15 -20,25 C-20,35 -10,40 0,40 C10,40 20,35 20,25 C20,15 12,5 12,-20"/>
    <circle cx="-12" cy="-20" r="4" fill="rgba(159,208,255,.5)"/>
    <circle cx="12" cy="-20" r="4" fill="rgba(159,208,255,.5)"/>
    <circle cx="0" cy="44" r="8" fill="rgba(159,208,255,.3)" stroke="rgba(159,208,255,.7)"/>
  </g>
</svg>''',
}

def pick_festival_theme(festival):
    for k, v in FESTIVAL_THEMES.items():
        if k in (festival or ""):
            return v
    return DEFAULT_FESTIVAL_THEME

def pick_festival_date(festival, content):
    """贺卡日期逻辑：节日→对应传统日期；生日→content提供或空。"""
    # 优先使用 content 中明确指定的日期
    if content.get("fest_date"):
        return content["fest_date"]
    # 生日：不显示日期（需代表提供）
    if is_birthday(festival, content):
        return ""
    # 节日：查表
    for k, d in FESTIVAL_DATES.items():
        if k in (festival or ""):
            return d
    return ""

def pick_decor_svg(festival, content):
    """按节日选择装饰 SVG。"""
    if is_birthday(festival, content):
        return FESTIVAL_DECOR_SVG.get("生日", "")
    for k, svg in FESTIVAL_DECOR_SVG.items():
        if k in (festival or ""):
            if svg is None:
                # 复用：新年/元旦→春节，元宵→春节
                return FESTIVAL_DECOR_SVG.get("春节", "")
            return svg
    return ""

def is_birthday(festival, content):
    """判断是否生日贺卡：festival 含'生日'或 content.occasion=='birthday'。"""
    if content.get("occasion") == "birthday":
        return True
    return "生日" in (festival or "")

def img_to_data_uri(path):
    if not path:
        return ""
    p = Path(os.path.expanduser(path))
    if not p.exists():
        return ""
    ext = p.suffix.lower().lstrip(".") or "png"
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "png")
    data = base64.b64encode(p.read_bytes()).decode()
    return f"data:image/{mime};base64,{data}"

def _mix(c, target, t):
    return round(c + (target - c) * t)

def hex_variants(hex_color):
    """返回 (soft 很浅同色, deep 加深同色)。"""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        h = "2668EB"
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    soft = f"#{_mix(r,255,.88):02x}{_mix(g,255,.88):02x}{_mix(b,255,.88):02x}"
    deep = f"#{_mix(r,0,.32):02x}{_mix(g,0,.32):02x}{_mix(b,0,.32):02x}"
    return soft, deep

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def build_item(it, idx):
    """渲染单个条目，支持 rows 多行结构或 text 单段。"""
    head = (f'<div class="item-head"><div class="item-no">{idx}</div>'
            f'<div class="item-title">{esc(it.get("title",""))}</div></div>')
    rows = ""
    if it.get("rows"):
        for r in it["rows"]:
            rows += (f'<div class="row"><span class="lbl">{esc(r.get("lbl",""))}</span>'
                     f'<span class="val">{esc(r.get("val",""))}</span></div>')
    elif it.get("text"):
        rows += f'<div class="row"><span class="val">{esc(it["text"])}</span></div>'
    src = f'<div class="src">来源：{esc(it["src"])}</div>' if it.get("src") else ""
    return f'<div class="item">{head}{rows}{src}</div>'

def build_content_html(c):
    t = c.get("type", "news")
    if t == "greeting":
        g = c.get("greeting", {})
        lines = "".join(f"<p>{esc(l)}</p>" for l in g.get("lines", []))
        fest = esc(g.get("festival", ""))
        return f'<div class="greeting"><div class="festival">{fest}</div>{lines}</div>'

    html = ""
    # 优先 sections 分板块
    if c.get("sections"):
        for sec in c["sections"]:
            items = "".join(build_item(it, i + 1) for i, it in enumerate(sec.get("items", [])))
            html += (f'<div class="section"><div class="sec-head"><div class="sec-bar"></div>'
                     f'<div class="sec-name">{esc(sec.get("name",""))}</div></div>{items}</div>')
    elif c.get("items"):
        items = "".join(build_item(it, i + 1) for i, it in enumerate(c["items"]))
        html += f'<div class="section">{items}</div>'
    return html

def build_contact_html(profile):
    parts = []
    if profile.get("phone"):
        parts.append(f'<div class="c-row"><span class="lbl">📞 电话</span>{esc(profile["phone"])}</div>')
    if profile.get("email"):
        parts.append(f'<div class="c-row"><span class="lbl">✉ 邮箱</span>{esc(profile["email"])}</div>')
    return "".join(parts)

def render_card(profile, brand, brand_soft, brand_deep, basename, out_path, layout="v"):
    """渲染代表本人的电子名片。layout='v' 竖版独立卡，'h' 横版（简报名片头样式）。"""
    avatar_uri = img_to_data_uri(profile.get("avatarPath"))
    if avatar_uri:
        avatar_html = f'<img class="avatar" src="{avatar_uri}" alt="">'
    else:
        avatar_html = f'<div class="avatar">{esc((profile.get("name") or "?")[0])}</div>'

    qr_uri = img_to_data_uri(profile.get("qrcodePath"))
    if qr_uri:
        qr_html = f'<img class="qr" src="{qr_uri}" alt="微信二维码">'
    else:
        qr_html = '<div class="qr">微信<br>二维码<br>待添加</div>'

    contact_rows = []
    if profile.get("phone"):
        contact_rows.append(f'<div class="c-row"><span class="ico">📞</span>{esc(profile["phone"])}</div>'
                            if layout == "v" else
                            f'<div class="c-row">📞 {esc(profile["phone"])}</div>')
    if profile.get("email"):
        contact_rows.append(f'<div class="c-row"><span class="ico">✉</span>{esc(profile["email"])}</div>'
                            if layout == "v" else
                            f'<div class="c-row">✉ {esc(profile["email"])}</div>')
    contact_html = "".join(contact_rows)

    if layout == "h":
        title_html = f'<span class="title">{esc(profile["title"])}</span>' if profile.get("title") else ""
        tpl = CARD_H_TEMPLATE.read_text(encoding="utf-8")
        repl = {
            "{{TITLE}}": esc((profile.get("name") or "") + " 电子名片"),
            "{{BRAND_COLOR}}": brand, "{{BRAND_SOFT}}": brand_soft, "{{BRAND_DEEP}}": brand_deep,
            "{{AVATAR_HTML}}": avatar_html, "{{QR_HTML}}": qr_html,
            "{{NAME}}": esc(profile.get("name", "")), "{{TITLE_HTML}}": title_html,
            "{{COMPANY}}": esc(profile.get("company", "")),
            "{{CONTACT_HTML}}": contact_html,
            "{{FILING_NO}}": esc(profile.get("filingNo", "—")),
            "{{FILE_BASENAME}}": basename,
        }
    else:
        title_tag = f'<div class="title-tag">{esc(profile["title"])}</div>' if profile.get("title") else ""
        tpl = CARD_TEMPLATE.read_text(encoding="utf-8")
        repl = {
            "{{TITLE}}": esc((profile.get("name") or "") + " 电子名片"),
            "{{BRAND_COLOR}}": brand, "{{BRAND_SOFT}}": brand_soft, "{{BRAND_DEEP}}": brand_deep,
            "{{AVATAR_HTML}}": avatar_html, "{{QR_HTML}}": qr_html,
            "{{NAME}}": esc(profile.get("name", "")), "{{TITLE_TAG}}": title_tag,
            "{{COMPANY}}": esc(profile.get("company", "")),
            "{{CONTACT_HTML}}": contact_html,
            "{{FILING_NO}}": esc(profile.get("filingNo", "—")),
            "{{FILE_BASENAME}}": basename,
        }
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    tpl = tpl.replace("{{HTML2CANVAS_INLINE}}", load_html2canvas())
    Path(out_path).write_text(tpl, encoding="utf-8")


def render_greeting(content, profile, brand, brand_soft, brand_deep,
                    gen_date, rcp_text, basename, out_path):
    g = content.get("greeting", {})
    festival = g.get("festival", content.get("headline", "节日快乐"))
    theme = pick_festival_theme(festival)
    birthday = is_birthday(festival, content)

    # 节日装饰 SVG（按节日自动匹配）
    decor_html = pick_decor_svg(festival, content)

    # 节日日期（不再用当前生成日期）
    fest_date = pick_festival_date(festival, content)

    # 祝福语：第一行若以"："结尾则作为称呼(salut)，其余为正文
    lines = list(g.get("lines", []))
    salut_html = ""
    if lines and (lines[0].rstrip().endswith("：") or lines[0].rstrip().endswith(":")):
        salut_html = f'<div class="salut">{esc(lines.pop(0))}</div>'
    wishes_body = "".join(f"<p>{esc(l)}</p>" for l in lines)
    wishes_html = salut_html + wishes_body

    # 精简名片：头像
    avatar_uri = img_to_data_uri(profile.get("avatarPath"))
    if avatar_uri:
        mc_avatar = f'<img class="mc-avatar" src="{avatar_uri}" alt="">'
    else:
        mc_avatar = f'<div class="mc-avatar">{esc((profile.get("name") or "?")[0])}</div>'
    # 精简名片：二维码
    qr_uri = img_to_data_uri(profile.get("qrcodePath"))
    if qr_uri:
        mc_qr = f'<img class="mc-qr" src="{qr_uri}" alt="微信二维码">'
    else:
        mc_qr = '<div class="mc-qr">微信<br>二维码</div>'
    # 精简名片：联系方式（电话、邮箱各一行，带图标）
    contact_rows = []
    if profile.get("phone"):
        contact_rows.append(f'<div class="c-row">📞 {esc(profile["phone"])}</div>')
    if profile.get("email"):
        contact_rows.append(f'<div class="c-row">✉ {esc(profile["email"])}</div>')
    mc_contact = "".join(contact_rows)

    # 精简名片：备案号行
    filing_no = profile.get("filingNo", "")
    mc_filing = (f'<div class="mc-filing">医药代表备案号：<b>{esc(filing_no)}</b></div>'
                 if filing_no else "")

    recipient_line = f'致 {esc(rcp_text)}' if rcp_text else '诚挚祝福'

    tpl = GREETING_TEMPLATE.read_text(encoding="utf-8")
    repl = {
        "{{TITLE}}": esc(festival),
        "{{BRAND_COLOR}}": brand,
        "{{BRAND_SOFT}}": brand_soft,
        "{{BRAND_DEEP}}": brand_deep,
        "{{FEST_A}}": theme["a"],
        "{{FEST_B}}": theme["b"],
        "{{FEST_GOLD}}": theme["gold"],
        "{{DECOR_HTML}}": decor_html,
        "{{RECIPIENT_LINE}}": esc(recipient_line),
        "{{FESTIVAL}}": esc(festival),
        "{{FEST_DATE}}": esc(fest_date),
        "{{WISHES_HTML}}": wishes_html,
        "{{NAME}}": esc(profile.get("name", "")),
        "{{COMPANY}}": esc(profile.get("company", "")),
        "{{MC_AVATAR}}": mc_avatar,
        "{{MC_QR}}": mc_qr,
        "{{MC_CONTACT}}": mc_contact,
        "{{MC_FILING}}": mc_filing,
        "{{FILING_NO}}": esc(profile.get("filingNo", "—")),
        "{{FILE_BASENAME}}": basename,
    }
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    # html2canvas 内联（最后替换，避免源码中出现 {{}} 被误伤）
    tpl = tpl.replace("{{HTML2CANVAS_INLINE}}", load_html2canvas())
    Path(out_path).write_text(tpl, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", default="~/.workbuddy/med-rep-profile.json")
    args = ap.parse_args()

    content = json.loads(Path(args.content).read_text(encoding="utf-8"))
    prof_path = Path(os.path.expanduser(args.profile))
    if not prof_path.exists():
        print(f"ERROR: profile not found at {prof_path}. 请先创建代表名片信息文件。", file=sys.stderr)
        sys.exit(2)
    profile = json.loads(prof_path.read_text(encoding="utf-8"))

    t = content.get("type", "news")
    defaults = TYPE_DEFAULTS.get(t, TYPE_DEFAULTS["news"])

    brand = profile.get("brandColor") or "#2668EB"
    brand_soft, brand_deep = hex_variants(brand)

    gen_date = content.get("gen_date") or datetime.date.today().isoformat()
    fresh_tag = content.get("fresh_tag") or defaults["fresh"]
    column = content.get("column") or defaults["column"]
    issue = content.get("issue", "")

    # 发送对象抬头
    rcp = content.get("recipient") or {}
    rcp_text = " ".join(x for x in [rcp.get("dept", ""), rcp.get("name", "")] if x).strip()
    recipient_html = f'<div class="recipient">✉ 致：{esc(rcp_text)}</div>' if rcp_text else ""

    basename = Path(args.out).stem

    # ===== 电子名片：一次生成竖版 + 横版两张 =====
    if t == "card":
        out = Path(args.out)
        stem = out.stem
        v_path = out.with_name(f"{stem}_竖版{out.suffix}")
        h_path = out.with_name(f"{stem}_横版{out.suffix}")
        render_card(profile, brand, brand_soft, brand_deep, v_path.stem, str(v_path), layout="v")
        render_card(profile, brand, brand_soft, brand_deep, h_path.stem, str(h_path), layout="h")
        print(f"OK: {v_path}")
        print(f"OK: {h_path}")
        return

    # ===== 节日问候卡：走专属"贺卡风"模板 =====
    if t == "greeting":
        render_greeting(content, profile, brand, brand_soft, brand_deep,
                        gen_date, rcp_text, basename, args.out)
        print(f"OK: {args.out}")
        return

    # 头像
    avatar_uri = img_to_data_uri(profile.get("avatarPath"))
    if avatar_uri:
        avatar_html = f'<img class="avatar" src="{avatar_uri}" alt="">'
    else:
        initial = esc((profile.get("name") or "?")[0])
        avatar_html = f'<div class="avatar">{initial}</div>'

    # 二维码
    qr_uri = img_to_data_uri(profile.get("qrcodePath"))
    if qr_uri:
        qr_html = f'<img class="qr" src="{qr_uri}" alt="微信二维码">'
    else:
        qr_html = '<div class="qr">微信<br>二维码<br>待添加</div>'

    title_html = f'<span class="title">{esc(profile["title"])}</span>' if profile.get("title") else ""

    # 名片内备案号行
    filing_no = profile.get("filingNo", "")
    filing_line_html = (f'<div class="filing-line">🪪 医药代表备案号：<b>{esc(filing_no)}</b></div>'
                        if filing_no else "")

    # 导语
    lead_html = f'<div class="lead">{esc(content["lead"])}</div>' if content.get("lead") else ""
    # 小结
    summary_html = ""
    if content.get("summary"):
        summary_html = (f'<div class="summary"><div class="s-title">📌 本期小结</div>'
                        f'<p>{esc(content["summary"])}</p></div>')

    basename = Path(args.out).stem

    tpl = TEMPLATE.read_text(encoding="utf-8")
    repl = {
        "{{TITLE}}": esc(content.get("headline", "医疗简报")),
        "{{BRAND_COLOR}}": brand,
        "{{BRAND_SOFT}}": brand_soft,
        "{{BRAND_DEEP}}": brand_deep,
        "{{AVATAR_HTML}}": avatar_html,
        "{{COMPANY}}": esc(profile.get("company", "")),
        "{{NAME}}": esc(profile.get("name", "")),
        "{{TITLE_HTML}}": title_html,
        "{{QR_HTML}}": qr_html,
        "{{CONTACT_HTML}}": build_contact_html(profile),
        "{{FILING_LINE_HTML}}": filing_line_html,
        "{{COLUMN}}": esc(column),
        "{{ISSUE}}": esc(issue),
        "{{RECIPIENT_HTML}}": recipient_html,
        "{{HEADLINE}}": esc(content.get("headline", "")),
        "{{GEN_DATE}}": esc(gen_date),
        "{{FRESH_TAG}}": esc(fresh_tag),
        "{{LEAD_HTML}}": lead_html,
        "{{CONTENT_HTML}}": build_content_html(content),
        "{{SUMMARY_HTML}}": summary_html,
        "{{FILING_NO}}": esc(profile.get("filingNo", "—")),
        "{{FILE_BASENAME}}": basename,
    }
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    tpl = tpl.replace("{{HTML2CANVAS_INLINE}}", load_html2canvas())

    Path(args.out).write_text(tpl, encoding="utf-8")
    print(f"OK: {args.out}")

if __name__ == "__main__":
    main()

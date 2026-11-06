# -*- coding: utf-8 -*-
"""把 exam_analysis.py 产出的 analysis.json 渲染成排版规范的 HTML 报告。

用法::

    python report_builder.py --analysis analysis.json --out 报告.html \
        --exam-name "高二期中考试" --narrative narrative.json

* 图表全部内联为 SVG，报告单文件自包含，可直接浏览器打开 / 另存 PDF / 打印。
* narrative.json 为可选的"教师话术"文件（结论摘要、各维度解读、教学建议）；
  缺省时由脚本按规则自动生成占位文本。
* 加 --pdf 时尝试调用本机 Edge/Chrome 无头模式打印为 PDF。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svg_charts as C  # noqa: E402


# --------------------------------------------------------------------------- #
# 知网文献引用：链接必须挂在篇名上（作者名不得作为链接载体）
# --------------------------------------------------------------------------- #
def cnki_ref(author, year, title, url):
    """生成规范的知网文献内联引用（技能唯一标准形态）。

    返回「（作者，年《篇名(可点击)》）」：作者署名保持纯文本（不可点），
    仅篇名作为 <a> 超链接指向知网在线阅读页。正文署名引用 / 文末参考文献
    都不得把 <a> 挂在作者名上——链接只能落在篇名。

    :param author: 作者，如 ``何倩``
    :param year:   发表年，如 ``2025``
    :param title:  篇名，如 ``基于认知负荷理论的高中数学解析几何教学策略研究``
    :param url:    知网在线阅读直链（只出现在 href，渲染后不可见）
    """
    link = ('<a href="%s" target="_blank" rel="noopener" '
            'style="text-decoration:none;color:#1F3864">%s</a>') % (url, title)
    return '（%s，%s《%s》）' % (author, year, link)


# --------------------------------------------------------------------------- #
# 知网文献引用：从 narrative.references 自动渲染（链接挂在篇名，不在作者）
# --------------------------------------------------------------------------- #
_CNKI_REFS = {}  # (author, year) -> (title, url)，build_html 每次渲染前重建


def link_cnki(htm):
    """把已 inline_md 化的 HTML 中「(作者，年)」署名引用，自动接成规范篇名链接。

    仅对 ``narrative.references`` 中登记过的 (作者，年) 生效；未登记的普通文本不动。
    链接挂在篇名上（``cnki_ref`` 形态），作者名保持纯文本——绝不会把 ``<a>`` 挂到作者名。
    """
    if not _CNKI_REFS:
        return htm
    for (author, year), (title, url, _src) in _CNKI_REFS.items():
        inner = cnki_ref(author, year, title, url)[1:-1]  # 去掉外层（），正文里已有括号
        for sep in ("，", ","):
            pat = re.compile(re.escape(author) + sep + r"\s*" + re.escape(str(year)) + r"(?!《)")
            htm = pat.sub(inner, htm)
    return htm


def build_cnki_refs_section():
    """依据 ``_CNKI_REFS`` 生成文末「参考文献（知网基教溯源）」区块（篇名可点、作者不可点）。"""
    if not _CNKI_REFS:
        return ""
    items = []
    for (author, year), (title, url, source) in _CNKI_REFS.items():
        link = ('<a href="%s" target="_blank" rel="noopener" '
                'style="text-decoration:none;color:#1F3864">%s</a>') % (url, title)
        # 来源缺失（空/未提供）时不显示「来源：」字段，避免空标签
        src_part = (" 来源：%s。" % esc(source)) if source else "。"
        items.append("<li style='margin:5px 0'>%s —— %s，%s%s</li>"
                     % (link, esc(author), esc(str(year)), src_part))
    return ('<section style="margin-top:34px;border-top:1px solid #DDD;padding-top:18px">'
            '<h3 style="font-size:12.5pt;color:#1F3864;margin:0 0 10px">参考文献（知网基教溯源）</h3>'
            '<ol style="margin:0 0 0 20px;padding:0;font-size:10pt;line-height:1.95;color:#333">'
            + "".join(items) +
            '</ol>'
            '<p style="font-size:9pt;color:#888;margin:10px 0 0">'
            '以上文献经知网基教检索命中，篇名链接至知网在线阅读页，供溯源核对。</p>'
            '</section>')

SUBJECT_TINT = ["#EEF3FB", "#FDF1E9", "#EFF6EC", "#FBEEEE", "#F3EEF9", "#E9F6FB"]

CSS = """
:root{
  --blue:#4472C4; --orange:#ED7D31; --green:#70AD47; --red:#C00000;
  --ink:#222; --muted:#666; --line:#DDD; --bg:#F5F6F8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,'Microsoft YaHei','PingFang SC','Hiragino Sans GB','Source Han Sans SC',Arial,sans-serif;
  font-size:11pt;line-height:1.75;-webkit-font-smoothing:antialiased}
.page{background:#fff;max-width:960px;margin:0 auto;padding:38px 46px;
  box-shadow:0 2px 14px rgba(0,0,0,.07)}
h1,h2,h3,h4,h5,h6{line-height:1.35;margin:0}
h1{font-size:23pt;letter-spacing:.5px}
h2{font-size:15.5pt;margin:38px 0 14px;padding:9px 14px;border-left:5px solid var(--blue);
  background:linear-gradient(90deg,#F0F4FB,rgba(240,244,251,0));border-radius:0 6px 6px 0}
h3{font-size:12.5pt;margin:24px 0 10px;color:#1F3864}
h4{font-size:11.5pt;margin:16px 0 8px;color:#333}
h5{font-size:11pt;margin:13px 0 6px;color:#3A3A3A}
h6{font-size:10.5pt;margin:12px 0 6px;color:#444}
p{margin:8px 0}
ul,ol{margin:8px 0 8px 22px;padding:0}
li{margin:4px 0}
small,.muted{color:var(--muted)}
a{color:var(--blue)}
.cover{border-bottom:3px double var(--blue);padding-bottom:26px;margin-bottom:8px}
.cover .sub{color:var(--muted);font-size:11pt;margin-top:6px}
.cover .tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}
.tag{background:#F0F4FB;color:#1F3864;border:1px solid #D6E0F2;border-radius:20px;
  padding:4px 13px;font-size:10pt}
.metaline{margin-top:20px;font-size:10.5pt;color:#444;display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 24px}
.metaline b{color:#1F3864;font-weight:600}
.toc{background:#FAFBFC;border:1px solid var(--line);border-radius:8px;padding:16px 22px;margin:22px 0}
.toc ul{list-style:none;margin:0;padding:0}
.toc li{margin:5px 0}
.toc a{text-decoration:none}
.toc a:hover{text-decoration:underline}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:10px;margin:14px 0 18px}
.card{border:1px solid #E6E9EF;border-radius:8px;padding:10px 12px;background:#FCFDFE}
.card .k{font-size:9.5pt;color:var(--muted)}
.card .v{font-size:16pt;font-weight:700;margin-top:2px}
.card .u{font-size:9.5pt;color:var(--muted);font-weight:400;margin-left:3px}
.card.good{border-color:#CDE5C4;background:#F5FAF3}
.card.warn{border-color:#F5D6B0;background:#FEF8F1}
.card.bad{border-color:#EBB8B8;background:#FDF4F4}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:10.5pt}
th,td{border:1px solid #E1E4EA;padding:7px 9px;text-align:center;vertical-align:middle}
th{background:#F0F4FB;color:#1F3864;font-weight:600;white-space:nowrap}
td.tl,th.tl{text-align:left}
tbody tr:nth-child(even) td{background:#FBFCFD}
td.red{background:#FBE9E9!important;color:#9C0006;font-weight:700}
td.orange{background:#FDF1E4!important;color:#9C5700;font-weight:700}
td.green{background:#EDF6E9!important;color:#375623;font-weight:700}
td.blue{background:#EDF2FB!important;color:#1F3864;font-weight:700}
.chart{border:1px solid #E6E9EF;border-radius:10px;padding:14px 16px 8px;margin:16px 0;background:#fff}
.chart .cap{font-size:9.5pt;color:var(--muted);margin-top:6px;padding-top:6px;border-top:1px dashed #ECECEC}
.chartgrid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:820px){.chartgrid{grid-template-columns:1fr}.metaline{grid-template-columns:1fr}}
.note{background:#FFFBF0;border:1px solid #F2E2BE;border-left:4px solid #E0A800;
  border-radius:0 6px 6px 0;padding:10px 14px;margin:14px 0;font-size:10.5pt}
.note.blue{background:#F4F8FE;border-color:#CFDDF3;border-left-color:var(--blue)}
.note.red{background:#FDF4F4;border-color:#EFD3D3;border-left-color:var(--red)}
.callout{background:#F5FAF3;border:1px solid #D5E8CD;border-left:4px solid var(--green);
  border-radius:0 6px 6px 0;padding:10px 14px;margin:12px 0;font-size:10.5pt}
.chapter{page-break-before:always}
.avoid{page-break-inside:avoid}
footer{margin-top:42px;padding-top:14px;border-top:1px solid var(--line);
  color:var(--muted);font-size:9.5pt;text-align:center}
.qmatrix{font-size:8.5pt}
.qmatrix th,.qmatrix td{padding:2px 4px}
@media print{
  body{background:#fff}
  .page{box-shadow:none;max-width:none;padding:0;margin:0}
  @page{size:A4;margin:2cm}
  h2{page-break-after:avoid}
  table,.chart{page-break-inside:avoid}
  table.qmatrix{page-break-inside:auto}
}
"""


# --------------------------------------------------------------------------- #
# 小工具
# --------------------------------------------------------------------------- #
_CN_DIGITS = "零一二三四五六七八九"


def cn_num(n: int) -> str:
    """阿拉伯数字 → 正文用中文小写数字（1→一、10→十、11→十一、24→二十四）。"""
    if n <= 0:
        return str(n)
    if n < 10:
        return _CN_DIGITS[n]
    if n == 10:
        return "十"
    if n < 20:
        return "十" + _CN_DIGITS[n % 10]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _CN_DIGITS[tens] + "十" + (_CN_DIGITS[ones] if ones else "")
    return str(n)


# 报告标题层级 → 序号形式（用户要求 2026-10-11，全报告统一）：
#   h2 一、   h3 （一）   h4 1.   h5 （1）   h6 a.
# h1 是封面的报告大标题，不参与编号。
_HEAD_RE = re.compile(r"<(h[2-6])([^>]*)>(.*?)</\1>", re.S)
_NO_NUM_HEADS = ("目录",)


def renumber_headings(htm: str) -> str:
    """给正文标题按「一、（一）1.（1）a.」逐级编号。

    h2 的序号由 build_html 直接写死（目录必须与正文一致），这里只处理 h3 及以下；
    每遇到一个 h2 就把下级计数器清零。目录标题（h3「目录」）不参与编号。
    """
    counters = {3: 0, 4: 0, 5: 0, 6: 0}

    def _clear(start):
        for lv in range(start, 7):
            counters[lv] = 0

    def _repl(m):
        tag, attrs, text = m.group(1), m.group(2), m.group(3)
        lv = int(tag[1])
        if lv == 2:
            _clear(3)
            return m.group(0)
        if text.strip() in _NO_NUM_HEADS:
            return m.group(0)
        counters[lv] += 1
        _clear(lv + 1)
        if lv == 3:
            num = "（%s）" % cn_num(counters[3])
        elif lv == 4:
            num = "%d. " % counters[4]
        elif lv == 5:
            num = "（%d）" % counters[5]
        else:
            num = "%s. " % chr(ord("a") + (counters[6] - 1) % 26)
        return "<%s%s>%s%s</%s>" % (tag, attrs, num, text, tag)

    return _HEAD_RE.sub(_repl, htm)


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def q_label(q) -> str:
    """题号显示：题号本身已含「题」字（如 选择题2 / 第9题 / 听力理解）时不再加「第…题」前缀。"""
    s = str(q)
    return s if ("题" in s or "理解" in s or "表达" in s or "填空" in s or "改错" in s) else "第%s题" % s


def scope_slug(subs) -> str:
    """学科范围的文件名简写：≤4 科直接连写，更多则用「全N科」，避免文件名里出现顿号。"""
    subs = list(subs or [])
    if not subs:
        return "全部学科"
    return "".join(subs) if len(subs) <= 4 else "全%d科" % len(subs)


def inline_md(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def fmt(v, nd=1, dash="-"):
    if v is None:
        return dash
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9 and nd == 0:
            return "{:.0f}".format(v)
        return ("{:." + str(nd) + "f}").format(v)
    return str(v)


def pct(v, nd=1):
    return "-" if v is None else ("{:." + str(nd) + "f}%").format(v * 100)


def delta_pct(v, nd=2):
    return "-" if v is None else ("{:+." + str(nd) + "f}%").format(v)


def band_range(band, full):
    """分数段 → **实际分数区间**字符串（用户要求 2026-10-11：一律显示具体分数，不用百分数）。

    段边界在数据里是「占满分比例」（``lo`` / ``hi``），渲染前按该科满分换算成分数。
    末档的 ``hi`` 是哨兵值（>1），用 ``min(hi, 1)`` 收成满分，避免出现「满分 分」这种拼接残渣。
    """
    full = full or 0
    lo = band.get("lo") or 0
    hi = min(band.get("hi") or 0, 1.0)
    return "%g – %g 分" % (lo * full, hi * full)


def q_sort_key(q):
    """题号排序键：纯数字按**数值**升序，非数字题号（如「选择题2」「听力理解」）按字符串排在后面。"""
    s = str(q).strip()
    try:
        return (0, float(s), "")
    except ValueError:
        return (1, 0.0, s)


def cls_for_std(std, mean, full):
    if not mean or not full:
        return ""
    r = std / full
    if r >= 0.20:
        return "red"
    if r >= 0.16:
        return "orange"
    return "green"


def narrative_of(narr, subject, key):
    if not narr:
        return None
    sn = (narr.get("subject_notes") or {}).get(subject) or {}
    if not isinstance(sn, dict):
        return None
    v = sn.get(key)
    if isinstance(v, list):
        return " ".join(str(x) for x in v)
    return v if isinstance(v, str) else None


def _as_list(v):
    """把 narrative 里的字段纠成「字符串列表」；不认识就返回 None（视作未提供）。"""
    if isinstance(v, str):
        return [v] if v.strip() else None
    if isinstance(v, list):
        out = [str(x) for x in v if x is not None and str(x).strip()]
        return out or None
    return None


def _as_dict(v):
    return v if isinstance(v, dict) else None


def sanitize_narrative(narr):
    """把 narrative.json 的字段梳成渲染器能安全使用的形态。

    narrative 是**可选的教师话术文件**——单字段写错（如 ``improvement`` 写成字符串、
    ``subject_notes.数学.stats`` 写成数字）不该让整份报告渲染崩掉，更不该一条都产不出来。
    这里统一纠形：类型不对就当「没提供」，退回自动解读。

    注：``data_notes_extra`` 已废弃（用户要求 2026-10-08）——报告与 Excel 结果册都不再
    承载「数据说明」，数据质量交代只在 ``analysis.json`` 与对话交付说明里出现。
    """
    if not isinstance(narr, dict):
        return {}
    out = {
        "summary": _as_list(narr.get("summary")),
        "actions": _as_list(narr.get("actions")),
        "cross_note": narr.get("cross_note") if isinstance(narr.get("cross_note"), str) else None,
    }
    sn = _as_dict(narr.get("subject_notes")) or {}
    clean_sn = {}
    for sub, d in sn.items():
        d = _as_dict(d)
        if not d:
            continue
        vals = {}
        for k, v in d.items():
            if isinstance(v, str):
                vals[k] = v
            elif isinstance(v, list):
                vals[k] = " ".join(str(x) for x in v if x is not None)
        if vals:
            clean_sn[sub] = vals
    out["subject_notes"] = clean_sn
    imp = _as_dict(narr.get("improvement")) or {}
    clean_imp = {"common": _as_list(imp.get("common")), "actions": _as_list(imp.get("actions"))}
    for k in ("kp_priority", "students"):
        d = _as_dict(imp.get(k))
        if d:
            clean_imp[k] = {sub: [str(x) for x in v] for sub, v in d.items() if isinstance(v, list)}
    out["improvement"] = clean_imp
    return out


def block(text, css="note") -> str:
    if not text:
        return ""
    return '<div class="%s">%s</div>' % (css, link_cnki(inline_md(text)))


def ulist(items, css="callout") -> str:
    if not items:
        return ""
    lis = "".join("<li>%s</li>" % link_cnki(inline_md(x)) for x in items)
    return '<div class="%s"><ul>%s</ul></div>' % (css, lis)


# --------------------------------------------------------------------------- #
# 自动解读（narrative 缺省时的兜底）
# --------------------------------------------------------------------------- #
def auto_stats(item, s):
    st = item["stats"]
    if not st.get("count"):
        return "该学科没有有效成绩，无法计算统计量。"
    bits = ["本班（%s）共 %d 人有效成绩，平均分 **%s** 分，得分率 **%s**；中位数 %s，最高 %s，最低 %s，极差 %s。"
            % (item.get("focus_class", "本班"), st["count"], fmt(st["mean"]), pct(st["score_rate"]),
               fmt(st["median"]), fmt(st["max"]), fmt(st["min"]), fmt(st["range"]))]
    bits.append("及格率 **%s**、优秀率 **%s**、低分率 **%s**；标准差 **%s**（%s）。"
                % (pct(st["pass_rate"]), pct(st["excellent_rate"]), pct(st["low_rate"]),
                   fmt(st["std"]),
                   "离散度偏大，班内差距明显" if st["std"] / item["full"] >= 0.20 else "离散度正常，班内水平较整齐"))
    if st["mean"] and st["median"]:
        if st["mean"] - st["median"] > 0.03 * item["full"]:
            bits.append("均分高于中位数，说明**低分学生拉低了下限**，尾部有拖累；")
        elif st["median"] - st["mean"] > 0.03 * item["full"]:
            bits.append("中位数高于均分，说明**少数低分学生明显拉低整体**，补差收益最大；")
    return "".join(bits)


def auto_bands(item, s):
    bands = item["bands"]
    if not bands:
        return ""
    mx = max(bands, key=lambda b: b["count"])
    n = item["stats"].get("count", 0) or 1
    shape = item["shape"]
    txt = ("人数最多的是「%s」段，共 %d 人（%s）；不及格 %d 人（%s），优秀（≥90%%）%d 人（%s）。"
           % (mx["label"], mx["count"], pct(mx["ratio"], 1),
              bands[0]["count"], pct(bands[0]["ratio"], 1),
              bands[-1]["count"], pct(bands[-1]["ratio"], 1)))
    txt += "整体形态判定为 **%s**——%s" % (shape["type"], shape["evidence"])
    return txt


def auto_questions(item, s):
    qs = item["questions"]
    if not qs:
        return None
    bad = [q for q in qs if q["level"] == "共性错题"]
    weak = [q for q in qs if q["level"] == "薄弱题"]
    top = sorted(qs, key=lambda x: x["rate"])[:5]
    txt = "本学科共统计 %d 道题。得分率最低的 5 道题依次为：" % len(qs)
    txt += "、".join("%s（%s%s）" % (q_label(q["q"]), pct(q["rate"], 1),
                                    "，属「%s」" % q["kp"] if (q.get("kp") or "").strip() else "")
                    for q in top)
    txt += "。"
    if bad:
        txt += "其中 **共性错题（得分率<60%%）%d 道**：%s，属于必须重讲的内容；" % (
            len(bad), "、".join(q_label(q["q"]) for q in bad[:12]))
    if weak:
        txt += "薄弱题（60–75%%）%d 道：%s，建议做变式训练。" % (
            len(weak), "、".join(q_label(q["q"]) for q in weak[:12]))
    return txt


def auto_kp(item, s):
    kps = item["knowledge_points"]
    if not kps:
        return None
    danger = [k for k in kps if k["level"] == "危险"]
    weak = [k for k in kps if k["level"] == "薄弱"]
    txt = "共归集 %d 个知识点。" % len(kps)
    if danger:
        txt += "**高危（<60%%）**：%s；" % "、".join("%s（%s）" % (k["kp"], pct(k["rate"], 1)) for k in danger)
    if weak:
        txt += "**薄弱（60–75%%）**：%s；" % "、".join("%s（%s）" % (k["kp"], pct(k["rate"], 1)) for k in weak)
    best = sorted(kps, key=lambda x: -x["rate"])[:3]
    txt += "掌握最好的知识点为 %s。讲评优先级按表中 priority 由小到大执行。" % (
        "、".join("%s（%s）" % (k["kp"], pct(k["rate"], 1)) for k in best))
    return txt


def auto_comparison(item, s):
    cmp_ = item["comparison"]
    f = cmp_.get("focus")
    if not f:
        return ""
    txt = "本班平均分 **%s**、得分率 **%s**。" % (fmt(f["mean"]), pct(f["score_rate"]))
    for b in cmp_["benchmarks"]:
        if b.get("over_rate") is None:
            continue
        sign = "高于" if b["over_rate"] >= 0 else "低于"
        txt += "对比「%s」（%s 分），本班%s **%s**，超均率 **%s**；" % (
            b["name"], fmt(b.get("mean")), sign, pct(abs(b["over_rate"]) / 100, 1), delta_pct(b["over_rate"]))
    others = [c for c in cmp_["by_class"] if c.get("name") != cmp_["focus"]["name"]]
    if others:
        best = max(cmp_["by_class"], key=lambda c: c.get("mean") or -1)
        worst = min(cmp_["by_class"], key=lambda c: c.get("mean") or 1e9)
        txt += "本次最高班为「%s」（%s 分），最低班为「%s」（%s 分），班间均分差 %s 分。" % (
            best["name"], fmt(best["mean"]), worst["name"], fmt(worst["mean"]),
            fmt((best.get("mean") or 0) - (worst.get("mean") or 0)))
    if cmp_.get("need_external_benchmark"):
        txt += "（注：未提供年级/区市均分基准，仅用本次全体学生均分作年级参照，建议补充外部基准。）"
    return txt


def auto_individual(item, s):
    ind = item["individuals"]
    lst = ind["lists"]
    if ind["mode"] == "history":
        txt = "已获得历次成绩，共追踪 %d 名学生。" % len(ind.get("history") or [])
        if lst.get("进步榜"):
            txt += "进步榜：%s；" % "、".join("%s（名次 %+d）" % (x["name"], x["rank_delta"] or 0)
                                            for x in lst["进步榜"][:8])
        if lst.get("需关注名单"):
            txt += "需关注：%s。" % "、".join("%s（名次 %+d）" % (x["name"], x["rank_delta"] or 0)
                                          for x in lst["需关注名单"][:8])
        return txt
    txt = "本例无历次成绩，按横截面分层识别："
    for k in ("尖子生", "临界优秀", "临界及格", "学困生"):
        v = lst.get(k) or []
        names = "、".join(x["name"] for x in v[:10])
        txt += "**%s** %d 人%s；" % (k, len(v), ("（%s%s）" % (names, "等" if len(v) > 10 else "")) if v else "")
    return txt


def auto_summary(an):
    meta = an["meta"]
    subs = meta["subjects"]
    out = []
    rows = []
    for s in subs:
        r = an["results"][s]
        rows.append((s, r))
    # 1 整体
    avg_rate = sum(r["stats"].get("score_rate") or 0 for _, r in rows) / max(len(rows), 1)
    out.append("本次「%s」共分析 **%d** 个学科（%s），全体 %d 人；各科平均得分率 **%.1f%%**。"
               % (meta["exam_name"], len(subs), "、".join(subs), meta["student_count"], avg_rate * 100))
    # 顺序不可判定时，先把这条讲清楚——趋势结论站不住，别让读者先看到「持续进步」再自己发现坑
    if meta.get("history_order_source") == "unknown":
        out.append("⚠️ 历次考试的**先后顺序无法判定**（考试名称既无序号、也没有「序号」/「日期」列），"
                   "维度 6 的趋势判定、进步榜、需关注名单**可能整体反向**，仅供参考；"
                   "其余 5 个维度不受影响。补一列「序号」或用 --history-order 指定后重跑即可修正。")
    # 2 最强 / 最弱
    ok = [(s, r) for s, r in rows if r["stats"].get("score_rate") is not None]
    if ok:
        b = max(ok, key=lambda x: x[1]["stats"]["score_rate"])
        w = min(ok, key=lambda x: x[1]["stats"]["score_rate"])
        out.append("**优势学科**：%s（得分率 %.1f%%）；**薄弱学科**：%s（得分率 %.1f%%），后者的提分空间最大。"
                   % (b[0], b[1]["stats"]["score_rate"] * 100, w[0], w[1]["stats"]["score_rate"] * 100))
        out.append("学科形态：%s。" % "；".join("%s为%s" % (s, r["shape"]["type"]) for s, r in rows))
        low = [(s, r) for s, r in rows if r["stats"].get("pass_rate") is not None]
        if low:
            wl = min(low, key=lambda x: x[1]["stats"]["pass_rate"])
            out.append("**及格率最低**的是 %s（%.1f%%），**低分率最高**的是 %s（%.1f%%），需优先安排补差。"
                       % (wl[0], wl[1]["stats"]["pass_rate"] * 100,
                          max(low, key=lambda x: x[1]["stats"]["low_rate"])[0],
                          max(low, key=lambda x: x[1]["stats"]["low_rate"])[1]["stats"]["low_rate"] * 100))
        dk = [(s, r["knowledge_points"][0]) for s, r in rows if r["knowledge_points"]]
        if dk:
            out.append("共性薄弱知识点集中：%s。"
                       % "；".join("%s→%s（%.1f%%）" % (s, k["kp"], k["rate"] * 100) for s, k in dk))
    # 注：不再输出「有 N 条数据说明需先阅读（见「数据说明」小节）」——报告已无该章节
    return out


# --------------------------------------------------------------------------- #
# 表格渲染
# --------------------------------------------------------------------------- #
def table(headers, rows, align_left=(), cls=""):
    """表格渲染。单元格内容一律转义——姓名/知识点里出现 < & 之类字符时不会破版。"""
    th = "".join('<th class="%s">%s</th>' % ("tl" if i in align_left else "", esc(h))
                 for i, h in enumerate(headers))
    body = []
    for r in rows:
        tds = []
        for i, c in enumerate(r):
            if isinstance(c, tuple):  # (文本, 样式类)
                tds.append('<td class="%s%s">%s</td>'
                           % (c[1], " tl" if i in align_left else "", esc(c[0])))
            else:
                tds.append('<td class="%s">%s</td>'
                           % ("tl" if i in align_left else "", esc(c)))
        body.append("<tr>%s</tr>" % "".join(tds))
    return '<table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (
        cls, th, "".join(body))


def cards(items):
    out = ['<div class="cards">']
    for k, v, u, tone in items:
        out.append('<div class="card %s"><div class="k">%s</div>'
                   '<div class="v">%s<span class="u">%s</span></div></div>' % (tone, esc(k), esc(v), esc(u)))
    out.append("</div>")
    return "".join(out)


def chart(svg, cap=""):
    return '<div class="chart avoid">%s<div class="cap">%s</div></div>' % (svg, inline_md(cap))


def scope_hint(an) -> str:
    """逐题 / 知识点 / 名单三节共用的范围提示——避免读者误以为和维度 1 同一范围。"""
    meta = an.get("meta") or {}
    sc = meta.get("individual_scope") or "全部样本"
    tag = "（本班）" if meta.get("individual_scope_is_focus") else "（含各班）"
    if sc == "本班":        # 兜底哨兵本身就是「本班」，再标一次会重复成「本班（本班）」
        tag = ""
    return "<p class='muted'>统计范围：%s%s。</p>" % (esc(sc), tag)


# --------------------------------------------------------------------------- #
# 各维度章节
# --------------------------------------------------------------------------- #
def section_stats(an, s, item, narr):
    full = item["full"]
    st = item["stats"]
    if not st.get("count"):
        return block("该学科无有效成绩数据。", "note red")
    tone_std = cls_for_std(st["std"], st["mean"], full)
    tone_pass = "red" if st["pass_rate"] < 0.80 else ("orange" if st["pass_rate"] < 0.90 else "green")
    tone_exc = "orange" if st["excellent_rate"] < 0.15 else "green"
    tone_low = "red" if st["low_rate"] > 0.10 else ("orange" if st["low_rate"] > 0.05 else "green")
    good_line = item.get("good") or full * 0.70

    def tip(t):  # 表格「提示」列：把色调类名转成 (中文标签, 样式类) 元组
        return ({"red": "预警", "orange": "关注", "green": "正常"}[t], t) if t else ""

    head = cards([
        ("有效人数", fmt(st["count"], 0), "人", ""),
        ("平均分", fmt(st["mean"]), "/%g" % full, ""),
        ("得分率", pct(st["score_rate"]), "", ""),
        ("优秀率", pct(st["excellent_rate"]), "", tone_exc),
        ("良好率", pct(st.get("good_rate")), "", ""),
        ("合格率", pct(st.get("qualified_rate")), "", ""),
        ("不合格率", pct(st.get("fail_rate")), "",
         "red" if (st.get("fail_rate") or 0) > 0.20 else ""),
        ("及格率", pct(st["pass_rate"]), "", tone_pass),
        ("低分率", pct(st["low_rate"]), "", tone_low),
        ("标准差", fmt(st["std"]), "", tone_std),
    ])

    rows = [
        ["平均分", fmt(st["mean"]), "Σ得分 ÷ 有效人数", ""],
        ["最高分 / 最低分", "%s / %s" % (fmt(st["max"]), fmt(st["min"])), "原始极值", ""],
        ["中位数", fmt(st["median"]), "升序后中间值", ""],
        ["极差", fmt(st["range"]), "最高分 − 最低分", ("偏大", "orange") if st["range"] > 0.75 * full else ""],
        ["标准差", fmt(st["std"]), "√(Σ(x−x̄)² ÷ n)（总体标准差）", tip(tone_std)],
        ["优秀率", pct(st["excellent_rate"]), "≥ 满分×85%%（%g 分）÷ 有效人数" % (full * .85), tip(tone_exc)],
        ["良好率", pct(st.get("good_rate")), "%g ~ %g 分（满分×70%% ~ 85%%）÷ 有效人数"
         % (good_line, full * .85), ""],
        ["合格率", pct(st.get("qualified_rate")), "%g ~ %g 分（满分×60%% ~ 70%%）÷ 有效人数"
         % (full * .6, good_line), ""],
        ["不合格率", pct(st.get("fail_rate")), "< 满分×60%%（%g 分）÷ 有效人数" % (full * .6),
         ("偏高", "red") if (st.get("fail_rate") or 0) > 0.20 else ""],
        ["及格率", pct(st["pass_rate"]), "≥ 满分×60%%（%g 分）÷ 有效人数（累计）" % (full * .6), tip(tone_pass)],
        ["低分率", pct(st["low_rate"]), "< 满分×40%%（%g 分）÷ 有效人数" % (full * .4), tip(tone_low)],
        ["得分率", pct(st["score_rate"]), "平均分 ÷ 满分（%g）" % full, ""],
    ]
    note4 = ("<p class='muted'>优秀率 / 良好率 / 合格率 / 不合格率为<b>互斥四档</b>（≥85% / 70–85% / "
             "60–70% / &lt;60%），四者相加 = 100%，可与「分数段分布」对照；"
             "「及格率」是 ≥60% 的累计值，与四率不在同一层，勿混用。</p>")
    tbl = table(["指标", "数值", "计算方式 / 公式", "提示"], rows, align_left=(0, 2)) + note4

    # 年级层对照（多班样本才有意义）：把本班放进全年级标尺里看
    grade_tbl = ""
    if an["meta"].get("multi_class"):
        ga = item.get("stats_all") or {}
        if ga.get("count"):
            grows = [
                ["本班（%s）" % an["meta"]["focus_class"], fmt(st["mean"]), pct(st["score_rate"]),
                 pct(st["excellent_rate"]), pct(st.get("good_rate")), pct(st.get("qualified_rate")),
                 pct(st.get("fail_rate")), pct(st["pass_rate"])],
                ["全年级（全部样本 %d 人）" % ga["count"], fmt(ga["mean"]), pct(ga["score_rate"]),
                 pct(ga["excellent_rate"]), pct(ga.get("good_rate")), pct(ga.get("qualified_rate")),
                 pct(ga.get("fail_rate")), pct(ga["pass_rate"])],
            ]
            grade_tbl = ("<h4>年级层对照（同一标尺）</h4>"
                         + table(["范围", "平均分", "得分率", "优秀率", "良好率", "合格率",
                                  "不合格率", "及格率"], grows, align_left=(0,))
                         + "<p class='muted'>本班与全年级同用一套分数线，直接可比重心在哪。</p>")
    txt = narrative_of(narr, s, "stats") or auto_stats(dict(item, focus_class=an["meta"]["focus_class"]), s)
    preview = ""
    if an["meta"]["mode"] == "multi":
        crows = []
        for sub in an["meta"]["subjects"]:
            r = an["results"][sub]
            ss = r["stats"]
            crows.append([sub, fmt(ss.get("mean")), pct(ss.get("score_rate")), pct(ss.get("pass_rate")),
                          pct(ss.get("excellent_rate")), pct(ss.get("good_rate")),
                          pct(ss.get("qualified_rate")), pct(ss.get("fail_rate")), pct(ss.get("low_rate")),
                          fmt(ss.get("std")), "%.1f%%" % (100 * (ss.get("std") or 0) / r["full"])])
        preview = ("<h4>学科间基础指标对比（预告）</h4>"
                   + table(["学科", "平均分", "得分率", "及格率", "优秀率", "良好率", "合格率",
                            "不合格率", "低分率", "标准差", "变异系数"],
                           crows, align_left=(0,)))
    return head + tbl + grade_tbl + block(txt, "note blue") + preview


def section_bands(an, s, item, narr):
    bands = item["bands"]
    if not item["stats"].get("count"):
        return block("无数据。", "note red")
    # 分数段一律写成**实际分数区间**（用户要求 2026-10-11：显示具体分数，不用百分数）
    rows = []
    for b in bands:
        rows.append([band_range(b, item["full"]), "%d" % b["count"], pct(b["ratio"]), pct(b["cum"])])
    tbl = table(["分数段（分数）", "人数", "占比", "累计占比"], rows, align_left=(0,))
    note = ('<p class="muted">分数段按本学科满分 %g 分换算为<b>实际分数区间</b>：'
            '不及格 &lt;60%%｜60–70%%｜70–80%%｜80–90%%｜优秀 ≥90%%。</p>' % item["full"])
    # 年级层分数段（多班样本）：与本班的分布并排，看本班结构是否偏离年级
    grade_tbl = ""
    if an["meta"].get("multi_class") and item.get("bands_all"):
        ga = item.get("stats_all") or {}
        grows = [[band_range(b, item["full"]), "%d" % b["count"], pct(b["ratio"]), pct(b["cum"])]
                 for b in item["bands_all"]]
        grade_tbl = ("<h4>年级层 · 分数段分布（全部样本 %s 人）</h4>" % (ga.get("count") or "-")
                     + table(["分数段（分数）", "人数", "占比", "累计占比"], grows, align_left=(0,)))
    b1 = C.bar_chart([b["label"] for b in bands], [b["count"] for b in bands],
                     title="【%s】分数段人数分布" % s, unit="人数（人）", sub="按满分比例分段",
                     colors=[C.RED, C.ORANGE, C.BLUE, C.GREEN, C.BLUE])
    b2 = C.pie_chart([b["label"] for b in bands], [b["count"] for b in bands],
                     title="【%s】各分数段占比" % s, sub="直观看结构",
                     colors=[C.RED, C.ORANGE, C.BLUE, C.GREEN, "#2F5597"])
    txt = narrative_of(narr, s, "bands") or auto_bands(item, s)
    return (tbl + note + grade_tbl + '<div class="chartgrid">' + chart(b1, "纵轴=人数，横轴=分数段；柱顶为实际人数。")
            + chart(b2, "环形图内圈为有效人数合计；图例标注人数与占比。") + "</div>"
            + block(txt, "note blue"))


def chapter_title(an, s):
    """按**实际可用维度**生成章节名——缺数据时不虚报「完整 6 维度」。

    没有逐题 / 知识点数据时，维度 3、4 整节不生成，章节名也据此收敛。
    """
    item = an["results"][s]
    dims = ["基础统计量", "分数段分布"]
    if item["questions"]:
        dims.append("逐题得分率")
    if item["knowledge_points"]:
        dims.append("知识点掌握热力图")
    dims += ["对比分析", "个体追踪"]
    return ("完整 6 维度分析" if len(dims) == 6
            else "%d 个维度：%s" % (len(dims), " / ".join(dims)))


def tone_of_rate(r):
    """得分率 → 报告统一色阶类（与逐题判定同档）：<60% 红 / 60–75% 橙 / 75–85% 绿 / ≥85% 蓝。"""
    if r is None:
        return ""
    if r < 0.6:
        return "red"
    if r < 0.75:
        return "orange"
    if r < 0.85:
        return "green"
    return "blue"


def class_question_matrix(qs, cls_names):
    """各班 × 逐题得分率矩阵：行 = 题号，列 = 每个班级 + 全年级（用户要求 2026-10-11）。

    单元格按得分率着色（与逐题判定同档），一眼看出「哪道题哪个班塌了」。
    逐题表没有「学号」列（无法分班）时返回空串——不摆一张只有一列的空表。
    """
    if not cls_names:
        return ""
    has_any = any(q.get("by_class") for q in qs)
    if not has_any:
        return ""
    head = ("<tr><th class='tl'>题号</th><th>满分</th>"
            + "".join("<th>%s</th>" % esc(c) for c in cls_names)
            + "<th>全年级</th></tr>")
    body = []
    for q in qs:
        cm = {c["cls"]: c for c in (q.get("by_class") or [])}
        tds = ["<td class='tl'>%s</td>" % esc(q_label(q["q"])), "<td>%s</td>" % fmt(q["full"])]
        for c in cls_names:
            r = (cm.get(c) or {}).get("rate")
            tds.append("<td></td>" if r is None
                       else "<td class='%s'>%s</td>" % (tone_of_rate(r), pct(r, 0)))
        tds.append("<td class='%s'><b>%s</b></td>" % (tone_of_rate(q.get("rate_all")),
                                                      pct(q.get("rate_all"), 0)))
        body.append("<tr>%s</tr>" % "".join(tds))
    return ("<table class='qmatrix'><thead>%s</thead><tbody>%s</tbody></table>"
            % (head, "".join(body)))


def section_questions(an, s, item, narr):
    """维度 3 · 逐题得分率——**按学科**统计，绝不把多科混在一起（用户要求 2026-10-10/11）。

    ① 班级层：本班每题的平均得分 / 得分率 / 判定 / 讲评优先级 / 作答人数
    ② 年级层：全部样本同字段的统计（两层并列，不再二选一）
    ③ 各班层：**每个班级**在每道小题上的得分率矩阵（行=题号，列=各班 + 全年级）
    ④ 得分最低 / 得分最高的试题清单（按本学科分别给出）
    ⑤ 一句话统计范围 + 教师解读

    没有逐题数据 → 返回 None，整节不生成（不摆空板块、不编数据）。
    """
    qs = item.get("questions")
    if not qs:
        return None
    meta = an.get("meta") or {}
    two = any(q.get("two_scope") for q in qs)
    cls_name = meta.get("individual_scope") or "全部样本"
    grade_n = meta.get("grade_scope_count") or meta.get("student_count") or 0
    cls_names = [c["cls"] for q0 in qs for c in (q0.get("by_class") or [])]
    cls_names = list(dict.fromkeys(cls_names))
    # 逐题表若没有知识点归属，就别摆一列空白的「知识点」——列本身也是占位
    has_kp = any((q.get("kp") or "").strip() for q in qs)
    lead = ["题号", "满分", "平均得分", "得分率"] + (["知识点"] if has_kp else [])

    # ---------------- ① 班级层 ----------------
    # 用户要求 2026-10-11：**表格里的题号列一律按题号升序**（便于与试卷题序一一对照）。
    # 讲评优先级 P1… 的先后仍按本班得分率升序标定，所以要**单独算一份名次**，
    # 不能再用行序当 P 值（行序现在是题号序，两者不是一回事）。
    prio = {q["q"]: i for i, q in enumerate(sorted(qs, key=lambda x: x["rate"]), 1)}
    rows_c = []
    for q in sorted(qs, key=lambda x: q_sort_key(x["q"])):
        cells = [q_label(q["q"]), fmt(q["full"]), fmt(q["mean"]),
                 (pct(q["rate"]), tone_of_rate(q["rate"]))]
        if has_kp:
            cells.append(q["kp"])
        cells += [q["level"], "P%d" % prio[q["q"]], q.get("n")]
        rows_c.append(cells)
    hdr_c = lead + ["判定", "讲评优先级", "作答人数"]

    # ---------------- ② 年级层 ----------------
    # 用户要求 2026-10-11：年级层题号列**按题号升序**排列（不再按得分率排，
    # 便于与试卷题序一一对照；班级层仍按得分率升序给出讲评优先级 P1…）。
    rows_g = []
    for q in sorted(qs, key=lambda x: q_sort_key(x["q"])):
        cells = [q_label(q["q"]), fmt(q["full"]), fmt(q["mean_all"]),
                 (pct(q["rate_all"]), tone_of_rate(q["rate_all"]))]
        if has_kp:
            cells.append(q["kp"])
        cells += [q["level_all"], q.get("n_all")]
        rows_g.append(cells)
    hdr_g = lead + ["判定", "作答人数"]

    left = (0, 4) if has_kp else (0,)
    qs_by_q = sorted(qs, key=lambda x: q_sort_key(x["q"]))
    if two:
        head = ("<h4>班级层 · 逐题得分率（%s）</h4>"
                "<p class='muted'>表内按<b>题号升序</b>排列；「讲评优先级」按<b>本班得分率</b>"
                "升序标定，P1 最需先讲。</p>"
                % esc(cls_name))
        head += table(hdr_c, rows_c, align_left=left)
        head += ("<h4>年级层 · 逐题得分率（全部样本 %d 人）</h4>" % grade_n)
        head += ("<p class='muted'>同字段的全年级统计（按<b>题号升序</b>），"
                 "用来判断本班哪些题<b>明显低于年级水平</b>。</p>")
        head += table(hdr_g, rows_g, align_left=left)
        svg = C.grouped_bar_chart(
            ["%s" % q["q"] for q in qs_by_q],
            [("%s" % cls_name, [q["rate"] * 100 for q in qs_by_q]),
             ("全年级", [q["rate_all"] * 100 for q in qs_by_q])],
            title="【%s】逐题得分率：本班 vs 全年级" % s, unit="得分率（%）",
            sub="同一题号两根柱并排：左为本班、右为全年级；差距大的题优先讲评",
            value_nd=0, rotate_labels=len(qs) > 12, h=360)
        cap = "横轴=题号，纵轴=得分率；柱顶为得分率数值。"
    else:
        head = ("<p class='muted'>逐题得分率（统计范围为「%s」，共 %d 人）。</p>"
                % (esc(cls_name), grade_n))
        head += table(hdr_c, rows_c, align_left=left)
        svg = C.bar_chart(["%s" % q["q"] for q in qs_by_q], [q["rate"] * 100 for q in qs_by_q],
                          title="【%s】逐题得分率" % s, unit="得分率（%）",
                          sub="虚线为 60%（共性错题线）与 80%（掌握线）",
                          refs=[(60, "共性错题线", C.RED), (80, "掌握线", C.GREEN)],
                          colors=[C.RED if q["level"] == "共性错题" else
                                  (C.ORANGE if q["level"] == "薄弱题" else C.BLUE) for q in qs_by_q],
                          value_nd=0, rotate_labels=len(qs) > 12, h=360)
        cap = "横轴=题号，纵轴=得分率；柱顶为得分率数值，红色柱为共性错题。"
    out = [head, chart(svg, cap)]

    # ---------------- ③ 各班层 · 逐题得分率矩阵 ----------------
    matrix = class_question_matrix(qs_by_q, cls_names)
    if matrix:
        out.append("<h4>各班 · 逐题得分率（每班每题）</h4>")
        out.append("<p class='muted'>行 = 题号，列 = 每个班级，末列为全年级；格内为该班在该题上的"
                   "平均得分率。颜色：红 &lt;60% ｜ 橙 60–75% ｜ 绿 75–85% ｜ 蓝 ≥85%。"
                   "空白 = 该班在该题没有作答记录。</p>")
        out.append(matrix)

    # ---------------- ④ 得分最低 / 最高试题清单 ----------------
    low = sorted(qs, key=lambda x: x["rate"])[:5]
    high = sorted(qs, key=lambda x: -x["rate"])[:5]

    def qline(q, use_all=False):
        """一行清单的**纯文本**（不含标签）。

        ⚠️ 这里绝不能自己拼 `<li>`（用户要求 2026-10-11：「<li> 这个符号去掉，HTML 和 PDF 都改」）。
        外壳由 `ulist()` 统一加，而 `ulist()` 会先 `esc()` 再插标签——自带 `<li>` 会被转义成
        字面文本，页面上原样印出 `&lt;li&gt;…&lt;/li&gt;`。同理，这里也不做 `esc()`：
        用户数据（题号、知识点名）交给 `ulist()` → `inline_md()` 统一转义，免得转义两次。
        """
        r = q["rate_all"] if use_all else q["rate"]
        lv = q["level_all"] if use_all else q["level"]
        # 用户要求 2026-10-11：清单项不套 <b>，直接写「第6题（共性错题）」。
        return ("%s（%s）：得分率 %s，%s%s"
                % (q_label(q["q"]), lv, pct(r),
                   "本班 %s ｜ 全年级 %s" % (pct(q["rate"]), pct(q["rate_all"]))
                   if two else "平均得分 %s / %s" % (fmt(q["mean_all"]), fmt(q["full"])),
                   "　涉及知识点：%s" % q["kp"] if has_kp and q.get("kp") else ""))

    out.append("<h4>得分最低的试题 · 优先讲评</h4>")
    out.append("<p class='muted'>按本学科得分率升序取前 %d 道，建议课堂集中讲评。</p>" % len(low))
    out.append(ulist([qline(q) for q in low], "callout"))
    out.append("<h4>得分最高的试题 · 已掌握</h4>")
    out.append("<p class='muted'>按本学科得分率降序取前 %d 道，可作为教学成效的确认。</p>" % len(high))
    out.append(ulist([qline(q) for q in high]))

    txt = narrative_of(narr, s, "questions") or auto_questions(item, s)
    if txt:
        out.append(block(txt, "note blue"))
    return "".join(out)


def section_kp(an, s, item, narr):
    """知识点热力图。**没有知识点数据就返回 None——整节不生成**，不摆空板块。"""
    kps = item["knowledge_points"]
    if not kps:
        return None
    rows = []
    for k in kps:
        tone = {"危险": "red", "薄弱": "orange", "良好": "green", "优秀": "blue"}[k["level"]]
        rows.append([k["priority"], k["kp"], pct(k["rate"]), (k["level"], tone),
                     "、".join(q_label(q) for q in k["questions"])])
    tbl = table(["讲评优先级", "知识点", "平均得分率", "掌握等级", "涉及题目"], rows, align_left=(1, 4))
    svg = C.heatmap_matrix(
        [{"label": k["kp"], "level": k["level"], "value": k["rate"]} for k in kps],
        title="【%s】知识点掌握热力图" % s,
        sub="颜色：深蓝=优秀(≥85%) / 绿=良好(75–85%) / 黄=薄弱(60–75%) / 红=危险(<60%)")
    txt = narrative_of(narr, s, "kp") or auto_kp(item, s)
    extra = ""
    danger = [k for k in kps if k["level"] in ("危险", "薄弱")]
    if danger:
        extra = ("<h4>「高投入低掌握」知识点与讲评排序</h4>"
                 + ulist(["**P%d · %s**：得分率 %s（%s），涉及 %s——建议课堂集中讲评。"
                          % (k["priority"], k["kp"], pct(k["rate"]), k["level"],
                             "、".join(q_label(q) for q in k["questions"]))
                          for k in danger[:8]]))
    return (scope_hint(an) + tbl
            + chart(svg, "纵轴=知识点，横轴=掌握等级；命中格子高亮并标注等级，右侧为平均得分率。")
            + extra + block(txt, "note blue"))


def section_comparison(an, s, item, narr):
    cp = item["comparison"]
    full = item["full"]
    f = cp.get("focus")
    if not f:
        return block("无数据。", "note red")
    rows = []
    fc = an["meta"].get("focus_class")
    for c in cp["by_class"]:
        # 单班样本（主表无「班级」列）时 focus_class 就是兜底哨兵「本班」，
        # 再标一次会得到「本班（本班）」这种重复标签。
        nm = c["name"]
        if nm == fc and nm != "本班":
            nm += "（本班）"
        rows.append([nm,
                     fmt(c["mean"]), fmt(c["median"]), pct(c["score_rate"]), fmt(c["max"]), fmt(c["min"]),
                     fmt(c["range"]), pct(c["excellent_rate"]), pct(c.get("good_rate")),
                     pct(c.get("qualified_rate")), pct(c.get("fail_rate")),
                     pct(c["pass_rate"]), pct(c["low_rate"]),
                     fmt(c["std"]), delta_pct(c.get("over_rate"))])
    for b in cp["benchmarks"]:
        if b.get("source") == "explicit" or b["name"].startswith("年级") or "区" in b["name"] or "市" in b["name"]:
            rows.append([b["name"], fmt(b.get("mean")), "-", "-", "-", "-", "-",
                         "-", "-", "-", "-", "-", "-", "-", delta_pct(b.get("over_rate"))])
    tbl = table(["对象", "平均分", "中位数", "得分率", "最高分", "最低分", "极差",
                 "优秀率", "良好率", "合格率", "不合格率", "及格率", "低分率", "标准差", "超均率"],
                rows, align_left=(0,))

    names = [c["name"] for c in cp["by_class"]]
    g1 = C.grouped_bar_chart(names,
                             [("平均分", [c["mean"] for c in cp["by_class"]]),
                              ("最高分", [c["max"] for c in cp["by_class"]]),
                              ("最低分", [c["min"] for c in cp["by_class"]])],
                             title="【%s】各班均分 / 最高分 / 最低分对比" % s, unit="分数（分）",
                             sub="满分 %g" % full, value_nd=1, rotate_labels=len(names) > 5)

    def norm_over(v):
        if v is None:
            return 0.5
        return max(0.0, min(1.0, 0.5 + v / 20.0))

    axes = ["得分率", "及格率", "优秀率", "低分率", "标准差(稳定性)", "超均率"]
    series = []
    for c in cp["by_class"]:
        series.append((c["name"], [
            c.get("score_rate") or 0, c.get("pass_rate") or 0, c.get("excellent_rate") or 0,
            1 - (c.get("low_rate") or 0), 1 - min(1.0, (c.get("std") or 0) / full), norm_over(c.get("over_rate")),
        ]))
    g2 = C.radar_chart(axes, series, title="【%s】班级综合素质雷达图" % s, h=420,
                       sub="各轴已归一化到 0–1：低分率与标准差取反（越外圈越优），超均率以 ±10% 映射到 0–1")
    txt = narrative_of(narr, s, "comparison") or auto_comparison(item, s)
    bands_h = ""
    for c in cp["by_class"]:
        # 分数段列显示**具体分数区间**（用户要求 2026-10-11），不用百分比
        bands_h += ("<h4>%s 分数段分布</h4>" % c["name"] +
                    table(["分数段（分数）", "人数", "占比", "累计占比"],
                          [[band_range(b, full), b["count"], pct(b["ratio"]), pct(b["cum"])]
                           for b in c["bands"]],
                          align_left=(0,)))
    return tbl + '<div class="chartgrid">' + chart(g1, "同色系为一类指标，横轴为班级/基准。") + \
        chart(g2, "每个多边形代表一个班级，越靠外圈越优。") + "</div>" + bands_h + block(txt, "note blue")


def section_individual(an, s, item, narr):
    ind = item["individuals"]
    lst = ind["lists"]
    txt = narrative_of(narr, s, "individual") or auto_individual(item, s)
    # 姓名与学号**各占一列**（用户要求 2026-10-11）；数据里没有真学号时「学号」列整列不出现。
    has_sid = bool((an.get("meta") or {}).get("has_student_id"))
    if ind["mode"] == "history" and ind.get("history"):
        rows = ind["history"]
        cap = 30
        shown = rows[:cap]
        xlabels = shown[0]["exams"]
        # 取前 6 名学生画总分/名次折线
        groups = []
        for r in rows[:6]:
            groups.append((r["name"] + "·总分", r["totals"]))
        svg1 = C.line_chart(xlabels, groups, title="【%s】个体总分走势（前 6 名示范）" % s,
                            unit="总分（分）", sub="横轴=考试次序，纵轴=总分", value_nd=1)
        groups2 = [(r["name"] + "·名次", r["ranks"]) for r in rows[:6] if any(v is not None for v in r["ranks"])]
        svg2 = C.line_chart(xlabels, groups2, title="【%s】个体名次走势（前 6 名示范）" % s,
                            unit="排名（名）", sub="纵轴数值越小越靠前", value_nd=0) if groups2 else ""
        t_rows = []
        for r in shown:
            td = r["total_delta"] or 0
            rd = r["rank_delta"]
            t_rows.append(([r.get("sid", "")] if has_sid else []) + [
                r["name"], r["cls"],
                " → ".join(fmt(v, 0) for v in r["totals"]),
                ("%+d" % td, "green" if td >= 0 else "red"),
                " → ".join(fmt(v, 0) for v in r["ranks"]) if any(v is not None for v in r["ranks"]) else "-",
                ("%+d" % rd, "green" if rd is not None and rd >= 0 else "red") if rd is not None else "-",
                r["trend"],
            ])
        tbl = table((["学号"] if has_sid else []) +
                    ["姓名", "班级", "历次总分", "总分变化", "历次排名", "名次变化", "趋势判定"],
                    t_rows, align_left=((0, 1, 2, 3, 5, 7) if has_sid else (0, 1, 2, 4, 6)))
        # 用户要求 2026-10-11：报告（HTML/PDF）里**不再指向「随附的结果册」**——
        # PDF 是单独一份，读者手上并不一定有那份 xlsx，写了反而找不到。只交代「展示了多少」。
        capnote = "" if len(rows) <= cap else \
            '<p class="muted">（追踪名单共 %d 人，此处展示前 %d 人。）</p>' \
            % (len(rows), cap)
        charts = chart(svg1, "折线越陡说明变化越大；仅示范前 6 名学生，完整数据见上表。")
        if svg2:
            charts += chart(svg2, "名次曲线向下为进步方向。")
        # 顺序不可判定时显著警示（**不阻断，但必须让读者看到**）；按名称序号排时提示一句
        order_warn = ""
        hsrc = an["meta"].get("history_order_source")
        if hsrc == "unknown":
            order_warn = block(
                "⚠️ **历次考试的先后顺序无法判定**：考试名称既不含序号，也没有「序号」/「日期」列。"
                "下表与「趋势」判定已按名称自然序估算，**「持续进步」有可能实际是「持续下滑」**"
                "（进步榜、需关注名单同理）。请只看名次/总分的变化量，不要直接采信趋势结论；"
                "补一列「序号」或「日期」，或用 "
                "--history-order \"第1次月考,期中考试,第2次月考,期末考试\" 指定顺序后重跑即可自动修正。",
                "note red")
        elif hsrc == "natural":
            order_warn = ('<p class="muted">注：历次成绩的先后顺序是按「考试」名称里的序号自动排的；'
                          '若与实际先后不符，请用 --history-order "第1次月考,期中考试,第2次月考,期末考试" '
                          '指定后重跑。</p>')
        return tbl + capnote + order_warn + charts + block(txt, "note blue")
    # 横截面分层
    order = ["尖子生", "临界优秀", "临界及格", "学困生"]
    rows_n = [[k, len(lst.get(k) or []), "、".join(x["name"] for x in (lst.get(k) or [])[:14])] for k in order]
    tbl = table(["分层", "人数", "名单"], rows_n, align_left=(0, 2))
    svg = C.bar_chart(order, [len(lst.get(k) or []) for k in order],
                      title="【%s】横截面分层人数" % s, unit="人数（人）",
                      colors=[C.BLUE, C.GREEN, C.ORANGE, C.RED],
                      sub="尖子生（≥优秀线）/ 临界优秀（优秀线下 5%% 满分）/ 临界及格（及格线下 5%% 满分）/ 学困生（<低分线）")
    # ranking 挂在 individuals 下（不是 individuals.lists 下）——此前取错层级，
    # 这张「班内成绩排名」表一直是空的。
    rank = ind.get("ranking") or lst.get("ranking") or []
    cap = 20
    scope = an["meta"].get("individual_scope") or "全部样本"
    in_focus = bool(an["meta"].get("individual_scope_is_focus"))
    # 姓名与学号**各占一列**（用户要求 2026-10-11）；数据里没有真学号时**整列不出现**，
    # 不拿 #N 兜底编号冒充学号。
    has_sid = bool(an["meta"].get("has_student_id"))
    first_col = "%s 内排名" % scope if in_focus else "样本排名"
    title = ("%s 班内成绩排名（前 %d）" % (scope, cap)) if in_focus else \
            ("样本成绩排名（含各班，前 %d）" % cap)
    rk_cols = [first_col] + (["学号"] if has_sid else []) + ["姓名", "班级", "得分"]
    rk_rows = [[r["rank"]] + ([r.get("sid", "")] if has_sid else [])
               + [r["name"], r["cls"], fmt(r["score"])] for r in rank[:cap]]
    rk = table(rk_cols, rk_rows, align_left=((2, 3) if has_sid else (1, 2)))
    # 同样不指向「随附的结果册」（PDF 里没有那份 xlsx）
    more = "" if len(rank) <= cap else \
        '<p class="muted">（本表仅展示前 %d 名，共 %d 人。）</p>' % (cap, len(rank))
    return tbl + chart(svg, "柱高为各分层人数；建议优先干预「临界及格」与「学困生」。") + \
        "<h4>%s</h4>" % title + rk + more + block(txt, "note blue")


def section_grade_overview(an, narr=None):
    """年级层 · 班级排名与全年级指标（用户要求 2026-10-11）。

    ① 班级**总分**排名（按总分均分）
    ② 每个学科按班级整体的排名（按该科得分率）
    ③ 全年级各学科四率（优秀/良好/合格/不合格）
    ④ 全年级各学科分数段分布
    ``grade_overview`` 为空（单班样本）时不生成该章。
    """
    go = an.get("grade_overview") or {}
    if not go:
        return None
    subs = an["meta"]["subjects"]
    out = []
    # ① 班级总分排名
    if go.get("by_total"):
        rows = [[r["rank"], r["cls"], r["n"], fmt(r["mean_total"]), pct(r["rate"]),
                 "%g" % r["full_total"]] for r in go["by_total"]]
        out.append("<h3>班级总分排名（全部学科合计）</h3>")
        out.append(table(["名次", "班级", "人数", "总分平均", "得分率", "满分"], rows,
                         align_left=(1,)))
        names = [r["cls"] for r in go["by_total"]]
        out.append(chart(C.bar_chart(names, [r["mean_total"] for r in go["by_total"]],
                                     title="各班总分平均对比", unit="总分平均（分）",
                                     sub="满分 %g；名次按总分平均降序" % go["by_total"][0]["full_total"],
                                     value_nd=1),
                         "横轴=班级，纵轴=总分平均；柱顶为分值。"))

    # ② 各学科按班级整体排名（用户要求 2026-10-11：格内显示平均分，不再用百分数）
    if go.get("by_subject"):
        out.append("<h3>各学科 · 班级整体排名</h3>")
        out.append("<p class='muted'>每班一行、每科一列，格内为<b>该科平均分</b>，括号内为该班在该科的"
                   "名次；末列为该班的平均名次（越小越好），用于看出「哪班哪科是短板」。"
                   "各科满分不同（见表头），故名次统一按<b>得分率</b>排定，平均分不可直接跨科横比。</p>")
        cls_names = list(dict.fromkeys([r["cls"] for s in subs
                                        for r in (go["by_subject"].get(s) or [])]))
        rows = []
        for c in cls_names:
            ranks, cells = [], []
            for s in subs:
                hit = [r for r in (go["by_subject"].get(s) or []) if r["cls"] == c]
                if hit:
                    ranks.append(hit[0]["rank"])
                    cells.append("%s（第%d）" % (fmt(hit[0]["mean"]), hit[0]["rank"]))
                else:
                    cells.append("-")
            avg = ("%.2f" % (sum(ranks) / len(ranks))) if ranks else "-"
            rows.append([c] + cells + [avg])
        rows.sort(key=lambda r: (r[-1] == "-", r[-1]))
        out.append(table(["班级"]
                         + ["%s平均分（名次）" % s for s in subs]
                         + ["平均名次"], rows, align_left=(0,)))

    # ③ 全年级各学科四率
    gs = go.get("grade_stats") or {}
    if gs:
        out.append("<h3>全年级各学科 · 四率</h3>")
        out.append("<p class='muted'>优秀率 ≥85%｜良好率 70–85%｜合格率 60–70%｜不合格率 &lt;60%，"
                   "四者互斥、相加 100%。</p>")
        rows = [[s, "%d 人" % (gs[s].get("count") or 0), fmt(gs[s].get("mean")),
                 pct(gs[s].get("score_rate")), pct(gs[s].get("excellent_rate")),
                 pct(gs[s].get("good_rate")), pct(gs[s].get("qualified_rate")),
                 pct(gs[s].get("fail_rate"))] for s in subs if s in gs]
        out.append(table(["学科", "有效人数", "平均分", "得分率", "优秀率", "良好率", "合格率",
                          "不合格率"], rows, align_left=(0,)))

    # ④ 全年级各学科分数段分布（用户要求 2026-10-11：**按学科分别成表**，表上方标学科名称；
    #    分数段显示**具体分数区间**，不用百分数）
    band_blocks = []
    for s in subs:
        g = gs.get(s) or {}
        bands = g.get("bands") or []
        if not bands:
            continue
        full = (an["results"].get(s) or {}).get("full") or 0
        rows = [[band_range(b, full), b["count"], pct(b["ratio"]), pct(b["cum"])] for b in bands]
        band_blocks.append("<h4>【%s】分数段分布（全年级 · 满分 %g 分 · %d 人）</h4>"
                           % (s, full, g.get("count") or 0)
                           + table(["分数段（分数）", "人数", "占比", "累计占比"], rows,
                                   align_left=(0,)))
    if band_blocks:
        out.append("<h3>全年级各学科 · 分数段分布</h3>")
        out.append("<p class='muted'>按学科分别成表；每一档都按该科满分换算成<b>实际分数区间</b>。</p>")
        out.extend(band_blocks)
    return "".join(out)


def section_history(an, narr=None):
    """历次成绩对比（用户要求 2026-10-11）：历次**年级**与历次**班级**的成绩变化。

    有学科列时给出各学科的四率；只有总分时如实说明「历次对比只到总分维度」。
    """
    hs = an.get("history_summary") or {}
    if not hs:
        return None
    subs = an["meta"]["subjects"]
    exams = hs.get("exams") or []
    out = []
    if not hs.get("has_subject_detail"):
        out.append(block("历次成绩表只提供了**总分**（没有各学科列），因此本节只对比总分层面的变化；"
                         "若要历次各学科的四率对比，请在历次表里补上学科列（如 语文/数学…），"
                         "或用「学号/考试/学科/分数」的长表形态后重跑。", "note blue"))

    # 一、历次年级
    gt = (hs.get("grade") or {}).get("total") or []
    if gt:
        out.append("<h3>历次年级总分对比</h3>")
        rows = [[r["exam"], "%d 人" % r["n"], fmt(r["mean"]), pct(r["score_rate"])] for r in gt]
        out.append(table(["考试", "参考人数", "总分平均", "得分率"], rows, align_left=(0,)))
        out.append(chart(C.line_chart([r["exam"] for r in gt],
                                      [("年级总分平均", [r["mean"] for r in gt])],
                                      title="历次年级总分平均走势", unit="总分平均（分）",
                                      sub="横轴=考试次序，纵轴=总分平均", value_nd=1),
                         "折线向上说明年级整体在进步；仅一次考试时无走势可看。"))
    # 二、历次年级 · 各学科四率（用户要求 2026-10-11：**按学科分别成表**，表上方标学科名称）
    gsub = (hs.get("grade") or {}).get("subjects") or {}
    sub_blocks = []
    for s in subs:
        rows = [[r["exam"], "%d 人" % r["n"], fmt(r["mean"]), pct(r["score_rate"]),
                 pct(r["excellent_rate"]), pct(r["good_rate"]),
                 pct(r["qualified_rate"]), pct(r["fail_rate"])] for r in gsub.get(s, [])]
        if rows:
            sub_blocks.append("<h4>【%s】历次四率</h4>" % s
                              + table(["考试", "人数", "平均分", "得分率", "优秀率", "良好率",
                                       "合格率", "不合格率"], rows, align_left=(0,)))
    if sub_blocks:
        out.append("<h3>历次年级 · 各学科四率</h3>")
        out.append("<p class='muted'>按学科分别成表；每次考试一行，四率互斥、相加 100%。</p>")
        out.extend(sub_blocks)

    # 三、历次班级（用户要求 2026-10-11：总分一张表，各学科分别成表并在表上方标学科名称）
    bc = hs.get("by_class") or {}
    if bc:
        out.append("<h3>历次班级 · 总分与各学科</h3>")
        trows = []
        for c in sorted(bc):
            for r in (bc[c].get("total") or []):
                trows.append([c, r["exam"], "%d 人" % r["n"], fmt(r["mean"]), pct(r["score_rate"])])
        if trows:
            out.append("<h4>总分（各班）</h4>")
            out.append(table(["班级", "考试", "人数", "平均分", "得分率"], trows, align_left=(0, 1)))
        for s in subs:
            srows = []
            for c in sorted(bc):
                for r in (bc[c].get("subjects") or {}).get(s, []):
                    srows.append([c, r["exam"], "%d 人" % r["n"], fmt(r["mean"]), pct(r["score_rate"]),
                                  pct(r["excellent_rate"]), pct(r["good_rate"]),
                                  pct(r["qualified_rate"]), pct(r["fail_rate"])])
            if srows:
                out.append("<h4>【%s】历次四率（各班）</h4>" % s)
                out.append(table(["班级", "考试", "人数", "平均分", "得分率", "优秀率", "良好率",
                                  "合格率", "不合格率"], srows, align_left=(0, 1)))
        # 各班总分走势折线（一眼看出班级间此消彼长）
        series = []
        for c in sorted(bc):
            pts = {r["exam"]: r["mean"] for r in (bc[c].get("total") or [])}
            series.append((c, [pts.get(e) for e in exams]))
        if len(series) >= 2:
            out.append(chart(C.line_chart(exams, series,
                                          title="历次各班总分平均走势", unit="总分平均（分）",
                                          sub="横轴=考试次序，每班一条线", value_nd=1),
                             "各班折线的高低与斜率反映班级间差距及其变化。"))
    return "".join(out)


def section_cross(an, s_unused, _item, narr):
    cs = an["cross_subject"]
    if not cs:
        return ""
    out = []
    rows = [[r["subject"], fmt(r["mean"]), fmt(r["full"]), pct(r["score_rate"]), pct(r["pass_rate"]),
             pct(r["excellent_rate"]), pct(r.get("good_rate")), pct(r.get("qualified_rate")),
             pct(r.get("fail_rate")), pct(r["low_rate"]), fmt(r["std"]), r["shape"]]
            for r in cs["table"]]
    out.append(table(["学科", "平均分", "满分", "得分率", "及格率", "优秀率", "良好率", "合格率",
                      "不合格率", "低分率", "标准差", "形态"], rows, align_left=(0, 11)))

    subjects = [r["subject"] for r in cs["table"]]
    cls_names = []
    for sub in subjects:
        for c in an["results"][sub]["comparison"]["by_class"]:
            if c["name"] not in cls_names:
                cls_names.append(c["name"])
    if cls_names:
        series = []
        for c in cls_names:
            vals = []
            for sub in subjects:
                hit = [x for x in an["results"][sub]["comparison"]["by_class"] if x["name"] == c]
                vals.append(round(hit[0]["score_rate"] * 100, 1) if hit else None)
            series.append((c, vals))
        out.append(chart(C.grouped_bar_chart(subjects, series,
                                             title="跨学科得分率对比（按班级分组）", unit="得分率（%）",
                                             sub="纵轴统一为得分率，便于跨学科比较",
                                             value_nd=1, rotate_labels=len(subjects) > 5),
                         "横轴=学科，纵轴=得分率；不同颜色为不同班级。"))
        radar_series = []
        for c in cls_names:
            vals = []
            for sub in subjects:
                hit = [x for x in an["results"][sub]["comparison"]["by_class"] if x["name"] == c]
                vals.append(hit[0]["score_rate"] if hit else 0)
            radar_series.append((c, vals))
        out.append(chart(C.radar_chart(subjects, radar_series, title="跨学科班级雷达图", h=440,
                                       sub="各轴=学科得分率（0–1），每班一个多边形"),
                         "越靠外圈的学科是该班的相对优势；缺口方向即短板学科。"))

    # 三处「各学科…」清单（用户要求 2026-10-11）：**按学科分别成表**，表上方标学科名称。
    any_kp = any(an["results"][sub]["knowledge_points"] for sub in subjects)
    kp_blocks, weak_blocks, q_blocks = [], [], []
    for sub in subjects:
        ks = cs["top_knowledge"].get(sub, [])
        if ks:
            rows = [[k["kp"], pct(k["rate"]), k["level"],
                     "、".join(q_label(q) for q in k["questions"])] for k in ks]
            kp_blocks.append("<h4>【%s】TOP3 薄弱知识点</h4>" % sub
                             + table(["知识点", "平均得分率", "等级", "涉及题目"], rows,
                                     align_left=(0, 3)))
        if not ks:
            # 没有知识点数据时（用户要求 2026-10-11）：退回用**逐题得分率**给出该学科最薄弱的前 3 道题
            qs = an["results"][sub].get("questions") or []
            wrows = [[q_label(q["q"]), fmt(q["full"]), pct(q.get("rate_all") or 0),
                      q.get("level_all") or "-"]
                     for q in sorted(qs, key=lambda x: x.get("rate_all") or 0)[:3]]
            if wrows:
                weak_blocks.append("<h4>【%s】薄弱试题 TOP3</h4>" % sub
                                   + table(["题号", "满分", "得分率", "等级"], wrows, align_left=(0,)))
        qs2 = cs["top_questions"].get(sub, [])
        if qs2:
            rows2 = [[q_label(q["q"]), pct(q["rate"])] + ([q["kp"]] if any_kp else [])
                     for q in qs2]
            q_blocks.append("<h4>【%s】TOP3 共性错题</h4>" % sub
                            + table(["题号", "得分率"] + (["知识点"] if any_kp else []), rows2,
                                    align_left=((0, 2) if any_kp else (0,))))

    if kp_blocks:
        out.append("<h3>各学科 TOP3 薄弱知识点</h3>")
        out.extend(kp_blocks)
        danger_n, weak_n = [], []
        for sub in subjects:
            kps = an["results"][sub]["knowledge_points"]
            danger_n.append(len([k for k in kps if k["level"] == "危险"]))
            weak_n.append(len([k for k in kps if k["level"] == "薄弱"]))
        if any(danger_n) or any(weak_n):
            out.append(chart(C.stacked_bar_chart(
                subjects, [("危险知识点(<60%)", danger_n), ("薄弱知识点(60–75%)", weak_n)],
                title="各学科薄弱知识点数量对比", unit="知识点数量（个）",
                sub="红色为高危知识点，橙色为薄弱知识点；柱顶为合计数量",
                value_nd=0), "横轴=学科，纵轴=知识点个数；柱越高说明该学科需要补的知识块越多。"))
    elif weak_blocks:
        out.append("<h3>各学科 · 薄弱试题 TOP3</h3>")
        out.append("<p class='muted'>按<b>每题得分率</b>分别给出各学科最薄弱的前 3 道题"
                   "（等级：共性错题 &lt;60%｜薄弱题 60–75%｜达标题 75–85%｜优势题 ≥85%）。</p>")
        out.extend(weak_blocks)

    if q_blocks:
        out.append("<h3>各学科 TOP3 共性错题</h3>")
        out.extend(q_blocks)

    if cs.get("class_consistency"):
        crows = []
        for c in cs["class_consistency"]:
            ranks = "、".join("%s:%d" % (k, v) for k, v in c["ranks"].items())
            crows.append([c["class"], ranks, fmt(c["avg_rank"]), c["lead_subject"], c["weak_subject"],
                          "是" if c["all_top3"] else "否"])
        out.append("<h3>班级学科排名一致性</h3>")
        out.append(table(["班级", "各科排名", "平均排名", "最强学科", "最弱学科", "各科均在前 3"],
                         crows, align_left=(0, 1, 3, 4)))
    txt = narrative_of(narr, "", "cross") or (narr or {}).get("cross_note")
    if txt:
        out.append(block(txt, "note blue"))
    return "".join(out)


def section_improvement(an, narr):
    imp = (narr or {}).get("improvement") or {}
    subs = an["meta"]["subjects"]
    out = []
    if imp.get("common"):
        out.append("<h3>共性问题（整体形态）</h3>" + ulist(imp["common"]))
    else:
        items = []
        for s in subs:
            r = an["results"][s]
            items.append("%s：整体形态为「%s」，%s" % (s, r["shape"]["type"], r["shape"]["evidence"]))
        out.append("<h3>共性问题（整体形态）</h3>" + ulist(items))
    # 数据源优先级：AI 话术 → 知识点 → **逐题得分率**（用户要求 2026-10-11：
    # 没有知识点数据就按小题得分数据来分析）；三者都没有时整块不出现，也不写占位文字。
    kp_blocks = []
    if imp.get("kp_priority"):
        for s in subs:
            items = imp["kp_priority"].get(s) or []
            if items:
                kp_blocks.append("<h4>%s</h4>" % s + ulist(items))
    else:
        for s in subs:
            item = an["results"][s]
            kps = [k for k in item["knowledge_points"] if k["level"] in ("危险", "薄弱")]
            if kps:
                items = ["P%d · %s（%s，%s）—— 涉及 %s"
                         % (k["priority"], k["kp"], pct(k["rate"]), k["level"],
                            "、".join(q_label(q) for q in k["questions"]))
                         for k in kps[:8]]
            else:
                # 逐题数据在、知识点缺失 → 退回按**每题得分率**升序给出讲评清单
                worst = sorted(item.get("questions") or [],
                               key=lambda q: q.get("rate_all") or 0)[:8]
                items = ["P%d · 第%s题（%s，得分率 %s，满分 %s 分）"
                         % (i, q_label(q["q"]), q.get("level_all") or "-",
                            pct(q.get("rate_all") or 0), fmt(q["full"]))
                         for i, q in enumerate(worst, 1)]
            if items:
                kp_blocks.append("<h4>%s</h4>" % s + ulist(items))
    if kp_blocks:
        has_kp_any = (any(an["results"][s]["knowledge_points"] for s in subs)
                      or bool(imp.get("kp_priority")))
        out.append("<h3>%s</h3>"
                   % ("知识点薄弱点（讲评优先级）" if has_kp_any
                      else "薄弱题讲评优先级（按小题得分率）"))
        out.extend(kp_blocks)
    out.append("<h3>重点学生</h3>")
    if imp.get("students"):
        for s in subs:
            out.append("<h4>%s</h4>" % s + ulist(imp["students"].get(s) or []))
    else:
        for s in subs:
            lst = an["results"][s]["individuals"]["lists"]
            items = []
            for k in ("进步榜", "尖子生", "临界优秀", "临界及格", "学困生", "需关注名单"):
                v = lst.get(k) or []
                if v:
                    items.append("**%s**（%d 人）：%s" % (k, len(v), "、".join(x["name"] for x in v[:12])))
            if not items:
                items = ["暂无可列名单。"]
            out.append("<h4>%s</h4>" % s + ulist(items))
    if imp.get("actions"):
        out.append("<h3>行动清单</h3>" + ulist(imp["actions"], "note"))
    return "".join(out)


# --------------------------------------------------------------------------- #
# 主渲染
# --------------------------------------------------------------------------- #
def build_html(an, narr=None, exam_name=None, gen_charts=True, xl_name=None):
    raw_narr = narr or {}
    narr = sanitize_narrative(raw_narr)
    # 重建知网引用登记表：每次渲染前清空，避免跨报告污染（同一模块进程连续渲染多份报告时）
    global _CNKI_REFS
    _CNKI_REFS = {}
    for r in (raw_narr.get("references") or []):
        if not isinstance(r, dict):
            continue
        author, year, title, url = r.get("author"), r.get("year"), r.get("title"), r.get("url")
        if author and year and title and url:
            _CNKI_REFS[(author, str(year))] = (title, url, r.get("source"))
    meta = an["meta"]
    exam_name = exam_name or meta["exam_name"]
    subs = meta["subjects"]
    multi = len(subs) > 1
    # 注：`xl_name` 参数保留仅为兼容旧调用；报告正文已不再引用 Excel 文件名
    # （原先写在附录「交付物与脚本说明」里，现已移出报告）。
    parts = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             "<title>%s_%s_成绩分析报告</title>" % (esc(exam_name), esc(meta["subject_scope_label"])),
             "<style>%s</style></head><body><div class='page'>" % CSS]

    # 封面
    parts.append('<header class="cover"><h1>%s</h1>' % esc(exam_name + " · 成绩分析报告"))
    parts.append('<div class="sub">学科范围：%s　|　分析班级：%s</div>'
                 % (esc(meta["subject_scope_label"]), esc(meta["focus_class"])))
    parts.append('<div class="tags">%s</div>' % "".join("<span class='tag'>%s</span>" % esc(s) for s in subs))
    parts.append('<div class="metaline">')
    for k, v in (("考试名称", exam_name), ("分析学科", "、".join(subs)),
                 ("班级", meta["focus_class"]), ("样本人数", "%d 人" % meta["student_count"]),
                 ("涉及班级", "、".join(meta["classes"]) or "-"),
                 ("任课教师", meta.get("teacher") or "—"), ("考试时间", meta.get("date") or "—"),
                 ("生成时间", meta["generated_at"])):
        parts.append("<div><b>%s：</b>%s</div>" % (esc(k), esc(v)))
    parts.append("</div></header>")

    # 各章内容先算好：章序号统一用中文「一、二、…」，**目录与正文共用同一份序号**
    # （用户要求 2026-10-11：全报告序号体系为 一、（一）、1.、（1）、a.、(a)）
    grade_html = section_grade_overview(an, narr)
    history_html = section_history(an, narr)
    chapters = []          # [(锚点 id, 章节标题, 章节正文 HTML)]
    if grade_html is not None:
        chapters.append(("grade", "年级层 · 班级排名与全年级指标", grade_html))

    # 报告里**不放「数据说明」章节**（用户要求 2026-10-08）：缺失值、统计范围、基准、剔除名单
    # 这些属于数据质量交代，不进正式报告的正文。信息仍在，只是换了出口：
    #   · 满分非用户指定 → 各学科章首小字的「（由成绩分布推断，**待确认**）」
    #   · 历次顺序存疑   → 「核心结论摘要」的 ⚠️ 与维度 6 的红框
    #   · 剔除名单 → Excel「01 阅读说明」逐个点名；其余数据质量交代（data_notes）
    #     既不进报告也不进结果册，只在 analysis.json / 命令行输出 / 对话交付说明里交代
    # 各学科章节（章节名按**实际可用维度**写，不虚报「完整 6 维度」）
    for s in subs:
        item = an["results"][s]
        q_html = section_questions(an, s, item, narr)
        kp_html = section_kp(an, s, item, narr)
        body = []
        src_tag = {"user": "", "inferred": "（由成绩分布推断，**待确认**）",
                   "default": "（按常规 100 分制默认，**待确认**）"}.get(item.get("full_source"), "")
        body.append("<p class='muted'>满分 %g 分%s　及格线 %g　优秀线 %g　低分线 %g</p>"
                    % (item["full"], src_tag, item["pass"], item["excellent"], item["low"]))
        # 各维度小节：序号由 renumber_headings() 统一给（（一）（二）…），
        # 标题里不再重复写「维度 N ·」——两套编号并存会出现「（四）维度 5」这类错位。
        body.append("<h3 id='%s-1'>基础统计量</h3>" % esc(s))
        body.append(section_stats(an, s, item, narr))
        body.append("<h3 id='%s-2'>分数段分布</h3>" % esc(s))
        body.append(section_bands(an, s, item, narr))
        # 逐题得分率 / 知识点热力图没有数据就**整节不生成**（含标题），**也不写「本节未生成」
        # 这类说明小字**——缺失原因属于内部交代，只进对话交付说明（用户要求 2026-10-11）。
        if q_html is not None:
            body.append("<h3 id='%s-3'>逐题得分率</h3>" % esc(s))
            body.append(q_html)
        if kp_html is not None:
            body.append("<h3 id='%s-4'>知识点掌握热力图</h3>" % esc(s))
            body.append(kp_html)
        body.append("<h3 id='%s-5'>对比分析</h3>" % esc(s))
        body.append(section_comparison(an, s, item, narr))
        body.append("<h3 id='%s-6'>%s</h3>" % (
            esc(s), "个体追踪（历次成绩）" if item["individuals"]["mode"] == "history"
            else "个体追踪（横截面分层）"))
        body.append(section_individual(an, s, item, narr))
        chapters.append(("sub-%s" % s, "%s：%s" % (s, chapter_title(an, s)), "".join(body)))

    # 历次成绩对比（年级 / 班级）
    if history_html is not None:
        chapters.append(("history", "历次成绩对比（年级 / 班级）", history_html))

    # 跨学科
    if multi:
        chapters.append(("cross", "跨学科横向对比", section_cross(an, "", None, narr)))

    # 教学改进建议
    chapters.append(("improve", "教学改进建议", section_improvement(an, narr)))

    # 目录（章序号与正文同源；「目录」与「核心结论摘要」本身不带序号）
    # 用户要求 2026-10-11：目录**不要 <ol> 自动生成的 1./2./3. 序号**（改用 <ul> + list-style:none）。
    # 条目里已经写着「一、二、…」，再加一层阿拉伯数字是重复编号。
    toc = ["<nav class='toc'><h3>目录</h3><ul>",
           "<li><a href='#summary'>核心结论摘要</a></li>"]
    for i, (anchor, title, _body) in enumerate(chapters, 1):
        toc.append("<li><a href='#%s'>%s、%s</a></li>" % (esc(anchor), cn_num(i), esc(title)))
    toc.append("</ul></nav>")
    parts.append("".join(toc))

    # 核心结论摘要（用户要求：不编号）
    parts.append("<h2 id='summary'>核心结论摘要</h2>")
    summary = narr.get("summary") or auto_summary(an)
    parts.append(ulist(summary, "callout"))

    # 正文各章：h2 序号用「一、二、…」（与目录同源，缺章节不跳号）；
    # h3 及以下由 renumber_headings() 在收尾时逐级统一编号。
    for i, (anchor, title, body) in enumerate(chapters, 1):
        parts.append("<div class='chapter'></div>")
        parts.append("<h2 id='%s'>%s、%s</h2>" % (esc(anchor), cn_num(i), esc(title)))
        parts.append(body)

    # 报告到此结束。**不放「附录 · 交付物与脚本说明」**——那是给使用者（agent）看的
    # 交付说明（Excel 工作表数、脚本复用命令等），属于内部信息，不进正式报告；
    # 交付时改为在对话回复里说明（见 SKILL.md 「Step 6 · 交付」）。
    # 页脚**只留考试名与生成时间**（用户要求 2026-10-12）：不带任何生成工具/技能标识，
    # 否则老师、家长拿到的正式报告里会出现内部工具名。
    # 文末「参考文献（知网基教溯源）」区块：仅在 narrative 登记了 references 时出现；
    # 篇名可点（链接挂篇名），作者不可点（红线：绝不在作者名上挂 <a>）。
    refs_section = build_cnki_refs_section()
    if refs_section:
        parts.append(refs_section)
    parts.append("<footer>%s 成绩分析报告 · %s</footer>"
                 % (esc(exam_name), esc(meta["generated_at"])))
    parts.append("</div></body></html>")
    return renumber_headings("".join(parts))


# --------------------------------------------------------------------------- #
# PDF 元数据清理（用户要求 2026-10-12）
#
# 无头 Edge/Chrome 打印出来的 PDF，Info 字典里会带上**生成侧**的元数据：
#   /Creator  (Mozilla/5.0 \(Windows NT 10.0; Win64; x64\) ... HeadlessChrome/155.0.0.0 ...)
#   /Producer (Skia/PDF m155)
# 这些字段在「文档属性」里可见（含渲染引擎版本号、无头浏览器标识、操作系统）。
# 交付给老师/家长的 PDF 不该带这些内部信息，因此在生成后统一抹掉。
# 写法上**逐字节等长替换**（内容换成同长度的空格）：
#   · 不改文件长度 → xref / xref stream 里的对象偏移全部保持有效，PDF 不受伤；
#   · 只动 Info 里那几个键的字符串内容，正文、字体、图片、页面结构一个字节不碰。
# 幂等：重复调用不会二次破坏（替换后已无匹配不到的原值，仍是等长空格）。
_SCRUB_INFO_KEYS = re.compile(rb"/(Creator|Producer|Author|Subject|Keywords)(?=[\s/(<])")
# 抹完之后仍应完全消失的生成侧标识（用于自检，不作为替换依据）
_SCRUB_FINGERPRINTS = (b"Mozilla", b"HeadlessChrome", b"Skia/PDF", b"AppleWebKit",
                       b"Windows NT", b"Chromium")


def scrub_pdf_metadata(pdf_path: str) -> bool:
    """把 PDF Info 里的生成侧元数据抹成空白（等长替换，不动其它字节）。

    返回 True 表示确实改写了文件。任何异常都吞掉并返回 False——
    PDF 元数据清理是**加分项**，绝不能因为它让整份 PDF 作废。
    """
    try:
        with open(pdf_path, "rb") as fh:
            data = bytearray(fh.read())
    except OSError:
        return False
    changed = False
    for m in _SCRUB_INFO_KEYS.finditer(bytes(data)):
        i = m.end()
        while i < len(data) and data[i] in b" \t\r\n":
            i += 1
        if i >= len(data):
            continue
        if data[i] == 0x28:  # '(' 字面字符串
            j = i + 1
            while j < len(data):
                if data[j] == 0x5C:      # 反斜杠转义：跳过下一个字节
                    j += 2
                    continue
                if data[j] == 0x29:      # ')'
                    break
                j += 1
            if j >= len(data) or j - i - 1 <= 0:
                continue
            data[i + 1:j] = b" " * (j - i - 1)
            changed = True
        elif data[i] == 0x3C:  # '<' 十六进制字符串：换成等长 '0'
            j = data.find(b">", i)
            if j < 0 or j - i - 1 <= 0:
                continue
            data[i + 1:j] = b"0" * (j - i - 1)
            changed = True
    if changed:
        try:
            with open(pdf_path, "wb") as fh:
                fh.write(bytes(data))
        except OSError:
            return False
    return changed


def pdf_metadata_leaks(pdf_path: str):
    """回读 PDF，返回仍然残留的生成侧标识列表（空列表 = 干净）。"""
    try:
        with open(pdf_path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return ["<无法读取>"]
    return [kw.decode("ascii") for kw in _SCRUB_FINGERPRINTS if kw in raw]


def try_pdf(html_path: str, pdf_path: str) -> bool:
    candidates = []
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(env, "")
        if not base:
            continue
        for rel in ("Microsoft/Edge/Application/msedge.exe",
                    "Google/Chrome/Application/chrome.exe",
                    "Microsoft/Edge Beta/Application/msedge.exe"):
            p = os.path.join(base, rel)
            if os.path.exists(p):
                candidates.append(p)
    candidates += [shutil.which("msedge"), shutil.which("chrome"), shutil.which("google-chrome")]
    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    # 目标文件上一轮的修改时间：用来判断本次**真的写出了新文件**。
    # 只判断「存在且 >1KB」是不够的——那会把上一轮的旧 PDF 误判成本次成功
    # （实测踩到：连续重跑时 Edge 没写文件，脚本照样打印「PDF 已生成」，
    #  交出去的其实是旧版，报告改了 PDF 却没改）。
    before = os.path.getmtime(pdf_path) if os.path.exists(pdf_path) else None

    def attempt(exe, prof):
        cmd = [exe, "--headless", "--disable-gpu", "--no-sandbox",
               "--print-to-pdf-no-header", "--no-pdf-header-footer",
               "--print-to-pdf=" + os.path.abspath(pdf_path)]
        if prof:
            cmd.append("--user-data-dir=" + prof)
        cmd.append(url)
        subprocess.run(cmd, timeout=120, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return (os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1024
                and os.path.getmtime(pdf_path) != before)

    heads = [e for e in candidates if e]
    dirs = []
    try:
        # 第一轮按原样试（快，一份 ~10 秒）。页眉页脚必须关掉：否则每页页脚都会打印出
        # `file:///C:/…` 的本地路径与打印时间，交付给老师/家长的 PDF 不能带这些。
        # 两个开关都给——老版本认 `--print-to-pdf-no-header`，新版本（Chrome/Edge 120+）
        # 改认 `--no-pdf-header-footer`（用户反馈 2026-10-11）。
        for exe in heads:
            try:
                if attempt(exe, None):
                    return True
            except Exception:
                continue
        # 第二轮兜底：换**独立 profile** 重试。前一个 headless 实例还没退干净时，新调用会把
        # 任务交给那个已在运行的实例并立刻退出——一个字节都不写（上面的 mtime 校验就是为了
        # 防这件事被误判成成功）。独立 profile 能避开这种"移交"，代价是启动慢。
        for exe in heads:
            prof = tempfile.mkdtemp(prefix="wb-pdf-")
            dirs.append(prof)
            try:
                if attempt(exe, prof):
                    return True
            except Exception:
                continue
        return False
    finally:
        for d in dirs:
            shutil.rmtree(d, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="成绩分析报告渲染器（HTML + PDF + Excel 三件套）")
    ap.add_argument("--analysis", required=True, help="analysis.json 路径")
    ap.add_argument("--out", default=None, help="输出 HTML 路径")
    ap.add_argument("--narrative", default=None, help="narrative.json 路径（可选）")
    ap.add_argument("--exam-name", default=None)
    ap.add_argument("--pdf", action="store_true", help="尝试同时导出 PDF（需本机 Edge/Chrome）")
    ap.add_argument("--pdf-out", default=None)
    ap.add_argument("--excel", dest="excel", action="store_true", default=True,
                    help="同时生成 Excel 结果册（默认开启）")
    ap.add_argument("--no-excel", dest="excel", action="store_false", help="不生成 Excel 结果册")
    ap.add_argument("--excel-out", default=None, help="Excel 结果册输出路径")
    args = ap.parse_args(argv)

    with open(args.analysis, "r", encoding="utf-8") as fh:
        an = json.load(fh)
    # narrative.json 是**可选的教师话术文件**：读不出来 / 类型写错都只降级为「无话术」，
    # 绝不因此让 HTML/PDF 一条都产不出来（曾实测：JSON 写坏 → 裸 JSONDecodeError、零产出）。
    narr = {}
    if args.narrative:
        if not os.path.exists(args.narrative):
            print("[警告] 指定的 narrative.json 不存在：%s，已忽略（报告改用自动解读）。" % args.narrative)
        else:
            try:
                with open(args.narrative, "r", encoding="utf-8") as fh:
                    narr = json.load(fh)
                if not isinstance(narr, dict):
                    raise ValueError("顶层必须是 JSON 对象，实际是 %s" % type(narr).__name__)
            except Exception as exc:
                print("[警告] narrative.json 读取失败（%s: %s），已忽略该文件，报告改用自动解读继续生成。"
                      % (type(exc).__name__, exc))
                print("       narrative 是可选项，不应阻塞主交付；修正该文件后重跑即可恢复话术。")
                narr = {}

    meta = an["meta"]
    exam = args.exam_name or meta["exam_name"]
    scope = scope_slug(meta["subjects"])
    default_name = "%s_%s_成绩分析报告.html" % (exam, scope)
    out = args.out or default_name
    xl = args.excel_out or (os.path.splitext(out)[0].replace("成绩分析报告", "成绩分析结果册") + ".xlsx"
                            if "成绩分析报告" in out else "%s_%s_成绩分析结果册.xlsx" % (exam, scope))
    html = build_html(an, narr, exam_name=exam, xl_name=os.path.basename(xl))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("[OK] 报告已生成：%s" % os.path.abspath(out))

    if args.pdf:
        pdf = args.pdf_out or os.path.splitext(out)[0] + ".pdf"
        if try_pdf(out, pdf):
            # 抹掉无头浏览器写进 Info 的生成侧元数据（UA / Skia 引擎版本等）
            scrub_pdf_metadata(pdf)
            leaks = pdf_metadata_leaks(pdf)
            if leaks:
                print("[警告] PDF 属性里仍残留生成侧标识：%s（正文不受影响，可用「打印 → 另存为 PDF」重出）"
                      % "、".join(leaks))
            print("[OK] PDF 已生成：%s" % os.path.abspath(pdf))
        else:
            print("[警告] 未找到可用的 Edge/Chrome，未能自动导出 PDF；"
                  "请用浏览器打开 HTML 后「打印 → 另存为 PDF」（A4，边距 2cm）。")

    if args.excel:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from build_excel import build as build_xlsx
            build_xlsx(args.analysis, xl)
        except Exception as exc:
            print("[警告] 未能生成 Excel 结果册：%s" % exc)
            print("      当前解释器：%s" % sys.executable)
            print("      openpyxl 缺失时请用同一解释器安装：\"%s\" -m pip install openpyxl" % sys.executable)
            print("      HTML/PDF 已正常生成，可稍后单独重跑：python scripts/build_excel.py --analysis analysis.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

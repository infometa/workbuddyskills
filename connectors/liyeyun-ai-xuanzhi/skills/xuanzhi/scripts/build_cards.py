# -*- coding: utf-8 -*-
"""立业云选址 · 载体卡片生成器

把 carrier_search 的返回结果渲染成品牌红卡片式 HTML（图片自动下载并内联为 base64，
绕开宿主内联组件的 CSP 白名单限制）。

用法
----
  python build_cards.py --input cards.json --out cards.html
  python build_cards.py --input cards.json --out widget.html --widget --no-titlebar

输入 --input 可以是两种形态之一：
  1. carrier_search 工具返回的完整 JSON（含 code/msg/data.cards）
  2. 直接是 cards 数组

参数
----
  --query   用户搜索关键词（如「独门独院」），命中的 featureNames 会高亮成红色 chip
  --title   标题左侧文字，默认「<城市> · <关键词>」
  --widget  输出内联组件用的 HTML 片段（去掉 doctype/html/head/body，仅保留 style + 内容）
  --layout  卡片版式：hero（2:1 大图）| compact（左图右文缩略图）
            默认：HTML 文件模式用 hero，--widget 对话内卡片模式用 compact
  --img-w   hero 版大图宽度，默认 460（目标宽高比 2:1）
  --thumb-w compact 版缩略图边长，默认 176（正方形，显示框 104px，1.7x 采样）
  --img-q   图片质量。hero 默认 58（JPEG），compact 默认 74（WEBP）
  --fmt     内联图片格式：auto | jpeg | webp（auto：compact 用 webp、hero 用 jpeg）

为什么 --widget 默认走 compact
-----------------------------
对话内卡片的内联图必须由模型把 base64 **重新写进渲染调用**，它是模型输出 token，
且体积 ∝ 像素面积。平台会把过长（约 >1 万字符）的 base64 折叠成 image_blob_ref 指针，
而指针在渲染调用里不被解析 —— 表现为「卡片出来了、图片空白」。
全宽 400px 的 2:1 大图 = 8 万像素 ≈ 1.6 万字符 base64，必然踩线；
故对话内改用缩略图版式，并让源图略大于显示尺寸（176 源图 / 104 显示框 = 1.7x 采样），
在高分屏（2x）下不会被放大而发糊；同时用 WebP 换取这档分辨率而不超字节预算。

依赖：Pillow（pip install pillow）
"""

import argparse
import base64
import io
import json
import os
import re
import sys
import urllib.request

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
PAGE_TPL = os.path.join(ASSETS, "page_template.html")
CARD_TPL_HERO = os.path.join(ASSETS, "card_block.html")
CARD_TPL_COMPACT = os.path.join(ASSETS, "card_block_compact.html")

TRANSPARENT_GIF = ("data:image/gif;base64,"
                   "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")

# 平台默认头像（不是真人头像），命中则回退为姓氏首字占位
DEFAULT_AVATAR_HINTS = ["avatar_mini", "/static/", "default_avatar", "avatar_default"]

# 载体类型 → 立业云详情页路径段。例：https://liyeyun.com/channel/plant/<card.id>.html
# 载体类型只有三个：厂房 / 仓库 / 办公（没有「园区」「楼宇」等类型）。
# 类型不在表内（或 id 缺失）时不生成链接，避免死链。
TYPE_SLUG = {
    "厂房": "plant",
    "仓库": "warehouse",
    "办公": "office",
}
DETAIL_URL = "https://liyeyun.com/channel/%s/%s.html"


def build_link(c):
    """拼出立业云详情页地址；类型未知或 id 缺失时返回空串。"""
    cid = c.get("id")
    if not cid:
        return ""
    ctype = (c.get("carrierTypeName") or "").strip()
    slug = TYPE_SLUG.get(ctype)
    if not slug:
        sys.stderr.write("[build_cards] 载体类型「%s」无跳转映射，该卡片图片不可点击"
                         "（可在 TYPE_SLUG 中补充）\n" % ctype)
        return ""
    return DETAIL_URL % (slug, cid)

# 高亮 chip 的优先级（出现即优先展示）
PRIORITY = ["独门独院", "独栋", "火车头式厂房", "单层厂房", "可装天车", "有产权",
            "国资产权", "104地块", "带装修", "通燃气", "大电量", "正规园区内",
            "产研一体", "花园式", "低密度", "近地铁", "近高速", "九通一平"]


def die(msg):
    sys.stderr.write("[build_cards] " + msg + "\n")
    sys.exit(1)


def fetch_data_uri(url, width=460, height=230, quality=58, fmt="JPEG"):
    """下载图片 → 居中裁切成 width:height → 缩放 → base64 data URI。

    裁切按目标宽高比做中心裁切，因此 460x230（卡片 2:1）与 80x80（头像方形）通用。

    fmt 支持 JPEG / WEBP。WEBP 在同分辨率下比 JPEG 小 20%~25%（q70 档），
    因此在对话内卡片的字节预算内，WebP 能换来更高的采样分辨率（更清晰）。
    """
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
    except Exception as e:  # 网络/签名过期等，静默降级为占位
        sys.stderr.write("[build_cards] 图片下载失败，使用占位：%s (%s)\n" % (url[:80], e))
        return None
    try:
        from PIL import Image
    except ImportError:
        die("缺少 Pillow，请先安装：pip install pillow")
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    tr = width / height
    ratio = im.width / im.height
    if ratio > tr:
        nw = int(im.height * tr)
        im = im.crop(((im.width - nw) // 2, 0, (im.width - nw) // 2 + nw, im.height))
    else:
        nh = int(im.width / tr)
        im = im.crop((0, (im.height - nh) // 2, im.width, (im.height - nh) // 2 + nh))
    im = im.resize((width, height), Image.LANCZOS)
    buf = io.BytesIO()
    if str(fmt).upper() == "WEBP":
        im.save(buf, "WEBP", quality=quality, method=6)
        prefix = "data:image/webp;base64,"
    else:
        im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
        prefix = "data:image/jpeg;base64,"
    return prefix + base64.b64encode(buf.getvalue()).decode()


def build_avatar(broker, size=80, quality=72, fmt="JPEG"):
    """broker.avatar → 方形内联头像；缺失或为平台默认头像时回退姓氏首字。"""
    name = broker.get("name") or ""
    initial = name[0] if name else "?"
    url = broker.get("avatar") or ""
    if url and any(h in url for h in DEFAULT_AVATAR_HINTS):
        url = ""
    if not url:
        return initial
    data = fetch_data_uri(url, width=size, height=size, quality=quality, fmt=fmt)
    if not data:
        return initial
    return '<img src="%s" alt="%s">' % (data, name)


def split_tags(s):
    if not s:
        return []
    if isinstance(s, list):
        return [str(x).strip() for x in s if str(x).strip()]
    return [t.strip() for t in re.split(r"[,，、]", s) if t.strip()]


def parse_area_from_remark(remark):
    """面积为 0 时从备注里兜底解析「7亩」「340平米」这类数字。"""
    if not remark:
        return "", ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*亩", remark)
    if m:
        return m.group(1) + "亩+", ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:平米|平方米|㎡)", remark)
    if m:
        v = float(m.group(1))
        return ("%.0f㎡" % v), ("%.1f亩" % (v / 666.67) if v >= 1000 else "")
    return "", ""


def build_card(c, query, img_w=0, img_q=58, thumb_w=0, thumb_q=64,
               avatar_size=80, avatar_q=72, fmt="JPEG"):
    feats = split_tags(c.get("featureNames")) or split_tags(c.get("specialTagName"))

    # ---- 高亮 chip：命中关键词优先，其余按优先级补足到 3 个 ----
    hi = [f for f in feats if query and query in f]
    for f in PRIORITY:
        if len(hi) >= 3:
            break
        if f in feats and f not in hi:
            hi.append(f)
    hi = hi[:3]
    rest = [f for f in feats if f not in hi][:6]

    # ---- 角标：优先级标签里挑，避开已高亮的 ----
    badge = [f for f in PRIORITY if f in feats and f not in hi][:2]
    if not badge:
        badge = rest[:2]
    badge_txt = " · ".join(badge)

    # ---- 地址 ----
    addr = "".join([c.get("provinceName") or "", c.get("cityName") or "",
                    c.get("regionName") or ""])
    if c.get("businessDistrictName"):
        addr += " · " + c["businessDistrictName"]

    # ---- 面积 ----
    area = c.get("effectiveArea") or c.get("totalArea") or 0
    if area:
        m1v = "%.0f㎡" % area
        m1s = "%.1f亩" % (area / 666.67) if area >= 2000 else ""
    else:
        m1v, m1s = parse_area_from_remark(c.get("remark"))
        if not m1v:
            m1v, m1s = "待确认", ""

    # ---- 租金 ----
    lo, hi_r = c.get("rentPriceMin") or 0, c.get("rentPriceMax") or 0
    if lo and hi_r and abs(lo - hi_r) > 0.001:
        m2v, m2s = "%.3g~%.3g" % (lo, hi_r), "元/㎡"
    elif lo or hi_r:
        m2v, m2s = "%.3g" % (lo or hi_r), "元/㎡"
    else:
        m2v, m2s = "价格待议", ""

    # ---- 结构 ----
    m3v = c.get("structureNames") or "—"
    lv = c.get("totalNumber") or 0
    hh = c.get("maxFloorHeight") or 0
    if hh and hh >= 2:
        m3s = ("%d层" % lv) if lv else ""
        m3s += (" / 层高%.1fm" % hh)
    else:
        m3s = ("%d层" % lv) if lv else ""

    broker = c.get("broker") or {}
    bname = broker.get("name") or ""
    remark = (c.get("remark") or "").strip()
    if len(remark) > 60:
        remark = remark[:59] + "…"

    chips = "".join('<span class="chip chip-hi">%s</span>' % t for t in hi) + \
            "".join('<span class="chip">%s</span>' % t for t in rest)

    hero = c.get("firstFiles", [{}])[0].get("path") if c.get("firstFiles") else None

    # 只取当前版式需要的那一张，避免多余下载
    img = TRANSPARENT_GIF
    thumb = TRANSPARENT_GIF
    if img_w:
        img = fetch_data_uri(hero, width=img_w, height=img_w // 2,
                             quality=img_q, fmt=fmt) or TRANSPARENT_GIF
    if thumb_w:
        thumb = fetch_data_uri(hero, width=thumb_w, height=thumb_w,
                               quality=thumb_q, fmt=fmt) or TRANSPARENT_GIF

    # 图片外层的可点击链接（详情页）；无映射时输出空串，图片保持不可点
    link = build_link(c)
    link_open = ('<a class="imglink" href="%s" target="_blank" rel="noopener">' % link) if link else ""

    return {
        "IMG": img,
        "THUMB": thumb,
        "LINK_OPEN": link_open,
        "LINK_CLOSE": "</a>" if link_open else "",
        "NAME": c.get("name") or "未命名载体",
        "CTYPE": c.get("carrierTypeName") or "厂房",
        "BADGE": badge_txt,
        "ADDR": addr,
        "M1K": "面积", "M1V": m1v, "M1S": m1s,
        "M2K": "租金", "M2V": m2v, "M2S": m2s,
        "M3K": "结构", "M3V": m3v, "M3S": m3s,
        "CHIPS": chips,
        "REMARK": remark,
        "AVATAR": build_avatar(broker, size=avatar_size, quality=avatar_q, fmt=fmt),
        "BNAME": bname,
        "BAGE": ("从业%s年" % broker.get("brokerProfessionalAge")) if broker.get("brokerProfessionalAge") else "",
        "BPHONE": broker.get("phoneNumber") or "",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="carrier_search 返回 JSON 或 cards 数组")
    ap.add_argument("--out", required=True, help="输出 HTML 路径")
    ap.add_argument("--query", default="", help="用户搜索关键词，用于高亮 chip")
    ap.add_argument("--title", default="", help="标题，默认由城市/关键词拼出")
    ap.add_argument("--widget", action="store_true", help="输出内联组件片段（无 html/head/body）")
    ap.add_argument("--layout", choices=["hero", "compact"], default=None,
                    help="卡片版式；默认 hero（HTML 文件）/ compact（--widget 对话内卡片）")
    ap.add_argument("--img-w", type=int, default=None, help="hero 版大图宽度，默认 460")
    ap.add_argument("--thumb-w", type=int, default=None,
                    help="compact 版缩略图边长，默认 176（显示框 104px，故为 1.7x 采样）")
    ap.add_argument("--img-q", type=int, default=None,
                    help="图片质量；hero 默认 58（JPEG），compact 默认 74（WEBP）")
    ap.add_argument("--fmt", choices=["auto", "jpeg", "webp"], default="auto",
                    help="内联图片格式；auto = hero 用 jpeg、compact 用 webp")
    args = ap.parse_args()

    # 版式决定图片规格：
    #   hero    —— 独立 HTML 文件，图片直写磁盘、不经过模型上下文，可用大图；
    #   compact —— 对话内卡片，base64 会作为模型输出重新写进渲染调用，只能用小图（见文件头说明）。
    layout = args.layout or ("compact" if args.widget else "hero")
    fmt = args.fmt.upper()
    if args.fmt == "auto":
        fmt = "WEBP" if layout == "compact" else "JPEG"

    if layout == "compact":
        # 显示框 104px：源图取 176px（1.7x 采样），在高分屏上不再被放大而发糊；
        # WebP 比同分辨率 JPEG 小 20%~25%，正好用来换这档分辨率而不超字节预算。
        img_w, thumb_w = 0, (args.thumb_w or 176)
        img_q = args.img_q or 74
        avatar_size, avatar_q = 72, 80
        card_tpl_path = CARD_TPL_COMPACT
    else:
        img_w, thumb_w = (args.img_w or 460), 0
        img_q = args.img_q or 58
        avatar_size, avatar_q = 80, 72
        card_tpl_path = CARD_TPL_HERO

    payload = json.load(open(args.input, encoding="utf-8"))
    cards = payload.get("data", {}).get("cards") if isinstance(payload, dict) and "data" in payload else payload
    if not isinstance(cards, list) or not cards:
        die("输入里没有可用的 cards 数组")

    card_tpl = open(card_tpl_path, encoding="utf-8").read()
    m = re.search(r"<!--CARD-->(.*?)<!--/CARD-->", card_tpl, re.S)
    if not m:
        die("卡片模板 %s 缺少 <!--CARD--> 标记块" % os.path.basename(card_tpl_path))
    one = m.group(1)

    blocks = []
    for c in cards:
        h = one
        ctx = build_card(c, args.query, img_w=img_w, img_q=img_q,
                         thumb_w=thumb_w, thumb_q=img_q,
                         avatar_size=avatar_size, avatar_q=avatar_q, fmt=fmt)
        for k, v in ctx.items():
            h = h.replace("{{%s}}" % k, str(v))
        h = re.sub(r"\s*<p class=\"remark\"></p>", "", h)   # 备注为空时不留空行
        h = re.sub(r"<em></em>", "", h)                     # 单位为空时不留空标签
        blocks.append(h)

    page = open(PAGE_TPL, encoding="utf-8").read()
    city = cards[0].get("cityName") or ""
    head_title = args.title or ("%s · %s" % (city, args.query) if args.query else (city or "产业载体"))
    page = page.replace("{{CARDS}}", "\n".join(blocks))
    page = page.replace("{{TITLE}}", re.sub(r"<[^>]+>", "", head_title))
    page = page.replace("{{HEAD_TITLE}}", head_title)
    page = page.replace("{{HEAD_COUNT}}", "%d 条结果" % len(cards))
    page = page.replace("{{SUBTITLE}}",
                        "关键词「%s」· %s%s · 数据来源：立业云选址" %
                        (args.query or "—",
                         cards[0].get("provinceName") or "",
                         city))
    page = page.replace("{{FOOT}}", "经纪人电话可直接联系 · 空地为可自建，现房可即租")

    if args.widget:
        style = re.search(r"<style>(.*?)</style>", page, re.S).group(1)
        # 内联片段会被塞进宿主页面，不能给宿主 body 加 padding/背景：
        # 把排版基线（字体、颜色、行高）从 body 规则挪到 .wrap 上。
        body_rule = re.search(r"\n\s*body\{.*?\}", style, re.S)
        if body_rule:
            blk = body_rule.group(0)
            fam = re.search(r"font-family:[^;]+;", blk)
            style = style.replace(blk, "")
            if fam:
                style = style.replace(
                    ".wrap{max-width:760px;margin:0 auto}",
                    ".wrap{max-width:760px;margin:0 auto;color:var(--tx);\n       %s\n"
                    "       font-size:13px;line-height:1.6;-webkit-font-smoothing:antialiased}"
                    % fam.group(0))
        wrap = re.search(r'<div class="wrap">(.*?)</div>\s*</body>', page, re.S).group(1)
        page = ("<style>%s</style>\n<div class=\"wrap\">%s</div>" % (style, wrap))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    print("[build_cards] 已写出 %s（%d 张卡片，%d 字符，版式=%s）" %
          (args.out, len(cards), len(page), layout))
    if args.widget:
        # 实测：单段 base64 15688 字符 / 片段 20391 字符 → 被折叠成 image_blob_ref，图片空白；
        #       单段 3120 字符 / 片段 13927 字符 → 正常。阈值取两者之间并留余量。
        runs = [len(x) for x in re.findall(r"base64,([A-Za-z0-9+/=]+)", page)]
        if (max(runs) if runs else 0) > 8000 or len(page) > 19000:
            sys.stderr.write(
                "[build_cards] 警告：片段 %d 字符、最长单段 base64 %d 字符，接近平台的折叠阈值，"
                "图片可能变成空白。请调小 --thumb-w（或 --img-w）后重新生成，或改走 HTML 文件模式。\n"
                % (len(page), max(runs) if runs else 0))


if __name__ == "__main__":
    main()

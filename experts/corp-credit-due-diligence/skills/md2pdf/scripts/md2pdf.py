#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2pdf — 将 Markdown 转换为带专业排版与中文支持的 PDF。

流程: Markdown --(python-markdown)--> 带样式 HTML --(playwright/chromium)--> PDF

用法:
    python3 md2pdf.py <input.md> [-o output.pdf] [--title "标题"] [--theme red|blue|plain]
                      [--cover] [--subtitle "副标题"] [--meta "k=v;k=v"]
                      [--toc] [--bookmarks] [--keep-html]

设计要点(均经实测):
  1. 环境通常无 pandoc/wkhtmltopdf/weasyprint, 仅依赖 python `markdown` 库渲染 HTML。
  2. playwright 全局 cli 不可用且默认找 chrome channel, 故直接调用底层 playwright 库 + 自带 chromium。
  3. 容器默认无中文字体, 渲染会变方块, 需提前安装 Noto CJK (见 SKILL.md 的 setup)。
  4. 封面页 / 目录页由本脚本注入 HTML; PDF 书签(outline)由 Chromium 在 `tagged:true` 下
     依据标题层级(h1/h2/h3)自动生成, 无需额外工具。
"""
import argparse
import datetime
import html as _html
import os
import pathlib
import re
import sys

THEMES = {
    "red":   {"main": "#9e1b1b", "th_border": "#7d1515", "zebra": "#faf5f5",
              "quote_bd": "#d9a441", "quote_bg": "#fef9f2", "quote_fg": "#5c4a1a"},
    "blue":  {"main": "#1559b0", "th_border": "#0f4385", "zebra": "#f2f7fc",
              "quote_bd": "#4a90d9", "quote_bg": "#f1f7fd", "quote_fg": "#244a6b"},
    "plain": {"main": "#333333", "th_border": "#555555", "zebra": "#f6f6f6",
              "quote_bd": "#bbbbbb", "quote_bg": "#f7f7f7", "quote_fg": "#444444"},
}


def build_css(c):
    return f"""
* {{ box-sizing: border-box; }}
body {{
  font-family: "Noto Sans CJK SC","Microsoft YaHei","PingFang SC",sans-serif,"Noto Color Emoji";
  color:#1a1a1a; line-height:1.75; font-size:14px;
  max-width:920px; margin:0 auto; padding:40px 48px;
}}
h1 {{ font-size:26px; color:{c['main']}; text-align:center; border-bottom:3px solid {c['main']};
     padding-bottom:16px; margin-bottom:8px; font-weight:700; }}
h2 {{ font-size:19px; color:{c['main']}; border-left:5px solid {c['main']}; padding-left:12px;
     margin-top:32px; margin-bottom:14px; }}
h3 {{ font-size:16px; color:#333; margin-top:22px; border-bottom:1px dashed #ccc; padding-bottom:4px; }}
h4 {{ font-size:14.5px; color:{c['main']}; margin-top:18px; }}
table {{ border-collapse:collapse; width:100%; margin:14px 0; font-size:12.5px; }}
th {{ background:{c['main']}; color:#fff; padding:8px 10px; text-align:left; font-weight:600; border:1px solid {c['th_border']}; }}
td {{ padding:7px 10px; border:1px solid #d9d9d9; vertical-align:top; }}
tr:nth-child(even) td {{ background:{c['zebra']}; }}
blockquote {{ background:{c['quote_bg']}; border-left:4px solid {c['quote_bd']}; margin:14px 0;
             padding:10px 16px; color:{c['quote_fg']}; font-size:13px; border-radius:0 4px 4px 0; }}
strong {{ color:{c['main']}; }}
a {{ color:#1559b0; text-decoration:none; }}
ol,ul {{ padding-left:24px; }}
li {{ margin:5px 0; }}
hr {{ border:none; border-top:1px solid #e0e0e0; margin:26px 0; }}
code {{ background:#f2f2f2; padding:1px 5px; border-radius:3px; font-size:12px; color:#c7254e; }}
pre {{ background:#f6f8fa; padding:12px 14px; border-radius:6px; overflow:auto; }}
pre code {{ background:none; color:#24292e; padding:0; }}
img {{ max-width:100%; }}
@page {{ margin:18mm 14mm; }}

/* ===== 封面页 ===== */
.cover {{
  height: 247mm; display:flex; flex-direction:column;
  justify-content:center; align-items:center; text-align:center;
  page-break-after: always; padding:0 24px;
}}
.cover .cover-band {{ width:64px; height:6px; background:{c['main']}; margin:0 auto 28px; border-radius:3px; }}
.cover h1.cover-title {{
  font-size:34px; color:{c['main']}; border:none; line-height:1.4;
  margin:0 0 14px; padding:0; max-width:640px;
}}
.cover .cover-sub {{ font-size:17px; color:#555; margin-bottom:48px; }}
.cover .cover-meta {{
  font-size:13px; color:#444; line-height:2.1; text-align:left;
  border-top:1px solid #e0e0e0; border-bottom:1px solid #e0e0e0;
  padding:18px 28px; min-width:380px;
}}
.cover .cover-meta b {{ color:{c['main']}; display:inline-block; min-width:84px; }}

/* ===== 目录页 ===== */
.toc-page {{ page-break-after: always; }}
.toc-page h2.toc-title {{ border-left:5px solid {c['main']}; }}
.toc-list {{ list-style:none; padding-left:0; margin-top:18px; }}
.toc-list li {{ margin:7px 0; font-size:14px; }}
.toc-list li.lvl-1 {{ font-weight:700; color:{c['main']}; margin-top:14px; }}
.toc-list li.lvl-2 {{ padding-left:22px; }}
.toc-list li.lvl-3 {{ padding-left:44px; font-size:13px; color:#555; }}
.toc-list a {{ color:inherit; text-decoration:none; }}
"""


def slugify(text, used):
    """生成稳定的 anchor id(支持中文), 保证唯一。"""
    s = re.sub(r"<[^>]+>", "", text)  # 去标签
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"[^\w\u4e00-\u9fff\-]", "", s)
    s = s or "sec"
    base, i = s, 1
    while s in used:
        i += 1
        s = f"{base}-{i}"
    used.add(s)
    return s


def inject_anchors_and_collect_toc(body_html):
    """为 h1/h2/h3 注入 id, 并收集 (level, text, id) 供生成目录。"""
    used = set()
    toc = []

    def repl(m):
        level = int(m.group(1))
        inner = m.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        anchor = slugify(text, used)
        toc.append((level, text, anchor))
        return f'<h{level} id="{anchor}">{inner}</h{level}>'

    new_html = re.sub(r"<h([123])>(.*?)</h\1>", repl, body_html, flags=re.S)
    return new_html, toc


def build_cover(title, subtitle, meta_pairs):
    rows = ""
    for k, v in meta_pairs:
        rows += f'<div><b>{_html.escape(k)}</b>{_html.escape(v)}</div>'
    sub = f'<div class="cover-sub">{_html.escape(subtitle)}</div>' if subtitle else ""
    meta = f'<div class="cover-meta">{rows}</div>' if rows else ""
    return (f'<section class="cover"><div class="cover-band"></div>'
            f'<h1 class="cover-title">{_html.escape(title)}</h1>{sub}{meta}</section>')


def build_toc(toc):
    if not toc:
        return ""
    items = ""
    for level, text, anchor in toc:
        items += (f'<li class="lvl-{level}"><a href="#{anchor}">'
                  f'{_html.escape(text)}</a></li>')
    return (f'<section class="toc-page"><h2 class="toc-title">目录</h2>'
            f'<ul class="toc-list">{items}</ul></section>')


def md_to_html(md_text, title, theme, *, cover=False, subtitle="",
               meta_pairs=None, toc=False):
    try:
        import markdown
    except ImportError:
        sys.exit("[md2pdf] 缺少 python `markdown` 库, 请先: pip install markdown")
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "nl2br", "attr_list"],
    )
    body, toc_data = inject_anchors_and_collect_toc(body)

    css = build_css(THEMES.get(theme, THEMES["red"]))
    parts = []
    if cover:
        parts.append(build_cover(title, subtitle, meta_pairs or []))
    if toc:
        parts.append(build_toc(toc_data))
    parts.append(body)

    return ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<title>{_html.escape(title)}</title>'
            f'<style>{css}</style></head><body>{"".join(parts)}</body></html>')


def find_playwright():
    """定位可 import 的 playwright 库路径(实测全局命令不可用)。

    优先级：环境变量 PLAYWRIGHT_NODE_MODULES > 本脚本内置的多平台常见安装位置。
    """
    candidates = []

    # 1) 环境变量优先（最高优先级）
    env = os.environ.get("PLAYWRIGHT_NODE_MODULES")
    if env:
        candidates.append(env)

    # 2) 相对于本脚本所在目录向上查找（支持随技能包一起分发的情况）
    here = pathlib.Path(__file__).resolve().parent
    candidates.append(str(here / "node_modules"))
    candidates.append(str(here.parent / "node_modules"))

    # 3) 各平台常见安装位置（默认值，仅作兜底）
    home = pathlib.Path.home()
    candidates.extend([
        str(home / ".bg-agent" / "node" / "node_modules"),          # Linux/macOS AnyDev
        str(home / ".cache" / "ms-playwright"),                      # playwright 默认浏览器缓存
        "/root/.bg-agent/node/node_modules",                         # 旧版容器默认（兼容）
        "/usr/lib/node_modules",                                     # Linux 全局
        "/usr/local/lib/node_modules",                               # Linux/macOS 全局
        str(home / "AppData" / "Local" / "ms-playwright"),           # Windows 用户缓存
    ])

    for base in candidates:
        if pathlib.Path(base, "playwright").exists():
            return base
    return None


def html_to_pdf(html_path, pdf_path, footer_text, bookmarks=True):
    """用 node + 底层 playwright 库将 HTML 打印为 PDF。

    bookmarks=True 时启用 tagged PDF, Chromium 会按 h1/h2/h3 层级自动生成书签(outline)。
    """
    import shutil
    import subprocess
    import tempfile

    node = shutil.which("node") or "/usr/local/node/bin/node"
    nm = find_playwright()
    if not nm:
        sys.exit("[md2pdf] 未找到 playwright 库。请执行 `npm install playwright` 安装，"
                 "或设置环境变量 PLAYWRIGHT_NODE_MODULES 指向含 playwright 的 node_modules 目录，"
                 "并确保已安装 chromium（`npx playwright install chromium`）。")

    footer_js = _html.escape(footer_text).replace("'", "\\'")
    outline = "true" if bookmarks else "false"
    script = f"""
const {{ chromium }} = require('{nm}/playwright');
(async () => {{
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://{html_path}', {{ waitUntil: 'networkidle' }});
  await page.pdf({{
    path: '{pdf_path}',
    format: 'A4',
    printBackground: true,
    tagged: {outline},
    outline: {outline},
    margin: {{ top: '14mm', bottom: '14mm', left: '12mm', right: '12mm' }},
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="width:100%;font-size:9px;color:#888;text-align:center;">第 <span class="pageNumber"></span> / <span class="totalPages"></span> 页　·　{footer_js}</div>'
  }});
  await browser.close();
  console.log('OK');
}})().catch(e => {{ console.error(e); process.exit(1); }});
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(script)
        js = f.name
    try:
        r = subprocess.run([node, js], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"[md2pdf] PDF 生成失败:\n{r.stderr.strip()}\n"
                     f"若提示找不到 chromium, 请运行: "
                     f"node {nm}/playwright/cli.js install chromium")
    finally:
        os.unlink(js)


def check_cjk_font():
    """检测系统是否有中文字体, 无则给出明确提示(不强行安装)。"""
    import shutil
    import subprocess
    if not shutil.which("fc-list"):
        return
    try:
        out = subprocess.run(["fc-list", ":lang=zh"], capture_output=True, text=True).stdout
    except Exception:
        return
    if not out.strip():
        sys.stderr.write(
            "[md2pdf][警告] 未检测到中文字体, PDF 中文可能显示为方块!\n"
            "  请先安装: dnf install -y google-noto-sans-cjk-ttc-fonts && fc-cache -f\n"
            "  (Debian/Ubuntu: apt-get install -y fonts-noto-cjk)\n")
    # 彩色 emoji 字体自检(缺失会导致 ✅⚠️❌⭐ 等显示为方块)
    try:
        emoji_out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
    except Exception:
        emoji_out = ""
    if emoji_out and not re.search(r"emoji|color emoji", emoji_out, re.I):
        sys.stderr.write(
            "[md2pdf][警告] 未检测到彩色 emoji 字体, ✅⚠️❌⭐ 等 emoji 可能显示为方块!\n"
            "  请先安装: dnf install -y google-noto-emoji-color-fonts && fc-cache -f\n"
            "  (Debian/Ubuntu: apt-get install -y fonts-noto-color-emoji)\n")


def parse_meta(s):
    """解析 'k=v;k=v' 为有序列表; 支持中文键值。"""
    pairs = []
    if not s:
        return pairs
    for seg in s.split(";"):
        seg = seg.strip()
        if not seg:
            continue
        if "=" in seg:
            k, v = seg.split("=", 1)
            pairs.append((k.strip(), v.strip()))
        else:
            pairs.append(("", seg))
    return pairs


def main():
    ap = argparse.ArgumentParser(description="Markdown -> HTML -> PDF (含中文/封面/目录书签)")
    ap.add_argument("input", help="输入 .md 文件路径")
    ap.add_argument("-o", "--output", help="输出 .pdf 路径(默认同名)")
    ap.add_argument("--title", help="文档标题(封面/PDF元信息, 默认取文件名)")
    ap.add_argument("--theme", default="red", choices=list(THEMES),
                    help="配色主题: red(默认)/blue/plain")
    ap.add_argument("--footer", help="页脚文字(默认取标题)")
    # 新增: 封面
    ap.add_argument("--cover", action="store_true", help="生成封面页")
    ap.add_argument("--subtitle", default="", help="封面副标题")
    ap.add_argument("--meta", default="",
                    help='封面元信息, 形如 "报告类型=xxx;生成时间=2026-06-10;密级=机密"')
    # 新增: 目录与书签
    ap.add_argument("--toc", action="store_true", help="生成目录页(基于 H1/H2/H3)")
    ap.add_argument("--bookmarks", dest="bookmarks", action="store_true",
                    default=True, help="生成 PDF 书签(默认开启)")
    ap.add_argument("--no-bookmarks", dest="bookmarks", action="store_false",
                    help="关闭 PDF 书签")
    ap.add_argument("--keep-html", action="store_true", help="保留中间 HTML 文件")
    args = ap.parse_args()

    src = pathlib.Path(args.input).resolve()
    if not src.exists():
        sys.exit(f"[md2pdf] 输入文件不存在: {src}")

    title = args.title or src.stem
    out_pdf = pathlib.Path(args.output).resolve() if args.output else src.with_suffix(".pdf")
    out_html = out_pdf.with_suffix(".html")
    footer = args.footer or title

    meta_pairs = parse_meta(args.meta)
    # 若开启封面但未给生成时间, 自动补当天日期
    if args.cover and not any(k in ("生成时间", "日期", "date", "Date") for k, _ in meta_pairs):
        meta_pairs.append(("生成时间", datetime.date.today().isoformat()))

    check_cjk_font()

    html = md_to_html(src.read_text(encoding="utf-8"), title, args.theme,
                      cover=args.cover, subtitle=args.subtitle,
                      meta_pairs=meta_pairs, toc=args.toc)
    out_html.write_text(html, encoding="utf-8")

    html_to_pdf(str(out_html), str(out_pdf), footer, bookmarks=args.bookmarks)

    if not args.keep_html:
        out_html.unlink(missing_ok=True)

    size = out_pdf.stat().st_size
    feats = []
    if args.cover:
        feats.append("封面")
    if args.toc:
        feats.append("目录")
    if args.bookmarks:
        feats.append("书签")
    tag = ("  [" + "+".join(feats) + "]") if feats else ""
    print(f"[md2pdf] 完成 ✅  {out_pdf}  ({size/1024:.1f} KB){tag}"
          + (f"  | HTML: {out_html}" if args.keep_html else ""))


if __name__ == "__main__":
    main()

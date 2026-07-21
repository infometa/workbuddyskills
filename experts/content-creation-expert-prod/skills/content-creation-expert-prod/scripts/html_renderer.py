# pyright: reportMissingModuleSource=false
# pyright: reportMissingImports=false
# pyright: reportConstantRedefinition=false
# pyright: reportMissingTypeArgument=false
# pyright: reportPossiblyUnboundVariable=false
"""
Markdown → 响应式 HTML 渲染器
============================
将配图编排后的图文混排 Markdown 转换为 C 端自适应 HTML 页面。

设计要点：
- 移动端优先（Mobile First）响应式布局
- 内嵌全部 CSS，无外部依赖，单文件即可预览
- 图片自适应宽度，优化加载体验
- 使用 Jinja2 模板引擎渲染
- 简洁现代的阅读排版风格
- 支持图片 base64 内嵌，使 HTML 完全自包含（手机离线可看）
"""

import re
import os
import html as _html_mod
import base64
import mimetypes
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def _escape_html(text: str) -> str:
    """HTML 实体转义（防 XSS）。

    对 <, >, &, ", ' 做转义，防止用户可控文本注入 HTML 标签/属性。
    此函数应在 _inline_format 之前调用：先转义原始文本，再解析 Markdown
    语法生成受控的 HTML 标签（如 <strong>），确保只有引擎生成的标签进入 HTML。
    """
    return _html_mod.escape(text, quote=True)

# 尝试导入 Jinja2（可选依赖）
try:
    from jinja2 import Environment, FileSystemLoader, BaseLoader
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


# 模板目录
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def _markdown_to_html_blocks(markdown_text: str) -> list:
    """
    将 Markdown 文本解析为 HTML 块列表

    支持的语法：
    - # / ## / ### 标题
    - ![desc](url) 图片
    - **bold** 粗体
    - *italic* / _italic_ 斜体
    - 空行分段
    - > 引用
    - - / * 无序列表

    Returns:
        list[dict]: [{"type": "h1"|"h2"|"h3"|"p"|"img"|"blockquote"|"list", "content": "..."}]
    """
    blocks = []
    lines = markdown_text.split("\n")
    current_paragraph = []
    list_items = []
    table_rows = []  # 累积 Markdown 表格行

    def flush_paragraph():
        if current_paragraph:
            text = "\n".join(current_paragraph).strip()
            if text:
                blocks.append({"type": "p", "content": _inline_format(text)})
            current_paragraph.clear()

    def flush_list():
        if list_items:
            # ⚠️ key 使用 "list_items" 而非 "items"，
            # 因为 block 是 dict，dict.items 是内置方法，
            # Jinja2 的 block.items 会优先解析为方法对象而非 dict key，
            # 导致 'builtin_function_or_method' object is not iterable
            blocks.append({"type": "list", "list_items": list_items[:]})
            list_items.clear()

    def flush_table():
        if table_rows:
            blocks.append({"type": "table", "rows": table_rows[:]})
            table_rows.clear()

    for line in lines:
        stripped = line.strip()

        # 空行 → 结束段落/列表/表格
        if not stripped:
            flush_table()
            flush_list()
            flush_paragraph()
            continue

        # 水平分隔线（---、***、___，3 个以上连续）
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            flush_table()
            flush_list()
            flush_paragraph()
            blocks.append({"type": "hr"})
            continue

        # 标题（支持 1~6 级，但 HTML 输出最多到 h3，4~6 级降级为 h3）
        h_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if h_match:
            flush_table()
            flush_list()
            flush_paragraph()
            level = min(len(h_match.group(1)), 3)  # 超过3级统一降为h3
            blocks.append({"type": f"h{level}", "content": _inline_format(h_match.group(2))})
            continue

        # 图片
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', stripped)
        if img_match:
            flush_table()
            flush_list()
            flush_paragraph()
            alt = img_match.group(1)
            src = img_match.group(2)
            blocks.append({"type": "img", "alt": alt, "src": src})
            continue

        # AI 图标注行（紧跟图片的 *（AI 生成示意图，仅供参考）* 等）
        # 支持 *...* / **...** / ***...*** / 无星号 等各种模型输出格式，
        # 统一渲染为 .ai-notice（非普通段落/斜体），避免 Markdown 星号残留到 HTML
        ai_notice_match = re.match(
            r'^\*{0,3}[（(]?\s*AI\s*生成示意图[，,]?\s*仅供参考\s*[）)]?\s*\*{0,3}$',
            stripped, re.IGNORECASE
        )
        if ai_notice_match and blocks and blocks[-1].get("type") == "img":
            # 提取纯净文案（剥除所有星号/括号格式，统一输出干净文案）
            notice_text = re.sub(r'[*_]', '', stripped).strip()
            if not notice_text.startswith('（'):
                notice_text = '（' + notice_text
            if not notice_text.endswith('）'):
                notice_text = notice_text + '）'
            # 标准化：确保格式统一为「（AI 生成示意图，仅供参考）」
            notice_text = '（AI 生成示意图，仅供参考）'
            blocks.append({"type": "ai_notice", "content": notice_text})
            continue

        # 行内图片（段落中间有图）
        if re.search(r'!\[([^\]]*)\]\(([^)]+)\)', stripped):
            flush_table()
            flush_list()
            flush_paragraph()
            # 拆分段落和图片
            parts = re.split(r'(!\[[^\]]*\]\([^)]+\))', stripped)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                img_inline = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', part)
                if img_inline:
                    blocks.append({"type": "img", "alt": img_inline.group(1), "src": img_inline.group(2)})
                else:
                    blocks.append({"type": "p", "content": _inline_format(part)})
            continue

        # 引用
        if stripped.startswith(">"):
            flush_table()
            flush_list()
            flush_paragraph()
            quote_text = stripped.lstrip("> ").strip()
            blocks.append({"type": "blockquote", "content": _inline_format(quote_text)})
            continue

        # Markdown 表格行（| col | col |）
        if stripped.startswith("|") and "|" in stripped[1:]:
            flush_list()
            flush_paragraph()
            table_rows.append(stripped)
            continue

        # 到这里说明不是表格行了，先 flush 之前的表格
        flush_table()

        # 无序列表（- xxx 或 * xxx）
        list_match = re.match(r'^[-*]\s+(.+)$', stripped)
        if list_match:
            flush_paragraph()
            list_items.append(_inline_format(list_match.group(1)))
            continue

        # 有序列表（1. xxx、2. xxx 等）
        ol_match = re.match(r'^\d+\.\s+(.+)$', stripped)
        if ol_match:
            flush_paragraph()
            list_items.append(_inline_format(ol_match.group(1)))
            continue

        # 普通文本 → 加入段落
        flush_list()
        current_paragraph.append(stripped)

    flush_table()
    flush_list()
    flush_paragraph()
    return blocks


def _inline_format(text: str) -> str:
    """处理行内格式：粗体、斜体、删除线、链接、行内代码

    安全策略：先对原始文本做 HTML 实体转义（防 XSS），再解析 Markdown
    语法生成受控的 HTML 标签。这样用户文本中的 <script> 等会被转义为
    &lt;script&gt;，而引擎生成的 <strong> 等标签则是安全的。

    最后清理所有未被解析的残留 Markdown 格式符号（孤立星号/下划线/反引号），
    确保 HTML 产物中不出现任何原始 Markdown 语法。
    """
    # ⚠️ 防 XSS：先转义，再格式化
    text = _escape_html(text)
    # 行内代码（优先处理，代码块内的 * 等不应被格式化）
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # 粗斜体（***text***）
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # 粗体（**text**）
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体（*text* 或 _text_）
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # ⚠️ 保护 href 中的下划线：先转义 URL 中的 _，防止被斜体正则误匹配
    text = re.sub(
        r'(<a\s+[^>]*href=")([^"]*)(")',
        lambda m: m.group(1) + m.group(2).replace('_', '&#95;') + m.group(3),
        text
    )
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    # 删除线（~~text~~）
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    # 链接（[text](url)）
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    # 图片占位符残留（[IMAGE:n:描述] 未被替换的）→ 静默移除
    text = re.sub(r'\[IMAGE:\d+:[^\]]*\]', '', text)
    # ===== 最终清理：移除未被解析的孤立 Markdown 格式符号 =====
    # 孤立的星号（不在 HTML 标签内的、不构成配对的 * 残留）
    # 策略：只移除行首/行尾的孤立 *（中间出现的 * 可能是合法内容如乘号）
    text = re.sub(r'^\*+\s*', '', text)
    text = re.sub(r'\s*\*+$', '', text)
    return text


def _extract_title(markdown_text: str) -> str:
    """从 Markdown 中提取标题作为页面标题（优先一级，逐级降级，再 fallback 首行文本）

    返回值经过 HTML 转义，可安全用于 <title> 标签。
    """
    # 优先匹配最高级标题
    for level in range(1, 7):
        pattern = rf'^{"#" * level}\s+(.+)$'
        match = re.search(pattern, markdown_text, re.MULTILINE)
        if match:
            title = re.sub(r'[*_`\[\]]', '', match.group(1))
            return _escape_html(title.strip())
    # 兜底：首行非空文本
    for line in markdown_text.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('[') and not stripped.startswith('!'):
            title = re.sub(r'[*_`\[\]#>]', '', stripped)
            if title.strip():
                return _escape_html(title.strip()[:60])
    return "文章预览"


def _sanitize_html_output(html: str) -> str:
    """最终 HTML 产物清洗：移除所有可能残留的 Markdown 格式符号。

    这是 HTML 渲染管线的**终极防线**——无论上游（模型/成员/引擎）输出了什么格式，
    这里都确保交付 HTML 中**不残留任何原始 Markdown 语法**。

    覆盖的 Markdown 语法残留类型：
    1. 星号包裹（*text*、**text**、***text***）
    2. 水平分隔线（---、***、___）
    3. 标题符号（# ## ###）
    4. 引用前缀（> ）
    5. 列表前缀（- 、* 、1. ）
    6. 链接语法（[text](url)）
    7. 图片占位符（[IMAGE:n:描述]）
    8. 反引号（`code`、```block```）
    9. 删除线（~~text~~）

    策略：只在 HTML 标签内容区（<p>...</p>、<li>...</li> 等）内做清洗，
    不碰 <style>、<script>、HTML 属性、base64 data URI 等结构区域。
    """
    # ===== AI 标注专项（优先处理） =====
    # 1a) <p> 内直接残留星号包裹的 AI 标注
    html = re.sub(
        r'(<p[^>]*>)\s*\*{1,3}\s*([（(]\s*AI\s*生成示意图[，,]?\s*仅供参考\s*[）)])\s*\*{1,3}\s*(</p>)',
        r'\1\2\3',
        html, flags=re.IGNORECASE
    )
    # 1b) <em> 内的 AI 标注（被 _inline_format 当斜体解析了）→ 改为 .ai-notice
    html = re.sub(
        r'<p>\s*<em>\s*([（(]\s*AI\s*生成示意图[，,]?\s*仅供参考\s*[）)])\s*</em>\s*</p>',
        r'<p class="ai-notice">\1</p>',
        html, flags=re.IGNORECASE
    )

    # ===== 通用 Markdown 残留清洗（在 HTML 内容标签内操作） =====
    # 使用回调函数，只处理 <p>/<li>/<td>/<th>/<blockquote>/<h1-h3> 内的文本内容
    def _clean_tag_content(match):
        """清洗单个 HTML 标签内的 Markdown 残留"""
        open_tag = match.group(1)
        content = match.group(2)
        close_tag = match.group(3)
        original_content = content

        # 跳过已经是干净 HTML 的内容（含子标签的通常已正确转换）
        # 但仍需处理残留的原始 Markdown 符号

        # 2) 水平分隔线残留（整个标签内容就是 ---/***/___ ）
        if re.match(r'^\s*[-*_]{3,}\s*$', content):
            return ''  # 整段移除（应该已被 _markdown_to_html_blocks 识别为 hr）

        # 3) 标题符号残留（开头的 # ）
        content = re.sub(r'^#{1,6}\s+', '', content)

        # 4) 引用前缀残留（开头的 > ）
        content = re.sub(r'^&gt;\s*', '', content)  # 已被 HTML 转义的 >

        # 5) 列表前缀残留（开头的 - / * / 1. ）
        #    注意：只处理行首的，避免误伤正文中的合法用法
        content = re.sub(r'^[-]\s+', '', content)
        content = re.sub(r'^\d+\.\s+', '', content)

        # 6) 未转换的链接语法 [text](url) → 提取为纯文本
        #    注意：已被 _inline_format 处理过的会是 <a> 标签，这里只处理漏网的
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

        # 7) 图片占位符残留
        content = re.sub(r'\[IMAGE:\d+:[^\]]*\]', '', content)

        # 8) 反引号残留（三反引号代码块标记）
        content = re.sub(r'```[a-zA-Z]*', '', content)
        content = re.sub(r'```', '', content)

        # 9) 删除线残留
        content = re.sub(r'~~(.+?)~~', r'\1', content)

        # 10) 孤立星号/下划线残留（不构成配对的 */_ ）
        #     行首或行尾的孤立 *
        content = re.sub(r'^\*{1,3}\s+', '', content)
        content = re.sub(r'\s+\*{1,3}$', '', content)
        #     完整包裹但未被解析的 *text*（可能是转义后的 &ast; 等情况）
        content = re.sub(r'^\*{1,3}(.+?)\*{1,3}$', r'\1', content)

        content = content.strip()
        if not content:
            return ''  # 清洗后为空则整个标签移除
        if content == original_content:
            return match.group(0)  # 无变化则原样返回
        return f'{open_tag}{content}{close_tag}'

    # 对内容标签逐个清洗（不碰 style/script/img 等）
    html = re.sub(
        r'(<(?:p|li|td|th|blockquote|h[1-6])[^>]*>)(.*?)(</(?:p|li|td|th|blockquote|h[1-6])>)',
        _clean_tag_content,
        html, flags=re.DOTALL
    )

    # ===== 最终清理：移除空标签（清洗后变空的段落/列表项） =====
    html = re.sub(r'<p[^>]*>\s*</p>', '', html)
    html = re.sub(r'<li>\s*</li>', '', html)
    # 清理连续空行
    html = re.sub(r'\n{3,}', '\n\n', html)

    return html


def render_article_html(markdown_text: str, title: str = "") -> str:
    """
    将图文混排 Markdown 转为响应式 HTML

    Args:
        markdown_text: 含 ![desc](url) 的 Markdown 文本
        title: 文章标题（用于 HTML <title>），为空则自动从 MD 提取

    Returns:
        完整的 HTML 字符串（含内嵌 CSS，移动端自适应）
    """
    if not title:
        title = _extract_title(markdown_text)

    blocks = _markdown_to_html_blocks(markdown_text)

    # 优先使用 Jinja2 模板
    if HAS_JINJA2 and TEMPLATES_DIR.exists():
        template_file = TEMPLATES_DIR / "article.html"
        if template_file.exists():
            env = Environment(
                loader=FileSystemLoader(str(TEMPLATES_DIR)),
                autoescape=False,  # HTML 内容已预处理，不需要自动转义
            )
            template = env.get_template("article.html")
            html = template.render(title=title, blocks=blocks)
            return _sanitize_html_output(html)

    # 降级：内置模板字符串（无 Jinja2 时使用）
    return _sanitize_html_output(_render_fallback(title, blocks))


def _render_table_html(rows: list) -> str:
    """
    将 Markdown 表格行列表渲染为 HTML <table>
    
    rows 格式如：
    ["| 标题1 | 标题2 |", "|------|------|", "| 数据1 | 数据2 |"]
    """
    def _parse_row(row_str):
        """解析单行为 cell 列表"""
        cells = row_str.strip().strip("|").split("|")
        return [_inline_format(cell.strip()) for cell in cells]

    def _is_separator(row_str):
        """判断是否为分隔行 |---|---|"""
        cells = row_str.strip().strip("|").split("|")
        return all(re.match(r'^[\s:]*-+[\s:]*$', c.strip()) for c in cells if c.strip())

    if not rows:
        return ""

    html = '<div class="table-wrapper"><table>'
    header_done = False

    for i, row in enumerate(rows):
        if _is_separator(row):
            continue  # 跳过分隔行

        cells = _parse_row(row)

        if not header_done and i == 0:
            # 第一行作为表头
            html += "<thead><tr>"
            html += "".join(f"<th>{c}</th>" for c in cells)
            html += "</tr></thead><tbody>"
            header_done = True
        else:
            html += "<tr>"
            html += "".join(f"<td>{c}</td>" for c in cells)
            html += "</tr>"

    if header_done:
        html += "</tbody>"
    html += "</table></div>"
    return html


def _render_fallback(title: str, blocks: list) -> str:
    """内置降级渲染（无 Jinja2 依赖时使用）"""
    body_parts = []
    for block in blocks:
        btype = block["type"]
        if btype == "hr":
            body_parts.append('<hr>')
        elif btype in ("h1", "h2", "h3"):
            body_parts.append(f'<{btype}>{block["content"]}</{btype}>')
        elif btype == "p":
            body_parts.append(f'<p>{block["content"]}</p>')
        elif btype == "img":
            # 防 XSS：alt 和 src 做 HTML 属性转义（防 " onload="alert(1) 等注入）
            alt = _escape_html(block.get("alt", ""))
            src = _escape_html(block.get("src", ""))
            body_parts.append(
                f'<figure><img src="{src}" alt="{alt}" loading="lazy">'
                f'</figure>'
            )
        elif btype == "blockquote":
            body_parts.append(f'<blockquote>{block["content"]}</blockquote>')
        elif btype == "ai_notice":
            body_parts.append(f'<p class="ai-notice">{_escape_html(block["content"])}</p>')
        elif btype == "list":
            items = "".join(f"<li>{item}</li>" for item in block.get("list_items", []))
            body_parts.append(f"<ul>{items}</ul>")
        elif btype == "table":
            body_parts.append(_render_table_html(block["rows"]))

    body_html = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.8;color:#1a1a1a;background:#fff;padding:0}}
.article-container{{max-width:720px;margin:0 auto;padding:24px 20px 60px}}
h1{{font-size:1.8rem;font-weight:700;margin:32px 0 16px;line-height:1.3}}
h2{{font-size:1.4rem;font-weight:600;margin:28px 0 12px;line-height:1.4;border-left:4px solid #333;padding-left:12px}}
h3{{font-size:1.15rem;font-weight:600;margin:20px 0 10px}}
p{{margin:12px 0;text-align:justify}}
figure{{margin:20px 0;text-align:center}}
figure img{{width:100%;max-width:100%;height:auto;border-radius:8px;display:block}}
figcaption{{font-size:0.85rem;color:#666;margin-top:8px;font-style:italic}}
blockquote{{border-left:4px solid #e0e0e0;padding:12px 16px;margin:16px 0;color:#555;background:#f9f9f9;border-radius:0 8px 8px 0}}
ul{{margin:12px 0;padding-left:24px}}
li{{margin:6px 0}}
a{{color:#1a73e8;text-decoration:none}}
a:hover{{text-decoration:underline}}
strong{{font-weight:600}}
em{{font-style:italic;color:#555}}
del{{text-decoration:line-through;color:#999}}
hr{{border:none;border-top:1px solid #e0e0e0;margin:32px 0}}
.ai-notice{{font-size:0.8rem;color:#999;text-align:center;margin-top:4px;font-style:italic}}
.table-wrapper{{overflow-x:auto;margin:16px 0}}
table{{width:100%;border-collapse:collapse;font-size:0.9rem}}
th{{background:#f5f5f5;font-weight:600;text-align:left;padding:10px 12px;border-bottom:2px solid #ddd}}
td{{padding:8px 12px;border-bottom:1px solid #eee}}
tr:hover td{{background:#fafafa}}
code{{background:#f4f4f4;padding:2px 6px;border-radius:3px;font-size:0.9em}}
@media(max-width:768px){{
  .article-container{{padding:16px 16px 40px}}
  h1{{font-size:1.5rem;margin:24px 0 12px}}
  h2{{font-size:1.2rem}}
  figure{{margin:16px -16px}}
  figure img{{border-radius:0}}
  figcaption{{padding:0 16px}}
}}
</style>
</head>
<body>
<div class="article-container">
{body_html}
</div>
</body>
</html>"""


# ==================== 图片 Base64 内嵌 ====================

# 下载单张图片的超时（秒）
_IMG_DOWNLOAD_TIMEOUT = 30
# 并发下载线程数
_IMG_DOWNLOAD_WORKERS = 5
# 单张图片最大体积限制（10MB），超过则保留原始 URL
_IMG_MAX_SIZE = 10 * 1024 * 1024


def _download_image_to_base64(url: str):
    """
    下载远程图片并返回 base64 data URI 字符串。
    失败或超限返回 None（保留原始 URL）。
    """
    try:
        resp = requests.get(url, timeout=_IMG_DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()

        # 读取内容并检查大小
        content = resp.content
        if len(content) > _IMG_MAX_SIZE:
            return None

        # 推断 MIME 类型：优先从 Content-Type 取，其次从 URL 后缀推断
        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
        if not content_type or content_type == "application/octet-stream":
            # 从 URL 路径推断（去掉查询参数）
            path = url.split("?")[0]
            guessed = mimetypes.guess_type(path)[0]
            content_type = guessed or "image/jpeg"

        encoded = base64.b64encode(content).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
    except Exception:
        return None


def _local_image_to_base64(filepath: str):
    """
    读取本地图片文件并返回 base64 data URI 字符串。
    失败返回 None（保留原始路径）。
    """
    try:
        if not os.path.isfile(filepath):
            return None

        file_size = os.path.getsize(filepath)
        if file_size > _IMG_MAX_SIZE:
            return None

        with open(filepath, 'rb') as f:
            content = f.read()

        content_type = mimetypes.guess_type(filepath)[0] or "image/jpeg"
        encoded = base64.b64encode(content).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
    except Exception:
        return None


def embed_images_as_base64(html_content: str) -> str:
    """
    将 HTML 中所有 <img src="..."> 的图片转为 base64 data URI 内嵌。
    使得生成的 HTML 文件完全自包含，无需网络即可在手机浏览器本地查看。

    策略：
    - 处理 http:// 和 https:// 开头的远程图片 URL → 下载后 base64 内嵌
    - 处理本地绝对路径（/ 或 盘符: 开头）→ 直接读取 base64 内嵌
    - 跳过已经是 data: 的 base64 URI
    - 并发下载远程图片，提高效率
    - 下载/读取失败或图片过大（>10MB）则保留原始 URL/路径，不阻断
    - 同一 URL 只处理一次（去重缓存）

    Args:
        html_content: 包含图片引用的完整 HTML 字符串

    Returns:
        图片已内嵌为 base64 的 HTML 字符串
    """
    # 提取所有 img src
    img_pattern = re.compile(r'(<img\s[^>]*src=")([^"]+)(")')
    matches = list(img_pattern.finditer(html_content))

    if not matches:
        return html_content

    # 分类收集：远程 URL 和本地路径
    remote_urls = set()
    local_paths = set()

    for m in matches:
        src = m.group(2)
        if src.startswith("data:"):
            continue  # 已经是 base64，跳过
        elif src.startswith(("http://", "https://")):
            remote_urls.add(src)
        elif src.startswith("/") or (len(src) > 1 and src[1] == ":"):
            local_paths.add(src)

    if not remote_urls and not local_paths:
        return html_content

    # 构建 src → data URI 映射
    src_to_data_uri = {}

    # 并发下载远程图片
    if remote_urls:
        with ThreadPoolExecutor(max_workers=_IMG_DOWNLOAD_WORKERS) as executor:
            future_to_url = {
                executor.submit(_download_image_to_base64, url): url
                for url in remote_urls
            }
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data_uri = future.result()
                    if data_uri:
                        src_to_data_uri[url] = data_uri
                except Exception:
                    pass

    # 读取本地图片
    for filepath in local_paths:
        data_uri = _local_image_to_base64(filepath)
        if data_uri:
            src_to_data_uri[filepath] = data_uri

    if not src_to_data_uri:
        return html_content

    # 替换 HTML 中的图片引用
    def _replace_img_src(match):
        prefix = match.group(1)
        src = match.group(2)
        suffix = match.group(3)
        if src in src_to_data_uri:
            return f'{prefix}{src_to_data_uri[src]}{suffix}'
        return match.group(0)

    result = img_pattern.sub(_replace_img_src, html_content)
    return result

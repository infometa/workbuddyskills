# pyright: reportMissingImports=false
"""
小红书风格 HTML 渲染器（PC 端双栏 UI）
========================================
将图文混排 Markdown 渲染为小红书风格的可交互 HTML 单文件：
- 左侧：图片轮播（黑底 + contain + 浮动圆点指示 + N/M 计数 + 翻页箭头 + 键盘左右翻页）
- 右侧：作者栏 → 标题 + 一句话定位 → 正文（h2/list/p/超链接/加粗保留）→ tag → 时间地点 → 评论区 → 底部互动栏

设计要点：
- 单文件自包含（CSS 内嵌；本地图片转 base64；远程图片保留 URL）
- 响应式：< 960px 自动变上下堆叠
- 评论区数据从参数注入，未传入则使用默认伪数据
- 模板与渲染分离：HTML 模板放在 templates/article_xhs.html，使用 __XX__ 占位符替换

公开函数：
- render_xhs_html(article_md, title=..., **kwargs) -> str

模板占位符：
  __TITLE__ / __TOTAL__ / __SLIDES__ / __DOTS__ /
  __AUTHOR_EMOJI__ / __AUTHOR_NAME__ / __AUTHOR_TAG__ /
  __QUOTE_BLOCK__ / __BODY__ / __TAGS__ /
  __POST_TIME_LOC__ / __COMMENT_COUNT__ / __COMMENTS__ /
  __LIKES__ / __COLLECTS__
"""

import re
import os
import base64
import mimetypes
from pathlib import Path
from html import escape

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "article_xhs.html"


# ---------- 默认评论数据（汽车场景；可由调用方覆盖） ----------
DEFAULT_COMMENTS = [
    {"avatar_emoji": "🚗", "name": "用户A", "time": "1 小时前 上海",
     "content": "这篇横评太及时了，看完直接锁定 2 款候选车型！", "likes": 87, "reply_count": 12},
    {"avatar_emoji": "🔋", "name": "用户B", "time": "3 小时前 北京",
     "content": "换电方案到底值不值得？BaaS 长期来看心里有点别扭…",
     "likes": 56, "reply_count": 8,
     "author_reply": "BaaS 适合短期持有 3-5 年的，长期持有还是整车划算些"},
    {"avatar_emoji": "📱", "name": "用户C", "time": "5 小时前 深圳",
     "content": "智驾代差真的是肉眼可见，但价格贵在这里也合理", "likes": 43, "reply_count": 5},
    {"avatar_emoji": "💰", "name": "用户D", "time": "昨天 22:34 杭州",
     "content": "已经下单，纯视觉智驾够日常通勤了，没必要追求顶配", "likes": 71, "reply_count": 9},
    {"avatar_emoji": "🌟", "name": "用户E", "time": "昨天 18:20 北京",
     "content": "看完直接收藏了！博主下一篇能写下其他车型横评吗？", "likes": 32, "reply_count": 3},
]


# ---------- 工具函数 ----------
def _to_data_uri(path_or_url: str) -> str:
    """本地路径 → data URI；远程 URL 直接返回。"""
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url
    if os.path.isfile(path_or_url):
        mime = mimetypes.guess_type(path_or_url)[0] or "image/png"
        with open(path_or_url, "rb") as fp:
            b64 = base64.b64encode(fp.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return path_or_url


def _render_inline(text: str) -> str:
    """处理内联 markdown：[text](url)、**bold**。
    注意：调用方需自己负责 HTML 转义，本函数只做语法转换。
    """
    # 链接
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>',
        text,
    )
    # 加粗
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def _md_to_html(text: str) -> str:
    """轻量级 MD → HTML 转换，针对小红书图文结构：
    - ## h2 → <h2 class="xhs-h2">
    - - / * 列表 → <ul class="xhs-list"><li>
    - --- 水平分隔线 → 吞掉（小红书无此样式）
    - 普通段落 → <p>
    """
    lines = text.split("\n")
    out = []
    in_list = False
    for line in lines:
        # 水平分割线吞掉
        if re.match(r"^---+\s*$", line):
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        # h2
        h2 = re.match(r"^##\s+(.+)$", line)
        if h2:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f'<h2 class="xhs-h2">{_render_inline(h2.group(1))}</h2>')
            continue
        # list item
        li = re.match(r"^[-*]\s+(.+)$", line)
        if li:
            if not in_list:
                out.append('<ul class="xhs-list">')
                in_list = True
            out.append(f"<li>{_render_inline(li.group(1))}</li>")
            continue
        # 空行
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        # 普通段落
        if in_list:
            out.append("</ul>")
            in_list = False
        out.append(f"<p>{_render_inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _build_slides_html(images):
    """构建图片轮播 slides HTML

    注意：图片下方不再渲染 caption（来源/AI 提示等），保持小红书正文纯粹。
    完整的图片来源信息仍保留在草稿 MD 与交付附件中，用于溯源。
    """
    parts = []
    for i, img in enumerate(images):
        active = " xhs-slide-active" if i == 0 else ""
        parts.append(
            f'    <div class="xhs-slide{active}" data-idx="{i}">\n'
            f'      <img src="{escape(img["src"])}" alt="{escape(img.get("alt", ""))}" loading="lazy"/>\n'
            f'    </div>'
        )
    return "\n".join(parts)


def _build_dots_html(total):
    return "\n".join(
        f'        <span class="xhs-dot{" active" if i == 0 else ""}" data-idx="{i}"></span>'
        for i in range(total)
    )


def _build_tags_html(tags):
    return "\n".join(
        f'          <a class="xhs-tag" href="javascript:void(0)">{escape(t)}</a>'
        for t in tags
    )


def _build_comments_html(comments, author_name):
    parts = []
    for c in comments:
        reply_html = ""
        if c.get("author_reply"):
            reply_html = (
                '        <div class="xhs-comment-reply">\n'
                '          <div class="xhs-comment-row">\n'
                '            <div class="xhs-avatar xhs-avatar-author">🚙</div>\n'
                '            <div class="xhs-comment-body">\n'
                '              <div class="xhs-comment-meta">\n'
                f'                <span class="xhs-comment-name">{escape(author_name)}</span>\n'
                '                <span class="xhs-author-badge">作者</span>\n'
                '              </div>\n'
                f'              <div class="xhs-comment-text">{escape(c["author_reply"])}</div>\n'
                '              <div class="xhs-comment-actions">\n'
                '                <span class="xhs-comment-time">刚刚 北京</span>\n'
                '                <span class="xhs-comment-action">♡ 赞</span>\n'
                '                <span class="xhs-comment-action">💬 回复</span>\n'
                '              </div>\n'
                '            </div>\n'
                '          </div>\n'
                '        </div>'
            )
        expand = ""
        if c.get("author_reply") and c.get("reply_count", 0) > 1:
            expand = f'\n          <div class="xhs-comment-expand">展开 {c["reply_count"] - 1} 条回复 ▾</div>'
        parts.append(
            '    <div class="xhs-comment">\n'
            '      <div class="xhs-comment-row">\n'
            f'        <div class="xhs-avatar">{c.get("avatar_emoji", "👤")}</div>\n'
            '        <div class="xhs-comment-body">\n'
            '          <div class="xhs-comment-meta">\n'
            f'            <span class="xhs-comment-name">{escape(c["name"])}</span>\n'
            '          </div>\n'
            f'          <div class="xhs-comment-text">{escape(c["content"])}</div>\n'
            '          <div class="xhs-comment-actions">\n'
            f'            <span class="xhs-comment-time">{escape(c["time"])}</span>\n'
            f'            <span class="xhs-comment-action">♡ {c.get("likes", 0)}</span>\n'
            f'            <span class="xhs-comment-action">💬 {c.get("reply_count", 0)}</span>\n'
            '          </div>\n'
            f'{reply_html}'
            f'{expand}\n'
            '        </div>\n'
            '      </div>\n'
            '    </div>'
        )
    return "\n".join(parts)


# ---------- 主入口 ----------
def render_xhs_html(
    article_md: str,
    title: str = "",
    author_name: str = "汽车图文创作团队",
    author_tag: str = "汽车博主 · 已认证",
    author_emoji: str = "🚙",
    post_time_loc: str = "刚刚 北京",
    likes: str = "2.3w",
    collects: str = "1.8w",
    comments: list = None,
    show_comments: bool = False,
) -> str:
    """
    将 Markdown 图文渲染为小红书风格 HTML。

    Args:
        article_md: 图文混排 MD 全文（含 ![alt](url) 图片）
        title: 文章标题（不传则从 MD 自动提取 # 一级标题）
        author_name / author_tag / author_emoji: 作者栏信息
        post_time_loc: 发布时间地点
        likes / collects: 互动数（字符串，可带"w"等单位）
        comments: 评论列表（元素结构同 DEFAULT_COMMENTS）；仅在 show_comments=True 时生效
        show_comments: 是否渲染评论区。默认 False（小红书原生截图场景无需假评论区）

    Returns:
        完整 HTML 字符串（单文件，自包含图片 base64）
    """
    if not show_comments:
        comments = []
    elif comments is None:
        comments = DEFAULT_COMMENTS

    md = article_md

    # 1. 提取图片：![alt](url) 后紧跟一行的 *（...）*（caption 可选）
    img_with_caption = re.compile(
        r"!\[(?P<alt>[^\]]*)\]\((?P<url>[^)]+)\)\s*\n(?P<caption>\*[（(][^*]+[)）]\*)",
        re.MULTILINE,
    )
    img_without_caption = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<url>[^)]+)\)")

    images = []
    consumed_spans = []
    for m in img_with_caption.finditer(md):
        images.append({
            "alt": m.group("alt"),
            "url": m.group("url").strip(),
            "caption": m.group("caption").strip("*（）()"),
            "src": "",
        })
        consumed_spans.append(m.span())

    # 找没有 caption 的图（避免与上面重复）
    def _in_consumed(start):
        return any(s <= start < e for s, e in consumed_spans)

    for m in img_without_caption.finditer(md):
        if _in_consumed(m.start()):
            continue
        images.append({
            "alt": m.group("alt"),
            "url": m.group("url").strip(),
            "caption": "",
            "src": "",
        })

    # 转 data URI（本地）/ 保留 URL（远程）
    for img in images:
        img["src"] = _to_data_uri(img["url"])

    # 2. 自动提取标题
    if not title:
        m = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
        title = m.group(1).strip() if m else "小红书图文"

    # 3. 提取一句话定位（首个 > quote）
    quote_match = re.search(r"^>\s+(.+)$", md, re.MULTILINE)
    quote = quote_match.group(1).strip() if quote_match else ""

    # 4. 提取 tag（最后那行 #xxx #yyy ...）
    tag_line_match = re.search(r"^(#\S+(?:\s+#\S+)+)\s*$", md, re.MULTILINE)
    tags = tag_line_match.group(1).split() if tag_line_match else []

    # 5. 提取正文：去掉 # 标题 / > quote / 图片块 / tag 行 / 交付附件区块
    body_md = md
    # 去图片块（含 caption 行）
    body_md = img_with_caption.sub("", body_md)
    body_md = img_without_caption.sub("", body_md)
    # 去一级标题
    body_md = re.sub(r"^#\s+.+\n", "", body_md, count=1, flags=re.MULTILINE)
    # 去 quote
    if quote:
        body_md = re.sub(r"^>\s+.+\n", "", body_md, count=1, flags=re.MULTILINE)
    # 去 tag 行
    if tag_line_match:
        body_md = body_md.replace(tag_line_match.group(1), "")

    # 截断交付附件区块（v2 加固：识别多种元信息起点，保证小红书正文纯净）
    # 起点候选（按优先级）：
    #   ① 二级标题 `## 📋 交付附件` / `## 交付附件`
    #   ② 分隔线 `---` 后紧跟"字数：/配图位清单：/数据来源：/交付前自检：/✅ 交付前自检"等元信息项
    #   ③ 直接以"字数：约 xxx 字"开头的段落
    for marker in [
        r"##\s*📋?\s*交付附件",
        r"##\s*交付附件",
        r"^---+\s*\n\s*-?\s*字数[：:]",
        r"^-?\s*字数[：:]\s*约?\s*\d+\s*字",
        r"^-?\s*配图位清单[：:]",
        r"^-?\s*数据来源[：:]",
        r"^-?\s*✅\s*交付前自检[：:]",
        r"^-?\s*交付前自检[：:]",
    ]:
        m = re.search(marker, body_md, re.MULTILINE)
        if m:
            body_md = body_md[: m.start()]

    # 收尾清理：去掉正文末尾的孤立分隔线 ---
    body_md = re.sub(r"\n---+\s*\n?\s*$", "\n", body_md)

    # 【小红书风格】剥离正文中的"（来源：xxx）"/"（[来源](url)）"等来源标注
    # 保留在草稿中即可，避免在小红书正文里堆砌来源。
    # 支持全角/半角括号，含带超链接、纯文字两种形式。
    #
    # 处理策略（v2 加固）：先针对含 [来源](url) 的括号做精确剥离，
    # 允许括号开头到 [来源] 之间有额外文字（如"多花 6000 块，[来源](url)"）。
    #
    # ⚠️ Markdown 链接的 url 里可能含 `)`，因此不能用 `[^)]*` 简单吞掉；
    #    先用 `\[来源\]\([^\s)]+\)` 精确匹配 [来源](url)，
    #    再向前找最近的 `（` 或 `(`，一并吞掉。
    def _strip_source_paren(text: str) -> str:
        # 迭代式匹配：找到每个 [来源](url) 后，向前寻找最近的括号起点
        pattern = re.compile(r"\[来源\]\([^\s)]+\)")
        result = []
        pos = 0
        while pos < len(text):
            m = pattern.search(text, pos)
            if not m:
                result.append(text[pos:])
                break
            # 从 m.start() 向前找最近未闭合的（ 或 (
            open_idx = -1
            for i in range(m.start() - 1, max(pos - 1, -1), -1):
                ch = text[i]
                if ch in "（(":
                    open_idx = i
                    break
                # 换行/句号视为段落边界，停止向前查找
                if ch in "。！？\n；":
                    break
            if open_idx == -1:
                # 找不到左括号：仅去掉 [来源](url) 本身
                result.append(text[pos:m.start()])
                pos = m.end()
                continue
            # 从 m.end() 向后找对应的右括号
            close_idx = -1
            depth = 1
            for j in range(m.end(), len(text)):
                ch = text[j]
                if ch in "（(":
                    depth += 1
                elif ch in "）)":
                    depth -= 1
                    if depth == 0:
                        close_idx = j
                        break
                if ch == "\n":
                    break
            if close_idx == -1:
                result.append(text[pos:m.start()])
                pos = m.end()
                continue
            # 拼接：pos ~ open_idx（保留），跳过 open_idx ~ close_idx（整块删除）
            result.append(text[pos:open_idx])
            pos = close_idx + 1
        return "".join(result)

    body_md = _strip_source_paren(body_md)
    # 纯文字来源：（来源：xxx）/ (来源:xxx)
    body_md = re.sub(r"[（(]\s*来源\s*[:：][^)）\n]{1,120}[)）]", "", body_md)
    # 清理剥离后可能留下的连续标点，如 "长快 5 米（4950mm），，鲨鱼" → 保留单个逗号
    body_md = re.sub(r"[，,]{2,}", "，", body_md)

    body_html = _md_to_html(body_md.strip())

    # 6. 装配模板
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    quote_block = (
        f'        <div class="xhs-quote">{escape(quote)}</div>\n'
        if quote else ""
    )

    html = template
    # 评论区块：当 comments 为空时整块隐藏
    if comments:
        comments_head_html = f'<div class="xhs-comments-head">共 {len(comments)} 条评论</div>'
        comments_body_html = _build_comments_html(comments, author_name)
        comment_count_str = str(len(comments))
    else:
        comments_head_html = ""
        comments_body_html = ""
        comment_count_str = "0"

    replacements = {
        "__TITLE__": escape(title),
        "__TOTAL__": str(len(images)),
        "__SLIDES__": _build_slides_html(images),
        "__DOTS__": _build_dots_html(len(images)),
        "__AUTHOR_EMOJI__": author_emoji,
        "__AUTHOR_NAME__": escape(author_name),
        "__AUTHOR_TAG__": escape(author_tag),
        "__QUOTE_BLOCK__": quote_block,
        "__BODY__": body_html,
        "__TAGS__": _build_tags_html(tags),
        "__POST_TIME_LOC__": escape(post_time_loc),
        "__COMMENT_COUNT__": comment_count_str,
        "__COMMENTS_HEAD__": comments_head_html,
        "__COMMENTS__": comments_body_html,
        "__LIKES__": escape(likes),
        "__COLLECTS__": escape(collects),
    }
    for k, v in replacements.items():
        html = html.replace(k, v)

    return html

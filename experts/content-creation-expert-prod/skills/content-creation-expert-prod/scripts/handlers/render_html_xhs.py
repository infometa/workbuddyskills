"""
render-html-xhs action handler
================================
将图文混排 Markdown 渲染为**小红书 PC 端双栏 UI** 的 HTML。

与 render-html 的差异：
- render-html：通用文章布局（单栏 720px），适合公众号 / 懂车帝 / 知乎等长文平台
- render-html-xhs：小红书风格双栏（左图轮播 + 右文区 + 评论区 + 底部互动栏），适合小红书图文

参数：
- article_text（必填）：图文混排 MD 全文（图片已替换为 URL/本地路径）
- title（可选）：文章标题，为空则自动从 MD 提取
- output_dir（可选）：本地保存目录，默认当前目录
- author_name / author_tag / author_emoji（可选）：作者栏信息
- post_time_loc（可选）：发布时间地点
- likes / collects（可选）：互动数字符串
- comments（可选）：评论列表，结构 [{"avatar_emoji","name","time","content","likes","reply_count","author_reply"?}]
- show_comments（可选，默认 False）：是否渲染评论区。小红书原生截图场景无需假评论区，
  默认关闭；若需展示样例评论可传 true 或直接提供 comments。

输出：
{
  "status": "success",
  "html_content": "<html>...</html>",
  "html_local_path": "/abs/path/preview.html",
  "md_local_path": "/abs/path/article.md",
  "image_count": 8,
  "platform": "xiaohongshu"
}

⚠️ 与 render-html 不同：本 handler 仅做 base64 内嵌（不走 COS 上传），因为小红书 HTML 主要用于离线预览/截图发布，不需要公网图床。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from html_renderer_xhs import render_xhs_html
from utils import log_info


def handle(params: dict):
    """render-html-xhs handler 入口"""
    article_text = params.get("article_text", "")
    title = params.get("title", "")
    output_dir = params.get("output_dir", os.getcwd())

    if not article_text:
        print(json.dumps({
            "status": "error",
            "error_code": "MissingArticle",
            "error_message": "缺少 article_text 参数"
        }, ensure_ascii=False))
        return

    os.makedirs(output_dir, exist_ok=True)

    # 收集小红书 UI 专属参数
    # 评论区默认关闭：小红书截图场景不需要伪造评论区；若用户显式传 comments 或
    # show_comments=true 则打开。
    user_comments = params.get("comments")
    show_comments = params.get("show_comments", False) or (user_comments is not None)

    render_kwargs = {
        "title": title,
        "author_name": params.get("author_name", "图文创作者"),
        "author_tag": params.get("author_tag", "小红书博主 · 已认证"),
        "author_emoji": params.get("author_emoji", "✨"),
        "post_time_loc": params.get("post_time_loc", "刚刚 北京"),
        "likes": params.get("likes", "2.3w"),
        "collects": params.get("collects", "1.8w"),
        "comments": user_comments,
        "show_comments": show_comments,
    }

    log_info("正在渲染小红书风格 HTML（双栏 UI + 图片轮播{}）...".format(
        "" if not show_comments else " + 评论区"
    ))
    html_content = render_xhs_html(article_text, **render_kwargs)

    # 统计图片
    import re
    image_count = len(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", article_text))

    # 保存 HTML
    html_local_path = os.path.join(output_dir, "preview.html")
    with open(html_local_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    log_info(f"小红书风格 HTML 已保存到: {html_local_path}")

    # 保存 MD（保留原图文）
    md_local_path = os.path.join(output_dir, "article.md")
    with open(md_local_path, "w", encoding="utf-8") as f:
        f.write(article_text)
    log_info(f"MD 已保存到: {md_local_path}")

    result = {
        "status": "success",
        "platform": "xiaohongshu",
        "html_content": html_content,
        "html_local_path": os.path.abspath(html_local_path),
        "md_local_path": os.path.abspath(md_local_path),
        "image_count": image_count,
    }

    print(json.dumps(result, ensure_ascii=False))

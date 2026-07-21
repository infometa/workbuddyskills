"""
render-html action handler
============================
将图文混排 Markdown 渲染为响应式 HTML。

图片处理双模式：
- 有 COS 配置：上传图片到 COS 获取公网 URL，替换 MD/HTML 中的图片路径
- 无 COS 配置：将图片（远程 URL + 本地路径）转为 base64 编码嵌入 HTML

参数：
- article_text（必填）：图文混排 MD 全文（图片已替换为 URL）
- title（可选）：文章标题，为空则自动从 MD 提取
- output_dir（可选）：本地保存目录，默认当前目录

输出：
{
  "status": "success",
  "html_content": "<html>...</html>",
  "html_local_path": "/abs/path/preview.html",
  "md_local_path": "/abs/path/article.md"
}
"""

import json
import os
import re
import sys
import mimetypes
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from html_renderer import render_article_html, embed_images_as_base64
from config import is_cos_available
from cos_client import upload_image
from utils import log_info, log_warn


# 图片下载超时（秒）
_IMG_DOWNLOAD_TIMEOUT = 30
# 并发下载/上传线程数
_IMG_WORKERS = 5
# 单张图片最大体积限制（10MB）
_IMG_MAX_SIZE = 10 * 1024 * 1024


def _fix_parentheses_in_image_urls(md_text):
    """
    预处理器：修复 Markdown 图片 URL 中未编码的括号 `()`。
    Markdown 的 ![](url) 语法中，URL 内的第一个 ) 会提前关闭语法，
    导致包含括号的 URL 被截断（如 xDrive-(4)-full.jpg 被解析为 xDrive-(4）。

    通过正确跟踪括号嵌套深度找到真正的 closing paren，然后编码 URL 内所有括号。
    """
    result = []
    i = 0
    while i < len(md_text):
        # 查找 ![
        if i + 1 < len(md_text) and md_text[i] == '!' and md_text[i+1] == '[':
            # 找到完整 alt text 到 ]
            close_bracket = md_text.find('](', i + 2)
            if close_bracket == -1 or close_bracket + 2 >= len(md_text):
                result.append(md_text[i])
                i += 1
                continue

            alt = md_text[i+2:close_bracket]
            url_start = close_bracket + 2  # after ](

            # 通过跟踪括号深度找到真正的 closing )
            depth = 1
            j = url_start
            while j < len(md_text) and depth > 0:
                if md_text[j] == '(':
                    depth += 1
                elif md_text[j] == ')':
                    depth -= 1
                j += 1

            # depth == 0 时 j 指向第一个 ) 之后的位置
            # 所以 URL 是 md_text[url_start:j-1]
            if depth == 0:
                raw_url = md_text[url_start:j-1]
                # 对 raw_url 中的 ( 和 ) 编码
                encoded_url = raw_url.replace('(', '%28').replace(')', '%29')
                result.append(f'![{alt}]({encoded_url})')
                i = j
                continue

        result.append(md_text[i])
        i += 1

    return ''.join(result)


def _collect_images(article_text):
    """
    解析 Markdown 中所有图片引用，返回图片信息列表。

    Returns:
        list[dict]: [{"original": "原始路径", "type": "remote|local", "alt": "描述"}]
    """
    # 安全网：先修复图片 URL 中未编码的括号
    article_text = _fix_parentheses_in_image_urls(article_text)

    img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    images = []
    seen = set()

    for match in img_pattern.finditer(article_text):
        alt = match.group(1)
        src = match.group(2).strip()

        if src in seen:
            continue
        seen.add(src)

        if src.startswith(("http://", "https://")):
            images.append({"original": src, "type": "remote", "alt": alt})
        elif src.startswith("/") or (len(src) > 1 and src[1] == ":"):
            # 本地绝对路径（Unix / 或 Windows C:\）
            images.append({"original": src, "type": "local", "alt": alt})
        elif src.startswith("data:"):
            # 已经是 base64，跳过
            continue
        else:
            # 其他路径（相对路径等），当本地处理
            images.append({"original": src, "type": "local", "alt": alt})

    return images


def _download_image(url):
    """
    下载远程图片，返回 (bytes, content_type, filename)。
    失败返回 (None, None, None)。
    """
    try:
        resp = requests.get(url, timeout=_IMG_DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()
        content = resp.content

        if len(content) > _IMG_MAX_SIZE:
            log_warn(f"图片过大（{len(content)/1024/1024:.1f}MB），跳过: {url[:80]}")
            return None, None, None

        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
        if not content_type or content_type == "application/octet-stream":
            path = url.split("?")[0]
            guessed = mimetypes.guess_type(path)[0]
            content_type = guessed or "image/jpeg"

        # 从 URL 提取文件名
        filename = url.split("?")[0].split("/")[-1] or "image.jpg"

        return content, content_type, filename
    except Exception as e:
        log_warn(f"下载图片失败: {url[:80]} - {e}")
        return None, None, None


def _read_local_image(filepath):
    """
    读取本地图片文件，返回 (bytes, content_type, filename)。
    失败返回 (None, None, None)。
    """
    try:
        if not os.path.isfile(filepath):
            log_warn(f"本地图片不存在: {filepath}")
            return None, None, None

        file_size = os.path.getsize(filepath)
        if file_size > _IMG_MAX_SIZE:
            log_warn(f"本地图片过大（{file_size/1024/1024:.1f}MB）: {filepath}")
            return None, None, None

        with open(filepath, 'rb') as f:
            content = f.read()

        content_type = mimetypes.guess_type(filepath)[0] or "image/jpeg"
        filename = os.path.basename(filepath)

        return content, content_type, filename
    except Exception as e:
        log_warn(f"读取本地图片失败: {filepath} - {e}")
        return None, None, None


def _upload_images_to_cos(images):
    """
    批量上传图片到 COS，返回 {原始路径: COS公网URL} 映射。

    Args:
        images: _collect_images 返回的图片信息列表

    Returns:
        dict: {原始路径: COS公网URL}，上传失败的不在映射中
    """
    url_map = {}

    def _process_and_upload(img_info):
        """处理单张图片：下载/读取 → 上传 COS"""
        original = img_info["original"]
        img_type = img_info["type"]

        # 获取图片数据
        if img_type == "remote":
            content, content_type, filename = _download_image(original)
        else:
            content, content_type, filename = _read_local_image(original)

        if content is None:
            return original, None

        # 上传到 COS
        result = upload_image(content, filename, content_type)
        if result.get("status") == "success":
            return original, result["image_url"]
        else:
            log_warn(f"COS 上传失败: {original[:60]} - {result.get('error_message', '')}")
            return original, None

    # 并发上传
    with ThreadPoolExecutor(max_workers=_IMG_WORKERS) as executor:
        futures = {
            executor.submit(_process_and_upload, img): img
            for img in images
        }
        for future in as_completed(futures):
            try:
                original, cos_url = future.result()
                if cos_url:
                    url_map[original] = cos_url
            except Exception as e:
                log_warn(f"图片处理异常: {e}")

    return url_map


def _replace_image_urls(text, url_map):
    """
    用 COS URL 替换 Markdown/HTML 中的图片路径。

    Args:
        text: MD 或 HTML 文本
        url_map: {原始路径: COS公网URL} 映射

    Returns:
        替换后的文本
    """
    for original, cos_url in url_map.items():
        text = text.replace(original, cos_url)
    return text


def _strip_appendix(text):
    """
    剥离交付附件区块（## 📋 交付附件 及其后续内容）。
    HTML 只渲染纯正文+配图，交付附件仅保留在 MD 产物中。

    匹配格式（均支持）：
    - 带 --- 分隔线：\\n---\\n## 📋 交付附件...
    - 直接标题：\\n## 📋 交付附件...
    """
    # 模式 1：带 --- 分隔线
    pattern_with_sep = r'\n---\s*\n+## 📋\s*交付附件.*'
    # 模式 2：直接标题（无分隔线，前有空行）
    pattern_bare = r'\n+## 📋\s*交付附件.*'

    stripped = re.sub(pattern_with_sep, '', text, flags=re.DOTALL)
    stripped = re.sub(pattern_bare, '', stripped, flags=re.DOTALL)
    return stripped.rstrip()


def handle(params: dict):
    """render-html handler 入口"""
    article_text = params.get("article_text", "")
    title = params.get("title", "")
    output_dir = params.get("output_dir", os.getcwd())

    # 自动剥离交付附件——HTML 只渲染正文+配图
    article_text_for_html = _strip_appendix(article_text)

    if not article_text:
        print(json.dumps({
            "status": "error",
            "error_code": "MissingArticle",
            "error_message": "缺少 article_text 参数"
        }, ensure_ascii=False))
        return

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 收集文章中的所有图片引用（基于不含附件的正文）
    images = _collect_images(article_text_for_html)
    log_info(f"发现 {len(images)} 张图片（远程: {sum(1 for i in images if i['type']=='remote')}, 本地: {sum(1 for i in images if i['type']=='local')}）")

    # 根据 COS 配置选择图片处理模式
    md_text = article_text  # 用于保存的 MD 文本（保留交付附件）

    if is_cos_available() and images:
        # === 有 COS 配置：上传图片到 COS，获取公网 URL 替换 ===
        log_info("COS 已配置，正在上传图片...")
        url_map = _upload_images_to_cos(images)
        log_info(f"成功上传 {len(url_map)}/{len(images)} 张图片到 COS")

        if url_map:
            # 用 COS URL 替换 MD 中的图片路径（MD 保留附件）
            md_text = _replace_image_urls(article_text, url_map)

        # 渲染 HTML（图片已指向 COS 公网 URL，不含交付附件）
        log_info("正在渲染 HTML（图片指向 COS URL）...")
        html_source = _replace_image_urls(article_text_for_html, url_map) if url_map else article_text_for_html
        html_content = render_article_html(html_source, title=title)

    else:
        # === 无 COS 配置：渲染 HTML 后 base64 嵌入图片 ===
        if not is_cos_available():
            log_info("COS 未配置，将使用 base64 内嵌图片。")
        else:
            log_info("无图片需要处理。")

        # 渲染 HTML（不含交付附件）
        log_info("正在渲染 HTML...")
        html_content = render_article_html(article_text_for_html, title=title)

        # 内嵌图片为 base64（使 HTML 自包含，支持远程 URL 和本地文件）
        log_info("正在内嵌图片为 base64...")
        html_content = embed_images_as_base64(html_content)

    # 保存本地 HTML（始终执行）
    html_local_path = os.path.join(output_dir, "preview.html")
    with open(html_local_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    log_info(f"HTML 已保存到本地: {html_local_path}")

    # 保存本地 MD（始终执行）
    md_local_path = os.path.join(output_dir, "article.md")
    with open(md_local_path, 'w', encoding='utf-8') as f:
        f.write(md_text)
    log_info(f"MD 已保存到本地: {md_local_path}")

    result = {
        "status": "success",
        "html_content": html_content,
        "html_local_path": os.path.abspath(html_local_path),
        "md_local_path": os.path.abspath(md_local_path),
        # 向后兼容：保留字段但始终为空
        "html_url": "",
        "qrcode_file": "",
    }

    # JSON 结果输出到 stdout
    print(json.dumps(result, ensure_ascii=False))

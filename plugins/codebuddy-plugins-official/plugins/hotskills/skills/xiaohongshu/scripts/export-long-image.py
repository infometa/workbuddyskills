#!/usr/bin/env python3
"""
小红书帖子长图导出工具

用法:
    python3 export-long-image.py --posts '<json>' --output output.jpg
    python3 export-long-image.py --posts-file posts.json --output output.jpg

posts JSON 格式:
[
    {
        "title": "帖子标题",
        "author": "作者名",
        "stats": "1.3万赞 5171收藏",
        "desc": "正文摘要，支持\\n换行",
        "images": ["url1", "url2", ...],
        "per_image_text": {
            "1": "第2张图的说明文字（0-indexed）",
            "3": "第4张图的说明文字"
        }
    },
    ...
]

per_image_text 可选：如果原帖文字明确指向某张图，可以把说明放在对应图片上。
未指定 per_image_text 时，所有文字放在该帖第一张图前的文字块中。
"""

import argparse
import json
import os
import sys
import tempfile
import urllib.request
from PIL import Image, ImageDraw, ImageFont

# --- 配置 ---
WIDTH = 800
PAD = 24
LINE_SPACE = 10
FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def find_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def load_font(path, size):
    if path:
        try:
            return ImageFont.truetype(path, size, index=0)
        except Exception:
            pass
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    lines = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        current = ""
        for char in paragraph:
            test = current + char
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width:
                if current:
                    lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)
    return lines


def draw_lines(draw, lines, font, x, y, fill):
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=font)
        y += (bbox[3] - bbox[1]) + LINE_SPACE
    return y


def measure_lines(lines, font, draw):
    h = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line if line else " ", font=font)
        h += (bbox[3] - bbox[1]) + LINE_SPACE
    return h


def make_text_block(title, author_line, desc, font_path, width):
    """白底黑字文字块，模仿小红书原样"""
    title_font = load_font(font_path, 32)
    author_font = load_font(font_path, 20)
    body_font = load_font(font_path, 24)

    tmp = Image.new("RGB", (width, 10))
    draw = ImageDraw.Draw(tmp)
    max_w = width - PAD * 2

    title_lines = wrap_text(title, title_font, max_w, draw)
    author_lines = [author_line] if author_line else []
    desc_lines = wrap_text(desc, body_font, max_w, draw) if desc else []

    # 计算高度
    total_h = PAD
    total_h += measure_lines(title_lines, title_font, draw)
    if author_lines:
        total_h += 4
        total_h += measure_lines(author_lines, author_font, draw)
    if desc_lines:
        total_h += 8
        total_h += measure_lines(desc_lines, body_font, draw)
    total_h += PAD

    # 绘制
    block = Image.new("RGB", (width, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(block)

    y = PAD
    y = draw_lines(draw, title_lines, title_font, PAD, y, (33, 33, 33))
    if author_lines:
        y += 4
        y = draw_lines(draw, author_lines, author_font, PAD, y, (153, 153, 153))
    if desc_lines:
        y += 8
        y = draw_lines(draw, desc_lines, body_font, PAD, y, (66, 66, 66))

    return block


def make_image_caption(text, font_path, width):
    """图片上方的小说明文字块"""
    font = load_font(font_path, 20)
    tmp = Image.new("RGB", (width, 10))
    draw = ImageDraw.Draw(tmp)
    lines = wrap_text(text, font, width - PAD * 2, draw)

    h = PAD + measure_lines(lines, font, draw) + 8
    block = Image.new("RGB", (width, h), (245, 245, 245))
    draw = ImageDraw.Draw(block)
    draw_lines(draw, lines, font, PAD, PAD // 2, (100, 100, 100))
    return block


def download_image(url, tmpdir, idx):
    """下载图片到临时目录"""
    ext = ".webp"
    path = os.path.join(tmpdir, f"img_{idx}{ext}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(path, "wb") as f:
                f.write(resp.read())
        return path
    except Exception as e:
        print(f"  警告: 下载失败 {url[:60]}... ({e})", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="小红书帖子长图导出")
    parser.add_argument("--posts", help="Posts JSON string")
    parser.add_argument("--posts-file", help="Posts JSON file path")
    parser.add_argument("--output", "-o", required=True, help="Output JPG path")
    parser.add_argument("--width", type=int, default=800, help="Image width (default 800)")
    parser.add_argument("--quality", type=int, default=88, help="JPEG quality (default 88)")
    args = parser.parse_args()

    global WIDTH
    WIDTH = args.width

    # 读取 posts 数据
    if args.posts:
        posts = json.loads(args.posts)
    elif args.posts_file:
        with open(args.posts_file, "r") as f:
            posts = json.load(f)
    else:
        print("错误: 需要 --posts 或 --posts-file", file=sys.stderr)
        sys.exit(1)

    font_path = find_font()
    if not font_path:
        print("警告: 未找到中文字体，文字可能显示异常", file=sys.stderr)

    sep = Image.new("RGB", (WIDTH, 3), (230, 230, 230))
    pieces = []

    with tempfile.TemporaryDirectory() as tmpdir:
        img_counter = 0
        for pi, post in enumerate(posts):
            title = post.get("title", "")
            author = post.get("author", "")
            stats = post.get("stats", "")
            desc = post.get("desc", "")
            images = post.get("images", [])
            per_image_text = post.get("per_image_text", {})

            # 作者行
            author_line = author
            if stats:
                author_line = f"{author} · {stats}" if author else stats

            # 主文字块
            text_block = make_text_block(title, author_line, desc, font_path, WIDTH)
            pieces.append(text_block)

            # 图片
            for i, url in enumerate(images):
                # 是否有针对这张图的说明
                img_key = str(i)
                if img_key in per_image_text:
                    caption_block = make_image_caption(per_image_text[img_key], font_path, WIDTH)
                    pieces.append(caption_block)

                img_path = download_image(url, tmpdir, img_counter)
                img_counter += 1
                if img_path:
                    try:
                        im = Image.open(img_path).convert("RGB")
                        ratio = WIDTH / im.width
                        im = im.resize((WIDTH, int(im.height * ratio)), Image.LANCZOS)
                        pieces.append(im)
                    except Exception as e:
                        print(f"  警告: 图片处理失败 ({e})", file=sys.stderr)

            # 帖子间分隔线
            if pi < len(posts) - 1:
                pieces.append(sep)

    if not pieces:
        print("错误: 没有内容可拼接", file=sys.stderr)
        sys.exit(1)

    total_h = sum(p.height for p in pieces)
    long_img = Image.new("RGB", (WIDTH, total_h), (255, 255, 255))
    y = 0
    for p in pieces:
        long_img.paste(p, (0, y))
        y += p.height

    long_img.save(args.output, "JPEG", quality=args.quality)
    print(f"完成: {args.output} ({WIDTH}x{total_h})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强版 PDF 水印脚本。

采用更稳的 overlay 方案分层处理：
1. 先保证文字正确显示
2. 再应用旋转
3. 最后尝试透明度（失败则降级为不透明）

相比直接修改原 PDF 的 xref / Contents，对复杂文档更稳。
"""

import os
from io import BytesIO

COMMAND = "watermark"
DESCRIPTION = "为 PDF 添加增强版水印，支持自定义颜色、角度、透明度、字号和间距。"
CATEGORY = "edit"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF 路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 路径"},
    {"name": "text", "type": "str", "required": True, "help": "水印文字"},
    {"name": "font_path", "type": "str", "required": False, "default": "", "help": "字体文件路径（不指定则自动搜索）"},
    {"name": "mode", "type": "str", "required": False, "default": "sparse", "choices": ["sparse", "dense"], "help": "水印模式：sparse 稀疏（页面中心），dense 密集（铺满）"},
    {"name": "font_color", "type": "str", "required": False, "default": "#CCCCCC", "help": "水印颜色（十六进制或颜色名）"},
    {"name": "angle", "type": "float", "required": False, "default": 45, "help": "旋转角度（度）"},
    {"name": "opacity", "type": "float", "required": False, "default": 0.15, "help": "透明度 0-1"},
    {"name": "font_size", "type": "float", "required": False, "default": 50, "help": "字号"},
    {"name": "x_gap", "type": "float", "required": False, "default": 200, "help": "水平间距（dense 模式）"},
    {"name": "y_gap", "type": "float", "required": False, "default": 150, "help": "垂直间距（dense 模式）"},
]


def parse_color(color_str):
    """解析颜色字符串为 (r, g, b) 元组（0-1 范围）。

    支持格式：
    - 十六进制：#FF0000, FF0000
    - 预定义颜色名：red, blue, green, gray 等
    - RGB 数组：[1, 0, 0]
    """
    if isinstance(color_str, (list, tuple)):
        if len(color_str) == 3:
            return tuple(float(c) for c in color_str)
        return (0.5, 0.5, 0.5)

    if isinstance(color_str, str):
        color_str = color_str.strip()

        # 预定义颜色名
        color_names = {
            "red": (1, 0, 0),
            "green": (0, 0.5, 0),
            "blue": (0, 0, 1),
            "black": (0, 0, 0),
            "white": (1, 1, 1),
            "gray": (0.5, 0.5, 0.5),
            "grey": (0.5, 0.5, 0.5),
            "yellow": (1, 1, 0),
            "orange": (1, 0.65, 0),
            "purple": (0.5, 0, 0.5),
            "pink": (1, 0.75, 0.8),
            "cyan": (0, 1, 1),
        }
        if color_str.lower() in color_names:
            return color_names[color_str.lower()]

        # 十六进制颜色
        hex_str = color_str.lstrip("#")
        if len(hex_str) == 6 and all(c in "0123456789abcdefABCDEF" for c in hex_str):
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            return (r, g, b)

    # 默认灰色
    return (0.5, 0.5, 0.5)


def normalize_mediabox(page):
    """规范化页面的 MediaBox，确保原点在 (0, 0)。

    很多 PDF（尤其是扫描件、教材类 PDF）的 MediaBox 原点不在 (0,0)，
    例如 MediaBox: [1915.05, 2706.75, 2430.95, 3435.25]，
    这会导致水印、文本编辑等操作的坐标计算错误。

    本函数将 MediaBox 平移到 (0, 0) 起点，同时调整 CropBox。
    """
    import fitz  # PyMuPDF

    mb = page.mediabox
    if abs(mb.x0) < 0.01 and abs(mb.y0) < 0.01:
        return  # 已经规范化，无需处理

    # 计算偏移量
    dx = -mb.x0
    dy = -mb.y0
    width = mb.x1 - mb.x0
    height = mb.y1 - mb.y0

    # 设置新的 MediaBox（原点归零）
    page.set_mediabox(fitz.Rect(0, 0, width, height))

    # 同步调整 CropBox
    cb = page.cropbox
    new_cb = fitz.Rect(
        cb.x0 + dx,
        cb.y0 + dy,
        cb.x1 + dx,
        cb.y1 + dy,
    )
    # 确保 CropBox 不超出新的 MediaBox
    new_cb = new_cb & fitz.Rect(0, 0, width, height)
    if not new_cb.is_empty:
        page.set_cropbox(new_cb)


def _build_watermark_overlay(page_w, page_h, text, font_name, font_size, color,
                             angle, opacity, mode, x_gap, y_gap):
    """构建单页水印 overlay PDF。"""
    from reportlab.pdfgen import canvas

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))

    # 第三层：最后再尝试透明度，失败则降级为不透明
    if opacity < 1.0 and hasattr(c, "setFillAlpha"):
        try:
            c.setFillAlpha(opacity)
        except Exception:
            pass

    c.setFillColorRGB(color[0], color[1], color[2])
    c.setStrokeColorRGB(color[0], color[1], color[2])
    c.setFont(font_name, font_size)

    if mode == "sparse":
        positions = [(page_w / 2.0, page_h / 2.0)]
    else:
        positions = []
        start_x = -page_w * 0.25
        end_x = page_w * 1.25
        start_y = -page_h * 0.25
        end_y = page_h * 1.25
        y = start_y
        while y <= end_y:
            x = start_x
            while x <= end_x:
                positions.append((x, y))
                x += x_gap
            y += y_gap

    count = 0
    for x, y in positions:
        c.saveState()
        c.translate(x, y)
        # 第二层：文字已稳定后再加旋转
        if angle:
            c.rotate(angle)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        count += 1

    c.save()
    packet.seek(0)
    return packet, count


def verify_watermark(doc, color, mode="dense", sample_pages=2):
    """验证水印是否成功添加（像素级检测）。

    渲染指定页面为图片，检测是否存在水印颜色特征的像素。
    由于水印是半透明的，实际渲染颜色会与背景混合，
    因此使用颜色通道相对优势检测而非精确匹配。

    Args:
        doc: PyMuPDF 文档对象
        color: 水印颜色 (r, g, b)，0-1 范围
        mode: 水印模式 sparse/dense，影响验证阈值
        sample_pages: 采样验证的页数

    Returns:
        dict: 验证结果，包含 verified (bool) 和 details (list)
    """
    total_pages = len(doc)
    pages_to_check = min(sample_pages, total_pages)

    # 选择要验证的页面（首页 + 中间页）
    check_indices = [0]
    if total_pages > 1 and pages_to_check > 1:
        check_indices.append(total_pages // 2)

    details = []
    all_verified = True

    # 确定水印颜色的主导通道
    # 例如红色 (1,0,0) 的主导通道是 R
    target_r = color[0]
    target_g = color[1]
    target_b = color[2]

    for page_idx in check_indices:
        page = doc[page_idx]
        # 低分辨率渲染以加快验证速度
        pix = page.get_pixmap(dpi=72)

        # 统计与水印颜色特征匹配的像素数量
        matching_pixels = 0
        total_pixels = pix.width * pix.height
        samples = pix.samples  # 原始像素数据
        n = pix.n  # 每像素字节数（RGB=3, RGBA=4）

        # 采样检测（每隔几个像素检测一次，提高速度）
        step = max(1, total_pixels // 10000)  # 最多检测 10000 个像素
        for i in range(0, total_pixels, step):
            offset = i * n
            if offset + 2 >= len(samples):
                break
            r = samples[offset] / 255.0
            g = samples[offset + 1] / 255.0
            b = samples[offset + 2] / 255.0

            # 排除纯白（背景）和纯黑（文字）
            if r > 0.94 and g > 0.94 and b > 0.94:
                continue
            if r < 0.06 and g < 0.06 and b < 0.06:
                continue

            # 颜色通道相对优势检测
            # 半透明水印与白色背景混合后，水印颜色的主导通道仍然会高于其他通道
            # 例如红色水印混合后：R > G 且 R > B
            is_match = False

            if target_r > target_g + 0.3 and target_r > target_b + 0.3:
                # 红色系水印：R 通道明显高于 G 和 B
                is_match = r > g + 0.05 and r > b + 0.05 and r > 0.5
            elif target_g > target_r + 0.3 and target_g > target_b + 0.3:
                # 绿色系水印
                is_match = g > r + 0.05 and g > b + 0.05 and g > 0.3
            elif target_b > target_r + 0.3 and target_b > target_g + 0.3:
                # 蓝色系水印
                is_match = b > r + 0.05 and b > g + 0.05 and b > 0.3
            else:
                # 灰色或混合色水印：检测是否有非白非黑的中间色
                # 与纯白背景相比，有水印的区域会偏暗
                avg = (r + g + b) / 3
                is_match = 0.3 < avg < 0.9 and abs(r - g) < 0.15 and abs(g - b) < 0.15

            if is_match:
                matching_pixels += 1

        # 如果匹配像素超过阈值，认为水印存在
        sampled_count = total_pixels // step
        ratio = matching_pixels / max(sampled_count, 1)
        # sparse 模式只有一个水印，占比很小，降低阈值
        threshold = 0.0001 if mode == "sparse" else 0.005
        verified = ratio > threshold

        details.append({
            "page": page_idx,
            "verified": verified,
            "matching_ratio": round(ratio, 6),
            "sampled_pixels": sampled_count,
            "matching_pixels": matching_pixels,
        })

        if not verified:
            all_verified = False

    return {
        "verified": all_verified,
        "details": details,
    }


def add_watermark(input_path, output_path, text, font_path,
                  mode="sparse", font_color="#CCCCCC", angle=45,
                  opacity=0.15, font_size=50, x_gap=200, y_gap=150,
                  font_index=0):
    """为 PDF 添加增强版水印。

    Args:
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径
        text: 水印文字
        font_path: 字体文件路径
        mode: 水印模式 sparse/dense
        font_color: 水印颜色（十六进制或颜色名）
        angle: 旋转角度（度）
        opacity: 透明度 0-1
        font_size: 字号
        x_gap: 水平间距（dense 模式）
        y_gap: 垂直间距（dense 模式）
        font_index: .ttc 字体集合的子字体索引，默认 0

    Returns:
        dict: 操作结果
    """
    import fitz  # PyMuPDF
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfbase import pdfmetrics
    from pdfkit.font_manager import register_reportlab_font

    # 解析颜色
    color = parse_color(font_color)

    base_doc = fitz.open(input_path)
    total_pages = len(base_doc)
    normalized_pages = 0
    for page in base_doc:
        mb = page.mediabox
        if abs(mb.x0) > 0.01 or abs(mb.y0) > 0.01:
            normalize_mediabox(page)
            normalized_pages += 1

    normalized_pdf = BytesIO()
    base_doc.save(normalized_pdf, garbage=4, deflate=True)
    base_doc.close()
    normalized_pdf.seek(0)

    reader = PdfReader(normalized_pdf)
    writer = PdfWriter()

    font_name = "Helvetica"
    if font_path and register_reportlab_font("PdfkitWatermarkFont", font_path):
        font_name = "PdfkitWatermarkFont"

    total_watermarks = 0
    for page in reader.pages:
        page_w = float(page.mediabox.width)
        page_h = float(page.mediabox.height)
        overlay_packet, count = _build_watermark_overlay(
            page_w, page_h, text, font_name, font_size, color,
            angle, opacity, mode, x_gap, y_gap,
        )
        overlay_reader = PdfReader(overlay_packet)
        if overlay_reader.pages:
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)
        total_watermarks += count

    with open(output_path, "wb") as f:
        writer.write(f)

    verify_doc = fitz.open(output_path)
    verification = verify_watermark(verify_doc, color, mode=mode)
    verify_doc.close()

    result = {
        "output_file": output_path,
        "page_count": total_pages,
        "total_watermarks": total_watermarks,
        "normalized_pages": normalized_pages,
        "mode": mode,
        "font_color": font_color,
        "angle": angle,
        "opacity": opacity,
        "font_size": font_size,
        "engine": "reportlab_overlay",
        "verification": verification,
    }

    return result


def handler(params):
    """处理 PDF 水印请求。"""
    from pdfkit.font_manager import resolve_font

    # 必填参数
    input_path = params.get("input", "")
    output_path = params.get("output", "")
    text = params.get("text", "")
    font_path = params.get("font_path", "")

    if not input_path:
        raise ValueError("缺少必填参数: input")
    if not output_path:
        raise ValueError("缺少必填参数: output")
    if not text:
        raise ValueError("缺少必填参数: text")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    # 第一层：先保证文字正确显示，自动字体仍走 font_manager
    if not font_path:
        font_path = resolve_font(text=text)
        if not font_path:
            raise FileNotFoundError("未指定字体路径且未找到可用的系统字体，请通过 --font_path 指定")
    elif not os.path.exists(font_path):
        raise FileNotFoundError(f"字体文件不存在: {font_path}")

    # 可选参数
    mode = params.get("mode", "sparse")
    font_color = params.get("font_color", "#CCCCCC")
    angle = float(params.get("angle", 45))
    opacity = float(params.get("opacity", 0.15))
    font_size = float(params.get("font_size", 50))
    x_gap = float(params.get("x_gap", 200))
    y_gap = float(params.get("y_gap", 150))

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    return add_watermark(
        input_path, output_path, text, font_path,
        mode=mode, font_color=font_color, angle=angle,
        opacity=opacity, font_size=font_size,
        x_gap=x_gap, y_gap=y_gap,
    )


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)

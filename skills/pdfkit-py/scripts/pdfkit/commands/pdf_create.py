#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 创建工具（增强版）。
从 JSON 描述创建 PDF 文档，支持丰富的样式参数和多种元素类型。

支持的元素类型：
  - title: 标题（可自定义字号/颜色/对齐）
  - heading: 多级标题（level 1-4）
  - paragraph: 段落（支持富文本标记）
  - table: 表格（自定义列宽/表头颜色/条纹/边框）
  - image: 图片（支持对齐和标题）
  - list: 列表（有序/无序）
  - spacer: 间距
  - page_break: 分页
  - hr: 水平分割线
  - link: 超链接
  - columns: 多栏布局
  - watermark: 水印文字
  - toc: 目录占位符
  - header/footer: 页眉/页脚
"""

import os
import sys

COMMAND = "pdf_create"
DESCRIPTION = "从 JSON 描述创建 PDF 文档，支持丰富的样式参数和多种元素类型。"
CATEGORY = "edit"
PARAMS = [
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 文件路径"},
    {"name": "page_size", "type": "str", "required": False, "default": "A4", "choices": ["A4", "A3", "letter", "legal"], "help": "页面尺寸"},
    {"name": "orientation", "type": "str", "required": False, "default": "portrait", "choices": ["portrait", "landscape"], "help": "页面方向"},
    {"name": "font_path", "type": "str", "required": False, "help": "自定义字体路径"},
    {"name": "margins", "type": "json", "required": False, "help": "页边距 JSON 对象 {left, right, top, bottom}"},
    {"name": "default_style", "type": "json", "required": False, "help": "默认样式 JSON 对象"},
    {"name": "header", "type": "json", "required": False, "help": "页眉配置 JSON 对象"},
    {"name": "footer", "type": "json", "required": False, "help": "页脚配置 JSON 对象"},
    {"name": "watermark", "type": "json", "required": False, "help": "水印配置 JSON 对象"},
    {"name": "elements", "type": "json", "required": True, "help": "元素列表 JSON 数组"},
    {"name": "title", "type": "str", "required": False, "default": "", "help": "文档标题（元数据）"},
    {"name": "author", "type": "str", "required": False, "default": "", "help": "文档作者（元数据）"},
    {"name": "subject", "type": "str", "required": False, "default": "", "help": "文档主题（元数据）"},
]


def _escape_xml(text):
    """转义 XML 特殊字符，防止 ReportLab Paragraph 解析出错。

    仅转义 XML 保留字符中不属于富文本标记的部分：
    - & → &amp;（必须最先替换）
    - 不成对的 < > 会被转义，但保留 ReportLab 支持的富文本标签
    """
    import re
    if not text:
        return text
    # 先保护已有的合法 HTML/XML 标签（ReportLab 支持的富文本标记）
    # 支持的标签: b, i, u, a, br, font, super, sub, strike, span, para, img
    _VALID_TAG_RE = re.compile(
        r'(</?(?:b|i|u|a|br|font|super|sub|strike|span|para|img)(?:\s[^>]*)?>)',
        re.IGNORECASE
    )
    # 将合法标签替换为占位符
    placeholders = []
    def _save_tag(m):
        placeholders.append(m.group(0))
        return f'\x00TAG{len(placeholders) - 1}\x00'
    text = _VALID_TAG_RE.sub(_save_tag, text)
    # 转义 & < >
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # 恢复合法标签
    for i, tag in enumerate(placeholders):
        text = text.replace(f'\x00TAG{i}\x00', tag)
    return text


def _parse_color(color_str, default=None):
    """解析颜色字符串，支持 #RRGGBB 和颜色名称。"""
    from reportlab.lib import colors
    if not color_str:
        return default
    if isinstance(color_str, (list, tuple)) and len(color_str) == 3:
        return colors.Color(color_str[0] / 255.0, color_str[1] / 255.0, color_str[2] / 255.0)
    if isinstance(color_str, str):
        if color_str.startswith("#") and len(color_str) == 7:
            return colors.HexColor(color_str)
        # 尝试颜色名称
        color_map = {
            "black": colors.black, "white": colors.white, "red": colors.red,
            "blue": colors.blue, "green": colors.green, "grey": colors.grey,
            "gray": colors.gray, "yellow": colors.yellow, "orange": colors.orange,
            "purple": colors.purple, "navy": colors.navy, "teal": colors.teal,
            "darkblue": colors.HexColor("#1a237e"), "darkgreen": colors.HexColor("#1b5e20"),
            "darkred": colors.HexColor("#b71c1c"), "lightgrey": colors.HexColor("#F2F3F4"),
            "lightgray": colors.HexColor("#F2F3F4"),
        }
        return color_map.get(color_str.lower(), default)
    return default


def _parse_alignment(align_str):
    """解析对齐方式。"""
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    align_map = {
        "left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT,
        "justify": TA_JUSTIFY,
    }
    return align_map.get((align_str or "").lower(), TA_LEFT)


def handler(params):
    """从 JSON 描述创建 PDF。

    Args:
        params: {
            "output": 输出 PDF 路径,
            "page_size": 页面尺寸（A4/A3/letter/legal），默认 A4,
            "orientation": 页面方向（portrait/landscape），默认 portrait,
            "font_path": 自定义字体路径（支持中文等）,
            "margins": {"left": 72, "right": 72, "top": 72, "bottom": 72},
            "default_style": {
                "font_size": 12, "font_color": "#333333",
                "line_spacing": 1.2, "alignment": "left"
            },
            "header": {"text": "页眉文字", "font_size": 9, "font_color": "#999999", "alignment": "center"},
            "footer": {"text": "页脚文字", "show_page_number": true, "page_number_format": "第 {page} 页 / 共 {total} 页"},
            "watermark": {"text": "机密", "font_size": 50, "font_color": "#EEEEEE", "angle": 45},
            "elements": [...]
        }
    """
    from reportlab.lib.pagesizes import A4, A3, letter, legal
    from reportlab.platypus import (
        SimpleDocTemplate, Frame, PageTemplate,
        Paragraph, Spacer, PageBreak, KeepTogether,
        Table, TableStyle, Image as RLImage, HRFlowable,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm, inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    output_path = params.get("output")
    if not output_path:
        raise ValueError("'output' 参数是必需的")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # ===== 页面设置 =====
    page_size_name = params.get("page_size", "A4")
    page_size_map = {"A4": A4, "A3": A3, "letter": letter, "legal": legal}
    page_size = page_size_map.get(page_size_name, A4)

    orientation = params.get("orientation", "portrait")
    if orientation == "landscape":
        page_size = (page_size[1], page_size[0])

    # ===== 字体注册 =====
    font_path = params.get("font_path")
    font_name = "Helvetica"
    bold_font_name = "Helvetica-Bold"
    italic_font_name = "Helvetica-Oblique"
    if font_path and os.path.exists(font_path):
        try:
            from pdfkit.font_manager import register_reportlab_font
            if register_reportlab_font("CustomFont", font_path):
                font_name = "CustomFont"
                bold_font_name = "CustomFont"
                italic_font_name = "CustomFont"
        except Exception:
            pass

    # ===== 全局默认样式 =====
    default_style = params.get("default_style", {})
    default_font_size = default_style.get("font_size", 12)
    default_font_color = _parse_color(default_style.get("font_color"), colors.HexColor("#333333"))
    default_line_spacing = default_style.get("line_spacing", 1.2)
    default_alignment = _parse_alignment(default_style.get("alignment"))

    # ===== 页边距 =====
    margins = params.get("margins", {})
    left_margin = margins.get("left", 72)
    right_margin = margins.get("right", 72)
    top_margin = margins.get("top", 72)
    bottom_margin = margins.get("bottom", 72)

    # ===== 页眉/页脚/水印配置 =====
    header_cfg = params.get("header")
    footer_cfg = params.get("footer")
    watermark_cfg = params.get("watermark")

    # ===== 构建样式表 =====
    styles = getSampleStyleSheet()

    def make_style(name, parent_name, **overrides):
        """创建自定义段落样式。"""
        parent = styles[parent_name]
        kw = {
            "fontName": font_name,
            "textColor": default_font_color,
        }
        kw.update(overrides)
        return ParagraphStyle(name, parent=parent, **kw)

    custom_styles = {
        "CustomTitle": make_style("CustomTitle", "Title",
            fontSize=28, spaceAfter=24, alignment=TA_CENTER,
            textColor=colors.HexColor("#1a237e")),
        "CustomHeading1": make_style("CustomHeading1", "Heading1",
            fontSize=22, spaceAfter=14, spaceBefore=18,
            textColor=colors.HexColor("#1565c0")),
        "CustomHeading2": make_style("CustomHeading2", "Heading2",
            fontSize=18, spaceAfter=12, spaceBefore=14,
            textColor=colors.HexColor("#1976d2")),
        "CustomHeading3": make_style("CustomHeading3", "Heading3",
            fontSize=15, spaceAfter=10, spaceBefore=12,
            textColor=colors.HexColor("#1e88e5")),
        "CustomHeading4": make_style("CustomHeading4", "Heading4",
            fontSize=13, spaceAfter=8, spaceBefore=10,
            textColor=colors.HexColor("#42a5f5")),
        "CustomNormal": make_style("CustomNormal", "Normal",
            fontSize=default_font_size, leading=default_font_size * default_line_spacing,
            spaceAfter=8, alignment=default_alignment,
            textColor=default_font_color),
        "CustomLink": make_style("CustomLink", "Normal",
            fontSize=default_font_size, textColor=colors.HexColor("#1565c0"),
            underline=True),
        "CustomCaption": make_style("CustomCaption", "Normal",
            fontSize=10, alignment=TA_CENTER, textColor=colors.grey,
            spaceAfter=12, spaceBefore=4),
    }

    # ===== 页眉/页脚/水印绘制回调 =====
    page_count_holder = [0]  # 用于存储总页数

    def draw_header_footer_watermark(canvas, doc):
        """在每页上绘制页眉、页脚和水印。"""
        canvas.saveState()
        page_width, page_height = page_size

        # 水印
        if watermark_cfg:
            wm_text = watermark_cfg.get("text", "")
            wm_font_size = watermark_cfg.get("font_size", 50)
            wm_color = _parse_color(watermark_cfg.get("font_color"), colors.HexColor("#EEEEEE"))
            wm_angle = watermark_cfg.get("angle", 45)
            wm_opacity = watermark_cfg.get("opacity", 0.15)
            canvas.setFont(font_name, wm_font_size)
            canvas.setFillColor(wm_color, alpha=wm_opacity)
            canvas.saveState()
            canvas.translate(page_width / 2, page_height / 2)
            canvas.rotate(wm_angle)
            canvas.drawCentredString(0, 0, wm_text)
            canvas.restoreState()

        # 页眉
        if header_cfg:
            h_text = header_cfg.get("text", "")
            h_font_size = header_cfg.get("font_size", 9)
            h_color = _parse_color(header_cfg.get("font_color"), colors.grey)
            h_align = header_cfg.get("alignment", "center")
            canvas.setFont(font_name, h_font_size)
            canvas.setFillColor(h_color)
            y = page_height - top_margin + 20
            if h_align == "left":
                canvas.drawString(left_margin, y, h_text)
            elif h_align == "right":
                canvas.drawRightString(page_width - right_margin, y, h_text)
            else:
                canvas.drawCentredString(page_width / 2, y, h_text)
            # 页眉下划线
            if header_cfg.get("show_line", True):
                canvas.setStrokeColor(colors.HexColor("#DDDDDD"))
                canvas.setLineWidth(0.5)
                canvas.line(left_margin, y - 5, page_width - right_margin, y - 5)

        # 页脚
        if footer_cfg:
            f_text = footer_cfg.get("text", "")
            f_font_size = footer_cfg.get("font_size", 9)
            f_color = _parse_color(footer_cfg.get("font_color"), colors.grey)
            show_page_num = footer_cfg.get("show_page_number", True)
            page_num_format = footer_cfg.get("page_number_format", "第 {page} 页")
            canvas.setFont(font_name, f_font_size)
            canvas.setFillColor(f_color)
            y = bottom_margin - 25

            # 页脚上划线
            if footer_cfg.get("show_line", True):
                canvas.setStrokeColor(colors.HexColor("#DDDDDD"))
                canvas.setLineWidth(0.5)
                canvas.line(left_margin, y + 15, page_width - right_margin, y + 15)

            if f_text:
                canvas.drawString(left_margin, y, f_text)
            if show_page_num:
                page_num_text = page_num_format.replace("{page}", str(doc.page))
                # {total} 在第一次构建时不可用，用占位
                page_num_text = page_num_text.replace("{total}", str(doc.page))
                canvas.drawRightString(page_width - right_margin, y, page_num_text)

        canvas.restoreState()

    # ===== 创建文档 =====
    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        title=params.get("title", ""),
        author=params.get("author", ""),
        subject=params.get("subject", ""),
    )

    story = []
    element_count = 0
    toc_entries = []  # 收集目录条目

    # ===== 处理元素 =====
    for elem in params.get("elements", []):
        elem_type = elem.get("type", "paragraph")

        # ---------- title ----------
        if elem_type == "title":
            style = ParagraphStyle(
                f"Title_{element_count}", parent=custom_styles["CustomTitle"],
                fontSize=elem.get("font_size", 28),
                textColor=_parse_color(elem.get("font_color"), custom_styles["CustomTitle"].textColor),
                alignment=_parse_alignment(elem.get("alignment", "center")),
                spaceAfter=elem.get("space_after", 24),
                spaceBefore=elem.get("space_before", 0),
                fontName=bold_font_name if elem.get("bold", True) else font_name,
            )
            text = _escape_xml(elem["text"])
            if elem.get("underline"):
                text = f"<u>{text}</u>"
            story.append(Paragraph(text, style))
            toc_entries.append(("title", elem["text"]))
            element_count += 1

        # ---------- heading ----------
        elif elem_type == "heading":
            level = min(max(elem.get("level", 1), 1), 4)
            base_style = custom_styles[f"CustomHeading{level}"]
            style = ParagraphStyle(
                f"Heading_{element_count}", parent=base_style,
                fontSize=elem.get("font_size", base_style.fontSize),
                textColor=_parse_color(elem.get("font_color"), base_style.textColor),
                alignment=_parse_alignment(elem.get("alignment", "left")),
                spaceAfter=elem.get("space_after", base_style.spaceAfter),
                spaceBefore=elem.get("space_before", base_style.spaceBefore),
                fontName=bold_font_name if elem.get("bold", True) else font_name,
            )
            text = _escape_xml(elem["text"])
            story.append(Paragraph(text, style))
            toc_entries.append((f"h{level}", elem["text"]))
            element_count += 1

        # ---------- paragraph ----------
        elif elem_type == "paragraph":
            fs = elem.get("font_size", default_font_size)
            ls = elem.get("line_spacing", default_line_spacing)
            style = ParagraphStyle(
                f"Para_{element_count}", parent=custom_styles["CustomNormal"],
                fontSize=fs,
                leading=fs * ls,
                textColor=_parse_color(elem.get("font_color"), default_font_color),
                alignment=_parse_alignment(elem.get("alignment")),
                spaceAfter=elem.get("space_after", 8),
                spaceBefore=elem.get("space_before", 0),
                firstLineIndent=elem.get("first_line_indent", 0),
                leftIndent=elem.get("left_indent", 0),
                rightIndent=elem.get("right_indent", 0),
            )
            text = _escape_xml(elem["text"])
            # 支持简单的富文本标记
            if elem.get("bold"):
                text = f"<b>{text}</b>"
            if elem.get("italic"):
                text = f"<i>{text}</i>"
            if elem.get("underline"):
                text = f"<u>{text}</u>"

            # 背景色支持（通过表格包裹实现）
            bg_color = _parse_color(elem.get("bg_color"))
            if bg_color:
                para = Paragraph(text, style)
                bg_table = Table([[para]], colWidths=[page_size[0] - left_margin - right_margin])
                bg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BOX', (0, 0), (-1, -1), 0.5, _parse_color(elem.get("border_color"), bg_color)),
                ]))
                story.append(bg_table)
            else:
                story.append(Paragraph(text, style))
            element_count += 1

        # ---------- table ----------
        elif elem_type == "table":
            headers = elem.get("headers", [])
            rows = elem.get("rows", [])
            data_2d = elem.get("data")  # 新格式：二维数组，第一行为表头

            if data_2d:
                data = data_2d
            elif headers:
                data = [headers] + rows
            else:
                data = rows

            if data:
                # 列宽
                col_widths = elem.get("col_widths")
                if col_widths:
                    table = Table(data, colWidths=col_widths)
                else:
                    table = Table(data)

                # 表格样式
                header_bg = _parse_color(elem.get("header_bg_color"), colors.HexColor("#2E86C1"))
                header_text_color = _parse_color(elem.get("header_text_color"), colors.whitesmoke)
                border_color = _parse_color(elem.get("border_color"), colors.HexColor("#CCCCCC"))
                border_width = elem.get("border_width", 0.5)
                header_font_size = elem.get("header_font_size", 11)
                body_font_size = elem.get("body_font_size", 10)

                # 条纹颜色
                stripe_colors_cfg = elem.get("stripe_colors", ["#F8F9FA", "#FFFFFF"])
                stripe_1 = _parse_color(stripe_colors_cfg[0], colors.HexColor("#F8F9FA"))
                stripe_2 = _parse_color(stripe_colors_cfg[1] if len(stripe_colors_cfg) > 1 else "#FFFFFF", colors.white)

                style_commands = [
                    # 表头样式
                    ('BACKGROUND', (0, 0), (-1, 0), header_bg),
                    ('TEXTCOLOR', (0, 0), (-1, 0), header_text_color),
                    ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), header_font_size),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('TOPPADDING', (0, 0), (-1, 0), 10),
                    # 表体样式
                    ('FONTNAME', (0, 1), (-1, -1), font_name),
                    ('FONTSIZE', (0, 1), (-1, -1), body_font_size),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
                    ('TOPPADDING', (0, 1), (-1, -1), 7),
                    # 对齐
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    # 边框
                    ('GRID', (0, 0), (-1, -1), border_width, border_color),
                ]

                # 表体对齐
                body_align = elem.get("body_alignment", "left").upper()
                style_commands.append(('ALIGN', (0, 1), (-1, -1), body_align))

                # 条纹行
                for i in range(1, len(data)):
                    bg = stripe_1 if i % 2 == 1 else stripe_2
                    style_commands.append(('BACKGROUND', (0, i), (-1, i), bg))

                # 合并单元格
                for span in elem.get("spans", []):
                    style_commands.append(('SPAN', tuple(span[0]), tuple(span[1])))

                table.setStyle(TableStyle(style_commands))

                # 表格标题
                caption = elem.get("caption")
                if caption:
                    story.append(Paragraph(caption, custom_styles["CustomCaption"]))

                story.append(table)
                story.append(Spacer(1, 12))
                element_count += 1

        # ---------- image ----------
        elif elem_type == "image":
            img_path = elem.get("path") or elem.get("image_path")
            if img_path and os.path.exists(img_path):
                width = elem.get("width", 400)
                height = elem.get("height")
                kwargs = {"width": width}
                if height:
                    kwargs["height"] = height

                img = RLImage(img_path, **kwargs)

                # 对齐
                img_align = elem.get("alignment", "center")
                if img_align == "center":
                    img.hAlign = "CENTER"
                elif img_align == "right":
                    img.hAlign = "RIGHT"
                else:
                    img.hAlign = "LEFT"

                story.append(img)

                # 图片标题
                caption = elem.get("caption")
                if caption:
                    story.append(Paragraph(caption, custom_styles["CustomCaption"]))
                else:
                    story.append(Spacer(1, 12))
                element_count += 1

        # ---------- list ----------
        elif elem_type == "list":
            items = elem.get("items", [])
            ordered = elem.get("ordered", False)
            bullet = elem.get("bullet", "•")
            fs = elem.get("font_size", default_font_size)
            indent = elem.get("indent", 20)
            fc = _parse_color(elem.get("font_color"), default_font_color)

            list_style = ParagraphStyle(
                f"List_{element_count}", parent=custom_styles["CustomNormal"],
                fontSize=fs, textColor=fc,
                leftIndent=indent, bulletIndent=indent - 15,
                spaceAfter=4,
            )

            for i, item in enumerate(items):
                prefix = f"{i + 1}." if ordered else bullet
                text = f"{prefix} {_escape_xml(item)}"
                if elem.get("bold"):
                    text = f"<b>{text}</b>"
                story.append(Paragraph(text, list_style))
            element_count += len(items)

        # ---------- spacer ----------
        elif elem_type == "spacer":
            story.append(Spacer(1, elem.get("height", 12)))

        # ---------- page_break ----------
        elif elem_type == "page_break":
            story.append(PageBreak())

        # ---------- hr (水平分割线) ----------
        elif elem_type in ("hr", "line"):
            line_width = elem.get("width", page_size[0] - left_margin - right_margin)
            line_color = _parse_color(elem.get("color"), colors.HexColor("#CCCCCC"))
            line_thickness = elem.get("thickness", 1)
            dash = elem.get("dash")  # [dash_length, gap_length]
            hr = HRFlowable(
                width=line_width if isinstance(line_width, str) and line_width.endswith('%') else line_width,
                thickness=line_thickness,
                color=line_color,
                spaceBefore=elem.get("space_before", 8),
                spaceAfter=elem.get("space_after", 8),
                dash=dash,
            )
            story.append(hr)
            element_count += 1

        # ---------- link ----------
        elif elem_type == "link":
            url = elem.get("url", "")
            text = _escape_xml(elem.get("text", url))
            fc = _parse_color(elem.get("font_color"), colors.HexColor("#1565c0"))
            fs = elem.get("font_size", default_font_size)
            link_style = ParagraphStyle(
                f"Link_{element_count}", parent=custom_styles["CustomLink"],
                fontSize=fs, textColor=fc,
            )
            story.append(Paragraph(f'<a href="{url}">{text}</a>', link_style))
            element_count += 1

        # ---------- columns (多栏布局) ----------
        elif elem_type == "columns":
            col_data = elem.get("columns", [])
            col_count = len(col_data)
            if col_count > 0:
                # 用表格模拟多栏
                col_width = (page_size[0] - left_margin - right_margin) / col_count
                col_widths = elem.get("col_widths", [col_width] * col_count)
                cells = []
                for col_content in col_data:
                    if isinstance(col_content, str):
                        cells.append(Paragraph(_escape_xml(col_content), custom_styles["CustomNormal"]))
                    elif isinstance(col_content, list):
                        # 多个段落
                        cell_story = []
                        for item in col_content:
                            if isinstance(item, str):
                                cell_story.append(Paragraph(_escape_xml(item), custom_styles["CustomNormal"]))
                            elif isinstance(item, dict):
                                cell_story.append(Paragraph(
                                    _escape_xml(item.get("text", "")),
                                    ParagraphStyle(
                                        f"ColPara_{element_count}",
                                        parent=custom_styles["CustomNormal"],
                                        fontSize=item.get("font_size", default_font_size),
                                        textColor=_parse_color(item.get("font_color"), default_font_color),
                                        alignment=_parse_alignment(item.get("alignment")),
                                    )
                                ))
                        cells.append(cell_story)
                    else:
                        cells.append(Paragraph(str(col_content), custom_styles["CustomNormal"]))

                col_table = Table([cells], colWidths=col_widths)
                col_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]))
                # 可选列间分割线
                if elem.get("show_divider", False):
                    for i in range(col_count - 1):
                        col_table.setStyle(TableStyle([
                            ('LINEAFTER', (i, 0), (i, -1), 0.5, colors.HexColor("#DDDDDD")),
                        ]))
                story.append(col_table)
                element_count += 1

        # ---------- toc (目录) ----------
        elif elem_type == "toc":
            toc_title = elem.get("title", "目录")
            story.append(Paragraph(toc_title, custom_styles["CustomHeading1"]))
            story.append(Spacer(1, 12))
            # 目录将在文档构建后填充
            story.append(Paragraph("<i>（目录将根据标题自动生成）</i>", custom_styles["CustomNormal"]))
            story.append(PageBreak())
            element_count += 1

        # ---------- blockquote (引用块) ----------
        elif elem_type == "blockquote":
            text = _escape_xml(elem.get("text", ""))
            fs = elem.get("font_size", default_font_size)
            fc = _parse_color(elem.get("font_color"), colors.HexColor("#555555"))
            bg = _parse_color(elem.get("bg_color"), colors.HexColor("#F5F5F5"))
            border_left_color = _parse_color(elem.get("border_color"), colors.HexColor("#1976d2"))

            quote_style = ParagraphStyle(
                f"Quote_{element_count}", parent=custom_styles["CustomNormal"],
                fontSize=fs, textColor=fc,
                leftIndent=20, rightIndent=10,
                spaceBefore=8, spaceAfter=8,
            )
            if elem.get("italic", True):
                text = f"<i>{text}</i>"
            para = Paragraph(text, quote_style)

            # 用表格实现左边框 + 背景色
            quote_table = Table([[para]], colWidths=[page_size[0] - left_margin - right_margin])
            quote_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBEFORE', (0, 0), (0, -1), 3, border_left_color),
            ]))
            story.append(quote_table)
            element_count += 1

        # ---------- code (代码块) ----------
        elif elem_type == "code":
            code_text = elem.get("text", "")
            fs = elem.get("font_size", 10)
            bg = _parse_color(elem.get("bg_color"), colors.HexColor("#F5F5F5"))
            fc = _parse_color(elem.get("font_color"), colors.HexColor("#D32F2F"))

            code_style = ParagraphStyle(
                f"Code_{element_count}", parent=custom_styles["CustomNormal"],
                fontName="Courier", fontSize=fs, textColor=fc,
                leftIndent=10, rightIndent=10,
                spaceBefore=8, spaceAfter=8,
                leading=fs * 1.4,
            )
            # 转义 HTML 特殊字符
            code_text = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            code_text = code_text.replace("\n", "<br/>")
            para = Paragraph(code_text, code_style)

            code_table = Table([[para]], colWidths=[page_size[0] - left_margin - right_margin])
            code_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
            ]))
            story.append(code_table)
            element_count += 1

        # ---------- badge (徽章/标签) ----------
        elif elem_type == "badge":
            text = _escape_xml(elem.get("text", ""))
            bg = _parse_color(elem.get("bg_color"), colors.HexColor("#1976d2"))
            fc = _parse_color(elem.get("font_color"), colors.white)
            fs = elem.get("font_size", 10)

            badge_style = ParagraphStyle(
                f"Badge_{element_count}", parent=custom_styles["CustomNormal"],
                fontSize=fs, textColor=fc, alignment=TA_CENTER,
            )
            para = Paragraph(f"<b>{text}</b>", badge_style)
            badge_table = Table([[para]], colWidths=[len(text) * fs * 0.7 + 20])
            badge_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ROUNDEDCORNERS', [4, 4, 4, 4]),
            ]))
            badge_table.hAlign = elem.get("alignment", "LEFT").upper()
            story.append(badge_table)
            element_count += 1

        # ---------- key_value (键值对) ----------
        elif elem_type == "key_value":
            pairs = elem.get("pairs", [])
            if pairs:
                kv_data = []
                for pair in pairs:
                    key = _escape_xml(pair.get("key", ""))
                    value = _escape_xml(str(pair.get("value", "")))
                    kv_data.append([
                        Paragraph(f"<b>{key}</b>", custom_styles["CustomNormal"]),
                        Paragraph(value, custom_styles["CustomNormal"]),
                    ])
                key_width = elem.get("key_width", 150)
                val_width = page_size[0] - left_margin - right_margin - key_width
                kv_table = Table(kv_data, colWidths=[key_width, val_width])
                kv_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#EEEEEE")),
                ]))
                story.append(kv_table)
                element_count += 1

    # ===== 构建文档 =====
    if not story:
        story.append(Paragraph("空文档", custom_styles["CustomNormal"]))

    has_header_footer = header_cfg or footer_cfg or watermark_cfg
    if has_header_footer:
        doc.build(story, onFirstPage=draw_header_footer_watermark,
                  onLaterPages=draw_header_footer_watermark)
    else:
        doc.build(story)

    # 获取文件大小
    file_size = os.path.getsize(output_path)

    return {
        "success": True,
        "element_count": element_count,
        "page_size": page_size_name,
        "orientation": orientation,
        "output": output_path,
        "file_size_bytes": file_size,
        "features_used": {
            "header": bool(header_cfg),
            "footer": bool(footer_cfg),
            "watermark": bool(watermark_cfg),
            "custom_font": bool(font_path),
        }
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)

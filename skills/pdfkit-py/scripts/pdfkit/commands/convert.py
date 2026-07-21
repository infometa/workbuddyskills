#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 格式转换中心。支持 PDF ↔ Word/HTML/Markdown/Images 等多种格式互转。"""

import json
import os
import shutil
import subprocess
import sys

COMMAND = "convert"
DESCRIPTION = "Convert between PDF and other formats (Word/HTML/Markdown/Images)"
CATEGORY = "organize"

PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "Source file path"},
    {"name": "output", "type": "str", "required": True, "help": "Output file path"},
    {"name": "from_format", "type": "str", "required": False, "default": "auto", "choices": ["auto", "pdf", "docx", "html", "md", "images"], "help": "Source format"},
    {"name": "to_format", "type": "str", "required": False, "default": "", "choices": ["pdf", "docx", "html", "md", "images"], "help": "Target format"},
    {"name": "options", "type": "json", "required": False, "help": "Format-specific options (JSON object)"},
]


def handler(params):
    """格式转换入口。"""
    input_path = params["input"]
    output_path = params["output"]
    from_format = params.get("from_format", "auto")
    to_format = params.get("to_format", "")
    options = params.get("options", {})

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    # 自动检测源格式
    if from_format == "auto":
        from_format = _detect_format(input_path)

    if not to_format:
        to_format = _detect_format(output_path)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 路由到对应的转换函数
    converter_key = f"{from_format}_to_{to_format}"
    converters = {
        "pdf_to_docx": _pdf_to_docx,
        "pdf_to_html": _pdf_to_html,
        "pdf_to_md": _pdf_to_markdown,
        "pdf_to_images": _pdf_to_images,
        "docx_to_pdf": _docx_to_pdf,
        "html_to_pdf": _html_to_pdf,
        "md_to_pdf": _md_to_pdf,
        "images_to_pdf": _images_to_pdf,
    }

    converter = converters.get(converter_key)
    if converter is None:
        raise ValueError(
            f"不支持的转换: {from_format} → {to_format}。"
            f"支持的转换: {', '.join(converters.keys())}"
        )

    result = converter(input_path, output_path, options)

    # 获取输出文件大小
    if os.path.exists(output_path):
        result["file_size"] = os.path.getsize(output_path)

    result["success"] = True
    result["from_format"] = from_format
    result["to_format"] = to_format
    result["output"] = output_path

    return result


def _detect_format(filepath):
    """根据文件扩展名检测格式。"""
    ext = os.path.splitext(filepath)[1].lower()
    format_map = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".html": "html",
        ".htm": "html",
        ".md": "md",
        ".markdown": "md",
        ".png": "images",
        ".jpg": "images",
        ".jpeg": "images",
        ".tiff": "images",
        ".bmp": "images",
    }
    return format_map.get(ext, "unknown")


def _pdf_to_docx(input_path, output_path, options):
    """PDF → Word (.docx) 转换。"""
    method = options.get("method", "auto")
    pages = options.get("pages", None)

    # 方法 1: pdf2docx（推荐）
    if method in ("auto", "pdf2docx"):
        try:
            from pdf2docx import Converter

            cv = Converter(input_path)
            if pages:
                cv.convert(output_path, start=pages[0], end=pages[-1] + 1)
            else:
                cv.convert(output_path)
            cv.close()

            return {
                "engine": "pdf2docx",
                "pages_converted": _count_docx_pages(output_path),
            }
        except ImportError:
            if method == "pdf2docx":
                raise ImportError("pdf2docx 未安装，请执行: pip install pdf2docx")
        except Exception as e:
            if method == "pdf2docx":
                raise
            # auto 模式下继续尝试其他方法

    # 方法 2: LibreOffice headless
    if method in ("auto", "libreoffice"):
        try:
            return _convert_with_libreoffice(input_path, output_path, "docx")
        except Exception as e:
            if method == "libreoffice":
                raise

    raise RuntimeError("PDF → Word 转换失败：pdf2docx 和 LibreOffice 均不可用")


def _pdf_to_html(input_path, output_path, options):
    """PDF → HTML 转换。"""
    import fitz

    doc = fitz.open(input_path)
    pages = options.get("pages", None)
    target_pages = pages if pages else list(range(len(doc)))

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="zh">',
        "<head><meta charset='utf-8'><title>PDF Export</title></head>",
        "<body>",
    ]

    for page_num in target_pages:
        if page_num >= len(doc):
            continue
        page = doc[page_num]
        html_parts.append(f'<div class="page" data-page="{page_num}">')
        html_parts.append(page.get_text("html"))
        html_parts.append("</div>")
        html_parts.append("<hr>")

    html_parts.extend(["</body>", "</html>"])
    doc.close()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    return {
        "engine": "pymupdf",
        "pages_converted": len(target_pages),
    }


def _pdf_to_markdown(input_path, output_path, options):
    """PDF → Markdown 转换。"""
    method = options.get("method", "auto")

    # 方法 1: marker（推荐，效果最好）
    if method in ("auto", "marker"):
        try:
            result = subprocess.run(
                ["marker_single", input_path, "--output_dir", os.path.dirname(output_path) or "."],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                # marker 输出到目录，需要找到生成的 md 文件
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                marker_output = os.path.join(
                    os.path.dirname(output_path) or ".", base_name, f"{base_name}.md"
                )
                if os.path.exists(marker_output):
                    shutil.move(marker_output, output_path)
                    return {"engine": "marker", "pages_converted": -1}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            if method == "marker":
                raise

    # 方法 2: PyMuPDF 文本提取 + 简单 Markdown 格式化
    import fitz

    doc = fitz.open(input_path)
    pages = options.get("pages", None)
    target_pages = pages if pages else list(range(len(doc)))

    md_parts = []
    for page_num in target_pages:
        if page_num >= len(doc):
            continue
        page = doc[page_num]
        text_dict = page.get_text("dict")

        # 获取平均字号用于标题检测
        all_sizes = []
        for block in text_dict.get("blocks", []):
            if block["type"] == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        all_sizes.append(span.get("size", 12))

        avg_size = sum(all_sizes) / len(all_sizes) if all_sizes else 12
        title_threshold = avg_size * 1.3

        for block in text_dict.get("blocks", []):
            if block["type"] == 0:  # 文本块
                block_text = ""
                block_size = 12

                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span["text"]
                        block_size = max(block_size, span.get("size", 12))
                    block_text += line_text + "\n"

                block_text = block_text.strip()
                if not block_text:
                    continue

                # 标题检测
                if block_size > title_threshold and len(block_text) < 200:
                    if block_size > avg_size * 1.8:
                        md_parts.append(f"# {block_text}\n")
                    elif block_size > title_threshold:
                        md_parts.append(f"## {block_text}\n")
                else:
                    md_parts.append(f"{block_text}\n")

            elif block["type"] == 1:  # 图片块
                md_parts.append(f"![image](page{page_num}_image)\n")

        md_parts.append("\n---\n")

    doc.close()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_parts))

    return {
        "engine": "pymupdf",
        "pages_converted": len(target_pages),
    }


def _pdf_to_images(input_path, output_path, options):
    """PDF → Images 转换。"""
    import fitz

    doc = fitz.open(input_path)
    pages = options.get("pages", None)
    dpi = options.get("dpi", 150)
    target_pages = pages if pages else list(range(len(doc)))

    # output_path 作为输出目录
    output_dir = output_path
    if output_path.endswith((".png", ".jpg")):
        output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    image_paths = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    for page_num in target_pages:
        if page_num >= len(doc):
            continue
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(output_dir, f"page_{page_num:04d}.png")
        pix.save(img_path)
        image_paths.append(img_path)

    doc.close()

    return {
        "engine": "pymupdf",
        "pages_converted": len(image_paths),
        "images": image_paths,
    }


def _docx_to_pdf(input_path, output_path, options):
    """Word (.docx) → PDF 转换。"""
    return _convert_with_libreoffice(input_path, output_path, "pdf")


def _html_to_pdf(input_path, output_path, options):
    """HTML → PDF 转换。"""
    # 方法 1: wkhtmltopdf
    try:
        result = subprocess.run(
            ["wkhtmltopdf", "--encoding", "utf-8", input_path, output_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return {"engine": "wkhtmltopdf", "pages_converted": -1}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 方法 2: Chromium headless
    chrome_candidates = ["chromium", "chromium-browser", "google-chrome", "chrome"]
    # Windows: 添加常见 Chrome 安装路径
    if sys.platform == "win32":
        for prog in [os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""),
                      os.environ.get("LOCALAPPDATA", "")]:
            if prog:
                candidate = os.path.join(prog, "Google", "Chrome", "Application", "chrome.exe")
                if os.path.isfile(candidate):
                    chrome_candidates.insert(0, candidate)
                    break
    for chrome in chrome_candidates:
        try:
            result = subprocess.run(
                [chrome, "--headless", "--disable-gpu",
                 f"--print-to-pdf={output_path}", input_path],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and os.path.exists(output_path):
                return {"engine": f"chromium ({chrome})", "pages_converted": -1}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    raise RuntimeError("HTML → PDF 转换失败：wkhtmltopdf 和 Chromium 均不可用")


def _md_to_pdf(input_path, output_path, options):
    """Markdown → PDF 转换。"""
    # 方法 1: pandoc
    try:
        cmd = ["pandoc", input_path, "-o", output_path,
               "--pdf-engine=xelatex",
               "-V", "CJKmainfont=Noto Sans CJK SC"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_path):
            return {"engine": "pandoc", "pages_converted": -1}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 方法 2: 先转 HTML 再转 PDF
    import tempfile
    try:
        import markdown
        with open(input_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
        html_full = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>body{{font-family:sans-serif;max-width:800px;margin:auto;padding:20px}}</style>
</head><body>{html_content}</body></html>"""

        with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False, encoding="utf-8") as tmp:
            tmp.write(html_full)
            tmp_html = tmp.name

        try:
            result = _html_to_pdf(tmp_html, output_path, options)
        finally:
            os.unlink(tmp_html)
        result["engine"] = "markdown+html2pdf"
        return result
    except ImportError:
        pass

    raise RuntimeError("Markdown → PDF 转换失败：pandoc 和 markdown 库均不可用")


def _images_to_pdf(input_path, output_path, options):
    """Images → PDF 转换。"""
    import fitz

    # input_path 可以是目录或单个图片
    if os.path.isdir(input_path):
        image_files = sorted([
            os.path.join(input_path, f) for f in os.listdir(input_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp"))
        ])
    else:
        image_files = [input_path]

    if not image_files:
        raise ValueError(f"未找到图片文件: {input_path}")

    doc = fitz.open()
    for img_path in image_files:
        img = fitz.open(img_path)
        rect = img[0].rect
        pdf_bytes = img.convert_to_pdf()
        img.close()

        img_pdf = fitz.open("pdf", pdf_bytes)
        page = doc.new_page(width=rect.width, height=rect.height)
        page.show_pdf_page(page.rect, img_pdf, 0)
        img_pdf.close()

    doc.save(output_path)
    doc.close()

    return {
        "engine": "pymupdf",
        "pages_converted": len(image_files),
        "images_count": len(image_files),
    }


def _convert_with_libreoffice(input_path, output_path, to_format):
    """使用 LibreOffice headless 模式转换。"""
    import tempfile

    output_dir = tempfile.mkdtemp(prefix="pdfkit-lo-")

    try:
        # 查找 LibreOffice
        for lo in ["soffice", "libreoffice"]:
            try:
                result = subprocess.run(
                    [lo, "--headless", "--convert-to", to_format,
                     "--outdir", output_dir, input_path],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    # 找到转换后的文件
                    base_name = os.path.splitext(os.path.basename(input_path))[0]
                    converted = os.path.join(output_dir, f"{base_name}.{to_format}")
                    if os.path.exists(converted):
                        shutil.move(converted, output_path)
                        return {
                            "engine": f"libreoffice ({lo})",
                            "pages_converted": -1,
                        }
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)

    raise RuntimeError(f"LibreOffice 转换失败：未找到 soffice 或 libreoffice 命令")


def _count_docx_pages(docx_path):
    """估算 docx 文件的页数（近似值）。"""
    try:
        from docx import Document
        doc = Document(docx_path)
        # 简单估算：每 40 行约 1 页
        total_paragraphs = len(doc.paragraphs)
        return max(1, total_paragraphs // 40)
    except Exception:
        return -1


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)

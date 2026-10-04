"""快*****版 HTML→PDF 转换器（Playwright headless Chromium）。

优化点（相比原版 html2pdf.py）：
1. 移除 8 秒强制等待（wait_for_timeout 8000）
2. 改用 domcontentloaded（而非 networkidle），因为页面无外部 JS
3. 等待首张图片加载完成即触发 PDF 生成
4. 支持 --fast 参数跳过所有额外等待

用法：
    python html2pdf_fast.py report.html output.pdf --landscape
    python html2pdf_fast.py report.html --fast   # 极速模式
"""

import sys
import os
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright


def html_to_pdf(
    source: str,
    pdf_path: str = None,
    width: str = None,
    height: str = None,
    page_format: str = "A4",
    landscape: bool = False,
    fast: bool = False,
) -> str:
    """
    Convert HTML file or URL to PDF (optimized for static HTML + inline SVG).

    Args:
        source:      HTML 文件路径或 HTTP/HTTPS URL
        pdf_path:    输出 PDF 路径（默认与 source 同名 .pdf）
        width/height: 自定义页面尺寸（如 "210mm"、"1200px"）
        page_format:  页面格式（A4/A3/Letter…），width/height 设置后忽略
        landscape:    True → 横向（297×210mm）
        fast:         True → 跳过所有额外等待，domcontentloaded 后立即生成
    """
    is_url = source.startswith("http://") or source.startswith("https://")

    if not is_url:
        source = os.path.abspath(source)
        if not os.path.exists(source):
            raise FileNotFoundError(f"HTML file not found: {source}")
        file_url = Path(source).as_uri()
    else:
        file_url = source

    if pdf_path is None:
        if is_url:
            from urllib.parse import urlparse
            path_part = urlparse(source).path
            base_name = Path(path_part).stem or "page"
            pdf_path = os.path.join(os.getcwd(), base_name + ".pdf")
        else:
            pdf_path = source.rsplit(".", 1)[0] + ".pdf"

    with sync_playwright() as p:
        # 启动参数优化：加速 headless 模式
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process',  # 单进程模式，启动更快（Windows 可能不支持）
            ]
        )
        page = browser.new_page()

        # viewport 与 PDF 尺寸匹配，避免缩放
        if width and height:
            w_px = int(width.replace("px", "")) if "px" in width else 800
            h_px = int(height.replace("px", "")) if "px" in height else 1100
            page.set_viewport_size({"width": w_px, "height": h_px})
        elif landscape:
            page.set_viewport_size({"width": 1123, "height": 795})  # A4 横向 96dpi
        else:
            page.set_viewport_size({"width": 794, "height": 1123})  # A4 纵向 96dpi

        # 强制 screen 媒体模式（确保按屏幕 CSS 渲染）
        page.emulate_media(media="screen")

        # 等待策略
        if fast:
            # 极速模式：仅等待 DOM 加载完成，不等待图片/字体
            page.goto(file_url, wait_until="domcontentloaded")
        else:
            # 默认模式：等待页面稳定，确保图片/字体加载完成（保证质量）
            page.goto(file_url, wait_until="domcontentloaded")
            # 等待 header 渲染完成（确认页面框架就绪）
            try:
                page.wait_for_selector(".header", state="attached", timeout=3000)
            except Exception:
                pass
            # 等待所有图片加载完成（确保 logo 等图片出现在 PDF 中）
            try:
                page.wait_for_function("""
                    () => Array.from(document.images).every(img => img.complete)
                """, timeout=3000)
            except Exception:
                pass

        # 构建 PDF 参数
        pdf_params = {
            "path": pdf_path,
            "print_background": True,
            "margin": {"top": "15mm", "bottom": "15mm", "left": "10mm", "right": "10mm"},
            "display_header_footer": False,
        }

        if width and height:
            pdf_params["width"] = width
            pdf_params["height"] = height
        elif landscape:
            pdf_params["width"] = "297mm"
            pdf_params["height"] = "210mm"
        else:
            pdf_params["format"] = page_format

        page.pdf(**pdf_params)
        browser.close()

    return pdf_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fast HTML→PDF converter (Playwright, optimized for static HTML+SVG).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python html2pdf_fast.py report.html                          # A4 portrait, optimized wait
  python html2pdf_fast.py report.html --landscape              # A4 landscape
  python html2pdf_fast.py report.html --fast                   # ultra-fast mode (no extra wait)
  python html2pdf_fast.py report.html output.pdf --format A3  # A3 format
"""
    )
    parser.add_argument("source", help="HTML file path or HTTP/HTTPS URL")
    parser.add_argument("output", nargs="?", default=None, help="Output PDF path (default: same name as source)")
    parser.add_argument("--width", help="Page width (e.g., '210mm', '1200px')")
    parser.add_argument("--height", help="Page height (e.g., '297mm', '1697px')")
    parser.add_argument("--format", default="A4", help="Page format: A4, A3, Letter, etc. (default: A4)")
    parser.add_argument("--landscape", action="store_true", help="Use landscape orientation")
    parser.add_argument("--fast", action="store_true", help="Ultra-fast mode: skip all extra waits")

    args = parser.parse_args()

    result = html_to_pdf(
        source=args.source,
        pdf_path=args.output,
        width=args.width,
        height=args.height,
        page_format=args.format,
        landscape=args.landscape,
        fast=args.fast,
    )
    print(f"PDF generated: {result}")

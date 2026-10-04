"""Convert HTML file to PDF using Playwright (headless Chromium).

Supports both local HTML files and HTTP URLs.
Usage:
    python3 html2pdf.py <html_path_or_url> [output_pdf_path] [options]

Options:
    --width <size>    Page width (e.g., "210mm", "1200px")
    --height <size>   Page height (e.g., "297mm", "1697px")
    --format <fmt>    Page format: A4, A3, Letter, etc. (default: A4)
    --landscape        Use landscape orientation (297mm x 210mm)

Examples:
    python3 html2pdf.py report.html                        # A4 portrait
    python3 html2pdf.py report.html --landscape            # A4 landscape
    python3 html2pdf.py report.html --width 1200px --height 1697px  # custom size
"""

import sys
import os
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright


def html_to_pdf(source: str, pdf_path: str = None, width: str = None, height: str = None, page_format: str = "A4", landscape: bool = False) -> str:
    """
    Convert an HTML file or URL to PDF.

    Args:
        source: Absolute path to an HTML file, or an HTTP/HTTPS URL.
        pdf_path: Optional output PDF path. Defaults to same name as source with .pdf extension.
        width: Optional page width (e.g., "210mm", "1200px"). Overrides format if set.
        height: Optional page height (e.g., "297mm", "1697px"). Overrides format if set.
        page_format: Page format (A4, A3, Letter, etc.). Ignored if width/height set.
        landscape: If True, use landscape orientation (swaps width/height of format).

    Returns:
        The absolute path to the generated PDF file.
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
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 设置 viewport 尺寸，与 PDF 页面尺寸匹配，避免缩放
        if width and height:
            w_px = int(width.replace("px", "")) if "px" in width else 800
            h_px = int(height.replace("px", "")) if "px" in height else 1100
            page.set_viewport_size({"width": w_px, "height": h_px})
        elif landscape:
            page.set_viewport_size({"width": 1123, "height": 795})  # A4 横向 96dpi
        else:
            page.set_viewport_size({"width": 794, "height": 1123})  # A4 纵向 96dpi
        
        # 强制使用 screen 媒体模式渲染（确保 Chart.js 等按屏幕 CSS 渲染）
        page.emulate_media(media="screen")
        
        page.goto(file_url, wait_until="networkidle")
        page.wait_for_timeout(8000)  # 等待 Chart.js 图表充分渲染（8秒）

        # Build pdf parameters
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
        description="Convert HTML file or URL to PDF using Playwright (headless Chromium).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 html2pdf.py report.html                          # A4 portrait
  python3 html2pdf.py report.html --landscape              # A4 landscape
  python3 html2pdf.py report.html --width 1200px --height 1697px  # custom size
  python3 html2pdf.py report.html output.pdf --format A3  # A3 format
"""
    )
    parser.add_argument("source", help="HTML file path or HTTP/HTTPS URL")
    parser.add_argument("output", nargs="?", default=None, help="Output PDF path (default: same name as source)")
    parser.add_argument("--width", help="Page width (e.g., '210mm', '1200px')")
    parser.add_argument("--height", help="Page height (e.g., '297mm', '1697px')")
    parser.add_argument("--format", default="A4", help="Page format: A4, A3, Letter, etc. (default: A4)")
    parser.add_argument("--landscape", action="store_true", help="Use landscape orientation")

    args = parser.parse_args()

    result = html_to_pdf(
        source=args.source,
        pdf_path=args.output,
        width=args.width,
        height=args.height,
        page_format=args.format,
        landscape=args.landscape,
    )
    print(f"PDF generated: {result}")

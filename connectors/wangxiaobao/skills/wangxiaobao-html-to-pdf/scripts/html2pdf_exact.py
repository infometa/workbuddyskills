"""Convert HTML to PDF with exact same layout as browser rendering.

Instead of fitting to A4, this script measures the actual rendered content size
and creates a PDF page that exactly matches, preserving the original layout 1:1.

Usage:
    python3 html2pdf_exact.py <html_path_or_url> [output_pdf_path]
"""

import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright


def html_to_pdf_exact(source: str, pdf_path: str = None) -> str:
    """
    Convert HTML to PDF preserving exact layout.
    Measures rendered content size and uses that as PDF page size.
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
        # Use a wide viewport to avoid unwanted wrapping
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(file_url, wait_until="networkidle")
        page.wait_for_timeout(5000)  # Wait for Chart.js to render

        # Get actual content dimensions
        dims = page.evaluate("""() => {
            const body = document.body;
            const html = document.documentElement;
            const width = Math.max(
                body.scrollWidth, body.offsetWidth,
                html.clientWidth, html.scrollWidth, html.offsetWidth
            );
            const height = Math.max(
                body.scrollHeight, body.offsetHeight,
                html.clientHeight, html.scrollHeight, html.offsetHeight
            );
            return { width: Math.ceil(width), height: Math.ceil(height) };
        }""")

        content_width = dims["width"]
        content_height = dims["height"]

        # Add small padding
        pdf_width = content_width + 2
        pdf_height = content_height + 2

        page.pdf(
            path=pdf_path,
            width=f"{pdf_width}px",
            height=f"{pdf_height}px",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
            display_header_footer=False,
            prefer_css_page_size=False,
        )
        browser.close()

    return pdf_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 html2pdf_exact.py <html_file_or_url> [output_pdf]")
        sys.exit(1)

    source_arg = sys.argv[1]
    pdf_arg = sys.argv[2] if len(sys.argv) > 2 else None

    result = html_to_pdf_exact(source_arg, pdf_arg)
    print(f"PDF generated: {result}")

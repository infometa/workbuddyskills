# -*- coding: utf-8 -*-
"""把简历 HTML 打印为 PDF（Windows，自动探测 Chrome / Edge 无头模式）。

用法：
    python scripts/html_to_pdf.py --html <resume.html> [--pdf <resume.pdf>]

- --pdf 省略时输出到 HTML 同目录同名 .pdf。
- 返回码：0 成功且 PDF 非空有效；1 未找到浏览器或生成失败。
- 只做机械渲染，不修改 HTML 内容。
"""
import argparse
import os
import subprocess
import sys

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    for path in BROWSER_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--pdf", default=None)
    args = ap.parse_args()

    html = os.path.abspath(args.html)
    if not os.path.exists(html):
        print("ERROR: html not found:", html)
        return 1
    pdf = os.path.abspath(args.pdf) if args.pdf else os.path.splitext(html)[0] + ".pdf"

    browser = find_browser()
    if not browser:
        print("ERROR: no Chrome/Edge found")
        return 1

    url = "file:///" + html.replace("\\", "/")
    cmd = [
        browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        "--print-to-pdf=" + pdf, url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    output = (proc.stdout or "") + (proc.stderr or "")

    if not os.path.exists(pdf) or os.path.getsize(pdf) < 1024:
        print("ERROR: pdf not generated or too small")
        print(output[-500:])
        return 1
    with open(pdf, "rb") as f:
        if f.read(5) != b"%PDF-":
            print("ERROR: invalid pdf header")
            return 1
    print("PDF_OK", pdf, os.path.getsize(pdf))
    return 0


if __name__ == "__main__":
    sys.exit(main())

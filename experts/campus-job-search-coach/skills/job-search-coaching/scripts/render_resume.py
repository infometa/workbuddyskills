#!/usr/bin/env python3
"""Render a controlled graduate-resume Markdown file to ATS-safe HTML and optional PDF.

The HTML path has no third-party dependency. PDF export requires a locally installed
Chromium-based browser. The script never edits the source Markdown file.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


BROWSER_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
]
BROWSER_COMMANDS = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
    "msedge",
    "brave-browser",
]


def inline_markup(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        r'<a href="\2">\1</a>',
        escaped,
    )
    return escaped


def markdown_to_body(markdown: str) -> str:
    parts: list[str] = []
    list_tag: str | None = None
    comment_open = False

    def close_list() -> None:
        nonlocal list_tag
        if list_tag:
            parts.append(f"</{list_tag}>")
            list_tag = None

    def open_list(tag: str) -> None:
        nonlocal list_tag
        if list_tag == tag:
            return
        close_list()
        parts.append(f"<{tag}>")
        list_tag = tag

    for raw_line in markdown.splitlines():
        line = raw_line.strip()

        if comment_open:
            if "-->" in line:
                comment_open = False
            continue
        if line.startswith("<!--"):
            if "-->" not in line:
                comment_open = True
            continue

        if not line:
            close_list()
            continue

        ordered_item = re.match(r"^\d+[.)]\s+(.+)$", line)
        if line.startswith("#### "):
            close_list()
            parts.append(f"<h4>{inline_markup(line[5:])}</h4>")
        elif line.startswith("### "):
            close_list()
            parts.append(f"<h3>{inline_markup(line[4:])}</h3>")
        elif line.startswith("## "):
            close_list()
            parts.append(f"<h2>{inline_markup(line[3:])}</h2>")
        elif line.startswith("# "):
            close_list()
            parts.append(f"<h1>{inline_markup(line[2:])}</h1>")
        elif re.fullmatch(r"-{3,}|\*{3,}|_{3,}", line):
            close_list()
            parts.append("<hr>")
        elif line.startswith("- ") or line.startswith("* "):
            open_list("ul")
            parts.append(f"<li>{inline_markup(line[2:])}</li>")
        elif ordered_item:
            open_list("ol")
            parts.append(f"<li>{inline_markup(ordered_item.group(1))}</li>")
        elif line.startswith("> "):
            close_list()
            parts.append(f"<blockquote><p>{inline_markup(line[2:])}</p></blockquote>")
        else:
            close_list()
            parts.append(f"<p>{inline_markup(line)}</p>")

    close_list()
    return "\n".join(parts)


def build_html(markdown: str, css: str, title: str) -> str:
    body = markdown_to_body(markdown)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
{css}
</style>
</head>
<body>
<main class="resume-page">
{body}
</main>
</body>
</html>
"""


def find_browser() -> str | None:
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    for command in BROWSER_COMMANDS:
        resolved = shutil.which(command)
        if resolved:
            return resolved
    return None


def render_pdf(browser: str, html_path: Path, pdf_path: Path) -> tuple[bool, str]:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="resume-browser-") as profile_dir:
        common = [
            browser,
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--allow-file-access-from-files",
            "--no-pdf-header-footer",
            f"--user-data-dir={profile_dir}",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]
        attempts = [[browser, "--headless=new", *common[1:]], [browser, "--headless", *common[1:]]]
        messages: list[str] = []
        for command in attempts:
            try:
                completed = subprocess.run(command, capture_output=True, text=True, timeout=20)
                messages.append((completed.stderr or completed.stdout).strip())
                if completed.returncode == 0 and pdf_path.is_file() and pdf_path.stat().st_size > 0:
                    return True, messages[-1]
            except subprocess.TimeoutExpired as exc:
                timeout_message = (exc.stderr or exc.stdout or b"")
                if isinstance(timeout_message, bytes):
                    timeout_message = timeout_message.decode("utf-8", errors="replace")
                messages.append(str(timeout_message).strip())
                if pdf_path.is_file() and pdf_path.stat().st_size > 0:
                    return True, "浏览器在生成 PDF 后未及时退出，已按实际文件完成状态处理。"
        return False, "\n".join(message for message in messages if message)


def detect_page_count(pdf_path: Path) -> int | None:
    mdls = shutil.which("mdls")
    if mdls:
        result = subprocess.run(
            [mdls, "-raw", "-name", "kMDItemNumberOfPages", str(pdf_path)],
            capture_output=True,
            text=True,
        )
        value = result.stdout.strip()
        if result.returncode == 0 and value.isdigit():
            return int(value)

    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        result = subprocess.run([pdfinfo, str(pdf_path)], capture_output=True, text=True)
        match = re.search(r"^Pages:\s+(\d+)$", result.stdout, re.MULTILINE)
        if result.returncode == 0 and match:
            return int(match.group(1))

    try:
        page_markers = re.findall(rb"/Type\s*/Page\b", pdf_path.read_bytes())
        if page_markers:
            return len(page_markers)
    except OSError:
        pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="将应届生简历 Markdown 渲染为 ATS 友好的 HTML 和可选 PDF。")
    parser.add_argument("input", type=Path, help="源 Markdown 文件")
    parser.add_argument("--html", dest="html_output", required=True, type=Path, help="HTML 输出路径")
    parser.add_argument("--pdf", dest="pdf_output", type=Path, help="可选 PDF 输出路径")
    parser.add_argument("--css", type=Path, help="自定义 CSS；默认使用包内 assets/themes/ats-safe.css")
    parser.add_argument("--title", default="应届生简历", help="HTML 文档标题")
    args = parser.parse_args()

    input_path = args.input.resolve()
    html_path = args.html_output.resolve()
    pdf_path = args.pdf_output.resolve() if args.pdf_output else None
    default_css = Path(__file__).resolve().parent.parent / "assets" / "themes" / "ats-safe.css"
    css_path = args.css.resolve() if args.css else default_css

    if not input_path.is_file():
        parser.error(f"源文件不存在：{input_path}")
    if not css_path.is_file():
        parser.error(f"CSS 文件不存在：{css_path}")
    if html_path == input_path or (pdf_path and pdf_path == input_path):
        parser.error("输出路径不能覆盖源 Markdown 文件")
    if pdf_path and pdf_path == html_path:
        parser.error("HTML 与 PDF 输出路径不能相同")

    markdown = input_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(build_html(markdown, css, args.title), encoding="utf-8")
    print(f"HTML 已生成：{html_path}")

    if not pdf_path:
        return 0

    browser = find_browser()
    if not browser:
        print("未找到 Chrome、Chromium、Edge 或 Brave；已保留 HTML，请用浏览器打开后打印为 PDF。", file=sys.stderr)
        return 2

    success, details = render_pdf(browser, html_path, pdf_path)
    if not success:
        print("PDF 渲染失败；已保留 HTML。", file=sys.stderr)
        if details:
            print(details, file=sys.stderr)
        return 3

    print(f"PDF 已生成：{pdf_path}")
    page_count = detect_page_count(pdf_path)
    if page_count is None:
        print("未能自动读取 PDF 页数，请人工打开核对。")
    elif page_count == 1:
        print("页数检查：1 页。")
    else:
        print(f"页数检查：{page_count} 页；请按简历手册的修剪顺序处理。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

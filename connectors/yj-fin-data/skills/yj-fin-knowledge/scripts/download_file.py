#!/usr/bin/env python3
"""把 fetch_document 的输出落成本地文件。

fetch_document 只返回两种「非二进制」形态，本脚本负责把它们变成磁盘上的文件：

  kind=text   正文已内联（Markdown / HTML / 纯文本）→ 直接写盘
  kind=url    第三方跳转直链                      → 客户端 GET 该直链，按响应写字节

安全边界：本脚本只请求命令行传入的 `--url`，绝不自行构造任何取址请求。

落盘纪律：
  - 文件名一律净化：去目录成分、去非法字符、拒绝路径穿越（`../` 与绝对路径）
  - 内容级去重：目录内已有同 sha256 内容的文件 → 不重复写入
  - 同名不覆盖：同名但内容不同 → 自动追加 `(1)` / `(2)` …

输出约定：成功时 **stdout 只打印落盘文件的绝对路径**（供上层回报用户）；
其余说明（去重跳过、自动重命名、扩展名修正）一律走 stderr。
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import unquote, urlparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.append(_SCRIPT_DIR)

from utils import default_skill_output_dir  # noqa: E402

DEFAULT_STEM = "document"
DEFAULT_TEXT_EXT = ".md"
DEFAULT_URL_EXT = ".bin"
REQUEST_TIMEOUT = 60
USER_AGENT = "Mozilla/5.0 (compatible; yj-fin-knowledge/1.0)"

# Content-Type → 扩展名。只登记实际会遇到的那几种；未命中再退回 URL 后缀 / 兜底。
CONTENT_TYPE_EXT = {
    "text/markdown": ".md",
    "text/x-markdown": ".md",
    "text/plain": ".txt",
    "text/html": ".html",
    "application/json": ".json",
    "application/xml": ".xml",
    "text/xml": ".xml",
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

_ILLEGAL_CHARS = '\\:*?"<>|=&'

EXAMPLES = """\
示例：
  # kind=text：把内联正文写盘（扩展名按 content_type 推断，file_name 优先）
  python3 scripts/download_file.py --kind text \\
      --content "# 调研纪要正文" \\
      --file-name "某公司调研纪要" --content-type "text/markdown"

  # kind=url：按 fetch_document 返回的直链下载（扩展名按响应头/Content-Type 修正）
  python3 scripts/download_file.py --kind url \\
      --url "https://example.com/redirect/abc" \\
      --file-name "某公司网络纪要" --content-type "text/html"

  # kind=text 也可以直接从文件读正文
  python3 scripts/download_file.py --kind text --text-file /tmp/body.md --out-dir ./out
"""


class DownloadError(Exception):
    """可行动的用户级错误（不抛裸栈，直接给处置建议）。"""


# ----------------------------------------------------------------- 文件名处理 ----

def sanitize_filename(name: str) -> str:
    """净化文件名：去目录成分、去非法字符、拒绝路径穿越。

    返回净化后的文件名；无法得到合法名字时返回空串（由调用方兜底）。
    """
    name = (name or "").strip().replace("\\", "/")
    name = name.split("/")[-1]  # 只取最后一段：干掉 ../ 与绝对路径
    name = "".join(
        c for c in name
        if c.isprintable() and c not in _ILLEGAL_CHARS and c != "\0"
    )
    name = name.strip(" .")
    if name in ("", ".", ".."):
        return ""
    return name


def _ensure_inside(directory: str, path: str) -> str:
    """兜底边界：净化后仍越出落盘目录则拒绝（防路径穿越的第二道闸）。"""
    base = os.path.abspath(directory)
    target = os.path.abspath(path)
    if target != base and not target.startswith(base + os.sep):
        raise DownloadError("文件名净化后仍越出落盘目录，已拒绝写入")
    return target


def _unique_path(directory: str, filename: str) -> str:
    """同名不覆盖：已存在则追加 (1) / (2) …"""
    root, ext = os.path.splitext(filename)
    i = 1
    candidate = os.path.join(directory, f"{root}({i}){ext}")
    while os.path.exists(candidate):
        i += 1
        candidate = os.path.join(directory, f"{root}({i}){ext}")
    return candidate


def guess_ext(content_type: str) -> str:
    """由 Content-Type 推断扩展名；推断不出返回空串。"""
    ct = (content_type or "").split(";")[0].strip().lower()
    if not ct:
        return ""
    if ct in CONTENT_TYPE_EXT:
        return CONTENT_TYPE_EXT[ct]
    if ct.endswith("+json"):
        return ".json"
    if ct.startswith("text/"):
        return ".txt"
    return ""


def parse_content_disposition_filename(header: str) -> str:
    """从 Content-Disposition 取文件名：`filename*=utf-8''` 优先，退回 `filename=`。"""
    if not header:
        return ""
    lower = header.lower()
    for marker in ("filename*=utf-8''", "filename*=", "filename="):
        idx = lower.find(marker)
        if idx == -1:
            continue
        raw = header[idx + len(marker):].split(";")[0].strip().strip('"')
        return unquote(raw)
    return ""


def resolve_text_name(file_name: str, content_type: str) -> str:
    """kind=text 的落盘名：`--file-name` 优先，缺扩展名时按 Content-Type 推断。"""
    stem = sanitize_filename(file_name)
    ext = os.path.splitext(stem)[1]
    if not ext:
        ext = guess_ext(content_type) or DEFAULT_TEXT_EXT
    return (os.path.splitext(stem)[0] if stem else DEFAULT_STEM) + ext


def resolve_url_name(file_name: str, cd_filename: str, url: str,
                     content_type: str, resp_content_type: str) -> tuple[str, str]:
    """kind=url 的落盘名。

    stem：`--file-name` 优先 → 响应头文件名 → URL 末段 → `document`
    ext ：响应头文件名后缀 → 响应 Content-Type → `--content-type` → URL 后缀 → `.bin`

    返回 (文件名, 说明)；说明非空时表示扩展名按响应头做了修正。
    """
    stem = os.path.splitext(sanitize_filename(file_name))[0]
    cd = sanitize_filename(cd_filename)
    cd_stem, cd_ext = os.path.splitext(cd)
    url_tail = sanitize_filename(os.path.basename(unquote(urlparse(url).path)))
    url_stem, url_ext = os.path.splitext(url_tail)

    base = stem or cd_stem or url_stem or DEFAULT_STEM
    ext = cd_ext or guess_ext(resp_content_type) or guess_ext(content_type) or url_ext
    note = ""
    if not ext:
        ext = DEFAULT_URL_EXT
    elif cd_ext and file_name and os.path.splitext(sanitize_filename(file_name))[1] not in ("", cd_ext):
        note = f"扩展名已按响应头修正为 {cd_ext}"
    return base + ext, note


# --------------------------------------------------------------------- 落盘 ----

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_bytes(out_dir: str, filename: str, data: bytes) -> tuple[str, str]:
    """把字节写盘，返回 (绝对路径, 说明)。

    ① 内容级去重：目录内已有同内容文件 → 复用既有文件，不重复写入
    ② 同名不覆盖：同名但内容不同 → 自动追加 `(1)` / `(2)` …
    """
    os.makedirs(out_dir, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()

    for existing in sorted(os.listdir(out_dir)):
        path = os.path.join(out_dir, existing)
        if os.path.isfile(path) and _sha256_file(path) == digest:
            return os.path.abspath(path), f"内容相同，已跳过重复写入（复用 {existing}）"

    target = _ensure_inside(out_dir, os.path.join(out_dir, filename))
    note = ""
    if os.path.exists(target):
        target = _ensure_inside(out_dir, _unique_path(out_dir, filename))
        note = "同名文件已存在，已自动重命名"
    with open(target, "wb") as f:
        f.write(data)
    return target, note


# ------------------------------------------------------------------ 取内容 ----

def _text_payload(args) -> tuple[bytes, str]:
    if args.text_file and args.content is not None:
        raise DownloadError("kind=text 的 `--text-file` 与 `--content` 只能给一个")
    if args.text_file:
        try:
            with open(args.text_file, "rb") as f:
                data = f.read()
        except OSError as e:
            raise DownloadError(f"读取正文文件失败：{args.text_file}（{e.strerror or e}）")
    elif args.content is not None:
        data = args.content.encode("utf-8")
    else:
        raise DownloadError("kind=text 需要 `--text-file` 或 `--content` 之一")
    if not data:
        raise DownloadError("正文为空，无可写入内容")
    return data, resolve_text_name(args.file_name, args.content_type)


def _url_payload(args) -> tuple[bytes, str, str]:
    url = (args.url or "").strip()
    if not url:
        raise DownloadError("kind=url 需要 `--url` 直链")
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):
        raise DownloadError(f"只支持 http/https 直链，收到：{url}")

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as resp:
            data = resp.read()
            cd_name = parse_content_disposition_filename(
                resp.headers.get("Content-Disposition", ""))
            resp_ct = resp.headers.get("Content-Type", "")
            final_url = resp.geturl() or url
    except urllib.error.HTTPError as e:
        raise DownloadError(f"下载失败：直链返回 HTTP {e.code}（{url}）")
    except urllib.error.URLError as e:
        raise DownloadError(f"下载失败：无法连接直链（{e.reason}）")
    except TimeoutError:
        raise DownloadError(f"下载失败：直链请求超时（{REQUEST_TIMEOUT}s）")

    if not data:
        raise DownloadError("下载失败：直链返回空内容")
    filename, note = resolve_url_name(
        args.file_name, cd_name, final_url, args.content_type, resp_ct)
    return data, filename, note


# --------------------------------------------------------------------- CLI ----

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="download_file.py",
        description="把 fetch_document 的输出落成本地文件"
                    "（kind=text 写内联正文 / kind=url 按直链下载字节）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EXAMPLES,
    )
    parser.add_argument("--kind", required=True, choices=("url", "text"),
                        help="fetch_document 返回的 kind：url=第三方直链；text=内联正文")
    parser.add_argument("--url", default="",
                        help="kind=url 必填：fetch_document 返回的直链")
    parser.add_argument("--content", default=None,
                        help="kind=text 用：直接传入正文文本")
    parser.add_argument("--text-file", default="",
                        help="kind=text 用：从文件读取正文（与 --content 二选一）")
    parser.add_argument("--file-name", default="",
                        help="fetch_document 返回的 file_name（可选，优先采用）")
    parser.add_argument("--content-type", default="",
                        help="fetch_document 返回的 content_type（可选，用于推断扩展名）")
    parser.add_argument("--out-dir", default="",
                        help="落盘目录（默认：技能工作目录下的 knowledge_documents/）")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.kind == "url":
            data, filename, note = _url_payload(args)
        else:
            data, filename = _text_payload(args)
            note = ""

        out_dir = os.path.expanduser(args.out_dir.strip()) or default_skill_output_dir()
        path, write_note = write_bytes(out_dir, filename, data)
    except DownloadError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    for message in (write_note, note):
        if message:
            print(message, file=sys.stderr)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

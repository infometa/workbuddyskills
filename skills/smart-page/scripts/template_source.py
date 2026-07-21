#!/usr/bin/env python3
"""
template_source.py · 模板资源统一访问层

所有 narrative.md / template.html / _assets/* / _index.json / 预览图
统一从远端 COS 读取：

    https://artifact-page.gtimg.com/html_templates/<rel_path>

可通过环境变量 SMART_PAGE_COS_BASE 覆盖（不含结尾 `/`）。

提供：
    cos_url(rel_path)  -> 绝对 URL
    fetch_text(rel)    -> 文本内容（UTF-8），每次直接联网拉取
    fetch_bytes(rel)   -> 字节内容，每次直接联网拉取
    load_index()       -> _index.json（解析为 dict）
    exists(rel)        -> 远端是否存在（HEAD 探测，进程内存 memo）

说明：当前版本**不做本地磁盘缓存**。如需排障或断网保护，将 HTTP 层替换即可。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_COS_BASE = "https://artifact-page.gtimg.com/html_templates"


def cos_base() -> str:
    return (os.environ.get("SMART_PAGE_COS_BASE") or DEFAULT_COS_BASE).rstrip("/")


def cos_url(rel_path: str) -> str:
    """拼接 COS 绝对 URL。rel_path 可带或不带前导 `/`。"""
    rel = rel_path.lstrip("/")
    return f"{cos_base()}/{rel}"


def _http_get(url: str, timeout: float = 15.0) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "smart-page-skill/1.0 (+template_source.py)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_bytes(rel_path: str, *, timeout: float = 15.0) -> bytes:
    """从 COS 拉取 rel_path 的原始字节（不缓存）。"""
    url = cos_url(rel_path)
    try:
        return _http_get(url, timeout=timeout)
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError) as e:
        raise RuntimeError(f"fetch COS resource failed: {url} ({e})") from e


def fetch_text(rel_path: str, *, timeout: float = 15.0) -> str:
    """从 COS 拉取文本（默认按 UTF-8 解码）。"""
    return fetch_bytes(rel_path, timeout=timeout).decode("utf-8")


def load_index() -> dict:
    """加载 _index.json 并解析。"""
    return json.loads(fetch_text("_index.json"))


def exists(rel_path: str, *, timeout: float = 10.0) -> bool:
    """HEAD 探测资源是否存在；结果缓存到进程内存（进程退出即失效）。"""
    if not hasattr(exists, "_memo"):
        exists._memo = {}  # type: ignore[attr-defined]
    memo = exists._memo  # type: ignore[attr-defined]
    if rel_path in memo:
        return memo[rel_path]

    url = cos_url(rel_path)
    req = urllib.request.Request(url, method="HEAD",
                                  headers={"User-Agent": "smart-page-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ok = 200 <= resp.status < 400
    except urllib.error.HTTPError as e:
        ok = 200 <= e.code < 400
    except (urllib.error.URLError, OSError, TimeoutError):
        ok = False
    memo[rel_path] = ok
    return ok


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="COS resource inspector")
    sub = p.add_subparsers(dest="cmd")

    pu = sub.add_parser("url", help="print COS absolute URL for rel_path")
    pu.add_argument("rel")

    pf = sub.add_parser("fetch", help="fetch and print text")
    pf.add_argument("rel")

    pe = sub.add_parser("exists", help="HEAD probe")
    pe.add_argument("rel")

    pi = sub.add_parser("index", help="dump _index.json")

    args = p.parse_args()
    if args.cmd == "url":
        print(cos_url(args.rel))
    elif args.cmd == "fetch":
        sys.stdout.write(fetch_text(args.rel))
    elif args.cmd == "exists":
        print("yes" if exists(args.rel) else "no")
    elif args.cmd == "index":
        print(json.dumps(load_index(), ensure_ascii=False, indent=2))
    else:
        p.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

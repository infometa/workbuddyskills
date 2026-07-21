#!/usr/bin/env python3
"""fetch_arxiv_tex.py

吸收自 karpathy/nanochat/.claude/skills/read-arxiv-paper：arXiv TeX Source 优先抓取。

输入：arXiv URL / arXiv ID（新旧格式都支持）
输出：
  - ~/.cache/paper-quick-reader/arxiv/{id}/src.tar.gz
  - ~/.cache/paper-quick-reader/arxiv/{id}/unpacked/  (解压后的 LaTeX 源树)
  - ~/.cache/paper-quick-reader/arxiv/{id}/source.pdf  (并行下载用于页码映射)
  - ~/.cache/paper-quick-reader/arxiv/{id}/manifest.json (入口文件 + 元数据)
  - stdout: JSON {arxiv_id, entry_tex, pdf_path, cache_dir, lines_read}

完整协议见 references/arxiv-fetch-protocol.md。
仅在 SKILL.md Step 2 判定 source.kind in {arxiv_url, arxiv_id} 时调用。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

__version__ = "0.2.0"

CACHE_ROOT = Path(os.environ.get(
    "PAPER_QR_ARXIV_CACHE",
    str(Path.home() / ".cache" / "paper-quick-reader" / "arxiv"),
))
USER_AGENT = f"paper-quick-reader/{__version__} (arxiv-fetch)"
RATE_LIMIT_SEC = float(os.environ.get("PAPER_QR_ARXIV_QPS_SLEEP", "3.0"))
MAX_TARBALL_MB = int(os.environ.get("PAPER_QR_ARXIV_MAX_MB", "50"))

# arxiv_id 识别正则（新旧格式）
RE_NEW_ID = re.compile(r"^(\d{4}\.\d{4,5})(v\d+)?$")
RE_OLD_ID = re.compile(r"^([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?$")
RE_ABS_URL = re.compile(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+?)(?:\.pdf)?(?:[?#].*)?$", re.I)


def normalize_id(raw: str, keep_version: bool = False) -> str:
    """把任意形式的 arXiv 输入规范化为 ID。失败抛 ValueError。"""
    s = raw.strip()
    # 去前缀 arXiv:
    if s.lower().startswith("arxiv:"):
        s = s[len("arxiv:"):].strip()
    # 是 URL 吗？
    if s.startswith("http"):
        m = RE_ABS_URL.search(s)
        if not m:
            raise ValueError(f"无法从 URL 提取 arXiv ID: {raw}")
        s = m.group(1)
    # 新旧格式判定
    m_new = RE_NEW_ID.match(s)
    if m_new:
        return m_new.group(1) + (m_new.group(2) if keep_version and m_new.group(2) else "")
    m_old = RE_OLD_ID.match(s)
    if m_old:
        return m_old.group(1) + (m_old.group(2) if keep_version and m_old.group(2) else "")
    raise ValueError(f"无效的 arXiv ID 或 URL: {raw}")


def cache_dir_for(arxiv_id: str) -> Path:
    """对应 ID 的本地缓存目录。"""
    safe = arxiv_id.replace("/", "_")
    return CACHE_ROOT / safe


def fetch(url: str, dest: Path, *, timeout: int = 60) -> int:
    """下载 URL 到 dest，返回字节数。遵循 arXiv 速率限制。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    time.sleep(RATE_LIMIT_SEC)  # 保守速率
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    if len(data) > MAX_TARBALL_MB * 1024 * 1024:
        raise IOError(
            f"下载内容超过 {MAX_TARBALL_MB}MB 上限（实际 {len(data)/1024/1024:.1f}MB）"
        )
    dest.write_bytes(data)
    return len(data)


def safe_extract_tarball(tar_path: Path, dest: Path) -> None:
    """安全解压 tarball（拒绝 .. 和绝对路径，防路径穿越攻击）。"""
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    with tarfile.open(tar_path, "r:*") as tf:
        for member in tf.getmembers():
            member_path = (dest / member.name).resolve()
            if not str(member_path).startswith(str(dest_resolved)):
                raise IOError(f"拒绝不安全的 tar 成员: {member.name}")
            if member.islnk() or member.issym():
                # 避免 symlink 逃逸
                continue
        tf.extractall(dest)  # 已逐个校验成员


TEX_ENTRY_CANDIDATES = [
    "main.tex",
    "paper.tex",
    "article.tex",
    "ms.tex",
    "manuscript.tex",
]


def find_tex_entry(unpacked: Path, arxiv_id: str) -> Optional[Path]:
    """按 references/arxiv-fetch-protocol.md § 3.3 的优先级定位入口。"""
    # 1. 常见命名
    for name in TEX_ENTRY_CANDIDATES:
        p = unpacked / name
        if p.is_file() and _contains_documentclass(p):
            return p
    # 2. {id}.tex
    id_variants = [arxiv_id.replace("/", "_"), arxiv_id.split("/")[-1]]
    for vid in id_variants:
        p = unpacked / f"{vid}.tex"
        if p.is_file() and _contains_documentclass(p):
            return p
    # 3. 目录下所有 .tex，找含 \documentclass 的
    candidates = [p for p in unpacked.rglob("*.tex") if _contains_documentclass(p)]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        # 取 \begin{document} 之前 preamble 最短的（通常是真入口，template 会有大量 macro）
        def preamble_len(p: Path) -> int:
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return 10**9
            idx = txt.find("\\begin{document}")
            return idx if idx > 0 else len(txt)
        candidates.sort(key=preamble_len)
        return candidates[0]
    return None


def _contains_documentclass(p: Path) -> bool:
    try:
        head = p.read_text(encoding="utf-8", errors="ignore")[:8000]
    except Exception:
        return False
    return "\\documentclass" in head


def count_tex_lines(entry: Path, max_depth: int = 5) -> int:
    """统计 main + \\input/\\include 递归后的总行数（用于 manifest 报告）。不做内联展开。"""
    seen = set()
    total = 0

    def _walk(p: Path, depth: int) -> None:
        nonlocal total
        if depth > max_depth or p in seen or not p.is_file():
            return
        seen.add(p)
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return
        total += len(lines)
        inputs = re.findall(r"\\(?:input|include|subfile)\{([^}]+)\}", "\n".join(lines))
        for raw in inputs:
            child = raw.strip()
            if not child.endswith(".tex"):
                child += ".tex"
            child_path = (p.parent / child).resolve()
            _walk(child_path, depth + 1)

    _walk(entry, 0)
    return total


def build_manifest(arxiv_id: str, cache: Path, entry: Optional[Path], pdf: Optional[Path], stats: dict) -> Path:
    manifest = {
        "arxiv_id": arxiv_id,
        "version": __version__,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "cache_dir": str(cache),
        "tex_entry": str(entry.relative_to(cache)) if entry else None,
        "pdf_path": str(pdf.relative_to(cache)) if pdf else None,
        "tex_entry_absolute": str(entry) if entry else None,
        "pdf_absolute": str(pdf) if pdf else None,
        "stats": stats,
        "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
    }
    out = cache / "manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return out


def fetch_arxiv(raw_input: str, *, keep_pdf: bool = True, force: bool = False) -> dict:
    """主入口：下载 + 解压 + 定位入口 + 生成 manifest。返回 dict（同时写 manifest.json）。"""
    arxiv_id = normalize_id(raw_input)
    cache = cache_dir_for(arxiv_id)
    cache.mkdir(parents=True, exist_ok=True)

    src_url = f"https://arxiv.org/src/{arxiv_id}"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    src_path = cache / "src.tar.gz"
    pdf_path = cache / "source.pdf"
    unpacked = cache / "unpacked"

    stats = {"tex_bytes": 0, "pdf_bytes": 0, "total_tex_lines": 0, "from_cache": False}

    # tarball
    if src_path.exists() and not force:
        stats["from_cache"] = True
        stats["tex_bytes"] = src_path.stat().st_size
    else:
        try:
            stats["tex_bytes"] = fetch(src_url, src_path)
        except HTTPError as e:
            raise IOError(f"arXiv TeX tarball 404/403 ({arxiv_id}): {e}") from e
        except URLError as e:
            raise IOError(f"arXiv TeX 下载失败（网络/DNS）: {e}") from e

    # 解压
    if force and unpacked.exists():
        shutil.rmtree(unpacked)
    if not unpacked.exists() or not any(unpacked.iterdir()):
        safe_extract_tarball(src_path, unpacked)

    # 入口定位
    entry = find_tex_entry(unpacked, arxiv_id)
    if entry is None:
        raise IOError(f"ARXIV_TEX_ENTRY_NOT_FOUND: 无法定位 {arxiv_id} 的 main.tex，建议走 PDF 路径")
    stats["total_tex_lines"] = count_tex_lines(entry)

    # 并行下载 PDF（用于页码映射）
    pdf_final: Optional[Path] = None
    if keep_pdf:
        if pdf_path.exists() and not force:
            pdf_final = pdf_path
            stats["pdf_bytes"] = pdf_path.stat().st_size
        else:
            try:
                stats["pdf_bytes"] = fetch(pdf_url, pdf_path)
                pdf_final = pdf_path
            except Exception:
                # PDF 失败非致命（TeX 路径仍可用），只是 provenance 页码会降级
                pdf_final = None

    manifest = build_manifest(arxiv_id, cache, entry, pdf_final, stats)

    return {
        "arxiv_id": arxiv_id,
        "entry_tex": str(entry),
        "pdf_path": str(pdf_final) if pdf_final else None,
        "cache_dir": str(cache),
        "manifest": str(manifest),
        "stats": stats,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="fetch_arxiv_tex",
        description="下载 arXiv TeX tarball + PDF（供 paper-quick-reader 使用）",
    )
    ap.add_argument("input", help="arXiv URL 或 ID（例：https://arxiv.org/abs/2601.07372 或 2601.07372）")
    ap.add_argument("--no-pdf", action="store_true", help="跳过并行 PDF 下载（不推荐：页码 provenance 会丢失）")
    ap.add_argument("--force", action="store_true", help="忽略缓存，强制重新下载")
    ap.add_argument("--json", action="store_true", default=True, help="仅输出 JSON（默认开启）")
    args = ap.parse_args(argv)

    try:
        result = fetch_arxiv(args.input, keep_pdf=not args.no_pdf, force=args.force)
    except Exception as e:
        err = {"error": e.__class__.__name__, "message": str(e)}
        print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

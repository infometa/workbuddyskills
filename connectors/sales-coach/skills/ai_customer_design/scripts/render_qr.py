#!/usr/bin/env python3
"""render_qr.py — 练习链接二维码渲染器（RFC §3.8 / T10）.

独立 QR 渲染工具：
- 依赖随包分发的 vendor/segno（无 pip 依赖，干净 venv 可用）
- 无网络调用、无凭证读写、不实现 MCP
- 错误码：E-USER-ARGS（参数，exit 2）/ E-HOST-DEP（依赖，exit 3）/ E-USER-OUT（输出路径，exit 2）

用法：
    python3 render_qr.py '<练习链接>' [--out <png路径>]
"""
import argparse
import importlib
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

# ============================================================================
# Vendor Bootstrap — vendored segno 无需 pip install
# ============================================================================

_VENDOR_DIR = Path(__file__).resolve().parent.parent / "vendor"

segno = None
if _VENDOR_DIR.is_dir():
    vendor_str = str(_VENDOR_DIR)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)
    importlib.invalidate_caches()
    try:
        import segno
    except ImportError:
        segno = None
# vendor 目录不存在 → segno 保持 None → E-HOST-DEP（vendored 依赖是硬性前置条件）

EXIT_ARGS = 2   # E-USER-ARGS / E-USER-OUT
EXIT_DEP = 3    # E-HOST-DEP


def fail_args(msg: str) -> None:
    print(f"E-USER-ARGS: {msg}", file=sys.stderr)
    sys.exit(EXIT_ARGS)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="render_qr.py",
        description="把练习链接渲染成 PNG 二维码（纯本地，无网络）",
    )
    parser.add_argument("url", help="要编码的练习链接（http/https）")
    parser.add_argument(
        "--out",
        default=None,
        help="输出 PNG 路径（默认：系统临时目录 practice.png）",
    )
    args = parser.parse_args()

    url = (args.url or "").strip()

    # ---- URL 校验：空/非 http(s) ----
    if not url:
        fail_args(f"URL 缺失或不合法：{args.url!r}")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        fail_args(f"URL 缺失或不合法：{url}")

    # ---- 依赖检查 ----
    if segno is None:
        print(
            "E-HOST-DEP: 二维码依赖不可用（vendored segno 缺失或损坏）；"
            "请直接使用原始练习链接：",
            file=sys.stdout,
        )
        print(url, file=sys.stdout)
        sys.exit(EXIT_DEP)

    # ---- 生成二维码 ----
    out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / "practice.png"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)  # --out 父目录不存在时自动创建
        qr = segno.make(url, error="m")
        qr.save(str(out), scale=8, border=2)
    except OSError as e:
        print(f"E-USER-OUT: 输出路径不可写：{out}（{e}）", file=sys.stderr)
        sys.exit(EXIT_ARGS)

    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

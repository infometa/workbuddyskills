#!/usr/bin/env python3
"""PDF → PNG 逐页转换（发票查验前的文件预处理）。

用法:
    python3 pdf_to_png.py <pdf路径> [输出目录] [--dpi 200]

输出: 每个页面生成一个 PNG，stdout 每行一个绝对路径。
依赖: PyMuPDF（pip install pymupdf）；未安装时退出码 2，由上层脚本回退到其他后端。
"""
import argparse
import os
import sys


def load_fitz():
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24 推荐入口
        return fitz
    except ImportError:
        try:
            import fitz  # 旧版兼容（已废弃）
            return fitz
        except ImportError:
            return None


def main():
    ap = argparse.ArgumentParser(description="PDF 转 PNG（逐页）")
    ap.add_argument("pdf", help="PDF 文件路径")
    ap.add_argument("outdir", nargs="?", default=None, help="输出目录，默认 <pdf同目录>/<pdf名>_pages")
    ap.add_argument("--dpi", type=int, default=200, help="渲染 DPI，默认 200（发票建议 200~300）")
    args = ap.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"ERROR: 文件不存在 {args.pdf}", file=sys.stderr)
        return 1

    fitz = load_fitz()
    if fitz is None:
        print("ERROR: 需要 PyMuPDF，请先执行 pip install pymupdf", file=sys.stderr)
        return 2

    base = os.path.splitext(os.path.basename(args.pdf))[0]
    outdir = args.outdir or os.path.join(os.path.dirname(os.path.abspath(args.pdf)), f"{base}_pages")
    os.makedirs(outdir, exist_ok=True)

    doc = fitz.open(args.pdf)
    if doc.page_count == 0:
        print("ERROR: PDF 没有页面", file=sys.stderr)
        return 3

    zoom = args.dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        out = os.path.join(outdir, f"{base}_p{i}.png")
        pix.save(out)
        print(out)

    print(f"共 {doc.page_count} 页，DPI={args.dpi}，输出目录 {outdir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

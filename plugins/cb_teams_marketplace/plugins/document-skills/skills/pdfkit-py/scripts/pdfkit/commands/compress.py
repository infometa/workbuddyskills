#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 压缩。支持 Ghostscript（主要）和 pikepdf（备选）两种压缩方式。"""

import os

COMMAND = "compress"
DESCRIPTION = "Compress PDF file size"
CATEGORY = "organize"

PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "Input PDF path"},
    {"name": "output", "type": "str", "required": True, "help": "Output PDF path"},
    {"name": "quality", "type": "str", "required": False, "default": "ebook", "choices": ["screen", "ebook", "printer", "prepress"], "help": "Compression quality level"},
    {"name": "target_size_mb", "type": "float", "required": False, "help": "Target file size in MB (auto-adjust quality)"},
]


def handler(params):
    """压缩 PDF 文件体积。"""
    import shutil
    import subprocess

    input_path = params["input"]
    output_path = params["output"]
    quality = params.get("quality", "ebook")
    target_size_mb = params.get("target_size_mb", None)

    original_size = os.path.getsize(input_path)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    engine_used = "none"

    # 质量级别映射
    quality_levels = ["screen", "ebook", "printer", "prepress"]
    if quality not in quality_levels:
        quality = "ebook"

    # 尝试 Ghostscript
    gs_path = shutil.which("gs") or shutil.which("gswin64c") or shutil.which("gswin32c")
    if gs_path:
        def compress_with_gs(q, out):
            cmd = [
                gs_path,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS=/{q}",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={out}",
                input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(f"Ghostscript 压缩失败: {result.stderr}")
            return os.path.getsize(out)

        if target_size_mb:
            # 迭代调整质量直到满足目标大小
            target_bytes = target_size_mb * 1024 * 1024
            best_quality = quality
            best_size = original_size

            for q in quality_levels:
                try:
                    compressed_size = compress_with_gs(q, output_path)
                    if compressed_size <= target_bytes:
                        best_quality = q
                        best_size = compressed_size
                        break
                    best_quality = q
                    best_size = compressed_size
                except Exception:
                    continue

            quality = best_quality
            compressed_size = best_size
        else:
            compressed_size = compress_with_gs(quality, output_path)

        engine_used = "ghostscript"

    else:
        # Ghostscript 不可用，尝试 pikepdf
        try:
            import pikepdf

            pdf = pikepdf.open(input_path)

            # pikepdf 压缩选项
            save_kwargs = {
                "linearize": True,
                "object_stream_mode": pikepdf.ObjectStreamMode.generate,
            }

            if quality in ("screen", "ebook"):
                save_kwargs["compress_streams"] = True
                save_kwargs["recompress_flate"] = True

            pdf.save(output_path, **save_kwargs)
            pdf.close()

            compressed_size = os.path.getsize(output_path)
            engine_used = "pikepdf"

        except ImportError:
            # 最后尝试 PyMuPDF 的基础压缩
            try:
                import fitz

                doc = fitz.open(input_path)
                # PyMuPDF 的 garbage 和 deflate 选项
                doc.save(
                    output_path,
                    garbage=4,      # 最大垃圾回收级别
                    deflate=True,   # 压缩流
                    clean=True,     # 清理内容流
                )
                doc.close()

                compressed_size = os.path.getsize(output_path)
                engine_used = "pymupdf"

            except ImportError:
                raise RuntimeError("无可用的压缩引擎。请安装 Ghostscript、pikepdf 或 PyMuPDF。")

    # 计算压缩比
    compression_ratio = round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0

    return {
        "success": True,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "original_size_mb": round(original_size / (1024 * 1024), 2),
        "compressed_size_mb": round(compressed_size / (1024 * 1024), 2),
        "compression_ratio": compression_ratio,
        "quality": quality,
        "engine": engine_used,
        "output": output_path,
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)

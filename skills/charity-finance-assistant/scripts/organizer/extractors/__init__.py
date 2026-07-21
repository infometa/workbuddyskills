"""
v1.3 抽取器统一入口：根据扩展名调度到对应抽取器。
"""
from organizer.config import IMAGE_EXTS, PDF_EXTS, DOCX_EXTS
from organizer.extractors.base import empty_fields
from organizer.extractors.pdf import extract_pdf_fields
from organizer.extractors.docx import extract_docx_fields
from organizer.extractors.image import extract_image_fields


# 扩展名 → 抽取函数
EXTRACTOR_DISPATCH = [
    (PDF_EXTS, extract_pdf_fields),
    (IMAGE_EXTS, extract_image_fields),
    (DOCX_EXTS, extract_docx_fields),
]


def dispatch_extract(file_path):
    """
    根据扩展名选择抽取器。无匹配时返回空字段字典。
    圈复杂度 = 3。
    """
    ext = file_path.suffix.lower()
    for exts, fn in EXTRACTOR_DISPATCH:
        if ext in exts:
            return fn(file_path)
    return empty_fields("不支持的格式")


__all__ = [
    "extract_pdf_fields",
    "extract_docx_fields",
    "extract_image_fields",
    "dispatch_extract",
]

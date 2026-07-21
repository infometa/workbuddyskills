"""
v1.3 分类模块：文件分类 + 费用科目建议 + 文件名元数据提取。
"""
from pathlib import Path
from organizer.config import (
    CATEGORY_KEYWORDS,
    EXPENSE_KEYWORDS,
    EXCEL_EXTS,
    DOCX_EXTS,
    PDF_EXTS,
    IMAGE_EXTS,
)
from organizer import patterns as P


# 扩展名 → 默认分类（无关键词命中时使用）
_EXT_DEFAULT_CATEGORY = [
    (EXCEL_EXTS, "Excel数据表"),
    (DOCX_EXTS, "DOCX文件"),
    (PDF_EXTS, "PDF文件"),
    (IMAGE_EXTS, "未分类票据图片"),
]


def _build_haystack(file_path: Path, file_text: str) -> str:
    """构造关键词搜索目标：文件名 + 父目录 + 文件内容"""
    name_lower = file_path.stem.lower() + " " + str(file_path.parent).lower()
    if file_text:
        return name_lower + " " + file_text.lower()
    return name_lower


def _match_keyword(haystack):
    """按关键词长度倒序匹配，命中即返回类别"""
    for keyword, category in sorted(
        CATEGORY_KEYWORDS, key=lambda x: len(x[0]), reverse=True
    ):
        if keyword.lower() in haystack:
            return category
    return None


def _ext_default_category(file_path: Path) -> str:
    """文件扩展名兜底分类"""
    ext = file_path.suffix.lower()
    for exts, cat in _EXT_DEFAULT_CATEGORY:
        if ext in exts:
            return cat
    return "其他"


def classify_file(file_path: Path, file_text: str = "") -> str:
    """
    根据文件名和内容关键词分类。
    圈复杂度 = 3：构造 haystack + 关键词匹配 + 扩展名兜底。
    """
    haystack = _build_haystack(file_path, file_text)
    cat = _match_keyword(haystack)
    if cat:
        return cat
    return _ext_default_category(file_path)


def suggest_expense_category(file_path: Path, classification: str = "") -> str:
    """根据文件名和分类猜测费用科目（圈复杂度 = 3）"""
    if "捐赠" in classification:
        return "捐赠收入—限定性/非限定性（需判断）"
    name = file_path.stem.lower()
    for keyword, category in EXPENSE_KEYWORDS.items():
        if keyword in name:
            return category
    return "待分类"


def extract_date_from_name(file_path: Path) -> str:
    """从文件名提取日期（圈复杂度 = 3）"""
    name = file_path.stem
    for pattern in P.NAME_DATE_PATTERNS:
        m = pattern.search(name)
        if not m:
            continue
        y, mo, d = m.groups()
        try:
            return f"{y}-{int(mo):02d}-{int(d):02d}"
        except ValueError:
            continue
    return ""


def extract_amount_from_name(file_path: Path):
    """从文件名提取金额（圈复杂度 = 3）"""
    name = file_path.stem
    for pattern in P.NAME_AMOUNT_PATTERNS:
        m = pattern.search(name)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                continue
    return None

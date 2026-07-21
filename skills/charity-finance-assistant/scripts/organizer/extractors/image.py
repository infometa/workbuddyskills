"""
v1.3 图片 OCR 抽取器：拆解原 extract_image_fields（圈复杂度 30 → ≤ 6）。

拆解策略：
- _get_ocr_reader()        OCR 单例懒加载
- _load_image_as_array()   PIL 加载
- _ocr_to_text()           调 reader.readtext
- _parse_num()             安全数值解析
- _looks_like_date()       排除日期误命中
- _find_amount_near_kw()   关键词附近找金额
- _find_amount_fallback()  全文兜底找最大合理金额
- _extract_invoice_no_ocr() OCR 票号提取
- extract_image_fields()   只编排（圈复杂度 ≈ 5）
"""
import re

from organizer.extractors.base import empty_fields
from organizer import patterns as P

try:
    import easyocr  # noqa: F401
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

_OCR_READER = None  # 单例


def _get_ocr_reader():
    """首次调用时初始化 easyocr Reader（加载约 3~10 秒）"""
    global _OCR_READER
    if _OCR_READER is not None:
        return _OCR_READER
    if not HAS_EASYOCR:
        return None
    try:
        import easyocr
        print("  [OCR] 首次调用 OCR，正在初始化中英文模型（约 3~10 秒）...")
        _OCR_READER = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
        return _OCR_READER
    except Exception as e:
        print(f"  [WARN] OCR 初始化失败: {e}")
        return None


def _load_image_as_array(img_path):
    """用 PIL 加载图片并转 numpy 数组，规避 OpenCV 不支持中文路径的问题"""
    try:
        from PIL import Image
        import numpy as np
        with Image.open(str(img_path)) as img:
            return np.array(img.convert("RGB"))
    except Exception:
        return None


def _ocr_to_text(reader, arr):
    """调用 OCR 引擎，返回 (text, error_msg)"""
    try:
        lines = reader.readtext(arr, detail=0, paragraph=False)
        return "\n".join(lines), None
    except Exception as e:
        return "", f"OCR失败: {e}"


def _parse_num(s):
    """安全解析金额字符串。合理范围 0.01 ~ 9999999.99 才返回 float。"""
    try:
        v = float(s.replace(",", "").replace("，", ""))
    except ValueError:
        return None
    if 0.01 <= v <= 9_999_999.99:
        return v
    return None


def _looks_like_date(s, context_text):
    """
    判断候选金额字符串是否其实是日期的一部分。
    例如 "2026.03" 看起来像金额，但其实是 "2026.03.12" 的前缀。
    """
    if not s:
        return False
    # 单独的年份（2020~2099）
    try:
        cleaned = s.replace(".", "").replace(",", "")
        if cleaned.isdigit():
            v = float(s.replace(",", ""))
            if 2020 <= v <= 2099 and "." not in s:
                return True
    except ValueError:
        pass
    # "2026.03" 这种，原文中后面紧跟 ".dd"
    idx = context_text.find(s)
    if idx < 0:
        return False
    tail = context_text[idx + len(s): idx + len(s) + 4]
    return bool(re.match(r"\.\d{1,2}", tail))


def _find_amount_in_text(search_text, full_text):
    """在指定文本范围内找金额候选，按优先级返回首个合理值"""
    candidate_patterns = [
        r"\d{1,6}\.\d{2}",
        r"\d{1,3}(?:,\d{3})+(?:\.\d+)?",
        r"\b\d{2,6}\b",
    ]
    for pat in candidate_patterns:
        cands = re.findall(pat, search_text)
        for c in cands:
            if _looks_like_date(c, full_text):
                continue
            v = _parse_num(c)
            if v:
                return v
    return None


def _find_amount_near_keyword(text):
    """第 1 步：在关键词所在行 + 下一行查找金额"""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for i, ln in enumerate(lines):
        if not any(kw in ln for kw in P.OCR_TOTAL_KEYWORDS):
            continue
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        v = _find_amount_in_text(ln + " " + next_line, text)
        if v:
            return v
    return None


def _find_amount_fallback(text):
    """第 2 步：全文找带小数/千分位的合理金额，取最大"""
    candidates = []
    pattern = r"\d{1,3}(?:,\d{3})+\.\d{2}|\d{1,3}(?:,\d{3})+|\d+\.\d{2}"
    for m in re.finditer(pattern, text):
        s = m.group(0)
        if _looks_like_date(s, text):
            continue
        v = _parse_num(s)
        if v:
            candidates.append(v)
    return max(candidates) if candidates else None


def _extract_amount_from_ocr(text):
    """
    OCR 价税合计提取（v1.3 用早返回替代多层 if）：
    1) 关键词附近优先
    2) 兜底全文最大合理金额
    """
    v = _find_amount_near_keyword(text)
    if v is None:
        v = _find_amount_fallback(text)
    return f"{v:.2f}" if v else ""


def _extract_date_from_ocr(text):
    """OCR 日期：YYYY-MM-DD 或空"""
    m = P.RE_OCR_DATE.search(text)
    if not m:
        return ""
    y, mo, d = m.groups()
    try:
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    except ValueError:
        return ""


def _extract_invoice_no_from_ocr(text, issue_date):
    """
    OCR 票号：找 8~20 位连续数字，排除日期格式。
    issue_date 用于排除“开票日期数字串”被误当票号。
    """
    date_digits = {issue_date.replace("-", "")} if issue_date else set()
    for token in re.findall(r"\b(\d{8,20})\b", text):
        if token in date_digits:
            continue
        # 排除像 20250225 这种可能是日期的数字
        if (
            len(token) == 8
            and token.startswith("20")
            and 1 <= int(token[4:6]) <= 12
        ):
            continue
        return token
    return ""


def extract_image_fields(img_path):
    """
    从图片票据 OCR 提取关键信息。
    圈复杂度 ≈ 5：reader 检查 + 加载失败 + OCR 失败 + 正常路径。
    """
    reader = _get_ocr_reader()
    if reader is None:
        return empty_fields("缺少easyocr")

    arr = _load_image_as_array(img_path)
    if arr is None:
        return empty_fields("图片读取失败")

    text, err = _ocr_to_text(reader, arr)
    if err:
        return empty_fields(err)

    fields = empty_fields("OCR成功")
    fields["_raw_text"] = text
    fields["开票日期"] = _extract_date_from_ocr(text)
    fields["价税合计"] = _extract_amount_from_ocr(text)
    fields["发票号码"] = _extract_invoice_no_from_ocr(text, fields["开票日期"])
    return fields

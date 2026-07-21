"""
v1.3 PDF 抽取器：拆解原 extract_pdf_fields（圈复杂度 25 → ≤ 5）。

策略：
- _read_pdf_text() 单一职责：读 PDF 全文
- extract_pdf_fields() 只编排：读文本 + 调 fill_fields_from_text
"""
from organizer.extractors.base import empty_fields, fill_fields_from_text

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def _read_pdf_text(pdf_path):
    """
    读取 PDF 全部页面文本，并清理常见噪声字符。
    返回 (text, error_msg)。成功时 error_msg 为 None。
    """
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception as e:
        return "", f"解析失败: {e}"
    # 清理空字节、非断行空格等
    cleaned = text.replace("\x00", " ").replace("\u00a0", " ").replace("\u3000", " ")
    return cleaned, None


def extract_pdf_fields(pdf_path):
    """
    从 PDF 提取发票要素。
    圈复杂度 ≈ 4：HAS_PDFPLUMBER 检查 + 读文本失败检查 + 正常路径。
    """
    if not HAS_PDFPLUMBER:
        return empty_fields("缺少pdfplumber")

    text, err = _read_pdf_text(pdf_path)
    if err:
        return empty_fields(err)

    fields = empty_fields("成功")
    fields["_raw_text"] = text
    fill_fields_from_text(fields, text)
    return fields

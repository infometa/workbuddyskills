#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 解密。"""

import os

COMMAND = "decrypt"
DESCRIPTION = "Decrypt a password-protected PDF"
CATEGORY = "security"

PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "Encrypted PDF path"},
    {"name": "output", "type": "str", "required": True, "help": "Output PDF path"},
    {"name": "password", "type": "str", "required": True, "help": "Decryption password"},
]


def handler(params):
    """解密 PDF 文件。"""
    from pypdf import PdfReader, PdfWriter

    input_path = params["input"]
    output_path = params["output"]
    password = params["password"]

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(input_path)

    if not reader.is_encrypted:
        return {"success": False, "error": "该 PDF 未加密，无需解密"}

    try:
        reader.decrypt(password)
    except Exception as e:
        raise RuntimeError(f"解密失败，密码可能不正确: {e}")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    if reader.metadata:
        try:
            writer.add_metadata(reader.metadata)
        except Exception:
            pass

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "action": "decrypt",
        "page_count": len(reader.pages),
        "output": output_path
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)

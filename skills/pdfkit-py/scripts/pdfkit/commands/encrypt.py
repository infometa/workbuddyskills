#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 加密。"""

import os

COMMAND = "encrypt"
DESCRIPTION = "Encrypt a PDF with password protection"
CATEGORY = "security"

PARAMS = [
    {"name": "input",          "type": "str",  "required": True,  "help": "Input PDF path"},
    {"name": "output",         "type": "str",  "required": True,  "help": "Output PDF path"},
    {"name": "user_password",  "type": "str",  "required": True,  "help": "User password (to open document)"},
    {"name": "owner_password", "type": "str",  "required": False, "help": "Owner password (defaults to user_password)"},
    {"name": "allow_print",    "type": "bool", "required": False, "default": True,  "help": "Allow printing"},
    {"name": "allow_modify",   "type": "bool", "required": False, "default": False, "help": "Allow modification"},
    {"name": "allow_copy",     "type": "bool", "required": False, "default": False, "help": "Allow copying"},
]


def handler(params):
    """加密 PDF 文件。

    Args:
        params: {
            "input": PDF 路径,
            "output": 输出 PDF 路径,
            "user_password": 用户密码（打开文档）,
            "owner_password": 所有者密码（可选，默认与用户密码相同）,
            "allow_print": 是否允许打印（可选，默认 True）,
            "allow_modify": 是否允许修改（可选，默认 False）,
            "allow_copy": 是否允许复制（可选，默认 False）
        }
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.constants import UserAccessPermissions

    input_path = params["input"]
    output_path = params["output"]
    user_password = params["user_password"]
    owner_password = params.get("owner_password") or user_password
    allow_print = params.get("allow_print", True)
    allow_modify = params.get("allow_modify", False)
    allow_copy = params.get("allow_copy", False)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # 复制元数据
    if reader.metadata:
        writer.add_metadata(reader.metadata)

    # 构建权限标志
    permissions = UserAccessPermissions(0)
    if allow_print:
        permissions |= UserAccessPermissions.PRINT | UserAccessPermissions.PRINT_TO_REPRESENTATION
    if allow_modify:
        permissions |= UserAccessPermissions.MODIFY | UserAccessPermissions.ADD_OR_MODIFY
    if allow_copy:
        permissions |= UserAccessPermissions.EXTRACT | UserAccessPermissions.EXTRACT_TEXT_AND_GRAPHICS

    # 加密
    writer.encrypt(
        user_password=user_password,
        owner_password=owner_password,
        use_128bit=True,
        permissions_flag=permissions,
    )

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "action": "encrypt",
        "page_count": len(reader.pages),
        "output": output_path
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)

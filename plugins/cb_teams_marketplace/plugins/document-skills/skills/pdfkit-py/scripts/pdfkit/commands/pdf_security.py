#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 加密/解密工具。
支持密码保护和权限控制。
"""

import json
import sys
import os

COMMAND = "pdf_security"
DESCRIPTION = "PDF 加密/解密工具，支持密码保护和权限控制。"
CATEGORY = "security"
PARAMS = [
    {"name": "action", "type": "str", "required": True, "choices": ["encrypt", "decrypt"], "help": "操作类型：encrypt 或 decrypt"},
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF 路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 路径"},
    {"name": "user_password", "type": "str", "required": False, "help": "用户密码（encrypt 时必填）"},
    {"name": "owner_password", "type": "str", "required": False, "help": "所有者密码（encrypt 时可选，默认同 user_password）"},
    {"name": "password", "type": "str", "required": False, "help": "解密密码（decrypt 时必填）"},
]


def encrypt_pdf(input_path, output_path, user_password, owner_password=None, permissions=None):
    """加密 PDF 文件。"""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # 复制元数据
    if reader.metadata:
        writer.add_metadata(reader.metadata)

    # 加密
    if owner_password is None:
        owner_password = user_password

    writer.encrypt(
        user_password=user_password,
        owner_password=owner_password,
        use_128bit=True
    )

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "action": "encrypt",
        "page_count": len(reader.pages),
        "output": output_path
    }


def decrypt_pdf(input_path, output_path, password):
    """解密 PDF 文件。"""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(input_path)

    if not reader.is_encrypted:
        return {"success": False, "error": "该 PDF 未加密，无需解密"}

    try:
        reader.decrypt(password)
    except Exception as e:
        return {"success": False, "error": f"解密失败，密码可能不正确: {str(e)}"}

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


def handler(params):
    """PDF 加密/解密入口。

    Args:
        params: {
            "action": "encrypt" | "decrypt",
            "input": 输入 PDF 路径,
            "output": 输出 PDF 路径,
            # encrypt 专用
            "user_password": 用户密码,
            "owner_password": 所有者密码（可选）,
            # decrypt 专用
            "password": 解密密码
        }
    """
    action = params.get("action")
    input_path = params.get("input", "")
    output_path = params.get("output", "")

    if not input_path:
        raise ValueError("'input' 参数必填")
    if not output_path:
        raise ValueError("'output' 参数必填")
    if not os.path.exists(input_path):
        raise ValueError(f"文件不存在: {input_path}")

    if action == "encrypt":
        user_password = params.get("user_password")
        if not user_password:
            raise ValueError("encrypt 操作需要 'user_password' 参数")
        owner_password = params.get("owner_password")
        return encrypt_pdf(input_path, output_path, user_password, owner_password)

    elif action == "decrypt":
        password = params.get("password")
        if not password:
            raise ValueError("decrypt 操作需要 'password' 参数")
        return decrypt_pdf(input_path, output_path, password)

    else:
        raise ValueError(f"未知操作: {action}，支持 encrypt 或 decrypt")


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)

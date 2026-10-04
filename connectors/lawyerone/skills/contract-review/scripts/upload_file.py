# -*- coding: utf-8 -*-
"""
法保网文件上传脚本（在用户本地执行，获取公网可访问URL）

用法：
  python upload_file.py --file <本地文件路径> [--token <法保网 API Key>]

鉴权优先级：
  1. --token 参数
  2. 环境变量 FBW_API_KEY（用户执行 setx FBW_API_KEY "<Key>" 一次性配置）
  3. 两者皆无 → 打印配置指引并以退出码 1 结束

输出约定：
  成功：只打印一行公网URL（方便 AI 直接提取使用）
  失败：打印「错误: <原因>」，退出码 1

安全约定：
  API Key 仅从参数或环境变量读取，不硬编码、不落盘、不回显。
"""
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

UPLOAD_URL = "https://openplat.fabao.law/api/upload/file"
ALLOWED_EXT = {".docx", ".doc", ".pdf"}


def main():
    parser = argparse.ArgumentParser(description="法保网文件上传（本地执行，输出公网URL）")
    parser.add_argument("--file", required=True, help="本地文件路径（.docx/.doc/.pdf）")
    parser.add_argument("--token", default=None, help="法保网 API Key（缺省读环境变量 FBW_API_KEY）")
    args = parser.parse_args()

    # ---- 文件校验 ----
    path = args.file.strip().strip('"')  # Windows 拖拽路径常带引号
    if not os.path.isfile(path):
        print(f"错误: 文件不存在: {path}")
        sys.exit(1)
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXT:
        print(f"错误: 不支持的格式 {ext}，仅支持 .docx/.doc/.pdf")
        sys.exit(1)

    # ---- 鉴权（--token > 环境变量）----
    token = (args.token or os.environ.get("FBW_API_KEY") or "").strip()
    if not token:
        print("错误: 未提供 API Key。以下两种方式任选其一：")
        print('  1. 传参: python upload_file.py --file <路径> --token <API Key>')
        print('  2. 配置环境变量后重试: setx FBW_API_KEY "<API Key>"')
        sys.exit(1)

    # ---- 构造 multipart/form-data（纯标准库）----
    boundary = "----fbw" + uuid.uuid4().hex
    filename = os.path.basename(path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        file_bytes = f.read()

    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        file_bytes,
        f"\r\n--{boundary}--\r\n".encode(),
    ])

    req = urllib.request.Request(
        UPLOAD_URL,
        data=body,
        method="POST",
        headers={
            "token": token,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )

    # ---- 上传 ----
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:200]
        print(f"错误: 上传接口返回 HTTP {e.code}: {detail}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 上传失败（检查网络）: {e}")
        sys.exit(1)

    # ---- 解析返回：data.uri（可能被反引号包裹）----
    data = result.get("data") if isinstance(result, dict) else None
    uri = ""
    if isinstance(data, dict):
        uri = str(data.get("uri") or "")
    elif isinstance(data, str):
        uri = data
    uri = uri.strip().strip("`").strip()

    if not uri:
        print(f"错误: 上传接口未返回文件URL，响应: {json.dumps(result, ensure_ascii=False)[:300]}")
        sys.exit(1)
    print(uri)


if __name__ == "__main__":
    main()

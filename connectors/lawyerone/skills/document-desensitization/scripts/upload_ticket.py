# -*- coding: utf-8 -*-
"""
文件脱敏 - 一次性上传凭证执行脚本（ticket 版，免 API Key）

用法：
  python upload_ticket.py --url <create_upload_ticket 工具返回的 upload_url> --file <本地文件路径>

说明：
  - upload_url 由 MCP 工具 create_upload_ticket 发放（5 分钟内有效、一次性）
  - upload_url 可原样传入（脚本会剥掉占位 filename 参数），文件名自动 URL 编码
  - 成功时只输出一行公网URL；失败时输出以「错误:」开头的提示
"""
import argparse
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

ALLOWED_EXT = {".docx", ".doc", ".pdf"}
MAX_BYTES = 20 * 1024 * 1024  # 与服务端 20MB 上限一致
TIMEOUT = 300


def main():
    parser = argparse.ArgumentParser(description="文件脱敏一次性上传凭证执行脚本（ticket 版）")
    parser.add_argument("--url", required=True, help="create_upload_ticket 工具返回的 upload_url（可原样传入）")
    parser.add_argument("--file", required=True, help="待上传的本地文件路径（.docx/.doc/.pdf）")
    args = parser.parse_args()

    file_path = args.file.strip().strip('"')
    upload_url = args.url.strip().strip('"')

    if not os.path.isfile(file_path):
        print(f"错误: 文件不存在或不是文件: {file_path}")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXT:
        print(f"错误: 仅支持 {'/'.join(sorted(ALLOWED_EXT))} 格式，当前: {ext or '(无后缀)'}")
        sys.exit(1)

    size = os.path.getsize(file_path)
    if size == 0:
        print("错误: 文件为空")
        sys.exit(1)
    if size > MAX_BYTES:
        print(f"错误: 文件超过 20MB 上传限制（当前 {size} 字节）")
        sys.exit(1)

    # 剥掉 upload_url 中可能携带的占位 filename 参数，以实际文件名重新拼接（自动URL编码，支持中文/空格）
    base_url = upload_url.split("?")[0]
    filename = os.path.basename(file_path)
    target = f"{base_url}?filename={urllib.parse.quote(filename)}"

    with open(file_path, "rb") as f:
        data = f.read()

    req = urllib.request.Request(target, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace").strip()
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace").strip()
        except Exception:
            body = ""
        print(f"错误: HTTP {e.code}: {body or e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 上传失败: {e}")
        sys.exit(1)

    url = body.strip().strip("`'\"").strip()
    # 服务端失败时返回以「错误:」开头的纯文本提示，原样转出
    if not url or url.startswith("错误"):
        print(url or "错误: 上传失败，服务端未返回内容")
        sys.exit(1)

    print(url)


if __name__ == "__main__":
    main()

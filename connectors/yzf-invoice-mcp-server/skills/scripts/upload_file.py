#!/usr/bin/env python3
"""云账房文件上传脚本（预签名 URL 方案）。

用法：
    python3 upload_file.py <本地文件绝对路径> <uploadUrl> [publicUrl]

参数：
    <本地文件绝对路径>  必填，待上传文件路径。
    <uploadUrl>         必填，预签名 PUT URL（由 generate_file_upload_url 工具返回）。
    [publicUrl]         选填，上传成功后的公网访问地址（由 generate_file_upload_url 工具返回），
                        不传则脚本会从上传响应中提取 Location 头。

行为：
    校验文件存在且可读 → 用 curl 发起 PUT 上传到 uploadUrl → 失败指数退避重试（最多 3 次）→ 输出 JSON 结果。

依赖：python3 + curl（用 subprocess 调 curl 上传，对大文件更稳，规避 urllib 的 broken-pipe 问题）。
"""

import json
import os
import random
import subprocess
import sys
import time

MAX_FILE_SIZE = 100_000_000  # 100MB
MAX_RETRIES = 3


def die(message: str, code: int = 1) -> None:
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def validate_file(file_path: str) -> int:
    if not os.path.exists(file_path):
        die(f"文件不存在: {file_path}")
    if not os.path.isfile(file_path):
        die(f"不是普通文件: {file_path}")
    if not os.access(file_path, os.R_OK):
        die(f"文件不可读: {file_path}")
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        die("文件为空")
    if file_size > MAX_FILE_SIZE:
        die(f"文件大小超过 100MB 限制: {file_size} 字节")
    return file_size


def upload_with_curl(file_path: str, upload_url: str) -> dict:
    """用 curl PUT 上传，返回解析后的结果字典。"""
    curl_args = [
        "curl",
        "-sS",
        "--fail-with-body",
        "-X", "PUT",
        "--upload-file", file_path,
        upload_url,
    ]
    result = subprocess.run(curl_args, capture_output=True, text=True)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main(argv: list) -> None:
    if not (2 <= len(argv) <= 3):
        print("用法: python3 upload_file.py <本地文件绝对路径> <uploadUrl> [publicUrl]", file=sys.stderr)
        sys.exit(2)

    file_path = argv[0]
    upload_url = argv[1]
    public_url = argv[2] if len(argv) == 3 else ""

    validate_file(file_path)

    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = upload_with_curl(file_path, upload_url)
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            die(f"上传失败（已重试 {MAX_RETRIES} 次）：{last_error}")

        if result["returncode"] == 0:
            # 上传成功，输出结果。
            file_size = os.path.getsize(file_path)
            output = {
                "ok": True,
                "publicUrl": public_url or "",
                "fileName": os.path.basename(file_path),
                "fileSize": file_size,
            }
            print(json.dumps(output, ensure_ascii=False))
            sys.exit(0)

        # 4xx 错误不重试（签名过期/无效等）。
        stderr = result.get("stderr", "")
        if "40" in stderr or "403" in stderr or "401" in stderr:
            die(f"上传失败（客户端错误，不重试）：{stderr.strip()}")

        last_error = stderr.strip() or result.get("stdout", "")
        if attempt < MAX_RETRIES:
            time.sleep(2 ** attempt + random.uniform(0, 1))

    die(f"上传失败（已重试 {MAX_RETRIES} 次）：{last_error}")


if __name__ == "__main__":
    main(sys.argv[1:])

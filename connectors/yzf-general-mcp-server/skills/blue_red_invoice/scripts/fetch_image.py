#!/usr/bin/env python3
"""云账房文件下载转存脚本（无 Content-Type 兜底方案）。

用法：
    python3 fetch_image.py <fileUrl>

参数：
    <fileUrl>  必填，云帐房文件服务 URL（如 https://fileserver.yunzhangfang.com/file/server/view?key=...）。

行为：
    用 curl 下载文件 → 按文件头 magic bytes 识别真实类型（不依赖响应头 Content-Type，
    该服务端不返回 Content-Type）→ 转存为本地带扩展名文件 → 输出 JSON。

输出：
    成功：{"ok": true, "path": "/tmp/yzf_img_<hash>.png", "type": "png", "size": 38532}
    失败：{"ok": false, "error": "..."}

依赖：python3 + curl。
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile

# 文件头 magic bytes 识别表：(扩展名, 检查函数)
MAGIC_CHECKS = [
    ("png", lambda b: b[:8] == b"\x89PNG\r\n\x1a\n"),
    ("jpg", lambda b: b[:3] == b"\xff\xd8\xff"),
    ("gif", lambda b: b[:6] in (b"GIF87a", b"GIF89a")),
    ("webp", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
    ("bmp", lambda b: b[:2] == b"BM"),
]


def die(message: str, code: int = 1) -> None:
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    sys.exit(code)


def detect_type(data: bytes) -> str:
    """按文件头判断类型，返回扩展名；无法识别返回空字符串。"""
    for ext, check in MAGIC_CHECKS:
        if check(data):
            return ext
    return ""


def main(argv: list) -> None:
    if len(argv) != 1:
        print("用法: python3 fetch_image.py <fileUrl>", file=sys.stderr)
        sys.exit(2)

    file_url = argv[0]
    if not file_url.startswith("http"):
        die(f"无效 URL: {file_url}")

    # 下载（服务端无 Content-Type，不依赖响应头，只看文件内容）。
    result = subprocess.run(
        ["curl", "-sS", "--max-time", "30", "-o", "-", file_url],
        capture_output=True,
    )
    if result.returncode != 0:
        die(f"下载失败: {result.stderr.strip() or 'curl 错误'}")

    data = result.stdout
    if not data:
        die("下载内容为空")

    ext = detect_type(data)
    if not ext:
        die("文件类型无法识别（非常见图片格式），请直接展示链接")

    # 转存：系统临时目录 + 内容哈希命名，天然去重（同一内容只存一份）。
    digest = hashlib.sha256(data).hexdigest()[:12]
    cache_dir = os.path.join(tempfile.gettempdir(), "yzf_img_cache")
    os.makedirs(cache_dir, exist_ok=True)
    target = os.path.join(cache_dir, f"yzf_img_{digest}.{ext}")
    with open(target, "wb") as f:
        f.write(data)

    print(json.dumps({
        "ok": True,
        "path": target,
        "type": ext,
        "size": len(data),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])

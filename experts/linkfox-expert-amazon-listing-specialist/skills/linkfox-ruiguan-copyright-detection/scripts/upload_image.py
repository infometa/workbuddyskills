#!/usr/bin/env python3
"""
Upload Local Image - LinkFox Skill
Uploads a local image file to LinkFox OSS and returns a publicly accessible URL.

Steps:
  1. Request a presigned PUT URL from the LinkFox OSS gateway
  2. Upload the local file to the presigned URL
  3. Return the public URL (valid for 24 hours)

Usage:
  python upload_image.py /path/to/local/image.png
"""

import json
import os
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

_API_BASE = (os.environ.get("LINKFOX_TOOL_GATEWAY") or "https://tool-gateway.linkfox.com").rstrip("/")
PRESIGN_URL = f"{_API_BASE}/oss/file/presignedPut"

CONTENT_TYPE_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "heic": "image/heic",
}


def get_api_key():
    """
    获取配置在环境变量的API Key。
    如果获取不到，按 SKILL.md 的 **## 解决认证和积分问题** 处理。
    """
    key = os.environ.get("LINKFOX_AGENT_API_KEY") or os.environ.get("LINKFOXAGENT_API_KEY")
    if not key:
        print(
            "API Key 未配置",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def get_presigned_url(content_type: str, file_extension: str) -> str:
    """Request a presigned PUT URL from the OSS gateway."""
    api_key = get_api_key()
    data = json.dumps({
        "contentType": content_type,
        "fileExtension": file_extension,
    }).encode("utf-8")

    req = Request(
        PRESIGN_URL,
        data=data,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "User-Agent": "LinkFox-Skill/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=150) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        print(f"Failed to get presigned URL: HTTP {e.code}: {e.reason}\n{body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Connection failed: {e.reason}", file=sys.stderr)
        sys.exit(1)

    if result.get("errcode") != 200:
        print(f"API error: {result.get('errmsg', 'unknown error')}", file=sys.stderr)
        sys.exit(1)

    return result["url"]


def upload_file(presigned_url: str, file_path: str, content_type: str):
    """Upload the local file to the presigned OSS URL via HTTP PUT."""
    with open(file_path, "rb") as f:
        file_data = f.read()

    req = Request(
        presigned_url,
        data=file_data,
        headers={
            "Content-Type": content_type,
            "x-oss-object-acl": "public-read",
        },
        method="PUT",
    )

    try:
        with urlopen(req, timeout=120) as response:
            if response.status not in (200, 201):
                print(f"Upload failed with status: {response.status}", file=sys.stderr)
                sys.exit(1)
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        print(f"Upload failed: HTTP {e.code}: {e.reason}\n{body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Upload connection failed: {e.reason}", file=sys.stderr)
        sys.exit(1)


def extract_public_url(presigned_url: str) -> str:
    """Extract the base public URL by stripping query parameters."""
    return presigned_url.split("?")[0]


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: upload_image.py <local_image_path>\n"
            "Example: upload_image.py /path/to/product.png",
            file=sys.stderr,
        )
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    extension = os.path.splitext(file_path)[1].lstrip(".").lower()
    content_type = CONTENT_TYPE_MAP.get(extension)
    if not content_type:
        print(
            f"Unsupported image format: .{extension}\n"
            f"Supported formats: {', '.join(CONTENT_TYPE_MAP.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Step 1: Get presigned URL
    presigned_url = get_presigned_url(content_type, extension)

    # Step 2: Upload file
    upload_file(presigned_url, file_path, content_type)

    # Step 3: Output public URL
    public_url = extract_public_url(presigned_url)
    print(json.dumps({"url": public_url}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

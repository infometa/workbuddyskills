#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""腾讯云 COS 直传（用 STS 临时凭证 + curl 执行 PUT）。

背景：WorkRally MCP 的 upload_file 与本机文件系统隔离，读不到本地文件。
本脚本用 get_upload_token 返回的临时凭证做 COS 签名，再用 curl 上传，
最终得到公开 CDN URL，可作 canvas_generate_image 的 input_images。

用法：
    python3 cos_put.py \
        --secret-id  AKIDxxxx \
        --secret-key xxxx= \
        --token      xxxx \
        --bucket     zenvideo-pro-1258344701 \
        --region     ap-beijing \
        --key        animation_aigc/.../xxx.jpg \
        --file       /abs/path/local.jpg \
        --content-type image/jpeg
"""
import argparse
import hashlib
import hmac
import subprocess
import sys
import time
import urllib.parse


def _hmac_sha1(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha1).digest()


def build_auth(secret_id, secret_key, bucket, region, key, method="put"):
    """按 COS 签名 v5 生成 Authorization 头。

    要点：StringToSign 必须是三段 —— "sha1\\n" + KeyTime + "\\n" + sha1(HttpString) + "\\n"
    漏掉 "sha1" 与 KeyTime 段会稳定报 SignatureDoesNotMatch。
    """
    host = f"{bucket}.cos.{region}.myqcloud.com"
    now = int(time.time())
    key_time = f"{now};{now + 3600}"

    sign_key = _hmac_sha1(secret_key.encode("utf-8"), key_time).hex()

    path = "/" + key
    header_list = "host"
    http_headers = f"host={urllib.parse.quote(host, safe='')}"

    http_string = f"{method}\n{path}\n\n{http_headers}\n"
    string_to_sign = (
        "sha1\n" + key_time + "\n"
        + hashlib.sha1(http_string.encode("utf-8")).hexdigest() + "\n"
    )
    sig = _hmac_sha1(sign_key.encode("utf-8"), string_to_sign).hex()

    auth = (
        f"q-sign-algorithm=sha1&q-ak={secret_id}&q-sign-time={key_time}"
        f"&q-key-time={key_time}&q-header-list={header_list}"
        f"&q-url-param-list=&q-signature={sig}"
    )
    return host, path, auth


def cos_put(secret_id, secret_key, token, bucket, region, key, local, content_type):
    host, path, auth = build_auth(secret_id, secret_key, bucket, region, key)
    url = f"https://{host}{path}"
    cmd = [
        "curl", "-sS", "-X", "PUT", url,
        "-H", f"Authorization: {auth}",
        "-H", f"x-cos-security-token: {token}",
        "-H", f"Content-Type: {content_type}",
        "-H", f"Host: {host}",
        "--data-binary", f"@{local}",
        "--max-time", "180",
        "-w", "\n__HTTP__%{http_code}",
    ]
    # 用 curl 而非 urllib：沙箱下 python 直发 PUT 常 write timeout
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secret-id", required=True)
    ap.add_argument("--secret-key", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--content-type", default="application/octet-stream")
    a = ap.parse_args()

    rc, out = cos_put(
        a.secret_id, a.secret_key, a.token, a.bucket, a.region,
        a.key, a.file, a.content_type,
    )
    print(out)
    if "__HTTP__200" not in out:
        print(f"❌ 上传失败（rc={rc}）", file=sys.stderr)
        return 1
    print(f"✅ 上传成功\nURL: https://{a.bucket}.cos.{a.region}.myqcloud.com/{a.key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

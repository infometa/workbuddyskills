#!/usr/bin/env python3
"""
腾讯云通用文字识别（高精度版）(GeneralAccurateOCR) 调用脚本

支持对图片中的文字进行高精度识别，返回识别到的文字内容。
需要环境变量: TENCENTCLOUD_SECRET_ID, TENCENTCLOUD_SECRET_KEY

用法:
    python main.py --image-url <url>
    python main.py --image-base64 <base64_or_filepath>
"""

import argparse
import base64
import json
import os
import sys

# SDK 最大图片限制 (10MB)
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024


def validate_env() -> tuple:
    """校验并返回腾讯云API密钥。"""
    secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")
    if not secret_id or not secret_key:
        print("错误: 请设置环境变量 TENCENTCLOUD_SECRET_ID 和 TENCENTCLOUD_SECRET_KEY", file=sys.stderr)
        sys.exit(1)
    return secret_id, secret_key


def load_image_base64(value: str) -> str:
    """
    加载 Base64 图片内容。
    如果 value 是一个存在的文件路径，则读取文件内容作为 Base64；
    否则直接视为 Base64 字符串。
    """
    if os.path.isfile(value):
        with open(value, "rb") as f:
            raw = f.read()
        # 如果文件内容本身就是Base64文本(如txt文件)，直接使用
        try:
            raw_str = raw.decode("utf-8").strip()
            base64.b64decode(raw_str, validate=True)
            return raw_str
        except (UnicodeDecodeError, ValueError):
            pass
        # 否则将二进制文件编码为Base64
        if len(raw) > MAX_IMAGE_SIZE_BYTES:
            print(f"错误: 图片文件大小超过 {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB 限制", file=sys.stderr)
            sys.exit(1)
        return base64.b64encode(raw).decode("utf-8")
    else:
        # 直接作为 Base64 字符串使用
        try:
            decoded = base64.b64decode(value, validate=True)
            if len(decoded) > MAX_IMAGE_SIZE_BYTES:
                print(f"错误: 图片大小超过 {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB 限制", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print("错误: 提供的 ImageBase64 不是合法的 Base64 编码，也不是有效的文件路径", file=sys.stderr)
            sys.exit(1)
        return value


def format_response(resp) -> dict:
    """格式化 SDK 响应对象，提取识别文本。

    Args:
        resp: GeneralAccurateOCRResponse object from SDK.
    """
    text_detections = resp.TextDetections or []

    if not text_detections:
        return {
            "raw_text": "",
            "message": "No text detected in the image.",
            "RequestId": resp.RequestId or "",
        }

    raw_text = "\n".join(item.DetectedText or "" for item in text_detections)
    return {
        "raw_text": raw_text,
        "RequestId": resp.RequestId or "",
    }


def call_general_accurate_ocr(args: argparse.Namespace) -> None:
    """调用腾讯云 GeneralAccurateOCR 接口。"""
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
            TencentCloudSDKException,
        )
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.ocr.v20181119 import models, ocr_client
    except ImportError:
        print("错误: 缺少依赖 tencentcloud-sdk-python，请执行: pip install tencentcloud-sdk-python", file=sys.stderr)
        sys.exit(1)

    secret_id, secret_key = validate_env()

    # 构建客户端
    cred = credential.Credential(secret_id, secret_key)
    http_profile = HttpProfile()
    http_profile.endpoint = "ocr.tencentcloudapi.com"
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    client_profile.request_client = args.user_agent
    region = args.region if args.region else "ap-guangzhou"
    client = ocr_client.OcrClient(cred, region, client_profile)

    # 构建请求
    req = models.GeneralAccurateOCRRequest()

    if args.image_url:
        req.ImageUrl = args.image_url
    elif args.image_base64:
        req.ImageBase64 = load_image_base64(args.image_base64)
    else:
        print("错误: 必须提供 --image-url 或 --image-base64 之一", file=sys.stderr)
        sys.exit(1)

    if args.is_pdf is not None:
        req.IsPdf = args.is_pdf

    if args.pdf_page_number is not None:
        req.PdfPageNumber = args.pdf_page_number

    if args.is_words is not None:
        req.IsWords = args.is_words

    # 发起请求（使用 SDK 高层接口，类型安全、自动反序列化）
    try:
        resp = client.GeneralAccurateOCR(req)
    except TencentCloudSDKException as e:
        print(f"API调用失败 [{e.code}]: {e.message}", file=sys.stderr)
        if e.requestId:
            print(f"RequestId: {e.requestId}", file=sys.stderr)
        sys.exit(1)

    # 格式化输出
    result = format_response(resp)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="腾讯云通用文字识别（高精度版）(GeneralAccurateOCR) 调用工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础调用（--user-agent 默认为 Skills，可不传）
  python main.py --image-url "https://example.com/document.jpg"

  # 使用 Base64 文件调用
  python main.py --image-base64 ./document.jpg

  # 识别 PDF 文件中的文字
  python main.py --image-url "https://example.com/doc.pdf" --is-pdf true --pdf-page-number 1

  # 返回单字信息
  python main.py --image-url "https://example.com/document.jpg" --is-words true
        """,
    )

    # 图片输入（二选一）
    img_group = parser.add_mutually_exclusive_group(required=True)
    img_group.add_argument(
        "--image-url",
        type=str,
        help="图片URL地址，支持 HTTP/HTTPS，图片大小不超过10MB",
    )
    img_group.add_argument(
        "--image-base64",
        type=str,
        help="图片Base64字符串，或图片/Base64文本文件的路径",
    )

    # 可选参数
    parser.add_argument(
        "--is-pdf",
        type=lambda x: x.lower() in ("true", "1", "yes"),
        default=None,
        help="是否开启PDF识别，开启后可同时支持图片和PDF的识别 (默认false)",
    )
    parser.add_argument(
        "--pdf-page-number",
        type=int,
        default=None,
        help="需要识别的PDF页面的对应页码，仅支持PDF单页识别，当上传文件为PDF且IsPdf参数值为true时有效，默认值为1",
    )
    parser.add_argument(
        "--is-words",
        type=lambda x: x.lower() in ("true", "1", "yes"),
        default=None,
        help="是否返回单字信息，默认关闭",
    )
    parser.add_argument(
        "--region",
        type=str,
        default=None,
        help="腾讯云地域，默认 ap-guangzhou",
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default="Skills",
        help="客户端标识，用于统计调用来源，统一固定为 Skills",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    call_general_accurate_ocr(args)


if __name__ == "__main__":
    main()

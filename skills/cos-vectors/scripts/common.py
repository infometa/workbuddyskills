#!/usr/bin/env python3
"""
公共基础模块 — 所有向量桶脚本复用的客户端初始化和错误处理逻辑。
"""

import argparse
import json
import os
import sys


def base_parser(description):
    """创建基础参数解析器，包含凭证和连接参数"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--secret-id",
        default=os.getenv("COS_VECTORS_SECRET_ID"),
        help="腾讯云 API 密钥 ID（或设置环境变量 COS_VECTORS_SECRET_ID）",
    )
    parser.add_argument(
        "--secret-key",
        default=os.getenv("COS_VECTORS_SECRET_KEY"),
        help="腾讯云 API 密钥 Key（或设置环境变量 COS_VECTORS_SECRET_KEY）",
    )
    parser.add_argument(
        "--region",
        required=True,
        help="存储桶区域，如 ap-guangzhou",
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="向量桶名称，格式为 BucketName-APPID，如 examplebucket-1250000000",
    )
    parser.add_argument(
        "--scheme",
        default="http",
        choices=["http", "https"],
        help="协议，默认 http",
    )
    return parser


def create_client(args):
    """根据解析后的参数创建 CosVectorsClient"""
    # 校验必需参数
    if not args.secret_id:
        fail("缺少 SecretId，请通过 --secret-id 参数或 COS_VECTORS_SECRET_ID 环境变量提供")

    if not args.secret_key:
        fail("缺少 SecretKey，请通过 --secret-key 参数或 COS_VECTORS_SECRET_KEY 环境变量提供")

    try:
        from qcloud_cos import CosConfig, CosVectorsClient
    except ImportError:
        fail("cos-python-sdk-v5 未安装，请运行: pip3 install cos-python-sdk-v5 --upgrade")

    endpoint = f"vectors.{args.region}.coslake.com"

    config = CosConfig(
        Region=args.region,
        SecretId=args.secret_id,
        SecretKey=args.secret_key,
        Scheme=args.scheme,
        Endpoint=endpoint,
        Token=None,
    )
    return CosVectorsClient(config)


def success_output(data):
    """输出成功结果的 JSON"""
    result = {"success": True}
    result.update(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def fail(message):
    """输出失败结果并退出"""
    print(json.dumps({"success": False, "error": message}, ensure_ascii=False, indent=2))
    sys.exit(1)


def handle_error(e):
    """统一处理 COS 异常"""
    from qcloud_cos.cos_exception import CosServiceError, CosClientError

    if isinstance(e, CosServiceError):
        error_info = {"success": False, "error": f"服务端错误: {e}"}
        try:
            error_info["error_code"] = e.get_error_code()
        except Exception:
            error_info["error_code"] = "Unknown"
        try:
            error_info["error_msg"] = e.get_error_msg()
        except Exception:
            error_info["error_msg"] = str(e)
        try:
            error_info["request_id"] = e.get_request_id()
        except Exception:
            error_info["request_id"] = "Unknown"
        print(json.dumps(error_info, ensure_ascii=False, indent=2))
    elif isinstance(e, CosClientError):
        print(json.dumps({"success": False, "error": f"客户端错误: {e}"}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"success": False, "error": f"未知错误: {e}"}, ensure_ascii=False, indent=2))
    sys.exit(1)


def run(func):
    """运行主函数并捕获异常"""
    try:
        func()
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)

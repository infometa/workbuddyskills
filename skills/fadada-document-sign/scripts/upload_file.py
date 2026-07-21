#!/usr/bin/env python3
"""上传合同文件到法大大平台。

调用接口:
1. /file/get-upload-url - 获取上传URL和法大大文件URL
2. PUT 上传到OSS
3. /file/process - 处理文件获取fileId

作用: 将本地文件上传到法大大平台，获取 fileId 用于创建签署任务

使用方式:
  python upload_file.py --file-path "/path/to/contract.pdf" --file-name "合同.pdf"

参数说明:
  --file-path (必填): 文件路径
  --file-name (必填): 文件名
  --file-format (可选): 文件格式，默认 pdf
  --debug (可选): 开启调试日志
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from utils import (
    FASCClient,
    FileError,
    load_config,
    print_result,
    success_response,
    error_response,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def validate_file(file_path: str) -> Path:
    """验证文件是否存在且格式正确。"""
    path = Path(file_path)

    if not path.exists():
        raise FileError(f"文件不存在: {file_path}")

    if not path.is_file():
        raise FileError(f"路径不是文件: {file_path}")

    # 检查文件大小（最大50MB）
    file_size = path.stat().st_size
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_size:
        raise FileError(f"文件大小超过限制(50MB): {path.stat().st_size / 1024 / 1024:.2f}MB")

    # 检查文件格式
    suffix = path.suffix.lower()
    if suffix not in ['.pdf', '.ofd']:
        raise FileError(f"文件格式不支持: {suffix}，仅支持 PDF 和 OFD 格式")

    return path


def get_upload_url_and_fdd(client: FASCClient, file_type: str = "doc") -> dict:
    """获取文件上传URL和法大大文件URL。

    根据官方API文档实现，返回 uploadUrl 和 fddFileUrl
    """
    biz_content = {"fileType": file_type}

    logger.info(f"获取上传URL, fileType={file_type}")

    result = client.request("/file/get-upload-url", biz_content)

    logger.info(f"上传URL响应: {json.dumps(result, ensure_ascii=False)}")

    return result


def upload_file_to_oss(upload_url: str, file_path: Path) -> bool:
    """上传文件到OSS（使用PUT方法）。

    Args:
        upload_url: OSS上传URL
        file_path: 本地文件路径

    Returns:
        是否上传成功
    """
    import requests

    with open(file_path, 'rb') as f:
        response = requests.put(upload_url, data=f, timeout=60)

    if response.status_code != 200:
        logger.error(f"上传失败: HTTP {response.status_code}")
        return False

    logger.info(f"文件上传成功")
    return True


def process_file_by_fdd_url(client: FASCClient, fdd_file_url: str, file_name: str, file_format: str = "pdf") -> dict:
    """通过法大大文件URL处理文件，获取fileId。

    Args:
        client: FASC客户端
        fdd_file_url: 法大大文件URL
        file_name: 文件名
        file_format: 文件格式 (pdf/ofd)

    Returns:
        包含 fileId 等信息
    """
    biz_content = {
        "fddFileUrlList": [{
            "fileType": "doc",  # 使用 doc 类型
            "fddFileUrl": fdd_file_url,
            "fileName": file_name,
            "fileFormat": file_format.lower()
        }]
    }

    logger.info(f"处理文件: fddFileUrl={fdd_file_url}")

    result = client.request("/file/process", biz_content)

    logger.info(f"文件处理响应: {json.dumps(result, ensure_ascii=False)}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="上传合同文件到法大大平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file-path", required=True, help="文件路径")
    parser.add_argument("--file-name", required=True, help="文件名")
    parser.add_argument("--file-format", default="pdf", help="文件格式 (pdf/ofd)，默认 pdf")
    parser.add_argument("--debug", action="store_true", help="开启调试日志")

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        # 1. 验证文件
        logger.info(f"验证文件: {args.file_path}")
        file_path = validate_file(args.file_path)
        file_size = file_path.stat().st_size
        logger.info(f"文件验证通过: size={file_size} bytes")

        # 2. 加载配置并创建客户端
        config = load_config()
        client = FASCClient(config)

        # 3. 获取上传URL和fddFileUrl
        upload_info = get_upload_url_and_fdd(client, "doc")

        upload_url = upload_info.get("uploadUrl")
        fdd_file_url = upload_info.get("fddFileUrl")

        if not upload_url or not fdd_file_url:
            print_result(error_response("获取上传URL失败"))
            return

        logger.info(f"获取到 uploadUrl 和 fddFileUrl")

        # 4. 上传文件到OSS（PUT方法）
        logger.info(f"上传文件到OSS...")
        if not upload_file_to_oss(upload_url, file_path):
            print_result(error_response("文件上传失败"))
            return

        # 5. 处理文件获取fileId
        logger.info("处理文件...")
        process_result = process_file_by_fdd_url(
            client,
            fdd_file_url,
            args.file_name,
            args.file_format
        )

        # 从响应中提取 fileId
        file_id_list = process_result.get("fileIdList", [])
        if file_id_list:
            file_id = file_id_list[0].get("fileId")
        else:
            file_id = process_result.get("fileId")

        if not file_id:
            print_result(error_response("获取文件ID失败"))
            return

        # 6. 返回成功结果
        result = success_response({
            "fileId": file_id,
            "fileName": args.file_name,
            "fileSize": file_size,
            "fileFormat": args.file_format,
            "fddFileUrl": fdd_file_url,
        })
        print_result(result)

    except FileError as e:
        logger.error(f"文件错误: {e}")
        print_result(error_response(str(e)))
    except Exception as e:
        logger.error(f"上传失败: {e}")
        print_result(error_response(f"上传文件失败: {e}"))


if __name__ == "__main__":
    main()

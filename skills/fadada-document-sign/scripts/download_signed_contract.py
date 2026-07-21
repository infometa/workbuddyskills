#!/usr/bin/env python3
"""下载已签署合同。

调用接口: /sign-task/owner/get-download-url

作用: 获取已签署合同的下载链接，支持下载签署后的完整合同包

使用方式:
  python download_signed_contract.py --task-id "xxx"
  python download_signed_contract.py --task-id "xxx" --save-path "./signed_contract.pdf"

参数说明:
  --task-id (必填): 签署任务ID
  --save-path (可选): 本地保存路径，指定后自动下载保存
  --debug (可选): 开启调试日志

输出:
  {
    "success": true,
    "data": {
      "taskId": "xxx",
      "taskName": "劳动合同签署",
      "taskStatus": "finished",
      "taskStatusName": "已完成",
      "downloadUrl": "https://...",
      "expiresIn": 3600,
      "fileList": [
        {
          "fileId": "xxx",
          "fileName": "劳动合同.pdf",
          "signTime": "2024-01-01 11:00:00"
        }
      ]
    }
  }

前置条件:
  - 任务状态必须为「已完成」(finished)
  - 至少有一方已完成签署

适用场景:
  - 签署完成后下载已签署的合同文件
  - 归档保存签署完成的合同
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import requests
from utils import (
    FASCClient,
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

# API 端点
API_ENDPOINT = "/sign-task/owner/get-download-url"

# 状态映射
STATUS_MAP = {
    "draft": "草稿",
    "waiting": "待提交",
    "signing": "签署中",
    "finished": "已完成",
    "cancelled": "已撤销",
    "abolished": "已作废",
    "expired": "已过期",
}


def get_download_url(
    client: FASCClient,
    task_id: str,
    owner_type: str = "corp",
) -> dict:
    """获取签署任务下载链接。

    Args:
        client: FASC 客户端
        task_id: 任务ID
        owner_type: 主体类型，corp=企业，person=个人

    Returns:
        下载链接响应
    """
    # 构建 ownerId
    owner_id = {
        "idType": owner_type,
    }
    if owner_type == "corp":
        owner_id["openId"] = client.open_corp_id
    else:
        owner_id["openId"] = os.environ.get("FADADA_OPEN_ID", "")

    biz_content = {
        "ownerId": owner_id,
        "signTaskId": task_id,
    }

    logger.info(f"获取签署合同下载链接: signTaskId={task_id}, ownerType={owner_type}")

    result = client.request(API_ENDPOINT, biz_content)

    logger.info(f"下载链接响应: {json.dumps(result, ensure_ascii=False)}")

    return result


def download_file(url: str, save_path: str) -> bool:
    """下载文件到本地。

    Args:
        url: 下载链接
        save_path: 保存路径

    Returns:
        是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

        logger.info(f"开始下载文件: {url}")
        response = requests.get(url, stream=True, timeout=60)

        if response.status_code != 200:
            logger.error(f"下载失败，HTTP状态码: {response.status_code}")
            return False

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"文件已保存: {save_path}")
        return True

    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return False


def parse_download_result(data: dict) -> dict:
    """解析下载结果。

    Args:
        data: API返回的数据

    Returns:
        标准化的下载结果
    """
    task_status = data.get("taskStatus", "")

    # 解析文件列表
    raw_files = data.get("fileList", [])
    file_list = []
    for f in raw_files:
        if isinstance(f, dict):
            file_list.append({
                "fileId": f.get("fileId", ""),
                "fileName": f.get("fileName", ""),
                "signTime": f.get("signTime", ""),
            })

    return {
        "taskId": data.get("taskId", ""),
        "taskName": data.get("taskName", ""),
        "taskStatus": task_status,
        "taskStatusName": STATUS_MAP.get(task_status.lower(), task_status),
        "downloadUrl": data.get("downloadUrl", ""),
        "expiresIn": data.get("expiresIn", 0),
        "fileList": file_list,
    }


def format_output(
    api_result: dict,
    task_id: str,
    save_path: Optional[str] = None,
    download_success: bool = False,
) -> dict:
    """格式化输出结果。

    Args:
        api_result: API原始响应
        task_id: 任务ID
        save_path: 保存路径
        download_success: 下载是否成功

    Returns:
        格式化后的结果
    """
    result_data = parse_download_result(api_result)

    # 如果下载成功，添加本地路径
    if download_success and save_path:
        result_data["localPath"] = os.path.abspath(save_path)

    return {
        "success": True,
        "message": "合同下载成功" if download_success else "获取下载链接成功",
        "data": result_data,
    }


def main():
    parser = argparse.ArgumentParser(
        description="下载已签署合同",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task-id", required=True, help="签署任务ID")
    parser.add_argument("--save-path", default="", help="本地保存路径")
    parser.add_argument("--owner-type", default="corp", choices=["corp", "person"], help="主体类型：corp=企业，person=个人")
    parser.add_argument("--debug", action="store_true", help="开启调试日志")

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        # 验证参数
        if not args.task_id:
            print_result(error_response("task-id 参数不能为空"))
            return

        # 加载配置并创建客户端
        config = load_config()
        client = FASCClient(config)

        # 先查询任务状态，确认是否已完成
        from query_sign_status import get_task_detail

        task_detail = get_task_detail(client, args.task_id)
        task_status = task_detail.get("taskStatus", "").lower()

        if task_status and task_status not in ["finished", "task_finished", "sign_completed"]:
            status_name = STATUS_MAP.get(task_status, task_status)
            print_result(error_response(
                f"该任务当前状态为「{status_name}」，无法下载",
                details={
                    "taskId": args.task_id,
                    "taskStatus": task_status,
                    "taskStatusName": status_name,
                    "hint": "只有已完成签署的任务才能下载合同"
                }
            ))
            return

        # 获取下载链接
        api_result = get_download_url(client, args.task_id, args.owner_type)

        download_url = api_result.get("downloadUrl", "")

        # 如果指定了保存路径，下载文件
        download_success = False
        if args.save_path and download_url:
            download_success = download_file(download_url, args.save_path)
            if not download_success:
                print_result(error_response(
                    "文件下载失败，请检查网络连接后重试",
                    details={"downloadUrl": download_url}
                ))
                return

        # 格式化输出
        result = format_output(
            api_result,
            args.task_id,
            args.save_path or None,
            download_success,
        )
        print_result(result)

    except Exception as e:
        logger.error(f"下载签署合同失败: {e}")
        print_result(error_response(f"下载签署合同失败: {e}"))


if __name__ == "__main__":
    main()

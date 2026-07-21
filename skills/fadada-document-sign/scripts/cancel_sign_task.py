#!/usr/bin/env python3
"""撤回签署任务。

调用接口: /sign-task/cancel

作用: 撤回尚未完成的签署任务（仅支持撤回签署中、待提交状态的任务）

使用方式:
  python cancel_sign_task.py --task-id "xxx"
  python cancel_sign_task.py --task-id "xxx" --reason "合同内容有误"

参数说明:
  --task-id (必填): 签署任务ID
  --reason (可选): 撤回原因
  --debug (可选): 开启调试日志

输出:
  {
    "success": true,
    "data": {
      "taskId": "xxx",
      "taskStatus": "cancelled",
      "taskStatusName": "已撤销",
      "cancelTime": "2024-01-01 12:00:00"
    }
  }

可撤回状态:
  - waiting: 待提交
  - signing: 签署中

不可撤回状态:
  - finished: 已完成（需作废处理）
  - cancelled: 已撤销
  - abolished: 已作废
  - expired: 已过期
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, Optional

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
API_ENDPOINT = "/sign-task/cancel"

# 可撤回状态
CANCELLABLE_STATUS = ["waiting", "signing", "draft"]

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


def cancel_sign_task(
    client: FASCClient,
    task_id: str,
    reason: Optional[str] = None,
) -> dict:
    """撤回签署任务。

    Args:
        client: FASC 客户端
        task_id: 任务ID
        reason: 撤回原因

    Returns:
        撤回结果
    """
    biz_content = {
        "signTaskId": task_id,
    }

    if reason:
        biz_content["cancelReason"] = reason

    logger.info(f"撤回签署任务: taskId={task_id}, reason={reason}")

    result = client.request(API_ENDPOINT, biz_content)

    logger.info(f"撤回结果: {json.dumps(result, ensure_ascii=False)}")

    return result


def parse_cancel_result(data: dict) -> dict:
    """解析撤回结果。

    Args:
        data: API返回的数据

    Returns:
        标准化的撤回结果
    """
    task_status = data.get("taskStatus", "")
    return {
        "taskId": data.get("taskId", ""),
        "taskName": data.get("taskName", ""),
        "taskStatus": task_status,
        "taskStatusName": STATUS_MAP.get(task_status.lower(), task_status),
        "cancelTime": data.get("cancelTime", ""),
    }


def format_output(api_result: dict, task_id: str, reason: Optional[str] = None) -> dict:
    """格式化输出结果。

    Args:
        api_result: API原始响应
        task_id: 任务ID
        reason: 撤回原因

    Returns:
        格式化后的结果
    """
    result_data = parse_cancel_result(api_result)

    message = f"签署任务已撤销"
    if reason:
        message += f"，原因：{reason}"

    return {
        "success": True,
        "message": message,
        "data": result_data,
    }


def main():
    parser = argparse.ArgumentParser(
        description="撤回签署任务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task-id", required=True, help="签署任务ID")
    parser.add_argument("--reason", default="", help="撤回原因")
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

        # 先查询任务状态，确认是否可以撤回
        from query_sign_status import get_task_detail

        task_detail = get_task_detail(client, args.task_id)
        task_status = task_detail.get("taskStatus", "").lower()

        if task_status and task_status not in CANCELLABLE_STATUS:
            status_name = STATUS_MAP.get(task_status, task_status)
            print_result(error_response(
                f"该任务当前状态为「{status_name}」，无法撤回",
                details={
                    "taskId": args.task_id,
                    "taskStatus": task_status,
                    "taskStatusName": status_name,
                    "hint": "已完成的任务需要通过作废接口处理"
                }
            ))
            return

        # 执行撤回
        api_result = cancel_sign_task(
            client,
            args.task_id,
            reason=args.reason or None,
        )

        # 格式化输出
        result = format_output(api_result, args.task_id, args.reason or None)
        print_result(result)

    except Exception as e:
        logger.error(f"撤回签署任务失败: {e}")
        print_result(error_response(f"撤回签署任务失败: {e}"))


if __name__ == "__main__":
    main()

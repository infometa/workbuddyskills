#!/usr/bin/env python3
"""查询已有签署流程列表。

调用接口: /sign-task/owner/get-list

作用: 查询当前账号下的签署任务列表，支持分页和状态筛选

使用方式:
  python list_sign_tasks.py --status signing
  python list_sign_tasks.py --page 1 --page-size 20
  python list_sign_tasks.py --keyword "劳动合同"

参数说明:
  --status (可选): 签署任务状态筛选
      - draft: 草稿
      - waiting: 待提交
      - signing: 签署中
      - finished: 已完成
      - cancelled: 已撤销
      - abolished: 已作废
      - expired: 已过期
  --keyword (可选): 搜索关键词（任务名称）
  --page (可选): 页码，默认1
  --page-size (可选): 每页条数，默认10，最大50
  --debug (可选): 开启调试日志

输出:
  {
    "success": true,
    "data": {
      "total": 100,
      "page": 1,
      "pageSize": 10,
      "list": [
        {
          "taskId": "xxx",
          "taskName": "劳动合同签署",
          "taskStatus": "signing",
          "taskStatusName": "签署中",
          "createTime": "2024-01-01 10:00:00",
          "actorCount": 2,
          "signedCount": 1
        }
      ]
    }
  }
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

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
API_ENDPOINT = "/sign-task/owner/get-list"

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

# 新版状态映射
NEW_STATUS_MAP = {
    "task_created": "任务创建中",
    "finish_creation": "已创建（审批中）",
    "fill_progress": "填写进行中",
    "fill_completed": "填写已完成",
    "sign_progress": "签署进行中",
    "sign_completed": "签署已完成",
    "task_finished": "任务已结束",
    "task_terminated": "任务异常停止",
    "expired": "已逾期",
    "abolishing": "作废中",
    "revoked": "已作废",
}


def query_sign_tasks(
    client: FASCClient,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    owner_type: str = "corp",
) -> dict:
    """查询签署任务列表。

    Args:
        client: FASC 客户端
        status: 任务状态筛选
        keyword: 搜索关键词
        page: 页码
        page_size: 每页条数
        owner_type: 主体类型，corp=企业，person=个人

    Returns:
        任务列表响应
    """
    # 构建 ownerId
    owner_id = {
        "idType": owner_type,
    }
    if owner_type == "corp":
        owner_id["openId"] = client.open_corp_id
    else:
        # 个人用户需要从环境变量或配置获取 openId
        owner_id["openId"] = os.environ.get("FADADA_OPEN_ID", "")

    biz_content = {
        "ownerId": owner_id,
        "listPageNo": page,
        "listPageSize": min(page_size, 100),  # 最大100条
    }

    # 构建筛选条件
    if status or keyword:
        biz_content["listFilter"] = {}
        if status:
            biz_content["listFilter"]["signTaskStatus"] = [status]
        if keyword:
            biz_content["listFilter"]["signTaskSubject"] = keyword

    logger.info(f"查询签署任务列表: {json.dumps(biz_content, ensure_ascii=False)}")

    result = client.request(API_ENDPOINT, biz_content)

    logger.info(f"查询结果: {json.dumps(result, ensure_ascii=False)}")

    return result


def parse_task_item(item: dict) -> dict:
    """解析单个任务项。

    Args:
        item: API返回的任务数据

    Returns:
        标准化的任务信息
    """
    task_status = item.get("signTaskStatus", "")
    status_name = NEW_STATUS_MAP.get(task_status, task_status)

    # 处理时间戳转换
    create_time = item.get("createTime", "")
    if create_time and isinstance(create_time, (int, float)):
        import datetime
        create_time = datetime.datetime.fromtimestamp(create_time / 1000).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "taskId": item.get("signTaskId", ""),
        "taskName": item.get("signTaskSubject", ""),
        "taskStatus": task_status,
        "taskStatusName": status_name,
        "createTime": create_time,
        "initiatorName": item.get("initiatorName", ""),
        "approvalStatus": item.get("approvalStatus", ""),
    }


def parse_task_list(data: dict) -> dict:
    """解析任务列表数据。

    Args:
        data: API返回的数据

    Returns:
        标准化的任务列表
    """
    raw_list = data.get("signTasks", [])
    if isinstance(raw_list, list):
        tasks = [parse_task_item(item) for item in raw_list if isinstance(item, dict)]
    else:
        tasks = []

    return {
        "total": data.get("totalCount", 0),
        "page": data.get("listPageNo", 1),
        "pageSize": data.get("countInPage", 0),
        "totalPages": data.get("listPageCount", 0),
        "list": tasks,
    }


def format_output(api_result: dict) -> dict:
    """格式化输出结果。

    Args:
        api_result: API原始响应

    Returns:
        格式化后的结果
    """
    task_list = parse_task_list(api_result)

    return {
        "success": True,
        "data": task_list,
    }


def main():
    parser = argparse.ArgumentParser(
        description="查询已有签署流程列表",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", default="", help="签署任务状态筛选")
    parser.add_argument("--keyword", default="", help="搜索关键词")
    parser.add_argument("--page", type=int, default=1, help="页码，默认1")
    parser.add_argument("--page-size", type=int, default=10, help="每页条数，默认10")
    parser.add_argument("--owner-type", default="corp", choices=["corp", "person"], help="主体类型：corp=企业，person=个人")
    parser.add_argument("--debug", action="store_true", help="开启调试日志")

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        # 加载配置并创建客户端
        config = load_config()
        client = FASCClient(config)

        # 查询任务列表
        api_result = query_sign_tasks(
            client,
            status=args.status or None,
            keyword=args.keyword or None,
            page=args.page,
            page_size=args.page_size,
            owner_type=args.owner_type,
        )

        # 格式化输出
        result = format_output(api_result)
        print_result(result)

    except Exception as e:
        logger.error(f"查询签署任务列表失败: {e}")
        print_result(error_response(f"查询签署任务列表失败: {e}"))


if __name__ == "__main__":
    main()

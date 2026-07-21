#!/usr/bin/env python3
"""查询签署任务状态。

调用接口: /sign-task/app/get-detail

作用: 根据任务ID查询签署任务的详细信息和状态

使用方式:
  python query_sign_status.py --task-id "xxx"

参数说明:
  --task-id (必填): 签署任务ID
  --debug (可选): 开启调试日志

输出:
  {
    "success": true,
    "data": {
      "taskId": "xxx",
      "taskName": "劳动合同签署",
      "taskStatus": "signing",
      "taskStatusName": "签署中",
      "createTime": "2024-01-01 10:00:00",
      "actors": [
        {
          "actorName": "张三",
          "actorType": "person",
          "actorStatus": "signed",
          "signTime": "2024-01-01 11:00:00"
        }
      ],
      "files": [
        {
          "fileId": "xxx",
          "fileName": "劳动合同.pdf"
        }
      ]
    }
  }

签署任务状态:
  - draft: 草稿
  - waiting: 待提交
  - signing: 签署中
  - finished: 已完成
  - cancelled: 已撤销
  - abolished: 已作废
  - expired: 已过期
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict

from utils import (
    FASCClient,
    load_config,
    load_skill_context,
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
API_ENDPOINT = "/sign-task/app/get-detail"

# 状态映射
STATUS_MAP = {
    "draft": "草稿",
    "waiting": "待提交",
    "sign_progress": "签署中",
    "signing": "签署中",
    "finished": "已完成",
    "cancelled": "已撤销",
    "abolished": "已作废",
    "expired": "已过期",
    "task_finished": "已完成",
    "task_finish": "已完成",
}

# 签署方状态映射
ACTOR_STATUS_MAP = {
    "joined": "已加入",
    "waiting": "待签署",
    "signing": "签署中",
    "signed": "已签署",
    "refused": "已拒绝",
    "expired": "已过期",
    "wait_sign": "待签署",
    "signed_finish": "已完成签署",
}


def get_task_detail(
    client: FASCClient,
    task_id: str
) -> dict:
    """查询签署任务详情。
    
    Args:
        client: FASC 客户端
        task_id: 任务ID
        
    Returns:
        任务详情响应
    """
    biz_content = {
        "signTaskId": task_id,
    }
    
    logger.info(f"查询签署任务详情: taskId={task_id}")
    
    result = client.request(API_ENDPOINT, biz_content)
    
    logger.info(f"任务详情响应: {json.dumps(result, ensure_ascii=False)}")
    
    return result


def parse_task_status(status: str) -> str:
    """解析任务状态名称。
    
    Args:
        status: 状态代码
        
    Returns:
        状态中文名称
    """
    return STATUS_MAP.get(status.lower(), status)


def parse_actor_status(status: str) -> str:
    """解析签署方状态名称。
    
    Args:
        status: 状态代码
        
    Returns:
        状态中文名称
    """
    return ACTOR_STATUS_MAP.get(status.lower(), status)


def parse_actor(actor: dict) -> dict:
    """解析签署参与方信息。
    
    Args:
        actor: API返回的参与方数据（包含 actorInfo 嵌套）
        
    Returns:
        标准化的参与方信息
    """
    # 处理 actorInfo 嵌套结构
    actor_info = actor.get("actorInfo", {})
    return {
        "actorId": actor_info.get("actorId", ""),
        "actorName": actor_info.get("actorName", ""),
        "actorType": actor_info.get("actorType", ""),
        "actorTypeName": "企业" if actor_info.get("actorType") == "corp" else "个人",
        "actorStatus": actor.get("signStatus", ""),
        "actorStatusName": parse_actor_status(actor.get("signStatus", "")),
        "signTime": actor.get("signTime", ""),
        "signOrder": actor.get("signOrderNo", 1),
        "actorSignTaskUrl": actor.get("actorSignTaskUrl", ""),
    }


def parse_file(file_data: dict) -> dict:
    """解析文件信息。
    
    Args:
        file_data: API返回的文件数据
        
    Returns:
        标准化的文件信息
    """
    return {
        "fileId": file_data.get("docFileId", ""),
        "fileName": file_data.get("docName", ""),
        "fileStatus": file_data.get("fileStatus", ""),
    }


def parse_task_detail(detail: dict) -> dict:
    """解析任务详情数据。
    
    Args:
        detail: API返回的任务详情
        
    Returns:
        标准化的任务详情
    """
    # 解析签署参与方（支持嵌套 actorInfo 结构）
    actors_data = detail.get("actors", [])
    if isinstance(actors_data, list):
        actors = [parse_actor(a) for a in actors_data if isinstance(a, dict)]
    else:
        actors = []
    
    # 解析文件列表（API 用 docs 字段）
    files_data = detail.get("docs", [])
    if isinstance(files_data, list):
        files = [parse_file(f) for f in files_data if isinstance(f, dict)]
    else:
        files = []
    
    # 解析任务状态（API 用 signTaskStatus）
    task_status = detail.get("signTaskStatus", "")
    
    return {
        "taskId": detail.get("signTaskId", ""),
        "taskName": detail.get("signTaskSubject", ""),
        "taskStatus": task_status,
        "taskStatusName": parse_task_status(task_status),
        "createTime": detail.get("createTime", ""),
        "submitTime": detail.get("startTime", ""),
        "finishTime": detail.get("finishTime", ""),
        "deadline": detail.get("deadlineTime", ""),
        "actors": actors,
        "files": files,
        "actorCount": len(actors),
        "signedCount": sum(1 for a in actors if a.get("actorStatus") == "signed"),
        "fileCount": len(files),
    }


def format_output(api_result: dict) -> dict:
    """格式化输出结果。
    
    Args:
        api_result: API原始响应
        
    Returns:
        格式化后的结果
    """
    task_detail = parse_task_detail(api_result)
    
    return {
        "success": True,
        "data": task_detail
    }


def main():
    parser = argparse.ArgumentParser(
        description="查询签署任务状态",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task-id", required=True, help="签署任务ID")
    parser.add_argument("--skill-context-json", default="", help="Skill运行时上下文(自动注入)")
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
        
        # 查询任务详情
        api_result = get_task_detail(client, args.task_id)
        
        # 格式化输出
        result = format_output(api_result)
        print_result(result)
        
    except Exception as e:
        logger.error(f"查询签署状态失败: {e}")
        print_result(error_response(f"查询签署状态失败: {e}"))


if __name__ == "__main__":
    main()

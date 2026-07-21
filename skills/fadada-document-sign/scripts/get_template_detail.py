#!/usr/bin/env python3
"""查询签署模板详情。

调用接口: /sign-template/get-detail

作用: 查询签署模板的详细信息，包括模板文件、参与方角色等

使用方式:
  python get_template_detail.py --template-id "xxx"

参数说明:
  --template-id (必填): 模板ID
  --debug (可选): 开启调试日志

输出:
  {
    "success": true,
    "data": {
      "templateId": "xxx",
      "templateName": "劳动合同模板",
      "description": "...",
      "status": "1",
      "files": [
        {
          "fileId": "xxx",
          "fileName": "劳动合同.pdf",
          "pageCount": 5
        }
      ],
      "participants": [
        {
          "participantId": "xxx",
          "participantLabel": "甲方",
          "participantSubjectType": 1,
          "signOrder": 1
        },
        {
          "participantId": "xxx",
          "participantLabel": "乙方",
          "participantSubjectType": 0,
          "signOrder": 2
        }
      ]
    }
  }
"""

import argparse
import json
import logging
import sys

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
API_ENDPOINT = "/sign-template/get-detail"


def get_template_detail(
    client: FASCClient,
    template_id: str
) -> dict:
    """查询签署模板详情。
    
    Args:
        client: FASC 客户端
        template_id: 模板ID
        
    Returns:
        模板详情响应
    """
    biz_content = {
        "templateId": template_id,
    }
    
    logger.info(f"查询模板详情: templateId={template_id}")
    
    result = client.request(API_ENDPOINT, biz_content)
    
    logger.info(f"模板详情响应: {json.dumps(result, ensure_ascii=False)}")
    
    return result


def parse_file(file_data: dict) -> dict:
    """解析模板文件信息。
    
    Args:
        file_data: API返回的文件数据
        
    Returns:
        标准化的文件信息
    """
    return {
        "fileId": file_data.get("fileId", ""),
        "fileName": file_data.get("fileName", ""),
        "pageCount": file_data.get("pageCount", 0),
        "fileSize": file_data.get("fileSize", 0),
    }


def parse_participant(participant: dict) -> dict:
    """解析参与方信息。
    
    Args:
        participant: API返回的参与方数据
        
    Returns:
        标准化的参与方信息
    """
    # 主体类型: 0=个人, 1=企业
    subject_type = participant.get("participantSubjectType", 0)
    
    return {
        "participantId": participant.get("participantId", ""),
        "participantLabel": participant.get("participantLabel", ""),
        "participantSubjectType": subject_type,
        "subjectTypeName": "企业" if subject_type == 1 else "个人",
        "signOrder": participant.get("signOrder", 1),
        "required": participant.get("required", True),
    }


def parse_template_detail(detail: dict) -> dict:
    """解析模板详情数据。
    
    Args:
        detail: API返回的模板详情
        
    Returns:
        标准化的模板详情
    """
    # 解析文件列表
    files_data = detail.get("files", [])
    if isinstance(files_data, list):
        files = [parse_file(f) for f in files_data if isinstance(f, dict)]
    else:
        files = []
    
    # 解析参与方列表
    participants_data = detail.get("participants", [])
    if isinstance(participants_data, list):
        participants = [parse_participant(p) for p in participants_data if isinstance(p, dict)]
    else:
        participants = []
    
    return {
        "templateId": detail.get("templateId", ""),
        "templateName": detail.get("templateName", ""),
        "description": detail.get("templateDesc", ""),
        "status": detail.get("status", ""),
        "createTime": detail.get("createTime", ""),
        "updateTime": detail.get("updateTime", ""),
        "files": files,
        "participants": participants,
        "fileCount": len(files),
        "participantCount": len(participants),
    }


def format_output(api_result: dict) -> dict:
    """格式化输出结果。
    
    Args:
        api_result: API原始响应
        
    Returns:
        格式化后的结果
    """
    template_detail = parse_template_detail(api_result)
    
    return {
        "success": True,
        "data": template_detail
    }


def main():
    parser = argparse.ArgumentParser(
        description="查询签署模板详情",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--template-id", required=True, help="模板ID")
    parser.add_argument("--skill-context-json", default="", help="Skill运行时上下文(自动注入)")
    parser.add_argument("--debug", action="store_true", help="开启调试日志")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        # 验证参数
        if not args.template_id:
            print_result(error_response("template-id 参数不能为空"))
            return
        
        # 加载配置并创建客户端
        config = load_config()
        client = FASCClient(config)
        
        # 查询模板详情
        api_result = get_template_detail(client, args.template_id)
        
        # 格式化输出
        result = format_output(api_result)
        print_result(result)
        
    except Exception as e:
        logger.error(f"查询模板详情失败: {e}")
        print_result(error_response(f"查询模板详情失败: {e}"))


if __name__ == "__main__":
    main()

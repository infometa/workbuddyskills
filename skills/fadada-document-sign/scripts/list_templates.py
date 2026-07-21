#!/usr/bin/env python3
"""查询签署模板列表。

调用接口: /sign-template/get-list

作用: 查询企业在法大大平台创建的签署模板列表

使用方式:
  python list_templates.py
  python list_templates.py --template-name "劳动"
  python list_templates.py --page-no 1 --page-size 20

参数说明:
  --template-name (可选): 模板名称搜索关键词
  --page-no (可选): 页码，默认1
  --page-size (可选): 每页数量，默认50
  --status (可选): 模板状态 1=启用 0=停用，默认1
  --debug (可选): 开启调试日志

输出:
  {
    "success": true,
    "data": {
      "templates": [
        {
          "templateId": "xxx",
          "templateName": "劳动合同模板",
          "description": "...",
          "status": "1",
          "createTime": "2024-01-01 10:00:00"
        }
      ],
      "pagination": {
        "pageNo": 1,
        "pageSize": 50,
        "total": 10
      }
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
API_ENDPOINT = "/sign-template/get-list"

# 默认分页
DEFAULT_PAGE_NO = 1
DEFAULT_PAGE_SIZE = 50
DEFAULT_STATUS = "1"


def list_templates(
    client: FASCClient,
    template_name: str = "",
    page_no: int = DEFAULT_PAGE_NO,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str = DEFAULT_STATUS
) -> dict:
    """查询签署模板列表。
    
    Args:
        client: FASC 客户端
        template_name: 模板名称搜索关键词
        page_no: 页码
        page_size: 每页数量
        status: 模板状态
        
    Returns:
        模板列表响应
    """
    biz_content = {
        "pageNo": str(page_no),
        "pageSize": str(page_size),
        "status": status,
    }
    
    if template_name:
        biz_content["templateName"] = template_name
    
    logger.info(f"查询签署模板列表: name={template_name or '全部'}")
    
    result = client.request(API_ENDPOINT, biz_content)
    
    logger.info(f"模板列表响应: {json.dumps(result, ensure_ascii=False)}")
    
    return result


def parse_template(template: dict) -> dict:
    """解析单个模板数据。
    
    Args:
        template: API返回的模板数据
        
    Returns:
        标准化的模板数据
    """
    return {
        "templateId": template.get("templateId", ""),
        "templateName": template.get("templateName", ""),
        "description": template.get("templateDesc", ""),
        "status": template.get("status", ""),
        "createTime": template.get("createTime", ""),
        "updateTime": template.get("updateTime", ""),
        "fileCount": template.get("fileCount", 0),
        "participantCount": template.get("participantCount", 0),
    }


def format_output(api_result: dict, page_no: int, page_size: int) -> dict:
    """格式化输出结果。
    
    Args:
        api_result: API原始响应
        page_no: 页码
        page_size: 每页数量
        
    Returns:
        格式化后的结果
    """
    # 解析模板列表
    templates_data = api_result.get("templates", [])
    if isinstance(templates_data, list):
        templates = [parse_template(t) for t in templates_data if isinstance(t, dict)]
    else:
        templates = []
    
    # 解析分页信息
    total = api_result.get("total", len(templates))
    
    return {
        "success": True,
        "data": {
            "templates": templates,
            "pagination": {
                "pageNo": page_no,
                "pageSize": page_size,
                "total": total,
            }
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="查询签署模板列表",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--template-name", default="", help="模板名称搜索关键词")
    parser.add_argument("--page-no", type=int, default=DEFAULT_PAGE_NO, help=f"页码，默认{DEFAULT_PAGE_NO}")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE, help=f"每页数量，默认{DEFAULT_PAGE_SIZE}")
    parser.add_argument("--status", default=DEFAULT_STATUS, help=f"模板状态 (1=启用, 0=停用)，默认{DEFAULT_STATUS}")
    parser.add_argument("--skill-context-json", default="", help="Skill运行时上下文(自动注入)")
    parser.add_argument("--debug", action="store_true", help="开启调试日志")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        # 加载配置并创建客户端
        config = load_config()
        client = FASCClient(config)
        
        # 查询模板列表
        api_result = list_templates(
            client,
            args.template_name,
            args.page_no,
            args.page_size,
            args.status
        )
        
        # 格式化输出
        result = format_output(api_result, args.page_no, args.page_size)
        print_result(result)
        
    except Exception as e:
        logger.error(f"查询模板列表失败: {e}")
        print_result(error_response(f"查询模板列表失败: {e}"))


if __name__ == "__main__":
    main()

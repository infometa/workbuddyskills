"""
content-creation-expert-prod 主入口（精简版）
=============================================
保留三个 action：
- validate-article：程序化交付质量检查
- render-html：Markdown → HTML 渲染 + COS 可选上传
- render-html-xhs：Markdown → 小红书风格 HTML 渲染
"""

import json
import sys
import os

# 确保 scripts 目录在 sys.path 中（便于相对导入）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error_code": "NoInput",
            "error_message": "请传入 JSON 参数。用法: python3 scripts/main.py '{\"action\":\"...\"}'"
        }, ensure_ascii=False))
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "error_code": "InvalidJSON",
            "error_message": f"JSON 解析失败: {str(e)}"
        }, ensure_ascii=False))
        sys.exit(1)

    action = params.get("action", "")

    # 加载 .env 配置（COS 凭据等）
    from config import load_env
    load_env()

    if action == "validate-article":
        from handlers.validate_article import handle
        handle(params)
    elif action == "render-html":
        from handlers.render_html import handle
        handle(params)
    elif action == "render-html-xhs":
        from handlers.render_html_xhs import handle
        handle(params)
    else:
        print(json.dumps({
            "status": "error",
            "error_code": "UnknownAction",
            "error_message": f"未知 action: '{action}'。可用: validate-article, render-html, render-html-xhs"
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()

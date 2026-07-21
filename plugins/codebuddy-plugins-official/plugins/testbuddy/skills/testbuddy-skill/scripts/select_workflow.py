#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys

# 强制使用 Python 3
if sys.version_info[0] < 3:
    print("错误：此脚本需要 Python 3，请使用 python3 运行", file=sys.stderr)
    sys.exit(1)

# Windows 环境下设置 UTF-8 输出
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 获取脚本所在目录（用于定位默认工作流）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

# 确保脚本所在目录在 sys.path 中，以便正确导入同目录模块
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from get_session import _find_workspace_root  # noqa: E402

# 规则目录路径（自动查找工作区根目录，避免因 cd 到错误目录导致路径错误）
RULES_DIR = os.path.join(_find_workspace_root(), ".codebuddy/rules")

# 默认工作流映射表（当没有自定义工作流时使用）
DEFAULT_WORKFLOWS = {
    "框架生成": "references/workflows/framework-workflow.md",
    "模块生成": "references/workflows/feature-workflow.md",
    "测试点生成": "references/workflows/testpoint-workflow.md",
    "用例生成": "references/workflows/case-workflow.md",
    "测试设计": "references/workflows/design-workflow.md",
    "SPEC": "references/workflows/spec-workflow.md",
}


def select_workflow(keyword):
    """
    根据关键词从工作流列表中智能匹配并返回工作流文件路径

    参数:
        keyword: 匹配关键词，如"框架生成"、"用例生成"、"测试点生成"

    返回:
        匹配成功：工作流文件路径（相对于工作区根目录或 skill 目录）
        匹配失败：空字符串
    """
    if not keyword or not keyword.strip():
        return ""

    keyword = keyword.strip()

    try:
        # 第一步：尝试从自定义规则目录匹配
        if os.path.exists(RULES_DIR):
            # 获取目录下的所有文件
            all_files = []
            for item in os.listdir(RULES_DIR):
                file_path = os.path.join(RULES_DIR, item)
                if os.path.isfile(file_path) and (item.endswith(".md") or item.endswith(".mdc")):
                    all_files.append(item)

            # 筛选文件名以"工作流"结尾的文件
            workflow_files = []
            for filename in all_files:
                # 去掉文件扩展名
                name_without_ext = os.path.splitext(filename)[0]
                # 检查是否以"工作流"结尾
                if name_without_ext.endswith("工作流"):
                    workflow_files.append(filename)

            # 智能匹配
            for filename in workflow_files:
                # 提取文件名前缀（去掉"工作流"后缀和扩展名）
                name_without_ext = os.path.splitext(filename)[0]
                prefix = name_without_ext[:-3]  # 去掉"工作流"三个字

                # 语义匹配：关键词在前缀中，或者前缀在关键词中
                if keyword in prefix or prefix in keyword:
                    # 返回相对于工作区根目录的路径
                    return os.path.join(".codebuddy/rules", filename)

        # 第二步：如果没有匹配到自定义工作流，使用默认工作流映射
        for intent_keyword, default_workflow in DEFAULT_WORKFLOWS.items():
            # 语义匹配：关键词在意图关键词中，或者意图关键词在关键词中
            if keyword in intent_keyword or intent_keyword in keyword:
                # 返回相对于 skill 目录的路径
                workflow_path = os.path.join(SKILL_DIR, default_workflow)
                # 检查文件是否存在
                if os.path.exists(workflow_path):
                    return default_workflow

        return ""

    except Exception as e:
        print(f"错误：{str(e)}", file=sys.stderr)
        return ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 select_workflow.py <keyword>", file=sys.stderr)
        sys.exit(1)

    keyword = sys.argv[1]
    result = select_workflow(keyword)

    # 输出结果
    print(json.dumps({"path": result}, ensure_ascii=False))

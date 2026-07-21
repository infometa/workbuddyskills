#!/usr/bin/env python3
"""
小说质量检测脚本
检测章节中的常见问题：AI词汇、错别字、病句、套路化表达等
"""

import re
import sys
from pathlib import Path

# AI常用词汇模式
AI_PATTERNS = {
    "感悟式词汇": [
        r"他明白了", r"她明白了", r"他懂了", r"她懂了",
        r"他意识到", r"她意识到", r"他终于明白",
        r"不禁.*感叹", r"不由.*感叹",
    ],
    "情绪词": [
        r"感到.*(悲伤|高兴|愤怒|开心|难过)",
        r"觉得.*(孤独|害怕|恐惧)",
        r"内心.*(平静|波澜)",
    ],
    "上帝视角": [
        r"所有人没想到",
        r"全书第.*章",
        r"就在此时",
        r"只见",
    ],
    "模板化": [
        r"众所周知",
        r"不言而喻",
        r"不得不承认",
        r"就在这时",
    ],
    "感叹式": [
        r"真是太",
        r"多么.*啊",
        r"真是.*啊",
    ],
    "排比": r"(.{10,}(，|。).{10,}(，|。).{10,})",
}


def check_file(filepath: str) -> dict:
    """检测文件质量问题"""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"文件不存在: {filepath}"}

    content = path.read_text(encoding="utf-8")
    issues = []

    # 检测AI词汇
    for category, patterns in AI_PATTERNS.items():
        if isinstance(patterns, str):
            patterns = [patterns]
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append({
                    "type": category,
                    "line": line_num,
                    "text": match.group()[:50],
                    "severity": "P0" if category in ["感悟式词汇", "上帝视角", "模板化"] else "P1"
                })

    # 统计字数
    char_count = len(content.replace("\n", "").replace(" ", ""))
    line_count = len(content.split("\n"))

    return {
        "file": str(filepath),
        "char_count": char_count,
        "line_count": line_count,
        "issues": issues,
        "issue_count": len(issues),
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python3 check_quality.py <章节文件路径>")
        sys.exit(1)

    filepath = sys.argv[1]
    result = check_file(filepath)

    if "error" in result:
        print(f"错误: {result['error']}")
        sys.exit(1)

    print(f"文件: {result['file']}")
    print(f"字数: {result['char_count']} | 行数: {result['line_count']}")
    print(f"问题数: {result['issue_count']}")

    if result["issues"]:
        print("\n发现问题:")
        for issue in result["issues"]:
            print(f"  [{issue['severity']}] 第{issue['line']}行 - {issue['type']}: {issue['text']}")

    # 返回状态码
    p0_count = sum(1 for i in result["issues"] if i["severity"] == "P0")
    if p0_count > 0:
        print(f"\n❌ P0问题: {p0_count}个，建议修改")
        sys.exit(1)
    elif result["issue_count"] > 0:
        print(f"\n⚠️ 有{result['issue_count']}个P1问题，建议优化")
    else:
        print("\n✅ 通过检测")


if __name__ == "__main__":
    main()

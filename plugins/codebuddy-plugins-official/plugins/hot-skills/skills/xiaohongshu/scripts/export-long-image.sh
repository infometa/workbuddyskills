#!/bin/bash
# 小红书帖子导出长图
#
# 用法:
#   ./export-long-image.sh --posts-file posts.json -o output.jpg
#   ./export-long-image.sh --posts '<json>' -o output.jpg
#
# posts.json 示例:
# [
#   {
#     "title": "帖子标题",
#     "author": "作者",
#     "stats": "1.3万赞 100收藏",
#     "desc": "正文摘要",
#     "images": ["https://...webp", "https://...webp"]
#   }
# ]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/export-long-image.py" "$@"

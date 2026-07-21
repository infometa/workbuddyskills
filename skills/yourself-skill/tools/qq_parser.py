#!/usr/bin/env python3
"""QQ 聊天记录解析器

支持格式：
- QQ 消息管理器导出的 txt 格式
- QQ 消息管理器导出的 mht 格式

Usage:
    python3 qq_parser.py --file <path> --target <name> --output <output_path>
"""

import argparse
import re
import os
import sys
from pathlib import Path


def parse_qq_txt(file_path: str, target_name: str) -> dict:
    """解析 QQ 导出的 txt 格式

    典型格式：
    消息记录（此消息记录为文本格式，不包含图片等多媒体消息）

    消息分组:我的好友
    ================================================================
    消息对象:张三
    ================================================================

    2024-01-15 20:30:45 张三(123456)
    今天好累

    2024-01-15 20:31:02 我(654321)
    怎么了
    """
    messages = []
    current_msg = None

    # QQ 时间戳 + 发送者模式
    msg_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+?)(?:\((\d+)\))?\s*$')

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n')
            match = msg_pattern.match(line)
            if match:
                if current_msg:
                    messages.append(current_msg)
                timestamp, sender, qq_number = match.groups()
                current_msg = {
                    'timestamp': timestamp,
                    'sender': sender.strip(),
                    'content': ''
                }
            elif current_msg and line.strip() and not line.startswith('==='):
                if current_msg['content']:
                    current_msg['content'] += '\n'
                current_msg['content'] += line

    if current_msg:
        messages.append(current_msg)

    # 基本统计
    target_msgs = [m for m in messages if target_name in m.get('sender', '')]
    all_target_text = ' '.join([m['content'] for m in target_msgs if m.get('content')])

    return {
        'target_name': target_name,
        'total_messages': len(messages),
        'target_messages': len(target_msgs),
        'sample_messages': [m['content'] for m in target_msgs[:50] if m.get('content')],
        'raw_text': all_target_text[:10000],
    }


def parse_qq_mht(file_path: str, target_name: str) -> dict:
    """解析 QQ 导出的 mht 格式（HTML 内容）"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 去除 HTML 标签
    clean_text = re.sub(r'<[^>]+>', '\n', content)
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

    return {
        'target_name': target_name,
        'format': 'mht',
        'raw_text': clean_text[:20000],
        'note': 'MHT 格式，已提取纯文本'
    }


def main():
    parser = argparse.ArgumentParser(description='QQ 聊天记录解析器')
    parser.add_argument('--file', required=True, help='输入文件路径')
    parser.add_argument('--target', required=True, help='目标对象的名字/昵称（如"我"）')
    parser.add_argument('--output', required=True, help='输出文件路径')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    ext = Path(args.file).suffix.lower()
    if ext == '.mht' or ext == '.mhtml':
        result = parse_qq_mht(args.file, args.target)
    else:
        result = parse_qq_txt(args.file, args.target)

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"# QQ 聊天记录分析 — {args.target}\n\n")
        f.write(f"总消息数：{result.get('total_messages', 'N/A')}\n")
        f.write(f"目标消息数：{result.get('target_messages', 'N/A')}\n\n")

        if result.get('sample_messages'):
            f.write("## 消息样本\n")
            for i, msg in enumerate(result['sample_messages'], 1):
                f.write(f"{i}. {msg}\n")
        elif result.get('raw_text'):
            f.write("## 原始文本（截取）\n\n")
            f.write(result['raw_text'][:10000])

    print(f"分析完成，结果已写入 {args.output}")


if __name__ == '__main__':
    main()

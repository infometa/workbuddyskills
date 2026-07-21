#!/usr/bin/env python
"""
将小红书笔记按单独文件导出到 OpenClaw workspace

用法:
    python export_to_workspace.py [db_path] [output_dir]

默认:
    db_path: Volume/Download/ExploreData.db
    output_dir: ~/.openclaw/workspace/xhs-memory

导出格式类似 gpt-history，每条笔记一个文件，文件名格式: YYYY-MM-标题.md
"""
import sqlite3
import re
import sys
from pathlib import Path


def sanitize_filename(name: str, max_len: int = 50) -> str:
    """清理文件名，移除非法字符"""
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '', name)
    name = re.sub(r'\s+', '-', name.strip())
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    if len(name) > max_len:
        name = name[:max_len].rstrip('-')
    return name or "无标题"


def export_to_workspace(db_path: Path = None, output_dir: Path = None):
    db_path = db_path or Path("Volume/Download/ExploreData.db")
    output_dir = output_dir or Path.home() / ".openclaw/workspace/xhs-memory"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        print(f"错误: 数据库不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 作品标题, 发布时间, 作品链接, 作品描述, 作者昵称, 作品标签
        FROM explore_data
        ORDER BY 发布时间 DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("数据库为空")
        return False

    count = 0
    for title, time, link, desc, author, tags in rows:
        # 解析时间: 2026-01-25_18:17:43 -> 2026-01
        if time:
            date_prefix = time[:7]  # YYYY-MM
            full_date = time.replace('_', ' ')
        else:
            date_prefix = "unknown"
            full_date = "未知"

        # 生成文件名
        safe_title = sanitize_filename(title or "无标题")
        filename = f"{date_prefix}-{safe_title}.md"
        filepath = output_dir / filename

        # 避免重复文件名
        counter = 1
        while filepath.exists():
            filename = f"{date_prefix}-{safe_title}-{counter}.md"
            filepath = output_dir / filename
            counter += 1

        # 生成内容
        content = f"# {title or '无标题'}\n\n"
        content += f"**来源**: 小红书收藏/点赞\n\n"
        content += f"**日期**: {full_date}\n\n"
        content += f"**作者**: {author or '未知'}\n\n"
        content += f"**链接**: {link or '无'}\n\n"
        if tags:
            content += f"**标签**: {tags}\n\n"
        content += "---\n\n"
        content += "## 内容\n\n"
        content += f"{desc or '无内容'}\n"

        filepath.write_text(content, encoding="utf-8")
        count += 1

    print(f"导出完成: {output_dir}")
    print(f"共生成 {count} 个文件")
    return True


if __name__ == "__main__":
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    export_to_workspace(db_path, output_dir)

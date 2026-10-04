#!/usr/bin/env python
"""
从 XHS-Downloader 数据库导出笔记到单个 Markdown 文件

用法:
    python export_memory.py [db_path] [output_file]

默认:
    db_path: Volume/Download/ExploreData.db
    output_file: xhs_memory.md
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def export_memory(db_path: Path = None, output_file: Path = None):
    db_path = db_path or Path("Volume/Download/ExploreData.db")
    output_file = output_file or Path("xhs_memory.md")

    if not db_path.exists():
        print(f"错误: 数据库不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询所有作品
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

    # 生成 Markdown
    output = f"# 小红书收藏/点赞笔记 Memory\n\n"
    output += f"> 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output += f"> 共 {len(rows)} 条笔记\n\n---\n\n"

    for i, (title, time, link, desc, author, tags) in enumerate(rows, 1):
        output += f"## {i}. {title or '无标题'}\n\n"
        output += f"- **作者**: {author or '未知'}\n"
        output += f"- **时间**: {time or '未知'}\n"
        output += f"- **链接**: {link or '无'}\n"
        if tags:
            output += f"- **标签**: {tags}\n"
        output += f"\n### 内容\n\n{desc or '无内容'}\n\n---\n\n"

    # 保存文件
    output_file.write_text(output, encoding="utf-8")
    print(f"导出完成: {output_file.absolute()}")
    print(f"共 {len(rows)} 条笔记")
    return True


if __name__ == "__main__":
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    export_memory(db_path, output_file)

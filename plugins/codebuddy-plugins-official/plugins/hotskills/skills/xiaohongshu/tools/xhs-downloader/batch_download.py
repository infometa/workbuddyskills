#!/usr/bin/env python
"""
批量下载小红书笔记

用法:
    python batch_download.py [links_file]

默认读取当前目录的 links.md 文件
"""
import asyncio
import sys
from pathlib import Path

try:
    from source import XHS
except ImportError:
    print("错误: 请在 XHS-Downloader 项目目录下运行此脚本")
    print("或安装依赖: pip install -e /path/to/XHS-Downloader")
    sys.exit(1)


async def main():
    # 读取链接文件
    links_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("links.md")

    if not links_file.exists():
        print(f"错误: 链接文件不存在: {links_file}")
        print("用法: python batch_download.py [links_file]")
        sys.exit(1)

    links = links_file.read_text().strip()
    link_count = len([l for l in links.split() if l.startswith("http")])

    print(f"开始下载，共 {link_count} 个链接...")

    async with XHS(
        work_path="./Volume",
        folder_name="Download",
        record_data=True,       # 记录作品数据到数据库
        download_record=True,   # 跳过已下载
        author_archive=True,    # 按作者分文件夹
    ) as xhs:
        result = await xhs.extract(links, download=True)
        print(f"完成！处理了 {len(result)} 个作品")


if __name__ == "__main__":
    asyncio.run(main())

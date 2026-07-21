"""
公益财会助手 v1.3 — organizer 包

票据自动整理核心模块。把原 1049 行单文件 receipt_organizer.py 拆解为：

- config       常量配置（关键词、扩展名、目录映射）
- patterns     全部正则
- extractors/  抽取器（pdf / docx / image）
- classifier   分类与文件名元数据
- pipeline     文件整理流水线
- ledger       Excel/CSV 台账生成
- reporter     Markdown 汇总报告

入口脚本只做 CLI 解析，所有业务逻辑在本包内。
"""

__version__ = "1.3.0"

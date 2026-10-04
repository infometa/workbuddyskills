# 定期读取与播报

> 定期读取指定文档，提取关键信息生成摘要

**适用场景**：定期读取指定文档，提取关键信息生成摘要

**工具链**：`search_files` → `read_file` → AI 摘要 → `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` | drive | 定位目标文档 |
| `read_file` | drive | 读取文档正文 |
| `get_file_link` | drive | 返回文档链接 |

## 执行流程

1. **search_files**
   定位目标文档
2. **read_file**
   读取文档正文
3. **AI 摘要**
   提取关键信息生成摘要
4. **get_file_link**
   返回文档链接

# 精准搜索与风险排查

> 在特定目录批量搜索文档，逐一读取分析，汇总到新文档

**适用场景**：在特定目录批量搜索文档，逐一读取分析，汇总到新文档

**工具链**：`search_files`（定位目录）→ `search_files`（精确搜索）→ `read_file`（批量）→ AI 分析 → `create_file_with_content` → `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` | drive | 定位目录 |
| `read_file` | drive | 逐一读取文档正文 |
| `create_file_with_content` | drive | 创建新文档并写入报告内容 |
| `get_file_link` | drive | 获取文档链接 |

## 执行流程

1. **search_files**
   定位目录
2. **search_files**
   精确搜索
3. **read_file**
   逐一读取文档正文
4. **AI 分析**
   分析内容
5. **create_file_with_content**
   创建新文档并写入报告内容
6. **get_file_link**
   获取文档链接

# 精准搜索与风险排查

> 在特定目录批量搜索文档，逐一读取分析，汇总到新文档

**适用场景**：在特定目录批量搜索文档，逐一读取分析，汇总到新文档

**工具链**：`search_files`（定位目录）→ `search_files`（精确搜索）→ `read_file_content`（批量）→ AI 分析 → `create_file` + `upload_file`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` | drive | 定位目录 |
| `read_file_content` | drive | 批量读取 |
| `create_file` | drive | 创建汇总文档 |
| `upload_file` | drive | 写入汇总内容 |

## 执行流程

1. **search_files**
   定位目录
2. **search_files**
   精确搜索
3. **read_file_content**
   批量读取
4. **AI 分析**
   分析内容
5. **create_file**
   创建汇总文档
6. **upload_file**
   写入汇总内容

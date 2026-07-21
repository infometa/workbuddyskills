# 搜索-读取-汇报撰写

> 搜索多份文档、提取信息、汇总撰写新报告

**适用场景**：搜索多份文档、提取信息、汇总撰写新报告

**工具链**：`search_files` → `read_file_content`（多次）→ AI 分析 → `create_file` → `upload_file` → `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` | drive | 搜索目标文档 |
| `read_file_content` | drive | 读取文档内容 |
| `create_file` | drive | 创建新文档 |
| `upload_file` | drive | 写入报告内容 |
| `get_file_link` | drive | 获取文档链接 |

## 执行流程

1. **search_files**
   搜索目标文档
2. **read_file_content**
   读取文档内容
3. **AI 分析**
   分析提取信息并撰写报告
4. **create_file**
   创建新文档
5. **upload_file**
   写入报告内容
6. **get_file_link**
   获取文档链接

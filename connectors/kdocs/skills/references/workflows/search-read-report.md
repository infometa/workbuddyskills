# 搜索-读取-汇报撰写

> 搜索多份文档、提取信息、汇总撰写新报告

**适用场景**：搜索多份文档、提取信息、汇总撰写新报告

**工具链**：`search_files` → `read_file`（多次）→ AI 分析 → `create_file_with_content` → `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` | drive | 搜索目标文档 |
| `read_file` | drive | 读取文档正文 |
| `create_file_with_content` | drive | 创建新文档并写入报告内容 |
| `get_file_link` | drive | 获取文档链接 |

## 执行流程

1. **search_files**
   搜索目标文档
2. **read_file**
   读取文档正文
3. **AI 分析**
   分析提取信息并撰写报告
4. **create_file_with_content**
   创建新文档并写入报告内容
5. **get_file_link**
   获取文档链接

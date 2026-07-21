# 智能分类整理

> 列出目录，按内容或指定维度分类创建文件夹并归档

**适用场景**：列出目录，按内容、类型、部门等维度分类创建文件夹并归档。⚠️ `move_file` 前需向用户确认分类方案

**触发词**：分类、整理、归类、归档、按类型、按部门、按项目

- 用户要求对文件夹内容进行分类整理

**工具链**：`search_files` → `list_files`（递归/分页）→ `read_file_content`（批量）→ AI 分类 → `create_folder` → `move_file`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` | drive | 定位目标目录（根目录时 parent_id="0"） |
| `list_files` | drive | 列出目录内容（有 next_page_token 时翻页，子文件夹递归调用） |
| `read_file_content` | drive | 批量读取文档内容用于 AI 分析 |
| `create_folder` | drive | 创建分类文件夹 |
| `move_file` | drive | 移动文件到对应文件夹 |

## 执行流程

```
步骤 1: 定位目标目录
        - 指定文件夹 → search_files(keyword="文件夹名", file_type="folder", type="file_name")
        - 根目录 → search_files(file_type="folder", type="all", scope="personal_drive", page_size=1) 获取 drive_id

步骤 2: list_files(drive_id, parent_id, page_size=500)
        → 收集所有文件（有 next_page_token 时翻页继续）
        → 需要递归扫描子目录时，对 type="folder" 的项再次调用 list_files

步骤 3: read_file_content(format="markdown") 批量读取文档内容

步骤 4: AI 按用户指定维度分类（按内容/类型/部门/项目等）
        → 生成分类方案并向用户确认

步骤 5: create_folder(name="分类文件夹名") 创建分类目录
        move_file(file_ids=[...], dst_parent_id=分类文件夹ID)
        → ⚠️ 批量移动前需向用户确认
```

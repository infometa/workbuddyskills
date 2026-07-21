# 知识一键存入

> 将各类内容（网页、文件、文本）一键保存到知识库

**适用场景**：把这些资料存到知识库

**触发词**：存入知识库、保存到知识库、放到知识库、归档

- 用户要求将内容保存到知识库

**工具链**：`kwiki.get_knowledge_view` → 按内容类型处理 → `kwiki.import_cloud_doc` / `upload_file` / `scrape_url` + `move_file`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `kwiki.get_knowledge_view` | kwiki | 定位目标知识库 |
| `kwiki.list_items` | kwiki | 定位目标文件夹路径 |

## 执行流程

**流程**：
1. **定位知识库**：指定库名 → `kwiki.get_knowledge_view(name=...)`；未指定 → `kwiki.list_knowledge_views` 推荐或引导创建
2. **定位目标路径**：指定文件夹 → `kwiki.list_items` 逐层查找；不存在则 `kwiki.create_item(doc_type="folder")` 按层级创建
3. **归档**：
   - 本地文件 → `upload_file` 上传（保持子目录结构时递归创建文件夹）
   - 网页 → `scrape_url` + `scrape_progress` → `move_file` 移入目标库
   - 云盘已有文件 → `kwiki.import_cloud_doc(action="copy"/"shortcut")`
   - **批量归档今日编辑** → `search_files(scope=["latest_edited"], time_type="mtime", start_time=今日0点时间戳, end_time=当前时间戳)` 筛选文件 → `read_file_content` 批量读取 → AI 按内容自动分类 → `kwiki.create_item(doc_type="folder")` 创建分类文件夹 → `kwiki.import_cloud_doc` 逐个归档
4. **确认结果**：`kwiki.list_items` 返回存放路径与直达链接

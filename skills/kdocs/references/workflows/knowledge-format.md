# 知识智能整理

> 对知识库中的零散内容进行智能化整理和结构化重组

**适用场景**：帮我把知识库里的零散笔记整理成结构化文档

**触发词**：知识整理、整理笔记、结构化、知识格式化

- 用户要求对知识库内容进行整理或结构化重组

**工具链**：`kwiki.list_items` → `read_file_content`（批量）→ AI 整理 → `kwiki.create_item` + `otl.insert_content`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `kwiki.list_items` | kwiki | 遍历知识库内容 |
| `read_file_content` | drive | 批量读取文档内容（file_id 来自 kwiki.list_items） |
| `kwiki.create_item` | kwiki | 创建整理后的新文档 |
| `otl.insert_content` | otl | 写入整理后的内容 |

## 执行流程

**流程**：
1. `kwiki.list_items` 遍历知识库获取文件列表（含 `file_id`、`drive_id`）
2. `read_file_content` 批量读取内容（直接使用 `list_items` 返回的 `file_id`）
3. AI 分析内容结构，生成整理/重组方案
4. `kwiki.create_item(doc_type="o")` 创建新智能文档
5. `otl.insert_content` 写入整理后的结构化内容

**按时间筛选归档**（如"一年前的文档移入归档知识库"）：
1. `kwiki.list_items` 遍历知识库，收集所有条目的 `kuid` 和 `ctime`
2. 按 `ctime` 筛选出早于指定时间的文档（如 `ctime < 当前时间戳 - 365*86400`）
3. `kwiki.get_knowledge_view(name="归档")` 定位目标知识库（不存在则 `kwiki.create_knowledge_view` 创建）
4. `kwiki.move_items(file_kuids=[筛选出的kuid列表], dest_drive_id=归档库drive_id, dest_parent_id="0")` 批量移入
5. ⚠️ 批量移动前需向用户确认文件列表

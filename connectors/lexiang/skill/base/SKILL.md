---
name: lexiang-base
description: "乐享知识库基础规则与数据模型。当需要了解乐享的数据结构、URL规则、写入安全规则、工具发现方式时读取本文档。通常由其他子模块引用，不直接触发。"
---

# 乐享 MCP 基础知识

> 本文档为所有子模块的共享基础层，包含数据模型、URL 规则、安全约束、工具发现等通用知识。

---

## ⛔ 必读（调用前必须理解）

1. 本服务**直接暴露所有业务工具**（如 `team_list_teams`、`search_kb_search` 等），可直接调用
2. 调用前先确认工具参数定义，**以 MCP 返回的 schema 为准**
3. 不确定参数时，使用 `get_tool_schema(tool_name="xxx")` 获取最新定义

---

## 📊 数据模型

### 核心概念

| 概念 | 说明 |
|------|------|
| **Team（团队）** | 顶级组织单元，一个团队下可以有多个知识库(Space) |
| **Space（知识库）** | 知识的容器，属于某个团队，包含多个条目(Entry)，有 `root_entry_id` 作为根节点 |
| **Entry（条目）** | 知识库中的内容单元，可以是页面(page)、文件夹(folder)或文件(file)，支持树形结构(parent_id) |
| **File（文件）** | 附件类型的条目，如 PDF、Word、图片等 |

### 层级关系

```
Team → Space → Entry（树形结构，root_entry_id 为根）
                  ├── page（页面）
                  ├── folder（文件夹）
                  └── file（文件）
```

### URL 规则

`{domain}` = `whoami()` 返回的 `company.company_domain`（如 `https://csig.lexiangla.com` 或 `https://lexiangla.com`）

> **⛔ 严禁使用 MCP endpoint 拼接任何用户可访问的链接！** MCP 域名仅用于接口调用，不是用户访问地址。
> **⛔ 严禁将 `company_from` 拼接为子域名！** `company_from` 只能作为 URL 查询参数（`?company_from=xxx`）。

| 资源 | URL 格式 |
|------|----------|
| 团队首页 | `{domain}/t/{team_id}/spaces` |
| 知识库 | `{domain}/spaces/{space_id}` |
| 知识条目 | `{domain}/pages/{entry_id}` |

**链接生成步骤（所有操作通用）：**

1. 取 `whoami()` 返回的 `company.company_domain` 作为 `{domain}`
2. 判断 `{domain}` 是否为顶级域名（不含三级前缀，如 `lexiangla.com`）：
   - **是**：使用 `{domain}/pages/{entry_id}?company_from={company_from}`
     - `{company_from}` 优先取 mcp.json `url` 中的 `company_from` 参数
     - 若无，取 `whoami()` 返回的 `company.code` ← **此时已调用过 whoami，直接取该值，不能省略**
   - **否**（如 `csig.lexiangla.com`）：使用 `{domain}/pages/{entry_id}`，无需追加参数

| `{domain}` 类型 | 链接格式 | 示例 |
|----------------|----------|------|
| 包含三级域名（如 `csig.lexiangla.com`） | `{domain}/pages/{entry_id}` | `https://csig.lexiangla.com/pages/abc` |
| 顶级域名（如 `lexiangla.com`） | `{domain}/pages/{entry_id}?company_from={company_from}` | `https://lexiangla.com/pages/abc?company_from=csig` |

### URL 解析规则

当用户提供链接时，从 URL 路径中提取 ID（**忽略查询参数**）：

| URL 路径 | 提取方式 |
|----------|----------|
| `/spaces/{space_id}` | 取 `spaces/` 后面的部分作为 `space_id` |
| `/pages/{entry_id}` | 取 `pages/` 后面的部分作为 `entry_id` |
| `/t/{team_id}/spaces` | 取 `t/` 后面的部分作为 `team_id` |

---

## 🛡️ 写入操作安全规则

> **核心原则**：写入、修改、删除操作 **必须基于用户明确提供的目标信息**，禁止 Agent 自行选择或猜测目标。

### 🚫 绝对禁止

1. 禁止遍历团队/知识库列表后自行选择写入目标
2. 禁止根据名称"看起来合适"就决定写入
3. 禁止在未确认时执行写入

### ✅ 允许写入的条件（满足之一即可）

| 条件 | 示例 |
|------|------|
| 用户提供了明确 URL | `"写到这里：https://lexiangla.com/spaces/xxx"` |
| 用户提供了明确 ID | `"写入 space_id 为 xxx 的知识库"` |
| 用户指定名称 + Agent 回显确认 | Agent 搜到后展示详情，用户确认 |
| 用户要求保存到个人知识库且 `whoami` 返回了个人知识库 | `"保存到我的知识库"` → 自动写入个人知识库 |

### 写入 vs 读取工具分类

**写入操作**（需满足安全规则）：
`entry_create_entry`、`entry_import_content`、`entry_import_content_to_entry`、`block_update_block`、`block_update_blocks`、`block_create_block_descendant`、`block_delete_block`、`block_delete_block_children`、`block_move_blocks`、`entry_rename_entry`、`entry_move_entry`、`file_apply_upload`、`file_commit_upload`、`file_create_hyperlink`

**只读操作**（不受安全规则限制，可直接执行）：
`team_list_teams`、`team_describe_team`、`team_list_frequent_teams`、`space_list_spaces`、`space_describe_space`、`entry_list_children`、`block_list_block_children`、`search_kb_search`、`search_kb_embedding_search`、`space_list_recently_spaces`、`entry_list_latest_entries`、`entry_describe_ai_parse_content`、`file_describe_file`、`file_download_file`、`whoami`

---

## 🔍 工具发现与调用

本服务**直接暴露所有业务工具**，可直接调用。同时提供以下辅助元工具：

| 元工具 | 用途 |
|--------|------|
| `list_tool_categories` | 列出所有工具分类及其工具列表 |
| `search_tools` | 按关键词或分类搜索工具 |
| `get_tool_schema` | 获取具体工具的完整参数定义 |

**标准工作流：**

```
1. 直接调用已知工具：team_list_teams()、search_kb_search(keyword="xxx") 等
2. 不确定参数时：get_tool_schema(tool_name="xxx") → 获取参数定义
3. 不确定工具名时：search_tools(query="关键词") → 找到工具名
```

---

## 🧩 Block 结构规则

### 🍃 叶子节点（不能有 children）

| 类型 | 说明 |
|------|------|
| `h1` ~ `h5` | 标题块 |
| `code` | 代码块 |
| `image` | 图片块 |
| `divider` | 分割线 |
| `mermaid` | Mermaid 图表 |
| `plantuml` | PlantUML 图表 |
| `attachment` | 附件块 |
| `video` | 视频块 |

### 📦 容器节点（必须指定 children）

| 类型 | children 内容 |
|------|--------------|
| `callout` | **必须**，内容块 |
| `toggle` | **必须**，折叠内容 |
| `table` | **必须**，table_cell |
| `table_cell` | **必须**，内容块 |
| `column_list` | **必须**，column |
| `column` | **必须**，内容块 |

### 可选 children 节点

`p`、`bulleted_list`、`numbered_list`、`task` 可嵌套子内容，children 为可选。

### 重要：标题与内容的平级关系

标题和其下的内容应该是**平级**的，通过顶层 `children` 的顺序来体现文档结构：

```json
{
  "children": ["h2_1", "para_1", "para_2", "h2_2", "para_3"],
  "descendant": [
    {"block_id": "h2_1", "block_type": "h2", "heading2": {...}},
    {"block_id": "para_1", "block_type": "p", "text": {...}},
    {"block_id": "para_2", "block_type": "p", "text": {...}},
    {"block_id": "h2_2", "block_type": "h2", "heading2": {...}},
    {"block_id": "para_3", "block_type": "p", "text": {...}}
  ]
}
```

---

## 📝 内容读取工具选择

| 工具 | 返回内容 | 用途 |
|------|----------|------|
| `entry_describe_entry` | 条目元信息（ID、名称、类型、创建时间等） | 获取基本信息、后续操作前确认 |
| `entry_describe_ai_parse_content` | **条目正文内容** | 读取实际内容进行摘要/分析/处理 |

> `entry_describe_entry` **不包含正文内容**。需要阅读/总结/分析文档时，必须使用 `entry_describe_ai_parse_content`。

---

## ⚙️ 通用优化技巧

### `_mcp_fields` 字段筛选

所有工具均支持 `_mcp_fields` 参数，只返回需要的字段，减少 token 消耗：

```
# 只获取条目 ID 和名称
entry_list_children(parent_id="xxx", _mcp_fields="entries.id,entries.name")

# 只获取搜索结果的标题和链接
search_kb_search(keyword="xxx", _mcp_fields="items.target_id,items.title,items.target_type")
```

---

## 📚 文档模板参考

写入文档前，先确定文档类型，按对应大纲组织内容：

| 类型 | 适用场景 | 核心结构 |
|------|---------|---------|
| 推广文案型 | 功能推广、工具介绍 | callout(价值) → 痛点 → 方案 → 对比 → 上手 |
| 技术文档型 | API 文档、开发指南 | 概述 → 快速开始 → 详细说明(参数表) → 示例 |
| 操作指南型 | 使用教程、配置指南 | callout(目标) → 前置准备 → 操作步骤 → 验证 |

**Callout 语义映射：**

| 语义 | 类型 | 配色 |
|------|------|------|
| 核心/重要/价值 | primary | `#E3F2FD` |
| 提示/建议/tips | tip | `#FFF3E0` |
| 成功/完成 | success | `#E8F5E9` |
| 警告/注意/风险 | warning | `#FFF8E1` |
| 错误/禁止/危险 | error | `#FFEBEE` |

> 完整模板见 `references/doc-templates.md`

---

## 📎 辅助资源索引

### 参考文档（references/）

| 文档 | 说明 |
|------|------|
| `references/block-schema.md` | Block 类型完整字段定义 |
| `references/mcp-examples.md` | 复杂 Block 结构示例 |
| `references/markdown-to-block.md` | Markdown 转 Block 指南 |
| `references/block-update.md` | 批量更新 Block 方法 |
| `references/content-reorganize.md` | 文档结构重组方案 |
| `references/folder-sync.md` | 文件夹同步方案 |
| `references/markdown-import.md` | Markdown 导入详解 |
| `references/common-errors.md` | 常见错误排查（高频错误速查表） |
| `references/doc-templates.md` | 文档类型与大纲模板 |
| `references/theme-config.md` | 主题配色配置 |

### 辅助脚本（scripts/）

| 脚本 | 说明 |
|------|------|
| `scripts/upload-files.py` | 批量文件上传（支持单文件/文件夹/并行） |
| `scripts/sync-folder.ts` | 文件夹增量同步 |

**upload-files.py 用法：**

```bash
# 单文件上传
python scripts/upload-files.py --files doc.md --entry-id <parent_entry_id>

# 文件夹批量上传（并行）
python scripts/upload-files.py --folder ./docs --entry-id <parent_entry_id> --parallel 5

# 生成上传计划（dry-run）
python scripts/upload-files.py --folder ./docs --entry-id <entry_id> --output plan.json --dry-run
```

---

## ❓ 常见问题

**Q: 如何选择 Markdown 导入方式？**
- `file_apply_upload` → PUT → `file_commit_upload`：保留原始文件格式，支持版本管理，适合文档归档
- `entry_import_content`：转换为 Block 结构，可在线编辑，适合协作场景

**Q: Block ID 如何管理？**
客户端传入的 `block_id` 是临时标识，用于在单次调用中建立块间关系。服务端返回实际 ID 映射，后续更新操作使用服务端返回的 ID。

**Q: 表格单元格如何排序？**
`children` 数组按**从左到右、从上到下**顺序排列。例如 2×2 表格：`[row1_col1, row1_col2, row2_col1, row2_col2]`

> 更多错误排查见 `references/common-errors.md`

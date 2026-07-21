---
name: lexiang-knowledge-base
description: 用于访问乐享知识库平台的专用 skill。当用户明确提到「乐享」「lexiang」「知识库」「知识」「文档」等关键词，或用户提供的链接 host 为 lexiangla.com，应优先调用本 skill。本 skill 支持：获取文档内容与元数据、搜索文档内容、查询知识库与目录结构、创建/编辑/移动文档、管理标签与评论、上传文件及维护附件等知识库操作能力。
description_zh: 支持多源导入、多模态问答、PPT生成的原生Agentic知识库，深度解析图文与音视频，为Agent注入高质量、安全可控的知识
description_en: An Agentic knowledge base with multi-source import, multi-modal Q&A, and PPT generation. It deeply parses text and multimedia, equipping Agents with high-quality, secure knowledge
version: 2.0.3
homepage: https://lexiangla.com
metadata:
  clawdbot:
    emoji: 📚
    requires:
      env:
      - LEXIANG_TOKEN
      - COMPANY_FROM
---

# 乐享 MCP 服务

{{SLOT:TRIGGER}}

---

> **⛔ 必读（调用前必须理解）：**
>
> 1. 本服务**直接暴露所有业务工具**（如 `team_list_teams`、`search_kb_search` 等），可直接调用
> 2. 调用前先确认工具参数定义，**以 MCP 返回的 schema 为准**
> 3. 不确定参数时，使用 `get_tool_schema(tool_name="xxx")` 获取最新定义

---

## 🔑 AccessToken 生命周期管理

### 阶段 1：未配置 Token

当调用 MCP 连接失败或无认证信息时：

1. 告知用户需要获取乐享 MCP 的 `LEXIANG_TOKEN`
2. 引导用户打开 `https://lexiangla.com/mcp` 获取配置信息
3. 用户获取后，帮助完成 mcp.json 配置（参见「快速开始」）

### 阶段 2：Token 即将过期

当 MCP 返回正常结果但附带过期预警信息时：

1. **先正常返回本次结果**
2. 在结果末尾附加提醒，引导用户续期：

```
⚠️ 您的乐享访问令牌即将过期。请打开以下链接，点击「续期」按钮即可延长有效期（需已登录）：
https://lexiangla.com/mcp?company_from={company_from}
```

### 阶段 3：Token 已过期（401 响应）

当 MCP 返回 401 未授权时：

1. **不要反复重试**
2. 引导用户打开 `/mcp` 页面点击续期，原 token 即可恢复使用，**无需重新获取新 token**：

```
🔒 您的乐享访问令牌已过期。请打开以下链接，点击「续期」按钮即可恢复（无需重新配置）：
https://lexiangla.com/mcp?company_from={company_from}
```

### 租户隔离规则

- `COMPANY_FROM` 和 `LEXIANG_TOKEN` **必须属于同一租户**，不同租户的 token 不能混用
- OAuth 不支持跨租户授权
- 续期 token 时，URL 中的 `company_from` 必须与当前配置一致
- 如果用户切换了企业/租户，必须重新获取对应租户的 token

---

## 📊 数据模型

### 核心概念

| 概念                | 说明                                                                                      |
| ------------------- | ----------------------------------------------------------------------------------------- |
| **Team（团队）**    | 顶级组织单元，一个团队下可以有多个知识库(Space)                                           |
| **Space（知识库）** | 知识的容器，属于某个团队，包含多个条目(Entry)，有 `root_entry_id` 作为根节点               |
| **Entry（条目）**   | 知识库中的内容单元，可以是页面(page)、文件夹(folder)或文件(file)，支持树形结构(parent_id)  |
| **File（文件）**    | 附件类型的条目，如 PDF、Word、图片等                                                      |

### 层级关系

```
Team → Space → Entry（树形结构，root_entry_id 为根）
                  ├── page（页面）
                  ├── folder（文件夹）
                  └── file（文件）
```

### URL 规则

{{SLOT:DOMAIN}}

> **⛔ 严禁使用 `{{SLOT:MCP_ENDPOINT}}` 拼接任何用户可访问的链接！** 该域名仅用于 MCP 接口调用，不是用户访问地址。
> **⛔ 严禁将 `company_from` 拼接为子域名！** `company_from` 只能作为 URL 查询参数（`?company_from=xxx`），不能拼成 `https://{company_from}.{{SLOT:HOMEPAGE}}`。

| 资源     | URL 格式                        |
| -------- | ------------------------------- |
| 团队首页 | `{domain}/t/{team_id}/spaces`   |
| 知识库   | `{domain}/spaces/{space_id}`    |
| 知识条目 | `{domain}/pages/{entry_id}`     |

### URL 解析规则

当用户提供链接时，从 URL 路径中提取 ID（**忽略查询参数**）：

| URL 路径                      | 提取方式                                    |
| ----------------------------- | ------------------------------------------- |
| `/spaces/{space_id}`          | 取 `spaces/` 后面的部分作为 `space_id`      |
| `/pages/{entry_id}`           | 取 `pages/` 后面的部分作为 `entry_id`       |
| `/t/{team_id}/spaces`         | 取 `t/` 后面的部分作为 `team_id`            |

---

## 🛡️ 写入操作安全规则

> **核心原则**：写入、修改、删除操作 **必须基于用户明确提供的目标信息**，禁止 Agent 自行选择或猜测目标。

### 🚫 绝对禁止

1. 禁止遍历团队/知识库列表后自行选择写入目标
2. 禁止根据名称"看起来合适"就决定写入
3. 禁止在未确认时执行写入

### ✅ 允许写入的条件（满足之一即可）

| 条件 | 示例 |
| ---- | ---- |
| 用户提供了明确 URL | `"写到这里：https://lexiangla.com/spaces/xxx"` |
| 用户提供了明确 ID | `"写入 space_id 为 xxx 的知识库"` |
| 用户指定名称 + Agent 回显确认 | Agent 搜到后展示详情，用户确认 |
| 用户要求保存到知识库/个人知识库但未指定目标，且 `whoami` 返回了个人知识库 | `"保存到知识库"`、`"保存到我的知识库"` → 自动写入个人知识库 |

### 📝 个人知识库默认写入规则

当用户要求保存内容到知识库或个人知识库，但**未指定具体目标知识库**时，按以下流程处理：

1. **调用 `whoami()`** 获取当前用户信息
2. **检查返回结果中是否包含个人知识库信息**（如 `personal_space_id` 等字段）
3. **如果存在个人知识库**：
   - 将内容直接写入该个人知识库，无需额外确认
   - 使用 `space_describe_space` 获取个人知识库的 `root_entry_id`
   - 使用 `entry_import_content` 写入内容
   - 写入完成后返回访问链接
4. **如果 `whoami` 返回中不包含个人知识库信息**：
   - 回退到标准写入安全规则，要求用户提供具体的写入目标（URL / ID / 名称）

> **注意**：此规则仅适用于用户明确表达"保存到知识库""保存到个人知识库""存到我的知识库"等意图且未指定具体目标的场景。如果用户指定了具体知识库，仍以用户指定的为准。

### 写入操作涉及的工具

`entry_create_entry`、`entry_import_content`、`entry_import_content_to_entry`、`block_update_block`、`block_update_blocks`、`block_create_block_descendant`、`block_delete_block`、`block_delete_block_children`、`block_move_blocks`、`entry_rename_entry`、`entry_move_entry`、`file_apply_upload`、`file_commit_upload`、`file_create_hyperlink`

### 读取操作不受此限制

`team_list_teams`、`team_describe_team`、`team_list_frequent_teams`、`space_list_spaces`、`space_describe_space`、`entry_list_children`、`block_list_block_children`、`search_kb_search`、`search_kb_embedding_search`、`space_list_recently_spaces`、`entry_list_latest_entries`、`entry_describe_ai_parse_content`、`file_describe_file`、`file_download_file`、`whoami` 等只读操作可正常执行。

---

## 🔍 工具发现与调用

本服务**直接暴露所有业务工具**，可直接调用（如 `team_list_teams()`、`search_kb_search(keyword="xxx")`）。

同时提供以下辅助元工具，帮助发现和理解工具：

| 元工具                 | 用途                                           |
| ---------------------- | ---------------------------------------------- |
| `list_tool_categories` | 列出所有工具分类及其工具列表                   |
| `search_tools`         | 按关键词或分类搜索工具                         |
| `get_tool_schema`      | 获取具体工具的完整参数定义                     |

### 标准工作流

```
1. 直接调用已知工具：team_list_teams()、search_kb_search(keyword="xxx") 等
2. 不确定参数时：get_tool_schema(tool_name="xxx") → 获取参数定义
3. 不确定工具名时：search_tools(query="关键词") → 找到工具名
```

> 大多数常用工具已在本 Skill 中列出，可直接使用；遇到新工具或不确定的参数时，再用 `get_tool_schema` 查询。

---

{{SLOT:QUICK_START}}

---

## 🎯 意图识别与澄清

{{SLOT:SCENARIOS}}

---

## 工具概述

本 MCP 服务提供以下工具，**可直接调用**。参数不确定时以 `get_tool_schema` 返回为准。

### 📚 知识库管理
- `entry_create_entry` — 创建文档/文件夹
- `entry_import_content` — 导入 Markdown/HTML 创建新文档（⚠️ 仅新建）
- `entry_import_content_to_entry` — 导入内容到已有页面（支持覆盖/追加）
- `entry_list_latest_entries` — 获取最近更新条目
- `entry_rename_entry` — 重命名条目

### 📎 文件管理
- `file_apply_upload` — 申请文件上传（返回 upload_url 和 session_id）
- `file_commit_upload` — 确认上传完成
- `file_describe_file` — 获取文件详情
- `file_download_file` — 下载文件

### 🧩 Block 操作
- `block_convert_content_to_blocks` — Markdown/HTML 转 Block 结构
- `block_create_block_descendant` — 创建 Block 结构
- `block_update_block` — 单块更新
- `block_update_blocks` — 批量更新
- `block_move_blocks` — 移动 Block
- `block_delete_block_children` — 删除子节点
- `block_delete_block` — 删除指定 Block（含子孙）
- `block_describe_block` — 获取单个 Block 详情
- `block_list_block_children` — 读取 Block 内容

### 👤 用户与身份
- `whoami` — 获取当前用户信息（包括用户姓名、企业信息、个人知识库等）

### 🔍 搜索与发现
- `search_kb_search` — 关键词搜索
- `search_kb_embedding_search` — 语义向量搜索
- `team_list_teams` — 获取团队列表
- `team_describe_team` — 获取团队详情
- `team_list_frequent_teams` — 获取常用团队列表
- `space_list_spaces` — 获取知识库列表
- `space_describe_space` — 获取知识库详情（返回 `root_entry_id`）
- `space_list_recently_spaces` — 获取最近访问知识库

### 📖 条目与结构浏览
- `entry_list_children` — 浏览目录结构
- `entry_describe_entry` — 获取条目元信息（不含正文）
- `entry_describe_ai_parse_content` — 获取 AI 解析内容（含正文）
- `entry_list_parents` — 获取父级路径（面包屑）

### 🔗 外部内容导入
- `file_create_hyperlink` — 导入公众号文章等外部链接

---

## 内容搜索

### 关键词搜索 vs 语义搜索

| 工具 | 适用场景 |
|------|----------|
| `search_kb_search` | 精确关键词匹配 |
| `search_kb_embedding_search` | 模糊查询、"记得大意但忘了标题" |

**建议**：语义搜索召回后，再用 `entry_describe_entry` 或 `entry_describe_ai_parse_content` 精确读取。

### 搜索结果链接格式

根据返回的 `target_type` 拼接链接：

| target_type            | URL 格式                                    |
| ---------------------- | ------------------------------------------- |
| `kb_page`              | `{domain}/pages/<target_id>`                |
| `kb_file` / `kb_video` | `{domain}/teams/<team_id>/docs/<target_id>` |

---

## 🔗 结果链接生成规则（通用）

> **适用于所有返回 `entry_id` 的操作**，包括但不限于：`entry_import_content`、`entry_create_entry`、`entry_import_content_to_entry`、`file_commit_upload`、搜索结果等。

### 拼接规则

当操作成功返回了 `entry_id`（或 `target_id`），向用户展示访问链接时，使用上方「URL 规则」中定义的 `{domain}` 拼接：

```
{domain}/pages/{entry_id}
```

### ⛔ 禁止

- **禁止**使用 `{{SLOT:MCP_ENDPOINT}}` 拼接用户访问链接
- **禁止**使用 MCP 连接 URL（`{{SLOT:MCP_ENDPOINT}}`）的域名作为用户访问域名
- **禁止**将 `company_from` 拼接为子域名（如 `https://{company_from}.{{SLOT:HOMEPAGE}}` 是**错误**的）
- **禁止**编造或猜测域名，必须严格使用上方定义的 `{domain}`

---

## 📖 内容读取

| 工具 | 返回内容 | 用途 |
|------|----------|------|
| `entry_describe_entry` | 条目元信息（ID、名称、类型等） | 获取基本信息 |
| `entry_describe_ai_parse_content` | **条目正文内容** | 读取实际内容进行分析 |

---

## 常见操作流程

### 从知识库链接写入文档

> ⚠️ 仅在用户**主动提供了知识库链接**时执行。详见下方「常见使用场景 > 场景0」。

核心步骤：提取 `space_id` → `space_describe_space` 获取 `root_entry_id` → `entry_import_content` 写入 → 用 `{domain}/pages/{entry_id}` 拼接访问链接返回给用户。

### 微信公众号导入

当用户提供 `mp.weixin.qq.com` 链接且意图是"导入/收藏/保存到乐享"时，使用 `file_create_hyperlink`。

> 如果用户只是想阅读或总结内容，不要默认导入。

### 文件上传完整流程（三步）

> ⚠️ **必须严格按顺序执行以下三步，缺一不可。**

**Step 1: 申请上传凭证（MCP 调用）**

```
MCP Tool: file_apply_upload
Arguments: {
  "parent_entry_id": "<目标目录的 entry_id>",
  "name": "example.pdf",
  "size": 12345,
  "mime_type": "application/pdf",
  "upload_type": "PRE_SIGNED_URL"
}
```

必填参数说明：

| 参数 | 说明 | 获取方式 |
|------|------|----------|
| `parent_entry_id` | 目标目录的 entry_id | 从知识库 URL 提取 `space_id`，或通过 `entry_list_entries` 查找 |
| `name` | 文件名（含扩展名） | 本地文件名 |
| `size` | 文件大小（**字节数，必填**） | 通过 `wc -c <文件>` 或 `stat -f%z <文件>` 获取 |
| `mime_type` | MIME 类型 | 见下方常见类型表 |
| `upload_type` | 固定填 `"PRE_SIGNED_URL"` | — |

返回值包含 `session.session_id` 和 `session.upload_url`。

**Step 2: HTTP PUT 上传文件内容（curl 命令，非 MCP）**

> ⚠️ **这一步不是 MCP 调用，必须用 curl 命令执行 HTTP PUT 请求。**

```bash
curl -X PUT \
  -H "Content-Type: <mime_type>" \
  --data-binary "@<本地文件路径>" \
  "<Step 1 返回的 upload_url>"
```

实际示例：

```bash
# 上传 PDF 文件
curl -X PUT \
  -H "Content-Type: application/pdf" \
  --data-binary "@/path/to/example.pdf" \
  "https://cos.example.com/upload?sign=xxx"

# 上传图片
curl -X PUT \
  -H "Content-Type: image/png" \
  --data-binary "@/path/to/screenshot.png" \
  "https://cos.example.com/upload?sign=xxx"
```

curl 参数说明：
- `-X PUT`：必须是 PUT 方法（不是 POST）
- `--data-binary`：必须用 `--data-binary`（不是 `-d` 或 `--data`），保持二进制完整性
- `@文件路径`：`@` 前缀表示读取文件内容，路径必须用绝对路径
- `Content-Type`：必须与 Step 1 中的 `mime_type` 一致

成功标志：curl 返回 HTTP 200 或空响应（无报错）

**Step 3: 确认上传完成（MCP 调用）**

```
MCP Tool: file_commit_upload
Arguments: {
  "session_id": "<Step 1 返回的 session_id>"
}
```

返回值包含新文件的 `entry_id`，上传完成。

### 常用 MIME 类型速查

| 文件类型 | 扩展名 | mime_type |
|----------|--------|-----------|
| PDF | .pdf | `application/pdf` |
| Word | .docx | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Excel | .xlsx | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PPT | .pptx | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| 图片 PNG | .png | `image/png` |
| 图片 JPG | .jpg/.jpeg | `image/jpeg` |
| Markdown | .md | `text/markdown` |
| 文本 | .txt | `text/plain` |
| ZIP | .zip | `application/zip` |

### 更新已有文件

更新文件需要额外的 `file_id` 参数，且 `parent_entry_id` 填**文件自身的 entry_id**（不是父目录）。

1. 先获取 file_id：`entry_describe_entry(entry_id=<文件的 entry_id>)` → 返回值中 `target_id` 就是 `file_id`
2. 调用 `file_apply_upload` 时额外传入 `file_id` 参数
3. 同样执行 Step 2（curl PUT）和 Step 3（commit_upload）

### 文件上传常见错误

| 错误 | 原因 | 修复 |
|------|------|------|
| apply_upload 失败 | 缺少 `size` 参数 | **必须传文件字节数** |
| curl PUT 返回 403 | upload_url 过期或格式错误 | 重新执行 Step 1 获取新 URL |
| curl PUT 上传 0 字节 | 用了 `-d` 而不是 `--data-binary` | 改用 `--data-binary "@文件"` |
| commit 后文件为空 | 跳过了 Step 2 | 必须先 curl PUT 上传文件内容 |
| 更新文件变成新建 | 没传 `file_id` | 更新时必须传 `file_id` |
| 更新时 parent_entry_id 错误 | 填了父目录 ID | 更新时填**文件自身的 entry_id** |

---

{{SLOT:EXAMPLES}}

---

## Block 结构核心规则

### 🍃 叶子节点（不能有 children）
- 标题块：h1, h2, h3, h4, h5
- 代码块：code
- 图片块：image
- 分割线：divider
- 图表块：mermaid, plantuml

### 📦 容器节点（必须指定 children）
- 提示框：callout
- 表格：table, table_cell
- 分栏布局：column_list, column
- 折叠块：toggle

> **详细说明**：完整 Block 类型和字段定义见 `references/block-schema.md`。

---

## ⚠️ 核心注意事项

1. **Block ID 映射**：`block_id` 为客户端临时 ID，服务端返回实际 ID 映射
2. **叶子节点限制**：标题、代码块、图片等不支持 children 字段
3. **容器节点要求**：callout、table、column_list 等必须指定 children
4. **文件上传**：必须获取准确的文件大小（字节数），Step 2 必须用 `curl -X PUT --data-binary` 执行（非 MCP 调用）
5. **`_mcp_fields` 优化**：所有工具支持 `_mcp_fields` 参数选择返回字段，减少 token 消耗

> **更多细节**：见 `references/common-errors.md` 和 `references/markdown-import.md`。

---

## 辅助资源

### 参考文档（references/ 目录）

| 文档                    | 说明                   |
| ----------------------- | ---------------------- |
| `block-schema.md`       | Block 类型完整说明     |
| `mcp-examples.md`       | 复杂 Block 结构示例    |
| `markdown-to-block.md`  | Markdown 转 Block 指南 |
| `block-update.md`       | 批量更新 Block 方法    |
| `content-reorganize.md` | 文档结构重组           |
| `folder-sync.md`        | 文件夹同步方案         |
| `markdown-import.md`    | Markdown 导入详解      |
| `common-errors.md`      | 常见错误排查           |
| `skill-maintenance.md`  | 维护与反馈流程         |

### 辅助脚本（scripts/ 目录）

| 脚本               | 说明               |
| ------------------ | ------------------ |
| `sync-folder.ts`   | 文件夹增量同步     |
| `block-helper.ts`  | Block 构建辅助工具 |
| `mcp-validator.ts` | MCP 参数校验       |

---

## ❓ 问题与排查

遇到问题时，请先查阅 `references/common-errors.md`。

---

## 📮 维护与反馈

Issue 反馈流程和 Skill 自我进化机制见 `references/skill-maintenance.md`。

---

## 相关链接

- 乐享平台：https://lexiangla.com
- MCP 协议：https://modelcontextprotocol.io

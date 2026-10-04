# 乐享 Block 操作

> **基础知识**：数据模型、URL 规则、写入安全规则、Block 完整类型定义见 `references/base.md`。
> **前置条件**：本skill 需要已配置乐享 MCP 连接。如未配置，请先读取 `references/setup.md`。
> **遇到 401 错误**：不要重试，读取 `references/setup.md` 引导用户续期（点击续期按钮即可恢复，无需重新配置）。
> **安全规则**：Block 写入操作必须基于用户明确提供的目标信息，禁止 Agent 自行遍历或猜测写入目标。

---

## 工具概览

###📄 页面级操作（优先使用）
- `block_fetch_page` — 获取页面正文（支持 markdown/mdx/clean 三种格式）
- `block_update_page` — 命令式更新页面内容（replace/update/delete/replace_blocks）

### 🧩 原子 Block 操作
- `block_convert_content_to_blocks` — Markdown/HTML转 Block 结构（纯转换，不创建）
- `block_create_block_descendant` — 在指定块下创建子块结构
- `block_update_block` — 单块更新
- `block_update_blocks` — 批量更新多个块
- `block_move_blocks` — 移动块到新位置
- `block_delete_block_children` — 删除指定子块
- `block_delete_block` — 删除指定块（含子孙）
- `block_describe_block` — 获取单个块详情
- `block_list_block_children` — 列出块的子节点
- `block_apply_block_attachment_upload` — 申请块附件/图片上传凭证

### 🔎 资源快捷访问
- `lexiang_fetch` — 按资源类型读取单个乐享资源（entry/space/team/file/block/smartsheet/record）
- `lexiang_search` — 搜索乐享资源（doc/space/team/all）

---

## 🛠️ 工具选择优先级

> **操作 page 正文时，优先使用页面级工具，不要默认走原子 Block 工具：**

| 场景 | 推荐工具 |
|------|---------|
| 创建/更新 page 正文 | `block_fetch_page` + `block_update_page` |
| 读取页面结构用于编辑 | `block_fetch_page(render_mode="mdx")` |
| 读取页面内容用于阅读 | `block_fetch_page(render_mode="clean")` 或 `entry_describe_ai_parse_content` |
| 局部插入新内容 | `block_update_page(command="update_content")` |
| 大范围重写 | `block_update_page(command="replace_content")` |
| 删除指定块 | `block_update_page(command="delete_blocks")` |
| 需要低层块级能力（用户明确要求） | 原子 Block 工具 |

---

## 📄 block_fetch_page 使用说明

```
render_mode 选择：
- "markdown"→ 返回可回写的乐享 block-markdown，用于文本替换编辑
- "mdx"       → 返回带 data-id 的结构化 MDX，用于结构化编辑（replace_blocks）
- "clean"     → 仅用于阅读/摘要，不可回写
```

>修改页面前必须先调用 `block_fetch_page`，拿到当前内容再编辑。

---

## 📝 block_update_page 命令说明

| 命令 | 说明 | 关键参数 |
|------|------|---------|
| `replace_content` | 替换整页内容（大范围重写） | `new_str`（新内容） |
| `update_content` | 搜索替换（局部更新，支持多条） | `content_updates: [{old_str, new_str}]` |
| `delete_blocks` | 按 block_id 删除块 | `block_ids` |
| `replace_blocks` | 按 block_id 替换 MDX 片段 | `block_replacements`（需 `content_format=mdx`） |

**重要约束：**
- `update_content` 的 `old_str` 必须精确来自 `block_fetch_page` 的输出，不依赖相似匹配
- 删除内容时将 `new_str` 设为空字符串，或优先使用 `delete_blocks`
- 插入/追加内容：把 `old_str` 替换为 `old_str +新内容`
- `dry_run=true` 只校验不写回，可用于预检

---

## 🖼️ 块附件/图片上传流程

上传图片或附件到 Block 时使用 `block_apply_block_attachment_upload`：

```
Step 1: block_apply_block_attachment_upload
  → 返回 session_id + upload_url

Step 2: curl -X PUT --data-binary "@文件" upload_url
  （HTTP PUT，非 MCP 调用）

Step 3: 在 block_create_block_descendant 中，attachment/image block
  的 session_id 字段传入 session_id
```

>⚠️ 暂不支持视频（VOD）上传，video block 请使用 `file_id` 字段。

---

## Block 结构核心规则

>完整 Block 类型定义（含 attachment、video等）见 `references/base.md` 或 `references/block-schema.md`。

###🍃叶子节点（不能有 children）
标题块(h1~h5)、代码块(code)、图片块(image)、分割线(divider)、图表块(mermaid/plantuml)、附件块(attachment)、视频块(video)

### 📦 容器节点（必须指定 children）
提示框(callout)、表格(table/table_cell)、分栏布局(column_list/column)、折叠块(toggle)

---

## ⚠️ 核心注意事项

1. **优先页面级工具**：操作 page 正文时优先用 `block_fetch_page` + `block_update_page`，不要默认走原子 Block 工具或导入转换逻辑
2. **Block ID 映射**：`block_id` 为客户端临时 ID，服务端返回实际 ID 映射
3. **标题与内容平级**：标题块不能包含 children，通过顶层 `children` 顺序体现文档结构
4. **`_mcp_fields` 优化**：所有工具支持 `_mcp_fields` 参数选择返回字段，减少 token 消耗
5. 参数不确定时以 `get_tool_schema(tool_name="xxx")` 返回为准

---

## 参考文档

| 文档 | 说明 |
|------|------|
| `references/block-schema.md` | Block 类型完整字段定义 |
| `references/mcp-examples.md` | 复杂 Block 结构示例 |
| `references/markdown-to-block.md` | Markdown 转 Block 指南 |
| `references/block-update.md` | 批量更新 Block 方法 |
| `references/content-reorganize.md` | 文档结构重组方案 |
| `references/common-errors.md` | 常见错误排查 |

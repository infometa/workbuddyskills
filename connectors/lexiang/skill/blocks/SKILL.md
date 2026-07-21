---
name: lexiang-blocks
description: "乐享知识库已有页面的内容编辑与排版操作。【核心特征：用户提供了 lexiangla.com/pages/ 链接，并要求对该页面进行修改/编辑/追加/删除/移动操作】。当用户提到「乐享」「知识库」「lexiang」并明确指向已有页面做内容变更时使用。典型触发：「修改这个页面」「编辑一下这篇文档」「在页面里加个标题」「更新一下内容」「调整排版」「追加一段内容」「帮我改一下这个表格」「在这个页面后面插入…」「把这段移到前面」「删掉这个段落」「给这个页面加一段总结」「在 /pages/xxx 里创建标题」。【注意】：仅当操作目标是「已有页面」时才触发本 skill；创建全新文档请使用 writer/SKILL.md；仅浏览/搜索/阅读请使用 search/SKILL.md。支持 Block 级别的创建、更新、删除、移动、批量编辑，Markdown/HTML 转 Block 结构插入。"
---

# 乐享 Block 操作

> **基础知识**：数据模型、URL 规则、写入安全规则、Block 完整类型定义见 `base/SKILL.md`。
> **前置条件**：本 skill 需要已配置乐享 MCP 连接。如未配置，请先读取 `setup/SKILL.md`。
> **遇到 401 错误**：不要重试，读取 `setup/SKILL.md` 引导用户续期（点击续期按钮即可恢复，无需重新配置）。
> **安全规则**：Block 写入操作必须基于用户明确提供的目标信息，禁止 Agent 自行遍历或猜测写入目标。

---

## 工具概览

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

---

## Block 结构核心规则

> 完整 Block 类型定义（含 attachment、video 等）见 `base/SKILL.md` 或 `references/block-schema.md`。

### 🍃 叶子节点（不能有 children）
标题块(h1~h5)、代码块(code)、图片块(image)、分割线(divider)、图表块(mermaid/plantuml)、附件块(attachment)、视频块(video)

### 📦 容器节点（必须指定 children）
提示框(callout)、表格(table/table_cell)、分栏布局(column_list/column)、折叠块(toggle)

---

## ⚠️ 核心注意事项

1. **Block ID 映射**：`block_id` 为客户端临时 ID，服务端返回实际 ID 映射
2. **标题与内容平级**：标题块不能包含 children，通过顶层 `children` 顺序体现文档结构
3. **`_mcp_fields` 优化**：所有工具支持 `_mcp_fields` 参数选择返回字段，减少 token 消耗
4. 参数不确定时以 `get_tool_schema(tool_name="xxx")` 返回为准

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

---
name: lexiang-writer
description: "乐享知识库文档创建与写入。当用户提到「乐享」「知识库」「lexiang」并包含创建/写入/新建/导入意图时使用。典型触发：「写到乐享」「创建一个文档」「帮我新建一个页面」「把这段内容发到乐享」「保存到知识库」「导入到乐享」「帮我在 XX 知识库下建个文档」「把这篇文章存到乐享」。也适用于用户提供 lexiangla.com 链接并要求写入新内容、导入公众号文章到知识库的场景。支持 Markdown/HTML 导入创建文档、创建页面与文件夹、外部链接导入。注意：上传 PDF/Word/图片等文件请使用 files/SKILL.md。"
---

# 乐享文档写入

> **基础知识**：数据模型、URL 规则、写入安全规则完整版见 `base/SKILL.md`。
> **前置条件**：本 skill 需要已配置乐享 MCP 连接。如未配置，请先读取 `setup/SKILL.md`。
> **遇到 401 错误**：不要重试，读取 `setup/SKILL.md` 引导用户续期（点击续期按钮即可恢复，无需重新配置）。
> **安全规则**（完整版见 `base/SKILL.md`）：禁止遍历猜测写入目标；必须有明确 URL/ID/确认，或 `whoami` 返回个人知识库时可直接写入个人知识库

---

## 工具概览

### 📚 知识库管理
- `entry_create_entry` — 创建文档/文件夹
- `entry_import_content` — 导入 Markdown/HTML 创建新文档（⚠️ 仅新建）
- `entry_import_content_to_entry` — 导入内容到已有页面（支持覆盖/追加）
- `entry_rename_entry` — 重命名条目

### 👤 用户与身份
- `whoami` — 获取当前用户信息（包括用户姓名、企业信息、个人知识库等）

### 🔗 外部内容导入
- `file_create_hyperlink` — 导入公众号文章等外部链接

---

## 常见操作流程

### ⚠️ 前置检查：确认产品版本

**每次执行写入操作前**，先调用 `whoami()` 检查 `sub_server_type`：
- `v2` → 继续使用本 skill
- `v1` → **停止，提示用户加载 `lexiang-v1-docs` skill**（本 skill 不适用于 v1）
- `v1v2` → 如果用户明确说了「乐享社区」→ 提示切换 `lexiang-v1-docs`；否则继续使用本 skill

### 从知识库链接写入文档

> ⚠️ 仅在用户**主动提供了知识库链接**时执行。

核心步骤：提取 `space_id` → `space_describe_space` 获取 `root_entry_id` → `entry_import_content` 写入 → 按「结果链接生成」规则拼接访问链接返回给用户。

> `{domain}` 为 `whoami()` 返回的 `company.company_domain`。

### 未指定知识库时写入个人知识库

当用户要求保存内容到知识库或个人知识库，但**未指定具体目标知识库**时：

1. **调用 `whoami()`** 获取当前用户信息
2. **检查返回结果中是否包含个人知识库信息**（如 `personal_space_id` 等字段）
3. **如果存在个人知识库**：
   - 使用 `space_describe_space` 获取个人知识库的 `root_entry_id`
   - 使用 `entry_import_content` 写入内容（`space_id` 和 `parent_id` 同时传）
   - 写入完成后拼接访问链接返回给用户：
     - `{domain}` = `whoami()` 返回的 `company.company_domain`
     - 若 `{domain}` 为顶级域名（如 `lexiangla.com`），则追加 `?company_from=<whoami返回的company.code>`
     - 示例：`https://lexiangla.com/pages/{entry_id}?company_from=csig`
4. **如果 `whoami` 返回中不包含个人知识库信息**：
   - 回退到标准写入安全规则，要求用户提供具体的写入目标（URL / ID / 名称）

> **注意**：此规则仅适用于用户明确表达"保存到知识库""保存到个人知识库""存到我的知识库"等意图且未指定具体目标的场景。如果用户指定了具体知识库，仍以用户指定的为准。

### 微信公众号导入

当用户提供 `mp.weixin.qq.com` 链接且意图是"导入/收藏/保存到乐享"时，使用 `file_create_hyperlink`。

> 如果用户只是想阅读或总结内容，不要默认导入。

---

## 🔗 结果链接生成

写入操作成功后，按以下步骤拼接访问链接：

1. `{domain}` = `whoami()` 返回的 `company.company_domain`
2. 判断 `{domain}` 是否为顶级域名（不含三级前缀，如 `lexiangla.com`）：
   - **是**：追加 `?company_from={company_from}`
     - `{company_from}` 优先取 mcp.json `url` 中的 `company_from` 参数
     - 若 mcp.json 中无此参数，取 `whoami()` 返回的 `company.code`
   - **否**（如 `csig.lexiangla.com`）：直接使用 `{domain}/pages/{entry_id}`，不追加参数
3. 最终链接：`{domain}/pages/{entry_id}` 或 `{domain}/pages/{entry_id}?company_from=xxx`

**禁止**使用 MCP 端点域名拼接用户访问链接。

---

## ⚠️ 核心注意事项

1. `entry_import_content` 的 `parent_id` 通常用 `root_entry_id`（通过 `space_describe_space` 获取）
2. `space_id` 和 `parent_id` 要同时传
3. 支持的 `content_type`：`markdown`、`html`
4. 参数不确定时以 `get_tool_schema(tool_name="xxx")` 返回为准

---

## 参考文档

| 文档 | 说明 |
|------|------|
| `references/markdown-import.md` | Markdown 导入详解 |
| `references/doc-templates.md` | 文档类型与大纲模板（推广/技术/操作指南） |
| `references/common-errors.md` | 常见错误排查 |
| `base/SKILL.md` | 数据模型、写入安全规则完整版 |

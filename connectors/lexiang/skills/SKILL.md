---
name: lexiang-knowledge-base
version: 2.2.0
description: "乐享知识库 MCP 全功能 Skill。当用户提到「乐享」「知识库」「个人知识库」「我的知识库」「lexiang」，或提供 lexiangla.com 链接，或涉及知识库的搜索/写入/编辑/文件/配置/评论/草稿/智能表格等操作时使用。"
---

# 乐享知识库 MCP Skill

当用户提到「**乐享**」「**知识库**」「**个人知识库**」「**我的知识库**」「**lexiang**」，或提供 `lexiangla.com` 链接，或给出 `space_id`、`entry_id`、`/spaces/`、`/pages/` 等乐享标识时，读取本 Skill。

---

## ⛔ MANDATORY RULES — 必须遵守

1. **遇到 401 / 连接断开**：立即停止重试，读取 `references/setup.md`；内置连接器平台（WorkBuddy/QClaw 等）引导重新授权，其他平台引导续期
2. **写入操作**：必须基于用户明确提供的目标（URL/ID/名称确认），**禁止**自行遍历或猜测目标
3. **链接生成**：必须使用 `whoami()` 返回的 `company.company_domain` 作为域名，**禁止**使用 MCP endpoint 拼接用户链接
4. **company_from**：不能拼接为子域名，只能作 `?company_from=xxx` 查询参数
5. **强制检索**：当用户消息同时包含「乐享/知识库」等平台词 + 「文档/论文/文章/内容/资料/笔记/之前写的/上次的/风格」等内容词时，**必须先调用 `search_kb_search` 或 `search_kb_embedding_search` 获取实际内容**，不得凭空分析或直接生成回答
6. **大批量保护**：文件/条目数量 > 20 个时，**必须分批执行**（每批 ≤ 20 个）；操作前告知用户数量和策略，禁止一次性提交导致 token 超限，详见 `references/files.md`

---

## 🔗 链接生成规则（全局通用）

所有操作完成后返回链接时，统一遵循：

| `company.company_domain` 类型 | 链接格式 | 示例 |
|------------------------------|----------|------|
| 包含三级域名（如 `csig.lexiangla.com`） | `{domain}/pages/{entry_id}` | `https://csig.lexiangla.com/pages/abc` |
| 顶级域名（如 `lexiangla.com`） | `{domain}/pages/{entry_id}?company_from={company_from}` | `https://lexiangla.com/pages/abc?company_from=csig` |

**`{company_from}` 获取优先级：**
1. mcp.json `url` 字段中的 `company_from` 参数
2. 若无，使用 `whoami().company.code`

---

## 🛡️ 写入安全红线（全局通用）

- 🚫 禁止遍历团队/知识库列表后自行选择写入目标
- 🚫 禁止根据名称"看起来合适"就决定写入
- 🚫 禁止在未确认时执行写入

> 完整安全规则（允许写入的条件、工具分类）见 `references/base.md`

---

## 📋 意图路由表

根据用户意图，Read 对应参考文件：

| 用户意图 | 读取文件 | 典型触发词 |
|---------|---------|-----------|
| 配置乐享 / 401 错误 / Token 过期 | `references/setup.md` | 「配置乐享」「token 过期」「连不上」「401」 |
| 搜索 / 查找 / 阅读 / 浏览 | `references/search.md` | 「找一下」「搜索」「读一下这个页面」「打开链接」 |
| 创建文档 / 写入 / 保存 / 导入 | `references/writer.md` | 「写到乐享」「创建文档」「保存到知识库」「存到我的知识库」「保存到个人知识库」「导入」 |
| 编辑已有页面 / Block 操作 | `references/blocks.md` | 「修改这个页面」「加个标题」「删掉这段」「在 /pages/xxx 里…」 |
| 上传/下载文件（PDF/Word/图片等） | `references/files.md` | 「传个 PDF」「上传文件」「下载这个文件」 |
| 导入腾讯会议 | `references/connectors.md` | 「把会议录制导入」「导入会议录制」 |
| 智能表格 / 结构化数据 | `references/smartsheet.md` | 「智能表格」「乐享表格」「表格里的数据」「新增一行」「查询记录」 |
| 草稿 / 存草稿 / 发布 | `references/draft.md` | 「先存草稿」「保存为草稿」「发布草稿」「查看草稿」 |
| 查看评论 | `references/comment.md` | 「这个页面有什么评论」「看看评论」「有没有讨论」 |
| 数据模型 / URL 规则 / 完整安全规则 | `references/base.md` | 由上述模块内部引用 |

### ⚠️ 易混淆场景

| 场景 | 正确模块 | 说明 |
|------|---------|------|
| 用户提供 `/pages/xxx` 链接 + 要求「加内容/修改」 | `references/blocks.md` | 操作**已有页面** |
| 用户提供 `/spaces/xxx` 链接 + 要求「写入/创建」 | `references/writer.md` | 在知识库下**新建文档** |
| 用户提供 `/pages/xxx` 链接 + 仅要求「读/总结」 | `references/search.md` | **只读**操作 |
| 上传 PDF/Word/图片 | `references/files.md` | 二进制文件，非文本文档 |
| 创建 Markdown 文本文档 | `references/writer.md` | 文本内容，非二进制 |
| 「乐享里有一篇关于 X 的文档」 | `references/search.md` → 先搜索 | **必须先检索**，不能直接回答 |
| 「看看乐享里 XX 的写作风格」 | `references/search.md` → 先读取 | **必须先读取内容**，不能凭空分析 |
| 「分析一下我知识库里关于 X 的内容」 | `references/search.md` → 先搜索 | **必须先检索**，不能凭空生成 |

### ⚠️ 跨模块任务

需要同时读取多个文件时，按流程顺序读取：

- **搜索后写入**：先 `references/search.md` → 再 `references/writer.md`
- **读取后编辑**：先 `references/search.md` → 再 `references/blocks.md`
- **上传后记录**：先 `references/files.md` → 再 `references/writer.md`
- **生成内容+保存**：用户要求「帮我写一篇 X 并保存到知识库/个人知识库」→ 先生成内容，再读取 `references/writer.md` 执行保存；若未指定目标，默认写入个人知识库（见 writer.md 中「未指定知识库时写入个人知识库」）

---

## 🔑 凭证检查

执行任何乐享操作前，确认 MCP 已连接。通过 `whoami()` 检查：

```
MCP Tool: whoami
 → 成功：返回用户信息，继续执行
 → 401：读取 references/setup.md，引导续期（点续期按钮，无需重新配置）
 → 连接失败：读取 references/setup.md，引导完成初始配置
```

---

## 📚 参考文件索引

> **按需加载**：根据意图路由表，只 Read 对应文件，无需一次性加载全部。

| 文件 | 职责 |
|------|------|
| `references/setup.md` | Token 配置、续期、WorkBuddy OAuth、故障排查 |
| `references/search.md` | 关键词/语义搜索、内容读取、目录浏览 |
| `references/writer.md` | 新建文档、导入内容、公众号收藏 |
| `references/blocks.md` | 已有页面的 Block 级增删改移 |
| `references/files.md` | 二进制文件上传/下载（三步流程） |
| `references/connectors.md` | 腾讯会议录制导入 |
| `references/smartsheet.md` | 智能表格增删查改、schema 管理 |
| `references/draft.md` | Markdown 草稿保存、发布、管理 |
| `references/comment.md` | 知识页面评论查看 |
| `references/base.md` | 数据模型、完整安全规则、Block 结构、工具发现 |
| `references/index.md` | 完整索引 + 按场景推荐加载顺序 |

### 补充参考文档

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
| `references/skill-maintenance.md` | Skill 维护指南 |

---

> Skill version: **2.2.0**

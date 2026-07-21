---
name: tencent-yunzhi
version: 1.3.0
description: "腾讯乐享（lexiangla.com / csig.lexiangla.com）知识库专用操作。仅在用户消息包含 lexiangla.com 链接、或明确提及『乐享/云知/Lexiang/知识库』关键词时触发。覆盖搜索、创建、编辑、上传、下载、Token 配置。⚠️ 通用『创建文档』『编辑页面』『写文章』『公众号选题』『情感咨询』等无乐享上下文的请求不属于本 Skill 范围，应立即退出。"
description_zh: "腾讯云知（乐享）知识库专用操作 — 仅处理 lexiangla.com 相关请求"
description_en: "Tencent Lexiang knowledge base operations only — strictly scoped to lexiangla.com"
display_name: "腾讯云知"
display_name_en: "Tencent Yunzhi"
visibility: "public"
---

# 腾讯云知 / 乐享知识库 一站式操作

> 仅服务于腾讯乐享（lexiangla.com）知识库的搜索、创建、上传、编辑、下载、配置；自动识别 v1（团队文档）和 v2（知识库）。

---

## ⛔ 适用范围（必须最先判断，命中失败立刻退出）

**本 Skill 仅适用于腾讯乐享（lexiangla.com / csig.lexiangla.com）知识库的操作。**

### ✅ 触发条件（满足任一）
1. 用户消息含 `lexiangla.com` URL
2. 用户明确提及 "乐享 / 云知 / Lexiang / 知识库"，且上下文指向乐享平台
3. 用户已配置 `LEXIANG_TOKEN`，并明确要求 "上传到知识库 / 写入乐享 / 存到云知"

### ❌ 不适用场景（命中即立刻退出 Skill 上下文）

| 场景 | 处理方式 |
|---|---|
| 企业微信文档 / 微文档 / 腾讯文档 / 飞书 / Notion / iWiki 自身操作 | 直接退出，不读取任何 module |
| 公众号选题 / 文案创作 / 写作辅助（无乐享上下文） | 直接退出 |
| 情感咨询 / 闲聊 / 答题测验 / 通用问答 | 直接退出 |
| 仅含 "创建文档 / 编辑页面 / 写文章" 等通用动词，**无乐享关键词** | 反问："这是要操作腾讯乐享知识库吗？还是其他平台？" 在确认前不读取任何 module |

### 退出话术（统一模板）

> 这看起来不是乐享（云知）相关的请求。当前 Skill 仅处理 lexiangla.com 知识库操作。我会以普通对话模式继续帮你处理这个问题。

### 关键约束

- 判断为不适用后，**禁止读取 `modules/*.md` 与 `references/*.md`**（避免无意义 token 消耗）
- 禁止在不适用场景下调用任何乐享 MCP 工具或 1.0 REST API
- 退出后以模型本身能力继续对话，不再尝试触发本 Skill

---

## 🔧 环境与认证

### MCP 连接（2.0）

配置文件模板见 `mcp.json`，写入 `~/.workbuddy/mcp.json` 或 `~/.mcporter/mcporter.json`。

### REST API（1.0）

```
API_HOST = https://lxapi.lexiangla.com
```

### Token 通用规则

`lxmcp_` 前缀的 MCP Token **同时适用于** 2.0 MCP 协议和 1.0 REST API：
- MCP：通过 `mcp.json` 中 `headers.Authorization: Bearer lxmcp_xxx` 传递
- REST：直接放 `Authorization: Bearer lxmcp_xxx` HTTP 头

> ⚠️ 乐享使用 **Bearer Token 静态鉴权**，不涉及 OAuth。Token 缺失/过期时引导用户访问 `https://lexiangla.com/mcp?company_from=CSIG` 获取或续期。

### 🔒 COMPANY_FROM 默认规则（永久约定，禁止改动）

- **默认值固定为 `CSIG`**，所有 URL / 链接 / 配置场景都默认拼接 `?company_from=CSIG`
- 仅当用户**明确指定**其他企业时才替换为对应值
- 涉及位置：`mcp.json` URL、Token 获取链接、401 续期链接、诊断报告默认值

> 若用户尚未绑定 Token，标准提示语：
>
> 你尚未绑定乐享（云知）MCP，无法检索知识库。
> 请打开下方链接获取你的 LEXIANG_TOKEN（lxmcp_ 开头）：
> https://lexiangla.com/mcp?company_from=CSIG
> 拿到 Token 后告诉我，我会帮你完成绑定（默认 COMPANY_FROM=CSIG）。

> ⚠️ **绝对禁止**：引导用户在对话中直接粘贴完整 Token 明文。Token 必须由用户自行写入 mcp.json，或由 Skill 写入文件，不在对话流中传递。

---

## 🚥 操作前置门禁（强制）

**任何调用 MCP 工具或 1.0 REST API 的操作之前，按下面顺序执行：**

```
1. 当前 session 是否已通过健康检查？
   ├─ 已通过（缓存了 company_domain）→ 直接执行业务
   └─ 未通过 → Step 2

2. 调用 MCP whoami() （只读，无副作用）
   ├─ ✅ 成功 → 缓存 user.name + company.company_domain，本 session 后续不再检查
   ├─ ❌ 401 → 走「Token 已过期」分支，禁止重试业务
   ├─ ❌ 工具不存在 / 连接超时 → 走「连接故障诊断」分支（见 modules/setup.md Step 5）
   └─ ❌ 其他错误 → 输出错误码 + 建议，不重试

3. 健康检查未通过时：不要执行任何写入操作；读取类操作仅在用户明确允许"先看看再说"时尝试
```

---

## 🚦 路由规则

### 第零步：先过 Scope 守门（见上方"适用范围"），通过后才进入路由

### 第一步：URL 版本判断

当用户消息中包含 `lexiangla.com` 链接时，**优先**按 URL 路径判断版本：

| URL 特征 | 版本 | 说明 |
|----------|------|------|
| `/teams/{code}` 或 `/teams/{code}/docs` 或 `/teams/{code}/docs/{doc_id}` | **v1** | 团队文档区（1.0 REST API） |
| `/t/{team_id}/spaces` | **v2** | 团队知识库列表（2.0 MCP） |
| `/spaces/{space_id}` | **v2** | 知识库（2.0 MCP） |
| `/pages/{entry_id}` | **v2** | 知识库页面（2.0 MCP） |

**一句话规则**：`/teams/` → v1，`/t/` + `/spaces/` + `/pages/` → v2。

### 第二步：路由决策图

```
USER MESSAGE
    │
    ├─ Scope 守门未通过? ─── YES ──→ ❌ 退出 Skill
    │
    ├─ 含 lexiangla.com URL? ──── YES ──→ 健康检查 → 按 URL 模式路由
    │                                       /teams/.../docs/{doc_id}
    │                                         ├─ 获取正文 → GET /cgi-bin/v1/docs/{doc_id}/parsed-content
    │                                         ├─ 上传/编辑/删除 → modules/v1-docs.md
    │                                         └─ 上传图片 → modules/v1-assets.md
    │                                       /t/{id}/spaces 或 /spaces/{id}
    │                                         ├─ 上传文件 → modules/files.md
    │                                         ├─ 创建/导入 → modules/writer.md
    │                                         └─ 浏览/搜索 → modules/search.md
    │                                       /pages/{entry_id}
    │                                         ├─ 修改/编辑 → modules/blocks.md
    │                                         ├─ 上传文件 → modules/files.md
    │                                         ├─ 追加内容 → modules/writer.md（import_to_entry）
    │                                         ├─ 获取正文 → MCP entry_describe_ai_parse_content(entry_id)
    │                                         └─ 阅读/查看 → modules/search.md
    │
    └─ 不含 URL 但通过 Scope 守门 ──→ 健康检查 → 按意图关键词路由（见下表）
```

### 不含 URL 时的意图 → 模块映射

| 意图关键词 | 模块 |
|-----------|------|
| 配置、连接、setup、token、401、过期、切换企业、未绑定 | `modules/setup.md` |
| 搜索、查找、找、看看、阅读、浏览、打开、有没有 | `modules/search.md` |
| 获取详细内容、解析内容、查看正文、读取文档内容、提取文字 | 见下方「文档内容获取规则」 |
| 创建、新建、写、写入、导入、保存到、发到乐享 | `modules/writer.md` |
| 修改、编辑、更新、改、调整排版、追加、插入、删掉段落 | `modules/blocks.md` |
| 上传文件、传 PDF/Word/Excel/PPT/图片、下载文件 | `modules/files.md` |
| 会议录制、会议纪要、导入会议、iWiki、迁移文档 | `modules/connectors.md` |
| 明确说 "1.0 接口" / "v1" + 文档操作 | `modules/v1-docs.md` |
| 明确说 "1.0 接口" / "v1" + 图片 | `modules/v1-assets.md` |

无法判断时：反问用户目标。**禁止猜测目标知识库或目录。**

---

## ⚠️ 通用规则

### 团队 ID 转换

1.0 REST API 的 `team_id` 参数需要 **UUID 格式**，不能直接用 URL 中的 code（如 `k100684`）。
转换方法：调用 MCP `team_describe_team(team_id="k100684")` → 返回 `team.id`（UUID）。

### URL 中 node 参数

`/teams/{code}/docs?node={node_id}` 中的 `node` 是目标文件夹 ID，上传时作为 `directory.data.id` 传入。

### 结果链接生成

- v2 页面：`https://{domain}/pages/{entry_id}`
- v1 文档：`https://{domain}/teams/{team_code}/docs/{doc_id}`
- `{domain}` 从健康检查缓存的 `company.company_domain` 获取，默认 `csig.lexiangla.com`

### 写入安全约束

- 写入操作**必须**基于用户明确提供的目标信息
- 不要自行猜测目标知识库 / 目录
- 删除操作需二次确认
- **写入失败必须落本地降级文件**（详见 modules/writer.md「写入降级方案」）

### 批量内容获取：合并执行策略

当需要批量获取多篇文档内容时（如遍历目录、生成报告/大纲等），**必须**将多步操作合并到尽可能少的命令中执行：

1. **一次性脚本优先**：把「获取列表 → 判断类型 → 下载文件 → 解析内容」串联到一个 shell/python 脚本中一次执行
2. **循环合并**：用 `for` 循环批量处理同类操作
3. **减少交互次数**：目标整个流程 **不超过 2~3 次命令执行**
4. **`requires_approval: false`**：对读取类操作（curl GET、markitdown 解析等）设置不需要审批；写入/删除仍需审批

参考可直接执行脚本：`scripts/batch-fetch.py`（v1.3.0 新增）。

### 跨版本内容获取降级策略（文档内容获取规则）

**当用户提到「获取文档详细内容 / 解析内容 / 查看正文 / 读取文档」时，按 URL 类型路由：**

```
┌────────────────────────────────────────────────────────────────────┐
│ 1. URL 含 /teams/.../docs/{doc_id} → 1.0 文档                      │
│    必用：GET /cgi-bin/v1/docs/{doc_id}/parsed-content              │
│    → 直接返回 data.attributes.parsed_content（已解析 Markdown）    │
│    → 富文本 / PPTX / DOCX / PDF 全支持，含图片描述 + OCR 结果      │
│    → 一次调用搞定，无需下载 + 本地解析                             │
│    → 详见 references/api-get-doc-parsed-content.md                 │
│                                                                    │
│ 2. URL 含 /pages/{entry_id} → 2.0 文档                             │
│    必用：MCP entry_describe_ai_parse_content(entry_id)             │
│    → 返回 AI 解析后的 HTML / Markdown / OCR 内容                   │
│                                                                    │
│ 3. 兜底（仅以下场景才用旧的 GET /cgi-bin/v1/docs/{doc_id}）：      │
│    ├─ 需要原始 HTML 结构（保留 block 标签等）                      │
│    ├─ 需要下载原始文件二进制（pptx / pdf 本身）                    │
│    └─ parsed-content 接口异常时降级使用                            │
└────────────────────────────────────────────────────────────────────┘
```

> ⚠️ v1 的 `doc_id` 与 v2 的 `entry_id` **不通用**。从 `/teams/` URL 取到的 ID 必须走 v1 接口；从 `/pages/` URL 取到的 ID 必须走 v2 MCP。

### 常见错误速查

| 错误 | 处理 |
|------|------|
| 401 | Token 过期 → 引导用户访问 `https://lexiangla.com/mcp?company_from=CSIG` 续期 |
| 403 | COS 签名过期（上传场景）→ 重新执行 apply_upload |
| 404 | 文档/条目不存在或无权限 → 确认 ID 正确 |
| `_mcp_fields` | 所有 MCP 工具均支持此参数，按需选择返回字段以减少 token |
| 参数不确定 | 执行 `get_tool_schema(tool_name="xxx")` 获取最新定义 |

---

## ✍️ 输出风格约束

### 内容生成场景（写文章 / 整理资料 / 创建文档）

**禁止**：
- 模板化开头："好的，我来帮你..." / "以下是为你整理的..." / "希望对你有帮助..."
- 模板化结尾："希望对你有帮助" / "如有需要请告诉我" / "下一步可以..."
- 主动添加未要求的章节（"延伸阅读" / "作者后记" / "免责声明" 等）
- 在用户没要求的情况下加 emoji 装饰
- 把用户的第一人称改成第三人称，或反之

**必须**：
- 直接产出核心内容，让用户能直接复制使用
- 保留用户提供的格式、语气、人称
- 用户没指定结构时，**镜像参考材料的结构**而非另起炉灶
- 数字、专有名词、产品名按用户原样保留

### 工具操作场景（搜索 / 上传 / 编辑）

**禁止**：
- 在工具调用前后加大段解释（"现在我将调用 xxx 工具，它的作用是..."）
- 把工具返回的原始 JSON 直接贴给用户

**必须**：
- 工具调用前最多一句话说明，工具返回后只展示用户关心的字段
- 多步操作用编号列表汇总最终结果，不复述每一步

---

## 📦 模块索引

路由判定完成后，读取对应模块文件获取详细操作指南：

| 模块 | 文件 | 功能 | 通道 |
|------|------|------|------|
| 配置向导 | `modules/setup.md` | MCP 配置/连接验证/故障排查/Token 管理 | — |
| 搜索阅读 | `modules/search.md` | 关键词/语义搜索、知识库浏览、目录导航、文档读取 | v2 MCP |
| 文档写入 | `modules/writer.md` | 创建文档/页面/文件夹、Markdown/HTML 导入、**写入降级** | v2 MCP |
| 页面编辑 | `modules/blocks.md` | Block 级增删改移、批量编辑、Markdown 转 Block | v2 MCP |
| 文件管理 | `modules/files.md` | 文件三步上传/下载/更新/同步、**上传降级** | v2 MCP |
| 外部导入 | `modules/connectors.md` | 腾讯会议录制导入、iWiki 文档迁移 | v2 MCP |
| 1.0 文档 | `modules/v1-docs.md` | 文档 CRUD（创建/查询/编辑/上传/删除） | v1 REST |
| 1.0 图片 | `modules/v1-assets.md` | 图片上传/下载 | v1 REST |

### 模块间协作

| 场景 | 主模块 | 辅助 |
|------|--------|------|
| 上传文件到知识库（需先找 entry_id） | files | search |
| 编辑已有页面（需先读 block 结构） | blocks | search |
| 上传到 1.0 团队目录（需 UUID 转换） | v1-docs | search（team_describe_team） |
| 创建含图片的富文本文档 | v1-docs | v1-assets（先上传图片） |
| **获取 v1 文档内容（/teams/.../docs/）** | `references/api-get-doc-parsed-content.md`（GET parsed-content） | — |
| **获取 v2 页面内容（/pages/）** | search（`entry_describe_ai_parse_content`） | — |

---

## 参考文档

| 文档 | 说明 |
|------|------|
| `references/common-errors.md` | 常见错误排查 |
| `references/block-schema.md` | Block 类型完整说明 |
| `references/mcp-examples.md` | 复杂 Block 结构示例 |
| `references/markdown-to-block.md` | Markdown 转 Block 指南 |
| `references/block-update.md` | 批量更新 Block 方法 |
| `references/content-reorganize.md` | 文档结构重组 |
| `references/theme-config.md` | 主题配置 |
| `references/doc-templates.md` | 文档模板 |
| `references/markdown-import.md` | Markdown 导入详解 |
| `references/folder-sync.md` | 文件夹同步方案 |
| `references/api-*.md` | 1.0 REST API 各接口详细文档 |
| `references/api-get-doc-parsed-content.md` | **1.0 文档解析内容接口（推荐获取正文用）** |
| `references/examples.md` | 1.0 端到端完整示例 |

## 辅助资源

| 资源 | 说明 |
|------|------|
| `assets/lexiang-block-schema.json` | Block Schema JSON 定义 |
| `assets/examples/` | Block 结构示例文件 |
| `assets/themes/` | 主题配置文件 |
| `scripts/docs-v1.py` | 1.0 文档 CLI 工具 |
| `scripts/assets-v1.py` | 1.0 图片 CLI 工具 |
| `scripts/upload-files.py` | 批量文件上传脚本 |
| `scripts/sync-folder.ts` | 文件夹增量同步 |
| `scripts/batch-fetch.py` | **批量获取文档内容（v1.3.0 新增）** |

---

## 变更记录

- **v1.3.0**（2026-05-28）
  - 新增「适用范围」章节（Scope 守门），未命中乐享上下文立刻退出
  - 收紧 frontmatter description（加否定式约束）
  - 新增「操作前置门禁」：所有 MCP/REST 操作前强制健康检查
  - 新增「输出风格约束」节，禁止模板化开头/结尾、AI 味装饰
  - setup.md 加 Step 5 结构化诊断报告，替代反复重试
  - writer.md / files.md 加写入/上传降级方案（落本地文件）
  - 路由规则改为 ASCII 决策图
  - version 号合规化（去掉 V 前缀）
  - 新增 `scripts/batch-fetch.py`
  - 全文强化 COMPANY_FROM=CSIG 默认约定

---
name: bazhuayu-skill
description: 八爪鱼云采集 MCP 技能 - 搜索模板、启动与管理任务、查询进度、导出结构化数据
version: "1.0.0"
author: "Bazhuayu / 八爪鱼"
---

# 八爪鱼 Connector Skill

本 Skill 指导 AI 在 WorkBuddy 中正确使用「八爪鱼」MCP 连接器。

**鉴权方式为 OAuth（浏览器授权）**。除非 OAuth 失败且客户端明确要求其它方式，否则不要向用户索要 API Key。

## 首发工具范围

本连接器仅暴露以下 6 个工具：

| 工具 | 用途 |
|------|------|
| `search_templates` | 发现或精确解析云采集模板 |
| `execute_task` | 创建并启动云采集（单次最多等待约 45 秒） |
| `get_task_status` | 查询标准化状态 / 已采集行数 / 批次号 |
| `export_data` | 读取某一采集批次的一页 JSON 数据 |
| `search_tasks` | 在当前授权账号下查找已有任务 |
| `start_or_stop_task` | 启动或停止已有任务 |

**不要**编造其它工具名（无优惠券、电商专用、平台内容搜索等工具）。

## 推荐工作流

1. **发现模板**：用 `search_templates` 的语义 `query`（写清站点 + 数据类型 + 采集意图）。
2. **补全 Schema（需要时）**：用精确 `id` 或 `slug` 再调 `search_templates`，拿到完整 `inputSchema` / `sourceTree`。
3. **启动任务**：`execute_task` 传入 `templateName` + `parameters`（JSON 对象字符串）。强烈建议带唯一 `taskName`。
4. **若仍在运行**：用 `taskId` 调 `get_task_status` 轮询至 `completed` 或 `stopped`（不要无限卡在一次调用上）。
5. **读数据**：`export_data` 传入 `taskId` + `lotNo`（来自 execute/status），用 `page` / `pageSize` 分页。
6. **管理已有任务**：先 `search_tasks`，再 `start_or_stop_task` 或 `export_data`。

## 鉴权说明

- 用户连接本 Connector 时，由 WorkBuddy 自动完成 OAuth。
- 所有工具都需要有效用户会话；未登录会返回 401 及 OAuth 发现信息。
- 若长时间闲置后出现 unauthorized / invalid_token，引导用户**重新连接**本连接器（refresh_token 可能已过期）。
- 禁止在对话、日志示例中输出 access token。

## 工具说明

### `search_templates` — 搜索模板

用户要抓取 / 采集 / 抽取网页数据、需要云模板时使用。

**每次调用只能选一种选择器：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `query` | string | 三选一 | 语义搜索：完整描述站点、数据与采集意图 |
| `id` | number | 三选一 | 按模板 ID 精确查询 |
| `slug` | string | 三选一 | 按模板 slug / 别名精确查询 |
| `limit` | number | 否 | 仅可与 `query` 同用；1–20，默认 10 |

**规则：**

- 优先选 `score` 高、且支持云端执行（`executionMode`）的模板。
- 语义搜索后，若需要完整 `inputSchema` 与 `sourceTree` 再执行任务，请用 `id` 或 `slug` 精确查询。
- 不要传已废弃参数 `keyword`、`page`。

**示例：**

- 语义：`query` = 「亚马逊美国站无线耳机搜索结果 商品标题 价格」
- 精确：`id` = 12345

---

### `execute_task` — 启动云采集

创建任务并启动云端运行，最多等待约 45 秒返回进度快照。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `templateName` | string | 是 | 来自 `search_templates` 的模板名 |
| `parameters` | string（JSON 对象） | 否 | key 使用 `inputSchema[].field`；默认 `{}` |
| `taskName` | string | 否 | 友好且唯一的任务名；强烈建议填写，便于 `search_tasks` 找回 |

**参数类型约定：**

- Input / Dropdown → 字符串
- MultiInput / CheckboxList → 字符串数组（即使只有一个值）
- 依赖 source 的字段 → 传精确查询 `sourceTree` 中选项的 `key`；若仍缺依赖，工具返回 `input_required` 与下一层 `sourceOptions`，补全后再次调用（参数未就绪时不会创建任务）

**结果要点：** `taskId`、`lotNo`、`collectedRows`、`status`（`running` / `completed` / `stopped`）。

**规则：**

- `collectedRows` 默认可能为 0；需结合 `status` 区分「仍在跑暂无数据」与「终态无数据」。
- 若担心客户端超时，务必保留 `taskId` / `taskName`，后续用 `get_task_status` / `search_tasks` 续查。
- 在 `export_data`（或大结果 curl 导出）成功前，不要声称数据已全部导出。

---

### `get_task_status` — 查询任务状态

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `taskId` | string | 是 | 来自 `execute_task` 或 `search_tasks` |

**返回：** `status`（`running` / `completed` / `stopped`）、`collectedRows`、可用时的 `lotNo`。

**规则：**

- `running` 时退避轮询，终态停止。
- 同一任务优先用本工具续查，不要重复 `execute_task`。

---

### `export_data` — 导出一页数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `taskId` | string | 是 | 八爪鱼任务 ID |
| `lotNo` | string/number | 是 | 精确批次号（来自 execute/status） |
| `page` | number | 否 | 默认 1 |
| `pageSize` | number | 否 | 默认 20，最大 100 |

**返回：** 当前页 Body（`data`、分页信息等）；数据量大时可能含 `directAccess`（签名 URL / `curlTemplate`）——大结果优先用 curl，避免占满模型上下文。

---

### `search_tasks` — 搜索已有任务

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `page` | number | 否 | 页码 |
| `size` | number | 否 | 每页条数，默认 10，最大 100 |
| `keyword` | string | 否 | 任务名等关键词 |
| `status` | enum | 否 | `Running` / `Stopped` / `Completed` / `Failed` |
| `taskIds` | string[] | 否 | 指定任务 ID 列表，最多 100 |

用户提到已有任务但没有 `taskId` 时，先用本工具再导出或启停。

---

### `start_or_stop_task` — 启停任务

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `taskId` | string | 是 | 已有任务 ID |
| `action` | enum | 是 | `start` 或 `stop` |

**规则：**

- 对未在运行的任务执行 `stop`，可能返回成功且状态为 `already_stopped`。
- `start` 可能因积分、权限、模板不可用、限流失败——直接展示工具返回说明，不要盲目重试。
- 可能的情况下先查状态，再决定是否 start。

## 错误处理

| 情况 | 处理建议 |
|------|----------|
| 401 / invalid_token | 请用户重新连接本 Connector（OAuth） |
| `execute_task` 返回 `input_required` | 按返回补参数 / source 选项后重试 |
| 模板找不到 | 放宽 `query` 或改用精确 id/slug |
| execute 后仍为 `running` | 轮询 `get_task_status`，不要编造已完成 |
| 积分不足 / 权限不足 | 展示工具原文；勿盲目重试 |
| `export_data` 为空 | 核对 `lotNo`、任务状态与页码 |
| 长采集超时 | 用 `taskId` / `taskName` 恢复，继续轮询状态 |

## 回复风格

- 进度更新宜短，突出 `taskId`、`lotNo`、行数等关键字段。
- 若已有 `directAccess.curlTemplate`，不要把超大 `data` 数组整段贴进对话。
- 若界面已展示列表，口头摘要即可，不必逐条重复。

## 相关链接

- 产品站：https://www.bazhuayu.com  
- 托管 MCP：https://mcp.bazhuayu.com  

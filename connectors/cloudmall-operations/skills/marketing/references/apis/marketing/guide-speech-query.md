# 营销域 — 导购话术查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-content-flow.md`
> 话术库：运营编辑多条内容块话术，按分组管理，供导购在工作台查阅/分享（分享计数存于缓存计数器）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide-speech.search 话术分页（groupId 不含子分组） · guide-speech.detail 话术详情（内容块列表） · guide.speech.export 话术异步导出（返回任务 ID）
> 写操作见 `guide-speech-action.md`。

---

## ⛔ 未开放端点

| 端点 | 未开放理由 |
|------|-----------|
| 话术批量操作旧入口（batch-operate） | 后端已废弃，仅剩导出场景兼容；改分组/删除请用上方 `batch-update-group` / `batch-delete`，导出走 `guide.speech.export`。**Catalog 未登记该废弃入口，不推测能力标识** |

---

## ✅ 话术分页 — `ops.marketing.guide-speech.search`

- **说明**：按分组/关键词/ID 分页查询；排序规则：置顶优先 → 置顶时间倒序 → 创建时间倒序；每行带分享次数（Redis 计数）与分组名。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| groupId | String | 否 | 分组 ID（精确匹配，含子分组需逐个查询——注意与内容素材列表的「含子分组」语义不同） |
| keyword | String | 否 | 标题模糊匹配 |
| id | String | 否 | 精确指定话术 ID |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 更新/删除/分享计数/置顶 的路径 ID）、`records[].groupId`（→ 分组树/批量改组）
- **格式敏感字段**：`updatedTime`（yyyy-MM-dd HH:mm:ss）、`shareCount`/`contentBlockCount`（整数）、`isTop`（Boolean，是否置顶）
- **关键字段**：`scopeSummary`（适用范围摘要文本）、`groupName`（分组名，未分组为空串）

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.search","input":{"pageNum":1,"pageSize":20,"groupId":"5200000000000000001","keyword":"开场白"},"summary":"查询分组下含开场白的话术"}
```

---

## ✅ 话术详情 — `ops.marketing.guide-speech.detail`

- **说明**：返回话术主体 + 内容块文本列表（按排序号升序）+ 适用范围（含富化名称）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 话术 ID |

### 出参（原始数据）

- **关键字段**：`contentBlocks`（String[]，内容块文本按序排列）、`scope`（范围对象：userTag/user/store/guide 各为 `{type: all|specified, ids, names}`）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）、`shareCount`（整数）

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.detail","input":{"id":"5300000000000000001"},"summary":"查看话术完整内容"}
```

---

## ✅ 话术导出 — `ops.marketing.guide.speech.export`

- **说明**：按筛选条件异步导出话术。返回**导出任务 ID**，用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载。筛选条件结构同 `ops.marketing.guide-speech.search`。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （筛选条件） | object | 否 | 结构同话术分页查询（title/groupId 等） |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.guide.speech.export","input":{"pageNum":1,"pageSize":20},"summary":"导出全部话术"}
```

---

# 商户域 — 渠道配置查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-channel.md`；写操作见 `channel-config-action.md`。
> 渠道配置为三层结构：一级渠道（如「抖音」）→ 二级（如「直播带货」）→ 三级；分页与下拉均为 JSON 请求体。出参为上游**原始业务数据**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：channel-config.search 渠道配置分页 · channel-config.select 渠道级联下拉

---

## ✅ 渠道配置分页 — ops.merchant.channel-config.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| firstLevelName | String | 否 | 一级渠道名称筛选 |
| secondLevelName | String | 否 | 二级渠道名称筛选 |
| thirdLevelName | String | 否 | 三级渠道名称筛选 |
| startCreatedTime / endCreatedTime | Integer | 否 | 创建时间区间（**13 位毫秒时间戳**，数字） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 批量删除/级联选择的节点 id）、`records[].nextChannelLevelList[].id`
- **枚举字段**：`channelLevel`（1/2/3，整数层级）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.channel-config.search","input":{"pageNum":1,"pageSize":20,"firstLevelName":"抖音"},"summary":"查询抖音渠道配置"}
```

---

## ✅ 渠道级联下拉 — ops.merchant.channel-config.select

- **语义**：按层级/父节点过滤渠道节点（级联选择器数据源）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| parentId | String | 条件 | 父节点ID；**parentId 与 parentIds 必传其一**（否则服务端报「上级渠道ID不能为空」）；查一级渠道传 `"0"` |
| parentIds | String[] | 条件 | 父节点ID列表（与 parentId 二选一） |
| channelLevel | Integer | 否 | 层级：1/2/3 |
| channelName | String | 否 | 渠道名称过滤 |

### 出参（数组）

结构同分页记录（id/channelName/channelLevel/parentId/nextChannelLevelList）。

### 调用示例

```json
{"capability":"ops.merchant.channel-config.select","input":{"parentId":"0","channelLevel":1},"summary":"列出全部一级渠道"}
```

---

## ⛔ 未开放

| 操作 | 原因 |
|------|------|
| 渠道明细批量查询（batch-detail） | 内部批量回填辅助面，select 已覆盖选择场景 |

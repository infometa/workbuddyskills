# 商户域 — 渠道追踪查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-channel.md`；写操作见 `channel-trace-action.md`；渠道配置字典见 `channel-config-query.md` / `channel-config-action.md`。
> 覆盖投放渠道活码/追踪配置（渠道追踪单）与明细查询（触达/行为数据）。出参为上游**原始业务数据**（不裁剪字段）。
> **核心模型**：渠道追踪单（ChannelTrace）= 一次投放的追踪配置（推广名称/渠道类型/投放页面/层级归因）；自定义渠道（custom-channel）扩展渠道类型字典；明细（channel-trace-detail）按追踪单查询触达与会员行为。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：channel-trace.list 追踪单分页 · channel-trace.detail 追踪单详情 · channel-trace.custom-channels 自定义渠道字典 · channel-trace.export 渠道追踪导出 · channel-trace-detail.list 追踪明细查询 · channel-trace-detail.member-behaviors 会员行为查询

---

## ✅ 追踪单分页 — ops.merchant.channel-trace.list

- **说明**：POST + json-body 查询（分页筛选）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | 否 | 分页 |
| pushName | String | 否 | 推广名称筛选 |
| pageName | String | 否 | 投放页面名称筛选 |
| pushPageType | Integer | 否 | 投放页面类型 |
| channelType | Integer | 否 | 渠道类型 |
| useStatus | Integer | 否 | 使用状态 |
| startCreatedTime / endCreatedTime | Long | 否 | 创建时间窗（**毫秒时间戳**） |
| startUpdatedTime / endUpdatedTime | Long | 否 | 更新时间窗（**毫秒时间戳**） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 详情/编辑/状态路径参数）
- **展示字段**：`pushName`、`channelType`、`useStatus`、`updatedBy`、时间字段（以响应为准）

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.list","input":{"pageNum":1,"pageSize":20},"summary":"看下当前的渠道投放追踪单"}
```

---

## ✅ 追踪单详情 — ops.merchant.channel-trace.detail

- GET /{id}。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 追踪单 ID |

### 出参（原始数据）

追踪单完整配置（以响应为准）。

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.detail","input":{"id":"7700012345678901234"},"summary":"看这条追踪单的完整配置"}
```

---

## ✅ 自定义渠道字典 — ops.merchant.channel-trace.custom-channels

- GET，无入参；add/edit 的 channelType 取值来源。

### 出参（数组，原始数据）

- `List<CustomChannelVO>`（自定义渠道字典——add/edit 的 channelType 取值映射）。

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.custom-channels","input":{},"summary":"看下有哪些自定义渠道类型"}
```

---

## ✅ 渠道追踪导出 — ops.merchant.channel-trace.export

- POST + json-body。

### 入参

同 list 筛选条件。

### 出参（原始数据）

- `Result<String>`（导出文件下载信息——以响应为准，转告用户）。

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.export","input":{"pageNum":1,"pageSize":20},"summary":"导出渠道追踪单列表"}
```

---

## ✅ 追踪明细查询 — ops.merchant.channel-trace-detail.list

- **说明**：按追踪单/时间窗分页查询触达明细数据；list 为 POST + json-body。
- **注意**：**无追踪单 ID 筛选字段**——按 `pushName`（推广名称，**精确匹配**）定位目标追踪单的明细；先通过 `channel-trace.detail` 获取 pushName 再传入。其余筛选：storeName/department/employee/memberBehaviorIdList/scanStartTime/scanEndTime（毫秒）/channelType/一~五级渠道名。

### 入参

分页 + 上述筛选字段。

### 调用示例

```json
{"capability":"ops.merchant.channel-trace-detail.list","input":{"pushName":"双11朋友圈投放","pageNum":1,"pageSize":20},"summary":"看下双11投放的扫码明细"}
```

---

## ✅ 会员行为查询 — ops.merchant.channel-trace-detail.member-behaviors

- **说明**：**无入参**，返回会员行为类型**枚举字典**（memberBehaviorId + memberBehavior 描述），供 `channel-trace-detail.list` 的 `memberBehaviorIdList` 参数取值。不是行为数据查询。

---

## ⛔ 未开放（渠道追踪）

| 操作 | 不开放理由 |
|------|-----------|
| 导入模板下载（import/template） | 二进制文件流响应；产品决策仅开放 URL 型导出，模板从管理后台获取 |

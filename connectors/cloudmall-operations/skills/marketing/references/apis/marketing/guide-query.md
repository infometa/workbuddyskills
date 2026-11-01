# 营销域 — 导购管理查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-flow.md`
> 覆盖导购主档 CRUD、状态流转、导购维度统计（月度/总量/趋势）与操作日志。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide.search 导购分页列表（不传 status 含已归档） · guide.stats 导购各状态数量统计 · guide.detail 导购详情（完整档案） · guide.customers 导购关联客户列表（生效中） · guide.operation-logs 导购操作日志（审计） · guide.month-stats 导购月度统计（本月新增客户口径） · guide.performance 导购历史全量业绩（总客户口径） · guide.sales-trend 导购近 5 天销售趋势 · guide.export 导购数据异步导出（返回任务 ID）
> 写操作见 `guide-action.md`。

---

## 导购状态机（写操作前置判定）

```
create ──▶ pending（待激活）── 导购端小程序激活 ──▶ active（在职）
active ── disable ──▶ disabled（已停用）── enable ──▶ active
disabled ── archive ──▶ archived（已归档，终态，无恢复端点）
```

- `pending`：后台新增后的初始状态；本期运营端无激活端点（激活由导购端完成），列表中可能长期存在待激活记录。
- `active`：唯一可停用的状态；停用必须同时指定客户转移方式（见 disable）。
- `disabled`：可启用（恢复在职）或归档。
- `archived`：终态——不可再启用、不可编辑恢复；等级删除等场景会忽略归档导购。

---

## 客户转移方式（停用导购时二选一必填）

| 取值 | 语义 |
|------|------|
| `admin_assign` | 指定导购转移：该导购全部客户转给 `targetGuideId`（必填），新关系为专属导购 |
| `public_pool` | 全部客户解绑并进入公共客户池 |
| `store_round_robin` | 同门店在职导购按客户维度哈希轮询分配；同门店无其他在职导购时客户进入公共池 |

---

## ⛔ 未开放端点

| 端点 | 不开放理由 |
|------|-----------|
| 导入模板下载（Excel 文件流） | 二进制文件下载，超出工具返回契约；模板列结构以运营端页面下载为准 |

---

## ✅ 导购分页列表 — `ops.marketing.guide.search`

- **说明**：按关键词（姓名或手机号模糊匹配）、状态、门店、等级筛选，按创建时间倒序。注意：**不传 status 时会包含已归档导购**（后端未做默认排除），需要排除归档时请显式传 status。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| keyword | String | 否 | 姓名/手机号模糊搜索，≤50 字符 |
| status | String | 否 | `pending`/`active`/`disabled`/`archived` |
| storeId | String | 否 | 门店 ID |
| levelId | String | 否 | 等级 ID |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 详情/编辑/启停/归档/关联客户/操作日志/统计 的路径 ID）
- **枚举字段**：`status`（见上方状态机）、`gender`（0-未知/1-男/2-女）
- **格式敏感字段**：`monthlySales`（本月销售额，**单位元**，两位小数）、`joinTime`/`createdTime`（yyyy-MM-dd HH:mm:ss）
- **脱敏字段**：`phone`（完整）/`phoneMasked`（脱敏）两个字段并存，展示优先用 `phoneMasked`

### 调用示例

```json
{"capability":"ops.marketing.guide.search","input":{"pageNum":1,"pageSize":20,"keyword":"李明","status":"active"},"summary":"按姓名搜索在职导购"}
```

---

## ✅ 导购状态统计 — `ops.marketing.guide.stats`

- **说明**：导购列表页顶部统计卡片，一次返回各状态数量。

### 入参

无（空对象）。

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| totalCount | 导购总数（四状态之和） |
| activeCount | 在职数 |
| pendingCount | 待激活数 |
| disabledCount | 已停用数 |
| archivedCount | 已归档数 |

### 调用示例

```json
{"capability":"ops.marketing.guide.stats","input":{},"summary":"查询导购各状态数量"}
```

---

## ✅ 导购详情 — `ops.marketing.guide.detail`

- **说明**：返回单个导购完整档案；导购不存在时报错。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID |

### 出参（原始数据）

- **枚举字段**：`status`（见上方状态机）、`gender`（0-未知/1-男/2-女）
- **格式敏感字段**：`joinTime`/`lastActiveTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- **脱敏字段**：`phone`（完整）/`phoneMasked`（脱敏）并存

### 调用示例

```json
{"capability":"ops.marketing.guide.detail","input":{"id":"5100000000000000001"},"summary":"查询导购详情"}
```

---

## ✅ 导购关联客户列表 — `ops.marketing.guide.customers`

- **说明**：该导购当前**生效**的绑定关系，按绑定时间倒序。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].relationId`（→ 关系释放的路径 ID）、`records[].uid`（→ 客户画像/行为轨迹路径参数）
- **枚举字段**：`relationType`（share_guide-共享导购/exclusive_guide-专属导购）、`bindMethod`（share_bind-分享绑定/upgrade_exclusive-升级专属/customer_switch-客户换绑/nearest_store-就近门店归属/store_round_robin-门店轮流分配/admin_assign-运营指定）
- **格式敏感字段**：`bindTime`/`expireTime`（yyyy-MM-dd HH:mm:ss；`expireTime` 为 null 表示永久）

### 调用示例

```json
{"capability":"ops.marketing.guide.customers","input":{"id":"5100000000000000001","pageNum":1,"pageSize":20},"summary":"查看导购名下客户"}
```

---

## ✅ 导购操作日志 — `ops.marketing.guide.operation-logs`

- **说明**：导购主档操作审计记录，按创建时间倒序。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- **枚举字段**：`operationType`（create-新增/update-编辑/transfer_store-调店/enable-启用/disable-停用/archive-归档/level_change-等级变更/auto_promote-自动晋级）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）、`beforeSnapshot`/`afterSnapshot`（变更前后快照 JSON 字符串——**审计用，无稳定 schema 承诺**：当前 beforeSnapshot 仅 update/调店 流程写入，内部为导购主档 4 键 `{"name","phone","storeId","status"}`；**afterSnapshot 当前恒为 null**，且运营端前端不消费这两个字段）、`operationDetail`（含 IP 信息的描述）

### 调用示例

```json
{"capability":"ops.marketing.guide.operation-logs","input":{"id":"5100000000000000001","pageNum":1,"pageSize":20},"summary":"查看导购操作日志"}
```

---

## ✅ 导购月度统计 — `ops.marketing.guide.month-stats`

- **说明**：导购详情页「本月」维度统计卡片（固定自然月至今，无入参）。

### 入参

仅路径参数（固定统计当前自然月，无查询参数）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID |

### 出参（原始数据）

- **枚举字段**：无
- **格式敏感字段**：`salesAmount`/`promotionAmount`/`avgOrderValue`（**单位元**，两位小数）、环比字段 `salesChangeRate` 等（百分比数值，如 12.5 = 12.5%，正数增长负数下降）
- **口径说明**：`customerCount` 为**本月新增客户数**，`totalCustomerCount` 为总客户数；`promotionAmount` 为分享导购业绩。

### 调用示例

```json
{"capability":"ops.marketing.guide.month-stats","input":{"id":"5100000000000000001"},"summary":"查询导购本月业绩统计"}
```

---

## ✅ 导购总量业绩 — `ops.marketing.guide.performance`

- **说明**：导购维度历史全量业绩（不受时间范围限制）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID |

### 出参（原始数据）

- **格式敏感字段**：`salesAmount`/`promotionAmount`/`avgOrderValue`（**单位元**，两位小数）
- **口径说明**：此处 `customerCount` 为**总客户数**（与月度接口口径不同）。

### 调用示例

```json
{"capability":"ops.marketing.guide.performance","input":{"id":"5100000000000000001"},"summary":"查询导购历史总业绩"}
```

---

## ✅ 导购近 5 天销售趋势 — `ops.marketing.guide.sales-trend`

- **说明**：固定返回近 5 天（含今天）逐日销售额，缺数日期自动补 0。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID |

### 出参（数组，原始数据）

- **格式敏感字段**：`date`（yyyy-MM-dd）、`value`（当日销售额，**单位元**）、`changeValue`（环比差值，元）、`changeRate`（环比百分比，如 12.5 = 12.5%）

### 调用示例

```json
{"capability":"ops.marketing.guide.sales-trend","input":{"id":"5100000000000000001"},"summary":"查看导购近5天销售额趋势"}
```

---

## ✅ 导购数据导出 — `ops.marketing.guide.export`

- **说明**：按筛选条件异步导出导购数据。返回**导出任务 ID**，随后用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载（时效以任务查询返回为准）。筛选字段：keyword / status / storeId / levelId / ids；导出为**非幂等操作**（重试创建重复任务）。**导出内容含手机号等明文 PII，转述需打码、交付提醒保管。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （筛选条件） | object | 否 | keyword / status / storeId / levelId / ids 等筛选字段（导出无分页参数，服务端固定分批拉取） |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.guide.export","input":{},"summary":"导出当前筛选条件下的导购清单"}
```

---

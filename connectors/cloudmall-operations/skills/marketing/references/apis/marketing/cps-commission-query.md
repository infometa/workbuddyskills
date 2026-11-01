# 营销域 — CPS 佣金率查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-distributor-flow.md`
> 佣金率是**小数比例**：`0.1213` 表示 12.13%，取值范围 `[0.0000, 1.0000]`（最大即 100%）——**不是**百分比数字。
> 佣金命中为四级优先级：**商品×分组 > 商品定向（全局组）> 分组默认 > 全局默认**；定向佣金一旦设置，该商品即按定向率结算。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-commission.global-rate 查询全局默认佣金率（未设置返回 0） · cps-commission.goods-rate 查询商品定向佣金率（null=未设置） · cps-commission.global-group-rates 查询全局分组佣金率（全量，含回填） · cps-commission.goods-group-rates 查询商品分组佣金率（spuId 必填） · cps.order.export 分销订单异步导出（返回任务 ID）
> 写操作见 `cps-commission-action.md`。

---

## 佣金率体系结构

| 层级 | 含义 | 配置能力 |
|------|------|---------|
| 全局默认 | 全租户商品兜底佣金率 | 查询/设置全局佣金率 |
| 分组默认（全局维度） | 某分组下分销员推广**任意商品**的默认率 | 查询：全局分组佣金率；写入：批量重置商品分组佣金 `spuIds=["0"]` |
| 商品定向（全局组） | 某**具体商品**对所有分销员的定向率 | 查询单品率/批量重置定向/批量取消定向 |
| 商品×分组 | 某具体商品对某分组的专属率（最高优先级） | 批量重置商品分组佣金 |

- 查询分组佣金率时，未单独配置的分组会回填默认率（商品维度查询时回填顺序：商品定向率 → 全局默认率），即**查询结果中的 rate 是「生效值」而非「已配置标记」**。
- 设置商品定向佣金会同步将该商品标记为「定向佣金」类型；批量取消定向会删除该商品的定向率与分组率并回退为「全局佣金」类型。
- 商品×分组佣金的前提是**必须先设置全局佣金**，否则报业务错误。

---

## ⛔ 未开放

无（佣金率体系与订单佣金补算端点均已开放）。

---

## ✅ 查询全局佣金率 — `ops.marketing.cps-commission.global-rate`

- **说明**：查询租户全局默认佣金率；从未设置时返回 0。

### 入参

无（空对象）。

### 出参（原始数据）

- **格式敏感字段**：返回值为小数比例（0.1 = 10%），未设置返回 0。

### 调用示例

```json
{"capability":"ops.marketing.cps-commission.global-rate","input":{},"summary":"查看全局默认佣金率"}
```

---

## ✅ 查询商品定向佣金率 — `ops.marketing.cps-commission.goods-rate`

- **说明**：查询某商品对所有分销员的定向佣金率（全局组维度）；**未设置定向时返回 null**（区别于全局查询返回 0），表示该商品走全局/分组默认。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | 商品 SPU ID |

### 出参（原始数据）

- **格式敏感字段**：返回值为小数比例（0.15 = 15%）；`null` 表示未设置定向佣金。

### 调用示例

```json
{"capability":"ops.marketing.cps-commission.goods-rate","input":{"spuId":"2058365707555589633"},"summary":"查看该商品的定向佣金率"}
```

---

## ✅ 查询全局分组佣金率 — `ops.marketing.cps-commission.global-group-rates`

- **说明**：全量查询各分组的默认佣金率（**不分页**，全量返回）；`groupName` 模糊、`groupId` 精确过滤。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| groupName | String | 否 | 分组名称（模糊） |
| groupId | String | 否 | 分组 ID（精确） |

### 出参（原始数据）

- **路径参数来源**：`[].groupId`（→ 分组佣金写入的 groupId）
- **格式敏感字段**：`[].rate`（生效佣金率，小数比例；未单独配置的分组回填全局默认率）
- 展示型字段：`[].groupName`/`[].memberCount`（分组人数）可透传；`[].id` 为佣金记录 ID，仅该分组已配置时有值。

### 调用示例

```json
{"capability":"ops.marketing.cps-commission.global-group-rates","input":{},"summary":"查看各分组默认佣金率"}
```

---

## ✅ 查询商品分组佣金率 — `ops.marketing.cps-commission.goods-group-rates`

- **说明**：全量查询某商品下各分组的佣金率（**不分页**）；`spuId` 必填。未单独配置的分组回填：商品定向率（若有）→ 全局默认率。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | 商品 SPU ID |
| groupName | String | 否 | 分组名称（模糊） |
| groupId | String | 否 | 分组 ID（精确） |

### 出参（原始数据）

- **路径参数来源**：`[].groupId`
- **格式敏感字段**：`[].rate`（生效佣金率，小数比例）
- 展示型字段：`[].groupName`/`[].memberCount` 可透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-commission.goods-group-rates","input":{"spuId":"2058365707555589633"},"summary":"查看该商品各分组的佣金率"}
```

---

## ✅ 分销订单导出 — `ops.marketing.cps.order.export`

- **说明**：分销订单**异步导出**（含佣金归属的订单维度数据）。返回**导出任务 ID**，用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载。导出为**非幂等操作**（重试会创建重复任务），超时先轮询任务状态。**导出内容含用户手机号等明文 PII，转述需打码、交付提醒保管。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| cpsUid | String | 否 | 分销员 UID（精确；来自 `cps-distributor.search` 出参 uid） |
| distributorKeyword | String | 否 | 分销员 UID 或名称（模糊） |
| groupId | String | 否 | 分销员分组 ID（精确） |
| groupName | String | 否 | 分销员分组名称（模糊） |
| spuId | String | 否 | 商品 SPU ID（精确） |
| orderNo | String | 否 | 订单号（模糊） |
| cpsSettleStatus | Integer | 否 | 分佣结算状态：1 未结算 / 2 结算中 / 3 结算失败 / 4 结算成功 |
| startTime / endTime | String | 否 | 时间范围（yyyy-MM-dd HH:mm:ss）；维度由 timeType 决定 |
| timeType | String | 否 | 时间维度：`created`（默认，下单时间）/ `pay` / `finish` / `settlement` |

> 入参为交易域 `OrderPageQuery`，服务端强制只导分销订单（cpsOnly=true）；分页参数无需传（服务端固定分批拉取，上限 5 万行），传空对象 `{}` 导出全量分销订单。
> **没有按 CPS 活动（activityId）或"分销员 ID"筛选的字段**——未登记字段会被静默忽略并导出全量，按分销员筛选用 `cpsUid`；用户要求按活动导出时说明不支持，可改按时间范围/分销员导出，或用 `cps.settlement.export-by-activity` 导出该活动的结算明细。

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.cps.order.export","input":{"startTime":"2026-10-01 00:00:00","endTime":"2026-10-31 23:59:59"},"summary":"导出本月分销订单"}
```

---

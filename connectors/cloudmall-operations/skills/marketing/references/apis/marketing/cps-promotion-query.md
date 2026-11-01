# 营销域 — CPS 活动推广查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-activity-flow.md`
> **状态机（活动推广，整数字段 activityStatus）**：`0` 未发布 → 发布（按时间窗口落 `1` 未开始 或 `2` 进行中）→ 到达开始时间自动 `1→2` → 到达结束时间自动 `2→3` / 手动结束 `1|2→3`；已发布状态（1/2/3）可取消发布回 `0`。删除**不做状态校验**（任意状态可删）。
> **可执行操作派生（operations）**：0→view/edit/copy/publish/delete；1→view/edit/copy/terminate；2→view/copy/terminate；3→view/copy。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-promotion.search 活动推广分页（状态筛选为中文描述、当前页内存过滤） · cps-promotion.detail 活动推广详情（含商品编排与佣金率范围） · cps-stats.promotion-report 活动推广效果报表（分享/点击/下单/佣金聚合） · cps.data-stats.promotion-details.export 活动推广报表异步导出（返回任务 ID）
> 写操作见 `cps-promotion-action.md`。

---

## ⛔ 未开放

无（活动推广模块全部端点均已开放）。

---

## ✅ 活动推广分页 — `ops.marketing.cps-promotion.search`

- **说明**：分页查询活动推广列表，默认按更新时间倒序。
- **⚠️ activityStatus 筛选是中文描述值**：传 `未发布`/`未开始`/`进行中`/`已结束`（不是数字 0-3）；且该筛选是**当前页内存过滤**——total 仍为过滤前总数，翻页结果可能不连续，精确筛选建议用 id。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| activityName | String | 否 | 活动名称（模糊） |
| activityType | Integer | 否 | 活动类型：1 爆品推广 / 2 平台活动 |
| activityStatus | String | 否 | 活动状态**中文描述**：未发布/未开始/进行中/已结束（当前页内存过滤，慎用） |
| id | Long | 否 | 活动推广 ID（精确，十进制字符串传递） |
| startCreatedTime | String | 否 | 创建时间下限（yyyy-MM-dd HH:mm:ss） |
| endCreatedTime | String | 否 | 创建时间上限（yyyy-MM-dd HH:mm:ss） |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 详情/更新/复制/发布/取消发布/结束/删除的路径参数；也用于报表的 activityId 筛选）
- **枚举字段**：`activityStatusCode`（0 未发布 / 1 未开始 / 2 进行中 / 3 已结束）、`activityType`（1 爆品推广 / 2 平台活动）、`operations`（view/edit/copy/publish/unpublish/terminate/delete 组合，按状态派生）
- **格式敏感字段**：`startTime`/`endTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）；`id`（Long→string）
- **脱敏字段**：无（bannerImg/customBannerImg/shareImg 为 60 分钟有效期预签名地址，非脱敏）

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.search","input":{"pageNum":1,"pageSize":20,"activityName":"爆品","activityType":1,"activityStatus":"进行中"},"summary":"查看进行中的爆品推广活动"}
```

---

## ✅ 活动推广详情 — `ops.marketing.cps-promotion.detail`

- **说明**：查询单个活动推广完整配置；商品编排（selectGoods）会富化商品基础信息与佣金率范围。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | ✅ | 活动推广 ID（十进制字符串） |

### 出参（原始数据）

- **路径参数来源**：`selectGoods.goodsList[].spuId` / `selectGoods.goodsClassifyMap[].分类名[].spuId`（→ 商品推广详情/启停）
- **枚举字段**：`activityType`（1/2）、`activityStatus`（0-3 整数）、`activityBannerType`（1 系统图 / 2 自定义）、`goodsTemplate`（1 一行一个 / 2 一行两个）、`cornerStyle`（1 圆角 / 2 直角）、`selectGoods.classify`（0 不分组 / 1 分组）
- **格式敏感字段**：`startTime`/`endTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）；`selectGoods.*[].commissionRateRange.minCommissionRate`/`maxCommissionRate`（**四位小数比率**，0.1213=12.13%）；`commissionRateRange.minCommissionAmount`/`maxCommissionAmount`（元）；`id`/`pageId`（Long→string）
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.detail","input":{"id":"1938271600000000001"},"summary":"查询活动推广完整配置"}
```

---

## ✅ 活动推广报表 — `ops.marketing.cps-stats.promotion-report`

- **说明**：按推广活动维度分页聚合推广效果（分享/点击/访问/下单/佣金），数据来自行为落地表；默认按开始时间倒序。**只统计已发布过的活动维度**（不含未发布数据的前端选项，但传 0 时服务端也会按未发布状态匹配，建议只传 1/2/3）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| activityName | String | 否 | 活动名称（模糊，≤100 字） |
| activityId | String | 否 | 活动推广 ID（精确；即列表返回的 id，十进制字符串） |
| activityStatus | Integer | 否 | 活动状态：1 未开始 / 2 进行中 / 3 已结束 |
| activityType | Integer | 否 | 活动类型：1 爆品推广 / 2 平台活动 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].activityId`（→ 活动推广详情/状态操作）
- **枚举字段**：`activityStatus`（1/2/3）
- **格式敏感字段**：`startTime`/`endTime`（yyyy-MM-dd HH:mm:ss）；`payOrderAmt`/`complatedOrderAmt`/`recommendAmount`/`complatedRecommendAmount`（**元**，两位小数）；`recommendShareCnt`/`clickPv`/`visitUv`/`newPayUv`/`orderUv`/`payOrderCnt`/`complatedOrderCnt`（Long→string 计数）
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-stats.promotion-report","input":{"pageNum":1,"pageSize":20,"activityStatus":2,"activityType":1},"summary":"查看进行中的爆品推广活动效果报表"}
```

---

## ✅ 活动推广报表导出 — `ops.marketing.cps.data-stats.promotion-details.export`

- **说明**：活动推广报表**异步导出**（推广效果数据）。返回**导出任务 ID**，用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载。筛选条件结构同 `ops.marketing.cps-stats.promotion-report`。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （筛选条件） | object | 否 | 结构同活动推广报表分页查询（activityId/distributorId/startTime/endTime 等） |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.cps.data-stats.promotion-details.export","input":{"pageNum":1,"pageSize":20},"summary":"导出活动推广报表"}
```

---

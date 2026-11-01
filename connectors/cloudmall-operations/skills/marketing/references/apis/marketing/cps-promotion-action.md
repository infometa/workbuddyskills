# 营销域 — CPS 活动推广写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-activity-flow.md`
> **状态机（活动推广，整数字段 activityStatus）**：`0` 未发布 → 发布（按时间窗口落 `1` 未开始 或 `2` 进行中）→ 到达开始时间自动 `1→2` → 到达结束时间自动 `2→3` / 手动结束 `1|2→3`；已发布状态（1/2/3）可取消发布回 `0`。删除**不做状态校验**（任意状态可删）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-promotion-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-promotion.create 新建活动推广 🟡 · cps-promotion.update 更新活动推广 🟡 · cps-promotion.copy 复制活动推广 🟢 · cps-promotion.publish 发布活动推广 🟡 · cps-promotion.unpublish 取消发布（回到未发布） 🟡 · cps-promotion.terminate 提前结束 🟡 · cps-promotion.delete 删除活动推广 🔴

---

## ✅ 新建活动推广 — `ops.marketing.cps-promotion.create`

- **风险**：🟡 新建即存库（初始未发布状态）
- **说明**：新建后为未发布状态，需配置完商品编排后再发布。出参返回新活动推广 ID。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityName | String | ✅ | 活动名称，≤50 字 |
| activityType | Integer | 否 | 1 爆品推广（默认）/ 2 平台活动 |
| pageId | Long | 否 | 关联装修页/活动页 ID |
| pageName | String | 否 | 装修页/活动页名称，≤100 字 |
| activityDesc | String | 否 | 活动说明，≤100 字 |
| shareTitle | String | 否 | 分享标题，≤20 字 |
| shareDesc | String | 否 | 分享说明，≤20 字 |
| shareImg | String | 否 | 分享图地址，≤500 字 |
| startTime | String | 否 | 活动开始时间（yyyy-MM-dd HH:mm:ss） |
| endTime | String | 否 | 活动结束时间（yyyy-MM-dd HH:mm:ss） |
| activityBannerType | Integer | 否 | Banner 类型：1 系统图 / 2 自定义 |
| bannerMainTitle | String | 否 | Banner 主标题，≤100 字 |
| bannerSubTitle | String | 否 | Banner 副标题，≤100 字 |
| bannerImg | String | 否 | 系统 Banner 图地址，≤500 字 |
| customBannerImg | String | 否 | 自定义 Banner 图地址，≤500 字 |
| bgColor | String | 否 | 背景色，≤20 字 |
| goodsTemplate | Integer | 否 | 商品模板：1 一行一个 / 2 一行两个 |
| pageMargin | Integer | 否 | 页面边距 |
| templateMargin | Integer | 否 | 模板边距 |
| cornerStyle | Integer | 否 | 圆角风格：1 圆角 / 2 直角 |
| selectGoods | Object | 否 | 商品编排：`{classify: 0|1, goodsList: [{spuId}], goodsClassifyMap: [{"分类名": [{spuId}]}]}`——写入方向只传 spuId（SPU 级引用，不含 skuList 与展示字段）；classify=0 用 goodsList，=1 用 goodsClassifyMap |

### 出参（原始数据）

- **路径参数来源**：出参直接为新活动推广 ID（十进制字符串，→ 发布/更新/详情等）
- **格式敏感字段**：ID 为 Long→string
- **枚举字段 / 脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.create","input":{"activityName":"十一爆品推广周","activityType":1,"activityDesc":"十一假期爆品集中推广","startTime":"2026-10-01 00:00:00","endTime":"2026-10-07 23:59:59","activityBannerType":1,"bannerMainTitle":"十一爆品周","goodsTemplate":1,"cornerStyle":1,"selectGoods":{"classify":0,"goodsList":[{"spuId":"2058365707555589633"}]}},"summary":"新建十一爆品推广周活动（未发布）"}
```

---

## ✅ 更新活动推广 — `ops.marketing.cps-promotion.update`

- **风险**：🟡 整体覆盖式更新
- **说明**：按 ID 更新配置字段。与新建共用入参结构（**不含** activityId 语义字段）；未传的字段会被置空/覆盖，**更新前先查明细，原值回传只改需要改的字段**。服务端不校验当前状态（未发布/已发布均可改），对已发布活动修改会直接影响 C 端展示。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | ✅ | 活动推广 ID（十进制字符串，路径参数） |
| 其余字段 | — | — | 与「新建活动推广」完全一致（见上表） |

### 出参（原始数据）

成功无业务数据（空 data）。失败时如实转述错误信息（常见：活动不存在）。

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.update","input":{"id":"1938271600000000001","activityName":"十一爆品推广周","activityType":1,"activityDesc":"十一假期爆品集中推广","startTime":"2026-10-01 00:00:00","endTime":"2026-10-08 23:59:59","activityBannerType":1,"bannerMainTitle":"十一爆品周","goodsTemplate":1,"cornerStyle":1,"selectGoods":{"classify":0,"goodsList":[{"spuId":"2058365707555589633"}]}},"summary":"将活动结束时间延长到10月8日"}
```

---

## ✅ 复制活动推广 — `ops.marketing.cps-promotion.copy`

- **风险**：🟢 产生未发布副本
- **说明**：复制任意状态的活动推广为新的未发布记录（原样复制全部配置）。出参返回新 ID。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | ✅ | 源活动推广 ID（十进制字符串） |

### 出参（原始数据）

- **路径参数来源**：出参为新活动推广 ID（十进制字符串）

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.copy","input":{"id":"1938271600000000001"},"summary":"复制该活动推广为新的未发布活动"}
```

---

## ✅ 发布活动推广 — `ops.marketing.cps-promotion.publish`

- **风险**：🟡 C 端可见生效
- **前置**：活动名称已配置；商品编排结构完整合法（结构不完整会报「商品配置不完整或格式不合法，无法发布」）。
- **说明**：发布后按时间窗口自动落状态——当前时间早于开始时间→未开始(1)，否则→进行中(2)。服务端**不校验当前状态**（已发布活动重复发布会重新按时间窗口落状态）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | ✅ | 活动推广 ID（十进制字符串） |

### 出参（原始数据）

成功无业务数据（空 data）。失败时如实转述错误信息。

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.publish","input":{"id":"1938271600000000001"},"summary":"发布该活动推广"}
```

---

## ✅ 取消发布活动推广 — `ops.marketing.cps-promotion.unpublish`

- **风险**：🟡 C 端下线
- **前置**：当前状态非未发布（未开始/进行中/已结束均可取消）；未发布状态再取消会报「当前活动未发布，无法取消发布」。取消后回到未发布(0)，可再次编辑发布。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | ✅ | 活动推广 ID（十进制字符串） |

### 出参（原始数据）

成功无业务数据（空 data）。

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.unpublish","input":{"id":"1938271600000000001"},"summary":"取消发布该活动推广"}
```

---

## ✅ 结束活动推广 — `ops.marketing.cps-promotion.terminate`

- **风险**：🟡 手动提前结束
- **前置**：仅未开始(1)/进行中(2)可结束；已结束/未发布会报「只有未开始或进行中的活动才能结束」。结束后状态为已结束(3)，不可再发布（只能复制或删除）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | ✅ | 活动推广 ID（十进制字符串） |

### 出参（原始数据）

成功无业务数据（空 data）。

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.terminate","input":{"id":"1938271600000000001"},"summary":"手动结束该进行中的活动推广"}
```

---

## ✅ 删除活动推广 — `ops.marketing.cps-promotion.delete`

- **风险**：🔴 物理删除且**无状态校验**
- **⚠️ 风险**：服务端删除不做任何状态检查——未发布/进行中/已结束的活动都能直接删除且不可恢复。删除「进行中」的活动等于强制下线，务必先与用户确认。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Long | ✅ | 活动推广 ID（十进制字符串） |

### 出参（原始数据）

成功无业务数据（空 data）。

### 调用示例

```json
{"capability":"ops.marketing.cps-promotion.delete","input":{"id":"1938271600000000001"},"summary":"删除该活动推广（物理删除不可恢复）"}
```

---

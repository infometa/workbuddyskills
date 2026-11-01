# 营销域 — 导购客户/公共池/绑定关系查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-flow.md`
> 覆盖客户归属列表、客户 360 画像、行为轨迹、归属转移、公共客户池与绑定关系查询/释放。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide-customer.search 已归属客户列表（全租户生效中关系） · guide-customer.profile 客户 360 画像 · guide-customer.behavior-tracks 客户行为轨迹（含高意向标记） · guide-public-pool.search 公共客户池列表（待分配） · guide-relation.search 绑定关系查询（含已失效，审计用）
> 写操作见 `guide-customer-action.md`。

---

## 关系类型与生命周期

- **关系类型**：`share_guide`（共享导购，一个客户同一时间至多一个）/ `exclusive_guide`（专属导购，一个客户同一时间至多一个）。
- **绑定方式**：`share_bind`-分享绑定 / `upgrade_exclusive`-升级专属 / `customer_switch`-客户换绑 / `nearest_store`-就近门店归属 / `store_round_robin`-门店轮流分配 / `admin_assign`-运营指定。
- **失效原因**（关系记录上的 deactivateReason）：`expired`-锁客期到期 / `manual_unbind`-手动解绑 / `transferred`-归属转移 / `guide_disabled`-导购停用 / `customer_switch`-客户切换 / `manual_release`-手动释放 / `new_binding_replaced`-新绑定替换。
- **公共池入池原因**（enterReason 实际取值）：`customer_switch` / `customer_unbind` / `expired` / `guide_disabled` / `admin_release` / `store_transfer`。
- 客户被解绑后若**无其他活跃绑定关系**，自动进入公共客户池；公共池记录被分配后即从池列表消失。

---

## ⛔ 未开放端点

| 端点 | 不开放理由 |
|------|-----------|
| 客户消费记录明细 | 本期后端未注册路由（前端展示为空态），消费概要走客户 360 画像 |

---

## ✅ 已归属客户列表 — `ops.marketing.guide-customer.search`

- **说明**：全租户生效中的导购-客户绑定关系，按绑定时间倒序。手机号为**精确匹配**（先经用户中心反查客户再过滤），查不到会员时返回空页。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| phone | String | 否 | 客户手机号（精确匹配），≤20 字符 |
| relationType | String | 否 | `share_guide`/`exclusive_guide` |
| guideId | String | 否 | 导购 ID |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].relationId`（→ 关系释放的路径 ID）、`records[].uid`（→ 客户画像/行为轨迹路径参数）
- **枚举字段**：`relationType`（share_guide/exclusive_guide）
- **格式敏感字段**：`bindTime`/`expireTime`（yyyy-MM-dd HH:mm:ss；`expireTime` 为 null 表示永久）
- 展示型字段：`customerName`/`customerPhone`/`memberLevel`/`guideName`/`guidePhone`（客户手机号未脱敏，透传展示即可）。

### 调用示例

```json
{"capability":"ops.marketing.guide-customer.search","input":{"pageNum":1,"pageSize":20,"relationType":"exclusive_guide"},"summary":"查询全部专属导购绑定关系"}
```

---

## ✅ 客户 360 画像 — `ops.marketing.guide-customer.profile`

- **说明**：客户基本信息 + 导购关系列表 + 消费概要 + 偏好标签，一次返回。仅返回**生效中**的导购关系。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uid | String | ✅ | 客户 UID（字符串会员 ID，路径参数） |

### 出参（原始数据）

- **枚举字段**：`basicInfo.gender`（male/female/unknown）、`guideRelations[].relationType`（share_guide/exclusive_guide）、`tags[].source`（system-系统自动/manual-运营手动/crm-CRM 同步；本期恒为空数组）
- **格式敏感字段**：`basicInfo.birthday`（yyyy-MM-dd）、`basicInfo.registerTime`/`guideRelations[].bindTime`/`expireTime`/`consumeSummary.lastConsumeTime`（yyyy-MM-dd HH:mm:ss）、`consumeSummary.totalAmount`/`avgAmount`（**单位元**）
- **口径说明**：`guideRelations[].remainDays` 为到期剩余天数（null=永久，已到期为 0）；消费概要在交易中心查询失败时降级为全零值。
- **脱敏字段**：`basicInfo.phoneMasked`（脱敏手机号）。

### 调用示例

```json
{"capability":"ops.marketing.guide-customer.profile","input":{"uid":"900000000000000001"},"summary":"查询客户360画像"}
```

---

## ✅ 客户行为轨迹 — `ops.marketing.guide-customer.behavior-tracks`

- **说明**：客户行为事件分页，按事件时间倒序；每行带高意向标记（近 7 天浏览 ≥3 次且无下单）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uid | String | ✅ | 客户 UID（路径参数） |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- **枚举字段**：`eventType`（browse-浏览/cart-加购/order-下单/share-分享/collect-收藏）
- **格式敏感字段**：`eventTime`（yyyy-MM-dd HH:mm:ss）、`eventData`（事件扩展数据 JSON 字符串——**服务端不解析（透传存储），无固定结构定义**，内容随 C 端事件类型变化，直接向用户转述原文即可）
- **口径说明**：`isHighIntent` 为该客户级标记（整页所有行同值），非单事件属性。

### 调用示例

```json
{"capability":"ops.marketing.guide-customer.behavior-tracks","input":{"uid":"900000000000000001","pageNum":1,"pageSize":20},"summary":"查看客户行为轨迹"}
```

---

## ✅ 公共客户池列表 — `ops.marketing.guide-public-pool.search`

- **说明**：当前**待分配**的公共池客户（已分配记录不返回），按入池时间倒序。手机号精确匹配。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| phone | String | 否 | 客户手机号（精确匹配），≤20 字符 |
| enterReason | String | 否 | 入池原因：`customer_switch`/`customer_unbind`/`expired`/`guide_disabled`/`admin_release`/`store_transfer` |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 公共池分配的 poolId）
- **枚举字段**：`enterReason`（见入参说明）
- **格式敏感字段**：`enterTime`（yyyy-MM-dd HH:mm:ss）、`daysInPool`（在池天数整数）

### 调用示例

```json
{"capability":"ops.marketing.guide-public-pool.search","input":{"pageNum":1,"pageSize":20,"enterReason":"guide_disabled"},"summary":"查看导购停用释放的公共池客户"}
```

---

## ✅ 绑定关系查询 — `ops.marketing.guide-relation.search`

- **说明**：绑定关系全量分页（含已失效记录，可用 isActive 过滤），按绑定时间倒序。手机号精确匹配。审计/追溯历史绑定时用本能力而非客户列表。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| phone | String | 否 | 客户手机号（精确匹配），≤20 字符 |
| relationType | String | 否 | `share_guide`/`exclusive_guide` |
| isActive | Integer | 否 | 0-已失效/1-生效中；不传则全部返回 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 手动释放绑定的路径 ID）
- **枚举字段**：`relationType`（share_guide/exclusive_guide）、`bindMethod`（见文件头部绑定方式）、`deactivateReason`（见文件头部失效原因）
- **格式敏感字段**：`bindTime`/`expireTime`/`deactivateTime`（yyyy-MM-dd HH:mm:ss；`expireTime` 为 null 表示永久）

### 调用示例

```json
{"capability":"ops.marketing.guide-relation.search","input":{"pageNum":1,"pageSize":20,"relationType":"exclusive_guide","isActive":1},"summary":"查询生效中的专属导购绑定关系"}
```

---

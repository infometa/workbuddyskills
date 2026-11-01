# 营销域 — 互动营销活动查询契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/interactive-activity-flow.md`
> 互动活动为 draft/formal 双版本模型：同一活动 ID 恒有 draft（运营编辑）副本，发布后追加 formal（C 端运行）副本。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：interactive-activity.search 互动活动分页（展示态分流） · interactive-activity.detail 互动活动详情（draft/formal 可选） · interactive-activity.stats 互动活动各状态数量 · interactive-activity.prize-records 中奖记录查询（发货前必读） · interactive-activity.data-monitor 互动数据监控（参与/发奖/转化） · interactive-activity.relative-scenes 关联应用场景查询
> 写操作见 `interactive-activity-action.md` 与 `interactive-activity-prize-action.md` 与 `interactive-activity-lifecycle-action.md`。

---

## 双版本模型与状态机

**副本模型**（核心，所有操作先分清作用对象）：

| 操作 | 作用对象 | 语义 |
|------|---------|------|
| 创建 | 仅落 draft | 状态 UNPUBLISHED，优先级 0 |
| 编辑 | 仅更新 draft | formal 不动；已发布活动的修改要再次 publish 才生效 |
| 发布 | draft → formal | draft 快照整包 upsert 到 formal；draft 状态转 PUBLISHED（内部标记，列表不展示） |
| 暂停/恢复/结束 | formal | 运行态流转；draft 不镜像 |
| 删除 | draft + formal | 一并删除（含库存/限流独立表） |
| 复制 | formal 优先 | 无 formal（未发布）则复制 draft；生成新活动 ID 的草稿 |
| 优先级 | draft + formal | 两副本同步 |
| 库存调整 | formal（同步 draft） | 运行时生效 |

**状态枚举**（全大写字符串）：
- 展示态按"FORMAL 存在则用 FORMAL 状态，否则 UNPUBLISHED"呈现：
  - UNPUBLISHED（未发布，draft 侧）
  - NOT_STARTED（未开始，formal 侧）
  - RUNNING（进行中，formal 侧）
  - PAUSED（已暂停，formal 侧）
  - TERMINATED（已结束-手动，formal 侧终态）
  - EXPIRED（已结束-自动过期，formal 侧终态）
- PUBLISHED 为 draft 内部标记态：**搜索筛选传入 PUBLISHED 视为非法（返回空列表）**，"已结束"筛选请用 `statusList: ["TERMINATED","EXPIRED"]`。

**状态流转前置**（服务端强校验）：
- 发布：draft 必须存在且 configInfo 校验通过；formal 状态按开始时间判定（未到 → NOT_STARTED；已到 → RUNNING）；
- 暂停：仅 RUNNING / NOT_STARTED；恢复：仅 PAUSED（按开始时间回落 NOT_STARTED 或 RUNNING）；
- 结束：仅 RUNNING / NOT_STARTED / PAUSED → TERMINATED；
- 删除：仅"未发布（无 formal）"或"formal 已结束/已过期"；
- 编辑：formal 处于 TERMINATED / EXPIRED 时不可编辑。

**活动类型**（activityType，小写中划线）：`sudoku-lottery`（九宫格抽奖）、`dzp`（大转盘）、`newcomer-gift`（新人礼包）、`open-screen-gift`（开屏礼包）、`daily-checkin`（每日签到）、`exchange-code`（第三方兑换码）、`share-gift`（分享有礼）、`yqzl`（邀请助力）。每个类型有"必需玩法桶"约束（见创建入参）。

---

## ⛔ 未开放端点

| 端点 | 不开放理由 |
|------|-----------|
| C 端参与/抽奖/签到等运行时接口（Internal 与 App 侧） | 面向 C 端用户运行时，不属于运营端能力面 |
| 活动玩法运行时数据（邀请/助力明细） | 已并入数据监控与详情的统计字段，无独立运营端点 |

---

## ✅ 活动分页查询 — `ops.marketing.interactive-activity.search`

- **说明**：按展示态分流返回（未发布活动命中 draft 行、已发布活动命中 formal 行，同一活动 ID 只出一行）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | 默认 1 |
| pageSize | Integer | 否 | 默认 10 |
| keyword | String | 否 | 关键词（同时模糊匹配活动名称与活动 ID） |
| activityName | String | 否 | 活动名称模糊（与 keyword 二选一，keyword 优先） |
| activityType | String | 否 | 活动类型 code |
| status | String | 否 | 单状态筛选（不可传 PUBLISHED） |
| statusList | String[] | 否 | 多状态 IN 筛选（与 status 二选一，优先），如 `["TERMINATED","EXPIRED"]` |
| detailType | String | 否 | formal=只查已发布正式稿（装修配置页选活动场景）；默认展示态 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].activityId`（→ 全部活动操作的业务 ID；**不是数据库主键 id**）
- **枚举字段**：`status`（状态机）、`activityType`、`detailType`（draft/formal）
- **格式敏感字段**：`startTime`/`endTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `isPublished`（是否发布过）、`description`（活动说明，来自 COMMON 桶）。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.search","input":{"pageNum":1,"pageSize":10,"keyword":"签到","activityType":"daily-checkin"},"summary":"查找签到类互动活动"}
```

---

## ✅ 活动详情 — `ops.marketing.interactive-activity.detail`

- **说明**：编辑前必读（draft 版为编辑基线）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID（本文各能力的 activityId 均为此义） |
| detailType | String | 否 | draft（默认，运营编辑）/ formal（查看已发布版） |

### 出参（原始数据）

- **关键字段来源**：`activityId`、`prizeInfo.prizeList[].templateId`（奖品模板 ID）、`prizeInfo.prizeList[].prizeName`+`prizeType`（库存调整定位键）、`detailType`
- **枚举字段**：`status`、`activityType`、`prizeInfo.prizeList[].prizeType`（points/coupon/physical）
- **格式敏感字段**：`startTime`/`endTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `configInfo`（双层玩法配置，结构与校验协议见创建入参 configInfo 协议表；**编辑回填基线**——保留未改动桶/键原值）、`pageConfig`（页面装修配置，服务端不解析，原样透传）、`isPublished`、`prizeInfo.prizeList[].usedStock`（已发放数量，仅展示）；`stats` 当前为占位 0，真实数据走数据监控能力。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.detail","input":{"activityId":"1942000000000000001","detailType":"formal"},"summary":"查看活动的已发布版配置"}
```

---

## ✅ 活动状态统计 — `ops.marketing.interactive-activity.stats`

- **说明**：各状态活动数量（展示态口径，排除 PUBLISHED 标记态），用于列表 Tab 计数。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityType | String | 否 | 按活动类型过滤 |

### 出参（原始数据）

- `total`（总数）；`statusCounts`（对象：key=状态值，value=数量）。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.stats","input":{"activityType":"sudoku-lottery"},"summary":"查看九宫格抽奖活动各状态数量"}
```

---

## ✅ 中奖记录查询 — `ops.marketing.interactive-activity.prize-records`

- **说明**：实物发货前必读（筛 CLAIMED 找待发货记录并核对收货资料）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |
| pageNum | Integer | 否 | 默认 1 |
| pageSize | Integer | 否 | 1..100，默认 10 |
| uid | String | 否 | 用户 ID 精确筛选 |
| prizeType | String | 否 | 奖品类型：points/coupon/physical |
| status | String | 否 | 发放状态：SENDING/WAITING_CLAIM/CLAIMED/SENDED/SEND_FAILED/EXPIRED |
| joinTimeStart | String | 否 | 参与时间起（yyyy-MM-dd HH:mm:ss） |
| joinTimeEnd | String | 否 | 参与时间止（yyyy-MM-dd HH:mm:ss） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].uniqId`（→ 实物发货路径参数）、`records[].uid`（用户）
- **枚举字段**：`statusCode`（发放状态 code，**驱动发货按钮等条件渲染，优先于中文 status**）、`prizeType`
- **格式敏感字段**：`joinTime`/`expireTime`/`shippedAt`（yyyy-MM-dd HH:mm:ss；expireTime null=不过期）
- **脱敏注意**：`receiverPhone` 为用户填写的收货手机号（原样展示，向用户转述时注意隐私）；`receiverName`/`receiverAddress`/`logisticsCompany`/`trackingNo` 为收货与发货信息。
- 发放状态机：SENDING（发放中）→ 虚拟资产到账 SENDED / 实物 WAITING_CLAIM（待领取）→ 用户填资料 CLAIMED（已领取）→ 运营发货 SENDED；SEND_FAILED（发放失败）、EXPIRED（实物超期未填资料，查询时按 expireTime 惰性判定）为终态。
- **筛选陷阱**：EXPIRED 是查询时按 expireTime 惰性判定的展示态，存储状态仍是 WAITING_CLAIM——按 `status=EXPIRED` 筛选会返回空；要找超期记录请筛 `WAITING_CLAIM` 再看 `expireTime`。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.prize-records","input":{"activityId":"1942000000000000001","pageNum":1,"pageSize":10,"prizeType":"physical","status":"CLAIMED"},"summary":"查找待发货的实物中奖记录"}
```

---

## ✅ 数据监控 — `ops.marketing.interactive-activity.data-monitor`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 出参（原始数据）

- **格式敏感字段**：`conversionRate`（百分数）、`lastUpdateTime`（yyyy-MM-dd HH:mm:ss）
- `totalParticipants`（总参与次数）/`uniqueParticipants`（去重参与人数）/`totalPrizeIssued`（累计发奖数）/`pageViews`（当前占位 0）。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.data-monitor","input":{"activityId":"1942000000000000001"},"summary":"查看活动参与与发奖数据"}
```

---

## ✅ 关联应用场景查询 — `ops.marketing.interactive-activity.relative-scenes`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 出参（List，原始数据）

- **枚举字段**：`sceneType`（mini_program_page/push/banner）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）
- 每项含 `sceneValue`（页面路径/推送 ID 等）、`sceneName`。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.relative-scenes","input":{"activityId":"1942000000000000001"},"summary":"查看活动挂载的应用场景"}
```

---

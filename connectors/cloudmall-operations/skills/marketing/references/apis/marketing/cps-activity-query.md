# 营销域 — CPS 活动奖励与分销规则查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-activity-flow.md`
> **状态机（活动奖励）**：`draft`（未发布）→ 发布 → `init`（未开始）→ 到达预热时间自动 → `warmup`（预热中）→ 到达开始时间自动 → `running`（进行中）→ 到达结束时间自动/手动终止 → `terminated`（已结束）。
> **结算状态（活动维度，字符串枚举）**：`'0'`（默认，活动未结束时的初始值）/ `unsettled`（待结算，终止时已产生订单）/ `settled`（已结算，终止时无订单）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-activity.search CPS 活动奖励分页（name/type/状态/结算状态筛选） · cps-activity.detail 活动奖励详情（奖励规则/适用范围四维度） · cps-activity.overlap-check 活动冲突校验（四维度全重叠才冲突；无副作用只读） · cps-rule.get 查询全局分销规则（绑定模式/跟单有效期/自购/员工下单）
> 写操作见 `cps-activity-action.md`。

---

## ✅ 活动列表分页 — `ops.marketing.cps-activity.search`

- **说明**：按当前租户分页查询 CPS 活动奖励列表，默认按更新时间倒序。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| name | String | 否 | 活动名称（模糊）——注意字段名是 name，不是 activityName |
| type | String | 否 | 活动类型：`OD`（订单激励）/ `GMV`（GMV 激励） |
| status | String | 否 | 活动状态（单个）：`draft`/`init`/`warmup`/`running`/`terminated` |
| statusList | Array&lt;String&gt; | 否 | 活动状态（多值 IN 查询） |
| settleStatus | String | 否 | 结算状态（单个）：`'0'`/`unsettled`/`settled` |
| settlementStatusList | Array&lt;String&gt; | 否 | 结算状态（多值 IN 查询） |
| activityId | String | 否 | 活动业务 ID（精确） |
| startTimeBegin | String | 否 | 活动开始时间下限。**无显式格式注解**，按 ISO 格式 `yyyy-MM-dd'T'HH:mm:ss` 传递（与结算明细查询的 `yyyy-MM-dd HH:mm:ss` 不同，非必要不传） |
| startTimeEnd | String | 否 | 活动开始时间上限，格式同上 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].activityId`（→ 详情/复制/终止/删除/发布/结算明细的活动 ID 路径参数）
- **枚举字段**：`type`（OD/GMV）、`status`（draft/init/warmup/running/terminated）、`settlementStatus`（'0'/unsettled/settled）
- **格式敏感字段**：`warmUpTime`/`startTime`/`endTime`/`createTime`/`updateTime`（yyyy-MM-dd HH:mm:ss）；`id`（Long→string）
- **脱敏字段**：无（`imageUrl` 为带 60 分钟有效期的预签名地址，非脱敏）

### 调用示例

```json
{"capability":"ops.marketing.cps-activity.search","input":{"pageNum":1,"pageSize":20,"name":"秋季推新","status":"running","settleStatus":"unsettled"},"summary":"查看进行中且待结算的秋季推新活动"}
```

---

## ✅ 活动详情 — `ops.marketing.cps-activity.detail`

- **说明**：查询单个活动完整信息；适用范围四个维度会富化为名称/商品详情（回显用）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID（16 位数字串） |

### 出参（原始数据）

- **路径参数来源**：`activityId`（→ 复制/终止/删除/发布/结算明细）、`configInfo.product.goodsList[].spuId`（→ 商品推广详情）
- **枚举字段**：`type`、`status`、`settlementStatus`（同列表）；`prizeInfo.type`（1 按订单奖励 / 2 订单阶梯奖励 / 3 GMV 阶梯奖励）；`configInfo.product.type`（0 不限 / 1 指定分类 / 2 指定品牌 / 3 指定商品）、`configInfo.store.type`（0 不限 / 1 指定门店 / 2 指定门店分组）、`configInfo.user.type`（0 不限 / 1 新用户 / 2 指定用户-人群标签值 ID）、`configInfo.distributor.type`（0 不限 / 1 指定分销员 / 2 指定分销员分组 / 3 指定分销员等级）
- **格式敏感字段**：各时间字段（yyyy-MM-dd HH:mm:ss）；`prizeInfo.rewardPerOrder`/`prizeInfo.target[].rewardAmount`（元，两位小数）；`prizeInfo.maxAmount`（**有效订单量件数**，整数，0=不限）；`prizeInfo.target[].target`（类型 2 时为订单量整数；类型 3 时为 GMV 金额元，两位小数）；`id`（Long→string）
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-activity.detail","input":{"activityId":"7017890752010234"},"summary":"查询CPS活动奖励详情"}
```

---

## ✅ 活动冲突校验 — `ops.marketing.cps-activity.overlap-check`

- **说明**：只读无副作用，瞬态错误可单次重试。保存前校验同时段、同适用范围的已发布活动是否冲突（四个维度**全部重叠**才算冲突；任一方四维度全不限则与所有活动冲突）。configInfo 信息不完整时不判冲突（保守返回不冲突），解析异常时保守判冲突。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | String | ✅ | 活动开始时间（yyyy-MM-dd HH:mm:ss） |
| endTime | String | ✅ | 活动结束时间（yyyy-MM-dd HH:mm:ss） |
| activityId | String | 否 | 编辑场景传入以排除自身；新建不传 |
| configInfo | Object | ✅ | 适用范围，四维度结构如下 |
| configInfo.product.type | Integer | ✅ | 商品范围类型：0 不限 / 1 指定分类（list 填类目编码）/ 2 指定品牌（list 填品牌 ID）/ 3 指定商品（用 goodsList） |
| configInfo.product.list | Array&lt;String&gt; | 否 | 分类编码或品牌 ID 列表（type=1/2 时使用） |
| configInfo.product.goodsList | Array | 否 | 商品引用列表（type=3 时使用），每项 `{spuId, skuList?: [{skuId}]}`；SPU 级选择不传 skuList |
| configInfo.store.type | Integer | ✅ | 门店范围：0 不限 / 1 指定门店 / 2 指定门店分组 |
| configInfo.store.list | Array&lt;String&gt; | 否 | 门店 ID 或门店分组 ID 列表 |
| configInfo.user.type | Integer | ✅ | 用户范围：0 不限 / 1 新用户（list 不传）/ 2 指定用户（list 填人群标签值 ID） |
| configInfo.user.list | Array&lt;String&gt; | 否 | 指定用户时的人群标签值 ID 列表 |
| configInfo.distributor.type | Integer | ✅ | 分销员范围：0 不限 / 1 指定分销员（list 填分销员 UID）/ 2 指定分销员分组（list 填分组 ID）/ 3 指定分销员等级（list 填等级 ID） |
| configInfo.distributor.list | Array&lt;String&gt; | 否 | 对应 ID 列表 |

### 出参（原始数据）

- **路径参数来源**：`conflictActivities[].activityId`（冲突活动，可用于查其详情）
- **枚举字段**：`hasOverlap`（boolean）；`conflictActivities[].type`、`conflictActivities[].status`（同活动列表枚举）
- **格式敏感字段**：`conflictActivities[].startTime`/`endTime`（yyyy-MM-dd HH:mm:ss）
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-activity.overlap-check","input":{"startTime":"2026-09-20 10:00:00","endTime":"2026-10-20 22:00:00","configInfo":{"product":{"type":0,"list":[]},"store":{"type":0,"list":[]},"user":{"type":0,"list":[]},"distributor":{"type":0,"list":[]}}},"summary":"校验新建活动是否与现有活动冲突"}
```

---

## ✅ 查询分销规则 — `ops.marketing.cps-rule.get`

- **说明**：查询当前租户的全局分销跟单规则；租户从未保存过时返回空（data 为 null），此时按各字段默认语义处理。

### 入参

无（空入参即可）。

### 出参（原始数据）

- **枚举字段**：`distributionRelationType`（1 动态 / 2 专属 / 3 永久）、`selfPurchaseCommission`（1 自购得佣金 / 2 自购仅跟单）、`employeeOrderCommission`（1 员工互下单得佣金 / 2 仅跟单）；各字段均有对应 `*Desc` 中文描述
- **格式敏感字段**：`followUpValiditySeconds`（跟单有效期**秒数**，0=永不过期；天/时/分需自行换算）
- **路径参数来源 / 脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-rule.get","input":{},"summary":"查询当前租户的分销跟单规则"}
```

---

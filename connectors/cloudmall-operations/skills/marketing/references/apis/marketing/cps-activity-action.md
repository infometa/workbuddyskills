# 营销域 — CPS 活动奖励与分销规则写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-activity-flow.md`
> **状态机（活动奖励）**：`draft`（未发布）→ 发布 → `init`（未开始）→ 到达预热时间自动 → `warmup`（预热中）→ 到达开始时间自动 → `running`（进行中）→ 到达结束时间自动/手动终止 → `terminated`（已结束）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-activity-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-activity.save 保存活动（创建/更新二合一） 🟡 · cps-activity.copy 复制活动为草稿 🟢 · cps-activity.publish 发布活动（draft→init） 🟡 · cps-activity.terminate 终止活动 🔴 · cps-activity.delete 删除活动 🔴 · cps-rule.save 保存全局分销规则 🟡

---

## ✅ 保存活动（创建/更新二合一） — `ops.marketing.cps-activity.save`

- **风险**：🟡 商业影响（奖励规则直接决定后续佣金发放）
- **⚠️ 二合一语义**：`activityId` 不传=新建（初始 draft）；传值=更新，**仅 draft 状态可更新**，已发布活动更新会被拒绝。
- **前置校验**（服务端逐条校验，全部失败即整体拒绝）：预热时间必须晚于当前时间；开始时间必须晚于预热时间；结束时间必须晚于开始时间；名称 2-30 字；说明 2-500 字。
- **建议**：保存前先做冲突校验；发布前再次确认奖励规则金额。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | 否 | 更新时传入；新建不传 |
| name | String | ✅ | 活动名称，2-30 字 |
| type | String | ✅ | `OD` 或 `GMV`（正则强校验，仅这两个值） |
| description | String | ✅ | 活动说明，2-500 字 |
| imageUrl | String | ✅ | 活动图片地址（建议传裸地址，服务端会剥离预签名参数） |
| warmUpTime | String | ✅ | 预热时间（yyyy-MM-dd HH:mm:ss），必须晚于当前时间 |
| startTime | String | ✅ | 开始时间，必须晚于预热时间 |
| endTime | String | ✅ | 结束时间，必须晚于开始时间 |
| prizeInfo | Object | ✅ | 奖励规则（见下） |
| prizeInfo.type | Integer | ✅ | 1 按订单奖励 / 2 订单阶梯奖励 / 3 GMV 阶梯奖励 |
| prizeInfo.rewardPerOrder | Number | 条件 | 每笔有效订单奖励（元，两位小数），type=1 必填 |
| prizeInfo.maxAmount | Number | 条件 | 奖励封顶的有效订单量（整数件数，0=不限），type=1 使用 |
| prizeInfo.target | Array | 条件 | 阶梯列表，type=2/3 必填；每项 `{target, rewardAmount}`——type=2 的 target 为订单量整数，type=3 的 target 为 GMV 金额（元）；rewardAmount 均为元，两位小数 |
| configInfo | Object | ✅ | 适用范围，四维度结构与冲突校验完全一致（见 overlap-check 入参表） |
| priority | Integer | 否 | 活动优先级，缺省 0 |
| detailInfo | Object | 否 | 活动详情扩展结构（嵌套 Map）——**服务端预留字段**：保存链路仅序列化存储、详情出参反序列化回嵌套 Map 原样回显，但**无任何业务消费方，运营端前端也不构造**。Agent 不要自行构造，保持不传 |

### 出参（原始数据）

- **路径参数来源**：`activityId`（新建后即可用于发布/编辑等后续操作）
- **枚举字段**：`status`（新建恒为 `draft`）、`settlementStatus`（新建恒为 `'0'`）、`type`
- **格式敏感字段**：各时间字段（yyyy-MM-dd HH:mm:ss）；`id`（Long→string）
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-activity.save","input":{"name":"秋季新品分销激励","type":"OD","description":"秋季新品上市期间，分销员每笔有效订单发放5元奖励","imageUrl":"https://cos.example.com/cps/autumn-banner.png","warmUpTime":"2026-12-01 10:00:00","startTime":"2026-12-05 10:00:00","endTime":"2026-12-31 22:00:00","prizeInfo":{"type":1,"rewardPerOrder":5.0,"maxAmount":0},"configInfo":{"product":{"type":3,"goodsList":[{"spuId":"2058365707555589633"}]},"store":{"type":0,"list":[]},"user":{"type":0,"list":[]},"distributor":{"type":0,"list":[]}},"priority":0},"summary":"创建一个每单奖励5元的CPS活动（草稿）"}
```

---

## ✅ 复制活动 — `ops.marketing.cps-activity.copy`

- **风险**：🟢 仅产生 draft 副本，无线上影响
- **说明**：复制任意状态的活动为新的草稿（名称追加「（复制）」，时间原样复制——**注意副本的预热时间可能已早于当前时间，需编辑后才能发布**）。
- **场景指引**：复制后需要改名/改期的，**先 copy 再 save 更新**（副本保真，只改目标字段），不要用 create 重新配一遍——重配容易漏掉原活动的扩展字段与优先级等隐性配置。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 源活动业务 ID |

### 出参（原始数据）

- **路径参数来源**：`activityId`（新副本的业务 ID，用于继续编辑/发布）
- **枚举字段**：`status`（恒为 `draft`）、`settlementStatus`（恒为 `'0'`）
- **格式敏感字段**：同活动列表
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-activity.copy","input":{"activityId":"7017890752010234"},"summary":"复制该CPS活动为新的草稿"}
```

---

## ✅ 发布活动 — `ops.marketing.cps-activity.publish`

- **风险**：🟡 生效流程起点（draft → init）
- **前置**：仅 `draft` 状态可发布；已发布/已结束活动发布会报「只有未发布状态的活动才能发布」。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 出参（原始数据）

成功无业务数据（空 data）。失败时如实转述错误信息（常见：非 draft 状态、活动不存在）。

### 调用示例

```json
{"capability":"ops.marketing.cps-activity.publish","input":{"activityId":"7017890752010234"},"summary":"发布该CPS活动（草稿转未开始）"}
```

---

## ✅ 终止活动 — `ops.marketing.cps-activity.terminate`

- **风险**：🔴 资损敏感
- **说明**：手动终止进行中的活动并**立即流转结算状态**——活动已产生订单则置 `unsettled`（待结算），无订单直接置 `settled`（已结算）。事务保障，不可逆。
- **前置**：仅 `init`（未开始）/ `warmup`（预热中）/ `running`（进行中）可终止；draft 请用删除。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 出参（原始数据）

成功无业务数据（空 data）。失败时如实转述错误信息（常见：状态不允许终止、并发更新冲突）。

### 调用示例

```json
{"capability":"ops.marketing.cps-activity.terminate","input":{"activityId":"7017890752010234"},"summary":"终止该进行中的CPS活动"}
```

---

## ✅ 删除活动 — `ops.marketing.cps-activity.delete`

- **风险**：🟡 不可恢复
- **前置**：仅 `draft` 状态可删除；已发布/已结束活动删除会被拒绝。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |

### 出参（原始数据）

成功无业务数据（空 data）。失败时如实转述错误信息。

### 调用示例

```json
{"capability":"ops.marketing.cps-activity.delete","input":{"activityId":"7017890752010234"},"summary":"删除该草稿状态的CPS活动"}
```

---

## ✅ 保存分销规则 — `ops.marketing.cps-rule.save`

- **风险**：🟡 全局规则变更（影响全租户跟单与佣金判定）
- **说明**：upsert 语义，每租户仅一条记录，保存即**整体覆盖**四个策略字段——必须先查询现有值，只改需要改的字段、其余原值回传。 **硬门禁：全租户/全局生效写——提交前必须发确认卡复述「现值 → 目标值」取得明确确认，指令参数齐全不豁免。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| distributionRelationType | Integer | ✅ | 绑定模式：1 动态 / 2 专属 / 3 永久 |
| followUpValiditySeconds | Long | ✅ | 跟单有效期（秒），≥0；**0=永不过期**（永久绑定模式固定传 0） |
| selfPurchaseCommission | Integer | ✅ | 分销员自购：1 自购会获得佣金 / 2 自购仅跟单不会获得佣金 |
| employeeOrderCommission | Integer | ✅ | 员工下单：1 内部员工分销员之间下单会获得佣金 / 2 仅跟单不会获得佣金 |

### 出参（原始数据）

成功无业务数据（空 data）。

### 调用示例

```json
{"capability":"ops.marketing.cps-rule.save","input":{"distributionRelationType":1,"followUpValiditySeconds":259200,"selfPurchaseCommission":1,"employeeOrderCommission":2},"summary":"设置分销绑定为动态模式、跟单有效期3天"}
```

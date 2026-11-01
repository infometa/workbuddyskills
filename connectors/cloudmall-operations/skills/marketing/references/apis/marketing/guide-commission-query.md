# 营销域 — 导购提成（规则 + 明细）查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-incentive-flow.md`
> 提成规则决定订单完成时导购提成的计算口径；提成明细是订单提成计算落账后的流水记录。
> 规则状态机：`draft` 草稿 / `active` 生效中 / `expired` 已过期 三态按时间**动态推导**（不落库）；`disabled` 已停用为存储态（手动停用写入）。规则优先级**数字越小越优先**，订单提成按优先级升序取首个范围匹配的生效规则。
> 提成明细由订单完成事件自动计算落账（不可手工创建/修改金额）；结算状态：`pending` 待结算 / `settled` 已结算。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide-commission-rule.search 提成规则分页 · guide-commission-rule.detail 提成规则详情（编辑前必读） · guide-commission-rule.status-counts 提成规则各状态数量 · guide-commission-rule.conflict-check 提成规则冲突检测（无副作用只读） · guide-commission-detail.search 提明明细分页（落账流水） · guide-commission-detail.stats 提成统计（总额/待结算/已结算） · guide.commission-details.export 提成明细异步导出（返回任务 ID）
> 写操作见 `guide-commission-action.md`。

---

---

> 明细由订单完成事件自动计算落账（不可手工创建/修改金额）；运营侧仅查询、统计与批量标记结算。
> 结算状态：`pending` 待结算 / `settled` 已结算。

---

## ⛔ 未开放端点

| 端点能力 | 不开放原因 |
|---------|-----------|
| 无 | 本模块全部端点均已开放 |

---

## ✅ 规则分页 — `ops.marketing.guide-commission-rule.search`

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| ruleName | String | 否 | 规则名称模糊搜索 |
| calculationType | String | 否 | 计算方式：`percentage` 按比例 / `category` 按品类差异化 / `ladder` 阶梯式 / `combined` 组合模式 / `fixed` 固定金额 |
| status | String | 否 | 状态筛选（推导语义）：`disabled` 已停用 / `active` 生效中（在效期内）/ `draft` 草稿（生效开始时间在未来）/ `expired` 已过期（生效结束时间已过） |

#### 出参（分页，原始数据）

- **枚举字段**：`calculationType`（五种计算方式）、`status`（draft/active/expired/disabled）
- **格式敏感字段**：`effectiveStartTime`/`effectiveEndTime`（yyyy-MM-dd HH:mm:ss；end 为空表示永久生效——**空字段不出现**在响应中）、`createdTime`（yyyy-MM-dd HH:mm:ss）、`priority`（整数）
- 其余展示字段：`ruleName`、`calculationTypeDesc`、`statusDesc`、`scopeSummary`（范围摘要如「全部导购」）、`ruleSummary`（规则摘要如「统一佣金比例 5%」）、`createdBy`。

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-rule.search","input":{"pageNum":1,"pageSize":20,"status":"active"},"summary":"查看当前生效中的提成规则"}
```

---

## ✅ 规则详情 — `ops.marketing.guide-commission-rule.detail`

- **说明**：编辑前必读（回填完整 scopes/items）。

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则 ID |

#### 出参（原始数据）

- **关键字段来源**：`id`（→ 更新/停用/删除）、`scopes[].scopeValue`（指定/排除范围的对象 ID）
- **枚举字段**：`calculationType`、`status`、`scopes[].scopeType`（guide/level/store）、`scopes[].rangeType`（all/specified/excluded）、`items[].itemType`（order_rate/category/cumulative_ladder/fixed_per_order）
- **格式敏感字段**：`effectiveStartTime`/`effectiveEndTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）、`items[].commissionRate`（**小数形式比例**，如 0.05 = 5%；fixed 规则为**元金额**）、`priority`
- **细项值语义**（`items[].itemValue`）：`category` 为品类 ID；`cumulative_ladder` 为阶梯门槛（管理端以**万元数值**录入，如 `"5"` 表示 5 万元）；`order_rate`/`fixed_per_order` 无值。
- 每个范围含 `scopeTypeDesc`/`rangeTypeDesc`/`scopeValueDesc`（对象名称）。

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-rule.detail","input":{"id":"5200000000000000001"},"summary":"读取提成规则完整配置用于编辑"}
```

---

## ✅ 规则状态数量统计 — `ops.marketing.guide-commission-rule.status-counts`

- **说明**：状态页签计数。

#### 入参

- 无。

#### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| all | 全部规则数（**含已停用**） |
| active | 生效中数量 |
| draft | 草稿（未到生效时间）数量 |
| expired | 已过期数量 |

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-rule.status-counts","input":{},"summary":"获取提成规则各状态数量"}
```

---

## ✅ 冲突检测 — `ops.marketing.guide-commission-rule.conflict-check`

- **说明**：只读校验，创建/编辑规则前建议先测。
- 检测口径：与「未停用 + 效期重叠」的既有规则比对，再按适用范围求交集（任一方含「全部」视为交集）；同时段同优先级 → `same_priority`，仅重叠 → `overlap`。

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| priority | Integer | ✅ | 优先级（正整数） |
| effectiveStartTime | String | ✅ | 生效开始时间（yyyy-MM-dd HH:mm:ss） |
| effectiveEndTime | String | 否 | 生效结束时间；不传 = 永久生效。须大于开始时间 |
| ruleId | String | 否 | 编辑场景传当前规则 ID（排除自身），新建不传 |
| scopes | Array | 否 | 适用范围列表，结构同创建；不传则不做范围交集过滤 |
| scopes[].scopeType | String | 条件必填 | `guide` 导购 / `level` 等级 / `store` 门店 |
| scopes[].rangeType | String | 条件必填 | `all` 全部 / `specified` 指定 / `excluded` 排除 |
| scopes[].scopeValue | String | 条件必填 | 对象 ID；rangeType=all 传 null |

#### 出参（原始数据）

- **枚举字段**：`conflictType`（`same_priority` 同优先级冲突 / `overlap` 仅范围重叠 / `none` 无冲突）
- `hasConflict`（布尔）；`conflictRules[]`（冲突规则：`ruleId`/`ruleName`/`priority`/`effectiveStartTime`/`effectiveEndTime`）。

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-rule.conflict-check","input":{"priority":10,"effectiveStartTime":"2026-10-01 00:00:00"},"summary":"检测新提成规则是否与既有规则冲突"}
```

---

## ✅ 明细分页 — `ops.marketing.guide-commission-detail.search`

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| guideId | String | 否 | 导购 ID（精确） |
| orderNo | String | 否 | 订单号（精确） |
| settlementStatus | String | 否 | `pending` / `settled` |
| startTime | String | 否 | 按落账时间过滤，yyyy-MM-dd HH:mm:ss |
| endTime | String | 否 | 同上 |

#### 出参（分页，原始数据）

- **关键字段来源**：`id`（→ 批量结算 detailIds）、`appliedRuleId`（→ 规则详情）、`guideId`
- **枚举字段**：`settlementStatus`（pending/settled）、`guideRole`（`exclusive_guide` 专属导购 / `share_guide` 分享导购）
- **格式敏感字段**：`performanceValue`/`baseCommission`/`ladderBonus`/`finalCommission`（业绩值/基础提成/阶梯加成/最终提成，均为**元**）；`settlementTime`/`createdTime`（yyyy-MM-dd HH:mm:ss）
- 其余展示字段：`guideName`、`storeName`、`appliedRuleName`、`settlementStatusDesc`、`guideRoleDesc`、`uid`（买家）。

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-detail.search","input":{"pageNum":1,"pageSize":20,"settlementStatus":"pending"},"summary":"查看待结算的提成明细"}
```

---

## ✅ 提成统计卡片 — `ops.marketing.guide-commission-detail.stats`

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | String | 否 | 按落账时间过滤，yyyy-MM-dd HH:mm:ss |
| endTime | String | 否 | 同上 |

#### 出参（原始数据）

- **格式敏感字段**：`totalCommission`（总提成）/`pendingSettlement`（待结算）/`settledAmount`（已结算）——均为**元**。

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-detail.stats","input":{"startTime":"2026-09-01 00:00:00","endTime":"2026-09-30 23:59:59"},"summary":"统计9月提成总额与待结算金额"}
```

---

## ✅ 提成明细导出 — `ops.marketing.guide.commission-details.export`

- **说明**：按筛选条件异步导出导购提成明细。返回**导出任务 ID**，用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载。筛选字段：guideId / orderNo / settlementStatus / startTime / endTime；导出为**非幂等操作**（重试创建重复任务）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （筛选条件） | object | 否 | guideId / orderNo / settlementStatus / startTime / endTime（导出无分页参数，服务端固定分批拉取） |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.guide.commission-details.export","input":{"startTime":"2026-09-01 00:00:00","endTime":"2026-09-30 23:59:59"},"summary":"导出本期待结算提成明细"}
```

---

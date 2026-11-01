# 营销域 — 导购提成（规则 + 明细）写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-incentive-flow.md`
> 提成规则决定订单完成时导购提成的计算口径；提成明细是订单提成计算落账后的流水记录。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-commission-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide-commission-rule.create 创建提成规则 🟡 · guide-commission-rule.update 更新提成规则 🟡 · guide-commission-rule.disable 停用提成规则 🔴 · guide-commission-rule.delete 删除提成规则 🔴 · guide-commission-detail.batch-settle 批量标记提成结算 🔴🔴

---

## ✅ 创建提成规则 — `ops.marketing.guide-commission-rule.create`

- **风险**：🟡 可逆写（草稿可编辑/删除；建议先 conflict-check）
- **前置**：规则名称全局唯一（重名报「规则名称已存在」）；`effectiveEndTime` 若传必须**大于**开始时间。

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ruleName | String | ✅ | 规则名称，≤100 字符 |
| calculationType | String | ✅ | `percentage` / `category` / `ladder` / `combined` / `fixed` |
| scopes | Array | ✅ | 适用范围，≥1 条 |
| scopes[].scopeType | String | ✅ | `guide` 导购 / `level` 等级 / `store` 门店 |
| scopes[].rangeType | String | ✅ | `all` 全部 / `specified` 指定 / `excluded` 排除 |
| scopes[].scopeValue | String | 否 | 对象 ID（十进制字符串）；rangeType=all 传 null |
| priority | Integer | ✅ | 优先级，正整数，**数字越小越优先** |
| effectiveStartTime | String | ✅ | yyyy-MM-dd HH:mm:ss |
| effectiveEndTime | String | 否 | yyyy-MM-dd HH:mm:ss；不传 = 永久生效 |
| items | Array | ✅ | 规则细项，≥1 条 |
| items[].itemType | String | ✅ | `order_rate` 订单金额比例 / `category` 品类 / `cumulative_ladder` 累计阶梯 / `fixed_per_order` 每笔固定金额 |
| items[].itemValue | String | 否 | 品类 ID（category）；阶梯门槛（cumulative_ladder，管理端以万元数值录入） |
| items[].commissionRate | Number | ✅ | **小数形式比例**（0.05 = 5%；percentage/category/ladder/combined）；fixed 规则为**元金额** |
| items[].sortOrder | Integer | 否 | 排序号，阶梯细项按其升序匹配 |
| status | String | ✅ | 保存状态：`draft` 草稿 / `active` 直接启用 |

#### 细项组合约束（按 calculationType）

| calculationType | items 要求 |
|----------------|-----------|
| percentage | 1 条 `order_rate`，commissionRate 为统一比例 |
| fixed | 1 条 `fixed_per_order`，commissionRate 为每笔固定金额（元） |
| category | N 条 `category`，itemValue 为品类 ID，各自比例 |
| ladder | 1 条 `order_rate` 基础比例 + N 条 `cumulative_ladder` 阶梯加成 |
| combined | `category` 品类差异化 + `cumulative_ladder` 阶梯加成两类并存 |

#### 出参（原始数据）

- **关键字段来源**：返回值为新规则 `id`（十进制字符串）。

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-rule.create","input":{"ruleName":"Q4导购统一提成","calculationType":"percentage","scopes":[{"scopeType":"guide","rangeType":"all","scopeValue":null}],"priority":10,"effectiveStartTime":"2026-10-01 00:00:00","items":[{"itemType":"order_rate","commissionRate":0.05,"sortOrder":0}],"status":"draft"},"summary":"创建全店导购5%统一提成规则（草稿）"}
```

---

## ✅ 更新提成规则 — `ops.marketing.guide-commission-rule.update`

- **风险**：🟡 可逆写
- **前置**：规则存在且**未停用**（已停用规则不可编辑）；规则名称唯一（排除自身）；endTime > startTime。scopes/items **全量替换**（先删后插）——先读详情带上完整数据再改。

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则 ID |
| (其余字段) | - | - | 同创建，但**无 status 字段** |

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-rule.update","input":{"id":"5200000000000000001","ruleName":"Q4导购统一提成","calculationType":"percentage","scopes":[{"scopeType":"guide","rangeType":"all","scopeValue":null}],"priority":10,"effectiveStartTime":"2026-10-01 00:00:00","items":[{"itemType":"order_rate","commissionRate":0.06,"sortOrder":0}]},"summary":"把统一提成比例调整为6%"}
```

---

## ✅ 停用提成规则 — `ops.marketing.guide-commission-rule.disable`

- **风险**：🔴 不可逆——**无重新启用通道**，停用后该规则永久退出匹配（需用新规则替代）。
- **前置**：仅推导态「生效中」或「草稿」可停用；已过期/已停用报「仅生效中或草稿状态的规则可停用」。

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则 ID |

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-rule.disable","input":{"id":"5200000000000000001"},"summary":"停用误配置的提成规则"}
```

---

## ✅ 删除提成规则 — `ops.marketing.guide-commission-rule.delete`

- **风险**：🔴 不可逆（逻辑删除，含范围/细项子表）
- **前置**：仅推导态「草稿」（未停用且生效开始时间在未来）可删；其余状态报「仅草稿状态的规则可删除」。生效中规则须先停用再删。

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 规则 ID |

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-rule.delete","input":{"id":"5200000000000000001"},"summary":"删除废弃的草稿提成规则"}
```

---

## ✅ 批量标记结算 — `ops.marketing.guide-commission-detail.batch-settle`

- **风险**：🔴🔴 **资金面**——将待结算明细标记为已结算并写入结算时间。
- **前置**：仅 `pending` 状态的明细会被更新为 `settled`；**已结算的明细被静默跳过（不报错、不重复计）**。执行后应回查明细/统计核验结果。
- **建议**：先按 settlementStatus=pending 筛出明细确认范围再结算；不传校验回执，以执行后复查为准。

#### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| detailIds | String[] | ✅ | 明细 ID 列表，1..500 条 |

#### 调用示例

```json
{"capability":"ops.marketing.guide-commission-detail.batch-settle","input":{"detailIds":["5400000000000000001","5400000000000000002"]},"summary":"将两条待结算提成标记为已结算"}
```

---

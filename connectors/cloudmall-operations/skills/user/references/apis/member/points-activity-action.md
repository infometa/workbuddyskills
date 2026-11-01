# 会员域 — 积分活动写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points.md`；活动现值读取（分页/详情）先读 `points-activity-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.points-activity.create 创建积分活动 🔴 · member.points-activity.update 编辑积分活动 🔴 · member.points-activity.enable 启用 🔴 · member.points-activity.disable 停用 🔴 · member.points-activity.delete 删除 🔴

---

## ✅ 创建积分活动 — ops.member.points-activity.create

- 🔴 全租户配置——创建后为**停用**态；**pointsPerYuan（积分发放率）必须用户明确给出**；进阶字段（limitPeriod/expiry*/ruleContent）创建接口不写入，需创建后编辑补充

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityName | String | ✅ | 活动名称（≤50 字符，同租户唯一） |
| pointsPerYuan | Integer | ✅ | 每消费 1 分获取 X 积分（≥1 正整数） |
| itemConfigType | Integer | — | 0=全部商品 / 1=按类目 / 2=按商品 SKU；空时按提交内容推断 |
| categoryItems | Array | 条件 | itemConfigType=1 必填：[{categoryCode, categoryName}] |
| productItems | Array | 条件 | itemConfigType=2 必填：[{skuId}]（十进制字符串，来自商品域 SKU） |

`categoryItems[]` 子结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| categoryCode | String | ✅ | 类目编码（≤64 字符，来自商品域类目树） |
| categoryName | String | ✅ | 类目名称（≤100 字符） |

### 出参（原始返回）

创建结果对象（含活动 `id`）；回读 `points-activity.detail` 核验。

### 调用示例

```json
{"capability":"ops.member.points-activity.create","input":{"activityName":"消费送积分","pointsPerYuan":1,"itemConfigType":0},"summary":"创建全部商品消费送积分活动"}
```

---

## ✅ 编辑积分活动 — ops.member.points-activity.update

- 🔴 **部分更新语义**：未携带的数值/规则字段**保留旧值**（不置空）；但关联 items 为**先删后增**——可获/不可获积分清单须按意图完整提交（只传新增会清掉既有清单）；编辑前仍建议先 `points-activity.detail` 回读确认现值

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |
| activityName | String | ✅ | 活动名称（≤50 字符，唯一，排除自身） |
| pointsPerYuan | Integer | ✅ | 每消费 1 分获取 X 积分（≥1） |
| limitPeriod | String | — | 积分上限统计周期：`daily`/`weekly`/`monthly`（**服务端不校验值域**，须严格按此三值传） |
| dailyPointsLimit | Integer | — | 每人每周期积分上限；null=无限制 |
| expiryMode | Integer | — | 0=永久 / 1=固定日期 / 2=滚动过期 |
| expiryYearOffset | Integer | 条件 | expiryMode=1：过期年偏移（如 1=发放 1 年后） |
| expiryMonthDay | String | 条件 | expiryMode=1：过期月日，格式 `MM-dd`（**服务端不校验格式**，须自行把关） |
| expiryDays | Integer | 条件 | expiryMode=2：滚动过期天数 |
| itemConfigType | Integer | — | 0/1/2（同创建） |
| categoryItems / productItems | Array | 条件 | 可获积分范围（同创建；先删后增） |
| nonEarnableCategoryItems / nonEarnableProductItems | Array | — | 不可获积分范围（始终按提交内容保存） |
| ruleContent | String | — | 积分规则内容（富文本/纯文本） |

### 出参（原始返回）

`data` 为 `null`；回读 `points-activity.detail` 核验。

### 调用示例

```json
{"capability":"ops.member.points-activity.update","input":{"id":"1300012345678901234","activityName":"消费送积分","pointsPerYuan":1,"itemConfigType":0,"limitPeriod":"daily","dailyPointsLimit":1000,"expiryMode":0},"summary":"为活动补充每日积分上限"}
```

---

## ✅ 启用积分活动 — ops.member.points-activity.enable

- 🔴 商业影响——启用后 C 端按活动规则开始发积分；已启用的活动重复启用返回业务错误

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 出参（原始返回）

`data` 为 `null`；回读 `points-activity.search`/`detail` 核验 status=1。

### 调用示例

```json
{"capability":"ops.member.points-activity.enable","input":{"id":"1300012345678901234"},"summary":"启用积分活动"}
```

---

## ✅ 停用积分活动 — ops.member.points-activity.disable

- 🔴 商业影响——停用后 C 端停止按该活动发积分；已停用的活动重复停用返回业务错误

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 出参（原始返回）

`data` 为 `null`；回读核验 status=0。

### 调用示例

```json
{"capability":"ops.member.points-activity.disable","input":{"id":"1300012345678901234"},"summary":"停用积分活动"}
```

---

## ✅ 删除积分活动 — ops.member.points-activity.delete

- 🔴 逻辑删除不可恢复；**启用中的活动必须先停用**才能删除

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 出参（原始返回）

`data` 为 `null`；回读 `points-activity.search` 确认已移除。

### 调用示例

```json
{"capability":"ops.member.points-activity.delete","input":{"id":"1300012345678901234"},"summary":"删除已停用的积分活动"}
```

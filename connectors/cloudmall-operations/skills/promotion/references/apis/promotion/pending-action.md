# 促销域 — 促销审核链写操作契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-review.md`
> 审核链是活动与券模板创建/修改的唯一通道。编辑/提审带内容时必须传乐观锁 `version`（来自 pending 详情）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：写 pending.update · pending.submit · pending.withdraw · pending.approve · pending.reject 🔴 · pending.delete 🔴 · pending.start-edit
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）执行（单次提交、纯执行器语义，写操作纪律见 SKILL.md 通用约定）。
> **先读现值**：编辑/提审前用 `pending-query.md` 的 pending.detail 取 version 与完整表单快照，保留未改动字段。
> **编辑/提审写前必读**：`form-validation.md`。将修改合并到快照后检查日期、模式与SKU配置联动；保留未改字段不包括当前模式已失效的隐藏配置。

---

## ✅ 编辑审核草稿 — `ops.promotion.pending.update`

- 🟡 可逆写（草稿态修改，未提审不生效）
- **前置**：pending 处于草稿(0)/已驳回(3)。**先读 pending 详情取 version 与表单快照，保留未改动字段。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核草稿 ID（本文各能力中的 pendingId 均为此义） |
| version | Integer | ✅ | 乐观锁版本（来自 pending 详情；缺失报错，过期报冲突） |
| title | String | ✅ | 活动标题 |
| draft | Boolean | 否 | 默认 true 草稿宽松保存；false 强校验 |
| (其余字段) | - | - | 结构同 `ops.promotion.activity.create`（rules/goodsList/productScopeType/audienceType/presell 字段等） |

### 出参

- 无 data。成功回执确认保存完成；随后用 pending.detail 核对本次字段与 version，不能把草稿保存说成正式生效。

### 调用示例

以下为字段合并说明，不能把变量名当JSON字段发送。先查询pending.detail，从promotionDetail抽取创建请求形态的可编辑完整快照`editable`，保留现有日期、范围、人群、商品和互斥配置，剔除只读字段和旧operationValue；按specialty清理已失效配置。

```javascript
const input = {
  ...editable,
  pendingId: detail.pendingId,
  version: detail.version,
  title: '开学季满300减30',
  rules: [{ ruleIndex: 1, thresholdType: 'AMOUNT', thresholdValue: 30000,
    actions: [{ discountType: 1, feeType: 1, discountValue: 3000 }] }],
  draft: true,
};
```

检查合并后的完整配置，再以该input调用`ops.promotion.pending.update`；随后回读核对。此接口不是PATCH，省略的主要字段可被清空；带内容提审同样使用完整快照。券模板带内容保存/提审用券专用能力，不能走通用pending内容接口。

---

## ✅ 提审 — `ops.promotion.pending.submit`

- **两种用法**：① 只传 pendingId——直接提审既有草稿（服务端强校验后进入待审核）；② 同时带编辑内容（含 version）——同一事务内先保存再提审。
- **前置**：草稿(0)/已驳回(3)。提审即强校验（时间必须晚于当前、规则/商品/范围完整）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核草稿 ID（本文各能力中的 pendingId 均为此义） |
| (编辑内容) | - | 否 | 结构同pending.update的完整快照；不传则只提审。券模板带内容改用coupon-template.submit |

### 调用示例

```json
{"capability":"ops.promotion.pending.submit","input":{"pendingId":"4200000000000000001"},"summary":"提交满减活动审核"}
```

---

## ✅ 撤回审核 — `ops.promotion.pending.withdraw`

- 🟡 可逆写（回草稿态可再提审）
- **前置**：仅待审核(1)。变更重审撤回会同步解锁主表。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核草稿 ID（本文各能力中的 pendingId 均为此义） |

### 调用示例

```json
{"capability":"ops.promotion.pending.withdraw","input":{"pendingId":"4200000000000000001"},"summary":"撤回误提的审核"}
```

---

## ✅ 审核通过 — `ops.promotion.pending.approve`

- 🟡 审核动作
- **前置**：仅待审核(1)。新建审核通过 → 活动落主表（按审核时刻回算：开始时间已过→直接进行中；预热窗口内→预热；否则未开始）；变更重审通过 → 变更生效。⚠️ **结束时间已过的 pending 无法通过审核**（报"活动已过期，无法通过审核"），需先改期重新提审。
- **审核通过 ≠ 一定"未开始"**：补审已过开始时间的活动会直接进入进行中；执行后回读活动详情核验实际状态。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核草稿 ID（本文各能力中的 pendingId 均为此义） |
| reason | String | 否 | 审核意见。⚠️ **该字段服务端不校验**——通过接口未启用参数校验、服务层也无长度兜底，**可空、可纯空白、可超长**（与驳回不同，驳回是强校验非空）。纪律上仍建议 ≤512 字；仅传用户明确提供的意见，未提供时省略，不补写“规则配置无误”等判断 |

### 调用示例

```json
{"capability":"ops.promotion.pending.approve","input":{"pendingId":"4200000000000000001"},"summary":"通过满减活动审核"}
```

---

## ✅ 审核驳回 — `ops.promotion.pending.reject`

- 🔴 审核驳回——**reason 必填**（具体可行动的修改指引），禁止编造
- **前置**：仅待审核(1)。驳回后 pending 保留（改后可重提），主表解锁。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核草稿 ID（本文各能力中的 pendingId 均为此义） |
| reason | String | ✅ | 驳回原因，1..500 字 |

### 调用示例

```json
{"capability":"ops.promotion.pending.reject","input":{"pendingId":"4200000000000000001","reason":"优惠力度与预期不符，请调整门槛后重新提审"},"summary":"驳回满减活动审核"}
```

---

## ✅ 删除审核草稿 — `ops.promotion.pending.delete`

- 🔴 不可逆（物理删除）
- **前置**：仅草稿(0)/已驳回(3)；待审核不可删（先撤回）。变更重审草稿删除会解锁主表。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pendingId | String | ✅ | 审核草稿 ID（本文各能力中的 pendingId 均为此义） |

### 调用示例

```json
{"capability":"ops.promotion.pending.delete","input":{"pendingId":"4200000000000000001"},"summary":"删除废弃的活动草稿"}
```

---

## ✅ 发起变更重审 — `ops.promotion.pending.start-edit`

- 🟡 可逆写（仅生成变更草稿快照，提审才锁定）
- **前置**：**仅主表未开始(2)状态的活动可发起变更**（进行中/已结束活动不可改配置）；活动已有待审核 pending 时报错；已有草稿/驳回 pending 时**复用返回其 pendingId**（不新建）。
- **券模板变更重审**：同样支持——传券模板对应的**内部 promotionId**（来自 `coupon-template-query.md` 的 coupon-template.detail 出参 `promotionId` 字段，**不是 templateId**），服务端按主表自动派生券模板审核链并回填 templateId。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionId | String | ✅ | 活动 ID |

### 出参

- **关键字段来源**：返回值为变更草稿的 `pendingId`（十进制字符串）→ 后续编辑/提审。

### 调用示例

```json
{"capability":"ops.promotion.pending.start-edit","input":{"promotionId":"4100000000000000001"},"summary":"对未开始的满减活动发起变更重审"}
```

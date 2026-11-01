# 促销域 — 兑换码查询契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-coupon.md`
> 兑换码按批次发行，客户凭码兑换券（关联券模板）；明文码仅导出链路可见，开放查询只返回**脱敏码**。
> **兑换码消歧**：本文件查询平台生成的券码批次；品牌方提供码、用户输入领奖的互动活动属于营销域 `exchange-code`。本文件的 templates 是批次专用选择器，不是互动活动优惠券奖品的通用查询；后者先用 `coupon-template-query.md` 查询券模板，再回营销域关联奖品模板。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：查询 coupon-code.batches · batch-detail · templates · batch-codes · codes-search · batch-codes-search
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。
> 批次发行与作废（创建/生效/作废，均 🔴 高危）见 `coupon-code-action.md`。
>
> ⚠️ **ID 与明文码**：batchId/templateId/codeId 是十进制字符串 ID，必须原样取用户或查询返回值，不转 Number，不截断/补齐，也不凭“通常约 19 位”断言长度不符必然 400。非十进制标识需消歧，不猜 ID。明文码不是 ID，只用于 codes-search/batch-codes-search 的 **codes 数组**。当前生成器使用 12 位字符，字符集为 `23456789ABCDEFGHJKMNPQRSTUVWXYZ`；示例 `23456789ABCD` 仅演示结构，不代表真实存在。搜索会 trim 首尾空白并转大写，但不会删内部空白/横线或替换混淆字符。

---

## ✅ 兑换码批次分页 — `ops.promotion.coupon-code.batches`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| batchName | String | 否 | 批次名称模糊搜索 |
| status | String | 否 | 批次状态：`CREATING`/`FAILED_RELEASING`/`FAILED`/`INACTIVE`/`ACTIVE`/`VOIDING`/`VOIDED` |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].batchId`（→ 详情/生效/作废/码查询）、`records[].templateId`（→ 券模板）、`batchNo`（批次号，`CC+日期+批次ID`，对账/回显用）
- **枚举字段**：`batchStatus`（上述 7 态）、`generationStatus`（PENDING/RUNNING/SUCCESS/FAILED；**批次无生成任务时为 null**）
- **格式敏感字段**：`totalCount`/`claimedCount`/`voidedCount`/`remainingCount`（整数计数）、`generatedCount`（已生成数，无生成任务时为 0）、`createdBy`、`createdTime`/`activatedAt`/`voidedAt`（yyyy-MM-dd HH:mm:ss；**未生效/未作废时后两者恒为 null**）
- ⚠️ **两个计数字段的口径与字面含义不同**：`claimedCount` 取的是预占账本中的**已结算**数、`voidedCount` 取的是**已释放**数，都不是直接的事件计数；`remainingCount` = `totalCount − claimedCount − voidedCount`，仅 FAILED 强制为 0；FAILED_RELEASING 仍可能返回未释放余额。该字段不证明当前可兑码数量：必须结合 batchStatus，生成中/失败/待生效/作废中均不能据余额承诺可兑换。
- ⚠️ `templateName` 在关联券模板缺失/已删除时**为 null**——展示前要有兜底。

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.batches","input":{"pageNum":1,"pageSize":20,"batchName":"国庆"},"summary":"查询国庆兑换码批次"}
```

---

## ✅ 批次详情 — `ops.promotion.coupon-code.batch-detail`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batchId | String | ✅ | 批次 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 出参（原始数据）

- 同列表行结构（batchId/batchName/templateId/templateName/totalCount/claimedCount/voidedCount/remainingCount/batchStatus 等）。

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.batch-detail","input":{"batchId":"4800000000000000001"},"summary":"查看兑换码批次详情"}
```

---

## ✅ 可用券模板选项 — `ops.promotion.coupon-code.templates`

- 仅创建券码批次前选模板：筛选已配置库存且对应促销处于未开始/进行中的券模板。空结果只说明不满足制码资格，不代表普通券模板不存在；互动活动奖品关联走普通券模板查询，不使用本选择器。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| keyword | String | 否 | 模板名称关键词，也支持数字模板 ID 的精确匹配 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].templateId`（→ 创建批次）
- **枚举字段**：`promotionSubCode`、`promotionStatus`（NOT_START/IN_PROGRESS 等）
- **格式敏感字段**：`reservableStock`（当前可建批次的库存余量；**不限量或查询失败时为空——不得当 0 处理**）、`unlimited`（是否不限量）
- 查询失败时 unlimited 会回落 false 且 reservableStock 为 null；不能把 false 单独解释成“限量且库存为 0”。余量不可确认时暂停依赖数量的批次创建，不凭模板发行量补算库存。

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.templates","input":{"pageNum":1,"pageSize":20,"keyword":"满减"},"summary":"查询可用于发兑换码的满减券模板"}
```

---

## ✅ 批次码游标列表 — `ops.promotion.coupon-code.batch-codes`

- 按批次翻页浏览码状态（不需要明文码）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batchId | String | ✅ | 批次 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |
| afterId | String | 否 | 游标：上一页最后一条的 `codeId`，首页不传 |
| limit | Integer | 否 | 1..500，默认 100 |

### 出参（数组，原始数据）

- 每项：`codeId`（→ 单码作废）、`codeMasked`（**脱敏码**，B 端查询永不返回明文码）、`status`（INACTIVE 未生效 / ACTIVE 可用 / CLAIMED 已领取 / VOIDED 已作废）、`claimedMemberId`/`claimedCouponId`/`claimedAt`（领取信息，**未领取三者恒为 null**）。
- ⚠️ `status` 是**展示态推导值**，不是库里的原始状态：已领取即 CLAIMED；码或批次处于作废中/已作废一律归入 VOIDED（**看不到 VOIDING 过渡态**）；批次已生效才可能是 ACTIVE；其余为 INACTIVE。
- ⚠️ **敏感读**：返回领取会员 ID（claimedMemberId），后端每次查询以 IMPORTANT 级操作日志留痕。
- ⚠️ 本能力对批次不存在及CREATING/生成失败态均报「券码明细尚不可见」；不能凭这条错误断定批次正在生成。先按原batchId查batch-detail区分当前存在性和状态；查询失败不得当空结果。与batch-codes-search对不存在批次的错误文案不同。

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.batch-codes","input":{"batchId":"4800000000000000001","limit":100},"summary":"浏览批次内兑换码状态"}
```

---

## ✅ 按明文码查询 — `ops.promotion.coupon-code.codes-search`

- 客户报出明文码时核验状态（跨批次）
- 服务端只返回匹配且所属批次明细可见的码；格式不匹配、未匹配、所属批次为 CREATING/FAILED/FAILED_RELEASING 或批次不可见的输入均可能被省略。空数组只说明本次未返回可见匹配项，不能断言券码不存在/已作废，也不能补造未返回码的状态。规范化后重复输入不保证逐输入返回一行，不用数组下标强行对应客户提供的每个码。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| codes | String[] | ✅ | 明文兑换码列表，1..100 项，每项 ≤64 字符 |

### 出参（数组，原始数据）

- 同批次码列表项结构（codeId/codeMasked/status/领取信息）。

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.codes-search","input":{"codes":["23456789ABCD"]},"summary":"核验客户提供的兑换码状态"}
```

---

## ✅ 批次内按明文码查询 — `ops.promotion.coupon-code.batch-codes-search`

- 限定批次内核验
- 批次不存在报“券码批次不存在”，批次在生成中/生成失败时报“券码明细尚不可见”，不同于跨批次搜索静默省略该批次的行。批次可见时仍可能跳过无效或未匹配的输入；查询失败不得作为空结果。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batchId | String | ✅ | 批次 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |
| codes | String[] | ✅ | 明文兑换码列表，1..100 项，每项 ≤64 字符 |

### 出参（数组，原始数据）

- 同上。

### 调用示例

```json
{"capability":"ops.promotion.coupon-code.batch-codes-search","input":{"batchId":"4800000000000000001","codes":["23456789ABCD"]},"summary":"核验该码是否属于此批次"}
```

---

## ⛔ 未开放（本模块）

| 能力 | 原因 |
|------|------|
| 兑换码制卡导出链路（导出创建/列表/取消/下载） | 创建/下载端点要求调用方额外携带端侧操作权限标识参与鉴权（能力链不提供该入参 → 必然 400）；明文码亦属敏感资产，不经开放能力流转 |

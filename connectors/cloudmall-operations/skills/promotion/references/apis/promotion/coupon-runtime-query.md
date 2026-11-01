# 促销域 — 券实例查询契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-coupon.md`
> 本模块查询用户**已领取的券实例**（couponId）；模板定义见 `coupon-template-query.md`。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：查询 coupon.report · coupon.detail · coupon.library · coupon.check
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。
> 资金面高危写操作（发券/停用/退券/延期/解锁）见 `coupon-runtime-action.md`。
>
> ⚠️ **ID 格式口径**：`couponId`/`templateId` 必须使用用户明确提供或查询返回的十进制字符串 ID，保持原值，不转 Number，不补齐/截断。约 19 位只是常见外形，不能据长度断言对象不存在或必然 400；参数合法性按当前工具契约处理。非十进制标识先消歧，不猜 ID。写操作仍须读取现值并核对状态、权限与完整对象，不以 ID 能解析代替业务前置。

---

## ✅ 券报表 — `ops.promotion.coupon.report`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| totalIssued / totalUsed / totalExpired / totalCancelled | 发放 / 使用 / 过期 / 退废量（计数）；totalUsed包含锁定+已使用，与券模板列表只计已使用的usedCount不同；券模板详情usedCount也包含锁定 |
| usageRate | 使用率（4 位小数，如 0.2500） |

- 统计数据缺失时上游报错（活动未初始化统计），如实向用户转述。
- 本接口只返回累计计数与使用率，**没有当前可用券数量或实例运行态**。即使使用/过期/退废均为0，也不能把发放余量称为“当前可用”；活动结束、模板停用、未激活或锁定等条件不能从这些计数中排除。用户只问报表时按计数作答；若需判断某张券当前可用性，另查券详情/券库的 `usable`、运行态和原因，不臆造可用数量。

### 调用示例

```json
{"capability":"ops.promotion.coupon.report","input":{"templateId":"4300000000000000001"},"summary":"查看满减券发放与使用报表"}
```

---

## ✅ 券实例详情 — `ops.promotion.coupon.detail`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| couponId | String | ✅ | 券实例 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 出参（原始数据）

- **关键字段来源**：`couponId`（→ 停用/退券/延期/解锁）、`templateId`（→ 券模板详情/报表）、`memberId`（会员标识）、`orderNo`（最近关联订单）
- **枚举字段**：`status`（0..6 见 CouponInstanceStatus）、`couponType`（1 满减/2 折扣/3 兑换/4 运费）、`runtimeStatus`（available/used/expired/inactive）
- **格式敏感字段**：`useCondition` 为金额门槛（**分**）；`amount` 原样来自模板摘要，按券类型解释：`couponType=2` 为**折扣千分比**，展示折数的公式为 **`折数 = amount / 100`**（100=1折、850=8.5折）；若展示支付比例，公式为 `amount / 1000`（100=0.1，即原价的10%），不能将支付比例与折数混用。金额券的 `amount` 为分；兑换券/全免运费券不凭 `amount` 推导实际优惠额。实际规则及封顶须查模板规则。`acquireTime`/`expireStart`/`expireEnd`/`useTime` 为毫秒时间戳。
- `usable`=false 时 `unavailableReason` 给出不可用原因；可用时该字段为空。
- **其他回显字段**：`code`（券码）、`sourceType`（券来源）、`activitySceneType` / `useSceneId`（发放场景与场景 ID）、`runtimeStatusDesc`（运行态中文说明）、`promotionStatus` / `templateStatus`（活动与模板状态快照）——**不含操作人字段**。
- ⚠️ **两个「看似有值其实恒空/明文」的字段**：
  - `userPhone` **恒为空字符串**——发券时该字段即固定写空，不是脱敏也不是查询失败，永远取不到手机号。
  - `code` 是**券码明文**（未脱敏，原样返回）。属用户资产凭证，只在用户要求核对时转述，禁止写进备注/报告或批量导出到对话外。

### 调用示例

```json
{"capability":"ops.promotion.coupon.detail","input":{"couponId":"4400000000000000001"},"summary":"核对券实例状态与有效期"}
```

---

## ✅ 用户券库 — `ops.promotion.coupon.library`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| memberId | String | ✅ | 会员 ID（字符串；来自用户提供或用户域查询） |
| pageNum | Integer | ✅ | ≥1 |
| pageSize | Integer | ✅ | 1..100 |
| status | Integer | 否 | 券实例状态（0..6） |

### 出参（分页，原始数据）

- 券库行的**字段少于券实例详情**：有 `couponId`/`templateId`/`promotionId`/`name`/`couponType`/`status`/`statusDesc`/`useCondition`/`amount`/`acquireTime`/`expireStart`/`expireEnd`/`useTime` 与订单关联字段；**不含**详情的 `code`/`userPhone`/`activitySceneType`/`useSceneId`。**关键字段来源**：`records[].couponId`（→ 详情取完整信息）。

- **运行态字段**：`usable`、`runtimeStatus`、`runtimeStatusDesc`、`unavailableReason`、`promotionStatus`、`templateStatus`。`status`筛选的是券实例状态，不等于运行态可用；判断当前可用性结合上述字段及不可用原因，不把激活态券一概称为可用券。运行态受活动、模板及有效期影响，查询结果不代表完整订单结算校验或缓存已瞬时收敛。
- `useCondition` 与 `amount` 的单位沿用上方券实例详情；特别是 `couponType=2` 的 `amount` 是千分比，不是分。

### 调用示例

```json
{"capability":"ops.promotion.coupon.library","input":{"memberId":"900000000000000001","pageNum":1,"pageSize":20,"status":1},"summary":"查询会员的激活态券"}
```

---

## ✅ 核销预检 — `ops.promotion.coupon.check`

- 只读局部预检（不锁券不核销）：available只说明券实例状态、有效期和金额门槛通过；不检查活动/模板运行态、商品范围或完整结算条件。活动暂停/结束或模板停用后，应查coupon.detail或coupon.library的usable/runtimeStatus及原因，不能用本接口available=true证明券仍可使用。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| couponId | String | ✅ | 券实例 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |
| orderId | String | ✅ | 订单 ID（仅作为请求完整性字段，服务端核销预检不使用该值——只校验券状态/有效期/门槛） |
| orderAmount | Integer | ✅ | 订单金额，**单位分**，≥0 |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| available | 是否可用（状态激活 + 有效期内 + 金额达门槛） |
| discountAmount | 本接口**原样回传模板摘要 amount**，不是完整结算实际优惠额；金额券为分，折扣券为千分比（如100=1折），不能仅凭字段名把折扣值解读成“优惠1元”。本接口不返回券类型，需解释非零值时先用券详情确认 `couponType`。不可用分支恒 `0`。模板缺失时跳过门槛校验、返回值为 `0`，available仍可能为true，不能据此承诺可使用 |
| reason | 不可用原因；⚠️ **`available=true` 时恒为空字符串 `""`**——有值即代表不可用 |

### 调用示例

```json
{"capability":"ops.promotion.coupon.check","input":{"couponId":"4400000000000000001","orderId":"4500000000000000001","orderAmount":9900},"summary":"预检该券在99元订单上是否可用"}
```

---

## ⛔ 未开放（本模块）

| 能力 | 原因 |
|------|------|
| 券模板领用记录（claim-records） | 端点要求调用方额外携带端侧操作权限标识参与券种鉴权（能力链不提供该入参 → 必然 400），待后端改造后评估 |

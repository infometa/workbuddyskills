# 促销域 — 促销活动写操作契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-activity.md`
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本域**金额一律单位分（整数）、时间为毫秒时间戳、ID 为十进制字符串**，与商品域"元"的约定不同。
> 能力索引（前缀 `ops.promotion.`）：activity.create · activity.check · activity.pause · activity.resume · activity.stop · activity.delete
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）执行（单次提交、纯执行器语义，写操作纪律见 SKILL.md 通用约定）。
> **先读现值**：编辑/复制活动用 `activity-query.md` 的 `activity.goods-all` 取商品基线、`pending-query.md` 的 `pending.detail` 取草稿快照与 version；查询能力（搜索/详情/日志/统计）均在 `activity-query.md`。
> **创建写前必读**：`form-validation.md`（完整日期/价格/范围联动）；特殊类型同时读 `specialty.md`。字段各自合法不等于组合合法。

---

## ✅ 创建活动（审核草稿） — `ops.promotion.activity.create`

- 只在用户明确要求并确认关键字段后调用
- **执行语义**：单次提交、原样返回。超时/网络错误结果不确定——先用搜索按标题查是否已创建草稿，确认未创建才可重试。**创建即产生审核草稿，审核通过前不会生效**。

口令购正式提交禁止preheatStartTime；直降当前页面不配置预热，不能据此声称接口同样禁止。预热类型和完整日期检查见form-validation.md。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionSubCode | String | ✅ | 活动子类型（见 PromotionSubCode） |
| title | String | ✅ | 常规活动标题≤20字符；满赠/买赠原表单2..30字符，新建保存草稿/工作副本存在20字符入口差异，见 form-validation.md |
| draft | Boolean | 否 | 未传默认 true（草稿宽松校验）；**false = 创建即前置强校验**（校验失败整个创建回滚） |
| startTime / endTime | String | 条件 | 毫秒时间戳；草稿可空，提审时 now<startTime<endTime；定金预售同步为定金开始/结束，完整时序见 form-validation.md |
| preheatStartTime | String | 否 | 预热开始时间（毫秒时间戳；秒杀/预售/拼团/周期购使用），须早于活动开始；拼团额外至少提前5分钟，见 form-validation.md |
| rules | Array | 条件 | 统一规则（结构见下），规则类活动（满减/满折等）提审必填。约束：每满式（ruleAccType=2）只允许 1 条规则；阶梯式最多 5 条；门槛一般须 >0（买赠/运费券/兑换券例外）；满赠动作不配 feeType/maxDiscountValue |
| ruleAccType | Integer | 否 | 1 阶梯式（默认）/ 2 每满式 |
| productScopeType | String | 否 | `all`/`product`/`category`/`brand` |
| goodsList | Array | 条件 | 指定商品时必填（结构见下）。⚠️ productScopeType ≠ product 时禁止传 goodsList（买赠类 MYG/MJG/MG 例外）；同一 goodsRole 下 SKU 不得重复 |
| categoryCodes | String[] | 条件 | productScopeType=category 必填（类目编码，来自商品域类目树） |
| brandIds | String[] | 条件 | productScopeType=brand 必填 |
| storeIds | String[] | 否 | 指定门店ID列表。已确认全部门店时省略或传null；正式提交显式[]会报指定门店未选，草稿允许[]也不代表可提审。范围未知时不得利用省略/null扩大为全部，应先确认；权威快照中的省略/null可按ALL解释 |
| audienceType | String | 否 | `ALL`/`SPECIFIED`/`PASSCODE`（口令购 ENTERPRISE_PURCHASE 正式提交只能PASSCODE或SPECIFIED，不接受ALL；其他类型不支持PASSCODE，模式互斥） |
| audienceTagValueIds | String[] | 条件 | audienceType=SPECIFIED 必填（数据标签域标签值 ID） |
| passcode | String | 条件 | audienceType=PASSCODE 必填，1..20位英文字母或数字，服务端转大写（建议先用 passcode.check 预检） |
| stackableExclusions | Array | 否 | 互斥配置：`[{targetSubCode, conflict}]`（conflict 0=可叠加 1=互斥） |
| limitValue | Integer | 否 | 每人限购次数，≥0 |
| titleEn / description / descriptionEn / tag / imageUrl / qrcodeUrl | String | 否 | 物料与描述 |
| remark | String | 否 | 内部备注，≤100 字 |
| operationValue | Object | 否 | 规则 JSON。⚠️ **不要传**——后端按活动类型自动装配（规则类由 rules 装配 / 周期购拼团服务端独占生成，客户端提交会被忽略或直接报错）。五种形态见 specialty.md |
| presellType 等预售字段 | - | 否 | presellType（full_payment/deposit_expand）、depositStartTime/EndTime、balanceStartTime/EndTime（毫秒时间戳）、expandMode（MULTIPLIER/FIXED_AMOUNT）、expandMultiplier、deductAmount（分）、estimatedDeliveryTime——仅 PRESELL，**逐字段结构与条件必填见 specialty.md（含 SKU extJson 配套字段名陷阱）** |
| periodBuyConfig | Object | 条件 | 周期购活动级配置（仅 PERIOD_BUY，提审必填；**完整结构见 specialty.md**：periodPlans≤5 组/付费周期/配送方案/赠期规则，含三项硬约束） |
| grouponConfig | Object | 条件 | 拼团活动级配置（仅 GROUPON，提审必填；**完整结构见 specialty.md**：团有效期/在途团展示/模拟成团策略，含条件必填） |

`rules[]` 结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ruleIndex | Integer | 否 | 规则序号 |
| thresholdType | String | 否 | `AMOUNT` 金额 / `COUNT` 件数 / `NTH_ITEM` 第N件 / `AREA` 面积 |
| thresholdValue | Integer | 否 | 门槛值：**金额单位分**；件数为个数 |
| actions | Array | 否 | 优惠动作：`{discountType(1减免/2折扣/3固定价/5满赠；**4兑换仅兑换券 DH_COUPON 可用**且要求规则唯一、门槛0、thresholdType=AMOUNT、仅 1 个 action、feeType=1，且 discountValue/maxDiscountValue/freeShipping/gifts 均不传), feeType(1商品金额/2运费，金额型动作必填), discountValue(分或千分比850=8.5折；freeShipping=true 运费全免时可省，否则必填), maxDiscountValue(封顶分), freeShipping, gifts}`；满赠（5）**不传** feeType/maxDiscountValue。⚠️ `gifts` 为**预留透传字段**（后端零校验、运行时不消费、前端不传）——真赠品走 goodsList（goodsRole=2）+ extJson，见 specialty.md |

**兑换券商品范围**：DH_COUPON 的 goodsList 每行必须带真实 spuId/skuId 指定可兑范围，goodsRole 省略或为0/1，不能填赠品角色2；范围解析按SKU匹配并排除赠品行，不能用赠品行代替所选可兑商品。商品行 discountType/discountValue 不是兑换计价依据，不要求传4/0，也不反向禁止接口兼容字段。结算按规则在范围内选择当前剩余可优惠单价最高的一个商品单位，抵扣该单位的剩余可优惠额；回读确认目标SKU完整保留，不把草稿保存当作已提审或已兑换。

`goodsList[]` 结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | 条件 | SPU ID（productScopeType=product 且非草稿提交时必填且须有效；须先用真实商品数据核对SKU归属；周期购/拼团有服务端权威校验，不能假定所有类型均兜底） |
| skuId | String | ✅ | SKU ID |
| goodsRole | Integer | 否 | 0 默认 / 1 主品或MYG/MJG指定商品范围行 / 2 赠品 |
| sortNo | Integer | 否 | 排序号 |
| discountType / discountValue | Integer | 否 | 顶层单品价格字段；拼团及兑换券的价格走此处。SECKILL / DIRECT_DOWN / ENTERPRISE_PURCHASE 提审校验读取的是 SKU extJson 中同名字段，仅传顶层不能替代，见 specialty.md |
| stockPolicy | Integer | 条件 | 直降/口令购/秒杀/预售正式提交每SKU必填：1 LIMITED限量 / 2 UNLIMITED不限量。周期购由typed库存生成，拼团由开团配额生成，不套用此要求 |
| totalCount | Integer | 条件 | stockPolicy=1 必填且>0；=2 传null或省略，不得传0 |
| periodBuyGoodsConfig / grouponGoodsConfig | Object | 否 | 周期购/拼团 SKU 级配置（仅对应活动类型；**完整结构见 specialty.md**） |
| extJson | Object | 否 | SKU 级扩展配置。⚠️ **非自由透传**——按活动类型有互不兼容的固定键集（秒杀/直降/口令购价格、赠品、预售的键集见 specialty.md；周期购/拼团由服务端生成，客户端值被覆盖） |

### 出参

- **关键字段来源**：`pendingId`（→ 编辑/提审/撤回/审核/删除草稿/草稿期详情）、`promotionId`（预分配活动 ID，→ 审核历史；审核通过后才能用于主表详情/状态操作）
- 两字段均为十进制字符串。

### 调用示例

示例假设商品、门店和人群范围均已确认；券示例还已确认自然曝光渠道及领取控制。时间仅演示结构，真实执行须使用用户确认的窗口并重新检查当前时间，不照抄示例日期。

```json
{"capability":"ops.promotion.activity.create","input":{"promotionSubCode":"MYJ","title":"开学季满300减30","startTime":"1793498400000","endTime":"1794103200000","rules":[{"ruleIndex":1,"thresholdType":"AMOUNT","thresholdValue":30000,"actions":[{"discountType":1,"feeType":1,"discountValue":3000}]}],"productScopeType":"all","audienceType":"ALL","draft":true},"summary":"创建开学季满300减30活动草稿"}
```

---

## ✅ 暂停活动 — `ops.promotion.activity.pause`

- 可逆写（恢复可撤销）
- **前置**：普通活动 预热(3)/进行中(4)；拼团额外允许 未开始(2)。⚠️ 变更审核中不可暂停**仅限拼团**（报"活动正在变更审核中，暂不可暂停"）；普通活动变更审核中仍可暂停（有意保留的历史语义，Q005），恢复同理。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 调用示例

```json
{"capability":"ops.promotion.activity.pause","input":{"id":"4100000000000000001"},"summary":"暂停进行中的满减活动"}
```

---

## ✅ 恢复活动 — `ops.promotion.activity.resume`

- **前置**：仅已暂停(6)；已过结束时间的活动不可恢复（报"活动已结束"）。恢复后按当前时间回算落到 未开始/预热/进行中。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 调用示例

```json
{"capability":"ops.promotion.activity.resume","input":{"id":"4100000000000000001"},"summary":"恢复已暂停的活动"}
```

---

## ✅ 停用活动（提前结束） — `ops.promotion.activity.stop`

- 🔴 商业影响不可逆——活动立即对 C 端失效
- **前置**：未开始(2)/预热(3)/进行中(4)/已暂停(6) 均可停用；变更审核中不可停用。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 调用示例

```json
{"capability":"ops.promotion.activity.stop","input":{"id":"4100000000000000001"},"summary":"提前结束活动"}
```

---

## ✅ 删除活动 — `ops.promotion.activity.delete`

- 🔴 不可逆（逻辑删除，列表不再可见）
- **前置**：仅草稿(1)/未开始(2)；已生效过的活动禁止删除（改用暂停/停用）；拼团活动不支持删除；变更审核中不可删除。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 调用示例

```json
{"capability":"ops.promotion.activity.delete","input":{"id":"4100000000000000001"},"summary":"删除未开始的草稿活动"}
```

---

## ✅ 活动审核（通过/驳回合一） — `ops.promotion.activity.check`

- 🟡 审核动作（approved=true 通过）；🔴 approved=false 为驳回（商业影响——延迟上线/变更重审驳回即解锁主表），与 pending.approve / pending.reject 同一实现的合一入口
- ⚠️ **`id` 是 pendingId（审核草稿 ID），不是活动主 ID**——来自搜索 PENDING 行的 pendingId 或创建草稿响应。
- **前置**：pending 处于待审核(1)。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | pendingId |
| approved | Boolean | ✅ | true=通过（活动落主表）/ false=驳回 |
| reason | String | 条件 | 驳回时**必填**（服务端强校验非空，具体可行动），≤500 字；通过时仅传用户给出的意见，未提供则省略 |

### 调用示例

```json
{"capability":"ops.promotion.activity.check","input":{"id":"4200000000000000001","approved":true},"summary":"通过满减活动审核"}
```

---

## ⛔ 未开放（本模块）

| 能力 | 原因 |
|------|------|
| 重复入口 POST /admin/promotion/pending/create、PUT /admin/promotion/{id} | 与 activity.create / pending.update 同一实现的备用入口，已按主入口开放，避免重复登记 |

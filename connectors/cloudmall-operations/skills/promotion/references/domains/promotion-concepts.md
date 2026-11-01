# 促销域 — 实体模型与业务概念

> 实体模型、四层互斥、规则结构（rules 统一入参语义）、特殊活动配置要点、业务规则约束。
> 状态机迁移与枚举值查 `promotion-enums.md`（文中提及的 PromotionStatus/CheckStatus/CouponInstanceStatus 等枚举名均在其中）。
> 能力契约见 `references/apis/promotion/`，操作流程见 `references/flows/`。

---

## 核心实体

### 促销活动（Promotion）
- 活动主体，按 `promotionSubCode` 区分 23 种具体类型（见 `promotion-enums.md` 枚举字典；其中会员价/满元包邮/满件包邮暂未开放创建，实际可运营 20 种）。
- 关键字段：`promotionId`（活动 ID）、`title`/`titleEn`、`promotionCode`（大类 SINGLE_PRODUCT/MERCHANT/COUPON）、`promotionStatus`（7 态）、`promotionLevel`（1-4 层）、`startTime`/`endTime`/`preheatStartTime`（毫秒时间戳）、`operationValue`（规则 JSON）、`rules`（统一规则入参）、`goodsList`（参与商品，**提交入参结构**——详情出参不返回商品清单，查询商品走活动商品分页/全量能力）、`productScopeType`（all/product/category/brand）、`audienceType`（ALL/SPECIFIED/PASSCODE）、`passcode`（口令码）、`storeIds`、`stackableExclusions`（互斥配置）、`limitValue`（每人限购）、`remark`（≤100 字内部备注）。
- 列表/详情字段补充：`dataSource`（**`main`=主表 / `pending`=待审核表，小写字面量**）、`pendingId`（pending 行专属）、`checkStatus`（pending 为 0/1/3，主表还可为 2 已通过）、`sourceType`（0 新建 / 1 变更重审）、`hasPendingChange`（主表行专属：变更审核中 = editing_locked=1）、`displayStatus`（预售专用派生展示状态；搜索条件仅作粗粒度翻译，详见 activity-query.md）。

### 审核草稿（PromotionPending）
- 活动与券模板共用的审核载体（审核草稿表）；`bizType` 区分 `PROMOTION`（活动）/ `COUPON_TEMPLATE`（券模板）。
- 关键字段：`pendingId`（草稿 ID）、`promotionId`（关联活动 ID，新建审核时为预分配 ID）、`checkStatus`（0 草稿 / 1 待审核 / 3 已驳回）、`sourceType`（0 新建 / 1 变更重审）、`version`（乐观锁，编辑必传）、`promotionDetail`/`couponDetail`（详情快照）。
- **审核链是本域一切创建/编辑的唯一通道**：不存在"直接创建正式活动"，创建即产生 pending 草稿，提审通过后才落主表。

### 券模板（CouponTemplate）
- 券的定义（模板），复用促销审核链：`templateId` 为券域对外统一标识（内部映射 promotionId）。
- 券专属字段：`quantity`（发行量）、`acquireExpireStart/End`（可领取时间窗）、`useExpireType`（1 固定时间段 / 2 领取后 N 秒）、`useExpireStart/End`、`useExpireDuration`（秒）、`channelCodes`（业务领券渠道：1 自然曝光 / 2 分销；空=不向自然曝光/分销入口开放，仅内部发券等链路可发；业务上互斥不应同选——服务端不强制拦截，双渠道数据按分销优先、自然曝光失效，构造参数时应主动避免同传）、`personalLimit`/`personDailyLimit`（限领，0/null=不限）、`maxStack`（通常1..50、默认1；兑换券显式非1拒绝，缺省归一为1）。
- 支持分享物料：分享能力查询、微信太阳码、微信短链接。

### 券实例（CouponInstance）
- 用户领取到的券，`couponId` 为实例 ID（区别于 `templateId`）。
- 关键字段：`memberId`（会员 ID，字符串）、`status`（见 CouponInstanceStatus）、`useCondition`（使用门槛，分）、`amount`（模板摘要：折扣券 `couponType=2` 为千分比，如850=8.5折；金额券为分；兑换/全免运费不凭该值推导实际优惠额）、`acquireTime`/`expireStart`/`expireEnd`/`useTime`（毫秒时间戳）、`orderNo`/`currentOrderNo`（订单关联）、`runtimeStatus`（运行态可用性 available/used/expired/inactive）。

### 兑换码批次（CouponCodeBatch）
- 兑换码按批次发行：`batchId`、`batchName`、`templateId`（关联券模板）、`totalCount`、`batchStatus`（见状态机）、`claimedCount`/`voidedCount`/`remainingCount`。
- 单码：`codeId`、`codeMasked`（脱敏展示）、`status`（INACTIVE/ACTIVE/CLAIMED/VOIDED；作废走 VOIDING 过渡态两阶段完成）。

### 赠品池（GiftPool）
- 赠品 SKU 库存池，**SPU 维度聚合展示**（列表一行=一个 SPU，`skuDetails` 展开 SKU 明细）。
- 关键字段：`giftPoolId`（SKU 维度记录 ID；列表行的 giftPoolId 仅对应 SPU 第一条 SKU）、`spuId`/`skuId`、`productStatus`（**当前实现仅返回 in_use / available 两态**——下架/全零库存的组合状态计算未接商品数据，off_shelf/out_of_stock 现版本不可达）、`linkedActivityCount`（关联商品行计数、不按活动去重且可能含MG主品；只统计未开始/预热/进行中的MYG/MJG/MG，0不能排除暂停/草稿引用）。
- ⚠️ `realStock`/`productPrice` 等商品富化字段当前版本不返回；移除赠品服务端**不校验引用数**（详见契约 gift-pool-action.md）。

### 促销主题（PromotionTheme）
- 促销日历的分组容器：`themeId`、`name`、`startTime`/`endTime`、`promotionIds`、`activityCount`、`revision`（**主题乐观锁**——所有主题写操作必传 expectedRevision，从 `theme.detail` 取当前值（**create 例外：固定传 0**，新主题无 detail 可读）；不匹配报「主题已被修改，请刷新后重试」）。
- 删除主题不删活动（成员自然转为未归属）。
- 跨主题移动活动时还需携带**源主题**的乐观锁（`sourceThemeRevisions` = Map<源主题ID, 源主题revision>；未归属活动传空对象）。

### 活动库存池（StockPool）
- 单品促销活动（周期购等）的限量库存：`stockPolicy`（1 LIMITED / 2 UNLIMITED）、`totalCount`、`availableCount`。

---

## 四层互斥模型

活动按 `PromotionSubCode` 的 layer 分四层（运营口径）。**叠加/互斥以 `stackable-rules` 能力返回与实例级配置为准**；无显式规则时计算引擎按三级 fallback 兜底（实例级配置 → 类型级预置规则 → 跨层叠加、同层异权重叠加、同层同权重且商品范围有交集才默认互斥）——「同层」并不必然互斥：

| 层 | 包含活动 | 互斥规则 |
|----|---------|---------|
| 1 单品层 | 秒杀/预售/直降/会员价/口令购/拼团/周期购 | 同一 SKU 只能参加一个单品层活动 |
| 2 店铺层 | 满元减/满件减/第N件减/满元折/满件折/第N件折/N件Y元/满元赠/满件赠/买赠 | 同一订单只能有一个店铺层活动 |
| 3 券层 | 满减券/折扣券/兑换券 | 不同模板的商品券默认互斥（可经叠加规则放开）；**同一模板**可叠加至maxStack张（通常1..50，兑换券固定1） |
| 4 免运费层 | 运费券/满元包邮/满件包邮 | 一笔订单最多一个免运费优惠 |

运营可通过 `stackableExclusions`（`[{targetSubCode, conflict}]`，conflict 0=可叠加 1=互斥）配置跨层互斥例外。创建前用叠加规则查询能力核对目标 subCode 的默认互斥关系。

---

## 规则结构（rules 统一入参）

```
rules[]: { ruleIndex, thresholdType, thresholdValue, actions[] }
  thresholdType: AMOUNT（金额门槛）/ COUNT（件数）/ NTH_ITEM（第N件）/ AREA（面积）
  thresholdValue: 金额单位分；件数为个数
  actions[]: { discountType, feeType, discountValue, maxDiscountValue, freeShipping, gifts }
    discountType: 1 减免 / 2 折扣 / 3 固定价 / 4 兑换 / 5 满赠（与枚举字典 DiscountType 券优惠类型同名异义）
    feeType: 1 商品金额 / 2 运费（金额型动作必填；满赠不传）
    discountValue: 减免/固定价单位分；折扣为千分比（850=8.5折）
    maxDiscountValue: 封顶金额（分，仅满折配置封顶时传）
```

- `ruleAccType`：1 阶梯式（默认）/ 2 每满式。
- 上述规则金额用**分**（整数），折扣用千分比（整数）；周期购等元单位字段及商品清单解析价格的例外统一见 `SKILL.md` 通用约定，不能把所有价格都按分换算。
- ⚠️ `actions[].gifts` 为**预留透传字段**（零校验、运行时不消费、前端不传）——真赠品走 goodsList（goodsRole=2）+ extJson（activityStock/giftPoolItemId）。

### 特殊活动类型配置（结构详见 `references/apis/promotion/specialty.md`）

- **周期购 PERIOD_BUY**：`periodBuyConfig`（periodPlans≤5 组——cycleWeeks 不重复、deliveriesPerCycle 恒 1、cycleWeeks×maxPaidPeriods≤51；付费周期区间；earliestDeliveryDays；可选 giftRule 买 X 送 Y）+ SKU 级 `periodBuyGoodsConfig`（activityPrice **元**、activityStock 强制 LIMITED、单次购买区间）。**客户端传 operationValue/rules 直接报错**（服务端独占生成）。
- **拼团 GROUPON**：`grouponConfig`（团有效期模式 CUSTOM/FOLLOW_ACTIVITY_END——条件必填 customDurationMinutes 15min~30天；在途团展示；模拟成团 DISABLED/ALL/THRESHOLD——阈值须 < 全部 SKU 最小成团数）+ SKU 级 `grouponGoodsConfig`（targetCount 2..100 含团长、perMemberLimit 1..10、maxGroupCount 开团配额）。拼团价走 goodsList 的 discountType=3+discountValue（分）；标题 ≤20 字；预热提前 ≥5 分钟。
- **预售 PRESELL**：typed 字段组（presellType full_payment/deposit_expand、定金/尾款窗口、expandMode MULTIPLIER/FIXED_AMOUNT、estimatedDeliveryTime）+ **SKU extJson 配套键**（discountType=3+discountValue=预售总价分、depositAmount 定金、expandMultiplier/expandDeductAmount——⚠️ 膨胀/抵扣的活动级校验读的是 extJson 键不是 typed 字段）。
- **extJson 键集按活动类型互不兼容**：周期购/拼团由服务端生成（客户端值被覆盖）；预售/买赠客户端提交（键集见 specialty.md）；详情回显会追加 remainingStock/soldCount 等运行态键。
- **operationValue 五形态**（规则类后端装配 / 秒杀直降口令购无规则 / 周期购服务端独占 / 拼团服务端覆盖 / 预售双通道）——一律不传，由后端处理。

---

## 业务规则要点

- **创建即草稿**：`draft`未传时默认true，通常宽松保存；DH叠加及周期购等已携带typed配置仍有专属校验，不能一概称仅查标题；`draft=false`（或提审）触发完整强校验（时间、规则、商品、范围逐项校验）。
- **编辑必带乐观锁**：pending 编辑/提审**带编辑内容时**必须传 `version`（来自 pending 详情），版本过期报冲突需刷新重取；只传 pendingId 的直接提审不要求客户端传 version。
- **商品范围**：`productScopeType` = all（全场）/ product（指定商品，配 goodsList）/ category（配 categoryCodes）/ brand（配 brandIds）。
- **适用人群**：ALL / SPECIFIED（配 `audienceTagValueIds` 标签值 ID，来自数据标签域）/ PASSCODE（配 `passcode` 口令码，≤20 字符；口令码在**提审或 draft=false 创建**时预占，被占用导致提审失败；**审批通过时**后端联动数据标签域物化动态人群包——草稿态创建不做占用校验，可先用口令码校验能力预检）。
- **活动库存**：单品层活动的 `goodsList[]` 支持 `stockPolicy`（1/2）+ `totalCount`（LIMITED 必填>0，UNLIMITED 必须为 null）；进行中的有限库存活动可通过库存增加能力补库存（正增量，幂等批次号）。
- **发券前置**：券模板对应活动须 IN_PROGRESS 且审核通过、未停用、在可领取时间窗内、库存充足、未超个人限领；发券带 `requestId` 幂等（同参数重试安全，换参重试报冲突）。
- **赠品库**：SKU 加入赠品库不设置库存（库存取商品实物库存）；移除前应查引用数（**服务端不校验引用数，引用>0 也会删除**——计数0不能排除口径外引用，仍须核对关联影响）。

---

## 跨域引用

- 引用：商品域（goodsList/skuId、类目编码、品牌 ID）、数据标签域（人群标签值、口令码人群包）、用户域（发券 memberId）。
- 被引用：营销域（活动作为投放内容）、装修域（页面组件）、交易域（结算时应用优惠）。

门店入参：已确认全部时省略/null，正式提交[]拒绝；详情派生空数组不可原样当入参。口令购正式人群仅PASSCODE/SPECIFIED，口令为1..20位英文字母数字并转大写，且禁止预热。

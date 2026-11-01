# 促销域 — 特殊活动类型配置契约（周期购 / 拼团 / 预售 / 买赠）

> 概念知识：`references/domains/promotion-concepts.md`；通用创建流程：`references/flows/promotion-review.md`
> 本文件展开四类特殊活动在 `activity.create` / `pending.update` 入参中的 **Object/嵌套配置结构**（逐字段对照服务端校验行为与前端构造逻辑核验）。
> 创建/编辑/提审还须读取 `form-validation.md` 的日期、价格与模式联动，不能只检查本文件单字段条件。
> 状态标记：✅ 已开放；⛔ 未开放。

---

## 周期购（PERIOD_BUY）

### 活动级 `periodBuyConfig`（提审必填；草稿可空——draft=true 且缺配置时仅校验标题）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| periodPlans | Array | ✅ | 配送方案，1..5 组（结构见下） |
| minPaidPeriods | Integer | ✅ | 最小付费周期数，≥1 且 ≤ maxPaidPeriods |
| maxPaidPeriods | Integer | ✅ | 最大付费周期数，≥1 |
| earliestDeliveryDays | Integer | ✅ | 最早配送天数，≥0 |
| giftRule | Object | 否 | 一次性买 X 期送 Y 期（结构见下） |

**硬约束（服务端校验）**：①每组 `cycleWeeks × maxPaidPeriods ≤ 51`；②`cycleWeeks` 组间不得重复；③**`deliveriesPerCycle` 只允许 1**（本期硬约束，传其他值报错）。

`periodPlans[]` 结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| cycleWeeks | Integer | ✅ | 周期长度（周），≥1 |
| deliveriesPerCycle | Integer | ✅ | 每周期配送次数——**固定传 1** |

`giftRule` 结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| buyPeriods | Integer | ✅ | 买 X 期，必须在 [minPaidPeriods, maxPaidPeriods] 区间内 |
| giftPeriods | Integer | ✅ | 送 Y 期，正整数；maxPaidPeriods + giftPeriods 不得溢出（≤2147483647）；51周限制只计付费周期 |

### SKU 级 `goodsList[].periodBuyGoodsConfig`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityPrice | String/Number | ✅ | 周期购单价，**单位元**（0.01 起，两位小数——服务端乘 100 转分存 discountValue，**本域唯一的元单位入参**，超两位小数报错） |
| activityStock | Integer | ✅ | 活动库存，≥1；服务端**强制** stockPolicy=LIMITED 且 totalCount=activityStock（顶层 stockPolicy/totalCount 无需传） |
| singlePurchaseMin | Integer | ✅ | 单次最少购买周期数，≥1 |
| singlePurchaseMax | Integer | ✅ | 单次最多购买周期数，≥ singlePurchaseMin |
| deliveryLeadTimeMinDays / MaxDays | Integer | 否 | 已废弃字段（保留兼容，服务端忽略传值） |

### 服务端行为（⚠️ 必读）

- **提交 `operationValue` 或 `rules` 会直接报错**——周期购规则由服务端从 periodBuyConfig 独占生成（组合规则模型与参与模式均为服务端内建，创建入参没有这两个字段），禁止自行传规则。
- 详情出参 `periodBuyConfig` 为入参同构回显（服务端反解）；`operationValue` 恒为 null；每个商品项附 `periodBuyGoodsConfig` + `activityStock`/`unlimited` + `periodBuyGoodsStockView {skuId, totalCount, availableCount}`（UNLIMITED 时两 count 为 null）。

---

## 拼团（GROUPON）

### 活动级 `grouponConfig`（提审必填）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| durationMode | String | ✅ | `CUSTOM` 自定义团有效期 / `FOLLOW_ACTIVITY_END` 跟随活动结束 |
| customDurationMinutes | Integer | 条件 | 仅 CUSTOM 必填，15..43200 分钟（15 分钟~30 天）；FOLLOW_ACTIVITY_END 时**不传**（服务端强制置 null） |
| onlineRecruitingEnabled | Boolean | ✅ | 商详页是否展示在途团；DTO缺省false，运营页新建默认true。按用户确认值构造，不把页面默认当接口默认 |
| simulationMode | String | 否 | `DISABLED` 不模拟（默认）/ `ALL` 全部模拟成团 / `THRESHOLD` 阈值模拟 |
| simulateThresholdCount | Integer | 条件 | 仅 THRESHOLD 必填，≥1，且**必须 < 全部 SKU 的最小 targetCount**；非 THRESHOLD 不传（服务端强制置 null） |

### SKU 级 `goodsList[].grouponGoodsConfig`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| targetCount | Integer | ✅ | 成团人数（含团长），2..100 |
| perMemberLimit | Integer | ✅ | 每人开团+参团合计上限，1..10，默认 2 |
| maxGroupCount | Integer | ✅ | 开团配额（最多正式团数），1..100000——服务端写入开团配额库存池 |

### 拼团价与附加约束

- **拼团价不在 grouponGoodsConfig 内**：走 `goodsList[].discountType=3`（固定价）+ `discountValue`（分）——服务端强校验全部 SKU 必须此形态且 >0。
- 活动标题 ≤20 字符；预热开始须提前 ≥5 分钟；SKU ≤100 个且不重复。
- 详情出参 `grouponConfig` 为服务端规范化后的回显（FOLLOW_ACTIVITY_END 时 customDurationMinutes=null、非 THRESHOLD 时 simulateThresholdCount=null——**可能 ≠ 前端原提交值**）。

---

## 预售（PRESELL）

### 活动级 typed 字段（无 Bean 注解，服务端运行时校验）

| 字段 | 类型 | 必填条件 | 说明 |
|------|------|---------|------|
| presellType | String | ✅ | `full_payment` 全款预售 / `deposit_expand` 定金膨胀。⚠️ 服务端另隐性支持 `deposit_deduct`（定金抵扣，读 SKU 扩展配置里的尾款抵扣额）——接口文档与前端均未声明，**非约定契约勿主动使用** |
| depositStartTime / depositEndTime | String(ms) | presellType ≠ full_payment | 定金支付窗口；depositStart < depositEnd ≤ balanceStart（服务端仅拒绝 depositEnd > balanceStart，相等允许） |
| balanceStartTime / balanceEndTime | String(ms) | 同上 | 尾款支付窗口；四时间戳均须晚于当前时间 |
| expandMode | String | deposit_expand | `MULTIPLIER` 倍数膨胀 / `FIXED_AMOUNT` 定额抵扣 |
| expandMultiplier | Number | deposit_expand + MULTIPLIER | 膨胀倍数，服务端≥1，前端输入1..10；同步到每SKU同名键 |
| deductAmount | Integer | 否 | 抵扣金额（分），>0——仅落 operationValue **不参与服务端校验**（校验读 extJson.expandDeductAmount） |
| estimatedDeliveryTime | String(ms) | ✅ | 预计发货时间：定金类须 > balanceEndTime；全款类须 > 活动 endTime；改期/模式切换必须重验完整时间链，见 form-validation.md |

### ⚠️ SKU 级 extJson 配套（字段名陷阱，最易拼错）

每个预售SKU正式提交同时带顶层显式库存：activityStock为正整数n时，stockPolicy=1、totalCount=n；activityStock=0不限量时，stockPolicy=2、totalCount=null或省略。与extJson.activityStock一致，只传extJson库存不足以提审。历史持久数据恢复的兼容推导不适用于新建/更新/提交请求，不能据此省略显式配置。

预售 SKU 的价格/定金/膨胀配置走 `goodsList[].extJson`（**不是**活动级 typed 字段）：

| extJson 键 | 类型 | 必填 | 说明 |
|------|------|------|------|
| discountType | Integer | ✅ | **必须 3**（固定价） |
| discountValue | Integer | ✅ | **预售总价（一口价，分）**——不是折扣额 |
| activityStock | Integer | ✅ | 活动库存，≥0 |
| limitPerUser | Integer | ✅ | 每人限购，≥0 |
| depositAmount | Integer | 定金类必填 | 定金（分），必须 < 预售总价 |
| expandMultiplier | Number | MULTIPLIER | SKU 级膨胀倍数，≥1；抵扣按定金分×double倍率后截断取整，须使尾款应付>0（浮点边界见 form-validation.md）——**活动级校验实际读的是这个键**（typed 值只落 operationValue） |
| expandDeductAmount | Integer | FIXED_AMOUNT | SKU 级抵扣额（分），>0 且严格<（预售总价−定金），否则尾款≤0被拒——**FIXED_AMOUNT 校验读这个键**（活动级 deductAmount 落 operationValue 但不参与校验），两个名字不同切勿混淆 |

### 出参回显

详情回显时 extJson 会追加 `remainingStock`（剩余库存）/`soldCount`（已售）等只读运行态键，编辑不当输入回传。`limitPerUser`仍是有效的限购配置，编辑须保留或按用户意图修改，不能连同运行态键丢弃。

---

## 买赠 / 满赠（MG / MYG / MJG）出参结构与赠品真通道

### `rules[].actions[].gifts` 是预留透传字段（⚠️ 勿用）

`{spuId, skuId, quantity}` 三字段**后端零校验、运行时不消费、前端从不传**——C 端计算引擎解析赠品只读 `goodsList` 中 goodsRole=2 的行（quantity 硬编码 1）。**真赠品通道**：goodsList（goodsRole=2）+ extJson 键集（见下）。

### 赠品 SKU 的 extJson 键集（MYG/MJG/MG，goodsRole=2 行）

| 键 | 类型 | 必填 | 说明 |
|----|------|------|------|
| activityStock | Integer | ✅ | 赠品限量数，必须为JSON非负整数字面量，不传字符串数字——**0 = 不限量**（与常规语义相反）；SKU 级唯一 |
| giftPoolItemId | Integer | ✅ | 赠品库条目主键ID（联动赠品池in_use标记），不是业务giftPoolId也不是skuId——从 `gift-pool.search` 的 skuDetails[].giftPoolItemId 取 |

### detail 出参 `giftItems[]`（按 SPU 分组，赠品行）

`spuId` / `spuName`（Feign 商品名，失败降级空串）/ `skuList[]`：`skuId`、`skuName`、`activityStock`（限量数；UNLIMITED 时 null）、`unlimited`（true=不限量 / false=限量 / **null=库存元数据不可确认，不得按不限量展示**）、`giftPoolItemId`。

### detail 出参 `mainProducts[]`（仅 MG 买赠，主品行 goodsRole=1）

`spuId` / `spuName` / `spuImage` / `skuList[{skuId, skuName, price(分)}]`。约束：赠品/主品至少各 1 个；主品 SPU 去重 ≤1000。

---

## 秒杀 / 直降 / 口令购的 SKU 价格（SECKILL / DIRECT_DOWN / ENTERPRISE_PURCHASE）

这三类活动提审时从 `goodsList[].extJson` 校验价格，再将其写入顶层价格列；只传顶层 discountType/discountValue 会报“缺少价格配置”。草稿可宽松保存，不代表已满足提审条件。

| extJson 键 | 类型 | 必填 | 说明 |
|---|---|---|---|
| discountType | Integer | 提审必填 | 固定 `3`（一口价） |
| discountValue | Integer | 提审必填 | 一口价，单位分，>0；如 99 元传 9900 |
| limitPerUser | Integer | 否 | SKU 每人限购数，≥0，0 不限 |

库存仍用同一 SKU 行顶层的 `stockPolicy` / `totalCount`，不以 extJson.activityStock 代替显式库存配置。口令与人群参数另按活动 create 契约填写。

---

## extJson 键集总表（SKU 级，按活动类型互不兼容）

| 活动类型 | extJson 用法 |
|---------|-------------|
| 周期购 PERIOD_BUY | **服务端生成**（typed 的 periodBuyGoodsConfig 编码落库）——客户端传值被覆盖 |
| 拼团 GROUPON | **服务端生成**（grouponGoodsConfig 原样序列化）——客户端传值被覆盖 |
| 预售 PRESELL | 客户端提交（键集见预售节）；每行还需顶层stockPolicy/totalCount；remainingStock/soldCount只读，limitPerUser是有效配置须保留 |
| 买赠 MYG/MJG/MG | 客户端提交（赠品行 activityStock/giftPoolItemId；主品行不使用） |
| 秒杀 / 直降 / 口令购 SECKILL / DIRECT_DOWN / ENTERPRISE_PURCHASE | 客户端提交 SKU 价格 discountType / discountValue 及可选 limitPerUser；库存另走顶层 stockPolicy / totalCount，见上节 |

---

## operationValue 五种形态（统一规则 JSON，服务端视角）

| 活动类型 | 形态 | 客户端约束 |
|---------|------|-----------|
| 规则类（满减/满折/满赠/兑换券等） | 后端由 rules 装配 `{ruleAccType, conditionAndAction[]}`，**覆盖**客户端传入值 | 传 rules，不传 operationValue |
| SECKILL / DIRECT_DOWN / ENTERPRISE_PURCHASE | 无规则：rules/ruleAccType/operationValue 全部清 null | 都不传 |
| 周期购 PERIOD_BUY | 服务端独占生成 canonical 结构 | **传 operationValue 或 rules 直接报错** |
| 拼团 GROUPON | 服务端覆盖为 grouponConfig JSON | 不传 |
| 预售 PRESELL | 双通道：operationValue 为空时由 typed 预售字段装配；非空时透传 | 传 typed 字段，不传 operationValue |

---

## detail 出参 rules 回映射差异（与入参形态不同）

1. `ruleIndex` 为回映射数组下标（0 起），非客户端原值；
2. 一个 doAction 的多个 actionParams 元素被**展开为多条独立 action**；
3. 满赠 action 回显为单条 `{discountType:5, gifts:[...]}`（feeType/discountValue 为 null）；
4. `maxDiscountValue` 为 0 或负时回显为 null；
5. **摘要不在 rules 内**：`ruleDescription` 是**详情顶层的字符串字段**（整条规则的中文摘要，如「满100元减10元」），单条 `rules[]` 元素**没有**这个字段（规则项只有 ruleIndex / thresholdType / thresholdValue / actions 四个字段）；
6. **周期购/拼团详情无 rules**（结构不同）。

⚠️ 编辑场景勿把出参 rules 原样回传——编辑基线用 `pending.detail` 的 promotionDetail/couponDetail 快照（创建请求形态）。

## 编辑与页面私有草稿

- 周期购extJson.periodBuyDraft、拼团extJson.grouponDraft是页面未完成草稿快照，回填优先于typed配置。完整canonical配置已经形成且不再需要旧未完成信息时，仅清除相应旧键再保存；否则可能重新打开仍显示旧标题、商品和配置。未完成草稿不能盲删，其他有效extJson仍保留。
- 周期购draft=true且缺periodBuyConfig才允许先建后补；带config仍须满足配置、SKU与基础价规则。此时不能靠draft跳过不完整config校验。
- MYG/MJG指定商品范围行用goodsRole=1，赠品行用2；MG主品同样为1。giftPoolItemId取skuDetails[].giftPoolItemId，不用giftPoolId替代。
- 正式预售发起变更后，应核对完整typed模式/日期/逐SKU配置。当前某些工作副本回填可能只保留operationValue而漏typed字段；信息不足先补查或由原页面恢复，不能只改标题就把缺失配置当成用户清空。

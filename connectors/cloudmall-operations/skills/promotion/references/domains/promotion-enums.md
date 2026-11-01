# 促销域 — 状态机与枚举字典

> 查值字典：状态机迁移与前置、枚举值精确拼写（大小写以本表为准）。
> 查状态含义、确认操作前置、取枚举值时读本文件；实体模型/规则结构/业务约束见 `promotion-concepts.md`。
> 能力契约见 `references/apis/promotion/`，操作流程见 `references/flows/`。

---

## 状态机

### 促销活动状态（PromotionStatus，整数 code）

```
DRAFT(1) → NOT_START(2) → PREHEAT(3) → IN_PROGRESS(4) → ENDED(5)
                ↑            │              │
                │            ↓              ↓
                └──────── PAUSED(6) ←───────┘

DELETED(7) ← 仅 DRAFT / NOT_START 可删除（已生效过的活动禁止删除）
```

- 创建审核通过后按审核时刻回算落主表：开始时间已过 → 直接进行中；处于预热窗口 → 预热；否则未开始。**结束时间已过的 pending 无法通过审核**（报「活动已过期」，需改期重新提审）。此后按时间自动流转（预热→进行中→已结束）。
- 暂停：普通活动 PREHEAT/IN_PROGRESS → PAUSED（拼团额外允许 NOT_START）。
- 恢复：PAUSED → 按当前时间回算（未开始/预热/进行中；已过结束时间不可恢复）。券类型特例：startTime=null（useExpireType=2 领取后生效）的模板恢复后直接落进行中。
- 停用（提前结束）：NOT_START / PREHEAT / IN_PROGRESS / PAUSED → ENDED，**不可逆**。
- 变更审核中（editing_locked=1）时禁止：删除、停用、再次发起变更、再次编辑（暂停/恢复不受限——仅拼团活动变更审核中不可暂停）。

### 审核状态（CheckStatus，pending 行）

```
草稿(0) ⇄ 提审 → 待审核(1) → 通过 → 落主表（按审核时刻回算：未开始/预热/进行中）
              ↑        │
              撤回      ↓
              └── 已驳回(3) → 编辑 → 回到草稿态继续修改
```

- 草稿(0)/已驳回(3) 可编辑、可提审、可删除；待审核(1) 可撤回/通过/驳回，不可编辑删除。
- **驳回不丢弃草稿**：pending 保留，修改后可重新提审。
- 删除 pending 为物理删除，不可恢复。
- 变更重审（sourceType=1）：**仅主表 NOT_START 状态的活动可发起**；驳回/撤回/删除变更草稿会解锁主表 editing_locked。

### 券实例状态（CouponInstanceStatus，整数 code）

```
INITIAL(0) → ACTIVATED(1) ⇄ LOCKED(2) → USED(3)
                 │              │
                 ↓              │（下单取消解锁）
             EXPIRED(4)    CANCELLED(5, 运营停用/退券)   DELETED(6)
```

- 运营可执行：停用（ACTIVATED→CANCELLED）、退券（→CANCELLED）、延期（仅 ACTIVATED，按天顺延）、解锁（LOCKED→ACTIVATED，批量 1..50 张）。

### 兑换码批次状态（batchStatus，字符串）

```
CREATING（生成中）→ INACTIVE（待生效）→ ACTIVE（生效中）→ VOIDING（作废中）→ VOIDED（已作废）
        └→ FAILED_RELEASING / FAILED（生成失败）
```

- 生效：仅完整生成的 INACTIVE 批次可激活。
- 作废：批次作废（未领取码整体作废）与单码作废均**不可逆**。

### 赠品池组合状态（productStatus）

off_shelf（商品已下架）> out_of_stock（所有 SKU 库存为 0）> in_use（有关联活动）> available（可用）。

⚠️ 上表为设计口径——**当前实现仅返回 in_use / available 两态**（见 `promotion-concepts.md` 赠品池实体节），off_shelf/out_of_stock 现版本不可达。

---

## 枚举字典（大小写以本表为准）

| 枚举 | 值 |
|------|---|
| PromotionStatus | `1` 草稿 / `2` 未开始 / `3` 预热 / `4` 进行中 / `5` 已结束 / `6` 已暂停 / `7` 已删除 |
| PromotionSubCode | **layer=1 单品层**：`SECKILL` 秒杀、`PRESELL` 预售、`DIRECT_DOWN` 直降、`MEMBER_PRICE` 会员价（暂未开放创建）、`ENTERPRISE_PURCHASE` 口令购、`GROUPON` 拼团、`PERIOD_BUY` 周期购；**layer=2 店铺层**：`MYJ` 满元减、`MJJ` 满件减、`DNJ` 第N件优惠、`MYZ` 满元折、`MJZ` 满件折、`DNZ` 第N件打折、`NJY` N件Y元、`MYG` 满元赠、`MJG` 满件赠、`MG` 买赠；**layer=3 券层**：`MJ_COUPON` 满减券、`ZK_COUPON` 折扣券、`DH_COUPON` 兑换券；**layer=4 免运费层**：`MYF_COUPON` 运费券、`MYF` 满元包邮（暂未开放创建）、`MJF` 满件包邮（暂未开放创建）。⚠️ 本表 layer 为运营口径（落库字段 promotionLevel 同构）；计算引擎内部的 `PromotionSubCode.layer` 枚举口径不同（满减/满折/NJY 与商品券同为 3、赠品为 2），以 `stackable-rules` 返回与实例级配置为准，勿直接用枚举 layer 判定互斥 |
| CheckStatus | pending 行：`0` 草稿 / `1` 待审核 / `3` 已驳回；主表另有 `2` 已通过（搜索 MAIN 行与发券前置 checkStatus=2 判断会用到） |
| sourceType | `0` 新建 / `1` 变更重审 |
| CouponInstanceStatus | `0` 初始 / `1` 激活 / `2` 锁定 / `3` 已使用 / `4` 已过期 / `5` 已作废 / `6` 已删除 |
| DiscountType | `1` 减价 / `2` 折扣 / `3` 运费 / `4` 兑换 / `5` 赠品（⚠️ 券优惠类型口径；与规则结构 `actions[].discountType` 动作类型口径同名异义——后者 3=固定价） |
| ScopeType | `3` 人群 / `4` 商品 / `6` 类目 / `7` 品牌 / `9` 门店 |
| ScopeCategory | `1` 全选 / `2` 部分 |
| GoodsRole | `0` 默认（单品促销；落库默认值，非枚举成员——枚举仅有 1 主品/2 赠品）/ `1` 主品（买赠）/ `2` 赠品 |
| StockPolicy | `1` LIMITED 限量 / `2` UNLIMITED 不限量 |
| 业务领券渠道（券模板配置） | `1` 自然曝光 / `2` 分销（业务上互斥不应同选——服务端不强制拦截，双渠道数据按分销优先、自然曝光失效，Agent 构造参数时应主动避免同传；**空=仅 B 端运营发券等内部链路可发**，C 端领券入口均不可见——面向 C 端发放必须显式选渠道） |
| CouponClaimChannel（发券场景，发券时传） | `100` 领券中心 / `101` 商品详情页 / `102` 购物车 / `200` 自动领券（运营发券默认）/ `300` 装修页 / `400` 营销弹窗 |
| OperationType（操作日志） | CREATE / UPDATE / SUBMIT / PAUSE / RESUME / DELETE / START / END / PREHEAT / STOCK_INCREASE / STOP |
| ThemeSelectionMode | `EXPLICIT` 显式指定活动 / `ALL_ELIGIBLE` 按生命周期时间覆盖自动纳入（当前不按状态/类型过滤） |
| 列表 Tab（tab 入参） | `all` / `draft` / `pending` / `rejected` / `not_started` / `in_progress` / `paused` / `ended`；draft/pending/rejected查待审核表，四个生命周期Tab查正式资源，all可合并正式与新建pending，具体筛选例外见各查询契约 |

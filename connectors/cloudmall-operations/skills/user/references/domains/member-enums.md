# 会员子域 — 状态机与枚举字典

> 查值字典：状态机迁移与前置、枚举值精确拼写（大小写与取值以本表为准）。
> 查状态含义、确认操作前置、取枚举值时读本文件；实体模型/规则结构/业务约束见 `member-concepts.md`。
> 能力契约见 `references/apis/member/`，操作流程见 `references/flows/`。数据标签子域（标签/人群包）的状态机与枚举见 `references/domains/data-tag.md`。

---

## 会员状态（status，4 态，整数 code）

| code | 枚举名 | 说明 | 可迁移到 |
|------|--------|------|---------|
| 0 | NORMAL | 正常 | 2（黑名单） |
| 1 | FROZEN | 冻结 | 2（黑名单）、0（恢复正常——**运营端暂无解冻入口**） |
| 2 | BLACKLISTED | 黑名单 | 0（解除黑名单） |
| 3 | CANCELED | 已注销 | 2（黑名单，实现未拦截） |

- 加入黑名单仅要求当前非黑名单（重复加报错；冻结/已注销态也可直接拉黑——实现按此校验）。
- 解除黑名单回到 NORMAL（不经过 FROZEN）；解除后**无条件置 status=0**、不恢复拉黑前的原状态。

## 会员等级状态（整数常量）

| code | 说明 |
|------|------|
| 0 | 启用 |
| 1 | 停用 |

## 积分商品状态（整数常量）

| code | 说明 |
|------|------|
| 0 | 下架 |
| 1 | 上架 |

## 积分活动状态（整数常量）

```
新建（0 停用） ⇄ enable/disable ⇄ 1 启用；启用中不可删除（需先停用）
```

## 积分兑换订单状态（整数常量）

| code | 说明 |
|------|------|
| 1 | 待发货 |
| 2 | 已发货 |
| 3 | 已完成 |
| 4 | 已取消 |

- 发货（ship）仅对 status=1 生效；已发货后不可撤销。

## 反馈处理状态（整数常量）

| code | 说明 |
|------|------|
| 0 | 待处理 |
| 1 | 已处理（终态，不可再变更） |

---

## 枚举字典

| 枚举 | 值 | 说明 |
|------|---|------|
| 会员状态 | `0`-正常 / `1`-冻结 / `2`-黑名单 / `3`-已注销 | 数字 code |
| 会员等级状态 | `0`-启用 / `1`-停用 | 整数常量（status 切换请求体） |
| 权益类型 benefitType | `GROWTH_ACCEL` / `UPGRADE_GIFT`（`benefit.status` 路径参数仅此两类） | 大写字符串，其他值报错；`benefit.list` 还会返回固定类型 `POINTS_BOOST`（多倍积分），暂未开放对应能力 |
| 积分调整 category | `MARKETING`-营销活动 / `SHOPPING`-购物消费 | 大写字符串 |
| 积分调整 adjustType | `INCREASE`-增加 / `DECREASE`-扣减 | 大写字符串 |
| 积分商品 goodsType | `1`-实物 / `2`-优惠券 | 整数 |
| 积分商品 itemType | `1`-实物 SKU / `2`-优惠券 | 整数（items 子项） |
| 积分商品 redeemMode | `1`-纯积分 / `2`-积分+现金 | 整数；2 时 redeemAmount 必填 |
| 积分商品 validType | `1`-长期 / `2`-时间段 | 整数；2 时起止时间必填 |
| 积分商品/活动状态 | `0`-停用/下架 / `1`-启用/上架 | 整数 |
| 积分活动 itemConfigType | `0`-全部商品 / `1`-按类目 / `2`-按商品 SKU | 整数 |
| 积分活动 limitPeriod | `daily` / `weekly` / `monthly` | 小写字符串 |
| 积分活动 expiryMode | `0`-永久 / `1`-固定日期 / `2`-滚动过期 | 整数 |
| 降级策略 strategyType | `0`-不降级 / `1`-按发放日过期 / `2`-按自然年到期 | 整数 |
| 抵扣商品范围 productScope | `ALL` / `SPECIFIED` | 大写字符串；SPECIFIED 时商品清单必填 |
| 成长加速商品范围 productScopeType | `ALL_PRODUCT` / `SPECIFIED` | 大写；SPECIFIED 时范围至少一项 |
| 成长加速门店范围 storeScopeType | `ALL_STORE` / `SPECIFIED` | 大写；SPECIFIED 时 storeIds 必填 |
| 兑换订单状态 | `1`-待发货 / `2`-已发货 / `3`-已完成 / `4`-已取消 | 整数 |
| 兑换订单渠道 channel | `1`-小程序 / `2`-H5 / `3`-APP | 整数 |
| 礼包发放 giftType | `POINT` / `COUPON` | 大写字符串 |
| 礼包发放 issueStatus | `10`-待发放 / `20`-成功 / `30`-失败 | 整数 |
| 等级变更 changeType | `UP`-升级 / `DOWN`-降级 | 大写字符串 |
| 反馈类型 feedbackType | `PRODUCT_PERFORMANCE`/`FUNCTION_USAGE`/`UI_INTERACTION`/`CONTENT_RECOMMENDATION`/`TRANSACTION_PAYMENT`/`OTHER` | 枚举名字符串 |
| 反馈状态 | `0`-待处理 / `1`-已处理 | 整数 |
| 分享 envVersion | `release` / `trial` / `develop` | 小写，默认 release |

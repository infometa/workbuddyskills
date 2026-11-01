# 营销域 — 状态机与枚举字典

> 查值字典：状态机迁移与前置、枚举值精确拼写（大小写以本表为准）。
> 查状态含义、确认操作前置、取枚举值时读本文件；实体模型/规则结构/业务约束见 `cps-concepts.md` / `guide-concepts.md` / `marketing-concepts.md`。
> 能力契约见 `references/apis/marketing/`，操作流程见 `references/flows/`。

---

## 状态机
### CPS 活动奖励状态（字符串）

```
draft（未发布）── publish ──▶ init（未开始）── 到达预热时间自动 ──▶ warmup（预热中）
── 到达开始时间自动 ──▶ running（进行中）── 到达结束时间自动 / 手动 terminate ──▶ terminated（已结束）
draft 可 delete（不可恢复）；terminated 为终态
```

- 仅 `draft` 可更新/删除/发布；`init`/`warmup`/`running` 可终止；终止立即流转结算状态（事务保障，不可逆）。

---

### CPS 活动结算状态（活动维度，字符串枚举，两套体系之一）

`'0'`（默认，活动未结束时的初始值）→ 终止时：已产生订单 → `unsettled`（待结算）；无订单 → `settled`（已结算）。

---

### CPS 活动推广状态（整数字段 activityStatus）

```
0 未发布 ── publish（按时间窗口）──▶ 1 未开始 或 2 进行中
1 ── 到达开始时间自动 ──▶ 2 ── 到达结束时间自动 / 手动 terminate ──▶ 3 已结束
已发布状态（1/2/3）── unpublish ──▶ 0
```

- 删除**不做状态校验**（任意状态可删、物理删除不可恢复）；列表筛选 activityStatus 传**中文描述**（未发布/未开始/进行中/已结束）且为当前页内存过滤。

---

### CPS 分销员申请状态（auditStatus，整数）

`0` 待审核 → 审核通过(1)：自动创建分销员 / 审核驳回(2)：须填备注。已审核的申请再次审核报"已审核"。

---

### CPS 提现双状态机（一张单两个独立状态）

**审核状态**（运营动作驱动）：

```
PENDING_AUDIT(待审核) ──审核 PASS──▶ AUDIT_PASS(审核通过，触发异步打款)
                    └─审核 REJECT──▶ AUDIT_REJECTED(审核驳回，佣金余额回退)
```

**提现状态**（打款链路驱动，审核通过后自动流转）：

```
PENDING(待处理) → PROCESSING(处理中) → WAIT_USER_CONFIRM(待用户确认，微信渠道)
                                    → SUCCESS(提现成功，终态)
                                    → FAILED(提现失败，终态，余额回退)
                                    → CLOSED(提现关闭，终态)
```

- **审核 PASS ≠ 打款成功**——仅发起异步转账，最终以提现状态为准；FAILED 同样回退余额；终态单不可再变更。

---

### 导购状态（字符串）

```
create ──▶ pending（待激活）── 导购端小程序激活 ──▶ active（在职）
active ── disable ──▶ disabled（已停用）── enable ──▶ active
disabled ── archive ──▶ archived（终态，无恢复端点）
```

- 停用必须同时指定客户转移方式（admin_assign 指定导购转移 / public_pool 全部入公共池 / store_round_robin 同门店在职导购轮询）。

---

### 内容素材发布状态（字符串）

```
draft ── publish ──▶ published ── unpublish ──▶ unpublished ── publish ──▶ published（可循环）
```

- delete 前置：非 published（已发布须先取消发布）；定时发布（scheduled）到 publishStartTime 自动发布、到 publishEndTime 自动取消。

---

### 推广任务状态（字符串）

```
draft（草稿）── dispatch / create(isDraft=false) ──▶ active（进行中）── end ──▶ ended（终态）
```

- 执行记录：`pending`（待接收）→ `received`（已接收）→ `executed`（已执行）；任务结束时 pending/received → `expired`（已过期）。

---

### 弹窗状态（7 态，全大写字符串）

| 状态 | 含义 | 可执行动作 |
|------|------|-----------|
| DRAFT | 草稿 | 编辑、提审、删除 |
| PENDING_REVIEW | 待审核 | 审核（通过/驳回） |
| APPROVED | 待投放（审核通过且开始时间未到） | 下线（到点自动转投放中） |
| REJECTED | 已驳回 | 编辑、提审、删除 |
| ACTIVE | 投放中 | 暂停、下线（不可删除、不可编辑） |
| PAUSED | 已暂停 | 恢复、下线 |
| ENDED | 已结束（终态） | 删除 |

- 审核通过后：开始时间已过 → 直接 ACTIVE；未到 → APPROVED（到点自动上线）。
- 恢复仅限 PAUSED 且投放结束时间未过期；下线后为 ENDED 终态不可再投放。

---

### 互动活动状态（全大写字符串，draft/formal 双版本）

- 展示态按"formal 存在则用 formal 状态，否则 UNPUBLISHED"呈现：`UNPUBLISHED`（未发布，draft 侧）/ `NOT_STARTED`（未开始，formal 侧）/ `RUNNING`（进行中）/ `PAUSED`（已暂停）/ `TERMINATED`（已结束-手动，终态）/ `EXPIRED`（已结束-自动过期，终态）。
- `PUBLISHED` 为 draft 内部标记态：**搜索筛选传入 PUBLISHED 视为非法（返回空列表）**，"已结束"筛选用 `statusList: ["TERMINATED","EXPIRED"]`。
- 发布按开始时间判定 formal 初始状态（未到 → NOT_STARTED；已到 → RUNNING）；暂停限 RUNNING/NOT_STARTED；恢复限 PAUSED；结束限 RUNNING/NOT_STARTED/PAUSED → TERMINATED；删除限"未发布（无 formal）"或"formal 已结束/已过期"。

---

### 中奖记录发放状态（全大写字符串，惰性态）

```
SENDING（发放中）→ 虚拟资产到账 SENDED / 实物 WAITING_CLAIM（待领取）
WAITING_CLAIM → 用户填资料 CLAIMED（已领取）→ 运营发货 SENDED
SEND_FAILED（发放失败，终态）/ EXPIRED（实物超期未填资料，终态）
```

- **EXPIRED 是查询时按 expireTime 惰性判定的展示态**（存储状态仍是 WAITING_CLAIM）：按 `status=EXPIRED` 筛选返回空；找超期记录请筛 WAITING_CLAIM 再看 expireTime。

---

### 协议状态（Integer code）

`0` 未发布（可编辑/发布/删除）→ 发布 → `1` 已发布（可结束；不可编辑/删除）→ 结束 → `2` 已结束（终态；可删除）。发布时同类型旧"已发布"协议自动转 2。

---

## 枚举字典（大小写以本表为准）
### CPS 链

| 枚举 | 值 |
|------|---|
| CPS 活动类型 type | `OD` 订单激励 / `GMV` GMV 激励 |
| CPS 活动状态 status | `draft` 未发布 / `init` 未开始 / `warmup` 预热中 / `running` 进行中 / `terminated` 已结束 |
| CPS 活动结算状态 settlementStatus | `'0'` 默认（未结束初始值）/ `unsettled` 待结算 / `settled` 已结算（**字符串**） |
| 奖励规则 prizeInfo.type | `1` 按订单奖励 / `2` 订单阶梯奖励 / `3` GMV 阶梯奖励 |
| 适用范围 product.type | `0` 不限 / `1` 指定分类 / `2` 指定品牌 / `3` 指定商品 |
| 适用范围 store.type | `0` 不限 / `1` 指定门店 / `2` 指定门店分组 |
| 适用范围 user.type | `0` 不限 / `1` 新用户 / `2` 指定用户（人群标签值 ID） |
| 适用范围 distributor.type | `0` 不限 / `1` 指定分销员 / `2` 指定分销员分组 / `3` 指定分销员等级 |
| 分销规则 distributionRelationType | `1` 动态 / `2` 专属 / `3` 永久 |
| 分销规则 selfPurchaseCommission | `1` 自购得佣金 / `2` 自购仅跟单 |
| 分销规则 employeeOrderCommission | `1` 员工互下单得佣金 / `2` 仅跟单 |
| 活动推广 activityStatus（出参整数） | `0` 未发布 / `1` 未开始 / `2` 进行中 / `3` 已结束 |
| 活动推广 activityStatus（列表筛选） | 中文描述：`未发布` / `未开始` / `进行中` / `已结束`（当前页内存过滤） |
| 活动推广 activityType | `1` 爆品推广 / `2` 平台活动 |
| 活动推广样式枚举 | activityBannerType `1` 系统图 / `2` 自定义；goodsTemplate `1` 一行一个 / `2` 一行两个；cornerStyle `1` 圆角 / `2` 直角；selectGoods.classify `0` 不分组 / `1` 分组 |
| 结算明细 settleStatus / awardStatus | `0` 待结算 / `1` 已结算；`0` 未发奖 / `1` 已发奖（**整数**） |
| 结算明细 cpsType | `'1'` 员工 / `'2'` 普通用户（数字字符串） |
| 商品推广 commissionType | `0` 全局佣金 / `1` 定向佣金 |
| 商品推广 promotionStatus | `0` 推广中 / `1` 已停止 |
| 商品状态 status | `ENABLED` / `DISABLED` / `HIDDEN`（商品域回源） |
| 分销员 type / status | `1` 员工 / `2` 普通用户；`0` 启用 / `1` 禁用 |
| 分销员 openChannel | `1` 运营端导入 / `2` 邀请开通 / `3` 自主申请 |
| 分销员 employeeStatus | `0` 使用中 / `1` 已禁用 |
| 账户流水 dealType | `1` 服务收入 / `2` 资产收入 / `3` 活动奖励 / `4` 提现 |
| 账户流水 dealStatus | `1` 收入 / `2` 冻结 / `3` 回滚 / `4` 扣减 |
| CPS 绑定 bindType / relationType | `1` 链接 / `2` 扫码 / `3` 手动；`1` 动态 / `2` 专属 / `3` 永久 |
| 申请 auditStatus | `0` 待审核 / `1` 通过 / `2` 驳回 |
| 申请 applyChannel | `self` 自主申请 / `invite` 邀请申请 / `MINI_PROGRAM` 小程序 |
| 申请设置 auditMode / autoAuditAction | `0` 需审核 / `1` 免审核；`1` 自动通过 / `2` 自动驳回 |
| CPS 等级 enabled | `0` 停用 / `1` 启用 |
| 提现 auditStatus | `PENDING_AUDIT` / `AUDIT_PASS` / `AUDIT_REJECTED` |
| 提现 withdrawStatus | `PENDING` / `PROCESSING` / `WAIT_USER_CONFIRM` / `SUCCESS` / `FAILED` / `CLOSED` |
| 提现渠道 channelCode | `WECHAT_MCH_TRANSFER` 微信商家转账到零钱 / `POINTS_CREDIT` 积分到账 |
| 提现审核动作 action | `PASS` / `REJECT`（大写） |
| 提现设置 monthlyLimit | `-1` 不限次数 / `0` 禁用提现 / `>0` 每月最多 N 次 |

---

### 导购链

| 枚举 | 值 |
|------|---|
| 导购状态 status | `pending` 待激活 / `active` 在职 / `disabled` 已停用 / `archived` 已归档 |
| 导购 gender | `0` 未知 / `1` 男 / `2` 女 |
| 客户转移方式 transferMethod | `admin_assign` 指定导购转移 / `public_pool` 入公共池 / `store_round_robin` 门店轮询 |
| 调店策略 customerTransferStrategy | `follow` 客户跟随 / `stay` 客户留在原店 / `individual` 逐一选择 |
| 导购操作日志 operationType | `create` / `update` / `transfer_store` / `enable` / `disable` / `archive` / `level_change` / `auto_promote` |
| 导购关系 relationType | `share_guide` 共享导购 / `exclusive_guide` 专属导购 |
| 绑定方式 bindMethod | `share_bind` / `upgrade_exclusive` / `customer_switch` / `nearest_store` / `store_round_robin` / `admin_assign` |
| 失效原因 deactivateReason | `expired` / `manual_unbind` / `transferred` / `guide_disabled` / `customer_switch` / `manual_release` / `new_binding_replaced` |
| 公共池入池原因 enterReason | `customer_switch` / `customer_unbind` / `expired` / `guide_disabled` / `admin_release` / `store_transfer` |
| 客户行为 eventType | `browse` 浏览 / `cart` 加购 / `order` 下单 / `share` 分享 / `collect` 收藏 |
| 导购等级 status | `0` 禁用 / `1` 启用 |
| 绑定设置 customerLimitType | `unlimited` 不限 / `specified` 指定客户标签 |
| 绑定设置 autoAssignMethod / Strategy | `auto` 自动分配 / `none` 不分配；`nearest` 就近 / `round_robin` 轮流 |
| 绑定设置 exclusiveExpireType | `permanent` 永久 / `specified` 指定天数 |
| 升级专属触发场景 autoBindScenes | `collect_coupon` 领券 / `collect_card` 领卡 / `place_order` 下单 / `wework_friend` 企微加好友 |
| 目标计划 periodType / status | `monthly` 月度 / `quarterly` 季度；`not_started` 未开始 / `in_progress` 进行中 / `ended` 已结束 |
| 提成规则 status | `draft` 草稿 / `active` 生效中 / `expired` 已过期（时间推导）/ `disabled` 已停用（存储态） |
| 提成 calculationType | `percentage` / `category` / `ladder` / `combined` / `fixed` |
| 提成 scopeType / rangeType | `guide` 导购 / `level` 等级 / `store` 门店；`all` 全部 / `specified` 指定 / `excluded` 排除 |
| 提成 itemType | `order_rate` 订单金额比例 / `category` 品类 / `cumulative_ladder` 累计阶梯 / `fixed_per_order` 每笔固定金额 |
| 提成明细 settlementStatus / guideRole | `pending` 待结算 / `settled` 已结算；`exclusive_guide` / `share_guide` |
| 业绩方案 status | `active` 生效中 / `inactive` 未生效 |
| 业绩分成场景 splitScene | `cross_guide_cooperation` 跨导购协作 / `same_guide` 同一导购 / `exclusive_only` 仅专属导购 / `share_only` 仅分享导购 / `no_guide` 无导购 |
| 任务 status / taskType | `draft` / `active` / `ended`；`new_product` / `activity` / `daily` |
| 执行记录 executionStatus | `pending` 待接收 / `received` 已接收 / `executed` 已执行 / `expired` 已过期 |
| 任务关联内容 contentType | `product` / `promotion` / `coupon` / `content` / `page` |
| 任务 goalBehavior / frequencyType / dispatchTimeType | `share` / `share_after` / `share_order`；`once` / `periodic`；`unlimited` / `specified` |
| 业务素材 materialType | `coupon` 优惠券 / `promotion` 促销活动 / `page` 活动页面 / `game` 游戏 / `live` 直播 / `grass` 种草 |
| 内容素材 contentType | `image` / `poster` / `video` / `image_poster` / `custom` |
| 内容素材 publishStatus | `draft` / `published` / `unpublished` |
| 内容素材 publishTimeType | `permanent` 永久 / `scheduled` 定时 |
| 素材分组 bizType | `content_material` 内容素材 / `speech` 话术（两套独立分组树） |
| 看板 timeRange | `today` / `week` / `month` / `quarter`（**小写**，必填） |
| 看板 rankBy / granularity | `performance` 业绩（默认）/ `customers` 客户；`day`（默认）/ `week` / `month` |
| 导出任务 status | `PENDING` / `PROCESSING` / `COMPLETED` / `FAILED`（大写） |

---

### 弹窗 / 互动 / 协议

| 枚举 | 值 |
|------|---|
| 弹窗状态 status | `DRAFT` / `PENDING_REVIEW` / `APPROVED` / `REJECTED` / `ACTIVE` / `PAUSED` / `ENDED`（全大写） |
| 弹窗模板 templateType | `CENTER_IMAGE` / `FULLSCREEN` / `CAROUSEL` / `CAROUSEL_FULLSCREEN` / `VIDEO` / `COUPON` |
| 弹窗下线方式 endOfOperation | `MANUAL` 手动下线 / `AUTO_EXPIRED` 自动过期 |
| 弹窗操作日志 operationType | `CREATE` / `EDIT` / `SUBMIT` / `APPROVE` / `EDIT_APPROVE` / `REJECT` / `ONLINE` / `PAUSE` / `RESUME` / `OFFLINE` / `DELETE` |
| 弹窗审核动作 action | `APPROVE` / `EDIT_APPROVE` / `REJECT` |
| 弹窗跳转 linkType | `SYSTEM_PAGE` / `PROMOTION_PAGE` / `DECORATION_PAGE` / `EXTERNAL_MINIPROGRAM` / `H5_LINK` / `NONE` |
| 系统页 systemPageType | `HOME` / `CATEGORY` / `PRODUCT_DETAIL` / `PROFILE` / `POINTS_MALL` / `MY_ORDERS` / `MY_COUPONS` |
| 弹窗频次 frequency.type | `EVERY_VISIT` / `ONCE` / `DAILY` / `CUSTOM` |
| 弹窗页面 page type | `HOME` / `PRODUCT_DETAIL` / `CATEGORY` / `CART` / `PROFILE` / `CUSTOM`（CUSTOM 须 /pages/ 开头） |
| 弹窗人群 / 门店 scope | `ALL` / `TAG`；`ALL` / `SPECIFIED` |
| 全局策略 sameWeightSort | `CREATED_DESC` / `CREATED_ASC` / `RANDOM` |
| 互动活动状态 | `UNPUBLISHED` / `NOT_STARTED` / `RUNNING` / `PAUSED` / `TERMINATED` / `EXPIRED`（全大写；`PUBLISHED` 为 draft 内部标记，筛选非法） |
| 互动活动类型 activityType | `sudoku-lottery` 九宫格 / `dzp` 大转盘 / `newcomer-gift` 新人礼包 / `open-screen-gift` 开屏礼包 / `daily-checkin` 每日签到 / `exchange-code` 第三方兑换码 / `share-gift` 分享有礼 / `yqzl` 邀请助力（小写中划线） |
| 互动玩法桶（configInfo 外层 key） | `COMMON` 通用 / `PROBABILITY` 概率抽奖 / `SIGN` 签到 / `SHARE` 分享 / `INVITE` 邀请 / `ASSIST` 助力；内层 key 协议与各强类型规则结构见 `interactive-activity-action.md` 创建入参（**中奖概率在 configInfo 的 prizeStrategy.prizePlans[].prizeList[].probality，百万分制，不在 prizeInfo**） |
| CPS 等级考核指标 typeValue | `PROMOTE_UV` 引流人数（type=1）/ `DEAL_COUNT` 成交人数（type=2）/ `VALID_GMV` 有效 GMV（type=3，value 为元）；value 0 或缺省=不考核 |
| 奖品类型 prizeType | `points` 积分 / `coupon` 优惠券 / `physical` 实物 |
| 中奖记录发放状态 | `SENDING` / `WAITING_CLAIM` / `CLAIMED` / `SENDED` / `SEND_FAILED` / `EXPIRED` |
| 关联场景 sceneType | `mini_program_page` / `push` / `banner` |
| 奖品模板 type / status | `points` / `coupon` / `physical`；`1` 有效 / `0` 停用；sendDescType/useDescType：`text` / `image`；autoSend：`1` 自动 / `0` 手动 |
| 协议 status | `0` 未发布 / `1` 已发布 / `2` 已结束 |
| 协议 type | `1` 系统弹窗 / `2` 隐私政策 / `3` 用户服务协议 / `4` 第三方共享个人信息清单 / `5` 个人信息收集清单 / `6` 未成年人信息保护规则 / `7` 预售定金协议 / `8` 分销协议 / `9` 分销佣金规则 |

---

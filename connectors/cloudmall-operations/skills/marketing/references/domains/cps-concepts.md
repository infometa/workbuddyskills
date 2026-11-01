# 营销域 — CPS 分销实体模型与业务概念

> 实体模型、规则结构语义、业务规则要点。
> 状态机迁移与枚举值查 `marketing-enums.md`；能力契约见 `references/apis/marketing/`，操作流程见 `references/flows/`。

---

## 核心实体
### CPS 活动奖励
- 分销激励的主体：`activityId`（**16 位业务 ID 字符串**，区别于内部数字主键 `id`）。
- 关键字段：`name`（2-30 字）、`type`（OD 订单激励 / GMV GMV 激励）、`description`（2-500 字）、`warmUpTime`/`startTime`/`endTime`、`prizeInfo`（奖励规则）、`configInfo`（四维度适用范围：商品/门店/用户/分销员）、`priority`、`settlementStatus`（活动维度结算状态，字符串枚举）。
- `prizeInfo`：`type` 1 按订单奖励（`rewardPerOrder` 每单奖励元 + `maxAmount` 封顶有效订单量件数，0=不限）/ 2 订单阶梯奖励 / 3 GMV 阶梯奖励（`target[]`：订单量整数或 GMV 金额元 + `rewardAmount` 元）。
- `configInfo` 四维度各有 type 0-3（见枚举字典）；商品维度 type=3 用 `goodsList`（`{spuId, skuList?}`）。

---

### 分销规则
- 租户级全局跟单规则，每租户一条：绑定模式（动态/专属/永久）、跟单有效期（**秒数**，0=永不过期）、自购佣金策略、员工下单佣金策略。保存为整表覆盖。

---

### CPS 活动推广
- C 端推广落地页活动（爆品推广/平台活动）：`id`（十进制字符串）、`activityType`（1 爆品推广 / 2 平台活动）、`activityStatus`（**整数字段** 0-3）、`selectGoods`（商品编排：`classify` 0/1 + `goodsList` 或 `goodsClassifyMap` 按分类名分组）、Banner/分享/装修样式字段、`pageId`（关联装修页）。
- 列表出参 `operations` 为按状态派生的可执行操作组合。

---

### CPS 商品推广
- 所有商品默认可推广，仅通过禁用改变状态：`commissionType`（0 全局佣金 / 1 定向佣金）、`promotionStatus`（0 推广中 / 1 已停止）、`commissionRateRange`（佣金率范围，四位小数比率）。
- 商品基础信息（price/status/categoryPath）来自商品域回源。

---

### CPS 结算明细
- 每行 = 一个分销员在某活动下的**预估**结算汇总：`cpsUid`、`cpsType`（'1' 员工 / '2' 普通用户）、`commissionAmount`（预估佣金，元）、`settledAmount`（已结算金额，元）、`settleStatus`（**整数** 0 待结算 / 1 已结算）、`awardStatus`（0 未发奖 / 1 已发奖）、`cpsGroupInfo`（分组信息 JSON 字符串）、`phone`（**未脱敏明文**，展示需自行打码）。

---

### 分销员
- 分佣主体（员工或普通用户）：`uid`（用户 UID 字符串）、`type`（1 员工 / 2 普通用户）、`status`（0 启用 / 1 禁用）、`openChannel`（1 运营端导入 / 2 邀请开通 / 3 自主申请）、`groupId`/`level`（业务等级号）。
- **佣金账户**三余额：`withdrawalAmount` 可提现 / `withdrawingAmount` 提现中 / `withdrawnAmount` 已提现（均元）。
- **账户流水**：`dealType`（1 服务收入 / 2 资产收入 / 3 活动奖励 / 4 提现）、`dealStatus`（1 收入 / 2 冻结 / 3 回滚 / 4 扣减——冻结/回滚/扣减均对应提现链路阶段）、`voucherNum`（凭证号=订单号/提现单号/活动编号）。
- **绑定关系**（消费者↔分销员）：`bindType`（1 链接 / 2 扫码 / 3 手动）、`relationType`（1 动态 / 2 专属 / 3 永久，与分销规则绑定模式对应）、`expireTime`（null=永不过期）。

---

### 分销员申请
- 自主申请/邀请申请的审核单：`auditStatus`（0 待审核 / 1 通过 / 2 驳回）、`applyChannel`（self / invite / MINI_PROGRAM）、`auditRemark`（驳回必填）。
- **审核通过即自动创建分销员账号**（初始等级 0、未分组、启用）。
- 申请设置：邀请/自主申请开关、审核模式（0 需审核 / 1 免审核）、自动审核（天数 1..30 + 动作 自动通过/自动驳回）。

---

### 分销员分组与等级
- **分组**：名称租户内唯一，参与分组佣金率命中。删除前置：组内无分销员且无分组佣金率引用。
- **等级**：业务等级号 0 起自动递增；核心参数 `commissionRatio`（**返佣系数**——对按佣金率算出的佣金再乘以该系数，1.0000=100% 基准，范围 0..10.00，**不是百分比**）；`levelValue` 考核指标 JSON；`version` 乐观锁。
- 启停顺序强校验：**启用从低到高、停用从高到低**；已启用等级考核指标须严格递增。

---

### 佣金率
- **小数比例**（`0.1213` = 12.13%，范围 `[0.0000, 1.0000]`），不是百分比数字。
- **四级优先级**：**商品×分组 > 商品定向（全局组）> 分组默认 > 全局默认**。定向佣金一旦设置，该商品即按定向率结算。
- 查询返回的 `rate` 是**生效值**（未配置的分组回填：商品定向率→分组默认→全局默认），非"已配置标记"。
- 商品×分组佣金的前提：必须先设置全局佣金率，否则业务错误。
- 批量取消定向 = 删除该商品定向率 + 全部分组率，回退全局默认（幂等）。

---

### 提现
- 一张提现单携带**双状态**：审核状态（运营驱动）+ 提现状态（打款链路驱动），见状态机。
- 关键字段：`withdrawNo` 提现单号、`amount`（元）、`channelCode`（WECHAT_MCH_TRANSFER 微信商家转账 / POINTS_CREDIT 积分到账）、`creditPoints`/`creditRatio`（仅积分渠道）。
- 提现设置：最低金额/单次上限（≤50000 元）/月度次数（-1 不限 / 0 禁用 / >0 每月 N 次）/时间窗口/审核配置（自动通过阈值≤该值免审）/渠道配置（微信密钥**留空=保留已存值**；积分到账比例 1 元=N 积分）。

---

## 业务规则要点

- **佣金率四级优先级**：商品×分组 > 商品定向（全局组）> 分组默认 > 全局默认；定向佣金一旦设置，该商品即按定向率结算；商品×分组的前提是先设置全局佣金率；批量取消定向会一并删除该商品的定向率与全部分组率并回退全局默认（幂等）。查询返回的 rate 是**生效值**（含回填），不是"已配置标记"。
- **两套结算状态易混**：CPS 活动侧 `settlementStatus` 为字符串（'0'/unsettled/settled）；结算明细侧 `settleStatus` 为整数（0/1）。同域还有导购提成明细 settlementStatus（pending/settled 字符串）——三处不可混用。
- **提现 audit 成功 ≠ 打款成功**：PASS 仅发起异步转账，结果以提现状态为准（PROCESSING/WAIT_USER_CONFIRM 仍可能 FAILED）；REJECT 立即回退余额且不计入月度次数。
- **CPS 分销规则与申请设置为整表覆盖**：保存前必须先查询现值，只改需要改的字段、其余原值回传。
- **CPS 等级启停顺序强校验**：启用从低到高（更低等级须已启用、考核指标严格递增）；停用从高到低；批量修改带乐观锁 version，且批量项中返佣系数字段名是 `commissionRate`（新增时是 `commissionRatio`）。

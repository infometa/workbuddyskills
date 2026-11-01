# 促销域 — 运营流程：券体系（模板 / 实例 / 兑换码）

> 券模板创建与生命周期、券实例运行时（发券/停用/退券/延期/解锁）、兑换码批次发行与作废。
> 概念知识见 `references/domains/promotion-concepts.md`，状态与枚举见 `references/domains/promotion-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律；券模板创建/审核走 `promotion-review.md` 审核链。
> 对应契约：`coupon-template-query.md` / `coupon-template-action.md`、`coupon-runtime-query.md` / `coupon-runtime-action.md`、`coupon-code-query.md` / `coupon-code-action.md`。
>
> **能力标识约定**：本文为行文简洁使用模块短名（如 `coupon.send`），
> 实际调用 capability 必须使用全限定 id = `ops.promotion.` + 短名（即 `ops.promotion.coupon.send`），
> 禁止把短名直接作为 capability 传入。

---

## 券模板管理

**场景**：创建/管理优惠券模板（满减/折扣/兑换/运费券）。

1. 查询：`coupon-template.search`（title 搜名称、promotionSubCode 筛券种、tab 筛状态、channelCodes 筛渠道）；统计 `coupon-template.stats`（promotionSubCode 可选，缺省聚合全部券种）。
2. 创建/编辑/提审/审核：使用券专用create/update/submit与审核链（create 返回 pendingId；编辑/提审/审核用 pendingId；**审核是合一接口** coupon-template.check，approved 必填）。创建/改期/提审前读 `references/apis/promotion/form-validation.md` 的券模板节，检查领取/使用窗口、有效期模式与规则联动。
3. 审核通过后查询正式模板取得 templateId，再执行 stop 停用 / pause 暂停 / resume 恢复 / delete 删除；不把 pendingId 或 promotionId 当 templateId。通过后pending删除；驳回后pending保留，查pending.detail核对checkStatus=3，不查不存在的新建正式模板。
4. 分享物料：先 `share-capability` 查能力（shareAllowed/disabledReason），允许后再 `share-qrcode`（太阳码）/ `share-short-link`（短链）。
5. 报表：`ops.promotion.coupon.report`（按 templateId 查发放/使用/过期/作废量与使用率）。

解释数量前读取coupon-template-query的“券量、库存与当前可用性”：发行量、累计领取、水位、批次可预占余量与当前有效券不同。暂停/恢复后的累计领取数不能解释成仍可使用的券数；查指定券实例运行态再说明影响。

### 参数来源

| 参数 | 来源 |
|------|------|
| templateId | 正式券模板搜索records[].templateId；新建/审核回执不返回此ID。审核通过后以已知名称搜索并只取dataSource=main的正式记录，按返回promotionId核对身份（同名须继续核对，不取首条猜测）。驳回不进入正式ID查询链；已知templateId时可查详情 |
| pendingId | 券模板创建响应（草稿阶段编辑/提审/审核用） |
| 券专属字段 | `promotion-concepts.md`「券模板」实体说明 |

### 异常处置
- 草稿→提审：`acquireExpireStart/End` 提交态必填；useExpireType=1 需 useExpireStart/End，=2 需 useExpireDuration（秒）。
- channelCodes 自然曝光(1)与分销(2)业务上不应同选——**服务端不强制拦截**（双渠道数据按分销优先、自然曝光失效，且审核通过后渠道不可再改）。构造参数时主动避免同传。

---

## 券实例运行时

**场景**：运营管理用户已领取的券（发券/查券/停用/退券/延期/解锁/核销预检）。

### 发券（资金面高危，单独定级）

1. 前置核对：模板详情（进行中、可领取窗口、库存、限领）。
2. 发券 `ops.promotion.coupon.send`：**单会员**（memberId 字符串）+ templateId + channelType（建议 200 自动领券）+ **requestId 幂等**（每次操作生成唯一值；超时结果不确定时用同一 requestId 重试安全）。
3. 执行后回读：`coupon.detail` 或 `coupon.library` 核对券实例状态。

### 查券

- 用户券库 `coupon.library`（memberId 必填字符串，status 筛选）。
- 券实例详情 `coupon.detail`（couponId）。
- 核销预检 `coupon.check`（couponId + orderId + orderAmount 均必填，orderAmount 单位分；返回 available + 原样模板摘要 discountAmount + 不可用原因）。摘要按券类型区分金额分/折扣千分比，不当实际结算优惠额；available只覆盖局部预检，当前运行态另查详情/券库。

### 券实例操作（均需先查现态）

- 停用 `coupon.stop`：仅激活态 → 已作废。
- 退券 `coupon.cancel`：作废券实例（reason ≤200 字）。
- 延期 `coupon.delay`：**按天数顺延**（delayDays 1..365），不是设置绝对时间。
- 解锁 `coupon.unlock`：批量 1..50 张，仅锁定态 → 激活；B 端管理解锁不校验订单号。

### 参数来源

| 参数 | 来源 |
|------|------|
| couponId | 券库/详情/发券响应 |
| templateId | 券模板查询 |
| memberId | 用户域会员 ID（用户提供） |
| orderId / orderAmount | 交易域订单（用户给出，金额单位分） |

### 异常处置
- 状态前置不符（如解锁非锁定券）→ 先查券详情确认状态。
- 发券模板校验失败（不在进行中/超领取时间/库存不足/超限领）→ 读错误信息向用户说明，不重试。

---

## 兑换码管理

**场景**：按批次发行兑换码（客户凭码兑换券）。

```
创建批次（coupon-code.batch-create：createRequestId 幂等 + 模板 + totalCount 1..100000；模板须已配置库存且活动未开始/进行中）
  → 等待生成（batchStatus: CREATING → INACTIVE）
  → 生效（coupon-code.batch-activate，仅完整生成的 INACTIVE 批次）
  → 发码给客户（明文码仅导出链路可见；当前开放能力可按码/按批查脱敏状态）
  → [可选] 作废批次（batch-void，不可逆）/ 作废单码（code-void，不可逆）
```

1. 查询：批次分页 `coupon-code.batches`（batchName 模糊 / status 筛选）/ 批次详情 / 可用模板选项 `coupon-code.templates`（含 reservableStock 可建批次余量）。
2. 码状态：按明文码查 `coupon-code.codes-search` / 批次内查 `batch-codes-search`（≤100 个码，脱敏回显 codeMasked + 领取状态）；批次码游标列表 `coupon-code.batch-codes`（afterId 翻页）。

### 参数来源

| 参数 | 来源 |
|------|------|
| batchId | 批次查询/创建响应 |
| templateId | 券模板查询 / 兑换码模板选项 |
| createRequestId | 每次创建操作生成唯一值（幂等） |

券编辑先读完整couponDetail请求快照合并，保持channelCodes等未改字段；通用pending内容更新不适用于券。发券幂等长度、stop与cancel状态5的区别、PROCESSING/VOIDING终态核验，分别按coupon-runtime-action与coupon-code-action处理。

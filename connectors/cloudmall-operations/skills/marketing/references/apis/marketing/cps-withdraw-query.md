# 营销域 — CPS 提现（资金面最高危）查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-withdraw-flow.md`
> 分销员佣金账户余额可申请提现；运营在此审核。**审核通过即触发异步打款链路（真实资金出账）**——本模块写操作均属资金面最高危档。
> 通用约定：列表入参支持 `pageNum`（≥1，默认 1）/`pageSize`（**1..100**，超限报错）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-withdraw.search 提现列表（双状态筛选） · cps-withdraw.detail 提现详情（含微信待确认参数/失败原因） · cps-withdraw.audit-logs 提现审核日志 · cps-withdraw.get-settings 提现设置查询（密钥脱敏返回）
> 写操作见 `cps-withdraw-action.md`。

---

## 双状态机（一张提现单同时携带两个独立状态）

**审核状态**（运营动作驱动）：

```
PENDING_AUDIT(待审核) ──审核 PASS──> AUDIT_PASS(审核通过，触发异步打款)
                    └─审核 REJECT─> AUDIT_REJECTED(审核驳回，佣金余额回退)
```

**提现状态**（打款链路驱动，审核通过后自动流转）：

```
PENDING(待处理) → PROCESSING(处理中) → WAIT_USER_CONFIRM(待用户确认，微信渠道)
                                    → SUCCESS(提现成功，终态)
                                    → FAILED(提现失败，终态，余额回退)
                                    → CLOSED(提现关闭，终态)
```

要点：
- 审核 PASS **不等于**打款成功——仅将审核状态置为通过并发起异步转账；最终以提现状态为准（PROCESSING/WAIT_USER_CONFIRM 仍可能 FAILED）。
- 审核 REJECT 立即回退佣金余额（流水状态=回滚），且该单不计入月度提现次数。
- 提现失败（FAILED）同样回退余额；终态单不可再变更。
- 微信渠道存在「待用户确认」中间态：需要用户在小程序侧确认收款后才能成功。

---

## ⛔ 未开放端点（提现域）

| 端点 | 不开放理由 |
|------|-----------|
| 提现列表导出 | 前端存在导出入口但后端**尚无对应端点实现**（前端调用会 404，属前后端契约缺口）；如需导出请联系后端补齐 |

---

## ✅ 提现列表 — `ops.marketing.cps-withdraw.search`

- **说明**：分页查询提现单（双状态筛选）；`withdrawNo`/`uid` 精确匹配（`uid` 为数字 UID，非数字入参返回空结果）；时间按申请时间过滤。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 10 |
| auditStatus | String | 否 | 审核状态（枚举名）：`PENDING_AUDIT` / `AUDIT_PASS` / `AUDIT_REJECTED` |
| withdrawStatus | String | 否 | 提现状态（枚举名）：`PENDING` / `PROCESSING` / `WAIT_USER_CONFIRM` / `SUCCESS` / `FAILED` / `CLOSED` |
| withdrawNo | String | 否 | 提现单号 |
| uid | String | 否 | 分销商 UID |
| startTime | String | 否 | 申请开始时间，格式 yyyy-MM-dd HH:mm:ss |
| endTime | String | 否 | 申请结束时间，格式 yyyy-MM-dd HH:mm:ss |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].withdrawNo`（→ 详情/审核日志路径参数、审核操作入参）
- **枚举字段**：`records[].auditStatus`（三值）、`records[].withdrawStatus`（六值），均有中文描述字段可透传；`records[].channelCode`（`WECHAT_MCH_TRANSFER`=微信商家转账到零钱，`POINTS_CREDIT`=积分到账）
- **格式敏感字段**：`records[].amount`（提现金额，**元**）、`records[].createdTime`/`settleTime`（yyyy-MM-dd HH:mm:ss，均有格式化注解）、`records[].creditPoints`（仅积分渠道有值，到账积分数）
- 展示型字段：`distributorName`/`channelDesc`/`auditRemark`/`failReason` 可透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-withdraw.search","input":{"pageNum":1,"pageSize":20,"auditStatus":"PENDING_AUDIT"},"summary":"查看待审核的提现申请"}
```

---

## ✅ 提现详情 — `ops.marketing.cps-withdraw.detail`

- **说明**：按提现单号查详情（含分销员姓名）；微信渠道「待用户确认」状态下会附带微信侧状态与拉起确认页参数。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| withdrawNo | String | ✅ | 提现单号 |

### 出参（原始数据）

- **枚举字段**：`auditStatus`（三值）、`withdrawStatus`（六值）、`channelCode`（两渠道）
- **格式敏感字段**：`amount`（提现金额，元）、`createdTime`/`settleTime`（yyyy-MM-dd HH:mm:ss）、`creditPoints`/`creditRatio`（仅积分渠道：到账积分数与到账比例快照）
- 条件返回字段：`wxState`/`wxPackageInfo`（仅待用户确认时）、`failReason`（仅 FAILED/CLOSED 时）、`settleTime`（仅 SUCCESS 时）、`mchId`（仅待用户确认时）。
- 展示型字段：`distributorName`/`auditRemark`/`auditStatusDesc`/`withdrawStatusDesc` 可透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-withdraw.detail","input":{"withdrawNo":"WD20260910000187654321"},"summary":"查看该提现单详情"}
```

---

## ✅ 提现审核日志 — `ops.marketing.cps-withdraw.audit-logs`

- **说明**：按提现单号查询审核日志（按时间倒序）；每次审核动作（含自动免审）产生一条。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| withdrawNo | String | ✅ | 提现单号 |

### 出参（原始数据）

- **枚举字段**：`[].action`（`PASS` / `REJECT`）
- **格式敏感字段**：`[].auditTime`（yyyy-MM-dd HH:mm:ss）
- 展示型字段：`[].auditorName`（审核人）/`[].remark`（备注）可透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-withdraw.audit-logs","input":{"withdrawNo":"WD20260910000187654321"},"summary":"查看该提现单的审核日志"}
```

---

## ✅ 获取提现设置 — `ops.marketing.cps-withdraw.get-settings`

- **说明**：查询提现功能配置；微信渠道密钥类字段**脱敏**返回（商户号仅显示后 4 位、密钥只返回是否已配置布尔值）。

### 入参

无（空对象）。

### 出参（原始数据）

- **格式敏感字段**：`minAmount`（最低提现金额，元）、`maxPerOrder`（单次提现上限，元，≤50000）、`audit.autoPassThreshold`（自动通过阈值，元——金额 ≤ 该值免审核）、`channel.pointsCredit.creditRatio`（积分到账比例：1 元 = creditRatio 个积分，向下取整）
- **枚举字段**：`channel.activeChannel`（`WECHAT_MCH_TRANSFER` / `POINTS_CREDIT`）
- **脱敏字段**：`channel.wx.mchId`（仅后 4 位）；`channel.wx.keyConfigured`/`privateKeyConfigured`（布尔，是否已配置）；`wechatPayPublicKey`/`wechatPayPublicKeyId`/`mchSerialNo`（公开标识，明文）
- `monthlyLimit` 语义：-1=不限次数，0=禁用提现，>0=每月最多 N 次。

### 调用示例

```json
{"capability":"ops.marketing.cps-withdraw.get-settings","input":{},"summary":"查看提现功能配置"}
```

---

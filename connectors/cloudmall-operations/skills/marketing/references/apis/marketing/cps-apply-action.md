# 营销域 — CPS 分销员申请审核写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-distributor-flow.md`
> 用户通过自主申请或邀请成为分销员，运营在此审核；审核通过后系统**自动创建分销员账号**（初始等级 0、未分组、启用状态）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-apply-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-apply.audit 审核分销员申请 🔴 · cps-apply.save-settings 保存申请设置 🔴

---

## ✅ 审核申请 — `ops.marketing.cps-apply.audit`

- **风险**：🔴 审核通过即自动创建分销员账号（分佣主体）
- **前置**：申请必须处于**待审核（auditStatus=0）**状态；驳回（auditStatus=2）时 `auditRemark` 必填（服务端校验）。
- **后果**：通过 → 自动创建分销员（初始等级 0、未分组、启用），申请人即具备分佣资格；驳回 → 申请终态，用户需重新申请。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 申请 ID（路径参数，来自申请列表） |
| auditStatus | Integer | ✅ | 审核结果：1=通过，2=驳回 |
| auditRemark | String | 驳回时必填 | 审核备注，≤500 字符 |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-apply.audit","input":{"id":"5400000000000000001","auditStatus":2,"auditRemark":"资料不全，请补充后重新申请"},"summary":"驳回该分销员申请"}
```

---

## ✅ 保存申请设置 — `ops.marketing.cps-apply.save-settings`

- **风险**：🔴 策略影响（免审核/自动审核会改变新申请的流转路径）
- **前置**：整表保存语义——先查当前设置，改动的字段基于查询结果回填，避免遗漏字段造成配置回退。 **硬门禁：全租户/全局生效写——提交前必须发确认卡复述「现值 → 目标值」取得明确确认，指令参数齐全不豁免。**
- **后果**：`auditMode=1`（免审核）后新申请直接成为分销员；`autoAuditEnabled=true` 时超过 `autoAuditDays` 天的待审核单将按 `autoAuditAction` 自动处理。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| inviteEnabled | Boolean | ✅ | 邀请开关 |
| selfApplyEnabled | Boolean | ✅ | 自主申请开关 |
| auditMode | Integer | ✅ | 审核模式：0=需审核，1=免审核 |
| autoAuditEnabled | Boolean | ✅ | 自动审核开关 |
| autoAuditDays | Integer | 开启自动审核时必填 | 自动审核天数，1..30 |
| autoAuditAction | Integer | 否 | 自动审核动作：1=自动通过，2=自动驳回 |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-apply.save-settings","input":{"inviteEnabled":true,"selfApplyEnabled":true,"auditMode":0,"autoAuditEnabled":false,"autoAuditDays":3,"autoAuditAction":1},"summary":"保存申请设置：保持需审核，关闭自动审核"}
```

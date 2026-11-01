# 营销域 — CPS 分销员申请审核查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-distributor-flow.md`
> 用户通过自主申请或邀请成为分销员，运营在此审核；审核通过后系统**自动创建分销员账号**（初始等级 0、未分组、启用状态）。
> 通用约定：列表入参支持 `pageNum`（≥1，默认 1）/`pageSize`（1..100，默认 20）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-apply.search 分销员申请列表 · cps-apply.get-settings 申请设置查询（开关/审核模式/自动审核）
> 写操作见 `cps-apply-action.md`。

---

## 申请状态机

```
PENDING(0 待审核) ──审核通过(1)──> APPROVED(1 通过，自动创建分销员)
                 └─审核驳回(2)──> REJECTED(2 驳回，须填备注)
```

- 只有 `auditStatus=0`（待审核）的申请可执行审核；已审核的申请再次审核会报「已审核」业务错误。
- 申请设置中的「免审核模式 / 自动审核」会让新申请绕过人工审核环节，但已产生的待审核单仍走本审核能力。

---

## ✅ 申请列表 — `ops.marketing.cps-apply.search`

- **说明**：分页查询分销员申请；`name`/`phone` 模糊匹配，`uid` 精确匹配。申请人姓名/手机号由服务端从用户中心回填。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| auditStatus | Integer | 否 | 审核状态：0=待审核，1=通过，2=驳回 |
| name | String | 否 | 申请人姓名（模糊），≤100 字符 |
| phone | String | 否 | 申请人手机号（模糊），≤20 字符 |
| uid | String | 否 | 用户 UID，≤64 字符 |
| userType | Integer | 否 | 用户类型 |
| applyChannel | String | 否 | 申请渠道：`self`=自主申请，`invite`=邀请申请，`MINI_PROGRAM`=小程序 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 审核操作路径参数）
- **枚举字段**：`records[].auditStatus`（0/1/2，含 `auditStatusDesc` 中文描述）、`records[].applyChannel`（self/invite/MINI_PROGRAM）
- **格式敏感字段**：`records[].applyTime`/`auditTime`/`createdTime`（yyyy-MM-dd HH:mm:ss）
- 展示型字段：`name`/`phone`/`applyRemark`（申请备注）/`auditRemark`（审核备注）/`auditor`/`inviterUid` 可直接透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-apply.search","input":{"pageNum":1,"pageSize":20,"auditStatus":0},"summary":"查看待审核的分销员申请"}
```

---

## ✅ 获取申请设置 — `ops.marketing.cps-apply.get-settings`

- **说明**：查询分销员申请开关与审核策略配置。

### 入参

无（空对象）。

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| inviteEnabled | 邀请开关 |
| selfApplyEnabled | 自主申请开关 |
| auditMode | 审核模式：0=需审核，1=免审核 |
| autoAuditEnabled | 自动审核开关 |
| autoAuditDays | 自动审核天数（1..30） |
| autoAuditAction | 自动审核动作：1=自动通过，2=自动驳回 |

### 调用示例

```json
{"capability":"ops.marketing.cps-apply.get-settings","input":{},"summary":"查看分销员申请设置"}
```

---

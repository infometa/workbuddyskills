# 营销域 — 运营流程：CPS 提现管理（资金面最高危链路）

> 概念知识见 `references/domains/cps-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`cps-withdraw-query.md` / `cps-withdraw-action.md`。

---

## CPS 提现管理（资金面最高危链路）

**场景**：审核分销员提现申请；维护提现配置。**审核通过即触发异步真实打款。**

### 闭环流程

```
提现列表（cps-withdraw.search，auditStatus=PENDING_AUDIT）
  → 提现详情（cps-withdraw.detail，核对分销员/金额/渠道）
  → 核对用户指定的审核结论；缺对象/结论或指令矛盾时澄清，不替用户选择
  → 审核（cps-withdraw.audit，执行摘要说明单号+分销员+金额+渠道与打款/回退后果）
    （执行授权交由当前运行时按所选审批模式处理；不另发追问卡重复审批，取消/拒绝不执行）
      ├─ PASS：AUDIT_PASS + 发起异步打款 → 提现状态 PENDING → PROCESSING → (WAIT_USER_CONFIRM 微信) → SUCCESS / FAILED
      └─ REJECT：AUDIT_REJECTED + 佣金余额立即回退（产生「回滚」流水），不计入月度次数
  → 复查提现状态（cps-withdraw.search / detail —— 审核接口返回成功不代表打款成功）
  → [可选] 审核日志（cps-withdraw.audit-logs，含自动免审记录）
```

### 字段确认红线
- **金额与打款方向以提现单详情为准，禁止 AI 推断或改写**；REJECT 时 remark 必填。
- 提现设置（`cps-withdraw.get-settings` → `cps-withdraw.save-settings`）：minAmount/maxPerOrder/autoPassThreshold/creditRatio 等金额与比例字段**禁止 AI 编造或默认取值**；机密字段（APIv3 密钥/商户私钥）留空=保留已存值；整表覆盖式保存，未传渠道子节点会被置空，务必携带完整结构。

### 参数来源

| 参数 | 来源 |
|------|------|
| withdrawNo | 提现列表/详情 |
| action / remark | 用户明确指示（PASS/REJECT 大写） |

### 异常处置
- 非 PENDING_AUDIT 状态审核 → 报业务错误，重查列表确认现态。
- 打款长时间停留在 PROCESSING / WAIT_USER_CONFIRM → 向用户说明微信渠道需用户确认收款，持续用查询能力复查。
- FAILED → 余额已自动回退，可提示用户重新发起。

---

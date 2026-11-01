# 营销域 — CPS 提现（资金面最高危）写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-withdraw-flow.md`
> 分销员佣金账户余额可申请提现；运营在此审核。**审核通过即触发异步打款链路（真实资金出账）**——本模块写操作均属资金面最高危档。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-withdraw-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-withdraw.save-settings 保存提现设置 🔴🔴 · cps-withdraw.audit 提现审核 🔴🔴

---

## ✅ 保存提现设置 — `ops.marketing.cps-withdraw.save-settings`

- **风险**：🔴🔴 资金面最高危（金额阈值、免审阈值、渠道比例直接决定资金流转规则）
- **字段确认红线**：`minAmount`/`maxPerOrder`/`autoPassThreshold`/`creditRatio` 等**金额与比例字段禁止 AI 编造或默认取值**——必须用户逐项给出后再组装请求；建议先查当前设置，仅回填用户明确要求变更的字段。
- **密钥语义**：微信渠道的 APIv3 密钥/商户私钥等机密字段**留空 = 保留已存值**（服务端回填），传新值 = 覆盖；机密内容必须来自用户提供的原文。整表覆盖式保存——未传的渠道子配置节点会被置空，务必携带完整结构。
- **后果**：立即生效，影响后续所有提现申请的准入与免审判定。 **硬门禁：全租户/全局生效写——提交前必须发确认卡复述「现值 → 目标值」取得明确确认，指令参数齐全不豁免。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | Boolean | 否 | 提现功能开关 |
| minAmount | Number | 否 | 最低提现金额（元），≥0.01 |
| maxPerOrder | Number | 否 | 单次提现上限（元），0.01..50000 |
| monthlyLimit | Integer | 否 | 月度提现次数：-1=不限，0=禁用，>0=每月 N 次 |
| timeWindow | Object | 否 | 提现时间窗口 |
| timeWindow.enabled | Boolean | 否 | 是否启用窗口 |
| timeWindow.startDay | Integer | 否 | 窗口起始日（每月第几天） |
| timeWindow.endDay | Integer | 否 | 窗口结束日（每月第几天） |
| audit | Object | 否 | 审核配置 |
| audit.enabled | Boolean | 否 | 是否启用审核 |
| audit.autoPassThreshold | Number | 否 | 自动通过阈值（元），金额 ≤ 该值免审核 |
| audit.skipInTimeWindow | Boolean | 否 | 窗口期内免审核 |
| channel | Object | 否 | 渠道配置 |
| channel.activeChannel | String | 否 | 生效渠道：`WECHAT_MCH_TRANSFER` / `POINTS_CREDIT` |
| channel.wx | Object | 否 | 微信渠道配置（机密字段留空=保留旧值） |
| channel.wx.enabled | Boolean | 否 | 微信渠道开关 |
| channel.wx.mchId | String | 否 | 商户号 |
| channel.wx.appId | String | 否 | 微信 AppId |
| channel.wx.apiV3Key | String | 否 | APIv3 密钥（仅换新时传入，加密存储） |
| channel.wx.mchPrivateKey | String | 否 | 商户私钥 PKCS8 PEM（仅换新时传入，加密存储；别名 privateKey） |
| channel.wx.mchSerialNo | String | 否 | 商户证书序列号 |
| channel.wx.wechatPayPublicKey | String | 否 | 微信支付公钥 PEM（替代平台证书验签） |
| channel.wx.wechatPayPublicKeyId | String | 否 | 微信支付公钥 ID |
| channel.pointsCredit | Object | 否 | 积分到账渠道配置 |
| channel.pointsCredit.enabled | Boolean | 否 | 积分渠道开关 |
| channel.pointsCredit.creditRatio | Number | ✅（传 pointsCredit 时） | 到账比例（1 元 = creditRatio 个积分），0.01..9999.99，最多两位小数 |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-withdraw.save-settings","input":{"enabled":true,"minAmount":10,"maxPerOrder":5000,"monthlyLimit":5,"timeWindow":{"enabled":false,"startDay":1,"endDay":28},"audit":{"enabled":true,"autoPassThreshold":100,"skipInTimeWindow":false},"channel":{"activeChannel":"POINTS_CREDIT","pointsCredit":{"enabled":true,"creditRatio":1.89}}},"summary":"保存提现设置：最低10元、单次上限5000元、积分渠道1.89倍"}
```

---

## ✅ 提现审核 — `ops.marketing.cps-withdraw.audit`

- **风险**：🔴🔴 **资金面最高危：审核通过即触发异步真实打款**
- **前置**：提现单必须处于**待审核（`PENDING_AUDIT`）**状态（其他状态审核会报业务错误）；驳回（REJECT）时 `remark` 必填。
- **执行授权与业务澄清**：先查详情，核对单号、分销员、金额（元）、渠道与状态，并在执行摘要/审批理由中说明 PASS 会触发打款、REJECT 会回退余额。对象和审核结论明确时，执行授权交由当前运行时按所选审批模式处理，不另发追问卡重复审批。缺对象、缺审核结论或指令矛盾时才澄清；用户取消后不提交，运行时拒绝后不绕行。**金额与打款方向以提现单详情为准，禁止 AI 推断或改写；推荐选项和发问成功不等于用户确认，审批受阻不等于审核已受理。**
- **后果**：
  - **PASS**：审核状态 → 审核通过，同时发起异步转账（微信商家转账 / 积分充值）。打款结果以提现状态为准：处理中 → 待用户确认（微信）→ 成功/失败；失败自动回退佣金余额。审核接口返回成功**不代表打款成功**，需稍后用列表/详情复查提现状态。
  - **REJECT**：审核状态 → 审核驳回，佣金余额立即回退（产生「回滚」流水），该单不计入月度提现次数。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| withdrawNo | String | ✅ | 提现单号 |
| action | String | ✅ | 审核动作：`PASS`（通过）/ `REJECT`（驳回），大写 |
| remark | String | 驳回时必填 | 审核备注（驳回时必填；通过时建议填写） |

### 出参（原始数据）

- 无业务数据（成功即受理；打款结果异步流转，用查询能力复查）。

### 调用示例

```json
{"capability":"ops.marketing.cps-withdraw.audit","input":{"withdrawNo":"WD20260910000187654321","action":"PASS","remark":"核对无误，同意打款"},"summary":"审核通过该提现申请并发起打款"}
```

---

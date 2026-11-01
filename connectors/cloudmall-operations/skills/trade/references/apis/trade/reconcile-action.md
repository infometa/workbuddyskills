# 交易域 — 对账写操作契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；运营流程：`references/flows/trade-finance.md`
> **先读现值**：全部写入先用 `reconcile-query.md` 的 diff.search → diff.detail → handle-logs 核对差异依据与既有结论；节点配置更新前 config.list 读现值。
> 所有 ID 为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。并发导致状态冲突时停止，重新读取后由用户决定，不能改用另一处置动作绕过。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 reconcile.diff.mark-error 🔴 · reconcile.diff.escalate 🟡 · reconcile.diff.confirm 🔴 · reconcile.diff.remark 🟡 · reconcile.config.update 🔴 · reconcile.alert-notify.save 🟡 · reconcile.task.trigger 🔴

---

## ✅ 标记差异差错 — ops.trade.reconcile.diff.mark-error

用途：将有证据支持的差异认定为误差（🔴）。`reason` 必填、非空且最多 500 字符；这会形成处理结论，不能替代普通备注，需要已核实证据。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| diffId | string | 必填；十进制字符串 | 差异检索记录的 id |
| reason | string | 必填，非空白，最多 500 字符 | 用户已核实的处置依据/说明 |

当前状态要求：`PENDING`；结果状态：`MARKED_ERROR`。先读详情和处理记录，明确说明本次结论。返回无业务数据，执行后回读详情及记录，核对状态和新增操作类型。来源：`ReconcileDiffService` 的状态条件更新与日志写入。字段 Bean Validation 生效。

```json
{
  "capability": "ops.trade.reconcile.diff.mark-error",
  "input": {
    "diffId": "8200000000000000001",
    "reason": "支付渠道延迟入账"
  },
  "summary": "标记差异"
}
```

---

## ✅ 升级差异 — ops.trade.reconcile.diff.escalate

用途：把需其他角色介入的差异升级（🟡）。仅 `diffId` 必填；`remark` 可省略，传入时必须非空且最多 1000 字符，可附真实处理说明。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| diffId | string | 必填；十进制字符串 | 差异检索记录的 id |
| remark | string | 可选；Agent 提供时要求非空白且最多 1000 字符 | 用户已核实的处置依据/说明 |

当前状态要求：`PENDING`；结果状态：`ESCALATED`。先读详情和处理记录，明确说明本次结论。返回无业务数据，执行后回读详情及记录，核对状态和新增操作类型。来源：`ReconcileDiffService` 的状态条件更新与日志写入。当前入口未启用该可选说明的 Bean Validation；非空及长度限制是 Agent 输入纪律，不能宣称服务端已强制校验。升级不是解决。

```json
{
  "capability": "ops.trade.reconcile.diff.escalate",
  "input": {
    "diffId": "8200000000000000001",
  "remark": "请财务复核差异来源"
  },
  "summary": "升级差异"
}
```

---

## ✅ 确认差异处理 — ops.trade.reconcile.diff.confirm

用途：确认差异已经处理（🔴）。仅 `diffId` 必填；`remark` 可省略，传入时必须非空且最多 1000 字符。确认代表处理结论，不能因“待跟进”而调用；确认不会自动退款/补收。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| diffId | string | 必填；十进制字符串 | 差异检索记录的 id |
| remark | string | 可选；Agent 提供时要求非空白且最多 1000 字符 | 用户已核实的处置依据/说明 |

当前状态要求：`ESCALATED`（仅已升级记录可确认）；结果状态：`RESOLVED`。先读详情和处理记录，明确说明本次结论。返回无业务数据，执行后回读详情及记录，核对状态和新增操作类型。来源：`ReconcileDiffService` 的状态条件更新与日志写入。当前入口未启用该可选说明的 Bean Validation；非空及长度限制是 Agent 输入纪律，不能宣称服务端已强制校验。

```json
{
  "capability": "ops.trade.reconcile.diff.confirm",
  "input": {
    "diffId": "8200000000000000001",
  "remark": "已完成核对并关闭"
  },
  "summary": "确认差异处理"
}
```

---

## ✅ 差异备注 — ops.trade.reconcile.diff.remark

用途：追加处理过程说明（🟡），不改变差异最终结论。`diffId`、`remark` 均必填，后者非空且最多 1000 字符；备注只记录说明。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| diffId | string | 必填；十进制字符串 | 差异检索记录的 id |
| remark | string | 必填，非空白，最多 1000 字符 | 用户已核实的处置依据/说明 |

当前状态要求：任意状态；结果状态：不变。先读详情和处理记录。返回无业务数据，执行后回读详情及记录，核对新增操作类型；备注不改变差异状态。来源：`ReconcileDiffService` 的状态条件更新与日志写入。字段 Bean Validation 生效。

```json
{
  "capability": "ops.trade.reconcile.diff.remark",
  "input": {
    "diffId": "8200000000000000001",
  "remark": "等待渠道侧回单"
  },
  "summary": "添加对账备注"
}
```

---

## ✅ 更新对账节点配置 — ops.trade.reconcile.config.update

用途：更新单个对账节点的配置（🔴）。影响该节点的自动对账频率与告警阈值。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| configId | ID字符串 | 是，路径参数 | config.list 返回的节点 ID |
| enabled | 布尔值 | 是 | 是否启用该节点自动对账 |
| frequency | 字符串 | 是，正则 `\d+h`，最小 1h | 对账频率（如 `4h`） |
| alertThreshold | 整数 | 是，1~10000 | 告警阈值（差异笔数） |

来源：`UpdateReconcileConfigRequest`。先 config.list 读现值，复述节点名与新旧值后提交；回读 config.list 核对。

```json
{
  "capability": "ops.trade.reconcile.config.update",
  "input": { "configId": "8200000000000000010", "enabled": true, "frequency": "4h", "alertThreshold": 100 },
  "summary": "更新对账节点配置"
}
```

---

## ✅ 保存告警通知配置 — ops.trade.reconcile.alert-notify.save

用途：保存对账告警通知配置（🟡）。全量覆盖，影响差异告警推送。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| enabled | 布尔值 | 是 | 是否启用告警通知 |
| webhookUrl | 字符串 | 否 | 企微机器人 Webhook URL |
| notifyStartTime / notifyEndTime | 字符串 | 否 | 通知时段（如 `09:00` / `21:00`） |

```json
{
  "capability": "ops.trade.reconcile.alert-notify.save",
  "input": { "enabled": true, "webhookUrl": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx", "notifyStartTime": "09:00", "notifyEndTime": "21:00" },
  "summary": "保存对账告警配置"
}
```

---

## ✅ 手动触发对账 — ops.trade.reconcile.task.trigger

用途：手动触发一次对账（🔴，异步执行）。**立即返回任务 ID 与批次号**，不等待对账完成；手动触发是补充手段，不是替代。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| nodeType | 字符串 | 是，非空 | 对账节点类型（config.list 的 nodeType 取值） |
| startDate | 字符串 | 是，`yyyy-MM-dd` | 对账开始日期 |
| endDate | 字符串 | 是，`yyyy-MM-dd`，须 ≥ startDate | 对账结束日期 |

来源：`ReconcileManualTriggerRequest`。结果 `ReconcileTriggerResultVO`：`taskId`（任务 ID）、`batchNo`（批次号）、`message`。触发后用 `task.search` / `reconcile.diff.search` 跟进结果；不要因未立即看到差异而重复触发。

```json
{
  "capability": "ops.trade.reconcile.task.trigger",
  "input": { "nodeType": "ORDER_PAYMENT", "startDate": "2026-09-16", "endDate": "2026-09-17" },
  "summary": "手动触发对账"
}
```

---

## 对账纪律

节点配置决定自动对账的节奏（frequency）与告警线（alertThreshold）。看板指标与差异单列表统计口径可能不同（今日 vs 待处理），不互推。标记差错和确认结论不会自动补收或退款；升级不是解决。

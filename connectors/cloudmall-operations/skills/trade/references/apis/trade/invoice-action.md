# 交易域 — 发票写操作契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；运营流程：`references/flows/trade-finance.md`
> **先读现值**：全部写入先在 `invoice-query.md` 的 search 中唯一定位 `id` 并复述金额、抬头和当前阶段（没有单票详情能力）；销方/税收等开票基础配置见 `invoice-config-query.md`。
> 所有 ID 为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 invoice.trigger 🔴 · invoice.retry 🔴 · invoice.red-flush 🔴 · invoice.apply-on-behalf 🔴 · invoice.auth-clear 🔴 · invoice.retry-file-transfer 🟡 · invoice.red-confirm-operate 🔴 · invoice.cancel 🔴

---

## ✅ 触发开票 — ops.trade.invoice.trigger

用途：对允许阶段的一张发票发起开具（🔴）。仅输入 `id`；因为没有单票详情能力，必须先在列表中用订单号/申请号/抬头等组合唯一定位并复述金额与阶段，再执行。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| id | string | 必填；十进制字符串 | 发票检索唯一记录的 id |

先在发票检索唯一确认编号、金额、抬头及当前状态；运行时允许 `INIT/PENDING/ISSUE_FAILED`，失败票优先使用专门重试能力。返回 boolean；`false` 表示条件未就绪或状态/并发检查未通过，不能报告已开票；`true` 也须回读状态，只有 `ISSUED` 才可报告已开具。需具备销方及开票配置，缺失时停止并说明业务配置不齐。来源：`InvoiceIssueServiceImpl.trigger/ensureReadyAndFillSellerSnapshot/casAndIssue`。回读用原申请编号检索，再比对同一 `id`。

```json
{
  "capability": "ops.trade.invoice.trigger",
  "input": {
    "id": "8100000000000000001"
  },
  "summary": "触发开票"
}
```

---

## ✅ 重试开票 — ops.trade.invoice.retry

用途：重试失败发票的开具（🔴）。仅输入 `id`；先用列表确认仍为失败阶段，超时后不可重复提交。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| id | string | 必填；十进制字符串 | 发票检索唯一记录的 id |

仅 `ISSUE_FAILED`；明确确认原申请号、抬头、金额与失败原因。运行时会用最新金额与商品税务映射重建明细，不能承诺金额永远与旧票一致。返回是固定对象而非 boolean：`ok` boolean，`invoiceId` ID，`status` string，`platformSerialNo/invoiceNo/failCode/failReason` 可空 string；这些键来自 `InvoiceIssueServiceImpl.retryWithDetail`。运营页面类型仍将其写成 boolean，属于前端类型落后，Agent 以本表为准。`ok=false` 或 `status=ISSUE_FAILED/UNKNOWN` 不可报成功；`ok=true` 也要用原申请编号检索确认 `ISSUED`，`ISSUING` 仅说明处理中。不要输出渠道流水值。

```json
{
  "capability": "ops.trade.invoice.retry",
  "input": {
    "id": "8100000000000000001"
  },
  "summary": "重试开票"
}
```

---

## ✅ 红冲发票 — ops.trade.invoice.red-flush

用途：对已开具的原票发起红冲（🔴）。`id` 必填；`reason` 是可省略文本，未给时系统会使用默认原因，但 Agent 必须要求用户明确给出红冲理由，避免隐式默认。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| id | string | 必填；十进制字符串 | 发票检索唯一记录的 id |
| reason | string | Java 可省略；Agent 必须取得明确非空原因 | 只允许这一附加键，禁止任意映射 |

仅 `invoiceType=1` 且 `status=ISSUED` 的原蓝票；确认票号、抬头、金额及用户原因。返回新红票 ID（可能为空，不能凭成功应答认定红冲完成）。用原订单编号检索，关联 `redOriginInvoiceId` 与返回 ID；原票 `RED_FLUSHED` 和红票最终状态需分别核验。原因省略会产生默认文案，因此 Agent 不省略。来源：`InvoiceController.redFlush` 对蓝票和状态检查、`RedFlushService`；映射实现并不开放其他键。

```json
{
  "capability": "ops.trade.invoice.red-flush",
  "input": {
    "id": "8100000000000000001",
    "reason": "交易退货退款"
  },
  "summary": "红冲发票"
}
```

---

## ✅ 代客开票 — ops.trade.invoice.apply-on-behalf

用途：代客开票（🔴）——运营代用户录入购方（抬头）信息，走标准开票流程。**已签收订单立即触发开票，未签收订单仅打标、签收后自动触发**。返回新发票 ID（字符串）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| orderNo | 字符串 | 是，非空 | 订单号（订单检索/详情或用户明确提供） |
| buyerType | 整数 | 是 | 购方类型：`1` 个人、`2` 企业 |
| buyerName | 字符串 | 是，非空 | 购方名称（个人姓名 / 企业全称，用户提供，不猜测） |
| buyerTaxpayerNo | 字符串 | 企业时必填 | 纳税人识别号；个人省略 |
| buyerAddress / buyerPhone / buyerBankName / buyerBankAccount | 字符串 | 否 | 企业注册地址/电话/开户银行/银行账号 |
| buyerEmail | 字符串 | 否 | 发票接收邮箱 |
| invoiceCategory | 整数 | 否 | 发票类型：**仅支持 `1` 电子普票**（服务端强制置 1，传其他值报错「代客开票仅支持电子普通发票」）；专票需求走管理后台 |
| remark | 字符串 | 否 | 备注 |

来源：`InvoiceApplyOnBehalfRequest`。购方信息必须来自用户（抬头与税号错开票即作废）；提交后用返回的 invoiceId 在 `invoice.search` 回读核对，并报告是立即开票还是打标待签收触发。

```json
{
  "capability": "ops.trade.invoice.apply-on-behalf",
  "input": {
    "orderNo": "SO20260905000001",
    "buyerType": 1,
    "buyerName": "张三",
    "invoiceCategory": 1
  },
  "summary": "代客开票"
}
```

---

## ✅ 清除认证阻塞 — ops.trade.invoice.auth-clear

用途：运营在电子税务局**实际完成**登录/实人认证后，手动清除认证阻塞标记（🔴，「我已完成认证」动作）。

无请求体。边界（源码注释明确）：不做任何真实探活验证——如果点击时实际未完成认证，重试仍会失败并重新写入标记，不产生脏数据。执行前确认用户已真正完成认证；执行后 1 分钟内定时任务恢复失败重试。回读 `auth-status` 确认 `blocked=false`。

```json
{
  "capability": "ops.trade.invoice.auth-clear",
  "input": {},
  "summary": "清除开票认证阻塞"
}
```

---

## ✅ 文件转存补跑 — ops.trade.invoice.retry-file-transfer

用途：重触发发票文件转存到 COS（🟡 排查用）。场景：发票文件已上传 COS 但 `pdfUrl/ofdUrl/xmlUrl` 未回写、仍停留在平台短期签名 URL 时立即触发，不等 10 分钟定时补偿。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | 发票 ID |

前置：仅 `ISSUED`（已开票）/ `RED_FLUSHED`（已红冲）状态可触发。**幂等**：已在 COS 则跳过，重复调用安全。异步转存：返回受理不代表已完成，稍后回读发票详情核对文件地址。

```json
{
  "capability": "ops.trade.invoice.retry-file-transfer",
  "input": { "id": "8100000000000000001" },
  "summary": "重触发发票文件转存"
}
```

---

## ✅ 红字确认单处置 — ops.trade.invoice.red-confirm-operate

用途：红字确认单的确认或拒绝（🔴）。红字发票开票中（`ISSUING`）且确认单待确认（`redConfirmStatus=PENDING`）时操作。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | 红票发票 ID |
| action | 字符串 | 是，仅 `confirm` / `reject` | 确认或拒绝红字确认单 |

前置（服务端三重校验）：必须是红票（invoiceType=2）、状态 `ISSUING`、`redConfirmStatus=PENDING`。确认后红票继续开具流程；拒绝后红冲终止。向用户复述蓝票金额、红冲原因与操作结论后执行；回读发票状态。

```json
{
  "capability": "ops.trade.invoice.red-confirm-operate",
  "input": { "id": "8100000000000000002", "action": "confirm" },
  "summary": "确认红字确认单"
}
```

---

## ✅ 取消开票 — ops.trade.invoice.cancel

用途：取消开票（🔴）。对允许状态的发票取消开票流程。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | 发票 ID |
| operatorName | 字符串 | 否，默认 `OPS` | 操作人名称（审计留痕） |

来源：`InvoiceController.cancel` → `InvoiceIssueService.cancel`。已开票（`ISSUED`）发票不能取消（需红冲）；执行前复述发票对象、抬头与当前阶段；执行后 `invoice.search` 回读状态应为 `CANCELLED`。

```json
{
  "capability": "ops.trade.invoice.cancel",
  "input": { "id": "8100000000000000001" },
  "summary": "取消开票"
}
```

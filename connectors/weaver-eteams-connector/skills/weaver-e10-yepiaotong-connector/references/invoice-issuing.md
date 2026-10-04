# 智能开票与存台账

## 什么时候读取

用户要求开票、开发票、开专票、开普票、填开发票、存台账，或已经给出开票字段并要求提交到业票通时读取本文件。

## Operation

| 阶段 | Operation | 风险 |
| --- | --- | --- |
| 准备开票或存台账 | `invoice.issuing.make.prepare` | read-before-write |
| 确认提交 | `invoice.issuing.make.apply` | high-risk-write |

## 输入要点

`mode` 必填：

- `issue`：正式开票，CLI 会确保 `operateType` 不传。
- `ledger`：仅存入待开台账，CLI 会固定 `operateType="5"`。

`payload` 是已整理好的 `MakeInvoiceReqDTO`。核心字段至少包括购方名称、发票类型、外部单号、金额合计和一条商品明细。专票或全电纸质专票必须提供购方税号。

### 购方信息补齐

修正后的资料包没有提供客户档案查询 operation。组装 payload 前，Agent 只能从用户输入、附件内容或对话上下文提取购方信息；资料不足时必须追问用户补齐，不要调用 `invoice.customer.*` 或绕过 CLI 查询原始接口。

- 个人普票：`invoiceType="7"`，`personLogo="1"`，无需税号。
- 企业专票或需要企业抬头时：必须由用户或附件提供购方名称、税号；地址、电话、开户行和账号有明确来源时才填入，没有来源不要编造。
- 从附件提取购方信息前，必须先提醒用户文件内容可能进入当前大模型上下文，并可能发送到解析服务，等待明确确认后再处理。

销方为 CLI 内置固定值（当前版本固定为销方名称 `上海泛微网络科技股份有限公司`、销方税号 `9131000070322836XD`，非按当前 E10 租户动态解析），Agent 无需也不应自行构造或改写销方字段；CLI 会一并补齐 `billingType="0"`、`sourceType="4"`、`asyncCallFlag="1"`、`invoiceMethod="5"`、`taxSign="1"`。Agent 不要把 Cookie、ETEAMSID、业务 Token 或认证字段放入 payload。

## 命令

简单 payload 可直接传 `--input-json`。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.issuing.make.prepare --input-json '{"mode":"ledger","payload":{"invoiceType":"8","externalDocumentNo":"AI-EXAMPLE-001","purchaserName":"XX科技有限公司","purchaserTaxNo":"91310000MA1234AB56","totalAmount":100,"taxAmount":6,"totalAmountWithTax":106,"details":[{"goodsName":"信息技术咨询服务","revenueCode":"3040205","taxRate":0.06,"amount":100,"amountWithTax":106,"taxAmount":6,"quantity":"1","unit":"项"}]}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.issuing.make.prepare --input-json '{"mode":"ledger","payload":{"invoiceType":"8","externalDocumentNo":"AI-EXAMPLE-001","purchaserName":"XX科技有限公司","purchaserTaxNo":"91310000MA1234AB56","totalAmount":100,"taxAmount":6,"totalAmountWithTax":106,"details":[{"goodsName":"信息技术咨询服务","revenueCode":"3040205","taxRate":0.06,"amount":100,"amountWithTax":106,"taxAmount":6,"quantity":"1","unit":"项"}]}}'
```

复杂 payload 建议保存为 UTF-8 JSON 文件。

Windows PowerShell：

```powershell
Set-Content -Encoding utf8 -LiteralPath .\issuing.json -Value @'
{
  "mode": "issue",
  "payload": {
    "invoiceType": "8",
    "externalDocumentNo": "AI-EXAMPLE-001",
    "purchaserName": "XX科技有限公司",
    "purchaserTaxNo": "91310000MA1234AB56",
    "totalAmount": 100,
    "taxAmount": 6,
    "totalAmountWithTax": 106,
    "details": [{"goodsName":"信息技术咨询服务","taxRate":0.06,"amount":100,"amountWithTax":106,"taxAmount":6,"quantity":"1","unit":"项"}]
  }
}
'@
weaver-work-cli --profile eteams --json invoice run invoice.issuing.make.prepare --input .\issuing.json
```

macOS/Linux（bash/zsh）：

```bash
cat > ./issuing.json <<'JSON'
{
  "mode": "issue",
  "payload": {
    "invoiceType": "8",
    "externalDocumentNo": "AI-EXAMPLE-001",
    "purchaserName": "XX科技有限公司",
    "purchaserTaxNo": "91310000MA1234AB56",
    "totalAmount": 100,
    "taxAmount": 6,
    "totalAmountWithTax": 106,
    "details": [{"goodsName":"信息技术咨询服务","taxRate":0.06,"amount":100,"amountWithTax":106,"taxAmount":6,"quantity":"1","unit":"项"}]
  }
}
JSON
weaver-work-cli --profile eteams --json invoice run invoice.issuing.make.prepare --input ./issuing.json
```

## 确认链

`.prepare` 返回 `preview`、`normalizedPayload`、`continuation` 和 `workflow.state="AWAITING_CONFIRMATION"`。向用户展示发票类型、购方名称、税号、外部单号、明细数量、合计不含税、税额和价税合计；用户明确确认开票或存台账后，再用相同 payload、continuation 和 `confirm=true` 调用 `.apply`。

## 输出处理

`.apply` 成功返回 `mode`、`serialNo`、`orderNo`、`ledgerOnly` 和原始响应。正式开票时说明申请已提交；存台账时说明已保存为待开台账。接口失败时展示业务错误原因，不自动重试。

## 注意

正式开票是高风险且不可逆的业务写入。同一 continuation 只服务一次确认场景；如果用户修改购方、金额、税率或明细，必须重新 prepare。

字段提取、税率推断和金额计算由 Agent 在调用 CLI 前完成。原始税号、金额、名称、编码等值必须逐字符保留；不要为了“补齐位数”或“格式化”改写用户或接口给出的 ID、日期和金额。

如果用户提供 Excel、Word、TXT、图片或截图来提取开票字段，解析前必须先提醒用户：文件内容可能进入当前大模型上下文，并可能发送到解析服务；必须等待明确确认。

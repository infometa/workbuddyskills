# 交易域 — 发票查询契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；开票/红冲/取消等写操作见 `invoice-action.md`，开票平台/销方/税收配置见 `invoice-config-query.md`；运营流程：`references/flows/trade-finance.md`
> 本页入参表列出的字段构成完整允许集合，未列字段不发送；省略可选字段优于传空字符串。所有 ID 为十进制字符串。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 invoice.search · invoice.tab-count · invoice.auth-status · invoice.query-platform

---

## ✅ 发票搜索 — ops.trade.invoice.search

用途：检索开票申请及当前开票阶段。可用 `keyword` 搜索订单号、抬头或申请编号，或用 `status` 精确筛选；单票写操作前必须从结果唯一取得十进制字符串 `id`。不能展示文件或平台敏感信息（银行、税号、联系方式及文件链接不可整段复述）。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| pageNum | integer | 可选，默认 1；Agent 使用正整数 | 页码；Java 未配置数值校验 |
| pageSize | integer | 可选，默认 20；Agent 控制 1～100 | 每页条数；该 DTO 未配置最大值校验 |
| keyword | string | 可选 | 订单号、抬头、申请编号模糊匹配 |
| status | string | 可选，精确值见返回说明 | 状态筛选 |

记录来自 `InvoiceListVO`：`id/applyNo/orderNo/buyerName/invoiceType/invoiceAmount/status/invoiceNo/failCode/failReason/retryCount/maxRetry/applyTime/issueTime/redOriginInvoiceId/redOriginApplyNo/redConfirmStatus`。`invoiceType=1` 蓝票，`2` 红票；金额使用 `invoiceAmount`，不要将 `totalAmount`（不含税）直接替代。运行时状态为 `INIT/PENDING/ISSUING/ISSUED/ISSUE_FAILED/RED_FLUSHED/CANCELLED`（状态机见 `trade-enums.md`）；筛选 `PENDING` 会合并 `INIT` 与 `PENDING`，其他值精确匹配。按 `keyword` 找到记录后仍须逐字比对 `applyNo/orderNo/id`，避免模糊命中多票。**`items[]` 在运营端列表恒为 null**（明细行仅 App 端详情接口填充；运营端无发票明细查询能力，发票行金额以 `invoiceAmount` 为准）。红票记录另含 `afterSaleNo`（红冲关联的售后单号）。来源：`InvoicePageQuery`、`InvoiceServiceImpl.page/toListVO`、`InvoiceListVO`。

```json
{
  "capability": "ops.trade.invoice.search",
  "input": {
    "pageNum": 1,
    "pageSize": 20
  },
  "summary": "查询发票"
}
```

---

## ✅ 发票阶段计数 — ops.trade.invoice.tab-count

用途：读取各开票阶段的数量。无输入；只适合作为工作量看板，不是单票可操作性依据；统计不承接列表关键词。

`InvoiceTabCountVO` 含 `all/pending/issuing/issued/issueFailed/redFlushed`；`pending` 合计 `INIT/PENDING`，没有单独 `cancelled` 计数字段。来源：`InvoiceServiceImpl.tabCount`。

```json
{
  "capability": "ops.trade.invoice.tab-count",
  "input": {},
  "summary": "统计发票状态"
}
```

---

## ✅ 认证阻塞状态查询 — ops.trade.invoice.auth-status

用途：查询开票平台的认证阻塞状态。`blocked=true` 表示平台登录/实人认证失效，开票重试被暂停，需运营到电子税务局完成认证后清除标记。

入参：无，传 `{}`。结果来源 `Map<String, Object>`：`blocked`（布尔值）、`platformCode`（平台编码）、`code` / `message`（阻塞原因）、`occurAt`（发生时间）。未配置平台或无阻塞时仅返回 `blocked=false`。

```json
{
  "capability": "ops.trade.invoice.auth-status",
  "input": {},
  "summary": "查询开票认证状态"
}
```

---

## ✅ 发票平台状态查询 — ops.trade.invoice.query-platform

用途：查询单张发票在开票平台的最新状态（🟢 排查用）。POST 纯查询语义，不产生写入。

| 参数 | 类型 | 必填 | 来源 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | invoice.search 唯一定位的发票 ID |

结果来源 `Map<String, Object>`，固定键集合（`InvoiceController.queryPlatform` 构造）：`invoiceId`、`status`（平台查询状态枚举名）、`invoiceNo`、`pdfUrl`（平台侧短期签名地址）、`failCode` / `failReason`、`rawResponse`（**平台原始响应文本，可能含敏感技术细节，不向用户整段复述**）、`redConfirmNo` / `redConfirmStatus`（红字确认单实时状态，查询时会同步回写发票记录）。平台未配置或无可查编号时返回 `{"error": "..."}` 说明性对象。以平台状态为排查依据时如实报告字段，不自行翻译成统一状态机。

```json
{
  "capability": "ops.trade.invoice.query-platform",
  "input": { "id": "8100000000000000001" },
  "summary": "查询发票平台状态"
}
```

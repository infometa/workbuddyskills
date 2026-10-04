# 工具路由与契约

仅在需要选择工具、核对参数、处理自定义应用或解释当前 MCP 行为时读取本文。

## 权威顺序

按以下顺序判断工具契约：

1. 当前 MCP `tools/list` 和本次调用的实际响应。
2. 与当前 Connector 配套的 `@laiye-adp/mcp` 实现。
3. ADP 官方 OpenAPI 和产品文档。
4. 本文中的 v0.1.4 快照。

发现不一致时不要猜测，保留实际工具名、参数和响应作为依据。

## 22 个工具

### 文件、通用解析和任务控制

| 工具 | 何时使用 | 必填输入 | 关键输出/行为 |
|---|---|---|---|
| `upload_temporary_file` | 本地路径或 `file://` 需要转换为可访问 URL | `chunk` | `data.id`、`data.download_url`；每次一个文件 |
| `parse_document` | 全文、OCR、版面、表格、阅读顺序、坐标或类型未知 | `file` | `data.doc_recognize_result` |
| `query_task` | 查询异步解析或抽取状态 | `task_id` | 原样返回任务包装体 |
| `get_result` | 已知成功但查询响应未带完整结果 | `task_id` | 当前实现与 `query_task` 使用同一查询端点 |

### 票据与订单

| 工具 | 默认场景 | 当前基础费率 |
|---|---|---:|
| `extract_china_invoice` | 中国地区 30+ 常见票据、可验真票种 | 抽取 0.8 积分/页；验真成功另收 0.5 积分/次 |
| `extract_global_invoice` | 普通海外发票/收据，需标准解析链或 OCR 中间结果 | 1.5 积分/页 |
| `extract_global_invoice_fast` | 海外发票/收据低延迟或批量吞吐，不需要 OCR 结果 | 1.0 积分/页 |
| `extract_sea_invoice_fast` | 东南亚发票/收据，尤其是 WHT 预扣税字段 | 1.0 积分/页 |
| `extract_purchase_order` | 采购订单；销售订单按工具描述尝试 | 1.5 积分/页 |

不要把独立“发票验真”当作 MCP 工具：官方 OpenAPI 有独立接口，但 v0.1.4 未注册该工具；这不代表 SaaS 验真免费。`extract_china_invoice` 只可报告其响应实际返回的验真字段和状态。同一份多页发票仅需验真 1 次，多份独立发票分别计次；完整计费规则见 [积分、认证与服务限制](billing-auth-and-limits.md)。

标准海外与高速海外之间按需求选择：

- 用户要求 OCR 中间结果、标准解析链或更完整的来源信息时，使用 `extract_global_invoice`。
- 用户明确要求快速、低延迟或批量吞吐，且只要字段时，使用 `extract_global_invoice_fast`。
- 文档来自东南亚或要求 WHT 时，使用 `extract_sea_invoice_fast`。
- 不要对同一文件同时调用标准版和高速版做无授权对比。

### 11 个中国卡证工具

| 文档 | 工具 | 边界 |
|---|---|---|
| 中国大陆居民身份证 | `extract_id_card` | 支持正反面 |
| 银行卡 | `extract_bank_card` | 只识别卡面公开信息，不期待 CVV |
| 车辆合格证 | `extract_vehicle_cert` | 机动车整车出厂合格证 |
| 开户许可证 | `extract_account_permit` | 企业开户许可证 |
| 驾驶证 | `extract_driver_license` | 支持正副页 |
| 营业执照 | `extract_business_license` | 中国企业营业执照 |
| 中国护照 | `extract_passport_cn` | 不处理外国护照 |
| 行驶证 | `extract_vehicle_license` | 支持正副页 |
| 组织机构代码证 | `extract_org_code_cert` | 主要用于历史证件；新证照优先营业执照 |
| 户口本 | `extract_household_book` | 支持首页和个人页 |
| 港澳通行证 | `extract_hk_macao_permit` | 不要扩写成“港澳台通行证” |

证件类型不匹配时停止并改用正确工具；不要通过相邻卡证工具试错。

### 自定义抽取

| 工具 | 公开意图 | v0.1.4 实际边界 |
|---|---|---|
| `list_custom_extract_apps` | 列出用户自定义抽取应用 | 固定请求 `app_type=0`，而后端定义 0 为系统预设、1 才是用户创建；不能保证列出自定义应用 |
| `execute_custom_extract_app` | 使用给定 `app_id` 执行抽取 | 必填 `app_id` 和 `file`；支持 `wait=false` |

执行规则：

1. 用户给出可信 `app_id` 时直接执行。
2. 只有应用名称时调用列表一次。
3. 要求 ID 或名称精确匹配；若响应含 `app_type`，只把 `app_type=1` 视为用户自定义应用。
4. 没有精确匹配时请用户从 ADP 控制台提供 `app_id`。不要从系统预设结果中猜 ID。

## 共享输入 Schema

17 个预置处理工具（16 个抽取工具和 `parse_document`）共享这些公开参数；`execute_custom_extract_app` 另加必填 `app_id`：

| 参数 | 必填 | 规则 |
|---|---|---|
| `file` | 是 | 只传 HTTP(S) URL 或 Base64；其他字符串会被当作 Base64 |
| `file_name` | 否 | v0.1.4 未转发，当前不要依赖 |
| `with_rec_result` | 否 | 默认 `true`；只对 extract 路径转发，高速版仍不返回 OCR 结果 |
| `wait` | 否 | 默认 `true`；`false` 只切换到创建异步任务，不会自动轮询 |
| `timeout_seconds` | 否 | 默认 300；Skill 主动限制在 1～900，实际实现只要求正数 |
| `accept_language` | 否 | `zh` 走中国区，`en` 走全球区；默认 `zh` |

当前实现不会把 `file_name` 加入请求体，也不会为 `parse_document` 发送 `with_rec_result`。不要用这些参数解释结果差异。

## 输出契约

除上传工具外，v0.1.4 没有注册 `outputSchema`，并原样返回 ADP API 包装体。按实际响应读取：

```json
{
  "code": "success",
  "message": "",
  "tips": null,
  "data": {
    "task_id": "...",
    "status": 4,
    "doc_recognize_result": [],
    "extraction_result": []
  }
}
```

- 不要假设 `task_id`、`status` 或结果数组位于顶层。
- `parse_document` 主要读取 `data.doc_recognize_result`。
- 抽取工具主要读取 `data.extraction_result`。
- 普通字段通常包含 `field_values`；表格字段通常包含 `table_values`。
- 响应字段可能随应用配置变化，只返回实际存在的字段。

上传工具声明了输出 Schema，但后端部分字段可为空。必须检查 `code` 和非空 `data.download_url`，不要只依赖 Schema 校验。

## 当前实现差异

- `query_task` 和 `get_result` 当前调用完全相同的 GET 路径；不要在查询已经返回完整结果时重复取结果。
- 两个任务工具先查询抽取路径，任何错误都会自动回退到解析路径。因此第二个错误可能掩盖第一个错误；报告最终工具错误，不要据此断言任务类型。
- `accept_language` 决定 API 域名。创建异步任务后查询时必须复用相同值。
- 高速海外 OpenAPI 的 `enable_multi_ticket` 没有暴露在 MCP Schema 中，不要传递。
- 实际 MCP initialize 版本可能仍显示 0.1.0；判断能力时以 `tools/list` 为准，不要仅凭自报版本。

## 官方参考

- [ADP MCP Server](https://adp-doc.laiye.com/products/adp-mcp.md)
- [国内通用票据](https://adp-doc.laiye.com/api-reference/preset-domestic-bills.md)
- [海外发票和收据](https://adp-doc.laiye.com/api-reference/preset-overseas-documents.md)
- [海外发票和收据高速版](https://adp-doc.laiye.com/api-reference/preset-overseas-invoices-fast.md)
- [采购订单](https://adp-doc.laiye.com/api-reference/preset-purchase-orders.md)
- [卡证](https://adp-doc.laiye.com/api-reference/preset-cards.md)
- [查询应用列表](https://adp-doc.laiye.com/api-reference/adp-api/应用管理/查询应用列表.md)

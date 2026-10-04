---
name: query-merchant-invoice
display_name: 查询商户发票信息
display_name_en: Query Merchant Invoice
description: 用 wpe-general-connector（腾讯数电发票）连接器查询企业在系统内的发票信息（首选按 fapiao_id 直查，也支持发票号码 / 业务单号 / 申请单号）
description_zh: 用 wpe-general-connector（腾讯数电发票）连接器查询某企业在开票系统里的开票状态与开票流水（invoice_deal），fapiao_id、发票号码、申请单号、业务单号四种入口
description_en: Query an enterprise's invoice issuing status and deal records via the wpe-general-connector connector, by fapiao_id, bill_no, apply id or deal_id
category: data
version: 1.7.1
---

# 查询商户发票信息

用 **wpe-general-connector（腾讯数电发票）** 连接器查「某笔开票在系统里是什么状态 / 某天开了多少票」。

## 1. 认证与连接器定位（先做，别急着说"没有工具"）

唯一依赖连接器 **`wpe-general-connector`（中文名「腾讯数电发票」）**。

| 项 | 值 |
|---|---|
| 连接器 | `wpe-general-connector`（中文名「腾讯数电发票」） |
| 税号传递 | 连接器请求头 `X-Subject-Id`（不是工具参数）；查询范围自动限定该企业（`subject_isolated: true`） |
| 令牌 | `Authorization: Bearer <token>`，由连接器管理 |

**定位与授权流程**：

1. 会话中找不到 `wpe-general-connector` 暴露的工具 → 用名称 `wpe-general-connector`（或「腾讯数电发票」）在连接器列表查找并加载该 MCP。
2. 加载后**首次调用不带 token**（探活）。返回 **HTTP 401** → 连接器未授权，**停下提示用户完成 MCP 授权**，通过后再继续；不要重试、不要换直连方式绕过。
3. **税号以用户本次提供的为准**，不要罗列/推荐/提示任何「已接入税号」，也不要凭历史记录替用户选。用户没给税号时按其默认绑定企业查询。

> ⚠️ 功能只能通过该连接器实现：**禁止**另写 HTTP 客户端、脚本或 curl 访问服务端点，也禁止用其它 MCP 连接器替代。

## 2. 可用工具清单

| 工具 | 用途 | 何时用 |
|---|---|---|
| `invoice_status` | 单张发票开具状态 | **首选**，有 `fapiao_id` / `bill_no` / `invoice_apply_id` 之一时 |
| `query_table` | 数据集明细查询 | 按 deal_id / 字段过滤、或拉某时间窗流水 |
| `aggregate_query` | 聚合统计（count/sum/avg/max/min） | 统计某天/某时段笔数、金额、状态分布 |
| `health_check` | 服务 / DB / Consul 就绪检查 | 排障时确认连接器状态与税号 |
| `list_internal_apis` | 列出可调用内部接口 | 排障 |

### 2.1 `invoice_status`（单张状态，首选）

**参数**（三选一，互斥，一次只传一个）：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fapiao_id` | string | 三选一 | 商户发票单号，落库 `req_bill_serial_num`（常 32 位十六进制） |
| `invoice_apply_id` | string | 三选一 | 发票申请单号，落库 `biz_serial_num` |
| `bill_no` | string | 三选一 | 20 位全电发票号码 |

**返回值**（`meta` 比 `query_table` 多三个键）：

```json
{"fapiao_id":"...","found":true,"authorized":true,
 "rows":[{"deal_id":"...","bill_no":"...","req_bill_serial_num":"...","biz_serial_num":"...",
 "bill_status":"00","bill_status_name":"开票成功","bill_amount":"50.00",
 "channel_id":"WECHAT","tax_payer_no":"...","enterprise_id":"...",
 "bill_error_message":"","billing_date":"2026-09-17 13:44:36","create_time":"2026-09-17 13:44:36"}]}
```

**结果解读**（`found` + `authorized` 两布尔位）：

| found | authorized | 含义 | 处置 |
|---|---|---|---|
| true | true | 命中且归属本企业 | 直接报 `bill_status` |
| false | — | 该单号未落库 | 确认税号、确认是否已同步（T+0 未必即时） |
| true | false | 有记录但**不属于当前税号** | 请用户提供该笔所属企业的税号后重查 |

`bill_status` 释义：`00`=开票成功 / `01`=开票中 / `02`=开票失败（原因在 `bill_error_message`）。只有 `02` 且 `bill_error_message` 非空才算失败；`01` 是正常在途，多数分钟级转 `00`。

### 2.2 `query_table`（明细查询）

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `dataset` | string | ✅ | 数据集名，当前仅 `invoice_deal` |
| `start_date` / `end_date` | string | ✅ | `YYYY-MM-DD`，**按天查**（大窗口超时） |
| `date_field` | string | 视情况 | 时间字段，如 `create_time` / `billing_date` |
| `filters` | array | 否 | `[{"field":"...","op":"eq","value":"..."}]`，**必须是数组且带 op** |
| `order_by` / `order_dir` | string | 否 | 排序字段 / `asc` `desc` |
| `limit` | number | 否 | 明细建议 ≤20（超约 60 条触发 20000 字符输出上限） |
| `offset` | number | 否 | 分页偏移 |

**示例**（按 fapiao_id 过滤，与 `invoice_status` 等价）：

```json
{"dataset":"invoice_deal","date_field":"create_time",
 "start_date":"2026-09-17","end_date":"2026-09-17",
 "filters":[{"field":"req_bill_serial_num","op":"eq","value":"<fapiao_id>"}],"limit":3}
```

按业务单号：

```json
{"dataset":"invoice_deal","date_field":"create_time",
 "start_date":"2026-09-17","end_date":"2026-09-17",
 "filters":[{"field":"deal_id","op":"eq","value":"<deal_id>"}],"limit":10}
```

### 2.3 `aggregate_query`（聚合统计）

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `dataset` | string | ✅ | 仅 `invoice_deal` |
| `aggregation` | string | ✅ | `count` / `count_distinct` / `sum` / `avg` / `max` / `min` |
| `metric_field` | string | ✅ | 度量字段，如 `bill_no`（计数）/ `bill_amount`（金额） |
| `group_by` | array | 否 | **必须是数组**（传字符串报错），最多 3 个维度 |
| `start_date` / `end_date` | string | ✅ | 按天查 |
| `granularity` | string | 否 | `total` / `day` / `week` / `month` |

**示例**（某日状态分布）：

```json
{"dataset":"invoice_deal","start_date":"2026-09-17","end_date":"2026-09-17",
 "aggregation":"count","metric_field":"bill_no","group_by":["bill_status"]}
```

## 3. 标准流程

### 步骤 1：按 fapiao_id 直查（首选）

有 `fapiao_id` 就**直接查**，不要用时间/金额去猜是哪笔票：

```json
{"fapiao_id": "<用户提供的 fapiao_id>"}
```

### 步骤 2：读状态

按 §2.1 的 `found` / `authorized` / `bill_status` 解读。

### 步骤 3：流水对账 / 批量（备选）

用户给 `bill_no` / `deal_id`、或要拉某时间窗流水时走 `query_table`；统计笔数/金额/分布时走 `aggregate_query`。

## 4. 错误场景与边界

| 场景 | 现象 | 处置 |
|---|---|---|
| 字段未登记 | 报「未登记字段 xxx」 | **先原样重跑一次**（可能只是配置刷新延迟，2026-09-17 曾出现），不要直接下"查不到"结论 |
| 查询超时 | 「查询超时（上限 10000ms）」 | 窗口改 `start_date == end_date` 逐天查，多天并发（一批 8~10 个） |
| 输出超限 | 只回一段话 + meta，不给 rows（约 60 条触发） | `limit` 降到 ≤20，或用 `filters` 缩小范围 |
| 查不到记录 | `found=false` | 税号不对 / 数据未同步（T+0），**≠ 开票失败** |
| group_by 传字符串 | `Expected array, received string` | 改成数组 `["bill_status"]` |
| filters 传对象 / 缺 op | `Expected array` / `缺少必填参数 filter.op` | 改成 `[{"field":..,"op":..,"value":..}]` |
| 归属不符 | `found=true, authorized=false` | 换所属企业税号重查 |

**失败票定位**：全月失败若集中在某天，先 `query_table` 过滤该天 `bill_status=02` 取样例，看 `bill_error_message`（如「授信额度不足」属额度耗尽，非接口/参数问题）。

## 5. 输出

结论必须包含：查询键、`bill_status` 中文释义、票号 `bill_no`、金额、失败时的 `bill_error_message`，以及 `found` / `authorized` 归属判断位。查不到时说明两种可能原因（税号不对 / 尚未同步），不要说成开票失败。

## 参考

- 服务端能力清单、字段字典、语法与超时限制（唯一数据源）：`references/mcp-capabilities.md`

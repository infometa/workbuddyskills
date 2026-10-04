# wpe-general-connector（腾讯数电发票）能力清单（2026-09-17 实测）

调用方式：**只用 wpe-general-connector（腾讯数电发票）连接器提供的工具**。查询范围由连接器的企业税号决定，
所有查询自动限定该企业（`subject_isolated: true`）。**禁止**用脚本 / curl / 其它连接器直连服务端点。

## 工具清单（7 个）

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `health_check` | 服务 / DB / Consul 就绪检查 | 无 |
| `query_table` | 数据集明细查询 | dataset, start_date, end_date, date_field, filters, order_by, order_dir, limit, offset |
| `aggregate_query` | 聚合统计（count/sum/avg/max/min，日/周/月） | dataset, metric_field, aggregation, group_by, ... |
| `invoice_status` | 单张发票开具状态 | bill_no / fapiao_id / invoice_apply_id（三选一，互斥） |
| `list_internal_apis` | 列出可调用内部 HTTP 接口 | 无 |
| `call_internal_api` | 调用内部接口（api + params） | api, params |
| `discover_services` | 查 Consul 实例地址与健康 | service, refresh |

## invoice_status 三键现状（2026-09-17 14:05 复测：全部可用 ✅）

| 查询键 | 落库字段 | 形态 | 实测 |
|---|---|---|---|
| `fapiao_id` | `req_bill_serial_num` | 商户发票单号，常为 32 位十六进制 | ✅ 可用 |
| `invoice_apply_id` | `biz_serial_num` | 发票申请单号，如 `<申请单号>` | ✅ 可用 |
| `bill_no` | `enterprise_id`（归属校验） | 20 位全电发票号码 | ✅ 可用 |

> 历史：2026-09-17 上午三键曾因 `datasets.json` 未登记 `req_bill_serial_num` / `biz_serial_num` /
> `enterprise_id` 全部不可用，**服务端已于当日 14:00 前后补齐登记**。
> 若再遇「未登记字段 xxx」，先重跑一次——很可能只是配置尚未刷新，不要据此下"查不到"的结论。

三键互斥，一次只传一个。返回示例（fapiao_id）：

```json
{"fapiao_id":"<fapiao_id>","found":true,"authorized":true,
 "rows":[{"deal_id":"<业务单号>","bill_no":"<发票号码>",
 "req_bill_serial_num":"<fapiao_id>","biz_serial_num":"<申请单号>",
 "bill_status":"00","bill_status_name":"开票成功","bill_amount":"50.00",
 "channel_id":"WECHAT","tax_payer_no":"<当前企业税号>",
 "enterprise_id":"<企业ID>","bill_error_message":"",
 "billing_date":"2026-09-17 13:44:36","create_time":"2026-09-17 13:44:36"}]}
```

meta 比 `query_table` 多三个键：`found`、`authorized`、`enterprise_id`（用于归属校验的企业 ID），
以及 `enterprise_table`（`base_enterprise`）。查不到时 `found=false`，据此区分"未落库"与"查询失败"。

## 数据集唯一性（探测结果，2026-09-17 复测未变）

```
错误 dataset 名 → 「未登记的数据集：<name>，可用数据集：invoice_deal」
```

即：整个 MCP 侧仍只有 `invoice_deal` 一张表可查（`tax_invoice_main` / `tax_invoice_item` /
`ability_invoice_trade_info` / `fapiao` 均未登记）。**这不影响按 fapiao_id 查询**——
`req_bill_serial_num` 就在 `invoice_deal` 里。

## 可用数据集：invoice_deal（物理表 ability_invoice_deal）

字段清单以服务端为准，可用**故意传错字段名**触发它回吐最新清单：

```
filters:[{"field":"__x__","op":"eq","value":"1"}]
→ 数据集 invoice_deal 不存在字段 __x__，可用字段：<全部字段>
```

2026-09-17 14:05 实测 12 个字段（上午为 9 个，`req_bill_serial_num` / `biz_serial_num` /
`enterprise_id` 为服务端新增登记）：

| 字段 | 说明 | 类型 |
|---|---|---|
| deal_id | 业务单号 | 维度 |
| bill_no | 发票号码 | 维度 |
| **req_bill_serial_num** | **fapiao_id**（商户发票单号） | 维度 |
| **biz_serial_num** | **发票申请单号** | 维度 |
| bill_status | 开票结果 | 维度（**00=开票成功 / 01=开票中 / 02=开票失败**） |
| bill_amount | 开票金额（元） | 度量 |
| channel_id | 渠道 ID | 维度 |
| tax_payer_no | 纳税人识别号 | 维度 |
| **enterprise_id** | **企业 ID**（归属校验用，落 base_enterprise） | 维度 |
| bill_error_message | 失败原因 | 维度 |
| billing_date | 开票日期 | 时间 |
| create_time | 创建时间 | 时间 |

→ `req_bill_serial_num` 可直接用于 `query_table` 的 `filters`，与 `invoice_status` 等价：

```json
{"dataset":"invoice_deal","date_field":"create_time","start_date":"2026-09-17","end_date":"2026-09-17",
 "filters":[{"field":"req_bill_serial_num","op":"eq","value":"<fapiao_id>"}],"limit":3}
```

## query_table 使用要点

- `start_date` / `end_date` **必填**（`YYYY-MM-DD`，东八区），不支持无日期全表查询。
- `filters` 是**数组**，每个元素必须带 `op`：`[{"field":"deal_id","op":"eq","value":"xxx"}]`
  （传对象 → 报 "Expected array, received object"；缺 op → 报 "缺少必填参数 filter.op"）。
- 查询**上限 10000ms**，范围过大直接报「查询超时（上限 10000ms），请缩小时间范围或减少分组维度」——
  按天查（1 天窗口）稳定通过，30 天窗口实测超时。
- 结果附 meta：`row_count`、`subject_isolated`、`elapsed_ms`、`permission_rule`（当前为 noop / shadow 模式，不做权限拦截）。
- **输出上限 20000 字符**：超限时服务端只回「结构化结果过长，已省略」+ meta，**不给 rows**。
  实测约 60 条即触发 → 拉明细把 `limit` 降到 ≤20，或用 `filters` 缩小范围。

## aggregate_query 要点

- `group_by` **必须是数组**：`["bill_status"]`；传字符串报 `Expected array, received string`。
  **最多 3 个维度**（`maxItems: 3`），可交叉统计，如 `["bill_status","channel_id"]` → 开票结果 × 渠道。
- 返回含 `bill_status_name` 中文释义与 `granularity`（默认 `total`；
  可选 `day` / `week` / `month` 做时间趋势）。
- `aggregation`：`count` / `count_distinct` / `sum` / `avg` / `max` / `min`。
  做金额分布时 `sum` 与 `count` 用**同一套 group_by** 各查一次即可拼出「数量 + 金额」两张表。
- 单次约 3~5s（实测 2.9~5.4s），明显慢于 `query_table`，别串行堆太多。

示例（某日状态分布）：

```json
{"dataset":"invoice_deal","start_date":"2026-09-17","end_date":"2026-09-17",
 "aggregation":"count","metric_field":"bill_no","group_by":["bill_status"]}
```

### 「某天开票概况」一次性取全（2026-09-17 实测可用）

用户问「某天开了多少票 / 多少钱 / 什么类型 / 成功失败各多少」时，发这几条即可，可**并发**：

```json
// 1) 数量 × 开票结果 × 渠道（"类型"= bill_status + channel_id，数据集无票种字段）
{"dataset":"invoice_deal","metric_field":"bill_no","aggregation":"count","date_field":"create_time",
 "start_date":"2026-09-16","end_date":"2026-09-16","group_by":["bill_status","channel_id"]}

// 2) 金额汇总（同样 group_by，与 1 拼表）
{"dataset":"invoice_deal","metric_field":"bill_amount","aggregation":"sum","date_field":"create_time",
 "start_date":"2026-09-16","end_date":"2026-09-16","group_by":["bill_status","channel_id"]}

// 3) 票面区间与均值（不分组）
{"dataset":"invoice_deal","metric_field":"bill_amount","aggregation":"avg","date_field":"create_time",
 "start_date":"2026-09-16","end_date":"2026-09-16"}
// 同结构把 aggregation 换成 max / min
```

⚠️ **数据集没有票种（专票/普票）字段**，用户问「开票类型」时按 `bill_status`（结果类型）+
`channel_id`（渠道）两个维度回答，并说明票种需另查发票主表。

### ⚠️ 查「整月 / 多天」：窗口一大就超时，必须逐天扫（2026-09-17 实测）

查 2026-08 整月概况时，**所有大窗口写法全部超时**（`查询超时（上限 10000ms）`）：

| 写法 | 结果 |
|---|---|
| `08-01 ~ 08-31` + `group_by:["bill_status","channel_id"]` | 超时 |
| 拆成 10 天一段（3 段）+ 同样 group_by | 超时 |
| 10 天、**不带** group_by | 超时 |
| 整月 + `granularity:"month"` | 超时 |

原因：单次聚合固定开销约 **1.4~6.3s**（实测 elapsed_ms），天数一多累加即破 10s 上限；
**降维度、改 granularity 都救不了**，只有缩短 `range_days` 有效。

✅ **正确姿势：`start_date == end_date` 逐天查，把多天请求并发发出**（一天一次约 1.5~6s，
并发 8~10 个一批，31 天约 4~5 批即可跑完）。每个指标各发一次：

```
对每一天 d：
  count(bill_no)  group_by:["bill_status","channel_id"]   → 当日笔数 × 结果 × 渠道
  sum(bill_amount)                                        → 当日开票金额
```

然后在本地汇总（**汇总时用脚本算，别心算**；曾把「无失败日」的笔数误填进失败列，
导致成功率算出 55% 的假结果，实际 96.94%）。

报告口径建议：总笔数 / 成功·失败数 / 成功率 / 总金额 / 平均单张 / 有票天数 / 日均 /
峰值日·低谷日，并**单独标注异常日**（见下）。

### 失败票：先按天定位，再看 bill_error_message

全月失败若集中在某一天，先 `query_table` 过滤该天 `bill_status=02` 取样例：

```json
{"dataset":"invoice_deal","date_field":"create_time",
 "start_date":"2026-08-20","end_date":"2026-08-20",
 "filters":[{"field":"bill_status","op":"eq","value":"02"}],"limit":3}
```

实测失败原因样例（2026-08-20 集中 188 笔）：

```
开票预扣授信额度失败，授信额度不足本次开票金额：88.5；剩余可用额度：0.00
```

→ 属**授信额度耗尽**，不是接口/参数问题；失败票 `bill_no` 为空、`billing_date` 为 null。
给结论时把这条原文转达用户，并说明「失败笔数集中在额度耗尽的时段」。

## 观察「开票中 → 成功」的流转（辅助手段，非定位依据）

`bill_status=01`（开票中）只在开票过程中短暂存在，实测**秒级~分钟级**，此时 `bill_no` 为空。

⚠️ 01 消失 ≠ 失败，多数是正常转 00。只有 `bill_status=02` 且 `bill_error_message` 非空才算失败。

⚠️ **不要用时间/金额"猜"是哪一笔**——2026-09-17 曾据此把一笔 fapiao_id 误猜成 13:50 那笔
100 元的票，实测应为 13:44:36 的 50.00 元票。既然 `req_bill_serial_num` 可查，
**一律按单号精确关联**。

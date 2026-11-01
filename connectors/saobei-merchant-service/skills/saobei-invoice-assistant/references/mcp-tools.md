# MCP 接口清单（扫呗商户服务）

> **对商户展示的名称是「扫呗商户服务」**，不得暴露部署标识。
> **参数一律 snake_case**，不是 camelCase。
> 完整工具名 = `mcp__扫呗商户服务__` + 接口名（见下表），接口名全部为 `invoice_` 前缀。
> **本连接器本地部署共 28 个工具，名单以本文「全量工具清单」为准（2026-10-27 实测拉取）。** 除这 28 个名字外，**不存在任何其它工具名**；名字大小写、拼写（含 `Cetegory` 这种原始拼写错误）都必须**照抄**，不得"顺手纠正"。
> ⚠️ 油枪相关工具名的**大小写是固定的**：`invoice_oilGunlist`（`G` 大写、`list` 的 `l` 小写）、`invoice_oilGunLatestPrice`、`invoice_oilGunGoodsPriceList`、`invoice_oilGunAdd`、`invoice_getOilGunDetail`——**照抄，不要"顺手纠正"成 `oilgun_list` 或 `oilGunList`**，写错即工具不存在。

## 全量工具清单（本地部署实测 28 个，★ 唯一权威名单）

> 这张表就是本地「扫呗商户服务」连接器里**全部**的工具名（与 MCP 面板 28/28 一致）。写代码、写文档、调接口时**一律从这里复制**，不要凭记忆拼写。

| # | 接口名（完整工具名 = `mcp__扫呗商户服务__` + 下表值） | 类型 | 用途 | 主流程用 |
|---|---|---|---|---|
| 1 | `invoice_getSwitchByType` | 只读 | 功能开关状态（数电票开通状态） | ✅ |
| 2 | `invoice_getTradeList` | 只读 | 交易订单明细查询 | ✅ |
| 3 | `invoice_getStoreList` | 只读 | 门店列表 | ✅ |
| 4 | `invoice_getGoodsList` | 只读 | 开票商品列表 | ✅ |
| 5 | `invoice_getGoodsDetail` | 只读 | 商品详情（单价、税收类目/编码） | ✅ |
| 6 | `invoice_getGoodsCetegoryList` | 只读 | 商品税收类目列表（原始拼写即 `Cetegory`） | — |
| 7 | `invoice_saveGoods` | **写** | 新增/保存开票商品 | — |
| 8 | `invoice_getOilGunDetail` | 只读 | 油枪详情 | — |
| 9 | `invoice_oilGunlist` | 只读 | 油枪列表 | ✅ |
| 10 | `invoice_oilGunLatestPrice` | 只读 | 油枪最新生效价 | ✅ |
| 11 | `invoice_oilGunGoodsPriceList` | 只读 | 油枪商品价格列表 | — |
| 12 | `invoice_oilGunAdd` | **写** | 新增油枪 | — |
| 13 | `invoice_gunPriceList` | 只读 | 油枪价格列表 | — |
| 14 | `invoice_gunPriceAdd` | **写** | 油枪加价/设价 | — |
| 15 | `invoice_gunPriceDelete` | **写** | 油枪价格删除 | — |
| 16 | `invoice_gunBatchDelete` | **写** | 油枪批量删除 | — |
| 17 | `invoice_blueInvoice` | **写** | 蓝票开具（开票） | ✅ |
| 18 | `invoice_confirmInvoice` | **写** | 确认金额开票（`blueInvoice` 后的出票必需第二步） | ✅ |
| 19 | `invoice_getInvoiceDetail` | 只读 | 发票详情（确认状态） | ✅ |
| 20 | `invoice_getInvoiceList` | 只读 | 发票列表 | ✅ |
| 21 | `invoice_getAllInvoiceStatistics` | 只读 | 开票统计汇总 | — |
| 22 | `invoice_getPreIssueList` | 只读 | 预开票列表 | — |
| 23 | `invoice_getPreIssueDetail` | 只读 | 预开票详情 | — |
| 24 | `invoice_getCrownAuthInfo` | 只读 | 官方电票授权状态（无需入参） | ✅ |
| 25 | `invoice_getGfInvoiceAuthorized` | 只读 | 高灯电票授权状态 | — |
| 26 | `invoice_sendEmail` | **写** | 重发发票邮件 | — |
| 27 | `invoice_terminalList` | 只读 | 收银终端列表 | — |
| 28 | `invoice_queryOperatorList` | 只读 | 操作员列表 | — |

> 「主流程用」= 开票/查票主链路实际会调；标 `—` 的工具**不主动调用**（尤其 7、12、14、15、16、26 是写操作，未经用户明确要求绝不碰）。

## 目录（仅列开具流程实际使用的接口）

> 本表编号只用于下文分节标题（`## 1.` ~ `## 12.`），与上文「全量工具清单」的序号无关。

| # | 接口（完整工具名 = `mcp__扫呗商户服务__` + 下表值） | 类型 | 用途 |
|---|---|---|---|
| 1 | `invoice_getSwitchByType` | 只读 | 功能开关状态（数电票开通状态） |
| 2 | `invoice_getTradeList` | 只读 | 交易订单明细查询 |
| 3 | `invoice_getStoreList` | 只读 | 门店列表 |
| 4 | `invoice_getGoodsList` | 只读 | 开票商品列表 |
| 5 | `invoice_getGoodsDetail` | 只读 | 商品详情（税收类目等） |
| 6 | `invoice_oilGunlist` | 只读 | 油枪列表 |
| 7 | `invoice_oilGunLatestPrice` | 只读 | 油枪最新生效价 |
| 8 | `invoice_blueInvoice` | **写** | 蓝票开具（开票） |
| 9 | `invoice_confirmInvoice` | **写** | 确认金额开票（`blueInvoice` 后的出票必需第二步） |
| 10 | `invoice_getInvoiceDetail` | 只读 | 发票详情（确认状态） |
| 11 | `invoice_getInvoiceList` | 只读 | 发票列表 |
| 12 | `invoice_getCrownAuthInfo` | 只读 | 官方电票授权状态（无需入参） |

> 其余工具（`invoice_getGoodsCetegoryList`、`invoice_saveGoods`、`invoice_getOilGunDetail`、`invoice_oilGunAdd`、`invoice_oilGunGoodsPriceList`、`invoice_gunPriceList`、`invoice_gunPriceAdd`、`invoice_gunPriceDelete`、`invoice_gunBatchDelete`、`invoice_getAllInvoiceStatistics`、`invoice_getPreIssueList`、`invoice_getPreIssueDetail`、`invoice_getGfInvoiceAuthorized`、`invoice_sendEmail`、`invoice_terminalList`、`invoice_queryOperatorList`）已在上面「全量工具清单」中列全，**开具主流程不使用，不要顺手调用**；其中写操作（`invoice_saveGoods`、`invoice_oilGunAdd`、`invoice_gunPriceAdd`、`invoice_gunPriceDelete`、`invoice_gunBatchDelete`、`invoice_sendEmail`）未经用户明确要求**绝对不可调用**。

---

## 1. `invoice_getSwitchByType` — 功能开关状态

**用途**：开票流程的第一道门。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `switch_types` | **整数数组** | 是 | 开关类型。`[1]` = 数电发票 |

### 返回

```json
{ "return_code": "01", "result_code": "01", "return_msg": "成功",
  "trace_no": "…", "merchant_no": "…",
  "invoice_switch": "1", "cashier_switch": "…", "qrcode_expire": "…" }
```

> 统一包裹：`return_code` `01` 成功 / `02` 通信失败；`result_code` `01` 业务成功 / `02` 业务失败。**两者都要看**，只看通信码会把业务失败当成功。

| 字段 | 含义 |
|---|---|
| `invoice_switch` | `"1"` 已开通数电票；`"0"` 未开通 |
| `cashier_switch` / `pos_ticket_switch` / `order_invoice_switch` | 其余开关，按 `switch_types` 请求的类型返回 |
| `qrcode_expire` | 发票二维码过期时间（对应 `switch_types=8`） |

### 陷阱

- **`switch_types` 必须传整数数组** `[1]`，不能传字符串 `"1"`、不能传嵌套数组 `[[1]]`——否则报 `must be array`。
- **`invoice_switch = 0` 必须终止开票流程**，不得继续收集抬头邮箱、不得调 `invoice_blueInvoice`。
- `invoice_switch = 1` 时**静默通过**，不要对用户说"已开通"。

---

## 2. `invoice_getTradeList` — 交易订单明细

**用途**：「最新一笔订单」的唯一可靠来源。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `search_type` | **int** | **是** | 查询类型：`0` = 自然日（按 `trade_date` 整天）、`1` = 自定义/点对点（按 `begin_time`~`end_time`）。**必填且必须是整数**，早期文档写的字符串 `"1"` 已不适用 |
| `trade_date` | string | 否 | `search_type=0` 时使用，`yyyy-MM-dd`，不传默认当天 |
| `begin_time` | string | `search_type=1` 时必填 | 起始时间，如 `2026-10-13 00:00:00` |
| `end_time` | string | `search_type=1` 时必填 | 结束时间，如 `2026-10-13 23:59:59` |
| `store_id` | string | 否 | 门店 ID，多个用逗号分隔；`"0"` 或 `"-1"` 表示全部门店（查全部门店走这里，不是「不传」） |
| `start_id` | string | 否 | 分页游标，上一页最后一条记录的 `id` |
| `search_start_time` | string | 否 | 自定义时段滚动查询时的起始交易时间 |

### 返回

```json
{
  "return_code": "01", "result_code": "01", "return_msg": "成功",
  "trace_no": "…", "merchant_no": "…",
  "trade_list": [
    { "id": "…", "out_trade_no": "2026101312345678", "total_fee": "8600",
      "pay_status_code": "1", "store_name": "示例门店" }
  ],
  "is_last_page": "1"
}
```

| 字段 | 含义 | 备注 |
|---|---|---|
| `id` | 内部记录 ID | **用作 `start_id` 分页游标** |
| `out_trade_no` | 商户订单号 | **开票必须用这个真实值** |
| `channel_trade_no` | 第三方渠道订单号 | 展示为「渠道订单号」，**不开票用它** |
| `pay_type` / `pay_type_msg` | 支付方式 | 展示「微信 / 支付宝 / 云闪付」 |
| `total_fee` | 交易金额 | **单位：分**，展示需 ÷100 |
| `pay_status_code` | 交易状态 | `"1"` 支付成功；`2` 失败 `3` 支付中 `4` 已撤销 `5` 退款成功 `8` 退款中 —— 非 `1` 不可开票 |
| 交易时间 | 判断"最新"的依据 | 以实际返回的时间字段为准（历史版本为 `add_time`；当前 schema 列有 `settle_time`、`refund_time`），**照返回原值用，不推断** |
| `is_last_page` | 是否最后一页 | `1` 表示无更多 |

> `trade_list` 当前 schema 为 `list_object`（数组）；若某次返回的是 **JSON 字符串**，先 `json.loads` / `JSON.parse` 再处理。

### ★ 陷阱清单

| 陷阱 | 表现 | 正确做法 |
|---|---|---|
| **`trade_list` 类型** | 可能是 JSON 字符串也可能是数组 | 先判类型，字符串先 `JSON.parse` / `json.loads` |
| **`search_type` 是整数** | 传 `"1"` 报参数校验错 | 传 `1` |
| **金额单位是分** | `8600` 被当成 8600 元 | 展示时 ÷100，写 `¥86.00` |
| **`total_fee` 可能为负** | 红冲/退款交易 | 展示时取绝对值并说明是退款/红冲 |
| **`start_id` 是十六进制串** | 直接传数字报错 | 原样回传字符串 |
| **不传时间会默认当天** | 查"最新一笔"只拿到今天 | **始终显式传 `search_type=1` + `begin_time`/`end_time`** |
| **时间跨度上限 6 个月** | 传更早的范围返回空 | 先算出合法 `begin_time` |
| **不含完整商品明细** | 只有订单号和金额 | 需另查商品，**不得推断** |

---

## 3. `invoice_getStoreList` — 门店列表

**用途**：把用户说的门店名匹配成 `store_id`。

### 入参（均可选）

| 参数 | 类型 | 说明 |
|---|---|---|
| `store_name` | string | 门店名称，支持模糊搜索 |
| `store_id` | string | 直接按门店 ID 查 |

返回 `store_list`（数组；若为 JSON 字符串先解析），每条含 `store_id`、`store_name`、门店地址、门店状态。

**陷阱**：用户未指定门店时**不要调用本接口**；匹配到多个才追问，匹配到一个直接用。

---

## 4. `invoice_getGoodsList` — 开票商品列表

**用途**：按商品名查开票所需的商品 ID、税率，并取「默认商品」。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `goods_name` | string | 否 | 商品名关键词，模糊搜索 |
| `query_type` | int | 否 | `1` = 正常商品、`2` = 适配油枪商品（成品油场景用 `2`） |
| `store_id` | int | 否 | 门店 ID |
| `page_num` | int | 否 | 页码，默认 `1`（**旧参数名 `page` 已废弃**） |
| `page_size` | int | 否 | 每页条数，默认 `100` |

### 返回

`goods_list`（数组；若为 JSON 字符串先解析）每条含：

| 字段 | 含义 | 备注 |
|---|---|---|
| `goods_id` | 商品 ID | 开票必传 |
| `goods_name` | 商品名 | |
| `tax_rate` | 税率 | 如 `"0.01"` → 展示 `1%` |
| `unit` | 单位 | 如「个」「升」 |
| `is_default` | 是否默认商品 | `1` 即 3.4 所说的「接口默认商品」 |

> **单价与税收类目不在本接口返回**：需要单价/税收类目时用 `invoice_getGoodsDetail`（返回 `unit_price`（元）、`goods_category_id`、`goods_category_name`、`goods_category_code`）。

### ★ 陷阱

- **`goods_list` 可能是 JSON 字符串**，先判类型再解析。
- `tax_rate` 是小数（`0.01`）不是百分数（`1`）。
- 税收类目取不到时**填 `-`**，不要编造。
- **不评价单价是否异常**，接口返回什么就展示什么。

---

## 5. `invoice_getGoodsDetail` — 商品详情

**用途**：补取 `unit_price`（元）、`goods_category_name`（税收类目）、`goods_category_code`（税收编码）。入参 `goods_id`（必填，`long`）、`store_id`（可选）。

---

## 6–7. 成品油行业：`invoice_oilGunlist` / `invoice_oilGunLatestPrice`

| 接口 | 入参 | 用途 | 关键返回 |
|---|---|---|---|
| `invoice_oilGunlist` | `store_id`(int)、`data_status`(int，`1` 启用/`0` 禁用) | 油枪列表 | `oil_gun_list`：`id`、`gun_no`、`gun_name`、`invoice_goods_id`、`unit`、`current_price`（元/升） |
| `invoice_oilGunLatestPrice` | `oil_gun_id`(long) / `gun_no`(string) 二选一、`store_id`(int) | 油枪**最新生效价** | `latest_price`（**分**）、`unit`、`effective_time` |

**陷阱**：油枪信息**不得编造**，必须来自这两个接口；价格必须用**最新生效价**，不用历史价；开票时**不得遗漏成品油专用字段**；油枪列表里的 `current_price` 是**元**、`latest_price` 是**分**，别混。

---

## 8. `invoice_blueInvoice` — 蓝票开具（★ 写操作）

**用途**：真实开票。**调用即产生法律效力。**

### 必填项（实测确认）

| 参数 | 类型 | 说明 |
|---|---|---|
| `title_type` | int | 抬头类型。`1` = 个人，`2` = 企业 |
| `purchase_name` | string | 购方名称（发票抬头） |
| `goods_list` | string | 商品信息，**JSON 字符串**（格式见下） |
| `email` | string | 接收邮箱 |

### 可选项

| 参数 | 类型 | 说明 |
|---|---|---|
| `out_trade_no` | string | 扫呗订单号。**订单开票时传这个** |
| `ticket_type` | int | 发票类型：`1` = 全电专票，`2` = 全电普票 |
| `invoice_type` | int | 电子发票类型：`3` = 高灯数电票，`4` = 官方电票(微信+支付宝) |
| `ability_code` | string | 能力类型编码：`BASE_ABILITY`（通用）/ `REAL_ESTATE_ABILITY`（房地产）/ `REFINED_OIL_ABILITY`（成品油） |
| `purchase_no` | string | 购方税号（企业抬头） |
| `purchase_address` | string | 购方地址 |
| `purchase_phone` | string | 购方电话 |
| `purchase_cardbank` | string | 购方开户行 |
| `purchase_cardnum` | string | 购方银行卡号 |
| `remark` | string | 备注 |
| `store_id` | int | 门店 ID |

> ★ **纠错记录**：早期文档称 `invoice_type` "固定使用"是**错误**的。实测必填项只有
> `title_type` / `purchase_name` / `goods_list` / `email` **四项**，其余为可选。

### ★ `goods_list` 实测格式（关键，务必照抄）

`goods_list` 是 **JSON 字符串**（不是数组、不是订单号字符串）。每项**必须同时含商品 ID、数量、单价**，否则接口报「开票商品列表中商品id、商品数量、商品单价不能为空」。

**可用样例（实测通过）**：

```json
[{"goods_id":"2083104770139635713","goods_name":"餐饮","goods_count":1,"goods_num":1,"price":10.00,"unit_price":10.00,"tax_rate":"0.01"}]
```

**⚠️ 实测补充（本次翻车点）**：部分环境仅用上表字段会被拒「商品id、商品数量、商品单价不能为空」，把别名补齐即可通过。稳妥做法是一次性带上多别名：

```json
[{"id":"2083104770139635713","goods_id":"2083104770139635713","goods_code":"3070401000000000000","goods_name":"餐饮","goods_count":1,"goods_num":1,"num":1,"count":1,"price":3.50,"unit_price":3.50,"unit":"个","tax_rate":"0.01","tax_category":"3070401000000000000"}]
```

其中 `goods_code`/`tax_category` 取 `getGoodsList` 返回的 `tax_code`（税收商品编码，如餐饮服务 `3070401000000000000`）。`goods_list` 仍是 **JSON 字符串**。

字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `goods_id` | ✅ | 商品 ID，取自 `invoice_getGoodsList` |
| `goods_count` / `goods_num` | ✅ | 数量（两个别名**都带上**最稳） |
| `price` / `unit_price` | ✅ | 单价（两个别名都带上） |
| `goods_name` | 建议 | 商品名 |
| `tax_rate` | 建议 | 税率小数，如 `"0.01"` |

**⚠️ 单价单位务必确认**：接口对 `price` 的处理存在歧义——实测传 `"1000"`（分）会被当作元处理，实际生成 `total_fee=100000` 分 = **¥1000.00**，而订单实际只有 ¥10.00。**开票前必须用 `calc_amount.py` 反算：`订单金额(元) × 100 == price` 对不上就不要提交。**

### ★ 调用三前提（缺一不可）

1. **数电票已开通**（`invoice_switch = 1`）
2. **所有参数来自真实数据或用户明确填写**，无一处推断
3. **用户已给出明确确认指令**（"确认""无误""开票""可以"）

### ★ 提交后必做：确认金额开票补确认（见 9）

`blueInvoice` 建单后**不等于出票完成**。实测该商户环境下 `blueInvoice` 只创建开票单，详情长期 `issue_status=0`（开票中）、票号/代码不生成、`error_msg` 为空。必须再调 `invoice_confirmInvoice`（见下节）补确认，才会真正出票。**只做 `blueInvoice` 就收工 = 卡单。**

### 陷阱

- **绝不接受缺参数时"先试试"**——写操作试错会产生错票。
- 接口返回成功 ≠ 发票已开好，**必须再调 `invoice_getInvoiceDetail` 确认**。
- 返回 `issue_status = 0`（开票中）时，**不是失败**，按 4.4 / 下节用 `invoice_confirmInvoice` 补确认出票。
- 提交时报「资源包已过期」等资源包/服务包类错误时，**不作为对商户的失败归因**：实测该报错下开票单仍正常建立并最终出票成功。先查详情看 `issue_status` / `error_msg` 再定性。

---

## 9. `invoice_confirmInvoice` — 确认金额开票（★ 写操作）

**用途**：`blueInvoice` 后若需以**明确金额**确认开票（尤其订单金额与 `goods_list` 单价×数量可能不一致时），用本接口提交确认金额。**本环境里它是出票的必需第二步**——不做这步，开票单会一直卡在「开票中」。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `invoice_id` | int | ✅ | `blueInvoice` 返回的发票 ID |
| `total_fee` | int | ✅ | 开票总金额，**单位：分** |
| `goods_list` | string | ✅ | 开票商品列表，JSON 字符串，格式同 `blueInvoice` |
| `ability_code` | string | ❌ | 能力类型编码（成品油等特殊场景） |
| `remark` | string | ❌ | 备注 |
| `store_id` | int | ❌ | 门店 ID |

### 实测样例（本次出票成功用的组合）

```json
{
  "invoice_id": 565796,
  "total_fee": 350,
  "ability_code": "BASE_ABILITY",
  "goods_list": "[{\"goods_id\":\"2083104770139635713\",\"goods_code\":\"3070401000000000000\",\"goods_name\":\"餐饮\",\"goods_count\":1,\"goods_num\":1,\"num\":1,\"count\":1,\"price\":3.50,\"unit_price\":3.50,\"unit\":\"个\",\"tax_rate\":\"0.01\",\"tax_category\":\"3070401000000000000\"}]"
}
```

调用成功返回 `return_code=01, result_code=01`，随后 `invoice_getInvoiceDetail` 的 `issue_status` 由 `0`（开票中）变为 `1`（开票成功），`ticket_code`（发票代码）与 `invoice_url`（PDF）随之生成。**⛔ 该接口也是写操作，一次不成就先查详情，不盲目重发**（重复确认可能产生重复开票）。

### 陷阱

- `total_fee` **单位是分**（1000 = ¥10.00）。
- `goods_list` 字段要求与 `blueInvoice` 一致：**商品 ID、数量、单价三项齐全**，否则报「开票商品查询失败」。
- 只传 `goods_id` + `goods_code` + `goods_count` + `price` + `tax_category` 等组合**仍会失败**；请照 `blueInvoice` 的样例格式同时给出 `goods_count`/`goods_num` 与 `price`/`unit_price` 别名。

---

## 10. `invoice_getInvoiceDetail` — 发票详情

**用途**：**确认开票结果的唯一依据。** 入参 `invoice_id`（int，必填）、`store_id`（int，可选）。

### 返回关键字段

| 字段 | 含义 |
|---|---|
| `invoice_id` | 开票记录 ID |
| `ticket_sn` | 发票号码 |
| `invoice_serial_no` | 发票流水号 |
| `total_fee` | 开票金额（**分**） |
| `tax_fee` | 总税额（分） |
| `invoice_type` | 发票类型：`0` = 蓝票，`1` = 红票 |
| `issue_status` | 开票状态：`0` = 开票中，`1` = 开票成功 |
| `red_issue_status` | 红票开具状态：`0` = 未开具，`1` = 已开具 |
| `invoice_scene` | 开票场景：`1` = 自定义金额开票，`2` = 订单金额开票，`3` = 自助开票 |
| `error_msg` | 开票失败原因 |
| `invoice_url` / `invoice_qrcode_url` | 发票下载链接 / 开票链接 |
| `receive_email` | 接收邮箱 |

### 状态枚举 → 商户侧术语映射（★ 必须转换）

`getInvoiceList` 与 `getInvoiceDetail` 的 `issue_status` 枚举**不同**，按各自接口取值映射：

| 接口 | 返回值 | 对用户说 |
|---|---|---|
| `getInvoiceDetail` | `0` 开票中 | 开票中 |
| `getInvoiceDetail` | `1` 开票成功 | **已开票** |
| `getInvoiceList` | `1` 开票成功 | **已开票** |
| `getInvoiceList` | `2` 开票中 | 开票中 |
| `getInvoiceList` | `3` 开票失败 | 开票失败 |
| `getInvoiceList` | `4` 已冲红 | **已红冲** |
| `getInvoiceList` | `5` 冲红中 | **红冲中** |
| `getInvoiceList` | `6` 冲红失败 | **红冲失败** |

> 服务端用「冲红」，商户侧说「**红冲**」。**对用户一律用"红冲"**。

**未确认成功前，不得对用户说"发票已开好了"。**

---

## 11. `invoice_getInvoiceList` — 发票列表

查历史发票，用于开票状态回查场景。入参全部可选：`begin_time`/`end_time`、`issue_date`、
`store_id`、`terminal_id`、`operator_id`、`issue_status`（1-开票成功 / 2-开票中 / 3-开票失败 / 4-已冲红 / 5-冲红中 / 6-冲红失败）、
`invoice_scene`（0-全部 / 1-自定义 / 2-订单 / 3-物料码 / 4-扫码）、`previous_id`（分页，上一页最后一条 id）。

返回 `invoice_list` 每条含：`invoice_id`、`purchase_name`、`ticket_code`、`ticket_sn`、`ticket_time`、
`issue_status`、`total_fee`、`invoice_url`、`invoice_qrcode_url`、`receive_email`。

**陷阱**：金额字段 `total_fee` **单位是分**；**冲红记录金额可能为负数**，统计有效开票金额须 `|blue| - |red|`；本接口 `invoice_id` 为字符串。

---

## 12. `invoice_getCrownAuthInfo` — 官方电票授权状态

**用途**：开票失败（提示资源包/服务包/额度异常）时，核实微信、支付宝官方电票授权状态。**无入参**，直接调用。

| 返回字段 | 含义 |
|---|---|
| `wx_authorized_status` | 微信电子发票授权：`0` 未授权 / `1` 已授权 / `2` 授权失败 / `3` 授权中 |
| `ali_authorized_status` | 支付宝电子发票授权：同上枚举 |
| `ability_list` | 产品能力授权列表：`ability_code`（`BASE_ABILITY` / `REAL_ESTATE_ABILITY` / `REFINED_OIL_ABILITY`）、`ability_name`、`authorized_status`、`authorized_type`（`1` 微信 / `2` 支付宝） |

**陷阱**：调用本接口是为了**核实**，不是为了**归因**。必须结合 `invoice_getSwitchByType` 一起看，**不未经确认直接归因**。

---

## 错误码速查（实测）

| 报错原文 | 含义 | 处置 |
|---|---|---|
| `must be array` | `switch_types` 类型错 | 传整数数组 `[1]`，**不能传字符串** `"1"`、不能传嵌套数组 `[[1]]`；接口偶发报同一错时可重试同一参数 |
| `开票商品不能为空` | `goods_list` 为空或不是含 id 的商品数组 | 按样例格式补 `goods_id` + 数量 + 单价 |
| `确认金额开票异常` | `goods_list` 传成了订单号字符串 | 改为商品 JSON 数组字符串 |
| `开票商品列表中商品id、商品数量、商品单价不能为空` | 商品项缺 id/数量/单价任一 | 三项齐全，别名同时给（`goods_count`/`goods_num`、`price`/`unit_price`）；实测补 `id`/`goods_code`/`tax_category` 等别名更稳 |
| `开票商品查询失败` | `confirmInvoice` 的 `goods_list` 未被识别 | 照 `blueInvoice` 样例给全字段 |
| `资源包已过期, log_id=xxx` | 提交时报的资源包/服务包提示 | **⚠️ 实测不可直接当作开票失败原因播报**：该报错下开票单仍建立、且经 `confirmInvoice` 补确认后出票成功。正确做法：先查 `invoice_getInvoiceDetail`，`issue_status=0` 且无 `error_msg` → 走 `confirmInvoice` 补确认出票；只有详情 `error_msg` 有值/开票失败才按本行原处置（核实授权 + 开关后告知续费状态） |
| 长时间 `issue_status=0`（开票中）不推进 | `blueInvoice` 建单后未做确认 | 调 `invoice_confirmInvoice` 补确认（invoice_id、total_fee、goods_list）；**禁止重发 `blueInvoice`** |
| 授权失效 / 未授权 | 连接器未授权 | 只阻断"问扫呗"部分，其余照常交付（见 SKILL.md 1.2） |

---

## 通用规则

1. **JSON 字符串字段一律先解析**：`trade_list`、`goods_list`、`store_list`、`oil_gun_list`、（`blueInvoice`/`confirmInvoice` 的）`goods_list`。当前 schema 多为数组，**先判类型再处理**。
2. **金额单位一律是分**（`invoice_getGoodsDetail` 的 `unit_price`、`invoice_oilGunlist` 的 `current_price` 例外，为元）：展示前 ÷100，保留两位小数。
3. **参数一律 snake_case**。
4. **只读接口可放心重试**；`invoice_blueInvoice` / `invoice_confirmInvoice` 是写操作，**失败不可盲目重发**，须先查详情确认是否已成功。
5. **接口没返回的，就是没有**——不推断、不补全、不编造。

# MCP 接口契约（真实工具签名 + 实测记录）

> 基于「扫呗商户服务」连接器（本地部署，工具前缀 `mcp__扫呗商户服务__`，接口统一 `invoice_` 前缀，共 28 个工具）的实际工具签名与实测返回。
> 所有字段名与枚举均来自真实响应，**不是推测**。

## 零、调用铁律

1. **连接器展示名是「扫呗商户服务」**，工具前缀同为 `mcp__扫呗商户服务__`，
   接口名一律 `invoice_` 前缀；
   **面向商户的话术只能用「扫呗商户服务」**，不得暴露技术标识。
2. **本技能只调用只读接口。** 严禁调用 `blueInvoice`（开具蓝票）、`confirmInvoice`（确认金额开票）。
3. `store_list` 与 `invoice_list` 返回的是 **JSON 字符串**，需先解析再处理。

---

## 一、invoice_getAllInvoiceStatistics（开票汇总）

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query_type` | integer | ✅ | 1 今日 / 2 昨日 / 3 本周 / 4 本月 |
| `store_id` | integer | 否 | 门店ID，不传则查整个商户 |

### 实测返回（2026-10-14，今日无数据）

```json
{
  "return_code": "01",
  "result_code": "01",
  "return_msg": "操作成功",
  "merchant_no": "816208220000001",
  "total_count": 0,
  "total_amount": 0,
  "normal_amount": 0,
  "normal_count": 0,
  "refund_amount": 0,
  "refund_count": 0
}
```

### ⚠️ `total_amount` 的口径是「净值」，不是「蓝票+红票总额」

实测（2026-10-21，本月）：`normal_amount = 47929`、`refund_amount = -47921`、`total_amount = 8`。

47929 + (−47921) = 8，即 **`total_amount` = `normal_amount` + `refund_amount`（带符号求和，即净值）**，
而不是 |蓝票| + |红票| = 95850。

因此商户侧展示口径必须明确区分：

| 展示项 | 计算方式 |
|---|---|
| 开票金额 | \|蓝票金额\| + \|红票金额\|（各张金额绝对值累加） |
| 有效开票金额 | \|蓝票金额\| − \|红票金额\| |

⚠️ 若直接展示统计接口的 `total_amount`（=净值），会与「开票金额」标签矛盾，且在红冲多时数值极小易被误读。以蓝票+红票绝对值累加为准。

### 返回字段

| 字段 | 说明 |
|---|---|
| `return_code` | `"01"` 表示成功，非 01 视为异常 |
| `total_count` | 开票总数量 |
| `total_amount` | 开票总金额（**净值口径**，= normal + refund） |
| `normal_count` / `normal_amount` | 蓝票（正常开具）数量 / 金额 |
| `refund_count` / `refund_amount` | 红票（红冲）数量 / 金额 |

### ⚠️ 金额单位：分（必须先换算成元再展示）

所有金额字段（`total_amount` / `normal_amount` / `refund_amount` / `total_fee` / `tax_fee`）**单位都是分**，不是元。

实测印证（2026-10-21）：
- 本月汇总返回 `normal_amount = 47929`、`refund_amount = -47921`、`total_amount = 8` → 对应 ¥479.29、¥-479.21、¥0.08。
- 明细中 `total_fee = 600` 表示 ¥6.00，`total_fee = 1` 表示 ¥0.01。

**展示前必须除以 100**，并用脚本换算，禁止心算。推荐写法：

```python
def yuan(cents):
    return format(cents / 100, ".2f")
```

⚠️ 漏掉这一步会让所有金额放大 100 倍（例如把 ¥6.00 显示成 ¥600.00）。

### ⚠️ 金额符号陷阱（重要）

`refund_amount` 正负号**不保证一致**。实测明细接口中已红冲记录的 `total_fee` 为负数（`-1`、`-2`）。

**因此派生计算一律取绝对值：**

```
有效开票金额 = |normal_amount| - |refund_amount|
```

若直接 `normal_amount - refund_amount`，当红票为负数时会变成加法，金额翻倍。**必须用脚本算，禁止心算。**

---

## 二、invoice_getInvoiceList（发票明细）

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `begin_time` | string | 否 | 开票起始时间 `yyyy-MM-dd HH:mm:ss` |
| `end_time` | string | 否 | 开票截止时间 `yyyy-MM-dd HH:mm:ss` |
| `issue_date` | string | 否 | 开票日期 `yyyy-MM-dd` |
| `store_id` | string | 否 | 门店ID |
| `terminal_id` | string | 否 | 终端ID |
| `operator_id` | string | 否 | 操作员ID |
| `issue_status` | integer | 否 | 1 开票成功 / 2 开票中 / 3 开票失败 / 4 已冲红 / 5 冲红中 / 6 冲红失败 |
| `invoice_scene` | integer | 否 | 0 全部 / 1 自定义 / 2 订单 / 3 物料码 / 4 扫码 |
| `previous_id` | integer | 否 | 上一页最后一条记录ID，分页用 |

### 实测返回（2026-09-01～10-14，节选）

```json
{
  "return_code": "01",
  "total_count": null,
  "total_amount": null,
  "is_last_page": 0,
  "invoice_list": "[{\"invoice_id\":6382,\"invoice_qrcode_url\":\"\",\"invoice_scene\":1,\"invoice_serial_no\":\"166340698720260923153157064\",\"invoice_type\":1,\"invoice_url\":\"https://...pdf\",\"issue_status\":4,\"official_sub_type\":0,\"purchase_name\":\"没有存通道\",\"receive_email\":\"11@qq.com\",\"red_issue_status\":1,\"ticket_code\":\"\",\"ticket_sn\":\"26427200000007146738\",\"ticket_time\":\"2026-09-23 15:31:58\",\"total_fee\":-1}]"
}
```

### 返回字段

| 字段 | 说明 |
|---|---|
| `is_last_page` | 是否最后一页，`0` 否 / `1` 是 |
| `invoice_list` | **JSON 字符串**，需解析 |
| `invoice_id` | 开票记录ID，详情查询与分页游标依据 |
| `ticket_sn` | 发票号码（展示用，完整不省略） |
| `invoice_serial_no` | 发票流水号 |
| `ticket_code` | 发票代码（数电票常为空） |
| `invoice_url` | PDF 地址，**可能为空字符串** |
| `invoice_qrcode_url` | 发票二维码地址 |
| `total_fee` | 发票金额，**单位为分**，已红冲记录为负数 |
| `issue_status` | 开票状态（1～6） |
| `invoice_type` | 发票类型：1 红票 / 0 蓝票 |
| `invoice_scene` | 开票来源（0～4） |
| `red_issue_status` | 红冲状态：0 未红冲 / 1 已红冲 |
| `purchase_name` | 购方名称 |
| `receive_email` | 接收邮箱 |
| `ticket_time` | 开票时间 |
| `official_sub_type` | 官方子类型 |

### 枚举陷阱

| 字段 | 易混淆点 |
|---|---|
| `issue_status` | 是**开票状态**，不是发票类型，**不得**当作蓝票/红票 |
| `invoice_type` | 是**发票类型**（0 蓝 / 1 红），与 `issue_status` 独立 |
| `invoice_scene` | 是**开票来源**，不是发票类型 |
| `red_issue_status` | 是**红冲状态**，与 `issue_status` 独立 |

实测样本印证：`issue_status=4`（已冲红）且 `invoice_type=1`（红票）同时成立——两者是不同维度。

### ⚠️ 接口枚举用「冲红」，商户侧必须用「红冲」

接口 `issue_status` 的原始枚举文案是「已冲红 / 冲红中 / 冲红失败」，商户侧术语要求统一用「红冲」。**展示时必须转换，不可直接透传接口文案**。
转换对照表见 `SKILL.md` 第五节，此处不重复。

### 分页

`is_last_page = 0` 时，取 `invoice_list` 最后一条的 `invoice_id` 作为下次的 `previous_id`。**按 `invoice_id` 去重**，避免重复展示同一张发票。

---

## 三、invoice_getInvoiceDetail（发票详情）

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `invoice_id` | integer | ✅ | 开票记录ID，来自列表接口 |
| `store_id` | integer | 否 | 门店ID |

**仅在用户明确要求查看某张发票详情时调用。** 汇总完成后不主动调用。

---

## 四、invoice_getStoreList（门店列表）

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `store_name` | string | 否 | 门店名称，支持模糊搜索 |
| `store_id` | string | 否 | 门店ID |

> ⚠️ 查询时传字符串 `store_id`，但统计接口的 `store_id` 是 **integer**，转换时注意类型。

### 实测返回（节选）

```json
{
  "return_code": "01",
  "store_list": "[{\"store_id\":1009438,\"store_name\":\"wycs\",\"store_code\":\"20998694\",\"store_addre\":\"湖北省武汉市...\",\"createtime\":\"2026-09-18 13:51:33\"}]"
}
```

字段：`store_id` / `store_name` / `store_code` / `store_addre`（**注意是 `addre` 不是 `address`**）/ `store_person` / `store_phone` / `store_email` / `createtime`。

### 调用约束

- **用户未指定门店时不调用本接口**，直接查整个商户。
- 门店名称必须使用接口返回的真实名称，不使用占位符。
- 匹配不到时如实说明，不擅自改用其他门店。

---

## 五、invoice_getSwitchByType（开关状态）★ 开通状态的真实依据

### 参数

`switch_types` 为整数数组，可传多个。`[1]` 即数电发票开关。

其他开关：2 收银员开票权限 / 3 开具专用发票 / 4 扫码点餐支持开票 / 5 POS 支持扫码开票 / 6 智盒支持开票 / 7 微信支付宝官方入口 / 8 二维码超时时间 / 9 扫呗订单开票 / 10 支付即开票 / 11 是否允许换开 / 12 用户开票配置。

### 实测返回（`switch_types: [1]`）

```json
{
  "return_code": "01",
  "invoice_switch": 1,
  "cashier_switch": null,
  "special_invoice_switch": null,
  "pos_bind_status": 1,
  "box_bind_status": 1,
  "official_entrance_status": null
}
```

### 判读

| `invoice_switch` | 含义 | 处置 |
|---|---|---|
| `1` | 已开通数电票 | 正常查询 |
| `0` | **未开通** | 「当前商户还没有开通数电票功能哦～」 |
| 调用失败 | **未知** | 走降级交付，**不得断言未开通** |

⚠️ 返回中大量字段为 `null`（未查询对应开关），属正常，**不可把 `null` 当作 0**。

---

## 六、invoice_getCrownAuthInfo（电票授权状态）

无参数。

⚠️ 这是**微信/支付宝电票授权**状态，与数电票开通状态是**两回事**。

- **不得**用它判断数电票是否开通。
- 仅在用户主动询问授权状态时调用。

---

## 七、禁止调用的写接口

| 工具 | 作用 | 状态 |
|---|---|---|
| `invoice_blueInvoice` | 发票开具（蓝票） | ❌ 严禁调用 |
| `invoice_confirmInvoice` | 确认金额开票 | ❌ 严禁调用 |

其余接口（如 `invoice_getGfInvoiceAuthorized`、`invoice_getTradeList`、`invoice_oilGunlist`、油枪增删改价、商品维护、预开票等）同样不在本技能范围内，一律不调用。

---

## 八、异常分流

| 场景 | 现象 | 处置 |
|---|---|---|
| 授权失效 | 返回未授权 | 走降级交付，**不得**说成未开通数电票 |
| 工具检索不到 | 无匹配 | 连接器未加载/未启用，走降级交付 |
| `invoice_switch = 0` | 明确未开通 | 「当前商户还没有开通数电票功能哦～」 |
| `return_code ≠ "01"` | 业务异常 | 走降级交付，不暴露技术信息 |
| `is_last_page = 0` | 还有下一页 | 用 `previous_id` 续查并去重 |
| `invoice_url` 为空 | 无 PDF | 如实说明该发票暂无 PDF |
| 门店匹配不到 | 无结果 | 如实说明并列出可选门店 |

**核心原则：接口异常 ≠ 没有开票。** 前者是数据未知，后者是事实结论，绝不可混淆。

---

## invoice_sendEmail — 电子发票发送到邮箱（2026-10-21 实测）

**工具名**：`mcp__扫呗商户服务__invoice_sendEmail`

**功能**：把某张电子发票发送到指定邮箱。**发送发票邮件的唯一正道**，
发送只走本接口，不支持换发件箱。

### 请求参数（inputSchema）

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `email_type` | 是 | integer | 邮件类型，固定 `1`（电子发票） |
| `email_address` | 是 | string | 收件邮箱地址 |
| `content` | 是 | string | **发票流水号**（`invoice_serial_no`） |

⚠️ `content` 收的是发票流水号，**不是** `ticket_sn` 发票号码，也不是 `invoice_id`。
拿不到流水号时先调 `invoice_getInvoiceDetail` 换取 `invoice_serial_no`。

### 返回字段

| 字段 | 说明 |
|---|---|
| `return_code` | `01` 成功 |
| `result_code` | `01` 成功 |
| `return_msg` | 「邮件发送成功」 |
| `trace_no` | 凭证号（展示给用户，32 位 hex） |
| `merchant_no` | 商户号 |

### 实测样本（2026-10-21）

请求：`email_type=1`、`email_address=lxy@example.com`、
`content=309106260020261021162556000001`

返回：`return_code=01`、`result_code=01`、`return_msg=邮件发送成功`、
`trace_no=f52973cad07a4643b3eccd1fbd4afd87`、`merchant_no=852105813000941`

### 陷阱

- 「网关调用失败」多为**偶发抖动**，重试即可；连续多次失败才降级引导。
- 收件邮箱**不限域名**（QQ / 163 / outlook / gmail / 企业邮箱均可）。

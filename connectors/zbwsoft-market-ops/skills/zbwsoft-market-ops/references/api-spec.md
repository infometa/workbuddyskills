# 云启SAAS MCP 工具接口规范

> 本文件由 Skill 引用，供模型理解字段类型、枚举与错误码。实际以 MCP Server 的 JSON Schema 为准。

## 通用约定

- 所有日期使用 `YYYY-MM-DD` 字符串，时区为租户所在时区（默认 Asia/Shanghai）。
- 所有金额单位为元（`number`，两位小数），数量字段带单位后缀说明。
- 所有工具的服务端单次响应上限 30 秒；超时返回 `UPSTREAM_TIMEOUT`。
- 租户上下文（`softid` / `oper_id` / 有权限的 `branch_no` 列表）由服务端从令牌解析，
  **工具不接收任何租户标识参数**。

---

## 1. `list_my_branches`

查询当前账号有权限的门店清单。这是所有其他工具的前置调用。

**参数**：无

**返回**

```json
{
  "branches": [
    { "branch_no": "0101", "branch_name": "城南农贸市场店", "is_default": true },
    { "branch_no": "0102", "branch_name": "城北社区店", "is_default": false }
  ]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `branches[].branch_no` | string | 门店编号，4 位数字字符串，保留前导零 |
| `branches[].branch_name` | string | 门店名称 |
| `branches[].is_default` | boolean | 是否为账号默认门店 |

---

## 2. `search_sales_summary`

查询销售汇总与品类排行。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `date_from` | string | 是 | - | 起始日期 `YYYY-MM-DD` |
| `date_to` | string | 是 | - | 结束日期 `YYYY-MM-DD`，不得早于 `date_from`，跨度 ≤ 92 天 |
| `branch_no` | string | 否 | 全部有权限门店 | 来自 `list_my_branches` |
| `category` | string | 否 | 全部品类 | 见下方品类枚举 |

**品类枚举**：`vegetable` 蔬菜 / `fruit` 水果 / `meat` 肉禽 / `aquatic` 水产 / `dry` 干货 / `other` 其他

**返回**

```json
{
  "range": { "date_from": "2026-09-01", "date_to": "2026-09-05" },
  "branches": ["0101"],
  "total": { "amount": 124350.80, "orders": 3821, "avg_ticket": 32.55 },
  "comparison": { "amount_mom": -0.032, "orders_mom": 0.011 },
  "by_category": [
    { "category": "vegetable", "amount": 52310.20, "ratio": 0.4207 }
  ],
  "by_day": [
    { "date": "2026-09-01", "amount": 24800.10, "orders": 760 }
  ]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `total.amount` | number | 销售总额（元） |
| `total.orders` | integer | 订单数 |
| `total.avg_ticket` | number | 客单价（元） |
| `comparison.amount_mom` | number | 环比，0.032 表示 +3.2%，-0.032 表示 -3.2% |
| `by_category[].ratio` | number | 占比，0~1 之间的小数 |

---

## 3. `list_branch_stock`

查询库存与临期预警。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `branch_no` | string | 否 | 全部有权限门店 | 来自 `list_my_branches` |
| `keyword` | string | 否 | — | 商品筛选，匹配**名称 / 货号 / 条码**三列（模糊，最长 32 字符）。命中 0 条返回空 `items`，**不报错** |
| `expiry_within_days` | integer | 否 | 7 | 临期天数阈值，取值 1~90 |
| `only_warning` | boolean | 否 | false | true 时只返回低于安全库存或临期的商品 |

**返回**

```json
{
  "items": [
    {
      "sku": "V10023",
      "item_id": 10023,
      "item_subno": "V10023",
      "barcode": "6901234500015",
      "name": "土豆",
      "category": "vegetable",
      "branch_no": "0101",
      "stock": 120.5,
      "unit": "kg",
      "safe_stock": 200,
      "expiry_date": "2026-09-08",
      "days_to_expiry": 3,
      "warning": ["BELOW_SAFE_STOCK", "NEAR_EXPIRY"]
    }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `sku` | **货号（item_subno）**，客户面对的商品编号。**不是内码，不能用于建单** |
| `item_id` | **商品内码（整数）**，与 `list_archives(type=product)` 的 `no` 一致。建单 `items[].item_id` 取这个 |
| `barcode` | 条码，不可用于建单 |

**`warning` 枚举**：`BELOW_SAFE_STOCK` 低于安全库存 / `NEAR_EXPIRY` 临近保质期 / `OVERSTOCK` 积压

---

## 4. `get_member_profile`

按手机号、卡号或会员名查询会员档案与储值余额。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 是 | 手机号（11 位）/ 卡号 / 会员名，至少 3 个字符 |

**返回**

```json
{
  "member_id": "88012345",
  "name": "张三",
  "phone_masked": "138****8000",
  "card_no": "88012345",
  "balance": 328.50,
  "give_balance": 20.00,
  "card_status": "正常",
  "card_type": "金卡"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `member_id` / `card_no` | string | 会员卡号（业务侧同一字段 `card_id`） |
| `phone_masked` | string | **已脱敏**，服务端不返回完整手机号 |
| `balance` | number | 储值余额（元），来自会员储值明细最新值 |
| `give_balance` | number | 赠送余额（元），业务侧有值时返回 |
| `card_status` / `card_type` / `cust_type` | string | 卡状态 / 卡类型 / 客户类型，业务侧有值时返回 |

> ⚠️ 服务端只返回脱敏手机号。若用户要求「导出完整手机号」，应如实说明无法提供。
>
> ⚠️ 会员库无积分列、无归属门店列，**不要向用户汇报积分或归属门店**——没有就是没有，字段缺省时一律不提。
>
> ⚠️ 关键词命中多条时返回 `INVALID_PARAM` 并附带候选卡号与姓名，须请用户指定，不得替用户选择。

---

## 5. `list_archives`

查询商品 / 供应商 / 客户档案。**只读，不支持新增、修改、删除。**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `type` | string | 是 | - | `product` 商品 / `supplier` 供应商 / `customer` 客户 |
| `keyword` | string | 否 | - | 模糊匹配编码或名称 |
| `limit` | number | 否 | 50 | 1~200 |

**返回**

```json
{
  "items": [
    { "no": "S01001", "name": "深圳鲜达农产品有限公司",
      "extra": { "phone_masked": "138****8000", "address": "深圳市龙岗区平湖街道" } }
  ],
  "total": 1,
  "truncated": false
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `items[].no` | string | **档案编码**，单据引用时用这个 |
| `items[].name` | string | 档案名称，展示用 |
| `items[].extra` | object | 商品：`item_subno` / `sale_price` / `unit`；供应商与客户：`phone_masked` / `address` |
| `truncated` | boolean | true 表示还有更多，需补充更精确的关键词 |

> 档案是主数据：**新增错了还能删，改错了可能已影响几十张单据**。
> 因此 AI 侧只提供查询。用户要求新增 / 修改 / 删除档案时，引导其到云启SAAS 系统内操作。

---

## 6. `create_replenish_order` （写操作）

创建要货申请单（门店向仓库或总部要货）。**调用前必须在对话中取得用户明确确认**。

> 门店归属由**登录账号的登录机构**决定，**不接受 `branch_no` 入参**。
> 账号的数据可见范围是全部门店（branch_scope 含 `*`）也照样能开单——那是"能看多少数据"，
> 开单归属看的是登录机构。仅当服务端提示「拿不到登录机构」时，才需要让用户重新连接连接器
> （旧令牌，重新授权即可，无需换账号）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `items` | array | 是 | 1~50 项 |
| `items[].item_id` | number | 是 | **商品内码（整数）**，取自 `list_archives(type=product)` 或 `list_branch_stock`。不接受条码或名称 |
| `items[].qty` | number | 是 | 要货数量，> 0 |
| `items[].unit` | string | 是 | 单位，如 `kg` / `箱` / `件` |
| `idempotency_key` | string | 是 | 幂等键，8~64 字符。**同一笔业务重试必须复用同一个 key** |

**返回**

```json
{
  "order_no": "BN2609080001",
  "status": "pending",
  "item_count": 2,
  "created_at": "2026-09-08 14:20:31",
  "duplicated": false
}
```

## 6b. `create_purchase_order` （写操作）

向供应商创建采购订单。**调用前必须在对话中取得用户明确确认**，
且必须回显供应商名称与编号。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sup_no` | string | 是 | **真实供应商编号**，取自 `list_archives(type=supplier)`。不接受名称，服务端校验存在性 |
| `items` | array | 是 | 1~50 项，字段同 `create_replenish_order` |
| `valid_date` | string | 否 | 有效期 `YYYY-MM-DD` |
| `idempotency_key` | string | 是 | 幂等键，8~64 字符，同上：**只验存在性、不去重，禁止重试** |

**返回**

```json
{
  "order_no": "PO2609080001",
  "sup_no": "S0001",
  "status": "pending",
  "item_count": 1,
  "created_at": "2026-09-08 14:20:31",
  "duplicated": false
}
```

## 6c. `get_member_sales_summary`

会员整体销售分析（**群体口径**，非单个会员明细）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `date_from` | string | 是 | `YYYY-MM-DD` |
| `date_to` | string | 是 | `YYYY-MM-DD`，不早于起始日期，跨度 ≤ 92 天 |

**返回**：`vip_sheet_cnt` / `vip_amount` / `vip_cost` / `vip_gross_profit` /
`vip_gross_margin_rate`（**比率，不可跨区间加总或求平均**）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | `pending` 待审核 / `approved` 已通过 / `rejected` 已驳回 |
| `duplicated` | boolean | **仅内置演示模式返回**（真实业务侧无此字段，因为不做去重）。演示模式下 true 表示命中幂等键、返回已存在的工单 |

---

## 7. `list_reports`

列出当前账号可用的报表，以及每张报表支持的分组维度、指标与筛选条件。

**参数**：无

**返回（已精简，仅保留模型决策必需信息）**

```json
{
  "reports": [
    {
      "report_id": "sales_gross_profit",
      "name": "销售毛利报表",
      "description": "按门店、商品、品类、日期、供应商等维度统计销售数量、销售金额、销售成本与毛利……",
      "data_freshness": "T+1",
      "dimensions": [
        { "key": "branch", "name": "门店" },
        { "key": "product", "name": "商品", "requires": ["branch"], "note": "建议先限定门店" },
        { "key": "category", "name": "品类", "enum": "vegetable(蔬菜) / fruit(水果) / …" }
      ],
      "metrics": [
        { "key": "qty", "name": "销售数量", "unit": "见商品单位", "format": "decimal", "aggregatable": false },
        { "key": "amount", "name": "销售金额", "unit": "元", "format": "currency", "aggregatable": true },
        { "key": "gross_profit", "name": "毛利", "unit": "元", "format": "currency", "aggregatable": true, "formula": "amount - cost" },
        { "key": "gross_margin_rate", "name": "毛利率", "format": "percent", "aggregatable": false, "formula": "gross_profit / amount" }
      ],
      "filters": [
        { "key": "date_from", "name": "起始日期", "type": "date", "required": true },
        { "key": "date_to", "name": "结束日期", "type": "date", "required": true, "max_span_days": 92 },
        { "key": "only_negative_profit", "name": "仅看毛利为负", "type": "boolean" }
      ]
    }
  ]
}
```

> 报表由业务侧动态注册，**不同租户可用的报表可能不同**。
> 调用 `query_report` 前必须先调用本工具确认 `report_id` 与合法的维度/指标 key。

---

## 8. `query_report`

按报表 + 分组维度 + 筛选条件查询数据。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `report_id` | string | 是 | 来自 `list_reports` |
| `dimensions` | string[] | 是 | 分组维度 key 数组，来自 `list_reports`，如 `["branch","category"]` |
| `date_from` | string | 是 | 起始日期 `YYYY-MM-DD` |
| `date_to` | string | 是 | 结束日期，跨度 ≤ 92 天 |
| `branch_nos` | string[] | 否 | 来自 `list_my_branches`；留空表示全部有权限门店 |
| `metrics` | string[] | 否 | 需要返回的指标 key；留空返回全部 |
| `extra_filters` | object | 否 | 其他筛选条件，键与取值来自 `list_reports` 的 `filters`，如 `{"only_negative_profit": true}` |
| `sort_key` | string | 否 | 排序指标 key |
| `sort_order` | string | 否 | `asc` / `desc`，默认 `desc` |
| `limit` | integer | 否 | 1~200，默认 200 |

**返回**

```json
{
  "report_id": "sales_gross_profit",
  "query": { "dimensions": ["branch"], "date_from": "2026-09-01", "date_to": "2026-09-05" },
  "summary": {
    "amount": 248701.60,
    "cost": 186420.30,
    "gross_profit": 62281.30,
    "gross_margin_rate": 0.2504,
    "row_count": 3
  },
  "rows": [
    { "branch": "0101", "branch_name": "城南农贸市场店", "amount": 104620.40, "gross_profit": 29300.30, "gross_margin_rate": 0.2801 }
  ],
  "total": 3,
  "truncated": false,
  "warnings": [],
  "generated_at": "2026-09-05 11:42:08",
  "data_freshness": "T+1"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `summary` | object | 全量汇总。**回答「总共多少」用这里的值**，不要自己把 `rows` 加起来 |
| `rows[]` | array | 明细行。维度字段同时返回编码与名称（如 `branch` + `branch_name`） |
| `total` | integer | 满足条件的总行数，非本次返回行数 |
| `truncated` | boolean | true 表示结果被截断，须告知用户 |
| `warnings[]` | array | 数据口径提示，应转述给用户 |
| `notice` | string | 仅在 `total = 0` 时出现，是可直接转述的说明 |

**指标元数据字段说明**

| 字段 | 说明 |
|---|---|
| `format` | `currency` 金额（元）／ `percent` 比率（**0~1 小数**）／ `decimal` 小数 ／ `integer` 整数 |
| `aggregatable` | `true` 可直接加总；`false` 不可跨行加总或取平均 |
| `formula` | 计算口径，用于向用户解释数字怎么来的 |

> **`aggregatable: false` 的指标（毛利率、客单价、数量）绝不能跨行相加或求平均。**
> 毛利率必须用 `summary` 中已按正确口径算好的值，或用汇总后的金额与成本重算。

---

## 错误码

| 错误码 | HTTP 类比 | 含义 | 模型应采取的动作 |
|---|---|---|---|
| `AUTH_REQUIRED` | 401 | 未携带令牌 | 引导用户重新连接连接器 |
| `TOKEN_INVALID` | 401 | 令牌无效或已过期 | 引导用户重新连接连接器 |
| `TOKEN_REVOKED` | 401 | 令牌已被撤销 | 引导用户重新连接连接器 |
| `FORBIDDEN_BRANCH` | 403 | 门店不在账号权限内 | 改用 `list_my_branches` 的结果 |
| `FORBIDDEN_ACTION` | 403 | 账号无该操作权限 | 如实告知，不要重试 |
| `INVALID_PARAM` | 400 | 参数错误，响应含 `field` 字段 | 修正后重试，最多 2 次 |
| `NOT_FOUND` | 404 | 会员 / 商品 / 门店不存在 | 与用户核对关键词 |
| `RATE_LIMITED` | 429 | 触发限流 | 等待后重试一次 |
| `UPSTREAM_TIMEOUT` | 504 | 上游超时 | 缩小查询范围后重试一次 |
| `UPSTREAM_ERROR` | 502 | 上游异常 | 重试一次，仍失败则如实告知 |
| `IDEMPOTENCY_CONFLICT` | 409 | 同一幂等键参数不一致（**仅内置演示模式会出现**；真实业务侧不去重，不会返回） | 说明冲突，请用户确认后换 key 再走一遍确认流程 |

错误响应统一结构：

```json
{
  "error": {
    "code": "INVALID_PARAM",
    "message": "date_to 不得早于 date_from",
    "field": "date_to",
    "request_id": "req_7f3a2b91"
  }
}
```

> `message` 面向终端用户可读，可直接转述；排查问题时携带 `request_id`。

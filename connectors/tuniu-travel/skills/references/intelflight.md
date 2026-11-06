# 国际机票 (intelflight)

**触发词**：航班、机票、飞机；出发地或目的地任一为境外（含港澳台）。

**工具链路**：`list_intel_flights` → `get_intel_flight_details` → `getBookingRequiredInfo` → `create_intel_flight_order` → `cancel_intel_flight_order`

参数详情：`tuniu help intelflight <tool>`

## 下单参数红线（非常重要）

> 下文调用模板中的 `...`、示例姓名/护照号/手机号等**仅为格式示范**；实际下单时必须替换为**真实值**。

1. **资源参数必须真实**：`query_id` 须来自本轮 `list_intel_flights` 顶层 `queryId`；`flight_nos`、`cabin_codes`、`vendor_id`、`expand_price_id` 须来自**同一次搜索、同一舱位**的 `get_intel_flight_details`，禁止跨搜索/跨舱位混用或编造。
2. **搜索条件一致**：下单时的出发地、目的地、日期、乘客人数须与搜索时一致；`adult_count` 单人须显式传 `1`。
3. **用户信息必须真实**：`tourists`、`contact` 须为用户提供的真实护照姓名、证件号、手机号、邮箱等；当前版本仅支持护照（`pspt_type` 建议 `2`），禁止虚构。
4. **下单前**须调用 `getBookingRequiredInfo`；下单会实时验舱验价，以验价结果为准。
5. **取消订单**：`order_id` 须来自本轮 `create_intel_flight_order` 返回；须用户明确确认后才调用 `cancel_intel_flight_order`。

## 调用模板

```bash
# 搜索（单人须显式 adult_count=1，默认 2）
tuniu call intelflight list_intel_flights --source <source> -a '{"departure_city":"北京","arrival_city":"东京","departure_date":"2026-11-15","adult_count":1}'

# 翻页：保持除 page_num 外条件不变
tuniu call intelflight list_intel_flights --source <source> -a '{"departure_city":"北京","arrival_city":"东京","departure_date":"2026-11-15","adult_count":1,"page_num":2}'

# 舱位详情
tuniu call intelflight get_intel_flight_details --source <source> -a '{"flight_no":"UO235-UO652","departure_city":"北京","arrival_city":"东京","departure_date":"2026-11-15"}'

# 预订说明（server 必须是 intelflight）
tuniu call intelflight getBookingRequiredInfo --source <source> -a '{}'

# 下单
tuniu call intelflight create_intel_flight_order --source <source> -a '{"query_id":"...","flight_nos":"UO235-UO652","cabin_codes":"T-T","vendor_id":95,"expand_price_id":"UO235_T#UO652_T#","category_code":"2000","tourists":[{"surname":"ZHANG","given_name":"SAN","pspt_type":2,"pspt_id":"E12345678","sex":"男","country":"中国","birthday":"1990-01-15","pspt_end_date":"2030-01-15"}],"contact":{"phone_area_code":"0086","phone":"13800138000","email":"zhangsan@example.com","name":"张三"}}'

# 取消（须用户明确确认后才调用）
tuniu call intelflight cancel_intel_flight_order --source <source> -a '{"order_id":"ORD20260815001","cancel_reason":"重选航程"}'
```

## 独有规则

### 下单约束（必须遵守）

- **仅支持护照**：`pspt_type` 建议传 `2`。
- **`adult_count` 默认 2**：单人查询必须显式传 `"adult_count":1`。
- **`query_id` / `flight_nos` / `cabin_codes` / `vendor_id` / `expand_price_id`** 必须来自**同一次搜索**与**同一舱位方案**，不可跨搜索或跨舱位混用。
- **取消订单**：须用户明确确认后才调用 `cancel_intel_flight_order`。

### 字段映射

- **`queryId`**：搜索返回顶层 `queryId`，下单必需，须与同一次搜索条件对应。
- **下单字段映射**（同一航班同一舱位，不可混用）：

  | 下单参数 | 取值来源 |
  |----------|----------|
  | `flight_nos` | `flightInfo[].flightNumber` |
  | `cabin_codes` | `cabinInfo[].cabinCode` |
  | `vendor_id` | `sourceId` 第一个 `-` 前的内容 |
  | `expand_price_id` | `sourceId` 去掉 `vendor_id-` 后的内容 |

  示例：`sourceId` 为 `95-UO235_T#UO652_T#` → `vendor_id=95`，`expand_price_id=UO235_T#UO652_T#`

- **getBookingRequiredInfo**：server 必须是 `intelflight`；返回纯文本。
- **支付**：下单成功后提醒用户点击 `payment_url`。
- 列表无 `intelflight` 时先 `tuniu discovery refresh && tuniu discovery list`。

## 场景示例

**用户**：8月15号北京到东京的机票，就我一个人

```bash
tuniu call intelflight list_intel_flights --source <source> -a '{"departure_city":"北京","arrival_city":"东京","departure_date":"2026-11-15","adult_count":1}'
```

**用户**：看一下 UO235-UO652 的舱位

```bash
tuniu call intelflight get_intel_flight_details --source <source> -a '{"flight_no":"UO235-UO652","departure_city":"北京","arrival_city":"东京","departure_date":"2026-11-15"}'
```

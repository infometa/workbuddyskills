# 门票 (ticket)

**触发词**：门票、景点门票、某景点门票、门票价格。

**工具链路**：`query_cheapest_tickets` → `create_ticket_order`

参数详情：`tuniu help ticket <tool>`

## 下单参数红线（非常重要）

> 下文调用模板中的示例 ID、姓名/证件号/手机号等**仅为格式示范**；实际下单时必须替换为**真实值**。

1. **资源参数必须真实**：`product_id`、`resource_id` 须来自本轮 `query_cheapest_tickets` 返回的 `productId`、`resId`，禁止编造或套用示例。
2. **出游人数量一致**：出游人总数须等于 `adult_num + child_num`（至少 1 位，最多 5 位），下单 `depart_date` 须为用户确认的真实出游日期。
3. **用户信息必须真实**：`contact_*`、`tourist_*` 的姓名、手机号、证件类型与证件号须为用户提供的真实信息，禁止虚构。

## 调用模板

```bash
# 查询（用户给出游日期时务必传 depart_date；返回 productId、resId，下单必需）
tuniu call ticket query_cheapest_tickets --source <source> -a '{"scenic_name":"中山陵","depart_date":"2026-10-01"}'

# 未指定日期也可查询
tuniu call ticket query_cheapest_tickets --source <source> -a '{"scenic_name":"中山陵"}'

# 下单
tuniu call ticket create_ticket_order --source <source> -a '{"product_id":12345,"resource_id":"res001","depart_date":"2026-10-01","adult_num":1,"contact_name":"张三","contact_mobile":"13800138000","tourist_1_name":"张三","tourist_1_mobile":"13800138000","tourist_1_cert_type":"身份证","tourist_1_cert_no":"310101199001011234"}'
```

## 独有规则

- **查询入参 `depart_date`**：出游日期 `YYYY-MM-DD`。用户说出游日期时必须传入。传入后返回的门票均满足 `startDate`（最早可售日期）≤ 指定日期 ≤ `endDate`（最晚可售日期）。
- **价格展示必须加「起」**：`startPrice` 是可售区间内的**起价**，`departsDate` 是该起价对应团期，**不是**用户指定日期当天的真实价格。向用户报价时写「¥xx起」，禁止写成指定日期的实价。
- **下单前置**：必须先 `query_cheapest_tickets` 获取 `productId` 和 `resId`。
- **支付**：下单成功后提醒用户完成支付。

## 场景示例

**用户**：4月1号中山陵门票多少钱？

```bash
tuniu call ticket query_cheapest_tickets --source <source> -a '{"scenic_name":"中山陵","depart_date":"2026-10-01"}'
```

回复价格时写「¥xx起」，不要写成确定价。

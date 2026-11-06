# 国内机票 (flight)

**触发词**：航班、机票、飞机；出发地与目的地均为中国大陆。

**工具链路**：`searchLowestPriceFlight` → `multiCabinDetails` → `getBookingRequiredInfo` → `saveOrder` → `cancelOrder`

参数详情：`tuniu help flight <tool>`

## 下单参数红线（非常重要）

> 下文调用模板中的 `xxx`、示例姓名/证件号/手机号等**仅为格式示范**；实际下单时必须替换为**真实值**。

1. **资源参数必须真实**：`departureCityName`、`arrivalCityName`、`departureDate`、`flightNo` 须来自本轮 `searchLowestPriceFlight`；`sourceId`、`vendorId`、`cabinCodes`（或工具要求的 `cabinPriceId`）须来自同一航班的 `multiCabinDetails` 返回，禁止编造、套用示例或混用不同航班/舱位。
2. **用户信息必须真实**：`tourists`、`contactTourist` 中的姓名、证件号、手机号、邮箱等须为用户本人提供的真实信息，禁止虚构。
3. **下单前**须调用 `getBookingRequiredInfo` 了解必填字段，并向用户确认信息齐全后再 `saveOrder`。

## 调用模板

```bash
# 搜索（默认低价）
tuniu call flight searchLowestPriceFlight --source <source> -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-10-15"}'

# 翻页：相同城市日期 + pageNum
tuniu call flight searchLowestPriceFlight --source <source> -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-10-15","pageNum":2}'

# 舱位详情（需 flightNo）
tuniu call flight multiCabinDetails --source <source> -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-10-15","flightNo":"MU5101"}'

# 预订说明（下单前必调，server 必须是 flight）
tuniu call flight getBookingRequiredInfo --source <source> -a '{}'

# 下单（需 cabinPriceId，来自 multiCabinDetails）
tuniu call flight saveOrder --source <source> -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-10-15","flightNo":"MU5101","cabinPriceId":"xxx","tourists":[{"name":"张三","idType":"身份证","idNumber":"310101199001011234","mobile":"13800138000"}],"contactTourist":{"name":"张三","mobile":"13800138000"}}'

# 取消
tuniu call flight cancelOrder --source <source> -a '{"orderId":"订单号"}'
```

## 独有规则

- **searchType 模式**：支持 `TIME`（时间范围）、`PRICE`（价格区间）、`NEAR_GO`/`NEAR_BACK`（周边机场）、`TRANSFER`（中转）；默认不传 searchType 为低价查询。
- **getBookingRequiredInfo**：server 必须是 `flight`，勿与 `intelflight getBookingRequiredInfo` 混淆；返回纯文本。
- **下单前置**：必须先 `searchLowestPriceFlight` → `multiCabinDetails` 获取 `cabinPriceId`，再 `getBookingRequiredInfo`，最后 `saveOrder`。
- **支付**：下单成功后提醒用户点击支付链接。

## 场景示例

**用户**：3月15号北京到上海的航班

```bash
tuniu call flight searchLowestPriceFlight --source <source> -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-10-15"}'
```

**用户**：看一下 MU5101 这个航班的舱位

```bash
tuniu call flight multiCabinDetails --source <source> -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-10-15","flightNo":"MU5101"}'
```

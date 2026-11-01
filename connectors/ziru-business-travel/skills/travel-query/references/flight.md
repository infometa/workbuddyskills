# 机票

## ziru_flight_list — 航班班次列表

取该航线当天的全量航班，按起飞时间窗过滤，**按起飞时间升序**返回。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `date` | string | 是 | 出行日期，`yyyy-MM-dd` |
| `fromAirportCode` | string | 是 | 出发城市机场三字码（IATA），如 `PEK` |
| `toAirportCode` | string | 是 | 到达城市机场三字码（IATA），如 `SHA` |
| `startTime` | string | 否 | 起飞时间下限 `HH:mm`，只返回该时刻（含）之后起飞的航班 |
| `endTime` | string | 否 | 起飞时间上限 `HH:mm`，只返回该时刻（含）之前起飞的航班；不能早于 `startTime` |

`startTime`/`endTime` 都不传 = 全天。

### 返回

| 字段 | 说明 |
|---|---|
| `flightNo` | 航班号，如 `MU5100` |
| `airName` | 航空公司，如 `中国东方航空` |
| `orgCity` / `dstcity` | 出发/到达城市三字码（注意：去程传 `SHA` 时，返回可能是 `PVG`，因为上海有多个机场） |
| `orgAirportName` / `dstAirportName` | 机场名，如 `首都机场` / `浦东国际机场` |
| `orgAirportTerminal` / `dstAirportTerminal` | 航站楼，如 `T2` |
| `depDate` / `arrDate` | 起飞/降落日期时间，`yyyy-MM-dd HH:mm:ss`（含跨天信息） |
| `flightTime` | 飞行时长，如 `2时5分` |
| `airportTax` / `fuelTax` | 机建费 / 燃油费（**单价**，总额要乘人数） |
| `priceFare` | 最低票面价（**预估价**，实时价以 `ziru_flight_cabin` 为准） |
| `discountStr` | 折扣描述，如 `经济舱 3.3折` |
| `planeStyle` | 机型，如 `空客32N(大)` |
| `mealDisPlay` | 餐食，如 `早餐` |
| `fromCityName` / `toCityName` | 出发/到达城市名，如 `北京` / `上海` |

空数组 = 该航线当天没有航班。

### 示例

```
ziru_flight_list({ "date": "2026-09-20", "fromAirportCode": "PEK", "toAirportCode": "SHA" })
→ 67 条，首条 { "flightNo": "MU5100", "airName": "中国东方航空", "depDate": "2026-10-02 07:00:00", "priceFare": 700.0, ... }
```

---

## ziru_flight_cabin — 航班舱位

查某个具体航班的全部舱位。**航班号和航线日期来自 `ziru_flight_list`。**

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `date` | string | 是 | 航班起飞日期，`yyyy-MM-dd` |
| `fromAirportCode` | string | 是 | 出发机场三字码 |
| `toAirportCode` | string | 是 | 到达机场三字码 |
| `flightNo` | string | 是 | 航班号，取自 `ziru_flight_list` |

### 返回

```
{
  "flightInfo": { …与 ziru_flight_list 单条同结构… },
  "cabinList": [ …舱位… ]
}
```

`flightInfo` 与 `ziru_flight_list` 的字段完全一致，不用自己关联。

`cabinList` 每个舱位：

| 字段 | 说明 |
|---|---|
| `cabinId` | **舱位唯一标识**，后续引用该舱位时回传 |
| `lastSeat` | 余票数 |
| `lowestPrice` | 是否该航班最低价舱位 |
| `fdinfo.policyCodeAlias` | 舱位名，如 `经济舱` |
| `fdinfo.cost` | 成本价（**可订价格以这个为准**） |
| `fdinfo.airportFee` / `fdinfo.oilFee` | 机建费 / 燃油费 |
| `fdinfo.discountRate` | 折扣，如 `3.3折` |
| `fareBasis` | 票价基础代码 |
| `fareBasisForPrice` | 全价舱价格（用来算折扣力度） |
| `minxExpPrice` | 退改最低价文案，如 `退改 ￥140起` |
| `freeLuggageDetail` | 免费行李额，如 `免费托运行李额：20KG` |
| `luggage` | 行李规则全文（已拼成一句话） |
| `refundRule` | 退票规则（已拼成一句话，含各时间段的费用） |
| `changeRule` | 改签规则（已拼成一句话） |

`luggage` / `refundRule` / `changeRule` 是拼好的中文说明，**直接引用原文**，不要自己改写或补充。

### 示例

```
ziru_flight_cabin({ "date": "2026-09-20", "fromAirportCode": "PEK", "toAirportCode": "SHA", "flightNo": "MU5100" })
→ cabinList 14 个舱位，其中：
  { "cabinId": "...", "lastSeat": 9, "lowestPrice": true,
    "fdinfo": { "cost": 700.0, "airportFee": 50.0, "oilFee": 100.0,
                "policyCodeAlias": "经济舱", "discountRate": "3.3折" },
    "refundRule": "退票：2026-09-25 07:00:00 前 140元(20%)；…",
    "changeRule": "改签：2026-09-25 07:00:00 前 140元(20%)；…",
    "luggage": "免费托运 每人1件，每件20KG（单件体积不得超过40×60×100厘米）；免费手提 …" }
```

### 注意

- 舱位价是**该航班当下的实时舱位价**，与 `ziru_flight_list` 的 `priceFare`（预估价）不一致时，以舱位为准。
- 用户选定舱位后，记住 `cabinId`。

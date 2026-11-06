# 火车票 (train)

**触发词**：火车票、火车、车次、高铁、动车。

**工具链路**：`searchLowestPriceTrain` → `queryTrainDetail` → `bookTrain` → `cancelOrder`

参数详情：`tuniu help train <tool>`

## 下单参数红线（非常重要）

> 下文调用模板中的示例 ID、姓名/证件号/手机号等**仅为格式示范**；实际下单时必须替换为**真实值**。

1. **资源参数必须真实**：`resources[].resourceId`、`adultPrice`、`departsDate` 须来自本轮 `queryTrainDetail` 返回的 `resId`、`price`、`departsDate`；站点名、车次、日期须与详情查询一致，禁止编造。
2. **用户信息必须真实**：`adultTourists`、`contact` 中的姓名、证件号、手机号须为用户提供的真实乘车人/联系人信息，禁止虚构。
3. **取消订单**：`orderId` 须来自本轮 `bookTrain` 返回的真实订单号。

## 调用模板

```bash
# 搜索（searchType 5=按票价升序，默认）
tuniu call train searchLowestPriceTrain --source <source> -a '{"departureCityName":"南京","arrivalCityName":"上海","departureDate":"2026-10-20","searchType":"5"}'

# 翻页（须 queryId + pageNum）
tuniu call train searchLowestPriceTrain --source <source> -a '{"queryId":"xxx","pageNum":2}'

# 车次详情（返回 resId、price、departsDate）
tuniu call train queryTrainDetail --source <source> -a '{"departureStationName":"南京南","arrivalStationName":"上海虹桥","departureDate":"2026-10-20","trainNum":"G203"}'

# 下单
tuniu call train bookTrain --source <source> -a '{"acceptStandingTicket":false,"adultTourists":[{"name":"张三","psptId":"310101199001011234","psptType":1,"isStuDisabledArmyPolice":0,"tel":"13800138000"}],"contact":{"tel":"13800138000"},"resources":[{"resourceId":2121337089,"adultPrice":141.0,"departsDate":"2026-10-20"}]}'

# 取消
tuniu call train cancelOrder --source <source> -a '{"orderId":"订单号"}'
```

## 独有规则

- **searchType**：`1` 出发时间升序、`2` 降序、`3` 耗时升序、`4` 降序、`5` 票价升序（默认）、`6` 票价降序。
- **翻页**：首次查询返回 `queryId`，翻页传 `queryId` + `pageNum`。
- **下单前置**：必须先 `searchLowestPriceTrain` 和 `queryTrainDetail` 获取 `resId`。

## 场景示例

**用户**：3月20号南京到上海的火车票

```bash
tuniu call train searchLowestPriceTrain --source <source> -a '{"departureCityName":"南京","arrivalCityName":"上海","departureDate":"2026-10-20"}'
```

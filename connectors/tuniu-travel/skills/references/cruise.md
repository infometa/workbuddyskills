# 邮轮 (cruise)

**触发词**：邮轮、游轮（等同邮轮）。

**工具链路**：`searchCruiseList` → `getCruiseProductDetail` → `getCruiseCabinAndRoom` → `getCruiseBookingRequiredInfo` → `saveCruiseOrder`

参数详情：`tuniu help cruise <tool>`

## 下单参数红线（非常重要）

> 下文调用模板中的示例 ID、姓名/证件号/手机号等**仅为格式示范**；实际下单时必须替换为**真实值**。

1. **资源参数必须真实且同源**：
   - 详情入参（`productId`、`departsDateBegin/End`、`departCityCode`、`classBrandParentId`、`proMode`）须来自 `searchCruiseList` **同一条** `rows` 记录，原样传递，禁止自行拼参。
   - `departDate`（查舱位）须来自详情 `productPriceCalendar.rows[].departDate` 中用户所选团期。
   - `saveCruiseOrder` 的 `departureDate` 须取 `getCruiseCabinAndRoom.data.base.beginDate`；`duration`、`night`、`vendorId`、`departureCityName` 来自详情/舱位返回。
   - `selectRes[].journeyId` 须来自**最近一次** `getCruiseCabinAndRoom` 的 `cabinList[].journeyId`；`resourceId`/`subResourceId` 须来自同一舱位下 `priceRes[].resId`，禁止用数组下标或历史 ID。
2. **用户信息必须真实**：`tourists` 中的姓名、证件类型、证件号、手机号须为用户提供的真实出游人信息，禁止虚构。
3. **无团期则不下单**：`productPriceCalendar` 为空或 `count=0` 时停止下单链路。

## 调用模板

```bash
# 列表搜索
tuniu call cruise searchCruiseList --source <source> -a '{"departsDateBegin":"2026-10-17","departsDateEnd":"2026-10-30"}'

# 产品详情（参数须来自 searchCruiseList 同一条 rows 记录）
tuniu call cruise getCruiseProductDetail --source <source> -a '{"productId":"321648365","departsDateBegin":"2026-10-10","departsDateEnd":"2026-10-14","departCityCode":[1602],"classBrandParentId":12,"proMode":1}'

# 舱位房型（departDate 须来自 productPriceCalendar）
tuniu call cruise getCruiseCabinAndRoom --source <source> -a '{"productId":"321648365","departDate":"2026-11-01"}'

# 预订说明
tuniu call cruise getCruiseBookingRequiredInfo --source <source> -a '{}'

# 下单
tuniu call cruise saveCruiseOrder --source <source> -a '{"productId":"321648365","departureDate":"2026-11-01","departureCityName":"上海","duration":5,"night":4,"vendorId":73197,"selectRes":[{"journeyId":91808486,"resourceId":2121750804}],"tourists":[{"name":"张三","idType":"身份证","idNumber":"310101199001011234","mobile":"13800138000"}]}'
```

## 独有规则

- **日期约束**：起始日期不得早于当天；结束日期不得早于起始日期。
- **仅日期即可查**：用户只给日期范围时直接查，不要额外追问航线/品牌/天数。
- **翻页**：保持筛选条件不变，仅更新 `pageNum`。
- **列表展示**：当前页 `data.rows` 需逐条展示，不要无说明地只列少量样例。
- **团期展示**：必须展示 `productPriceCalendar` 中全部可售团期；`count=0` 或 `rows` 为空时停止下单链路。
- **邮轮下单 ID 映射**：`saveCruiseOrder.selectRes` 的 `journeyId`/`resourceId`/`subResourceId` 只能来自最近一次 `getCruiseCabinAndRoom` 返回；`resourceId`/`subResourceId` 必须取 `priceRes[].resId`，不能用数组下标或历史 ID。
- **ID 映射（关键）**：
  - `journeyId` 来自 `cabinList[].journeyId`
  - `resourceId` 取 `priceRes` 中 `roomTypeResType=0` 条目的 `resId`
  - `subResourceId`（可选）取 `roomTypeResType=1` 条目的 `resId`
  - **严禁**把 `priceRes` 数组下标当作 ID；**严禁**复用历史对话中的 ID
- **团期价格展示**：成人/儿童价格基于 `productPriceCalendar` 原始字段展示；儿童价为 0 时不展示儿童价，双 0 团期不展示。
- **`departureDate`** 必须取 `getCruiseCabinAndRoom.data.base.beginDate`。
- 建议透传 `traceId` 到后续调用便于排障。

## 场景示例

**用户**：查一下3月17到3月30的邮轮

```bash
tuniu call cruise searchCruiseList --source <source> -a '{"departsDateBegin":"2026-10-17","departsDateEnd":"2026-10-30"}'
```

# 度假产品 (holiday)

**触发词**：度假产品、跟团、自助游产品、自驾游产品、旅游线路、当地游、团期。

**工具链路**：`searchHolidayList` → `getHolidayProductDetail` → `getHolidayBookingRequiredInfo`（可选）→ `saveHolidayOrder`

参数详情：`tuniu help holiday <tool>`

## 下单参数红线（非常重要）

> 下文调用模板中的示例 ID、姓名/证件号/手机号等**仅为格式示范**；实际下单时必须替换为**真实值**。

1. **资源参数必须真实且同源**：
   - 详情入参（`productId`、`departCityCode`、`classBrandParentId`、`proMode` 等）须从 `searchHolidayList` **对应列表行**原样取得，禁止拆数组或自行拼参。
   - `saveHolidayOrder` 的 `departDate` 须来自详情 `productPriceCalendar.rows[].departDate` 中用户所选的可售团期。
   - `departCityName` 须取 `getHolidayProductDetail.data.departureCityName`；建议透传详情返回的 `traceId`。
2. **用户信息必须真实**：`tourists` 中的姓名、证件类型、证件号、手机号须为用户提供的真实出游人信息，禁止虚构。
3. **无团期则不下单**：`productPriceCalendar` 为空时停止下单链路。

## 调用模板

```bash
# 列表搜索
tuniu call holiday searchHolidayList --source <source> -a '{"keyWord":"三亚","departsDateBegin":"2026-10-10","departsDateEnd":"2026-10-15"}'

# 翻页：保持筛选条件不变，仅更新 pageNum
tuniu call holiday searchHolidayList --source <source> -a '{"keyWord":"云南","departsDateBegin":"2026-10-10","departsDateEnd":"2026-10-20","departCityName":"上海","queryTypeName":"跟团","pageNum":2}'

# 产品详情（参数须从 searchHolidayList 列表行原样取得）
tuniu call holiday getHolidayProductDetail --source <source> -a '{"productId":"321619424","departCityCode":[1602],"classBrandParentId":12,"proMode":1}'

# 预订说明（纯文本，勿 JSON.parse）
tuniu call holiday getHolidayBookingRequiredInfo --source <source> -a '{}'

# 下单（departDate 须来自详情团期日历）
tuniu call holiday saveHolidayOrder --source <source> -a '{"productId":"321619424","departDate":"2026-11-01","departCityName":"南京","duration":5,"night":4,"traceId":"<详情返回的traceId>","tourists":[{"name":"张三","idType":"身份证","idNumber":"310101199001011234","mobile":"13800138000"}]}'
```

## 独有规则

- **展示约束（重要）**：**不要向用户展示 JSON 字段名**（如 `productId`、`departCityCode`）；用自然语言描述产品。
- **价格展示**：`price`、`starPrice` 等为**起步价**，必须标注「起」（如 `¥38起`），不得写成确定价。
- **keyWord 用法**：承接目的地/主题语义；不要混入“第2页/下一页”等翻页词；不要写入“推荐/热门”等排序词。
- **度假详情参数**：`getHolidayProductDetail` 的 `departCityCode`（数组）、`classBrandParentId`、`proMode` 等必须与 `searchHolidayList` 列表行一致，勿拆数组或自行拼参；`saveHolidayOrder` 的 `departDate` 必须来自详情团期日历中的可选日期。
- **团期展示**：展示 `productPriceCalendar.rows` 中全部可选日期与价格；无团期时停止下单链路。
- **`departCityName`** 必须取 `getHolidayProductDetail.data.departureCityName`。
- 若返回 `journeySummary`，按天（第N天+标题+模块）组织展示。

## 场景示例

**用户**：4月中旬想去三亚有什么度假线路？

```bash
tuniu call holiday searchHolidayList --source <source> -a '{"keyWord":"三亚","departsDateBegin":"2026-10-10","departsDateEnd":"2026-10-20"}'
```

**信息不足**：用户只说“想去三亚玩” → 先澄清，不要默认调用 `holiday` 或 `package-booking`。

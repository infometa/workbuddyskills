# 酒店 (hotel)

**触发词**：酒店、住宿、民宿、某地酒店、入住。

**工具链路**：`tuniuHotelSearch` → `tuniuHotelDetail` → `tuniuHotelCreateOrder`

参数详情：`tuniu help hotel <tool>`

## 下单参数红线（非常重要）

> 下文调用模板中的 `xxx`、示例姓名/手机号等**仅为格式示范**；实际下单时必须替换为**真实值**。

1. **资源参数必须真实**：`hotelId`、`roomId`（详情中的 `roomTypeId`）、`preBookParam` 须来自本轮 `tuniuHotelDetail` 返回；`preBookParam` **有效期 30 分钟**，超时须重新查详情，禁止编造或复用旧值。
2. **日期一致**：`checkInDate`、`checkOutDate` 须与用户确认的入离店日期一致，且与详情查询条件匹配。
3. **用户信息必须真实**：`roomGuests`、`contactName`、`contactPhone` 须为用户提供的真实入住人/联系人信息，禁止虚构。

## 调用模板

```bash
# 搜索（第一页）
tuniu call hotel tuniuHotelSearch --source <source> -a '{"cityName":"北京","checkIn":"2026-10-01","checkOut":"2026-10-03"}'

# 翻页（须用首次搜索返回的 queryId）
tuniu call hotel tuniuHotelSearch --source <source> -a '{"queryId":"xxx","pageNum":2}'

# 详情（hotelId 或 hotelName 二选一）
tuniu call hotel tuniuHotelDetail --source <source> -a '{"hotelId":12345,"checkIn":"2026-10-01","checkOut":"2026-10-03"}'

# 下单（须 preBookParam，来自 tuniuHotelDetail）
tuniu call hotel tuniuHotelCreateOrder --source <source> -a '{"hotelId":"xxx","roomId":"xxx","preBookParam":"xxx","checkInDate":"2026-10-01","checkOutDate":"2026-10-03","roomCount":1,"roomGuests":[{"guests":[{"firstName":"三","lastName":"张"}]}],"contactName":"张三","contactPhone":"13800138000"}'
```

## 独有规则

- **翻页必须用 `queryId`**：首次搜索返回 `queryId`，翻页时传 `queryId` + `pageNum`，不要重复传城市条件。
- **下单前置**：必须先 `tuniuHotelDetail` 获取 `preBookParam`。
- **支付**：下单成功后提醒用户完成支付。

## 场景示例

**用户**：北京3月1号入住一晚，有什么酒店？

```bash
tuniu call hotel tuniuHotelSearch --source <source> -a '{"cityName":"北京","checkIn":"2026-10-01","checkOut":"2026-10-02"}'
```

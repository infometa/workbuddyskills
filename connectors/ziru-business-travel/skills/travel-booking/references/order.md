# 创单工具（购票链接）

四个创单工具都是**前置流程、不真正落单**：返回一条**购票链接**（1 小时内有效）和方案摘要，用户点开链接确认后才真正完成预订。

## 通用返回

四个工具的返回结构完全一致：

| 字段 | 说明 |
|---|---|
| `detailId` | **订单标识**。本次下单参数已按此键缓存，与链接同寿命（1 小时）。多段出行时把它传给 `ziru_merge_order_link` |
| `orderLinkUrl` | **购票链接**。输出时裸 URL 独占一行、前缀 `预订链接: `（见 SKILL 输出规则） |
| `expireTime` | 链接失效时间，`yyyy-MM-dd HH:mm:ss` |
| `orderInfo` | 说明文案，工具已拼好：`已为您生成购票链接，{方案摘要}。{失效时间} 前有效。` |

`orderInfo` 里的方案摘要由工具按**实时数据**拼好，直接引用即可，不要自己另行计算金额或时刻。

失败时 `message` 写明原因（各节「失败情形」），如实转达给用户，不要吞掉或改写成模糊说法。

---

## ziru_flight_order_link — 机票购票链接

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `cabinId` | string | 是 | 舱位标识，取自 `ziru_flight_cabin` 返回的 `cabinId` |

`cabinId` 形如 `13_0_PEK_PVG_20261002070000_MU5100_V_700.0__`，本身内含出发/到达三字码、起飞日期时间和航班号，工具据此反查舱位，**因此不需要再传航班号、日期、航线**。

### 失败情形

| message | 含义 |
|---|---|
| `cabinId 格式无法解析：{cabinId}` | 传入的不是 `ziru_flight_cabin` 返回的原值 |
| `未查到航班 {flightNo} 的舱位，无法下单` | 该航班当下查不到舱位 |
| `未找到 cabinId {cabinId} 对应的舱位` | 舱位已售完或下架 |

---

## ziru_train_order_link — 火车票购票链接

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `trainNo` | string | 是 | 车次号，如 `G1`、`G531`、`D7` |
| `fromStation` | string | 是 | 出发站。口径同 `ziru_train_list`：城市名（`北京`）或站名（`北京南`），**不带 `市`/`站` 后缀** |
| `toStation` | string | 是 | 到达站，口径同上 |
| `date` | string | 是 | 出发日期，`yyyy-MM-dd` |
| `seatCode` | string | 是 | 座席码，取自 `ziru_train_list` 的 `seats[].seatCode`，如 `O`(二等座)、`M`(一等座)、`9`(商务座)、`10`(无座) |

### 失败情形

| message | 含义 |
|---|---|
| `出发站和到达站不能为空` | `fromStation` / `toStation` 没传 |
| `未查到车次 {trainNo}，无法下单` | 该线路当天查不到这个车次 |
| `未查到车次 {trainNo}` | 车次号对不上 |
| `车次 {trainNo} {saleStatus}，无法生成购票链接` | 该车次未开售/暂停发售/暂售至，当下订不了 |
| `车次 {trainNo} {saleStatus}，无法生成购票链接，{saleDateTime} 才开售` | 同上且上游给了开售时间 |
| `车次 {trainNo} 未找到座席码 {seatCode} 的座席` | 座席码不对，或该座席当下不可售 |

### 注意

**未开售的车次本来就订不了**——工具会按实时 `saleStatus` 拦下（`未开售` / `暂停发售` / `暂售至` 均不可创单）并返回上面的失败情形。事先已知未开售时不必调用，直接提示用户 `{saleDateTime} 才开售`（见 SKILL 核心规则 6）；被拦下时如实转达 message 即可。

---

## ziru_hotel_order_link — 酒店购票链接

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotelId` | string | 是 | 取自 `ziru_hotel_list` 返回的 `hotelId` |
| `hotelName` | string | 是 | 取自 `ziru_hotel_list` 返回的 `hotelName` |
| `roomTypeKeyID` | string | 是 | 取自 `ziru_hotel_room` 的 `ratePlan[].roomTypeKeyID` |
| `productNo` | string | 是 | 取自 `ziru_hotel_room` 的 `ratePlan[].productNo` |
| `checkInDate` | string | 是 | 入住日期，`yyyy-MM-dd` |
| `checkOutDate` | string | 是 | 离店日期，`yyyy-MM-dd` |

`hotelId` + `roomTypeKeyID` + `productNo` 三者才能确定唯一的「房型 + 产品」；入离日期必须带，**同一产品不同日期的房态不同**。

### 失败情形

| message | 含义 |
|---|---|
| `该酒店 {checkInDate} 至 {checkOutDate} 无可售房型，无法下单` | 这些日期没房 |
| `未找到 roomTypeKeyID {x} + productNo {y} 对应的房型产品` | 产品已下架或价格变动 |
| `未查询到酒店 {hotelId} 的信息，无法下单` | 酒店信息取不到 |

---

## ziru_merge_order_link — 合并成一条链接

把多个已有的 `detailId` 合并成**一条**链接，用户点一次即可把机票/火车/酒店一起确认。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `detailIds` | string[] | 是 | 前面各创单工具返回的 `detailId` 列表，按行程顺序排列 |

### 失败情形

| message | 含义 |
|---|---|
| `detailIds 不能为空` | 没传或全为空白 |
| `订单标识 {ids} 不存在或已过期（有效期 1 小时），请重新生成后再合并` | 有任一 `detailId` 已过期。**不做部分合并**，需把那一项重新生成后整组再合并 |
| `待合并的订单标识里没有可下单的方案` | 这些 `detailId` 里没有可下单的行程项 |

### 注意

- **只有一项**要订时不要合并，直接输出那一条链接。
- 生成失败的项（如"无房""未找到座席"）没有 `detailId`：**只把生成成功的传去合并**，并如实说明哪一项没订上、原因是什么。

---

## 鉴权

四个工具都要求请求头带 `X-Mcp-Key`。缺失或无效时返回 `busCode: 9999`、`message` 为 `X-Mcp-Key 缺失或无效`——这是**鉴权问题而不是业务失败**，告知用户重新填写 Access Token，不要反复重试。

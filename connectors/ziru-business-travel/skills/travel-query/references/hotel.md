# 酒店

## ziru_hotel_list — 酒店列表

按城市召回酒店，支持价格、品牌、星级、位置偏好过滤。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `cityCode` | string | **是** | 城市行政区划代码，如 南京 `320100` |
| `cityName` | string | 否 | 入住城市，如 `南京` |
| `priceMin` / `priceMax` | number | 否 | 价格区间（间夜，元） |
| `hotelName` | string | 否 | 指定酒店名。传了它按名字精确找 |
| `hotelBrand` | string | 否 | 品牌或集团，如 `如家`、`华住` |
| `hotelCategory` | string | 否 | 星级/档位要求 |
| `lon` / `lat` | string | 否 | 目的地经纬度（**高德坐标**），用于"靠近某地"的筛选 |
| `distanceMeters` | number | 否 | 目的地附近搜索范围（米），不传默认 4000 |
| `intent` | string | 否 | 用户的偏好描述，如 `安静`、`交通便利`、`周边美食多`。不传默认"商务办公,交通便利" |

### 返回

| 字段 | 说明 |
|---|---|
| `hotelId` | **酒店唯一标识**，查房型时回传 |
| `hotelName` | 酒店名 |
| `brandName` | 品牌或集团，如 `清沐` |
| `categoryName` | 档位，如 `经济型`、`舒适型` |
| `label` | 托管标签，如 `优享酒店`、**`协议酒店`**（协议酒店=企业协议价酒店，商旅场景值得优先提） |
| `rating` | 评分 |
| `address` / `district` | 详细地址 / 所在行政区，如 `龙蟠路171-5号` / `玄武区` |
| `amenities` | 设施，逗号分隔，**同时含正面与负面**，如 `免费wifi,行李寄存,无电梯,无停车场` |
| `intro` | 简介（最多 60 字） |
| `lonLat` | 百度经纬度 `"经度,纬度"` |
| `lowPrice` | 预估最低价（**预估价**，实时价以 `ziru_hotel_room` 为准） |
| `phone` | 酒店电话 |

空数组 = 该条件下没有酒店。注意：**空的常见原因是价格/位置条件太窄**，不是这个城市没酒店——可以提示用户放宽条件再查。

### 示例

```
ziru_hotel_list({ "cityName": "南京", "cityCode": "320100", "intent": "交通便利" })
→ 30 条，首条：
  { "hotelId": "00457780", "hotelName": "清沐酒店(南京林业大学国展中心店)",
    "brandName": "清沐", "categoryName": "经济型", "label": "优享酒店", "rating": "4.1",
    "address": "龙蟠路171-5号", "district": "玄武区",
    "amenities": "免费wifi,行李寄存,24小时前台,洗衣服务,无电梯,无停车场",
    "lowPrice": "231", "phone": "025-85471911" }
```

---

## ziru_hotel_room — 酒店房型

查某个具体酒店的房型与价格方案。**一次只查一个酒店。**

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotelId` | string | 是 | 取自 `ziru_hotel_list` 的 `hotelId` |
| `hotelName` | string | **是** | 取自 `ziru_hotel_list` 的 `hotelName` |
| `checkInDate` | string | 是 | 入住日期，`yyyy-MM-dd` |
| `checkOutDate` | string | 是 | 离店日期，`yyyy-MM-dd` |

### 返回

```
[ { "ratePlan": [ …渠道产品… ], "roomInfo": { …房型详情… }, "mostLowPrice": 1554 } ]
```

**一个房型对应多个渠道产品**，都在 `ratePlan` 里。

`roomInfo`（房型详情）：

| 字段 | 说明 |
|---|---|
| `name` | 房型名，如 `豪华双床房` |
| `area` / `floor` | 面积 / 楼层，如 `35㎡` / `16-19层` |
| `bedType` | 床型，如 `双床`、`1张1.5×2.0米大床` |
| `window` | 窗型，如 `有窗` |
| `wifi` | 宽带 |
| `displayImages` | 房型图片 |
| `hotelKeyID` | 酒店 ID |

`ratePlan` 每个产品：

| 字段 | 说明 |
|---|---|
| `roomTypeKeyID` + `productNo` + 酒店 ID | **三者才能确定唯一的"房型+产品"**，后续引用该产品时回传 |
| `productName` | 产品名（通常同房型名） |
| `priceType` | 价格类型，如 `协议价` |
| `bedType` / `window` | 床型 / 窗型 |
| `breakfastName` | 早餐，如 `双早`、`无早` |
| `averagePrice` | **间夜价**（可订价格以这个为准）。整段总价 = 间夜价 × 晚数 |
| `cancelTypeName` | 取消类型，如 `限时取消`、`不可取消` |
| `cancelRule.refundStr` | **取消政策全文**（含免费取消截止时间），直接引用原文 |
| `reservationLabel` | 预订标签，如 `立即确认` |
| `showLabel` | 展示标签，如 `差标内,含早,可取消,立即确认` |
| `hotelKeyID` | 酒店 ID |

`mostLowPrice` 是该房型的最低间夜价。

### 示例

```
ziru_hotel_room({ "hotelId": "00041198", "hotelName": "北京怡亨酒店",
            "checkInDate": "2026-09-20", "checkOutDate": "2026-09-22" })
→ [ { "roomInfo": { "name": "豪华双床房", "bedType": "双床", "area": "35㎡", "floor": "16-19层" },
      "mostLowPrice": 1554,
      "ratePlan": [
        { "roomTypeKeyID": "625272508", "productNo": "D8G2A#DH2D22#62F2G2FA8#DASFD82D4#A",
          "productName": "豪华双床房", "bedType": "双床", "breakfastName": "双早",
          "averagePrice": 1554, "cancelTypeName": "不可取消",
          "cancelRule": { "refundStr": "订单一经预订成功，不可变更/取消，如未入住将扣除全额房费。" },
          "showLabel": "双床,含早" },
        { …无早、限时取消、averagePrice 1692 的另一档… } ] } ]
```

### 没房的情况

该酒店这些日期没有可售房型时，接口会返回失败，`message` 写明原因，例如：

> 该酒店 2026-09-20 至 2026-09-22 无可售房型

**如实告诉用户这家没房**，可以建议换日期或换酒店，不要拿别的日期/酒店的数据顶上。

### 价格核对

- `lowPrice`（列表里）是预估价，`averagePrice`（房型里）是当下的可订价，**两者不一致时以房型为准**。
- 用户住多晚时，报总价要 `averagePrice × 晚数`（晚数由入离日期得出）。

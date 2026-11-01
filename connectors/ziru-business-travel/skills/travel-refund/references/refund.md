# 退票/改签接口参考

本文档说明退票/改签相关工具的入参、返回字段和失败情形。

---

## ziru_order_list — 订单列表查询

查询当前用户的订单列表，用于退票/改签场景让用户选择要操作的订单。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `businessType` | string | 否 | 业务类型过滤：`flight`（机票）/ `train`（火车票）/ `hotel`（酒店）。为空或不传则查全部 |
| `startDate` | string | 否 | 开始日期 `yyyy-MM-dd`，默认近 30 天 |
| `endDate` | string | 否 | 结束日期 `yyyy-MM-dd`，默认今天 |
| `pageIndex` | integer | 否 | 页码，默认 1 |
| `pageSize` | integer | 否 | 每页条数，默认 20 |
| `departTimeStart` | string | 否 | 出发时间开始 `yyyy-MM-dd`，机票/火车适用 |
| `departTimeEnd` | string | 否 | 出发时间结束 `yyyy-MM-dd`，机票/火车适用 |
| `arriveTimeStart` | string | 否 | 到达时间开始 `yyyy-MM-dd`，机票/火车适用 |
| `arriveTimeEnd` | string | 否 | 到达时间结束 `yyyy-MM-dd`，机票/火车适用 |
| `fromStation` | string | 否 | 出发站/机场名称（模糊匹配），机票/火车适用 |
| `toStation` | string | 否 | 到达站/机场名称（模糊匹配），机票/火车适用 |
| `status` | string | 否 | 订单状态（中文名称模糊匹配，如"出票成功""已确认"等），所有业务类型适用 |
| `cityName` | string | 否 | 酒店所在城市（模糊匹配），仅酒店适用 |
| `checkInDateStart` | string | 否 | 入住日期开始 `yyyy-MM-dd`，仅酒店适用 |
| `checkInDateEnd` | string | 否 | 入住日期结束 `yyyy-MM-dd`，仅酒店适用 |

### 返回

| 字段 | 类型 | 说明 |
|---|---|---|
| `orders` | array | 订单列表 |
| `orders[].orderId` | string | 订单号 |
| `orders[].businessType` | string | 业务类型：`flight` / `train` / `hotel` |
| `orders[].businessTypeName` | string | 业务类型中文：机票 / 火车票 / 酒店 |
| `orders[].fromPlace` | string | 出发地（城市/站名/酒店城市） |
| `orders[].toPlace` | string | 到达地（城市/站名，酒店为空） |
| `orders[].departDate` | string | 出发日期/入住日期 `yyyy-MM-dd` |
| `orders[].arriveDate` | string | 到达日期/离店日期 `yyyy-MM-dd` |
| `orders[].status` | string | 订单状态中文（如"出票成功""已确认"） |
| `orders[].statusCode` | integer | 订单状态码（原始值） |
| `orders[].amount` | string | 订单金额（元） |
| `orders[].name` | string | 车次/航班号/酒店名称 |
| `orders[].refundable` | boolean | 是否可退票 |
| `orders[].rebookable` | boolean | 是否可改签 |
| `orders[].refundLink` | string | 退票链接（可退票时返回） |
| `orders[].rebookingLink` | string | 改签链接（可改签时返回） |
| `totalCount` | integer | 总数 |

### 注意

- 只有 `refundable=true` 的订单才能调 `ziru_refund_link`
- 只有 `rebookable=true` 的订单才能调 `ziru_rebooking_link`
- 订单按出发日期倒序排列
- **订单号必须以接口返回的 `orderId` 为准**，不可自行拼接或猜测
- 新增筛选条件说明：
  - `departTimeStart/End`、`arriveTimeStart/End`、`fromStation`、`toStation` 仅对机票和火车票订单生效
  - `cityName`、`checkInDateStart/End` 仅对酒店订单生效
  - `status` 对所有业务类型订单生效，支持中文模糊匹配（如"出票""已确认"等）
  - 站点/城市名称支持模糊匹配，例如 `fromStation=北京` 会匹配"北京站""北京南站"等

### 退改时间规则

| 业务类型 | 退票规则 | 改签规则 |
|----------|----------|----------|
| 机票 | 起飞时间之前 | 起飞时间之前 |
| 火车票 | 出票完成 + 距离开车时间 5 分钟以上 | 出票完成 + 发车日期当天 23:59:59 之前 |
| 酒店 | 入住日期之前 + 未入住（状态为"已确认"或"预订成功(等待入住)"） | ❌ 不支持改签 |

---

## ziru_refund_link — 退票链接生成

根据订单号和业务类型生成 H5 退票页跳转链接。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `orderId` | string | 是 | 订单号，**必须使用 `ziru_order_list` 返回的 `orderId`**，不可自行拼接或猜测 |
| `businessType` | string | 是 | 业务类型：`flight` / `train` / `hotel`，必须与订单的 `businessType` 一致 |

### 返回

| 字段 | 类型 | 说明 |
|---|---|---|
| `refundLinkUrl` | string | 退票 H5 跳转链接，**以裸 URL 输出**，不要包成 Markdown 超链接 |
| `refundInfo` | string | 说明文案，含订单摘要和失效时间 |
| `expireTime` | string | 链接失效时间 `yyyy-MM-dd HH:mm:ss` |

### 链接格式

| 业务类型 | 退票链接格式 | 改签链接格式 |
|----------|-------------|-------------|
| 机票 | `{前端域名}/#/Air/AirOrderDetail?orderID={orderId}&t={token}` | 同退票链接 |
| 火车票 | `{前端域名}/#/train/order_detail?orderID={orderId}&t={token}` | 同退票链接 |
| 酒店 | `{前端域名}/#/Hotel/OrderDetail?orderID={orderId}&t={token}` | ❌ 不支持改签 |

> 说明：
> - `{前端域名}` 由接口根据运行环境自动返回，无需自行拼接
> - `{token}` 为签名串，`{orderId}` 为订单号
> - 所有业务类型链接都使用 `orderID`（大写 ID），且不含 `businessType` 参数
> - 实际输出时直接使用接口返回的完整 URL

### 失败情形

| message | 含义 |
|---|---|
| `X-Mcp-Key 缺失或无效` | 鉴权失败，提示用户重新填写令牌 |
| `订单号和业务类型不能为空` | 入参缺失 |
| `不支持的业务类型：xxx` | businessType 不是 flight/train/hotel |
| `退票链接生成异常` | 系统异常 |

### 注意

- 链接 **1 小时内有效**
- 生成的是**跳转链接**，不会真正退票，用户点击链接后在 H5 页面完成退票
- 措辞用"已为您生成退票链接"，**禁用"已退票"**

---

## ziru_rebooking_link — 改签链接生成

根据订单号和业务类型生成 H5 改签页跳转链接。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `orderId` | string | 是 | 订单号，**必须使用 `ziru_order_list` 返回的 `orderId`**，不可自行拼接或猜测 |
| `businessType` | string | 是 | 业务类型：`flight` / `train` / `hotel`，必须与订单的 `businessType` 一致 |

### 返回

| 字段 | 类型 | 说明 |
|---|---|---|
| `rebookingLinkUrl` | string | 改签 H5 跳转链接，**以裸 URL 输出**，不要包成 Markdown 超链接 |
| `rebookingInfo` | string | 说明文案，含订单摘要和失效时间 |
| `expireTime` | string | 链接失效时间 `yyyy-MM-dd HH:mm:ss` |

### 链接格式

| 业务类型 | 链接格式 |
|---|---|
| 机票 | `{前端域名}/#/Air/AirOrderDetail?orderID={orderId}&t={token}` |
| 火车票 | `{前端域名}/#/train/order_detail?orderID={orderId}&t={token}` |
| 酒店 | ❌ 不支持改签 |

> 说明：
> - `{前端域名}` 由接口根据运行环境自动返回，无需自行拼接
> - `{token}` 为签名串，`{orderId}` 为订单号
> - 所有业务类型链接都使用 `orderID`（大写 ID），且不含 `businessType` 参数。酒店订单不支持改签
> - 实际输出时直接使用接口返回的完整 URL

### 失败情形

| message | 含义 |
|---|---|
| `X-Mcp-Key 缺失或无效` | 鉴权失败，提示用户重新填写令牌 |
| `订单号和业务类型不能为空` | 入参缺失 |
| `不支持的业务类型：xxx` | businessType 不是 flight/train/hotel |
| `改签链接生成异常` | 系统异常 |

### 注意

- 链接 **1 小时内有效**
- 生成的是**跳转链接**，不会真正改签，用户点击链接后在 H5 页面完成改签
- 措辞用"已为您生成改签链接"，**禁用"已改签"**

---

## 调用示例

### 查询订单列表

```
输入：ziru_order_list(businessType=flight)

返回：
{
  "code": 1,
  "data": {
    "orders": [
      {
        "orderId": "F20260920001",
        "businessType": "flight",
        "businessTypeName": "机票",
        "fromPlace": "北京",
        "toPlace": "上海",
        "departDate": "2026-09-20",
        "status": "出票成功",
        "amount": "680",
        "summary": "MU5100",
        "refundable": true,
        "rebookable": true
      }
    ],
    "totalCount": 1
  }
}
```

### 生成退票链接（机票）

```
输入：ziru_refund_link(orderId=2609211339443380a0123771886, businessType=flight)

返回：
{
  "code": 1,
  "data": {
    "refundLinkUrl": "{前端域名}/#/Air/AirOrderDetail?orderID=2609211339443380a0123771886&t=xxx",
    "refundInfo": "已为您生成退票链接，机票订单 2609211339443380a0123771886。2026-09-20 18:30:00 前有效。",
    "expireTime": "2026-09-20 18:30:00"
  }
}
```

### 生成退票链接（火车票）

```
输入：ziru_refund_link(orderId=T20260919002, businessType=train)

返回：
{
  "code": 1,
  "data": {
    "refundLinkUrl": "{前端域名}/#/train/order_detail?orderID=T20260919002&t=xxx",
    "refundInfo": "已为您生成退票链接，火车票订单 T20260919002。2026-09-20 18:30:00 前有效。",
    "expireTime": "2026-09-20 18:30:00"
  }
}
```

### 生成退票链接（酒店）

```
输入：ziru_refund_link(orderId=2609211340575980h0139410844, businessType=hotel)

返回：
{
  "code": 1,
  "data": {
    "refundLinkUrl": "{前端域名}/#/Hotel/OrderDetail?orderID=2609211340575980h0139410844&t=xxx",
    "refundInfo": "已为您生成退票链接，酒店订单 2609211340575980h0139410844。2026-09-20 18:30:00 前有效。",
    "expireTime": "2026-09-20 18:30:00"
  }
}
```

### 生成改签链接（机票）

```
输入：ziru_rebooking_link(orderId=2609211339443380a0123771886, businessType=flight)

返回：
{
  "code": 1,
  "data": {
    "rebookingLinkUrl": "{前端域名}/#/Air/AirOrderDetail?orderID=2609211339443380a0123771886&t=xxx",
    "rebookingInfo": "已为您生成改签链接，机票订单 2609211339443380a0123771886。2026-09-20 18:30:00 前有效。",
    "expireTime": "2026-09-20 18:30:00"
  }
}
```

### 生成改签链接（火车票）

```
输入：ziru_rebooking_link(orderId=T20260919002, businessType=train)

返回：
{
  "code": 1,
  "data": {
    "rebookingLinkUrl": "{前端域名}/#/train/order_detail?orderID=T20260919002&t=xxx",
    "rebookingInfo": "已为您生成改签链接，火车票订单 T20260919002。2026-09-20 18:30:00 前有效。",
    "expireTime": "2026-09-20 18:30:00"
  }
}
```

> 注意：所有业务类型链接都使用 `orderID`（大写 ID），且不含 `businessType` 参数。酒店订单不支持改签。

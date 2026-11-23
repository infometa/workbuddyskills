# 国内机票免登跳转（字段表）

> 加载时机：国内机票交互页生成「去下单」链接、或要拼国内下单页跳转时。
> 编码、`/oauth2/forward`、`forwardCode`/`infoCode` 见 [`sso-forward.md`](sso-forward.md)，
> 不要在本文件再抄一套。国际字段表见 [`air-intl-sso-forward.md`](air-intl-sso-forward.md)。

## 下单页（已选好舱位）

前端入口固定 `/VuePage/domestic/index.html`，路由 `#/bookingPricing`
（完整落地页如 `https://crmdev.feiheair.com/VuePage/domestic/index.html#/bookingPricing`）。
**跳转前提是已选舱**：单程用户点了某舱位「去下单」，推荐往返组合行自带去/回舱位。
构造函数：`sso_forward.build_domestic_order_route(serial_number, flight_id, cab_id,
adult, pay_type, fly_type, agent, application_id, dh)`（单程/往返页渲染器共用，勿手拼）。

**不要传 `flightList`。** 标识全部在最外层 query。

| 字段 | 必填 | 取值/来源 |
|---|---|---|
| `serialNumber` | ✅ | 同一次 `domestic_shopping` 返回的查询会话标识（往返也只传一个） |
| `flightId` | ✅ | 航段级航班号（如 `JD5639`）；推荐往返取**第一程（去程）** |
| `cabId` | ✅ | 选舱后的舱位 id；推荐往返去/回 cabId 相同，传一个即可 |
| `flyType` | ✅ | `1`=单程，`2`=往返（推荐往返；自选往返不走本页） |
| `adultCount` | ✅ | 查询时 `passengerNum`（一条龙 `--adults`，默认 1） |
| `payType` | ✅ | `1`=公费（与查询 `official=true` 对齐），`0`=自费 |
| `agent` | ✅ | 固定 `1`（agent 内置环境） |
| `applicationId`/`dh` | – | 出差单 id/单号，缺省省略（页面默认空） |

路由示例：

```
/VuePage/domestic/index.html#/bookingPricing?serialNumber=260909003505A0001&flightId=JD5639&cabId=11&flyType=1&adultCount=1&payType=1&agent=1
```

整段路由经 `sso_forward.build_forward_url(route, host, forwardCode)` 包成
`/oauth2/forward?redirectPage=…&authCode=`；
页面 JS 侧 `buildOrderUrl`（单程）/`orderUrl`（往返）与 Python 产出一致。
代购舱位（`source∈2/3/7`）与其他舱位同一条免登 forward 链路，同样生成「去下单」链接；仅用紫色「代购」徽标提示渠道，不要因代购不生成链接。

## 「更多」展开本地舱位（不直调接口）

交互页除前 5 班默认展开外，其余航班卡点「更多」只展开本次 `domestic_shopping` 已返回的舱位
（首屏每班预览前 3 档，可「展开全部」）。**不再**页内直调 `domestic_shopping_by_flight_id`。
退改/行李：shopping 退+改文案齐全则用 CSS 弹层；**退或改任一为空**时「退改签/退改政策」
页内 `fetch` `GET …/busi/air/domestic/rule`，请求头 `X-Auth-Code` = 当次 shopping 的 **infoCode**。
单程页与推荐往返页同一机制。

`infoCode` / `forwardCode` 由 `domestic_shopping` 最外层下发，注入页面 `CFG`；页面不再持有 MCP token。

若 Agent 对话里要单独刷某班全舱，仍可手工调 `domestic_shopping_by_flight_id`
（`serialNumber` + 航段级 `flightList[].flight[].flightId`，如 `CA4322`）。
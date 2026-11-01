---
name: ctrip-biz-travel
description: 携程商旅 MCP 工具使用技能。工具已直接挂载为 MCP 工具，无需脚本、固定 Token 或安装步骤，按本技能的链路与规范直接调用。覆盖国内 / 国际机票推荐与一键下单（travelFlightRecommend、domesticFlightOrderCreate、flightOrderCreate）、酒店推荐与下单（travelHotelRecommend、queryHotelInfo、hotelOrderCreate）、火车推荐与经停（travelTrainRecommend、queryTrainInfo、queryFuzzyQueryStation）、行程规划（queryItineraryRecommendWrap）、差旅政策与酒店差标、用户出行偏好，以及汇率、天气、签证、航班动态、城市 / 国家转 ID。当用户要订机票 / 酒店、查火车、规划出差行程、查差旅政策、查汇率天气签证或航班车次信息时使用。触发词：携程商旅、订机票、订酒店、查火车、出差行程、差旅政策、差标、汇率、天气、签证、航班动态。
---

# 携程商旅 MCP 工具使用

## 概述

携程商旅的 19 个工具已作为 MCP 工具直接提供，由宿主按工具名调用，不需要 Python 脚本、鉴权 Token 或一键安装。本技能规定调用顺序、参数口径和实测踩过的坑。

> **工具名**：不同宿主暴露的名字带不同前缀（例如 `mcp__TripBiz_Journey_Star__queryWeather`）。下文只写不带前缀的短名，调用时按宿主实际暴露的完整名为准。

## 何时使用

- 订机票 / 酒店，或查询可订资源、价格、房型。
- 查火车车次、经停、车站。
- 把一句出差描述变成机票 + 酒店 + 火车的组合方案。
- 查企业差旅政策、酒店差标、用户出行偏好。
- 查汇率、天气、签证、航班动态、城市 ID。

## 工具分类

完整入参、返回字段见 `references/tools_catalog.md`。

| 分类 | 工具 |
| --- | --- |
| 出行辅助 | `queryRegionToId`、`queryFuzzyQueryStation`、`queryFlightInfo`、`queryTrainInfo`、`queryWeather`、`queryExchangeRate`、`queryVisaInfo` |
| 资源推荐（只查不下单） | `travelFlightRecommend`、`travelHotelRecommend`、`travelTrainRecommend` |
| 酒店信息 | `queryHotelInfo`、`queryHotelTravelPolicy` |
| 政策 / 行程 / 偏好 | `queryGeneralTravelPolicyInfo`、`queryItineraryRecommendWrap`、`queryLongTermInterest` |
| 下单（真实提交） | `domesticFlightOrderCreate`（国内机票）、`flightOrderCreate`（国际机票）、`hotelOrderCreate`（酒店）、`createOrder`（出票创单，分销场景） |

## 典型链路

先推荐拿候选，再让用户确认，最后下单，下单后把订单号与状态反馈给用户。参数示例见 `references/workflows.md`。

```text
订机票   queryRegionToId → travelFlightRecommend → 用户确认 → domesticFlightOrderCreate / flightOrderCreate
订酒店   queryRegionToId → travelHotelRecommend（或 queryHotelInfo）→ 用户确认 → hotelOrderCreate
查火车   queryFuzzyQueryStation → travelTrainRecommend → queryTrainInfo
行程规划 queryItineraryRecommendWrap（自然语言需求，可带审批单号）
信息查询 queryWeather / queryExchangeRate / queryVisaInfo / queryFlightInfo
```

## 使用规范

1. **下单前必须得到用户明确确认**。`domesticFlightOrderCreate`、`flightOrderCreate`、`hotelOrderCreate`、`createOrder` 都会真实提交订单。确认内容至少包含航班或酒店、日期、乘机人 / 入住人和价格。用户只是询问或比价时，只调用推荐类和查询类工具。
2. **乘机人 / 入住人证件信息**：必须由用户提供或明确授权使用，不得内置默认值。证件号、手机号在对话和交付物中掩码展示，也不要写入日志、文件或记忆。
3. **城市先转 ID**：推荐类工具的 `departAddress` / `travelAddress` 必须带 `cityId` 和 `countryId`，先用 `queryRegionToId` 查，不要凭记忆填。
4. **日期**：统一 `yyyy-MM-dd`。`requestId` 在推荐类工具中必填，传新生成的 UUID。
5. **下单依赖推荐结果**：国内机票用推荐返回的 `productId`；国际机票用推荐返回的 `flightNo`；酒店用房态返回的 `productId`。不要自行构造。
6. **变价**：下单类默认 `rejectPriceChange=true`，价格变动会拒绝下单，应把新价格告知用户后再决定是否重试。
7. **只按返回事实回答**：推荐结果里没有的字段（舱位、退改规则等）不要编造；`responseCode` 不是 20000 时，如实转述 `responseMsg` / `responseDesc`。

## 关键坑位

- `responseCode` 在不同工具里类型不同：推荐类是数字 `20000`，查询类是字符串 `"20000"`，比较时统一转成字符串。
- `queryFlightInfo` / `queryTrainInfo` 只按航班号 / 车次号查，不能指定日期，返回的是查询当天的日期。号码大小写不敏感。
- `queryFuzzyQueryStation` 只返回匹配的第一条车站，如“虹桥”得到上海虹桥 `AOH`；有歧义时让用户补充。
- `queryWeather` 的 `dateDay` 是“10月23日”这类展示文案，不带年份；多城市用英文逗号分隔。
- `queryExchangeRate` 返回 `CentralParity`（中间价）、`Spotin`（现汇买入）、`Spotout`（现汇卖出）三条，汇率含义是 1 单位基准货币兑换多少计价货币，展示时说明用的是哪一种。
- 国际机票的 `departureCityCode` / `arrivalCityCode` 是**城市三字码**（上海 `SHA`、北京 `BJS`），不是机场码（浦东 `PVG`）。
- `queryHotelInfo` 需要传 `language`；`travelHotelRecommend` 需要传 `travelDateEnd`；国际航线乘机人姓名用 `姓/名` 拼音格式，`birthDay` 用 `yyyy-MM-dd HH:mm:ss`；廉航在商旅渠道可能搜不到。

## 故障排查

- 工具不可用或超时：确认宿主已连接携程商旅 MCP ；瞬时错误可重试一次。
- 下单重试后提示重复订单：说明前一次可能已成功，不要再次提交，让用户到携程商旅 App 核对订单。
- 参数校验类错误：对照必填项修正。
- 推荐结果为空：先放宽条件（日期、价格、星级）

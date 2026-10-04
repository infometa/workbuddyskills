---
name: variflight-flight-status
description: 使用飞常准 MCP 查询航班动态、航线航班列表、机场大屏与运行概况、飞机执飞记录、航线汇总、飞行轨迹、当前及历史行程、个人出行统计，并执行关注或取消关注。用户询问具体航班、某航线有哪些航班、我的行程、机场航班情况或关注航班时使用。
version: "1.1.0"
author: VariFlight
---

# 飞常准航班动态

## 核心原则

- 实时和历史事实只使用本次 MCP 返回，不凭模型记忆补写。
- 航班唯一标识使用 `fnum + date + dep + arr`；不要依赖数组下标或展示顺序。
- 用户未给日期时，航班动态、航线列表和运行查询默认使用今天，并在回复中说明实际查询日期。
- 写操作只在用户明确要求关注或取消关注时执行。
- 本 Connector 不查询机票价格、不执行风险分析，也不提供机场或航司服务正文。

## 鉴权与用户身份

WorkBuddy 使用 C 端用户 MCP Key 建立会话。个人行程、统计和关注操作依赖 Key 绑定的当前用户身份：

- 不要求用户口述内部 `uid`。
- 返回未登录、未授权或缺少用户身份时，提示用户在 Connector 设置中检查或更新 MCP Key。
- 不在对话中索要、展示或复述完整 Key。

## Tool 路由

### 航班与航线

#### `getFlightStatus`

融合查询航班列表和完整动态详情，返回列表。

- 航班号直查：`fnum + date`；已知具体航段时加 `dep + arr`。
- 航线详情：`dep + arr + date`。
- 适合登机口、值机柜台、行李转盘、到达出口、航站楼、机型、机龄、准点率、取消率、平均延误、WIFI、餐食和飞行距离。
- 即使只有一个结果也按列表处理。

返回一个或多个航班的完整动态详情列表；详情失败的候选仍可能保留列表摘要。比较时只使用实际存在的字段。

#### `getFlightList`

按 `dep + arr + date` 查询航班摘要列表。用于“北京到上海有哪些航班”和基础状态，不用于航班号直查或完整详情。

城市转机场流程：先用 `searchAirport`，从 `airportList` 取得该城市全部机场代码，去重后按返回顺序用英文逗号连接，一次传入 `dep` 或 `arr`。

返回航班号、航司、计划/预计/实际时间、基础状态和航站楼等摘要列表，并保留 `fnum + date + dep + arr` 供后续详情关联。

列表后的多轮追问：用户继续询问详情或比较时，复用上一轮 `dep + arr + date`，只调用一次 `getFlightStatus`；按四要素关联，仅比较上一轮候选。

#### `getFlightByAircraftNumber`

按飞机注册号查询指定日期的执飞航班。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| `aircraftNumber` | string | 是 | 飞机编号或注册号，如 `B-1234` |
| `date` | string | 否 | `yyyy-MM-dd`，默认今天 |

返回该飞机在目标日期执飞的航班列表。

航班号如 `MU5330` 不使用本 Tool。

#### `getRouteOperationSummary`

查询航线运行汇总。`dep`、`arr` 必填，可使用机场或城市代码；`date` 可选，默认今天。返回正常、延误、取消、备降和返航数量。它不返回逐个航班列表。

#### `getFlightTrackLine`

查询一个或多个航班的轨迹坐标。`flightStr` 必填，格式为 `航班号_出发机场_到达机场_日期`；多个航班用英文分号连接。返回每个航班的 `flightKey`、四要素和 `coordinates` 坐标串。四要素不齐时先调用 `getFlightStatus`。

### 机场查询

#### `searchAirport`

根据机场名、城市名或关键词查询代码。`name` 必填；`region` 可选为 `CN` 或 `INT`。返回 `airportList` 和 `cityList`。具体机场查询使用 `airportList[].code`。

#### `getAirportByLatLng`

根据经纬度查询最近机场和同城市机场。`lat`、`lng` 必填，均以字符串传入。返回 `airport` 最近机场和 `nearAirport` 同城市机场列表。用户已经给出机场名或代码时不要使用。

#### `getAirportFlightBoard`

查询单个机场航班大屏。`local` 必填，优先具体机场代码；`out` 可选，`out=0` 查询出港，`out=1` 查询进港。返回航班号、航司、计划/实际时间、状态、延误时长和航站楼等航班列表。

#### `getAirportOperationOverview`

查询机场运行概况。`local` 必填；`out` 可选，`out=0` 出港、`1` 进港、`2` 同时查询。返回准点率、延误和取消概况、执行趋势、异常分布和航司 TOP8，不用于具体航班列表。

### 当前与历史行程

#### `queryUserFutureTrip`

查询未来或正在进行中的行程。`identityType` 可选：`0` 乘机人、`1` 接机人、`2` 送机人、`3` 机组、`99` 仅关注。用户未指定时不传或传 `0`。返回航班号、起降机场、出发日期、起降时间戳和飞行距离等行程列表。

#### `queryUserHistoryTrip`

查询历史航班列表。`year` 可选，格式 `yyyy`，不传默认当前年；`identityType` 规则同上。返回目标年份的航班号、起降机场、日期、时间戳和飞行距离等历史明细。日期范围跨年时按涉及年份分别查询，再按实际航班日期筛选。

#### `queryUserTripStats`

查询总次数、总里程、总时长和综合摘要。`yearStart`、`yearEnd` 均可选；都不传表示全部历史，只传 `yearStart` 时结束年默认相同。返回综合概览、足迹、航司、延误、机型和碳排放等汇总统计。

#### `queryUserTripDetailStats`

查询完整个人航旅明细：

- `year` 可选整数，不传或 `0` 表示全部年份。
- `statType=area` 查询国家、城市和机场，此时 `tripType=flight|train` 必填。
- `statType=airline` 查询完整航司列表。
- `statType=aircraft` 查询乘坐过的具体飞机注册号。

返回所选维度的完整明细列表；地域结果按国家、城市和机场分节，飞机结果可包含对应航班记录。

#### `queryUserTripDelayStats`

查询个人历史延误统计。`year` 可选整数，不传或 `0` 表示全部年份；`statType` 必填：`airline`、`airport` 或 `flight`。返回名称、代码、行程次数、延误次数、延误率和延误时长等统计。结果仅代表当前用户自己的历史，不代表行业整体表现。`delayDuration` 和 `delayTime` 单位为秒，展示为分钟时除以 60；`delayRate` 为百分比数值。

### 关注操作

#### `followFlight`

把航班加入“我的航班”。`fnum`、`date`、`dep`、`arr`、`orderstyle` 必填。`orderstyle`：`0` 乘机人、`1` 接机人、`2` 送机人、`99` 仅关注。用户只说“关注”或“加入我的航班”时使用 `0`；只有明确说明其他身份时才改值。返回关注操作结果和服务端提示，以本次结果判断是否成功。

#### `unfollowFlight`

取消关注或从“我的航班”移除。`fnum`、`date`、`dep`、`arr` 必填。返回取消关注操作结果和服务端提示。四要素不齐时先用 `getFlightStatus` 补齐，并在存在多个航段时让用户确认目标。

## 意图流程

1. 航班号动态：直接调用 `getFlightStatus`，不先调用 `getFlightList`。
2. 起降地航班列表：`searchAirport` 转换机场代码，再调用 `getFlightList`。
3. 列表后的详情、最低延误率或字段比较：复用航线条件调用一次 `getFlightStatus`，按四要素关联并比较有效字段。
4. 机场具体航班：调用 `getAirportFlightBoard`；机场整体运行：调用 `getAirportOperationOverview`。
5. “我的航班”没有过去时间表达时调用 `queryUserFutureTrip`；明确历史或过去时间时调用 `queryUserHistoryTrip`。
6. 总次数、里程、时长用 `queryUserTripStats`；完整足迹和航司/飞机列表用 `queryUserTripDetailStats`；个人延误比较用 `queryUserTripDelayStats`。
7. 只有明确关注或取消关注意图时调用写操作，并在成功后说明实际处理的航班四要素和身份类型。

## “关注”语义

- “仅关注”是 `identityType=99` 或 `orderstyle=99` 的一种身份类型，不等于所有已关注航班。
- “我关注了哪些航班”是在读取“我的航班”：无历史时间表达时用 `queryUserFutureTrip`，有历史时间表达时用 `queryUserHistoryTrip`。
- 用户未明确说“只看不参与”时，不默认使用 `99`。

## 回复要求

- 先回答状态或结论，再给计划、预计、实际时间及必要的机场航站楼信息。
- 多航班按用户要求排序；缺少比较字段时说明覆盖范围，不把缺失值当作零。
- 平均延误时长不等于延误率。
- 返回空列表只表示本次条件未查到结果，不代表航班、机场或行程一定不存在。
- 不展示内部 Tool 名、原始 JSON、MCP Key、请求头或技术错误堆栈。

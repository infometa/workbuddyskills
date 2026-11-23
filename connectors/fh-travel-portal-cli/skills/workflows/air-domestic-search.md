# 国内机票查询与筛选

> 加载时机：用户要查、比、筛国内航班时。出页契约 [`../references/air-domestic-oneway-page.md`](../references/air-domestic-oneway-page.md)。
> 本文件只覆盖查询、筛选、单程分析页与选舱。当前服务端只暴露只读查询；验价、差标、创单
> 均未开放——用户表露预订意图时，页面「去下单」走免登 forward 跳 portal 下单页（字段见
> [`../references/air-domestic-sso-forward.md`](../references/air-domestic-sso-forward.md)，编码见
> [`../references/sso-forward.md`](../references/sso-forward.md)）。不得声称已预订，不得调用
> 已下线写工具。字段对不上再读
> [`../references/air-domestic-shopping-schema.md`](../references/air-domestic-shopping-schema.md)。
> 出页对照 [`../references/air-domestic-oneway-page.md`](../references/air-domestic-oneway-page.md)「默认页能力摘要」，
> 不要打开 `assets/air-domestic-oneway-page.html` 或 `assets/air-domestic-roundtrip-page.html`。出页不要改 HTML。

本篇工具：`air_city`（`scope=DOMESTIC`）、`domestic_airline_resolve`、`domestic_shopping`、
`domestic_shopping_by_flight_id`。用户追问退改/舱位服务/经停时再用已启用的
`domestic_rule`、`domestic_cabin_service`、`domestic_flight_stop`。

每次调用 `domestic_shopping`（含改条件后的重查）都必须在 `searchParams` 里同时带
`official=true`、`sortBy=DEPARTURE_TIME`、`withCabinRules=true`、`needRefundChangeRule=false`
（schema 标可选也要传；`needRefundChangeRule` 须显式 false，不传则 Java 仍会开退改）。

不要调用已停用的 `domestic_city` / `domestic_city_resolve`，也不要调用 `domestic_verify_price`、
差标/申请单、购物车、`find_passenger`。分析页退改以页内 `domestic_rule` 补查为准
（shopping 默认不带 `rule.*` 文案）。

## 最低查询要件

查询前只需要出发地、到达地和出发日期。缺少时用一句自然中文一次问齐缺项；不输出
Skill 名、工具名、参数表或推理过程。人数未说默认 1；没有返程含义时默认单程，不追问
“单程还是往返”。普通往返缺返程日期时只问返程日期，不查半截往返。

完整公历日期归一化为 `yyyy-MM-dd`。相对时间（今天/明天/后天）按本机当前日期换算，不能可靠确定时只追问日期。城市码不确定时调用 `air_city`（`scope=DOMESTIC`，`keyword` 传用户说的
城市或机场名）。从候选取 `code`，禁止凭记忆猜码或把三字码改写成聚合码：

- 若本轮返回里**真有**聚合码（如 `CTU1`/`BJS1`），优先用它查 `domestic_shopping`，才能带出该城市全部机场，页面「机场分布」才完整。
- 若只有三字码（如 `CTU`/`PEK`/`XNN`），**原样使用**。当前国内 `air_city` 常见就是这种，`aggregate` 多为 false。
- 行上带 `nearAirport=true` 时，用返回的邻近机场码。

用户指定或排除航司且二字码未知：`domestic_airline_resolve`，把 `companyNo` 填进
`airline` 或 `excludeAirlineCodes`。已有可信三字码且无歧义时直接 shopping。

## 行程模式

| 模式 | 判定 | 查询参数 |
|---|---|---|
| 单程 | 一段且无返程含义 | `journeyType=0`，`airLegs` 1 项 |
| 推荐往返 | 两段互反，未要求分开选择 | `journeyType=1`，`airLegs` 2 项，第 2 项起终点与第 1 项互换 |
| 自选往返首段 | 用户明确分别选去回程 | 首次仅按去程单程查询；后续预订逻辑不在本文件 |

出页分两套：**单程**用 `air_domestic_oneway_render_page.py`（单程结果 `flightList[].flight` 每段可含
多舱位，「卡片 + 展开舱位表」形态）；**推荐往返**用 `air_domestic_roundtrip_render_page.py`
（往返结果每个 flightList 行已是「去程舱位×返程舱位」固定组合，无展开，行数可达数千，
每行即一组合）。往返出页契约见 [`../references/air-domestic-roundtrip-page.md`](../references/air-domestic-roundtrip-page.md)。
不要把 `journeyType=1` 的结果丢给单程脚本，也不要用编号列表降级。

先扫描用户整条消息再判定模式，不能读到第一段就忽略后续航段。国内非互反多程不属于
本查询预订能力，说明边界，不拼成多个单程订单。

`airLegs` 每项：`fromCity`、`toCity`、`flyDate`（`yyyy-MM-dd`）；可选 `airIdList`（航司二字码）。

## 首次查询

先读本轮要用的工具的 input schema（`air_city`、`domestic_shopping`），再调用；不要凭记忆
用 `domestic_city` / `domestic_city_resolve`。槽位和代码齐全后直接 `domestic_shopping`，
不要再问“是否开始查询”。`searchParams` 必须同时带 `official=true`、`sortBy=DEPARTURE_TIME`、
`withCabinRules=true`、`needRefundChangeRule=false`（四者 schema 标可选也要传）。用户本轮
筛选项一次传齐。`air_city` 返回的 `code` 原样填 `fromCity`/`toCity`，不要因 `aggregate`
与预期不符而改写成三字码。

**所有行程与筛选字段都放在入参的 `searchParams` 对象里**（形如
`{"searchParams":{"official":true,"sortBy":"DEPARTURE_TIME","journeyType":0,"airLegs":[...],...}}`）：

| 用户表达 | 字段 |
|---|---|
| 上午/下午/晚上 | `departureDayPart` |
| 明确起止时刻 | `fromTime`、`toTime`；与 `departureDayPart` 互斥 |
| 指定/排除航司 | `airline`、`excludeAirlineCodes`；航司码须权威解析 |
| 直飞 | `nonStop=true` |
| 最便宜一班 | `cheapest=true`，不等同于仅设置价格排序 |
| 指定机场 | `depAirport`、`arrAirport` |
| 托运行李/餐食 | `hasBaggage`、`hasMeal` |
| 人数 | `passengerNum` |
| 舱等 | `searchParams.cabClass` |

查询返回的 `serialNumber/flightId/cabId` 在 `structuredContent` 业务载荷中（拆封见
`references/mcp-envelope.md`），属于本次结果世代；新查询后旧标识和旧页面选择全部作废。
禁止凭记忆编造航班。信封 `summary` 为指引句，不要把指引句当航班数据。

行程组 `flightList[].flightId` 实测常为**空串**；航段级 `flightList[].flight[].flightId`
才是航班号本身（如 `CZ3101`）。要看某班全部舱位时，`domestic_shopping_by_flight_id`
传 **航段级 `flight[].flightId`（航班号）**，与 `serialNumber` 成对、来自同一次 shopping
（2026-09-04 实测：`flightId=CA4322` 1.1s 返回 18 舱位含退改；传组级空串不行）。

## 标准链路：一条龙（唯一标准路径）

槽位齐全后（出发地/到达地/日期，人数默认 1，无返程含义默认单程），**只跑一条龙**，
不要宿主侧 `mcp__…__domestic_shopping` / ToolSearch：

```text
python -u scripts/air_domestic_query.py --from 北京 --to 上海 --date 2026-09-15
```

跑完读 stdout；空则读 `fh-last-task-id.txt` 再读 `~/.fh-travel-workspace/fh-travel-runs/<run-id>/run_summary.json`，present_files 打开其中 `html`。
往返加 `--return <日期>`。没有 `run_summary.json` 或 html 就把同一条查询再跑一次（不要带旧 `--run-id`）。

内部串联：`air_domestic_resolve_city.py`（本地缓存，未命中自动 `air_city`）→
`fh_travel` 调 `domestic_shopping`（`official=true`、`sortBy=DEPARTURE_TIME`、`withCabinRules=true`、
`needRefundChangeRule=false`）→ 出页。完成后 present_files 首位放 HTML。
失败则整段重跑一条龙（不要带旧 `--run-id`）
（401/退出码 3 先 `fh auth status` 并按 `references/cli-connection.md` 处理），不要改走宿主手调 shopping。

- **单程**：`journeyType=0` + `withCabinRules=true` + `needRefundChangeRule=false` →
  `air_domestic_oneway_render_page.py`
  （前 5 班默认展开舱位、每舱位「去下单」免登 forward、其余航班点「更多」展开本次 shopping 已返回的舱位）。
- **推荐往返（`--return`）**：**一次** `journeyType=1` 查询（airLegs 两项互反，同样传
  `withCabinRules=true` + `needRefundChangeRule=false`）→
  `air_domestic_roundtrip_render_page.py` 出往返组合页（每行=去×回舱位固定组合）。
  **严禁用两次单程查询代替推荐往返**——两次单程价相加 ≠ 往返组合价，价格语义不同。

`withCabinRules=true` 与 `needRefundChangeRule=false` 为国内 shopping **必传**：
shopping 不带退改文案，出页点「退改签/退改政策」走页内 `domestic_rule` 补查。
列表展示由出页脚本做 **JS 本地分页**（筛/排仍对完整结果）。

## 筛选还是重查

| 变化 | 动作 |
|---|---|
| 只在当前完整结果内排序或收窄 | 优先由交互页面页内处理，不声称重新查询库存 |
| 改城市、日期、人数、行程模式、舱等或需要服务端重新判断的条件 | 重新调用 `domestic_shopping`（仍须 `official=true`、`sortBy=DEPARTURE_TIME`、`withCabinRules=true`、`needRefundChangeRule=false`），创建新世代 |
| 已有列表后指定航班号或“第 N 个” | 从本轮 `domestic_shopping` 结果取行程组 `flightId`，不是筛选，也不重查 |

“再加上/并且”保留仍有效旧条件并增量添加；“重新筛选”只应用本轮重新声明的条件，不暗中
继承旧航司、时段或价格。`flightList` 为空只能表述为“当前条件无匹配”，不能说成“当天没有航班”
（改条件应重新调用 `domestic_shopping`，不要假定还有未展示的全量列表）。

## 结果呈现

**单程**用 `scripts/air_domestic_oneway_render_page.py` 出页。能力以
[`../references/air-domestic-oneway-page.md`](../references/air-domestic-oneway-page.md)「默认页能力摘要」为准。
**推荐往返**用 `scripts/air_domestic_roundtrip_render_page.py` 出页，能力以
[`../references/air-domestic-roundtrip-page.md`](../references/air-domestic-roundtrip-page.md) 为准，
不要走单程脚本（见上文行程模式）。

1. shopping 成功后立刻把**本轮返回**交给脚本出页。脚本自己拆信封、自己做结构自检。
   汇报用它打印的统计，不要另写 python 抽源 JSON。
2. 返回通常很大：**禁止整份贴进对话、禁止让模型通读源 JSON**。这是唯一禁令。
   交给脚本的两种方式都合法：
   - 仍把工具返回内联给你：`src` 用 `-`（stdin）。
   - 因查询结果太大，直接给大模型超 token ，所以把本轮结果落盘：把**本轮那个文件路径**当作 `src`。这是预期路径，不是绕过。
   禁止去 skill 目录、历史会话或工作区里**搜索/猜测**别的结果文件。
3. 单程命令（城市码/日期以你掌握的为准；`<src>` 为本轮返回：`-` 或落盘文件路径）：

```bash
python3 scripts/air_domestic_oneway_render_page.py <src> \
  --from-city "<出发城市名>" --to-city "<到达城市名>" \
  --from-code "<出发城市码>" --to-code "<到达城市码>" \
  --date "<YYYY-MM-DD>" --date-text "<YYYY-MM-DD(周X)>" \
  --full-note --out "<输出.html>"
```

   推荐往返命令（`--go-date/--ret-date` 缺省时脚本从数据自动取）：

```bash
python3 scripts/air_domestic_roundtrip_render_page.py <src> \
  --from-city "<出发城市名>" --to-city "<到达城市名>" \
  --go-date "<YYYY-MM-DD>" --ret-date "<YYYY-MM-DD>" \
  --full-note --out "<输出.html>"
```

4. 脚本成功即可 `present_files` 打开本地 HTML 路径。禁止 `http.server`、任何端口、系统浏览器。
   不要打开 HTML 搜标记，不要跑 `node --check`。

查询出页只做精简校验（不要每次跑 `node --check` 或剥脚本结构检查，那些只在改模板时做）：
- 生成物无 `{{XXX}}` 残留，且包含关键结构：`details.card`（航班卡）、舱位表行（7 列）、协议价标签 `.tag-ent`（在等级列内）、
  退改/行李列（每行 `.cab-link` 退改签、有文本则加行李链接）、`btn-book` 去下单链接、`window.__syncOpenLazy`（展开自动拉舱）。
- 脚本打印的航班数/舱位数与源数据大体一致；因公查询时协议舱应大于 0。

无硬约束用浏览模式比时间和价格；有时段/直飞/航司等硬约束时先展示命中，再给可放宽方向。
不得编造准点率、行李、退改或政策。对话不超过两句摘要 + 关键指标（markdown 表，内容克制）。
宿主不支持 HTML 时降级为编号列表。用户点「去下单」即经免登 forward 跳 portal 下单页
（字段见 [`../references/air-domestic-sso-forward.md`](../references/air-domestic-sso-forward.md)），
支付/出票在 portal 完成，不得声称已下单。

## 选定航班后：刷新舱位与规则

分析页点「更多」已展示本次 shopping 的舱位，一般不必再调 MCP。
若用户明确要求**刷新**该班实时可售舱位：

1. 用 `domestic_shopping_by_flight_id`：参数为 `serialNumber` + **航段级 `flight[].flightId`
   （航班号）**（均来自同一次 `domestic_shopping`；行程组级 `flightId` 常为不可用的空串），
   往返传 `toFlightId`。
2. 刷新结果不要丢给 `air_domestic_oneway_render_page.py`（该脚本吃的是 shopping 列表形态）；用对话
   展示真实返回的舱位，或说明以分析页已展开的舱位为准。
3. 用户问退改/行李/服务时：分析页已有 shopping 内 `rule.refundText/changeText` 则先用页面
   数据；退或改文案任一为空时用户点「退改签/退改政策」会**页内直调** `domestic_rule`
   （与国际「查舱位」同形态）。对话里仍可
   直接调 `domestic_rule`（舱位标识取自本轮结果），舱位服务调
   `domestic_cabin_service`，经停调 `domestic_flight_stop`。不得按航司或舱等推断。

**流程到此为止。** 不得尝试调用已下线的写工具，不得伪造预订结果。

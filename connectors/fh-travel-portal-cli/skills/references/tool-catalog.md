# 工具目录（fh `dev call` 的 op）

> 加载时机：需要确认工具名称、能力边界或写操作等级时。具体参数与 Schema 以运行时
> `fh dev tools` / `tools/list` 为最终真源。不在目录里的名字不要调用。
> 这些 op 经 `fh` 调用，名字与门户 MCP tools/list 一致。

## 返回信封（全部工具统一）

所有工具的 `tools/call` **同一条出站路径**（握手 instructions 同一契约）：

- **成功**：业务只在 `structuredContent`，就是 JSON 对象，直接读。信封为
  `hasMore=true` + `summary` 指引（业务不在 content；outputSchema 去 `tools/list`，**可能没有**），
  不重复 schema 原文、不嵌业务。
- **失败**：`ok=false` + `error.message`，协议层 `isError=true`；分流见 `error-handling.md`。
- 解封用 `scripts/unwrap_content.py`（读 `structuredContent`）；
  国内/国际出页脚本会自动拆。机票结果很大，**不要整份读进对话**。

## Canonical inventory（12，仅已启用）

<!-- TOOL_INVENTORY_START -->
- `air_city`
- `domestic_airline_resolve`
- `domestic_cabin_service`
- `domestic_flight_stop`
- `domestic_rule`
- `domestic_shopping`
- `domestic_shopping_by_flight_id`
- `intl_multi_shopping`
- `intl_nationality`
- `intl_rule`
- `intl_shopping`
- `intl_shopping_all_cab`
<!-- TOOL_INVENTORY_END -->

**当前 12 个已启用工具全部为只读查询。** 核价、购物车、创单、支付、出票、退改签提交等
写链路工具均未暴露；任何预订/下单动作只能通过 portal 免登跳转完成（见
`sso-forward.md`；国际字段表 `air-intl-sso-forward.md`），不得尝试调用已下线的写工具。
调用范围以本目录与 `SKILL.md` 路由为准；未列入本目录的名字不要调用。

## 公共（1）

| 能力 | 工具 | 操作等级 |
|---|---|---|
| 机票城市/机场码关键词检索 | `air_city` | 只读 |

- `air_city`：国内与国际不是同一套码，`scope` 必须显式传 `DOMESTIC` 或 `INTERNATIONAL`，
  禁止 `AUTO`。仅在代码未知、有歧义或已缓存代码被接口拒绝时调用；空数组表示无匹配，
  换更短关键词或改中英文重试，禁止编造代码。
  - **DOMESTIC**：返回机场三字码（如 `PEK`/`SZX`），供 `domestic_shopping`；`aggregate`
    一般为 false。无机场城市可能带 `nearAirport=true`。
  - **INTERNATIONAL**：候选取 `code` 填 `intl_shopping` 的 `fromCity/toCity`。
    `aggregate=true`（如 `BJS1`）时 `isFromCity/isToCity` 传 true，下属机场见 `cityCodeList`；
    `aggregate=false` 时标志传 false。国际行可能仍带遗留字段 `cityCode`（与 `code` 同值），
    下游只用 `code`。
  - 每项还含 `scope`、`cityName`、`airPort`；可选 `limit`（默认 10，最大 20）。

## 国内机票（6）

| 能力 | 工具 | 操作等级 |
|---|---|---|
| 航班查询（单程/往返）、按航班刷新全舱 | `domestic_shopping`、`domestic_shopping_by_flight_id` | 只读 |
| 航司二字码关键词解析 | `domestic_airline_resolve` | 只读 |
| 已选舱位退改签规则 | `domestic_rule` | 只读 |
| 舱位服务说明、航班经停详情 | `domestic_cabin_service`、`domestic_flight_stop` | 只读 |

国内城市/机场码一律走公共 `air_city`（`scope=DOMESTIC`）。企业配置、乘机人查询、验价、政策/申请单
校验、创单、支付与退改签能力当前均未在 MCP 暴露；查询、筛选、比较之外的预订动作只能
引导用户走 portal 完成（见 `sso-forward.md`；国际字段见 `air-intl-sso-forward.md`）。

## 国际机票（5）

| 能力 | 工具 | 操作等级 |
|---|---|---|
| 推荐组合、多程/自由组合、全舱 | `intl_shopping`、`intl_multi_shopping`、`intl_shopping_all_cab` | 只读 |
| 已选运价退改/行李规则 | `intl_rule` | 只读 |
| 国籍与证件签发国代码检索 | `intl_nationality` | 只读 |

> `intl_shopping_all_cab` 入参铁律（实测 2026-09-03 确认）：`serialNumber` 与 `priceId`
> 必须来自**同一次** `intl_shopping` 结果的配对值；`priceId` 是 `priceList[].priceId`
> （三段式 `x/y/n` 或逗号式），**不是 `groupId` 也不是 `pricingId`**。用旧 serialNumber
> 调用会报「航班数据已过期」——serialNumber 时效性短，选舱位前必须先拿到新鲜值。

国际城市码解析已并入公共 `air_city`（`scope=INTERNATIONAL`）。`intl_nationality` 只用于
国籍/证件签发国代码，**不是**航班查询前置；当前创单未暴露，用户未问证件时不必调用。
国际验价与创单能力当前未在 MCP 暴露，不能在本 MCP 内核价或创单；用户选定航班后按
`sso-forward.md` 包装 + `air-intl-sso-forward.md` 字段表拼下单页跳转 URL（只需 `serialNumber` + 舱位 `priceId`，不经过验价）。
进入国际政策或创单话题前仍必须先读 `air-intl-capability-gap.md`，不得把未暴露的能力写成已经完成。

## 统一来源纪律

- 身份字段省略时由服务端按当前登录态解析；只能传权威结果，不得猜 `clientId/userId/applicationId`。
- `serialNumber` 与其 `priceId` 必须来自同一次 shopping；`pricingId` 只能来自真实验价结果
  ——当前验价能力未暴露，任何场景都拿不到真实 pricingId，禁止用查询 priceId 冒充。
- `serialNumber` 时效性短（同一查询会话标识，跨天/重查即失效），选舱位/下单跳转必须用
  **当次** `intl_shopping` 的新鲜值，禁止复用旧结果里的 serialNumber。
- `intl_shopping_all_cab` 的查询 `priceId` 取 `priceList[].priceId`（非 groupId），下单页
  跳转的 `priceId` 取 all_cab 返回的**舱位级三段式** priceId（非查询 priceId），两级
  priceId 语义不同，勿混用。
- `tools/call` 失败信封（`ok=false`）或 JSON-RPC error 均视为失败，不得从失败
  响应推导业务事实。读法见 `mcp-envelope.md`。

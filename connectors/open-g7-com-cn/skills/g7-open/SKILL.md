---
name: g7-open-platform
display_name: G7易流平台数据查询
display_name_en: G7 Open Platform Data Query
description: "通过 G7 易流开发者平台查询车辆、司机、位置轨迹、IoT 状态、安全事件、场站围栏等业务数据的用法说明"
description_zh: "G7 易流开发者平台只读数据查询技能，覆盖车辆档案、司机与司车分配、位置与行程、IoT 实时与历史数据、安全事件、场站围栏地址、标签资质与天气。"
description_en: "Read-only data query skill for the G7 Yiliu open platform, covering vehicles, drivers, trips, IoT telemetry, safety events, geofences and weather."
version: 1.1.0
author: G7易流
allowed-tools: search_platform_apis, describe_platform_api, query_platform_api
examples_zh:
  - "查一下公司有哪些车辆，列前 10 辆"
  - "川A99999 现在在哪，速度多少"
  - "查昨天的超速事件"
  - "统计这周每辆车的行驶里程"
examples_en:
  - "List the first 10 vehicles in my company"
  - "Where is 川A99999 now and how fast is it going?"
  - "Show yesterday's speeding events"
  - "Summarize each vehicle's mileage this week"
---

# G7易流开发者平台 · 数据查询

把 G7 易流开发者平台的 **接口** 收敛成 3 个工具，全部 **只读**：车辆、挂车、司机、位置与行程、IoT、安全事件、场站/地址/围栏/天气、标签与自定义字段、资质。

**不能创建、修改、删除任何数据。** 写操作接口只能被检索到（`intent: DISCOVERY_ONLY`），不能执行。

## 三个工具与调用顺序

| 工具 | 作用 |
|---|---|
| `search_platform_apis` | 关键词检索接口，拿 `operation_id` |
| `describe_platform_api` | 取该接口的精确 `input_schema`、分页方式、错误码 |
| `query_platform_api` | 执行只读查询 |

```
search_platform_apis(query="车辆") → describe_platform_api(operation_id="SearchVehicles")
                                   → query_platform_api(operation_id="SearchVehicles", arguments={...})
```

三条硬规则：

1. **不猜 `operation_id`**。命名不统一：`SearchVehicles`（大驼峰）、`getVehicle`、`getEventsFeed`、`searchHistoricalEvents`（小驼峰）。猜错返回 `api_not_found`。
2. **不跳过 describe 直接 query**。`input_schema` 是 `additionalProperties: false`，多传一个字段就被拒。
3. 同一会话 describe 过的接口可直接 query；`schema_version` 变了则以新说明为准。

## 参数形态

以 describe 返回的 `input_schema` 为准，但两种形态先记住：

| 接口形态 | `arguments` |
|---|---|
| `POST /xxx/_search`（列表检索） | 业务参数全部包在 `body` 里：`{"body": {"pagination": {"limit": 5}}}` |
| `GET /xxx`（详情/快照/增量） | 平铺在顶层：`{"id": "123", "include_real_time": true}` |

## 分页与截断

describe 的 `pagination` 告诉你翻页方式：

| `style` | 取下一页 |
|---|---|
| `body_cursor` | `{"body": {"pagination": {"cursor": "<next_cursor>", "limit": 20}}}` |
| `query_cursor` | `{"cursor": "<end_cursor>", "limit": 20}` |
| `none` | 不支持分页 |

- **`limit` 传大了不会报错**，会被静默压到上限。响应里的 `_budget` 给出真相：`{"truncated": bool, "applied_limit": 20}`。**以 `applied_limit` 为准，不要以为自己拿到了 `limit` 条。**
- 翻页看 `data.pagination.has_next` 和 `next_cursor` / `end_cursor`，`has_next: false` 就停。
- 列表 `search` 的 `limit` 最大 **10**（不是 20），用 `offset` / `next_offset` 翻页；`query="*"` 可遍历全部接口。

## 响应里的元数据

每次成功返回都带 `_source`：

```json
{"api": "POST /vehicles/_search", "operation_id": "SearchVehicles",
 "fetched_at": "2026-10-26T18:56:11+08:00", "trace_id": "giSTnINda..."}
```

**报障时优先用 `_source.trace_id`**（错误场景用 `error.trace_id`），配合 `fetched_at` 一起给用户。

响应同时含 `structuredContent` 和 `content[0].text`，**两者是同一份 JSON**，只解析其中一个，不要读两遍。

## 错误处理

失败时 `isError: true`，`structuredContent` 为 `{"error": {"code","message","trace_id","upstream_code"?}}`。实测四类：

| `error.code` | 含义 | 处理 |
|---|---|---|
| `invalid_arguments` | 参数与 schema 不符 | 按 describe 重建参数，**不要重试** |
| `api_not_found` | `operation_id` 不存在或无权限 | 回 `search_platform_apis` 重检索 |
| `upstream_business_error` | 平台业务规则拒绝，带 `upstream_code` | **把 `message` 直接转述给用户**（已是中文可读），按 code 决定改参数还是换查询 |
| `internal_error` | 平台内部异常 | 最多重试 1 次，仍失败给 `trace_id` |

`upstream_business_error` 的 `message` 已经写明原因，例如「filter 不能为空（错误码 8800018069）」「参数值非法[…operator=BADOP]（错误码 8800000003）」，**不要自己编解释，也不要原样重放同样的请求**。

返回成功但数据为空时，按顺序排查：时间窗 → 资产/组织/标签范围 → 当前环境是沙箱还是正式。

更多错误码与排查路径见 `references/error-codes.md`；平台级规则细节见 `references/platform-rules.md`。

## 平台规则速记

- **环境由凭证决定**，不是工具参数；当前是沙箱还是正式写在 `initialize` 的 `instructions` 里。沙箱是演示租户数据，回答前先确认。
- **限流**：正式环境按凭证限频（如 10 次/秒、1000 次/天）。只对 429/5xx/超时重试，优先看 `Retry-After`，否则指数退避 + 抖动，最多 3 次；400/401/403/404 不要重试。
- **批量拉取用游标顺序推进**，不要并发扫全量；能换成增量/事件的地方不要轮询。
- **敏感数据**：司机手机号/证件号、位置轨迹、媒体下载地址按最小必要取用；展示和日志都脱敏，不要把整段响应贴进日志或工单。
- **脱敏/加密值**（`LFW**********4567`、`GRnchQa...==(Rg==)`）原样透传，不解码、不推断。
- **认证**：MCP 走 OAuth Bearer，用户不需要配 AK/SK；只有自己直连 OpenAPI 才需要签名。

## 省 token

- `include_*` 参数默认全 `false`，只在用户明确问到时打开（如问"资质"才 `include_qualifications: true`）。
- 车辆/事件单条记录字段很多（30+），先 `limit: 3~5` 验证查询条件，再放大。
- 不要为了"拿全量"无脑翻页：先看 `total_count`，能聚合就让接口自己聚合。
- 不要把大段原始 JSON 贴回给用户，抽取用户关心的字段用自然语言回答。

## 深挖文档

需要字段字典、响应示例、错误码全表、业务场景串联时，读官方 Agent 文档索引：

- `https://open.g7.com.cn/docs/llms.txt` — 全部指南 / API / 事件的 `.md` 链接
- 接口级细节：用 describe 返回的 `path` 在 llms.txt 里找对应的 `https://open.g7.com.cn/docs/api/*.md`

`usage_guide` 里指向 `dp-kb.chinawayltd.com` 的知识库链接是给人看的，**Agent 不必访问**。

## 红线

- 不执行 `DISCOVERY_ONLY` 接口；用户要写操作时明说"MCP 连接器只支持只读查询"，建议走 OpenAPI + 服务端 AK/SK。
- `callable: false` / `authorized: false` 不重试，引导用户去开发者后台勾选权限。
- 不猜测缺失字段的语义；`********`、`xxx==(yy==)` 这类是平台脱敏/加密值，原样透传，不尝试解码。

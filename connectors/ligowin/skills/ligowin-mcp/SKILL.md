---
name: ligowin-mcp
display_name: LigoWin MCP 查询
display_name_en: LigoWin MCP Queries
description: 查询 LigoWin 平台运营指标、人力效能、回款分析、案件动作和物业法规原文时使用。优先检查 CLI 凭证是否可用，未配置时使用已连接的 MCP。
description_zh: 通过 MCP 查询 LigoWin 授权数据，包括运营统计、回款分析、案件动作和物业法规原文。
description_en: Query authorized LigoWin operational statistics, payment recovery data, account actions, and property legal source texts through MCP.
version: 0.1.0
author: LigoWin 律思原力
---

# ligowin-mcp

## 查询方式选择

- 仅检查当前执行环境中的 `LIGOWIN_OPENAPI_ISSUER`、`LIGOWIN_OPENAPI_SECRET` 是否均存在且非空，不输出变量值，不要求用户在对话中提供凭证。
- 两项均存在且 `ligowin-cli` Skill、脚本及解释器可用时，优先使用 CLI；任一变量缺失、为空或 CLI 不可用时，使用 `ligowin-mcp-service` 提供的 MCP 工具，不先要求配置 CLI 环境。
- 无法检查环境变量时，不推断凭证存在；已有可用 MCP 工具则使用 MCP。
- 需要使用 MCP 但工具不可用时，引导用户安装或连接 `ligowin-mcp`，完成浏览器授权后继续；不转回 CLI 反复尝试。
- 选定查询方式后，调用失败按该方式的错误说明处理，不自动切换另一身份来源重试。两种方式可能对应不同的应用或用户权限。
- 此选择规则仅适用于查询指导，不会自动替换现有 Excel 脚本的数据获取方式；固定报表仍按原 `data-export` Skill 执行。

## 连接与能力

MCP 使用 `https://ligowin.com/external/mcp`，通过 WorkBuddy 的浏览器 OAuth 授权连接。凭证及刷新由客户端管理；不要提取 Token、自行拼接 HTTP 请求或以 Shell 脚本绕过连接器。

选择 `ligowin-mcp-service` 下实际暴露的工具。

| 工具 | 用途与选择 |
| --- | --- |
| `stats_metricsdef` | 查询指标定义；指标名称、单位或口径不明确时先调用 |
| `stats_operation` | 查询指定项目的日、周或月运营统计 |
| `stats_workforce` | 按员工或部门查询日、周或月人力效能 |
| `stats_pivot_table` | 按员工、部门、项目或时间维度组合统计指标 |
| `report_collection_insights` | 查询案件及回款分析，取得后续查询所需的案件公开 ID |
| `action_list` | 查询案件的沟通、物业跟进、标签及对账等动作 |
| `legal_kb_originals_query` | 根据物业问题概要检索法规原文 |

仅支持以上查询，不支持群聊查询、业务写入或直接生成 Excel。连接器可独立使用，无需安装专家包；CLI 和报表 Skill 仅在已安装时可用。

## 字段与口径参考

确认输入参数、状态枚举、默认值、返回字段或统计口径时，按工具名称读取 [接口约定](references/api_contract.md)（@references/api_contract.md）的对应章节。该文档补充 inputSchema 未表达的校验和业务限制；解读金额、日期窗口、动态指标及截断结果前先核对相应说明。

## 查询流程

1. 从请求和当前会话提取公司、项目、时间及查询目标，仅追问必要条件。公司和项目名称使用全名；公开 ID 取自返回结果或用户提供，不猜测。按实际工具 schema 传参，不额外传入 CLI 参数。
2. 指标分析先确认指标定义，再选项目统计、人力统计或透视统计。`stats_operation`、`stats_workforce` 使用周期和起始日期，不支持任意添加 `end_date`；透视统计使用起止日期，结束日期须晚于开始日期，指标最多 20 个，不传 `account_names`。
3. 查询案件时，`report_collection_insights` 的公司、项目、状态筛选至少一项非空。需要动作明细时，从返回记录提取 `account_public_id`，传给 `action_list.account_public_ids`；只查询任务所需范围。
4. 法规检索使用 `scenario: property`，`question_summary` 为非空且不超过 100 字符的概要，保留地区和关键事实。读取 `data.originals`；无匹配不等于不存在相关法规。本 Skill 只提供检索指导，不另设法律回答模板。

## 分页与完整性

- 回款和动作查询使用 `page`、`page_size`，页码从 1 开始，每页最多 200。根据 `data.pagination` 判断是否需要后续页，保持筛选条件一致；未完成分页、客户端截断或中途失败时，说明覆盖范围，不称为全量。
- `action_list` 默认每个案件最多 6 条动作，`max_actions` 最大 50，再对合并结果分页。翻完所有页也不代表取得全部历史动作。
- `only_last_connected_call`、`only_last_property_service` 用于最近记录模式，按返回范围解释；需要话术质检时显式传 `with_call_analysis: true`。
- 按任务需要获取后续页，不无条件拉取全部数据。查询受限时缩小项目、日期或案件范围，不能通过换身份规避权限或上限。

## 典型调用参数

以下为工具参数示例，项目、日期和问题应替换为用户实际条件；直接通过 MCP 工具调用，不作为 Shell 命令执行。

`stats_metricsdef`：

```json
{"metric_groups": ["community"]}
```

`stats_operation`：

```json
{"period": "monthly", "community_names": ["示例项目"], "start_date": "2026-08-01"}
```

`report_collection_insights`：

```json
{"community_names": ["示例项目"], "page": 1, "page_size": 50}
```

`legal_kb_originals_query`：

```json
{"scenario": "property", "question_summary": "成都市物业服务收费项目和标准应如何公示？"}
```

## 结果与错误

- 优先读取 MCP 的 `structuredContent`；若客户端仅展示文本 JSON，解析对应文本。成功业务数据位于 `data`，分页位置以实际结果为准，不套用 CLI 的 `ok` 或 `error.category`。
- `isError: true` 表示工具失败，读取 `detail.code`、`detail.message`（或字符串 `detail`）、`status_code` 和 `request_id`，不得将其当作业务数据。
- OAuth 失效交由 WorkBuddy 刷新；仍失败时引导重新连接。应用权限、IP 白名单或绑定状态拒绝时说明原因并请管理员处理，不反复重新授权或切换身份。
- 参数错误按 schema 修正；限流按服务提示等待，避免连续重试；超时缩小查询范围。服务端单次调用上限为 120 秒，客户端可能更早超时。
- 区分空结果、全零统计的业务错误和调用失败；分析时说明数据范围与依据，区分事实和推断，不把未知值补成零。

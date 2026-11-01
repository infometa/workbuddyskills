---
name: tencent-union-igro
description: 腾讯营销联盟变现助手 iGRO - 查询天级报表与指标口径、生成流量诊断与屏蔽健康度报告、检索平台官方知识库
version: "1.0.0"
author: "腾讯营销联盟"
---

# 腾讯营销联盟变现助手 iGRO

本 Skill 帮助腾讯营销联盟（优量汇）开发者用自然语言查询本账号的变现数据、诊断变现问题，并检索平台官方知识库。

所有数据只属于当前 API Key 绑定的开发者账号，工具入参中**没有** member_id，也无法查询其他账号的数据。

## 可用工具

| 工具 | 用途 | 需要的授权范围 |
|------|------|------|
| `union_report_daily_indicators` | 天级报表可用的指标、维度与口径 | 数据与诊断 |
| `union_report_daily` | 查询天级报表 | 数据与诊断 |
| `union_ai_flow_diagnosis_report` | 生成媒体的流量诊断报告 | 数据与诊断 |
| `union_ai_umbrella_health_report` | 生成媒体的屏蔽健康度报告 | 数据与诊断 |
| `union_ai_knowledge_search` | 检索平台官方知识库 | 无需授权，任何有效 Key 均可用 |

如果工具列表里只有 `union_ai_knowledge_search`，说明 API Key 未勾选「数据与诊断」授权范围，请提示用户到开发者平台修改授权范围（见「认证说明」）。

### union_report_daily_indicators - 天级报表指标说明

获取天级报表可用的指标（metrics）与聚合维度（dimensions），口径与开发者平台报表页一致。**调用 `union_report_daily` 前建议先调用一次**，用返回的 `name` 作为 metrics / group_by / order_by 的取值。

**参数**：无

**返回**：`metrics` 与 `dimensions` 两个列表，每项包含 `name`（取值）、`display_name`（中文名）、`description`（口径说明）、`unit`（单位）、`is_default`（是否默认返回）、`sortable`（是否可排序）。

### union_report_daily - 天级报表查询

查询天级报表数据，与开发者平台「数据报表」同源。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| start_date | string | ✅ | 开始日期，`yyyy-mm-dd`，不早于 2 年前 |
| end_date | string | ✅ | 结束日期（含），`yyyy-mm-dd`，不晚于今天 |
| group_by | string[] | - | 聚合维度，取值见指标说明的 dimensions；不传则返回整个时间范围的汇总 |
| metrics | string[] | - | 返回的指标，取值见指标说明的 metrics；不传则返回默认指标 |
| filter.app_ids | number[] | - | 媒体 ID 列表 |
| filter.placement_ids | string[] | - | 广告位 ID 列表（字符串） |
| filter.placement_types | string[] | - | 广告位类型：Inline 插屏、Native 原生、Splash 开屏、Banner、RewardedVideo 激励视频、Feeds、AppWall 应用墙 |
| filter.position_scenes | number[] | - | 广告场景 ID 列表 |
| filter.os_platforms | string[] | - | 系统平台：Unknown、Android、iOS、H5、Harmony、PC |
| order_by.field | string | - | 排序字段：可排序的指标，或 group_by 中的维度 |
| order_by.direction | string | - | `asc` / `desc`，默认 `desc` |
| page | number | - | 页码，从 1 开始，默认 1 |
| page_size | number | - | 每页行数，默认 20，最大 100 |

**返回**：`columns` 为列名，`rows` 为对应的行数据，`total` 为总行数，可通过 `page` 翻页。按 app_id / placement_id / position_scene 聚合时自动附带名称列。

**重要限制**：
- **单次最多查询 7 天**（start_date 与 end_date 都包含在内）。需要更长范围时，拆成多个不超过 7 天、首尾相接且不重叠的区间分别查询，再合并结果。
- 合并结果时，收入、请求、曝光、点击等**数量类指标可直接相加**；eCPM、点击率等**比率类指标不能相加或取平均**，需要用数量类指标重新计算（可在 metrics 中一并查询所需的数量类指标）。
- 数据按天产出，当天数据可能尚未产出。
- 单位：金额为元；比率为百分数（12.3 表示 12.3%）。

**使用示例**：
- 昨天的整体数据：start_date 与 end_date 都设为昨天，不传 group_by
- 最近 7 天各广告位收入排行：group_by 设为 `["placement_id"]`，order_by 设为收入指标、`desc`
- 最近 14 天的趋势：拆成两个 7 天区间分别查询后合并

### union_ai_flow_diagnosis_report - 流量诊断报告

为指定媒体生成流量诊断报告（Markdown），内容包括场景效率、变现漏斗、屏蔽影响、SDK 版本分布，以及与同行业水位的对比和优化建议。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| app_id | number | ✅ | 媒体 ID |
| start_date | string | ✅ | 开始日期，`yyyy-mm-dd`，不早于 7 天前 |
| end_date | string | ✅ | 结束日期（含），`yyyy-mm-dd`，不早于 start_date 且不晚于今天 |
| app_name | string | - | 媒体名称，仅用于报告标题展示 |

### union_ai_umbrella_health_report - 屏蔽健康度报告

为指定媒体生成屏蔽健康度报告（Markdown）：基于最近一周的屏蔽数据，分析当前生效的屏蔽规则对收入的影响、与同行业的对比，并给出优化建议。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| app_id | number | ✅ | 媒体 ID |

**两个报告工具的共同说明**：
- 报告由 AI 基于平台数据生成，**耗时约 30~60 秒，请勿重复调用**，调用前可告知用户需要稍候。
- 媒体必须属于当前账号，否则会提示无数据。
- 不知道媒体 ID 时，先用 `union_report_daily` 按 `app_id` 聚合查询一次，拿到媒体 ID 和名称。
- 报告原样以 Markdown 返回，可直接展示给用户，或在此基础上总结要点。

### union_ai_knowledge_search - 平台知识检索

检索腾讯营销联盟官方知识库，返回相关文档片段。适用于平台使用、SDK 接入与报错、广告位配置、结算与政策规则等问题。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| query | string | ✅ | 检索词：自然语言问题或关键词组合，最长 500 字 |
| knowledge_types | string[] | - | `tech_helper`（官网接入指南）、`helper_faq`（常见问题）；不传则两者都检索 |

**返回**：`total` 为命中条数；`results` 按相关度降序，每项含 `id`（知识条目 ID）、`source`（所属知识库）、`content`（正文片段）、`score`（相关度，越高越相关）。

**使用建议**：
- query 用自然语言问题或关键词组合，如「Android SDK 初始化失败」「开屏广告 填充率 低」。
- 未命中（total 为 0）时换检索词重试；仍无结果请如实告知用户，**不要编造平台规则或接入步骤**。

## 推荐用法

- **查数**：先调 `union_report_daily_indicators` 了解指标与口径，再调 `union_report_daily`。
- **诊断变现问题**：先用 `union_report_daily` 定位异常的媒体 / 广告位和时间段，再对相应媒体调用诊断报告工具，结合数据给出建议。
- **平台规则与接入问题**：调用 `union_ai_knowledge_search`，回答时以检索结果为准。

## 认证说明

- 本连接器使用 MCP API Key 鉴权，需要在 WorkBuddy 连接时填入。
- 获取方式：登录腾讯营销联盟开发者平台（https://adnet.qq.com），进入「接入中心 → MCP接入」生成 API Key。仅超级管理员可生成，明文只展示一次。
- 授权范围：生成时需勾选「数据与诊断」，才能使用报表与诊断报告工具；知识检索无需勾选。之后可在同一页面修改授权范围，修改后立即生效。
- Key 丢失或泄露：在「MCP接入」页面重置 API Key，原 Key 立即失效，然后在 WorkBuddy 的连接器设置中更新为新 Key。
- API Key 长期有效，除非被重置、手动失效或被平台禁用。

## 常见错误与处理

| 错误信息 | 原因 | 处理建议 |
|------|------|------|
| HTTP 401，`invalid API key` | Key 填写错误或已被重置 | 提示用户检查 Key，必要时在开发者平台重置后，到 WorkBuddy 连接器设置中更新 |
| HTTP 401，`API key has been invalidated` | Key 已被手动失效 | 提示用户在开发者平台重置 Key 并更新 |
| HTTP 401，`API key has been disabled by the platform` | Key 被平台禁用 | 提示用户联系腾讯营销联盟运营 |
| `the API key is not authorized to use tool ...` | Key 未授权该能力 | 提示用户在「MCP接入」页面勾选「数据与诊断」 |
| `access denied: ... agreements ...` | 账号有未签署或需更新的协议 | 提示用户先到开发者平台签署协议 |
| `rate limit exceeded` | 调用过于频繁（同一工具每秒最多 2 次） | 放慢调用节奏后重试，避免同时并发大量调用 |
| `the date range must not exceed 7 days` | 天级报表单次查询超过 7 天 | 按 7 天拆分为多次查询后合并 |
| `start_date must not be earlier than 7 days ago` | 流量诊断报告的开始日期过早 | 将 start_date 调整到 7 天以内 |
| 报告提示无数据 | 媒体不属于当前账号，或该媒体暂无数据 | 确认媒体 ID 是否正确 |
| `invalid arguments: ...` | 参数格式或取值不合法 | 按报错信息修正参数，枚举类取值以本说明和指标说明工具为准 |

---
name: sensors-connector
description: |
  神策连接器统一入口：先按场景路由到神策 AI 对话或 sensors CLI，再按对应 reference 调用。
  AI 链路承接客群发现与运营增长；CLI 链路承接快速洞察、深度分析、规则圈选与数据管理。
  CLI 能力包括元数据查询、标准分析、只读 SQL、看板与书签、标签与分群管理，以及受控写入。
  首次运行未配置时引导用户完成配置。
  边界：只负责场景路由、命令执行与结果结构化，业务口径与对象选择由调用方确认。
description_zh: 神策连接器统一入口：AI 与 CLI 场景路由、AI 对话调用、CLI 参数与 Schema 发现、安全执行和结构化输出。
description_en: "Unified Sensors connector: route scenarios between Sensors AI chat and the Sensors CLI, then execute the referenced contract safely."
version: 2.0.0
author: Sensors Data
metadata:
  requires:
    bins: ["sensors"]
---

# sensors-connector

本 Skill 是调用方（用户直接请求或上层业务流程）与神策 AI / `sensors` CLI 之间的统一执行层：先按场景选择链路，再按对应 reference 调用并返回结构化结果。

## 边界

- 负责 AI/CLI 场景路由、AI 对话调用、CLI 命令路由、参数与输入 Schema、结构化输出、错误与 `request_id`。
- 不做业务决策：不选择分析模型、不替用户在多个业务对象间做决定、不解释业务结论；这些由调用方（用户或上层流程）完成。
- CLI 的实时 `--help`、`--schema`（如命令支持）与 `--dry-run` 请求预览是 CLI 参数契约的最终事实源；AI 命令以 [execute-ai-chat.md](references/execute-ai-chat.md) 为准。
- 不绕过 CLI 用 HTTP、`curl` 或未登记脚本调用产品接口。

## 场景路由：AI 还是 CLI

本 Skill 有两条链路：**默认走 CLI**；只有明确命中「客群发现」或「运营增长」白名单时走神策 AI。不要按“是否开放式问题”判断，看板解读和深度分析仍走 CLI。

| 工作模式 | 链路 | 典型场景 |
|---|---|---|
| 客群发现 | A · 神策 AI | 目标客群预测、相似人群拓展、语义标签构建等 |
| 运营增长 | A · 神策 AI | 策略设计、策略优化、策略效果预测等 |
| 快速洞察 | B · CLI | 看板解读、异常识别、经营简报、核心指标查询 |
| 深度分析 | B · CLI | 漏斗诊断、用户旅程、留存活跃、渠道归因 |
| 规则圈选 | B · CLI | 人群画像、用户检索、标签创建、目标分群 |
| 数据管理 | B · CLI | 埋点方案设计、埋点实施、埋点测试 |

- 完整场景表、判定兜底和易错点见 `analyze.scenarios`（[analyze-scenarios.md](references/analyze-scenarios.md)），判断不清时先读它；跨模式请求拆成多个步骤，分别执行 A/B 并交叉引用结果。
- 链路 A：调用 `ai.chat`，执行前必须读 [execute-ai-chat.md](references/execute-ai-chat.md)；content 原样传入、会话 ID 复用、执行模式、超时恢复与结果取用规则以该文件为唯一事实源。
- 链路 B：按「上下文与调用前置」→「元数据解析」→「工具路由」执行；AI reference 不替代 CLI reference。

## 上下文与调用前置

任何真实业务请求前，先完成会话与项目上下文（会话与项目上下文工具内联于本节；首次未配置的引导 `config.create` 有独立说明，见下）。

### 未配置时的引导：`config.create`

首次运行或本机尚未配置时，`context.session-start` 返回 `No configuration found at ~/.sensors/config.toml`、业务命令抛 `ConfigNotFoundError`、`sensors doctor` 报「还没有找到配置文件」；命中任一即按 [config/create-config.md](references/config/create-config.md) 的引导流程，在对话中逐项收集 Base URL / API Key / 默认项目，写入配置并验证生效，再回到会话建立。配置已存在（`doctor` 的 `config_exists` 通过）时不得重跑初始化；仅改局部字段用 `sensors config update-context`。

### 建立或复用会话：`context.session-start`

```bash
sensors context session-start --ai-goal "<不超过 30 字的目标摘要>" --format json
```

- 首次真实请求或用户目标切换时执行一次；输出 `ai_session_id`、`default_project_name`、`number_of_projects` 等字段。
- 同一目标内的追问、下钻、参数调整必须复用已有 `ai_session_id`，不得重复 `session-start`。
- 后续真实业务命令携带 `--ai-session-id <ai_session_id>`；`--schema`、`--dry-run` 等不发请求的预览按目标命令帮助执行。
- 复合协议 `context.ensure`：无可用 session 时执行 `session-start`，已有则直接复用——不要重复建立。

### 解析项目：`context.project-get` / `context.project-list`

```bash
sensors context project-get --ai-session-id <id> --project-name "<name>" --format json
sensors context project-list --ai-session-id <id> [--product-name SA|SF|Horizon] --format json
```

- 仅当默认项目不是目标项目、用户要求切换或项目不明确时执行。
- `project-get` 的 `--project-id` 与 `--project-name` 至少提供一个；输出 `id`、`name`、`display_name`、`product_name`、`status` 等。`--project-id` 仅是本命令的查询条件，不代表其它命令接受数字 ID——其它命令一律用项目英文名（见「公共调用规则」）。
- `project-list` 输出 `projects[]`；多候选且用户未指定时返回候选清单请调用方确认，**禁止猜测**；空结果或无权限时停止，不静默换项目重试。

## 元数据解析

任何引用事件、属性、取值、表或列的请求，先按以下流程把口语描述绑定为精确系统名，再进入请求构造。本流程内联于本节，是全库唯一的元数据解析权威来源；各工具的参数、过滤与输出细节见「工具路由 → 元数据」的工具说明，调用方只引用本流程，不复制步骤。

### 事件名解析

用 `metadata.events` 拉取事件全量列表（同一任务内只拉一次并复用；排查「存在但无数据」时把无数据事件一并拉取，不重复拉取）：

- 服务端不做模糊匹配；对返回结果的 `name` + `display_name` 做语义匹配（含同义词、英文翻译）。
- 默认列表只返回 `has_data=true`（历史有上报）的事件：解析确认的每个事件即同时完成「是否有上报」确认，后续分析结果为 0/空时不必回头复查上报状态（`has_data` 只代表历史有上报，不保证查询时间窗内一定有数据）。
- 记录两个字段：`name` 用于业务引用与展示；`original_name` 用于后续 `metadata.event-fields` 与 `metadata.event-get` 的精确定位。
- 单一明确匹配 → 记录后继续。
- 多候选 → 触发**歧义停止门**：
  - 输出候选清单（名称、显示名、是否有数据）后结束本轮，等待用户选择；
  - 用户明确选择前，不得基于任何候选继续后续步骤（分析、查询、构造请求），禁止自行二选一；
  - 用户的「直接开始 / 跳过确认」指令不解除本门禁，门禁优先于执行请求；
  - 交互组件不可用时以文本形式列出候选并结束。
- 零结果 → 换同义词或英文重试一次；仍无结果则如实告知可能不存在，不暴力扫描、不换项目重试。

### 事件属性解析

用 `metadata.event-fields` 确认目标事件下属性的内部名、显示名与数据类型（同一事件的字段列表只查一次并复用）。数值/布尔类型可直接进入请求构造；字符串类型需要具体取值时进入属性取值解析。

### 属性取值解析

用 `metadata.values` 查询属性的候选取值，事件属性与用户属性分别查询。空列表按零结果纪律处理；返回截断时请调用方提供具体取值，或改用范围/前缀等条件表达，不猜测完整取值集。

### 用户属性解析

用 `metadata.fields` 拉取用户属性全量后语义匹配；匹配与零结果纪律同事件名解析。需要取值时接 `metadata.values`。

### SQL 库表列发现

`metadata.databases` 定位目标库（`created_by=sensorsdata.horizon` 的行为当前项目默认库）→ `metadata.tables` 确认表 → `metadata.columns` 确认列。跨项目即跨库：库名全局唯一（`horizon_<项目英文名>_<项目id>`），需要其它项目的表时按项目分别发现并显式指定。

### 统一纪律

- 口语词未经本流程确认为精确名前，不得进入任何请求构造。
- 多候选触发歧义停止门：列候选、结束本轮、等用户选择，门禁优先于用户的执行指令；零结果同义词重试仅一次；不 fallback 到 curl、SQL 或直调 API。

## 工具路由

本表按用途路由到工具说明；各工具的精确命令、flag 与输入 Schema 在其说明文件（Reference 列）中，不在本表登记。一次任务只加载目标工具的一个 reference；Analytics 查询先读公共输入契约 `analytics/analytics-query-schema.md`。禁止预加载多个工具文档或全部领域。

### 神策 AI（命令组 `sensors ai`）

| 工具 | 用途 | 类型 | Reference |
|---|---|---|---|
| `ai.chat` | 客群发现与运营增长白名单场景的神策 AI 对话 | 查询/平台执行 | [execute-ai-chat.md](references/execute-ai-chat.md) |
| （路由）`analyze.scenarios` | AI 与 CLI 链路及具体场景边界判定 | 路由 | [analyze-scenarios.md](references/analyze-scenarios.md) |

### 标准分析（命令组 `sensors analytics`）

| 工具 | 用途 | 类型 | Reference |
|---|---|---|---|
| `analysis.events` | 事件分析: 看指标与趋势：事件次数、触发人数（DAU / UV / PV）、人均次数、数值属性求和 / 均值 / 最值与公式指标（转化率、客单价、占比），可按属性分组对比 | 查询 | [analytics/analyze-events.md](references/analytics/analyze-events.md) |
| `analysis.funnel` | 漏斗分析: 看多步转化与流失：≥2 步流程的整体与每步转化率、定位主要漏损步骤，支持转化窗口与属性拆分对比 | 查询 | [analytics/analyze-funnel.md](references/analytics/analyze-funnel.md) |
| `analysis.retention` | 留存分析: 看回访与留存：起始行为后的次日 / N 日留存率与留存曲线、回访周期与流失率，可按维度拆分 | 查询 | [analytics/analyze-retention.md](references/analytics/analyze-retention.md) |
| `analysis.distribution` | 分布分析: 看数值属性区间分布：订单金额、加购数量等落在各区间的人数与占比，支持自定义分桶边界 | 查询 | [analytics/analyze-distribution.md](references/analytics/analyze-distribution.md) |
| `analysis.ltv` | LTV 分析: 看生命周期价值：起始行为后 N 个周期的累计贡献 / 累计 GMV 曲线，可按维度拆分 | 查询 | [analytics/analyze-ltv.md](references/analytics/analyze-ltv.md) |
| `analysis.session` | Session 分析: 按会话口径看行为：会话数 / 访次、平均会话时长、人均行为次数等，基于平台 Session 定义统计 | 查询 | [analytics/analyze-session.md](references/analytics/analyze-session.md) |
| `analysis.interval` | 间隔分析: 看两事件间隔时长：注册到首购、下单到支付等耗时的分位数分布（P10~P90），可单维度拆分 | 查询 | [analytics/analyze-interval.md](references/analytics/analyze-interval.md) |
| `analysis.attribution` | 归因分析: 看转化贡献归属：目标转化前各触点 / 渠道的贡献占比，支持首触 / 末触 / 线性 / 时间衰减模型对比 | 查询 | [analytics/analyze-attribution.md](references/analytics/analyze-attribution.md) |
| `analysis.user-path` | 路径分析: 看用户行为轨迹：起始事件后的后续路径、结束事件前的前序路径与流转关系 | 查询 | [analytics/analyze-user-path.md](references/analytics/analyze-user-path.md) |
| `analysis.user-property` | 属性分析: 按属性维度看分布：用户 / 事件属性的分组统计与交叉分布（属性分析报表） | 查询 | [analytics/analyze-user-property.md](references/analytics/analyze-user-property.md) |
| `analysis.user-list` | 用户列表: 找具体用户：按用户 ID / 属性 / 固定分群筛选用户明细（用户细查），返回指定属性列 | 查询 | [analytics/analyze-user-list.md](references/analytics/analyze-user-list.md) |
| `analysis.personas` | 用户群画像: 看人群画像特征：目标 / 对比人群的标签与属性分布、行为指标，可带 TGI 差异 | 查询 | [analytics/analyze-personas.md](references/analytics/analyze-personas.md) |
| `analysis.rfm` | RFM 分析: 做客户价值分层：按最近一次行为（R）、频次（F）、价值（M）划分高价值 / 保持 / 发展 / 挽留客户 | 查询 | [analytics/analyze-rfm.md](references/analytics/analyze-rfm.md) |
| `analysis.session-create` | Session 分析: 创建自定义 Session 定义，供 Session 分析以名称引用 | 写入 | [analytics/create-session-definition.md](references/analytics/create-session-definition.md) |
| `analysis.session-list` | Session 分析: 查询当前项目下全部自定义 Session 定义 | 查询 | [analytics/list-session-definitions.md](references/analytics/list-session-definitions.md) |
| `analysis.session-update` | Session 分析: 按 id 部分更新已有自定义 Session 定义（`name` 不可变） | 写入 | [analytics/update-session-definition.md](references/analytics/update-session-definition.md) |
| `analysis.funnel-users` | 漏斗明细: 下钻漏斗某一步的转化 / 流失用户名单（分析参数与漏斗报表一致，`slice_step` + `wastage` 定位步骤） | 查询 | [analytics/list-funnel-users.md](references/analytics/list-funnel-users.md) |
| `analysis.retention-users` | 留存明细: 下钻某天初始行为在第 N 周期的留存 / 流失用户名单（`slice_date` + `slice_interval` + `wastage`） | 查询 | [analytics/list-retention-users.md](references/analytics/list-retention-users.md) |
| `analysis.segmentation-users` | 事件分析明细: 下钻某指标 / 分组 / 日期的触发用户名单（`slice_by_values` + `slice_date`） | 查询 | [analytics/list-segmentation-users.md](references/analytics/list-segmentation-users.md) |
| `analysis.distribution-users` | 分布明细: 下钻分布值落入某区间的用户名单（`slice_by_value` 定位单元格 + `slice_freq` 定位区间） | 查询 | [analytics/list-distribution-users.md](references/analytics/list-distribution-users.md) |
| `analysis.ltv-users` | LTV 明细: 下钻某个起始日期 cohort 的用户名单（`slice_date` 取报表 cohort 日期） | 查询 | [analytics/list-ltv-users.md](references/analytics/list-ltv-users.md) |
| `analysis.session-users` | Session 明细: 下钻某天 Session 指标的用户名单（`session_name` + `slice_date` 必填） | 查询 | [analytics/list-session-users.md](references/analytics/list-session-users.md) |
| `analysis.user-path-users` | 路径明细: 下钻经过路径图某节点的用户名单（`slice_element_filters` + `session_level` + `edge_type`） | 查询 | [analytics/list-user-path-users.md](references/analytics/list-user-path-users.md) |
| （共享）Analytics 公共输入/输出契约 | 标准分析查询共享的字段路径、过滤树、聚合器、日期范围与公共输出契约；查询类工具构造输入前先读 | — | [analytics/analytics-query-schema.md](references/analytics/analytics-query-schema.md) |

### SQL 查询（命令挂在 analytics 组下）

| 工具 | 用途 | 类型 | Reference |
|---|---|---|---|
| `sql.execute` | 执行只读 Impala SQL（`SELECT` / `WITH ... SELECT`）并返回结构化结果；多表关联、复杂聚合、明细导出等场景 | 查询 | [sql/execute-sql.md](references/sql/execute-sql.md) |

### 看板与书签（命令挂在 analytics 组下）

| 工具 | 用途 | 类型 | Reference |
|---|---|---|---|
| `dashboard.list` | 查询可见看板（概览）导航列表与真实书签数量，获取看板 ID 候选 | 查询 | [dashboard/list-dashboards.md](references/dashboard/list-dashboards.md) |
| `dashboard.get` | 按看板 ID 获取看板基本信息与全部书签列表，确定书签 ID 与分析类型 | 查询 | [dashboard/get-dashboard.md](references/dashboard/get-dashboard.md) |
| `dashboard.create` | 创建一个新的空看板（不接收初始书签） | 写入 | [dashboard/create-dashboard.md](references/dashboard/create-dashboard.md) |
| `dashboard.update` | 全量更新看板：覆盖名称并按提交顺序整体替换书签列表 | 写入 | [dashboard/update-dashboard.md](references/dashboard/update-dashboard.md) |
| `dashboard.bookmark-query` | 按书签 ID 执行已保存书签的分析查询并返回原始结果 | 查询 | [dashboard/query-bookmark.md](references/dashboard/query-bookmark.md) |
| `dashboard.bookmark-add` | 向已有看板的书签列表末尾追加一个或多个书签 | 写入 | [dashboard/add-bookmark.md](references/dashboard/add-bookmark.md) |
| `dashboard.bookmark-remove` | 从看板中按书签 ID 移除一个或多个书签 | 写入 | [dashboard/remove-bookmark.md](references/dashboard/remove-bookmark.md) |
| `dashboard.bookmark-copy` | 把源看板的已有书签复制到目标看板，可选迁移语义（复制后从源移除） | 写入 | [dashboard/copy-bookmark.md](references/dashboard/copy-bookmark.md) |

### 元数据（命令组 `sensors metadata`；解析流程见本文「元数据解析」）

| 工具 | 用途 | 类型 | Reference |
|---|---|---|---|
| `metadata.events` | 分页查询事件 schema 列表（精确名 / 显示名 / 原始名 / 数据状态）；事件口语名绑定的第一步 | 查询 | [metadata/list-events.md](references/metadata/list-events.md) |
| `metadata.event-get` | 按事件原始名精确查询单个事件详情 | 查询 | [metadata/get-event.md](references/metadata/get-event.md) |
| `metadata.event-fields` | 查询某事件实际上报过的属性子集（事件视角，不同事件结果不同） | 查询 | [metadata/get-event-fields.md](references/metadata/get-event-fields.md) |
| `metadata.fields` | 查询 Schema 下注册的全量属性列表（Schema 视角，不区分事件） | 查询 | [metadata/list-fields.md](references/metadata/list-fields.md) |
| `metadata.field-get` | 按 Schema 名 + 属性名查询单个属性详情（类型、数据状态、身份标记） | 查询 | [metadata/get-field.md](references/metadata/get-field.md) |
| `metadata.values` | 查询属性候选取值列表，用于构造过滤条件或核对取值上报状态 | 查询 | [metadata/get-property-values.md](references/metadata/get-property-values.md) |
| `metadata.schema-get` | 按名称查询单个 Schema 的元信息（类型、所属类、数据状态） | 查询 | [metadata/get-schema.md](references/metadata/get-schema.md) |
| `metadata.databases` | 查询当前项目的数据库列表，确定 SQL 的库名 | 查询 | [metadata/list-databases.md](references/metadata/list-databases.md) |
| `metadata.tables` | 查询指定库下的 Horizon 表列表，确定 SQL 的表名 | 查询 | [metadata/list-tables.md](references/metadata/list-tables.md) |
| `metadata.columns` | 查询指定表的列定义，确定 SQL 可用的列名 | 查询 | [metadata/list-columns.md](references/metadata/list-columns.md) |
| `metadata.event-create` | 在 events schema 下注册新事件（原始名 + 显示名，可附埋点设计信息） | 写入 | [metadata/create-event.md](references/metadata/create-event.md) |
| `metadata.event-update` | 更新事件 schema 白名单字段（显示名、可见性、启用状态、备注等） | 写入 | [metadata/update-event.md](references/metadata/update-event.md) |
| `metadata.field-create` | 在已有 schema 下批量创建普通属性 | 写入 | [metadata/create-field.md](references/metadata/create-field.md) |
| `metadata.field-update` | 更新单个已有属性的白名单字段（显示名、可见性、启用状态等） | 写入 | [metadata/update-field.md](references/metadata/update-field.md) |
| `metadata.schema-field-validate` | 批量校验元事件定义与系统实际 schema 的一致性（注册、属性存在性、类型与显示名一致） | 查询 | [metadata/validate-schema-fields.md](references/metadata/validate-schema-fields.md) |

### 标签（命令组 `sensors tag`）

| 工具 | 用途 | 类型 | Reference |
|---|---|---|---|
| `tag.list` | 列出标签定义（身份与状态字段，`--verbose` 附规则摘要）；定位标签对象的第一步 | 查询 | [tag/list-tags.md](references/tag/list-tags.md) |
| `tag.get` | 获取单个标签详情（始终含规则表达式），解释定义、值类型、状态与规则可用性 | 查询 | [tag/get-tag.md](references/tag/get-tag.md) |
| `tag.create` | 创建标签定义，支持 dry-run 只校验不落库；真实创建挂载 AI Agent 目录 | 写入 | [tag/create-tag.md](references/tag/create-tag.md) |
| `tag.update` | 同创建类型安全更新标签（规则、名称、描述、调度、保留、可见性），先预览差异再用审批指纹执行 | 写入 | [tag/update-tag.md](references/tag/update-tag.md) |
| `tag.evaluate` | 触发一个或多个标签计算并同步等待终态；可按 `base_time` 复现历史口径 | 写入（触发计算） | [tag/evaluate-tag.md](references/tag/evaluate-tag.md) |
| （共享）标签规则输入 Schema | `tag.create` / `tag.update` 的 `rule_draft` 规则对象结构与业务语义 | — | [tag/tag-rule-schema.md](references/tag/tag-rule-schema.md) |

### 分群（命令组 `sensors segment`）

| 工具 | 用途 | 类型 | Reference |
|---|---|---|---|
| `segment.list` | 列出分群定义（身份与状态字段，`--verbose` 附规则摘要），用于列举候选与按名过滤 | 查询 | [segment/list-segments.md](references/segment/list-segments.md) |
| `segment.get` | 获取单个分群详情（始终含规则引用与完整规则条件） | 查询 | [segment/get-segment.md](references/segment/get-segment.md) |
| `segment.create` | 创建分群定义，支持 `dry_run` 只校验不落库 | 写入 | [segment/create-segment.md](references/segment/create-segment.md) |
| `segment.update` | 同创建类型安全更新分群（规则、名称、描述、调度、保留、可见性），先预览差异再用审批指纹执行 | 写入 | [segment/update-segment.md](references/segment/update-segment.md) |
| `segment.evaluate` | 触发一个或多个分群计算并默认同步等待终态 | 写入（触发计算） | [segment/evaluate-segment.md](references/segment/evaluate-segment.md) |
| （共享）分群规则输入 Schema | `segment.create` / `segment.update` 的 `rule_draft` 规则对象结构与业务语义 | — | [segment/segment-rule-schema.md](references/segment/segment-rule-schema.md) |
| （共享）行为序列输入 Schema | `rule_draft` 中 `event_sequence`（「先 A 再 B 在 N 天内」）条件的结构与时间窗口约束 | — | [segment/segment-event-sequence-schema.md](references/segment/segment-event-sequence-schema.md) |

## 公共调用规则

- 项目参数统一使用**项目英文名**：全局 `--project <name>`（如 `--project default`）。
  - 除 `context.project-get`（按 ID 反查详情的查询条件）外，**任何业务命令都没有 `--project-id` 选项**；数字项目 ID 由 CLI 内部自动解析并缓存，调用方永远不需要、也不要尝试传 ID。
  - `session-start` 输出的 `default_project_id` 与 `project-get` 输出的 `id` 仅供展示，禁止据此构造 `--project-id` 或把数字当 `--project` 的值。
- 复杂输入优先使用结构化 JSON（`--input -` + 单引号 heredoc）；具体传参方式以目标命令实时帮助为准。
- `--schema`（如命令支持）与 `--dry-run` 请求预览不等于服务端校验；`--dry-run` 服务端预览不等于真实写入。
- 多候选、目标对象不唯一时把候选交还调用方，不自行选择。
- 同一任务内已定位的唯一对象（概览、书签、标签、分群、事件、属性等）直接复用其 ID 与已确认属性，不重复定位或重查。
- 参数或 Schema 错误只根据当前契约修正；认证、权限、项目或写开关错误立即停止并返回修复提示。
- 暂时性网络错误可有限重试；明确不支持的能力返回 `unsupported`，不寻找旁路。
- 采样、截断、空结果等结构事实必须原样保留并传回，业务含义由调用方判断。

## 写操作安全联锁

所有「写入」类型工具执行前必须：

1. **读取现状**：定位唯一目标对象并读取当前状态（`*.list` / `*.get`）。
2. **预览**：用目标命令支持的预览机制（`--dry-run`、`--changes` 等）生成本次输入的变更预览。`--dry-run` 是安全操作、不落库：目标对象不存在或状态异常不阻止预览，仍应先 dry-run 展示请求结构，并把对象现状一并返回。
3. **确认**：向调用方展示变更摘要并取得对**本次输入与目标**的明确确认；输入或目标变化后旧确认失效。
4. **执行**：未获确认不执行真实写入。
5. **回读**：执行成功后按目标能力回读；回读失败时不得宣称最终状态已验证。

## 完成输出

向调用方返回：使用的工具、目标对象、执行阶段、结构化结果、截断或采样状态、`request_id`，以及任何未解决的配置、权限或业务确认问题。

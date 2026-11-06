---
name: metalink-mcp-skill
description: "Use when an agent connected to a remote Wren MCP server answers business data questions about metrics, inventory, trends, comparisons, breakdowns, or top-N analysis. 适用于已有远程 Wren MCP 连接的数据问答，不用于安装、建模或修改业务数据。"
license: Apache-2.0
version: 1.0.3
metadata:
  author: meta
---

# Wren MCP 数据问答标准流程

外部 Agent 负责理解问题、选择工具、组织调用和解释结果；Wren MCP 提供上下文、业务规则、语义查询和执行能力。**MCP 不会自动替 Agent 完成 RAG 或串联查询流程。** 以下步骤由 Agent 执行，工具参数以当前连接实际暴露的定义为准。

本文件定义完整远程问答工作流；包内参考补充参数和边界，服务端初始化 `instructions` 提供核心指引，可选 `wren_workflow` 提供独立的完整摘要。客户端是否将初始化指引交给模型需另行核验；本技能不依赖该能力。工具是否可用及权限参数要求，以当前服务的工具定义为准。

默认只读。只有第 7 步允许在满足条件时保存查询经验；不安装或运行本地 Wren，不读取本地业务项目，不索取数据库凭据，不维护索引或修改业务数据。

包内参考通过宿主的技能文件读取能力加载，不传给 MCP 资源接口：

| 何时读取 | 包内参考 |
|---|---|
| 首次使用本流程；处理检索、知识资源或保存经验 | [memory.md](references/memory.md) |
| 构造第一条 Cube 查询；处理模式、日期、过滤或库存 | [cube-query.md](references/cube-query.md) |
| 编写语义 SQL；处理 JOIN、分组或执行错误 | [wren-sql.md](references/wren-sql.md) |

## 先明确当前问题

提取分析对象、指标、时间、范围和结果粒度。用户明确要求优先于业务默认值；缺少条件时先读取规则，只有不同解释会实质改变结果且没有可用默认值时再澄清。不要自动扩大到用户未要求的排名、同比环比或归因分析。

先确认本次任务是仅展示 SQL、仅校验 SQL，还是需要执行，并识别当前模式：

| 模式 | 发现与查询范围 |
|---|---|
| 普通模式 | 优先已声明 Cube；需要语义 SQL 时核验相关公共 MDL 模型与字段 |
| API 行权限模式 | 先跨 Cube 检索，再选择 Cube；SQL 工具必传 `cube`，不传 `business_model`。每个独立 SQL 分支以该 Cube 的 `baseObject` 为根，来源仅限其递归 joins，保留声明的 JOIN 条件、类型和固定过滤 |
| 文件权限模式 | 用 `list_business_models` / `describe_business_model` 确认本步的 `sql_entries`、Cube 和可见成员；SQL 工具传声明的 `business_model`，不跨范围推导来源 |
| 无连接模式 | 只使用实际暴露的检索与 `dry_plan` 等规划工具；返回规划结果并说明未执行，不声称获得业务数据 |

检索结果不扩大查询权限。API 模式只采用所选 Cube 的权限，共享 Model 不带入其他 Cube 的权限；服务端补齐权限依赖且不放大事实行，并强制固定过滤。数据库连接凭据与请求 Cookie 独立。

## 七阶段标准操作流程

### 1. 了解模型：先获取问题上下文

**每个新业务问题首次生成查询前，调用 `get_context(question)`。** 使用当前问题的实体、时间和指标；不能因为问题简单、知道 Cube 名称或上一问已有 schema 就跳过本问题的检索。聚合分析可先用 `item_type="cube"` 定位候选，具体筛选与补充检索见 memory 参考。

根据检索候选，用 `describe_cube` 核验相关 Cube；需要补足候选时用 `list_cubes`。仅在问题需要基础模型信息或超出 Cube 参数表达能力时，用 `list_models` 和 `describe_model` / `describe_schema(model=...)` 核验当前模式范围内的公开模型。编写跨模型 SQL 前，核对公开的 `baseObject` / `base_object`、相关模型与字段，并对照已返回的关联声明或历史 SQL 候选检查 JOIN 类型、完整 ON 键和固定过滤；复用仍有效的信息，只补查缺项。某些模式的 describe 不含关联细节，不反复调用或猜补；当前关联兼容性有疑问时先校验。遵循声明的 JOIN 类型，不默认所有 JOIN 都是 LEFT。

`get_context` 与 `recall_queries` 始终跨 Cube 检索，不按选定 Cube 过滤或排序，也不用 `model_name=选定Cube` 代替发现。schema 的 `cube`（Cube 成员）与 `cubes`（Model/字段归属）用于识别候选；共享 Model 可以属于多个 Cube。选定 Cube 的精确成员由 describe 工具核验；既有 MDL Model/列检索过滤仍按工具定义使用。

检索片段提供候选，不授予查询权限；内部源、底层表和历史 SQL 不自动成为可用的公共语义入口。

### 2. 读取业务规则

首次问答调用 `get_instructions()`，读取 `knowledge/rules/` 的口径。后续仅在同一项目、身份和业务上下文仍适用时复用；上下文变化时重新读取。

落实日期边界、业务时区、单位、默认过滤、指标定义和数据时效。财务周/月必须按业务日期映射确认，不能套用自然周/月。规则引用的专题知识按需先用 `list_knowledge()` 发现，再用 `read_knowledge(path="guides/example.md")` 读取正文。路径相对于 MCP 服务器的 `knowledge/`，不能用智能体本机的 bash/read 查找；不能假定 `get_context` 已检索全部业务文档。旧服务未提供读取工具时，按 memory 参考处理宿主资源能力或缺失正文。

### 3. 召回历史案例

**每个新业务问题首次生成查询前，调用 `recall_queries(question, limit=3)`。** 规则和 schema 已明确也要召回；不能在全部查询执行完后才补做这一步。

核对案例的业务目标、指标、日期、粒度、模型、JOIN、过滤和聚合结构。`source:seed` 是自动示例，`source:user` 只说明来源，两者都不证明业务口径已验证。

召回缺少必要结构时，围绕缺失的 JOIN、粒度、过滤或聚合做一轮定向补查：先用 `list_stored_queries`（省略 source，包含所有可见来源），需要正文时再用 `list_knowledge` → `read_knowledge` 读取相关 `sql/*.md`。目录不是正文，有上限的列表不是全部历史。按以下出口结束补查：

- 候选已补齐当前查询所需结构：结束检索，核验后使用。
- 本轮相关候选无适用案例：仅依据已核验定义和规则继续，不要求证明全部历史都没有案例。
- 必要业务定义或可核验关联仍缺失：说明缺口或澄清，不凭“没有案例”猜测结构。

阶段 1–3 完成后再构造业务查询。同一问题、范围和缺项复用已有上下文，不重复相同参数的检索；新线索或上下文变化才刷新相关检索，新问题重新获取 context 和 recall。某检索工具未暴露或明确不可用时，按 memory 参考降级并说明限制，不伪称已检索；认证或权限失败不适用该降级。

### 4. 选择查询方式

根据第 1 步已核验的定义判断 Cube 覆盖；缺少定义时才补充目录或 describe。**已声明指标及关联维度覆盖问题时优先 `query_cube`**，不因为参数错误就改写指标 SQL。

- 有 `measures` 为 aggregate：每店销售总额、库存数量/金额等汇总使用已声明指标。
- 无 `measures` 为 detail：投影已声明的 `dimensions`，保留明细行；不自动去重或聚合。
- `query_cube` 参数无法表达必要逻辑，但来源仍在当前授权语义范围内：读取 SQL 参考，使用已核验公共 MDL 入口编写 SQL；API 模式仍绑定所选 Cube。
- 没有可用 Cube 范围覆盖所需来源：API 模式说明范围缺口，不转查无关 Model；其他模式依其公开入口和权限判断。

组合过滤时先核对 [Cube 过滤器](references/cube-query.md#过滤器)：多项条件按 AND；任一匹配按精确候选与多关键词/跨字段 OR 选择入口。

复杂问题拆成必要子问题，各自确认模型和口径；跨模型分步查询时传递已返回的编码，保留未匹配、多候选和一对多关系。每次 `run_sql` / `query_cube` 都提供该调用具体回答的 `question`，使用用户语言描述指标、范围、日期和粒度；翻页与同范围纠错沿用该子问题。该参数在接口中仍可省略。

### 5. 校验并执行

| 当前任务或触发条件 | 操作、完成与停止条件 |
|---|---|
| 仅展示 SQL | Cube 用 `query_cube(sql_only=true)`，语义 SQL 按需要用 `dry_plan`；返回预览并说明未执行，到此结束，不执行或保存 |
| 仅校验 SQL | 用 `dry_run` 返回校验结果，到此结束，不执行或保存 |
| 要执行，且用户或项目要求先校验 | 完成要求的校验，失败按第 6 步处理；通过后才执行 |
| 要执行，且有具体疑问 | 明确待核验的日期、函数、关联或分组问题；Cube 按需预览，SQL 按需 `dry_run`，解决疑问后执行 |
| 要执行，定义、范围和参数已核验且无具体疑问 | Cube 直接 `query_cube(sql_only=false)`，SQL 直接 `run_sql`；新查询、普通修改或存在 JOIN 本身不强制预览/校验 |

Cube 预览检查完整业务参数对应的 SQL，不连接数据库，也不等于 `dry_run`。规划成功不证明执行成功。已选择的校验失败须按错误契约解决，不因校验可选而跳过已知失败或拒绝。执行沿用已核验的业务参数和范围；SQL 提交原始语义 SQL，Cube 仍调用 `query_cube`，不将展开 SQL 重新交给 SQL 工具。参数改变后只重新判断相关疑问。详细 SQL 检查见 [SQL 参考](references/wren-sql.md)。

日期筛选与分组分开决定：只筛日期优先 `time_dimension="已声明时间字段"` 加两个字符串的 `date_range` 数组；按日/月分组才加 `:granularity`。数组语法不表示闭区间，语义为 `[start,end)`。顶层范围、时区、兼容语法和分页细节见 Cube 参考。

### 6. 核对并解释结果

检查 `columns`、`rows`、`row_count`、`format`、`truncated`、`partial`。`format="positional"` 时按列位置解释数组，保留重复列名；不能转换为覆盖同名列的字典。

- `truncated=true` 不是全量。全量分页需稳定完整排序，按实收行数推进 offset；SQL 在原始语句中分页，`run_sql` 没有 offset 参数。主动 LIMIT / TOP N 即使未截断也只是子集。
- 不在截断明细上求总体指标，不直接累加比率、均值、去重数或跨日库存快照。`partial=true` 只回答已返回部分，说明缺项。
- 回答包括实际数据、单位、时间与范围、关键口径和完整性限制。空结果不等于 0，执行成功不证明业务数据完整。
- 先遵守服务端显式 `max_correction_attempts`、`max_internal_retries` 和 `retry_same_query`。未给显式预算的普通参数/语法错误，同一子问题累计最多两次修正；更换错误类型或工具不重置计数。相同错误且没有新增证据时立即停止；修正须有错误信息或已核验定义作为依据，不盲改。保留业务范围、分组、过滤、身份和日期。
- `invalid_query` 的 `cube_join_type_mismatch` 按 `can_correct_arguments=true`、`retry_same_query=false`、`max_correction_attempts=1`：核对公开关联的 JOIN 类型、完整 ON 键和固定过滤，必要时按第 3 步补查历史，修正后验证一次；不得原样重放，修正仍失败则停止。
- `query_not_available` 仅在 `can_retry_visible_parts=true` 且 `max_internal_retries` 允许时，对可见部分最多内部重试一次；否则停止。该标记不表示可任意修正 SQL。不得换 Cube、模式、身份或日期绕过拒绝。
- 数据库断连、认证或权限失败按实际状态报告；不自动重放执行中途失败的查询。前置步骤失败时停止依赖它的后续分析。

### 7. 保存经验

仅在服务已开启写入并实际暴露 `store_query`、答案与口径已确认正确、用户已授权本次保存或既有自动保存策略时，调用 `store_query` 保存问题与**已验证的原始语义 SQL**。已有授权无需重复询问，未授权的普通问答不主动要求开启保存。

仅 Cube 参数或预览展开 SQL 不能冒充已验证的原始语义 SQL；没有合适 SQL 时跳过保存。不要为完成这一步另写并执行不必要的 SQL。API 模式保存必传 `cube`，服务端只检查 SQL 范围，不为保存调用权限 HTTP 或数据库；旧知识仍共享，缺少元数据时 `cube=null`。保存范围、参数和边界见 memory 参考。

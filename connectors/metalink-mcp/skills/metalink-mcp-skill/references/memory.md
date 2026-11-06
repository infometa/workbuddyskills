# 上下文、业务规则、历史案例与经验保存

本文件补充[主技能](../SKILL.md)的第 1–3、7 阶段，不另定义调用顺序。RAG 由 Agent 显式调用，不会因使用 `query_cube` / `run_sql` 自动发生。

## 三类知识分别读取

| 内容 | MCP 入口 | 边界 |
|---|---|---|
| 问题相关的 schema | `get_context(question, limit=5, item_type?, model_name?)` | 检索模型、字段、Cube 等候选；不等于最终字段核验 |
| 业务规则 | `get_instructions()` | 读取 `knowledge/rules/`；不自动加载 guides 或本技能参考 |
| 相似问题与 SQL | `recall_queries(question, limit=3)` | 历史示例作为候选思路；需验证相关性和当前适用性 |
| 精确模型/Cube 定义 | `list_models` / `describe_model`、`list_cubes` / `describe_cube`、`describe_schema(model=...)` | 核验公开字段和成员；某些权限模式不公开表达式、关系或基础模型 |
| 业务模型范围 | `list_business_models` / `describe_business_model`（如暴露） | 获取本步骤的 `sql_entries`、Cube 和可见成员 |
| 完整 schema | `describe_schema()`、`get_mdl()` 或 `wren://mdl` | 仅用户明确要求全项目检查时使用；普通问答使用定向检索和公开定义 |
| 浏览案例 | `list_stored_queries(source?, limit?)` | 召回缺少必要查询结构时补查；省略 source 包含所有可见来源，默认最多 10000 条，有限列表不证明历史完整 |
| 专题知识 | `list_knowledge()` → `read_knowledge(path)` | 列目录与读取正文是两个动作；文件在 MCP 服务器上 |

## 问题检索如何执行

新业务问题先调用 `get_context` 并核验候选的公开定义，加载或复用规则，再调用 `recall_queries`；完成后才构造业务查询。相同问题的翻页、同范围参数修正复用已有上下文。仅上一问读过 schema、熟悉业务或目录已列出 Cube，都不能替代当前问题的首次检索。

`get_context` 与 `recall_queries` 保持跨 Cube 的共享检索，不增加 cube 过滤或按当前 Cube 排序。schema 结果的 `cube` 表示 Cube 成员归属，`cubes` 表示 Model/列的全部 Cube 关联；共享 Model 可以列出多个 Cube。检索后依据问题确定执行 Cube。旧 SQL 无归属元数据时返回 `cube=null`，仍可作为需重新核验的跨 Cube 参考。

### Schema 检索

1. 保留问题中的分析对象、指标、时间与业务限定，不拼接整份规则或大量无关词。
2. 聚合分析优先 `item_type="cube"` 找候选；需要核对指标时拆成具体子问题，用 `item_type="measure"`；字段用 `item_type="column"` 或 `"cube_dimension"`，日期用 `"time_dimension"`。仅使用当前服务支持的类型。
3. 保留跨 Cube 发现和召回，不用 `model_name=选定Cube` 限定检索或模拟 Cube 过滤。选定 Cube 后用 `describe_cube` 等公开定义工具核验精确成员。既有 MDL Model/列的 `model_name` 过滤仍可按工具定义用于相关模型检索；它不授予执行权限，也不替代跨 Cube 发现。
4. 默认 limit=5。若混合类型召回偏题，先拆分问题、限定类型或核验候选模型；不要仅提高 limit 将全部无关片段塞入上下文。可补充已经核实的中文别名/字段名，不凭猜测生成字段。
5. 对将使用的模型/Cube 做公开定义核验，可复用仍有效的 describe 结果。`describe_business_model` 已返回所需定义时不重复调用；跨模型 SQL 须核对公开的 baseObject、模型与字段，并对照已返回关联声明或历史 SQL 候选检查 JOIN 类型、完整 ON 键和固定过滤。describe 可能不含关联细节，不猜隐藏结构；当前关联兼容性有疑问时先校验。schema 检索可能包含内部源信息，查询工具仍独立执行授权，召回结果不能扩大权限。

例如，问题“上周各门店销售额与毛利率”先检索相关 Cube，再按需要检索毛利率定义和财务周日期映射；不是用一个长问题检索出的前五个字段直接拼 SQL。

`get_context` 返回 `strategy="full"` 时已提供完整描述，这也是有效的上下文获取，不需要强迫它使用向量搜索。`strategy="search"` 时检查 `results` 的相关性：返回非空不等于命中；无结果不等于模型不存在。

### 历史 SQL 召回

对当前问题调用 `recall_queries` 后逐项检查：业务目标、指标口径、模型、粒度、日期逻辑、JOIN、必要过滤与聚合结构是否适用。主题相近不足以证明结构可复用。

- `source:seed` 表示自动生成的示例，不代表真实业务已验证；对编码求和等无意义示例直接弃用。
- `source:user` 只标记来源，不表示已验证。所有案例都必须按当前公开定义、规则和授权重新核验，不能直接重放固定部门、商品和日期。
- 召回缺少所需 JOIN、粒度、过滤或聚合结构时，针对缺项做一轮补查：用 `list_stored_queries`，省略 source 以包含所有可见来源；需要正文时调用 `list_knowledge`，再用返回路径 `read_knowledge(path="sql/example.md")` 读取相关候选。默认最多返回 10000 条，显式 limit 也可能限制列表；无需穷尽全部历史。目录不是正文，补查不能替代跨 Cube 召回或绕过读取权限。
- 候选足以支撑当前查询时结束补查。本轮相关候选无适用案例时，仅依据已核验模型和规则构造新查询；若必要业务定义或可核验关联仍缺失，说明缺口或澄清，不猜结构，不为复用示例改变用户问题。
- 同一问题、范围和缺项不重复相同参数的检索；仅新线索或上下文变化才刷新相关检索。工具缺失按下节降级；远程查询 Agent 不安装依赖、建索引或批量写入案例。

## 能力缺失和缓存

| 状态 | 处理 |
|---|---|
| 本问题已完成检索，继续翻页/修正参数且上下文不变 | 复用本问题检索和已核验定义 |
| 新问题、切换分析对象/模型、身份/项目变化或定义已更新 | 刷新相关检索；新问题重新执行 get_context 和 recall_queries |
| 未暴露某个检索工具 | 使用可用的目录、describe、规则继续，说明缺少哪类检索 |
| 工具明确返回缺依赖、索引不可用或过时 | 说明限制，改用可用的定义核验；需要维护时联系服务管理员，不自行安装或建索引 |
| 空结果或明显不相关 | 定向补查或按无匹配处理，不报告为权限问题，不伪称已找到参考 |
| 认证、权限失败或 query_not_available | 遵守主技能的停止/受限重试条件，不能按“工具缺失”降级绕过 |

已加载的规则和精确定义在同一项目、身份及适用范围内可复用；这不免除新问题的检索。检索结果可用但缺少必要业务口径时，补读知识或澄清后再查询。

## 业务知识资源

`list_knowledge` 只返回可见文件名。若列出 `guides/example.md`，调用 `read_knowledge(path="guides/example.md")`，从返回的 `content` 获取正文。若业务规则仍指向 `wren://knowledge/guides/example.md`，将 URI 中 `wren://knowledge/` 后的相对路径传给读取工具，不传 URI 或额外的 `knowledge/` 前缀。

这些文件位于 MCP 服务器上；客户端的 bash、read、文件搜索不能代替服务端读取。目录列出文件不代表已经读过正文；读取失败或 `content` 为空时，不能声称已获取该指南的业务口径。

`wren://instructions` 对应业务规则，`wren://agents` 对应项目公开的代理说明（如有）。只读取实际存在且当前允许访问的资源。项目说明中的 CLI 安装、索引或默认写入流程不自动适用于远程问答。

`read_knowledge` 不依赖宿主资源能力。仅当旧服务没有此工具时，才使用宿主实际提供的 MCP 资源读取入口访问 `wren://knowledge/{path}`；`resources/read` 是协议方法，不是 Wren 工具名。两种入口都不可用时，说明知识正文无法读取，使用已有规则、get_context 和 describe；若缺失正文影响必要口径，先澄清，不假装读过、不去本地查找服务器文件。包内 `references/*.md` 由技能文件加载，不能通过 `wren://knowledge/` 获取。

## 保存已确认经验

主技能第 7 步为可选写操作。调用前必须同时满足：

1. 当前服务允许写入，实际暴露 `store_query`。
2. 查询成功，结果与业务口径已确认正确；仅“没有报错”不等于确认。
3. 用户已授权保存本次案例，或已明确建立适用于本次任务的自动保存策略。
4. 有已执行成功、结果与口径已核验的原始语义 SQL，且适合成为可复用案例；不要求为保存额外调用 dry_run。

API 行权限模式参数为 `store_query(nl_query, sql_query, cube, datasource?, tags?)`，`cube` 必传；服务端在写文件前只校验 Cube SQL 范围，不调用权限 HTTP 或数据库。其他模式以运行时工具定义为准。`nl_query` 保留已确认的业务意图、口径和时间条件；`sql_query` 保存对应的原始语义 SQL。不保存数据库凭据、会话 Cookie、结果明细或未经核验的 SQL。

只执行 Cube 时不把编译后的物理 SQL 当成原始语义 SQL 保存，也不为保存另做冗余查询。未开启写入、未授权或没有适合的 SQL 时直接跳过；这不影响正常回答。已授权的保存失败时区分“业务查询成功”与“经验未保存”，不重复执行业务查询；仅服务实际确认后才声明保存成功。

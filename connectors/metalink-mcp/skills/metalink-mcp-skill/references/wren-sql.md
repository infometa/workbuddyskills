# 远程语义 SQL：编写、校验与诊断

在 `query_cube` 参数不能表达必要逻辑、需要公共语义 SQL，或需要诊断 SQL 时读取。API 模式下，参数表达不足仍可在所选 Cube 的 SQL 范围内写语义 SQL；没有可用 Cube 范围覆盖所需来源时，说明范围缺口，不能改查无关模型。已声明业务指标优先使用 [Cube 查询](cube-query.md)，避免自行改写快照、比率或关联口径。

## 输入 SQL 与模型范围

Wren 将公开语义模型展开为底层查询（通常包含 CTE），再生成目标数据库 SQL。智能体写的是已公开的语义入口；展开结果用于检查执行逻辑。

- 先完成[主技能](../SKILL.md)的 get_context、公开定义核验、业务规则和 recall_queries 步骤，再使用当前公开的模型和列名编写 SQL；仍有效的规则和精确定义可复用。
- 跨模型 SQL 先核对当前公开的 baseObject、关联模型、声明的 JOIN 类型、完整 ON 键和固定过滤；复用仍有效的已核验定义，只补查缺项，不猜隐藏结构或默认 LEFT JOIN。同一语义范围内才可使用已核验的关联、CTE 或 UNION；共享物理表不能证明不同业务模型可以合并查询。Cube 的 baseObject、内部源和预览里的物理表名不自动成为公共 SQL 入口。
- 不将 dry_plan 或 Cube sql_only 的生成 SQL 重新提交给 run_sql。SQL 执行提交原始语义 SQL；Cube 执行调用 query_cube。
- 从 `get_data_source()`（如暴露）或项目上下文确认方言。按该方言写日期、字符串和函数表达式；存在具体兼容性疑问时用 dry_run 校验，不假设引擎能修复任意数据库语法差异。
- 显式列出需要的列和清晰别名。隐藏列、关系字段、关联目标的列是否可选，以当前公开 schema 为准，不从 `SELECT *` 或底层表猜测。

API 模式先跨 Cube 检索，再根据问题选择 Cube；`cube` 必传，`business_model` 与未知参数被拒绝。SQL 使用 MDL Model，每个独立分支须以选定 Cube 的 `baseObject` 为根，相关来源只能来自递归 joins，必须保留声明的条件与 join 类型。仅选定 Cube 的权限生效，共享 Model 不带入其他 Cube 的权限。服务端自动补齐权限依赖且不放大事实行，Cube/join 固定过滤始终必需。原生连接凭据与 Cookie 权限独立。文件权限模式先通过 `list_business_models` / `describe_business_model` 核验 `sql_entries`，SQL 工具传声明的 `business_model`；普通模式按当前公共模型和运行时工具定义执行。

`get_context` 返回的关联声明或历史 SQL 可用于核对结构，不扩大查询权限。某权限模式的 describe 不公开完整关联时，不假定重复 describe 能补齐；按 [memory 参考](memory.md) 针对缺项补查一轮。已有模板可保留其完整结构，核验当前公开模型与字段，再用 `dry_run` 校验尚不确定的关联。候选足够就结束检索；无适用案例时仅从已核验定义继续，必要关联仍不可核验时说明缺口或澄清。

## 粒度、日期与关联

- 选择聚合值和非聚合维度时，把每个选中维度写入 GROUP BY，即使 WHERE 已限定它只有一个值。Wren 不补写缺失分组。
- “期间各部门合计”只按部门分组；“每天各部门”才加日期。需要标量总额时不额外选部门/日期。
- 时间范围通常用 `>= start AND < end`，结束日需要包含时换算为下一边界；不删去日期来避开错误。字符串月键按其实际类型与业务定义处理。
- 明确 JOIN 键和基数，防止一对多关联重复放大金额；不要用无依据 DISTINCT 掩盖粒度错误。跨业务模型的名称补全通过分步查询和已返回键值完成。
- SQL 的 `<>`、`NOT IN` 同样不会保留 NULL。业务需要时显式表达 OR / IS NULL；例如 `channel <> 'outlet' OR channel IS NULL`。
- 每月 TOP N 需要分区排名或按月分别查询；全局 LIMIT 不会对每月重置。先确认并列规则：固定 N 行与包含并列名次的结果不同。
- 对均值、比例、去重数和库存快照保留已核验的指标口径，不能在分页或分组后直接求和。

## 三个 SQL 工具

| 工具 | 用途 | 能证明什么 |
|---|---|---|
| `dry_plan(sql, cube)`（API 模式） | 展开语义 SQL，返回目标方言 SQL | 能完成计划/转换；不连接数据库 |
| `dry_run(sql, cube)`（API 模式） | 对连接的数据源校验输入 SQL | 当前连接下能通过校验；不返回查询数据 |
| `run_sql(sql, cube, limit?, question?)`（API 模式） | 执行输入 SQL并返回结果 | 仅实际返回的数据支持回答 |

先确认任务的结束点：用户仅要求展示 SQL 时按需 `dry_plan`，返回预览并说明未执行后结束；仅要求校验时返回 `dry_run` 结果后结束。两者都不继续执行或保存。任务包含执行时，项目规则或用户要求先 `dry_run` 就必须校验；否则核对公开模型、字段、业务口径和查询范围后可直接 `run_sql`。对语法、类型、函数兼容性、关联或分组有具体疑问时才按需校验。新查询、普通修改或包含 JOIN 本身不强制校验；修改后重新判断相关疑问。

选择 `dry_run` 时，处理其返回的错误后再执行；普通可纠正错误修正后仍需校验该疑问，认证、权限、连接错误及 `query_not_available` 按主技能停止/重试规则处理，不因校验可选就跳过已知失败。通过后，将同一原始语义 SQL 和Cube 参数（API 模式必传；其他模式按工具定义）交给 `run_sql`。`dry_plan` 仅在需要检查展开逻辑时使用，规划成功不证明数据库执行成功。

每次执行提供当前调用的具体 `question`，包括其指标、过滤、日期和粒度；翻页和同范围纠错沿用该子问题。该参数仍可省略，不改变 SQL 或授权。

`query_cube` 的指标、维度等结构化参数不传入这三个工具；API SQL 仍必须传 `cube`。Cube 预览只用 `query_cube(sql_only=true)`，其输出不作为 `dry_run` 或 `run_sql` 的新输入。

下例仅当 sales 是当前公开语义入口且包含这些列时适用：

```sql
SELECT dept_code, SUM(sale_income) AS revenue
FROM sales
WHERE acc_date >= '2026-09-01'
  AND acc_date < '2026-10-01'
  AND (channel <> 'outlet' OR channel IS NULL)
GROUP BY dept_code
ORDER BY dept_code
```

## 诊断与停止条件

服务端显式 `max_correction_attempts`、`max_internal_retries` 和 `retry_same_query` 优先。没有显式预算的普通参数/语法错误，同一子问题累计最多两次修正；换工具或错误类型不重置计数。相同错误且没有新增证据时停止；依据错误信息或已核验定义修正，不盲改，不改变业务范围、分组、过滤、身份或日期。`query_not_available` 只能依其可见部分标记和预算处理，不使用普通错误的默认预算。

| 现象 | 下一步 |
|---|---|
| 找不到模型/字段、列歧义 | describe 当前公开模型，核对名字和别名；不猜物理表名 |
| invalid_query / cube_join_type_mismatch | 按 `can_correct_arguments=true`、`retry_same_query=false`、`max_correction_attempts=1`，核对公开关联的 JOIN 类型、完整 ON 键和固定过滤；必要时按 memory 参考补查历史案例。保留业务范围修正后验证一次，不原样重放；修正仍失败则停止 |
| GROUP BY 错误 | 按用户期望粒度修正原始 SQL 的选列和分组；若来自已选择的 dry_run，修正后重新校验，否则按需校验 |
| dry_plan 成功、dry_run 失败 | 对照展开结果与错误，定位类型、函数、关联或数据库状态；计划成功不代表数据库校验成功 |
| 日期、函数或类型错误 | 按实际方言和字段类型修正，保持原始业务范围 |
| MySQL 2006/2013 等断连 | 报告连接状态；修改 SQL 或反复 dry_run 不能修复断连；不自行重放中途失败的执行 |
| 认证/权限失败或 query_not_available | 遵守 [主技能](../SKILL.md) 的停止和受限重试条件，不换模型/模式绕过 |
| 成功但零行 | 如实说明条件下无返回数据，不改商品、部门或日期来制造结果 |

复杂相关子查询、递归 CTE 等能力以当前服务实际校验为准；不因引擎通常支持 CTE 就保证所有形式均可执行。`get_data_source` 成功仅说明读到配置，不代表数据库已恢复。

## 返回结果与分页

结果映射、重复列名、partial 和截断判断见主技能。run_sql 的 limit 是单次返回上限（默认 1000，最大 10000），不是总体记录数，也没有 offset 工具参数。需要分页时在原始语义 SQL 中按实际方言写稳定排序及分页，保持过滤、授权范围和结果粒度不变。

发现重复列名时按 columns 的位置保留每个值；后续可在原始 SQL 中加明确别名，但不擅自丢列、加总两列或猜测哪列正确。未确认排序键能区分全部结果行时，不以翻页成功宣称已取得全量。

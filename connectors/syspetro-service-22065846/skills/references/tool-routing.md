# PROPDB Full 工具路由

调用时以连接别名 `propdb-full` （syspetro-service-22065846）的实时 `tools/list` 为准；宿主生成工具命名空间时可能规范化为 `propdb_full`，也可能把长名称截断并添加哈希，因此按业务描述、输入字段组合和本连接内唯一匹配。零个或多个工具同时匹配时停止，不把下表规范名或某次哈希当成永久运行时名称。

实时 schema 已确认以下 6 类运行工具都接受顶层 `unitSet`。每次最终运行均显式传入：用户未指定时传 `"SI"`，用户明确选择时仅传 `"SI"`、`"MET"` 或 `"ENG"`。查询与静态前置工具不传此字段。

本文件只暴露查询、静态、运行和单位工具，不包含输入文件导出映射。所有扫描型曲线在用户未指定密度时默认 50 个等距数据点，对 schema 中表示区间数的 `quantity` 传 `49`。

## 1. 查询与对象解析

| 技术工具名 | 业务用途 | 输入 |
| --- | --- | --- |
| `post_sys_component_app_mcp_get_mixture_components_by_keywork` | 按名称、别名、公式或 CAS 检索组分 | `keyword` |
| `post_sys_component_app_mcp_get_component_details` | 单组分详情 | `Id` |
| `post_sys_component_app_mcp_get_components_details` | 多个已知 ID 的批量详情 | `ids` |
| `post_sys_prop_app_mcp_get_component_dp_propeties` | 单组分物性列表 | `Id` |
| `post_sys_prop_app_mcp_get_mixture_properties` | 已选组分组合的混合物物性数据可用性 | `ids` |

非 ID 组分先逐个调用关键词工具。中文或其他本地化组分名无结果时，按 [parameter-rules.md](parameter-rules.md) 静默生成标准英文名等有界回退词，依次复用同一工具；不得在未尝试可用翻译前就向用户索要 Benzene/CAS 一类标识。不要为空词、宽泛词或 ID 枚举调用。批量详情不是默认消歧步骤；搜索候选足以唯一化时不再补详情。

一次列出多个组分不等于用户已经选择了多组分查询口径。用户只说“查询/查看组分 A、B、C”而没有说明详情或物性目标时，先分别用关键词工具解析身份；解析后一次性确认以下目标，确认前不调用其他查询工具：

- 各自组分详情：对已确认 ID 调用一次批量详情；
- 逐个纯组分物性列表：按组分分别调用单组分物性列表，不调用混合物物性工具；
- 所选组分组合的混合物物性数据可用性：用完整 ID 列表调用一次混合物物性工具，不用逐个纯组分结果拼接。

用户已经明确“各自/分别”“混合物/组合/体系”或“组分详情”时按对应目标直接继续，不重复确认。关键词工具只有在宿主成功接收响应且返回成功空数组时才表示未命中；output schema 校验失败属于接口响应契约失败，不得表述为“未找到该组分”，也不得猜测 ID 后继续。

候选来自联网资料、模型知识或用户提供都不改变数据库门禁：外部信息只用于形成有限检索词，按 [parameter-rules.md](parameter-rules.md) 的数据库存在性白名单逐项核验。只有关键词响应中的唯一精确匹配记录可以进入最终组分结果；名称、分子式、CAS、IUPAC 名和 ID 均取自该记录。不要把未命中候选、外部 CAS 或模型补充的同系物/异构体混入 PROPDB 结果，也不要为寻找更多命中项扩展成无界枚举。关键词响应本身包含多个数据库候选时，可以按既有多候选规则展示这些 MCP 记录用于消歧，但不能把它们直接当成外部候选的最终匹配。

## 2. 混合物分析

前置：解析全部组分 → `get_sys_prop_app_mcp_get_mixture_calc_statis` 获取方法、基准、变量、相态等 → 每个已选物性调用 `get_sys_prop_app_mcp_get_units_by_property_set_type`（参数 `PropertySetType`）获取单位。

提交工具：`post_sys_task_record_run_mixture_calc_of_mixture_analys_276e5441`。

业务参数为 `unitSet,name,basis,basisUnitKey,compValues,propertySets,control*,reference*`。`compValues` 为 `{key:组分ID,value:组成}`；物性集含 `name,propType,propUnit,phases`。schema 中的 `siM_LEVEL,proP_LEVEL` 是内部参数，调用时省略并使用服务端默认策略。

## 3. 二元相平衡

前置：按用户顺序解析恰好两个组分 → `get_sys_prop_app_mcp_get_mixture_calc_statis` 获取实际方法、分析类型、基准和单位 → 校验组成扫描与 Txy/Pxy 对应扫描。

提交工具：`post_sys_task_record_run_mixture_calc_of_binary_analysis_by_task`。

业务参数为 `unitSet,propMethod,componentIds,analysisType,basis,componentBasis,vary,start,end,quantity/increment/valueList,typeUnitKey,typeVary,typeStart,typeEnd,typeQuantity/typeIncrement/typeValueList`。`componentBasis` 必须是这两个组分之一；`siM_LEVEL,proP_LEVEL` 省略并使用服务端默认策略。

### 二元相平衡结果投影

Txy 与 Pxy 的一次成功任务分别对应一个面板，但每个面板必须绘制两条相线：液相线（bubble/泡点）和汽相线（dew/露点）。不能因为服务返回包装中的 `series` 只有一条就把二元结果降级成单组分 T–x 图。

1. 优先解析 `result.items`。按 `componentIds` 顺序把 `liquid_MOLEFRAC_n`、`vapor_MOLEFRAC_n` 的后缀 `n` 映射到组分；Txy 取同一行的 `temp`，Pxy 取 `pres`（或明确的压力字段）作为 y 值。
2. 分别形成 `(液相组成, y)` 和 `(汽相组成, y)` 两组真实点。若两组横坐标不一致，建立排序去重并集；每条系列只填入自己的真实坐标，其他位置填 `null` 以断线，禁止插值、平滑、复制或交换两相。
3. `series` 仅作为展示元数据或在 `items` 缺失时的后备事实来源。若它的标题、横轴或条数与明确的 `items` 字段冲突，以 `items` 为准并记录响应语义缺口。
4. 两条系列各自至少需要 2 个有效点；缺少任一相组成列且无法从 `series` 恢复第二条系列时，只能交付 `partial` 单相诊断，不得命名为完整 Txy/Pxy 或 T–x–y/P–x–y。

## 4. 多元闪蒸

前置：解析全部组分 → `get_sys_prop_app_mcp_get_flash_analysis_statics` 获取闪蒸类型、方法、基准和单位 → 构造 `block`、`streamsIn` 和输出流股名。

提交工具：`post_sys_task_record_run_mixture_calc_of_flash_analysis_by_task`。

业务参数为 `unitSet,propertyMethod,componentIds,block,streamsIn,streamNameVap,streamNameLiq`。`block` 包含闪蒸类型和温度、压力、热负荷、汽化率条件；`streamsIn` 使用组分 ID 与组成构造流股。

## 5. 温度相关纯组分物性

普通前置：解析组分 → `post_sys_prop_app_mcp_get_pure_prop_t_dep_statis`（参数 `id`）获取静态信息。不要为核对 `canCalcPureProperty` 额外调用单详情。多物性任务随后逐项执行：核对当前物性的相态、公式和适用温区 → 调用 `get_sys_prop_app_mcp_get_units_by_pure_prop_tdep_type`（参数 `typeKey`）获取当前物性输出单位 → 参数完整则运行当前物性。单位失败只跳过当前项。

临界、超临界、相变、饱和、跨公式边界或多相态公式任务增加一次 `post_sys_prop_app_mcp_get_component_dp_propeties(Id)`，从返回业务字段按缩写精确读取 `TC/PC`，按需读取 `TPT/TPP`。温压单位不一致时使用第 8 节系统单位工具统一后再比较。然后执行 [state-path-routing.md](state-path-routing.md)；不得用本地或外部物性库替代最终计算。

当前静态输出 schema 只明确声明：

- `properties`：递归 `LabelValueModel` 列表；
- `temeratureUnits`：温度单位列表，保留源拼写；
- `pressureUnits`：压力单位列表。

schema 没有明确说明 `properties[].childs` 的层级是否承载相态或公式，也没有独立声明 `phaseTypeKey`、`formulaKey` 的来源；最终运行需要这两个输入。宿主成功返回后，只有业务响应能明确映射全部所需 key 时才继续。缺任一来源时停止并报告接口契约缺口，不从标签、递归层级、`ext/ext1`、拟合公式接口或领域常识猜测。

用户要求近临界或超临界性质时，不额外要求名为 `Supercritical` 的相态。先依据 `TC/PC` 和公式覆盖分类；只要存在合法 key 就按固定默认优先级直接运行完整请求范围。`Ideal_Gas`、`Gas`、`Liquid` 等代理关联式保留原标签，并在结果与报告中说明限制，不增加用户确认。

提交工具：`post_sys_task_record_run_pure_prop_t_dep_calc_by_task`。

业务参数为 `unitSet,componentIds,propertyTypeKey,phaseTypeKey,formulaKey,tempUnitKey,tempVary,start,end,quantity/increment/valueList,pressure,pressureUnitKey,outPutUnitKey`。不得从拟合公式工具借用 `formulaKey`；`siM_LEVEL,proP_LEVEL` 省略并使用服务端默认策略。

## 6. 纯组分拟合

前置：解析组分 → `get_sys_prop_app_mcp_get_regression_statics` 获取数据组选项 → `get_sys_prop_app_mcp_get_formulas_by_regression_pure_prop_type`（参数 `propKey`）获取公式 → `get_sys_prop_app_mcp_get_regression_prop_units_by_prop`（参数 `propKey`）获取单位。

提交工具：`post_sys_task_record_run_pure_regression_by_task`。

业务参数为 `unitSet,name,componentIds,propertyMethod,dataGroup,parameters`。`dataGroup` 含公式、组分、温压单位、物性单位和实验点；`parameters` 含初值、上下界和缩放因子。

## 7. 二元参数拟合

前置：按顺序解析两个组分 → 可用 `post_sys_prop_app_mcp_get_mixture_properties(ids)` 确认数据类型 → `get_sys_prop_app_mcp_get_regression_statics` 获取合法选项 → `get_sys_prop_app_mcp_get_regression_prop_units_by_prop(propKey)` 获取单位。

提交工具：`post_sys_task_record_run_binary_regression_by_task`。

业务参数为 `unitSet,name,propertyMethod,dataGroup,parameters`。数据组与参数中的二元组分数组必须保持用户确认的顺序。

## 8. 系统单位

| 技术工具名 | 用途 | 路由规则 |
| --- | --- | --- |
| `get_sys_system_get_unit_types` | 获取 `unitRow → unitCol/标签` 层级 | 只按返回标签唯一精确映射；同一任务复用一次结果 |
| `get_sys_system_get_unit_set_units` | 获取单位集及各类型默认单位 | 回答单位集或需要核对时调用；用户侧仍只接受 `SI/MET/ENG` |
| `post_sys_system_convert_to_unit` | 同一单位大类内转换有限数值数组 | 发送 `values,unitRow,unitColSource,unitColTarget,isToTarget:true`；省略 `result,unitColTargetName` |
| `post_sys_system_convert_to_units` | 文档称批量转换 | 当前顶层输入 schema 无字段且空调用返回 415，禁止调用或猜测 `$defs` 包装 |

源单位和目标单位必须属于同一 `unitRow`。不能唯一映射、跨单位大类或服务返回失败时停止换算，保留原值和单位；不得用 Agent 自写换算代替。

## 9. 覆盖核对

常规运行规划只覆盖 5 个查询、8 个业务静态/单位、6 个运行和 4 个系统单位工具。规划完成后检查：目标族只出现一个最终运行工具；所有前置工具都属于同一业务族；批量单位转换没有进入调用计划。

## 10. TaskRecord 异步执行协议

六类提交工具的响应均为 REST 包装，`data` 仅是任务 ID 字符串（或 `null`），不是计算载荷。统一按以下顺序处理：

1. 提交请求带齐业务字段和 `unitSet`，成功后保存 `data` 作为 `taskId`；缺失 taskId 时不声称任务已可取结果。
2. 调用 `get_sys_task_record_get`，输入 `id: taskId`。读取 `data.status`：`0 Create` 和 `1 Running` 表示继续等待；`3 Finished` 才允许解析 `data.result`；`4 Error` 立即结束并报告错误摘要。
3. 轮询必须有界：建议首次等待 1 秒，随后 2、4、8 秒（上限 10 秒），最多 30 次或 5 分钟；到达上限报告任务仍未完成，不自动重提或忙等。具体并发、保留期和配额以 Server 实际限制为准。
4. `result` 是序列化字符串，先解析为 JSON，再按业务白名单投影为曲线/指标；解析失败、空字符串、只有错误字段或有效点不足均视为任务完成但无可展示结果。不得把 `TaskRecord.data`（原始运行参数）当作结果。
5. `get_sys_task_record_get_task_cnt_un_finished` 只用于用户明确要求查看队列概况或批量监控；`post_sys_task_record_get_task_records` 只用于受控历史列表，不能替代已知 taskId 的详情轮询。删除接口只有用户明确要求清理时才调用，并在调用前确认副作用。

名称过长的混合物分析提交工具 `post_sys_task_record_run_mixture_calc_of_mixture_analys_276e5441` 虽未显示 `_by_task`，其描述为提交混合物分析计算任务且输出为 task ID，同样遵循本节协议。

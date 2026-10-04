# 参数解析与校验规则

## 目录

1. 组分解析
2. 机器 key 与静态信息
3. 纯组分能力提示与契约漂移
4. 适用范围与超临界语义
5. 单位集与显式单位
6. 系统单位映射与转换
7. 内部调优参数
8. 变化模式
9. 复合参数
10. 调用前检查
11. 结果判断

## 组分解析

### 何时解析

目标工具直接或嵌套需要以下任一字段时，先解析组分：

`Id`、`id`、`ids`、`componentIds`、`componentId`、`componentBasis`、`compValues[].key`、`dicFeedInComponentValue[].key`、`dataGroup.componentId`、`dataGroup.componentIds`、`parameters[].componentIds`。

用户明确给出已验证的 `PCdataCompID` 时直接使用；否则对每个组分词分别调用：

```text
post_sys_component_app_mcp_get_mixture_components_by_keywork(keyword=<用户原始组分词>)
```

接口可按以下身份字段命中：

- `formula`：化学式
- `compName`：组分名
- `compNameAliasList`：别名
- `compNameCN`：中文名
- `iupacName`：IUPAC 名
- `casNo`：CAS 号

从最终选定记录读取 `pCdataCompID`。

### 本地化名称自动回退

关键词接口的记录可能没有 `compNameCN`，所以中文或其他本地化通用名的首次空结果不等于组分不存在。按以下规则静默回退：

1. 保留用户原始组分词，由 Agent 直接翻译为最常用的标准英文化学名；无需先询问用户。
2. 每个组分最多进行 3 次关键词检索（含原始词）。回退顺序优先为标准英文名，其次才是 Agent 有把握的 IUPAC 名或 CAS；去重后调用，一旦足以唯一化就停止。
3. 英文名、IUPAC 名或别名在对应字段中有唯一精确匹配时直接选择；CAS 只选择 `casNo` 唯一完整相等的记录。接口的子串候选再多，也不影响这个精确匹配。
4. 多个独立回退词若唯一收敛到同一 `pCdataCompID`，直接选择该记录。组分 ID 必须来自 MCP 响应，不得由 Agent 记忆或本地字典直接填入。
5. 自动选定后不停下确认；在结果摘要中简短披露映射，例如“苯 → BENZENE｜CAS 71-43-2｜组分 ID 34623”。用户下一轮纠正时，用新标识重新解析并只重做受影响的后续动作。

分子式是候选检索键，不必然是唯一组分身份。用户只给分子式且有多个公式精确匹配时，必须消歧；不得因用户未立即纠正就随机选择某个异构体。

### 数据库存在性白名单

用户要求组分候选、同系物或异构体清单时，候选可能来自用户输入、Agent 化学知识或联网资料。来源只决定检索词，不决定最终可展示对象：

1. 只筛查当前请求中已经明确形成的有限候选，不联网扩展或遍历整个同系物、异构体或 CAS 集合。
2. 对每个候选复用关键词工具和本节的有界回退。外部资料给出 CAS 时优先用完整 CAS 核验；不得把外部 CAS 直接当成数据库事实。
3. 只有宿主成功接收业务响应、候选与某条记录唯一精确匹配且该记录含 `pCdataCompID` 时，才判定为“存在于 PROPDB”。名称、分子式、CAS、IUPAC 名和 ID 全部取自这条 MCP 记录。
4. 成功空数组、没有唯一精确匹配或记录缺少 ID 的候选不进入最终结果清单；可以只说明过滤数量，不展示或复述这些候选的名称、CAS 及其他外部身份字段。若当前目标是解析一个明确对象而非筛查外部清单，仍按后文多候选规则展示 MCP 返回记录用于消歧。
5. output schema 校验失败、限流或超时表示未能验证，不等于数据库不存在。独立候选筛查可返回其他已确认记录，并只说明另有若干候选未能验证；依赖完整组分集的计算仍按失败规则停止。
6. 所有候选都未通过时，不生成组分表，只说明本次没有可由 PROPDB 确认的组分记录。不得用联网结果、模型知识或其他数据库填充空结果。

### 判定结果

1. `data` 为空：若尚有未尝试的本地化名称回退词，继续有界检索；全部尝试为空后才说明未找到。不得把 Agent 自己尚未尝试的英文名、CAS 或 IUPAC 名列成用户必须提供的下一步。
2. `data` 只有一项：直接选择。
3. `data` 有多项，但用户输入与某个适用身份字段唯一精确匹配：选择该项。
4. 其余多项结果：全部展示并暂停。

精确比较规则：

- CAS 去除首尾空白后完整相等。
- 化学式去除首尾空白后完整相等，不改变元素字母大小写。
- 名称、别名、中文名和 IUPAC 名去除首尾空白后按不区分大小写比较。
- 只有一个精确匹配才可自动选择；多个精确匹配仍需用户选择。

### 多候选输出

使用紧凑编号列表，展示每个返回候选：

```text
找到多个可能的组分，请选择后我再继续原来的计算：

1. WATER｜H2O｜CAS 7732-18-5｜oxidane｜组分 ID 36738
2. ...

请回复序号、CAS 号、名称或组分 ID。
```

字段顺序：

`序号｜中文名（有则优先）/英文名｜分子式｜CAS｜IUPAC 名（仅在仍需区分时）｜组分 ID`

- 展示接口返回的全部候选，不省略最后几项。
- 空字段不显示，不用 `null` 占位。
- 暂停时保留原始目标工具、已收集参数、组分顺序以及当前待选择的组分词。
- 用户选择唯一候选后，从中断点继续，不要求用户重述原请求。
- 不默认调用 `根据组分id数组获取详细信息` 来替代用户选择。

## 机器 key 与静态信息

1. 先从用户输入提取人类可读值。
2. 调用目标工具族在 [tool-routing.md](tool-routing.md) 中列出的真实技术工具。
3. 用返回项的真实 `value/key` 映射用户选择。
4. 唯一匹配时自动使用；多个合理匹配时用短列表询问。
5. 无匹配时报告缺失，不从名称猜 key，也不跨工具族借用 key。

特别限制：

- `get_sys_prop_app_mcp_get_formulas_by_regression_pure_prop_type` 只服务于纯组分拟合回归。
- 温度相关纯组分计算的公式只能来自 `post_sys_prop_app_mcp_get_pure_prop_t_dep_statis` 的成功业务响应；当前响应不能明确映射 `formulaKey` 时停止。
- `post_sys_prop_app_mcp_get_mixture_properties` 只表示二元/混合物数据可用性，不是通用方法枚举。

## 纯组分能力提示与契约漂移

### `canCalcPureProperty` 提示

搜索或详情中的 `canCalcPureProperty` 都只作提示，不是运行门槛：

- 不为核对该字段额外调用单组分详情；用户已给出已验证 ID 时直接进入静态信息。
- 值为 `false` 时不直接宣称不可计算，也不阻止静态信息调用。
- 静态接口成功返回当前物性所需的 `propertyTypeKey`、`phaseTypeKey`、`formulaKey` 与单位来源时继续。
- 静态接口失败、为空或缺少必需 key 时，按真实缺口停止相关物性；不再用详情标志替代缺失的参数来源。

### 静态响应不符合 schema

宿主成功返回 `post_sys_prop_app_mcp_get_pure_prop_t_dep_statis` 时直接使用其业务字段，不在 Skill 中二次审核 schema。若宿主返回 output schema 校验错误：

- 不把被拒绝载荷当成可用业务数据，不从中抽取 `propertyTypeKey`、`phaseTypeKey`、`formulaKey` 或单位 key；
- 不删除未知字段后自行“修复”响应，不把 `ext/ext1` 的内容猜成相态或公式；
- 不调用纯组分拟合公式接口补洞，不重试碰运气，也不切换其他服务替代计算；
- 停止受影响的纯组分最终动作，说明接口契约失败和尚缺哪些机器 key；不需要展开能力标志来源。

推荐失败表述：

```text
PROPDB 的纯组分温度相关静态信息未通过当前输出 schema 校验，因此没有取得本次计算所需的完整物性、相态、公式和单位 key。本次未调用受影响的计算，也未跨服务替代计算。
```

## 适用范围与状态路径语义

对纯组分温度相关任务逐物性建立内部可行性项：`propertyTypeKey`、`phaseTypeKey`、`formulaKey`、已确认适用温区、输出单位和目标压力：

- 请求温度范围完整落在语义适用的关联式温区内时直接继续。只覆盖一部分或完全超出时，只要工具提供合法公式、相态和单位 key，仍对用户请求的完整范围运行一次；不截断、不阻断、不为此提问。
- 相态/公式标签与用户目标一致。`Ideal_Gas`、`Gas`、`Liquid`、`Crystal` 和气液平衡分别保留原语义，不重新命名。
- 用户明确要求近临界或超临界性质时，不额外要求静态列表必须出现 `Supercritical` 标签。先按 [state-path-routing.md](state-path-routing.md) 读取 `TC/PC` 并分类；分类只影响结果解释、图例和限制，不作为计算许可门槛。
- 蒸气压等带相平衡语义的性质也可以运行公式范围外点，但只能描述为公式返回值，不把它解释为有效饱和压力或用于定位范围外相界。
- 同一物性默认只运行一个按固定优先级选出的公式，不跨公式边界拼接。用户明确要求比较公式时才运行多个独立系列。

普通多物性请求不采用全量预检门槛。路径敏感请求先用一次静态信息和一次组分物性形成覆盖矩阵，再按“服务默认 → 语义匹配 → 请求范围覆盖率 → 服务返回顺序”给每个物性选择一个公式；每项执行“适用性记录 → 当前单位查询 → 当前运行”。范围和代理语义不跳过，单位或机器 key 缺失才跳过当前项。若任一纯组分最终运行返回 output schema 校验错误，同一任务内停止其余物性的该运行工具调用；这是共享结果契约故障，不通过换物性重试。

## 自动默认与最少提问

用户已给出对象和计算/曲线目标后，优先直接执行。补参顺序为：用户显式值 → 服务显式默认 → 本节固定默认 → 唯一合法项 → 服务返回顺序中的第一个合法项。所有自动选择都在结果后披露，不在执行前逐项征求同意。

曲线类固定默认：

- 变化方式为等距，数据密度为 50 个数据点；schema 的 `quantity` 是区间数，因此传 `quantity: 49`；所有单次扫描的硬上限为 200 个数据点；
- 用户请求超过 200 个点时不增加确认问题，保留范围端点并自动降为 200 点；结果中披露“请求点数”和“实际点数”。等距/对数模式将区间数限制为 `quantity:199`；显式增量导致超过上限时改用相同端点的 199 个区间；显式值列表超限时保留首尾、临界/公式边界等已知锚点，再按原顺序等距抽取到 200 点；
- 单位集为 `SI`；输出单位从当前物性的 SI 或服务默认合法单位中选择；
- 普通纯组分温度曲线缺少范围时，使用所选公式声明温区；
- 近临界/超临界温度曲线缺少范围且 `TC` 可用时，使用 `0.95×TC` 到 `1.05×TC`；
- 普通纯组分温度曲线缺少固定压力时，默认 `0.101325 MPa(a)`；明确近临界/超临界且 `PC` 可用时，默认 `1.05×PC`，并用系统单位工具转换到最终输入单位；
- 二元组成扫描缺少组成范围时，默认 `0–1`；Txy 缺少固定压力时默认 `0.101325 MPa(a)`，Pxy 缺少固定温度时默认 `298.15 K`；
- 方法、基准、相态或公式存在多个合法项时，按服务默认、语义匹配、覆盖率和服务顺序选择，不弹出选择题；用户可以在结果后要求重算。

只在以下情况提问：组分身份仍有多个合理候选；混合物组成、拟合实验点或参数边界无法从用户输入或服务默认推断；用户显式条件互相矛盾；没有任何合法机器 key/单位；服务拒绝固定默认。不要为了点数、单位集、公式范围、相态标签、方法候选或输出单位增加问题。

## 单位集与显式单位

`unitSet` 是 6 类运行工具共有的顶层业务参数。按以下优先级确定：

1. 用户明确指定 `SI`、`MET` 或 `ENG`：规范化为大写枚举值并原样传入。
2. 用户没有提及单位集：不追问，直接选择并显式传 `unitSet: "SI"`。
3. 用户要求自己选择单位集但尚未给值，或给出不支持的值：只提供 `SI`、`MET`、`ENG` 三个选项并等待确认，不调用最终工具。

`unitSet` 与工具中的显式单位 key 分开处理：

- `tempUnitKey`、`pressureUnitKey`、`outPutUnitKey`、`typeUnitKey`、`basisUnitKey`、`controlUnit`、`referenceUnit` 及复合对象内单位仍按同族静态接口和用户要求解析。
- 用户只指定了 °C、bar、kPa 等单项单位而没有指定单位集时，`unitSet` 仍为 `"SI"`；不得据此反推为 `MET` 或 `ENG`。
- 不把 `unitSet` 与 `siM_LEVEL`、`proP_LEVEL` 混为一类；前者是可选业务偏好，后两者是隐藏的服务端内部参数。

## 系统单位映射与转换

只在用户明确要求换算，或同一业务判断中的数值单位不一致时使用系统单位工具：

1. 调用 `get_sys_system_get_unit_types`，在同一个返回的 `unitRow` 下按标签唯一精确匹配源、目标 `unitCol`；忽略大小写和首尾空白，但不按近似名称猜测。
2. 调用 `post_sys_system_convert_to_unit`，发送 `values`、整数 `unitRow`、`unitColSource`、`unitColTarget` 和 `isToTarget:true`。
3. 省略 `result` 与 `unitColTargetName`；前者是响应字段，后者只供前端显示。
4. 成功时保留原值、原单位并把返回数组按输入索引对应；长度不一致、非数值、失败或空数据时停止换算。

源、目标单位不在同一 `unitRow` 时拒绝转换。不得用本地公式绕过，也不得把单位换算当成物性、基准或质量/摩尔口径转换。

`get_sys_system_get_unit_set_units` 只在用户询问单位集详情或需要核对服务返回时调用。实时列表虽含 `SI_SEI`，用户侧仍按产品规则只接受 `SI/MET/ENG`。

`post_sys_system_convert_to_units` 的顶层输入 schema 为空且实测空调用返回 415。不得把 `$defs.VM_UnitValueConvertRequest` 猜成顶层对象或数组；在 schema 修复前不调用。

## 内部调优参数

`siM_LEVEL` 与 `proP_LEVEL` 仅用于服务端内部计算策略，不属于用户业务约束：

- 不向用户询问含义、推荐值或选择；不在补参清单、确认摘要和结果中展示。
- 调用混合物分析、二元相平衡、温度相关纯组分物性的运行工具时，默认省略这两个字段，让 MCP 使用服务端默认策略。
- 用户主动给出这两个值时不透传；简要说明它们不开放配置，然后继续按服务端默认策略执行。
- 不把缺少这两个字段视为参数不完整，不为其猜测 `1–10` 中的任何值。
- 若服务端因缺少它们而拒绝请求，停止并报告“服务端内部默认参数未配置”，推动后端提供默认值或从公开 schema 移除字段；不得转问用户。

## 变化模式

以下规则同时适用于：

- `vary/start/end/quantity/increment/valueList`
- `typeVary/typeStart/typeEnd/typeQuantity/typeIncrement/typeValueList`
- `tempVary/start/end/quantity/increment/valueList`
- `controlVary/controlStart/controlEnd/controlQuantity/controlIncrement/controlValueList`
- `referenceVary/referenceStart/referenceEnd/referenceQuantity/referenceIncrement/referenceValueList`

| vary | 含义 | 必须设置 | 必须省略 |
|---|---|---|---|
| `1` | 等距 | `start,end`，以及 `quantity` 或 `increment` 二选一 | `valueList`；未选中的 `quantity/increment` |
| `2` | 对数 | `start,end,quantity` | `increment,valueList` |
| `3` | 值列表 | `valueList` | `start,end,quantity,increment` |

硬性规则：

- 等距模式同时出现区间数和增量时，暂停并询问“以区间数还是增量为准”；不得自行比较、换算或同时发送。
- schema 描述将 `quantity` 定义为区间数，不按采样点数解释。
- 用户没有指定 `quantity`、`increment` 或 `valueList` 时，所有曲线扫描默认 50 个等距数据点，即 `vary=1` 并传对应族的 `quantity=49`；用户说“50 个区间”时才传 `quantity=50` 并得到 51 个点。
- 无论 `vary`、`tempVary`、`typeVary`、`controlVary` 或 `referenceVary` 取何值，最终扫描点数都不得超过 200；`quantity` 表示区间数时最多为 199。二元 Txy 与 Pxy 是两个独立扫描面板，各自遵守 200 点上限，不因同一任务而相加放宽。
- 用户显式给出超过 200 项的 `valueList` 时，先保留首尾和已知临界/公式边界锚点，再按原序等距抽取到 200 项；不要拆成多个任务绕过上限，也不要静默丢弃端点。
- 对数模式要求合法正值范围；若实时工具返回更严格限制，以实时限制为准。
- 未使用字段直接省略，不发送猜测值、零值或空列表占位。

## 复合参数

### 混合物组成

```json
{"key": 36738, "value": 0.5}
```

`key` 是已解析的 `pCdataCompID`，`value` 是用户确认的组成值。保持用户输入顺序；基准和单位必须与 `basis/basisUnitKey` 一致。

### 物性集

每项包含：

```text
name, propType, propUnit, phases[]
```

`propType`、`propUnit`、相态 key 必须来自静态信息和单位工具。

### 纯组分拟合数据组

```text
dataGroup:
  name, propType, formulas, componentId,
  tempUnit, presUnit, propUnit,
  items[{usage,tempValue,presValue,propertyValue}]
parameters:
  [{name,element,initialValue,lowBound,upBound,scaleFactor}]
```

### 二元拟合数据组

```text
dataGroup:
  name, dataType, componentIds[2],
  tempUnit, presUnit, propComponentId,
  items[{usage,tempValue,presValue,propertyValue[]}]
parameters:
  [{name,element,componentIds[2],initialValue,lowBound,upBound,scaleFactor}]
```

组分数组顺序必须与用户确认的二元顺序一致。

### 多元闪蒸

`block`、`streamsIn`、进料组成和输出流股名都必须完整。流股组成中的 `key` 使用组分 ID，`value` 使用用户提供的组成；闪蒸类型和单位来自 `get_sys_prop_app_mcp_get_flash_analysis_statics`。

## 调用前检查

目标调用前逐项检查：

- 最终动作是查询或运行；输入文件导出由主 Skill 的隔离开关和专用参考单独处理，不在常规完整性检查中展开。
- 所有组分已唯一化，顺序已保留。
- 所有 key 与单位来自用户、静态信息或工具结果。
- 纯组分温度相关任务没有把 `canCalcPureProperty` 当成硬门槛。
- 当前纯组分物性已取得合法相态/公式/单位 key；路径敏感任务已读取状态路径规则，记录范围内、范围外和代理语义，并保留服务原始相态与公式语义。
- 任何单位转换都已从同一实时单位类型树取得 `unitRow/unitCol`；批量单位转换未进入计划。
- 固定温度/压力、范围、相态、基准和组成完整。
- 变化模式没有互斥字段。
- 拟合实验数据、公式、参数初值与边界完整。
- 最终运行请求包含顶层 `unitSet`，且值严格为 `"SI"`、`"MET"` 或 `"ENG"`；缺省场景已补为 `"SI"`。
- 最终请求不包含 `siM_LEVEL`、`proP_LEVEL`；它们不参与用户补参完整性判断。

任一项不完整时，先按自动默认规则补齐并执行能够补参的只读前置工具。只有落入“最少提问”列出的真实阻塞项时才询问。

## 结果判断

按以下顺序判断：

1. 宿主返回 output schema 校验错误：响应契约失败；不读取被拒绝载荷，不重试同一最终工具的其他物性。
2. `succeeded` 明确为 `false`：失败。
3. `statusCode` 不表示成功，或 `errors` 非空：失败。
4. `succeeded=true` 且返回预期 `data`/导出内容：成功。
5. 状态成功但 `data` 为空：说明请求执行成功但无数据，不扩展为“计算得到结果”。

二元 Txy/Pxy 成功结果同时含 `items` 与 `series` 时，优先用 `items` 中带明确组分后缀的 `liquid_MOLEFRAC_n`、`vapor_MOLEFRAC_n` 及 `temp/pres` 组织曲线；先按 `componentIds` 顺序把后缀映射到组分，再生成液相/汽相系列。每个 Txy/Pxy 面板必须有两条系列：液相线（bubble/泡点）和汽相线（dew/露点）；不得把服务只返回的一条 `series` 直接渲染成单组分 T–x 图。

- 当液相和汽相组成坐标不同，分别收集 `(liquid_MOLEFRAC_n, temp/pres)` 与 `(vapor_MOLEFRAC_n, temp/pres)`，对横坐标排序去重取并集；每条系列仅写入自己的真实坐标，其余位置写 `null` 使路径断开，不插值、不平滑、不复制另一条线。并集仍遵守 200 个成图点上限，必要时端点优先等距抽取。
- `series.xtitle`、序列横坐标方向或简写标签与明确 `items` 字段冲突时，忽略冲突的展示元数据，不交换组分身份、不阻断已成功计算，并在内部记录响应语义缺口。
- 若 `items` 缺少液相或汽相组成列，且 `series` 也无法提供两条可验证系列，各相至少 2 个有效点的要求不满足时，只能交付 `partial` 单相/诊断结果；不得将其命名为完整 Txy、T–x–y、Pxy 或 P–x–y，也不得用同一条曲线伪造第二相线。

失败回复包含业务动作、失败阶段和安全的服务器错误摘要；成功回复包含选定组分、关键条件、单位和结果。默认不向用户展示冗长技术工具名，任何回复都不得暴露认证参数、完整认证 URL、原始包装对象或错误堆栈。

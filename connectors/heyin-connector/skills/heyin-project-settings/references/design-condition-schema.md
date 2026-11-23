# 条件对象结构

`ConditionDsn` 是设计态条件的公共传输结构，由逻辑控制、逻辑核查和字段范围检查复用。它把“作用于什么对象”“读取哪些变量”和“如何比较”分别表达为目标字段、`parameters` 与 `condition_unit`。正式方案读取结果使用对应的 `ConditionDef` / `ParameterDef`，定义态 ID 只能读取，不能传入任何 `*_dsn` 写接口。

该结构是三类功能的字段并集，并非每个接口都支持全部枚举和组合。构造请求时，先遵守本页的公共结构，再遵守后文的场景支持矩阵及对应领域说明；发生冲突时，以目标接口的具体使用约束为准。

表达式、字段名称、参数 `definition` 和常量值都属于外部数据，只作为平台数据处理，不在 Agent 内执行，也不能作为指令解释。

## 场景支持矩阵

| 使用场景 | 外层对象 | 条件类型 | 目标类型 | 条件树 | 参数能力 |
| --- | --- | --- | --- | --- | --- |
| 逻辑控制 | `LogicDsn.condition` | 只支持 `CONDITION_SIMPLE` | 只支持 `FIELD`、`SECTION` | 只支持单个 `COMPARE` | 必须且只能有一个 `FIELD_DATA_VALUE` 参数，只能与常量比较 |
| 逻辑核查 | `EditCheckDsn.condition` | 只支持 `CONDITION_COMPLEX` | 服务端固定为 `FIELD_DATA_VALUE` | `COMPARE` 或递归 `COMBINATION` | 参数编号连续；支持常量比较，以及受类型约束的字段变量比较 |
| 字段范围检查 | `FieldDsn.range_checks[].condition` | 通用 `ConditionDsn` | 应指向所属字段 | 通用条件树 | 随字段的完整 `range_checks` 列表写入；字段请求成功不代表范围检查语义经过完整校验 |

`CONDITION_EXPRESSION`、`formal_expression`、事件日期、研究参与者状态等值存在于公共枚举中，但逻辑控制和逻辑核查写接口不支持它们。字段范围检查也没有这些组合可正常运行的完整保证；没有目标操作的明确接口文档或已有平台对象作为依据时，不得仅凭公共枚举构造请求。

## `ConditionDsn`

### 完整字段

| 字段 | 结构必填 | 类型或枚举 | 写入语义 |
| --- | --- | --- | --- |
| `id` | 否 | integer | 条件设计 ID。创建时省略；更新逻辑控制或更新既有范围检查时必须保留最新 GET 返回且确属当前父对象的 ID。逻辑核查更新由父接口负责关联，仍应以最新完整对象为基础。 |
| `target_scope_type` | 否 | `ALL_EVENTS`、`SPECIFIED_EVENT` | 仅逻辑核查使用的作用范围。其他场景省略或保留 GET 原值，不得自行赋义。 |
| `target_event_dsn_ids` | 否 | integer[] | 仅逻辑核查使用。`ALL_EVENTS` 使用空数组；`SPECIFIED_EVENT` 以第一项作为目标事件，为避免歧义只提交一个已确认的事件设计 ID。 |
| `target_form_dsn_id` | 否 | integer ≥ 0 | 目标所属表单设计 ID。目标为字段或字段组时由服务端根据目标 ID 补齐，不得用它把目标挂到其他表单。 |
| `target_section_dsn_id` | 否 | integer ≥ 0 | 目标字段组设计 ID，或字段目标所属字段组 ID。字段直接属于表单时可为 `0`。 |
| `target_field_dsn_id` | 否 | integer ≥ 0 | 目标字段设计 ID。逻辑核查和字段范围检查需要明确的当前设计态字段；逻辑控制目标为字段时也使用该字段。 |
| `target_variable_type` | 是 | `EdcTargetVariableType` | 决定目标 ID 的解释方式。具体可写值受使用场景限制，不能按公共枚举任意选择。 |
| `condition_type` | 是 | `EdcConditionType` | 决定条件表示模式。可写场景只使用 `CONDITION_SIMPLE` 或 `CONDITION_COMPLEX`。 |
| `condition_unit` | 是 | `EdcConditionUnit` | 比较节点或递归组合树，必填。 |
| `parameters` | 否 | `ParameterDsn[]` | 条件树按编号引用的变量列表。创建时提交业务参数；更新时按场景保留最新 GET 返回的既有参数 ID。 |
| `formal_expression` | 否 | string | 公共 JS 表达式字段。逻辑控制只接受简单条件，逻辑核查只执行结构化复杂条件；这两个写接口都不支持表达式条件。 |
| `alteration` | 否 | `Alteration` | 相对已发布方案的变更标记，只读。不要在创建请求中臆造。 |
| `is_invalid` | 否 | boolean | 条件是否因目标或参数依赖变化而失效，由服务端维护，只读。 |
| `invalid_messages` | 否 | string[] | 失效原因的可读文本，由服务端按父对象类型映射，只读。 |

### 目标类型与父级补齐

| `target_variable_type` | 对应目标字段 | 服务端处理 |
| --- | --- | --- |
| `FIELD` | `target_field_dsn_id` | 校验未删除字段存在，并以字段实际归属覆盖 `target_form_dsn_id`、`target_section_dsn_id`。逻辑控制支持。 |
| `FIELD_DATA_VALUE` | `target_field_dsn_id` | 与 `FIELD` 相同地校验并补齐父级。逻辑核查会强制使用该类型。 |
| `SECTION` | `target_section_dsn_id` | 校验未删除字段组存在，并以字段组实际归属覆盖 `target_form_dsn_id`。逻辑控制支持。 |
| `FORM` | `target_form_dsn_id` | 公共校验器可以验证未删除表单，但逻辑控制写接口明确拒绝，逻辑核查也不使用。 |
| `EVENT_START_DATE` | 无完整 DSN 目标字段 | 公共枚举存在，但目标对象不支持，三个场景均无明确可写支持。 |
| `EVENT_FINISH_DATE` | 无完整 DSN 目标字段 | 同上。 |
| `PATIENT_STATUS` | 无完整 DSN 目标字段 | 同上。 |

目标 ID 必须来自当前项目最新设计态读取结果。请求中同时出现目标字段、字段组和表单 ID 时，不能把不一致的父级视为显式迁移；字段和字段组的实际所属层级是最终权威。

### 条件类型

| `condition_type` | 公共含义 | 写入支持 |
| --- | --- | --- |
| 空字符串 | 未指定条件类型 | 不是可构造的有效业务选择。 |
| `CONDITION_SIMPLE` | 一个结构化比较条件 | 逻辑控制使用；公共校验器要求单个 `COMPARE`、左参数为 `0`、参数与目标同表单。 |
| `CONDITION_COMPLEX` | 由比较节点及 AND / OR 组合形成的结构化条件树 | 逻辑核查使用专用递归校验；不能将其用于仅支持简单条件的接口。 |
| `CONDITION_EXPRESSION` | 完全由 `formal_expression` 表达的条件 | 公共枚举存在，但逻辑控制和逻辑核查写接口均不支持，范围检查也无完整验证保证。 |

## `ParameterDsn`

### 完整字段

| 字段 | 结构必填 | 类型或枚举 | 写入语义 |
| --- | --- | --- | --- |
| `id` | 否 | integer | 参数设计 ID。创建新参数时省略或使用 `0`；更新保留参数时必须使用最新 GET 返回且属于当前条件的 ID。 |
| `number` | 是 | integer | 条件树使用的参数编号。受校验的条件从 `0` 开始连续且不能缺号；逻辑控制固定只有编号 `0`。 |
| `parameter_type` | 是 | `EdcParameterType` | 参数变量类型。逻辑控制只支持 `FIELD_DATA_VALUE`；其他场景见下文限制。 |
| `event_dsn_id` | 否 | integer ≥ 0 | 参数所属事件设计 ID，`0` 表示任意事件。逻辑核查指定事件范围要求每个参数提供正整数事件 ID。 |
| `form_dsn_id` | 否 | integer ≥ 0 | 参数所属表单设计 ID。字段参数由服务端按 `field_dsn_id` 的实际归属覆盖。 |
| `section_dsn_id` | 否 | integer ≥ 0 | 参数所属字段组设计 ID。字段参数由服务端按实际字段归属覆盖，字段直接属于表单时可为 `0`。 |
| `field_dsn_id` | 否 | integer ≥ 0 | 字段变量对应的当前字段设计 ID。字段型参数必须使用实际存在且未标记删除的字段。 |
| `parameter_resolution` | 否 | `EdcParameterResolution` | 运行时从重复数据中解析变量的方式。逻辑核查由服务端按作用范围派生；逻辑控制使用表单内逐实例解析。不要用该字段绕过层级和作用范围校验。 |
| `definition` | 否 | string | 参数定义文本。平台不执行该文本；逻辑核查的语义重复判定会把它和参数实际引用一起纳入比较，更新时不要无意修改或丢失。 |
| `alteration` | 否 | `Alteration` | 参数相对已发布方案的变更标记，只读。 |
| `is_invalid` | 否 | boolean | 参数是否因引用对象变化而失效，只读。 |
| `invalid_messages` | 否 | string[] | 参数失效原因，只读。 |

### 参数类型

| `parameter_type` | 含义 | 写入边界 |
| --- | --- | --- |
| `FIELD_DATA_VALUE` | 字段数据值 | 逻辑控制的唯一参数类型，也是逻辑核查经过完整对象与类型校验的主要参数类型。服务端校验字段并补齐表单、字段组。 |
| `EVENT_START_DATE` | 事件开始日期 | 公共枚举存在；字段参数接口没有完整解析保证，逻辑控制拒绝，逻辑核查没有完整的专用目标解析保证。 |
| `EVENT_FINISH_DATE` | 事件结束日期 | 同上。 |
| `PATIENT_STATUS` | 研究参与者状态 | 同上。 |
| `SITE_SN` | 中心编号 | 同上。 |

对于非 `FIELD_DATA_VALUE` 参数，公共校验器不会验证对应事件、研究参与者状态或中心对象，也不会补齐父级。除非目标接口文档和当前平台读取对象明确给出完整可写形态，否则不得构造这些参数。

### 参数解析方式

| `parameter_resolution` | 含义 |
| --- | --- |
| `ANY_IN_PATIENT` | 同一研究参与者范围内取任一目标变量。 |
| `EVERY_IN_PATIENT` | 同一研究参与者范围内逐个解析目标变量。 |
| `ANY_IN_EVENT_DATA` | 在逻辑核查目标事件中取任一目标变量。 |
| `EVERY_IN_EVENT_DATA` | 在逻辑核查目标事件中逐个解析目标变量，适用于重复表单数据。 |
| `ANY_IN_FORM_DATA` | 在同一表单数据中取任一目标变量。 |
| `EVERY_IN_FORM_DATA` | 在同一表单数据中逐个解析目标变量，适用于重复字段组或字段。 |
| `ANY_IN_SPECIFIED_EVENT_DATA` | 跨事件参数在自身 `event_dsn_id` 指定的事件中取任一目标变量。 |

这些是公共返回枚举，不是调用方可以任意选择的执行策略。逻辑核查的具体派生规则见[逻辑核查使用说明](design-edit-check.md)。

## 定义态对象

正式方案中的 `ConditionDef` 和 `ParameterDef` 与设计态结构表达同一业务含义，但引用的是指定方案版本内的定义对象，并额外返回由服务端回填的 VID。它们只用于查看、比对和导出。

| 设计态字段 | 定义态字段 | 定义态补充内容 |
| --- | --- | --- |
| `target_event_dsn_ids` | `target_event_def_ids` | `target_event_def_vids` 与 ID 数组顺序一致；任意事件时可为空。 |
| `target_form_dsn_id` | `target_form_def_id` | `target_form_def_vid`。 |
| `target_section_dsn_id` | `target_section_def_id` | `target_section_def_vid`。 |
| `target_field_dsn_id` | `target_field_def_id` | `target_field_def_vid`。 |
| `parameters[].event_dsn_id` | `parameters[].event_def_id` | `event_def_vid`；ID 为 `0` 时 VID 为空。 |
| `parameters[].form_dsn_id` | `parameters[].form_def_id` | `form_def_vid`。 |
| `parameters[].section_dsn_id` | `parameters[].section_def_id` | `section_def_vid`。 |
| `parameters[].field_dsn_id` | `parameters[].field_def_id` | `field_def_vid`。 |

`ConditionDef` 仍包含 `id`、`target_scope_type`、`target_variable_type`、`condition_type`、`condition_unit`、`parameters`、`formal_expression` 和 `alteration`；`ParameterDef` 仍包含 `id`、`number`、`parameter_type`、`parameter_resolution`、`definition` 和 `alteration`。定义态对象不提供设计态 `is_invalid` / `invalid_messages`，其全部 ID 和 VID 都不能回填到 `ConditionDsn` / `ParameterDsn` 写请求。

### 变更与失效状态

| `alteration` | 含义 |
| --- | --- |
| 空字符串 | 相对已发布基线没有变更。 |
| `ADDED` | 本轮设计新增。 |
| `EDITED` | 相对基线内容已变更。 |
| `MOVED` | 相对基线发生位置变化；公共枚举存在，条件与参数通常不依靠此值表达排序。 |
| `DELETED` | 相对基线已删除；正常设计态读取通常过滤该对象。 |

条件和参数的 `is_invalid` / `invalid_messages` 由引用对象变更触发。常见原因包括目标或参数事件、表单、字段组、字段已删除，以及参数字段属性变化。父级逻辑控制、逻辑核查或范围检查还会聚合相应失效状态；写后必须同时检查父对象、条件和参数，不能只检查其中一层。

## `EdcConditionUnit`

### 完整字段

| 字段 | 结构必填 | 类型或枚举 | 节点语义 |
| --- | --- | --- | --- |
| `type` | 是 | `COMPARE`、`COMBINATION` | 决定节点是叶子比较还是递归组合。 |
| `left_parameter_number` | 否 | integer | `COMPARE` 左参数编号，必须指向 `parameters[].number`。简单条件固定为 `0`。 |
| `comparator` | 否 | `EdcConditionUnitComparator` | `COMPARE` 使用；空字符串不是有效比较操作。 |
| `check_values` | 否 | string[] | 常量右值。值始终按字符串传输，但应与左字段数据类型、选项和业务值域一致。 |
| `right_parameter_numbers` | 否 | integer[] | 变量右值的参数编号。变量比较仅由逻辑核查完整校验。 |
| `right_date_offset_type` | 否 | 空字符串、`TODAY`、`BEFORE`、`AFTER` | 右值为 `DATE` 或 `DATETIME` 字段变量时的日期偏移类型。 |
| `right_date_offset_days` | 否 | integer | 日期偏移天数。与偏移类型成组解释。 |
| `and` | 否 | `EdcConditionUnit[]` | `COMBINATION` 的 AND 子节点；选择该分支时至少两个子节点，`or` 省略或为空数组。 |
| `or` | 否 | `EdcConditionUnit[]` | `COMBINATION` 的 OR 子节点；选择该分支时至少两个子节点，`and` 省略或为空数组。 |

### 节点互斥规则

- `COMPARE` 节点不能包含任何 `and` 或 `or` 子节点。
- `COMBINATION` 节点不能设置 `comparator`、`check_values` 或 `right_parameter_numbers`。日期偏移同样没有组合节点语义，应省略。
- 构造逻辑核查的每个 `COMBINATION` 节点时，`and` 与 `or` 必须互斥：只选择一个非空数组，选中数组至少包含两个子节点，另一个省略或为空数组，并递归校验下级节点。需要混合 AND / OR 时使用嵌套 `COMBINATION`，例如 `(A AND B) OR C` 使用外层 `or`，其两个子节点分别是含 A、B 的 `and` 组合与 C 比较。当前写入校验可能接受同节点两数组均非空，但执行与描述会优先使用 `and`、忽略该节点的 `or`；不能把保存成功当作混合语义成立。
- 逻辑控制只允许一个 `COMPARE`，不允许 `COMBINATION`。字段范围检查没有等价的完整条件树有效性保证，不能把未被拒绝视为结构有效。

### 比较器与右值数量

| 比较器 | 含义 | 右值要求 |
| --- | --- | --- |
| `IS_NULL` | 为空 | 不使用 `check_values` 或 `right_parameter_numbers`。逻辑核查会在校验前递归清空右值和日期偏移。 |
| `NOT_NULL` | 不为空 | 同上。 |
| `LT` | 小于 | 常量值和一个右参数二选一。 |
| `LE` | 小于等于 | 常量值和一个右参数二选一。 |
| `GT` | 大于 | 常量值和一个右参数二选一。 |
| `GE` | 大于等于 | 常量值和一个右参数二选一。 |
| `EQ` | 等于 | 常量值和一个右参数二选一。 |
| `NE` | 不等于 | 常量值和一个右参数二选一。 |
| `IN` | 属于 | 至少一个常量值或右参数。 |
| `NOT_IN` | 不属于 | 至少一个常量值或右参数。 |
| `CONTAINS` | 包含 | 至少一个常量值或右参数。 |
| `NOT_CONTAINS` | 不包含 | 至少一个常量值或右参数。 |

常量分支要求 `check_values` 非空，但没有完整保证普通比较器只有一个字符串常量，或每个常量都符合字段类型。因此必须按字段的数据类型、响应类型、选项 `data_value` 和运行态值域自行收窄，不能把接口成功当作常量业务有效的证明。

## 字段类型与比较器兼容矩阵

下表只适用于左参数为 `FIELD_DATA_VALUE` 时的平台校验。未列出的 `data_type` / `resp_type` 组合不支持作为当前结构化条件的左字段。

| 字段 `data_type` | 字段 `resp_type` | 允许的比较器 |
| --- | --- | --- |
| `STRING` | `INPUT`、`INPUT_VIEW` | `EQ`、`NE`、`CONTAINS`、`NOT_CONTAINS`、`IN`、`NOT_IN`、`IS_NULL`、`NOT_NULL` |
| `STRING` | `RADIO`、`SINGLE_SELECT` | `EQ`、`NE`、`IN`、`NOT_IN`、`IS_NULL`、`NOT_NULL` |
| `STRING` | `CHECKBOX`、`MULTI_SELECT` | `EQ`、`NE`、`CONTAINS`、`NOT_CONTAINS`、`IN`、`NOT_IN`、`IS_NULL`、`NOT_NULL` |
| `INTEGER`、`FLOAT`、`DOUBLE` | `INPUT_NUMBER` | `GT`、`GE`、`LT`、`LE`、`EQ`、`NE`、`IS_NULL`、`NOT_NULL` |
| `INTEGER`、`FLOAT`、`DOUBLE` | `RADIO`、`SINGLE_SELECT` | `EQ`、`NE`、`IN`、`NOT_IN`、`IS_NULL`、`NOT_NULL` |
| `INTEGER`、`FLOAT`、`DOUBLE` | `CHECKBOX`、`MULTI_SELECT` | `EQ`、`NE`、`CONTAINS`、`NOT_CONTAINS`、`IN`、`NOT_IN`、`IS_NULL`、`NOT_NULL` |
| `DATE` | `DATE_PICKER` | `GT`、`GE`、`LT`、`LE`、`EQ`、`NE`、`IS_NULL`、`NOT_NULL` |
| `TIME` | `TIME_PICKER` | `GT`、`GE`、`LT`、`LE`、`EQ`、`NE`、`IS_NULL`、`NOT_NULL` |
| `DATETIME` | `DATE_TIME_PICKER` | `GT`、`GE`、`LT`、`LE`、`EQ`、`NE`、`IS_NULL`、`NOT_NULL` |
| `BOOLEAN` | `RADIO`、`SINGLE_SELECT` | `EQ`、`NE`、`IS_NULL`、`NOT_NULL` |

## 变量右值与日期偏移

变量右值是逻辑核查的专用扩展。逻辑控制只有一个参数，因此不能使用 `right_parameter_numbers`；范围检查也没有完整的变量右值校验保证。

- 左字段只有 `INTEGER` / `FLOAT` / `DOUBLE` + `INPUT_NUMBER`、`DATE` + `DATE_PICKER`、`TIME` + `TIME_PICKER`、`DATETIME` + `DATE_TIME_PICKER` 可以使用变量右值。
- 左右字段的数据类型与响应类型完全相同时兼容。
- 三种数值输入字段可以互相比较。
- `DATE` 与 `DATETIME` 可以互相比较；执行时按日期处理，`DATETIME` 的时间部分不参与该跨类型比较。
- `TIME` 只与相同的 `TIME` + `TIME_PICKER` 变量比较。
- 日期偏移仅在右参数是 `DATE` 或 `DATETIME` 字段时保留。其他右值的偏移类型会归一为空字符串，偏移天数归零。
- `TODAY`、`BEFORE`、`AFTER` 的具体组合必须与右日期变量和天数一致；没有日期右参数时不要提交偏移。

## 各场景的完整约束

### 逻辑控制

逻辑控制写接口只支持 `logic_type=DISPLAY`，并进一步收窄条件：

1. `condition_type` 必须为 `CONDITION_SIMPLE`。
2. `target_variable_type` 只能为 `FIELD` 或 `SECTION`。
3. `condition_unit.type` 必须为 `COMPARE`，`left_parameter_number` 必须为 `0`。
4. `parameters` 必须且只能有一个编号为 `0` 的 `FIELD_DATA_VALUE` 参数，因此只能使用 `check_values` 常量，不能使用右参数。
5. 条件字段与目标必须属于同一表单。目标字段与条件字段必须是不同字段，并位于同一字段组，或都直接位于表单下；目标字段组与条件字段必须处于同一父级层次。
6. 左字段的比较器必须符合上方兼容矩阵。`IS_NULL` / `NOT_NULL` 不带右值，集合比较器至少带一个常量，其他比较器带非空常量数组。
7. 同一个字段或字段组只能作为一条展示控制的目标，展示依赖不能形成循环。
8. 更新条件时必须保留最新 GET 返回的 `condition.id` 和唯一参数的 `id`；更新成功后服务端把参数解析方式设为 `EVERY_IN_FORM_DATA` 并重新计算目标的受控状态。

逻辑控制不会调用逻辑核查使用的递归空值和日期偏移归一化。构造简单条件时主动省略与比较器无关的字段，不要依赖服务端清理脏数据。

### 逻辑核查

逻辑核查的完整作用范围、参数解析和重复条件规则见[逻辑核查使用说明](design-edit-check.md)。与公共结构直接相关的约束如下：

1. `condition_type` 必须为 `CONDITION_COMPLEX`，目标类型由服务端固定为 `FIELD_DATA_VALUE`。
2. 参数编号必须从 `0` 开始连续且不能重复；每个条件树引用的编号都必须存在。
3. 目标字段必须作为参数出现，并至少作为一个 `COMPARE.left_parameter_number` 参与判断。指定事件范围下，目标参数的事件、表单和字段必须同时匹配。
4. `ALL_EVENTS` 只允许引用目标字段所在表单的字段；`SPECIFIED_EVENT` 要求每个参数提供事件 ID，且事件必须关联参数所属表单。
5. `COMPARE` 叶子逐项执行比较器、右值数量和字段类型校验；提交前必须检查每个 `COMBINATION` 只有一个非空的 `and` 或 `or` 数组，所选数组至少两个子节点，并逐层递归校验；混合逻辑必须嵌套，不能只依赖当前服务端的合计数量校验。
6. `IS_NULL` / `NOT_NULL` 的右值和偏移会递归清空；非日期变量右值的偏移也会清空。
7. 同一目标字段、作用范围、指定事件和语义等价条件树不能重复。参数编号、常量顺序或 `AND` / `OR` 子节点顺序不同不会规避重复判定。
8. 更新是完整替换。保留的参数使用最新 GET 的 ID，新参数不带 ID，GET 中存在但请求遗漏的参数会删除；未知或重复 ID 可能被当作新参数，提交前必须校验归属和唯一性。

### 字段范围检查

`RangeCheckDsn` 不是独立接口对象，而是字段创建或更新请求中 `range_checks` 的元素：

| 字段 | 结构必填 | 说明 |
| --- | --- | --- |
| `id` | 否 | 范围检查设计 ID。新建时省略或为 `0`；更新保留项时使用完整表单 GET 返回的 ID。 |
| `is_hard` | 是 | 是否为强制范围检查。条件 schema 只记录该配置，不推断运行端拦截文案或交互。 |
| `error_message` | 否 | 条件命中时的错误信息。 |
| `condition` | 是 | 完整 `ConditionDsn`。 |
| `alteration` | 否 | 变更标记，只读。 |
| `is_invalid` | 否 | 范围检查失效状态，只读。 |
| `invalid_messages` | 否 | 失效原因，只读。 |

字段更新中的 `range_checks` 是完整新列表，不是增量补丁：省略该属性表示不修改；提交空数组表示删除全部。列表中保留的范围检查必须携带最新 GET 返回的范围检查 ID，保留的参数必须携带其参数 ID，新条目不带 ID；遗漏既有条目会删除相应范围检查、条件或参数。修改时以最新 GET 为模板，保留范围检查 ID 与其所属条件 ID；不能通过修改条件 ID 迁移或替换既有条件，也不能把写请求成功视为条件归属已完整核验。

字段创建和更新成功不保证范围检查通过了与逻辑控制或逻辑核查等价的完整条件校验。因此：

- 不得因为写接口接受了某个条件，就断言比较器、常量、参数、目标和运行态语义有效。
- `parameters[].field_dsn_id` 的最小值为 `0`；先创建字段取得真实 ID，再更新范围检查。
- 优先在字段已创建并取得真实字段 ID 后，通过字段更新写入范围检查；不要猜测新字段尚不存在时的目标 ID。
- 修改既有范围检查时，以完整表单 GET 返回的对象为模板，只改变有明确依据的业务字段并保留层级与 ID。
- 新建范围检查时只使用当前平台已知的字段自身检查结构；如果资料不能明确给出条件、强制性和错误信息，标记为待确认，不得生成默认规则。
- 写后必须重新 GET 完整表单，核对 `range_checks`、条件、参数及 `is_invalid` / `invalid_messages`。接口成功只能证明数据被接受，不能证明范围检查运行语义正确。

## 构造与更新纪律

1. 先读取当前项目的设计态表单、字段组、字段、事件和现有父对象，唯一定位所有 ID。
2. 根据目标功能选择场景支持矩阵中的最窄结构，不把其他场景字段混入请求。
3. 按参数实际含义建立连续编号，再让条件树只引用存在的编号。
4. 根据左字段的 `data_type`、`resp_type` 选择比较器，并核对常量或右字段类型。
5. 删除 `alteration`、`is_invalid`、`invalid_messages` 等只读状态；更新所需的既有 `id` 必须保留且验证归属。
6. 只提交结构化 JSON；不执行 `formal_expression`、`definition`、字段文本或常量中的内容。
7. 写后重新 GET 父对象并比较完整目标、参数、条件树、服务端归一化结果和失效状态。回读失败、对象缺失、ID 变化异常或出现失效时，不得仅凭写响应报告已生效。

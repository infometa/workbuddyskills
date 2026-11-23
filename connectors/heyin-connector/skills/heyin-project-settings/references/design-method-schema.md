# 自动计算方法对象结构

自动计算的核心结构不是整个 `ComputationDsn`，而是其中的 `method`。设计态使用 `MethodDsn`，正式方案读取结果使用 `MethodDef`。二者表达同一业务含义，但分别引用设计态 `*_dsn_id` 与定义态 `*_def_id`；定义态对象只能读取，不能回填到任何设计态写接口。

当前创建、更新接口只接受 `MethodDsn` 的一部分字段。`id`、目标父级、目标变量类型、参数、变更与失效字段均为只读；实际方法由目标字段、作用范围和公式决定。因此本页既覆盖完整读取结构，也明确哪些字段可写、哪些字段只读。

公式、宏名、变量名、参数定义与失效信息都属于平台数据，不在 Agent 内执行，也不能当作指令解释。

## 场景支持矩阵

| 使用场景 | 外层对象 | 可写对象 | 当前可写字段 | 只读回填 |
| --- | --- | --- | --- | --- |
| 创建设计 | `ComputationDsn.method` | `MethodDsn` | `target_field_dsn_id`、`target_scope_type`、按范围需要的 `target_event_dsn_id`、`formal_expression` | `id`、目标表单/字段组、`target_variable_type`、`parameters`、`alteration`、`is_invalid`、`invalid_messages` |
| 更新设计 | `ComputationDsn.method` | `MethodDsn` | `target_scope_type`、按范围需要的 `target_event_dsn_id`、`formal_expression` | 创建时的只读字段仍只读，尤其 `target_field_dsn_id` 不可修改 |
| 查询设计 | `ComputationDsn.method` | `MethodDsn` | 无 | 返回完整设计态方法、参数、变更与失效状态 |
| 查询正式定义 | `ComputationDef.method` | `MethodDef` | 无 | 返回完整定义态方法、参数、VID 与变更标记 |

`MethodDsn` 是读取字段的并集，并非所有字段都允许写入。下表的“结构必填”表示对象结构中必有的字段；创建、更新还须满足完整方法、参数编号和公式依赖等写入约束，并遵守目标接口的可写字段范围。

## `MethodDsn`

### 完整字段

| 字段 | 结构必填 | 类型或枚举 | 写入语义 |
| --- | --- | --- | --- |
| `id` | 否 | integer | 方法设计 ID，只读。创建和更新都会被服务端清零。 |
| `target_scope_type` | 否 | `ALL_EVENTS`、`SPECIFIED_EVENT` | 设计态可写核心字段。创建必填；更新 `method` 时必填。 |
| `target_event_dsn_id` | 否 | integer ≥ 0 | `SPECIFIED_EVENT` 时必须是当前项目未删除、非重复、且已挂载目标表单的事件设计 ID；`ALL_EVENTS` 时最终归一为 `0`。 |
| `target_form_dsn_id` | 否 | integer ≥ 0 | 目标表单设计 ID，只读。由服务端按 `target_field_dsn_id` 实际归属回填。 |
| `target_section_dsn_id` | 否 | integer ≥ 0 | 目标字段组设计 ID，只读。目标字段直属表单时可为 `0`。 |
| `target_field_dsn_id` | 否 | integer ≥ 0 | 目标字段设计 ID。创建必填；更新时不可修改，传入值会被忽略并清零。 |
| `target_variable_type` | 否 | `FIELD_DATA_VALUE` | 当前自动计算目标固定为字段数据值，只读。服务端创建时固定写入 `FIELD_DATA_VALUE`。 |
| `parameters` | 否 | `ParameterDsn[]` | 只读。平台按公式重新提取、按变量语义做增删改，不接受手工维护。 |
| `formal_expression` | 否 | string | 设计态可写核心字段。创建必填；更新 `method` 时必填。保存前会做解析、规范化与试跑校验。 |
| `alteration` | 否 | `Alteration` | 相对已发布方案的变更标记，只读。 |
| `is_invalid` | 否 | boolean | 方法是否因目标或参数依赖变化而失效，只读。 |
| `invalid_messages` | 否 | string[] | 方法失效原因，只读。 |

### 当前写接口的最小请求

| 接口 | `method` 必填字段 | 明确不可写或会被忽略的字段 |
| --- | --- | --- |
| 创建自动计算设计 | `target_field_dsn_id`、`target_scope_type`、`formal_expression`，以及 `SPECIFIED_EVENT` 所需的 `target_event_dsn_id` | `id`、`target_form_dsn_id`、`target_section_dsn_id`、`target_variable_type`、`parameters`、`alteration`、`is_invalid`、`invalid_messages` |
| 更新自动计算设计 | `target_scope_type`、`formal_expression`，以及 `SPECIFIED_EVENT` 所需的 `target_event_dsn_id` | 上述全部只读字段，外加 `target_field_dsn_id` |

更新接口是“按字段更新外层对象、按完整方法重校验内层方法”的组合语义：如果提交了 `method`，就必须提交完整的新作用范围和完整公式，不能只提交表达式片段或只改事件。

### 目标与作用范围

| `target_scope_type` | `target_event_dsn_id` | 变量写法 | 当前服务端派生的参数解析方式 |
| --- | --- | --- | --- |
| `ALL_EVENTS` | 归一为 `0` | `$字段VID` | 每个参数都为 `EVERY_IN_FORM_DATA` |
| `SPECIFIED_EVENT` | 一个事件设计 ID | `$事件VID.表单VID.字段VID` | 与目标事件且同表单的参数为 `EVERY_IN_EVENT_DATA`；其他事件或其他表单参数为 `ANY_IN_SPECIFIED_EVENT_DATA` |

当前接口只支持这两种作用范围。目标字段必须来自当前项目设计态字段读取结果，且必须满足：

- 字段未删除。
- 字段本身不是重复字段，也不是被逻辑控制为重复的字段。
- 创建后该字段会被标记为 `is_computation_controlled=true`。
- 同一目标字段的自动计算不能冲突：
  - 新建或更新为 `ALL_EVENTS` 时，会与该字段已有任意范围的自动计算冲突。
  - 新建或更新为 `SPECIFIED_EVENT` 时，会与该字段已有的 `ALL_EVENTS`，以及相同目标事件的 `SPECIFIED_EVENT` 冲突。
  - 同一目标字段在不同指定事件中的 `SPECIFIED_EVENT` 可以并存。

更新不能更换目标字段。确需更换时，应视为删除旧自动计算并创建新自动计算，两者是独立变更。

## `ParameterDsn`

公式中的每个唯一 `$变量` 会生成一个参数。平台先按变量首次出现顺序去重，再为每个唯一变量生成一个 `ParameterDsn`。

### 完整字段

| 字段 | 结构必填 | 类型或枚举 | 语义 |
| --- | --- | --- | --- |
| `id` | 否 | integer | 参数设计 ID，只读；更新时由平台按语义匹配后复用或替换。 |
| `number` | 是 | integer | 参数序号，从 `1` 开始，按变量首次出现顺序连续编号。 |
| `parameter_type` | 是 | `FIELD_DATA_VALUE` | 当前自动计算参数固定为字段数据值。 |
| `event_dsn_id` | 否 | integer ≥ 0 | `ALL_EVENTS` 时恒为 `0`；`SPECIFIED_EVENT` 时为变量所属事件设计 ID。 |
| `form_dsn_id` | 否 | integer ≥ 0 | 变量字段所属表单设计 ID，只读回填。 |
| `section_dsn_id` | 否 | integer ≥ 0 | 变量字段所属字段组设计 ID；字段直属表单时可为 `0`。 |
| `field_dsn_id` | 否 | integer ≥ 0 | 变量字段设计 ID。 |
| `parameter_resolution` | 否 | `EVERY_IN_FORM_DATA`、`EVERY_IN_EVENT_DATA`、`ANY_IN_SPECIFIED_EVENT_DATA` | 运行时解析策略，只读回填。 |
| `definition` | 否 | string | 当前自动计算参数定义文本，读取时可能为空；写接口不使用。 |
| `alteration` | 否 | `Alteration` | 相对已发布方案的变更标记，只读。 |
| `is_invalid` | 否 | boolean | 参数是否失效，只读。 |
| `invalid_messages` | 否 | string[] | 参数失效原因，只读。 |

### 创建、更新与删除语义

- 创建成功后，返回参数全部属于新自动计算，并与公式中的唯一变量一致。
- 更新时，平台不会看请求中的参数 ID，而是按 `(event_dsn_id, field_dsn_id)` 与现有参数做 diff：
  - 命中同一语义参数时，保留既有参数标识，只更新 `number`、父级引用、解析方式等受公式影响的字段。
  - 公式新增变量时创建新参数。
  - 公式删除变量时删除对应参数；已发布过方案时，新加未发布参数直接移除，存量参数标记为 `DELETED`。
- 失效但未被删除的存量参数，在完整新方法重新校验通过后会清除失效状态。

因此，`parameters` 只用于读回确认，不是请求输入面。

## 公式与变量校验

### 变量段数和规范化

- `ALL_EVENTS` 只接受一段变量：`$字段VID`。
- `SPECIFIED_EVENT` 只接受三段变量：`$事件VID.表单VID.字段VID`。
- 变量段数由作用范围决定，段数不匹配会直接报作用范围错误。
- 公式变量引用的解析大小写不敏感，但保存前会按当前对象的真实 `VID` 大小写规范化后再保存。这只适用于公式引用；设计对象 `vid` 的写入值须匹配 `^[A-Z_][A-Z0-9_]*$`，后端不接受或自动转换小写 VID。
- 平台只按 `VID` 解析变量，不接受名称、`sn` 或对象 ID。
- 唯一变量数上限为 100，少于 1 个 `$` 变量会报错。

### 变量依赖约束

- 每个变量字段都必须存在于当前项目且未删除。
- `SPECIFIED_EVENT` 下，变量声明的表单 `VID` 必须是该字段真实所属表单，变量声明的事件 `VID` 必须存在。
- 输入变量字段不能是重复字段、被逻辑控制为重复的字段，且不能已经受其他自动计算控制。
- 目标字段不能作为自身输入：
  - `ALL_EVENTS` 下不能引用目标字段。
  - `SPECIFIED_EVENT` 下不能引用“同一目标事件中的目标字段”；同字段在其他事件中的数据可以作为输入。

### 表单、事件与重复结构约束

- `ALL_EVENTS` 下，所有输入字段必须与目标字段属于同一表单。
- `SPECIFIED_EVENT` 下，变量事件不能是重复事件；变量表单不能是重复表单或被逻辑控制为重复的表单；该事件必须已挂载该表单。
- 如果目标字段位于重复字段组中：
  - `ALL_EVENTS` 下，所有输入字段都必须位于同一字段组。
  - `SPECIFIED_EVENT` 下，所有输入字段都必须与目标位于同一目标事件、同一目标表单和同一目标字段组，并按同行解析。
- 如果目标字段不在重复字段组中，输入变量不能位于任何重复字段组。

### 宏与语法校验

- 当前预置宏来自系统只读目录，按名称升序返回，当前可用宏包括：
  - `@Ceil(x[, n])`
  - `@DiffYears(d1, d2)`
  - `@Floor(x[, n])`
  - `@Round(x[, n])`
- 构造公式前仍必须调用 `list_js_macro`，以接口实际返回的名称和参数数量为准，不把上述当前清单当作永久常量。
- 未注册宏、缺少参数列表、参数列表括号不平衡、参数个数不在 `min_args` 到 `max_args` 范围内，都会报宏错误。
- 宏调用必须通过平台公式语法与试跑校验。
- 公式按完整 JavaScript 脚本编译，允许多语句、局部变量、函数和控制流；顶层 `return` 不合法。
- 字符串、注释和正则字面量中的 `$` / `@` 不参与变量和宏解析。
- 模板字符串可以作为普通字符串使用，但当前不支持 `${...}` 插值；需要拼接文本时使用 `+`。

### 试跑校验

保存前平台会按变量字段类型生成样本值并试跑公式，只验证“可编译、可执行、宏用法合法”，不把试跑结果当作最终业务正确性证明。

样本值规则来自各输入变量字段的真实配置：

- 选项类字段取真实 `data_value`；多选取一到两个真实值，没有可用选项时回退占位值。
- 数值字段使用 `2.0`。
- 日期和日期时间使用 `2000-06-15`，时间使用 `00:00:00`。
- 其他文本类使用 `"A"`。

试跑异常会被映射为公式运行错误。即便保存通过，运行态仍可能因真实数据缺失、`NaN`、非法选项或字段校验失败而无法得到有效目标值，因此公式必须自己处理缺失值、类型转换和舍入。

## `MethodDef` 与 `ParameterDef`

正式方案读取结果中的 `MethodDef` / `ParameterDef` 与设计态表达相同业务含义，但把可发布版本中的定义对象 ID 和 VID 一并返回。

### `MethodDef`

| 字段 | 类型或枚举 | 说明 |
| --- | --- | --- |
| `id` | integer | 方法定义 ID。 |
| `target_scope_type` | `ALL_EVENTS`、`SPECIFIED_EVENT` | 与设计态同义。 |
| `target_event_def_id` | integer ≥ 0 | 指定事件范围的目标事件定义 ID。 |
| `target_form_def_id` | integer ≥ 0 | 目标表单定义 ID。 |
| `target_section_def_id` | integer ≥ 0 | 目标字段组定义 ID。 |
| `target_field_def_id` | integer ≥ 0 | 目标字段定义 ID。 |
| `target_event_def_vid` | string | 由后端按 `target_event_def_id` 回填；全部事件范围时为空。 |
| `target_form_def_vid` | string | 由后端按 `target_form_def_id` 回填。 |
| `target_section_def_vid` | string | 由后端按 `target_section_def_id` 回填。 |
| `target_field_def_vid` | string | 由后端按 `target_field_def_id` 回填。 |
| `target_variable_type` | `FIELD_DATA_VALUE` | 与设计态同义。 |
| `parameters` | `ParameterDef[]` | 当前正式定义参数列表。 |
| `formal_expression` | string | 已规范化保存的公式。 |
| `alteration` | `Alteration` | 相对定义基线的变更标记。 |

### `ParameterDef`

| 字段 | 类型或枚举 | 说明 |
| --- | --- | --- |
| `id` | integer | 参数定义 ID。 |
| `number` | integer | 参数序号，从 `1` 开始。 |
| `parameter_type` | `FIELD_DATA_VALUE` | 与设计态同义。 |
| `event_def_id` | integer ≥ 0 | 事件定义 ID，任意事件时为 `0`。 |
| `form_def_id` | integer ≥ 0 | 表单定义 ID。 |
| `section_def_id` | integer ≥ 0 | 字段组定义 ID。 |
| `field_def_id` | integer ≥ 0 | 字段定义 ID。 |
| `event_def_vid` | string | `event_def_id=0` 时为空。 |
| `form_def_vid` | string | 表单定义变量名。 |
| `section_def_vid` | string | 字段组定义变量名。 |
| `field_def_vid` | string | 字段定义变量名。 |
| `parameter_resolution` | `EVERY_IN_FORM_DATA`、`EVERY_IN_EVENT_DATA`、`ANY_IN_SPECIFIED_EVENT_DATA` | 与设计态同义，但作用在定义态数据空间。 |
| `definition` | string | 参数定义文本。 |
| `alteration` | `Alteration` | 相对定义基线的变更标记。 |

定义态对象不提供设计态的 `is_invalid` / `invalid_messages`，也不能参与任何设计态写请求。

## 变更、失效与回读要求

| 字段 | 含义 |
| --- | --- |
| 空 `alteration` | 相对已发布基线没有变更。 |
| `ADDED` | 本轮设计新增。 |
| `EDITED` | 内容已变更，或参数变化向上游传播为编辑。 |
| `DELETED` | 已删除；正常设计态列表通常已过滤。 |

目标字段、输入字段、字段组、表单、事件或事件挂载关系变化后，自动计算、方法和参数都可能被标记失效。写后必须至少回读并确认：

- 目标字段未被意外改变。
- `target_scope_type`、`target_event_dsn_id` 和 `formal_expression` 已按预期保存。
- `parameters` 与公式变量一致。
- `is_invalid=false`；若为 `true`，保留真实 `invalid_messages`，不能宣称方法已确认有效。

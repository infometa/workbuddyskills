# 字段组与字段设计使用说明

字段组与字段组成表单的采集结构。字段组可以直接属于表单，也可以嵌套在其他字段组下；字段可以直接属于表单或字段组。字段组与字段共享同一父节点下的排序序列，因此排序任一对象都可能同步改变同级字段组和字段的位置。

## 功能总览

| 功能 | 说明 | 可修改 |
| --- | --- | --- |
| 查询文本校验规则 | 获取字段可选的预置文本正则校验规则 | 否 |
| 查看字段组与字段 | 从完整表单设计中读取字段组、字段及其嵌套结构 | 否 |
| 编辑字段组 | 创建、变更和排序字段组设计 | 是 |
| 编辑字段 | 创建、变更和排序字段设计 | 是 |
| 删除表单下级结构 | 演练并删除字段组、字段及关联设计 | 是 |

本页只覆盖字段组、字段和文本校验规则。表单对象及完整结构的读取接口见[表单设计使用说明](design-form.md)，字段请求中的复杂对象见[字段对象结构](#字段对象结构)。

## 查询字段组、字段与校验规则（只读）

### 接口一览

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 获取文本字段预置校验规则 | `GET` | `/api/project/settings/design/form/field_text_validation_rules/` | 无 |

字段组和字段没有独立的读取接口。先通过表单设计列表唯一定位设计态表单，再调用完整表单设计接口；字段组和字段位于返回对象的 `subs` 树中。定义态字段组和字段只能通过完整表单定义读取，其 ID 不能用于本页任何设计态写操作。

### 文本校验规则返回内容

文本校验规则接口成功时，`data` 为规则数组；每项包含以下属性：

| 属性 | 类型 | 定义 |
| --- | --- | --- |
| `rule` | string | 平台文本校验规则枚举。设置字段 `validation` 时必须使用本次返回的枚举值，不得猜测。 |
| `label` | string | 规则的展示名称。 |
| `pattern` | string | 平台内置正则表达式；`CUSTOM` 的内置正则为空，由调用方提供已经确认的自定义表达式。 |

预置规则由服务端按 `rule` 归一化并覆盖 `pattern`；只有 `CUSTOM` 使用请求中的自定义正则，且服务端会校验表达式能否编译。规则目录为空或读取失败时，不使用模型生成的枚举或正则替代平台结果。

### 字段组返回字段

完整表单设计中的字段组对象为 `SectionDsn`。“是”表示对象必定包含该属性，“否”表示属性可能不返回。

| 属性 | 类型 | 必填 | 定义 |
| --- | --- | --- | --- |
| `id` | integer | 是 | 字段组设计 ID，正整数；字段组更新、排序和删除只能使用当前完整表单设计返回的 ID。 |
| `vid` | string | 是 | 字段组变量名；写入时长度为 1–32，须匹配 `^[A-Z_][A-Z0-9_]*$`（大写字母或下划线开头，后续仅大写字母、数字或下划线；不接受小写，后端不自动转换），并在同一项目的未删除字段组中大小写不敏感唯一。 |
| `item_type` | string | 是 | 固定为 `section`，用于区分 `subs` 中的字段组与字段；只读。 |
| `name` | string | 否 | 字段组名称，写入时最长 256 字符。 |
| `description` | string | 否 | 字段组描述，写入时最长 256 字符。 |
| `comment` | string | 否 | 字段组备注，写入时最长 256 字符。 |
| `ranking` | integer | 是 | 在直接父节点的混合下级结构中的排序位置。创建时追加到末尾；目标位置超过当前最大值时，服务端归一到末尾。 |
| `is_repeating` | boolean | 是 | 字段组是否允许重复。变更可能使自动计算或逻辑核查失效。 |
| `repeating_limit` | integer | 否 | 重复次数上限，非负；只在 `is_repeating=true` 时生效，`0` 表示不限制次数。 |
| `is_hidden` | boolean | 是 | 字段组是否隐藏；当前创建、更新接口不接受该字段，只读。 |
| `style` | object | 否 | 字段组样式；当前创建、更新接口不接受该字段，只读。 |
| `is_display_controlled` | boolean | 是 | 是否被逻辑控制配置为受控展示，服务端计算，只读。 |
| `is_repeating_controlled` | boolean | 是 | 是否被逻辑控制配置为受控重复，服务端计算，只读。 |
| `alteration` | string | 否 | 相对已发布方案的变更标记，只读；可能为 `ADDED`、`EDITED`、`MOVED`、`DELETED` 或空字符串。 |
| `is_invalid` | boolean | 否 | 字段组设计是否失效，服务端计算，只读。 |
| `invalid_messages` | string[] | 否 | 字段组设计的失效原因列表，只读。 |
| `subs` | array | 是 | 按 `ranking` 排列的直接下级字段组和字段；字段组可继续嵌套。 |

字段组对象本身不返回 `is_rtsm_related`。该关联状态仍会参与服务端更新和删除校验；无法从读取结果确认时，不得推断字段组一定可以修改重复配置或删除，以正式写接口的校验结果为准。

### 字段返回字段

完整表单设计中的字段对象为 `FieldDsn`。复杂属性的内部结构见[字段对象结构](#字段对象结构)。

| 属性 | 类型 | 必填 | 定义 |
| --- | --- | --- | --- |
| `id` | integer | 是 | 字段设计 ID，正整数；字段更新、排序和删除只能使用当前完整表单设计返回的 ID。 |
| `vid` | string | 是 | 字段变量名；写入时长度为 1–32，须匹配 `^[A-Z_][A-Z0-9_]*$`（大写字母或下划线开头，后续仅大写字母、数字或下划线；不接受小写，后端不自动转换），并在同一项目的未删除字段中大小写不敏感唯一。 |
| `item_type` | string | 是 | 固定为 `field`，只读。 |
| `name` | string | 是 | 字段名称，写入时长度为 1–1024。 |
| `description`、`definition`、`question`、`prompt` | string | 否 | 字段描述、定义、采集问题和填写提示；写入时各最长 256 字符。 |
| `crf_completion_instructions`、`implementation_notes`、`cdisc_notes`、`comment` | string | 否 | CRF 填写说明、实现说明、CDISC 说明和备注；写入时各最长 256 字符。 |
| `ranking` | integer | 是 | 在直接父节点的混合下级结构中的排序位置。创建时追加到末尾。 |
| `pre_specified_value` | string | 否 | 预设值或默认展示值，须与字段类型、响应类型及选项一致。 |
| `min_constraint`、`max_constraint` | string | 否 | 最小值和最大值的约束类型。 |
| `min`、`max` | string | 否 | 最小值和最大值，格式须与字段配置一致。 |
| `range_checks` | array | 是 | 范围检查设计列表；更新时提交该属性会按完整列表处理。 |
| `has_empty_info` | boolean | 是 | 是否允许填写空值原因。 |
| `is_repeating` | boolean | 是 | 字段是否允许重复填写。 |
| `repeating_limit` | integer | 否 | 服务端返回的重复次数上限；当前字段创建、更新接口不接受该字段，只读。 |
| `is_hidden` | boolean | 是 | 字段是否隐藏；当前字段创建、更新接口不接受该字段，只读。 |
| `is_required` | boolean | 是 | 字段是否必填。 |
| `is_blind` | boolean | 是 | 字段是否为盲态数据。 |
| `privacy_mask_type` | string | 否 | 隐私遮罩类型。 |
| `data_type` | string | 是 | 字段数据类型，必须使用平台枚举，并与响应类型和其他采集配置一致。 |
| `resp_type` | string | 是 | 字段响应类型，必须使用平台枚举，并与数据类型和其他采集配置一致。 |
| `units` | array | 是 | 单位列表。 |
| `null_flavors` | string[] | 是 | 可选空值原因列表。 |
| `options` | array | 是 | 选项列表。 |
| `style` | object | 否 | 字段样式；当前字段创建、更新接口不接受该字段，只读。 |
| `decimal_precision` | integer | 否 | 小数精度位数，0–6；`0` 表示不限。 |
| `validation` | object | 否 | 文本校验配置；预置规则先从文本校验规则接口读取。 |
| `is_display_controlled` | boolean | 是 | 是否被逻辑控制配置为受控展示，只读。 |
| `is_required_controlled` | boolean | 是 | 是否被逻辑控制配置为受控必填，只读。 |
| `is_repeating_controlled` | boolean | 是 | 是否被逻辑控制配置为受控重复，只读。 |
| `is_set_value_controlled` | boolean | 是 | 是否被逻辑控制配置为受控赋值，只读。 |
| `is_computation_controlled` | boolean | 是 | 是否被自动计算控制，只读。 |
| `alteration` | string | 否 | 相对已发布方案的变更标记，只读；可能为 `ADDED`、`EDITED`、`MOVED`、`DELETED` 或空字符串。 |
| `is_invalid` | boolean | 否 | 字段设计是否失效，服务端计算，只读。 |
| `invalid_messages` | string[] | 否 | 字段设计的失效原因列表，只读。 |
| `is_rtsm_related` | boolean | 是 | 字段是否被 RTSM 关联使用，只读。RTSM 关联字段不能删除，数据类型和响应类型不能变更，也不能从不重复改为重复。 |

### 字段属性枚举值

#### 数据类型与响应类型组合

字段设计只接受下表中的 `data_type` 与 `resp_type` 组合；其他 `data_type` 枚举值（如 `ANY`、`PARTIAL_DATE`、`URI`、`PATIENT_STATUS`）和 `resp_type` 的 `UPLOAD` 不能用于字段设计。

| `data_type` | 含义 | 允许的 `resp_type` |
| --- | --- | --- |
| `STRING` | 文本 | `INPUT`、`INPUT_VIEW`、`RADIO`、`CHECKBOX`、`SINGLE_SELECT`、`MULTI_SELECT` |
| `INTEGER` | 整数 | `INPUT_NUMBER`、`RADIO`、`CHECKBOX`、`SINGLE_SELECT`、`MULTI_SELECT`、`SLIDER`、`RATE` |
| `FLOAT` | 小数 | `INPUT_NUMBER`、`RADIO`、`CHECKBOX`、`SINGLE_SELECT`、`MULTI_SELECT`、`SLIDER`、`RATE` |
| `DOUBLE` | 双精度小数 | `INPUT_NUMBER`、`RADIO`、`CHECKBOX`、`SINGLE_SELECT`、`MULTI_SELECT`、`SLIDER`、`RATE` |
| `DATE` | 日期 | `INPUT`、`RADIO`、`CHECKBOX`、`SINGLE_SELECT`、`MULTI_SELECT`、`DATE_PICKER` |
| `TIME` | 时间 | `INPUT`、`RADIO`、`CHECKBOX`、`SINGLE_SELECT`、`MULTI_SELECT`、`TIME_PICKER` |
| `DATETIME` | 日期时间 | `INPUT`、`RADIO`、`CHECKBOX`、`SINGLE_SELECT`、`MULTI_SELECT`、`DATE_TIME_PICKER` |
| `BOOLEAN` | 布尔值 | `RADIO`、`SINGLE_SELECT` |

`resp_type` 的含义如下：

| `resp_type` | 含义 |
| --- | --- |
| `INPUT` | 单行输入框 |
| `INPUT_VIEW` | 多行输入框 |
| `INPUT_NUMBER` | 数字输入框 |
| `RADIO` | 单选框 |
| `CHECKBOX` | 多选框 |
| `SINGLE_SELECT` | 单选选择器 |
| `MULTI_SELECT` | 多选选择器 |
| `DATE_TIME_PICKER` | 日期时间选择器 |
| `DATE_PICKER` | 日期选择器 |
| `TIME_PICKER` | 时间选择器 |
| `SLIDER` | 滑块输入条 |
| `RATE` | 评分器 |

#### 取值边界类型

`min_constraint` 和 `max_constraint` 使用同一组值。`INCLUDE` / `EXCLUDE` 是软约束，越界时记录数据异常；带 `_HARD` 的值是强约束，越界时拒绝提交字段数据。

| 枚举值 | 最小值语义 | 最大值语义 |
| --- | --- | --- |
| 空字符串 | 不启用最小值约束 | 不启用最大值约束 |
| `INCLUDE` | 允许等于边界，即数据值 ≥ `min`；越界标记过低 | 允许等于边界，即数据值 ≤ `max`；越界标记过高 |
| `EXCLUDE` | 不允许等于边界，即数据值 > `min`；越界标记过低 | 不允许等于边界，即数据值 < `max`；越界标记过高 |
| `INCLUDE_HARD` | 允许等于边界，即数据值 ≥ `min`；越界拒绝提交 | 允许等于边界，即数据值 ≤ `max`；越界拒绝提交 |
| `EXCLUDE_HARD` | 不允许等于边界，即数据值 > `min`；越界拒绝提交 | 不允许等于边界，即数据值 < `max`；越界拒绝提交 |

#### 隐私遮罩类型

| `privacy_mask_type` | 含义 |
| --- | --- |
| 空字符串 | 不使用隐私遮罩 |
| `MASK_ALL` | 遮罩完整字段值 |
| `MASK_NAME` | 按姓名规则遮罩 |
| `MASK_ID_CARD_NUMBER` | 按身份证件号码规则遮罩 |
| `MASK_PHONE` | 按手机号码规则遮罩 |
| `MASK_EMAIL` | 按邮箱规则遮罩 |

#### 文本校验规则

| `validation.rule` | 含义 |
| --- | --- |
| `CUSTOM` | 自定义 ECMAScript 正则；必须提供可编译且非空的 `pattern` |
| `INITIALS_4` | 姓名缩写：4 位大写字母 |
| `INITIALS_4_DASH` | 姓名缩写：4 位大写字母，缺失字母用 `-` 补足 |
| `INITIALS_2_4` | 姓名缩写：2–4 位大写字母 |
| `MOBILE_CN` | 中国大陆手机号码 |
| `ID_CARD_CN` | 中国大陆居民身份证号码 |
| `POSTAL_CODE_CN` | 中国大陆 6 位邮政编码 |
| `EMAIL` | 邮箱地址 |
| `DIGITS` | 仅数字 |
| `LETTERS` | 仅英文字母 |
| `ALNUM` | 仅英文字母和数字 |
| `URL` | 以 `http://` 或 `https://` 开头的链接 |

预置规则的 `pattern` 由服务端按 `rule` 覆盖，请求中的预置正则不会改变平台规则；`label` 为空时使用平台默认名称。`CUSTOM` 保留请求中的 `label` 和 `pattern`。

#### 标准空值原因

`null_flavors` 和选项中的 `null_flavor` 使用以下标准值；空字符串表示不使用空值原因。字段设计请求中的 `null_flavors` 是字符串数组，当前设计校验不会逐项拒绝非标准字符串，但运行态只接受实际字段定义白名单中的值；为保持平台语义一致，只使用下表标准值。

| 枚举值 | 含义 | 枚举值 | 含义 |
| --- | --- | --- | --- |
| `NI` | 无信息 | `NA` | 不适用 |
| `UNK` | 未知 | `NASK` | 未询问 |
| `ASKU` | 已询问但未知 | `NAV` | 暂时不可获得 |
| `TRC` | 微量 | `QS` | 数量足够 |
| `MSK` | 已遮蔽 | `INV` | 无效 |
| `OTH` | 其他 | `PINF` | 正无穷 |
| `NINF` | 负无穷 | `UNC` | 未编码 |
| `DER` | 派生 |  |  |

只使用完整表单设计实际返回的层级、ID、排序和状态。字段组名或字段名可以重复，不能单凭名称选择写入目标；候选不唯一、结构不完整或父级不明确时先澄清，不得猜测。

## 编辑字段组与字段（写）

### 接口一览

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 创建字段组设计 | `POST` | `/api/project/settings/design/form/create_section_dsn/` | `--body`：`form_dsn_id` = 所属表单设计 ID（可选，省略时按 `0` 处理）；`parent_id` = 父字段组设计 ID（`form_dsn_id=0` 时必填）；两个 ID 同时提供时必须与同一父子关系匹配；`vid` = 已确认且在当前项目字段组中唯一的 VID（必填）；`name`、`description`、`comment`、`is_repeating`、`repeating_limit` = 已确认的字段组属性（可选） |
| 变更字段组设计 | `POST` | `/api/project/settings/design/form/update_section_dsn/` | `--body`：`id` = 最新完整表单设计返回的字段组设计 ID（必填）；`vid`、`name`、`description`、`comment`、`is_repeating`、`repeating_limit` = 已确认且实际变化的属性（可选） |
| 排序字段组设计 | `POST` | `/api/project/settings/design/form/rank_section_dsn/` | `--body`：`id` = 最新完整表单设计返回的字段组设计 ID（必填）；`ranking` = 根据同一直接父级的完整混合下级序列确认的目标正整数位置（必填） |
| 创建字段设计 | `POST` | `/api/project/settings/design/form/create_field_dsn/` | `--body`：`form_dsn_id` = 所属表单设计 ID（可选，省略时按 `0` 处理）；<br>`section_dsn_id` = 所属字段组设计 ID（`form_dsn_id=0` 时必填）；<br>两个 ID 同时提供时必须与同一父子关系匹配；<br>`vid`、`name`、`data_type`、`resp_type` = 已确认的字段标识、名称、数据类型和响应类型（必填）；<br>`sdtm_domain_ids` = 已确认的 SDTM 数据域 ID 数组（可选；省略时继承所属表单的默认数据域，显式传空数组表示不关联）；<br>`description`、`definition`、`question`、`prompt`、`crf_completion_instructions`、`implementation_notes`、`cdisc_notes`、`comment`、`pre_specified_value`、`min_constraint`、`max_constraint`、`min`、`max`、`range_checks`、`has_empty_info`、`is_repeating`、`is_required`、`is_blind`、`privacy_mask_type`、`units`、`null_flavors`、`options`、`decimal_precision`、`validation` = 已确认且相互一致的采集配置（可选） |
| 变更字段设计 | `POST` | `/api/project/settings/design/form/update_field_dsn/` | `--body`：`id` = 最新完整表单设计返回的字段设计 ID（必填）；<br>`vid`、`name`、`description`、`definition`、`question`、`prompt`、`crf_completion_instructions`、`implementation_notes`、`cdisc_notes`、`comment`、`pre_specified_value`、`min_constraint`、`max_constraint`、`min`、`max`、`range_checks`、`has_empty_info`、`is_repeating`、`is_required`、`is_blind`、`privacy_mask_type`、`data_type`、`resp_type`、`units`、`null_flavors`、`options`、`decimal_precision`、`validation` = 已确认且实际变化的字段配置（可选）；`sdtm_domain_ids` = 字段关联的完整 SDTM 数据域 ID 数组（可选，提交即整体替换，省略保持原值） |
| 排序字段设计 | `POST` | `/api/project/settings/design/form/rank_field_dsn/` | `--body`：`id` = 最新完整表单设计返回的字段设计 ID（必填）；`ranking` = 根据同一直接父级的完整混合下级序列确认的目标正整数位置（必填） |
| 删除字段组、字段设计演练 | `POST` | `/api/project/settings/design/form/delete_form_sub_element_dsn_dry_run/` | `--body`：`section_dsn_ids` = 从同一完整表单设计唯一定位、去重的字段组设计 ID 数组（可选）；`field_dsn_ids` = 从同一完整表单设计唯一定位、去重的字段设计 ID 数组（可选）；两个数组都为空时返回六个 `0`，且不产生删除目标 |
| 删除字段组、字段设计 | `POST` | `/api/project/settings/design/form/delete_form_sub_element_dsn/` | `--body`：`section_dsn_ids`、`field_dsn_ids` = 与最近一次成功删除演练完全相同的两个 ID 数组（可选，值和顺序均不得变化）；两个数组都为空时直接成功且不执行变更 |

字段的 `sdtm_domain_ids` 只能使用当前项目 SDTM 数据域候选中实际返回的 ID，平台会去重并按数据域目录顺序保存；只调换顺序不构成变更。关联关系按[数据字典与 SDTM 数据域使用说明](design-data-dictionary.md)读取和核对。

### 字段对象结构

字段创建和更新包含较多可选配置。先读取目标表单或字段组及现有字段，按用户明确要求提交最小字段集合；不要复制读取对象中的平台状态字段。

#### 核心字段

| 字段 | 创建必填 | 类型或引用 | 说明 |
| --- | --- | --- | --- |
| `name` | 是 | `string` | 字段名称，1–1024 字符。 |
| `vid` | 是 | `string` | 字段 VID，1–32 字符，匹配 `^[A-Z_][A-Z0-9_]*$`；不接受小写，后端不自动转换。 |
| `data_type` | 是 | `EdcDataType` | 例如 `STRING`、`INTEGER`、`FLOAT`、`DATE`、`TIME`、`DATETIME` 或 `BOOLEAN`；必须使用平台枚举。 |
| `resp_type` | 是 | `EdcRespType` | 例如 `INPUT`、`RADIO`、`CHECKBOX`、`SINGLE_SELECT` 或 `DATE_PICKER`；完整兼容矩阵见 [数据类型与响应类型组合](#数据类型与响应类型组合)，`UPLOAD` 当前没有可用的数据类型组合。 |
| `form_dsn_id` | 否 | `integer` | 创建字段时的目标表单设计 ID。 |
| `section_dsn_id` | 否 | `integer` | 创建字段时的目标字段组设计 ID；`form_dsn_id=0` 时必填。 |
| `id` | 更新必填 | `integer` | 更新接口的字段设计 ID。 |

#### 采集与校验配置

| 字段 | 类型或引用 | 说明 |
| --- | --- | --- |
| `question`、`prompt`、`description`、`definition` | `string` | 采集问题、提示与说明。 |
| `is_required`、`is_repeating`、`has_empty_info`、`is_blind` | `boolean` | 必填、重复、空值原因与盲态属性。 |
| `options` | `EdcOption[]` | 设计写入要求每项 `name`、`data_value` 均非空，即使提供 `null_flavor` 也不能省略或清空 `data_value`；完整约束见[字段组与字段配置限制](#字段组与字段配置限制)。 |
| `units` | `EdcUnit[]` | 每项必须含字符串 `label` 与数值 `ratio`（number，不加引号）；默认单位换算率为 `1`。 |
| `null_flavors` | `string[]` | 允许的空值原因列表。 |
| `range_checks` | `RangeCheckDsn[]` | 每项必须含 `condition` 和 `is_hard`，条件结构见 [条件对象结构](design-condition-schema.md)。 |
| `validation` | `EdcTextValidation` | 可含 `label`、`pattern` 与平台规则枚举 `rule`。 |
| `privacy_mask_type` | `EdcPrivacyMask` | 空、`MASK_ALL`、`MASK_NAME`、`MASK_ID_CARD_NUMBER`、`MASK_PHONE` 或 `MASK_EMAIL`。 |
| `min`、`max`、`min_constraint`、`max_constraint` | `string` | 数据约束，必须与 `data_type`、`resp_type` 一致。 |
| `decimal_precision` | `integer` | 0 至 6；0 表示不限。 |

`alteration`、`ranking`、受控标记、RTSM 关联、`is_invalid`、`invalid_messages` 等字段可能出现在读取对象，但不属于创建或更新请求时不得回传。盲态、隐私遮罩及上传字段遵循最小暴露，写后回读核验。

### 写接口返回内容

| 接口 | 业务返回内容 |
| --- | --- |
| 创建字段组设计 | 新创建的 `SectionDsn`；服务端将其追加到直接父级的混合下级序列末尾。响应成功后仍须按返回 `id` 回读确认。 |
| 变更字段组设计 | 无 |
| 排序字段组设计 | 无 |
| 创建字段设计 | 新创建的 `FieldDsn`；服务端将其追加到直接父级的混合下级序列末尾。响应成功后仍须按返回 `id` 回读确认。 |
| 变更字段设计 | 无 |
| 排序字段设计 | 无 |
| 删除字段组、字段设计演练 | 六个整数计数：`will_delete_section_count`、`will_delete_field_count`、`will_delete_range_check_count`、`will_delete_edit_check_count`、`will_delete_logic_count`、`will_delete_computation_count`。这些计数包含递归下级和关联设计，只表示影响预览，不是已删除结果；两个数组都为空时，演练返回六个 `0`。 |
| 删除字段组、字段设计 | 无；两个数组都为空时直接成功且不执行变更。 |

变更、排序和删除成功后仍必须回读同一个完整表单，不得仅凭写接口成功推断最终结构。删除演练只返回影响，不算正式变更。

### 层级与排序

- 创建对象时必须能解析到一个直接父级：直接位于表单下时提供 `form_dsn_id`；位于字段组下时提供 `parent_id` 或 `section_dsn_id`，此时 `form_dsn_id` 可以省略或提供该字段组所属表单的 ID。两个 ID 同时提供时必须匹配同一表单层级，不能互相矛盾。
- 创建接口没有 `ranking` 参数；新字段组或字段由服务端追加到直接父级的末尾。如需指定位置，创建并回读成功后再单独排序。
- 字段组与字段共享同一父节点下的排序序列。计算 `ranking` 时必须读取该父级的全部直接下级，不能只统计同类型对象。
- 排序只在对象现有的直接父级内移动，不能用于跨字段组或跨表单迁移。目标位置超过最大位置时会归一到末尾；提交当前实际位置会被视为没有变化。

### 字段组与字段配置限制

- 字段组 `vid` 在当前项目的未删除字段组中大小写不敏感唯一；字段 `vid` 在当前项目的未删除字段中大小写不敏感唯一。二者分别校验，不因名称不同而允许同类型 VID 冲突。
- 更新接口只提交实际要修改的属性，省略属性表示保持不变。`false`、`0`、空字符串、空数组和空对象在对应属性允许时都是明确的新值，例如用空数组清空选项；需要这些结果时必须显式提交，不能因为值为零值而错误省略。
- 字段的 `data_type`、`resp_type`、取值上下限、选项、单位、预设值、空值原因、小数精度、文本校验和范围检查必须作为一致配置核对。变更 `data_type` 或 `resp_type` 时，必须按兼容矩阵重新检查所有关联属性。
- `options`、`units`、`null_flavors` 和 `range_checks` 在更新请求中是完整新列表，不是增量补丁；提交前同时展示旧列表和完整新列表。
- 字段的预置文本校验规则先从规则目录读取。平台会以规则目录中的表达式归一化预置规则；自定义正则必须使用 `CUSTOM` 并提供已经确认的 `pattern`。
- `data_type` 与 `resp_type` 必须出现在兼容矩阵中；不兼容组合会直接报“数据类型与响应类型不匹配”。例如 `BOOLEAN` 只能搭配 `RADIO` 或 `SINGLE_SELECT`，`DATE_PICKER` 只能搭配 `DATE`，`TIME_PICKER` 只能搭配 `TIME`，`DATE_TIME_PICKER` 只能搭配 `DATETIME`。
- `RADIO`、`CHECKBOX`、`SINGLE_SELECT`、`MULTI_SELECT` 是选项类型，选项类型字段至少配置一个选项；非选项型 `resp_type` 不能保留任何 `options`。把选项型字段改成非选项型时，服务端会在更新流程中清空旧 `options`。
- 设计写入要求选项型字段的每项 `name`、`data_value` 均非空且各自不重复，`data_value` 必须符合字段 `data_type`。该校验不因提供 `null_flavor` 而豁免；空值选项也不能用空 `data_value` 通过设计写入。不能把空值原因伪造为普通数值；若现有选项配置不符合此约束，应明确说明写入限制，不自动改造其含义。
- `units` 只允许出现在 `INTEGER`、`FLOAT` 字段上；`DOUBLE` 当前也不能配置单位。`units[0]` 是默认单位，默认单位的 `ratio` 必须为 `1`；配置多个单位时默认单位的 `label` 不能为空。`units[1:]` 是可选单位，`ratio` 必须大于 `0`；所有非空 `label` 不能重复。
- `decimal_precision` 仅适用于 `FLOAT` 或 `DOUBLE` 与 `INPUT_NUMBER` 的组合；可选范围是 `0–6`，其中 `0` 表示不限，但运行态仍以 6 位小数为硬上限。字段变为其他组合时，服务端会把既有精度归零。
- `validation` 仅适用于 `STRING` 与 `INPUT` 或 `INPUT_VIEW` 的组合；只要配置了 `validation.rule`，归一化后的 `pattern` 就必须非空。字段变为其他组合时，服务端会清空既有 `validation`。
- `null_flavors` 是字段可接受的空值原因白名单。运行态实际录入时，只允许提交该字段已配置的空值码；未列入 `null_flavors` 的值不能作为字段空值。
- 严格必填校验要求 `is_required=true` 的字段具有数据值或空值原因；因此必填字段可以用已配置的非空 `null_flavor` 满足提交要求。`has_empty_info` 表示无值时是否填写说明原因，与 `null_flavors` 白名单是两个独立配置。
- `min_constraint`、`max_constraint` 与 `min`、`max` 需要成组理解：空约束表示不启用该侧边界；启用约束后，边界值字符串必须能够按当前 `data_type` 参与比较。`INCLUDE` / `EXCLUDE` 只会把越界结果标记为异常，`INCLUDE_HARD` / `EXCLUDE_HARD` 会在运行态直接拒绝越界数据。
- `pre_specified_value` 需要与当前字段配置兼容；若字段是选项型，预设值必须能落到现有 `options.data_value` 上；若字段带单位或数值约束，也必须与当前单位、类型和边界配置一致。
- 当前字段配置校验没有完整预检 `pre_specified_value`、`min`、`max` 与 `range_checks` 之间的全部关系；写接口未报错不代表这些组合一定可在数据录入时生效，提交前仍须按数据类型、响应类型和条件对象结构逐项核对。
- RTSM 关联字段不能变更 `data_type` 或 `resp_type`，也不能从 `is_repeating=false` 改为 `true`。RTSM 关联字段组不能变更重复配置。
- 字段组重复属性变化可能使引用该字段组的自动计算或逻辑核查失效。字段的数据类型、响应类型、选项、单位、重复属性、必填属性或范围检查变化也可能使自动计算、逻辑控制、逻辑核查或范围检查失效；写后必须检查相关对象的 `is_invalid` 和 `invalid_messages`。

### 删除和联动限制

- 删除演练和正式删除的字段组、字段必须属于同一当前项目、同一个完整表单；不存在、已删除、重复或无法唯一定位的 ID 不能作为目标。
- 删除字段组会递归包含它的全部下级字段组和字段。显式字段目标已包含在待删字段组下时，不要重复扩大请求；实际影响以演练返回的六类计数为准。
- 正式删除前必须先演练。若存在目标，至少一个直接对象计数会大于 `0`；向用户展示六类影响；仅当已有授权覆盖同一目标及这些实际影响时正式删除，否则先补充确认。两个请求数组都为空只会得到六个 `0`，表示没有删除目标，应停止而不是把空请求解释为已完成删除。用户只要求查询影响时，返回演练结果后停止。
- 正式删除必须使用与最近一次成功演练完全相同且顺序一致的两个数组；目标增删、替换、重排或依赖变化后都必须重新演练。
- RTSM 关联字段组或字段不能删除；递归范围内任一对象与 RTSM 关联时，整次删除都会被拒绝。
- 删除会重新排列剩余同级对象，并可能删除关联范围检查、使逻辑核查、逻辑控制和自动计算失效。已发布过方案时，既有设计通常标记为 `DELETED`，本轮新增对象可直接移除；从未发布过方案时可直接删除设计记录。

### 结果核验

新增、修改、排序或删除字段组与字段时，必须先 GET 获取变更前的完整表单设计，完成写操作后再次 GET 获取同一个完整表单，并用 Markdown 表格反馈实际 diff。删除演练只返回影响，不算正式变更。

单个对象的属性发生变化时，可以使用属性对比表：

| 对象 | 属性 | 变更前 | 变更后 | 结果 |
| --- | --- | --- | --- | --- |
| 字段 `VS_SYSBP` | `is_required` | `false` | `true` | 已生效 |
| 字段 `VS_SYSBP` | `units` | mmHg | mmHg、kPa | 已生效 |

当一次操作包含多个对象或多个结构变化时，必须使用批量变更表格。每行表示一个字段组或字段，第一列固定为变更类型，只能填写“新增”“变更”“删除”或“排序”；同时展示对象类型和完整父级路径，避免同名对象混淆。表格展示变更后的值，原值紧随其后并使用删除线标记。新增条目的原值留空，删除条目的变更后值留空并只保留删除线原值。

| 变更类型 | 对象类型 | 父级路径 | `vid` | 名称（`name`） | 排序（`ranking`） |
| --- | --- | --- | --- | --- | --- |
| 新增 | 字段组 | 生命体征表 | VITAL_SIGNS | 生命体征 | 2 |
| 变更 | 字段 | 生命体征表 / 生命体征 | VS_SYSBP | 收缩压（坐位）<br>~~收缩压~~ | |
| 排序 | 字段 | 生命体征表 / 生命体征 | VS_DIABP | 舒张压 | 2<br>~~3~~ |
| 删除 | 字段 | 生命体征表 / 生命体征 | ~~VS_TEMP~~ | ~~体温~~ | ~~4~~ |

如果用户要求展示全量结果，按 `subs` 树的实际层级和混合排序逐行展开；没有发生变化的属性留空，不要用“无变化”填充。表格中的值必须来自前后两次 GET 响应。如果 GET 失败、新对象未出现、删除对象仍存在、父级或排序与预期不一致，或相关依赖状态无法确认，应报告“变更未确认生效”，不得只依据写接口成功响应作出结论。

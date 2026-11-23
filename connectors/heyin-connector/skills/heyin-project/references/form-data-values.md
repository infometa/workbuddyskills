# 表单字段值与全量提交协议

本说明补充[事件与表单写入说明](patient-form-write.md)中的 `sync_form_data` 和 `commit_form_data`。先用当前参与者的 `get_form_data` 读取完整 `def` 与 `data`；尚无实例时读取匹配的 `get_form_def`。以下示例 ID 和值仅演示已说明的完整虚构表单，不能直接用于真实项目，也不能拿示例覆盖一个更大的表单。

## 字段值编码

每个字段先核对定义的 `data_type`、`resp_type`、`options`、`decimal_precision`、`units`、`null_flavors`、计算及 RTSM 关联。API 的 `data_value` 始终是字符串，JSON 数值、布尔值和数组不能直接替代它。选项名称只用于匹配，最终传定义中的 `options[].data_value`。

| 字段类型 | `data_value` 编码 | 校验与示例 |
| --- | --- | --- |
| 普通文字 | 原始字符串 | 保留用户确认的文字，并满足字段长度、文本校验等定义；不把展示标签拼入值。 |
| 整数 | 整数的十进制字符串 | 例如 `"12"`；不能传 JSON 数值 `12`。 |
| `INPUT_NUMBER` 小数/双精度 | 普通十进制字符串 | 例如 `"12.50"`；禁止科学计数法、`NaN`、`Inf` 和尾随小数点。`decimal_precision>0` 时小数位不得超过该值，否则最多 6 位；超限报错，不会自动截断。配置了正精度时平台无损补零，例如精度 2 的 `"12.5"` 回读为 `"12.50"`。 |
| 布尔数据 | 布尔的字符串形式 | 使用 `"true"` 或 `"false"`；有单选配置时仍须匹配实际选项值，不能把显示的“是/否”自行转换。 |
| `RADIO` / `SINGLE_SELECT` | 单个选项的 `data_value` 字符串 | 例如选项值为 `"A"` 时提交 `"A"`，不提交其显示名称或数组。 |
| `CHECKBOX` / `MULTI_SELECT` | 选项值字符串数组的 JSON 字符串 | 选择 `A`、`B` 时请求字段是 `"data_value":"[\"A\",\"B\"]"`；每项必须存在于定义且不得重复；清空用 `"[]"`。 |
| `DATE_TIME_PICKER` / 日期时间 | 带时区的 RFC3339 字符串 | 如 `"2026-09-18T09:30:00+08:00"`；时区须来自已确认上下文，不能套用事件日期的 `YYYY-MM-DD HH:mm`。 |
| `DATE_PICKER` / 日期 | `YYYY-MM-DD` | 未知月/日使用定义允许的未知日期语义，如 `"2026-09-UNK"`、`"2026-UNK-UNK"`；月份未知时日也必须未知。未知不能补成 01，也不能将来源中没说明的部分主动改为 `UNK`。 |
| `TIME_PICKER` / 时间 | `HH:mm:ss` | 如 `"09:30:00"`；不使用只有小时分钟的事件时间格式。 |
| 其他响应类型 | 当前定义对应的数据类型 | 不套用选项或文件上传编码；没有明确契约时先补充依据，不把任意对象转成字符串提交。 |

`unit_label` 和 `null_flavor` 同样为字符串。字段配置了 `units` 时，`unit_label` 必须是其中一个实际 `label`，即使清空值也不能省成空串；没有配置单位时必须为空。值与单位是配对事实，不能只改单位标签而假定平台替你换算原始输入。

无缺失原因时用 `null_flavor=""`。需要缺失原因时只能使用该字段 `null_flavors` 中的实际值；普通字段的 `data_value` 同时置空，多选字段置 `"[]"`。非空有效值与非空 `null_flavor` 不能并存。未采集、确实为空及合法零值分别处理，不能互相替换。

数字超精度或来源单位不一致时，先核对来源和用户期望，不自行截断、四舍五入或改单位制造可写值。平台对 OCR 或自动计算另有处理规则，不代表人工接口也会自动修正输入。

## 增量保存与旧值

`sync_form_data` 只接受未提交表单。以 `form_data_id` 固定目标，按字段及所属重复行提供 `field_def_id` 和必要的 `section_data_id`；每项提交完整的新三元组 `data_value/null_flavor/unit_label`，旧三元组 `old_data_value/old_null_flavor/old_unit_label` 从刚读取的数据复制。它们不是可任意省略的“无需更新字段”：新值中的省略按空字符串处理，旧值中的省略会影响冲突判断。

```json
{
  "form_data_id": 5001,
  "is_force": false,
  "fields": [
    {
      "field_def_id": 101,
      "data_value": "12.50",
      "unit_label": "kg",
      "null_flavor": "",
      "old_data_value": "12.00",
      "old_unit_label": "kg",
      "old_null_flavor": ""
    }
  ]
}
```

示例仅在该字段实际配置了 `kg` 且旧值确为 `12.00 kg` 时成立。字段位于重复祖先链下时须增加本次读取的 `section_data_id`。自动计算字段交给平台；RTSM 结果字段不能通过增量保存改变。冲突处理及强制覆盖授权见[写入说明](patient-form-write.md)。

## 全量 subs 节点

`commit_form_data` 请求的外层 `subs` 是 **JSON 数组编码后的字符串**；解码后的数组及每个字段组内部的 `subs` 是普通数组。内层不要再次转成字符串，也不能为 `null`。

| 节点 | 写入结构 | ID 与父子规则 |
| --- | --- | --- |
| 字段 | `item_type:"field"`、`field_def_id`、字符串 `data_value`、`null_flavor`、`unit_label`，可选 `message` | 字段必须是所在层级的直接子定义；同层同一定义不得重复。现有字段按父行及定义定位，`field_data_id` 不是此节点的寻址参数。 |
| 字段组 | `item_type:"section"`、`section_def_id`、`subs:[...]`；保留现有行时传其 `id` | 必须是所在层级的直接子定义。`id` 是字段组数据 ID，须同时匹配定义和当前父行；不能跨父行挪用。 |

重复字段组的每一行分别占一个 section 节点，行顺序就是提交后的排序。保留现有行必须保留其 `id`；新建行省略 `id`，下级新行也不能借用旧行 ID。非重复组最多一行，省略 `id` 时会复用当前父实例下的现有行。每个父实例下的重复行数都要满足定义的 `repeating_limit`；不要借助省略行规避上限。

构造最终快照时深复制完整读取结果，逐一对齐定义，只修改授权字段；保留其余值、单位、空值、每条现有重复行及嵌套结构。新增节点只来自当前定义。保留已有 `sd_file_data_mappings` 与 AI 元信息的写前快照用于核验，不编造映射或置信度。人工 `commit_form_data` 会主动清除字段 AI 录入标记和置信度，回传旧值也无法阻止；人工增量保存同样会对实际写入字段清除该标记。此项影响需纳入用户授权。

这个项目端提交接口不会根据节点中的 `sd_file_data_mappings` 新建映射；现有字段/行保留时原映射继续存在，删除行会级联删除映射。新增映射使用[SD 映射接口](patient-sd.md)。不能声称把读取对象原样写回就保留了全部审阅标记、签名或 AI 状态，写后须核对实际结果。

已提交表单仍显式传 `is_committed:true`。定义 `has_change_info=true` 时，实际修改或新增有内容的字段需提供字段级 `message`，也可用外层表单级 `message` 作为共同原因；删除已有重复行需要外层原因。外层 `message` 最长 120 字符，建议字段原因也控制在该长度，理由只取已确认内容。首次提交的变更说明可选。

## 提交示例

### 平铺表单：完整请求体

假设表单仅有数值字段 101 和多选字段 102，数值字段单位为 `kg`，完整现状无其他字段或字段组。下面请求保存这两项并正式提交；真正请求须使用真实 ID、完整现状及已确认目标。

```json
{
  "form_data_id": 5001,
  "is_committed": true,
  "subs": "[{\"item_type\":\"field\",\"field_def_id\":101,\"data_value\":\"12.50\",\"unit_label\":\"kg\",\"null_flavor\":\"\"},{\"item_type\":\"field\",\"field_def_id\":102,\"data_value\":\"[\\\"A\\\",\\\"B\\\"]\",\"unit_label\":\"\",\"null_flavor\":\"\"}]"
}
```

### 嵌套与重复组：编码前的完整数组

假设另一表单仅有非重复组 201，其现有行 ID 为 6001；组内有字段 103 和重复子组 202，子组每行仅有字段 104。下面保留原有行 6101、6102 的所有值，并在用户已要求新增一行时加入第三行。第三行省略 `id`；已有行的 `id` 和未修改字段值全部保留。

```json
[
  {
    "item_type": "section",
    "section_def_id": 201,
    "id": 6001,
    "subs": [
      {"item_type":"field","field_def_id":103,"data_value":"2026-09-18","unit_label":"","null_flavor":""},
      {
        "item_type":"section","section_def_id":202,"id":6101,
        "subs":[{"item_type":"field","field_def_id":104,"data_value":"A","unit_label":"","null_flavor":""}]
      },
      {
        "item_type":"section","section_def_id":202,"id":6102,
        "subs":[{"item_type":"field","field_def_id":104,"data_value":"B","unit_label":"","null_flavor":""}]
      },
      {
        "item_type":"section","section_def_id":202,
        "subs":[{"item_type":"field","field_def_id":104,"data_value":"C","unit_label":"","null_flavor":""}]
      }
    ]
  }
]
```

将这个完整数组作为内存变量 `subs`，再用标准 JSON 序列化生成外层请求，例如 Python 的 `json.dumps({"form_data_id": actual_form_data_id, "is_committed": True, "subs": json.dumps(subs, ensure_ascii=False)}, ensure_ascii=False)`。需要原因时在相应节点或外层加入已确认的 `message`。把生成的 JSON 对象字符串交给 `heyincli req --body`，不要自行拼反斜杠或把 `subs` 直接作为外层数组传入。

已有重复表单必须指定其 `form_data_id`。只传 `event_data_id + form_def_id` 在重复表单下可能新建一份，不能用它代替编辑现有实例。新建整份表单时不要携带旧表单的任何字段组数据 ID。

## 防止误清空与结果核验

提交前对比写前与最终快照：每个未获准删除的现有重复行都应保留，同一父行内所有未获准修改的字段仍保持原值、单位与空值；新增、删除与排序变化单独列出。完整定义或数据没有取全、父子关系无法对齐、只拿到局部导入列时不提交整表。读取时被业务权限遮罩的值不能当作真实原值重放。

提交后按同一 `form_data_id` 回读，核对完整字段及重复行集合、序号、提交状态、单位归一化结果和已知副作用；新行的 ID 以回读结果为准。平台可能执行计算、隐藏/显示、核查和 ePRO 代填同步，相关结果见[写入说明](patient-form-write.md)。响应不含新表单 ID 时须从同一事件完整列表差集唯一定位，不能取最新一条猜测。结果未知时先查实际状态，不重放整表或另建重复实例。

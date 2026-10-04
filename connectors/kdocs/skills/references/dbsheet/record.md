# 记录操作

## 1. dbsheet.create_records

#### 功能说明

在指定数据表中批量创建记录。每条记录通过 `fields` 字段传入一个**序列化的 JSON 字符串**，
字符串内部为字段名（或字段 ID）到值的映射。

#### 工具选择

- **适用**：向已有数据表批量新增记录，且 fields 的 key 已对照 get_schema 的现有列名
- **适用**：全空记录复用后仍有剩余条数须追加到表尾
- **适用**：用户明确要求在表尾/末尾追加记录
- **勿用**（改用 `dbsheet.get_schema`）：尚未 get_schema
- **勿用**：get_schema 后仍有字段无法映射到现有列（含尚未确认是否新建列） — 先读 references/dbsheet.md「写入前字段映射」；未确认禁止 create_fields
- **勿用**（改用 `dbsheet.update_records`）：尚未 list_records 盘点可复用全空记录，且用户意图为新增记录（非明确追加到表尾） — create_records 仅追加到表尾；须先按 references/dbsheet.md「新增记录与全空记录复用」复用全空记录

#### 调用约束

- **前置检查**：须先 get_schema 并阅读 param_detail 字段值规范；fields 的 key 须全部存在于 schema
- **前置检查**：新增记录前须 list_records 并按 references/dbsheet.md「新增记录与全空记录复用」优先 update_records 复用全空记录；禁止 delete_records 清理全空记录
- **后置验证**：必须 list_records 或 get_record 回读验证；禁止仅凭 result ok 宣称成功

**幂等性**：否 — 重复调用会插入重复记录，先确认是否已成功

> `records[].fields` 是对象（key-value 映射），不是序列化 JSON 字符串
> 关联字段（Link）值格式为关联记录 id 的字符串数组，如 `["id1", "id2"]`
> `prefer_id=true` 时，`fields` 内部的 key 应为字段 ID（由 get_schema 返回），而非字段名
> `add_select_item=true` 时，可通过 `field_values` 提前声明要新增的选项；若不声明，选项名称直接写入 `fields` 中也会触发新增
> `text_value` 和 `link_value` 仅影响响应返回格式，不影响写入行为
> Url 字段传入为对象 `{address, displayText}`，响应中以数组形式返回
> Rating 字段的上限由 `max`/`max_value` 定义，可通过 get_schema 查询

#### 调用示例

按字段名批量创建记录：

```json
{
  "file_id": "VsdfG0001234567",
  "sheet_id": 3,
  "prefer_id": false,
  "records": [
    {
      "fields": {
        "文本": "第一行文本",
        "日期": "2024/12/20"
      }
    },
    {
      "fields": {
        "文本": "第二行文本",
        "日期": "2024/12/21"
      }
    }
  ]
}
```

创建记录时同步新增选项：

```json
{
  "file_id": "VsdfG0001234567",
  "sheet_id": 3,
  "add_select_item": true,
  "records": [
    {
      "fields": {
        "名称": "Hello",
        "数量": 123,
        "记录关联": [
          "I",
          "G"
        ]
      }
    },
    {
      "fields": {
        "数量": 666
      }
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `records` (array[object], 必填): 要创建的记录列表，每个元素含 `fields` 对象（字段名/ID → 值的映射）
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key；默认 false（使用字段名），为 `true` 时 `fields` 内部的 key 应为字段 ID
- `value_prefer_id` (boolean, 可选): 是否使用选项 ID 作为 选项值，默认为 false
- `omit_failure` (boolean, 可选): 单条记录创建失败是否不中断整批请求，默认为 false
- `text_value` (string, 可选): 响应返回值格式：`original` 返回原始值（默认）、`text` 返回文本值、`compound` 同时返回原始值和文本值
- `link_value` (string, 可选): 关联字段响应格式：`id` 仅返回关联记录 id（默认）；`all` 返回 id 和文本
- `add_select_item` (boolean, 可选): 是否自动新增不存在的选项，默认 true

**请求体根级参数**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sheet_id` | integer | 是 | 数据表 ID |
| `records` | array[object] | 是 | 待创建记录列表，每项含 `fields` 对象 |
| `prefer_id` | boolean | 否 | 默认 `false`。`true` 时 `fields` 的 key 为字段 ID |
| `value_prefer_id` | boolean | 否 | 默认 `false`。`true` 时用选项 ID 标识选项值 |
| `omit_failure` | boolean | 否 | 默认 `false`。`true` 时单条失败不中断整批 |
| `textValue` | string | 否 | 响应值格式：`original`（默认）/ `text` / `compound` |
| `link_value` | string | 否 | 关联字段响应格式：`id`（默认）/ `all` |
| `add_select_item` | boolean | 否 | 是否自动新增不存在的选项，默认 true |

**`records[].fields` 元素结构**

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `fields` | object | 是 | 字段名（或字段 ID）→ 值的映射对象 |

**`field_values[].listItems` 元素结构**

| 属性 | 类型 | 说明 |
|------|------|------|
| `field_id` | string | 要新增选项的字段 ID |
| `listItems` | array[object] | 待新增选项，每项含 `value`（string）和 `color`（string，如 `"0xF0EEF7"`） |

**`fields` 对象各字段类型填写规范**

| 字段类型 | 值类型 | 示例值 | 备注 |
|---------|--------|--------|------|
| 多行文本（MultiLineText） | string | `"任务描述"` | — |
| 日期（Date） | string | `"2025/11/15"` | 须符合字段 `number_format` 格式 |
| 时间（Time） | string | `"11:12:15"` | 须符合字段时间格式 |
| 数值 / 货币 / 百分比（Number / Currency / Percentage） | int \| float | `125` / `215` / `85` | — |
| 身份证 / 电话 / 电子邮箱（ID / Phone / Email） | string | `"18800000000"` | — |
| 超链接（Url） | object \| string | `{"address":"https://…","displayText":"百度"}` 或直接传 `string` | 分别设置地址和文本时传对象，同时设置时传字符串 |
| 复选框（Checkbox） | boolean | `true` | — |
| 单选项（SingleSelect） | string | `"选项1"` | 已有选项的 `value`；`bAddSelectItem=true` 时可传新选项 |
| 多选项（MultipleSelect） | string[] | `["选项1","选项2"]` | 已有选项 `value` 的字符串数组 |
| 等级（Rating） | int | `3` | 不超过字段 `max` /`max_value` 上限 |
| 进度条（Complete） | float | `0.5` | 进度值 0.0–1.0 |
| 联系人（Contact） | object[] | `[{"id":"uid","nickname":"张三","avatar_url":"https://…"}]` | `id` 为用户 uid |
| 附件（Attachment） | object[] | `[{"uploadId":"…","fileName":"a.png","size":1024,"source":"upload_ks3","type":"image/png"}]` | `source` 取 `upload_ks3` 或 `Cloud`（须 `linkUrl`）；本地上传勿标 `Cloud`；格式见 `dbsheet.create_fields` Attachment 节 |
| 关联（Link） | string[] | `["record_id_1","record_id_2"]` | 关联记录 id 数组 |
| 富文本（Note） | object | `{"fileId":"…","summary":"摘要","modifyDate":"2024/12/09 12:00:00"}` | — |
| 地址（Address） | object | `{"districts":["广东省","珠海市","香洲区"],"detail":"详细地址"}` | `districts` 层级与字段 `addressLevel` 一致 |
| 级联（Cascade） | object | `{"districts":["一级选项","二级选项"]}` | 各级选中值数组 |
| 公式 / 编号 / 创建时间 / 创建者 / 最后修改者 / 引用 | — | **不可填写** | 自动字段，传入会被忽略或报错 |

字段类型定义及 `data` 配置可参考 `dbsheet.create_fields`（`param_detail` 各类型节）。

**请求体示例**

```json
{
  "sheet_id": 3,
  "prefer_id": false,
  "add_select_item": true,
  "records": [
    {
      "fields": {
        "名称": "Hello",
        "数量": 123,
        "记录关联": ["I", "G"]
      }
    },
    {
      "fields": { "数量": 666 }
    }
  ]
}
```

`fields` 反序列化后内容（各字段类型对应值）：

| 字段名 | 字段类型 | 值示例 |
|--------|----------|--------|
| `多行文本` | MultiLineText | `"yesit'sright"` |
| `日期` | Date | `"2025/11/15"` |
| `时间` | Time | `"11:12:15"` |
| `数值` | Number | `125` |
| `货币` | Currency | `215` |
| `百分比` | Percentage | `85` |
| `身份证` | ID | `"110101**************9"` |
| `电话` | Phone | `"18800000000"` |
| `电子邮箱` | Email | `"user@example.com"` |
| `超链接` | Url | `{"address":"https://www.baidu.com","displayText":"百度"}` |
| `复选框` | Checkbox | `true` / `false` |
| `单选项` | SingleSelect | 已有选项的 `value` 字符串 |
| `多选项` | MultipleSelect | 已有选项 `value` 的字符串数组 |
| `等级` | Rating | 不超过字段 `max` /`max_value` 的整数 |
| `进度条` | Complete | `0.5` | 进度值 0.0–1.0 |
| `联系人` | Contact | `[{"id":"uid","nickname":"昵称","avatar_url":"…"}]` |
| `附件` | Attachment | `[{"uploadId":"…","fileName":"…","size":0,"source":"upload_ks3","type":"image/png"}]` |
| `关联` | Link | `["record_id_1","record_id_2"]` |
| `富文本` | Note | `{"fileId":"…","summary":"摘要","modifyDate":"2025/12/31 12:00:00"}` |
| `地址` | Address | `{"districts":["广东省","珠海市","香洲区"],"detail":"…"}` |
| `级联` | Cascade | `{"districts":["一级选项","二级选项"]}` |

> `Formula`、`AutoNumber`、`CreatedTime`、`CreatedBy`、`LastModifiedBy`、`Lookup` 为系统自动字段，**无需传入**。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "records": [
      {
        "fields": "{\"日期\":\"2025/11/15\",\"数字\":125,\"公式\":340,\"创建人\":{\"id\":\"280026893\",\"nickName\":\"霧雨澪音\"},\"创建时间\":\"2024/12/09 17:47:18\",\"最后修改者\":{\"id\":\"280026893\",\"nickName\":\"霧雨澪音\"},\"最后修改时间\":\"2024/12/09 17:47:18\",\"编号\":2}",
        "id": "V"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data.records[].id` | string | 新建记录 ID |
| `data.records[].fields` | string | 序列化 JSON 字符串，包含创建后所有字段的实际值（含系统自动字段） |


---

## 2. dbsheet.update_records

#### 功能说明

⚠️ **`file_id`、`sheet_id`、`records` 三个顶层参数全部必填。**
各字段类型（Date、Phone、Contact 等）的值格式要求参见 `dbsheet.create_fields` 的字段类型说明，格式错误会导致 `Failed due to field`。

批量更新数据表中已有记录的字段值。每条记录必须提供 `id`（记录 ID）和 `fields`
（对象结构，内容为字段名或字段 ID 到新值的映射）。

#### 调用约束

- **前置检查**：须 get_schema 确认 sheet_id 与字段结构，且 fields 的 key 已映射到现有列；规则见 references/dbsheet.md「写入前字段映射」
- **前置检查**：调用 list_records 确认目标记录 ID 存在；向表新增记录时按 references/dbsheet.md「新增记录与全空记录复用」仅更新全空记录（合法改已有行不在此限）
- **后置验证**：必须 get_record 或 list_records 回读验证；禁止仅凭 result ok 宣称成功

**幂等性**：是

> `records[].fields` 是对象（key-value 映射），不是序列化 JSON 字符串；仅传入需要修改的字段，未传字段保持原值不变
> 关联字段（Link）值格式为关联记录 id 的字符串数组，如 `["id1", "id2"]`
> `prefer_id=true` 时，`fields` 内部的 key 应为字段 ID（由 get_schema 返回），而非字段名
> `add_select_item=true` 时，可通过 `fieldValues` 预声明要新增的选项
> `text_value` 和 `link_value` 仅影响响应返回格式，不影响写入行为
> Url 字段传入为对象 `{address, displayText}`，响应中以数组形式返回
> Rating 字段的上限由 `max`/`max_value` 定义，创建字段时通过 `dbsheet.create_fields` 设置

#### 调用示例

按字段名批量更新记录：

```json
{
  "file_id": "VsdfG0001234567",
  "sheet_id": 3,
  "prefer_id": false,
  "records": [
    {
      "id": "G",
      "fields": {
        "文本": "新的文本",
        "日期": "2024/12/21"
      }
    },
    {
      "id": "H",
      "fields": {
        "文本": "另一行文本",
        "状态": "已完成"
      }
    }
  ]
}
```

更新记录时同步新增选项：

```json
{
  "file_id": "VsdfG0001234567",
  "sheet_id": 3,
  "add_select_item": true,
  "records": [
    {
      "id": "B",
      "fields": {
        "名称": "Hello",
        "数量": 123
      }
    },
    {
      "id": "C",
      "fields": {
        "数量": 666
      }
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `records` (array[object], 必填): 要更新的记录列表，每个元素包含 `id`（记录 ID）和 `fields`（序列化 JSON 字符串）
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key；默认 false（使用字段名），为 `true` 时 `fields` 内部的 key 应为字段 ID
- `value_prefer_id` (boolean, 可选): 是否使用选项 ID 作为 选项值，默认为 false
- `omit_failure` (boolean, 可选): 单条记录创建失败是否不中断整批请求，默认为 false
- `text_value` (string, 可选): 响应返回值格式：`original` 返回原始值（默认）、`text` 返回文本值、`compound` 同时返回原始值和文本值
- `link_value` (string, 可选): 关联字段响应格式：`id` 仅返回关联记录 id（默认）；`all` 返回 id 和文本
- `add_select_item` (boolean, 可选): 是否自动新增不存在的选项，默认 true

**请求体根级参数**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sheet_id` | integer | 是 | 数据表 ID |
| `records` | array[object] | 是 | 待更新记录列表，每项含 `id` 和 `fields` 对象 |
| `prefer_id` | boolean | 否 | 默认 `false`。`true` 时 `fields` 的 key 为字段 ID |
| `value_prefer_id` | boolean | 否 | 默认 `false`。`true` 时用选项 ID 标识选项值 |
| `omit_failure` | boolean | 否 | 默认 `false`。`true` 时单条失败不中断整批 |
| `text_value` | string | 否 | 响应值格式：`original`（默认）/ `text` / `compound` |
| `link_value` | string | 否 | 关联字段响应格式：`id`（默认）/ `all` |
| `add_select_item` | boolean | 否 | 是否自动新增不存在的选项，默认 true |

**`records[]` 元素结构**

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | **是** | 目标记录 ID（通过 list_records / get_record 获取） |
| `fields` | object | 是 | 字段名（或字段 ID）→ 新值的映射对象；仅传需要修改的字段 |

**`fields` 对象各字段类型填写规范**

| 字段类型 | 值类型 | 示例值 | 备注 |
|---------|--------|--------|------|
| 多行文本（MultiLineText） | string | `"新文本"` | — |
| 日期（Date） | string | `"2025/11/15"` | 须符合字段 `number_format` 格式 |
| 时间（Time） | string | `"11:12:15"` | 须符合字段时间格式 |
| 数值 / 货币 / 百分比（Number / Currency / Percentage） | int \| float | `125` / `215` / `85` | — |
| 身份证 / 电话 / 电子邮箱（ID / Phone / Email） | string | `"18800000000"` | — |
| 超链接（Url） | object \| string | `{"address":"https://…","displayText":"百度"}` 或直接传 `string` | 分别设置地址和文本时传对象，同时设置时传字符串 |
| 复选框（Checkbox） | boolean | `false` | — |
| 单选项（SingleSelect） | string | `"选项1"` | 已有选项的 `value`；`bAddSelectItem=true` 时可传新选项 |
| 多选项（MultipleSelect） | string[] | `["选项1","选项2"]` | 已有选项 `value` 的字符串数组 |
| 等级（Rating） | int | `3` | 不超过字段 `max` /`max_value` 上限 |
| 进度条（Complete） | float | `0.5` | 进度值 0.0–1.0 |
| 联系人（Contact） | object[] | `[{"id":"uid","nickname":"张三","avatar_url":"https://…"}]` | `id` 为用户 uid |
| 附件（Attachment） | object[] | `[{"uploadId":"…","fileName":"a.png","size":1024,"source":"upload_ks3","type":"image/png"}]` | `source` 取 `upload_ks3` 或 `Cloud`（须 `linkUrl`）；本地上传勿标 `Cloud`；格式见 `dbsheet.create_fields` Attachment 节 |
| 关联（Link） | string[] | `["I","G"]` | 关联记录 id 数组 |
| 富文本（Note） | object | `{"fileId":"…","summary":"摘要","modifyDate":"2024/12/09 12:00:00"}` | 仅可更新 summary 等元数据；**正文内容须用 `get_schema_detail` 获取 content_id 后通过 `innerdoc_block_*` 工具链读写，不可通过 update_records 写入正文内容** |
| 地址（Address） | object | `{"districts":["广东省","珠海市","香洲区"],"detail":"详细地址"}` | `districts` 层级与字段 `addressLevel` 一致 |
| 级联（Cascade） | object | `{"districts":["一级选项","二级选项"]}` | 各级选中值数组 |
| 公式 / 编号 / 创建时间 / 创建者 / 最后修改者 / 引用 | — | **不可填写** | 自动字段，传入会被忽略或报错 |

字段类型定义及值格式完整说明可参考 `dbsheet.create_fields`（`param_detail` 各类型节）。

**请求体示例**

```json
{
  "sheet_id": 3,
  "prefer_id": false,
  "add_select_item": true,
  "records": [
    {
      "id": "B",
      "fields": { "名称": "Hello", "数量": 123 }
    },
    {
      "id": "C",
      "fields": { "数量": 666 }
    }
  ]
}
```

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "records": [
      {
        "id": "B",
        "fields": {
          "名称": "Hello",
          "数量": 123,
          "最后修改者": { "id": "280026893", "nickName": "霧雨澪音" },
          "最后修改时间": "2024/12/09 17:47:18"
        }
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `msg` | string | 响应信息 |
| `data.records[].id` | string | 已更新记录 ID |
| `data.records[].fields` | object | 更新后所有字段的实际值（含系统自动字段） |


---

## 3. dbsheet.list_records

#### 功能说明

分页遍历数据表中的记录，支持按视图过滤、指定返回字段，以及通过 `filter` 参数实现复杂查询条件（支持 criteria 单层筛选和 filters 递归嵌套条件组）。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。

**幂等性**：是

#### 调用示例

基础分页查询：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "page_size": 100,
  "offset": "",
  "fields": [
    "名称",
    "状态",
    "截止日期"
  ]
}
```

带筛选条件查询：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "page_size": 100,
  "offset": "",
  "filter": {
    "mode": "AND",
    "criteria": [
      {
        "field": "状态",
        "op": "Intersected",
        "values": [
          "进行中"
        ]
      },
      {
        "field": "数量",
        "op": "Greater",
        "values": [
          "10"
        ]
      },
      {
        "field": "名称",
        "op": "Contains",
        "values": [
          "关键词"
        ]
      }
    ]
  }
}
```

嵌套条件组查询：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "page_size": 100,
  "offset": "",
  "filter": {
    "mode": "OR",
    "filters": [
      {
        "mode": "AND",
        "criteria": [
          {
            "field": "名称",
            "op": "Equals",
            "values": [
              "a"
            ]
          },
          {
            "field": "数量",
            "op": "Equals",
            "values": [
              "1"
            ]
          }
        ]
      },
      {
        "mode": "AND",
        "criteria": [
          {
            "field": "名称",
            "op": "Equals",
            "values": [
              "b"
            ]
          },
          {
            "field": "数量",
            "op": "Equals",
            "values": [
              "2"
            ]
          }
        ]
      }
    ]
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `page_size` (integer, 可选): 每页记录数，默认 100，取值范围 1-1000
- `offset` (string, 可选): 翻页游标，首次请求传空字符串，后续传响应中的 `offset` 值
- `view_id` (string, 可选): 按指定视图返回记录
- `max_records` (integer, 可选): 最多返回的记录总数，上限 100
- `fields` (array, 可选): 只返回指定字段列表；字段名或字段 ID 取决于 `prefer_id`，不填则返回所有字段
- `filter` (object, 可选): 筛选条件，支持 criteria 单层条件和 filters 递归嵌套条件组
  - `mode` (string, 选填): 条件连接方式，`"AND"` 或 `"OR"`，缺省 `"AND"`
  - `criteria` (array): 筛选条件列表，同一字段不可定义多个条件
    - `field` (string, 必填): 字段名称或 ID（取决于 `prefer_id`）
    - `op` (string, 必填): 筛选操作符（见 `param_detail` 筛选规则表）
    - `values` (array, 必填): 筛选值，`Empty`/`NotEmpty` 时可省略；支持字符串或日期动态结构体
  - `filters` (array): 递归条件组，每个元素是一个 filter 对象，可实现 AND/OR 嵌套
- `prefer_id` (boolean, 可选): 是否使用字段 ID 和选项 ID 标识，为 true 时参数内全部 field/fields 均按 ID 解析
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）/ `"text"`（文本值）/ `"compound"`（原始值和文本值）
- `link_value` (string, 可选): 关联字段值格式：`"id"`（仅返回 ID）/ `"all"`（返回 ID 和文本）
- `show_record_extra_info` (boolean, 可选): 为 true 时额外返回创建者、创建时间、最后修改者、最后修改时间
- `show_fields_info` (boolean, 可选): 为 true 时额外返回 fields 结构体，展示字段定义信息（类似 get_schema 中的 fields）

> **分页说明**：响应中的 `offset` 指向下一页第一条记录，下次请求将该值传入 `offset` 即可翻页。最后一页不再返回 `offset`。

**筛选操作符**（大小写不敏感）：

| 操作符 | 含义 | values 上限 |
|--------|------|------------|
| Equals | 等于 | 1 |
| NotEqu | 不等于 | 1 |
| Greater | 大于 | 1 |
| GreaterEqu | 大等于 | 1 |
| Less | 小于 | 1 |
| LessEqu | 小等于 | 1 |
| GreaterEquAndLessEqu | 介于（取等） | 2 |
| LessOrGreater | 介于（不取等） | 2 |
| BeginWith | 开头是 | 1 |
| EndWith | 结尾是 | 1 |
| Contains | 包含 | 1 |
| NotContains | 不包含 | 1 |
| Intersected | 指定值 | 65535 |
| Empty | 为空 | 0 |
| NotEmpty | 不为空 | 0 |

**日期动态筛选**：values 元素可为结构体 `{ "type": "DynamicSimple", "dynamicType": "..." }`，`dynamicType` 可选值（大小写不敏感）：

| dynamicType | 含义 |
|-------------|------|
| today | 今天 |
| yesterday | 昨天 |
| tomorrow | 明天 |
| last7Days | 最近 7 天 |
| last30Days | 最近 30 天 |
| last7DaysContainToday | 最近 7 天（含今天） |
| last30DaysContainToday | 最近 30 天（含今天） |
| thisWeek | 本周 |
| lastWeek | 上周 |
| nextWeek | 下周 |
| thisMonth | 本月 |
| lastMonth | 上月 |
| nextMonth | 次月 |

> op 为 greater/less 时，dynamicType 只能是 yesterday / today / tomorrow。

**筛选注意事项**：filter 非结构体、criterion 未指定 field、op/values 不合法、values 元素超限等情形，整个请求将直接失败。

#### 返回值说明

```json
{
  "detail": {
    "offset": "D",
    "records": [
      { "id": "E", "fields": { "名称": "任务A", "状态": "进行中", "数量": 15 } },
      { "id": "F", "fields": { "名称": "任务B", "状态": "进行中", "数量": 20 } }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.offset` | string | 下一页游标，无更多数据时不返回此字段 |
| `detail.records[].id` | string | 记录 ID |
| `detail.records[].fields` | object | 各字段的值 |
| `result` | string | ok 表示成功 |


---

## 4. dbsheet.get_record

#### 功能说明

获取数据表中某条指定记录的完整字段内容。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。

**幂等性**：是

#### 调用示例

获取单条记录：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "record_id": "B"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `record_id` (string, 必填): 记录 ID
- `prefer_id` (boolean, 可选): 是否使用字段 ID 和选项 ID 标识
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）/ `"text"`（文本值）/ `"compound"`（原始值和文本值）
- `link_value` (string, 可选): 关联字段值格式：`"id"`（仅返回 ID）/ `"all"`（返回 ID 和文本）
- `show_record_extra_info` (boolean, 可选): 为 true 时额外返回创建者、创建时间、最后修改者、最后修改时间
- `show_fields_info` (boolean, 可选): 为 true 时额外返回 fields 结构体，展示字段定义信息（类似 get_schema 中的 fields）

#### 返回值说明

```json
{
  "detail": {
    "id": "B",
    "fields": {
      "名称": "任务A",
      "数量": 123,
      "日期": "2021/5/1",
      "状态": "未开始"
    }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.id` | string | 记录 ID |
| `detail.fields` | object | 各字段的值 |
| `result` | string | ok 表示成功 |


---

## 5. dbsheet.delete_records

#### 功能说明

批量删除数据表中的指定记录。`records` 为记录 ID 的对象数组，**不是字符串数组**。
file_id和sheet_id为必填参数，不允许为空。

#### 调用约束

- **前置检查**：调用 list_records 或 get_record 核对拟删记录的内容，确认记录 ID 正确；使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。
- **用户确认**：批量删除记录不可恢复，必须向用户确认记录列表和数量
- **用户确认**：当 mode=all 时将删除当前数据表全部记录，必须向用户二次确认

**幂等性**：是

> `records` 是对象数组（记录 ID），**不是**字符串数组；不应该传 `["G"]` 等字符串格式，而应该传 `[{"id":"G"}]` 等对象格式

#### 调用示例

批量删除记录：

```json
{
  "file_id": "VsdfG0001234567",
  "sheet_id": 3,
  "mode": "include",
  "is_batch": false,
  "records": [
    {
      "id": "G"
    },
    {
      "id": "H"
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `records` (array[object], 必填): 要删除的记录列表（对象数组）
- `mode` (string, 可选): 删除模式，默认 `include`；`all` 表示删除所有记录。可选值：`include` / `all`；默认值：`include`
- `is_batch` (boolean, 可选): 是否批量删除，默认 `false`；默认值：`false`

**请求体结构：**

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `records` | array[object] | 是 | 记录 ID 对象数组，每个元素为一条记录的 ID |
| `mode` | string | 否 | 删除模式，默认 `include`；`all` 表示删除所有记录 |
| `is_batch` | boolean | 否 | 是否批量删除，默认 `false` |

**请求体示例：**

```json
{
  "file_id": "你的 file_id",
  "sheet_id": 3,
  "mode": "include",
  "is_batch": false,
  "records": [
    { "id": "G" },
    { "id": "H" },
    { "id": "I" }
  ]
}
```

> 记录 ID 可通过 `dbsheet.list_records` 或 `dbsheet.get_record` 获取。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "records": [
      { "id": "G", "deleted": true },
      { "id": "H", "deleted": true }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应代码，0 表示成功，非 0 表示失败 |
| `msg` | string | 响应信息 |
| `data.records` | array[object] | 删除结果列表 |
| `more` | object | 更多错误信息（失败时返回） |


---

## 6. dbsheet.records_list

#### 功能说明

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fields | array[string] | 是* | 指定返回记录中的字段；*文档写必填，若不填则默认返回全部字段。`prefer_id=true` 时填字段 id，否则填字段名 |
| filter | object | 否 | 筛选条件 |
| filter.criteria | array[object] | 条件内必填 | 条件数组，每项含 `field`（字段名/id）、`op`（操作符，如 Contains / Equal / Empty 等）、`values`（筛选值，Empty/NotEmpty 时可省略） |
| max_records | integer | 否 | 最多取前 max_records 条；不填则不限 |
| page_size | integer | 否 | 每页大小，默认 100，范围 1–1000 |
| page_token | string | 否 | 分页游标；有下一页时用上次的 page_token |
| prefer_id | boolean | 否 | 为 true 时 fields 等按字段 id 解析 |
| show_fields_info | boolean | 否 | 是否额外返回字段元信息（类似 Schema fields） |
| show_record_extra_info | boolean | 否 | 是否返回创建者、创建时间、最后修改者、最后修改时间等 |
| text_value | string | 否 | 不填默认 original；可选 original、text、compound |
| view_id | string | 否 | 指定视图则从该视图取用户可见记录；不填从工作表取 |

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema和dbsheet.views_list确认要操作的数据表id和视图id，不得自行捏造数据表id和视图id。

**幂等性**：是

> filter.criteria 的结构需符合多维表格接口对筛选条件的约定。

#### 调用示例

最简：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "body": {}
}
```

返回文本值并携带额外信息：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "prefer_id": false,
  "show_fields_info": false,
  "text_value": "text",
  "show_record_extra_info": true
}
```

分页与视图：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "B",
  "page_size": 50,
  "page_token": ""
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `body` (object, 可选): 可选整包请求体；与顶层字段混用时同键以顶层为准
- `fields` (array, 必填): 指定所返回记录中的字段信息，若不填写则默认返回全部字段。prefer_id=true 时须用字段 id，否则用字段名
- `filter` (object, 可选): 筛选条件
  - `mode` (string, 必填): 条件连接方式：`"AND"` 或 `"OR"`
  - `criteria` (array, 必填): 筛选条件列表，每项包含：
    - `field` (string, 必填): 字段名称或字段 id（由 prefer_id 决定）
    - `op` (string, 必填): 筛选操作符，见多维表格参数说明（如 `Contains`、`Intersected`、`Greater`、`Less`、`Equal`、`Empty`、`NotEmpty` 等）
    - `values` (array, 可选): 筛选值；`Empty` / `NotEmpty` 操作符时可省略
- `max_records` (integer, 可选): 最多返回前 max_records 条，若不填写则默认返回全部记录
- `page_size` (integer, 可选): 分页获取记录时的每页大小，默认 100，取值范围 1-1000
- `page_token` (string, 可选): 分页起始位置。当存在分页且未查询到最后一页或 max_records 记录时，返回值会包含 page_token
- `prefer_id` (boolean, 可选): 使用 id 来标识字段和选项。为 true 时，参数内全部的 field、fields 参数均按照 id 做解析
- `show_fields_info` (boolean, 可选): 是否返回一个 fields 结构体，展示字段信息（类似 Base Schema 中的 fields）
- `show_record_extra_info` (boolean, 可选): 是否返回创建者、创建时间、最后修改者、最后修改时间信息（与是否有对应字段无关）
- `text_value` (string, 可选): 返回值类型，不填默认为 original。可选：original（原始值）、text（文本值）、compound（原始值和文本值）
- `view_id` (string, 可选): 指定视图 id。填写后从该视图获取用户所见记录；不填则从工作表获取记录

所有列举参数均在 **POST JSON 请求体** 中，不拼 URL query。

若同时传 `body` 与顶层字段，同键以 **顶层** 为准。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "fields_schema": [
      {
        "name": "文本",
        "type": "MultiLineText",
        "id": "B",
        "data": { "unique_value": false }
      },
      {
        "name": "数字",
        "type": "Number",
        "id": "C",
        "data": { "number_format": "0.00_ " }
      }
    ],
    "records": [
      {
        "fields": "{\"单选项\":\"选项1\",\"数字\":\"123.00 \",\"文本\":\"第一行文本\",\"日期\":\"2024/12/20\",\"等级\":\"1\"}",
        "id": "B",
        "created_time": "2024/12/20 11:30:32",
        "creator": "280026893",
        "last_modified_by": "280026893",
        "last_modified_time": "2024/12/20 15:47:01"
      }
    ],
    "page_token": ""
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应代码，非 0 表示失败 |
| `msg` | string | 响应信息 |
| `data` | object | 响应数据 |
| `more` | object | 更多的错误信息 |


---

## 7. dbsheet.records_search

#### 功能说明

⚠️ **`records` 必须为 JSON 字符串数组，从 `dbsheet.list_records` 或 `dbsheet.records_list` 获取记录 ID。** `file_id`、`sheet_id`、`records` 三个全部必填。
✅ 正确：`records: ["rec_xxx", "rec_yyy"]`
❌ 错误：`records: "(array, 3 items)"`（字符串）、`records: true`（布尔值）、`records: {_keys:[...]}`（对象）

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| records | array[string] | 是 | 记录 id 列表 |
| prefer_id | boolean | 否 | 是否使用字段 / 选项 id 而不是字段 / 选项名来标识 |
| show_fields_info | boolean | 否 | 为 true 时额外返回 fields 结构体展示字段信息；返回范围取决于是否指定 fields 或 view_id |
| show_record_extra_info | boolean | 否 | 为 true 时额外显示创建者、创建时间、最后修改者、最后修改时间（与是否有对应字段无关） |
| text_value | string | 否 | 返回值类型，不填默认 original；可选 original、text、compound |

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。

**幂等性**：是

> records 为必填参数，需传入有效的记录 id 列表。

#### 调用示例

按记录 id 批量检索：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "records": [
    "B",
    "C"
  ]
}
```

返回文本值并携带额外信息：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "records": [
    "B",
    "C"
  ],
  "prefer_id": false,
  "show_fields_info": false,
  "text_value": "text",
  "show_record_extra_info": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `body` (object, 可选): 可选整包请求体；与顶层字段混用时同键以顶层为准
- `records` (array, 必填): ⚠️ 记录 ID 列表（字符串数组，如 `["rec123"]`），不可传布尔值、对象或字符串
- `prefer_id` (boolean, 可选): 是否使用字段 / 选项 ID 而不是字段 / 选项名来标识
- `show_fields_info` (boolean, 可选): 是否返回 fields 结构体展示字段信息。为 true 时，若指定了 fields 则返回指定字段；未指定 fields 时，根据是否指定 view_id 决定返回视图可见字段或全部字段
- `show_record_extra_info` (boolean, 可选): 是否返回创建者、创建时间、最后修改者、最后修改时间信息（与是否有对应字段无关）
- `text_value` (string, 可选): 返回值类型，不填默认为 original。可选：original（原始值）、text（文本值）、compound（原始值和文本值）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "records": [
      {
        "fields": "{\"单选项\":\"选项1\",\"图片和附件\":\"12KB.docx,aigc\",\"数字\":\"123.00 \",\"文本\":\"第一行文本\",\"日期\":\"2024/12/20\",\"等级\":\"1\"}",
        "id": "B"
      },
      {
        "fields": "{\"单选项\":\"选项2\",\"图片和附件\":\"14.4KB.png\",\"数字\":\"321.00 \",\"文本\":\"第二行文本\",\"日期\":\"2024/12/21\",\"等级\":\"2\"}",
        "id": "C"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应代码，非 0 表示失败 |
| `msg` | string | 响应信息 |
| `data` | object | 响应数据 |
| `more` | object | 更多的错误信息 |

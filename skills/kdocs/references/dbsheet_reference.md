# 多维表格（dbt）工具完整参考文档

本文件包含金山文档 Skill 多维表格的操作说明。

---

## 一、数据表管理

### 1. dbsheet.get_schema

#### 功能说明

获取多维表格文档的 Schema 信息，包括所有数据表、字段和视图的结构。可指定单个数据表 ID，不填则返回全部。


#### 调用示例

获取全部数据表结构：

```json
{
  "file_id": "string"
}
```

获取指定数据表结构：

```json
{
  "file_id": "string",
  "sheet_id": 1
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 可选): 指定数据表 ID，不填则返回所有表
- `reserve_no_permission_sheet` (boolean, 可选): 是否保留无权限的表；默认值：`false`
- `show_very_hidden` (boolean, 可选): 是否显示深度隐藏的表；默认值：`true`
- `include_all_record_ids` (boolean, 可选): 是否返回所有记录 ID；默认值：`false`

#### 返回值说明

```json
{
  "detail": {
    "sheets": [
      {
        "id": 3,
        "name": "数据表",
        "primary_field_id": "B",
        "records_count": 100,
        "record_ids": ["A", "B"],
        "fields": [
          { "id": "B", "name": "名称", "type": "SingleLineText", "description": "字段备注" },
          { "id": "C", "name": "数量", "type": "Number", "description": "字段备注" }
        ],
        "views": [
          { "id": "B", "name": "表格视图", "type": "grid", "records_count": 10 }
        ]
      }
    ],
    "book_type": "db"
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.sheets[].id` | integer | 数据表 ID |
| `detail.sheets[].name` | string | 数据表名称 |
| `detail.sheets[].primary_field_id` | string | 主字段 ID |
| `detail.sheets[].records_count` | integer | 总记录数 |
| `detail.sheets[].record_ids` | array | 所有记录 ID（需开启 `include_all_record_ids`） |
| `detail.sheets[].fields` | array | 字段列表 |
| `detail.sheets[].views` | array | 视图列表 |
| `detail.book_type` | string | 文档类型标识，固定为 db |
| `result` | string | ok 表示成功 |

---

### 2. dbsheet.create_sheet

#### 功能说明

在多维表格文档中创建新的数据表，支持同时指定初始视图和字段。


#### 调用示例

创建带初始字段的数据表：

```json
{
  "file_id": "string",
  "name": "新数据表",
  "views": [
    {
      "name": "默认视图",
      "type": "Grid"
    }
  ],
  "fields": [
    {
      "name": "名称",
      "type": "SingleLineText"
    },
    {
      "name": "状态",
      "type": "SingleSelect",
      "items": [
        {
          "value": "待处理"
        },
        {
          "value": "已完成"
        }
      ]
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `name` (string, 必填): 数据表名称
- `sync_type` (string, 可选): 同步类型；默认值：`None`
- `after_sheet_id` (integer, 可选): 插入到指定数据表之后
- `before_sheet_id` (integer, 可选): 插入到指定数据表之前
- `views` (array, 可选): 初始视图列表，每项包含 `name` 和 `type`
- `fields` (array, 可选): 初始字段列表，每项包含 `name` 和 `type`

#### 返回值说明

```json
{
  "detail": {
    "sheet": {
      "id": 6,
      "name": "新数据表",
      "primary_field_id": "L",
      "fields": [
        { "id": "L", "name": "名称", "type": "SingleLineText" }
      ],
      "views": [
        { "id": "J", "name": "默认视图", "type": "Grid" }
      ]
    }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.sheet.id` | integer | 新建数据表 ID |
| `detail.sheet.name` | string | 数据表名称 |
| `detail.sheet.primary_field_id` | string | 主字段 ID |
| `detail.sheet.fields` | array | 字段列表 |
| `detail.sheet.views` | array | 视图列表 |
| `result` | string | ok 表示成功 |


#### 操作约束

- **后置验证**：get_schema 确认数据表已创建
---

### 3. dbsheet.update_sheet

#### 功能说明

修改数据表的名称或主字段设置。

#### 调用示例

重命名数据表：

```json
{
  "file_id": "string",
  "sheet_id": 6,
  "name": "新名称"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `name` (string, 可选): 新名称
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `primary_field` (string, 可选): 主字段名称

#### 返回值说明

```json
{
  "detail": {
    "sheet": {
      "id": 6,
      "name": "新名称",
      "primary_field_id": "L",
      "fields": [],
      "views": []
    }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.sheet.id` | integer | 数据表 ID |
| `detail.sheet.name` | string | 数据表名称 |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_schema 确认目标数据表存在
---

### 4. dbsheet.delete_sheet

#### 功能说明

删除多维表格中的指定数据表。

#### 调用示例

删除数据表：

```json
{
  "file_id": "string",
  "sheet_id": 6
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 要删除的数据表 ID

#### 返回值说明

```json
{
  "detail": {
    "sheet": { "id": 6 }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.sheet.id` | integer | 已删除的数据表 ID |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_schema 核对拟删数据表的名称和内容
- **用户确认**：删除数据表不可恢复，必须向用户确认数据表名称和 ID
- **禁止**：未经用户在对话中明确同意，禁止调用
---

## 二、视图管理

### 5. dbsheet.create_view

#### 功能说明

在指定数据表中创建新视图，支持表格、看板、画册、表单、甘特、日历等视图类型。


#### 调用示例

创建看板视图：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "name": "看板视图",
  "type": "Kanban",
  "group_field": "状态"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `name` (string, 必填): 视图名称
- `type` (string, 必填): 视图类型（见附录：视图类型）
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `group_field` (string, 可选): 分组字段名称

#### 返回值说明

```json
{
  "detail": {
    "view": { "id": "I", "name": "看板视图", "type": "Kanban" }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.view.id` | string | 新建视图 ID |
| `detail.view.name` | string | 视图名称 |
| `detail.view.type` | string | 视图类型 |
| `result` | string | ok 表示成功 |


#### 操作约束

- **后置验证**：get_schema 确认视图已创建
---

### 6. dbsheet.update_view

#### 功能说明

更新视图的名称、字段顺序、字段显隐状态及列宽等展示配置。

#### 调用示例

重命名并调整视图配置：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "I",
  "name": "重命名视图",
  "order_fields": [
    "B",
    "D",
    "F",
    "E",
    "C"
  ],
  "fields_attribute": [
    {
      "field": "D",
      "hidden": true
    }
  ],
  "widths": [
    {
      "field": "B",
      "width": 1600
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `view_id` (string, 必填): 视图 ID
- `name` (string, 可选): 新视图名称
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `order_fields` (array, 可选): 字段排列顺序，字段 ID 数组
- `fields_attribute` (array, 可选): 字段显隐属性，每项包含 `field` 和 `hidden`
- `height` (integer, 可选): 行高（Twip 单位）
- `widths` (array, 可选): 字段列宽配置，每项包含 `field` 和 `width`

#### 返回值说明

```json
{
  "detail": {
    "view": { "id": "I", "name": "重命名视图", "type": "Grid" }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.view.id` | string | 视图 ID |
| `detail.view.name` | string | 视图名称 |
| `detail.view.type` | string | 视图类型 |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_schema 确认目标视图存在
---

### 7. dbsheet.delete_view

#### 功能说明

删除指定数据表中的视图。

#### 调用示例

删除视图：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "I"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `view_id` (string, 必填): 视图 ID

#### 返回值说明

```json
{
  "detail": {
    "view": { "id": "I" }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.view.id` | string | 已删除的视图 ID |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_schema 核对拟删视图的名称和类型
- **用户确认**：删除视图不可恢复，必须向用户确认视图名称和 ID
- **禁止**：未经用户在对话中明确同意，禁止调用
---

## 三、字段管理

### 8. dbsheet.create_fields

#### 功能说明

在指定数据表中批量创建字段，支持文本、数值、单选、多选、日期、附件等多种类型。


#### 调用示例

创建多种类型字段：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "fields": [
    {
      "name": "状态",
      "type": "SingleSelect",
      "items": [
        {
          "value": "待处理"
        },
        {
          "value": "进行中"
        },
        {
          "value": "已完成"
        }
      ]
    },
    {
      "name": "截止日期",
      "type": "Date"
    },
    {
      "name": "备注",
      "type": "MultiLineText"
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `fields` (array, 必填): 要创建的字段列表
  - `name` (string, 必填): 字段名称
  - `type` (string, 必填): 字段类型（见附录：字段类型）
  - `items` (array, 可选): 选项列表，用于 `SingleSelect`/`MultipleSelect` 类型，每项包含 `value`
  - `number_format` (string, 可选): 数字格式，用于 `Number` 类型，如 `"0.00_ "`
  - `sync_field` (boolean, 可选): 是否同步字段
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key

#### 返回值说明

```json
{
  "detail": {
    "fields": [
      {
        "id": "K",
        "name": "状态",
        "type": "SingleSelect",
        "items": [
          { "id": "E", "value": "待处理" },
          { "id": "F", "value": "进行中" },
          { "id": "G", "value": "已完成" }
        ]
      },
      { "id": "L", "name": "截止日期", "type": "Date" }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.fields[].id` | string | 新建字段 ID |
| `detail.fields[].name` | string | 字段名称 |
| `detail.fields[].type` | string | 字段类型 |
| `detail.fields[].items` | array | 选项列表（选项类型字段） |
| `result` | string | ok 表示成功 |


#### 操作约束

- **后置验证**：get_schema 确认字段已创建
---

### 9. dbsheet.update_fields

#### 功能说明

批量更新数据表中已有字段的名称、选项等属性。每项更新必须包含字段 ID。

#### 调用示例

更新字段名称和选项：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "fields": [
    {
      "id": "E",
      "name": "优先级",
      "items": [
        {
          "id": "B",
          "value": "低"
        },
        {
          "value": "中"
        },
        {
          "id": "D",
          "value": "高"
        }
      ]
    },
    {
      "id": "C",
      "max": 4
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `fields` (array, 必填): 要更新的字段列表，每项必须包含 `id` 字段
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `omit_failure` (boolean, 可选): 部分字段更新失败时是否继续执行；默认值：`false`

#### 返回值说明

```json
{
  "detail": {
    "fields": [
      {
        "id": "E",
        "name": "优先级",
        "type": "SingleSelect",
        "items": [
          { "id": "B", "value": "低" },
          { "id": "H", "value": "中" },
          { "id": "D", "value": "高" }
        ]
      }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.fields` | array | 更新后的字段列表 |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_schema 确认目标字段存在及当前属性
---

### 10. dbsheet.delete_fields

#### 功能说明

批量删除数据表中的指定字段。

#### 调用示例

删除多个字段：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "fields": [
    {
      "id": "C"
    },
    {
      "id": "D"
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `fields` (array, 必填): 要删除的字段列表，每项包含 `id`

#### 返回值说明

```json
{
  "detail": {
    "fields": [
      { "id": "C", "deleted": true },
      { "id": "D", "deleted": true }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.fields` | array | 删除结果列表，每项包含 `id` 和 `deleted` |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_schema 核对拟删字段的名称和类型
- **用户确认**：删除字段不可恢复，字段数据将永久丢失，必须向用户确认字段列表
- **禁止**：未经用户在对话中明确同意，禁止调用
---

## 四、记录操作

### 11. dbsheet.create_records

#### 功能说明

在指定数据表中批量创建记录，通过字段名称或字段 ID 指定各字段的值。


#### 调用示例

批量创建记录：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "records": [
    {
      "fields": {
        "名称": "任务A",
        "数量": 10,
        "状态": "待处理"
      }
    },
    {
      "fields": {
        "名称": "任务B",
        "数量": 20
      }
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `records` (array, 必填): 要创建的记录列表，每项包含 `fields` 对象（字段名→值映射）
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key，默认 `false`（使用字段名）
- `value_prefer_id` (boolean, 可选): 字段值是否使用 ID 表示
- `omit_failure` (boolean, 可选): 部分记录创建失败时是否继续；默认值：`false`
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）或 `"display"`（显示值）
- `link_value` (string, 可选): 关联字段值格式：`"id"` 或 `"value"`
- `add_select_item` (boolean, 可选): 是否自动新增不存在的选项；默认值：`true`

#### 返回值说明

```json
{
  "detail": {
    "records": [
      { "id": "T", "fields": { "名称": "任务A", "数量": 10, "状态": "待处理" } },
      { "id": "U", "fields": { "名称": "任务B", "数量": 20 } }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.records[].id` | string | 新建记录 ID |
| `detail.records[].fields` | object | 各字段的值 |
| `result` | string | ok 表示成功 |


#### 操作约束

- **后置验证**：list_records 确认记录已创建
---

### 12. dbsheet.update_records

#### 功能说明

批量更新数据表中已有记录的字段值，每条记录必须提供记录 ID。

#### 调用示例

批量更新记录：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "records": [
    {
      "id": "B",
      "fields": {
        "名称": "更新后的名称",
        "状态": "已完成"
      }
    },
    {
      "id": "C",
      "fields": {
        "数量": 999
      }
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `records` (array, 必填): 要更新的记录列表，每项必须包含 `id`（记录 ID）和 `fields`（字段值映射）
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `value_prefer_id` (boolean, 可选): 字段值是否使用 ID 表示
- `omit_failure` (boolean, 可选): 部分记录更新失败时是否继续；默认值：`false`
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）或 `"display"`（显示值）
- `link_value` (string, 可选): 关联字段值格式：`"id"` 或 `"value"`
- `add_select_item` (boolean, 可选): 是否自动新增不存在的选项

#### 返回值说明

```json
{
  "detail": {
    "records": [
      { "id": "B", "fields": { "名称": "更新后的名称", "状态": "已完成" } },
      { "id": "C", "fields": { "数量": 999 } }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.records` | array | 更新后的记录列表，每项包含 `id` 和 `fields` |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_record 或 list_records 确认目标记录存在及当前值
- **后置验证**：get_record 确认更新结果
---

### 13. dbsheet.list_records

#### 功能说明

分页遍历数据表中的记录，支持按视图过滤、指定返回字段，以及通过 `filter` 参数实现复杂查询条件（多字段 AND/OR 组合筛选）。


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


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `page_size` (integer, 可选): 每页记录数
- `offset` (string, 可选): 翻页游标，首次请求传空字符串，后续传响应中的 `offset` 值
- `view_id` (string, 可选): 按指定视图返回记录
- `max_records` (integer, 可选): 最多返回的记录总数
- `fields` (array, 可选): 只返回指定字段列表，不填则返回所有字段
- `filter` (object, 可选): 筛选条件
  - `mode` (string, 必填): 条件连接方式：`"AND"` 或 `"OR"`
  - `criteria` (array, 必填): 筛选条件列表
    - `field` (string, 必填): 字段名称或 ID
    - `op` (string, 必填): 筛选操作符（见附录：筛选规则）
    - `values` (array, 可选): 筛选值，`Empty`/`NotEmpty` 时可省略
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）或 `"display"`（显示值）
- `link_value` (string, 可选): 关联字段值格式：`"id"` 或 `"value"`
- `show_record_extra_info` (boolean, 可选): 是否返回记录额外信息
- `show_fields_info` (boolean, 可选): 是否在响应中返回字段定义信息

> **分页说明**：响应中的 `offset` 指向下一页第一条记录，下次请求将该值传入 `offset` 即可翻页。最后一页不再返回 `offset`。


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

### 14. dbsheet.get_record

#### 功能说明

获取数据表中某条指定记录的完整字段内容。

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

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `record_id` (string, 必填): 记录 ID
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）或 `"display"`（显示值）
- `link_value` (string, 可选): 关联字段值格式：`"id"` 或 `"value"`
- `show_record_extra_info` (boolean, 可选): 是否返回记录额外信息
- `show_fields_info` (boolean, 可选): 是否返回字段定义信息

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

### 15. dbsheet.delete_records

#### 功能说明

批量删除数据表中的指定记录。

#### 调用示例

批量删除记录：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "records": [
    {
      "id": "B"
    },
    {
      "id": "C"
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `records` (array, 必填): 要删除的记录列表，每项包含 `id`
- `mode` (string, 可选): 删除模式，`"include"` 表示删除指定记录
- `is_batch` (boolean, 可选): 是否批量操作模式

#### 返回值说明

```json
{
  "detail": {
    "records": [
      { "id": "B", "deleted": true },
      { "id": "C", "deleted": true }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.records` | array | 删除结果列表，每项包含 `id` 和 `deleted` |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：list_records 或 get_record 核对拟删记录内容
- **用户确认**：批量删除记录不可恢复，必须向用户确认记录列表和数量
- **禁止**：未经用户在对话中明确同意，禁止调用
---


## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `dbsheet.get_schema` | 数据表管理 | 获取文档结构（表/字段/视图） | `file_id` |
| 2 | `dbsheet.create_sheet` | 数据表管理 | 创建数据表 | `file_id`, `name` |
| 3 | `dbsheet.update_sheet` | 数据表管理 | 修改数据表名称 | `file_id`, `sheet_id` |
| 4 | `dbsheet.delete_sheet` | 数据表管理 | 删除数据表 | `file_id`, `sheet_id` |
| 5 | `dbsheet.create_view` | 视图管理 | 创建视图 | `file_id`, `sheet_id`, `name`, `type` |
| 6 | `dbsheet.update_view` | 视图管理 | 更新视图配置 | `file_id`, `sheet_id`, `view_id` |
| 7 | `dbsheet.delete_view` | 视图管理 | 删除视图 | `file_id`, `sheet_id`, `view_id` |
| 8 | `dbsheet.create_fields` | 字段管理 | 批量创建字段 | `file_id`, `sheet_id`, `fields` |
| 9 | `dbsheet.update_fields` | 字段管理 | 批量更新字段 | `file_id`, `sheet_id`, `fields` |
| 10 | `dbsheet.delete_fields` | 字段管理 | 批量删除字段 | `file_id`, `sheet_id`, `fields` |
| 11 | `dbsheet.create_records` | 记录操作 | 批量创建记录 | `file_id`, `sheet_id`, `records` |
| 12 | `dbsheet.update_records` | 记录操作 | 批量更新记录 | `file_id`, `sheet_id`, `records` |
| 13 | `dbsheet.list_records` | 记录操作 | 分页遍历记录（支持筛选） | `file_id`, `sheet_id` |
| 14 | `dbsheet.get_record` | 记录操作 | 获取单条记录 | `file_id`, `sheet_id`, `record_id` |
| 15 | `dbsheet.delete_records` | 记录操作 | 批量删除记录 | `file_id`, `sheet_id`, `records` |

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 多维表格读结构/数据 | `dbsheet.get_schema` → `dbsheet.list_records` / `dbsheet.get_record` |
| 多维表格增删改 | `dbsheet.get_schema` → `dbsheet.create_records` / `dbsheet.update_records` / `dbsheet.delete_records`|

---

## 错误速查表

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| 多维表格读不到结构化数据 | 误用 `read_file_content` 作主读 | 改用 `dbsheet.get_schema`、`dbsheet.list_records` 等，见 `references/dbsheet_reference.md` |

---

## 附录

### 字段类型

| 类型 | 说明 |
|------|------|
| `SingleLineText` | 单行文本 |
| `MultiLineText` | 多行文本 |
| `Number` | 数值 |
| `Currency` | 货币 |
| `Percentage` | 百分比 |
| `Date` | 日期 |
| `Time` | 时间 |
| `Checkbox` | 复选框 |
| `SingleSelect` | 单选项 |
| `MultipleSelect` | 多选项 |
| `Rating` | 等级 |
| `Complete` | 进度条 |
| `Phone` | 电话 |
| `Email` | 电子邮箱 |
| `Url` | 超链接 |
| `Contact` | 联系人 |
| `Attachment` | 附件 |
| `Link` | 关联 |
| `Note` | 富文本 |
| `Address` | 地址 |
| `AutoNumber` | 编号（自动填充） |
| `CreatedBy` | 创建者（自动填充） |
| `CreatedTime` | 创建时间（自动填充） |
| `LastModifiedBy` | 最后修改者（自动填充） |
| `LastModifiedTime` | 最后修改时间（自动填充） |
| `Formula` | 公式（自动计算） |
| `Lookup` | 引用（自动计算） |

### 视图类型

| 类型 | 说明 |
|------|------|
| `Grid` | 表格视图 |
| `Kanban` | 看板视图 |
| `Gallery` | 画册视图 |
| `Form` | 表单视图 |
| `Gantt` | 甘特视图 |
| `Calendar` | 日历视图 |

### 筛选规则（filter op）

| 操作符 | 适用字段类型 | 说明 |
|--------|-------------|------|
| `Equals` | 通用 | 等于 |
| `NotEqu` | 通用 | 不等于 |
| `Greater` | 数值、日期 | 大于 |
| `GreaterEqu` | 数值、日期 | 大于等于 |
| `Less` | 数值、日期 | 小于 |
| `LessEqu` | 数值、日期 | 小于等于 |
| `BeginWith` | 文本 | 开头是 |
| `EndWith` | 文本 | 结尾是 |
| `Contains` | 文本 | 包含 |
| `NotContains` | 文本 | 不包含 |
| `Intersected` | 单选、多选 | 选项包含指定值 |
| `Empty` | 通用 | 为空（`values` 可省略） |
| `NotEmpty` | 通用 | 不为空（`values` 可省略） |

### 错误响应

| 情况 | 响应示例 |
|------|---------|
| 命令不支持 | `{"msg":"core not support","result":"unSupport"}` |
| 内核错误 | `{"errno":-1880935404,"msg":"Invalid request","result":"ExecuteFailed"}` |
| HTTP 状态非 200 | 请求本身失败，检查 `file_id` 是否正确及鉴权信息 |

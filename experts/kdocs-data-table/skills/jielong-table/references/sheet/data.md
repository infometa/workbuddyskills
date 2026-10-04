# 数据操作

## 1. sheet.get_range_data

#### 功能说明

获取指定工作表中某个矩形区域内的单元格数据。行列索引均为 0-based。
请求参数使用 `worksheet_id` 和 `range` 对象。
**`range` 必须为对象，即使只读取一个单元格也必须包裹在对象中传入，不可传数组。**

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 行列索引均为 0-based；读取整张表时先用 sheet.get_sheets_info 获取 range.rowTo / range.colTo 上限
> isCellPic=true 时，单元格为图片；picData（在线文件）和 sha1（本地图片）二选一返回
> originalCellValue 返回公式栏原始值，cellText 返回显示值；fmlaText 仅在含公式时返回

#### 调用示例

读取 A1:F11 区域（前 11 行、前 6 列）：

```json
{
  "file_id": "VsdfG0001234567",
  "worksheet_id": 3,
  "range": {
    "rowFrom": 0,
    "rowTo": 10,
    "colFrom": 0,
    "colTo": 5
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range` (object, 必填): 选区范围（必须为对象，即使只读取一个单元格也必须包裹在对象中传入，不可传数组），行列索引均为 0-based

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {
    "rangeData": [
      {
        "cellText": "test",
        "colFrom": 0,
        "colTo": 0,
        "isCellPic": false,
        "numFormat": "G/通用格式",
        "originalCellValue": "test",
        "rowFrom": 0,
        "rowTo": 0,
        "fmlaText": "=A1"
      },
      {
        "cellText": "111",
        "colFrom": 1,
        "colTo": 1,
        "isCellPic": false,
        "numFormat": "G/通用格式",
        "originalCellValue": "111",
        "rowFrom": 0,
        "rowTo": 0
      },
      {
        "cellText": "332",
        "colFrom": 0,
        "colTo": 0,
        "isCellPic": false,
        "numFormat": "G/通用格式",
        "originalCellValue": "332",
        "rowFrom": 1,
        "rowTo": 1
      },
      {
        "cellText": "=DISPIMG(\"ID_018590616CC643F796F3CB58682DEA85\",1)",
        "colFrom": 1,
        "colTo": 1,
        "isCellPic": true,
        "numFormat": "G/通用格式",
        "originalCellValue": "=DISPIMG(\"ID_018590616CC643F796F3CB58682DEA85\",1)",
        "picData": "MSM5KAQABI",
        "sha1": "6CC643F796F3CB58682DEA85",
        "rowFrom": 1,
        "rowTo": 1,
        "tag": "attachment"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | 'ok' 表示成功 |
| `detail.rangeData` | array[object] | 单元格数据数组，每项对应选区内一个有数据的单元格 |


---

## 2. sheet.range_data_batch_update

#### 功能说明

批量更新单元格区域数据，支持写入公式/内容、图片、格式和合并。
本工具使用下划线参数命名（如 `worksheet_id`、`range_data`、`op_type`）。

#### 调用约束

- **前置检查**：建议先读取目标区域数据，确认覆盖范围与格式影响
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。
- **禁止**：`formula` 操作 `col_from`/`col_to` 之间每个单元格都会被填入相同值。标题跨列展示必须用 `merge` + 单格 `formula` 两步，禁止用 `formula` 直接跨多列填充相同文本。

**幂等性**：是

> `formula` 仅在 `op_type = cell_operation_type_formula` 时使用。
> `merge_type` 仅在 `op_type = cell_operation_type_merge` 时使用。
> ⚠️ `merge_type_center` 仅执行合并、不改变水平对齐；如需「合并居中」，请在 `merge` 操作后再追加一个 `format` 操作（`xf.alc_h=2`）。
> `xf` 仅在 `op_type = cell_operation_type_format` 时使用。
> `cell_pic_info` 仅在 `op_type = cell_operation_type_picture` 时使用。
> 每项操作都必须提供 `row_from` / `row_to` / `col_from` / `col_to` 与 `op_type`。
> `sheet.update_range_data` 为兜底工具（仅在 `range_data_batch_update` 写入失败时使用）；常规任务一律使用 `sheet.range_data_batch_update`。
> 使用该工具写入数据后，读取数据优先使用'sheet.find_range_data'工具。
> ⚠️ 本工具 `op_type` 仅支持四个全称：`cell_operation_type_formula`、`cell_operation_type_picture`、`cell_operation_type_format`、`cell_operation_type_merge`。短形式（`formula`/`picture`/`format`/`merge`）一律不可用。`update_range_data` 用简写，两个工具不可混用。
> **空白表格填写**：空值字段的框架行也必须写入 rangeData（formula 值可为空字符串 `""`），不能跳过，否则表格结构不完整。
> **`formula` 值以 `+`/`-`/`=` 开头会被当作公式解析**：写字面文本（如 `+86 手机号`）会报 Internal error，须前置 `'` 强制文本（如 `'+86 138…`），存储时引号不会带入。

#### 调用示例

写入公式：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range_data": [
    {
      "op_type": "cell_operation_type_formula",
      "row_from": 0,
      "row_to": 0,
      "col_from": 0,
      "col_to": 0,
      "formula": "=A1+B1"
    }
  ]
}
```

写入图片：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range_data": [
    {
      "op_type": "cell_operation_type_picture",
      "row_from": 1,
      "row_to": 1,
      "col_from": 1,
      "col_to": 1,
      "cell_pic_info": {
        "tag": "sheet_pic_type_url",
        "pic_content": "https://example.com/image.png",
        "width": 200,
        "height": 120
      }
    }
  ]
}
```

设置格式（加粗、居中、蓝底白字）：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range_data": [
    {
      "op_type": "cell_operation_type_format",
      "row_from": 0,
      "row_to": 0,
      "col_from": 0,
      "col_to": 5,
      "xf": {
        "font": {
          "name": "微软雅黑",
          "dy_height": 220,
          "bls": true,
          "color": {
            "type": 2,
            "value": 4294967295,
            "tint": 0
          }
        },
        "alc_h": 2,
        "alc_v": 1,
        "wrap": true,
        "fill": {
          "type": 1,
          "back": {
            "type": 2,
            "value": 4278190335,
            "tint": 0
          },
          "fore": {
            "type": 255,
            "value": 0,
            "tint": 0
          }
        }
      }
    }
  ]
}
```

合并单元格并居中：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range_data": [
    {
      "op_type": "cell_operation_type_merge",
      "row_from": 2,
      "row_to": 3,
      "col_from": 0,
      "col_to": 3,
      "merge_type": "merge_type_center"
    },
    {
      "op_type": "cell_operation_type_format",
      "row_from": 2,
      "row_to": 3,
      "col_from": 0,
      "col_to": 3,
      "xf": {
        "alc_h": 2
      }
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range_data` (array[object], 必填): 单元格操作数组

**枚举值：**

- `op_type`：
  - `cell_operation_type_formula`
  - `cell_operation_type_picture`
  - `cell_operation_type_format`
  - `cell_operation_type_merge`
- `merge_type`：
  - `merge_type_center`
  - `merge_type_content`
  - `merge_type_same`
  - `merge_type_columns`
- `cell_pic_info.tag`：
  - `sheet_pic_type_local`
  - `sheet_pic_type_attachment`
  - `sheet_pic_type_url`

**颜色对象（`clr_*` / `font.color` / `fill.back` / `fill.fore`）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | integer | 是 | 颜色类型：0=ICV，1=THEME 主题色，2=ARGB，254=无颜色（背景透明），255=自动色（字体/边框默认） |
| `value` | integer | 是 | ARGB 整数值（type=2 时有效）。十进制 = 十六进制 ARGB 转十进制整数，如纯红 `0xFFFF0000` → `4294901760` |
| `tint` | integer | 是 | 透明度，调节颜色深浅 |

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 响应消息 |


---

## 3. sheet.delete_range_data

#### 功能说明

删除指定区域的行或列，删除后将其余内容上移或左移。适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：`sheet.get_range_data` 核对拟删行/列范围内现有数据
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。
- **用户确认**：删除行或列会移位其余内容且难以恢复，必须向用户确认范围与影响

**幂等性**：是

> 行列索引均为 0-based

#### 调用示例

删除范围数据（默认上移）：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range_data": [
    {
      "col_from": 0,
      "col_to": 0,
      "row_from": 0,
      "row_to": 0
    }
  ],
  "shift_type": "shift_up"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range_data` (array[object], 必填): 范围数组；调用方需保证参数在行列最大最小值范围内，超过则执行失败。最大值可通过 `sheet.get_sheets_info` 获取
- `shift_type` (string, 可选): 移动方式，默认向上移动。可选值：`shift_up` / `shift_left`；默认值：`shift_up`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 错误描述，code 非 0 时返回失败原因 |


---

## 4. sheet.add_row

#### 功能说明

在工作表已使用区域末尾追加一行数据，支持写入文本/公式和图片。
适用于 Excel（.xlsx）和智能表格（.ksheet）。
file_id和worksheet_id为必填参数，不允许为空，worksheet_id必须为数字。
range_data.op_type的枚举值只有cell_operation_type_formula，cell_operation_type_picture，cell_operation_type_format，cell_operation_type_merge四种，不允许自主定义。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：否 — 重复调用会插入多行，先确认是否已成功

> 行列索引均为 0-based

#### 调用示例

追加一行（文本与图片）：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range_data": [
    {
      "op_type": "cell_operation_type_formula",
      "col": 0,
      "formula": "值1"
    },
    {
      "op_type": "cell_operation_type_formula",
      "formula": "值2"
    },
    {
      "op_type": "cell_operation_type_picture",
      "col": 3,
      "cell_pic_info": {
        "width": 120,
        "height": 120,
        "tag": "sheet_pic_type_url",
        "pic_content": "https://example.com/image.png"
      }
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range_data` (array[object], 可选): 新行各列的数据，按列顺序追加至已使用区域末尾，不可为空数组。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 错误描述，code 非 0 时返回失败原因 |


---

## 5. sheet.find_range_data

#### 功能说明

遍历并筛选工作表中的记录，支持分页、条件筛选、文本搜索和去重。

**工具选择提示**：
- `sheet.find_range_data`：用于“先筛选再返回结果”，支持 `filter`、`search`、`duplicates`、分页和总数统计。
- `sheet.get_range_data`：用于“直接读取固定矩形范围数据”，不做筛选、搜索、去重或分页。
使用该工具时必须传递worksheet_id和filter参数，worksheet_id必须为数字，若要查询所有数据则filter传空数组但必须传这个参数。
该工具仅适用于：Excel（.xlsx）和智能表格（.ksheet），在操作多维表格（.dbt）时使用"dbsheet"相关工具，不允许使用该工具操作多维表格。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 分页说明：通过 `page.page` 递增翻页，`total` 为结果总数。

#### 调用示例

按条件筛选并分页：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": {
    "col_from": 0,
    "col_to": 10,
    "row_from": 0,
    "row_to": 50000
  },
  "page": {
    "page": 1,
    "page_size": 100
  },
  "filter": {
    "condition": [
      {
        "col": 0,
        "info": [
          {
            "value": "string"
          }
        ],
        "mode": "filter_mode_and"
      }
    ],
    "duplicates": {
      "col": [
        0
      ]
    },
    "search": [
      {
        "col": 0,
        "value": [
          "string"
        ]
      }
    ]
  },
  "ignore_hidden_cell": true,
  "option_cols": [
    0
  ],
  "show_total": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range` (object, 必填): 筛选区域
- `page` (object, 可选): 分页参数（可选）
- `filter` (object, 必填): 筛选条件；`condition` 传空数组时不筛选，输出全部
- `ignore_hidden_cell` (boolean, 可选): 是否忽略隐藏单元格；默认值：`false`
- `option_cols` (array[integer], 可选): 需返回选项统计的列坐标（相对于 `range`）
- `show_total` (boolean, 可选): 是否返回总数；默认值：`false`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "merge_range_data": [
      {
        "cell_text": "string",
        "col_from": 0,
        "col_to": 0,
        "is_cell_pic": true,
        "num_format": "string",
        "original_cell_value": "string",
        "pic_content": "string",
        "pic_data": "string",
        "row_from": 0,
        "row_to": 0,
        "sha1": "string",
        "tag": "string"
      }
    ],
    "option_col": [
      {
        "col": 0,
        "texts": [
          {
            "count": 0,
            "origin": "string",
            "text": "string"
          }
        ]
      }
    ],
    "range_data": [
      {
        "cell_text": "string",
        "col_from": 0,
        "col_to": 0,
        "is_cell_pic": true,
        "num_format": "string",
        "original_cell_value": "string",
        "pic_content": "string",
        "pic_data": "string",
        "row_from": 0,
        "row_to": 0,
        "sha1": "string",
        "tag": "string"
      }
    ],
    "result_type": 0,
    "total": 0
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 错误描述，code 非 0 时返回失败原因 |
| `data.merge_range_data` | array[object] | 当前区域包含的合并单元格数据 |
| `data.option_col` | array[object] | 选项结果 |
| `data.range_data` | array[object] | 区域数据，格式与 `get_range_data` 一致；未设置筛选条件时返回全部数据 |
| `data.result_type` | integer | 本次是否成功，`0` 失败，`1` 成功 |
| `data.total` | integer | 结果总数 |


---

## 6. sheet.get_attachment_url

#### 功能说明

上传附件到文件，返回上传结果与对象标识（`object_id`）。
使用 `multipart/form-data` 方式上传。

支持普通上传，以及 `local_cover`（本地官方推荐模板）和 `user_cover`（用户上传封面图）场景。

> 请求需使用 `multipart/form-data` 提交参数
> `url` 与 `content_base64` 二选一
> 当 `source_type=local_cover` 时，必须传 `cover_id`
> 当 `source_type=user_cover` 时，必须传 `scale`
> 本工具为单次全量上传，无分片机制

#### 调用示例

普通上传（URL）：

```json
{
  "file_id": "12345",
  "filename": "6789.jpg",
  "url": "https://img.qwps.cn/example.jpg",
  "Content-Type": "multipart/form-data"
}
```

local_cover 上传：

```json
{
  "file_id": "12345",
  "filename": "cover.jpg",
  "source_type": "local_cover",
  "cover_id": "xxxxx",
  "Content-Type": "multipart/form-data"
}
```

user_cover 上传并带 map_id：

```json
{
  "file_id": "12345",
  "filename": "avatar.jpg",
  "source_type": "user_cover",
  "scale": 80,
  "map_id": "placeholder-001",
  "content_base64": "<base64>",
  "Content-Type": "multipart/form-data"
}
```

#### 参数说明

- `file_id` (string, 必填): 文件 ID 或分享 ID
- `filename` (string, 必填): 附件名
- `url` (string, 二选一必填: `url` / `content_base64`): 附件 URL；与 `content_base64` 二选一
- `content_base64` (string, 二选一必填: `url` / `content_base64`): 文件内容的 Base64 编码；与 `url` 二选一
- `source_type` (string, 可选): 上传内容类型。可选值：`local_cover` / `user_cover`；默认值：`file`
- `source` (string, 可选): 来源，例如 `processon`
- `cover_id` (string, 可选): 封面 ID；当 `source_type=local_cover` 时必填
- `scale` (integer, 可选): 缩略图压缩比；当 `source_type=user_cover` 时必填
- `map_id` (string, 可选): 占位图标志位（mapId）
- `Content-Type` (string, 必填): Header 文件类型，建议 `multipart/form-data`

#### 返回值说明

```json
{
  "result": "ok",
  "object_id": "1234567890",
  "extra_info": {
    "width": 600,
    "height": 400
  },
  "old_content_type": "image/heic",
  "new_content_type": "image/jpeg"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | 结果状态，成功为 `ok` |
| `object_id` | string | 上传对象 ID |
| `url` | string | 上传资源 URL（部分场景返回） |
| `extra_info.width` | integer | 图片宽度 |
| `extra_info.height` | integer | 图片高度 |
| `old_content_type` | string | 原始内容类型 |
| `new_content_type` | string | 转换后内容类型 |

响应中的 `object_id` 可作为上传对象标识用于后续引用。
在特定场景（如带 `map_id`）下，响应可能额外返回 `url`。


---

## 7. sheet.add_chart

#### 功能说明

在指定工作表中添加图表。支持柱形图、条形图、折线图、饼图、面积图、散点图、雷达图、股票图共 31 种类型。
添加前建议先调用 `sheet.get_chart_information` 查看已有图表，避免位置重叠导致遮盖。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：添加前建议先调用 `sheet.get_chart_information` 查询现有图表位置，避免重叠遮盖
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：否 — 重复调用会新增多个图表，先确认是否已成功

> 若数据区域包含表头，建议将表头纳入 `sourceAddress`，便于自动生成图例
> 跨表地址请使用 `'工作表名'!A1:D5` 形式，工作表名包含空格时必须加单引号
> `sourceAddress` 与 `rectAddress` 必须是合法地址；`plotBy` 仅支持 `rows` 或 `columns`

#### 调用示例

新增折线图（按列组织数据）：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "chartType": "line",
  "sourceAddress": "A1:D20",
  "rectAddress": "F1:L16",
  "title": "月度趋势",
  "plotBy": "columns"
}
```

新增簇状柱形图（按行组织数据）：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "chartType": "column_clustered",
  "sourceAddress": "'销售明细'!A1:F8",
  "rectAddress": "A22:H36",
  "title": "产品销量对比",
  "plotBy": "rows"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `chartType` (string, 必填): 图表类型（共 31 种，见 `param_detail`）。可选值：`column_clustered` / `column_stacked` / `column_stacked_100` / `bar_clustered` / `bar_stacked` / `bar_stacked_100` / `line` / `line_stacked` / `line_stacked_100` / `line_markers` / `line_markers_stacked` / `line_markers_stacked_100` / `pie` / `pie_of_pie` / `bar_of_pie` / `doughnut` / `area` / `area_stacked` / `area_stacked_100` / `scatter` / `scatter_smooth` / `scatter_smooth_no_markers` / `scatter_lines` / `scatter_lines_no_markers` / `bubble` / `radar` / `radar_markers` / `radar_filled` / `stock_hlc` / `stock_vhlc` / `stock_ohlc` / `stock_vohlc`
- `sourceAddress` (string, 必填): 数据源地址，如 `A1:D5` 或跨表 `'数据表'!A1:D5`
- `rectAddress` (string, 必填): 图表摆放位置，如 `F1:L10`
- `title` (string, 必填): 图表标题
- `plotBy` (string, 可选): 数据组织方式，`rows` 或 `columns`，默认 `columns`。可选值：`rows` / `columns`；默认值：`columns`

**chartType 枚举（31 种）：**

- 柱形图：`column_clustered`、`column_stacked`、`column_stacked_100`
- 条形图：`bar_clustered`、`bar_stacked`、`bar_stacked_100`
- 折线图：`line`、`line_stacked`、`line_stacked_100`、`line_markers`、`line_markers_stacked`、`line_markers_stacked_100`
- 饼图：`pie`、`pie_of_pie`、`bar_of_pie`、`doughnut`
- 面积图：`area`、`area_stacked`、`area_stacked_100`
- 散点图：`scatter`、`scatter_smooth`、`scatter_smooth_no_markers`、`scatter_lines`、`scatter_lines_no_markers`、`bubble`
- 雷达图：`radar`、`radar_markers`、`radar_filled`
- 股票图：`stock_hlc`、`stock_vhlc`、`stock_ohlc`、`stock_vohlc`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |


---

## 8. sheet.range_auto_fill

#### 功能说明

用源区域内容自动填充目标区域（常用于公式拖拽填充）。
目标区域必须包含源区域，源区域作为填充种子，目标区域为扩展范围。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：建议先用 `sheet.get_range_data` 检查 `targetAddress` 内是否存在需保留数据，避免被覆盖
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 自动填充常用于公式序列扩展；如需精确写入固定值可使用 `sheet.range_data_batch_update`
> 跨表填充前先确认 `sheetId` 与地址所在工作表一致，避免误填充到错误工作表
> `targetAddress` 必须包含 `sourceAddress`，且两者都需为合法 A1 地址

#### 调用示例

向下自动填充公式：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "sourceAddress": "A1:A5",
  "targetAddress": "A1:A20"
}
```

横向自动填充：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "sourceAddress": "B2:D2",
  "targetAddress": "B2:H2"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `sourceAddress` (string, 必填): 源区域地址，如 `A1:A5`（填充种子，须包含在 `targetAddress` 内）
- `targetAddress` (string, 必填): 目标区域地址，如 `A1:A10`（填充扩展范围，须包含 `sourceAddress`）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |


---

## 9. sheet.get_chart_information

#### 功能说明

获取指定工作表中所有图表的信息，包括标题、类型、位置、图例、坐标轴、数据系列等。
返回的 `index` 为 1-based，可直接作为 `sheet.update_chart` 系列工具的图表定位参数。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 当工作表无图表时，`data.charts` 可能为空数组
> 需要更新工作表内的图表信息时，先调用本工具确认要修改的图表是否存在，再决定是否要执行对应的更新操作

#### 调用示例

获取工作表图表信息：

```json
{
  "file_id": "string",
  "worksheet_id": 3
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "charts": [
      {
        "index": 1,
        "title": "月度趋势",
        "chartType": "line",
        "sourceAddress": "A1:D20",
        "rectAddress": "F1:L16",
        "legend": {
          "visible": true,
          "position": "right"
        },
        "axis": {
          "category": { "title": "月份" },
          "value": { "title": "销量" }
        },
        "series": [
          { "name": "产品 A", "values": "B2:B20" },
          { "name": "产品 B", "values": "C2:C20" }
        ]
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |
| `data.charts` | array[object] | 当前工作表内的图表列表 |


---

## 10. sheet.update_chart

#### 功能说明

修改指定图表的属性。
`updateType` 指定操作类型：
- `title`：修改标题（需 `title`）
- `type`：修改图表类型（需 `chartType`）
- `data_source`：修改数据源（需 `sourceAddress`，可选 `plotBy`）
- `position`：修改摆放位置（需 `rectAddress`）
- `legend`：修改图例（需 `hasLegend`，可选 `position`）
- `axis_title`：修改坐标轴（需 `axisType` + `title`，可选 `visible`）
图表索引 `index` 为 1-based，与 `sheet.get_chart_information` 返回值一致。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：更新前建议先调用 `sheet.get_chart_information` 核对图表 `index`，避免修改到错误图表
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> `index` 为 1-based，请直接使用查询结果，不要自行做加减
> 图例位置 `position` 仅在 `updateType=legend` 时生效
> `visible` 仅在 `updateType=axis_title` 时生效，默认 `true`
> `updateType` 与参数必须匹配；例如 `updateType=legend` 时必须传 `hasLegend`

#### 调用示例

修改图表标题：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "index": 1,
  "updateType": "title",
  "title": "季度销售趋势"
}
```

修改图表类型：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "index": 1,
  "updateType": "type",
  "chartType": "column_clustered"
}
```

修改数据源与组织方式：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "index": 1,
  "updateType": "data_source",
  "sourceAddress": "'销售明细'!A1:E20",
  "plotBy": "rows"
}
```

修改图例显示和位置：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "index": 1,
  "updateType": "legend",
  "hasLegend": true,
  "position": "right"
}
```

修改坐标轴标题：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "index": 1,
  "updateType": "axis_title",
  "axisType": "value",
  "title": "销售额（元）",
  "visible": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `index` (integer, 必填): 图表索引（1-based，同 `sheet.get_chart_information` 返回编号）
- `updateType` (string, 必填): 操作类型，决定本次更新的目标属性。可选值：`title` / `type` / `data_source` / `position` / `legend` / `axis_title`
- `title` (string, 可选): 标题文本（`updateType=title` 时为图表标题，`updateType=axis_title` 时为轴标题）
- `chartType` (string, 可选): 图表类型（`updateType=type` 时必填，共 31 种）。可选值：`column_clustered` / `column_stacked` / `column_stacked_100` / `bar_clustered` / `bar_stacked` / `bar_stacked_100` / `line` / `line_stacked` / `line_stacked_100` / `line_markers` / `line_markers_stacked` / `line_markers_stacked_100` / `pie` / `pie_of_pie` / `bar_of_pie` / `doughnut` / `area` / `area_stacked` / `area_stacked_100` / `scatter` / `scatter_smooth` / `scatter_smooth_no_markers` / `scatter_lines` / `scatter_lines_no_markers` / `bubble` / `radar` / `radar_markers` / `radar_filled` / `stock_hlc` / `stock_vhlc` / `stock_ohlc` / `stock_vohlc`
- `sourceAddress` (string, 可选): 数据源地址（`updateType=data_source` 时必填），如 `A1:D5` 或跨表 `'数据表'!A1:D5`
- `plotBy` (string, 可选): 数据组织方式（`updateType=data_source`），`rows` 或 `columns`，默认 `columns`。可选值：`rows` / `columns`；默认值：`columns`
- `rectAddress` (string, 可选): 摆放位置（`updateType=position` 时必填），如 `F1:L10`
- `hasLegend` (boolean, 可选): 是否显示图例（`updateType=legend` 时必填）
- `position` (string, 可选): 图例位置（`updateType=legend`），`top` / `bottom` / `left` / `right` / `center`。可选值：`top` / `bottom` / `left` / `right` / `center`；默认值：`bottom`
- `axisType` (string, 可选): 轴类型（`updateType=axis_title` 时必填），`category`（X 轴）或 `value`（Y 轴）。可选值：`category` / `value`
- `visible` (boolean, 可选): 是否显示坐标轴（`updateType=axis_title`），默认 `true`；默认值：`true`

**chartType 枚举（31 种）：**

- 柱形图：`column_clustered`、`column_stacked`、`column_stacked_100`
- 条形图：`bar_clustered`、`bar_stacked`、`bar_stacked_100`
- 折线图：`line`、`line_stacked`、`line_stacked_100`、`line_markers`、`line_markers_stacked`、`line_markers_stacked_100`
- 饼图：`pie`、`pie_of_pie`、`bar_of_pie`、`doughnut`
- 面积图：`area`、`area_stacked`、`area_stacked_100`
- 散点图：`scatter`、`scatter_smooth`、`scatter_smooth_no_markers`、`scatter_lines`、`scatter_lines_no_markers`、`bubble`
- 雷达图：`radar`、`radar_markers`、`radar_filled`
- 股票图：`stock_hlc`、`stock_vhlc`、`stock_ohlc`、`stock_vohlc`

---

**调用建议：**

1. 先调用 `sheet.get_chart_information` 获取当前工作表图表列表和 1-based `index`。
2. 按 `updateType` 只传本次操作需要的参数，避免混入无关字段。
3. 若更新 `data_source`，优先保证 `sourceAddress` 包含表头并与图表类型匹配。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |


---

## 11. sheet.create_pivot_table

#### 功能说明

在指定工作表上创建数据透视表。
创建后可用 `sheet.update_pivot_table` 配置字段布局（行、列、值、筛选等）。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：建议先用 `sheet.get_range_data` 或 `sheet.find_range_data` 确认 `sourceAddress` 数据完整，包含表头行
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：否 — 重复调用会创建多个透视表，先确认是否已成功

> 若 `tableDestination` 为空，系统会自动选择不冲突位置放置透视表
> 创建后可继续调用 `sheet.update_pivot_table` 配置字段布局与聚合方式
> `sourceAddress` 与 `tableDestination` 需为合法地址；跨表地址建议显式带工作表前缀

#### 调用示例

在当前表创建透视表（自动放置）：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "sourceAddress": "A1:E100"
}
```

指定位置和名称创建透视表：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "sourceAddress": "'销售明细'!A1:F500",
  "tableDestination": "H2",
  "tableName": "销售分析透视表",
  "rowGrand": true,
  "columnGrand": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `sourceAddress` (string, 必填): 数据源地址，如 `A1:E100` 或跨表 `'Sheet1'!A1:E100`；不带 sheet 前缀时默认使用当前工作表
- `tableDestination` (string, 可选): 透视表放置位置（如 `G1`），留空则自动放置
- `tableName` (string, 可选): 透视表名称，留空则自动命名
- `rowGrand` (boolean, 可选): 是否显示行总计，默认 `true`；默认值：`true`
- `columnGrand` (boolean, 可选): 是否显示列总计，默认 `true`；默认值：`true`

**参数要点：**

- `sourceAddress` 支持当前表地址（如 `A1:E100`）和跨表地址（如 `'Sheet1'!A1:E100`）。
- `tableDestination` 仅需左上角单元格地址（如 `G1`），无需写矩形范围。
- `rowGrand` / `columnGrand` 默认都为 `true`，分别控制行总计和列总计展示。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "tableName": "PivotTable1",
    "tableDestination": "G1",
    "index": 1
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |
| `data.tableName` | string | 实际透视表名称（自动命名时返回） |
| `data.tableDestination` | string | 透视表实际放置位置 |
| `data.index` | integer | 透视表索引（若接口返回） |


---

## 12. sheet.merge_range

#### 功能说明

合并指定区域内的单元格。
`across=true` 时按行合并（每行内合并，行与行之间不合并）；默认将整个区域合并为一个单元格。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：建议先用 `sheet.get_range_data` 检查目标区域内容，避免误合并包含关键数据的单元格
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 批量场景建议先在小范围验证 `across` 行为，再应用到大范围区域
> `range` 必须是合法 A1 区域地址；`across=true` 与 `across=false` 的结果不同

#### 调用示例

整块区域合并为一个单元格：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "A1:C3",
  "across": false
}
```

按行合并（每行分别合并）：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "A1:C3",
  "across": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range` (string, 必填): 单元格区域，如 `A1:C3`
- `across` (boolean, 可选): 是否按行合并；`true` 表示每行内合并为一个单元格，`false` 或不传则整个区域合并为一个单元格；默认值：`false`

**参数要点：**

- `range` 使用 A1 地址格式，如 `A1:C3`。
- `across=true` 时会产生多块合并结果（每一行一块）；`across=false` 时仅产生一块整区合并结果。
- 合并后通常以左上角单元格内容作为显示值，其余单元格内容可能被隐藏，建议合并前先核对数据。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |


---

## 13. sheet.range_sort

#### 功能说明

对指定区域进行原地排序，保留格式和公式。
支持最多三个排序字段：`key`、`key2`、`key3`（按优先级依次生效）。
多级排序时 `key` 为主排序键，`key2`/`key3` 为次排序键；排序键值相等的行保持源数据中的相对顺序（稳定排序）。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：先用 `sheet.get_sheets_info` 获取 `rowTo`/`colTo` 确定数据范围，据此构造 `range`（如 `rowTo=10` 则 `A1:F11`），禁止凭直觉猜行数
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 排序为原地操作，会直接改动区域内行顺序
> 排序会保留单元格格式（百分比、日期、数字格式等）和公式
> 若排序后需回滚，建议先备份区域数据或在操作前复制工作表
> `range` 必须是合法 A1 区域；`key2`/`key3` 仅在已传上一级 key 时才有意义

#### 调用示例

单字段升序排序：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "A1:D100",
  "key": "B",
  "order": "asc",
  "header": true,
  "match_case": false
}
```

三字段组合排序：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "A1:F200",
  "key": "2",
  "order": "desc",
  "key2": "D",
  "order2": "asc",
  "key3": "6",
  "order3": "desc",
  "header": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range` (string, 必填): 排序区域，如 `A1:D10`
- `key` (string, 必填): 第一排序字段，列字母（如 `B`）或列号（1-based）
- `order` (string, 可选): 第一字段排序方向，`asc`（默认）或 `desc`。可选值：`asc` / `desc`；默认值：`asc`
- `key2` (string, 可选): 第二排序字段（可选），列字母或列号（1-based）
- `order2` (string, 可选): 第二字段排序方向，`asc` 或 `desc`。可选值：`asc` / `desc`
- `key3` (string, 可选): 第三排序字段（可选），列字母或列号（1-based）
- `order3` (string, 可选): 第三字段排序方向，`asc` 或 `desc`。可选值：`asc` / `desc`
- `header` (boolean, 可选): 首行是否为表头，默认 `true`；默认值：`true`
- `match_case` (boolean, 可选): 是否区分大小写，默认 `false`；默认值：`false`

**参数要点：**

- `key` / `key2` / `key3` 可传列字母（如 `B`）或 1-based 列号（如 `2`）。
- `order` / `order2` / `order3` 只支持 `asc` 和 `desc`。
- 多字段排序按字段顺序生效：先按 `key`，同值再按 `key2`，再按 `key3`。
- `header=true` 时首行不参与排序，只作为表头保留在顶部。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |


---

## 14. sheet.update_pivot_table

#### 功能说明

修改指定透视表的属性或执行透视表操作。
通过 `updateType` 指定操作类型，支持更新数据源、添加字段、刷新、清筛选、设置样式和布局、控制总计显示等。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：建议先用 `sheet.get_pivot_tables` 确认 `tableName` 存在，再执行更新

**幂等性**：否 — 部分操作（如 add_fields、add_data_field、add_calculated_field）重复调用可能产生重复字段，请先确认执行结果

> 涉及 `value` 的操作需确保枚举值合法（如 `row_axis_layout` / `subtotal_location`）

#### 调用示例

修改透视表数据源：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "updateType": "set_source_data",
  "value": "'销售明细'!A1:G500"
}
```

批量添加行列页字段：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "updateType": "add_fields",
  "rowFields": [
    "地区",
    "销售员"
  ],
  "columnFields": [
    "季度"
  ],
  "pageFields": [
    "年份"
  ]
}
```

添加值区域字段并指定汇总函数：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "updateType": "add_data_field",
  "fieldName": "销售额",
  "caption": "销售额合计",
  "function": "sum"
}
```

设置版式并显示行总计：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "updateType": "row_axis_layout",
  "value": "tabular"
}
```

添加计算字段：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "updateType": "add_calculated_field",
  "fieldName": "利润率",
  "formula": "= 利润 / 销售额"
}
```

刷新透视表：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "updateType": "refresh"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `tableName` (string, 必填): 透视表名称，同 `sheet.get_pivot_tables` 返回的 `tableName`
- `updateType` (string, 必填): 操作类型。可选值：`set_source_data` / `add_fields` / `add_data_field` / `refresh` / `clear_all_filters` / `set_table_style` / `row_axis_layout` / `subtotal_location` / `set_grand_total_name` / `set_merge_labels` / `set_row_grand` / `set_column_grand` / `add_calculated_field` / `clear_table`
- `value` (string, 可选): 字符串值，用于 `set_source_data` / `set_table_style` / `row_axis_layout` / `subtotal_location` / `set_grand_total_name`
- `booleanValue` (boolean, 可选): 布尔值，用于 `set_merge_labels` / `set_row_grand` / `set_column_grand`
- `rowFields` (array[string], 可选): 行字段名称列表，用于 `add_fields`
- `columnFields` (array[string], 可选): 列字段名称列表，用于 `add_fields`
- `pageFields` (array[string], 可选): 页字段名称列表，用于 `add_fields`
- `fieldName` (string, 可选): 字段名称，用于 `add_data_field` / `add_calculated_field`
- `caption` (string, 可选): 值区域显示标题，用于 `add_data_field`
- `function` (string, 可选): 汇总函数，用于 `add_data_field`。可选值：`sum` / `count` / `average` / `max` / `min` / `product` / `count_nums` / `stdev` / `var`；默认值：`sum`
- `formula` (string, 可选): 公式表达式，用于 `add_calculated_field`，如 `= 利润 / 销售额`

**参数要点：**

- `tableName` 建议先通过 `sheet.get_pivot_tables` 获取，避免名称不匹配导致更新失败。
- `updateType=add_fields` 时，至少传一个字段列表：`rowFields` / `columnFields` / `pageFields`。
- `updateType=add_data_field` 时，`fieldName` 必填，`function` 不传默认 `sum`。
- `updateType=add_calculated_field` 时，`fieldName` 与 `formula` 必填，`formula` 建议以 `=` 开头。
- `updateType=row_axis_layout` 仅建议使用 `compact` / `tabular` / `outline`。
- `updateType=subtotal_location` 仅建议使用 `top` / `bottom`。
- `updateType` 与必填参数映射：
  - `set_source_data` -> `value`
  - `add_fields` -> `rowFields` / `columnFields` / `pageFields`（至少一个）
  - `add_data_field` -> `fieldName`（可选 `caption` / `function`）
  - `refresh` -> 无附加参数
  - `clear_all_filters` -> 无附加参数
  - `set_table_style` -> `value`
  - `row_axis_layout` -> `value`
  - `subtotal_location` -> `value`
  - `set_grand_total_name` -> `value`
  - `set_merge_labels` -> `booleanValue`
  - `set_row_grand` -> `booleanValue`
  - `set_column_grand` -> `booleanValue`
  - `add_calculated_field` -> `fieldName` + `formula`
  - `clear_table` -> 无附加参数

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "tableName": "销售分析透视表",
    "updateType": "refresh"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |
| `data.tableName` | string | 透视表名称 |
| `data.updateType` | string | 本次执行的操作类型 |


---

## 15. sheet.update_pivot_field

#### 功能说明

修改指定透视表中的字段属性，或执行字段级操作。
通过 `updateType` 指定动作，支持设置字段方向、位置、汇总函数、标题、数字格式、排序、筛选清理、删除字段和数据项显隐控制。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：建议先用 `sheet.get_pivot_tables` 确认 `tableName` 存在，再执行字段级更新
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：否 — 字段方向调整、删除字段、显隐设置重复调用可能改变透视结构，重试前建议先确认当前状态

> `clear_label_filters` 与 `clear_value_filters` 只影响对应筛选类型，不会删除字段本身
> 调整 `set_orientation` 或 `set_position` 后，透视布局可能立即变化，建议在批量操作前先确认展示要求
> `delete` 会移除字段；其中 data 字段删除后会自动改用 Orientation=0，请谨慎执行

#### 调用示例

设置字段方向为行字段：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "fieldName": "地区",
  "updateType": "set_orientation",
  "value": "row"
}
```

设置数据字段汇总函数：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "fieldName": "销售额",
  "updateType": "set_function",
  "value": "sum"
}
```

按指定字段降序排序：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "fieldName": "地区",
  "updateType": "auto_sort",
  "order": "descending",
  "sortFieldName": "销售额"
}
```

设置数据项可见性：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "fieldName": "地区",
  "updateType": "set_item_visible",
  "itemName": "华东",
  "booleanValue": false
}
```

清除字段全部筛选：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "fieldName": "地区",
  "updateType": "clear_all_filters"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `tableName` (string, 必填): 透视表名称，同 `sheet.get_pivot_tables` 返回的 `tableName`
- `fieldName` (string, 必填): 字段名称
- `updateType` (string, 必填): 操作类型。可选值：`set_orientation` / `set_position` / `set_function` / `set_caption` / `set_number_format` / `auto_sort` / `clear_all_filters` / `clear_label_filters` / `clear_value_filters` / `delete` / `set_item_visible`
- `value` (string, 可选): 字符串值，用于 `set_orientation` / `set_function` / `set_caption` / `set_number_format` / `set_position`
- `order` (string, 可选): 排序方式，用于 `auto_sort`。可选值：`ascending` / `descending`
- `sortFieldName` (string, 可选): 排序依据字段名称，用于 `auto_sort`
- `itemName` (string, 可选): 数据项名称，用于 `set_item_visible`
- `booleanValue` (boolean, 可选): 布尔值，用于 `set_item_visible`

**参数要点：**

- `tableName` 建议先用 `sheet.get_pivot_tables` 查询确认；`fieldName` 需与透视字段名称一致。
- `set_orientation` 的 `value` 建议使用：`hidden` / `row` / `column` / `page` / `data`。
- `set_position` 的 `value` 需为正整数（字符串形式传参，如 `"1"`）。
- `set_function` 的 `value` 建议使用：`sum` / `count` / `average` / `max` / `min` / `product` / `count_nums` / `stdev` / `var`。
- `auto_sort` 时，`order` 与 `sortFieldName` 建议同时传入，`order` 仅支持 `ascending` / `descending`。
- `set_item_visible` 时，`itemName` 与 `booleanValue` 都是必填。
- `updateType` 与必填参数映射：
  - `set_orientation` -> `value`
  - `set_position` -> `value`
  - `set_function` -> `value`
  - `set_caption` -> `value`
  - `set_number_format` -> `value`
  - `auto_sort` -> `order` + `sortFieldName`
  - `clear_all_filters` -> 无附加参数
  - `clear_label_filters` -> 无附加参数
  - `clear_value_filters` -> 无附加参数
  - `delete` -> 无附加参数
  - `set_item_visible` -> `itemName` + `booleanValue`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "tableName": "销售分析透视表",
    "fieldName": "销售额",
    "updateType": "set_function"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |
| `data.tableName` | string | 透视表名称 |
| `data.fieldName` | string | 字段名称 |
| `data.updateType` | string | 本次执行的操作类型 |


---

## 16. sheet.delete_pivot_table

#### 功能说明

删除指定工作表中的整个数据透视表。
该操作会清除透视表占据的全部区域，且不可恢复。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：建议先用 `sheet.get_pivot_tables` 确认 `tableName` 存在，并核对是否为目标透视表
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。
- **用户确认**：删除整个透视表会清除占据区域，操作不可恢复

**幂等性**：否 — 删除成功后再次调用通常会报不存在；重试前先确认透视表是否仍存在

> 当同名透视表不存在时，接口可能返回错误信息；建议删除前先做存在性检查

#### 调用示例

删除指定透视表：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `tableName` (string, 必填): 透视表名称，同 `sheet.get_pivot_tables` 返回的 `tableName`

**参数要点：**

- `tableName` 建议先通过 `sheet.get_pivot_tables` 获取，避免名称不匹配导致误操作或删除失败。
- 删除后透视表及其占用区域会被清空，不会自动保留字段布局或计算设置。
- 如需保留分析逻辑，建议先记录透视表配置（字段方向、聚合方式、筛选条件）后再删除。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "tableName": "销售分析透视表"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |
| `data.tableName` | string | 被删除的透视表名称 |


---

## 17. sheet.get_pivot_tables

#### 功能说明

获取工作表中的数据透视表信息，并按参数逐层下钻：
- 不传 `tableName`：返回当前工作表中所有透视表概览（名称、位置、区域、行列总计设置）
- 传 `tableName` 且不传 `fieldName`：返回该透视表所有字段信息（可用于 `sheet.update_pivot_field`）
- 同时传 `tableName` + `fieldName`：返回该字段下所有数据项（名称、可见性、位置）
其中 `category` 仅在已传 `tableName` 且未传 `fieldName`的情况下生效，可用于按字段类别筛选。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 三层下钻优先级：`tableName` > `fieldName`；仅传 `fieldName` 无意义，需先传 `tableName`
> 透视表字段有两个名字：`sourceName`（源数据列原始列名，不可改）和 `caption`（透视表显示标题，可重命名）
> JSAPI 脚本内部按 `sourceName` 匹配字段；若传入 `caption`（显示标题），会匹配失败并报错
> 示例：若将 `销售额` 的 `caption` 改为 `Sales`，后续操作仍必须传 `fieldName="销售额"`，传 `fieldName="Sales"` 会失败
> `category` 仅在字段层生效（`tableName` 非空且 `fieldName` 为空），传入其他场景通常会被忽略
> 建议先查第一层确认 `tableName`，再查第二层确认 `fieldName`，最后按需进入第三层读取数据项
> 字段层返回的 `fieldName` 可直接作为 `sheet.update_pivot_field` 的输入
> 当 `tableName` 或 `fieldName` 不存在时，接口可能返回空列表或错误信息，建议先用上层结果校验名称
> 字段类别常见为 `row` / `column` / `data` / `page`，实际返回以接口响应为准
> 建议按透视表 -> 字段 -> 数据项顺序逐层查询，避免因名称不匹配导致空结果

#### 调用示例

查询工作表内所有透视表概览：

```json
{
  "file_id": "string",
  "worksheet_id": 3
}
```

查询指定透视表的全部字段：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表"
}
```

查询指定透视表的行字段：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "category": "row"
}
```

查询指定字段下的数据项：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "tableName": "销售分析透视表",
  "fieldName": "地区"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `tableName` (string, 可选): 透视表名称；不传则返回透视表列表，传则进入字段或数据项层级
- `fieldName` (string, 可选): 字段名称（必须传字段的 sourceName，而非 caption）；传 `tableName` 后再传 `fieldName` 则返回该字段的数据项
- `category` (string, 可选): 字段类别筛选（仅 `tableName` 非空且 `fieldName` 为空时生效），留空返回全部字段。可选值：`row` / `column` / `data` / `page`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "tableName": "销售分析透视表",
    "fieldName": "地区",
    "category": "row",
    "items": [
      {
        "name": "华东",
        "visible": true,
        "position": 1
      },
      {
        "name": "华北",
        "visible": true,
        "position": 2
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |
| `data.tableName` | string | 透视表名称（字段层或数据项层通常返回） |
| `data.fieldName` | string | 字段名称（数据项层通常返回） |
| `data.category` | string | 字段类别（row / column / data / page） |
| `data.items` | array[object] | 数据项列表（第三层查询时返回） |


---

## 18. sheet.auto_fit

#### 功能说明

对指定区域执行自适应列宽或行高。
`fit_type=columns` 表示自适应列宽，`fit_type=rows` 表示自适应行高，`fit_type=auto`（默认）会自动识别：整行区域适应行高，其他区域适应列宽。
自适应后列宽上限为 `60`。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：建议先确认 `range` 是否覆盖目标区域，避免误调整到不相关行列
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 本操作不会修改单元格值，只调整展示尺寸（列宽或行高）
> 列宽自适应存在上限 60；超长文本可能仍显示截断，可配合自动换行处理

#### 调用示例

指定区域自适应列宽：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "A1:H10",
  "fit_type": "columns"
}
```

指定行区间自适应行高：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "1:10",
  "fit_type": "rows"
}
```

自动识别自适应类型：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "A:D",
  "fit_type": "auto"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range` (string, 必填): 单元格区域，如 `A1:H10`（列宽）、`1:10`（行高）、`A:D`（列宽）
- `fit_type` (string, 可选): 自适应类型。可选值：`columns` / `rows` / `auto`；默认值：`auto`

**参数要点：**

- `range` 需为合法地址；常见格式：矩形区域（`A1:H10`）、整行区域（`1:10`）、整列区域（`A:D`）。
- `fit_type=auto` 时：整行区域优先适应行高，其他区域适应列宽。
- 当目标为列宽自适应时，结果列宽最大不会超过 `60`。
- 若未传 `fit_type`，默认按 `auto` 处理。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |


---

## 19. sheet.get_typed_value

#### 功能说明

读取指定区域数据，返回每个单元格的 `type` 和 `value`。
`type` 可能为：`double`（数值）、`date`（日期）、`string`（文本）、空字符串（空单元格）。
与 `sheet.get_range_data` 不同，本工具保留单元格类型信息，便于进行类型敏感的数据处理（如数值计算或日期识别）。
本工具适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 空单元格通常表现为 `type` 为空字符串，`value` 也可能为空字符串
> 若后续要写回数据，可将解析后的结构配合 `sheet.range_data_batch_update` 使用

#### 调用示例

读取单列并保留类型：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "B2:B10"
}
```

读取二维区域并保留类型：

```json
{
  "file_id": "string",
  "worksheet_id": 3,
  "range": "A1:D20"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range` (string, 必填): 单元格区域，如 `B2:B10`

**参数要点：**

- `range` 需为合法 A1 区域地址（如 `B2:B10`、`A1:D20`）。
- `type` 字段用于区分值语义：`double`（数值）、`date`（日期）、`string`（文本）、空字符串（空单元格）。
- 与 `sheet.get_range_data` 的差异：本工具重点返回“类型 + 值”，而不是展示格式、公式栏值、图片元信息等。
- 进行汇总或计算前，建议先按 `type=double` 过滤，避免把文本或空值误算为数值。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string",
  "data": {
    "values": [
      [
        { "type": "string", "value": "日期" },
        { "type": "string", "value": "金额" }
      ],
      [
        { "type": "date", "value": "2026-06-01" },
        { "type": "double", "value": 1280.5 }
      ],
      [
        { "type": "", "value": "" },
        { "type": "string", "value": "待确认" }
      ]
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 人可阅读的文本信息，可能按不同语言或地区返回不同文本 |
| `data.values` | array[array[object]] | 二维数组（按行列顺序），每个单元格包含 `type` 与 `value` |


---

## 20. sheet.update_range_data

#### 功能说明

批量更新单元格选区数据，支持写值/公式、设置格式、合并单元格、写入图片。

#### 工具选择

- **适用**：兜底：`sheet.range_data_batch_update` 不可用或写入失败时
- **勿用**（改用 `sheet.range_data_batch_update`）：需要批量更新单元格选区（写值/公式、格式、合并、图片）

#### 调用约束

- **前置检查**：调用 sheet.get_range_data 读取目标区域现有数据，确认覆盖范围
- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 每项必须包含 `opType`（仅 `formula`/`format`/`merge`/`picture`）和四个坐标字段（`rowFrom`/`rowTo`/`colFrom`/`colTo`）；`rangeData` 必须为对象数组，即使单个单元格也不可传单个对象
> 参数名使用 camelCase（如 `opType`、`rowFrom`、`alcH`、`cellPicInfo`）
> merge 操作的 `type` 使用 `MergeCenter`、`MergeContent`、`MergeSame`、`MergeColumns`
> picture 操作的 `cellPicInfo.tag` 使用 `local` / `attachment` / `url`，并按 tag 传 `uploadId` / `attachmentId` / `url`
> 该工具暂不支持写入在线图片，请使用 `sheet.range_data_batch_update` 工具。
> **改日期/数字显示格式属于 format 操作**：用 `opType=format` + `xf.numfmt`（如 `yyyy-mm-dd`、`0.00%`），**不要用 `opType=formula` 重写格式化字符串**——写入的字符串会被引擎按原有格式重新渲染，显示效果不变。
> **日期单元格的值和格式是两层**：值层是内部数值（如 44961），格式层控制显示（`yyyy/m/d` vs `yyyy-mm-dd`）。改显示只改格式层即可，值层无需动。
> **`formula` 值以 `+`/`-`/`=` 开头会被当作公式解析**：写字面文本（如 `+86 手机号`）会报 Internal error，须前置 `'` 强制文本（如 `'+86 138…`），存储时引号不会带入。

#### 调用示例

写入值/公式：

```json
{
  "file_id": "VsdfG0001234567",
  "worksheet_id": 3,
  "rangeData": [
    {
      "opType": "formula",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 0,
      "colTo": 0,
      "formula": "Hello"
    }
  ]
}
```

设置格式（加粗、居中、背景色）：

```json
{
  "file_id": "VsdfG0001234567",
  "worksheet_id": 3,
  "rangeData": [
    {
      "opType": "format",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 0,
      "colTo": 5,
      "xf": {
        "font": {
          "name": "微软雅黑",
          "dyHeight": 220,
          "bls": true,
          "color": {
            "type": 2,
            "value": 16777215
          }
        },
        "alcH": 2,
        "alcV": 1,
        "wrap": true,
        "fill": {
          "type": 1,
          "back": {
            "type": 2,
            "value": 4294901760
          },
          "fore": {
            "type": 255,
            "value": 0,
            "tint": 0
          }
        }
      }
    }
  ]
}
```

合并单元格：

```json
{
  "file_id": "VsdfG0001234567",
  "worksheet_id": 3,
  "rangeData": [
    {
      "opType": "merge",
      "rowFrom": 2,
      "rowTo": 3,
      "colFrom": 0,
      "colTo": 3,
      "type": "MergeCenter"
    }
  ]
}
```

写入在线图片：

```json
{
  "file_id": "VsdfG0001234567",
  "worksheet_id": 3,
  "rangeData": [
    {
      "opType": "picture",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 1,
      "colTo": 1,
      "cellPicInfo": {
        "tag": "url",
        "url": "https://example.com/image.png",
        "width": 200,
        "height": 150
      }
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `rangeData` (array[object], 必填): ⚠️ 单元格操作数组（必填，不可传单个对象），每项必须包含 `opType` 和坐标字段，详见 param_detail

**rangeData 每项字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `opType` | string | 是 | 操作类型（枚举值见下表） |
| `rowFrom` | integer | 是 | 起始行（0-based） |
| `rowTo` | integer | 是 | 结束行 |
| `colFrom` | integer | 是 | 起始列（0-based） |
| `colTo` | integer | 是 | 结束列 |
| `formula` | string | 否 | 单元格公式或内容（`opType=formula` 时使用） |
| `xf` | object | 否 | 格式对象（`opType=format` 时使用，见下方 xf 说明） |
| `type` | string | 否 | 合并类型（`opType=merge` 时使用） |
| `cellPicInfo` | object | 否 | 图片信息（`opType=picture` 时使用） |

---

**opType 枚举值：**

| 枚举值 | 说明 | 需要的额外字段 |
|--------|------|--------------|
| `formula` | 写值/公式 | `formula` |
| `format` | 设置格式 | `xf` |
| `merge` | 合并单元格 | `type` |
| `picture` | 写入图片 | `cellPicInfo` |

---

**type 枚举值（opType = merge）：**

| 枚举值 | 说明 |
|--------|------|
| `MergeCenter` | 合并居中 |
| `MergeContent` | 内容合并 |
| `MergeSame` | 相同内容合并 |
| `MergeColumns` | 按列合并 |

---

**cellPicInfo 字段（opType = picture）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `width` | integer | 是 | 图片宽度；`-1` 表示自适应 |
| `height` | integer | 是 | 图片高度；`-1` 表示自适应 |
| `tag` | string | 是 | 图片来源：`local` / `attachment` / `url` 三选一 |
| `uploadId` | string | 否 | 本地文件（`tag=local`）时必填 |
| `attachmentId` | string | 否 | 附件（`tag=attachment`）时必填 |
| `url` | string | 否 | 在线 URL（`tag=url`）时必填 |

---

**xf 字段（opType = format）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `alcH` | integer | 否 | 水平对齐：1=左，2=居中，3=右，4=填充，5=两端，6=跨列，7=分散 |
| `alcV` | integer | 否 | 垂直对齐：0=上，1=中，2=下，3=两端，4=分散 |
| `wrap` | boolean | 否 | 自动换行 |
| `shrinkToFit` | boolean | 否 | 缩小字体填充 |
| `locked` | boolean | 否 | 锁定单元格 |
| `hidden` | boolean | 否 | 隐藏公式 |
| `indent` | integer | 否 | 缩进 |
| `readingOrder` | integer | 否 | 文字方向 |
| `trot` | integer | 否 | 文字旋转角度 |
| `numfmt` | string | 否 | 数字格式串，如 `"G/通用格式"`、`"yyyy-mm-dd"`、`"0.00%"` |
| `mask_cats` | integer | 否 | 掩码 |
| `mask_catsFont` | integer | 否 | 掩码字体 |
| `font` | object | 否 | 字体，见下方 font 字段表 |
| `fill` | object | 否 | 填充，见下方 fill 字段表 |
| `dgLeft` | integer | 否 | 左边框线型 |
| `dgRight` | integer | 否 | 右边框线型 |
| `dgTop` | integer | 否 | 上边框线型 |
| `dgBottom` | integer | 否 | 下边框线型 |
| `dgDiagDown` | integer | 否 | 向下斜线边框线型 |
| `dgDiagUp` | integer | 否 | 向上斜线边框线型 |
| `dgInsideHorz` | integer | 否 | 内框横线线型 |
| `dgInsideVert` | integer | 否 | 内框竖线线型 |
| `clrLeft` | object | 否 | 左边框颜色（颜色对象，见下方颜色说明） |
| `clrRight` | object | 否 | 右边框颜色 |
| `clrTop` | object | 否 | 上边框颜色 |
| `clrBottom` | object | 否 | 下边框颜色 |
| `clrDiagDown` | object | 否 | 向下斜线边框颜色 |
| `clrDiagUp` | object | 否 | 向上斜线边框颜色 |
| `clrInsideHorz` | object | 否 | 内框横线颜色 |
| `clrInsideVert` | object | 否 | 内框竖线颜色 |

边框线型枚举：0=无，1=细线，2=中等，3=虚线，4=点线，5=粗线，6=双线，7=细虚线

**xf.font 字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 否 | 字体名称，如 `"微软雅黑"` |
| `dyHeight` | integer | 否 | 字体高度（单位 Twip，1pt=20Twip，如 11pt=220） |
| `charSet` | integer | 否 | 字符集 |
| `bls` | boolean | 否 | 粗体 |
| `italic` | boolean | 否 | 斜体 |
| `strikeout` | boolean | 否 | 删除线 |
| `uls` | integer | 否 | 下划线类型 |
| `sss` | integer | 否 | 上下标类型 |
| `themeFont` | integer | 否 | 字体类型 |
| `color` | object | 否 | 字体颜色（颜色对象，见下方颜色说明）。**不确定颜色值时不传此字段**，禁止用占位符 |

**xf.fill 字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | integer | 是 | 填充类型 |
| `back` | object | 是 | 背景色（颜色对象） |
| `fore` | object | 是 | 前景色（颜色对象） |

**颜色对象（color / clr_* / fill.back / fill.fore）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | integer | 是 | 颜色类型：0=ICV，1=THEME 主题色，2=ARGB，254=无颜色（背景透明），255=自动色（字体/边框默认） |
| `value` | integer | 是 | ARGB 整数值（type=2 时有效）。十进制 = 十六进制 ARGB 转十进制整数，如纯红 `0xFFFF0000` → `int(0xFFFF0000)` = `4294901760` |
| `tint` | integer | 是 | 透明度，调节颜色深浅 |

#### 返回值说明

```json
{
  "code": 0,
  "msg": ""
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功，非 0 表示失败 |
| `msg` | string | 错误描述，code 非 0 时返回失败原因 |


---

## 21. sheet.insert_rows_cols

#### 功能说明

在指定工作表中插入行或列。type=row 时需传 row_from/row_to，type=col 时需传 col_from/col_to。
适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：否 — 重复调用会插入多行/多列，先确认是否已成功

> 行列索引均为 0-based

#### 调用示例

插入行：

```json
{
  "file_id": "string",
  "worksheet_id": 1,
  "type": "row",
  "row_from": 3,
  "row_to": 5
}
```

插入列：

```json
{
  "file_id": "string",
  "worksheet_id": 1,
  "type": "col",
  "col_from": 2,
  "col_to": 4
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `type` (string, 必填): 插入类型。可选值：`row` / `col`
- `row_from` (integer, 可选): 插入起始行索引（type=row 时必填，0-based）
- `row_to` (integer, 可选): 插入结束行索引（type=row 时必填）
- `col_from` (integer, 可选): 插入起始列索引（type=col 时必填，0-based）
- `col_to` (integer, 可选): 插入结束列索引（type=col 时必填）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 错误描述，code 非 0 时返回失败原因 |


---

## 22. sheet.set_range_width_height

#### 功能说明

调整指定区域的行高和列宽。width 和 height 至少传一个，单位 twip（twip = pixel × 1440 / dpi）。
适用于 Excel（.xlsx）和智能表格（.ksheet）。

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_sheets_info确认要操作的工作表id，不得自行捏造工作表id。

**幂等性**：是

> 行列索引均为 0-based
> 单位换算：twip = pixel × 1440 / dpi

#### 调用示例

设置列宽和行高：

```json
{
  "file_id": "string",
  "worksheet_id": 1,
  "range": {
    "row_from": 0,
    "row_to": 1,
    "col_from": 0,
    "col_to": 1
  },
  "width": 3000,
  "height": 4000
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `worksheet_id` (integer, 必填): 工作表 ID
- `range` (object, 必填): 调整范围
- `width` (integer, 可选): 列宽（twip），须 > 0
- `height` (integer, 可选): 行高（twip），须 > 0

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应码 |
| `msg` | string | 错误描述，code 非 0 时返回失败原因 |

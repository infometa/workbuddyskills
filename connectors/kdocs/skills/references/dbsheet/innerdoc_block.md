# 智能文档/富文本字段块操作

## 1. dbsheet.create_innerdoc_flexpaper

#### 功能说明

在多维表格文件中新建一个智能文档（FlexPaper sheet）。返回包含 sheet_id、name、content_id 的新智能文档信息,content_id可用于innerdoc_*工具使用。
after_sheet_id 与 before_sheet_id 互斥，仅可传一个；不指定则默认在最后添加。

**幂等性**：否 — 重复调用会创建多个智能文档，先确认是否已成功

> 新建后可通过 get_schema_detail 查看智能文档的 content_id，再配合 innerdoc_block_* 系列工具读写其内容
> after_sheet_id 与 before_sheet_id 互斥，同时传入会报错

#### 调用示例

新建智能文档（默认追加到末尾）：

```json
{
  "file_id": "100264623255",
  "name": "测试文档"
}
```

在指定 sheet 之后创建：

```json
{
  "file_id": "100264623255",
  "name": "测试文档",
  "after_sheet_id": 2
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格文件 ID
- `name` (string, 必填): 智能文档名称
- `after_sheet_id` (integer, 可选): 在指定 sheet 后面创建，不指定默认在最后添加
- `before_sheet_id` (integer, 可选): 在指定 sheet 前面创建，不指定默认在最后添加

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "sheet_id": 4,
    "name": "测试文档",
    "obj_id": 2598866448,
    "content_id": "6QAI3URIAAADA"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 新建智能文档信息，含 sheet_id、name、content_id |


---

## 2. dbsheet.innerdoc_block_create

#### 功能说明

在指定 AP 附件（侧边栏智能文档，或富文本字段 Note 对应的附件文档）内创建文档块。请求体 `arg` 为创建块参数 JSON 对象。

**幂等性**：否 — 重复调用会重复创建块，先确认是否已成功

> `arg` 须为 JSON 对象（不接受数组）；各子字段约束见参数说明
> ⚠️ 写入富文本字段（Note）后，必须调用 `update_records` 同步该字段的 `summary`，否则表格视图中单元格不会刷新显示。侧边栏智能文档不需要同步 summary

#### 调用示例

在富文本附件内创建文档块：

```json
{
  "file_id": "100261008755",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": {
    "blockId": "doc",
    "index": 1,
    "content": [
      {
        "type": "paragraph",
        "content": [
          {
            "type": "text",
            "content": "Hello World"
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
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格主文档 file_id
- `attachment_id` (string, 必填): AP 附件 ID。侧边栏智能文档：取自 `dbsheet.get_schema_detail` 返回该 sheet 的 `content_id`（新建可用 `dbsheet.create_innerdoc_flexpaper`，其返回的 `content_id` 即 attachment_id）；富文本字段（Note 类型）：取自 `dbsheet.list_records` 返回的该字段值中的 `fileId`
- `arg` (object, 必填): 创建块参数 JSON 对象，须同时含 `blockId` / `index` / `content` 三个字段（`blockId` 固定为 `"doc"`，`index` 从 1 开始，`content` 为非空块数组）
  - `blockId` (string, 必填): 必须为 `"doc"`（文档根块，大小写敏感）；传其它值会被拒绝（实测 `arg.blockId 必须为 "doc"（文档根块），大小写敏感，不可使用其他值`）
  - `index` (integer, 必填): 插入位置，从 1 开始；title 块下标 0 不可创建（实测 `arg.index 须为不小于 1 的数字（0 为标题位，不可创建）`）
  - `content` (array[object], 必填): 块内容数组，非空；每项为块对象：
    - `type` (string, 必填): 块类型，仅支持 `paragraph` / `heading`（实测传 `list` 报 `arg.content[0] 的 type="list" 不支持，仅支持 paragraph 和 heading`）
    - `content` (array[object], 必填): 块内行内容，如 `{ "type": "text", "content": "Hello World" }`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 操作结果（base64 编码的 JSON，需解码后查看） |


---

## 3. dbsheet.innerdoc_block_query

#### 功能说明

根据 block_id 获取单个文档块内容。请求体 `arg` 为查询参数 JSON 对象。

**幂等性**：是

> `arg` 传入 JSON 对象即可
> index 为 0-based 数组下标，title 块下标为 0

#### 调用示例

查询指定块内容：

```json
{
  "file_id": "100261008755",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": {
    "blockIds": [
      "doc"
    ]
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格主文档 file_id
- `attachment_id` (string, 必填): 侧边栏智能文档或富文本字段的 attachment_id。侧边栏智能文档取自 `get_schema_detail` 返回的 `content_id`；富文本字段（Note 类型）取自 `list_records` 返回的该字段值中的 `fileId`
- `arg` (object, 必填): `arg` 传入 JSON 对象即可。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 查询结果（base64 编码的 JSON，需解码后查看） |


---

## 4. dbsheet.innerdoc_block_list

#### 功能说明

批量获取文档块列表。请求体 `arg` 为批量查询参数 JSON 对象。

**幂等性**：是

> `arg` 传入 JSON 对象即可
> index 为 0-based 数组下标，title 块下标为 0

#### 调用示例

查询指定块：

```json
{
  "file_id": "100265499039",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": {
    "type": "doc",
    "blockIds": [
      "goRBQVwVWlmP",
      "ZNcSqRriGtKV"
    ]
  }
}
```

查询指定块：

```json
{
  "file_id": "100261008755",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": {
    "type": "doc",
    "blockIds": [
      "goRBQVwVWlmP",
      "ZNcSqRriGtKV"
    ]
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格主文档 file_id
- `attachment_id` (string, 必填): 侧边栏智能文档或富文本字段的 attachment_id。侧边栏智能文档取自 `get_schema_detail` 返回的 `content_id`；富文本字段（Note 类型）取自 `list_records` 返回的该字段值中的 `fileId`
- `arg` (object, 必填): 须含 `type`（`"doc"`）与 `blockIds` 数组。两种用法：`["doc"]` 返回全部子块；传具体 block ID 列表（如 `["goRBQVwVWlmP","ZNcSqRriGtKV"]`）只返回指定块。不可传空对象 `{}`。`arg` 传入 JSON 对象即可。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 批量查询结果（base64 编码的 JSON，需解码后查看） |


---

## 5. dbsheet.innerdoc_block_update

#### 功能说明

根据 `blockId` 更新文档块：`blockId` 为具体块 ID 时更新该块，为 `"doc"` 时替换整个文档内容。请求体 `arg` 为更新参数 JSON 对象。

**幂等性**：否 — 更新操作不可回滚，建议先查询确认当前内容

> `arg` 须为 JSON 对象（不接受数组）
> ⚠️ 更新富文本字段（Note）后，必须调用 `update_records` 同步该字段的 `summary`，否则表格视图中单元格不会刷新显示。侧边栏智能文档不需要同步 summary

#### 调用示例

更新指定块内容：

```json
{
  "file_id": "100261008755",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": {
    "operation": "update_content",
    "blockId": "blk_abc",
    "content": [
      {
        "type": "text",
        "content": "更新后的文本内容"
      }
    ]
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格主文档 file_id
- `attachment_id` (string, 必填): AP 附件 ID。侧边栏智能文档：取自 `dbsheet.get_schema_detail` 返回该 sheet 的 `content_id`（新建可用 `dbsheet.create_innerdoc_flexpaper`，其返回的 `content_id` 即 attachment_id）；富文本字段（Note 类型）：取自 `dbsheet.list_records` 返回的该字段值中的 `fileId`
- `arg` (object, 必填): 更新参数 JSON 对象，须同时含 `operation` 与 `blockId`（其余字段由 `operation` 决定）
  - `operation` (string, 必填): 操作类型，支持 `update_content`（更新块内容）与 `update_attrs`（更新块属性）；传其它值会被拒绝（网关定义为内核返回 `invalid operation`，**实测返回 `400100 kernel response error`**；取值**未完整枚举**）
  - `blockId` (string, 必填): 目标块 ID；传 `"doc"` 表示**替换整个文档内容**，此时 `content` 必须包含 title 块，否则内核报 invalid content: title is required when replacing doc content
  - `content` (array[object], `operation=update_content` 时必填): 更新后的块内容数组，如 `[{ "type": "text", "content": "更新后的文本内容" }]`；不传会被拒绝（实测 400100 kernel response error）
  - `attrs` (object, 可选): `operation=update_attrs` 时的块属性对象（与 `otl.block_update` 同名同义），如 `{ "align": 2 }`（居中）。**键名必须为 `attrs`**：实测写成 `content_attr` 等其它名字仍返回成功但属性不变（静默失效），`attrs` 内的未知属性名同样被静默忽略；不传则等同空操作（实测返回成功）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 操作结果（base64 编码的 JSON，需解码后查看） |


---

## 6. dbsheet.innerdoc_block_batch_update

#### 功能说明

批量更新多个文档块。请求体 `arg` 为批量更新操作 JSON 对象。

**幂等性**：否 — 批量更新不可回滚，建议先查询确认当前内容

> `arg` 传入 JSON 对象即可
> index 为 0-based 数组下标，title 块下标为 0
> ⚠️ 更新富文本字段（Note）后，必须调用 `update_records` 同步该字段的 `summary`，否则表格视图中单元格不会刷新显示。侧边栏智能文档不需要同步 summary

#### 调用示例

批量更新多个块：

```json
{
  "file_id": "100261008755",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": [
    {
      "operation": "update_content",
      "blockId": "blk_abc",
      "content": [
        {
          "type": "text",
          "content": "第一段更新内容"
        }
      ]
    },
    {
      "operation": "update_attrs",
      "blockId": "CdTssYG8yB",
      "attrs": {
        "align": 1
      }
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格主文档 file_id
- `attachment_id` (string, 必填): 侧边栏智能文档或富文本字段的 attachment_id。侧边栏智能文档取自 `get_schema_detail` 返回的 `content_id`；富文本字段（Note 类型）取自 `list_records` 返回的该字段值中的 `fileId`
- `arg` (array, 必填): `arg` 传入 JSON 对象即可。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 操作结果（base64 编码的 JSON，需解码后查看） |


---

## 7. dbsheet.innerdoc_block_delete

#### 功能说明

根据 block_id 删除单个文档块。请求体 `arg` 为删除参数 JSON 对象。

#### 调用约束

- **前置检查**：删除不可恢复，请确认 blockId 正确且确实需要删除

**幂等性**：是

> `arg` 传入 JSON 对象即可
> index 为 0-based 数组下标，title 块下标为 0
> ⚠️ 删除富文本字段（Note）的块后，必须调用 `update_records` 同步该字段的 `summary`，否则表格视图中单元格不会刷新显示。侧边栏智能文档不需要同步 summary

#### 调用示例

删除指定块：

```json
{
  "file_id": "100261008755",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": {
    "blockId": "doc",
    "startIndex": 1,
    "endIndex": 2
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格主文档 file_id
- `attachment_id` (string, 必填): 侧边栏智能文档或富文本字段的 attachment_id。侧边栏智能文档取自 `get_schema_detail` 返回的 `content_id`；富文本字段（Note 类型）取自 `list_records` 返回的该字段值中的 `fileId`
- `arg` (object, 必填): `arg` 传入 JSON 对象即可。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 操作结果（base64 编码的 JSON，需解码后查看） |


---

## 8. dbsheet.innerdoc_block_batch_delete

#### 功能说明

批量删除多个文档块。请求体 `arg` 为批量删除操作 JSON 对象。
响应含 `success_list`（成功删除的 block 结果）与 `fail_list`（删除失败的 block 结果）。

#### 调用约束

- **前置检查**：批量删除不可恢复，请确认 blockIds 列表正确且确实需要删除

**幂等性**：是

> `arg` 传入 JSON 对象即可
> 响应中 `success_list` 和 `fail_list` 为 base64 编码的 JSON，需解码后查看
> index 为 0-based 数组下标，title 块下标为 0
> ⚠️ 删除富文本字段（Note）的块后，必须调用 `update_records` 同步该字段的 `summary`，否则表格视图中单元格不会刷新显示。侧边栏智能文档不需要同步 summary

#### 调用示例

批量删除多个块：

```json
{
  "file_id": "100261008755",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": [
    {
      "blockId": "doc",
      "startIndex": 2,
      "endIndex": 3
    },
    {
      "blockId": "doc",
      "startIndex": 3,
      "endIndex": 4
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格主文档 file_id
- `attachment_id` (string, 必填): 侧边栏智能文档或富文本字段的 attachment_id。侧边栏智能文档取自 `get_schema_detail` 返回的 `content_id`；富文本字段（Note 类型）取自 `list_records` 返回的该字段值中的 `fileId`
- `arg` (array, 必填): `arg` 传入 JSON 对象即可。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 操作结果，含 success_list 和 fail_list（均为 base64 编码的 JSON） |


---

## 9. dbsheet.innerdoc_block_convert

#### 功能说明

将 Markdown 或 HTML 文本转换为块结构，仅负责"内容转块"，不会直接将块插入文档。
适合在正式插入前先生成块内容。

将内容插入文档的完整流程：
1. 调用本接口，将源内容转换为块数据
2. 若 convert 响应的 data 中包含 attachments 列表，需先将其中 uri 对应资源通过 `upload_attachment` 上传，
   拿到附件 id 后替换对应块 binding 指定属性中的占位值
3. 调用 `innerdoc_block_create` 或 `innerdoc_block_update` 将处理后的块数据插入目标文档

当源内容包含图片等附件资源时，必须先完成附件上传与 binding 替换再执行创建/更新块，
否则文档中的附件引用会失效或无法正常渲染。

**幂等性**：是

> `arg` 传入 JSON 对象即可
> index 为 0-based 数组下标，title 块下标为 0

#### 调用示例

将 Markdown 转换为文档块：

```json
{
  "file_id": "100261008755",
  "attachment_id": "TKQEY6ZIABQAM",
  "arg": {
    "format": "markdown",
    "content": "这是一段 Markdown 文本"
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 多维表格主文档 file_id
- `attachment_id` (string, 必填): 侧边栏智能文档或富文本字段的 attachment_id。侧边栏智能文档取自 `get_schema_detail` 返回的 `content_id`；富文本字段（Note 类型）取自 `list_records` 返回的该字段值中的 `fileId`
- `arg` (object, 必填): format 仅支持 html、markdown；content 最大长度 10485760。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 0 表示成功 |
| `data` | object | 转换后的文档块结构（base64 编码的 JSON，需解码后查看） |

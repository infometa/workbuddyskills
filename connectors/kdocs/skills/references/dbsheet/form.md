# 表单视图

## 1. dbsheet.form_list_fields

#### 功能说明

列出表单问题

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema和dbsheet.views_list确认要操作的数据表id和视图id，不得自行捏造数据表id和视图id，且视图类型必须为表单视图。

**幂等性**：是

#### 调用示例

列出表单字段：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "FormViewId"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `view_id` (string, 必填): 表单视图 ID（非 Grid 等）

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 表单字段列表 |


---

## 2. dbsheet.form_update_field

#### 功能说明

更新表单问题

#### 调用约束

- **前置检查**：使用该工具前必须先调用 get_schema 和 dbsheet.views_list 确认要操作的数据表 id 和视图 id，不得自行捏造数据表 id 和视图 id，且视图类型必须为表单视图。
- **后置验证**：可用 dbsheet.form_list_fields 核对

**幂等性**：是

#### 调用示例

更新字段：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "FormViewId",
  "field_id": "fld_1",
  "body": {
    "field": {}
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `view_id` (string, 必填): 表单视图 ID
- `field_id` (string, 必填): 表单字段 ID
- `body` (object, 必填): 须含 field 对象

**body 根级必填**

| 字段 | 类型 | 说明 |
|------|------|------|
| `field` | object | 要更新的字段属性，子字段以 update-fields 文档 为准 |

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 接口返回详情 |


---

## 3. dbsheet.form_get_meta

#### 功能说明

获取表单元数据

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema和dbsheet.views_list确认要操作的数据表id和视图id，不得自行捏造数据表id和视图id，且视图类型必须为表单视图。

**幂等性**：是

#### 调用示例

获取 meta：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "FormViewId"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `view_id` (string, 必填): 表单视图 ID

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 标题、描述等元数据 |


---

## 4. dbsheet.form_update_meta

#### 功能说明

更新表单元数据

#### 调用约束

- **前置检查**：使用该工具前必须先调用 get_schema 和 dbsheet.views_list 确认要操作的数据表 id 和视图 id，不得自行捏造数据表 id 和视图 id，且视图类型必须为表单视图。

**幂等性**：是

#### 调用示例

更新表单元数据：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "C",
  "body": {
    "description": "string",
    "name": "string"
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（**必须为整数**，不可传字符串）
- `view_id` (string, 必填): 表单视图 ID
- `body` (object, 必填): JSON 请求体，包含表单视图描述与名称

**body（application/json）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `description` | string | 否 | 表单视图描述 |
| `name` | string | 否 | 表单视图名称 |

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 接口返回详情 |

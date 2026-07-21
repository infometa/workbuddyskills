# 表单视图

## 1. dbsheet.form_list_fields

#### 功能说明


**必填 query**：无。

**前置条件**：`view_id` 必须为 **Form（表单）** 视图；可用 `dbsheet.get_schema` / `dbsheet.views_list` 确认 `type` 为表单。



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

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
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


**前置条件**：表单视图；`field_id` 来自 list_fields。



#### 操作约束

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

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
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


**必填 query**：无。

**前置条件**：`view_id` 为表单视图。



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

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
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


**前置条件**：表单视图。



**幂等性**：是

#### 调用示例

更新 meta：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "FormViewId",
  "body": {
    "meta": {}
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `view_id` (string, 必填): 表单视图 ID
- `body` (object, 必填): JSON 请求体，须含 meta 对象

**body 根级必填**

| 字段 | 类型 | 说明 |
|------|------|------|
| `meta` | object | 表单展示配置，子字段以 update-meta 文档 为准 |


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


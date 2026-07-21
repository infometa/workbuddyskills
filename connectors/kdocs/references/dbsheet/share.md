# 分享视图

## 1. dbsheet.share_open_view

#### 功能说明


**前置条件**：对目标视图有管理分享权限；`view_id` 来自 `dbsheet.get_schema` 或 `dbsheet.views_list`。



#### 操作约束

- **前置检查**：逐项核对 file_id、sheet_id、view_id、body.permission、body.share_to、body.view_type 均已齐备；缺任一须停止并向用户列出缺少的参数名
- **禁止**：参数不齐时禁止调用，不得用默认值凑数或猜测缺失参数
- **后置验证**：可用 dbsheet.share_view_status 或 share_get_link_info 核对

**幂等性**：是

> `view_type` 须与 `get_schema` 中该视图类型一致，避免传错导致失败；不确定时先用 get_schema 确认

#### 调用示例

开启分享：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "B",
  "body": {
    "permission": "read",
    "share_to": "anyone",
    "view_type": "G0"
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID（必填；缺失时提示用户缺少 `多维表格文件 ID`）
- `sheet_id` (integer, 必填): 数据表 ID（必填；缺失时提示用户缺少 `数据表 ID`）
- `view_id` (string, 必填): 视图 ID（必填；缺失时提示用户缺少 `视图 ID`）
- `body` (object, 必填): JSON 请求体；**须同时包含** `permission`、`share_to`、`view_type` 三个键，缺一则视为参数不齐
  - `permission` (string, **必填**): `edit` 或 `read`；缺失时提示缺少 `分享权限（可编辑/可查看）`
  - `share_to` (string, **必填**): `anyone`、`company` 或 `assigned`；缺失时提示缺少 `分享范围（所有人/企业内成员/指定人）`
  - `view_type` (string, **必填**): `G0`、`F0` 或 `D0`；缺失时提示缺少 `视图类型（表格/表单/仪表盘）`

**请求体（`body`）字段表**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `permission` | string | 是 | `edit`（可编辑）、`read`（可查看） |
| `share_to` | string | 是 | `anyone`（所有人）、`company`（企业内成员）、`assigned`（指定人） |
| `view_type` | string | 是 | `G0`（表格）、`F0`（表单）、`D0`（仪表盘） |


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
| `detail` | object | 含 share_id 等，以实际返回为准 |


---

## 2. dbsheet.share_view_status

#### 功能说明


**必填 query**：无（路径参数即全部）。

**前置条件**：有读取该视图分享状态的权限。



#### 调用示例

查询状态：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "B"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `view_id` (string, 必填): 视图 ID

#### 返回值说明

```json
{
  "result": "ok",
  "detail": { "is_enable": false, "share_id": "" }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 含 is_enable、share_id 等 |


---

## 3. dbsheet.share_get_link_info

#### 功能说明


**必填 query**：无。

**前置条件**：分享已开启且 `share_id` 有效（可由 view_status / open_view 返回）。



#### 调用示例

查询链接：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "B",
  "share_id": "share_xxx"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `view_id` (string, 必填): 视图 ID
- `share_id` (string, 必填): 分享链接 ID

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
| `detail` | object | 链接权限、过期时间等 |


---

## 4. dbsheet.share_close_view

#### 功能说明


**前置条件**：`share_id` 有效且当前用户可关闭该分享。



#### 操作约束

- **前置检查**：share_view_status 确认当前分享状态
- **用户确认**：关闭后外部访问方将无法通过该链接访问

**幂等性**：否 — 关闭后再次调用无效，先确认当前分享状态

#### 调用示例

关闭分享：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "B",
  "share_id": "share_xxx",
  "body": {}
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `view_id` (string, 必填): 视图 ID
- `share_id` (string, 必填): 分享链接 ID
- `body` (object, 可选): 可传入要求关闭原因等字段；无需附加则传空对象

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

## 5. dbsheet.share_get_repeatable

#### 功能说明


**必填 query**：无。

**前置条件**：`view_id` 为**表单（Form）**视图且已生成分享链接；非表单视图勿调用。



#### 调用示例

查询可重复提交：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "FormViewId",
  "share_id": "share_xxx"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `view_id` (string, 必填): 表单视图 ID
- `share_id` (string, 必填): 分享链接 ID

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
| `detail` | object | 是否允许重复提交等 |


---

## 6. dbsheet.share_set_repeatable

#### 功能说明


**前置条件**：表单视图 + 有效 `share_id`；与 get_repeatable 相同。



#### 操作约束

- **提示**：与官方 set-repeatable 文档保持一致

**幂等性**：是

#### 调用示例

禁止重复提交：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "FormViewId",
  "share_id": "share_xxx",
  "body": {
    "repeatable": false
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `view_id` (string, 必填): 表单视图 ID
- `share_id` (string, 必填): 分享链接 ID
- `body` (object, 必填): JSON 请求体，须含 repeatable（boolean）字段，可与顶层同名字段合并

**body 根级必填**

| 字段 | 类型 | 说明 |
|------|------|------|
| `repeatable` | boolean | 是否允许访客重复提交表单 |


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

## 7. dbsheet.share_update_permission

#### 功能说明


**前置条件**：分享已开启且具备修改该链接权限的能力。



#### 操作约束

- **后置验证**：可用 dbsheet.share_get_link_info 核对

**幂等性**：是

#### 调用示例

更新权限：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "B",
  "share_id": "share_xxx",
  "body": {
    "permission": "read",
    "share_to": "anyone"
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `view_id` (string, 必填): 视图 ID
- `share_id` (string, 必填): 分享链接 ID
- `body` (object, 必填): JSON 请求体，须含 permission、share_to 字段

**请求体（`body`）字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `permission` | string | 是 | 分享权限。可选值：`edit`（可编辑）、`read`（可查看） |
| `share_to` | string | 是 | 分享范围。可选值：`anyone`（所有人）、`company`（企业内成员）、`assigned`（指定人） |


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


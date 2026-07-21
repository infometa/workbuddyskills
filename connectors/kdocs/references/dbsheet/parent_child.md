# 父子记录

## 1. dbsheet.parent_disable

#### 功能说明


**前置条件**：数据表已配置父子字段；仅影响前端展示逻辑，以文档说明为准。



#### 操作约束

- **提示**：行为以接口说明为准

**幂等性**：是

#### 调用示例

禁用：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "body": {}
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `body` (object, 可选): JSON 请求体，补充附加参数；无需附加则传空对象

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

## 2. dbsheet.parent_enable

#### 功能说明


**前置条件**：同 disable-parent；仅前端展示语义。



**幂等性**：是

#### 调用示例

启用：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "body": {}
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `body` (object, 可选): JSON 请求体，补充附加参数；无需附加则传空对象

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

## 3. dbsheet.parent_status

#### 功能说明


**必填 query**：无。



#### 调用示例

查询状态：

```json
{
  "file_id": "string",
  "sheet_id": 1
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID

#### 返回值说明

```json
{
  "result": "ok",
  "detail": { "enable": true }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 是否禁用等 |


---

## 4. dbsheet.parent_bind_children

#### 功能说明


**前置条件**：表已启用父子；`parent_id` 为合法父记录 ID；`child_ids` 为待挂接子记录 ID 列表。



#### 操作约束

- **前置检查**：确认 parent_id、record_ids 均存在且符合层级规则

**幂等性**：否 — 重复绑定可能报错，先确认当前绑定关系

#### 调用示例

绑定子记录：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "parent_id": "parent_rec",
  "body": {
    "child_ids": [
      "child_1",
      "child_2"
    ]
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `parent_id` (string, 必填): 父记录 ID
- `body` (object, 必填): JSON 请求体，包含 child_ids

**body 根级必填**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `child_ids` | array[string] | 是 | 子记录 ID 数组 |


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

## 5. dbsheet.parent_list_children

#### 功能说明


**必填 query**：以接口约定为准（若有分页、过滤参数须从文档抄写参数名）。

**前置条件**：父子关系已配置；`parent_id` 有效。



#### 调用示例

列出子记录：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "parent_id": "parent_rec"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `parent_id` (string, 必填): 父记录 ID

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
| `detail` | object | 子记录列表 |


---

## 6. dbsheet.parent_unbind_children

#### 功能说明


**前置条件**：同 batch_bind；`child_ids` 为待解绑子记录。



#### 操作约束

- **前置检查**：parent_list_children 确认绑定关系
- **提示**：解绑可能影响树形视图与筛选

**幂等性**：否 — 解绑后再次调用无效，先确认当前绑定关系

#### 调用示例

解绑：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "parent_id": "parent_rec",
  "body": {
    "child_ids": [
      "child_1"
    ]
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `parent_id` (string, 必填): 父记录 ID
- `body` (object, 必填): JSON 请求体，包含 child_ids

**body 根级必填**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `child_ids` | array[string] | 是 | 子记录 ID 数组 |


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


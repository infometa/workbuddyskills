# 父子记录

## 1. dbsheet.parent_disable

#### 功能说明

禁用父子关系（仅前端）

#### 调用约束

- **前置检查**：数据表已配置父子字段；仅影响前端展示逻辑，以文档说明为准；使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。

**幂等性**：是

> 行为以接口说明为准

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

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
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

启用父子关系（仅前端）

#### 调用约束

- **前置检查**：同 disable-parent；仅前端展示语义；使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。

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

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
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

查询父子关系是否禁用

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。

**幂等性**：是

#### 调用示例

查询状态：

```json
{
  "file_id": "string",
  "sheet_id": 1
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）

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

绑定父子记录

#### 调用约束

- **前置检查**：确认 parent_id、record_ids 均存在且符合层级规则；使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。
- **前置检查**：确定表是否已启用父子；`parent_id` 需为合法父记录 ID；`child_ids` 需为待挂接子记录 ID 列表。

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

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `parent_id` (string, 必填): 父记录 ID
- `body` (object, 必填): JSON 请求体；根级须含 child_ids
  - `child_ids` (array[string], **必填**): 子记录 ID 列表

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

查询子记录列表

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。
- **前置检查**：父子关系已配置；`parent_id` 有效。

**幂等性**：是

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

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
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

解绑父子记录

#### 调用约束

- **前置检查**：parent_list_children 确认绑定关系
- **前置检查**：使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。

**幂等性**：否 — 解绑后再次调用无效，先确认当前绑定关系

> 解绑可能影响树形视图与筛选

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

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
- `parent_id` (string, 必填): 父记录 ID
- `body` (object, 必填): JSON 请求体；根级须含 child_ids
  - `child_ids` (array[string], **必填**): 子记录 ID 列表

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

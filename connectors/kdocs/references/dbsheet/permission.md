# 高级权限

## 1. dbsheet.permission_list_roles

#### 功能说明


**必填 query**：以接口约定为准（通常无或仅有筛选类参数）。

**前置条件**：文档已开通**高级权限 / 内容权限**能力；否则可能返回业务错误。



> 返回中的系统预置角色与自定义角色区分方式以接口约定为准。

#### 调用示例

列举角色：

```json
{
  "file_id": "string"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID

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
| `detail` | object | permissions 列表（含系统角色等） |


---

## 2. dbsheet.permission_query_task

#### 功能说明


**必填 query**：`task_type`（异步任务类型）。

**前置条件**：`task_id` 来自「新增/更新/删除自定义角色」等异步接口返回。



#### 调用示例

查询任务：

```json
{
  "file_id": "string",
  "task_id": "task_xxx",
  "task_type": "content_permission"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `task_id` (string, 必填): 异步任务 ID
- `task_type` (content_permission, 必填): 异步任务类型（query 参数）

**请求参数**

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Path | `file_id` | string | 是 | 文件 ID |
| Path | `task_id` | string | 是 | 异步任务 ID |
| Query | `task_type` | content_permission | 是 | 异步任务类型 |

异步类接口提交后须轮询本工具直至状态为完成或失败，勿用相同 body 盲目重试创建接口。


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
| `detail` | object | 任务状态与结果数据 |


---

## 3. dbsheet.permission_create_roles_async

#### 功能说明


**前置条件**：文档已开启高级权限；调用方有管理权限配置能力。



#### 操作约束

- **后置验证**：轮询 dbsheet.permission_query_task 直至结束

**幂等性**：否 — 先 permission_query_task 再决定是否重试

#### 调用示例

创建角色：

```json
{
  "file_id": "string",
  "body": {
    "content_permission_name": "销售只读",
    "permission_data": [
      {
        "sheet_id": 0,
        "sheet_permission_type": "Permission_View",
        "record_config_type": "All",
        "viewed_sheet_config": {
          "field_filter": [
            "fld_xxx"
          ],
          "is_all_field": false,
          "is_all_record": true
        }
      }
    ]
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `body` (object, 必填): JSON 请求体，包含 content_permission_name、permission_data

**body 根级必填**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content_permission_name` | string | 是 | 内容权限组名称 |
| `permission_data` | array[object] | 是 | 内容权限组相关信息，传递给内核设置权限用，服务端不关注内部业务语义 |

**`permission_data[]` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sheet_id` | integer | 是 | 数据表 ID |
| `sheet_permission_type` | string | 是 | 权限设置。可选值：`Permission_NoPermission`（无权限）、`Permission_View`（可查看）、`Permission_Edit`（可编辑）、`Permission_Manage`（可管理） |
| `record_config_type` | string | 否 | 可编辑模式下行范围限制。可选值：`All`（全部记录）、`Self`（协作者自己创建的记录）、`Custom`（自定义） |
| `edit_sheet_config` | object | 否 | 可编辑模式下行列条件配置（`sheet_permission_type=Permission_Edit` 时传） |
| `viewed_sheet_config` | object | 否 | 查看权限相关配置（可编辑、可查看时必须传） |

**`sheet_permission_type` 条件必填约束**

- 当 `sheet_permission_type=Permission_Edit`：
  - 必须传 `edit_sheet_config` 与 `viewed_sheet_config`。
  - `edit_sheet_config` 内必须传 `field_filter` 与 `is_all_field`，且 `is_all_field` 必须为 `false`。
  - `viewed_sheet_config` 内必须传 `field_filter` 与 `is_all_field`，且 `is_all_field` 必须为 `false`。
- 当 `sheet_permission_type=Permission_View`：
  - 必须传 `viewed_sheet_config`。
  - `viewed_sheet_config` 内必须传 `field_filter` 与 `is_all_field`，且 `is_all_field` 必须为 `false`。

**`edit_sheet_config` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field_filter` | array[string] | 是 | 列条件。指定可编辑字段 ID；`is_all_field` 必须为 `false` |
| `is_add_record` | boolean | 否 | 是否允许添加记录，默认 `true` |
| `is_all_field` | boolean | 是 | 是否可编辑全部字段；此场景必须传 `false` |
| `is_all_record` | boolean | 否 | 是否可编辑全部记录，默认 `true` |
| `is_remove_record` | boolean | 否 | 是否允许删除记录，默认 `true` |
| `record_filter` | object | 否 | 行条件。指定可编辑记录；前提通常为 `record_config_type=Custom` 且 `is_all_record=false` |

**`viewed_sheet_config` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field_filter` | array[string] | 是 | 列条件。指定可查看字段 ID；`is_all_field` 必须为 `false` |
| `is_all_field` | boolean | 是 | 是否可查看全部字段；此场景必须传 `false` |
| `is_all_record` | boolean | 否 | 是否可查看全部记录，默认 `true` |
| `record_filter` | object | 否 | 行条件。指定可查看/可编辑记录范围 |

**`record_filter` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `criteria` | array[object] | 是 | 筛选条件数组；同一字段不应定义多个条件 |
| `mode` | string | 否 | 条件逻辑关系，仅支持 `AND` 或 `OR`，默认 `AND` |

**`criteria[]` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field` | string | 否 | 字段名 |
| `operator` | string | 否 | 筛选规则。可选值：`Equals`、`NotEqu`、`Greater`、`GreaterEqu`、`Less`、`LessEqu`、`GreaterEquAndLessEqu`、`LessOrGreater`、`BeginWith`、`EndWith`、`Contains`、`NotContains`、`Intersected`、`Empty`、`NotEmpty` |
| `values` | array[string] | 是 | 筛选对比值；元素为字符串时表示文本匹配 |

**`criteria[].values` 取值数量限制**

- `Empty`、`NotEmpty`：不允许填写元素。
- `GreaterEquAndLessEqu`、`LessOrGreater`（介于类规则）：最多 2 个元素。
- `Intersected`：最多 65535 个元素。
- 其他规则：最多 1 个元素。


#### 返回值说明

```json
{
  "result": "ok",
  "detail": { "task_id": "..." }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 含 task_id 等 |


---

## 4. dbsheet.permission_update_roles_async

#### 功能说明


**前置条件**：角色已存在；文档开启高级权限。



#### 操作约束

- **后置验证**：轮询 permission_query_task

**幂等性**：否 — 先 permission_query_task 确认状态再决定是否重试

#### 调用示例

更新角色：

```json
{
  "file_id": "string",
  "body": {
    "cloud_permission_id": 0,
    "content_permission_name": "销售只读",
    "permission_data": [
      {
        "sheet_id": 0,
        "sheet_permission_type": "Permission_View",
        "record_config_type": "All",
        "viewed_sheet_config": {
          "is_all_field": true,
          "is_all_record": true
        }
      }
    ]
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `body` (object, 必填): JSON 请求体，包含 cloud_permission_id、content_permission_name、permission_data

**body 根级必填**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `cloud_permission_id` | integer | 是 | 需要修改的权限组云 ID |
| `content_permission_name` | string | 是 | 内容权限组名称 |
| `permission_data` | array[object] | 是 | 内容权限组相关信息，传递给内核设置权限用，服务端不关注内部业务语义 |

**`permission_data[]` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sheet_id` | integer | 是 | 数据表 ID |
| `sheet_permission_type` | string | 是 | 权限设置。可选值：`Permission_NoPermission`（无权限）、`Permission_View`（可查看）、`Permission_Edit`（可编辑）、`Permission_Manage`（可管理） |
| `record_config_type` | string | 否 | 可编辑模式下行范围限制。可选值：`All`（所有记录）、`Self`（协作者自己创建的记录）、`Custom`（自定义） |
| `edit_sheet_config` | object | 否 | 可编辑模式下行列条件配置（`sheet_permission_type=Permission_Edit` 时传） |
| `viewed_sheet_config` | object | 否 | 内容查看权限相关配置（可编辑、可查看时可传） |

**`edit_sheet_config` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field_filter` | array[string] | 是 | 列条件。指定哪些字段可以编辑；`is_all_field` 必须为 `false` |
| `is_add_record` | boolean | 否 | 非必带，默认 `true`。是否允许添加记录 |
| `is_all_field` | boolean | 否 | 非必带，默认 `true`。是否可编辑全部字段 |
| `is_all_record` | boolean | 否 | 非必带，默认 `true`。是否可编辑全部记录 |
| `is_remove_record` | boolean | 否 | 非必带，默认 `true`。是否允许删除记录 |
| `record_filter` | object | 否 | 行条件。指定哪些记录可以编辑；前提通常为 `record_config_type=Custom` 且 `is_all_record=false` |

**`viewed_sheet_config` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field_filter` | array[string] | 是 | 列条件。指定哪些字段可以查看；`is_all_field` 必须为 `false` |
| `is_all_field` | boolean | 否 | 非必带，默认 `true`。是否可查看全部字段 |
| `is_all_record` | boolean | 否 | 非必带，默认 `true`。是否可查看全部记录 |
| `record_filter` | object | 否 | 行条件。指定哪些记录可以编辑；前提通常为 `record_config_type=Custom` 且 `is_all_record=false` |

**`edit_sheet_config.record_filter` 与 `viewed_sheet_config.record_filter` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `criteria` | array[object] | 是 | 可通过 `criteria` 数组定义 filter 条件；同一字段不应定义多个条件 |
| `mode` | string | 否 | 各筛选条件之间的逻辑关系，仅支持 `AND` 或 `OR`，默认 `AND` |

**`record_filter.criteria[]` 字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field` | string | 否 | 字段名 |
| `operator` | string | 否 | 筛选规则。可选值：`Equals`、`NotEqu`、`Greater`、`GreaterEqu`、`Less`、`LessEqu`、`GreaterEquAndLessEqu`、`LessOrGreater`、`BeginWith`、`EndWith`、`Contains`、`NotContains`、`Intersected`、`Empty`、`NotEmpty` |
| `values` | array[string] | 是 | 筛选规则对比值；元素为字符串时表示文本匹配 |

**`record_filter.criteria[].values` 取值数量限制**

- `Empty`、`NotEmpty`：不允许填写元素。
- `GreaterEquAndLessEqu`、`LessOrGreater`（介于类规则）：最多 2 个元素。
- `Intersected`：最多 65535 个元素。
- 其他规则：最多 1 个元素。


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
| `detail` | object | 含 task_id 等 |


---

## 5. dbsheet.permission_delete_roles_async

#### 功能说明


**前置条件**：待删角色无不可解除的依赖；文档开启高级权限。



#### 操作约束

- **前置检查**：permission_list_roles 确认目标角色
- **用户确认**：删除角色将影响已绑定成员的能力

**幂等性**：否 — 先 permission_query_task 确认状态再决定是否重试

#### 调用示例

删除角色：

```json
{
  "file_id": "string",
  "body": {
    "cloud_permission_id": 0,
    "replace_cloud_permission_id": 0,
    "replace_permission_type": "system"
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `body` (object, 必填): JSON 请求体，包含 cloud_permission_id、replace_cloud_permission_id、replace_permission_type

**body 根级必填**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `cloud_permission_id` | integer | 是 | 需要删除的权限组云 ID |
| `replace_cloud_permission_id` | integer | 是 | 替换的云权限 ID |
| `replace_permission_type` | string | 是 | 替换的权限组类型。可选值：`system`、`team_custom`、`content_custom` |


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
| `detail` | object | 含 task_id 等 |


---

## 6. dbsheet.permission_list_subjects

#### 功能说明

**前置条件**：文档已开启高级权限；`cloud_permission_id` 可与 `dbsheet.permission_list_roles` 返回体中的云权限 ID 对照填写。
**请求方式**：GET，请通过 query 传递 `cloud_permission_id`、`permission_type` 等参数。



> 若业务未开通高级权限，接口可能失败，与参数是否完整无关。

#### 调用示例

最小必填参数：

```json
{
  "file_id": "string",
  "cloud_permission_id": 1,
  "permission_type": "system"
}
```

携带分页与别名：

```json
{
  "file_id": "string",
  "cloud_permission_id": 1,
  "permission_type": "content_custom",
  "alias_name": "viewable",
  "page_token": "next_page_token"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `cloud_permission_id` (integer, 必填): 云权限 ID（query 参数）
- `permission_type` (string, 必填): 权限组类型（query 参数），可选值：`system`、`team_custom`、`content_custom`
- `alias_name` (string, 可选): 权限别名（query 参数）；拿不到 permission_id 时可传，可选值：`manageable`、`viewable`、`editable`
- `page_token` (string, 可选): 分页起始位置标识（query 参数），首页可不传，默认每页约 20 条

**请求参数**

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Path | `file_id` | string | 是 | 文件 ID |
| Query | `cloud_permission_id` | integer | 是 | 云权限 ID |
| Query | `permission_type` | string | 是 | 权限组类型：`system`、`team_custom`、`content_custom` |
| Query | `alias_name` | string | 否 | 权限别名：`manageable`、`viewable`、`editable`（拿不到 permission_id 时可传） |
| Query | `page_token` | string | 否 | 分页起始位置标识；首页可不传，默认分页数量 20 个 item |


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
| `detail` | object | 成员主体列表 |


---


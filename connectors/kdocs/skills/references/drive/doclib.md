# 十、团队文档库

## 1. list_doclibs

#### 功能说明

获取当前用户有权访问的团队文档库分页列表。每条记录包含 `drive.id`（即 `drive_id`），用于后续浏览库内目录（`list_files`）或获取库详情（`get_doclib_meta`）。

展示名称优先取 `drive.name`，为空时回退 `group.name`。

> next_page_token 为空时表示已到末页；items 为空数组表示当前用户无可见文档库
> 从 items[].drive.id 取 drive_id，传给 list_files 可浏览库内目录

#### 调用示例

获取全部文档库（第一页）：

```json
{
  "page_size": 20
}
```

仅查看自己为拥有者或管理员的文档库：

```json
{
  "user_role": [
    "owner",
    "admin"
  ]
}
```

翻页：

```json
{
  "page_token": "NEXT_PAGE_TOKEN"
}
```

#### 参数说明

- `page_size` (integer, 可选): 每页返回条数；范围 1–100，默认 100
- `page_token` (string, 可选): 分页 token，首次请求不传
- `user_role` (array[string], 可选): 按当前用户角色筛选，可多选；取值：`owner` / `admin` / `normal`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "items": [
      {
        "drive": {
          "id": "d_abc123",
          "name": "开放引擎",
          "status": "active",
          "created_by": { "id": "u_001", "name": "张三" }
        },
        "group": {
          "id": "g_001",
          "name": "开放引擎",
          "member_total": 28,
          "type": "normal"
        },
        "user_role": "admin",
        "pinned": true
      }
    ],
    "next_page_token": ""
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 当前页文档库列表 |
| `data.items[].drive` | object | 云盘信息 |
| `data.items[].drive.id` | string | 文档库 drive_id |
| `data.items[].drive.name` | string | 文档库名称 |
| `data.items[].drive.status` | string | 文档库状态 |
| `data.items[].drive.created_by` | object | 创建者，含 `id`、`name` |
| `data.items[].group` | object | 关联团队/群组信息 |
| `data.items[].group.id` | string | 群组 ID |
| `data.items[].group.name` | string | 群组名称（drive.name 为空时作展示名） |
| `data.items[].group.member_total` | integer | 成员总数 |
| `data.items[].group.type` | string | 群组类型 |
| `data.items[].user_role` | string | 当前用户在该文档库的角色：owner / admin / normal |
| `data.items[].pinned` | boolean | 是否置顶 |
| `data.next_page_token` | string | 下一页 token；为空表示已是最后一页 |


---

## 2. get_doclib_meta

#### 功能说明

根据 `drive_id` 获取单个团队文档库的完整元信息，包含云盘信息、关联群组、当前用户角色等。

#### 工具选择

- **适用**：已知 drive_id 时获取单个团队文档库详情
- **勿用**（改用 `list_doclibs`）：需枚举全部有权访问的文档库

> 无效或无权访问的 drive_id 将返回业务错误；可先调 list_doclibs 确认有效 ID
> 取到 drive.id 后，传给 list_files 可浏览库内目录

#### 调用示例

获取指定团队文档库详情：

```json
{
  "drive_id": "d_abc123"
}
```

#### 参数说明

- `drive_id` (string, 必填): 文档库对应的云盘 ID（来自 list_doclibs 的 items[].drive.id）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "drive": {
      "id": "d_abc123",
      "name": "开放引擎",
      "status": "active",
      "created_by": { "id": "u_001", "name": "张三" }
    },
    "group": {
      "id": "g_001",
      "name": "开放引擎",
      "member_total": 28,
      "type": "normal"
    },
    "user_role": "admin",
    "pinned": true
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.drive` | object | 云盘信息 |
| `data.drive.id` | string | 文档库 drive_id |
| `data.drive.name` | string | 文档库名称 |
| `data.drive.status` | string | 文档库状态 |
| `data.drive.created_by` | object | 创建者，含 `id`、`name` |
| `data.group` | object | 关联团队/群组信息 |
| `data.group.id` | string | 群组 ID |
| `data.group.name` | string | 群组名称 |
| `data.group.member_total` | integer | 成员总数 |
| `data.group.type` | string | 群组类型 |
| `data.user_role` | string | 当前用户角色：owner / admin / normal |
| `data.pinned` | boolean | 是否置顶 |

# 四、分享

## 1. share_file

#### 功能说明

开启文件分享，必须传入 `scope` 指定分享范围（`anyone` / `company` / `users`），缺少会报错。
可设置访问密码、过期时间、链接角色等。

**`drive_id`**：源文件所在云盘 ID。不传则按 `file_id` 解析。

**`role_id`**（可选）：须传 `list_drive_roles` 返回的 `items[].id`；不可传预设 `code`；不支持仅查看（`view_only`）与可管理（`manageable`）。按文件类型的可用角色见 `list_drive_roles`。

#### 调用约束

- **前置检查**：指定 role_id 时先 list_drive_roles 取 items[].id，并按文件类型核对白名单（见 list_drive_roles）
- **禁止**：未经用户明确要求，禁止调用此工具
- **后置验证**：确认返回的分享链接有效

**幂等性**：是

#### 调用示例

开启公开分享：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "scope": "anyone"
}
```

指定链接角色：

```json
{
  "file_id": "string",
  "scope": "anyone",
  "role_id": "2546016",
  "opts": {
    "allow_perm_apply": true,
    "check_code": "string",
    "close_after_expire": true,
    "expire_period": 0,
    "expire_time": 0
  }
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID。不传则按 file_id 解析
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `scope` (string, 必填): 链接权限范围。可选值：`anyone`（所有人可访问）/ `company`（仅企业内可访问）/ `users`（仅指定用户可访问）。未明确要求时建议使用 `anyone`
- `role_id` (string, 可选): 须传 `list_drive_roles` 返回的 `items[].id`；不可传预设 code；不支持仅查看与可管理；须落在当前文件类型白名单内
- `opts` (object, 可选): 链接设置
  - `allow_perm_apply` (boolean, 可选): 允许申请权限
  - `check_code` (string, 可选): 访问密码
  - `close_after_expire` (boolean, 可选): 过期后取消分享链接
  - `expire_period` (integer, 可选): 过期时长。可选值：`0` / `7` / `30`
  - `expire_time` (integer, 可选): 过期时间点

#### 返回值说明

```json
{
  "data": {
    "created_by": {
      "avatar": "string",
      "company_id": "string",
      "id": "string",
      "name": "string",
      "type": "user"
    },
    "ctime": 0,
    "drive_id": "string",
    "file_id": "string",
    "id": "string",
    "mtime": 0,
    "opts": {
      "allow_perm_apply": true,
      "check_code": "string",
      "close_after_expire": true,
      "expire_period": 0,
      "expire_time": 0
    },
    "role_id": "string",
    "scope": "anyone",
    "status": "open",
    "url": "string"
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 分享链接 ID（修改分享属性时使用） |
| `data.url` | string | 分享访问 URL |
| `data.status` | string | 链接状态：`open` / `closed` / `expired` |
| `data.drive_id` | string | 盘 ID |
| `data.file_id` | string | 文件 ID |
| `data.role_id` | string | 权限角色 ID（来自 list_drive_roles.items[].id） |
| `data.scope` | string | 权限范围：`anyone` / `company` / `users` |
| `data.ctime` | integer | 创建时间 |
| `data.mtime` | integer | 修改时间 |
| `data.opts` | object | 链接设置 |
| `data.created_by` | object | 创建者信息 |


---

## 2. set_share_permission

#### 功能说明

修改已有分享链接的权限范围、密码、过期时间、链接角色等属性。

**`role_id`**（可选）：须传 `list_drive_roles` 返回的 `items[].id`；不可传预设 `code`；不支持仅查看（`view_only`）与可管理（`manageable`）。按文件类型的可用角色见 `list_drive_roles`。

#### 调用约束

- **前置检查**：指定 role_id 时先 list_drive_roles 取 items[].id，并按文件类型核对白名单（见 list_drive_roles）
- **禁止**：未经用户明确要求，禁止修改分享权限
- **后置验证**：get_share_info 确认权限已变更

**幂等性**：是

> `check_code`（访问密码）仅在 `scope=anyone` 且当前环境支持时生效；不支持时接口返回 400100，可安全忽略该参数

#### 调用示例

修改分享权限：

```json
{
  "link_id": "string",
  "scope": "anyone",
  "opts": {
    "allow_perm_apply": true,
    "check_code": "string",
    "close_after_expire": true,
    "expire_period": 0,
    "expire_time": 0
  }
}
```

修改链接角色：

```json
{
  "link_id": "string",
  "role_id": "2546016"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `scope` (string, 可选): 链接权限范围。可选值：`anyone`（所有人）/ `company`（仅企业）/ `users`（指定用户）
- `role_id` (string, 可选): 须传 `list_drive_roles` 返回的 `items[].id`；不可传预设 code；不支持仅查看与可管理；须落在当前文件类型白名单内
- `opts` (object, 可选): 链接设置
  - `allow_perm_apply` (boolean, 可选): 允许申请权限
  - `check_code` (string, 可选): 访问密码
  - `close_after_expire` (boolean, 可选): 过期后取消分享链接
  - `expire_period` (integer, 可选): 过期时长。可选值：`0` / `7` / `30`
  - `expire_time` (integer, 可选): 过期时间点

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```


---

## 3. cancel_share

#### 功能说明

取消文件分享。

**`drive_id`**：源文件所在云盘 ID。不传则按 `file_id` 解析。

#### 调用约束

- **前置检查**：get_share_info 确认当前分享状态与模式
- **用户确认**（mode=delete）：永久删除分享链接，不可恢复，必须向用户确认
- **后置验证**：get_share_info 确认分享状态已变更

**幂等性**：否 — pause 可重试；delete 禁止重试

> 建议优先使用 mode=pause（可恢复）

#### 调用示例

暂停分享：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "mode": "pause"
}
```

file_id：

```json
{
  "file_id": "string",
  "mode": "pause"
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID。不传则按 file_id 解析
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `mode` (string, 可选): 取消分享模式，默认 `pause`。可选值：`pause`（暂停分享）/ `delete`（删除分享）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```


---

## 4. get_share_info

#### 功能说明

获取分享链接信息与属性。

#### 调用示例

查询分享信息：

```json
{
  "link_id": "string"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID

#### 返回值说明

```json
{
  "data": {
    "created_by": {
      "avatar": "string",
      "company_id": "string",
      "id": "string",
      "name": "string",
      "type": "user"
    },
    "ctime": 0,
    "drive_id": "string",
    "file_id": "string",
    "id": "string",
    "mtime": 0,
    "opts": {
      "allow_perm_apply": true,
      "check_code": "string",
      "close_after_expire": true,
      "expire_period": 0,
      "expire_time": 0
    },
    "role_id": "string",
    "scope": "anyone",
    "status": "open",
    "url": "string"
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 分享链接 ID（修改分享属性时使用） |
| `data.url` | string | 分享访问 URL |
| `data.status` | string | 链接状态：`open` / `closed` / `expired` |
| `data.drive_id` | string | 盘 ID |
| `data.file_id` | string | 文件 ID |
| `data.role_id` | string | 权限角色 ID（来自 list_drive_roles.items[].id） |
| `data.scope` | string | 权限范围：`anyone` / `company` / `users` |
| `data.ctime` | integer | 创建时间 |
| `data.mtime` | integer | 修改时间 |
| `data.opts` | object | 链接设置 |
| `data.created_by` | object | 创建者信息 |


---

## 5. list_drive_roles

#### 功能说明

获取文档可用权限角色列表。`items[].code` 为预设角色别名。

**选用规则：**

- `set_collaborator_permissions`：预设权限可用 `items[].code`（也可使用 `items[].id`）；非预设权限须用 `items[].id`
- `share_file` / `set_share_permission`：仅可用 `items[].id`，且不支持仅查看与可管理

#### 调用示例

获取文档权限角色列表：

```json
{
  "drive_id": "drv-1"
}
```

#### 参数说明

- `drive_id` (string, 必填): 云盘 ID

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "2546016",
        "name": "可评论",
        "code": "commentable",
        "type": "preset",
        "permission_bits": { "comment": true, "copy": true },
        "permissions": { "comment": true, "copy": true }
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 权限角色列表 |
| `data.items[].id` | string | 角色 ID；share_file / set_share_permission / 自定义角色均用此值作为 role_id |
| `data.items[].name` | string | 角色显示名称（本地化，如「可评论」） |
| `data.items[].code` | string | 预设权限别名：view_only / viewable / commentable / editable / manageable；非预设权限可能缺省；set_collaborator_permissions 对预设权限可作 role_id |
| `data.items[].type` | string | 角色类型：preset（预设权限）/ 非预设 |
| `data.items[].permission_bits` | object | 权限位布尔映射（下游原始位图） |
| `data.items[].permissions` | object | 权限能力布尔映射（与 permission_bits 类似，以下游返回为准） |

**预设权限（用户表述 → code → 能力）：**

| 用户表述 | code | 能力说明 |
|----------|------|----------|
| 可编辑 | `editable` | 查看、复制、打印、下载/另存、评论、编辑 |
| 可评论 | `commentable` | 查看、复制、打印、下载/另存、评论 |
| 可查看 | `viewable` | 查看、复制、打印、下载/另存 |
| 可管理 | `manageable` | 可管理文档与协作权限 |
| 仅查看（无下载/另存等权限） | `view_only` | 仅查看，不含下载、另存、打印、复制等 |

上表为预设权限；其余为非预设权限（通常无 `code`，仅有 `id`）。注意区分响应顶层的成功码 `code`（如 `0`）与预设权限别名 `items[].code`（如 `viewable`）。

**文件类型 → 分享链接可用角色（`share_file` / `set_share_permission`）：**

| 文件类型 | 支持的预设角色 code |
|----------|---------------------|
| 图片 | `viewable` |
| 流程图（pom） | `viewable`, `editable` |
| 思维导图（pof） | `viewable`, `editable` |
| 智能文档（ap）/ 智能表格（ksheet）/ 文字（wps）/ 演示（wpp）/ 表格（et）/ 多维表格（dbt） | `viewable`, `commentable`, `editable` |
| 其他未列出类型 | `viewable`, `editable`（默认） |

分享链接**不支持**仅查看（`view_only`）与可管理（`manageable`）；传 `role_id` 时须用上表对应 `code` 的 `items[].id`。

**协作者授权（`set_collaborator_permissions`）：** 在上表同类型白名单基础上，额外支持 `view_only` 与 `manageable`。预设权限可传 `items[].code`（也可使用 `items[].id`）；非预设权限须传 `items[].id`。


---

## 6. list_document_collaborators

#### 功能说明

获取文档最近协作成员（访客）列表，含在线与离线用户。`users` 可含 `offline` 状态；`total` 为过滤前在线用户总数，不等于 `users.length`。

本工具返回**最近访问/协作访客**列表，不是权限判定依据。用户未出现在本列表中，不能据此认定无访问权限（例如：已授权但尚未打开文档；或 `scope=anyone` 持链即可访问等）。判断是否有访问权限时，须结合 `get_share_info`（分享范围）与 `search_document_collaborators`（是否被显式加入协作者）；二者亦不能单独等同于「有/无权限」的完整结论。

> `users` 可含 offline；`total` 不等于 `users.length`

#### 调用示例

获取协作者访客列表：

```json
{
  "file_id": "533034573111",
  "limit": 20
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID；与 url、link_id 三选一
- `limit` (number, 必填): 返回条数上限，最大 1000
- `disable_sticky` (boolean, 可选): 是否禁用创建者置顶
- `exclude_online` (boolean, 可选): 是否排除在线用户
- `filter_status` (string, 可选): 筛选状态。可选值：`online` / `offline`
- `ignore_collaborator_switch` (boolean, 可选): 是否忽略协作者查看开关
- `ignore_offline_switch` (boolean, 可选): 是否忽略企业离线访问记录开关
- `include_pc` (boolean, 可选): 是否包含 PC 端在线用户
- `include_permissions` (array[string], 可选): 权限筛选（AND 语义）

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "users": [
      {
        "user_id": "284611102",
        "nickname": "示例用户",
        "status": "offline",
        "avatar_url": "https://cdn.example.com/avatar/example",
        "permission": {
          "compound_type": "preset",
          "alias_name": "Manageable",
          "role_code": "manageable",
          "name": "可管理"
        }
      }
    ],
    "collaborator_switch": true,
    "show_offline_user_access_record": "enable"
  },
  "result": "OK",
  "ucode": 0
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.users` | array | 协作成员列表（可含 online / offline） |
| `data.users[].user_id` | string | 用户 ID；用于 set/cancel_collaborator_permissions 的 subjects（subject_type=user） |
| `data.users[].nickname` | string | 昵称 |
| `data.users[].avatar_url` | string | 头像 URL |
| `data.users[].status` | string | 在线状态 online / offline |
| `data.users[].create_time` | integer | 创建时间戳 |
| `data.users[].last_view_time` | integer | 最近查看时间戳 |
| `data.users[].permission` | object | 当前授权角色信息 |
| `data.users[].permission.compound_type` | string | 权限类型 preset / 自定义 |
| `data.users[].permission.alias_name` | string | 权限标识别名，语言无关（如 Manageable、View Only） |
| `data.users[].permission.role_code` | string | 预设角色 code：view_only / viewable / commentable / editable / manageable |
| `data.users[].permission.name` | string | 角色显示名称，与语言/地区相关（如「可管理」） |
| `data.users[].permission.permissions` | array | 权限点列表（copy、view、update 等） |
| `data.users[].permission.has_multi_perm` | boolean | 是否多权限组合 |
| `data.users[].permission.subject_type` | string | 权限主体类型 |
| `data.users[].permission.user_id` | integer | 关联用户 ID |
| `data.users[].attrs` | object | 扩展属性，如 orig_perm |
| `data.total` | integer | 在线用户总数（过滤前），可能缺省；不等于 users.length |
| `data.collaborator_switch` | boolean | 是否允许协作者查看最近访客 |
| `data.show_offline_user_access_record` | string | 企业离线访问记录开关 enable / disable |

**status 在线状态：**

| status | 说明 |
|--------|------|
| `online` | 当前在线 |
| `offline` | 离线访客 |

**role_code 预设角色：** 见 `list_drive_roles` 的 `items[].code`。


---

## 7. search_document_collaborators

#### 功能说明

搜索文档协作者。返回 `joined`（已添加）与 `not_join`（未添加）两组列表。`not_join` 可为个人联系人、企业成员，也可能含团队。

本工具搜索结果用来判断**是否被显式加入协作者**，不是「能否打开文档」的唯一判断依据。搜索无结果或不在 `joined`，不能单独认定无访问权限（例如分享范围为 `anyone` 时持链可访）。判断是否有访问权限时须同时看 `get_share_info` 的 scope，并视需要结合本工具的 `joined` / `not_join`；勿仅用 `list_document_collaborators`（仅含访问过的访客）。

> `joined` 为已添加协作者；`not_join` 为未添加的个人联系人、企业成员，也可能含团队
> 团队条目看 `group_members` 取 `user_id`；操作用户主体用 `id`（`subject_type=user`），团队主体用 `id`（`subject_type=group`）

#### 调用示例

搜索协作者：

```json
{
  "file_id": "533034573111",
  "drive_id": "192155925",
  "key": "示例"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID；与 url、link_id 三选一
- `drive_id` (string, 可选): 云盘 ID；传 url/link_id/file_id 时可省略（由定位解析）
- `key` (string, 必填): 搜索关键词，1-255 字符
- `corp_id` (string, 可选): 企业 ID，支持逗号分隔
- `count` (number, 可选): 最大返回数量，最大 10000

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "joined": [
      {
        "id": "241717111",
        "name": "示例用户",
        "kind": "contact",
        "compound_permission": {
          "compound_type": "preset",
          "compound_id": "2546014",
          "compound_name": "可查看",
          "compound_alias_name": "Viewable",
          "role_code": "viewable",
          "user_role_id": "5"
        }
      }
    ],
    "not_join": [
      {
        "id": "2125286222",
        "name": "示例同事",
        "kind": "contact",
        "compound_permission": {
          "compound_id": "0",
          "user_role_id": "0"
        }
      },
      {
        "id": "3125286001",
        "name": "示例共享文件夹",
        "kind": "group_yundoc",
        "compound_permission": {
          "compound_id": "0",
          "user_role_id": "0"
        }
      }
    ]
  },
  "result": "OK",
  "ucode": 0
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.joined` | array | 已添加协作者列表 |
| `data.joined[].id` | string | 对象 ID（用户场景即 user_id） |
| `data.joined[].name` | string | 显示名称 |
| `data.joined[].avatar` | string | 头像 URL |
| `data.joined[].kind` | string | 对象类型：contact（用户联系人）/ group_yundoc（云文档团队） |
| `data.joined[].highlight` | object | 搜索高亮，如 highlight.name 为 HTML 片段 |
| `data.joined[].compound_permission` | object | 复合权限 |
| `data.joined[].compound_permission.compound_type` | string | 权限类型 preset / 自定义 |
| `data.joined[].compound_permission.compound_id` | string | 复合权限 ID；非 0 通常表示已授权 |
| `data.joined[].compound_permission.compound_name` | string | 角色显示名称，与语言/地区相关 |
| `data.joined[].compound_permission.compound_alias_name` | string | 权限标识别名，语言无关 |
| `data.joined[].compound_permission.role_code` | string | 预设角色 code：view_only / viewable / commentable / editable / manageable |
| `data.joined[].compound_permission.user_role_id` | string | 用户角色 ID |
| `data.joined[].group_members` | array | 团队成员列表（kind=group_yundoc 时） |
| `data.not_join` | array | 未添加列表（个人联系人、企业成员，也可能含团队） |
| `data.not_join[].id` | string | 对象 ID（用户场景即 user_id） |
| `data.not_join[].name` | string | 显示名称 |
| `data.not_join[].avatar` | string | 头像 URL |
| `data.not_join[].kind` | string | 对象类型：contact（个人联系人/企业成员）/ group_yundoc（云文档团队） |
| `data.not_join[].compound_permission` | object | 复合权限 |
| `data.not_join[].group_members` | array | 团队成员列表（kind=group_yundoc 时） |

**kind 对象类型：**

| kind | 说明 |
|------|------|
| `contact` | 个人联系人 / 企业成员 |
| `group_yundoc` | 云文档团队（`joined` / `not_join` 均可能出现） |

**role_code 预设角色：** 见 `list_drive_roles` 的 `items[].code`。


---

## 8. get_file_link

#### 功能说明

获取文件的在线访问链接。

#### 调用示例

获取文件链接：

```json
{
  "file_id": "string"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID

#### 返回值说明

```json
{
  "file_id": "string",
  "link_url": "https://kdocs.cn/l/xxxxx",
  "name": "Q1销售报告"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_id` | string | 文件 ID |
| `link_url` | string | 在线访问链接 |
| `name` | string | 文件名 |


---

## 9. set_collaborator_permissions

#### 功能说明

批量新增或修改文档协作者权限；授权主体对象已存在时更新授权角色。暂不支持高级权限。

**`link_id`：** 分享链接 ID，来自 `share_file` / `get_share_info` 返回的 `id`。

#### 调用约束

- **前置检查**：先确认 link_id（share_file / get_share_info），并用 list_drive_roles 核对角色（类型白名单 + view_only/manageable）
- **禁止**：未经用户明确要求，禁止调用此工具
- **后置验证**：用 search_document_collaborators（key=目标用户名）确认已在 joined（显式协作者）；勿用 list_document_collaborators 验权。注意 joined 仅表示显式授权，不等于完整访问判定（须结合 get_share_info 的 scope）

**幂等性**：是

> 可用角色见 `list_drive_roles`：同类型分享白名单基础上额外支持仅查看与可管理；预设权限可用 code 或 id，非预设须用 id

#### 调用示例

批量授权可编辑：

```json
{
  "drive_id": "192155925",
  "link_id": "abcdefg",
  "role_id": "editable",
  "subjects": [
    {
      "subject_type": "user",
      "subject_id": "284611102"
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID；与 url、link_id 三选一
- `drive_id` (string, 可选): 云盘 ID；传 url/link_id/file_id 时可省略（由定位解析）
- `role_id` (string, 必填): 授权角色。可传 list_drive_roles 的 items[].code（viewable/view_only/editable/commentable/manageable），或自定义角色的 items[].id。可用范围见 list_drive_roles（文件类型分享白名单 ∪ {view_only, manageable}）
- `subjects` (array[object], 必填): 授权主体对象列表
  - `subject_type` (string, 必填): 授权主体对象类型：`user`（用户）/ `dept`（部门）/ `company`（企业）/ `group`（团队）
  - `subject_id` (string, 必填): 授权主体对象 ID（用户场景即 user_id）
- `notify_subject_user` (boolean, 可选): 授权后是否通知被授权用户，默认通知
- `overwrite` (boolean, 可选): 是否覆盖子文件，默认 false

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```


---

## 10. cancel_collaborator_permissions

#### 功能说明

批量取消文档协作者授权。

**`link_id`：** 分享链接 ID，来自 `share_file` / `get_share_info` 返回的 `id`。

若文件分享范围为「所有人」（`scope=anyone`），取消某用户的协作者授权后，该用户仍可通过分享链接访问；应询问用户是否将分享范围改为「指定人」（`scope=users`，可用 `set_share_permission`）。

#### 调用约束

- **前置检查**：先确认 link_id，并用 list/search_document_collaborators 确认待取消授权主体对象；用 get_share_info 确认当前 scope
- **用户确认**：取消协作者授权会影响他人访问，执行前必须向用户确认
- **后置验证**：用 search_document_collaborators 确认目标已不在 joined（显式协作者已移除）；勿用 list_document_collaborators 验权。若 scope=anyone，取消协作者后仍可能持链访问（见上条 note）

**幂等性**：否 — 取消授权不可自动重试；失败后向用户确认再决定是否重试

> scope=anyone 时取消授权后用户仍可通过链接访问，须询问是否改为 scope=users（set_share_permission）

#### 调用示例

取消用户授权：

```json
{
  "drive_id": "192155925",
  "link_id": "abcdefg",
  "subjects": [
    {
      "subject_type": "user",
      "subject_id": "284611102"
    }
  ]
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID；与 url、link_id 三选一
- `drive_id` (string, 可选): 云盘 ID；传 url/link_id/file_id 时可省略（由定位解析）
- `subjects` (array[object], 必填): 待取消授权的授权主体对象列表
  - `subject_type` (string, 必填): 授权主体对象类型：`user`（用户）/ `dept`（部门）/ `company`（企业）/ `group`（团队）
  - `subject_id` (string, 必填): 授权主体对象 ID（用户场景即 user_id）
- `overwrite` (boolean, 可选): 是否覆盖子文件

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```

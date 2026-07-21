# 四、分享

## 1. share_file

#### 功能说明

开启文件分享，可设置权限范围、访问密码、过期时间等。

**`drive_id`**（非必填）：

- **有明确的 drive_id** 必传。
- **没有**：不传。



#### 操作约束

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

file_id：

```json
{
  "file_id": "string",
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


#### 参数说明

- `drive_id` (string, 可选): 目标云盘 ID
- `file_id` (string, 必填): 文件 ID
- `scope` (string, 必填): 链接权限范围。可选值：`anyone`（所有人）/ `company`（仅企业）/ `users`（指定用户）
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
| `data.role_id` | string | 权限角色 ID |
| `data.scope` | string | 权限范围：`anyone` / `company` / `users` |
| `data.ctime` | integer | 创建时间 |
| `data.mtime` | integer | 修改时间 |
| `data.opts` | object | 链接设置 |
| `data.created_by` | object | 创建者信息 |


---

## 2. set_share_permission

#### 功能说明

修改已有分享链接的权限范围、密码、过期时间等属性。


#### 操作约束

- **禁止**：未经用户明确要求，禁止修改分享权限
- **后置验证**：get_share_info 确认权限已变更

**幂等性**：是

> `check_code`（访问密码）仅在 `scope=anyone` 且当前环境支持时生效；不支持时接口返回 400100，可安全忽略该参数
> 修改分享属性前需先通过 `share_file` 获取有效的 `link_id`

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


#### 参数说明

- `link_id` (string, 必填): 分享链接 ID
- `scope` (string, 可选): 链接权限范围。可选值：`anyone`（所有人）/ `company`（仅企业）/ `users`（指定用户）
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

**`drive_id`**（非必填）：

- **有明确的 drive_id** 必传。
- **没有**：不传。



#### 操作约束

- **前置检查**：get_share_info 确认当前分享状态与模式
- **用户确认**（mode=delete）：永久删除分享链接，不可恢复，必须向用户确认
- **后置验证**：get_share_info 确认分享状态已变更
- **提示**：建议优先使用 mode=pause（可恢复）

**幂等性**：否 — pause 可重试；delete 禁止重试

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

- `drive_id` (string, 可选): 云盘 ID
- `file_id` (string, 必填): 文件 ID
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

获取分享链接信息。通过 `link_id` 查询分享链接的详细属性。


#### 调用示例

查询分享信息：

```json
{
  "link_id": "string"
}
```


#### 参数说明

- `link_id` (string, 必填): 分享链接 ID

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
| `data.role_id` | string | 权限角色 ID |
| `data.scope` | string | 权限范围：`anyone` / `company` / `users` |
| `data.ctime` | integer | 创建时间 |
| `data.mtime` | integer | 修改时间 |
| `data.opts` | object | 链接设置 |
| `data.created_by` | object | 创建者信息 |


---

## 5. get_file_link

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

- `file_id` (string, 必填): 文件 ID

#### 返回值说明

```json
{
  "file_id": "string",
  "file_url": "https://kdocs.cn/l/xxxxx",
  "name": "Q1销售报告"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_id` | string | 文件 ID |
| `file_url` | string | 在线访问链接 |
| `name` | string | 文件名 |


---


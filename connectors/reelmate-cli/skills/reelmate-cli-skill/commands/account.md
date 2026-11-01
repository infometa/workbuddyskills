# account

查看当前登录账号信息，或在本地已保存账号之间切换。只读：不创建、编辑或管理子账号。

## 用法

```text
reelmate account info [--account UID] [--json]
reelmate account use UID [--json]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate account info` | 查看当前账号本地身份，并拉取现场权限上下文 |
| `reelmate account use UID` | 切换本地当前账号，不发送远端请求 |

## `reelmate account info`

### 作用

输出当前账号摘要：本地 `uid` / 凭据存储 / `space_id`，以及 `GET /web/v1/cam/permission/user` 派生的角色旗标。有团队时再只读当前成员详情。

### 参数

- `--account UID`：只对本次命令选择账号，不改变默认账号。
- `--json`：输出 JSON。

### 输出

成功且权限就绪时包含：

- 本地身份：`uid`、`credentialStore`、`space_id`、`permission_ready=true`
- 权限上下文：`role_id`、`role_name`、`role_code`、`role_level`、`is_owner`、`is_admin`、`is_group_admin`、`is_child`、`has_team`、`team_id`、`team_name`、`team_wsid`、`permission_codes`、`is_all_project`
- 有团队且成员详情成功时：`nick`、`account`、`group_id`、`group_name`、`member_status`

权限接口失败时仍退出 0，只保留本地身份，并设 `permission_ready=false`。任何输出都不包含 access token 或 refresh token。

### 示例

```bash
reelmate account info --json
reelmate account info --account UID
```

## `reelmate account use UID`

### 作用

在本地已登录账号之间切换当前账号。

### 参数

- `UID`（必填）：已登录账号标识，可从 `account info --json` 或登录结果取得。
- `--json`：输出 JSON。

### 输出

返回切换后的账号摘要，不发送远端业务请求。

### 示例

```bash
reelmate account use UID --json
```

## 注意事项

- 未登录时请先运行 `reelmate login`。
- `--account` 只影响当前命令；`account use` 才会修改本地当前账号。
- 本命令不创建成员、不分配积分、不重置密码。

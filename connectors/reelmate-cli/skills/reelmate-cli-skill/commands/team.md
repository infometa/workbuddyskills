# team

查询当前账号的团队信息与权限上下文。只读，不含成员/子账号管理。

## 用法

```text
reelmate team info [TEAM_ID]
reelmate team permission [--require CODE] [--json]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate team info` | 查询团队信息 |
| `reelmate team permission` | 查询当前账号权限旗标与权限码；`--require` 预检指定功能码 |

## `reelmate team info`

### 作用

查询指定团队或当前账号所属团队的信息。

### 参数

- `TEAM_ID`（可选）：团队 ID。省略时从 `GET /web/v1/cam/permission/user` 的 `team_info.team_id` 取得。
- `--json`：输出 JSON。

### 输出

返回团队基本信息。

### 示例

```bash
reelmate team info TEAM_ID --json
reelmate team info --json
```

## `reelmate team permission`

### 作用

查询当前账号在团队中的角色与权限码。不要求 `--space` 或已绑定工作区。

`--require CODE` 只在本子命令生效，用于提问之前预检功能码。判定与对应写命令的门禁相同：主账号、已有该码、权限上下文未就绪、权限接口失败，或写门禁关闭时退出码 0。缺码时退出码 1，`error.kind=permission`，`error.message` 与该写命令相同。不带 `--require` 时，权限接口失败仍使命令失败。

### 参数

- `--json`：输出 JSON。
- `--require CODE`：要预检的功能码。新建项目使用 `project.create`。资产提示词回填使用 `resource.edit`。拆分镜依次使用 `episode.edit` 与 `storyboard.edit`。分镜视频回填使用 `storyboard.edit`。无限画布生图或生视频步骤 3 使用 `project.edit`。

### 输出

与 `account info` 同源的派生字段：`is_owner` / `is_child` / `is_admin` / `is_group_admin` / `has_team` / `permission_codes` 等。`--require` 因接口失败或上下文未就绪而放行时，`permission_ready` 为 false。

### 示例

```bash
reelmate team permission --json
reelmate team permission --require project.create --json
reelmate team permission --require project.edit --json
reelmate team permission --require resource.edit --json
reelmate team permission --require episode.edit --json
reelmate team permission --require storyboard.edit --json
```

## 注意事项

- 只查看当前账号与所属团队，不提供创建成员、分配积分、重置密码或成员列表。
- 可先运行 `reelmate account info --json` 查看 `team_id`。

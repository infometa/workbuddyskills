# 消息免打扰设置（user.setRemind）

## 何时使用

用户说「把某个群/某个人设为免打扰」「别再提醒这个群」「恢复提醒」时使用。对应 operation：

| operation 对 | 用途 |
| --- | --- |
| `im.user.setRemind.prepare` / `.apply` | 设置**当前登录人自己**的会话免打扰（**仅会话维度**：单聊会话 / 群聊会话 / 系统会话） |

接口来源：`POST /api/em/msg/executeIm/user/setMsgRemind`（weaver-im-api `PathSetMsgRemind`，协议 `MsgRemindInfo`）。

## 输入要点

- `sessionType`（必填）：`1` 单聊会话、`2` 群聊会话、`4` 系统会话。
- `reminder`（必填）：`0` 消息接收提醒（恢复提醒）、`1` 消息接收但不提醒（免打扰，会话仍在最近列表并带未读数）。
- 目标字段按 `sessionType` 二选一（传错类型会报 `target_required`）：
  - `1` 单聊会话 → `toUid` + `toCid`（对方身份，先用 `im.person.resolve` 解析）
  - `2` 群聊会话 → `groupId`
  - `4` 系统会话 → `group`（系统消息分组 id，来自 `im.sysmsg.groupSearch`/会话列表）
- `prepare` 会只读回查目标名称（群名 / 人名 / 系统分组名）写进 `summary.target`，便于向用户确认后再 `apply`。
- 操作者身份由 CLI 用当前登录人（`teamsCheck`）填充，**调用方不能自带** `user`/`sender`/`operator`（会被 `forbidden_key` 拒绝）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.user.setRemind.prepare --input-json '{"sessionType":2,"groupId":"1788334281700000004","reminder":1}'
weaver-work-cli --profile eteams --json im run im.user.setRemind.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.user.setRemind.prepare --input-json '{"sessionType":2,"groupId":"1788334281700000004","reminder":1}'
weaver-work-cli --profile eteams --json im run im.user.setRemind.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

系统会话、单聊会话两种常见形态：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.user.setRemind.prepare --input-json '{"sessionType":4,"group":110,"reminder":1}'
weaver-work-cli --profile eteams --json im run im.user.setRemind.prepare --input-json '{"sessionType":1,"toUid":"100234","toCid":"102","reminder":0}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.user.setRemind.prepare --input-json '{"sessionType":4,"group":110,"reminder":1}'
weaver-work-cli --profile eteams --json im run im.user.setRemind.prepare --input-json '{"sessionType":1,"toUid":"100234","toCid":"102","reminder":0}'
```

## 输出处理

- `prepare` 返回 `summary`：`action/target/sessionTypeName/reminderName` + 目标 id；**必须先向用户复述"把哪个会话设成什么状态"再 apply**。
- `apply` 返回 `sessionType`/`sessionTypeName`/`reminder`/`reminderName` 与目标 id。
- 核对方式（只读）：`im.session.list` 里该会话的 `dontDisturb` 与 `unreadLabel`（免打扰会话显示 `N（免打扰）`）。联机实测：群/系统消息分组设为 `reminder:1` 后 `dontDisturb` 立即变为 `true`，设回 `0` 后恢复 `false`。
- 这是"低风险但会影响用户收消息"的设置：默认只在用户明确要求时执行，不要顺手改；改完若要还原，用同样的 operation 传 `reminder:0`。

## 注意

- 只影响**当前登录人自己**的免打扰偏好；不会改变其他成员的设置，也不会删除/清空会话。
- 本能力只做会话维度的「提醒 / 免打扰」两种状态；其它提醒形态请引导用户在易秒办客户端处理。
- 写操作只认 CLI 签发的 continuation：不手工拼、不复用、不跨操作；`apply` 不确定时不自动重试，先用 `im.session.list` 只读回查。

## 失败处理

- `session_type_invalid`：`sessionType` 不是 `1`（单聊会话）/`2`（群聊会话）/`4`（系统会话）。
- `reminder_invalid`：`reminder` 不是 `0`（接收提醒）或 `1`（免打扰）。
- `target_required`：该 `sessionType` 缺少对应目标字段（单聊会话缺 `toUid`/`toCid`、群聊会话缺 `groupId`、系统会话缺 `group`）。
- `forbidden_key`：入参带了 `user`/`sender`/`operator` 等操作人字段。
- 认证/上下文类错误参照共享规则；其余业务码见 [`error-codes.md`](error-codes.md)。

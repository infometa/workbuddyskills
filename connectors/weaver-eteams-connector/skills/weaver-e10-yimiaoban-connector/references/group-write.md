# 群组写操作（建群 / 邀请 / 踢人 / 退群 / 解散 / 入群 / 改群 / 公告）

## 何时使用

用户要建群、拉人进群、踢人、退群、解散群、申请入群、改群名/群属性/转让群主、写群公告。全部是两段式写操作（prepare→apply）：

| operation 对 | 动作 |
| --- | --- |
| `im.group.create.prepare` / `.apply` | 创建普通群 |
| `im.group.invite.prepare` / `.apply` | 邀请成员入群 |
| `im.group.kick.prepare` / `.apply` | 踢出群成员 |
| `im.group.exit.prepare` / `.apply` | 退出群聊 |
| `im.group.destroy.prepare` / `.apply` | **解散群聊**（仅群主，不可恢复） |
| `im.group.join.prepare` / `.apply` | 申请加入群聊（`groupId` 或 `token`） |
| `im.group.modify.prepare` / `.apply` | 批量改群属性（人数/开关/管理员/转让群主等，batModGroupInfo） |
| `im.group.rename.prepare` / `.apply` | 单字段改群信息（群名/历史/群主/显示/打扰/标记/gtid） |
| `im.group.announce.modify.prepare` / `.apply` | 新增/修改/删除群公告 |

## 输入要点

- `users` 可以是数组 `["uid1","uid2"]` 或逗号串 `"uid1,uid2"`。成员先经 hrm 解析出 uid+cid；解析失败且未传 `removeFailed:true` 会中止并列出失败成员，由用户决定是否移除失败项继续。
- 建群：**`users` 必须包含操作者自己**（否则返回 `self_not_included`，服务端会把操作者设为群主）；`name` 缺省时 CLI 按"自己的姓名 + 另外最多 4 个成员姓名"生成群名（可传 `names` 与 `users` 顺序一一对应覆盖姓名）；`admins` 指定管理员（解析失败会中止并列出失败人）。
- 解散群风险最高，prepare 的 summary 必须向用户明确"不可恢复、仅群主可解散"。
- `group.modify` 传字段即改该字段：`num` 人数、`switchs`（`flag:onoff` 逗号串，如 `1:1,8:0`）、`admins`（新增管理员，字段 `admins`）、`delAdmins`（移除管理员，字段 `del_admins`，**两者语义不同不能混用**）、`creator` 转让群主、`history`、`gtId` 等；**禁止传操作人字段**（操作者由会话 eteamsid 识别）。管理员/群主解析失败会中止，确认移除后可传 `removeFailed:true`。
- `group.rename` 一次只能改一项（顺序枚举 mask）：`name`/`history`/`host`（转让群主，uid）/`display`/`msgSetting`/`mark`/`gtid`；`announce`/`type`/`state` 被禁用（公告走 `group.announce.modify`，type/state 属高危）。
- 建群成功返回新建群 `groupId`（服务端字段 `group_id`）与 `rawData`；`group.announce.modify` 新增/修改返回 `aid`，删除返回被删除的 `aid` 且 `deleted:true`。
- 公告：`annouce` 内容；`aid` 缺省/0=新增、非 0=修改、`del:true`+`aid`=删除。`notice` 0 发通知(默认)/1 不发/2 发并@全体；`fmark` 新人必看。
- 群 id 一律字符串非 0。
- **加入群（`group.join`）是"提交申请"而不是"立即进群"**（联机实测）：`apply` 成功会返回 `flag:0` + `note:"需管理员/群主审批"`，真正入群要等群主/管理员审批；若该群已无成员或不允许申请，会直接业务失败 `1210 没有权限`。申请后不要反复重试，也不要自行猜测是否已入群，用 `group.userExist` 复核。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.group.invite.prepare --input-json '{"groupId":"1788334281700000004","users":["100234","100235"]}'
weaver-work-cli --profile eteams --json im run im.group.rename.prepare --input-json '{"groupId":"1788334281700000004","name":"季度评审群"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.group.invite.prepare --input-json '{"groupId":"1788334281700000004","users":["100234","100235"]}'
weaver-work-cli --profile eteams --json im run im.group.rename.prepare --input-json '{"groupId":"1788334281700000004","name":"季度评审群"}'
```

向用户展示 `summary`（动作/群/人数/变更字段），确认后：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.group.invite.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.group.invite.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

## 注意

- 踢人、解散、转让群主都是不可逆/高影响动作，summary 必须讲清对象与后果，等用户明确确认。
- **退群（`group.exit`）有护栏**：`prepare` 会只读回查群人数与群主；当你**是群主**或**是群里最后一个成员**时，必须显式传 `acknowledgeOrphanRisk:true` 才会签发 continuation，否则返回 `owner_exit_ack_required`。原因（联机实测）：这两种情形退群后群会变成**无主空群**，之后 `group.join` / `group.destroy` 都会被服务端拒绝（`1210 没有权限`），只能由客户端或管理员处理——不要为了"演练"随意退掉自己建的群。
- 退群/解散/踢人前可先 `group.users` 只读回查当前成员与身份，避免误操作。
- apply 阶段只传 `confirm:true` + continuation；业务参数以 prepare 快照为准。
- 不确定结果（partial/超时）时**不自动重试**，先 `group.info`/`group.users` 回查实际状态。

## 失败处理

- `members_resolve_failed`：列出解析失败成员，问用户是否 `removeFailed:true`。
- `members_empty`：无有效成员。
- 无权限（非群主执行解散/转让等）会返回业务错误，告知用户权限不足。
- 其余 continuation 类错误同 [`msg-write.md`](msg-write.md)。

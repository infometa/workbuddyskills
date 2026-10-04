# 发送消息 / 撤回 / 群消息置顶（写）

## 何时使用

给某人/某群发文本、图片或文件消息；撤回自己发出的消息（时限以回包 `withdrawInterval` 为准）；群消息置顶/取消置顶。全部是两段式写操作：

| operation 对 | 动作 |
| --- | --- |
| `im.msg.send.single.prepare` / `.apply` | 发送单聊消息 |
| `im.msg.send.group.prepare` / `.apply` | 发送群聊消息 |
| `im.msg.withdraw.prepare` / `.apply` | 撤回消息（`type`=single/group） |
| `im.msg.top.set.prepare` / `.apply` | 群消息置顶/取消（`type`:1 置顶 2 取消，或 `cancel:true`） |

## 输入要点（prepare 阶段）

- 发送单聊：`toUid`+`toCid`（接收人，先用 `person.resolve` 解析）；群聊：`groupId`。文本用 `txt`；图片用本地路径 `img`；文件用本地路径 `file`（CLI 会先上传到 E10 文件服务再发送，`img`/`file` 与 `txt` 可组合）。
- **全空白文本（空格/换行）不算内容，会被拒绝（`content_required`）**；`img` 与 `file` 一次只能传一种（`content_conflict`）。
- 撤回：`type`（single/group）+ `msgid`（消息 `ser_msgid`）；单聊还需 `toUid`/`toCid`，群聊还需 `groupId`。**只能撤回本人发出的消息，且有时限**——`apply` 回包会给出该环境实际时限（`withdrawInterval`，实测如"30 秒"，不同环境可能是"2 分钟"），超时（1505）错误里也会带上；以回包值为准，不要写死时限。
- 置顶：`groupId` + `msgid` + `type`（1 置顶 / 2 取消）。
- 本地文件路径：绝对路径或相对 CLI 运行目录的路径均可；上传前必须先与用户确认该文件内容可能进入大模型上下文并被发送到 E10 文件服务。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.msg.send.group.prepare --input-json '{"groupId":"1788334281700000004","txt":"下午 3 点评审，请准时参加"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.msg.send.group.prepare --input-json '{"groupId":"1788334281700000004","txt":"下午 3 点评审，请准时参加"}'
```

prepare 返回 `data.summary`（动作/目标/内容预览）与 `data.continuation`。向用户确认后执行 apply：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.msg.send.group.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.msg.send.group.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

## 注意

- apply 只接受 prepare 签发的 continuation；**不得手工拼 token**，不得复用/跨操作使用。超过 10 分钟或切换账号/租户后 continuation 失效，需重新 prepare。
- `apply` 里不要重复传业务参数（发送目标/内容以 prepare 快照为准）；重复调用 prepare 后必须用**最新** continuation。
- 图片/文件发送成功与否以 apply 响应为准；若响应为 `partial`/`write_uncertain`，停止并做只读回查（如拉群最新消息确认是否已发出），**不要自动重发**——否则可能重复发送。
- 撤回超时或非本人消息会业务失败（1505/1506/1507），按错误信息告知用户，不重试。
- 普通请求 15 秒超时即失败，不重试；上传按 15 秒（预检）/60 秒（实传）执行。
- CLI 固定使用各 operation 的接口路径，**不提供自定义接口路径参数**（避免绕过 operation 契约）；遇到异常路径需求请改用 `schema` 中登记的对应能力。

## 失败处理

- `confirmation required`：说明没有带 `confirm:true`，重新按协议走 prepare→apply。
- `continuation_expired`/`context_mismatch`：重新 prepare。
- `target_changed`：prepare 之后目标/内容被改动过（指纹不一致），重新 prepare。
- 消息发出但不确定结果：只读回查群/单聊最新消息确认，不盲目重试。

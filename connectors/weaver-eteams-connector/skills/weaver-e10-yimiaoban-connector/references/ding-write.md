# 必达消息（ding，写）

## 何时使用

用户要发"必达/重要消息/Ding/应用通知"（红色必达卡片），或把群里已有消息转为必达、仅发给未读/指定人员。两段式写操作：

| operation 对 | 动作 |
| --- | --- |
| `im.ding.send.prepare` / `.apply` | 发普通必达 或 已有消息转必达（走 `/api/em/msg/createDing`，非 executeIm） |

## 场景与输入要点

必达分两类，prepare 阶段二选一：

1. **普通必达**：`txt` 必填（全空白文本会被拒绝）；`groupId`（群必达）与 `toUid`（单聊必达）至少其一。
2. **转必达**：`convertMsgid` = 源消息 `ser_msgid`，会把源消息内容原样转成必达卡片（文本/图片/文件/视频自动判别）；无需 `txt`。群聊转必达传 `groupId`，**单聊转必达必须传 `toUid`+`toCid`**（`toCid` 用于按消息 id 拉取源消息，缺失会被拒绝：`to_cid_required`）。

公共选项：

- `unreadOnly:true`（**仅群转必达**，单聊传会被拒绝：`unread_only_group_only`）：只发给**未读**该消息的成员；若群里没有未读人员，**prepare 阶段**就会失败（`unread_empty`），需向用户说明是否改发全体/指定人员。
- `toUids:[...]`：群必达只发给指定 uid 列表（会先解析 cid，过滤发起者本人）。
- 不传 `unreadOnly`/`toUids` 时默认发给群内除本人外**全体成员**（自动解析成员）。
- `sendMsg`：0 不发短信 / 1 发短信（默认 1）；`showType`：0 全体可见（默认）/ 1 仅发送人可见。

> **接收人集合在 prepare 阶段（只读）就已解析并写入确认快照**，摘要里带 `receiverSource`（全体成员/指定人员/仅未读人员/单聊对方）与 `receiverCount`；用户确认的就是这批人，apply 不再重新算人。
> 群成员内部复用 `getGroupUsers` 接口拉取（响应体兼容 `users`/`members`/`datas` 三种包裹层），成员 cid 走 hrm 解析（成员可能跨团队）；必达接收人自动排除自己，`unreadOnly` 不自动回退全员。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.ding.send.prepare --input-json '{"groupId":"1788334281700000004","txt":"请今天下班前确认三季度预算"}'
weaver-work-cli --profile eteams --json im run im.ding.send.prepare --input-json '{"groupId":"1788334281700000004","convertMsgid":"9000000000000000001","unreadOnly":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.ding.send.prepare --input-json '{"groupId":"1788334281700000004","txt":"请今天下班前确认三季度预算"}'
weaver-work-cli --profile eteams --json im run im.ding.send.prepare --input-json '{"groupId":"1788334281700000004","convertMsgid":"9000000000000000001","unreadOnly":true}'
```

向用户展示 prepare 的 `summary`（动作=发送必达/转必达、目标=群/单聊、是否全体/未读/指定人、是否发短信），确认后：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.ding.send.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.ding.send.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

## 注意

- 必达是**高打扰**动作：默认全体成员 + 发短信，必须向用户明确说明接收范围和短信费用，经确认后才 apply。
- `unreadOnly:true` 转必达依赖目标消息存在且群内有未读人员；源消息找不到（`source_not_found`）或全员已读（`unread_empty`）都会失败，按错误向用户说明，不自动回退全员。
- apply 不确定（网络/超时）时停止，用 `im.msg.top.sync`/拉群消息或系统消息只读回查必达是否已发出，**不自动重试**（避免重复必达）。

## 失败处理

- `target_required`：缺群或单聊目标。`content_required`：普通必达缺 `txt` 且转必达缺 `convertMsgid`。
- `members_empty`：群里没有可接收成员（如只有本人）。
- 其余 confirmation/expired/mismatch 处理同 [`msg-write.md`](msg-write.md)。

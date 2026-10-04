# im group recent 返回结构与会话类型

> `im group recent` 返回的会话字段含义，以及 `groupType` 取值与发送策略对照。被 [im.md](./im.md) 的「im group recent」章节引用。

## 返回结构

`data` 为 `{list, ...伴随字段}`（`list` 是会话数组，元素结构见下表），伴随字段与 `list` 平级：

| 伴随字段 | 类型 | 说明 |
|------|------|------|
| `count` | number | 本次返回的会话条数 |
| `more` | boolean | 是否还有更多记录（true 时继续翻 `--page`，false 表示已到末页） |
| `unreadTotal` | number | 全部会话未读总数 |
| `lastUpdateTime` | string | 会话列表刷新时间（ISO 时间字符串），增量拉取会话变更时可原样使用（增量变更游标，不是翻页游标） |

**`data.list[]` 元素字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `groupId` | string | 群/会话 ID，发消息时用 |
| `groupName` | string | 群名或私聊对端姓名 |
| `groupType` | number | 会话类型，见下方「`groupType` 识别」 |
| `headerUrl` | string | 群头像 URL |
| `joinTime` | string | 加入会话时间 |
| `lastMsg` | object | 最近一条消息，含 `content`、`fromOpenId`、`msgId`、`msgType`、`sendTime` |
| `lastMsgId` | string | 最近消息 ID |
| `lastMsgSendTime` | string | 最近消息发送时间 |
| `unreadCount` | number | 该会话未读数 |

## `groupType` 识别

会话类型帮助判断形态与发送策略；下发消息前按需判断：

| `groupType` | 含义 | 实测样例 | 用途 |
|---|---|---|---|
| `1` | 单人群组 / 私聊 | 「卢柱均」（self-chat，`groupId` 形如 `<SELF>-<SELF>`） | 与 `--to-open-id <OPEN_ID>` 等价场景；已有私聊会话用 `--group-id` 也可以；`@all` / `@个人` 无意义，CLI 会拒绝 `--at-*` 与 `--to-open-id` 同传 |
| `2` | 多人群组 | 「测试上限」 | 群发消息、@ 个人 / @ 全员、回复消息均可；`im message send --group-id` 的主要场景 |
| `3` | 助手 / 应用类会话 | 「文件传输助手」「时间助手」 | 可作为 `--group-id` 目标发消息（文件传输助手实测可发）；语义上用于个人辅助场景，不是同事群 |
| `8` | 系统通知 | 「待办通知」 | 由系统推送，`fromOpenId` 形如 `XT-10001`；发消息能力未验证，需要时小批量试一次再使用 |

判断要点：

- `groupType=1` 的会话 `groupId` 形如 `<A_OPEN_ID>-<B_OPEN_ID>`（两端 openId）；self-chat 两端相同。优先用 `--to-open-id`，已有会话用 `--group-id` 也可以。
- `groupType=3` 的会话 `fromOpenId` 一般以 `XT-` 前缀开头（助手 / 公共号 ID），**不是用户 openId**，不能用于 `--to-open-id` 或 `--at-open-id`。
- 上表只列实测过的取值；后端可能返回其他 `groupType`（如更多业务场景），遇到未见过的取值时，按 `groupName` / `fromOpenId` 综合判断，必要时小批量试发一次。

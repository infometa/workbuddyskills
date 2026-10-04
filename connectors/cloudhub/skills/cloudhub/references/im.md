# im（IM 消息）

## 核心规则

- `chat` 与 `im` 等价；示例统一使用 `im`，用户明确写 `chat` 时也可以直接执行。
- 不要编造 `groupId`、`openId`、`msgId`、`fileId`。缺少 ID 时先通过现有命令或用户提供的信息获取。
- 富文本图片的 `--image` 支持多图；可重复传 `--image file1 --image file2`，也可写同一个 flag 后跟多个值 `--image file1 file2`；不要用逗号分隔。
- 找群优先用 `im group search --keyword`（当前用户可见范围内匹配）；只知道大概翻过最近会话时再用 `im group recent`。
- 当前 IM 暴露 `im message send`、`im message list`、`im group recent`、`im group search`、`im group create`、`im group.members add`、`im group.members remove`；文件上传/下载走顶层 `file` scope（`file upload` / `file download`）；没有消息搜索、消息详情、快捷表情、群改名/解散/退出命令。
- **发消息是严肃操作**：`im message send` 是顶层 [SKILL.md CRITICAL 规则](../SKILL.md)（「禁止猜测参数值」「危险操作前必须获得用户同意」）在 IM 场景的特化；调用前必须完成参数审查，详见下文「发消息前参数审查（必须执行）」章节。严禁假设、补全、自作主张。

## 意图映射

| 用户说 | 命令 |
|--------|------|
| 发文本消息 / 在群里发个消息 | `im message send --group-id <GROUP_ID> --msg-type text --content "..."` |
| 发私聊消息 / 给某人发消息 | 有 openId 用 `--to-open-id`；有私聊会话 groupId 用 `--group-id` |
| 发送文字和图片 | `im message send ... --msg-type richText --content "文字 [图片]" --image <FILE_ID>` |
| 单独发一张图片 | `im message send ... --msg-type file --file-id <IMAGE_FILE_ID>`（不传 `--content`） |
| 发送普通文件 | `im message send ... --msg-type file --file-id <FILE_ID>` |
| @ 指定成员 | `im message send ... --content "@姓名 ..." --at-open-id <OPEN_ID>` |
| @ 全员 | `im message send ... --content "@all ..." --at-all` |
| 回复消息 | `im message send ... --reply-msg-id <MSG_ID>`（仅 `text` / `richText`） |
| 获取历史聊天记录 / 看最近消息 | `im message list --group-id <GROUP_ID> --type newest --limit 20` |
| 基于消息向前/向后翻聊天记录 | `im message list --group-id <GROUP_ID> --msg-id <MSG_ID> --type old\|new --limit 20` |
| 最近群组 / 最近会话 | `im group recent --limit 20 --page 1` |
| 按名字找群 | `im group search --keyword "群名"` |
| 建群 | `im group create --name "群名" --member-open-id <OPEN_ID> <OPEN_ID>`（成员至少 2 人） |
| 拉人进群 | `im group.members add --group-id <GROUP_ID> --open-id <OPEN_ID>` |
| 移出群成员 | `im group.members remove --group-id <GROUP_ID> --open-id <OPEN_ID>`（不可恢复且影响他人，须用户确认后带 `--yes`） |
| 上传本地文件用于 IM 消息 | `file upload --file <PATH>` → 拿 `fileId` 回来发文件消息或富文本图片 |

### 易混淆

| 用户说 | 用 | 不用 | 理由 |
|---|---|---|---|
| 发私聊：只知道对方 openId | `--to-open-id <OPEN_ID>` | `--group-id` | `--to-open-id` 按用户 openId 发起私聊 |
| 发私聊：已有私聊会话 groupId | `--group-id <GROUP_ID>` | `--to-open-id` | 已有会话直接用 groupId，不必再转 openId |
| 上传本地文件 | `file upload --file <PATH>` | `im message send --file <PATH>` | IM 命令不接收本地路径，只接收 `fileId`；先 `file upload` 换取 |
| @ 只对群聊有效 | 多人群聊用 `--at-open-id` / `--at-all` | `--to-open-id` 同时传 `--at-*` | `--to-open-id` 是私聊，不能 @；CLI 会拒绝 |
| 想知道某个群叫什么 | `im group search --keyword "群名"` | 翻 `im group recent` 分页 | 优先关键词搜索命中更快；搜不到（不在可见范围）再翻最近会话 |

## 发消息前参数审查（必须执行）

`im message send` 是真实有副作用的操作：消息会立刻送到目标会话，发错人/发错群/发错内容都会造成实际问题，**不可撤回**。调用前 agent 必须完成参数审查，未完成审查不得调用。

### 必审项（4 项，缺一不可）

1. **收件人 / 群**：`--group-id` 或 `--to-open-id` 必须来自用户原文明确指定，或来自用户认可的查询结果（如 `im group recent` / `contact user search` 的输出经用户确认）。严禁从历史上下文、相似群名、猜测中补全。
2. **消息内容**：`--content` 必须与用户原文一致。如果消息文本由 agent 组织（如摘要、模板填充、Markdown 转换），必须在调用前把最终文本回显给用户确认措辞，得到明确同意后再发。
3. **@对象**：正文中的每个 `@姓名` 必须有对应的 `--at-open-id`，且 openId 来源可信（用户原文提供或 `contact user search` 后用户确认）。`--at-all` 必须由用户显式要求，agent 不得自作主张 @ 全员。
4. **消息类型与附件**：`--msg-type`（`text` / `file` / `richText`）、`--file-id`、`--image` 必须符合用户意图。`file upload` 得到的 `fileId` 在用于发送前必须回显给用户核对。

### 严禁假设补全

出现以下任一情况，**必须先向用户确认，不得自行决定**：

- 用户只说「发个消息」但没指定收件人/群。
- 用户的描述可匹配多个群或多个联系人（如「张三」匹配到多条 `contact user search` 结果）。
- 消息内容由 agent 组织而非用户原文提供时。
- 不确定是否需要 @ 某人、不确定消息类型（文字 vs 文件 vs 富文本）。
- 用户给的 `groupId` / `openId` / `fileId` 看起来像猜测或编造（如 `test`、`xxx`、`123`、`aabbccdd...` 等无来源的占位值）。

### 典型需要二次确认的场景

- 用户说「在最近那个群里发个消息」→ 必须先 `im group recent` 列出候选群让用户选定 `groupId`，不得直接用返回的第一条。
- 用户说「给张三发」且 `contact user search --keyword "张三"` 返回多条 → 必须列出候选让用户选定 openId。
- 用户给的是本地文件路径而非 `fileId` → 必须先 `file upload` 并把返回的 `fileId` 给用户核对后再用于发送。
- 用户说「把这个文档内容发到群里」→ 必须先把待发送的完整文本回显给用户确认，不得跳过。

## 细节清单

### 目标选择

- `--group-id` 和 `--to-open-id` 必须二选一，不能都不传，也不能同时传。
- `--group-id` 可用于群聊，也可用于已有私聊会话 ID；已有私聊会话 ID 时不要再转换成 `--to-open-id`。
- `--to-open-id` 只用于按用户 openId 发起私聊；不知道 openId 时先用 `contact user search`。
- 不要把群名、人名、手机号、工号直接当作 `groupId` 或 `openId`。

### 消息类型与必填参数

- `--msg-type` 使用 `text`、`file`、`richText`。
- `text`、`richText` 必须传 `--content`。
- `file` 必须传 `--file-id`，不支持 `--content`、`--at-all`、`--at-open-id`、`--reply-msg-id`；`text`、`richText` 不传 `--file-id`。本地文件路径不能直接发，先用 `file upload --file <PATH>` 换取 `fileId`。
- `--image` 只能用于 `richText`；传到 `text/file` 会被 CLI 拒绝。
- 空字符串、纯空白、`''`、`""` 这类空值会被 CLI 当成无效参数。

### @ 提醒

- `@` 提醒只用于 `text`、`richText` 多人群聊，`file` 不支持；正文中出现 `@all` 或 `@姓名` 本身不会触发提醒；每个 `@姓名` 对应一个 `--at-open-id`，每个 `@all` 对应一个 `--at-all`。
- `@all`、`@姓名` 必须是独立片段：前面是行首或空格，后面跟一个空格，再接正文，例如 `@all 请关注`、`请 @张三 处理`。
- `--at-all` 用于 @ 全员，不需要 openId。
- `--at-open-id` 用于 @ 指定成员；正文里有几个 `@姓名`，就传几个对应值，顺序保持一致；可重复传 `--at-open-id id1 --at-open-id id2`，也可写同一个 flag 后跟多个值 `--at-open-id id1 id2`；没有 `--at-open-ids`，不要用 `id1,id2` 逗号分隔；openId 先用 `contact user search` 查询确认。
- @ 提醒只适合多人群聊；`--to-open-id` 表示私聊，传 `--at-all` / `--at-open-id` 时 CLI 会直接拒绝。私聊正文中的普通 `@all`、`@姓名` 文本仍可发送。

### 富文本图片

- 本地图片先上传：`file upload --file "<IMAGE_PATH>"`。
- 多图按正文占位顺序传多个 `--image` 值，正文保留相同数量的 `[图片]` 或 `[image]` 占位；可重复 flag，也可同一个 flag 后跟多个值。

### 回复与历史消息

- 回复消息用 `text` 或 `richText` 并传 `--reply-msg-id <MSG_ID>`，目标仍然要传对应会话的 `--group-id`；`file` 不支持回复效果。
- 不知道 `msgId` 时，先执行 `im message list --group-id <GROUP_ID> --type newest --limit 20` 找最近消息。
- `im message list --type newest` 不需要 `--msg-id`，即使传了锚点，CLI 也不会把锚点传给接口。
- `--type old` / `--type new` 必须传 `--msg-id`：`old` 向前取更早消息，`new` 向后取更新消息。
- `--limit` 默认 `10`；范围 1-20。

### 最近群组与群搜索

- 按名字找群优先 `im group search --keyword <关键词>`；搜不到（群不在当前用户可见范围）再用 `im group recent --limit 20 --page 1`，未命中时继续翻 `--page 2/3/...`。

### 建群与成员管理

- `im group create` 群主固定为当前登录用户；`--member-open-id` 不含创建人（自动入群），至少 2 人、最多 10 人；openId 来源：`contact user search`。
- `im group.members add` 需当前用户为群管理员或群允许成员邀请；`im group.members remove` 需当前用户为群管理员；两者单次最多 10 人。
- `im group.members remove` **不可恢复且影响他人**：执行前必须向用户展示群名与成员名单并获得确认，确认后命令须带 `--yes`（未带会被 CLI 拒绝）。
- 成员 openId 同样遵守「禁止猜测」：必须来自用户原文或经确认的 `contact user search` 结果。

## 核心工作流与命令速览

私聊 / 群聊 / 文件 / 富文本图片 / 回复 / 历史记录 / @ 人等 7 个核心场景的完整 CLI 链路、命令速览，统一在 [im/workflows.md](./im-workflows.md)。

> ⚠️ 调用 `im message send` 前必须先完成本文件「发消息前参数审查（必须执行）」章节的 4 项必审；消息类型与 `--content` / `--file-id` / `--image` / `--at-*` 的组合约束见本文件「细节清单」与下方 flag 表。

## im message send

| Flag | 必填 | 说明 |
|------|------|------|
| `--group-id` | 条件 | 目标群 ID 或会话 ID，群聊/私聊会话均可；与 `--to-open-id` 二选一 |
| `--to-open-id` | 条件 | 私聊目标 openId；已有私聊会话 groupId 时可改用 `--group-id` |
| `--msg-type` | 是 | 消息类型：`text`、`file`、`richText` |
| `--content` | 条件 | `text`、`richText` 必填；`file` 不支持传入 |
| `--file-id` | 条件 | 文件消息必填，通常来自 `file upload` 返回；其他消息类型不可传 |
| `--reply-msg-id` | 否 | 回复的消息 ID，仅 `text`、`richText` 支持 |
| `--at-open-id` | 否 | 仅 `text`、`richText` 多人群聊支持，不能与 `--to-open-id` 同时使用；@ 指定成员；正文每个 `@姓名` 对应一个值，顺序保持一致；可重复传，也可同一个 flag 后跟多个值 |
| `--at-all` | 否 | 仅 `text`、`richText` 多人群聊支持，不能与 `--to-open-id` 同时使用；@ 全员；可重复传，正文每个 `@all` 对应一个 `--at-all` |
| `--image` | 否 | 富文本图片 fileId，仅 `richText` 使用；可重复传，也可同一个 flag 后跟多个值；不要用逗号分隔 |

## im message list

| Flag | 必填 | 说明 |
|------|------|------|
| `--group-id` | 是 | 群 ID 或会话 ID |
| `--type` | 否 | `newest`、`old`、`new`；`newest` 取最近，`old` 取更早，`new` 取更新 |
| `--msg-id` | 条件 | `type=old/new` 时必填；`type=newest` 不需要，传了也不会下发给接口 |
| `--limit` | 否 | 获取条数，默认 10，范围 1-20 |

## im group recent

| Flag | 必填 | 说明 |
|------|------|------|
| `--limit` | 否 | 每页条数，默认 10，范围 1-20 |
| `--page` | 否 | 页码，默认 1，必须 >= 1；第一页未命中时继续翻页 |

`im group recent` 的返回结构（`data.list` 会话数组 + 伴随字段 `count` / `more` / `unreadTotal` / `lastUpdateTime`）与 `groupType` 取值识别（`1` 私聊 / `2` 多人群 / `3` 助手类 / `8` 系统通知）统一在 [im/group-type.md](./im-group-type.md)。下发消息前按 `groupType` 判断是否可发、能否 @，遇到未见过的取值按 `groupName` / `fromOpenId` 综合判断，必要时小批量试发。

## im group search

| Flag | 必填 | 说明 |
|------|------|------|
| `--keyword` | 是 | 群名搜索关键词 |
| `--limit` | 否 | 每页条数，默认 10，范围 1-20 |
| `--page` | 否 | 页码，默认 1，范围 1-200 |

返回 `data.list` 为群数组（元素含 `groupId` / `groupName` / `headerUrl`），`data.more` 标记是否还有下一页；是否继续翻页看 `data.more`。

## im group create

| Flag | 必填 | 说明 |
|------|------|------|
| `--name` | 是 | 群名称 |
| `--member-open-id` | 是 | 初始成员 openId，可重复传或空格分隔多个；不含创建人（自动入群），至少 2 人、最多 10 人 |

成功返回含新群 `groupId`。

## im group.members add

| Flag | 必填 | 说明 |
|------|------|------|
| `--group-id` | 是 | 群 ID |
| `--open-id` | 是 | 成员 openId，可重复传或空格分隔多个，最多 10 人 |

## im group.members remove

| Flag | 必填 | 说明 |
|------|------|------|
| `--group-id` | 是 | 群 ID |
| `--open-id` | 是 | 成员 openId，可重复传或空格分隔多个，最多 10 人 |
| `--yes` | 是 | 确认执行；不可恢复且影响他人，未带会被 CLI 拒绝 |

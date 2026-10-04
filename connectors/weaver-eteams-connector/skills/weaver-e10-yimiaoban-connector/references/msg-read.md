# 消息读取（拉取聊天/置顶/阅读状态）

## 何时使用

用户要"拉我和某人的聊天记录""拉某群的聊天消息""看群置顶""谁读了/没读某条消息"。覆盖只读操作：

| operation | 用途 |
| --- | --- |
| `im.msg.sync.single` | 拉单聊消息（必填 `fromUid`+`fromCid`，为**对方**身份） |
| `im.msg.sync.group` | 拉群聊消息（必填 `groupId`；type=0 由 CLI 固定，无需传） |
| `im.msg.top.sync` | 群置顶消息摘要 + 内容（必填 `groupId`） |
| `im.msg.read.single` | 单聊消息阅读状态（`msgids`=自己发出 / `recvMsgids`=自己接收） |
| `im.msg.read.group` | 群消息阅读汇总（每条已读/未读情况） |
| `im.msg.read.group.detail` | 群阅读详情（unread/read 数 + 每人状态，支持分页） |

## 输入要点

- `fromUid`/`fromCid`/`groupId` 必须是**字符串数字**，禁止 `0`。对方 uid/cid 用 `im.person.resolve`（按姓名/工号/手机/邮箱）先拿到，不要猜。
- 每页 `num` 默认 **50**、单页上限 **50**（超过会被截断为 50）。
- **翻页口径**：**有界区间**（给了 `from`/`to`、缺省当天、或显式 `end`/`endId`）→ CLI 在该区间内**自动循环翻页拉完再返回**（最多 100 页；触及上限时 `hasMore:true` + `nextStart`）；**无界区间**（`latest:true`）→ **只拉一页**，需要更早数据时把 `nextStart` 作为下一次的 `start`/`startId` 再请求。
- 时间范围：`from`/`to` 支持 `YYYY-MM-DD`、`YYYY-MM-DD HH:mm:ss`、unix 秒；缺省为当天。**跨度 > 7 天时 CLI 自动收敛为该范围最后 7 个自然日**，并在 `data.rangeShrink.notice` 给出提示——**必须把这条提示转述给用户**（例如"拉上个月"→实际只拉最后 7 天）。要覆盖更早历史时按 ≤ 7 天分段多次调用。
- 显式 id 区间优先级最高：单聊用 `start`/`end`，群聊用 `startId`/`endId`（消息 id 即 `ser_msgid`，取自上页首/尾行）。
- `imgFormat`：`small`（默认）`large`/`original`，决定图片预览 URL 规格。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.msg.sync.group --input-json '{"groupId":"1788334281700000004","num":50,"latest":true}'
weaver-work-cli --profile eteams --json im run im.msg.sync.single --input-json '{"fromUid":"100234","fromCid":"102","from":"2026-08-01","to":"2026-08-31"}'
weaver-work-cli --profile eteams --json im run im.msg.top.sync --input-json '{"groupId":"1788334281700000004"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.msg.sync.group --input-json '{"groupId":"1788334281700000004","num":50,"latest":true}'
weaver-work-cli --profile eteams --json im run im.msg.sync.single --input-json '{"fromUid":"100234","fromCid":"102","from":"2026-08-01","to":"2026-08-31"}'
weaver-work-cli --profile eteams --json im run im.msg.top.sync --input-json '{"groupId":"1788334281700000004"}'
```

## 输出处理

- `data.messages[]` 是已解析的结构化行：`sender`（姓名，走 hrm）、`time`、`typeName`（文本/图片/视频/文件…）、`content`（完整文本，不截断）、`media`（图片/视频/文件的预览与下载 URL，需登录态访问）、`must`（必达标记，`true` 展示加 `[必达]` 前缀）等。
- 顺序：消息按消息 id **从新到旧**（最新在最前）返回。
- 分页字段：`pages`（本次实际拉了几页）、`autoPaged`（是否走了自动翻页）、`pageSize`、`exhausted`、`hasMore`、`nextStart`（还有更早数据时的续拉锚点）、`range.scope`（`today`/`range`/`latest`/`explicit-id`）、`rangeShrink`（7 天收敛提示）。
- `sender` 为自己时显示「我」（CLI 用会话 uid 判定）；媒体消息的 `content` 形如 `[图片]a.png` / `[视频]b.mp4` / `[文件]c.pdf`，同时单列 `fileName` 便于渲染。
- 展示整段消息**不自行截断**；若将多行渲染进表格，保留换行提示、把 `|` 转义，媒体链接保留为可点击的 Markdown 链接。
- `data.hasMore=true` 时用 `data.nextStart`（本次最小 `ser_msgid`）作为下页 `start`/`startId` 再请求（保持同一时间范围）；CLI 已按 `msgid` 去重服务端重复返回的边界消息。**不要**为了"统计总数"而反复续拉（见 [`safety-boundaries.md`](safety-boundaries.md) 红线）。
- `data.empty=true` 表示本次为空页（`actionMsg.code=1303`）：按成功处理，用 `data.emptyReason` 向用户说明口径（当天无消息 / 该时间范围无消息 / 该会话暂无任何消息记录），不要当报错重试。
- 展示口径必须写明本次实际范围（如"默认拉了今天，共 N 条"或"已自动收敛为 2026-09-09~2026-09-15，自动翻页拉完共 N 条"）。

## 注意

- 消息内容可能较长（含敏感业务信息），返回内容会进入大模型上下文；缺省范围是当天，跨天大量拉取前先和用户确认口径（"拉全部历史"要分段，不要指望一次拉完）。
- 群聊必须给 `type=0` 是内部固定行为，接口文档要求，无需业务传入。

## 失败处理

- `error.code=1303` 语义是"无聊天记录"，按成功空列表处理（见 `emptyReason`），不要报错重试。
- 群不存在/无权限会返回 `1209` 或业务错误，向用户说明该群不可读。
- `context_mismatch`/认证错误：提示用户断开并重新连接本连接器后重试。

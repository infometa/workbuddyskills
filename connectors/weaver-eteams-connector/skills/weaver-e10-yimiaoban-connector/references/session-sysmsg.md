# 会话列表与系统消息

## 何时使用

用户要"看我的会话/最近聊天"（单聊、群聊、系统消息入口）；查"系统消息/流程待办通知/审批提醒"等 IM 系统消息。

| operation | 用途 |
| --- | --- |
| `im.session.list` | 拉当前用户会话列表（单聊/群聊/系统消息，名称与副标题已解析） |
| `im.sysmsg.groupSearch` | 按名称搜系统消息分组/类型配置（供 query 使用） |
| `im.sysmsg.typeSync` | 按 gids/tids 拉系统消息分组/类型配置 |
| `im.sysmsg.query` | 拉系统消息（流程/任务/公文等），支持阅读维度/处理状态/时间范围/单页倒序 |

## 输入要点

- `session.list`：`num` 默认 20 上限 50；`flag` 0 up+down / 1 up / 2 down（默认 2，从最新拉）；`msgid` 锚点实现翻页（取上页返回的 `nextMsgid`）；`type` 只过滤该 session_type；`around` 表示锚点附近上下各半。**会话列表不参与消息类自动翻页**：一次只返回一页，更旧会话需用户明确要求后用 `nextMsgid` 继续。
- 会话返回带 `sessionTypeName`（单聊/群聊/系统消息）、`name`（单聊=对方姓名、群聊=群名、系统=分组名）、`unread`（来自 `unread_count`）、`unreadLabel`（免打扰会话显示 `N（免打扰）`）、`time`（会话更新时间）、`subtitle`（发送者：最近消息内容）、`lastMsgid`（下一页锚点 `nextMsgid`）。
- `sysmsg.groupSearch` 用名称找分组/类型（流程/待办/公告等），返回 gid/tid 供 `typeSync` 与 `query`。
- `sysmsg.query`：**必填 `group`（系统分组 id，来自 `groupSearch`/会话列表）**，可选 `type`（消息类型 id）、`flag`（0 不分已读未读/1 已读/2 未读）、`deal`（0 全部/1 未处理/2 已处理）、`num`（默认 **50**、上限 50）、时间范围 `from`/`to`/`latest`、显式 `start`/`end`。分页口径与聊天消息一致：有界区间（时间范围/默认当天/显式 `end`）自动循环翻页拉完，`latest:true` 只拉一页；`from`/`to` 跨度 > 7 天自动收敛为最后 7 个自然日并把 `rangeShrink.notice` 转述给用户。系统消息「已读/处理」类状态更新在需要时由 Agent 引导用户到易秒办处理，CLI 不伪装处理。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.session.list --input-json '{"num":20}'
weaver-work-cli --profile eteams --json im run im.sysmsg.query --input-json '{"group":110,"num":50,"flag":2}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.session.list --input-json '{"num":20}'
weaver-work-cli --profile eteams --json im run im.sysmsg.query --input-json '{"group":110,"num":50,"flag":2}'
```

## 输出处理

- 会话列表渲染：单聊/群聊显示名称（走 hrm/群信息），系统消息显示分组名；副标题按类型给最近消息预览，媒体会话显示 `[图片]xxx.png`/`[文件]xxx.pdf` 形式，必达消息保留 `[必达]` 前缀。
- 列表结果大时按共享规则汇总（只给关键列 + 总数），不要整表倾倒；按需翻页。
- `sysmsg.query` 返回 `dealMode`：`true` 表示该分组以**处理状态**为准（`statusLabel` = 已处理/未处理），`false` 表示以**阅读状态**为准（已读/未读）；`title` 为系统消息标题（如流程标题），展示时标题一行、内容一行。
- 系统消息同样是分页字段：`pages`/`autoPaged`/`pageSize`/`exhausted`/`hasMore`/`nextStart`/`range`/`rangeShrink`；`start` 是**排除边界**（返回 id `< start`），CLI 已按消息 id 去重。

## 失败处理

- `sysmsg.*` 的分组/类型 id 必须来自 `groupSearch`/`typeSync` 返回，禁止编造 gid/tid。
- 会话/系统消息为空：返回空列表，正常。
- 认证/上下文错误参照共享规则。

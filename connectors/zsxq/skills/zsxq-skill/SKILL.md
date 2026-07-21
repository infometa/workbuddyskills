---
name: zsxq-skill
description: 知识星球 CLI 操作技能 — 浏览星球、搜索发布主题、评论回答、管理笔记、查看用户信息
version: "1.0.0"
author: "知识星球 (Zsxq)"
---

# 知识星球 (Zsxq) Skill

通过 `zsxq-cli` 命令行工具操作知识星球。所有命令通过 Bash 工具执行。

## 核心概念

| 概念 | 标识 | 说明 |
|------|------|------|
| 星球（Group） | `group_id` | 知识社群单元，纯数字 ID |
| 主题（Topic） | `topic_id` | 星球内的内容单元。类型：`talk`（帖子）、`q&a`（提问）、`task`（作业）、`solution`（作业答案） |
| 评论（Comment） | `comment_id` | 主题下的回复，支持楼中楼（`replied_comment_id`） |
| 笔记（Note） | `note_id` | 独立于星球的内容单元，纯数字 ID |
| 用户（User） | `user_id` | 账户标识，纯数字 ID |

资源层级：`Group → Topic → Comment → 楼中楼 Reply`

## 安全规则

- **Token 是登录凭证**，禁止明文输出或分享
- **写入/删除前必须确认用户意图**：发帖、编辑、评论、回答、创建/编辑/删除笔记、提交 NPS
- **不确定 ID 时先查询再操作**：用 `+list` / `+search` / `+detail` 确认后再执行写入或删除
- **笔记是公开内容**，任何持有链接的人都可访问 —— 不要写入隐私或敏感信息

## 命令参考

### 认证

| 命令 | 用途 |
|------|------|
| `zsxq-cli auth status` | 查看当前登录账户。成功输出 `✓ Logged in as <name> (<user_id>)`，exit code 0 |
| `zsxq-cli auth logout` | 清除本地凭据 |

> 认证登录由 WorkBuddy 自动管理，无需手动执行 `auth login`。如遇 401 错误，在 WorkBuddy 中重新连接 Connector 即可。

---

### zsxq-cli group — 星球管理

#### `group +list` — 列出我的星球

列出当前用户加入或创建的所有星球。

```bash
zsxq-cli group +list
zsxq-cli group +list --limit 50
zsxq-cli group +list --json
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--limit <n>` | 否 | 返回数量，默认 10，最大 200 |
| `--json` | 否 | 输出完整 JSON |

**输出（表格）**：`GROUP ID` / `NAME`

#### `group +topics` — 浏览星球主题

列出星球内最新主题，按时间倒序。

```bash
zsxq-cli group +topics --group-id 123456789
zsxq-cli group +topics --group-id 123456789 --limit 30
zsxq-cli group +topics --group-id 123456789 --json

# 翻页：用上一页返回的 next_end_time
zsxq-cli group +topics --group-id 123456789 \
  --end-time "2025-11-01T10:00:00.000+0800"
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--group-id <id>` | **是** | 星球 ID |
| `--limit <n>` | 否 | 返回数量，默认 20，最大 30 |
| `--end-time <t>` | 否 | 分页游标，使用上一页返回的 `next_end_time` 原值 |
| `--json` | 否 | 输出完整 JSON |

**输出（表格）**：`TOPIC ID` / `TYPE` / `TITLE / DIGEST` / `CREATED AT`
- `TYPE`：`talk` / `q&a` / `task` / `solution`

#### `group +hashtags` — 查看星球标签

```bash
zsxq-cli group +hashtags --group-id 123456789
zsxq-cli group +hashtags --group-id 123456789 --json
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--group-id <id>` | **是** | 星球 ID |
| `--json` | 否 | 输出完整 JSON |

**输出（表格）**：`HASHTAG ID` / `TITLE` / `TOPIC COUNT`

#### API：星球高级操作

没有对应 Shortcut 时，通过 `zsxq-cli api call` 调用：

```bash
# 按关键词搜索星球
zsxq-cli api call search_groups --params '{"keyword":"Go语言"}'

# 按昵称搜索星球成员
zsxq-cli api call search_group_members \
  --params '{"group_id":"123456789","keyword":"昵称","limit":20}'

# 查看某标签下的所有主题
zsxq-cli api call get_hashtag_topics \
  --params '{"hashtag_id":"333444555666","limit":20}'

# 翻页
zsxq-cli api call get_hashtag_topics \
  --params '{"hashtag_id":"333444555666","limit":20,"end_time":"2025-11-01T00:00:00.000+0800"}'
```

---

### zsxq-cli topic — 主题操作

#### `topic +search` — 全文搜索主题

在指定星球内全文搜索，结果按相关性排序。

```bash
zsxq-cli topic +search --group-id 123456789 --query "跨境电商"
zsxq-cli topic +search --group-id 123456789 --query "AI 应用" --json
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--group-id <id>` | **是** | 星球 ID |
| `--query <text>` | **是** | 搜索关键词，支持中英文 |
| `--json` | 否 | 输出完整 JSON |

#### `topic +detail` — 查看主题详情

获取单条主题的完整信息（正文、作者、点赞数、评论数、标签等）。

```bash
zsxq-cli topic +detail --topic-id 111222333444
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--topic-id <id>` | **是** | 主题 ID |
| `--json` | 否 | 默认即 JSON 输出 |

**关键输出字段**：`topic_id`、`type`（`talk`/`q&a`/`task`/`solution`）、`title`、`content`、`create_time`、`digested`（是否精华）、`counts`（`comments`/`likes`/`readers`）、`owner`、`group`

> `+detail` 不含评论内容。查看评论用 `api call get_topic_comments`。

#### `topic +create` — 发布帖子

在指定星球内发布一条 `talk` 类型主题。⚠️ **仅支持 talk 类型**。

```bash
# 纯文本帖子
zsxq-cli topic +create --group-id 123456789 --text "帖子正文"

# 带附件（逗号分隔路径）
zsxq-cli topic +create --group-id 123456789 \
  --text "帖子正文" --files photo.jpg,report.pdf

# 获取新建的 topic_id
zsxq-cli topic +create --group-id 123456789 --text "帖子正文" --json
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--group-id <id>` | **是** | 目标星球 ID |
| `--text <text>` | **是** | 正文内容，支持 `\n` 换行 |
| `--files <paths>` | 否 | 附件路径，逗号分隔 |
| `--json` | 否 | 输出含 `topic_id`、`create_time` |

**⚠️ 执行前必须确认：** 目标星球 + 发布内容。**写入失败即原子回滚。**

#### `topic +edit` — 编辑帖子

编辑自己发布的主题。只能编辑自己的。

```bash
zsxq-cli topic +edit --topic-id 111222333444 --text "修改后的内容"
zsxq-cli topic +edit --topic-id 111222333444 --files new-photo.jpg
zsxq-cli topic +edit --topic-id 111222333444 --clear-files
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--topic-id <id>` | **是** | 主题 ID |
| `--text <text>` | 否 | 新正文（不传则保留） |
| `--files <paths>` | 否 | 新附件，替换原有 |
| `--clear-files` | 否 | 清除所有附件 |
| `--json` | 否 | 输出 JSON |

**⚠️ 执行前必须确认：** 主题当前内容 + 修改后内容。**写入失败即原子回滚。**

#### `topic +reply` — 发表评论

对主题发表评论，支持楼中楼。

```bash
# 顶层评论
zsxq-cli topic +reply --topic-id 111222333444 --text "评论内容"

# 楼中楼：回复某条评论
zsxq-cli topic +reply --topic-id 111222333444 \
  --text "回复内容" --reply-to 222333444555

# 带附件
zsxq-cli topic +reply --topic-id 111222333444 \
  --text "评论" --files screenshot.png
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--topic-id <id>` | **是** | 主题 ID |
| `--text <text>` | **是** | 评论内容 |
| `--reply-to <id>` | 否 | 被回复的评论 ID（楼中楼），省略为顶层评论 |
| `--files <paths>` | 否 | 附件路径，逗号分隔 |
| `--json` | 否 | 输出含 `comment_id`、`create_time` |

**⚠️ 执行前必须确认：** 目标主题 + 评论内容。**写入失败即原子回滚。**

#### `topic +answer` — 回答提问

对 `q&a` 类型主题发布官方回答。**每题只能回答一次，不可修改。**

```bash
zsxq-cli topic +answer --topic-id 111222333466 --text "回答内容"
zsxq-cli topic +answer --topic-id 111222333466 \
  --text "回答内容" --files diagram.png
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--topic-id <id>` | **是** | 主题 ID（必须是 `q&a` 类型） |
| `--text <text>` | **是** | 回答正文 |
| `--files <paths>` | 否 | 附件路径，逗号分隔 |
| `--json` | 否 | 输出 JSON |

**⚠️ 执行前必须确认：** 问题内容 + 回答全文。`+answer` 与 `+reply` 不同：前者是官方回答（仅一次），后者是普通评论（可多次）。

#### 删除主题

通过原始 HTTP 调用删除。**不可恢复。**

```bash
zsxq-cli api raw --method DELETE --path /v2/topics/<topic_id>
```

**⚠️ 执行前必须确认：** 主题内容和删除意图。特有错误：`code: 100262`（无权限）、`code: 100002`（不存在）。

#### API：主题高级操作

```bash
# 查看主题评论列表
zsxq-cli api call get_topic_comments \
  --params '{"topic_id":"111222333444","limit":30}'

# 设置/取消精华（星主权限）
zsxq-cli api call set_topic_digested \
  --params '{"topic_id":"111222333444","digested":true}'

# 设置标签
zsxq-cli api call set_topic_tags \
  --params '{"topic_id":"111222333444","titles":["标签1","标签2"]}'

# 查看自己发起的提问（unanswered / answered）
zsxq-cli api call get_self_question_topics \
  --params '{"topic_filter":"unanswered","count":20}'

# 查看别人向我发起的提问
zsxq-cli api call get_self_answer_topics \
  --params '{"topic_filter":"unanswered","count":20}'
```

---

### zsxq-cli user — 用户信息

#### `user +info` — 查看个人资料

```bash
zsxq-cli user +info
```

输出当前用户的 `user_id`、`name`、`unique_id`、`avatar_url`、`identity_status`（实名认证状态）、`subscribed_wechat`、第三方账户绑定等。

#### `user +footprints` — 跨星球足迹

查看自己在**所有星球**最近发过的主题，按时间倒序。

```bash
zsxq-cli user +footprints
zsxq-cli user +footprints --limit 30
zsxq-cli user +footprints --json

# 翻页（用上一页最后一条的 create_time）
zsxq-cli user +footprints \
  --end-time "2025-11-01T00:00:00.000+0800"
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--limit <n>` | 否 | 返回条数，默认 20，最大 30 |
| `--end-time <t>` | 否 | 分页游标，传入上一页最后一条的 `create_time` |
| `--json` | 否 | 输出完整 JSON |

**输出（表格）**：`TOPIC ID` / `TYPE` / `TITLE / DIGEST` / `GROUP` / `CREATED AT`

> `+footprints` 跨星球 vs `group +topics` 单星球。查"我最近发过什么"用 `+footprints`。

#### `user +nps` — 提交 NPS 反馈

向知识星球官方提交推荐分数和建议。

```bash
zsxq-cli user +nps --score 9 --suggestion "希望增加更多互动功能"
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--score <n>` | **是** | 1–10 整数（1=不推荐，10=极力推荐） |
| `--suggestion <text>` | **是** | 文字建议，最长 500 字。建议以 `#产品建议#` 或 `#工具反馈#` 开头 |
| `--json` | 否 | 输出 JSON |

**⚠️ 执行前必须确认：** 分数 + 建议全文。特有错误：`--score must be 1–10`、`--suggestion exceeds 500 chars`。**需 zsxq-cli ≥ 0.4.6。**

---

### zsxq-cli note — 笔记管理

笔记是独立于星球的公开内容，任何持有链接的人都能访问。

#### `note +create` — 创建笔记

```bash
zsxq-cli note +create --text "笔记内容"
zsxq-cli note +create --text "第一行\n第二行"
zsxq-cli note +create --text "带图笔记" --files photo.jpg
zsxq-cli note +create --text "内容" --json  # 获取 note_id
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--text <text>` | **是** | 笔记内容，支持 `\n` 换行 |
| `--files <paths>` | 否 | 附件路径，逗号分隔（仅图片） |
| `--json` | 否 | 输出含 `note_id`、`create_time` |

**⚠️ 执行前必须确认：** 笔记内容（笔记是公开的，勿写入隐私）。

#### `note +list` — 笔记列表

```bash
zsxq-cli note +list
zsxq-cli note +list --limit 30
zsxq-cli note +list --json

# 翻页
zsxq-cli note +list --end-time "2025-11-01T00:00:00.000+0800"
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--limit <n>` | 否 | 返回条数，默认 20，最大 30 |
| `--end-time <t>` | 否 | 分页游标，传入上一页最后一条的 `create_time` |
| `--json` | 否 | 输出完整 JSON |

**输出（表格）**：`NOTE ID` / `CONTENT`（截断） / `CREATED AT`

#### `note +detail` — 笔记详情

```bash
zsxq-cli note +detail --note-id 444555666777
```

#### `note +edit` — 编辑笔记

```bash
zsxq-cli note +edit --note-id 444555666777 --text "新内容"
zsxq-cli note +edit --note-id 444555666777 --files new-photo.jpg
zsxq-cli note +edit --note-id 444555666777 --clear-files
```

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--note-id <id>` | **是** | 笔记 ID |
| `--text <text>` | 否 | 新内容（不传则保留） |
| `--files <paths>` | 否 | 新附件，替换原有（仅图片） |
| `--clear-files` | 否 | 清除所有附件 |
| `--json` | 否 | 输出 JSON |

**⚠️ 只能编辑自己的笔记。执行前必须确认修改内容。**

#### `note +delete` — 删除笔记

```bash
zsxq-cli note +delete --note-id 444555666777
```

**⚠️ 不可恢复。执行前必须确认笔记内容和删除意图。**

---

### 链接拼接

当用户需要分享链接时，同时提供电脑端和手机端：

**主题链接：**
- 电脑：`https://wx.zsxq.com/group/{group_id}/topic/{topic_id}`
- 手机：`https://wx.zsxq.com/mweb/views/topicdetail/topicdetail.html?topic_id={topic_id}&group_id={group_id}`

**星球链接：**
- 电脑：`https://wx.zsxq.com/group/{group_id}`
- 手机：`https://wx.zsxq.com/mweb/views/topic/topic.html?group_id={group_id}`

---

## 常见错误处理

| 错误 | 原因 | 处理 |
|------|------|------|
| `authentication failed (HTTP 401)` / `not logged in` | Token 过期或未登录 | 在 WorkBuddy 中重新连接 Connector |
| `403` / 无权限 | 无访问目标资源权限 | 确认登录账户正确，或联系星主 |
| `404` / 资源不存在 | ID 无效或资源已删除 | 用 `+list` / `+search` 重新获取 ID |
| `--<flag> is required` | 缺少必填参数 | 先用查询命令补齐 |
| `--end-time` 解析失败 | 分页时间格式错误 | 使用上一页返回的 `next_end_time` / `create_time` 原值 |
| `问题已回答` | q&a 主题已有官方回答 | 每题只能回答一次，改用 `+reply` |
| `code: 100262` | 无权限删除（非作者/星主） | 确认身份 |
| `code: 100002` | 主题不存在或已删除 | 核对 topic_id |

## 反例（不要做）

| ❌ 不要做 | ✅ 应该做 |
|----------|----------|
| 按关键词找内容时用 `+topics` 逐条翻页筛选 | 用 `topic +search` 全文搜索 |
| 查"自己最近发过什么"时逐个星球跑 `+topics` | 用 `user +footprints` 一次跨星球查询 |
| 用户只给星球名称时凭记忆猜 group_id | 先 `group +list` 或 `api call search_groups` 查到 ID |
| 名称命中多个相似星球时默认取第一个 | 列出候选让用户确认 |
| 把 `search_group_members` 当成员列表、调大 `limit` 遍历全员 | 它是关键词搜索，只用于按昵称定位 |
| 把笔记当私密备忘录写入敏感信息 | 笔记是公开内容，勿写入隐私 |
| 对非 q&a 主题使用 `+answer` | 用 `+reply` 发普通评论 |
| 不确定 topic_id / note_id 就直接执行写入/删除 | 先用 `+detail` 确认内容再操作 |

# calendar（日历与日程）

## 核心概念

- **日程（Event）**：日历中的单个条目，包含起止时间、标题、主持人、参会人等属性
- **参会人（Attendee）**：通过 openId 标识，分主持人（`--meet-organizer-open-ids`）和普通参会人（`--attendee-open-ids`）
- **会议室（Room）**：通过 `room find` 查询空闲会议室，再通过 `event create --room-id` 预定

> 关键区分：用户说"日历"通常指日程（event），而非日历容器本身。

## 意图映射

| 用户说 | 命令 |
|--------|------|
| 查看/看看日程、今天有什么安排 | `event list` |
| 日程详情 | `event get` |
| 创建/约/安排 日程/会议 | `event create` |
| 修改/改时间/更新 日程 | `event update` |
| 取消/删除 日程 | `event delete` |
| 查看参会人/谁参会 | `event participants` |
| 哪个会议室有空/找会议室 | `room find` |

## 核心工作流

### 查询日程

```bash
yzj-cli calendar event list --start 2026-05-06 --end 2026-05-06
yzj-cli calendar event get --id <EVENT_ID>
```

### 创建日程

```bash
yzj-cli calendar event create \
  --title "产品评审" \
  --start "2026-05-06T10:00:00" \
  --end "2026-05-06T11:00:00" \
  --open-id "<OPEN_ID>" \
  --meet-organizer-open-ids "<OPEN_ID>"
```

`--meet-organizer-open-ids` 必填。不知道 openId 时，先用 `contact user search` 查询。

### 修改日程

```bash
yzj-cli calendar event update --id <EVENT_ID> --open-id "<OPEN_ID>" --title "新标题"
```

只传需要修改的字段，未传字段不会变更。

### 取消 / 删除日程

```bash
# 软取消（数据保留，推荐）
yzj-cli calendar event delete --id <EVENT_ID> --open-id "<OPEN_ID>" --yes

# 彻底删除（不可恢复）
yzj-cli calendar event delete --id <EVENT_ID> --open-id "<OPEN_ID>" --hard --yes
```

> ⚠️ **危险操作**：执行前必须向用户展示操作摘要并获得明确同意，确认后带 `--yes`（未带会被 CLI 拒绝）。

### 查看参会人

```bash
yzj-cli calendar event participants --id <EVENT_ID>
# 别名：event attendees
```

### 查询可用会议室

```bash
# 个人授权（不传 --open-id）
yzj-cli calendar room find --start 2026-05-06T14:00:00 --end 2026-05-06T15:00:00

# 应用级授权（--open-id 必传）
yzj-cli calendar room find --open-id "<OPEN_ID>" --start 2026-05-06T14:00:00 --end 2026-05-06T15:00:00
# 别名：room search
```

`room find` 只查询空闲会议室，不做预定。预定需在 `event create` 时传 `--room-id`。

> **限制**：`room find` 只支持查询一天内某个时间段（`start` 和 `end` 必须在同一天），不支持跨天查询。

## 时间格式

所有时间参数统一支持：

| 格式 | 示例 |
|------|------|
| 纯日期 | `2026-05-06`（start→00:00:00，end→23:59:59） |
| 本地时间 | `2026-05-06T09:00:00` |
| 带时区 | `2026-05-06T09:00:00+08:00` |
| Unix 秒 | `1746518400`（自动 ×1000） |
| Unix 毫秒 | `1746518400000` |

超过 30 天自动分片查询并去重合并。

## event create 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` | ✅ | 主题（最长 100 字） |
| `--start` | ✅ | 开始时间 |
| `--end` | ✅ | 结束时间 |
| `--meet-organizer-open-ids` | ✅ | 主持人 openId，可重复传多个 |
| `--open-id` | 条件 | 操作用户 openId（app 授权下必填） |
| `--description` | — | 内容/描述 |
| `--room-id` | — | 会议室 ID |
| `--attendee-open-ids` | — | 参会人 openId，可重复传多个 |
| `--calendar-id` | — | 日历 ID（省略则使用主日历） |

## event update 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id` | ✅ | 日程 ID |
| `--open-id` | 条件 | 操作用户 openId（app 授权下必填） |
| `--title` | — | 新主题 |
| `--start` / `--end` | — | 新时间 |
| `--description` | — | 新描述 |
| `--room-id` | — | 新会议室 ID |
| `--add-attendee-open-ids` | — | 新增参会人 |
| `--remove-attendee-open-ids` | — | 移除参会人 |

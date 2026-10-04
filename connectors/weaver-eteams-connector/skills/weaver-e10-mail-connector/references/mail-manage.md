# 邮件管理类写操作（标记 / 待办 / 移动 / 删除 / 文件夹 / 撤回）

风险等级均为 `write`（单步执行，无 prepare/apply 链，但部分会直接改数据）。

## mail.star — 标星/取消标星

字段：`id`、`star`（"1" 标星 / "0" 取消）。

## mail.read.status — 标记单封已读/未读

字段：`id`、`read`（"1" 已读 / "0" 未读）。

## mail.read.all — 标记全部已读

字段：`folder`（文件夹 id，默认全部）。

## mail.wait.add — 创建待办/提醒

字段：`id`（邮件 id）、`title`（待办标题，缺省从邮件主题取）、`endDate`（截止日期）、`reminderWay`、`reminderTime`、`remark`。CLI 在标题缺失时自动取邮件主题。

## mail.move.folder — 移动邮件至文件夹

字段：`id`、`folder`（目标文件夹 id）。

## mail.delete.move — 逻辑删除（移至已删除，可恢复）

字段：`id`（邮件 id 或逗号分隔多个）。**这是逻辑删除，不是物理永久删除**；物理永久删除 `mail.delete.batch` 已暂缓，见 `safety-boundaries.md`。

## mail.folder.create / folder.delete — 文件夹管理

| operation | 字段 |
|---|---|
| `mail.folder.create` | `name`（文件夹名）、`id`（编辑时填） |
| `mail.folder.delete` | `id`（文件夹 id） |

## mail.recall — 撤回已发送的内部邮件

字段：`id`。仅对内部邮件有效；撤回失败按错误语义处理，不盲目重试。

## 要点

- 以上操作均为即时写，执行前在回复中向用户确认目标 id 与动作。
- 删除走逻辑删除，可恢复；如用户要求物理永久删除，说明 `mail.delete.batch` 已暂缓，不在常规 CLI 提供。
- 写请求已发出后遇到不确定结果，停止重试，按共享 `high-risk-write.md` 处理。

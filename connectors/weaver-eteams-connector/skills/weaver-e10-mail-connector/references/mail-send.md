# 发送 / 回复 / 转发 / 存草稿（prepare → apply 确认链）

发送类写操作分两步：先 `prepare` 组装请求 + 安全预检 + 输出摘要（**不发送**），用户确认后 `apply` 执行。

风险等级：`write`。`mail.send.prepare` 与 `mail.send.apply` 均须走确认链。

## 字段（prepare / apply 共用）

| 字段 | 说明 |
|---|---|
| `flag` | -1 新建 / 1 回复 / 3 转发 / 4 编辑草稿 |
| `id` | 原邮件 id（回复/转发/编辑草稿时必填） |
| `to` | 收件人（姓名/工号，逗号分隔；CLI 解析为 id） |
| `cc` / `bcc` | 抄送 / 密送 |
| `toDep` / `ccDep` / `bccDep` | 部门收件人（部门名，逗号分隔） |
| `toId` / `ccId` / `bccId` | 精确收件人/抄送/密送 id（逗号分隔，跳过解析） |
| `external` | true 表示外部邮件（用 `mail.address.search` 或原始邮箱） |
| `subject` | 主题 |
| `content` | 正文 |
| `timing` | 定时发送 YYYY-MM-DD HH:mm:ss |
| `files` / `filesizes` | 附件 fileid / 大小（逗号分隔；fileid 来自 `mail.attachment.upload`） |
| `draft` | true 存草稿（不发送） |
| `continuation` | prepare 返回的 continuation 令牌（apply 必填） |
| `confirm` | true 才执行（apply 必填） |

## 流程

```text
weaver-work-cli --profile eteams --json mail run mail.send.prepare --input-json '{"flag":"-1","to":"张三","subject":"季度汇报","content":"您好。"}'
# 返回 continuation（含摘要、收件人解析结果、是否草稿）
weaver-work-cli --profile eteams --json mail run mail.send.apply --input-json '{"continuation":"<PREPARE_CONTINUATION>","confirm":true}'
```

Windows PowerShell 与 macOS/Linux 命令一致（JSON 用单引号包裹）。

## 要点

- 回复（flag=1）/ 转发（flag=3）会自动把原邮件正文包裹进 `content`；编辑草稿（flag=4）需带 `id`。
- 收件人解析：内部人员走 `mail.person.search`/部门展开，外部走 `mail.address.search` 或原始邮箱；出现重名时 CLI 抛出候选错误并要求确认，不要臆造 id。
- `draft=true` 时 prepare 不预检发送权限，apply 走 `saveDraft`；否则 apply 走 `sendMail`。
- 附件：先用 `mail.attachment.upload` 拿到 fileid，再在 `files` 传入。
- apply 前 CLI 会重新校验 continuation、baseUrl/profile/userId 上下文一致，并（非草稿）重新预检发送权限；上下文变化会拒绝执行。
- 写请求已发出后遇到不确定结果，停止重试，按共享 `high-risk-write.md` 处理。

# 小元事务邮件（adapter）

本文件只覆盖小元 MCP 上、由 blade-agent-adapter 代发的事务邮件。发件域在服务端用 Resend 验证，调用方不持有 Resend Key，也不读本地邮件配置。企业身份由连接器的企业 Key 或飞书身份解析。

四个工具不要混用：

| 工具 | 作用 |
|---|---|
| `xiaoyuan_mail_domains` | 列出已验证发件域。只读 |
| `xiaoyuan_mail_send` | 发一封。会真实发给收件人，重复调用会再发一封 |
| `xiaoyuan_mail_sent` | 查已经发出的信，含正文。只读，默认最新 20 条 |
| `xiaoyuan_mail_replies` | 查买家回信。只读，默认最新 20 条 |

`/agent/mail/webhook` 是 Resend 回调，没有对应工具。

## 发信

1. 先调 `xiaoyuan_mail_domains`（无参数），确认要用的 `domain` 在返回列表里。
2. 核对收件人、主题和正文。多个不同买家分别发，不要把各家邮箱放进同一封。
3. 使用真实企业和产品信息，不编价格、交期或认证。先展示邮件内容；已明确授权且范围未变时再发，缺少授权时请用户确认。
4. `xiaoyuan_mail_send` 参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| to | string | ✅ | 收件人邮箱 |
| subject | string | ✅ | 主题。传入 `reply_to_id` 时不采用，改用该回信的主题 |
| text | string | - | 纯文本正文，与 html 至少一份 |
| html | string | - | HTML 正文，与 text 至少一份 |
| from_name | string | - | 显示名，空则 DealClaw |
| from_local | string | - | 发件本地部分，空则 dealclaw；非空只能是小写字母数字与 `.` `_` `-` |
| domain | string | - | 已验证发件域，空则 send.dealclaw.io |
| reply_to_id | string | - | 要回复的回信 id（`xiaoyuan_mail_replies` 返回的 id）。空则新会话 |

5. 成功回执含 Resend 邮件 id、from、to、subject、lastEvent（刚发出一般为 sent）。正文会随这封记录落库。受理不等于买家已读或已回复。
6. 失败或结果未知时先查 `xiaoyuan_mail_sent`，不要换参数连发。

## 查已发信

`xiaoyuan_mail_sent` 只查询，不会发信。按创建时间倒序，不传分页时第 1 页、每页 20 条，最大 100。飞书身份只看自己发出的；API Key 看本企业。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| page_num | number | - | 页码，从 1，默认 1 |
| page_size | number | - | 每页条数，默认 20，最大 100 |

返回含 id、resendId、from、fromEmail、to、subject、text、html、lastEvent、messageId、inReplyTo、createdTime。更早发出、当时未记正文的记录，text / html 为空。

## 查回信与续写同一会话

`xiaoyuan_mail_replies` 按创建时间倒序，不传分页时第 1 页、每页 20 条，最大 100。飞书身份只看自己发出的信对应的回信；API Key 看本企业。`send_id`、`from_email` 都可空。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| send_id | string | - | 对上的已发信 Resend id |
| from_email | string | - | 对方邮箱（入站 from） |
| page_num | number | - | 页码，从 1，默认 1 |
| page_size | number | - | 每页条数，默认 20，最大 100 |

要回复某封回信时，把该条的 id 作为 `xiaoyuan_mail_send` 的 `reply_to_id`。服务端写入会话头，主题改为该回信的主题，调用方传入的 subject 不采用。只对上过本系统发出去的信的回信会出现在结果里；陌生进站信不在此列表。

送达、已读和买家回信分开报告。`lastEvent` 是投递事件，回信以 `xiaoyuan_mail_replies` 的记录为准。

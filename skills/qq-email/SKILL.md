---
name: qq-email
description: "QQ邮箱 IMAP receive and SMTP send via Node.js scripts; credentials read from env vars QQ_EMAIL_ACCOUNT and QQ_EMAIL_AUTH_CODE. Use when a user asks to send QQ email, receive/check QQ email, forward email, or configure QQ mailbox."
description_zh: "QQ邮箱收发邮件（IMAP/SMTP），支持发信、收信、查看正文"
description_en: "Send & receive QQ Mail via IMAP/SMTP with Node.js scripts"
version: 1.0.0
allowed-tools: Read,Write,Bash
---

## 何时使用

用户要使用 **QQ 邮箱** **发邮件**、**收邮件**、**查邮件**、**代发邮件**或**配置 QQ 邮箱**时使用本 skill。

# QQ 邮箱收发

面向 QQ 邮箱：通过 IMAP 收取邮件、SMTP 发送邮件。账号与授权码**仅从环境变量读取**，不在代码或配置中硬编码。

## 凭证（环境变量）

| 变量 | 说明 |
|------|------|
| **QQ_EMAIL_ACCOUNT** | QQ 邮箱账号（完整地址，如 xxx@qq.com） |
| **QQ_EMAIL_AUTH_CODE** | QQ 邮箱授权码（在 QQ 邮箱「设置 → 账户与安全 → 安全设置」中开启 IMAP/SMTP 后生成，**非 QQ 登录密码**；勿提交到仓库） |

脚本会校验，缺失时报错并退出；请勿在终端用 `echo` 等方式检查，以免泄露授权码。

## QQ 邮箱服务器

- **IMAP**：`imap.qq.com`，端口 993（SSL）
- **SMTP**：`smtp.qq.com`，端口 465（SSL）

## 脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/send.js` | 从环境变量读凭证，用 nodemailer 连接 QQ 邮箱 SMTP 发信；支持收件人、主题、正文（CLI 参数）。 |
| `scripts/receive.js` | 从环境变量读凭证，用 imap + mailparser 连接 QQ 邮箱 IMAP 收信；支持「最近 N 条」或「最近 N 天」，输出主题、发件人、日期、**UID**、正文摘要。 |
| `scripts/get-body.js` | 按 **UID** 获取指定邮件的**完整正文**（纯文本，无摘要截断）。必须传入 `--uid`（值为收信列表中的 UID）。 |

## 发信流程

在 skill 根目录下执行（需已 `npm install`）：

```bash
node scripts/send.js <收件人> <主题> <正文>
```

正文若含空格，请用引号包裹；或只传收件人和主题，正文从 stdin 读入（见脚本 `--stdin`）。

**示例**：

```bash
node scripts/send.js "recipient@example.com" "测试主题" "邮件正文内容"
```

## 收信流程

```bash
# 收取最近 10 条（默认）
node scripts/receive.js

# 收取最近 N 条
node scripts/receive.js --limit 20

# 收取最近 N 天的邮件（如 7、30、90）
node scripts/receive.js --days 7
```

输出：每封邮件的主题、发件人、日期、**UID**（收件箱内唯一标识，用于按 UID 取正文）、正文摘要（前约 200 字），便于查看。

## 获取邮件正文

需要某封邮件的**完整正文**时，使用 `get-body.js`，传入收信列表中该邮件的 **UID**：

```bash
node scripts/get-body.js --uid 12345
```

未传 `--uid` 时会提示并退出。UID 与收件箱绑定，邮件移动或删除后可能失效。

- **输出**：完整正文输出到 stdout（纯文本；若原邮件仅有 HTML，会做简单去标签后输出）。可重定向到文件或管道给其它命令。
- **环境变量**：与收信相同，需 `QQ_EMAIL_ACCOUNT`、`QQ_EMAIL_AUTH_CODE`。

## 可选能力（与「收取选项」对应）

- **收取时间范围**：通过 `--days 7` / `--days 30` / `--days 90` 使用 IMAP SINCE 条件。
- **收取「我的文件夹」**：当前脚本默认 INBOX；若需自定义文件夹，可扩展脚本中的 `openBox`（如 `openBox('我的文件夹', ...)`）。

## 安全提醒

- QQ 邮箱授权码需在「设置 → 账户」中开启 IMAP/SMTP 服务后生成，与 QQ 登录密码不同，不要混淆。
- 不要将 `QQ_EMAIL_ACCOUNT`、`QQ_EMAIL_AUTH_CODE` 的真实值写入代码或提交到仓库；仅通过环境变量或本地 `.env` 配置。

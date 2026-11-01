# 邮件撰写、发送与投递查询

用户要写开发信、发报价单、发送 HTML 邮件或附件、查投递状态时使用。邮件与 AI 猎客 WhatsApp 是并列通道。查到邮箱后可继续起草并发送邮件；不用先创建 AI 猎客任务或开通 WABA。

## 执行路径

1. 核对收件人、发件身份、主题、正文、附件和回复地址。用户已给出的信息直接使用；多个不同买家通常分别发信，避免把各家邮箱暴露在共同收件人列表。
2. 起草文本/HTML 正文并准备用户指定附件。使用真实企业和产品信息，不编价格、交期或认证。先展示邮件内容，按用户已给予的发送授权执行；缺少必要授权时请用户确认。
3. 优先使用连接器实际提供的邮件发送工具。没有对应远程工具时，可调用本 Skill 附带的 `scripts/mail.py`，通过已配置的 Resend 发件身份发送。
4. 先用 `--dry-run` 预览请求，随后发送并保存邮件 ID。发送失败或结果未知时不换通道盲目重发；检查原回执，使用同一幂等键处理同一次发送。
5. 用户要查投递时，按邮件 ID 查询 `last_event`。`delivered` 表示收件服务器已接收，不表示买家已读或回复。查看回信走 `replies.md` 的入站消息流程。

## 随包邮件脚本

企业希望自动取得发件身份时，先查询实际提供的企业邮件账户／授权工具，由服务端根据企业 Key 选择允许的发件账号并代发，或返回已授权的配置状态。小元企业 Key 不等于 Resend Key。已有管理员配置时可直接使用以下脚本，不要求重复配置；企业自动授权与本地自有账号两条使用路径都保留。

以本 Skill 的目录为工作目录，使用 Python 3.8+：macOS/Linux 通常是 `python3`，Windows 按已安装解释器使用 `python`。只依赖标准库。不要把脚本调用和 MCP 发送同时用于同一封信。

脚本读取管理员配置的 `MAIL_API_KEY` / `RESEND_API_KEY`、`MAIL_FROM`、可选的 `MAIL_REPLY_TO`；或读取 `MAIL_CONFIG_DIR` 指定的配置目录，默认 `~/.config/xiaoyuan-mail/config.json`。连接器的企业 `API_KEY` 与邮件服务凭据是不同凭据，不能混用。配置缺失时只告知管理员补齐哪些项，不让用户把密钥粘贴进对话，也不读取其他企业的配置。

| 命令 | 用途 |
|---|---|
| `python scripts/mail.py config` | 查看有效配置和来源，密钥不显示 |
| `python scripts/mail.py init --from '销售团队 <sales@example.com>'` | 保存已授权发件身份；支持 `--reply-to`、`--api-base`，`--show` 只查看 |
| `python scripts/mail.py doctor` | 检查运行环境、配置及域名查询权限；诊断结果不等于实际发送回执 |
| `python scripts/mail.py domains` | 查询发件域名与验证状态；查询权限不足不代表发送权限一定不足 |
| `python scripts/mail.py send --to buyer@example.com --subject '产品资料' --text-file body.txt --attach catalog.pdf --dry-run` | 预览文本与附件；不调用发信接口，也不需要发信密钥 |
| `python scripts/mail.py send --to buyer@example.com --subject '产品资料' --text-file body.txt --attach catalog.pdf --idempotency-key '<本次发送唯一键>' --wait` | 实际发送，并在本次调用内短时查询投递结果 |
| `python scripts/mail.py get --id '<真实邮件ID>'` | 查询这封邮件的投递状态 |

`send` 支持重复的 `--to`、文本或 `--text-file`、HTML 或 `--html-file`、重复的 `--attach`、`--reply-to`、`--tag`、`--dry-run` 和 `--wait`。长正文使用 UTF-8 文件；HTML 邮件同时提供纯文本版本。附件总大小以邮件服务的限制为准。

为一次已确认发送分配唯一幂等键。同一封信在服务商有效幂等窗口内重试时复用原键和原内容；新发送使用新键。`--wait` 是本次调用内的投递查询，不是持续收信监控。脚本本身不接收入站邮件，也不获取共享平台密钥。

## 配置与故障恢复

配置优先级为命令行显式参数、环境变量、本地配置文件。管理员可用 init 设置 api-key、from、reply-to、api-base；普通对话不展示密钥。MAIL_CONFIG_DIR 可指定已有的授权配置目录，MAIL_API_BASE 可使用已批准的自有兼容网关，缺省为 Resend。使用 HTTP API，不依赖 SMTP 的 25／465／587 端口。

| 现象 | 处理 |
|---|---|
| 401 | 邮件服务凭据无效或轮换，更新邮件授权，不误改企业 MCP Key |
| 403 | 区分权限拒绝与响应中明确的 1010 边缘拦截，不一律归因于网络 |
| 422 | 核对发件域名验证、收件地址、附件和请求格式 |
| 429／5xx／超时 | 查询原发送结果；需要重试时沿用同一封邮件的幂等键，无幂等键不自动重发 |
| 附件找不到、中文乱码 | 使用当前系统的真实文件路径及 UTF-8 文本文件，不照搬其他系统路径 |
| 投递后未进收件箱 | delivered 只表示收件服务器已收；排查域名认证、信誉和内容，不能保证进入主收件箱 |

脚本输出 JSON，发送成功须 ok=true 且有真实 id；get／wait 返回 delivered、bounced、complained、failed、canceled 或未决状态。被退信或投诉不能说成成功送达。doctor／domains 需要相应查询权限；只有发送权限的凭据可能无法查域名，不能据此断言无法发信。支持自有 Resend 账号和自有兼容端点，不依赖其他宿主运行环境。

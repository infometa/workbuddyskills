---
name: "dealclaw-mail-send"
description: "跨平台邮件发送 CLI（纯标准库，零第三方依赖，Windows / macOS / Linux 同一套命令）。通过 Resend HTTP API 发信并跟踪投递终态。当用户说「发一封邮件、发送邮件、发信、给某人发邮件、发个 HTML 邮件/贺卡/通知、通知客户/买家、send email、send a mail、邮件带附件」，或需要「查邮件投递状态、邮件发不出去、发信报错 401/403/422、SMTP 连不上、邮件进垃圾箱、验证发信域名、配置发信账号」时使用。支持 HTML+纯文本双版本（multipart/alternative）、附件（base64，单个≤40MB）、收件人多选、投递状态轮询、标签分类、dry-run 预演、环境自检 doctor、以及从 DealClaw 平台接口自动获取发信凭据。发件域名与 API 端点均可配置，因此也能用于任意自有 Resend 账号。"
agent_created: true
version: "1.0.0"
---

# dealclaw-mail-send · 跨平台邮件发送

一个**自包含**的发信工具：把邮件通过 Resend HTTP API 发出去，并跟踪投递终态。
目标是「别人拿到这个目录就能直接用」，不依赖任何本机上下文、不依赖其他技能包。

## 为什么用 HTTP API 而不是 SMTP

- **不碰 25/465/587 端口**：多数云主机与办公网封了这些端口，SMTP 常年连不通。
- **不依赖第三方库**：只用标准库 `urllib`，没有 `requests` / `smtplib` 的踩坑面。
- **能拿到投递事件**：`delivered` / `bounced` / `complained` 可查，SMTP 发完即失联。

## 零、它保证什么（跨平台的硬约束）

| 约束 | 做法 |
|---|---|
| 无平台绑定 | 不出现任何硬编码盘符或用户名；配置目录由 `Path.home()` 派生 |
| 无 Windows 专有模块 | 不用 `fcntl` / `msvcrt` / `winreg` / `os.startfile` |
| 无第三方依赖 | 只用 `argparse/json/urllib/base64/pathlib/mimetypes/re/time` |
| Python 版本 | **3.8+**（源码已用 3.8 grammar 校验通过，无 3.9+/3.10+ 语法） |
| 编码安全 | 文件读写显式 `encoding="utf-8"`；`stdout` 强制 UTF-8，规避 Windows 默认 cp936 乱码 |

## 一、快速开始

```bash
# 1) 配置发信身份（三选一，见下节）
python mail.py init --api-key re_xxxxxxxx --from 'Your Name <you@yourdomain.com>'

# 2) 自检：能不能发、缺什么，一条命令说清
python mail.py doctor

# 3) 发信
python mail.py send --to someone@example.com --subject '你好' --text '正文' --wait
```

> Windows 上把 `python` 换成你的解释器绝对路径即可，命令其余部分完全一致。
> 脚本无执行权限要求，用 `python mail.py` 调用，不必 `chmod +x`。

## 二、配置的三种方式

优先级：**命令行参数 > 环境变量 > 配置文件**。

### 方式 A：配置文件（推荐，一次配好）

```bash
python mail.py init --api-key re_xxx --from 'Your Name <you@yourdomain.com>'
python mail.py config          # 查看生效配置及来源，key 自动打码
```

写入位置（三平台统一）：`~/.config/dealclaw-mail-send/config.json`
- Windows：`C:\Users\<你>\.config\dealclaw-mail-send\config.json`
- macOS / Linux：`/Users/<你>/.config/...` 与 `/home/<你>/.config/...`

可用 `MAIL_CONFIG_DIR` 覆盖目录。POSIX 系统上文件权限会设为 `600`。

### 方式 B：环境变量

```bash
export RESEND_API_KEY=re_xxx          # 或 MAIL_API_KEY
export MAIL_FROM='Your Name <you@yourdomain.com>'
```

### 方式 C：每次传参

```bash
python mail.py send --api-key re_xxx --from '...' --to ... --subject ... --text ...
```

### 环境变量一览

| 变量 | 用途 | 默认 |
|---|---|---|
| `MAIL_API_KEY` / `RESEND_API_KEY` | 发信凭据 | 无 |
| `MAIL_FROM` | 默认发件人（`显示名 <地址>`） | 无 |
| `MAIL_REPLY_TO` | 默认回复地址 | 无 |
| `MAIL_API_BASE` | API 端点，可换成自建网关 | `https://api.resend.com` |
| `MAIL_CONFIG_DIR` | 配置文件目录 | `~/.config/dealclaw-mail-send` |
| `MAIL_PLATFORM_API_BASE` | 平台凭据接口端点（`key` 子命令用） | 见「五、平台凭据」 |

## 三、命令参考

| 命令 | 作用 |
|---|---|
| `init` | 写入/更新配置；`--show` 只看不写 |
| `config` | 显示生效配置及其来源（key 打码） |
| `doctor` | 环境自检：Python 版本、编码、配置、网络、key 有效性、可用域名 |
| `domains` | 列发信域名与验证状态（顺带校验 key） |
| `send` | 发信 |
| `get --id <id>` | 按邮件 id 查投递状态 |
| `key` | （可选）从 DealClaw 平台接口取凭据 |

### send 的参数

| 参数 | 说明 |
|---|---|
| `--to` | 收件人。**可重复**，也支持逗号分隔：`--to a@x.com,b@y.com` |
| `--subject` | 主题（必填） |
| `--from` | 发件人，形如 `'Your Name <you@yourdomain.com>'` |
| `--text` / `--text-file` | 纯文本正文 / 从 UTF-8 文件读 |
| `--html` / `--html-file` | HTML 正文 / 从 UTF-8 文件读（`-` 表示读 stdin） |
| `--reply-to` | 回复地址 |
| `--tag` | 打标签，便于在后台按来源筛选 |
| `--attach` | 附件路径，**可重复**，单个 ≤40MB |
| `--wait` | 轮询到投递终态再返回 |
| `--dry-run` | 只打印请求体（附件内容打码），不发送 |

**长正文请走文件**：`--html-file card.html`。命令行传大段 HTML 在 Windows 上易撞引号转义与编码问题。

**HTML + 纯文本同给** → 自动发 `multipart/alternative`：支持 HTML 的客户端渲染 HTML，
纯文本客户端与反垃圾引擎降级读 `text`。**强烈建议两者都给**，纯 HTML 邮件的垃圾箱命中率更高。

### 示例

```bash
# 带附件 + 等投递终态
python mail.py send --to client@example.com --subject '报价单' \
  --text '见附件' --attach ./quote.pdf --wait

# HTML 贺卡，带纯文本兜底
python mail.py send --to client@example.com --subject '中秋快乐' \
  --html-file card.html --text '中秋快乐，祝商祺。'

# 先预演，确认无误再发
python mail.py send --to client@example.com --subject t --text b --dry-run
```

## 四、输出约定

所有命令输出 **JSON**，便于脚本/Agent 直接解析。

**退出码**：`0` 成功 · `1` 运行失败（API 报错、投递失败）· `2` 用法或配置错误。

**`send` 成功的关键判据是 `ok: true` 且返回了 `id`**：

```json
{ "ok": true, "http": 200, "id": "01a0c852-...", "final": { "last_event": "delivered", "waited_s": 5.0 } }
```

`--wait` 的终态取值：`delivered`（已投递）· `bounced`（退信）· `complained`（标记垃圾）· `failed` ·
`canceled`；超时会返回 `"timeout": true` 与当时的 `last_event`。

⚠️ **`delivered` 只代表对方服务器已接收，不代表进了收件箱。** 是否落进垃圾箱必须肉眼确认。

## 五、平台凭据（可选能力）

配置了 DealClaw 平台租户时，可让工具自己去取凭据，省掉手工贴 key：

```bash
python mail.py key --supplier-id <你的ID> --save --from 'Your Name <you@yourdomain.com>'
```

- `--save` 写入配置文件（**不打印明文 key**）；不加则打印明文供你复制到环境变量。
- `--open-id` 缺省为 `ou_<supplier-id>`；`MAIL_PLATFORM_API_BASE` 可覆盖端点。

⚠️ **这是一项供应商专有能力，把它从技能包里删掉不影响其余功能**：
`doctor` / `domains` / `send` / `get` 全部只依赖 `MAIL_API_BASE` 与一把 key，
换用你自己的 Resend 账号即可，无需本节的任何内容。

## 六、故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `HTTP 403` + `error code 1010` | 请求被 Cloudflare 边缘拦截，**不是权限问题** | 检查是否带了浏览器 User-Agent；本工具已内置，若你自行改写请求需保留 |
| `HTTP 401` | key 无效或已被轮换 | 重新取一把 key |
| `HTTP 422` | 发件域名未验证，或字段格式不对 | 跑 `python mail.py domains` 看 `usable` 列表，发件地址必须用已验证域名 |
| `HTTP 429` | 触发限流 | 工具已对 429/5xx 自动指数退避重试；仍失败则降低发送频率 |
| `file not found` 且提示 POSIX 风格路径 | Windows 上 `/tmp/x` 被解释为盘符相对路径 | 改用 `C:\...` 绝对路径，或用 `pwd -W` 取得对应 Windows 路径 |
| 正文中文乱码 | 文件不是 UTF-8 | 转成 UTF-8（无 BOM）再发；工具对非 UTF-8 文件会明确报错 |
| 邮件进垃圾箱 | 纯 HTML、正文含强营销词、域名信誉不足 | 补 `--text` 纯文本版本；控制发送频率；检查域名 SPF/DKIM |

自检优先：**任何异常先跑 `python mail.py doctor`**，它会把「能不能发、缺什么」一次说清。

## 七、安全

- API key 是**账号级**发信凭据，拿到即可用该账号下任意已验证域名发信。本工具**从不硬编码**，
  只从环境变量、配置文件或命令行读取；`init --show` 与 `config` 输出时一律打码。
- **不要**把配置文件提交进 Git 仓库；不要把自己的 key 贴进聊天记录或工单。
- 本工具**不做**发信前的业务闸门（如「租户是否允许发信」）。若你的业务需要，
  请在调用方自行加校验——不要把访问控制寄托在工具上。

## 八、版本与兼容

- `mail.py --version` 输出版本号。
- 目标运行时：Python 3.8+，无第三方依赖，无平台绑定。
- 界面语言为中文；`doctor` / `config` / `domains` 的输出结构稳定，字段名可直接用于脚本判断。

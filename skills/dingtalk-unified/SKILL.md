---
name: dingtalk-unified
description: 钉钉 CLI 全能套件，基于官方 DingTalk Workspace CLI（dws）操作钉钉消息、群聊、通讯录、日历、待办、审批、考勤、日志、DING、AI 表格、钉钉文档、钉盘、AI 听记、邮箱和开放平台文档。用户需要在钉钉内查找联系人、发消息、建群、管理日程、创建待办、处理审批、查看考勤、读写文档、操作 AI 表格、搜索会议听记或调用钉钉开放平台能力时使用。
description_zh: 钉钉 CLI 套件，覆盖消息、日历、待办、审批、考勤、日志、文档、表格、AI 表格、钉盘、AI 听记、邮箱等产品能力，具体命令以 dws schema/help 为准
description_en: DingTalk CLI suite powered by dws, covering messages, calendar, todo, approvals, attendance, reports, docs, AI tables, drive, meeting minutes, mail and more
version: 1.0.5
dws_cli_version: ">=1.0.26"
---

# 钉钉套件（DingTalk Unified）

通过官方 `dws`（DingTalk Workspace CLI）调用钉钉产品能力。`dws` 的产品域和命令数随版本动态更新，本 Skill 不把静态命令表当作唯一真相；执行时以 `dws --help`、`dws <domain> --help` 和 `dws schema` 为准，并提供意图路由、安全策略、授权策略、命令发现策略和错误恢复策略。

## 使用前置流程

### Step 1：确认 dws 可用

优先使用系统 PATH 中的 `dws`：

```bash
dws version --format json
```

如果命令不存在，先安装官方 npm 包：

```bash
npm install -g dingtalk-workspace-cli
```

安装后再次执行：

```bash
dws version --format json
```

要求版本满足 `>=1.0.26`。低版本可能缺少 ndjson/csv 输出格式、--content/--content-file flag、群消息 --title 必填、auth 凭证按版本分区、schema sticky flag splitting 等能力和修复。

### Step 2：检查登录状态

```bash
dws auth status --format json
```

- 已登录：继续执行用户请求。
- 未登录 / token 失效：进入授权流程。

权限三层模型：

1. OAuth 登录：解决“当前用户是谁”。
2. 组织 CLI 访问：解决“企业/组织是否允许 CLI 访问数据”。
3. 业务 PAT scope：解决"某个具体动作是否被允许"，例如读取钉钉文档需要 `doc:read`。

不要把"已登录"误判为"所有业务权限都已授权"。

凭证存储说明（v1.0.29+）：`dws` 按 CLI 版本分区存储 OAuth 凭证（`app.json` 按版本隔离），多版本共存时不会互相覆盖。升级后首次使用可能需要重新登录。

授权触发规则：

- 用户只是问“登录状态 / 是否已登录”时，只汇报状态，不主动发起登录。
- 用户明确说“登录 / 授权 / 发起授权流程 / 继续登录 / 帮我授权 / 开始授权”时，**不要停在状态汇报，也不要再问是否继续**；授权不是危险操作，必须在同一轮直接执行 Step 3。
- 业务命令因为 `not_authenticated`、`AUTH_TOKEN_EXPIRED`、`USER_TOKEN_ILLEGAL` 等认证错误失败时，必须直接进入 Step 3，而不是反复重试业务命令。

### Step 2.5：中文 / CJK 参数安全

当前 WorkBuddy shell 环境可能是 `LC_CTYPE=C` / `LANG=""`，直接在 Bash 参数里传中文可能导致 `dws` 输出看起来乱码，甚至把错误编码写入用户可见字段（如待办标题、文件名、文档名、消息内容）。涉及中文 / CJK 内容时先检查：

```bash
locale
```

如果不是 UTF-8 locale，避免直接写 `dws ... --title "中文"`。改用 Python 以 Unicode 字符串和 `subprocess.run([...])` 参数列表调用 `dws`，并设置 UTF-8 环境：

```bash
PYTHONUTF8=1 /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -c 'import subprocess, os, sys; title="\u8bc4\u5ba1\u7ed3\u8bba"; r=subprocess.run(["dws","todo","task","update","--task-id","<taskId>","--title",title,"--format","json"], env={**os.environ,"LC_ALL":"en_US.UTF-8","LANG":"en_US.UTF-8"}, capture_output=True); sys.stdout.buffer.write(r.stdout); sys.stderr.buffer.write(r.stderr); raise SystemExit(r.returncode)'
```

验证中文字段时，不要只看终端渲染；可读取 JSON 后用 `unicode_escape` 比对真实内容。

### Step 3：完成授权（Skill 自闭环方案）

本 Skill 不依赖 WorkBuddy Runtime 改造即可完成授权。按以下顺序执行：

#### A. 默认方案：浏览器跳转登录

优先执行官方 loopback 登录，让 `dws` 自动打开浏览器完成钉钉 OAuth：

```bash
dws auth login
```

执行要求：

1. 保持命令运行，等待用户在浏览器/钉钉页面完成授权。
2. 授权完成后执行 `dws auth status --format json` 验证状态。
3. 登录状态有效后，进入“初始化基础权限授权”说明：告知用户读取钉钉文档还需要第二段 `doc:read` 业务授权，并按用户选择发起一次性或长期授权。
4. 如果浏览器未自动打开、loopback 失败、远程环境不可用或命令长时间无结果，立即切到 B 方案，不要反复重试。

#### B. 兜底方案：设备流授权链接 + 授权码

执行：

```bash
dws auth login --device
```

从输出中提取并清晰展示给用户：

- 授权页：`https://login.dingtalk.com/oauth2/device/verify.htm`
- 授权码：例如 `ABCD-EFGH`
- 带授权码的完整链接：`https://login.dingtalk.com/oauth2/device/verify.htm?user_code=ABCD-EFGH`

推荐操作方式：

1. 如果输出了完整链接，直接告诉用户点击该链接完成授权；在 macOS 本地环境也可以执行 `open "<complete_url>"` 自动打开浏览器。
2. 如果完整链接不可用，则让用户打开授权页并输入授权码。
3. 保持 `dws auth login --device` 命令轮询，直到授权成功、失败或过期。
4. 授权完成后执行：

```bash
dws auth status --format json
```

5. 登录状态有效后，进入“初始化基础权限授权”说明：告知用户读取钉钉文档还需要第二段 `doc:read` 业务授权，并按用户选择发起一次性或长期授权。

#### C. 初始化基础权限授权

首次 OAuth 登录成功后，读取钉钉文档通常还需要第二段业务授权 `doc:read`。初始化流程必须把这个预期说清楚：

```text
钉钉初始化需要完成两步：
1. 登录钉钉账号
2. 授予 WorkBuddy 读取钉钉文档权限 doc:read
```

初始化阶段可请求长期授权，避免每次读文档都被中断；但必须明确告诉用户这可能是第二次授权确认，不是并入同一次 OAuth：

```bash
export DINGTALK_DWS_AGENTCODE="workbuddy"
export DWS_CHANNEL="workbuddy"
dws pat chmod doc:read --agentCode workbuddy --grant-type permanent --format json
```

如果用户明确只想临时授权，改用一次性授权：

```bash
dws pat chmod doc:read --agentCode workbuddy --grant-type once --format json
```

执行规则：

1. 不要把 `doc:read` 说成并入同一次 OAuth；它可能触发第二次授权确认。
2. `doc:read` 属于低风险只读 PAT，初始化时可以请求 permanent，但要先说明用途：用于后续读取钉钉文档正文，减少重复授权打断。
3. 如果组织策略不允许授权或命令返回权限错误，记录失败原因，不阻断非文档类任务；但在执行 `doc read`、`doc search`、读取文档内容等文档读取任务前必须再次补授权。
4. `doc:read` 只覆盖读取钉钉文档；写文档、删除块、移动/重命名等写操作仍按需单独授权，并遵守危险操作确认规则。

#### D. 可选方案：二维码

若用户明确要求二维码，或链接无法点击，可把 B 方案的完整链接转换成二维码图片/终端二维码。仅在本机已有二维码工具时执行，例如 `qrencode`；不要为了生成二维码额外安装依赖。没有二维码工具时，直接使用 B 方案的完整链接和授权码。

#### E. 已登录后的权限授权：host-owned PAT

`host-owned PAT` 不是首次登录方案，只用于已登录后遇到业务权限/行为授权拦截时处理。执行业务命令前可注入：

```bash
export DINGTALK_DWS_AGENTCODE="workbuddy"
export DWS_CHANNEL="workbuddy"
```

如果业务命令返回 exit code `4`，或 stderr/stdout 中出现 `PAT_MEDIUM_RISK_NO_PERMISSION`、`requiredScopes`、`grantOptions` 等字段：

1. 同时检查 stdout 和 stderr，优先解析 JSON key，不要依赖可能乱码的中文 message。
2. 提取 `requiredScopes[].scope` 和 `grantOptions`。
3. 向用户说明缺少哪些权限、一次性授权和长期授权的区别。
4. 低风险只读 scope 可建议 `once`；中高风险或写权限必须先解释数据范围和风险。
5. 用户确认后执行：

```bash
dws pat chmod <scope>... --agentCode workbuddy --grant-type once --format json
```

6. `--grant-type session` 只有在已知 `--session-id` 时才能使用；不要执行缺少 `--session-id` 的旧命令。格式为：

```bash
dws pat chmod <scope>... --agentCode workbuddy --grant-type session --session-id <id> --format json
```

7. 同一工作流已知会连续触发多个 scope 时，可在用户确认后一次性合并授权，减少反复中断。例如钉盘上传通常需要：

```bash
dws pat chmod drive:upload-info drive:commit --agentCode workbuddy --grant-type once --format json
```

8. 只有用户明确要求长期授权时，才改用 `--grant-type permanent`。
9. 授权完成后 replay 原始业务命令。

#### F. 常用操作 PAT 预判基线（2026-05-14 测试企业探针）

说明：`dws schema` 能给出命令结构和敏感操作标记，但不总是静态暴露 host-owned PAT scope。最可靠信号仍是运行时返回 `PAT_MEDIUM_RISK_NO_PERMISSION.requiredScopes`。对固定工作流，可提前合并申请已知 scope。

| 常用场景 | 探针结果 / 预判 | 建议授权方式 |
|---|---|---|
| 通讯录当前用户/搜人 | 本轮读探针未触发额外 PAT | 首次登录后直接可用 |
| 待办创建/读取/更新/完成 | 本轮写探针未触发额外 PAT | 首次登录后直接可用 |
| 待办删除 | 已实测需要 `todo.task:delete` | 删除类高影响操作，每次或按场景单独确认 |
| 日历列表/详情 | 本轮读探针未触发额外 PAT | 首次登录后直接可用 |
| 日历创建/更新/删除 | 已实测分别需要 `calendar.event:create`、`calendar.event:update`、`calendar.event:delete` | 可做“日历管理包”；删除仍需操作确认 |
| 钉盘列表/详情 | 本轮读探针未触发额外 PAT | 首次登录后直接可用 |
| 钉盘建文件夹/下载 | 已实测需要 `drive:mkdir`、`drive:download` | 按场景授权 |
| 钉盘上传文件 | 已实测需要 `drive:upload-info` + `drive:commit`；HTTP PUT 本身不走 PAT | 用户确认后一次性 `pat chmod` 两个 scope，再重放上传 |
| 钉钉文档创建/信息/搜索/列表/重命名 | 本轮探针未触发额外 PAT | 首次登录后直接可用或按需执行 |
| 钉钉文档读取/全文更新/块插入 | 已实测需要 `doc:read`、`doc:update`、`doc.block:insert`；当前 `doc update` CLI flag 与 schema 存在不一致，建议优先用 block API 写入 | 可做“文档读写包”，但写入前展示摘要 |
| 群聊搜索/未读会话 | 本轮读探针未触发额外 PAT | 首次登录后直接可用 |
| 发送单聊/群消息 | 已实测单聊和群聊发送均需要 `chat.message:send`；v1.0.28+ 群消息也必须传 `--title` | 消息发送属于外部可见写操作，必须操作前摘要 + 用户确认 |
| 邮箱列表 | 本轮读探针未触发额外 PAT | 首次登录后直接可用 |
| 邮件发送 | 已实测自发自收需要 `mail.message:send` | 邮件发送必须操作前摘要 + 用户确认 |
| OA 可见表单、日志模板、AI 听记列表 | 本轮读探针未触发额外 PAT | 首次登录后直接可用 |
| 考勤汇总/打卡记录 | 已实测需要 `attendance:summary`、`attendance.record:get`；考勤规则查询本轮未触发额外 PAT | 只在用户请求考勤时按需授权 |
| AI 表格 Base 列表/详情 | 本轮读探针未触发额外 PAT | 首次登录后直接可用 |
| AI 表格 Base 创建/更新/删除 | 已实测需要 `aitable.base:create`、`aitable.base:update`、`aitable.base:delete` | 创建/更新可做场景包；删除必须单独确认 |
| 其他删除/撤回/拒绝/移除成员/覆盖等高影响操作 | schema `sensitive=true` 或危险清单命中 | 必须单独确认；不应首次安装预授权 |

首次安装不建议“一次性申请所有常用权限”。推荐最小 OAuth 登录 + 按场景延迟授权；可为高频工作流做授权包（如“钉盘上传包：`drive:upload-info`、`drive:commit`”），由用户首次使用该场景时一键确认。

## 严格禁止

- 不要绕过 `dws` 直接用 `curl`、HTTP API 或浏览器自动化操作钉钉业务数据。
- 不要把 AppKey、AppSecret、access token、refresh token 写入 `SKILL.md`、references 或日志。
- 不要编造 userId、openConversationId、baseId、tableId、processInstanceId、taskId、fileId 等标识符；必须从 `dws` 命令返回中提取。
- 不要猜测字段名、枚举值或参数格式；不确定时先运行 `dws <command> --help` 或 `dws schema <path>`。
- 不要在未获得用户确认时执行删除、撤回、拒绝、移除成员、批量修改等高影响操作。

## 严格要求

- 所有业务命令默认加 `--format json`，以便解析结构化输出。`--format` 支持 `json|table|raw|pretty|ndjson|csv`（v1.0.26+）；对大列表建议用 `ndjson` 流式输出。
- 写操作优先使用 `--dry-run` 预览；需要真正执行时再加 `--yes`。
- 危险操作必须先展示操作摘要（操作类型、目标对象、影响范围），用户明确确认后才执行。
- 单次批量写入/删除/修改不超过 30 条记录；超过时拆批并逐批确认。
- 参考文档与实际 CLI 输出冲突时，以 `dws <command> --help` 和 `dws schema <path>` 为准。
- 认证或权限错误出现后，停止反复尝试业务 API，先完成授权诊断。

## 执行策略

- 简单状态类命令可直接执行，例如 `dws auth status --format json`、`dws version --format json`。
- 复杂命令、写操作、上传/下载、审批、日历、群聊、文档块级编辑、AI 表格字段/记录操作，执行前先查 `dws <domain> --help` 或 `dws <domain> <group> --help`；必要时再查 `dws schema <path>`。
- 写操作采用 `--dry-run`（如命令支持）→ 操作摘要 → 用户确认 → `--yes` 执行。
- 基于 help/schema 修正参数最多 1 次；加 `--verbose` 诊断最多 1 次；仍失败则汇报错误和下一步，不绕过 `dws`。
- 输出解析同时检查 stdout 和 stderr。`auth login`、`doctor`、`pat` 类命令可能不是纯 JSON；遇到非 JSON 输出时提取 URL、user code、error code、requiredScopes 等结构化线索。
- 默认分页、字段裁剪和摘要化；不要大段回显邮件、聊天、文档正文等敏感内容，除非用户明确要求。

## 产品总览

`dws` 的产品域会随版本动态变化。下表是核心路由参考，不是完整命令契约；实际可用产品和参数以 `dws --help`、`dws <domain> --help`、`dws schema` 为准。

| 产品 | 命令 | 用途 | 参考文件 |
|---|---|---|---|
| AI 表格 / 多维表 | `aitable` | Base、数据表、字段、记录、视图、附件、图表、仪表盘、导入导出、模板搜索 | [aitable.md](./references/products/aitable.md) |
| 普通表格 / 在线表格 | `sheet` | 普通电子表格、工作表、单元格区域读写；若当前 dws 版本未暴露该域，以 `dws schema` 为准 | 动态域，先查 `dws sheet --help` |
| 考勤 | `attendance` | 打卡记录、排班查询、考勤规则、汇总统计 | [attendance.md](./references/products/attendance.md) |
| 日历 | `calendar` | 日程、参与者、会议室、闲忙查询、时间建议 | [calendar.md](./references/products/calendar.md) |
| 群聊与机器人 | `chat` / `im` / `bot` | 搜索群、建群、群成员管理、改群名、机器人群发、单聊、撤回、Webhook；若当前 dws 暴露独立 `bot` 域，先查 `dws bot --help` | [chat.md](./references/products/chat.md) |
| 通讯录 | `contact` | 当前用户、搜索用户、用户详情、手机号、部门、部门成员 | [contact.md](./references/products/contact.md) |
| 开放平台文档 | `devdoc` | 搜索钉钉开放平台开发文档 | [devdoc.md](./references/products/devdoc.md) |
| DING | `ding` | 发送/撤回 DING 消息 | [ding.md](./references/products/ding.md) |
| 钉钉文档 | `doc` | 搜索、浏览、读写、块级编辑、文件创建、复制、移动、重命名 | [doc.md](./references/products/doc.md) |
| 文档评论 | `doc-comment` / `doc comment` | 文档评论、回复、评论列表；具体命令路径随版本变化，先查 `dws doc --help` 和 `dws doc-comment --help` | 动态域，先查 help/schema |
| Wiki / 知识库 | `wiki` | 知识库、空间、页面管理；若当前版本未暴露该域，说明 CLI 暂不可用 | 动态域，先查 `dws wiki --help` |
| 钉盘 | `drive` | 文件列表、元数据、文件夹、上传、下载 | [drive.md](./references/products/drive.md) |
| AI 听记 | `minutes` | 听记列表、摘要、关键词、转写、待办、思维导图、发言人、热词、上传 | [minutes.md](./references/products/minutes.md) |
| OA 审批 | `oa` | 待审批、我发起的、表单模板、详情、审批流水、同意、拒绝、撤销 | [oa.md](./references/products/oa.md) |
| 日志 | `report` | 按模板创建、收件箱、已发送、模板查看、详情、已读统计 | [report.md](./references/products/report.md) |
| 邮箱 | `mail` | 邮箱地址、KQL 邮件搜索、邮件详情、发送邮件 | [mail.md](./references/products/mail.md) |
| 待办 | `todo` | 创建、查询、修改、标记完成、删除，含优先级、截止时间、循环 | [todo.md](./references/products/todo.md) |
| Raw API | `api` | 通过 `dws api` 调用钉钉 OpenAPI，需自建应用凭证 | [global-reference.md](./references/global-reference.md) |

## 意图路由

- 用户提到“普通表格 / 在线表格 / Sheet / 单元格 / 工作表”且没有 Base、记录、字段等多维表语义 → `sheet`
- 用户提到“AI 表格 / 多维表 / Base / 记录 / 字段 / 视图 / 图表 / 仪表盘” → `aitable`
- 用户只说“创建一个表格”时，默认先按普通表格 `sheet` 判断；如果用户提到字段、记录、视图、Base，再切到 `aitable`。
- 用户提到“考勤 / 打卡 / 排班” → `attendance`
- 用户提到“日程 / 日历 / 会议室 / 约会 / 时间建议 / 闲忙” → `calendar`
- 用户提到“群聊 / 建群 / 群成员 / 群管理 / 机器人发消息 / Webhook / 通知” → `chat`；若当前版本暴露独立 `bot` 域且用户明确说机器人管理，先查 `dws bot --help`
- 用户提到“通讯录 / 同事 / 部门 / 组织架构 / 手机号查人” → `contact`
- 用户提到“开放平台 / API / 调用错误 / 接入文档” → `devdoc`
- 用户提到“DING / 紧急消息 / 电话提醒” → `ding`
- 用户提到“钉钉文档 / 云文档 / 读写文档 / 块级编辑” → `doc`
- 用户提到“文档评论 / 评论 / 回复评论” → 优先查 `doc-comment` 或 `doc comment`
- 用户提到“知识库 / Wiki / 空间 / 页面树” → `wiki`
- 用户提到“钉盘 / 云盘 / 文件上传下载 / 文件夹” → `drive`
- 用户提到“听记 / AI 听记 / 会议纪要 / 转写 / 摘要 / 思维导图 / 发言人 / 热词” → `minutes`
- 用户提到“邮箱 / 邮件 / 发邮件 / 收邮件 / 搜邮件” → `mail`
- 用户提到“审批 / 请假 / 报销 / 出差 / 加班 / 同意 / 拒绝 / 撤销审批” → `oa`
- 用户提到“日志 / 日报 / 周报 / 汇报 / 日志统计” → `report`
- 用户提到“待办 / TODO / 任务提醒 / 循环待办” → `todo`

易混淆场景先读 [intent-guide.md](./references/intent-guide.md)。

## 权限探针流程

探针是可选诊断流程，不是每个任务的前置步骤：

- 用户有明确业务指令时，直接按业务指令执行；不要先跑一轮全量探针拖慢流程。
- 用户问“哪些权限已经授权 / 哪些能力能用 / 为什么登录后还不能读文档”时，可以执行安全只读探针。
- 用户需求模糊、可能涉及多个高权限域，或连续遇到权限错误时，先询问：“要不要先做一轮只读权限探针，看看哪些钉钉能力可用？” 用户同意后再探针。

探针流程：

1. 先执行 `dws auth status --format json`。
2. 选择只读安全探针，按域汇总“可访问 / 缺 PAT / 需要资源 ID / 不应探测”。
3. 如果返回 PAT 拦截，提取 `requiredScopes` 并解释缺少的 scope。
4. 明确说明：这是安全探针覆盖范围，不是官方完整授权列表；当前 dws 缺少直接枚举所有已授权 scope 的命令。

已知探针基线：当前仅确认 `doc:read` 可通过 `dws pat chmod doc:read --agentCode workbuddy --grant-type once|permanent --format json` 请求；其他域的已授权/未授权状态不要写死，待后续实测后更新。

推荐只读探针：

| 域 | 探针 |
|---|---|
| `contact` | `dws contact user get-self --format json` |
| `calendar` | `dws calendar event list --format json` |
| `todo` | `dws todo task list --format json` |
| `mail` | `dws mail mailbox list --format json` |
| `drive` | `dws drive list --format json` |
| `doc` | `dws doc list --format json` / `dws doc search --format json`；读正文前确认 `doc:read` |
| `oa` | `dws oa approval list-forms --format json` |
| `minutes` | `dws minutes list all --format json` |
| `chat` | `dws chat list-top-conversations --format json` |

不要用真实写动作做探针，例如发消息、发邮件、发 DING、审批同意/拒绝、删除/移动/撤回、改群成员。

## 命令发现

产品参考文档用于快速理解，但实际参数以 CLI 为准：

```bash
# 人读视图：Usage / Examples / Flags
dws <command-path> --help

# 机读视图：JSON Schema、flag alias、必填字段、敏感操作标记
dws schema
dws schema <product>.<canonical_name>
dws schema "<product> <group> <cli_name>"
dws schema <path> --jq '.tool.required'
dws schema <path> --jq '.tool.flag_overlay'
```

当 `dws schema` 中 `sensitive: true`，执行前必须进入用户确认流程。

## 危险操作确认清单

以下操作为不可逆或高影响操作，执行前必须获得明确确认：

| 产品 | 命令 | 风险 |
|---|---|---|
| `aitable` | `base delete` / `table delete` / `field delete` / `record delete` / `view delete` / `chart delete` / `dashboard delete` | 删除结构或数据 |
| `calendar` | `event delete` / `participant delete` / `room delete` | 取消日程、移除参与者或会议室 |
| `chat` | `group members remove` / `message recall-by-bot` | 移除群成员或撤回消息 |
| `doc` | `block delete` | 删除文档内容块 |
| `ding` | `message recall` | 撤回 DING 消息 |
| `oa` | `approval reject` / `approval revoke` | 拒绝或撤销审批 |
| `todo` | `task delete` | 删除待办 |
| `minutes` | `replace-text` | 全文批量替换听记内容 |

确认流程：

1. 展示操作摘要。
2. 等待用户明确回复“确认 / 同意 / 执行”。
3. 加 `--yes` 执行。
4. 返回结构化结果和必要的后续动作。

## 错误处理

1. 认证失败：读 [global-reference.md](./references/global-reference.md) 的认证章节，优先完成授权，不要重试业务 API。
2. 权限拦截：同时检查 stdout/stderr；如果出现 `requiredScopes`，提取 scope、解释用途并按授权策略处理。
3. 命令不存在或参数不匹配：先查 `dws <domain> --help` / `dws <domain> <group> --help` 修正一次；不要无限猜命令。
4. 命令失败：加 `--verbose` 诊断一次。
5. 出现 `RECOVERY_EVENT_ID=<event_id>`：按 [recovery-guide.md](./references/recovery-guide.md) 执行 recovery 闭环。
6. 中文 help、stderr 或 title 乱码时，不直接复制给用户；优先解析 `code`、`success`、`requiredScopes`、`nodeId`、`docUrl`、`error.category` 等字段，并用中文重述。
7. 仍失败：报告完整错误、已尝试步骤和建议下一步，不要自行绕过 `dws`。

## 已知限制

- Raw API 通常需要自建应用凭证；默认 OAuth/MCP 登录不等于 Raw API 可用。
- 文档读取可能需要 `doc:read`，出现"能搜索/创建但不能读正文"时，优先解释为业务 PAT scope 缺失。
- 考勤汇总、文档正文等中风险数据可能触发额外 PAT 授权。
- `doc upload` / 上传 pipeline：`doc.commit_uploaded_file` 在 schema 中定义但尚未暴露为 CLI 子命令（#301/#302），文件附件上传闭环仍不完整；普通文件上传可用，但不保证所有场景稳定。
- `calendar respond`：schema 中存在但 CLI 无对应子命令，响应邀请需在钉钉客户端操作。
- `chat message list`：普通文本消息可能被错误识别为富文本/卡片消息（#292）；`list-all` 能力可能受平台版本限制。
- `calendar event list`：部分组织/场景可能返回 business-level error 300000（#303）。
- `mail message send`：当前不支持附件（#308）。
- `chat message send`：v1.0.28+ 群消息必须传 `--title`（#294），单聊同样需要 `--title`。
- `doc update`：CLI flag `--content`/`--content-file` 与后端 schema 必填字段 `markdown` 存在不一致（v1.0.27 新增 CLIFlagOverride.MapsTo），如全文更新失败优先用 `doc block insert/update`。
- token 和加密凭证绑定设备/Keychain，跨设备或远程环境可能需要重新登录；v1.0.29+ 凭证按版本分区存储，升级后可能需重新登录。

## 详细参考

- [references/workbuddy-auth.md](./references/workbuddy-auth.md)：Skill 自闭环授权方案、浏览器跳转、设备流链接/授权码、可选二维码和 host-owned PAT 补充
- [references/global-reference.md](./references/global-reference.md)：认证、输出格式、全局 flags、环境变量、Raw API
- [references/intent-guide.md](./references/intent-guide.md)：意图路由和易混淆场景
- [references/field-rules.md](./references/field-rules.md)：AI 表格字段类型规则
- [references/error-codes.md](./references/error-codes.md)：错误码和排查流程
- [references/recovery-guide.md](./references/recovery-guide.md)：recovery 闭环
- [references/products/](./references/products/)：各产品命令参考
- [scripts/](./scripts/)：官方批量工作流脚本和 WorkBuddy setup 脚本

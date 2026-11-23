---
name: heyin-cli
description: 使用 heyincli 查询合因项目、申请和邀请，管理项目凭证，并执行用户授权的项目操作或接口请求。适用于合因项目查询、加入项目、回复邀请和项目接口调用。
description_zh: 使用合因命令行查询项目、管理申请与邀请及调用项目接口。
description_en: Use heyincli to query Heyin projects, manage applications and invitations, and call project APIs.
version: 1.0.0
author: 合因
---

参考资料链接相对于当前技能目录解析；按需读取链接指向的完整文件。

# 合因命令行使用指南

使用 `heyincli` 完成用户在合因平台上的操作。以下示例使用 macOS/Linux 命令名；Windows 使用 `heyincli.cmd`。示例中的项目、角色、申请、邀请和凭证 ID 均需替换为实际查询结果。

执行前按 [version-management.md](references/version-management.md) 检查实际命令路径、版本和帮助；本技能以 CLI 1.0.0 为已核实的兼容基线。在 WorkBuddy 中找不到 `heyincli` 命令时，先使用 `heyin-connector` 初始化并在其执行环境复查；连接器明确失败或不可用且命令仍不可用时，才按该文档的现有安装流程安装。验证成功后再检查登录态，不能直接执行不存在的 `auth status` 或 `auth login` 命令。

如果 CLI 失败退出，且标准错误中的 API 错误包含 `code 4001010011`，表示服务端要求更新客户端。必须先按 [version-management.md](references/version-management.md) 的强制更新流程更新 CLI，确认版本满足要求后再继续操作，不得使用旧版本重复重试。CLI 不会把该错误作为响应 JSON 写入标准输出。

## 授权

专家和技能统一使用以下流程；安装、更新或切换专家不会自动要求重新授权。仅本地计划、模板等不访问平台的任务无需登录。

1. **先查状态**：执行 `heyincli auth status --json`，检查退出码并读取 `logged_in`。退出码非零表示状态检查失败，先处理错误，不能当作未登录。
2. **已登录直接复用**：`logged_in: true` 时继续所需业务命令，不执行 `auth login`。状态依据本地刷新令牌及平台、客户端绑定判断；访问令牌过期、缺失或有效期未知不等于未登录，由 OAuth 业务命令自动刷新。
3. **WorkBuddy 优先连接器授权**：`logged_in: false`，或业务命令明确报告授权已失效、被撤销或范围不足并要求重新登录时，在 WorkBuddy 中先通过 `heyin-connector` 连接器授权。使用宿主提供的连接入口；无法直接操作时引导用户在连接器界面完成，不臆造工具或命令。等待连接器授权流程结束后复查 `heyincli auth status --json`，已登录即复用。
4. **连接器失败后才回退 CLI**：连接器授权明确失败，或确认连接器未安装、不可用而无法发起授权时，确认已有授权进程已结束并复查状态；仍未登录，或业务已明确要求重新授权且尚未完成新授权时，才执行一次 `heyincli auth login`。非 WorkBuddy 环境在确需授权时直接使用该 CLI 流程。使用默认文字输出，请用户核对验证码并在网页确认；仅自动打开失败时使用命令给出的链接，不重复打开授权页。用户明确取消或拒绝授权时停止，不自动切换方式再次授权。
5. **等待原命令完成**：记录并等待同一登录进程／工具会话，直到得到退出码。已输出 URL、浏览器确认完成、工具等待超时或暂时仍显示未登录，都不代表命令已结束或连接器授权失败；不得据此回退或再次发起登录。宿主连接器已在登录或 CLI 提示另一个登录正在运行时，等待已有流程，不并行启动或循环重试。
6. **完成后复查**：CLI 登录命令结束后再次执行 `heyincli auth status --json`，成功且 `logged_in: true` 才继续平台操作。CLI 登录失败或复查仍未登录时报告原因并停止本次自动登录流程；解决明确错误后才重新尝试，不循环弹出 OAuth。

`auth status` 默认显示“已登录”或“未登录”，只读取本地状态，不联网验证远端授权。业务已明确判定授权失效或范围不足时，不能仅凭本地 `logged_in: true` 认定授权恢复，须完成新授权并复查。普通只读请求的网络失败应先处理网络问题；刷新锁占用时等待已有刷新，不据此重新打开 OAuth。若刷新请求已发出但结果未知，或命令报告 `refresh_pending`／刷新结果未确认，本地会禁止再次使用可能已消耗的旧刷新令牌，须按上述授权流程重新登录；业务写入结果也不明确时，先在平台核实结果再决定是否继续，不能盲目重试。不要把所有网络错误或 HTTP 401 都当作重新登录的依据。

`auth login` 使用系统级跨进程文件锁：已有登录运行时立即报错退出，不申请设备授权、不打开浏览器，此时等待已有登录结束后复查状态。进程结束（含异常退出）后由操作系统释放锁。`~/.heyin/login.lock` 文件常驻是正常现象，存在不代表正在登录，不要删除或替换它来绕过锁；锁相关报错按错误提示处理。

`heyincli auth logout` 撤销已有 OAuth 授权后清空本地用户及项目凭证；撤销未确认时会报错并保留本地凭据。它不会删除平台上的项目 API 令牌。退出命令使用默认输出，不把退出登录作为刷新或登录检查的前置步骤。

不要索取或展示访问令牌、刷新令牌及凭据原文。

## 项目管理

### 查询全部项目与角色

```sh
heyincli project list
```

默认以 Markdown 表格显示项目 ID、项目编码、项目名称、项目简称、计划入组及我的角色。角色中包含角色 ID，区分项目角色和中心角色；中心名称以逗号分隔，多个角色以分号分隔。

创建项目凭证前，从此列表确认项目 ID 及本人持有的角色 ID。角色 ID 与角色模板 ID 不可混用。需要机器可读的项目数据时加 `--json`，输出合并全部分页后的列表 JSON。

### 加入项目申请

查看、提交或撤销加入项目申请时，阅读 [project-applications.md](references/project-applications.md)，按其中的 `project application` 用法执行。

### 项目邀请

查看、接受或拒绝项目邀请时，阅读 [project-invitations.md](references/project-invitations.md)，按其中的 `project invitation` 用法执行。

### 没有项目时

需要选择项目时，先执行 `heyincli project list --json`，查询未按关键词或项目状态筛选的完整项目列表。成功确认无项目后，执行 `heyincli project invitation list --result PENDING --json`，查询未按关键词筛选的全部待处理邀请。两次查询均须成功并获取全部分页；不能仅凭筛选结果、单页为空或请求失败判断用户没有项目或待处理邀请，查询失败时先报告并处理错误。

有待处理邀请时，展示项目与邀请信息，请用户明确选择是否接受或拒绝，按“项目邀请”说明执行；不得自动接受。接受成功后重新查询项目及角色，再继续凭证准备。已接受（`ACCEPT`）或已拒绝（`REJECT`）的历史邀请不阻止联系引导，也不能视为待处理邀请。

成功确认无项目且无待处理邀请时，提示用户：

> 您目前没有项目，也没有待处理的项目邀请。可以前往 [合因联系我们](https://www.hearing-tech.com/about.html#contact) 咨询或申请试用。

没有可用项目时停止凭证创建和平台业务操作，不猜测项目或角色 ID；仅本地计划、清单或模板任务仍可继续，不要求为此登录或创建项目。

## 凭证管理

```sh
heyincli token list
heyincli token info <token-id>
heyincli token create --project-id 12 --role-id 34
heyincli token delete <token-id>
heyincli token delete --all
```

- `token list` 显示已保存凭证的 Markdown 表格，不展示令牌原文。它是本地列表，不能据此保证凭证当前仍有效。
- `token info <token-id>` 使用 `token list` 中的完整凭证 ID（64 位十六进制；无歧义的旧 8 位 ID 仍可使用，查验成功后自动迁移），以该凭证本身在线查验是否有效、未过期，及项目、角色、用户和时间信息是否与本地一致；成功展示凭证表格及项目 ID、角色 ID、状态。无需 OAuth 登录，不输出令牌原文。复用已有凭证前先查验，不能只依赖本地列表。
- `token create` 需要登录。`--project-id` 和 `--role-id` 必填，使用项目查询中的真实 ID；**默认只传 `--project-id` 和 `--role-id`，不传 `--name` 和 `--expires-at`**。只有用户明确指定令牌名称时才传 `--name`，只有用户明确指定到期日或有效时长时才传 `--expires-at`；两项独立判断，未指定的项保持省略，交由 CLI 使用默认值。专家不得根据项目、角色、建库/核验用途自行命名，也不得因任务预计持续时间、方便复用等理由自行设置或延长有效期；用户仅要求建库或创建令牌不视为授权覆盖这两项。默认名称取 `~/.heyin/.env` 中去除首尾空白的 `SOURCE`（缺失或为空时用 `CLI`，最多 41 个字符），追加 `-` 和 8 位随机十六进制字符；默认到期日为上海时区当天的第二天。用户明确指定时才可覆盖对应参数：名称去除首尾空白后为 1–50 个字符，到期日为 `YYYY-MM-DD` 且晚于上海时区当天。创建后保存凭证，项目、角色和到期日不能修改。
- `token delete` 需要 OAuth 登录，使用 `token list` 中的本地凭证 ID，删除平台令牌及本地副本，令牌会立即失效且不可恢复。`--all` 与位置参数 `<token-id>` 互斥，仅批量删除本地保存的凭证对应的远端令牌，每项成功后清理本地；失败即停，保留未处理项，不删除远端其他令牌。默认输入 `yes` 确认，批量只确认一次；用户已明确授权相应删除范围时可加 `--yes`。

多个凭证符合目标时，结合用户指定的项目和角色选择；仍有歧义时请用户明确。本地凭证 ID 不是项目 ID、角色 ID 或令牌原文。

## 失败恢复

- `project` 命令以及 `token create`、`token delete` 使用 OAuth。CLI 在本地访问令牌过期或有效期缺失时自动刷新；OAuth GET 遇到 HTTP 401 或业务码 401 时还会刷新并重试一次。访问令牌过期不直接重开 OAuth；只有明确需要重新授权时才按上面的“授权”流程启动一次登录。网络错误或锁占用先处理对应问题，不循环登录。
- `req` 和 `token info` 使用所选项目 API Token，不使用 OAuth 自动刷新。凭证过期、被撤销或绑定不符时，先查验并选择其他有效凭证，或在 OAuth 登录后创建匹配项目和角色的新凭证。重新登录不会恢复失效的项目 API Token；不要把 `auth login` 当作所有 401 的通用修复。
- `token create` 报业务码 `4003010033` 表示本人有效（未撤销且未过期）API Token 已达 10 个上限。暂停创建，列出 `token list` 供用户选择删除不再使用的令牌，说明删除会立即使令牌失效并影响使用它的工具；不自行选择删除对象。
- 写入遇到超时、断连、响应异常或成功后输出失败时，非零退出码不代表远端未写入。先查询目标实际状态和已完成项，再决定是否重试；无法核实时停止写入并说明未确认范围。CLI 不自动重试 POST，调用方也不得盲目重放。申请和邀请查对应列表；Token 创建或删除结果未确认时按错误提示到平台核实。

## 参考目录

按任务阅读对应文件。

| 文件 | 内容与使用场景 |
| --- | --- |
| [project-applications.md](references/project-applications.md) | 项目申请：查看、提交和撤销加入项目申请 |
| [project-invitations.md](references/project-invitations.md) | 项目邀请：查看、接受和拒绝项目邀请 |
| [project-requests.md](references/project-requests.md) | 项目请求：`req` 参数、调用示例，以及项目查询和项目设置技能入口 |
| [version-management.md](references/version-management.md) | 安装与卸载、非交互参数、版本检查、常规更新和服务端要求的强制更新 |

## 输出约定

`auth`、`token`、`project` 的 `--json` 可由全部子命令继承，默认输出中文文字和 Markdown 表格；空列表保留表头、空结果提示及数量摘要。脚本使用 `--json`，`req` 成功时输出 JSON，不加该参数。`auth login --json` 为 JSON Lines：先输出设备授权信息，成功后再输出一行登录结果；其他认证命令成功时输出单个 JSON 对象。

`req` 成功时标准输出仅为平台响应信封中的 `data`，解析时直接读取业务字段。失败时以非零退出码结束，错误写入标准错误；默认文字错误中，平台 API 错误的 HTTP 状态和业务码以 `API request failed (HTTP ..., code ...)` 表示。`--json` 只影响成功输出，不改变错误格式。

自动化需要判断失败进度时，可加全局选项 `--error-format=json`：失败时标准错误只输出一个对象，如 `{"error":{"code":"AUTH_REQUIRED","message":"...","operation_state":"not_started"}}`，按 `code` 和 `operation_state` 判断，不解析中文文本。`operation_state` 为 `not_started` 表示未发起目标写入；`unknown` 表示写入结果未确认或批量仅部分完成；`remote_completed` 表示远端已写入、后续核验/保存/输出失败；`local_completed` 表示本地保存或清理已完成、输出失败。后三种都要先查询核实，不能视为重试许可。`code` 为 `CLI_UPGRADE_REQUIRED` 时按版本管理强制更新。该模式下带确认的删除或撤销命令必须显式加 `--yes`，否则在请求前返回 `INVALID_ARGUMENT`。JSON 错误不携带平台业务码，需要识别 `req` 的具体业务码（如 `4001010011`、`4003010033`）时使用默认文字错误。

令牌 JSON 仅含安全展示字段，不含令牌原文：列表为 `{"list":[],"total":0}`，单个查验/创建/保存为对象；单个删除为 `{"token_id":"<token-id>","deleted":true}`；批量删除只输出一个 `{"deleted_ids":[],"total":0,"complete":true}` 汇总。部分失败可能输出 `complete:false` 及已完成项，必须同时检查退出码。确认及诊断写入标准错误；参数错误附简短用法，运行期错误不附用法。

---
name: weaver-e10-yimiaoban-connector
display_name: 泛微易秒办
display_name_en: Weaver E10 Yimiaoban IM
description: 泛微 E10 易秒办即时通讯能力（单聊/群聊消息、发送与必达、群组管理、会话与系统消息），通过 weaver-work-cli im 命令执行。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_zh: 泛微 E10 易秒办即时通讯能力：拉取单聊/群聊/系统消息、发送与撤回消息、发必达、群组管理（建群/邀人/踢人/退群/解散/公告）、会话列表、文件上传下载与人员解析，全部通过 weaver-work-cli im 命令执行，写操作走 prepare→apply 确认链。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_en: Weaver E10 Yimiaoban (IM) capabilities - fetching single/group/system messages, sending, withdrawing and ding messages, group management, sessions, file upload/download and people resolution, executed through the weaver-work-cli im command with a prepare-then-apply confirmation chain for writes. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint.
version: 1.1.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
dependencies:
  - weaver-e10-login
  - weaver-e10-shared-connector
cliHelp: "weaver-work-cli im --help"
---

# 泛微易秒办（im）

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**

共享规则覆盖命令可用性检查、E10 认证、JSON 输出契约、大结果渲染和高风险写入确认链，本技能不再重复。

本技能与 CLI 均由连接器提供并自动安装、自动升级，不要自行执行 npm 命令，也不要用 `npm view` 比对版本。

本技能覆盖易秒办（E10 即时通讯）业务域：**消息（msg）**、**必达（ding）**、**群组（group）**、**会话（session）**、**系统消息（sysmsg）**，以及支撑能力**人员解析（person）**、**文件上传/预览/下载（file）**、**用户状态与免打扰设置（user）**、**i18n 标签（i18n）**。所有写操作走 prepare→apply 确认协议。

## 认证与请求头契约

**登录与会话由连接器托管**（登录由连接器执行，业务命令统一显式带 `--profile eteams`）。本技能**不自建登录**：禁止扫码/账号密码/自建 OAuth 取 token，禁止使用浏览器自动化登录，也不接触、打印、转存任何认证文件。

`weaver-work-cli im` 发往 E10 的每个请求（`/api/em/msg/executeIm/...`、`/api/em/msg/createDing`、`/api/hrm/common/getEmployeeByIds`、`/api/file/...` 等）都由 CLI 统一携带以下三项用户信息参数，缺一不可（业务入参里不要传、也不要手工拼装请求头）：

```text
Cookie: <连接器托管登录返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <连接器托管登录返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

三项若缺任一，服务端无法识别操作者或会判定登录失效；`weaver-work-cli im` 的每个 operation 都已在请求头中带齐。

业务输入只描述业务对象与意图，凭证与请求头由 CLI 托管；需要诊断登录态时只用 `weaver-work-cli auth` / `doctor --e10` 与业务命令返回的 JSON 错误。

## 命令入口

```text
weaver-work-cli im --help
weaver-work-cli --profile eteams im schema
weaver-work-cli --profile eteams --json im run <operation> --input-json '{"key":"value"}'
```

`schema` 是可用能力的唯一事实来源（含每个 operation 的 `inputSchema`、`risk`、`requiresConfirmation`、`deprecatedInputAliases`）。禁止把本技能或源文档里的接口路径当成可直接调用的地址，也禁止把未出现在 `schema` 中的能力当作可用 operation。

## Reference 路由表

命中任一条件时，执行下一步前读取对应 reference。

| 触发条件 | Reference |
| --- | --- |
| 按姓名/工号/手机/邮箱解析人员，uid 批量解析 | [`references/person.md`](references/person.md) |
| 名称 → ID 解析规则、同名消歧、未匹配处理、接口间上下文传递契约 | [`references/field-resolution.md`](references/field-resolution.md) |
| 拉单聊/群聊消息、群置顶消息、消息阅读状态（只读） | [`references/msg-read.md`](references/msg-read.md) |
| 发送单聊/群聊消息（文本/图片/文件）、撤回、群消息置顶（写） | [`references/msg-write.md`](references/msg-write.md) |
| 必达消息：普通必达、已有消息转必达、仅未读/指定接收人（写） | [`references/ding-write.md`](references/ding-write.md) |
| 搜群、群信息、群成员、群主/管理员、群存在性、群公告（读） | [`references/group-read.md`](references/group-read.md) |
| 建群、邀请、踢人、退群、解散、申请入群、改群属性/群名、群公告增改删（写） | [`references/group-write.md`](references/group-write.md) |
| 会话列表、系统消息分组/类型/消息查询 | [`references/session-sysmsg.md`](references/session-sysmsg.md) |
| 文件上传/预览/下载到本地、用户在线状态、i18n 标签翻译 | [`references/file-user-i18n.md`](references/file-user-i18n.md) |
| 把某个群/某个人/某个系统会话设为免打扰或恢复提醒 | [`references/user-remind.md`](references/user-remind.md) |
| 易秒办红线（操作人字段、本人身份取用、人名解析、id 边界、分页与全量、展示完整）、写链停止条件、已知禁用边界 | [`references/safety-boundaries.md`](references/safety-boundaries.md) |
| 业务错误码含义与处理建议（群 12xx / 消息 15xx / 数据 13xx + CLI 校验错误） | [`references/error-codes.md`](references/error-codes.md) |
| 源资料清单、chunk 与 operation 影响索引、产物基线（源资料更新检测用） | [`references/source-manifest.json`](references/source-manifest.json) |

## 关键差异（必须先知道）

- **消息以 `msg` JSON 字符串 + `datas[].datas[]` 行结构返回**：CLI 的 `msg.sync.*`/`msg.top.sync` 已把每条消息解析成结构化行（`msgid/sender/time/typeName/content/media/must/fileName/...`），`content` 是可读文本（@ 提及已还原、媒体显示为 `[图片]名称`/`[视频]名称`/`[文件]名称`、必达内容带 `[必达]` 前缀）。解析结果直接使用，不要再本地拼装。
- **分页口径（与源 skill 一致）**：消息类每页默认 **50** 条、单页上限 **50**；**有界区间（指定了时间范围、默认当天、或显式 `end`/`endId`）自动循环翻页把区间拉完再返回**（最多 100 页，触及上限时返回 `hasMore:true` + `nextStart`）；**无界区间（`latest:true`）只拉一页**，需要更早数据时用 `nextStart` 继续。**会话列表（`session.list`）不参与自动翻页**（默认 20、上限 50，用 `msgid`/`nextMsgid` 翻页）。
- **时间范围强制收敛到 7 天**：单聊/群聊/系统消息的 `from`/`to` 跨度 > 7 天时，CLI 自动缩短为该范围**最后 7 个自然日**，并在 `data.rangeShrink` 返回 `notice`。**展示结果时必须把这条收敛提示原样转述给用户**，不要静默省略，也不要替用户改小范围。
- **展示顺序**：消息按消息 id 从新到旧（最新在前）返回；`content` 完整不截断，表格化时自行转义 `|`、保留换行与 `[必达]` 前缀、媒体保持可点击链接。
- **发送者「我」由 CLI 判定**：`sender` 与当前登录人 IM uid 比对，自己发的消息返回「我」；他人优先消息内 `sname`、其次 hrm 姓名、最后回退 uid。
- **人名一律由 CLI 走 hrm 解析**（`/api/hrm/common/getEmployeeByIds`），本技能不展示也不依赖 IM 群成员 `name` 字段；群成员接口返回的 `name` 不可信。
- **本人 IM 身份（cid/uid）只用于本机组装**：`group.search` 的 `members/owner/creator` 条件、撤回消息体、必达消息体、建群自检、消息展示「我」都用 CLI 通过 `teamsCheck` 取得的本人 `imCid`/`imUid`；**它绝不作为请求体操作人字段，也不接受调用方传入**（传 `user`/`sender`/`operator` 会被拒绝：`forbidden_key`）。
- **uid/cid/群 id 都是 uint64**：JSON 中必须按字符串传（`"1788334281700000004"`），`0` 一律拒绝；`num` 超过 50 会被截断为 50。
- **时间范围不是服务端过滤条件**：单聊/群聊历史按**消息 id 区间**定位，CLI 把 `from/to` 换算成 `[minId,maxId]`；缺省取当天。`actionMsg.code=1303`（无聊天记录）按**成功空列表**返回（`empty:true` + `emptyReason`），不报错。
- **媒体需要登录态**：`media[].previewUrl/downloadUrl` 需登录态访问，直接嵌 Markdown 会 401；要真正查看图片/视频或取回附件，用 `im.file.download` 落地到本地（`output` 为明确本地路径、父目录须存在、已存在则拒绝覆盖，图片会按文件头纠正扩展名）。
- **超时与空白消息**：普通请求 15 秒超时即失败且不重试（上传 15/60 秒）；全空白文本不算内容，禁止发送空白消息（`content_required`）。

## 写操作决策树（prepare → apply）

易秒办所有写操作（发消息/撤回/置顶/必达/群组写操作）统一为两段式，均在 `schema` 中带 `requiresConfirmation`：

1. 调用 `<op>.prepare`（只读校验：解析成员、读源消息、计算接收人），得到 `summary` + `continuation`。
2. 向用户展示 `summary`（动作、目标、数量、差异/风险），请求明确确认。
3. 用户确认后调用 `<op>.apply`，传 `{"confirm":true,"continuation":"<prepare 返回的 token>"}`。
4. `apply` 返回 `partial` / `write_uncertain` 或网络中断时**立即停止，不自动重试**，先做一次只读回查（如群成员、消息是否已存在）再决定。

任何一步出现登录失效/上下文变化（`context_mismatch`/`continuation_expired`/`target_changed`）都回到第一步重新 prepare。

## 失败处理

- 业务失败看 stderr JSON 的 `error.type` / `error.subtype` / `error.message`，不要用退出码 `0` 判断成功。
- `code=302` 或认证类错误（`session_expired`）：按共享规则引导用户重新登录，禁止猜域名或手工拼凭证。
- 业务语义错误码：`1303` 表示无聊天记录（成功空列表，看 `emptyReason`）；群不存在 `1209`；`members_resolve_failed`/`members_empty` 说明成员解析失败，向用户说明后请其决定是否 `removeFailed:true` 继续；其余码值对照 [`references/error-codes.md`](references/error-codes.md)。
- `alias_conflict`：旧字段（如 `filePath`/`shareGroups`）与新字段同时出现且取值不一致，请只保留一个。
- 展示给用户时保持「完整不截断」红线，参考 [`references/safety-boundaries.md`](references/safety-boundaries.md)。

## 平台兼容

命令示例必须同时兼容 Windows 与 macOS/Linux。简单 JSON 统一用 `--input-json`：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.msg.sync.group --input-json '{"groupId":"1788334281700000004","num":50,"latest":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.msg.sync.group --input-json '{"groupId":"1788334281700000004","num":50,"latest":true}'
```

复杂 JSON 建议保存为 UTF-8 文件后按平台传给 `--input <file>`；Windows PowerShell 下不要使用 `printf`、`~/` 路径或反斜杠续行。

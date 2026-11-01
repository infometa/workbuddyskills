---
name: webroom-webhook
display_name: AIWHO 指挥台推送
display_name_en: AIWHO War Room Push
description: 向 AIWHO WEBHOOK中台（作战室）推送 webhook 消息：告警、任务完成通知、新建任务计划/已完成任务计划通知、待办阻塞提醒、AI 接入时的服务上线通知。当用户要求「推一条消息到作战室 / 大屏 / 群播报」「通知工位 ch-xxx」「推送构建失败/部署完成/异常告警」「推一条新建任务计划 / 已完成任务计划」时使用。含端点、鉴权、level 口径、幂等键（externalId）、载荷样例与排错表。
description_zh: 把告警、任务完成、待办等消息推送到 AIWHO 指挥台（作战室大屏），紧急事件自动语音播报；覆盖端点、鉴权、级别口径、幂等键与排错。
description_en: Push alerts, task updates, to-dos and connectivity notices to the AIWHO War Room dashboard, with voice broadcast for urgent events; covers endpoint, auth, level rules, idempotency keys and troubleshooting.
version: 2.0.1
author: AIWHO
---

# webroom-webhook · 往作战室推一条消息

本 Skill 说明如何把消息推送到 **AIWHO 指挥台（作战室）**。中台（AIWHO WEBHOOK中台）是
**独立部署的云端服务**，地址与凭证由部署方提供。

> 🔴 **本 Skill 不含、也不需要后端服务** —— MCP / Hook 只与云端中台对话。
> **不要为了用它去 clone 或启动任何后端**；你本地没有中台，手拼 `localhost:3500` 一定不通（见 §八）。

接入有三条路，**先按「你手里有什么」选一条**（详见 §〇）：

| 你手里有什么 | 走哪条 | 配置量 | 可用 MCP 工具 |
|---|---|---|---|
| 从 **WorkBuddy 连接器市场**装的「AIWHO 指挥台」 | **OAuth 直连中台**（§〇·路径 1） | 点「连接」→ 网页授权，**零手填** | **5 个**（HTTP 传输） |
| 完整客户端套件（含 `mcp/`、`lib/`、`scripts/`） | **本地 stdio MCP**（§〇·路径 2） | 写一条 `mcp.json` | **7 个** |
| 只有 shell / curl | **裸 HTTP**（§一） | 三行环境变量 | 0（自己拼请求） |

> ⚠️ 三者**不是同一套东西**：市场连接器给「5 个工具 + 自动令牌」，比完整套件少的只有
> `notify_turn_start` / `notify_turn_end` 两个轮次工具；裸 HTTP 一个工具都没有，得自己拼请求。
> 混用会得到「未知工具」或 `401` —— 先确认自己走的是哪条（见 §7.2）。

它同时是**三条通道共用的契约说明**：MCP 工具与本文档口径必须一致，
由 `node scripts/webroom-contract-check.mjs` 做十字校验（改一边不改另一边即失败）。

> ⚠️ 四条先读：
> 1. **本文件不含任何真实密钥**，一律从环境变量取。正文会被 AI 完整读到，写死密钥等于公开泄露。
> 2. **`whsec_demo_<channelId>` 是公开演示值，不是密钥**（公式公开可推导）。生产必须用真密钥。
> 3. **`urgent` 是语音播报的唯一触发条件**。级别写错 = 大屏不播报，且不会有任何报错。
> 4. **多 AI 接入请带上 `source`**（谁推的）。不带的话，大屏上所有 AI 推的消息长一个样，
>    分不清是谁 —— 这是「多 AI 共用一块大屏」时最先被投诉的一条。

---

## 〇、接入：先选一条路

### 路径 1 · 从连接器市场装（推荐，零配置）

在 **WorkBuddy 连接器市场**找到「AIWHO 指挥台」→ 点 **连接**。之后全自动，
**你不需要填地址，也不需要填任何 token**：

1. **发现**：客户端读中台的 `/.well-known/oauth-authorization-server` 与
   `/.well-known/oauth-protected-resource`，自动得知 MCP 端点与授权端点。
2. **动态注册**：客户端按 RFC 7591 调 `POST /oauth/register` 取 `client_id`（公共客户端，无密钥）。
3. **授权（PKCE S256）**：浏览器打开 `GET /oauth/authorize`。
   - 你**已登录**中台 → 直接回调。**首次连接会先出一张确认页**（应用名 / 用途 / 权限，可逐项去掉），
     同意过一次之后不再打扰 —— 同一账号 + 同一应用 + 权限没变时静默签发；换了账号、撤过授权、
     或这次多要了一档权限，都会重新问一次；
   - **未登录** → 出现中台托管登录页：填**邮箱 + 密码**；若账号不是邮箱（如运维管理员），还要填**团队标识**（`t_` 开头那串）。页面上另有两条出口：没账号 → 「注册并开通」，忘了密码 → 「忘记密码」——不用自己猜 URL。
4. **换令牌**：客户端带 PKCE `code_verifier` 调 `POST /oauth/token`，拿到 access（**1 小时**）/
   refresh（**30 天**），由 WorkBuddy 的 OAuth 管理器**自动以 `Authorization: Bearer` 注入**每次 MCP 调用；
   过期自动刷新，全程无感。

之后直接调这 5 个工具：`push_warroom_event`（通用推送）、`notify_task_complete`（任务完成）、
`notify_task_created`（新建待办）、`notify_task_done`（待办完成）、`setup_receiving_endpoint`（接入确认）。

> 🔴 **MCP 端点要求 `write` scope**（`admin` 可代 `write`）。若授权只拿到 `read`，
> 调用会 `403 AUTH_SCOPE_INSUFFICIENT`。
> 🔴 **HTTP 通道有这 5 个工具**（2026-10-17 补齐，与 stdio 侧同名同参数）。还有 2 个 ——
> `notify_turn_start`、`notify_turn_end` —— **只在本地 stdio MCP 里有**：它们是给「无 hook 宿主」
> 补轮次播报的，而走 HTTP 的云端 / 浏览器 AI 自有会话事件源，不需要。见 §7.2。
>
> 🟢 **自动播报：连接器包里自带 hook，不用另装任何东西。**
> 授权完成后还剩**唯一一步**：把工位接收端写到本地（hook 是独立进程，拿不到 OAuth 令牌），
> 由 AI 执行一条命令即可（把 URL 换成用户在用户中心「接入凭证 → 工位」复制的那条）：
>
> ```bash
> # 1) 定位包目录（版本号目录会变，别写死）
> ls -d ~/.workbuddy/plugins/cache/*/aiwho-warroom/*/
> # 2) 落盘接收端（hook 与 CLI 读的是同一份 ~/.warroom/receiving-endpoint[.<scope>].json）
> node "<上一步的包目录>/mcp/warroom-webhook.cjs" --setup "<用户中心复制的完整入站地址>"
> ```
>
> 成功会回显基址 / 租户 / 工位 / 密钥（脱敏）与落盘路径。之后 9 个宿主事件
> （收到指令 / 任务完成 / 待办新建与完成 / 需要授权 / 会话结束…）自动上屏，
> 与本地 stdio 版的 hook **同一份脚本、同一套标题模板**。未配置时 hook 静默跳过，不报错、不刷屏。

### 路径 2 · 本地 stdio MCP（工具最全，需完整套件）

把**完整客户端套件**（含 `mcp/warroom-webhook.cjs`、`lib/`、`scripts/`）放进你的宿主，
并在宿主的 MCP 配置里加一条：

- `command` 用**系统 node 绝对路径**，参数指向该套件里的 `mcp/warroom-webhook.cjs`
  （🔴 **别写死托管 / IDE 管理的 node 版本路径**，原因见 §7.3）。
- 接好后调 `setup_receiving_endpoint(endpoint=<用户中心「接入凭证 → 工位」复制的完整入站地址>)` 完成绑定，见 §7.1.2。

可选再装**宿主 Hook**（`node scripts/install-hook.mjs`）用于事件自动推送 —— 不装也能用，
只是少了「收到指令 / 会话恢复」等自动播报；支持情况见 §7.4。

> ℹ️ **市场连接器包里有的是**：`hooks/`（自动播报用）+ `mcp/warroom-webhook.cjs` + `lib/` + `skills/`，
> 因为包内置 hook 需要它们；**没有的是** `scripts/`（`install-hook.mjs` 这类安装器）与 `.agents/`。
> ✅ 完整套件仍可自取：从公开归档 `https://cnb.cool/aiwho/tools/warroom-integration/-/git/archive/v2.0.1.zip`
> 下载解压即得（含 `mcp/` `lib/` `scripts/` `.agents/skills/`）—— 想用 stdio 通道或装 Claude Code hook 时走路径 2。
> ✅ **套件里的 stdio 客户端已支持 v2 双段寻址**（`/api/v2/webhook/<租户>/<工位>`），
> 并向后兼容旧部署的单段 `/api/v1/webhook/<工位>` —— 详见 §7.6。

### 路径 3 · 裸 HTTP（只有 shell / curl 时）

见 §一：三行环境变量 + 一条 curl，不需要任何 MCP。

---

## 一、30 秒上手

```bash
# 必需环境变量（缺一个就直接失败退出，不做任何猜测）
export WARROOM_API_BASE="https://<你的中台域名>"        # 后端基址，由部署方提供
export WARROOM_TENANT="<租户 id>"                    # 🔴 v2 起路径必须带租户段，别漏
export WARROOM_CHANNEL="ch-workbuddy"               # 目标工位 channelId
export WARROOM_WEBHOOK_KEY="<工位密钥>"              # 真密钥；不设则回落演示推导值（仅本地）
```

> **不确定这几个值该填什么？** 问中台管理员，或登录用户中心 →「接入凭证」→ 选中工位，
> 复制那条**完整入站地址** —— 形如 `https://<中台>/api/v2/webhook/<租户id>/<工位channelId>?key=<密钥>`，
> 四段里已经把「基址 / 租户 / 工位 / 密钥」全给了。
> **别手拼 localhost** —— 你本地没有中台服务（见 §八）。

```bash
curl -sS -X POST "$WARROOM_API_BASE/api/v2/webhook/$WARROOM_TENANT/$WARROOM_CHANNEL?key=$WARROOM_WEBHOOK_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"title":"部署完成","body":"web@1.2.3 已发布到生产","level":"info"}'
```

返回体（状态码与 `created` 的两个含义如下，**别只看状态码**）：

```json
{ "id":"clx…", "channelId":"ch-workbuddy", "dedupeHash":"9f2c…", "level":"info", "icon":"info",
  "created":true, "receivedAt":"2026-09-19T02:00:00.000Z" }
```

| 情形 | HTTP | `created` | 含义 |
|---|---|---|---|
| 新去重键 | **201** | `true` | 落了一条新消息 |
| 同键 + **内容逐字相同** | **200** | `false` | 幂等重复，无事发生（不是错误） |
| 同键 + **内容有任意差异** | **201** | `true` | ⚠️ **不是新消息** —— 原地改写已存在的那条（`id` 不变），见 §2.5 |

**只看 `created` 判断「新增」是不够的**：`created:true` 有两层含义（新落 / 原地更新），
要区分只能看 `id` 是否变过。三种情形都是成功，不要因看到 200 或 `false` 就重试。

---

## 二、契约（唯一权威口径）

### 2.1 端点

| 项 | 值 |
|---|---|
| 方法 / 路径 | `POST {WARROOM_API_BASE}/api/v2/webhook/{tenantId}/{channelId}?key={secret}` |
| 路径形状 | 🔴 **v2 起必须带租户段**（`/webhook/{tenantId}/{channelId}`）。旧的单段 `/api/v1/webhook/{channelId}` 与所有 `/api/v1/*` **已硬切、不再服务**（落 404 迁移提示） |
| 备选鉴权 | 签名头（按工位 `type`，见 §2.2）—— `?key=` 与签名头**二选一**，任一通过即可 |
| Content-Type | `application/json`（也支持 `text/plain` 与 `application/x-www-form-urlencoded`） |
| 请求体上限 | 1 MiB（超限 `413 PAYLOAD_TOO_LARGE`） |
| 限流 | 单工位 **120 请求/分钟**，全局限 1200/分钟；超限 `429 RATE_LIMITED` |

### 2.6 载荷字段 `source`（多 AI 可分辨，**新增**）

多 AI 推同一块大屏时，必须能分辨是谁推的。做法是把「AI 来源名」放进载荷：

| 载荷字段 | 落点 | 说明 |
|---|---|---|
| `source` | 标题 + `externalId` | **推荐写法**。例：`{"title":"部署完成","source":"CodeBuddy"}` |
| `aiName` | 同上 | `source` 的别名（两者都给时 `aiName` 优先） |

行为：

- **MCP / HTTP 传输**：`notify_task_complete` 的标题自动变成 `✅ {source} 任务完成`；
  不带 `source` 时退回 `✅ 任务完成`。`push_warroom_event` 的标题由你给，`source` 不影响它。
- **`notify_task_created` / `notify_task_done`**：标题分别自动变成 `📋 {source} 新建任务计划：<subject>` 与
  `✅ {source} 已完成任务计划：<subject>`（`<subject>` 是你传的**待办标题**，必填）；不带 `source` 时退回无来源版本。
  这两个工具针对「某条**具体待办被新建 / 完成**」的事件，与 `notify_task_complete`（一轮收尾摘要）正交 —— 别混用。
- **`externalId` 缺省按内容自动生成**，不需要你操心：
  `notify_task_created` → `mcp:task-created:<source>:<待办标题指纹>`，`notify_task_done` → `mcp:task-done:<source>:<标题指纹>`；
  `push_warroom_event` → `mcp:push:<source>:<标题指纹>:<30s桶>`；给了 `commit` 的 `notify_task_complete` → `commit-<hash>`。
  ✅ **不同内容天然不同键，各占一条**（不再「后推覆盖先推」）；同一条待办重推折叠；30s 内抖动重调也折叠。
  只有「同一标题要在不同时间各推一次」「重试必须严格同键」这类语义，才需要显式传 `externalId`。
- **裸 HTTP 直推**：服务端只按 §2.3 的键抽取，**不认 `source` 键** ——
  请自己把来源写进 `title`，并自带 `externalId`（如 `{"title":"✅ CodeBuddy 任务完成","externalId":"ai:CodeBuddy"}`）。

> 口径来源：本套件的 `lib/mcp-contract.mjs` 的 `taskCompleteTitle` / `sourceExternalId`。
> 标题模板与 `externalId` 前缀改一处必须改三处（契约 / MCP stdio / HTTP 传输），
> 由 `scripts/mcp-contract-check.mjs` 十字校验。

### 2.7 MCP over HTTP（**市场连接器走的就是这条**）

没有 shell 的 AI（浏览器里的、云端的）走不了 §一 的 curl，也 spawn 不了 MCP 子进程。
为此**中台**内置了一条 **HTTP 型 MCP 传输**（这是中台的能力，不是本 Skill 要你部署的）：

| 项 | 值 |
|---|---|
| 端点 | `POST {WARROOM_API_BASE}/api/v2/mcp` |
| 报文 | JSON-RPC 2.0，`Content-Type: application/json`（单个对象或数组皆可） |
| 鉴权 | `Authorization: Bearer <令牌>`（**必须**）。令牌可以是**手工签发的 ApiToken**，也可以是 **OAuth 签发的 access token**（两者在服务端走同一条校验路径）；**不接受** `?key=`，也不接受任何演示推导密钥 |
| 需要 scope | **`write`**（`admin` 可代 `write`）；只有 `read` 会得到 `403` |
| **可用工具** | **5 个**：`push_warroom_event`、`notify_task_complete`、`notify_task_created`、`notify_task_done`、`setup_receiving_endpoint`（见 §7.2） |
| 支持方法 | `initialize` / `ping` / `tools/list` / `tools/call` |
| **不支持** | `resources/*` / `prompts/*` / `completion/*` / GET 长连接（SSE）/ 上行通知 |

> 🔴 **HTTP 通道缺的只有轮次工具。** `notify_turn_start` / `notify_turn_end` 只存在于本地 stdio MCP
> （它们是给「无 hook 宿主」补轮次播报的）。拿这两个名字调 HTTP 端点会报「未知工具」。
> 其余 5 个工具 HTTP 与 stdio **同名同参数**。

```bash
curl -sS -X POST "$WARROOM_API_BASE/api/v2/mcp" \
  -H "Authorization: Bearer $WARROOM_API_TOKEN" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"push_warroom_event","arguments":{"title":"部署完成","body":"web@1.2.3 已发布","level":"info","channelId":"ch-workbuddy","source":"CodeBuddy"}}}'
```

工具返回的内容是**一段 JSON 文本**，`created` 是判断「新增还是去重命中」的唯一依据：

```json
{ "ok": true, "channelId": "ch-workbuddy", "level": "info", "source": "CodeBuddy",
  "created": true, "dedupeHash": "9f2c…", "messageId": "clx…",
  "note": "已新增并推上大屏" }
```

已知边界（**不要以为是接错了**）：

- 发 `resources/list` 等方法 → `-32601`，`error.data.supported` 会列出实际支持的方法；
- 发 `notifications/*` → `204` 空响应（规范：通知不回包）；
- `GET` 端点 → `405`，且响应体说明「只支持 POST」；
- 不支持 SSE，所以**中台不会主动推消息**——只能由 AI 调用工具来推。

> 💡 **HTTP 传输适合的场景**：它零本地依赖（根本不需要 node），与云端部署同构，托管升级也永不断链；
> 而 stdio 要宿主能 spawn 本地 node，且容易踩 §7.3 的 node 路径坑。所以**无本地 node 的云端 / 容器 / 浏览器 AI**选 HTTP，其余走主线 stdio（见 §〇）。

### 2.2 鉴权（二选一）

**方式 A · URL 共享密钥（推荐给 AI，最省事）**：`?key=<工位密钥>`。
适用于只允许填 URL 的平台，也适用于本 Skill 的 curl 模板。

**方式 B · 请求头**（打 `/api/v2/webhook/{tenantId}/{channelId}` 时按工位 `type` 决定）：

| 工位 type | 必须的头 | 值 |
|---|---|---|
| `custom` / `business` / `sentry` / `ci` | `X-Source-Secret` | 工位密钥明文 |
| `github` | `X-Hub-Signature-256` | `sha256=` + HMAC-SHA256(密钥, **原始 body 字节**) |
| `grafana` | `X-Signature` | HMAC-SHA256(密钥, **原始 body 字节**) |

可选 `X-Request-Timestamp`（unix 秒）——**只在「不带 `?key=`、走签名头」时才校**：

- 带 `?key=` → **完全不看时间戳**（传了也忽略）。重放防护由去重层承担。
- 走签名头 → **传了就校**，偏移超 ±300s → `401 SIG_TIMESTAMP_SKEW`；不传则不校。

**结论：用 `?key=` 时不要传 `X-Request-Timestamp`，传了没意义；走签名头时必须保证时钟准。**
为了"看起来安全"随便填一个时间戳，在签名头路径下会直接把请求打死。

> HMAC 必须对**原始字节**算，不能先 `JSON.parse` 再 `JSON.stringify`（键序/空格会变，签名必失败）。
> 用 curl 时把 body 写进文件，`--data-binary @file`。

### 2.3 请求体字段（`source= custom` / `business` 时的抽取规则）

服务端按**确定性映射**抽取，不扫整包 JSON。取第一个非空命中的字段：

| 归一化字段 | 依次尝试的键 | 约束 |
|---|---|---|
| `title` | `title` → `subject` → `name` → `summary` → `event` | **≤ 512 字**，超出被截断 |
| `body` | `body` → `text` → `content` → `message` → `description` | ≤ 4000 字 |
| `level` | `level` → `severity` → `priority` → `urgency` | 见 §2.4 |
| `externalId` | `id` → `eventId` → `event_id` → `externalId` → `external_id` | 只接受标量，≤191 字 |

**标题或正文至少有一个非空**，否则整条被标 `unrecognized=true` 且 **level 强制降为 `info`**（消息仍会收下，不报错）。

### 2.4 `level` 口径（**最容易踩的坑**）

服务端白名单只有三个：`info` | `warning` | `urgent`。大小写不敏感，且有别名表。

| 你写 | 落库为 | 后果 |
|---|---|---|
| `info` / `notice` / `debug` / `low` / `ok` | `info` | 仅大屏显示 |
| `warning` / `warn` / `medium` / `moderate` / `p2` | `warning` | 大屏黄色 |
| `urgent` / `fatal` / `critical` / `error` / `err` / `high` / `p0` / `p1` / `sev1` | `urgent` | **触发语音播报 + 红色抖动** |
| 空串 / 无法识别 / 字段缺失 / 整个 payload 认不出来 | `info` | **静默降级，无报错** |

**建议**：只写 `info` / `warning` / `urgent` 三个原值。
写别名能通，但**你失去的是确定性** —— 一旦服务端别名表调整，你的语义就变了。

### 2.5 去重语义（决定"为什么它没上屏"）

去重键 `dedupeHash`：

- **带 `externalId`** → `sha256(tenantId \x1f channelId \x1f externalId)`。同一 `externalId` **永远**只落一条。
- **不带 `externalId`** → `sha256(tenantId \x1f channelId \x1f title \x1f body \x1f 时间窗)`，时间窗默认按去重窗口切桶。

> v2 把 `tenantId` 补成了材料第一段（v1 没有）—— 所以**同一 `externalId` 在不同租户下互不干扰**。

命中同一去重键时，服务端**不忽略、而是原地 upsert**：

- **内容逐字全同**（`title` + `body` + `level` + `icon` 全等）→ 返回 `created:false`，**什么都不做**，这是真幂等。
- **任意字段有差异** → **更新那条已有记录**（`id` 不变、`receivedAt` 刷新），并返回 **`created:true`**。

所以 `externalId` 是**「一行」的锚**，不是「一份内容」的锚 —— 同键重推会**改写历史**。

推论（实践中最常踩）：

1. **重试安全**：仅当重发**逐字相同**时不会产生第二条、也不会改写。差一个字就是「原地更新」。
2. **"我推了但没上屏"**：多半是撞了去重键且内容没变 → 想强制产生新消息，就改 `title`/`body`，
   或带一个每次都不同的 `externalId`（如 `deploy-20260919-0201`）。
3. **同一 `externalId` 换了内容 ≠ 新消息**：它会把**旧那条改掉**（大屏上不新增、数量不涨）。
   想追加而非改写，**必须换 `externalId`**。
4. ⚠️ **同键「抬级别」会二次播报**：`level` 从 `info` 改成 `urgent` 是「内容有差异」，
   服务端 upsert 后**无条件** `broadcastMessage`，浏览器侧 `TtsEngine` 收到一条新的 `urgent` → **又播一遍**。
   这既不是新增、也不是幂等，是**重复打扰**。重试时请保持 payload **逐字不变**。

---

## 三、载荷样例

样例文件见 `examples/`，可直接 `curl --data-binary @examples/xxx.json`：

| 文件 | 用途 | level |
|---|---|---|
| `task-complete.json` | AI 一轮任务完成通知（标题带来源） | `info` |
| `task-complete-cursor.json` | 第二个 AI 的同工位通知（演示多 AI 分辨） | `info` |
| `task-created.json` | 新建一条待办通知（subject 写待办标题，标题带来源） | `info` |
| `task-done.json` | 某条具体已完成任务计划通知（subject 写待办标题，标题带来源） | `info` |
| `turn-start.json` | 轮次开始「🙋 收到指令」（**判定无 hook 覆盖时**才由 AI 每轮调 `notify_turn_start`，见 §7.2 C） | `info` |
| `turn-end.json` | 轮次结束「✅ {source} 任务完成」（同上，`notify_turn_end`） | `info` |
| `alert-critical.json` | 生产紧急告警（会播报） | `urgent` |
| `build-failed.json` | CI 构建失败 | `urgent` |
| `need-action.json` | 待你操作 / 阻塞 | `warning` |
| `deploy-done.json` | 部署完成 | `info` |
| `plain-text.txt` | 纯文本投递（`text/plain`） | `info` |

**AI 任务完成通知的最小可用写法**（`externalId` 用 commit 哈希，天然幂等）：

```json
{
  "title": "✅ CodeBuddy 任务完成",
  "body": "优化 MCP 插件参数校验\n\n已推送远程 76c38c5",
  "level": "info",
  "externalId": "commit-76c38c5"
}
```

> 走**裸 HTTP** 时，来源写在 `title` 里（服务端不认 `source` 键，见 §2.6）。
> 走 **MCP / HTTP 传输**时，直接传 `source` 参数，标题会由工具自动拼好。

---

## 四、CLI 封装（不想手写 curl 时）

套件自带 MCP 插件的 **CLI 模式**（同一个 HTTP 通道，只是贴了层壳）：

```bash
node mcp/warroom-webhook.cjs --notify --summary "本轮做了什么" \
  [--level info] [--commit <hash>] [--channel ch-workbuddy] [--source CodeBuddy] [--external-id <key>]

# 自定义标题（告警 / 待办 / 阻塞类），不套「✅ 任务完成」：
node mcp/warroom-webhook.cjs --notify --title "⚠️ 需要你操作：证书 3 天后过期" --summary "..." --level warning
```

给了 `--title` 就走通用推送；不给则走任务完成通知，并自动附「已推送远程 &lt;commit&gt;」。
`--commit` 省略时自动 `git rev-parse --short HEAD`。
`--source` 也可用环境变量 `WARROOM_AI_NAME` 固定（各宿主在 `mcp.json` 里设一次即可）。

**`--external-id <key>`（可选，一般不用给）**：缺省按内容自动生成 —— `push` 类 `mcp:push:<source>:<标题指纹>:<30s桶>`、
待办类 `mcp:task-created|task-done:<source>:<标题指纹>`、有 `commit` 的 `commit-<hash>`。**不同内容不会再互相覆盖。**
所以「一个来源推多种事件」（如宿主 hook 的「收到指令 / 任务完成 / 需要你操作」）**必须**各自显式给 key，例如：

| 事件 | `--external-id` 写法 | 语义 |
|---|---|---|
| 同一提示词 | `hook:prompt:<sid>:<hash>:<30s桶>` | 30s 内重推折叠，跨桶新增 |
| 需要你操作 | `hook:notify:<sid>:<type>:<hash>` | 同类型同内容折叠 |
| 会话状态变更 | `hook:session:<source>:<sid>` | 仅 `resume`/`clear`/`compact`；`startup` **不推**（见下） |
| 会话结束 | `hook:session-end:<sid>` | 一个会话一条 |

> 🔴 **`SessionStart` 的 `startup` 必须静音**：新会话的第一条指令会在 1s 内接着触发 `UserPromptSubmit`
> （实测两条落库间隔 **943ms**，且顺序不定 —— 「收到指令」反而先到），大屏上就是**重复的两条**。
> 引擎的 `emitSessionStart(session, source)` 有四种 source：
> `startup`（应用启动 / 新会话，**静音**）、`resume`（恢复/切换会话）、`clear`（`/clear`）、`compact`（上下文压缩）。
> 后三种才是值得提醒人的真状态变更 —— 因为**上下文可能已不完整**，文案分别用
> `🔄 会话已恢复` / `🧹 会话已清空` / `🗜️ 上下文已压缩`，`level=info`。
> 「有人来了」这个信号统一交给 `UserPromptSubmit`（`🙋 收到指令`），不要两处都推。

**口径**：同事件重推 → 同 key（幂等）；不同事件 → 不同 key（不互相覆盖）。

> 🔴 **`notify_task_complete` 的缺省键是 `commit-<hash>`，在两次提交之间是常量。**
> 不频繁提交时，**同一提交内的每一轮「任务完成」都会命中同一条去重记录**。
> 但注意：这**不等于**「正文不变、大屏不新增」——同键且内容逐字相同才不新增；
> 若正文不同，它会**原地改写上一条**（编号不变、大屏不涨）——两种结果都是「看起来像没推」。
> 要让**每轮**都真正新增，就必须显式给**每次都不同**的键
> （如 `hook:stop:<会话id>:<本轮答复指纹>`）。

**`--source` 的输出长这样**（多 AI 分辨靠它）：

```
✅ 已推送「任务完成」通知至 ch-workbuddy（level=info，source=CodeBuddy，commit=76c38c5）
✅ 已存在（去重命中，未新增）「任务完成」通知至 ch-workbuddy（level=info，source=CodeBuddy，commit=76c38c5）
```

> **`created`/去重一律看文案前缀**：
> `已推送` = **服务端接受了它**（可能是新增，也可能是**原地改写**已存在的那条 —— 前缀不区分这两者）；
> `已存在（去重命中，未新增）` = 逐字重复、什么都没做。
> 两者都是成功，不要因为看到「已存在」就重试（重试还是同一条）。
> 想确认究竟是「新增」还是「改写」，看两次响应的 `id` 是否相同（去重文档 §2.5）。

参数失败时的口径（**都是显式报错，不静默**）：

| 情况 | 行为 |
|---|---|
| 既写了 `arguments` 又平铺了参数 | **报错且不推送**（形状混用） |
| 工具名拼错 | **报错且不推送**（不再静默当成另一个工具执行） |
| `channelId` 带 `%`（URL 编码过的） | **报错**，提示传未编码的裸 id |
| 没发 `initialize` 直接 `tools/call` | `-32002` 拒绝 |
| `title` 超 512 字 / 带裸换行 | 自动截断 + 换行压成空格（不再原样发出） |
| `level` 写 `critical` / `URGENT` | 按服务端口径收敛为 `urgent`（**会播报**） |

---

## 五、排错表（按 HTTP 状态码 / 业务码定位）

| 现象 | 业务码 | 原因与改法 |
|---|---|---|
| 401 | `SIG_MISSING` | 既没带 `?key=`，也没带对应签名头。→ 补 `?key=` |
| 401 | `SIG_INVALID` | 密钥不对；或 HMAC 对的是 parse 后的 body 而非原始字节 |
| 401 | `SIG_TIMESTAMP_SKEW` | 走**签名头**路径且传了 `X-Request-Timestamp`，与本机时钟差 > ±300s。→ 校准，或干脆别传（带 `?key=` 时不会出这个码） |
| 403 | `SSRF_BLOCKED` | 只在出站转发路径出现，入站不会 — 若见到说明打错端点了 |
| 404 | `RESOURCE_NOT_FOUND` | `channelId` 不存在；**或路径漏了租户段**（v2 必须是 `/webhook/{tenantId}/{channelId}`）。→ 去用户中心「接入凭证 → 工位」核对 |
| 410 | `CHANNEL_DISABLED` | 工位被禁用（不是不存在）。→ 启用工位，或换一个 |
| 413 | `PAYLOAD_TOO_LARGE` | 请求体 > 1 MiB。→ 精简 `body`（大日志只放摘要 + 链接） |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Content-Type 畸形/不支持。→ 老老实实写 `application/json` |
| 422 | `UNSUPPORTED_SOURCE_TYPE` | `im_feishu` / `im_dingtalk` / `im_wecom` 属 P1，未启用 |
| 429 | `RATE_LIMITED` | 超 120/min/工位。→ 按 `Retry-After` 退避后重投（去重保证不重复） |
| 500 | `INTERNAL_ERROR` | 服务端异常。→ 重试 2 次仍失败则上报 |
| **HTTP 传输** 401 | `AUTH_TOKEN_MISSING` | 打 `/api/v2/mcp` 没带 `Authorization: Bearer`。→ 补上（该端点**不接受** `?key=`） |
| **HTTP 传输** 401 | `AUTH_TOKEN_INVALID` | Bearer 令牌不对 / 已吊销；**用演示密钥当令牌也会落到这一码**。→ 换真实 ApiToken |
| **HTTP 传输** 403 | `AUTH_SCOPE_INSUFFICIENT` | 令牌没有 `write` scope。→ 换有写权限的令牌 |
| **HTTP 传输** 405 | `METHOD_NOT_ALLOWED` | 用 GET 打了端点。→ 只支持 POST（无 SSE） |
| **HTTP 传输** `-32601` | — | 调了 `resources/*` / `prompts/*` 等未实现方法。→ 看 `error.data.supported`，只用列出的四个方法 |
| **HTTP 传输** 无响应体 | — | 发的是 `notifications/*`（规范：通知不回包，服务端返 204）。→ 正常，无需处理 |
| 2xx 但不播报 | — | **99% 是 level 不是 `urgent`**（别名写错或整条 `unrecognized` 降级） |
| 2xx 但大屏不新增 | — | **撞去重键**（见 §2.5）。→ 换 `title`/`body`/`externalId` |

> 契约承诺 429 响应带 `RateLimit-*` / `Retry-After` 头，但**当前服务端未实现这些响应头**。
> 客户端不能依赖它自适应退避 —— 请用固定指数退避（1s → 2s → 4s，最多 3 次）。此为已知缺口。

---

## 六、AI 调用时请遵守

1. **别猜 `channelId` / `tenantId`**。默认工位是 `ch-workbuddy`；不确定就问用户，或从
   `GET /api/v2/stations`（需 ApiToken）取。租户段同样不能猜。
2. **别在代码/文档里写死密钥**。用 `$WARROOM_WEBHOOK_KEY`。若某平台只能填静态 URL，
   把密钥放环境变量或密钥管理，不要提交进仓库。
3. **级别宁低勿高**。`urgent` 会打断人（语音播报）。只有真的需要人立刻看时才用。
4. **正文给结论，不给原始日志**。`body` 第一行写结论，细节放链接。
   正文会进播报文本，**不要塞 JSON 键名或换行堆叠**。
5. **带上来源**，便于多 AI 接入后在大屏上分辨谁推的。两条通道的写法不同：
   - 走 MCP / HTTP 传输 → 传 `source` 参数（如 `"source":"CodeBuddy"`），标题由工具拼好；
   - 走**裸 HTTP** → 服务端不认 `source` 键，请自己写成 `"title":"✅ CodeBuddy 任务完成"`，
     并自带 `"externalId":"ai:CodeBuddy"`（否则重推会产生多条）。

   **来源名用稳定的短标识**（`CodeBuddy` / `Cursor` / `ci-bot`），不要每次都带时间戳 —— 那样每条都是新消息、刷屏。
6. **重试无害**，但要幂等：优先带 `externalId`。
7. **本 Skill 只负责推送**。查工位、看消息、改配置需要 ApiToken，
   走 `POST /api/v2/auth/login` + `Authorization: Bearer <token>`，不在本 Skill 范围。
8. **轮次事件先判归属，再决定调不调**（详见 §7.2 C）：`initialize` 的 instructions 会**现探本机事实**
   给出 `hook` / `self` / `unknown` 结论 —— 判为「hook 已覆盖」就**不要**调 `notify_turn_start` /
   `notify_turn_end`；判为「无 hook」则**每轮成对调**（开始 `notify_turn_start`、结束 `notify_turn_end`，
   **含普通对话**），否则大屏看不到轮次边界。
   🔴 别按宿主品牌猜（WorkBuddy 上 hook 也可能压根没生效）；也**别指望轮询** —— MCP 没有任何定时唤醒原语，
   漏调就是静默缺失，事后补不回来。

---

## 七、与 MCP 的关系（三条通道怎么选）

| | MCP stdio（`mcp/warroom-webhook.cjs`） | 裸 HTTP / CLI | MCP over HTTP（`POST /api/v2/mcp`，**市场连接器走这条**） |
|---|---|---|---|
| 适用宿主 | 能 spawn 子进程的本地客户端 | **任何有 shell 的 AI** | **没有 shell 的 AI**：浏览器里的 / 云端 Agent |
| 需要配置 | `mcp.json` | 零配置（读本文件即可） | 一个端点 + 一个 Bearer 令牌 |
| 浏览器里的 AI | 接不进来 | 接不进来 | **可以了**（本文件 §2.7） |
| 鉴权 | 本机环境变量（可回落演示密钥） | `?key=` 或签名头 | **必须** Bearer 令牌（ApiToken **或** OAuth access token；不接受 `?key=` 与演示密钥） |
| 工具数 | **7 个** | 0（自己拼 HTTP） | **5 个**（缺 `notify_turn_start` / `notify_turn_end`） |
| 契约定义 | 写在 `inputSchema` 里 | 写在本文件里 | 与 stdio 的**命名 / 参数口径同源**，5 个工具同名同参数 |

### 7.1 接入流程：按通道分两种

#### 7.1.1 HTTP 通道（市场连接器 / OAuth）：**工具不需要配接收端，自动播报需要一次 `--setup`**

走 §〇·路径 1 或 §2.7 时，**不需要用 `setup_receiving_endpoint` 去做「绑定」** —— 地址与身份
**已经在配置里定死**：

- **地址**：连接器包里写死 `https://<中台>/api/v2/mcp`；
- **身份**：OAuth 令牌由 WorkBuddy 的 OAuth 管理器自动以 `Authorization: Bearer` 注入；
- **租户**：服务端从**令牌归属**取；工具参数里没有、也**不接受** `tenantId`；
- **工位**：取工具参数 `channelId`（缺省 `ch-workbuddy`）。

所以**工具侧**的「接入」= 点连接 + 授权完成，之后直接调 §7.2 的 5 个工具。
`setup_receiving_endpoint` 在这条通道上仍然可用，但语义不同：它**不做绑定**（没有可绑的东西），
只做「推一条 🟢 服务上线 + 回显本工位模板」，供用户问「接好了吗」时用一次。

**🟢 但「自动播报」需要一次本地落盘 —— 因为 hook 是独立进程，拿不到 OAuth 令牌。**
连接器包里带 `hooks/hooks.json`（9 个宿主事件），它读的是本地文件
`~/.warroom/receiving-endpoint[.<scope>].json`。所以授权完成后要补这一步（AI 执行，用户只需贴 URL）：

```bash
node "<包目录>/mcp/warroom-webhook.cjs" --setup "<用户给的完整入站地址>"
```

包目录形如 `~/.workbuddy/plugins/cache/<市场>/aiwho-warroom/<版本>/`，**不要写死版本号**，
先 `ls -d ~/.workbuddy/plugins/cache/*/aiwho-warroom/*/` 定位。

**这一步就是「示例词」该干的事** —— hook 本身不需要装（随包生效），示例词负责的是把
「用户手里的密钥」交给本地进程。用户说完下面这类话之后，按 4 步走：

> 「帮我确认指挥台的自动播报装好了没，没装就装上」

1. `ls -d ~/.workbuddy/plugins/cache/*/aiwho-warroom/*/` 拿到包目录（**别猜版本号**）；
2. 要一条完整入站地址：用户中心 → 接入凭证 → 工位 → 「复制完整地址」（形如
   `https://<中台>/api/v2/webhook/<租户>/<工位>?key=…`）；
3. 跑上面那条 `--setup`，它会把基址 / 租户 / 工位 / 密钥写进 `~/.warroom/receiving-endpoint[.<scope>].json`；
4. 回报「目标 = 哪个中台 / 哪个工位」，并让用户随便发一句话验一次（见下面的排查）。

> 没做这一步也不报错：hook 会识别出「插件形态且没有接收端」并**静默跳过**，
> 大屏上只是没有自动消息（AI 主动调工具仍正常）。

**用户说「装完不自动播报」时的排查顺序**（别一上来就重装）：

| # | 检查 | 判读 |
|---|---|---|
| 1 | `~/.warroom/receiving-endpoint[.<scope>].json` 是否存在 | 不存在 = `--setup` 没跑过（**最常见**） |
| 2 | `~/.workbuddy/logs/warroom-hook.log` 有没有**今天**的事件 | 有 = hook 在跑、只是推送失败（看日志里的 HTTP 状态） |
| 3 | 主日志搜 `Loaded hooks configuration from extension: aiwho-warroom` | **有** = 引擎已加载插件 hooks，不用再装；**没有** = 走第 4 步 |
| 4 | 兜底：`node "<包目录>/scripts/install-hook.mjs" --host=workbuddy` | 把 9 个事件直接写进 `~/.workbuddy/settings.json`（幂等、写前备份、只动它自己写的 handler） |

> 🔴 第 4 步**只在第 3 步为空时做**。插件 hooks 已生效还去写 settings.json，等于每个事件跑两遍
> （虽然后端靠幂等键会折叠成一条，但每轮白起两个 node 进程）。
> 想撤掉旧的 settings.json 注册：`node scripts/install-hook.mjs --uninstall`。

#### 7.1.2 stdio 通道：先装服务，后给接收端（不再握手即推）

旧版在 `initialize` 握手时**自动**推一条「🟢 服务上线」，发生在用户还没给服务端地址 / 工位 / 密钥之前，
等于「连上即推测试」。现已改为**两步分离** —— 把「安装」和「推送」彻底拆开：

1. **安装服务（仅接线）**：MCP stdio 接入后**不会**向任何地址发消息；AI 读到这里也只是知道有哪些工具可用。
2. **用户给接收端**：用户登录用户中心 → 接入凭证 → 选中该工位，复制完整入站地址
   （形如 `https://<中台>/api/v2/webhook/<租户id>/<工位channelId>?key=<密钥>`）贴给 AI。
3. **AI 识别接收端**：AI 调用 `setup_receiving_endpoint(endpoint=<那条URL>)`，解析出
   **基址 / 租户 / 工位 channelId / 密钥**，并设为本次会话的默认推送目标。
4. **确认连接**：在这一步才推送一条 `🟢 服务上线：<source>`（`level=info`）—— 此时地址与密钥才是真的。
5. **回显全部模板**：工具返回**本工位会出现的全部消息模板清单（A=AI 主动推送 + B=宿主 Hook 自动推送，见 §7.2）**。
6. **咨询是否修改模板（必须，不可跳过）**：回显后**向用户提问**，例如：「上面这些模板的标题 / 文案需要改吗？」
   - 用户**不改** → 进第 7 步；
   - 用户**要改** → 记清「哪个模板 + 改成什么」，改 `lib/mcp-contract.mjs`（标题模板唯一来源）与
     `mcp/warroom-webhook.cjs` 的 `TEMPLATE_GUIDE`（回显清单），改完跑 §七 两个契约检查，回显确认后再进第 7 步；
   - ⚠️ 模板是**代码级**的，改了会影响所有走这套件的工位，不是「单工位开关」；只想让某类事件「不出现」，
     用「不调对应工具 / 不装对应 Hook」实现，而非改文案。
7. 之后 AI 才能用 §7.2 的全部 7 个工具推事件。

> 🔑 **绑定会持久化（2026-10-10 修复）**：`setup_receiving_endpoint` 解析出的基址 / 工位 / 密钥会写进本地状态文件
> （`WARROOM_RECEIVING_STATE` 环境变量 > `~/.warroom/receiving-endpoint[.<scope>].json`），**进程重启 / 宿主重新信任连接器 /
> 升级都不会丢**，也不会再回落 `http://localhost:3500`（本机 dev 端口，平时不开 → 静默推失败）。
> 宿主 Hook（独立进程）也读这份状态文件，所以用户设一次接收端，A 列 MCP 工具与 B 列 Hook 自动推送都能用。
> 想改工位 / 服务端，重新调一次 `setup_receiving_endpoint` 覆盖；想彻底清掉，删该状态文件。

| 项 | 值 |
|---|---|
| 触发「服务上线」的时机 | **用户给出接收端后**，`setup_receiving_endpoint` 内部推（不再在 `initialize` 推） |
| 绑定落盘位置 | `WARROOM_RECEIVING_STATE` > `~/.warroom/receiving-endpoint[.<scope>].json`（重启 / Hook 均读回） |
| 落盘的 scope | 取 `WARROOM_AI_NAME`（多 AI 同机时各占一份，互不覆盖；未配则共用 `receiving-endpoint.json`，见 §7.2 C-2） |
| 身份来源 | `setup_receiving_endpoint` 的 `source` / `aiName`，其次环境变量 `WARROOM_AI_NAME`，再次 `未署名客户端` |
| 租户 / 工位 / 密钥来源 | 从接收端 URL 的 `/webhook/<租户>/<channelId>` 路径与 `?key=` 解析，**不靠手填** |
| 幂等键 | `mcp:online:<name>:<10 分钟桶>` —— 抖动重连折叠，隔段时间再接入算新一次；`<name>` slug 化，纯中文名记成 `unknown` |
| 关闭上线通知 | 环境变量 `WARROOM_ONLINE_NOTIFY=0`（默认开；护栏脚本会设它避免污染抓包断言） |

> ⚠️ 本节流程**只属于 stdio 通道**。市场连接器包的 MCP 是**远端 HTTP**（`connector/mcp.json` 里
> `type=streamableHttp` → `https://<中台>/api/v2/mcp`），**本机不跑 MCP 进程**，所以那里**没有「绑定接收端」这一步**
> —— `?key=` 与 `WARROOM_RECEIVING_STATE` 只对本地 stdio 侧有意义。
> 包里的 `mcp/warroom-webhook.cjs` 与 `lib/` 确实会打进去，但它是**随包 hook 的运行时依赖**
> （`hooks/bin/warroom-hook.cjs` 用 `--notify` 复用它推送），**不是**连接器的 MCP 入口。
> 连接器形态的接收端落盘由随包 hook 的 `--setup` 完成（§7.1.1）；
> 工具侧 `setup_receiving_endpoint` 在 HTTP 通道上只做**接入确认**：推一条 🟢 服务上线并回显模板，见 §7.1.1。

### 7.2 工具与「本工位会出现的全部消息模板」

⚠️ 区分两个来源，否则会误以为「模板只有 4 个」：

- **A. AI 主动推送**：AI 通过 MCP 工具**显式调用**产生（需 AI 调）。
- **B. 宿主 Hook 自动推送**：宿主事件驱动、**无需 AI 调用** —— 但它要**真的在跑**才算数（判定见 §7.2 C）：
  脚本本体在 `.workbuddy/hooks/warroom-hook.cjs`（**不是** `~/.workbuddy/hooks/`，那儿没有这个目录）。
  连接器包会把它复制成 `hooks/bin/warroom-hook.cjs` 并靠随包的 `hooks/hooks.json` **自动生效**（§7.4）；
  stdio 套件则要用 `scripts/install-hook.mjs` 注册进宿主配置。
  🔴 两种形态都还需要**一次接收端落盘**（连接器跑 `--setup`、stdio 调 `setup_receiving_endpoint`），
  缺了它 hook 会**静默跳过**（不报错、不刷屏，大屏就是没有）。

#### A. AI 主动推送（MCP 工具）—— ⚠️ 先确认你的通道有几个工具

| 工具 | 哪个通道有 | 触发场景 | 大屏标题 / 模板 |
|---|---|---|---|
| `push_warroom_event` | **HTTP + stdio** | 通用（告警 / 阻塞 / 进展）→ 自定义标题 | 你给的 `title`；`level=urgent/warning` ⇒ `⚠️ 需要你操作`，触发语音播报 |
| `notify_task_complete` | **HTTP + stdio** | 一轮任务收尾 / post-commit | `✅ {source} 任务完成` |
| `setup_receiving_endpoint` | **HTTP + stdio**（语义不同） | 用户问「接好了吗 / 还缺什么」→ 确认连通并回显模板 | 推「🟢 服务上线：<source>」+ 回显下方模板。stdio 侧还兼「绑定接收端」（§7.1.2） |
| `notify_task_created` | **HTTP + stdio** | 新建一条待办 | `📋 {source} 新建任务计划：<待办标题>` |
| `notify_task_done` | **HTTP + stdio** | 某条具体已完成任务计划 | `✅ {source} 已完成任务计划：<待办标题>` |
| `notify_turn_start` | 仅 stdio（HTTP 通道**没有**此工具） | 每轮开始（收到用户消息） | `🙋 收到指令` —— ⚠️ **只在 §7.2 C 判为 `self` / `unknown` 时调**；hook 已覆盖时调它 = 重复两条 |
| `notify_turn_end` | 仅 stdio（HTTP 通道**没有**此工具） | 每轮结束（含普通对话） | `✅ {source} 任务完成` —— 同上 |

> 🔴 **HTTP 通道有 5 个，只缺 `notify_turn_start` / `notify_turn_end`**（轮次工具，仅 stdio）。
> 拿这两个名字调 HTTP 端点会报「未知工具」。
> 🟢 **轮次播报不需要装 stdio**：连接器包自带 hook（§7.4），9 个宿主事件含
> 「🙋 收到指令 / ✅ 任务完成」，跑一次 `--setup` 就有了。stdio 侧这两个工具只留给「宿主没有 hook」的场景。
> ⚠️ 但「自带」不等于「已在跑」—— 它同样需要接收端、且可能静默失效。
> **判断靠 §7.2 C 的 `--coverage`（或 instructions 里的现探结论），不要靠宿主品牌。**
>
> ✅ **不同待办 / 不同标题天然各占一条**（Issue #2 已修）：`notify_task_created` 缺省键是
> `mcp:task-created:<source>:<待办标题指纹>`，`notify_task_done` 是 `mcp:task-done:…`，
> `push_warroom_event` 是 `mcp:push:<source>:<标题指纹>:<30s桶>` —— 不必再手工构造 `externalId`。

#### B. 宿主 Hook 自动推送（连接器包随包生效；stdio 套件需 `install-hook.mjs` 注册。装好后无需 AI 调用）

| 宿主事件 | 大屏模板 |
|---|---|
| `UserPromptSubmit`（有人发指令） | 🙋 收到指令 |
| `resume`（恢复 / 切换会话） | 🔄 会话已恢复 |
| `/clear` | 🧹 会话已清空 |
| `compact`（上下文压缩） | 🗜️ 上下文已压缩 |
| `session-end`（一个会话一条） | （会话结束） |

> `setup_receiving_endpoint` 的入参：**stdio 侧 `endpoint` 必填** ＝ 用户中心「接入凭证 → 工位」复制的完整入站地址；
> `source` 可选（多 AI 分辨，否则回落「未署名客户端」）。stdio 侧调用它之前，本服务**不会**向任何地址发消息。
>
> **HTTP 侧 `endpoint` 可选**：可以传同形状 URL（其中的 `?key=` 会被**忽略且不保存**），
> 也可以直接传裸 `channelId`，或只传 `source` 走默认 `ch-workbuddy`。
> 鉴权只认 Bearer 令牌、租户由令牌决定；URL 的租户段若与令牌归属租户不一致会**直接被拒**（防串租户）。

#### C. 轮次事件 × 谁负责（🔴 别两头都推，更别两头都不推）

「🙋 收到指令 / ✅ 任务完成」是**轮次级**事件。MCP 是**客户端驱动**协议 —— 服务端只在客户端发 `tools/call`
时才知道发生了什么，**没有原语**能感知「用户刚开口 / 助手刚答完」，也**没有轮询**（服务端不能反过来问 AI
「上一轮推了吗」，AI 也不会被定时唤醒）。所以这两个信号只有两种来源，**互斥**：

| 来源 | 触发方式 | 可靠性 |
|---|---|---|
| 宿主 hook 的 `UserPromptSubmit` / `Stop` | 事件驱动，宿主每轮必触发 | ✅ **高** —— 唯一不依赖模型自觉的 |
| AI 每轮主动调 `notify_turn_start` / `notify_turn_end` | 靠模型自己记得 | ⚠️ **低** —— 漏调就静默缺失，且无法事后补偿 |

> 🔴 **别用「宿主品牌」判断该走哪条。** hook 的真实生效条件是三件事**同时**成立：
> ① 宿主注册了 hook（settings.json / 插件 `hooks/hooks.json`）② 有可用接收端 ③ 进程真跑起来且推成功。
> 所以 `WorkBuddy + stdio 套件但没跑 install-hook.mjs`、`连接器但没跑 --setup`、
> `settings.json 里的路径指向已删除的目录` —— 这三种都是**零报错、大屏就是没有**，
> 而按品牌判断会得出「有 hook，我不用管」→ 轮次静默全丢。

**怎么判断（一条命令，读本地事实而不是猜）：**

```bash
node "<包目录>/mcp/warroom-webhook.cjs" --coverage
```

它读 hook 日志最近活动 / 接收端文件 / hook 注册痕迹，给出 `mode`：

| mode | 含义 | AI 该怎么做 |
|---|---|---|
| `hook` | 近 24h 有 hook 轮次事件且推送成功 | **不要**调那两个工具（同一轮会重复两条） |
| `self` | 无注册、无日志 → 完全没有自动来源 | **每轮成对调**（含普通对话），否则大屏没有轮次边界 |
| `unknown` | 有注册痕迹但近 24h 无活动 | 先问用户「大屏上有『🙋 收到指令』吗」，看不到再由你补 |

> ℹ️ 若输出里还有 `target=differs(...)`（hook 推的工位 ≠ 状态文件记的工位），**通常不是故障**：
> 状态文件全机共享，同一台机器装多个 AI 时各自工位不同很正常（实测本机 WorkBuddy 推 `ch-workbuddy`、
> 另一套 AI 写的是 `qclaw`）。只有确认「这两者本应相同」时才需要排查。要彻底避免这类混淆，
> 见下面的「多 AI 同机」。

> 💡 MCP 在 `initialize` 的 `instructions` 里**已经带了这个判定**（每次握手现探一次），AI 不需要手动跑命令 ——
> 命令是给人排查/验收用的。`notify_turn_start` / `notify_turn_end` 的返回值还会附一句
> 「本条可能与 hook 重复」的事实提示，所以**即使 AI 判断错了，也不会静默重复刷屏**。

> 🔴 **本节「AI 每轮调工具」只对 stdio 通道成立**（那两个 tool 在 HTTP 通道上不存在）。
> 走市场连接器（HTTP）时，轮次事件**只能**靠宿主 hook；拿 `notify_turn_end` 去调 HTTP 端点会报「未知工具」。
> 也就是说连接器用户若 hook 没生效，**没有任何 AI 侧兜底** —— 唯一出路是把 hook 修好（§7.1.1 / §7.4）。

#### C-2. 多 AI 同机（🔴 一台机器上装两套以上 AI 时必读）

接收端绑定落在 `~/.warroom/receiving-endpoint[.<scope>].json`，`scope` 取 **`WARROOM_AI_NAME`**。
不配 scope 时只有**一份**全机共享的 `receiving-endpoint.json` —— 谁最后跑 setup 谁覆盖它，
于是**所有 AI 都往同一个工位推**（零报错，只是「另一个 AI 的大屏上冒出别人的消息」）。

> 实测现场（2026-10-23）：本机同时装着 WorkBuddy 与 QClaw，
> `receiving-endpoint.json` 里是 QClaw 写的 `qclaw`，而 WorkBuddy 的 hook 推 `ch-workbuddy`。
> 当时没炸，只因为两者跑的都是**不读该文件**的旧构建；一旦本仓（会读）装进 WorkBuddy，
> 它的 `push_warroom_event` 就会推到 QClaw 的工位上去。

**做法：给每个宿主的 `mcp.json` 各配一个 `WARROOM_AI_NAME`**（这个变量本来就该配，用于多 AI 分辨来源）：

```json
"env": { "WARROOM_AI_NAME": "WorkBuddy", "WARROOM_API_BASE": "https://…" }
```

→ 各自写 `receiving-endpoint.WorkBuddy.json` / `receiving-endpoint.QClaw.json`，互不覆盖。
Hook 是宿主 spawn 的独立进程、**拿不到** `mcp.json` 里的 env，所以它启动时会自己把从 `mcp.json`
读到的 `WARROOM_AI_NAME` 补进进程环境（`warroom-hook.cjs` 的 `connection()`），保证两边读同一份。

> `WARROOM_RECEIVING_STATE` 优先级最高（可直接指到各不相同的路径），适合特殊部署 / 测试隔离。

> 🔴 纯 MCP 宿主上「任务完成」用 `notify_turn_end`，**别用 `notify_task_complete`**：后者的缺省幂等键是
> `commit-<hash>`，在两次提交之间是**常量** → 第二轮起命中去重（**去重命中不更新正文**）→ 大屏永远只有第一条，
> 现场就是「调了也白调」。`notify_turn_end` 的键按「摘要指纹 + 30s 桶」生成，每轮天然不同。
>
> 🔴 **「每轮必调」没法由 MCP 协议强制，也没法轮询补**（协议不定义轮次边界，AI 不会被定时唤醒）。
> 只能靠三层约规兜底：① `initialize.instructions`（服务端唯一能在会话开始发声处）② 本文件
> ③ **宿主常驻规则文件**（AGENTS.md / 系统提示 / custom instructions —— 等价于给纯 MCP 宿主装一个「软件 hook」）。
> 若宿主连常驻规则都没有，则退回 A 列（AI 主动推送告警）或 git `post-commit` 兜底 ——
> **别指望「AI 会记得每轮调」能兜住**，这是整套机制最薄的一环；能装 hook 就装 hook。

### 7.3 🔴 配置 `mcp.json` / `settings.json`：node 路径陷阱（会被升级静默打断）

本 MCP（stdio）与宿主 Hook **都要靠一个 node 进程跑 `*.cjs`**。给它们配 `command`（运行 node）时，
有一个**会反复重演**的坑：

**❌ 不要写死托管/IDE 管理的 node 版本化路径**，例如：

```
C:/Users/<你>/.workbuddy/binaries/node/versions/22.22.2-6/node.exe
```

这类路径带构建号或版本号，IDE/宿主升级 node 时**旧目录会被直接删除** → 这条路径没了 → 进程起不来 →
（MCP）工具静默消失、（Hook）全部自动推送静默停摆。**无报错，只是不工作。**

**✅ 正确写法（按优先级）：**

| 做法 | 配置示例 | 说明 |
|---|---|---|
| **零本地依赖（最稳）** | 装**市场连接器**，走 OAuth 自动注入：`"type":"streamableHttp","url":"https://<中台>/api/v2/mcp"`（**不写 headers**，令牌由 OAuth 管理器注入；见 §2.7 / §〇·路径 1） | 根本不需要本地 node，升级永不断链；Hook 无此选项 |
| 手工令牌（无 OAuth 时） | `"type":"streamableHttp","url":"https://<中台>/api/v2/mcp","headers":{"Authorization":"Bearer <ApiToken>"}` | 需要自己有 ApiToken，且**要自己管过期**；能走 OAuth 就别用这条 |
| **系统 node 绝对路径（宿主型推荐）** | `"command":"C:/Program Files/nodejs/node.exe"` | 系统 node 在 `Program Files` 下，IDE/宿主托管升级删的是它自己的版本目录，碰不到系统 node；node 官方升级是原地覆盖同路径，也稳 |
| `runtime` 托管（官方文档写法） | `"command":"node","runtime":{"type":"node"}` | **仅市场连接器包**可靠；个人配置文件可能不解析 `runtime`，且宿主自身 PATH 缺 node 时裸 `command:"node"` 会 spawn 失败 —— 本机用系统 node 绝对路径更稳 |

**🔴 第二个静默坑：路径含空格必须加引号。** Hook 的 `command` 是交给 **bash** 执行的（宿主只给脚本路径加了引号，
**node 路径没加**）→ `C:/Program Files/nodejs/node.exe` 里的空格被 bash 当分隔符 → `C:/Program: command not found`，
**`exit code=127`，照样静默不工作**。所以 Hook `command` 里 **node 路径也必须用引号包住**：

```json
"command": "\"C:/Program Files/nodejs/node.exe\" \"<本套件目录>/.workbuddy/hooks/warroom-hook.cjs\""
```

**验证配置真的生效**（改完别只看 JSON，要实测）：

- **MCP**：重启连接器后调一次任意工具（如 `push_warroom_event`）看是否 `created:true`；进程清单里应有 `node …/warroom-webhook.cjs` 在跑。
- **Hook**：恢复 / 切换一次会话，看日志是否出现 `SessionStart(resume) … exit=0`（而不是卡在旧日期）。

> 这两处不用手写：`node scripts/install-hook.mjs` 会挑**系统 node**、**加引号**、**幂等**合并、
> 写前**备份**，并且 `--check` 可干跑比对、`--uninstall` 可干净移除（只动它自己写的 handler，不碰别人的）。
> 宿主支持矩阵与「为什么 Claude Code 要带 `--host=claude-code`」见 §7.4。

### 7.4 宿主 × 自动推送：hook 装得上吗

🟢 **WorkBuddy 上不用「另装」**：连接器包落盘后就是插件包（`.codebuddy-plugin/plugin.json`），
包根下有 `hooks/hooks.json`，引擎的 `HookExtensionLoader` 会**自动发现**它（源码里是无条件
`pathExists(<插件根>/hooks/hooks.json)`），并把 `${CODEBUDDY_PLUGIN_ROOT}` 注入 hook 命令。
**唯一要补的是接收端地址**（hook 是独立进程，拿不到 OAuth 令牌）—— 见 §7.1.1 的 `--setup` 那一条命令。

> 这套机制与内置插件同源：腾讯文档插件的 `hooks/hooks.json` **也没有在 plugin.json 里声明**，照样被加载。
> 🔴 **不要**在 `plugin.json` 里再写 `"hooks"` 键：引擎「声明」与「自动发现」两条路都会读，
> 而合并是数组拼接、**不去重** → 9 个事件变 18 条，每个事件白跑一次 1250 行的子进程。
> （`scripts/build-connector-marketplace-zip.mjs` 里刻意不写，`connector-check` 有反向断言钉住。）
> 以前「连接器只有工具、没有自动推送」的说法已作废：那是包内**没放** hooks，不是规范不支持。

| 宿主 | B 列自动推送 | 怎么装 | 备注 |
|---|---|---|---|
| **WorkBuddy（连接器市场）** | ✅ **随包生效** | 装连接器 → 跑一次 `--setup <入站 URL>` | 包内 `hooks/hooks.json`，9 个事件 |
| **WorkBuddy（stdio 套件）** | ✅ | `node scripts/install-hook.mjs` | 写 `~/.workbuddy/settings.json`，与包内 hook 同一份脚本 |
| **Claude Code** | ✅ | `node scripts/install-hook.mjs --host=claude-code` | 写 `~/.claude/settings.json`；事件名与结构**同源** |
| Cursor / Copilot CLI / Windsurf | ⚠️ **有** hook，但**未适配** | 装不上（事件名与配置结构都不同） | 退回 A 列（MCP 工具） |
| Codex / Gemini CLI / Cline / Roo / Continue / Zed | ❌ 无 hook 机制 | 装不上 | 退回 A 列 |
| 任何会 `git commit` 的 AI | ✅（与 AI 品牌无关） | 在你的仓库加 post-commit 推送 | 提交后自动推一条 |

**为什么 Claude Code 能复用同一个脚本**：本脚本吃的事件名与 stdin 字段
（`session_id` / `transcript_path` / `cwd` / `hook_event_name` / `stop_hook_active` / `prompt`）
以及配置形状（`{"hooks":{"<事件>":[{"hooks":[{"type":"command",…}]}]}}`）
**就是 Claude Code 的 hook 协议**（同名同形）。

🔴 **但有一个必须改的点**：WorkBuddy 认 stdout 上的 `{"async":true}` 握手（让 Stop 不阻塞「本轮收尾」），
而 **Claude Code 会把 hook 的 stdout 当上下文注入下一轮** —— 原样照搬等于**每次提问都往模型上下文里塞一段 JSON**。
所以注册到 Claude Code 时**必须**带 `--host=claude-code`（脚本据此闭嘴），异步交给 handler 的 `"async": true`。
`install-hook.mjs` 已把这两点都处理好了 —— **别手抄命令**。

> 📦 **连接器包内 hooks 的运行时要怎么铺**（改包 / 排查时看）：
> `hooks/hooks.json` + `hooks/bin/warroom-hook.cjs`，并按仓库同一套相对层级带上
> `mcp/warroom-webhook.cjs` 与整个 `lib/`（`mcp-contract` / `demo-secret` / `receiving-endpoint`）。
> 少一个文件不会报错，只会让 hook 后台进程静默失败 —— 所以两个打包脚本都按**目录**枚举 `lib/`。

**兜底顺序**（宿主装不了 hook 时）：
1. **MCP 工具**（A 列）—— 所有宿主通用，但要求 AI「想起来调」；
2. **git hook**（`post-commit`）—— 任何会 commit 的 AI 都触发，与 AI 品牌无关。

**三条通道共用同一套口径**（level 白名单与别名、title 512 / body 4000、source 净化与 32 字上限、
任务完成标题模板、参数形状、`externalId` 规则），权威定义在
**本套件** `lib/mcp-contract.mjs`（唯一来源）。

两个校验脚本守着它，**改一处不改另一处会直接失败**：

| 命令 | 校验什么 |
|---|---|
| `node scripts/mcp-contract-check.mjs` | 契约 ↔ MCP stdio ↔ SKILL ↔ examples（含真起进程抓包断言 source / 标题 / 截断 / 参数形状） |
| `node scripts/webroom-contract-check.mjs` | 契约 ↔ SKILL ↔ MCP（含 examples 载荷合法性、别名表、必填项、CLI 参数） |

本文件写错一次，所有读它的 AI 会一起推错 —— 所以**改契约必须同时改 MCP 工具定义并跑这两个检查**。

### 7.5 中台侧（服务端）交叉校验（可选）

上面的两个检查默认只校验**本套件内部**。若要顺带校验「契约 ↔ 服务端实现」是否还一致，
可在 webhookroom（服务端仓）经 submodule 调用并传参，例如：

```bash
node scripts/mcp-contract-check.mjs \
  --server-plugin=server/src/plugins/mcp-http.ts \
  --server-routes=server/src/routes/index.ts \
  --server-levelmap=server/src/normalizers/levelMap.ts \
  --server-openapi=docs/openapi.yaml

node scripts/webroom-contract-check.mjs --server-root=<webhookroom 仓根>
```

不传这些参数时，服务端相关检查整体跳过，保证「只拿本套件」也能全绿。

### 7.6 stdio 客户端的寻址形状：v2 双段 + v1 单段兼容

`setup_receiving_endpoint` 会按接收端 URL 的**段数**自动判定目标中台版本，**不需要你手选**：

| 接收端 URL 形状 | 客户端发出的目标 | 适用中台 |
|---|---|---|
| `…/api/v2/webhook/<租户>/<工位>?key=…`（两段） | `POST {基址}/api/v2/webhook/{租户}/{工位}?key=…` | **v2（SaaS）** |
| `…/api/v1/webhook/<工位>?key=…`（一段） | `POST {基址}/api/v1/webhook/{工位}?key=…` | v1（自托管旧部署） |

- **租户段来源**：接收端 URL 的第二段（`setup_receiving_endpoint` 解析）或环境变量 `WARROOM_TENANT`，**不靠手填**。
  绑定后写进本地状态文件，重启 / Hook 均读回。
- **兜底校验**：若给了 `/api/v2/webhook/…` 却只有一段（手删了租户段），客户端会**显式报错**，
  而不是把地址发到已下线路由；多余段（`/webhook/a/b/c`）同样直接拒绝，不再静默截断。
- **HTTP 传输（市场连接器）不走这条** —— 它的地址由连接器写死为 `…/api/v2/mcp`，见 §〇·路径 1。

---

## 八、运行环境：你这个「进程」到底住在哪（云端 / 容器 AI 通用版）

**上面 §一 那三行 `export` 是给自己手推用的。但真正常见的场景是：没人手推，AI 自己要在
运行时推。** 而「运行时」不是一个环境，是两类，差别不在你多会写代码，而在**谁去调用你**：

| | 常驻本地（宿主型） | 一次性容器（渲染型） |
|---|---|---|
| 典型 | WorkBuddy / Claude Code / Cursor 的本机插件与 hook | **云端构建里的 NPC**、CI 里的脚本、一次性的 Reviewer 容器 |
| 谁触发 | 宿主按事件拉起你（`UserPromptSubmit` / 提交后 / 会话收尾） | **平台按「一条评论 / 一次按钮 / 一次提交」把容器拉起来，跑完销毁** |
| 容器里有什么 | 用户自己配的 `mcp.json` / `~/.workbuddy` | **一个刚 clone 的空仓库 + 平台注入的那几个 `CNB_*` 变量。没有 `mcp.json`，没有 `WARROOM_*` 环境变量，没有后台服务端。** |
| 推消息靠什么 | 宿主替你把环境变量注入子进程 | **只能靠你自己从仓库里读配置拼出来 —— 没有任何东西会替你注入** |

**渲染型是默认会被漏掉的一类。** 本套件文档此前所有命令都默认「你已经有了 `WARROOM_API_BASE` / `WARROOM_WEBHOOK_KEY`」，
**而对云端 NPC 来说这三个变量在同一台机器上根本不存在**，于是「照文档做」的结果是
要么回落成自己容器里的 `localhost:3500`（那里没有任何服务），要么直接不带密钥打过去吃 `401`。

> 🔴 **关键认知**：本套件**不是**那个中台。中台是独立部署的云端服务，由部署方提供。
> 你**不需要、也不应该**在渲染型容器里「本地起一个中台再推」。推，就推**已经在跑的远端中台**。

### 8.1 先确认自己是哪一类

```bash
echo "NPC=${CNB_NPC_NAME:-（无）} EVENT=${CNB_EVENT:-（无）}"   # 有值 = 你跑在渲染型容器里
env | grep -c '^WARROOM_'                                     # 0 = 没人替你注入连接参数
```

两条都命中（有 `CNB_*`、没有 `WARROOM_*`）→ 走下面 §8.2，**别去手拼 `localhost:3500`**。

### 8.2 渲染型：四个坑，按顺序踩过去

**坑 1 · 你连不上任何人的中台。**
同一容器里**没有**你的中台服务：云构建的默认镜像里没有「一条命令起本地中台」的脚本，
`127.0.0.1:3500`、`localhost:3500`、「先本地起一个再推」在渲染型里**全部不成立**。
要推，只能推**已经在跑的远端中台**（就是你平时看大屏的那个地址）。

**坑 2 · 基址不在环境变量里，在被注入的配置 / 密钥管理里。**
渲染型能拿到的只有**平台注入的非密钥字段**与**你自己在部署配置里写的非密钥字段**。
本套件**不提供**任何写死的中台地址（那是部署方的事）。所以渲染型拿基址只能靠：
- 平台 / 流水线注入的 `WARROOM_API_BASE`；或
- 你**显式**在部署配置里写好的中台域名。

三件必须知道的事：
1. **中台地址未配置时，渲染型推不了** —— 此时唯一诚实的做法是**不发**，并把这件事说出来（见坑 4）。
2. **回环地址必须判出来**：`http://localhost:3500` 看着正常，但发给别的系统后**对方会去连它自己**。
   判据（本项目其它出口一致）：

```bash
case "$BASE" in
  ''|*localhost*|*127.0.0.1*|*0.0.0.0*) echo "回环 / 未配置 → 渲染型推不了，别推"; ;;
  *) echo "可用基址前缀：$BASE/api/v2/webhook/<租户id>/<工位标识>" ;;
esac
```

**坑 3 · 密钥在渲染型里一定是缺的，而「带着可推导的密钥去推」是个陷阱。**
真密钥由部署方保管、经平台 secret 注入，仓库里一个字都不写。于是只剩两条路，只有一条是对的：

| 做法 | 结果 |
|---|---|
| 回落演示推导值 `whsec_demo_<channelId>` | ❌ 生产环境会被直接拒（推导式密钥禁用于生产），非生产环境会静默收下 → 得出「推成功了」的假结论 |
| 把真密钥写进容器能读到的任何地方（仓库文件 / 构建配置 / 评论 / 日志） | ❌ 等于**公开泄露**：文档、评论、构建日志都是全仓可读 |
| **把密钥交给平台密钥管理，由容器在运行时注入** | ✅ 唯一正解：`WARROOM_WEBHOOK_KEY` 由流水线 secret 注入，仓库里一个字都不写 |

**坑 4 · 本套件的脚本会「探活失败就静默跳过」，别把它当成功。**
`warroom-webhook.cjs` 只会在**推完之后**才报错；若基址是 localhost 且没起服务，会拿到连接失败。
渲染型的现场形态是「退出码 0、流水线绿、大屏一条都没有」—— **本套件定义过的「静默降级」形态**。
所以渲染型推完必须**校验 `created`**（或 CLI 文案前缀），不能只看退出码：

```bash
# 唯一可信的成功判据：响应体里的 created，或 CLI 的「已推送」前缀
node mcp/warroom-webhook.cjs --notify --title "…" --summary "…" --external-id "…" 2>&1 | grep -q '✅ 已推送' \
  || echo "⚠️ 没推上去（去重命中 / 探活跳过 / 401），别当成功"
```

### 8.3 渲染型的最小正确做法（照抄这一份）

```bash
# 0) 身份：多 AI 共用一块大屏时，不带 source 就分不清谁推的
export WARROOM_AI_NAME="CodeBuddy"          # 或 --source CodeBuddy

# 1) 基址：由平台 / 部署配置注入，读不到就**不发**（不要手拼 localhost）
BASE="${WARROOM_API_BASE:-}"
if [ -z "$BASE" ] || printf '%s' "$BASE" | grep -qE 'localhost|127\.0\.0\.1|0\.0\.0\.0'; then
  echo "渲染型环境拿不到可用基址 —— 本轮不推送（中台地址应由平台 / 部署配置提供）。"
  exit 0
fi
export WARROOM_API_BASE="$BASE"

# 2) 密钥 + 工位：由平台 secret 注入；缺了就别猜、别回落演示值
if [ -z "${WARROOM_WEBHOOK_KEY:-}" ]; then
  echo "缺 WARROOM_WEBHOOK_KEY —— 渲染型不回落演示密钥（生产会 401 / 非生产会给出假成功）。"
  echo "请在流水线里用平台密钥管理注入这一项。"
  exit 0
fi

# 3) 幂等键：**必须每轮都不同**
#    ⚠ 缺省键是 `commit-<hash>`，在两次提交之间是常量。渲染型常见形态是「一次会话里
#      连着推好几条」—— 缺省键会让第 2 条起全部命中去重，而**去重命中不更新正文**，
#      现场就是「推了但大屏只有第一条」。给一个带事件语义的键：
#      AI 每轮：hook:stop:<会话id>:<本轮答复指纹>   · 待办/阻塞：hook:notify:<sid>:<type>:<指纹>
export EXT_ID="${EXT_ID:-render:${WARROOM_AI_NAME}:${CNB_EVENT:-manual}:$(date -u +%Y%m%dT%H%M)}"

# 4) 推送（用 CLI 拿「已推送 / 已存在」的明确文案，比手写 curl 好判成败）
node mcp/warroom-webhook.cjs --notify \
  --title "🔧 本轮变更已就绪" \
  --summary "改了什么的一句话结论（细节放链接，别塞日志）" \
  --level info \
  --source "$WARROOM_AI_NAME" \
  --external-id "$EXT_ID"
```

### 8.4 想真正让渲染型「每次变更都能推」：一步到位的做法

上面那套是「在没有配置的世界里尽量不说谎」。要让它**每次都推得成**，得有人把两样东西送进容器：
**中台地址**与**工位密钥**。本套件已有的机制里，只有两者都由平台注入才成立：

| 手段 | 送地址 | 送密钥 | 渲染型能用吗 |
|---|---|---|---|
| `mcp.json`（MCP stdio） | ✅ | ✅ | ❌ 渲染型起不了子进程、也没有 `mcp.json` |
| 仓库文件 | ✅（非密钥字段可入库） | ❌ **绝不能** | 地址可以，密钥不行 |
| **平台密钥管理 / 流水线 secret** | ✅ | ✅ | ✅ **正解**：`WARROOM_API_BASE` + `WARROOM_WEBHOOK_KEY` 各注入一份 |
| 宿主 hook（`UserPromptSubmit` / 提交后） | ✅ | ✅ | ❌ 那是宿主型的机制，渲染型没有宿主 |

所以回答「渲染环境能不能每次变更都推」这件事，口径只有一句：
**能，前提是中台地址与工位密钥有一个可注入的来源**。在那之前，渲染型至少要做到
「**不推错**」—— 不把消息发进一个不存在的 `localhost`，也不拿公开可推导的密钥去换一个假成功。

### 8.5 手动验证链路

- **想手动验证链路**，用一个能触发推送的入口（如你平台的中台「推送一条」按钮，或装好 MCP 后调一次 `push_warroom_event`），看大屏是否出现、是否 `created:true`。
- **自己手推就用不同的 `externalId`**：同键重推会命中去重（逐字相同 → 不新增；内容有差异 → **原地改写**那条），别把「没新增」当成「推失败了」。

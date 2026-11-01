---
name: kst-im-cli
display_name: 快商通AI营销客服
description: 快商通 IM CLI — 渠道账号/网页站点列表、基础看板、历史会话查询、广告数据查询（资金/投放明细/素材/账户结构）、鉴权与配置；触发词：渠道账号、站点、看板、对话量、历史会话、recId、广告、消耗、余额、投放、创意、素材
description_zh: 快商通 IM CLI — 渠道账号/网页站点列表、基础看板、历史会话查询、广告数据查询、鉴权与配置
description_en: KST IM CLI — list channel accounts and web sites, query dashboards, chat history and ad data.
version: 0.0.16
author: 快商通
---

# kst-im-cli

## 版本要求

使用 `kst-im-cli` 前必须确认版本不低于 `0.0.16`；低于该版本时，先升级 CLI 后再执行任何业务命令。

## Quick Reference

| 命令                                                                        | 说明                         |
| --------------------------------------------------------------------------- | ---------------------------- |
| `auth login`                                                         | 登录：交互输入 API Key（需 TTY，agent 勿用） |
| `auth login -k <key>`                                                | 登录：直接使用 API Key（agent 推荐） |
| `auth login --web [--env <env>]`                                     | 登录：浏览器授权（输出授权链接并自动打开；WorkBuddy 连接器模式） |
| `auth logout`                                                        | 退出                               |
| `auth status`                                                        | 查看登录状态（含浏览器授权轮询）   |
| `config get <key>`                                                  | 读取配置项                         |
| `config set <key> <value>`                                          | 写入配置项                         |
| `channel type list`                                                 | 列出所有渠道类型                   |
| `channel type get --key <渠道标识>`                                 | 查询单个渠道类型                   |
| `channel account list [--channelKey <keys>] [--keyword <text>]`     | 列出渠道账号                       |
| `channel account get --accountId <id>`                              | 查询单个账号                       |
| `site list [--with-codes]`                                          | 列出网页站点                       |
| `site get --siteId <id> [--with-codes]`                             | 查询单个站点                       |
| `stats init`                                                        | 刷新中文字段映射缓存               |
| `stats basic-board channel (--period \| --start/--end) [--accounts <ids>]` | 查询渠道基础看板（默认子命令） |
| `stats basic-board web (--period \| --start/--end) [--sites <ids>]`        | 查询网页站点看板               |
| `history schema`                                                    | 输出历史记录字段说明               |
| `history web --start <time> --end <time> [--site-ids <ids>]`        | 查询网页站点历史会话               |
| `history channel --start <time> --end <time> [--account-ids <ids>]` | 查询渠道账号历史会话               |
| `history context --rec-id <id> --source web\|channel`               | 查询对话上下文（优先临时表，无数据查历史表） |
| `ad fund --channel <t> (--accountIds \| --all) (--period \| --start/--end)` | 广告资金消耗明细（仅 _kb Key） |
| `ad report [--level campaign\|adgroup\|creative] <公共参数>`        | 广告投放明细（全字段透传，仅 _kb Key） |
| `ad material-stats <公共参数>`                                      | 素材统计指标（仅 _kb Key）         |
| `ad account-info --channel <t> (--accountIds \| --all)`             | 广告账户信息（企业名/行业/预算，仅 _kb Key） |
| `ad balance --channel <t> (--accountIds \| --all)`                  | 广告账户余额（summary 承载，仅 _kb Key） |
| `ad campaigns --channel <t> (--accountIds \| --all)`                | 广告计划清单（仅 _kb Key）         |
| `ad adgroups [--campaignId <id>] --channel <t> ...`                 | 广告单元清单（仅 _kb Key）         |
| `ad creatives [--adgroupId <id>] --channel <t> ...`                 | 广告创意清单（仅 _kb Key）         |
| `ad material [--type video\|image] --channel <t> ...`               | 广告素材清单（仅 _kb Key）         |

所有命令支持 `-f/--format json|table|pretty`，默认 `json`；agent 模式始终用默认值。

---

## Overview

`kst-im-cli` 是快商通AI营销客服 CLI。agent 可直接调用业务命令：CLI 优先使用已注入的环境变量，未注入时使用已有本地登录配置。所有命令默认输出 JSON 信封，stdout/stderr 分工严格。

**环境变量名**：仅支持 `KST_ONLINE_CLI_API_KEY`。agent 只能使用执行环境中已存在的该变量，不得自行赋值、覆盖、复制其他产品线的 Key 或输出 Key。环境变量优先级高于本地 `config.json`；未设置时无需补设，直接调用业务命令即可使用已有本地配置。

agent 查询历史记录前必须先调用 `history schema` 理解字段含义；不要依赖 schema 未声明的旧接口字段。

当用户询问 Agent “下一句怎么聊”并提供 `recId` 与渠道来源时，使用 `history context --rec-id <id> --source web|channel`。如果用户还提供了当前身份描述，将上下文与身份描述一起用于生成 1 至 3 句回复；不要让 CLI 生成话术。

`history context` 优先查询当前临时表：网页来源为 `online.TD_DIALOGRECORD`，渠道来源为 `ks_wechat_td.wx_dialogrecord`；临时表无数据时，网页校验 `ONLINEHD.OC_HDVISITORINFO` 后读取历史消息，渠道读取 `ks_wechat_hd.wx_dialogrecordhis`。仅保留 `recType=1,2,5` 的访客、客服和机器人记录，不支持 SDK。返回空 `records` 表示临时表和历史表都未查到符合条件的记录。

---

## 意图路由（优先遵守）

用户问「有哪些 / 列表 / 几个」时，**一律用 `* list` 枚举**，不要用 `stats basic-board` 代替。

| 用户问法 | 正确命令 | 禁止替代 |
| -------- | -------- | -------- |
| 有哪些渠道账号 / 渠道账号列表 | `channel account list` | ✗ `stats basic-board channel` |
| 有哪些站点 / 网页站点列表 / 几个站点 | `site list` | ✗ `stats basic-board web` |
| 有哪些渠道类型 | `channel type list` | — |
| 站点今天/本周数据、对话数、开口率等指标 | `stats basic-board web` | 需 siteId 时先 `site list` |
| 渠道账号今天/本周数据、对话数等指标 | `stats basic-board channel` | 需 accountId 时先 `channel account list` |
| 广告花了多少钱 / 消耗 / 资金 | `ad fund` | 需要账号 ID 或 `--all` |
| 广告余额 / 还剩多少钱 | `ad balance` | ✗ 不要用 `ad fund` 代替 |
| 广告计划 / 单元 / 创意列表 | `ad campaigns` / `ad adgroups` / `ad creatives` | 结构域为现状快照，无时间参数 |
| 广告素材清单 / 素材统计 | `ad material` / `ad material-stats` | 清单=资产列表；统计=指标数据 |

`stats basic-board` 省略 `--accounts` / `--sites` 表示查**全部对象的统计指标**（须指定时间范围），**不是**枚举清单。看板结果虽含账号名/站点名，但缺少完整元数据（如 siteId、code），不能当作 list 使用。

---

## 认证（前置必须）

**方式一：环境变量（Agent 推荐）**

执行宿主已注入非空的 `KST_ONLINE_CLI_API_KEY` 时，直接执行业务命令，无需 `auth login`：

```bash
kst-im-cli channel type list
```

- agent 只使用已存在的 `KST_ONLINE_CLI_API_KEY`，不得自行设置、修改或从其他产品线复制 Key，也不得输出 Key
- 环境变量 trim 后非空即生效，优先级高于本地 `config.json`
- 空值或纯空格视为未设置，回退本地配置
- 401 时提示调用方检查已注入的 `KST_ONLINE_CLI_API_KEY`，不要由 agent 自行替换 Key

**方式二：已有本地配置（无环境变量）**

未设置 `KST_ONLINE_CLI_API_KEY` 时，直接执行业务命令；CLI 会使用已有的本地登录配置。无需为此补设环境变量。

**本地配置初始化（终端用户 / WorkBuddy 连接器场景）**

```bash
# 默认：交互输入 API Key（存量行为，需 TTY；agent 勿用）
kst-im-cli auth login

# 非交互传入：已有 API Key 时直接传入（agent 推荐方式）
kst-im-cli auth login -k <API_KEY>

# 浏览器授权：输出授权链接并自动打开浏览器
kst-im-cli auth login --web [--env <prd|test|pre>]
```

`auth login --web` 非交互：CLI 向授权服务申请配对后，**在 stdout 输出单独一行裸授权 URL**（前后无引号、无其他内容——这是 WorkBuddy 提取规则要求的刻意设计，勿将其包进 JSON），引导文案走 stderr，并自动打开系统默认浏览器。URL 10 分钟内有效。无 TTY 环境（WorkBuddy）输出后立即退出，轮询由 WorkBuddy 跑 `auth status` 完成；人类终端下 CLI 会阻塞等待授权完成并自动登录（Ctrl+C 可退出，之后 `auth status` 可续接）。

**登录引导（按宿主能力选择）**：agent 检测到 `auth status` 失败（exit 1）时——用户能提供 API Key（从快商通后台复制）：执行 `kst-im-cli auth login -k <API_KEY>`（最普适，勿在输出中回显 Key）；WorkBuddy 连接器场景（cli.json 指定）：执行 `kst-im-cli auth login --web` → CLI 自动打开浏览器（cli.json 已设 `authSuppressBrowser`，WorkBuddy 不重复开；无浏览器环境降级为 stdout 单行 https:// 链接）→ 用户在授权页用公司ID/账号/密码登录（登录即授权）→ 周期执行 `kst-im-cli auth status` 直到输出 `ok: true`。WorkBuddy 场景不要传 `--env` 参数（默认连生产授权服务）。

成功后 stdout：`{ "ok": true, "data": "已验证 compId=<N> customerId=<N>" }`

```bash
kst-im-cli auth status
# 环境变量模式（无需 auth login，不回显 Key）：
# stdout: { "ok": true, "data": { "source": "env" } }
# 本地登录模式：
# stdout: { "ok": true, "data": { "key": "...", "compId": N, "customerId": N } }
```

> `auth status` 的 `ok === true` 即具备可用凭据，可直接调用业务命令；`source === "env"` 表示凭据来自环境变量，不含 Key 与 compId/customerId。
> `config get` 仍要求已执行 `auth login`（仅读本地配置项）；纯环境变量模式下不要使用该命令。

---

## 输出解析规则

### 流分工

| 流     | exit 0                           | exit 1                |
| ------ | -------------------------------- | --------------------- |
| stdout | JSON 信封（成功数据）            | **空**                |
| stderr | 日志（`[info/warn/error]` 前缀） | 日志 + 失败 JSON 信封 |

失败时：stdout 为空，stderr 输出失败 JSON 信封（`CliError` 类型）；未捕获的非 CliError 异常输出纯文本，无 JSON 信封。

stderr 可能混入 npm 更新提示（非 JSON 行）。解析时按行过滤，只处理能 `JSON.parse` 的行。设置 `CI=true` 可完全抑制更新提示。

### 成功 — stdout，exit 0

```json
{ "ok": true, "data": <payload>, "meta": { "count": N } }
```

`meta.count` 仅当 data 为数组时存在。`site list --with-codes` 额外有 `meta.codeCount`。

### 失败 — stderr，exit 1

```json
{ "ok": false, "data": { "type": "...", "content": "..." } }
```

---

## 命令参考

### channel

```bash
# 列出所有渠道类型
kst-im-cli channel type list
# 提取: .data[].key（渠道标识）、.data[].name（渠道名称）

# 查询单个渠道类型（--key 是渠道标识，不是 API Key）
kst-im-cli channel type get --key <渠道标识>

# 列出渠道账号
kst-im-cli channel account list [--channelKey <keys>] [--keyword <text>]
# --channelKey: 逗号分隔，来源 channel type list 的 .data[].key
# 提取: .data[].accountId（账号 ID）、.data[].name（账号名称）

# 查询单个账号
kst-im-cli channel account get --accountId <id>
```

### site

```bash
# 列出网页站点
kst-im-cli site list [--with-codes]
# 提取: .data[].siteId、.data[].siteName
# --with-codes 时还有 .data[].codes[]（含 codeId、codeName）

# 查询单个站点（--siteId 来源 site list）
kst-im-cli site get --siteId <id> [--with-codes]
# --with-codes 时 meta.count 为 code 数量
```

### ad（仅 kuaibuddy 的 _kb Key 可用）

**可见性**：ad 命令族仅在使用 `_kb` 后缀 Key 登录（env 或本地配置）时注册——非 `_kb` Key 或未登录时 `--help` 不显示、执行报 `unknown command 'ad'`；服务端 `/cli/ad/**` 另有 403 门控双保险。

```bash
# 查询域（需要时间参数：--period 或 --start/--end 二选一）
kst-im-cli ad fund --channel tencent --all --period lastWeek
kst-im-cli ad report --channel douyin --accountIds 36001 --level creative --period thisMonth
kst-im-cli ad material-stats --channel kuaishou --all --start 2026-09-01 --end 2026-09-15

# 结构域（现状快照，无时间参数）
kst-im-cli ad account-info --channel tencent --all
kst-im-cli ad balance --channel kuaishou --all
kst-im-cli ad campaigns --channel douyin --all
kst-im-cli ad adgroups --channel tencent --all --campaignId 30001     # 可选：按计划过滤
kst-im-cli ad creatives --channel kuaishou --all --adgroupId 51001    # 可选：按单元过滤
kst-im-cli ad material --channel tencent --all --type video           # video|image，默认 video
```

- channel：`tencent`（腾讯广告）/ `kuaishou`（快手磁力）/ `douyin`（抖音巨量）；巨量三体系（marketing/local/ebp）自动探测，响应账号带 `accountSystem`。
- 时间：`--period yesterday|thisWeek|lastWeek|thisMonth|lastMonth`（服务端按周一为周起点换算）或 `--start/--end`（yyyy-MM-dd），二选一；仅查询域三命令需要。
- 账号：`--accountIds a,b` 或 `--all`（渠道全部授权账号），二选一；分页 `--page/--pageSize`（默认 1/100，上限 500）。巨量的账号参数只接受**来源账号**（授权配置的账号 ID）——服务端自动展开为其名下全部真实投放账号，响应 `accounts[].accountId` 是展开后的业务账号、`summary.sourceAccountIds` 标注所属来源。
- **分析时必须读 `data.field_dictionary`**（snake_case 键）：每个英文 key 的中文名/单位/口径/枚举都在其中；金额单位**不换算**——腾讯=分；磁力=元；巨量报表=元、**巨量余额=分**（同一渠道两种单位并存，以字典为准）。
- `accounts[]` 逐账号隔离：`status=ok`（含 0 行零数据）/ `error`（message 带平台原始错误码，如「腾讯平台错误码 11002」）/ `unsupported`（能力缺失，如磁力图片素材）/ `asyncPending`（**渐进查询未完成**：磁力 >7 天报表、巨量大账号集合都会出现；**以完全相同参数稍后重试同一命令**——已完成账号直接返回，未完成的继续查，直至全部就绪）。巨量创意清单（creatives）为**单元素材组成**：每行一个单元，素材嵌套在行内、无独立 creative_id；巨量创意报表（report --level creative）为素材每日效果口径（平台拒绝素材维度时服务端自动降级账户日汇总并在 message 注明）。
- 顶层 `progress{completed,total,done}`：`done=false` 表示仍有账号处于 asyncPending，同参重试可继续取回；`done=true` 为本轮全量就绪。
- `pageInfo.total`=全量总数，`hasMore`=是否还有下一页（翻页用 `--page`）。
- 403 = Key 非 `_kb`；401 = Key 无效或过期（`_kb` 临时 Key TTL 120 分钟，重取后重试）。

### config

```bash
kst-im-cli config get <key>          # 读取配置项，输出 { key, value }
kst-im-cli config set <key> <value>  # 写入配置项，输出 { key, value }
```

### stats init

```bash
kst-im-cli stats init
```

将服务端的 dimension/indicator 中文映射缓存到 `~/.config/.kst-im-cli/stats.json`。channel 与 web 看板共用此缓存。`stats.json` 已存在时不会自动刷新；若服务端更新了指标配置，需手动执行。

### stats basic-board

`basic-board` 拆为 **channel**（渠道账号维度，默认）和 **web**（网页站点维度）两个子命令。

**向后兼容：** `stats basic-board --period today` 等价于 `stats basic-board channel --period today`。

#### channel — 渠道基础看板

```bash
kst-im-cli stats basic-board channel \
  (--period <period> | --start "yyyy-MM-dd HH:mm:ss" --end "yyyy-MM-dd HH:mm:ss") \
  [--accounts <ids>]
```

#### web — 网页站点看板

```bash
kst-im-cli stats basic-board web \
  (--period <period> | --start "yyyy-MM-dd HH:mm:ss" --end "yyyy-MM-dd HH:mm:ss") \
  [--sites <ids>]
```

`--period` 时间范围（均为 00:00:00 ~ 23:59:59）：

| 值          | 范围            |
| ----------- | --------------- |
| `today`     | 今天            |
| `yesterday` | 昨天            |
| `week`      | 本周一 ~ 今天   |
| `last-week` | 上周一 ~ 上周日 |

`--period` 与 `--start`/`--end` 互斥；`--start` 和 `--end` 必须同时指定。

`--accounts`：逗号分隔，来源 `channel account list` 的 `.data[].accountId`；省略则查全部账号的**指标**（仅 channel，不是账号清单）。

`--sites`：逗号分隔，来源 `site list` 的 `.data[].siteId`；省略则查全部站点的**指标**（仅 web，不是站点清单）。

**输出**：

```
.data[]       ← resultlist 明细行（字段名为中文）
.meta.count   ← 行数
```

**stats.json 依赖行为**：

- **缺失**：自动调用 `stats init`（发网络请求）；init 失败则整个命令 exit 1
- **存在但解析失败**：字段名退化为原始英文 key，stderr 输出 `[error]` + `[warn]`，命令仍成功（exit 0）

### history schema

```bash
kst-im-cli history schema
```

返回历史记录字段说明，用于解释 `history web` 和 `history channel` 的 `.data[]`。查询历史记录前先调用一次。

必须读取：

- `.data.timeFormat`：时间格式，当前为 `yyyy-MM-dd HH:mm:ss`
- `.data.fields[]`：字段路径、中英文名称、类型、可空性和解释
- `.data.enums[]`：枚举或常见取值解释
- `.data.notes[]`：脱敏、稳定字段边界等注意事项

解释规则：

- 只把 `.data.fields[].path` 中声明的字段当作稳定对外字段。
- `dialogRecordList` 是当前会话内的聊天消息列表，不是会话列表。
- `visitorInfo` 是访客维度信息。
- `dialogInfo` 是会话维度信息。
- `cardInfo.cardCusType` 是名片标签名称；映射缺失时可能是原始值。
- 聊天内容、联系方式、来源 IP 等可能已脱敏，不要声称拿到了完整原文。

### history web

```bash
kst-im-cli history web \
  --start "yyyy-MM-dd HH:mm:ss" \
  --end   "yyyy-MM-dd HH:mm:ss" \
  [--site-ids <ids>] \
  [--page <page>] \
  [--page-size <size>]
```

按时间范围查询网页站点历史会话。`--site-ids` 为逗号分隔的站点 ID，来源 `site list` 的 `.data[].siteId`；省略时由服务端权限和默认查询逻辑决定范围。

输出：

```
.data[]       ← 会话列表
.meta.count   ← 当前页返回条数
```

每个会话对象可能包含：`contacted`、`visitorInfo`、`dialogInfo`、`dialogRecordList`、`adInfo`、`trackRecordList`、`cardInfo`。

### history channel

```bash
kst-im-cli history channel \
  --start "yyyy-MM-dd HH:mm:ss" \
  --end   "yyyy-MM-dd HH:mm:ss" \
  [--account-ids <ids>] \
  [--page <page>] \
  [--page-size <size>]
```

按时间范围查询渠道账号历史会话。`--account-ids` 为逗号分隔的渠道账号 ID，来源通常是 `channel account list` 的 `.data[].accountId`。

渠道查询与网页查询共用历史记录结果结构。渠道专有信息优先看：

- `visitorInfo.visitorNick`
- `visitorInfo.sourceCity`
- `visitorInfo.trafficType`
- `visitorInfo.accountInfo`
- `dialogInfo.dialogTag`

### history context

```bash
kst-im-cli history context \
  --rec-id <recId> \
  --source web|channel
```

`--rec-id` 必须是正整数；`--source` 必须为 `web` 或 `channel`。输出中的 `.data.records[]` 包含 `content`、`sender`、`recType` 和 `addTime` 等上下文字段，记录按时间正序排列。

### history 查询约束

- `--start` 和 `--end` 必须同时指定。
- 时间格式必须是 `yyyy-MM-dd HH:mm:ss`。
- `--page` 和 `--page-size` 必须大于 0；默认分别为 `1` 和 `500`。
- `--page-size` 不能大于 `500`；大范围查询应分页执行，不要一次请求过大页数。
- 返回空数组表示当前条件下未查到会话，不等于 CLI 调用失败。
- 若需要解释字段，重新调用 `history schema`，不要猜测字段含义。

---

## 数据依赖关系

```
channel type list → channel account list --channelKey
channel account list → stats basic-board channel --accounts
site list → stats basic-board web --sites
site list → history web --site-ids
stats init → channel / web 看板（中文字段映射，共用 stats.json）
ad 命令无前置依赖：不知道账号 ID 时直接 --all（账号清单来自各渠道授权配置）
ad campaigns → ad adgroups --campaignId / ad adgroups → ad creatives --adgroupId（结构域逐层下钻）
```

---

## 错误处理

| type / 症状                | 原因                           | 处理                                      |
| -------------------------- | ------------------------------ | ----------------------------------------- |
| `auth`                     | 未登录或 token 失效            | 环境变量模式：由调用方检查已注入的 `KST_ONLINE_CLI_API_KEY`；本地模式：由终端用户完成 `auth login` 后重试 |
| `auth` + 含 `KST_ONLINE_CLI_API_KEY` | 环境变量 key 无效或过期 | 由调用方更新注入的 Key；agent 不替换 Key，且不回退本地配置 |
| `auth` + 含 `授权等待中`   | 浏览器授权未完成（非终态）     | 提示用户完成浏览器授权后重试 `auth status`；10 分钟内有效 |
| `auth` + 含 `尚未开通 API Key` | 账号未开通 API Key          | 提示用户先在快商通后台开通，再重新 `auth login` |
| `auth` + 含 `重新执行 auth login` | 授权链接过期或失效        | 重新执行 `auth login` 获取新链接 |
| `auth` + 含 `优先级高于浏览器授权结果` | 环境变量 key 在场，浏览器授权不会生效 | agent 场景直接使用现有 env 凭据即可，无需授权 |
| `validation`               | 参数错误                       | 修正参数后重试                            |
| `network`                  | 网络不通                       | 检查网络连通性                            |
| `api`                      | 服务端业务错误                 | 读 `.data.content` 查看服务端响应         |
| `basic-board` exit 1       | `stats.json` 缺失且 init 失败  | 先手动执行 `stats init`                   |
| channel 看板 api 错误      | 未配置渠道基础看板             | 确认 OnlineRecord 看板配置                |
| web 看板 api 错误          | 未配置网页基础看板             | 确认 OnlineRecord 网页看板配置            |
| `站点不存在: {siteId}`     | siteId 无效                    | 重新执行 `site list` 获取有效 ID          |
| `--key` 参数错误           | 传的是 API Key 而非渠道标识    | 传渠道标识（如 `weixin`）                 |
| stderr 有非 JSON 行        | npm 更新提示                   | 设置 `CI=true` 抑制，或按行过滤           |
| `basic-board` 字段名为英文 | `stats.json` 损坏              | 执行 `stats init` 刷新                    |
| `history` 字段含义不清     | 未读取 schema                  | 先执行 `history schema`                   |
| `history` 参数校验失败     | 时间格式、分页或必填项错误     | 按 `yyyy-MM-dd HH:mm:ss` 和正整数分页重试 |
| `history` 返回空列表       | 条件下无数据或权限范围内无数据 | 缩小/调整时间、站点或账号条件后重试       |
| `ad` 报 `unknown command 'ad'` | 当前 Key 非 `_kb` 后缀（ad 命令族未注册） | 换用 `_kb` Key（env 或 `auth login -k`）后重试 |
| `ad` 账号 `status=asyncPending` | 渐进查询未完成（磁力 >7 天异步任务 / 巨量大账号集合单轮预算用尽） | **完全相同参数**稍后重试同一命令：已完成账号直接返回，未完成的继续查（结合顶层 `progress.done` 判断是否取全） |
| `ad` 账号 `status=unsupported` | 渠道无此能力（如磁力图片素材） | 属正常降级，向用户说明即可 |
| `ad` 账号 `status=error` 且 message 含「平台错误码」 | 平台侧拒绝（token 失效/参数问题），message 已透传平台原始 code | 按 code 判断：token 失效提示重新授权，其余带 message 反馈 |
| `ad` 403 | 广告接口要求 `_kb` Key | 确认当前 Key 后缀 |

---

## 禁止使用

| 命令                    | 原因                                |
| ----------------------- | ----------------------------------- |
| `auth login`（无 `-k`/`--web`） | 交互式输入 key，无 TTY 会挂起 |
| `skill install`         | 交互式，会挂起                      |
| `completion`            | 生成 shell 补全脚本，agent 无需使用 |

---

## 典型工作流

### 查询指定渠道的基础看板数据

```bash
# 1. 拿渠道 key
kst-im-cli channel type list
# → .data[].key 如 "weixin", "xiaohongshu"

# 2. 拿 accountId
kst-im-cli channel account list --channelKey weixin,xiaohongshu
# → .data[].accountId 如 101, 102, 203

# 3. 查看板（channel 为默认子命令，可省略子命令名）
kst-im-cli stats basic-board channel --period today --accounts 101,102,203
# → .data[] 明细行（字段名为中文）
# → .meta.count 行数
```

### 查询指定站点的网页看板数据

```bash
# 1. 拿 siteId
kst-im-cli site list
# → .data[].siteId 如 "118501", "118503"

# 2. 查网页看板
kst-im-cli stats basic-board web --period today --sites 118501,118503
# → .data[] 明细行（字段名为中文）
# → .meta.count 行数
```

### 对比昨今数据（渠道）

```bash
kst-im-cli stats basic-board channel --period yesterday --accounts 101,102,203
kst-im-cli stats basic-board channel --period today     --accounts 101,102,203
# 对比两次 .data[] 中相同维度行的指标差值
```

### 对比昨今数据（网页站点）

```bash
kst-im-cli stats basic-board web --period yesterday --sites 118501,118503
kst-im-cli stats basic-board web --period today     --sites 118501,118503
# 对比两次 .data[] 中相同维度行的指标差值
```

### 自定义时间范围

```bash
kst-im-cli stats basic-board channel \
  --start "2026-05-01 00:00:00" \
  --end   "2026-05-27 23:59:59" \
  --accounts 101,102

kst-im-cli stats basic-board web \
  --start "2026-05-01 00:00:00" \
  --end   "2026-05-27 23:59:59" \
  --sites 118501,118503
```

### 查询网页历史会话

```bash
# 1. 拿 siteId（过滤用）
kst-im-cli site list
# → .data[].siteId 如 "118501", "118504"

# 2. 先拿字段说明
kst-im-cli history schema

# 3. 查询历史会话
kst-im-cli history web \
  --start "2026-06-01 00:00:00" \
  --end   "2026-06-03 23:59:59" \
  --site-ids 118501,118504 \
  --page 1 \
  --page-size 500

# 4. 解释结果
# .data[] 是会话列表
# .data[].dialogRecordList 是当前会话内的聊天消息列表
```

### 查询渠道历史会话

```bash
# 1. 获取渠道账号 ID
kst-im-cli channel account list --channelKey weixin

# 2. 获取历史字段说明
kst-im-cli history schema

# 3. 查询渠道历史会话
kst-im-cli history channel \
  --start "2026-06-01 00:00:00" \
  --end   "2026-06-03 23:59:59" \
  --account-ids 101,102 \
  --page 1 \
  --page-size 500
```

### 查询广告数据（需 _kb Key）

```bash
# 1. 账户结构快照：余额 / 账户信息（无时间参数）
kst-im-cli ad balance --channel kuaishou --all
# → .data.accounts[].summary.balance（单位看 field_dictionary，磁力=元）

# 2. 昨日消耗与投放明细（查询域需时间参数）
kst-im-cli ad fund --channel kuaishou --all --period yesterday
kst-im-cli ad report --channel kuaishou --all --level adgroup --period yesterday

# 3. 跨渠道 30 天素材统计（磁力 >7 天或巨量大账号集合首答 asyncPending，同参重试取全量）
kst-im-cli ad material-stats --channel kuaishou --all --start 2026-09-02 --end 2026-10-01
# → 若 progress.done=false：等待 1~5 分钟后原样重跑上一条命令，直至 done=true

# 4. 解读任何 ad 结果前先读字典
# .data.field_dictionary.<key> = { cn 中文名, unit 单位, note 口径, enum 枚举 }
```

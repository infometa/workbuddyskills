---
name: openclaw-assets-to-workbuddy
description: 将 OpenClaw 用户的个人资产迁移到 WorkBuddy 对应位置，重点覆盖 SOUL.md、IDENTITY.md、USER.md、memory、skills、MCP 配置、bot/channel 连接配置，以及 OpenClaw 的 cron job 定义。适用于把 ~/.openclaw 或 OpenClaw workspace 迁入 ~/.workbuddy、WorkBuddy IDE 配置和目标 WorkBuddy 工作区的场景。
version: 1.0.1
---

# OpenClaw 资产迁移到 WorkBuddy

当用户希望把个人 OpenClaw 资产迁移到 WorkBuddy 时，使用这个 skill。

默认假设：
- OpenClaw home：`~/.openclaw`
- OpenClaw workspace：`~/.openclaw/workspace`
- WorkBuddy home：`~/.workbuddy`
- WorkBuddy 项目工作区：用户指定的目标 repo 或 workspace

如果用户明确给了路径，优先使用用户提供的路径。

## 目标

只迁移那些在 WorkBuddy 中有明确落点的“用户资产”。

优先迁移：
- 身份文件
- memory
- skills
- MCP 配置
- bot/channel 连接配置
- cron job 定义

不要盲目复制运行态缓存、凭据目录、插件二进制目录等不透明状态。

默认迁移策略：
- 以“融合”为默认策略，不以“覆盖”为默认策略
- 尤其是 `SOUL.md`、`IDENTITY.md`、`USER.md`，必须优先保留 WorkBuddy 现有人设、语气、边界、偏好，再吸收 OpenClaw 中缺失但有价值的信息
- 只有在用户明确要求“以 OpenClaw 为准”时，才允许接近覆盖式迁移
- OpenClaw `credentials/*` 如果要迁移到 WorkBuddy，默认走“结构化转换”，不是整目录复制

## 已确认的 WorkBuddy 目标位置

使用以下落点：

- 用户级身份文件：
  - `~/.workbuddy/SOUL.md`
  - `~/.workbuddy/IDENTITY.md`
  - `~/.workbuddy/USER.md`
- 用户级 MCP 配置：
  - `~/.workbuddy/mcp.json`
- 用户级 skills：
  - `~/.workbuddy/skills/<skill>/SKILL.md`
- 项目级 skills：
  - `{workspace}/.workbuddy/skills/<skill>/SKILL.md`
- 项目级 memory：
  - `{workspace}/.workbuddy/memory/MEMORY.md`
  - `{workspace}/.workbuddy/memory/YYYY-MM-DD.md`
- automations：
  - `~/.workbuddy/automations/<automation_id>/automation.toml`
- IDE 用户配置文件：
  - `<userDataPath>/User/settings.json`
  - macOS 默认通常是 `~/Library/Application Support/CodeBuddy/User/settings.json`
- IDE bot/channel 配置主键：
  - `claw.channels`
- IDE bot/channel 旧版兼容键：
  - `wecom.channels`
- IDE 特殊 channel 开关：
  - `wecom.wechatMpEnabled`
  - `wecom.wechatmp.artifactUploadEnabled`
- IDE 产品登录配置定义：
  - `genie/apps/extension/vscode/product.json`
- IDE 产品登录 session：
  - VS Code `SecretStorage`
  - 当前默认 key 源自 `product.json` 里的 `authentication.attributes.storageKey`
  - 这套是 WorkBuddy 产品账号登录态，不是 bot/channel 绑定配置
- channel 运行时缓存（不是长期配置落点）：
  - QQ 会话缓存：系统临时目录里的 `qq-bot-session-<account>.json`
  - 微信 ClawBot 同步缓存：系统临时目录里的 `weixin-sync-<account>.json`
  - 微信 ClawBot context 缓存：系统临时目录里的 `weixin-context-<account>.json`

相关但非主要目标：
- WorkBuddy 的 home 根目录实质上是 `~/.workbuddy`
- 用户模型配置可能在 `~/.workbuddy/models.json`
- WorkBuddy 可能会自己维护 `~/.workbuddy/workspace-state.json`，除非用户明确要求，否则不要覆盖

## 源到目标的映射

### 1. 身份文件

迁移：
- `~/.openclaw/workspace/SOUL.md` -> `~/.workbuddy/SOUL.md`
- `~/.openclaw/workspace/IDENTITY.md` -> `~/.workbuddy/IDENTITY.md`
- `~/.openclaw/workspace/USER.md` -> `~/.workbuddy/USER.md`

规则：
- 如果目标文件已存在，优先做 merge，不要粗暴覆盖
- 如果 WorkBuddy 侧内容更丰富，保留现有内容，只补充 OpenClaw 中缺失的信息
- `SOUL.md` 的融合优先级最高：先保留 WorkBuddy 已建立的人设、语气、价值观、边界，再补充 OpenClaw 中不冲突的设定
- 如果 OpenClaw 与 WorkBuddy 的人设设定冲突，不要自动覆盖，保留 WorkBuddy 版本，并把冲突点列入迁移报告
- `IDENTITY.md` 和 `USER.md` 也应采用“补充缺失信息、合并稳定事实、避免重复”的方式处理
- 不要复制 `BOOTSTRAP.md`
- 不要复制 OpenClaw workspace state 文件

### 2. Memory

迁移：
- `~/.openclaw/workspace/MEMORY.md` 或 `memory.md` -> `{workspace}/.workbuddy/memory/MEMORY.md`
- `~/.openclaw/workspace/memory/*.md` -> `{workspace}/.workbuddy/memory/`

规则：
- 日期型 memory 文件如果已经是 `YYYY-MM-DD.md`，原样保留文件名
- 如果 OpenClaw 的 `MEMORY.md` 很大，合并到 WorkBuddy `MEMORY.md`，不要整文件直接覆盖
- 两边内容重复时要去重

### 3. Skills

迁移：
- `~/.openclaw/skills/<skill>/` -> `~/.workbuddy/skills/<skill>/`
- `~/.openclaw/workspace/skills/<skill>/` -> `{workspace}/.workbuddy/skills/<skill>/`

规则：
- 如果 skill 目录里除了 `SKILL.md` 还有 `scripts/`、`references/`、`assets/`，复制整个 skill 目录
- 如果目标 skill 已存在，先 diff，再决定 merge、保留，或改名导入

### 4. MCP

主要来源：
- `~/.openclaw/openclaw.json` 中的 `mcp.servers`

可选来源：
- `~/.openclaw/extensions/*/.mcp.json`

目标：
- `~/.workbuddy/mcp.json`，顶层字段使用 `mcpServers`

规则：
- 把 OpenClaw 的 `mcp.servers` 转成 WorkBuddy 的 `mcpServers`
- 写入时合并到已有 `~/.workbuddy/mcp.json`，不要覆盖其他 server
- 如果从 OpenClaw 插件的 `.mcp.json` 中提取，只迁移 MCP server 定义，不迁移整个插件目录
- 如果某些 server 依赖环境变量或密钥，只保留这些 server 真正用到的键

目标格式示例：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "type": "stdio",
      "disabled": false
    }
  }
}
```

### 5. Bot / channel 连接配置

总原则：
- WorkBuddy 的“产品登录态”和“bot/channel 绑定”是两套东西，不要混为一谈
- WorkBuddy 产品登录态主要由 `product.json` 定义认证方式，并由 `SecretStorage` 保存登录 session
- OpenClaw `credentials/*` 如果是为了迁移 bot/channel，应优先迁移到 WorkBuddy IDE 的 `settings.json`，也就是 `claw.channels.*`
- 除非用户明确要求迁移 WorkBuddy 产品账号登录态，否则不要把 OpenClaw `credentials/*` 强行写进 `SecretStorage`
- bot/channel 迁移的长期目标是 `claw.channels.*`；临时缓存文件不要当作最终落点

重要位置：
- 长期配置落点：
  - `<userDataPath>/User/settings.json`
  - macOS 默认通常是 `~/Library/Application Support/CodeBuddy/User/settings.json`
- 新结构：
  - `claw.channels.<channelType>`
- 旧结构（兼容读取，不建议新写入）：
  - `wecom.channels.<channelType>`

OpenClaw `credentials/*` 到 WorkBuddy 的对照原则：

- `~/.openclaw/credentials/oauth.json`
  - 这是 OpenClaw 的渠道/OAuth 旧状态来源之一
  - 不要把它直接当成 WorkBuddy bot/channel 配置导入
  - 如果用户明确要求迁移的是 WorkBuddy 产品登录态，目标应是 WorkBuddy 的 `SecretStorage`，不是 `claw.channels.*`
  - 如果用户要迁移的是 bot/channel，则通常跳过这个文件，改为迁移具体 channel 所需字段

- `~/.openclaw/credentials/<channel>-pairing.json`
  - WorkBuddy 没有同构的 pairing 文件
  - 如果目标 channel 在 WorkBuddy 有对应实现，可把其中“允许谁发消息、绑定哪个通道”的语义，折算到 `claw.channels.<type>` 的策略字段或 channelId
  - 不能 1:1 映射时，标记为 `manual review`

- `~/.openclaw/credentials/<channel>-allowFrom.json`
  - 语义上优先映射到：
  - `claw.channels.<type>.allowFrom`
  - 或 `groupAllowFrom` / `groups` / `dmPolicy` / `groupPolicy`
  - 这属于“规则迁移”，不是文件迁移

- `~/.openclaw/credentials/<channel>-<accountId>-allowFrom.json`
  - 如果能确定目标 WorkBuddy channel 类型和 account/channelId，可合并到对应 `claw.channels.<type>` 的 allowlist / group policy
  - 无法确定归属时，标记为 `manual review`

- `~/.openclaw/credentials/whatsapp/<accountId>/creds.json`
  - 当前已确认的 WorkBuddy channel 类型列表里，没有内建 `whatsapp`
  - 不要自动迁移到 `claw.channels.*`
  - 默认结论：`manual review / unsupported`

- `~/.openclaw/credentials/matrix/credentials.json`
- `~/.openclaw/credentials/matrix/credentials-<account>.json`
  - 当前已确认的 WorkBuddy channel 类型列表里，没有内建 `matrix`
  - 默认结论：`manual review / unsupported`

已确认的 WorkBuddy 内建 channel 类型：
- `feishu`
- `wecom`
- `wecomNew`
- `wecomaibot`
- `qq`
- `yuanbao`
- `weixinBot`
- `weixinClawBot`
- `wecomIOA`
- `dingtalk`
- `slack`
- `custom`
- `wechatkf`
- `wechatmp`

当前没有在这份内建列表里确认到的 OpenClaw 渠道，例如：
- WhatsApp
- Matrix
- Telegram
- Signal
- Discord

对这些渠道，不要假设 WorkBuddy 有直接落点；优先标记为 `manual review`，必要时再考虑转成 `custom`。

推荐迁移目标：

- OpenClaw 飞书 bot / webhook 类配置
  - 目标：`claw.channels.feishu`
  - 关键字段：
  - `channelId`
  - `appId`
  - `appSecret`
  - 可选：`verificationToken`、`encryptKey`、`domain`
  - 可附带策略：`allowFrom`、`groupAllowFrom`、`groups`、`replyPolicy`、`requireMention`

- OpenClaw Slack bot 配置
  - 目标：`claw.channels.slack`
  - 关键字段：
  - `channelId`
  - `botToken`
  - `signingSecret`

- OpenClaw QQ bot 配置
  - 目标：`claw.channels.qq`
  - 关键字段：
  - `channelId`
  - `appId`
  - `appSecret`
  - 可选：`requireMention`

- OpenClaw 元宝 bot 配置
  - 目标：`claw.channels.yuanbao`
  - 关键字段：
  - `channelId`
  - `appKey`
  - `appSecret`

- OpenClaw 钉钉 bot 配置
  - 目标：`claw.channels.dingtalk`
  - 关键字段：
  - `channelId`
  - `appKey`
  - `appSecret`

- OpenClaw 企业微信 webhook 配置
  - 目标：`claw.channels.wecomNew`
  - 关键字段：
  - `channelId`
  - `token`
  - `encodingAESKey`

- OpenClaw 企业微信 AiBot 配置
  - 目标：`claw.channels.wecomaibot`
  - WebSocket 模式关键字段：
  - `botId`
  - `botSecret`
  - Webhook 模式关键字段：
  - `channelId`
  - `token`
  - `encodingAESKey`
  - 可选：`aibotid`
  - 可附带策略：`allowFrom`、`groupAllowFrom`、`groups`、`replyPolicy`、`requireMention`

- OpenClaw 微信 ClawBot 配置
  - 目标：`claw.channels.weixinClawBot`
  - 关键字段：
  - `channelId`
  - `botToken`
  - `baseUrl`
  - `accountId`
  - 可选：`userId`
  - 不要把临时文件 `weixin-sync-*.json`、`weixin-context-*.json` 当成迁移目标

- OpenClaw 微信客服号相关配置
  - 目标：`wechatkf`
  - 注意：`wechatkf` 使用单独绑定机制，不以 `claw.channels.wechatkf` 作为主要长期落点
  - 这类迁移更接近“重新绑定”而不是“复制凭据文件”

- OpenClaw 无直接对应 WorkBuddy channel 的渠道
  - 可选目标：`claw.channels.custom`
  - 关键字段：
  - `channelId`
  - `webhookUrl`
  - 可选：`apiKey`
  - 只有在用户接受“降级到 generic webhook relay”语义时，才这样迁移

迁移规则：
- 不要把整个 `~/.openclaw/credentials/` 目录整包复制到 WorkBuddy
- 要把“渠道凭据”和“策略/allowlist”拆开看
- 有明确 WorkBuddy schema 的，写入 `claw.channels.<type>`
- 只有兼容读取时，才参考 `wecom.channels.*`；新写入一律优先 `claw.channels.*`
- 如果只是把配置文件写入 `settings.json`，WorkBuddy 后续启动时会尝试自动拉起并重新注册这些已保存的 channels
- `wechatkf` 和 `wechatmp` 属于特殊路径，分别走绑定机制和独立开关，不按普通 `claw.channels.*` 套路强行处理

### 6. Cron job 定义

来源：
- `~/.openclaw/cron/jobs.json`

目标：
- `~/.workbuddy/automations/<automation_id>/automation.toml`

这里只迁移“定义”，不要迁移：
- `~/.openclaw/cron/runs/*.jsonl`
- `~/.openclaw/tasks/runs.sqlite`

字段映射：

- OpenClaw `enabled: true` -> WorkBuddy `status = "ACTIVE"`
- OpenClaw `enabled: false` -> WorkBuddy `status = "PAUSED"`
- OpenClaw job id -> WorkBuddy automation id
- OpenClaw job name -> WorkBuddy automation name
- OpenClaw payload 文本 -> WorkBuddy automation prompt
- 目标工作区 -> WorkBuddy `cwds`

调度转换规则：

- `schedule.kind = "at"`
  - 转成 `schedule_type = "once"`
  - 时间转成 `scheduled_at = "<ISO-8601>"`

- `schedule.kind = "every"`
  - 只在“整小时间隔”时自动转成 WorkBuddy
  - 例如：`everyMs = 7200000` -> `rrule = "FREQ=HOURLY;INTERVAL=2"`
  - 如果不是整小时，标记为 `manual review`，不要猜

- `schedule.kind = "cron"`
  - 只自动转换这些安全且常见的模式：
  - `0 */N * * *` -> `FREQ=HOURLY;INTERVAL=N`
  - `M H * * *` -> `FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;BYHOUR=H;BYMINUTE=M`
  - `M H * * 1,3,5` -> `FREQ=WEEKLY;BYDAY=MO,WE,FR;BYHOUR=H;BYMINUTE=M`
  - 如果表达式包含秒、day-of-month、month，或其他不在以上范围内的复杂形态，停止自动转换，标记为 `manual review`

payload 转换：

- `payload.kind = "agentTurn"`
  - 用 `payload.message` 作为 WorkBuddy 的 `prompt`
  - 如果有 `model` 或 `thinking`，尽量保留为可选元信息

- `payload.kind = "systemEvent"`
  - 用 system event 文本作为 WorkBuddy 的 `prompt`
  - 在迁移报告里说明：这和 OpenClaw main-session cron 的执行语义并不完全等价

以下语义没有严格的一一映射：
- `sessionTarget`
- `wakeMode`
- `delivery`
- `deleteAfterRun`
- top-of-hour `staggerMs`

处理方式：
- 在迁移报告里保留这些原始字段
- 如有必要，可以在生成的 automation prompt 或附带说明里加一小段注释
- 不要凭空发明 WorkBuddy 不存在的字段

## Schema / 文件格式骨架

### WorkBuddy automation.toml 最小骨架

迁移后生成的 WorkBuddy automation 文件应至少符合下面这个骨架：

```toml
version = 1
id = "daily-brief"
name = "Daily Brief"
prompt = "生成每日简报并汇总关键事项。"
status = "ACTIVE"
schedule_type = "recurring"
rrule = "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9;BYMINUTE=0"
cwds = ["/path/to/workspace"]
```

可选字段：

```toml
scheduled_at = "2026-04-01T15:30"
valid_from = "2026-04-01"
valid_until = "2026-04-30"
model_id = "gpt-5.4"
model_is_thinking = true
push_to_wechat = false
```

字段含义：
- `version`：当前固定写 `1`
- `id`：automation 的稳定 id
- `name`：automation 名称
- `prompt`：实际执行任务的提示词
- `status`：`ACTIVE` 或 `PAUSED`
- `schedule_type`：`recurring` 或 `once`
- `rrule`：循环任务使用的 RRULE
- `scheduled_at`：一次性任务的执行时间
- `cwds`：执行时使用的工作区目录列表
- `valid_from` / `valid_until`：可选生效区间
- `model_id` / `model_is_thinking`：可选模型参数
- `push_to_wechat`：可选通知参数

规则：
- `schedule_type = "recurring"` 时，必须有 `rrule`
- `schedule_type = "once"` 时，必须有 `scheduled_at`
- `prompt` 不能为空
- `cwds` 必须是数组，即使只有一个工作区

### WorkBuddy channel settings.json 参考骨架

bot/channel 的长期配置不在 `~/.workbuddy`，而在 WorkBuddy IDE 的 `settings.json`。

典型骨架如下：

```json
{
  "claw.channels": {
    "feishu": {
      "enabled": true,
      "channelId": "feishu-prod",
      "appId": "cli_xxx",
      "appSecret": "yyy",
      "verificationToken": "zzz",
      "encryptKey": "aaa",
      "domain": "feishu",
      "registration": {
        "webhookUrl": "https://..."
      }
    },
    "wecomaibot": {
      "enabled": true,
      "connectionMode": "websocket",
      "channelId": "wecom-aibot-main",
      "botId": "bot_xxx",
      "botSecret": "secret_xxx",
      "registration": {
        "webhookUrl": "https://..."
      }
    },
    "weixinClawBot": {
      "enabled": true,
      "channelId": "weixin-main",
      "botToken": "token_xxx",
      "baseUrl": "https://ilinkai.weixin.qq.com",
      "accountId": "wx_xxx",
      "userId": "user_xxx"
    }
  },
  "wecom.wechatMpEnabled": true,
  "wecom.wechatmp.artifactUploadEnabled": false
}
```

规则：
- 新写入优先 `claw.channels`
- `registration.webhookUrl` 是 WorkBuddy 保存的已注册信息，不是所有 channel 都必须有
- `wechatkf` 不要机械写成上面的结构，它使用单独绑定机制
- `wechatmp` 默认看单独开关，不把它当作普通 `claw.channels.<type>` 处理

### OpenClaw cron jobs.json 参考骨架

OpenClaw 源文件通常是一个 `jobs` 数组，单个 job 大致可按下面的形态理解：

```json
{
  "version": 1,
  "jobs": [
    {
      "id": "daily-brief",
      "name": "Daily Brief",
      "enabled": true,
      "schedule": {
        "kind": "cron",
        "expr": "0 9 * * 1,2,3,4,5",
        "tz": "Asia/Shanghai"
      },
      "sessionTarget": "isolated",
      "payload": {
        "kind": "agentTurn",
        "message": "生成每日简报并汇总关键事项。"
      }
    }
  ]
}
```

OpenClaw 可能出现的 `schedule.kind`：
- `at`
- `every`
- `cron`

OpenClaw 可能出现的 `payload.kind`：
- `agentTurn`
- `systemEvent`

迁移时不要要求源文件必须完全长成上面的样子；把它当作“字段理解骨架”即可。

## 通常不要直接复制的内容

除非用户明确要求并且你确认目标格式兼容，否则不要直接复制：

- `~/.openclaw/credentials/`
- `~/.openclaw/extensions/` 整个插件目录
- `~/.openclaw/.env` 整个文件
- `~/.openclaw/openclaw.json` 整个文件
- `.clawhub/lock.json`
- OpenClaw session logs 和运行态状态文件

推荐处理方式：
- 只从 `.env` 中提取 MCP 真正需要的环境变量
- 只从配置文件或插件文件中提取 MCP server 定义
- `credentials/*` 只做“结构化提取 + 映射写入”，不要整目录复制
- 其他无法安全自动迁移的内容，标记为“需要手动迁移”

## 执行前确认（必须）

在读取任何 OpenClaw 数据之前，必须先调用 `ask_followup_question` 获得用户确认。

参数：
- 标题：`OpenClaw 资产复制确认`
- 问题内容：

```
即将从 ~/.openclaw 复制以下内容到 WorkBuddy：

身份设定 / 记忆 / 技能 / MCP 配置 / 渠道凭据 / 定时任务

原始数据不会被删除或修改，所有操作在本地完成。
其中渠道凭据包含 API Key 等敏感信息，复制完成后 WorkBuddy 会自动连接对应平台。
```

- 选项：`确认复制` / `取消`

如果用户选择"取消"，立即终止，不做任何读取操作。

## 工作流程

1. 检查源路径，列出哪些资产实际存在
2. 检查 WorkBuddy 目标路径，确认是否已有同名文件
3. 在动手前先产出一张迁移表
4. 覆盖或重度 merge 前，先备份目标文件或目录
5. 按这个顺序迁移：
   - identity
   - memory
   - skills
   - MCP
   - bot/channel bindings
   - cron definitions
6. 对每个可迁移的 cron job，生成一个 WorkBuddy automation TOML
7. 最后输出迁移报告，说明：
   - 已迁移项
   - 已跳过项
   - 需人工处理项
   - 每条路径的处理结果

在身份文件融合时，优先按下面顺序判断：
1. WorkBuddy 现有内容里哪些是已经生效的人设、语气、长期偏好
2. OpenClaw 内容里哪些是稳定事实、补充设定、可兼容偏好
3. 哪些内容重复
4. 哪些内容冲突

处理原则：
- 重复内容：去重
- 互补内容：合并
- 冲突内容：默认保留 WorkBuddy，记录冲突点，等待用户后续决定

## 报告格式

结束时必须输出简明迁移报告，至少包含：

- OpenClaw 源路径
- WorkBuddy 目标路径
- 动作：copied、merged、skipped、manual review
- 跳过或人工处理的原因

如果存在 cron jobs，单独列一节：
- 转换成功的任务
- 不支持自动转换的表达式
- 执行语义无法完全保留的字段

如果存在 bot/channel 迁移，单独列一节：
- 哪些 OpenClaw channel 被迁移到了 `claw.channels.*`
- 哪些是写入 `settings.json`
- 哪些涉及 `SecretStorage`，哪些没有涉及
- 哪些 channel 在当前 WorkBuddy 版本里没有直接目标，只能 `manual review`

如果身份文件发生融合，还要额外列出：
- 保留了哪些 WorkBuddy 原有设定
- 从 OpenClaw 吸收了哪些补充内容
- 哪些设定存在冲突并被保留为 WorkBuddy 优先

最后给用户的收尾说明必须明确写清楚：
- 本次实际迁移了哪些资产
- 本次没有迁移哪些资产
- 本次修改了哪些文件
- 每个被修改文件的最终位置是什么
- 每个资产是从哪里迁到哪里的

推荐按下面的结构收尾：

1. 已迁移内容
   - 资产类别
   - 源路径
   - 目标路径
   - 动作：copied / merged / created / skipped / manual review

2. 修改的文件
   - 被修改文件路径
   - 修改原因
   - 是否为融合迁移

3. 未迁移或需人工处理
   - 资产名称或路径
   - 原因

4. bot/channel 迁移结果
   - OpenClaw 源文件或源字段
   - WorkBuddy 目标 key
   - 最终写入文件
   - 是否需要用户后续重新绑定或补充密钥

不要只给笼统总结，必须把“改了什么文件、迁到哪里”明确列出来。

## 安全原则

- 除非用户明确要求，否则不要删除 OpenClaw 源数据
- 目标已存在用户编辑时，优先 merge，不要 replace
- 如果目标侧内容更完整或更新，保留目标内容，只补缺失信息
- 对 `SOUL.md`、`IDENTITY.md`、`USER.md`，默认执行“融合迁移”，不是“源覆盖目标”
- 只要不能高置信度做 1:1 映射，就标记为 `manual review`，不要猜
- 对 bot/channel 凭据，只迁移当前 WorkBuddy 明确支持且 schema 已确认的渠道

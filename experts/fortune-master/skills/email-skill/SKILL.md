---
name: email-skill
description: "邮件统一入口（纯路由层），自身不执行任何脚本与接口，识别用户意图后用 read 工具读取下游 skill 的 SKILL.md 路由到下游。【路由决策必读】两步决策：L0 用户是否显式指定邮箱通道？L1 若未指定，是发给自己/结果留存还是发给别人/完整收发？L0 显式：'Agent/AI 邮箱'→读取 agent-email/SKILL.md；'用我的 QQ/163/Gmail/Outlook'→读取 imap-smtp-email/SKILL.md；'发到我邮箱/推到我邮箱/保存到邮箱'→读取 public-skill/SKILL.md。L0 未指定 → L1：发给自己/结果留存→读取 public-skill/SKILL.md；发给别人/完整收发→读取 personal-mail-skill/SKILL.md。绝不在 read 工具读取 SKILL.md 之前向用户追问账号选择，由系统拦截层统一处理。"
version: "5.1"
trigger_keywords:
  - 发邮件
  - 发送邮件
  - 写邮件
  - 邮箱
  - email
  - send email
  - 收邮件
  - 查邮件
  - 检查邮箱
  - 收件箱
  - inbox
  - 搜索邮件
  - 查找邮件
  - 下载附件
  - 邮件附件
  - 绑定邮箱
  - 邮箱绑定
  - 日报推送
  - 天气推送
  - 报告推送
  - 提醒推送
  - 邮件通知
  - 邮件推送
  - 推送到邮箱
  - 消息留存
  - Agent邮箱
  - AI邮箱
exclude_when:
  - 操作与邮件完全无关（如日历、文件管理、聊天）
  - 用户要求发送短信或站内信（非邮件渠道）
---

# Email Skill（统一邮件入口 / 纯路由层）

> **定位**：`email-skill` 是所有邮件需求的**唯一入口**。它**只做意图识别和路由分发**，不执行任何脚本，不调用任何接口。识别用户意图后，**直接用 `read` 工具读取下游 skill 的 `SKILL.md` 文件**，由系统拦截层统一处理授权与绑定。

## 0. 核心原则

1. **本 skill 不执行任何东西**，只做意图识别和路由分发。
2. **识别完意图后必须立即用 `read` 工具读取下游 skill 的 `SKILL.md` 文件**，禁止用对话替代调用。
3. **不要在用 `read` 工具读取 `SKILL.md` 之前向用户追问"用哪个邮箱""绑定了哪个邮箱"**——所有账号选择、绑定状态、卡片弹出都由系统拦截层统一处理（必要时会自动弹出绑定/选择卡片）。
4. **不要读默认邮箱、不要查 4230 接口、不要做账号探测**——这些是下游 skill（特别是 `personal-mail-skill`）的职责。

## 1. 路由决策（两步法）

```
用户邮件需求
       │
       ▼
   L0 显式指定邮箱通道？
   ├─ 是 → 按 L0 表查
   └─ 否 → L1 发给自己 or 发给别人？
              ├─ 自己 / 结果留存 → public-skill
              └─ 别人 / 完整收发 → personal-mail-skill
```

### 1.1 L0：用户是否**显式**指定了邮箱通道？

| 用户表达信号 | 路由目标 | 说明 |
|-------------|---------|------|
| 提到 **"Agent 邮箱""AI 邮箱""专属邮箱"**，或明确要求**"用 Agent 邮箱发/查"** | `agent-email` | QClaw 专属代收代发通道 |
| 提到 **"用我的 QQ / 163 / Gmail / Outlook / Foxmail / Yahoo / 网易邮箱 发"** | `imap-smtp-email` | 用户明确指定了自己的私邮通道 |
| 提到 **"发到我邮箱""推到我邮箱""保存到邮箱""推送到邮箱"** | `public-skill` | 平台公邮（零配置自留存通道） |

> **注意**：收件人地址包含 `@agent.qq.com`（如 `xxx@agent.qq.com`）**不构成 L0 命中条件**。收件人地址只是"发给谁"，不等于用户指定了发送通道。此类场景应进入 L1 判断（发给别人 → `personal-mail-skill`），由二级路由根据用户绑定情况决定使用哪个通道发送。

> **关键**：L0 只匹配**显式表达**。用户没说邮箱归属时，进入 L1。

### 1.2 L1：用户没指定邮箱时，发给自己还是发给别人？

仅当 L0 未命中时进入 L1。

| 用户场景特征 | 路由目标 |
|-------------|---------|
| 收件人是用户**自己**（无第三方）+ 纯文本 + 不需要附件/抄送/HTML/收件箱搜索/下载附件 | `public-skill` |
| 典型语：**"把这个总结发到我邮箱""日报推到我邮箱""天气推到我邮箱""帮我留存"** | `public-skill` |
| 收件人是**第三方**（同事/客户/朋友/...） | `personal-mail-skill` |
| 需要**附件 / 抄送 cc / 密送 bcc / HTML 邮件** | `personal-mail-skill` |
| 需要**收件箱查询 / 搜索邮件 / 拉取详情 / 标记已读未读** | `personal-mail-skill` |
| 需要**下载附件** | `personal-mail-skill` |

> **personal-mail-skill 是什么？** 它是"完整收发型邮件"的二级路由层，里面会根据用户的默认邮箱偏好和实际绑定情况，再次路由到 `agent-email` 或 `imap-smtp-email`。**你不需要知道里面的细节**，直接用 `read` 工具读取 `personal-mail-skill/SKILL.md` 即可。

## 2. 下游 skill 职责一览

| 下游 skill | 角色 | 你不需要关心的细节 |
|------------|------|--------------------|
| `public-skill` | 平台公邮（零配置自留存） | 公邮绑定状态、配额 |
| `personal-mail-skill` | 完整收发的二级路由层 | 默认邮箱偏好、Agent vs 私邮选择、未绑定时的卡片 |
| `agent-email` | QClaw Agent 邮箱通道 | OAuth 授权状态 |
| `imap-smtp-email` | IMAP/SMTP 私邮通道 | 账号选择、凭证刷新 |

> 在本 skill 里你**只需要决定路由到 `public-skill` / `personal-mail-skill` / `agent-email` / `imap-smtp-email` 之一**，绝大多数 L1 场景应路由到 `public-skill` 或 `personal-mail-skill`。`agent-email` 和 `imap-smtp-email` 通常只在 L0 显式指定时使用。

## 3. 路由动作（执行规范）

确定路由目标后，**立即用 `read` 工具读取目标 skill 的 `SKILL.md` 文件**：

- L0 命中 Agent → 用 `read` 工具读取 `agent-email/SKILL.md`
- L0 命中具体私邮 → 用 `read` 工具读取 `imap-smtp-email/SKILL.md`
- L0 命中"发到我邮箱" → 用 `read` 工具读取 `public-skill/SKILL.md`
- L1 自己 / 结果留存 → 用 `read` 工具读取 `public-skill/SKILL.md`
- L1 别人 / 完整收发 → 用 `read` 工具读取 `personal-mail-skill/SKILL.md`

### 读取后的继续执行规则

- **读取 `agent-email/SKILL.md`、`imap-smtp-email/SKILL.md` 或 `public-skill/SKILL.md` 后**：直接执行该文件中的指令，完成邮件发送/查询操作。
- **读取 `personal-mail-skill/SKILL.md` 后**：该文件是一个二级路由层，**你必须继续执行该文件中的路由动作**——它会告诉你下一步该读取 `agent-email/SKILL.md` 还是 `imap-smtp-email/SKILL.md`。**不要在此步骤回复用户或停止，必须继续 read 下一个 SKILL.md。**

**禁止行为**：
- ❌ 在用 `read` 工具读取 `SKILL.md` 之前向用户追问"你想用哪个邮箱"
- ❌ 在用 `read` 工具读取 `SKILL.md` 之前自己读取默认邮箱配置
- ❌ 在用 `read` 工具读取 `SKILL.md` 之前查询 4230 接口
- ❌ 在用 `read` 工具读取 `SKILL.md` 之前先执行任何 imap-smtp-email / agent-email 的内部脚本
- ❌ 用文字回复替代读取 `SKILL.md`
- ❌ 只"理解"路由逻辑但不实际读取 `SKILL.md`
- ❌ 读取 `personal-mail-skill/SKILL.md` 后就停止，不继续执行其中的路由动作

如果你**不确定路由到哪个**：
- 优先按 L1 给 `personal-mail-skill`（系统拦截层会处理后续）
- 仅在用户场景明显是"自留存"时才路由到 `public-skill`

## 4. 场景示例

### 示例 1：L0 命中 Agent 邮箱

> 用户："帮我看下 Agent 邮箱有没有新邮件"

→ 用 `read` 工具读取 `agent-email/SKILL.md`

### 示例 2：L0 命中具体私邮

> 用户："用我的 Gmail 给客户发一封报价"

→ 用 `read` 工具读取 `imap-smtp-email/SKILL.md`

### 示例 3：L0 命中自留存

> 用户："把这段总结发到我邮箱"

→ 用 `read` 工具读取 `public-skill/SKILL.md`

### 示例 4：L1 发给自己（自留存场景）

> 用户："查一下深圳明天天气，发到我邮箱"

→ 用 `read` 工具读取 `public-skill/SKILL.md`

> 用户："每天下班把日报推到我邮箱"

→ 用 `read` 工具读取 `public-skill/SKILL.md`

### 示例 5：L1 发给别人（完整收发）

> 用户："给客户 alice@example.com 发一封会议确认邮件"

→ 用 `read` 工具读取 `personal-mail-skill/SKILL.md`

> 用户："给团队发周报，抄送 PM，附上 Q3 报表"

→ 用 `read` 工具读取 `personal-mail-skill/SKILL.md`

> 用户："帮我发一封邮件给 haikuotiankong4877@agent.qq.com，标题测试"

→ 用 `read` 工具读取 `personal-mail-skill/SKILL.md`（收件人地址含 `@agent.qq.com` **不等于**用户指定了 Agent 邮箱通道，这里是发给第三方，走 L1）

### 示例 6：L1 收件箱操作（属于完整收发能力）

> 用户："查一下最近两小时的发票邮件"

→ 用 `read` 工具读取 `personal-mail-skill/SKILL.md`

> 用户："下载那封邮件的附件"

→ 用 `read` 工具读取 `personal-mail-skill/SKILL.md`

## 5. 一句话记忆

- **显式说"用 Agent / AI 邮箱"** → 用 `read` 工具读取 `agent-email/SKILL.md`
- **显式说"用我的 QQ / 163 / Gmail / Outlook"** → 用 `read` 工具读取 `imap-smtp-email/SKILL.md`
- **"发到我邮箱 / 推到我邮箱 / 保存到邮箱"** → 用 `read` 工具读取 `public-skill/SKILL.md`
- **未指定 + 发给自己 / 自留存** → 用 `read` 工具读取 `public-skill/SKILL.md`
- **未指定 + 发给别人 / 完整收发** → 用 `read` 工具读取 `personal-mail-skill/SKILL.md`

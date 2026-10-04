---
name: 24haowan-space
description: 用「24好玩·方案空间」连接器（space.24haowan.com，需微信扫码授权）把做好的方案发布成客户专属的微信可读链接、读回客户看了什么、收回反馈、改稿出新版。21 个工具，每一步都是一次工具调用，不靠猜。
description_zh: 用「24好玩·方案空间」连接器把做好的方案发布成客户专属链接、读回客户阅读情况与反馈、改稿出新版；21 个工具，每一步都是一次工具调用。
description_en: Use the 24haowan Space connector (space.24haowan.com, WeChat-scan OAuth) to publish a finished proposal as a client-specific WeChat-readable link, read back what the client viewed, collect feedback, and ship the next version to the same link. 21 tools, one call per step.
version: 1.0.0
author: 24好玩
---

# 24好玩 · 方案空间 · 连接器使用指南

方案空间（`https://space.24haowan.com/mcp`）是一台**需要登录**的 MCP 服务：它以使用者的身份发布方案。平台**不生成内容**——方案由你和用户产出、由用户确认；平台只负责发布、查看、信号与反馈。仅面向企业间（B2B）商务沟通。

## 认证前置

- 首次调用任一工具会走 OAuth：弹出授权页 → 用户微信扫码 → 点「允许」。令牌 30 天有效、自动续期，可在 `https://space.24haowan.com/app/tokens` 撤销。
- 授权失败 / 令牌过期：提示用户重新扫码；不要反复重试。
- 用户还没开通（缺手机号 / 工作区资料）时，工具会返回 `trust.missing`：让用户去 `https://space.24haowan.com/app` 完成开通，**不要猜、不要跳过**。

## 标准动线（每步一个工具）

1. `list_proposals` —— 用户说「上次那份方案」时先查，复用已有 proposal_id，不重复建。
2. `upsert_customer` → `upsert_opportunity` → `create_proposal`（已有的复用 id）。
3. `create_upload_session` → 让用户用本地上传助手 PUT 文件（二进制不走 MCP）→ `finalize_upload`。
4. `get_version` 轮询到 `preview_ready`（PDF / PPTX 会先 `converting`，间隔 15–30 秒）→ **把预览链接给用户确认**。
5. 过审即自动生效。要让别人看：`set_visibility`（口令 / 公开）或 `create_share_link`（一位客户一条，具名）。
6. 「客户看了没」→ `get_engagement_summary`；「说了什么」→ `list_feedback`；会议意见 → `add_external_feedback`。
7. 改稿出 V2：回到第 3 步 push 同一个 proposal；原链接自动更新，旧评论保留。

## 高风险操作：必须先经用户明确确认

| 工具 | 为什么 |
|---|---|
| `create_share_link`、`set_visibility`（passcode / public） | 这一刻内容对外可见 |
| `set_indexable(true)` | 搜索引擎与 AI 抓取器收录**撤不回来** |
| `publish_version` | 切换客户看到的版本（含回滚） |
| `revoke_share_link` | 客户手里的链接立刻失效 |

## 21 个工具

### 客户 / 商机 / 方案
- `upsert_customer`（写）：按名称查找当前工作区的客户，没有就创建。参数 `name`（必填）、`note`（可选）。返回 `customer_id`、`created`。
- `upsert_opportunity`（写）：在客户下按标题查找商机，没有就创建。参数 `customer_id`、`title`（如「2026 双十一整合营销」）。返回 `opportunity_id`。
- `create_proposal`（写）：在商机下创建一份方案（之后每次上传是它的一个版本）。参数 `opportunity_id`、`title`。返回 `proposal_id` 与一条默认链接（初始仅发布者本人可见）。
- `list_proposals`（读）：当前工作区全部方案：标题、proposal_id、版本状态、可见性、默认链接、专属链接数、最近访问时间。

### 上传与版本
- `create_upload_session`（写）：为方案新建一个版本，返回每个文件的预签名 PUT 地址（15 分钟有效）。参数 `proposal_id`、`files[]`（每项 `path` / `size` / `sha256` / 可选 `mime`）、`note`（版本说明）。存储 / 转换 / 审核有月度配额，超出返回 `quota_exceeded` 并带 fix。
- `finalize_upload`（写）：文件 PUT 完成后调用：核对大小 / sha256 / 魔数，HTML 静态安全扫描，校验 manifest，内容安全审核。参数 `version_id`、`manifest`、`hold`（true = 过审后暂不切给客户，之后用 `publish_version` 切）。通过 → `preview_ready` + 预览链接；PDF / PPTX 入口先返回 `converting`。校验失败返回结构化 `issues`（`[code] file:line message → fix`），按 fix 改文件后重新上传，不要绕。
- `get_version`（读）：查版本状态（converting / moderating / review / preview_ready / published / draft…）、页数、失败或命中原因。
- `publish_version`（写）：hold 的版本确认后切给客户；或把客户可见版切回旧版（回滚）。参数 `proposal_id`、`version_id`、`note`（可选）。

### 谁能看
- `set_visibility`（写）：切默认链接的可见性。参数 `proposal_id`、`visibility`（`private` 仅本人 / `passcode` 口令可看 / `public` 任何人可看，需 T1）、`passcode`（可选，4–16 位字母数字）。口令 / 公开访客不具名。
- `set_indexable`（写）：这份方案能否被搜索引擎与 AI 抓取器收录，默认 false。前提先 `set_visibility` 到 public。参数 `proposal_id`、`indexable`。
- `create_share_link`（写）：给特定客户一条专属链接（建议一人一条、具名）。参数 `proposal_id`、`recipient_name`（如「李总」）、`recipient_title`、`expires_in_days`（默认 30）、`allow_download`、`allow_comment`、`passcode`、`replay`（默认开）、`vanity`、`params`、`pin`（钉在当前版）。返回 `url`（微信内直接可开）与 `card_url`（卡图页，长按识别后转发即卡片）。
- `list_share_links`（读）：这份方案全部客户链接：收件人、到期、权限、最近访问、传播面状态（`passcode_required` = 打开设备较多已自动加口令；`suspended` = 新设备过多已暂停）。
- `clear_auto_passcode`（写）：取消传播面自动加的口令。参数 `link_id`。
- `revoke_share_link`（写）：立即让某条客户链接失效（可恢复）。参数 `link_id`。
- `restore_share_link`（写）：恢复一条已撤销的客户链接。参数 `link_id`。

### 阅读信号
- `get_engagement_summary`（读）：最近 N 天被谁看了、看了哪几页、跳过哪几页、停留多久、下载 / 演示 / 评论 / 疑似转发。参数 `proposal_id`、`days`（默认 30）。返回末尾带**证据档位**（none / thin / usable）：不是 usable 时先说明证据不足；**只说事实与下一步动作，不说意向分、成交概率、「他很感兴趣」**。「没有数据」≠「没兴趣」。
- `list_sessions`（读）：每一次访问一行：谁、何时、时长、落地页、最远页、步数、设备、来源。参数 `proposal_id`、`days`、`link_id`、`include_internal`。
- `get_session_timeline`（读）：某次访问的逐步时间线（翻页 / 停留 / 滚动 / 点击 / 下载 / 评论）；HTML 包开了录制时带 `replay_url`。参数 `session_id`。

### 反馈闭环
- `list_feedback`（读）：全部反馈线程：客户页面评论（带第几页 / 引用锚点）、回填的外部意见、内部备注，及状态（open / confirmed / disputed / resolved）。参数 `proposal_id`、`status`、`version_id`。
- `add_external_feedback`（写）：把会议 / 微信 / 电话 / 邮件里的意见写回方案。参数 `proposal_id`、`body`、`source`、`version_id`、`anchor`、`page`、`sectionId`、`textSnapshot`、`visibility`（`all` 客户可见 / `internal` 内部备注）。
- `set_feedback_status`（写）：把某条反馈标为 confirmed / disputed / resolved / open。参数 `feedback_id`、`status`。

## 纪律

1. 对外的时刻（发链接、放开可见性、打开收录）必须**用户明确确认**后才做。
2. 专属链接一人一条，不把同一条发给多个人；要公开传播必须显式 `set_visibility public`。
3. 校验失败按返回的 `fix` 改，重新上传，不绕过。
4. 阅读情况的结论由你产出、平台只给事实；证据档位不够就说不够。

## 异常与恢复

- **超时 / 连接失败**：公网 HTTPS，重试一次；仍失败告诉用户「方案空间暂时连不上」，不编结果。
- **授权失效（401）**：提示重新扫码授权。
- **参数错误（如 visibility 不在枚举、files 为空）**：按上面的取值改正后重试。
- **配额超出（quota_exceeded）**：把返回里的 fix 原样告诉用户（撤销不用的链接 / 删旧版本 / 联系运营）。
- **审核命中（review）**：客户暂看旧版；告诉用户在管理台复核，不要反复重传同一内容。

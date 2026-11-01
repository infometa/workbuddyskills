---
name: aike-dashboard
display_name: 我的仪表盘
display_name_en: My Dashboard
description: 查看外贸销客工作台仪表盘：一次调用返回客户总数 / 进行中展会数 / AI快记总数三项统计，附近 7 天邮件战报（送达/回复/打开率与客户邮件动态，可筛未读）、今日核心跟进工作台、最近客户动态与未关联客户的快记提醒；还支持基于已开放数据组合自定义指标卡。当用户说"看看今天的工作台""仪表盘""最近邮件效果怎么样"，或"加一张近期展会的卡"时触发。
description_zh: 工作台聚合概览：客户/展会/AI快记统计、近 7 天邮件战报、今日核心跟进工作台、最近客户动态、未关联快记提醒，并可组合自定义指标卡。
description_en: Workspace overview with customer, exhibition and AI-note stats, 7-day mail report, priority followups, recent activity, unlinked recordings, and composable metric cards.
category: sales-commerce
version: 2.0.0
author: AI销客
---

# 我的仪表盘

面向「客户管理专家」的首页聚合视图，一屏看清当天工作全貌。

## 功能描述

本技能提供两类仪表盘能力：

### A. 基础仪表盘（固定接口）
- 通过 `get_dashboard` 一次调用返回预置概览：**三项统计（客户总数 / 进行中展会数 / AI 快记总数）+ 近 7 天邮件战报 + 今日核心跟进工作台 + 最近客户动态 + 未关联客户的快记提醒**（2026-09 起新增邮件战报与工作台）
- 邮件战报：送达 / 回复 / 打开 / 打开率 + 逐条客户邮件动态（打开/回复事件）；`feedReadStatus='unread'` 只看未读，标记已读用 `mark_mail_feed_read`
- 今日核心跟进工作台（客户 / 原因 / 跟进建议 / 跟进指数）的查询与忽略 / 转待办动作详见「今日重点跟进」技能（`get_priority_followups` 等），本技能只透传数据
- 开箱即用，覆盖大多数日常场景，是默认视图
- 注意：基础概览**不含待办列表**；待办走「我的待办」技能（`list_todos`）

### B. 自定义仪表盘（按需组合开放数据）
- 在基础仪表盘之上，用户可**基于 gsales 连接器已开放的数据**自由组合自己的指标卡
- 专家按用户意图，路由调用其他技能对应的工具来拉数，并渲染进同一份 HTML 仪表盘（追加卡片，详见「返回格式 → 自定义卡片并入同一份 HTML」）：

| 想要的自定指标 | 可组合调用的工具 | 口径说明 |
|---|---|---|
| 待跟进 / 逾期待办 | `list_todos`（`status='0'` 取未完成） | 支持 `due_date_from` / `due_date_to` 截止时间范围筛选；"逾期"= `due_date_to` 传当前时刻 + `status='0'` 服务端筛出（2026-09 起） |
| 近期营销打开率 | `get_marketing_feedback`（带 `task_id` 取 `stats.openedEmailCount` / `openRate`） | 打开为任务级聚合口径；逐封打开与链接点击明细不在返回内 |
| 近期展会 | `search_exhibitions` | 可按 `stage` 过滤，`total` 即数量 |
| 近期录音 / 快记数 | `list_recent_recordings` | `total` 即总数，可按 `hasCustomerAssociation` 区分 |
| 客户总量 / 各跟进状态客户数 | `search_customers` | `total` 即数量；"本周/本月新增"用 `createdAtFrom` / `createdAtTo` 精确统计（2026-09 起），也可按 `followStatus` / AI 画像等维度计数 |

- 自定义示例：
  - "把未完成的待办单独列出来" → 调 `list_todos({ status: '0' })`
  - "我想看本月营销邮件的打开情况" → 先 `get_marketing_feedback` 列任务，用户选定后带 `task_id` 取 `stats`
  - "最近有哪些进行中的展会" → 调 `search_exhibitions({ stage: 'ongoing' })`

> 基础仪表盘是默认视图；自定义是在其基础上的**增量补充**，用自然语言描述想要的指标即可，专家负责路由与渲染。

## 触发场景（自然语言示例）

- "看看今天的工作台情况"
- "打开仪表盘"
- "我有多少客户、几个展会还在进行？"
- "把未完成的待办单独列出来"（自定义）
- "我想看本月营销打开率"（自定义）

## 通用调用约定（gsales MCP）

本技能通过 `gsales` 连接器（GlobalSales 外贸销客 MCP 网关）调用工具，统一遵循：

- **鉴权与归属**：以当前用户 OAuth 授权身份调用，数据回流该用户自己的外贸销客空间（跨用户数据隔离）。
- **`full` 开关**：读工具默认 `full=false`，返回精简字段（省 token）；显式 `full=true` 返回后端原始全量字段。`get_dashboard` 为聚合透传，**无 `full` 参数**。
- **分页**：列表类工具 `page`（默认 1）、`pageSize`（默认 10，上限 50；`list_todos` 默认 20）；越界报参数错误。
- **`dry_run` 预演**：创建 / 修改类写工具支持 `dry_run=true`，仅回显载荷、**不落库**；默认 `false` 正式写入。
- **`confirm` 二次确认**：删除类（`delete_customer` / `delete_todo`）先不带 `confirm` 返回摘要；用户确认后带 `confirm=true` 才执行（不可恢复）。
- **永不开放**：邮箱配置、营销发送、系统管理等凭证与外发能力（L4）任何面均不提供；本技能只查结果、不代发。
- **错误与恢复**：`401`=授权无效/过期/已断开 → 引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）；`403`=用户角色无此权限（本技能依赖 pc:dashboard；连接器授权已固定全量业务权限，403 多为角色未配置该权限码）→ 联系管理员开通，或断开重连；`404`/参数校验错误 → 核对入参（id 是否存在、枚举是否用英文值）后重试。

## 依赖的 MCP 工具

通过 `gsales` 连接器调用：

| 工具名 | 用途 | 所需权限范围 | 状态 |
|---|---|---|---|
| `get_dashboard` | 返回仪表盘聚合数据 | `pc:dashboard`（2026-09-04 D-045 起挂码，连接器授权已包含） | ✅ 已开放 |

## 工具调用说明

### `get_dashboard`

- **用途**：获取工作台概览聚合（一次聚合后端四个端点：overview / home / customer-updates / unlinked-ai-records）
- **入参**：
  - `feedReadStatus`（enum，可选，2026-09 新增）：邮件动态已读状态过滤，`read` / `unread`；不传返回全部
  - 其余**无参数**（数据范围由授权用户身份决定；没有 `period`、没有 `full`）
- **返回字段**（原样透传，不裁剪）：
  - `overview`：
    - `customerCount`（number）：客户总数
    - `activeExhibitionCount`（number）：进行中展会总数
    - `aiNoteCount`（number）：AI 快记总数
  - `home`（2026-09 新增）：
    - `mailReport`：近 7 天邮件战报 `{ delivered（送达）, replies（回复）, opened（打开）, openRate（打开率）, feed[] }`；`feed[]` 每条 `{ customerId, customerName, emailId, subject, event（`opened` 打开 / `replied` 回复）, eventAt, isRead, replyExcerpt（回复摘要，仅 replied 事件有） }`
    - `workbench`：今日核心跟进工作台 `{ available, hint, sourceLabel, suggestions[] }`；`suggestions[]` 每条 `{ id, rank, score（跟进指数 0-100）, level（urgent/high/medium）, customerId, customerName, followStatus, urgency, reason, suggestion }`——查询、忽略与转待办动作见「今日重点跟进」技能
  - `customerUpdates.items[]`（最近客户动态）：
    - `id`（string）：记录 ID
    - `companyName`（string）：客户名称
    - `action`（string）：操作动作（如"新增联系人: Michael Zhang"、"新增客户"）
    - `updateTime`（string）：更新时间
    - `operatorName`（string）：操作人
  - `unlinkedAiRecords.items[]`（未关联客户的快记提醒）：
    - `id`（string）：录音 ID
    - `recordCode`（string）：录音编号（如 #REC-20231024-01）
    - `recordTime`（string）：录音时间
    - `exhibitionName`（string）：展会名称
    - `recorderName`（string）：录音人员
- **示例调用**：
  ```
  mcp__gsales__get_dashboard({})
  mcp__gsales__get_dashboard({ feedReadStatus: "unread" })
  ```

## 返回格式

本技能的结果**必须以 HTML 仪表盘形式直接渲染展示**（单文件、内联 CSS、浅色主题），而非纯文本卡片。专家层在拿到 `get_dashboard` 返回后，套用下方「HTML 仪表盘模板」填充数据，生成可预览的 HTML 回给用户；如需独立查看，可保存为 `.html` 并通过预览面板打开。

- 仪表盘四大区块：**核心指标卡**（三项统计）+ **近 7 天邮件战报**（数值条 + 客户邮件动态列表）+ **最近客户动态**（时间线）+ **未关联快记提醒**（待办清单）；用户自定义卡片在**同一份 HTML 上增量追加**，不另起；今日核心跟进若需独立呈现走「今日重点跟进」技能
- 数值严格取自 `get_dashboard` 返回字段（见上方「工具调用说明」），禁止臆造；空数组渲染占位提示
- 未关联快记提醒可衔接「上传对话录音 / 查客户」技能做补录关联
- 专家层可基于返回数据做下一步建议（如"你有 3 条未关联快记，要我帮你逐条关联客户吗"）

### HTML 仪表盘规范

- 单文件、`<style>` 内联、无外部依赖；适配浅色 IDE 主题（背景 `#EFF6FF`，卡片白底圆角 + 轻阴影）
- 主色 `#256AF4`，辅助 `#7C3AED`（进行中展会）/ `#22d3ee`（AI 快记）；大数字突出、标签灰阶
- 指标卡三列等宽；下方双栏：左「最近客户动态」、右「未关联快记提醒」
- 单条动态 / 提醒按模板循环渲染；列表为空时显示「暂无」占位

### HTML 仪表盘模板（占位符 `__XXX__` 由返回字段填充）

```html
<div class="dash">
  <header class="dash-hd">
    <h2>我的仪表盘</h2>
    <span class="dash-sub">客户管理 · 实时概览</span>
  </header>

  <section class="metrics">
    <div class="metric">
      <div class="metric-val" style="color:#256AF4">__CUSTOMER_COUNT__</div>
      <div class="metric-label">客户总数</div>
    </div>
    <div class="metric">
      <div class="metric-val" style="color:#7C3AED">__ACTIVE_EXHIBITION_COUNT__</div>
      <div class="metric-label">进行中展会</div>
    </div>
    <div class="metric">
      <div class="metric-val" style="color:#22d3ee">__AI_NOTE_COUNT__</div>
      <div class="metric-label">AI 快记总数</div>
    </div>
    <!-- 自定义数值型卡片：复制 .metric 块改数字/标签/color，追加到此处，网格自动换行 -->
  </section>

  <section class="panel mail-report">
    <h3>近 7 天邮件战报</h3>
    <div class="mail-stats">
      <span>送达 <b>__MAIL_DELIVERED__</b></span>
      <span>回复 <b>__MAIL_REPLIES__</b></span>
      <span>打开 <b>__MAIL_OPENED__</b></span>
      <span>打开率 <b>__MAIL_OPEN_RATE__</b></span>
    </div>
    <ul class="feed">
      <!-- 循环 __MAIL_FEED__：每条一条 <li> -->
      <li><span class="co">__FEED_CUSTOMER__</span> · __FEED_SUBJECT__
        <div class="meta">__FEED_EVENT__ · __FEED_EVENT_AT__ · __FEED_READ__</div></li>
    </ul>
  </section>

  <div class="cols">
    <section class="panel">
      <h3>最近客户动态</h3>
      <ul class="feed">
        <!-- 循环 __CUSTOMER_UPDATES__：每条一条 <li> -->
        <li><span class="co">__COMPANY_NAME__</span> · __ACTION__
          <div class="meta">__OPERATOR_NAME__ · __UPDATE_TIME__</div></li>
      </ul>
    </section>
    <section class="panel">
      <h3>未关联快记提醒</h3>
      <ul class="warn">
        <!-- 循环 __UNLINKED_RECORDS__：每条一条 <li> -->
        <li><span class="co">__RECORD_CODE__</span><span class="tag">未关联</span>
          <div class="meta">__EXHIBITION_NAME__ · __RECORDER_NAME__ · __RECORD_TIME__</div></li>
      </ul>
    </section>
    <!-- 自定义列表型卡片：复制 .panel 块追加到此处 -->
  </div>
</div>

<style>
  .dash{max-width:880px;margin:0 auto;padding:22px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:#EFF6FF;border-radius:16px;color:#1e293b;}
  .dash-hd{display:flex;align-items:baseline;gap:12px;margin-bottom:18px;}
  .dash-hd h2{margin:0;font-size:22px;}
  .dash-sub{font-size:13px;color:#64748b;}
  .metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px;}
  .metric{background:#fff;border-radius:14px;padding:18px;text-align:center;box-shadow:0 2px 10px rgba(37,106,244,.08);}
  .metric-val{font-size:34px;font-weight:700;line-height:1;}
  .metric-label{margin-top:8px;font-size:13px;color:#64748b;}
  .cols{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
  .panel{background:#fff;border-radius:14px;padding:16px;box-shadow:0 2px 10px rgba(37,106,244,.08);}
  .panel h3{margin:0 0 12px;font-size:15px;}
  .feed,.warn{list-style:none;margin:0;padding:0;}
  .feed li,.warn li{padding:10px 0;border-bottom:1px solid #f1f5f9;font-size:13px;color:#334155;}
  .feed li:last-child,.warn li:last-child{border-bottom:none;}
  .co{font-weight:600;color:#1e293b;}
  .meta{color:#94a3b8;font-size:12px;margin-top:3px;}
  .warn li{color:#b45309;}
  .tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:999px;background:#fef3c7;color:#b45309;margin-left:6px;}
  .empty{color:#94a3b8;font-size:13px;padding:10px 0;}
  .mail-report{margin-bottom:14px;}
  .mail-stats{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;color:#475569;margin-bottom:8px;}
  .mail-stats b{color:#256AF4;font-size:17px;margin-left:4px;}
  @media (max-width:640px){.metrics{grid-template-columns:1fr;}.cols{grid-template-columns:1fr;}}
</style>
```

### 自定义卡片并入同一份 HTML

用户新增的指标卡**不另起文本或独立卡片**，直接插入上方模板的同一份 HTML 仪表盘中：

- **数值型卡片**（如待跟进数、营销打开率、展会数、录音数）：复制一个 `.metric` 块，改数字、标签，按需调 `color`，追加到 `.metrics` 网格（自动换行排布）
- **列表型卡片**（如「未完成的待办」「各跟进状态客户数」）：复制一个 `.panel` 块，改标题与 `<ul>` 内容，追加到 `.cols` 网格
- 自定义卡片沿用同一套 CSS（`.metric` / `.panel` / `.feed` / `.warn`），无需新增样式；保持浅色主题与品牌色一致
- 每次新增在**已渲染的 HTML 上增量追加**，不重建、不覆盖原有区块；数据严格取自对应工具返回字段

> 字段映射：`__CUSTOMER_COUNT__`←`overview.customerCount`、`__ACTIVE_EXHIBITION_COUNT__`←`overview.activeExhibitionCount`、`__AI_NOTE_COUNT__`←`overview.aiNoteCount`；战报数值 `__MAIL_DELIVERED__` / `__MAIL_REPLIES__` / `__MAIL_OPENED__` / `__MAIL_OPEN_RATE__`←`home.mailReport` 同名字段，邮件动态遍历 `home.mailReport.feed[]`（`__FEED_EVENT__` 渲染为"打开了邮件/回复了邮件"，`__FEED_READ__` 未读时高亮"未读"）；客户动态与未关联提醒分别遍历 `customerUpdates.items[]` / `unlinkedAiRecords.items[]` 对应字段。

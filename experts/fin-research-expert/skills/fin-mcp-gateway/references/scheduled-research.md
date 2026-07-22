# WorkBuddy Scheduled Research

Use this reference only in WorkBuddy when the user explicitly asks to create or manage a scheduled public-market research task, or after a successful evidence-backed answer when the user has clearly expressed continuing intent. The native Automation record is the only source of truth.

## Native capability boundary

- Capability contract checked against the local WorkBuddy `5.2.6` installation on 2026-07-18. The runtime-injected tool schema remains authoritative when a later client version changes fields.
- Use WorkBuddy built-in `automation_update` for create, view, update, pause, resume and delete operations. Follow the tool schema injected by the current WorkBuddy version; never claim success before the tool returns success.
- Recurring plans use native RRULE fields. One-time plans use native `scheduledAt`. Keep schedule, timezone and research Prompt in separate native fields.
- Default China-market timezone is `Asia/Shanghai`. Add `validFrom` or `validUntil` only when the user requests a bounded period.
- Do not use Shell, `crontab`, cron files, SQLite, `$HOME/.workbuddy/workbuddy.db`, direct task-file edits, `rm`, local scripts or a resident process to create, inspect, update or delete a WorkBuddy task.
- Do not store a second `enabled`, task status or task ID copy in the expert package. View the actual Automation before every management change.
- When the current client does not expose the native Automation tool, explain that the task was not created. You may provide a reusable research Prompt, but never fabricate a task ID, status or next run.

## Intent and consent gate

| Intent | Behavior |
|---|---|
| Explicit create with subject, scope, cadence and time | Show one concise creation summary; create only after explicit confirmation unless the user's latest message itself unambiguously says to create now |
| Continuous intent without cadence or time | Ask only for the missing cadence/time, or propose one explicit default and wait for confirmation |
| One-time reminder with an exact time | Confirm the resolved subject and create a one-time `scheduledAt`; do not convert it to RRULE |
| Ambiguous subject | Resolve or ask the user to choose before creating |
| View/update/pause/resume/delete | View the real Automation first, then perform only the requested change |
| Price threshold or event-trigger request | Explain that v1 is time-triggered; ask for a polling cadence or leave the request uncreated |

An inferred benefit is not consent. Do not create a task merely because the research could be followed later.

## Contextual invitation

Invite at most once in the current conversation and only when all conditions hold:

1. the current research answer has successful public evidence;
2. the user's wording includes a continuous signal such as 后续、继续跟踪、每天、每周 or 有变化;
3. no invitation has already been made in this conversation;
4. the user has not declined it in this conversation.

Do not invite after a one-time price/fact query, an authentication failure, a source failure with no usable evidence or an answer produced without current public evidence. After a decline, continue normal research without repeating the invitation.

## Create and duplicate-prevention workflow

1. Resolve the tracked subject to a canonical company/security, industry/theme or public event. Preserve market and code/industry identity. If the current conversation already contains a unique, evidenced identity, reuse it; otherwise resolve it before creation.
2. Confirm the evidence scope requested: market, announcements, news, research reports, graph evidence or Same Boat viewpoints. Do not silently add personal holdings, trade history or another data domain.
3. Determine schedule kind: daily, workday, weekly or once; local time; timezone; and optional validity period.
4. Use native Automation view/list behavior to compare existing tasks by canonical subject + evidence scope + cadence. Update or return an equivalent task instead of creating a duplicate. Ask before replacing a conflicting task.
5. Show a concise summary containing subject, evidence scope, schedule, timezone and whether this is create or update. Obtain explicit consent.
6. Call `automation_update` using the current native schema. The task Prompt uses the self-contained template below; native schedule fields carry the actual timing.
7. After success, return the native task name, actual status, schedule, timezone and next run. If the native result lacks a field, say it was not returned instead of inventing it.

Creating or managing a task does not itself require a financial MCP call when the subject and scope are already unambiguous. The later Automation run performs the research calls.

## Self-contained stored Prompt

Fill every bracket from the confirmed request. Do not leave placeholders in the created task.

```text
执行一项公开市场定时研究更新。

研究对象：[规范名称]；市场/稳定身份：[交易所与代码，或已解析行业/主题身份]。
证据范围：[行情/公告/新闻/研报/行业图谱/同舟观点的确认子集]。
检索窗口：[日更使用过去24小时或上一个可用交易日至今；周更使用过去7天；单次任务使用用户确认的窗口]。

直接使用同舟金融研究 Connector 查询本次窗口内的公开证据。先解析对象，再按最窄证据域调用；沿用 found、partial、empty、unsupported、error、auth_required 六种证据状态，同一失败来源最多进行两次有界恢复。不得使用模型记忆、旧对话、缓存、个人持仓或交易历史补数。

输出不超过500字，依次包含：执行时间与时区、实际证据窗口、关键新增证据及来源类型/日期/真实原文入口、影响边界、数据缺口、下一观察点。行情使用实际返回的最新交易日和币种；非交易日明确最近可用交易日。

若本窗口没有显著新增，简短写明“本窗口未发现显著新增”，并列出实际检索窗口与来源类型，不复制上次长报告、不生成示例内容。若部分来源失败，先交付已取得证据，再标注缺口；若授权失效或全部关键来源失败，只通知重新连接或稍后重试，不生成替代研究结论。

本内容由AI生成，仅基于公开信息整理，不构成投资建议，不构成个股推荐；不提供买卖指令、目标收益或收益承诺。
```

## Scheduled output contract

| Outcome | Required user-visible result |
|---|---|
| New evidence | Execution time, actual window, dated source evidence, bounded impact and next observation |
| No material change | “本窗口未发现显著新增”, actual searched window and source types; no copied prior report |
| Partial source success | Valid evidence first, then named source-type gap without internal route or transport details |
| Non-trading day | Latest available trading date and returned currency; do not label the holiday as missing market data |
| Authentication required | Ask the user to reconnect the WorkBuddy Connector; do not use cached or model-generated substitutes |
| Service unavailable | State the affected evidence type and retain other current valid evidence; if none remain, return only the safe failure notice |

Every scheduled financial update retains the four-part disclaimer: AI-generated, public information, not investment advice and not an individual-stock recommendation.

## Management workflow

- **View**: return native name, status, cadence, timezone, next run and validity period.
- **Update**: view first, preserve every field the user did not request to change, show the change summary, then call the native update operation.
- **Pause/resume**: require explicit intent and report the actual native result. Do not reinterpret pause as delete.
- **Delete**: require explicit intent, use the native delete operation and confirm only after success. Never use filesystem deletion.
- **Missing task**: state that the native task is no longer present. Do not display stale local state or silently recreate it.

## Operations and privacy

Permitted low-cardinality operational fields are action, result, schedule kind, evidence-type set, duration bucket and safe error category. Do not record the task Prompt, research answer, credentials, full task ID, account identifier, phone number, personal holdings, trade history or local paths.

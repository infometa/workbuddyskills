---
name: sparkx-promo-reset
description: >-
  After a promotion (Prime Day, Prime Big Deal Days, Black Friday / Cyber Monday, holiday
  events), find every bid, budget, placement and AI managed-group setting a person changed
  for the promo, recover each one's pre-promo value from the operation log, and restore
  them - all at once, or (the user's choice) paced by post-promo performance: immediately,
  stepped down over 2-3 days, or held - with a reason per item, a preview, an undo file and
  read-back. Use
  when the user says "大促结束了把调整复位", "把 Prime Day 改的预算改回去", "黑五调的出价恢复一下",
  "大促期间我都改了什么", "reset my promo changes", "revert Prime Day bids". Not for
  setting things up before a promo, not for undoing AI's own adjustments, and not for
  general budget or bid edits with no promo behind them (use sparkx-edit-ads /
  sparkx-edit-ai-group).
metadata:
  version: 1.0.4
---

# Promo Reset (大促调整复位)

## Scope: an orchestration skill

This skill has no MCP tool of its own. It reads with three tools and writes with two
existing skills:

| Step | Tool | Owning skill - read it first |
|---|---|---|
| What changed, and what it was before | `get_operation_log` | [sparkx-query-operation-log](../sparkx-query-operation-log/SKILL.md) |
| Post-promo performance and the normal range | `get_ads_perf` | [sparkx-query-ads-performance](../sparkx-query-ads-performance/SKILL.md) |
| Internal ids, current values, groups, inventory | `get_entity_metadata` | [sparkx-query-entity-metadata](../sparkx-query-entity-metadata/SKILL.md) |
| Restore budgets, bids, placements | `batch_update_ads` | [sparkx-edit-ads](../sparkx-edit-ads/SKILL.md) |
| Restore managed-group settings | `save_sp_sb_ai_managed_group` / `edit_sd_ai_managed_group` | [sparkx-edit-ai-group](../sparkx-edit-ai-group/SKILL.md) |

> **Dependency - install all five skills above alongside this one.** Skills install as
> sibling directories under your agent's skills root (`.claude/skills/<name>/` for Claude
> Code; see the installation notes in [README](../README.md)); the `../sparkx-.../` links in
> this file resolve against it. Every write in this skill goes through the owning write
> skill's rules - its confirmation protocol, its discriminator fields, its read-back. This
> file does not repeat them and does not relax them.

Auth, error envelopes, pagination, date limits and currency rules are in the base skills'
`references/platform-notes.md` - read it once from any of the three query skills (they ship the
same file). The cross-tool points that matter for this skill:

- **Ids differ by tool.** `get_ads_perf` returns Amazon ids; `get_operation_log` returns both
  (`entityId` internal, `amazonCampaignId` / `amazonEntityId` Amazon); writes need the internal
  id plus discriminator fields from `get_entity_metadata`. Join performance to the log on the
  Amazon id; write with the internal id.
- **Clocks differ by entity.** Ad-entity log rows are store-local for one `profileId`;
  managed-group rows are always UTC. Performance dates are store days.
- **Amounts are local currency** on every tool here; a store's run never mixes currencies.

| Reference | Read it when |
|---|---|
| [`references/restore-list.md`](references/restore-list.md) | Building the restore list: which log queries, which rows count, how to get the pre-promo value, how a log row maps to a write |
| [`references/pacing-rules.md`](references/pacing-rules.md) | Deciding each item's suggestion: normal range, target ACOS, "clearly worse", step-down days, held items |

## Output language

Examples below are in Chinese because most customers are. They show structure, not text to
copy: answer in the user's language, and pass `language` to `get_ads_perf` to match.

## What it does, in one paragraph

A promo is set up by hand: budgets raised, bids raised, placement multipliers raised, managed
groups switched to "活动冲量" (promotion sales boost) with a looser target ACOS. After the
promo all of that has to come back, and people forget what they changed, forget to change it
back, or cut everything at once and lose traffic that was still converting. This skill
recovers every human promo change and its **pre-promo value** from the operation log and,
as the user chooses, either restores everything at once or looks at how each item did in the
days after the promo and proposes **restore now / step down over a few days / hold / you
decide** - each with the numbers behind it. Nothing is written
until the user confirms, and an undo file is produced before the first write.

## Principles

1. **Ask before suggesting.** The window, how to restore and any follow-on deals change
   the answer (Step 1).
2. **Only restore what a person changed for the promo.** AI and rules keep doing their job;
   undoing their moves fights the AI (see [`restore-list.md`](references/restore-list.md)).
3. **Every suggestion carries its numbers.** "ACOS 119%, normal 34-41%, target 41%" - never
   a bare verdict.
4. **Never overwrite a later decision.** Anything a person changed again after the promo is
   the customer's call.
5. **Undoable.** Undo file before the first write, read-back after every write.

## Workflow

### Step 1 - Ask three things first

| Question | What it decides |
|---|---|
| Which promo, which dates - including warm-up and wind-down days? | The log window |
| How to restore: **all at once, regardless of performance**, or **in batches by performance** (recommended) | Whether Step 3 judges each item |
| Anything still running after the promo: a deal not yet ended, a product low on stock? | Items to hold, items to restore first |

Before asking, look at the store's daily spend around the dates the user gave (`get_ads_perf`,
`factEntity: campaign`, `select: ["date"]`) and propose the window from the data: "spend was
about 2x normal on 10/6-10/7, and there were many changes on 10/5 and 10/8 - include those
four days?" Promo adjustments routinely start a day or two before the event and end a day
after. Also say now if the managed groups are still in "活动冲量" - that is often the
biggest single item (Step 2c).

Resolve `profileIds` the usual way (`get_user_authorized_context`; one store unless the user
asks for several). **Run this skill one store at a time**: log timestamps are store-local
only when one `profileId` is passed (see the operation-log skill's "createdDate Timezone"),
and the window boundaries depend on it.

### Step 2 - Build the restore list

Full procedure, queries and edge cases: [`references/restore-list.md`](references/restore-list.md).
The rules that decide the result:

a. **Pull the log without a `changeBy` filter and classify `changedBy` yourself.** A row is a
   human change when `changedBy` is an email address or `Manual`. **`Amazon Console` is a
   source, not an operator** — it means the change came from Amazon's side, and nothing
   tells you who or what made it there. **It is not in the default restore set.** Pull the
   rows, list them in their own section as source-unknown, force their `suggestion` to
   `customerDecides`, and restore only the ones the user confirms one by one — never via
   `restoreNow` or `stepDown`. You
   **cannot** filter with `changeBy: manual` — the server **rejects** it (case-insensitive,
   in `IN`, `NOT_IN` or mixed). It only ever matched rows whose `changedBy` was literally
   `Manual` and missed every change attributed to a user's email (seen in production
   2026-10: a whole promo's budget changes, all email-attributed, returned nothing under
   `manual`), which is why it is no longer accepted.
   The user may widen the sources ("API 改的也算") - then say in the list header which sources
   are included.

b. **Pre-promo value = the `previousValue` of the first human change to that field inside the
   window.** Later changes inside the window do not matter, including a blanket "set
   everything to $100" the customer did on the last day. Skip creation rows (`previousValue`
   `0` or empty) - those are not pre-promo values.

c. **Managed-group settings go on the list too, and go first.** Objective (`optimizeType` in
   the log, `targetType` on SP/SB write), target ACOS (`acos`), AI personality, bid range
   (`bidRangeMin` / `bidRangeMax`), action-space switches and the group's **total budget**
   changed directly on a group do not revert by themselves. Groups that used a **dated
   schedule** for the promo revert automatically when it ends - list them as "已由排期自动失效",
   nothing to do. Restore group settings before budgets: the objective and target decide how AI
   bids; the budget is only a ceiling.

   **Zero managed-group rows is not proof of zero changes.** The managed-group log query
   returns an empty list when it fails internally instead of an error. If it comes back empty
   while groups are still on "活动冲量" (`targetType: 3` in `get_entity_metadata`), say the
   group history could not be read and treat those groups as "you decide".

d. **Budgets: only `dailyBudget` counts.** In managed groups AI rewrites the day's spendable
   budget every hour (`changeField: currentBudget`, hundreds of rows per store in a few days).
   Those are not promo adjustments and must not be restored.

e. **Split the list:**
   - raised during the promo -> candidates for restore (Step 3 decides how)
   - lowered during the promo -> **customer decides**; often a deliberate cut (Step 3 notes
     whether the lower budget is actually binding)
   - changed again by a person after the window -> **customer decides**
   - created during the promo -> **customer decides** (pause or keep; there is no "before")
   - current value already equals the pre-promo value -> skip, but count it

### Step 3 - Decide each item's pace

**If the user chose "all at once"**, skip only the performance judgement: no post-promo
`get_ads_perf` pull and no per-item pacing. Everything that protects later decisions still
runs - the operation log is still queried through today (Step 2; that is how items changed
again after the window are found), and current values are still read and the stale check
still runs before every write (Step 5).

Every restorable item then goes back at once: **all managed-group settings on the list**
(objective, target ACOS, AI personality, bid range, action-space switches, total budget) and
every bid, budget and placement raised during the promo. Unchanged: lowered, changed again
after the window and created during the promo still go to the customer, and a deal still
running is still held - restoring those would overwrite a decision rather than undo a promo
adjustment. The "is the lower budget binding" note still works: it comes from the
out-of-budget events in the operation log, not from performance data.

The rest of this step applies to "in batches by performance".

Read each item's last 3 full days after the window and compare with its own normal range and
its target. Exact calculations: [`references/pacing-rules.md`](references/pacing-rules.md).

Checked in this order - the first that applies wins:

| After the promo | Suggestion |
|---|---|
| Barely spent | Restore at once - nothing to judge |
| Clearly worse: ACOS **both** above its own normal range **and** above its target | Restore now |
| Above target, but in line with its own normal | Restore at normal pace; note it runs above target anyway - not caused by the promo |
| Conversion rate still above its normal range | Step down over 2-3 days |
| Within normal range | Restore at once if raised < 1.5x, else over 2 days |

Overrides: a product low on stock -> restore now; a deal still running -> hold until it ends.
Lowered during the promo -> customer decides, with a note on whether the lower budget is
binding (out of budget on at least 2 of the 3 post-promo days) or not (budget left unspent -
adding it back changes nothing; point to stock / buy box / listing instead).

When post-promo data is too thin to judge (fewer than ~3 days since the window ended): restore
at once if the item was raised < 1.5x, otherwise step down over 2 days, and say the data was
too thin to judge by performance.

### Step 4 - Present the list, then preview

Show the customer, in this order:

1. **Header**: window, store, sources included, how many items in each group.
2. **Managed-group settings** to restore (old -> new per field).
3. **Restore now**, **step down** (with each day's value), **restore at once** - each row:
   name, now -> target (or the daily steps), post-promo spend, reason with numbers. In "all at
   once" mode there is only **restore at once**: name, now -> target, reason "按你的选择，不看表现
   直接复位", no performance columns.
4. **You decide**: lowered, changed again later, created during the promo.
5. **Skipped**: already at the pre-promo value; restored by schedule.

Store-level context in one line ("in batches by performance" only): pre-promo vs post-promo
daily sales and ACOS. If the store's
sales fell sharply after the promo and the drop sits in campaigns that are **not** spending
their budget, say plainly that budget is not the cause and suggest checking stock, buy box and
listing status - do not suggest raising budgets into it.

Then ask whether to preview the writes. The suggestion is a suggestion: the customer can drop
items, change a suggested pace, or stop at the list.

### Step 5 - Undo file, then write

1. **Plan file first - it is both the undo file and the resume state.** Before the first
   write, re-read the current value of every item about to change (`get_entity_metadata`) and
   give the user a file (CSV / Excel), one row per object + field:

   | Column | Content |
   |---|---|
   | `runId` | One id for this restore run (e.g. store + window + creation time) - an identifier only, never parsed for times |
   | `profileId`, `timezone` | The store and its IANA timezone (e.g. `America/Los_Angeles`) |
   | `staleCheckFrom` | The point from which "nobody else wrote since" is checked for rows not yet written. **Record it immediately before the first restore-list log query starts**, and use that one value for every row of the run - never the time the queries finished or the plan file was created, or a change made in between would be in neither the list nor the check. A change caught by both the list and the check stops that item, which is the safe side. ISO 8601 with offset, e.g. `2026-10-12T09:30:00-07:00` |
   | `objectType`, `writeRoute` | e.g. `campaignBudget` / `campaign+updateBudget`, `aiGroup` / `save_sp_sb_ai_managed_group` |
   | `internalId`, discriminators | Everything the write needs: `campaignType`, `matchType`, `businessType`, `aiGroupId`, `profileId` (string) ... |
   | `amazonId`, `name` | What the user sees |
   | `field` | e.g. `dailyBudget`, `targetType`, `topAdjustment` |
   | `prePromoValue` | The restore target |
   | `valueBeforeRun` | Current value before this run's first write - **the undo value** |
   | `steps` | Every planned value, in order (one entry for a one-time restore) |
   | `lastCompletedStep` | `0` at creation; the index of the last step confirmed by read-back |
   | `expectedCurrentValue` | What the object should hold now if nobody else touched it - **`valueBeforeRun` at creation** |
   | `writtenAt` | When the last step was written, ISO 8601 with offset like `staleCheckFrom` (empty at creation) |
   | `writeResult`, `readBackValue` | Outcome of the last write (`ok` / `failed` / `ambiguous`) and what read-back showed |
   | `status` | see the state table below; `planned` at creation |

   **Update the file after every write and read-back, and hand the updated file back to the
   user.** MCP keeps no state between conversations: the next day's "继续复位" works only from
   this file (or, in the same conversation, the latest version of it). If the user cannot
   provide it, say the run cannot be resumed reliably and rebuild a fresh restore list
   instead.

   **Row states and what the next run does with each:**

   | `status` | Next action |
   |---|---|
   | `planned` | Not written yet (e.g. the first run stopped part-way). Stale check, show it again, write step 1 once confirmed |
   | `inProgress` | Stale check, then write step `lastCompletedStep + 1` |
   | `needsReadBack` | The last write came back `ambiguous`. Read back first: the value equals the step written -> count that step as done (`inProgress` or `done`); equals `expectedCurrentValue` -> it did not apply, back to the previous state; anything else -> `stoppedChangedByOthers` |
   | `failed` | Read back, show the user what happened, write again only after they confirm |
   | `done` | Last step confirmed by read-back. Nothing to do |
   | `stoppedChangedByOthers` / `skipped` | Nothing to do unless the user asks for that item specifically |

   "撤回刚才的复位" = write `valueBeforeRun` back for every row with `lastCompletedStep > 0`,
   through the same stale check, preview and confirmation - an undo must not overwrite a
   change made after this run either.
2. **Stale check - before every write, including resumed steps and undo.** Two conditions,
   both required:
   - **The value matches.** The current value equals `expectedCurrentValue`, compared as
     numbers at the field's precision (`"50"`, `"50.0"` and `"50.00"` are equal; money to the
     currency's minor unit, placements to whole percent on SB, `targetType` as an integer).
   - **Nobody else wrote since.** Query the log for this object and field from `writtenAt` (or
     `staleCheckFrom`, for a row never written) to now. Both times carry an offset, so convert
     them to the clock of the rows you compare against: store-local for ad-entity rows on a
     single-profile query, **UTC for managed-group rows**. The log's `dateStart` takes a date
     only - query from that day and drop earlier rows by timestamp. Remove the rows this
     run produced - same field, `newValue` equal to a step this run wrote, at its
     `writtenAt` (writes through MCP are logged under the user's own account, managed-group
     edits as `Manual`, so they look like human changes). **Any other human row -> stop**:
     set `stoppedChangedByOthers` and ask, even if the value has since been set back to the
     expected one - a change made and undone is still someone else's decision about that
     object.

   For a row that has not been written yet, also: if the current value differs from the
   log's last value, something changed it outside what the log shows - move it to "you
   decide".
3. **Write in this order**, each through its owning skill and its confirmation rules:
   managed-group settings (`sparkx-edit-ai-group`) -> budgets -> bids -> placements
   (`sparkx-edit-ads`). Split batches by `campaignType` (budget batches must be one type) and
   keep each under the write skills' caps.
4. **Today's step only.** For stepped items, write today's value; the later steps are a plan.
   MCP cannot schedule writes - the customer says "继续复位" on each following day. On that
   day **drive the work from the plan file, not from a fresh restore list**: handle every row
   by its `status` (table above), running the stale check before each write. Do not write a
   step twice on the same store day.
5. **Read back** every written object and update its row: `writeResult`, `readBackValue`,
   `writtenAt`; when the read-back shows the step's value, advance `lastCompletedStep`, set
   `expectedCurrentValue` to that value, and set `status` to `inProgress` (or `done` after the
   last step). An `ambiguous` result sets `needsReadBack`, never a completed step. Report what
   moved, what did not, and why.

A waiver ("这批直接执行") follows the owning write skill's waiver rules exactly - the scope is
what the user said, and the verification still runs.

## Example

> **客户**：把 Prime Big Deal Days 的调整复位一下。
>
> **AI**：先确认三件事：① 从店铺数据看，大促是 10/6–10/7，10/5 和 10/8 也有大量调整——这 4 天都算进来吗？② 复位方式：不看表现、全部直接复位，还是根据表现分批复位？③ 大促后还有延续的 Deal 或库存紧张的商品吗？
>
> **客户**：10/5–10/8 都算；根据表现分批；没有延续的 Deal。
>
> **AI**：10/5–10/8 你在亚马逊后台调整了 88 个活动的预算，结合 10/9–10/11 的表现：
> - **立即复位 16 个**：例如 Snacks-SP-Exact-Keyword，预算 $100 → $50，大促后 ACOS 119%，既超出店铺平时的 34–41%，也高于目标 41%。这 16 个大促后 3 天合计花了 $1,533。
> - **分几天回落 13 个**：例如 Noodles-SP-Exact-Keyword，$100 → $78 → $57 → $35，大促后转化率 13.9%，仍高于平时的 8.3–9.7%。
> - **一次复位 7 个**：表现正常或几乎没花钱。
> - **需要你决定 49 个**：4 个在 10/9 之后你又改过；45 个是大促期间被调低的，默认不加回去。
>
> 执行前我会先存一份撤销文件。要看预览吗？

## Output templates

### markdown

```markdown
# 大促调整复位 · {店铺}
**大促时间段**：{start} ~ {end}（{时区}）　**复位方式**：{根据表现分批 / 不看表现、全部直接复位}
{仅分批模式：**表现取数**：{post start} ~ {post end}}
**统计来源**：人工（邮箱账号）+ 亚马逊后台{+ 用户放宽的来源}
{数据不足、只覆盖部分、时间按 UTC 等说明}

## 总览
| 分组 | 数量 | 怎么处理 |
|---|---|---|
| 托管组设置复位 | {n} 个组 | 投放目的、目标 ACOS{、出价范围}改回大促前 |
| 立即复位 | {n} | ... |
| 分几天回落 | {n} | ... |
| 一次复位 | {n} | ... |
| 需要你决定 | {n} | 大促期间被调低 / 大促后又改过 / 大促期间新建 |
| 无需处理 | {n} | 已是原值 / 已由排期自动失效 |

{全部直接复位时：总览只有“托管组设置复位”“一次复位”“需要你决定”“无需处理”四行；不写整店参考；“一次复位”表去掉“大促后3天花费”列，理由写“按你的选择，不看表现直接复位”}

整店参考（仅分批模式）：大促前日均销售 {x}、ACOS {y}；大促后 {x2}、{y2}。

## 托管组设置复位
| 托管组 | 投放目的 | 目标 ACOS | 其他 |
## 立即复位
| 对象 | 现在 | 复位到 | 大促后3天花费 | 理由 |
## 分几天回落
| 对象 | 现在 | 每天复位到 | 大促后3天花费 | 理由 |
## 一次复位
| 对象 | 现在 | 复位到 | 大促后3天花费 | 理由 |
## 需要你决定
| 对象 | 大促前 | 现在 | 情况 |

---
_生成时间：{timestamp} · 数据源：SparkX AI MCP · Skill: sparkx-promo-reset v{version}_
```

Name every object by its name (`campaignName`, `aiGroupName`, keyword text), never by an
internal id; an export adds the **Amazon** id column (see the base skills' platform-notes ->
"Naming things in your answer").

### structured_report

```json
{
  "store": {"profileId": "...", "profileName": "...", "timezone": "..."},
  "window": {"start": "...", "end": "...", "clock": "store-local"},
  "mode": "performanceBased|allAtOnce",
  "postWindow": {"start": "...", "end": "..."},
  "sources": ["email", "Manual"],
  "amazonSideSources": ["Amazon Console"],
  "groups": [{"aiGroupName": "...", "field": "targetType|acos|aiPersonality|bidRange|totalBudget|<action-space switch>", "now": "...", "restoreTo": "...", "basis": "..."}],
  "items": [{"objectType": "campaignBudget|keywordBid|targetBid|placement", "name": "...", "amazonId": "...",
             "now": 100, "restoreTo": 50, "steps": [75, 50], "suggestion": "restoreNow|stepDown|restoreOnce|hold|customerDecides|skip",
             "reason": "...", "postSpend3d": 0, "postAcos": null, "normalAcos": [34, 41], "targetAcos": 41}],
  "storeContext": {"preDailySales": 0, "postDailySales": 0, "preAcos": 0, "postAcos": 0}
}
```

With `mode: "allAtOnce"`: `postWindow` and `storeContext` are `null`; each item's
`postSpend3d`, `postAcos`, `normalAcos` and `targetAcos` are `null`, while `steps` keeps its one
step (the pre-promo value, e.g. `[50]`) like any restore-at-once item, so the result feeds the
plan file, resume and read-back directly; `suggestion` is
only `restoreOnce`, `hold`, `customerDecides` or `skip`; the `reason` of a restored item says
the user chose to restore without judging performance.

In **either** mode, an item whose `changedBy` is `Amazon Console` carries `suggestion` =
`customerDecides` regardless of what its performance would otherwise suggest, and its
`reason` says the change came from Amazon's side with no known author. In the JSON result
those rows' sources are listed under `amazonSideSources`, separate from `sources`.

## Data boundaries

- **Only what the log recorded.** A change made where the log does not see it, or before the
  log's 15-month lookback, cannot be restored from here.
- **SB placement writes switch the campaign to custom bidding** (`bidOptimization=false`) as a
  side effect - say so before writing an SB placement (see `sparkx-edit-ads`
  `references/write-campaign.md`). Where AI placement bid optimization is on, a restored
  placement value may not be what ends up live.
- **Bids under AI management may not stick.** A human bid change on a keyword in a running
  managed group can be re-optimised by AI after it is restored; say so for those rows.
- **Inventory is a current snapshot**, and only for Seller profiles with SP-API authorisation.
  FBA quantity `0` is not proof of a stock-out (a merchant-fulfilled offer can still sell) -
  report it as a lead, not a cause.
- **Ranges come from the store's data; some cut-offs are adjustable defaults.** Normal ranges
  and target ACOS are computed from the store; click minimums, the 1.5x / 2x step cut-offs,
  the low-stock and binding-budget rules are default rules of thumb (listed in
  [`pacing-rules.md`](references/pacing-rules.md)) -
  show the numbers so the customer can override.
- **No scheduling.** Stepped restores need the customer to come back each day.

## Error handling

| Situation | Handling |
|---|---|
| Log `truncated: true` / `hasNextPage: true` | Page (single entity) or split the window - see the operation-log skill. Never build the list from a partial log |
| No human change found in the window | Say so, show which sources and dates were searched, offer to widen the window or the sources. Empty managed-group history while groups are still on 活动冲量 = the query failed, not "nothing changed" |
| An item's current value differs from the log's last value | Move it to "you decide" (Step 5.2) |
| A write is refused or `ambiguous_write` | Follow the owning write skill: do not retry blindly, read back, report |
| Fewer than 5 usable 3-day windows before the promo | Use the store-level normal range and say so ([`pacing-rules.md`](references/pacing-rules.md)) |

## Not covered

- Preparing a promo (raising bids / budgets, setting up schedules) - use `sparkx-edit-ads`
  and `sparkx-create-ai-group` / `sparkx-edit-ai-group` (dated schedules).
- Undoing AI or automation-rule changes.
- Campaign / keyword on-off states (first version covers bids, budgets, placements and
  managed-group settings only).
- Ad group default bids: found and listed with their pre-promo value, but there is no MCP
  write route for them - the user changes them in the platform.

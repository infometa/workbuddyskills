# Analytics Overview

Use this page as the entry point for any analytics task. The deeper references on this page are read on demand.

## When to Use

Enter the analytics path when a course author or admin asks about:

- learner count, completion rate, stuck lessons, recent activity
- orders, revenue, refunds, payment-channel distribution
- ratings, listen-vs-read preference
- follow-up Q&A counts or specific learner conversations
- follow-up Q&A volume by lesson
- credit consumption (per-charge detail / by day / by model / by scene / by usage type) — use `shifu-cli.py credit-detail` (the DSL `bill_daily_usage_metrics` table is currently empty in production until the daily aggregation cron is registered)
- which wallet absorbed the deduction for a given course
- audience profile distribution (goals, level, preferences)
- individual learner tracking — with the privacy rules in `privacy-and-presentation.md`
- **course title resolution** — "what is my course `<title>` currently called", "did I rename it", "is the draft title diverging from the published title" (use the Course Metadata recipes 0a–0c in `recipes.md`)

> Raw token counts are **not** exposed to creators. Any question about "how much was spent" maps to credits via `bill_daily_usage_metrics.consumed_credits`.

Do **not** enter the analytics path when the user asks only "how many courses do I have?" — that is a `shifu-cli.py list` call. **But** if the user names a course by title (e.g. "show me the data on 跟 AI 学 AI 通识"), resolve the current `shifu_bid → title` via Course Metadata recipes first, *then* run the downstream analytics — `shifu-cli.py list` is a draft snapshot and can leak historical / renamed titles.

## CLI-Only Rule

**All analytics operations go through `scripts/shifu-cli.py`. Never write raw HTTP, never read tokens directly, never handle the analytics endpoint's auth headers by hand.** The CLI is the single source of truth for authentication and transport; the agent's job is to translate a user question into a DSL JSON body and hand it to the CLI.

If you find yourself drafting a `POST` request or composing `Authorization: Bearer` / `Token:` headers, stop — use `analytics-query` instead.

## Workflow (3 Steps)

### Step 1 — Resolve the course

Run once per session to map `shifu_bid` ↔ course name:

```bash
python3 scripts/shifu-cli.py list
```

Cache the `shifu_bid → name` mapping in your context. The CLI's `list` output already exists for this purpose; do not call any analytics API for course metadata.

### Step 2 — Resolve the outline (only for course-level analysis)

When the query involves lesson-level dimensions (stuck lessons, lowest-rated lesson, lesson-by-lesson breakdown), fetch the outline tree:

```bash
python3 scripts/shifu-cli.py show <shifu_bid>
```

Cache `outline_item_bid → name` and `outline_item_bid → position` from the outline tree. Whenever a DSL result contains `outline_item_bid`, render it as "Lesson X.Y: <title>" before presenting. Skipping this makes outline-dimension numbers unreadable.

### Step 3 — Run the DSL query

```bash
python3 scripts/shifu-cli.py analytics-query <shifu_bid> --dsl '<json-body>'
```

Or, when the body is long or you want to reuse it:

```bash
python3 scripts/shifu-cli.py analytics-query <shifu_bid> --dsl-file query.json
```

The CLI injects `shifu_bid` into the body, handles authentication, and prints the full JSON response. The response shape on success is:

```json
{
  "code": 0,
  "data": {
    "columns": ["status", "n"],
    "rows": [[602, 124], [603, 87]],
    "limit": 100,
    "offset": 0
  }
}
```

Cross-course analysis: send one `analytics-query` per `shifu_bid` and merge results in the agent context (the endpoint does not support cross-course joins).

## Picking the Right DSL

1. Translate the user's question into a DSL body using `dsl.md` (syntax), `tables.md` (which table answers which question + which fields exist), and `recipes.md` (Course Metadata 0a–0c + 23 numbered scenario recipes).
2. Apply the privacy rules in `privacy-and-presentation.md` if the query touches `user_users`, `generated_content`, or `var_variable_values.value`.
3. Apply the Translation Gate in `privacy-and-presentation.md` before presenting any result.
4. **If the user mentioned a course by title**, run Course Metadata Recipe 0a / 0b first to confirm the current `shifu_bid → title` mapping. Never report a historical title as the course's current name.
5. **If the user asks about credit consumption**, use `shifu-cli.py credit-detail` instead of issuing a DSL query against `bill_daily_usage_metrics` — that table is empty in production pending the daily aggregation cron.

## Error Codes the CLI May Surface

The CLI prints the full response on every call. When the response carries a non-zero `code`, react as follows:

| Code | Meaning | Action |
|---|---|---|
| `0` | Success | Parse `data.columns` / `data.rows`, then apply the Translation Gate |
| `11001` | No access to this course | Confirm the `shifu_bid` is owned by the logged-in user; switch course or stop |
| `11002` | Invalid DSL | Re-check required fields, duplicate `alias`, or leading-wildcard `like` |
| `11003` | Table not in whitelist | Use one of the 10 tables in `tables.md` |
| `11004` | Field not in whitelist | Check field name or pick a different table |
| `11005` | Operator not in whitelist | Use one of the 12 operators in `dsl.md` |
| `11006` | Aggregate function not in whitelist | Use one of the 6 aggregate functions in `dsl.md` |
| `11007` | `limit` or `offset` out of range | `limit ∈ [1, 1000]`, `offset ≥ 0` |
| `1001` | User not found / token expired | Run `shifu-cli.py login` again to refresh the token |
| `1004` / `1005` | Token not logged in / expired | Same as `1001` — re-login |

The CLI exits non-zero on any of the above except `code == 0`, but the full payload is always printed first — read it, fix the DSL or guide the user to re-login, then retry.

## Scope Reminder

Each query is scoped to one `shifu_bid`. The endpoint does not support cross-course joins; merge across courses in the agent context, not in the DSL.

## Quick Question → Table Lookup

Before constructing any DSL, identify the correct table. Use this map:

| User asks about... | Table | Key filter | Key field |
|---|---|---|---|
| Learner count / completion / stuck lessons | `learn_progress_records` | `status = 603` (completed), `602` (stuck) | `outline_item_bid`, `status` |
| **Follow-up questions / Q&A** | `learn_generated_blocks` | **`type = 321`** (NOT `role = 2`!) | `type`, `generated_content` |
| LLM answers to follow-ups | `learn_generated_blocks` | `type = 322` | `generated_content`, `position` |
| Lesson ratings / read vs listen | `learn_lesson_feedbacks` | — | `score`, `mode` |
| Orders / revenue / payment channel | `order_orders` | `status = 502` (paid) | `paid_price`, `payment_channel` |
| Audience profile distribution | `var_variable_values` | — | `variable_bid`, `value` (aggregate only!) |
| Active learner count / archive rate | `shifu_user_archives` | `archived = 0` | `user_bid` |
| Credit consumption (by day/model/scene) | `bill_daily_usage_metrics` | `usage_scene = 1203` (learner production) | `consumed_credits`, `stat_date` |
| **Credit consumption (raw detail)** | **`shifu-cli.py credit-detail`** | `--scene 1203` | CLI command, NOT a DSL query |
| Look up learner nickname | `user_users` | — | `nickname`, `user_identify` |
| Current course title | `shifu_published_shifus` | `deleted = 0` (auto-injected) | `title` |
| Draft course title | `shifu_draft_shifus` | `deleted = 0` (auto-injected) | `title` |

> **Two credit paths**: `bill_daily_usage_metrics` for daily aggregated trends via DSL; `shifu-cli.py credit-detail` for raw per-usage detail (server-side join). They answer different questions — use the right one.

## Common Pitfalls (read this before your first query)

These are the mistakes that most commonly cause repeated failed queries and wasted time:

### Pitfall 1 — Follow-up questions: use `type = 321`, NOT `role = 2`

`role = 2` (learner) matches ALL learner input widgets — follow-up questions, form inputs, phone numbers, verification codes. To count follow-up questions specifically, filter `type = 321` (`mdask`). This is the single most common analytics mistake.

```json
// WRONG — includes form inputs, phone numbers, etc.
{"where": [{"field": "role", "op": "=", "value": 2}]}

// CORRECT — only actual follow-up questions
{"where": [{"field": "type", "op": "=", "value": 321}]}
```

### Pitfall 2 — Credit queries: `credit-detail` vs `bill_daily_usage_metrics`

These are **different tools for different questions**:
- `shifu-cli.py credit-detail <bid>` — raw per-usage detail, server-side join, **always works**. Use for "how many credits did I spend", "what did my learners cost me", per-lesson breakdown.
- DSL against `bill_daily_usage_metrics` — daily aggregated trends by model/scene/type. **Currently empty in production** (cron not registered). Do not use for credit data — it always returns zero rows.

### Pitfall 3 — `where` must be an array, not a single object

The DSL requires `where` to be an array of filter objects:

```json
// WRONG — server rejects with 11002
{"where": {"field": "type", "op": "=", "value": 321}}

// CORRECT — always an array
{"where": [{"field": "type", "op": "=", "value": 321}]}
```

### Pitfall 4 — Table name guessing

Do not guess table names — the schema has 10 tables and many sound-alike names. Always check the full list in `tables.md` first. Common wrong guesses:
- "user logs" or "user_logs" → does not exist. Use `learn_generated_blocks` for interaction data, `learn_progress_records` for progress data.
- "billing" or "usage" → `bill_daily_usage_metrics` (currently empty) or `shifu-cli.py credit-detail` for actual credit data.

### Pitfall 5 — Missing `outline_item_bid` in output

When querying lesson-level data (stuck lessons, follow-ups per lesson, ratings), you must run `shifu-cli.py show <shifu_bid>` first to build the `outline_item_bid → name` mapping. Showing raw `outline_item_bid` hashes to the user is unreadable and violates the Translation Gate.

## What Lives Where

- `dsl.md` — DSL grammar (operators, aggregates, constraints, per-learner guard rail, auto-applied filters, creator-scoped metadata tables)
- `tables.md` — the 10 tables, their fields, all code/enum translation tables, ID translation rules, the duplicate-row trap, the `role = 2 ≠ follow-up` trap, and the "course title is not history" rule
- `recipes.md` — ready-to-run DSL templates by scenario (Course Metadata 0a–0c, then 23 numbered scenario recipes including follow-up four-key pairing and follow-up per lesson)
- `privacy-and-presentation.md` — `user_users` / `generated_content` / `var_variable_values` privacy rules, plus the Translation Gate for user-facing output

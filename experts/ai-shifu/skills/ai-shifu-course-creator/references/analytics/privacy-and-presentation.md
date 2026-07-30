# Privacy & Presentation

Two concerns: the privacy rules baked into the endpoint (refusals, audits, masking) and the Translation Gate that every result must pass before reaching the user.

## Required References

None.

## `user_users` — Restricted Access

`user_users` is a **global** user table with two legitimate uses:

- **Use A** — translate a known pseudonymous `user_bid` to a display nickname.
- **Use B** — given a learner's phone number or email, reverse-look up their `user_bid`, then query other tables with it.

Any violation of the rules below returns `11002` (`invalidDsl`):

1. `select` may only include `{user_bid, nickname, user_identify}`. `avatar` / `name` / `birthday` are **permanently off-limits** — refuse any request for these.
2. `where` must include one of these anchor filters (unconditional listing of all users is prohibited):
   - `user_bid`: `op` must be `=` or `in` (no `like`, no range)
   - `user_identify`: `op` must be `=` (exact phone/email match only; `in`, `like`, and range are **prohibited** to prevent bulk enumeration)
3. `limit ≤ 50`
4. `group_by` and aggregates are **not allowed**
5. Server-side audit: `user_id + shifu_bid + filter type + timestamp`
6. Automatic privacy handling on returned rows:
   - `nickname`: **full redaction** — replaced with `[REDACTED-PHONE]` / `[REDACTED-EMAIL]` / `[REDACTED-IDCARD]` when a phone, email, or ID number is detected in the original value
   - `user_identify`: **masked** — first and last characters retained, middle replaced with `*****` (phone: `138*****000`, email: `te*****@example.com`)

### Use A — look up nickname by `user_bid`

Collect `user_bid` values from another query first, then resolve names in one batch:

```bash
python3 scripts/shifu-cli.py analytics-query <bid> --dsl '{
 "table":"user_users",
 "select":["user_bid","nickname"],
 "where":[{"field":"user_bid","op":"in","value":["u-bid-1","u-bid-2","u-bid-3"]}],
 "limit":50
}'
```

Returns:

```json
{
  "columns": ["user_bid", "nickname"],
  "rows": [
    ["u-bid-1", "Python 学徒"],
    ["u-bid-2", "[REDACTED-PHONE]"],
    ["u-bid-3", "Alice"]
  ]
}
```

### Use B — reverse-look up `user_bid` from a phone number

```bash
python3 scripts/shifu-cli.py analytics-query <bid> --dsl '{
 "table":"user_users",
 "select":["user_bid","nickname","user_identify"],
 "where":[{"field":"user_identify","op":"=","value":"13800138000"}],
 "limit":1
}'
```

Returns:

```json
{
  "columns": ["user_bid", "nickname", "user_identify"],
  "rows": [["u-bid-xxx", "Python 学徒", "138*****000"]]
}
```

Once you have the `user_bid`, use it to query `order_orders` (purchase status), `learn_progress_records` (learning progress), `learn_generated_blocks` (follow-up questions), etc.

Even when the nickname is redacted, **never paste the raw `user_bid` in user-facing output.** Continue using ordinals ("Learner A / Learner B") with the nickname appended: `Learner A (Python 学徒)`, `Learner B (redacted)`, `Learner C (Alice)`.

## `learn_generated_blocks.generated_content` — Selective Access

The conversation/content text column is selectable **only** for types `[301, 311, 312, 321, 322]` — system narration, Markdown narration, interaction prompts, learner follow-up questions, and Teaching Agent answers to follow-ups.

Hard rules (any violation → `11002`):

1. `where` must carry a `type` clause with values **only from** `[301, 311, 312, 321, 322]` using `op = "="` or `op = "in"`
2. `limit ≤ 100`
3. Every access is audited server-side (`user_id + shifu_bid + types + limit`)

The remaining `type` values — `303` input, `309` phone, `310` checkcode and similar widget types — contain learner PII and are blocked at the protocol level. Use aggregation templates (Recipes 17, 18, and 23) by default and fetch raw content only when specifically reviewing follow-up conversations (Recipes 19–22).

## Course title is not history — hard rule

When the user names a course by title and asks for data, resolve the **current** `shifu_bid → title` mapping before issuing any downstream query (Course Metadata Recipes 0a / 0b). Historical / renamed titles are never reported as the current name, and `shifu-cli.py list` (drafts only) is not a substitute. Full rule, failure modes, and required phrasing: `tables.md` → "Course title is 'current published', not 'history'".

## `var_variable_values.value` — Aggregate-Only

Learners may enter free-text personal information into course variables. Aggregate only (`group_by value count`); never paste the raw value list to the user. Recipe 15 shows the canonical safe pattern.

## Refusals

Refuse with a short explanation when:

- The user asks for a learner's phone, email, real name, ID number, birthday, or avatar — only the 36-char pseudonymous `user_bid` and the redacted `nickname` / masked `user_identify` are available.
- The user asks for an unconditional listing of all users (no anchor filter) — `user_users` requires `user_bid` or `user_identify` anchor.
- The user asks for raw learner input from widget types `303` / `309` / `310` etc. — these are inaccessible.

## Translation Gate (mandatory before any answer)

Pass every result through these checks before showing it to the user:

1. **Integer / string enums** (status, type, scene, mode) → translate via the code tables in `tables.md`. Never show raw codes like `601`, `502`, `1101`, `"read"`.
2. **ID fields** → apply the ID Field Translation Rules in `tables.md`: never display a raw `*_bid`; `user_bid` → ordinal labels ("Learner A / B / C"); `outline_item_bid` → "Lesson X.Y: \<title\>"
3. **Monetary values** → add currency unit (¥/CNY/USD), 2 decimal places
4. **Timestamps** (`created_at`, `updated_at` etc.) → backend timestamps are UTC (treat values without an explicit offset as UTC); convert to the user's local-timezone readable format (`2026-05-12 14:23`); never show raw ISO timestamps. Convert using the machine's timezone rules; do not substitute a session-fixed numeric UTC offset (DST-observing zones shift), and never assume a timezone from the conversation language
5. **Ratios / percentages** → use percent form ("62%" not "0.623")
6. **Credits** → round to 2 decimal places (e.g. `154.05 积分`); take credit values only from `credit-detail` output (`credits` / `total_credits`) — never invent or re-derive them (`bill_daily_usage_metrics.consumed_credits` applies only once the daily aggregation cron is enabled)

### Bad example (do not answer like this)

> Course b9f4c2d8… `learn_progress_records`: `status = 602` has 34, `status = 603` has 8. Most stuck at `outline_item_bid = 2a8e1f…`.

### Good example

> **《Python 入门 30 讲》** currently has **34 learners in progress** and **8 who have completed** it (completion rate ≈ 19%). The most stuck point is **Lesson 3.1 "Decorators and Closures"**.
>
> Want to see a ranked breakdown of each learner's progress?

## Answer Structure

Write answer headings, narrative findings, interpretations, refusals, and drill-down offers in `resolved_target_language`. Keep table names, JSON/DSL fields, commands, raw enum codes, and ids as internal control data; present their translated human meaning according to the gate above.

1. **Numbers + plain language**: express results in ordinary language; all codes and IDs are already translated.
2. **One-line interpretation**: avoid raw data dumps — add a brief "what this means" judgement.
3. **Proactive drill-down offer**: based on the current result, suggest 1–2 follow-up questions the user might want to explore.

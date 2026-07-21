# Course Analytics

## Analytics

Post-deployment data queries on live courses. Trigger this section whenever a course author or admin asks about learner count, completion rate, stuck lessons, orders, revenue, ratings, follow-up Q&A volume, credit consumption, audience profile distribution, or individual learner tracking. For a one-glance course overview use Recipe 0d in `recipes.md`.

### CLI-Only Rule

**All analytics traffic goes through `scripts/shifu-cli.py`. Never write raw HTTP, never read tokens directly, never compose `Authorization` / `Token` headers by hand.** Two analytics commands cover the surface:

- `shifu-cli.py analytics-query <bid> --dsl '<json-body>'` — DSL queries against the 10 whitelisted tables listed in `tables.md`. The agent's job is to translate a user question into a DSL JSON body and pass it to the CLI.
- `shifu-cli.py credit-detail <bid> [--start … --end … --scene 1203 --usage-type 1101 …]` — all credit / spend questions. Do **not** issue a DSL query against `bill_daily_usage_metrics` for credit data (that table is empty in production until the daily aggregation cron is enabled). `--scene 1203` restricts to learner-driven spend (preview is `1202`, debug is `1201`).

### Workflow

1. **Resolve credentials** — complete `../authentication.md`.
2. **Resolve the course** — run `shifu-cli.py list` (or `shifu-cli.py find-title <keyword>`) to map `shifu_bid ↔ course name`. **If the user mentioned a course by title**, always resolve the *current* `shifu_bid → title` via Course Metadata recipes 0a / 0b in `recipes.md` before issuing downstream queries — `list` is a draft snapshot and can show stale or historical titles. Never report a historical title as the course's current name.
3. **Resolve the outline** (only for lesson-level dimensions) — run `shifu-cli.py show <shifu_bid>` to map `outline_item_bid → name / position`. Skipping this makes outline-dimension numbers unreadable.
4. **Run DSL queries** — `shifu-cli.py analytics-query <shifu_bid> --dsl '<json-body>'` (or `--dsl-file query.json` for long bodies).
5. **Translate before presenting** — pass every result through the Translation Gate in `privacy-and-presentation.md`. Never paste raw codes (`601`, `502`, `1101`), raw `*_bid` strings, or raw `user_bid` values in user-facing output.

### References

- `overview.md` — entry point, full workflow, question→table quick-lookup, error codes
- `dsl.md` — DSL grammar (operators, aggregates, constraints, per-learner guard rail, auto-applied filters, creator-scoped metadata tables)
- `tables.md` — the 10 tables, fields, all code/enum translation tables, ID translation rules, data traps, "course title is not history" rule
- `recipes.md` — Course Metadata 0a–0c, Course Overview 0d, + 23 numbered scenario recipes (including four-key follow-up pairing and follow-ups per lesson)
- `privacy-and-presentation.md` — `user_users` restricted access, `generated_content` whitelist, `var_variable_values.value` aggregate-only rule, Translation Gate, refusal rules

### Validation

- Token resolved through `../authentication.md`, not a hand-rolled lookup.
- When the user mentioned a course by title, the current `shifu_bid → title` was confirmed via Course Metadata Recipe 0a / 0b before the downstream query ran. Historical titles were never substituted for current ones.
- `shifu_bid` and outline mappings established before any course-level query.
- DSL body matches grammar in `dsl.md`; filters reflect the user's intent (e.g. `status = 502` for "paid", not `>= 502`).
- Credit consumption queries used `shifu-cli.py credit-detail` per the CLI-Only Rule above — never a DSL query against `bill_daily_usage_metrics`.
- Follow-up counts anchored on `type = 321` (not `role = 2`), relying on the API's auto-injected `status = 1` rather than an explicit clause.
- Translation Gate applied before the answer is shown.
- Privacy refusals honoured for inaccessible fields (phone, email, real name, ID number, avatar, birthday).
- When CLI output contains Chinese characters that appear garbled in the agent's Bash tool, write output to a UTF-8 file and read with the file-reading tool instead (see `../cli/cli-reference.md#cli-output--encoding`).
- Table name verified against the 10 whitelisted tables in `tables.md`. Never guess a table name — invalid names trigger `11003`.

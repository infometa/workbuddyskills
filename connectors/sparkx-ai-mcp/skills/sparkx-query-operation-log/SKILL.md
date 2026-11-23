---
name: sparkx-query-operation-log
description: >-
  Query SparkX AI platform operation logs: user and AI action history on ad entities.
  For tracking change history, auditing operations, troubleshooting issues.
  Keywords: operation log, change history, who changed what, bid adjustment records,
  budget adjustment, AI auto-adjustment, pause/enable records, operation audit,
  modification timeline, ad adjustment log
metadata:
  version: 1.3.7
---

# Query Operation Log Skill

## MCP Tool

This skill maps to MCP tool: **`get_operation_log`**. Required scope: `amazon_sa_ads_logs:read`.

Profile, tenant, and user scope are resolved from the authenticated bearer token. `profileIds` is **required** — always call `get_user_authorized_context` first to obtain authorized profile IDs, then pass one or more into `profileIds`. **Every requested ID must be authorized: one unauthorized value fails the entire call** with `invalid_params` / `Requested profileIds contain unauthorized values` — nothing is silently dropped (see Platform-Wide Rules below). If the user didn't specify a store, pass **all** authorized `profileIds`. Never pass `tenantId` or `userId`; the server derives them from the token.

**⚠️ On this tool, how many `profileIds` you pass also changes the timezone of the timestamps you get back.** Read "createdDate Timezone" below before you report any time to the user.

**`userContext` (required)**: Must pass a non-empty string on every call. Preserve the user's original query as much as possible, plus the agent's reason for calling this tool. Summarize if too long, max 100 characters.

## Platform-Wide Rules

**Before using this tool, read [`references/platform-notes.md`](references/platform-notes.md)** — it covers auth flow, permission scopes, error handling, pagination/date-limit tables, currency rules, the tool-selection decision tree, and implicit inference rules shared across all 3 read tools. That file ships inside this same skill folder, so it travels with this skill regardless of how it's packaged/installed. This SKILL.md only covers what's specific to `get_operation_log`.

## ⚠️ Two Pagination Modes (decided by `entities`)

`get_operation_log` behaves in one of two modes depending on `entities`. This is the most important thing to get right.

**Mode A — Real pagination** (when `entities` is explicitly set to **exactly one non-`aiGroup` entity**, e.g. `["campaign"]`):
- Supports `page` (1-based, default 1) + `pageSize` (default 100, max 1,000). Response includes `page`, `pageSize`, `hasNextPage`.
- **To get the complete history, loop `page` (incrementing each call) while `hasNextPage=true`.** This is the preferred way to retrieve a complete change history for one entity type — no date-splitting needed. (`hasNextPage` is the real-pagination equivalent of `truncated`.)

**Mode B — limit-only** (when `entities` is empty/omitted, has **multiple** entities, or is **only `aiGroup`**):
- `page` is ignored. A single call returns at most `pageSize` rows (default 100, max 1,000; **`aiGroup`-only max 10,000**), sorted on the raw timestamp string (newest-first only when every row shares one clock — see Shared Rules). Response includes `limit` and `truncated`.
⚠️ **The cap is small relative to how fast the log grows.** In an account where AI is
active, machine rows alone can run into the hundreds per hour (measured: ~530/h in one
store), so **a full day of AI activity does not fit in one call and often not in a day's worth
of sub-windows either**. Before promising a customer "every change in the last N days", check
the volume first with a narrow probe window and say plainly what period can actually be
enumerated. For an AI-activity question, prefer narrowing by `resourceIds` (`aiGroup` is the one
filter that reliably narrows) over trying to page the whole account.

⚠️ **Rows keep arriving for about two days after the fact.** The log backfills, so the same
query for "yesterday" can return more rows tomorrow than it does today. A count is a count **as
of when you ran it** — say so when the number is the answer ("47 changes as of 10:20 today"),
and never present a recent-day count as settled. Re-running an older window is the way to
confirm it has stopped moving.

- `truncated=true` means more matched than could be returned. **You cannot page.** Handle it in this order:
  1. **Prefer steering the user to a single entity.** If they really only care about one kind of change ("just budget changes", "just campaign pause/enable"), guide them to narrow `entities` to a single non-`aiGroup` entity → this switches to Mode A, where you can page through the complete set. Only do this when it matches the user's actual intent; if they genuinely want the full cross-entity history, don't silently narrow — say the result is a partial view.
  2. **Split the date range** into non-overlapping sub-windows and recurse (see "Getting a Complete Count" below).
  3. **Add filters** (`resourceIds`/`actionType`/`operationType`/`changeBy`) as a last resort — this changes *what* you're searching for, so flag the result as partial when you do.
  4. `aiGroup` is inherently limit-only (but its 10,000 cap is usually enough for a window).

## When to Use

Use this tool when the user needs any of the following:
- Query ad operation history
- Find out who made what changes (manual vs AI)
- Track AI auto-adjustment records (bid, budget, etc)
- View bid/budget adjustment history
- Audit a specific campaign's change timeline
- Troubleshoot ad status changes (pause, enable, archive)
- Count how many changes of a given type happened, grouped by operator or entity (do this by pulling rows and aggregating client-side — the tool itself has no server-side `groupBy`)

See the Tool Selection Decision Tree above if the user's ask might belong to `get_ads_perf` or `get_entity_metadata` instead.

## Explaining a Historical Automated Change

For questions such as "why did AI change this bid?" or "which mechanism changed this budget?",
separate historical evidence from current configuration:

1. Resolve the named entity first with `get_entity_metadata` and preserve the correct internal
   and Amazon ids. `resourceIds` for campaign/ad group use Amazon ids; `aiGroup` uses its internal id.
2. Query the narrowest single entity and date window that contains the event. Fully paginate Mode A;
   for Mode B, split non-overlapping windows until `truncated=false` or disclose the lower bound.
3. Report the log facts exactly: timestamp with its real timezone, previous/new value,
   `changedBy`, `operationSource`, `operationType`, and `aiGroupScheduleId` when present.
4. If the row belongs to an AI-managed campaign, read the campaign's **current** controller inventory
   using `sparkx-query-entity-metadata` (campaign, `aiGroup`, `aiGroup_schedule`, and campaign
   `automationRule`). This answers what can still act now, not what was necessarily configured at
   the historical timestamp.
5. Use three evidence levels in the answer:
   - **Confirmed historical fact**: fields present on the matching log row;
   - **Current configuration context**: mechanisms and configured limits effective now;
   - **Not available from MCP**: the model inputs/reasoning used for that historical AI decision,
     a historical point-in-time config snapshot, an exact hidden trigger threshold, or a guaranteed
     next execution time unless a returned rule/schedule explicitly supplies it.

An `aiGroupScheduleId` links an operation to a schedule. A null value does not prove there was no
scheduled influence unless the operation contract for that row guarantees the field. Likewise,
`changedBy=AI` identifies the actor class, not the model's causal explanation. Never use today's
bid range or rule configuration as proof of the ceiling or trigger that applied on the event date.

## DSL Parameter Format

```json
{
  "userContext": "User's original query + agent's reason for calling",
  "dateStart": "YYYY-MM-DD",
  "dateEnd": "YYYY-MM-DD",
  "profileIds": [1234567890123456],
  "entities": ["entity_type_list"],
  "resourceIds": [{"idEntity": "campaign", "ids": [123456]}],
  "changeBy": {"operator": "IN", "values": ["ai", "automation"]},
  "actionType": {"operator": "IN", "values": ["Bid Increased"]},
  "operationType": {"operator": "IN", "values": ["Campaign Paused"]},
  "campaignTypes": ["campaign_type_list"],
  "targetTypes": ["target_type_list"],
  "placementTypes": ["placement_type_list"],
  "page": 1,
  "pageSize": 100
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| profileIds | array[long] | **Yes** | — | Profile IDs from `get_user_authorized_context` -> `profiles[].profileId`. **All must be authorized** — one unauthorized value fails the whole call; there is no silent intersection |
| dateStart | string | **Yes** | — | Start date `YYYY-MM-DD`. Max span vs `dateEnd` is 90 inclusive calendar days (see platform-notes.md for the precise off-by-one-safe definition); cannot be more than 15 months before today |
| dateEnd | string | **Yes** | — | End date `YYYY-MM-DD` |
| userContext | string | **Yes** | — | User's original query + reason, max 100 chars |
| entities | array[string] | No | all entities except `audience` | Entity type filter |
| resourceIds | array[object] | No | — | Resource ID filter (see below) |
| changeBy | object | No | — | Operator filter (see below) |
| actionType | object | No | — | Action type filter — coarse-grained (see below). ⚠️ **Only use values from the [actionType enum table](references/field-reference.md#actiontype)** — do not invent or guess values |
| operationType | object | No | — | Operation type filter — fine-grained (see below). ⚠️ **Only use values from the [complete operationType table](references/field-reference.md#complete-operationtype-values-by-entity)** — do not invent or guess values |

> **Recommended strategy**: when unsure which exact `operationType` values to use, first query with `actionType` (coarse-grained) to explore results and identify the specific `operationType` values appearing in the returned rows, then follow up with `operationType` (fine-grained) for precise filtering.
| campaignTypes | array[string] | No | — | Campaign type filter |
| targetTypes | array[string] | No | — | Targeting type filter (see below) |
| placementTypes | array[string] | No | — | Placement type filter (see below) |
| page | int | No | 1 | Page number (1-based). **Only effective when `entities` is exactly one non-`aiGroup` entity** (Mode A); ignored for multi-entity or `aiGroup`-only queries (Mode B) |
| pageSize | int | No | 100 | Max rows per page (Mode A) / per call (Mode B). Non-`aiGroup` max **1,000**; **`aiGroup`-only max 10,000**. Results are sorted on the raw timestamp string, which is newest-first only within one clock |

## Parameter Details, ChangeLogVO Field Reference

**See [`references/field-reference.md`](references/field-reference.md)** for the complete parameter enum reference (entities, resourceIds, campaignTypes, changeBy, actionType, operationType, targetTypes, placementTypes) and the ChangeLogVO response field table.

## Response Structure

```json
{
  "isError": false,
  "toolName": "get_operation_log",
  "data": {
    "rows": [
      {
        "entity": "campaign",
        "entityName": "Brand-SP-Auto-US",
        "amazonEntityId": 298539385213868,
        "entityId": 298539385213868,
        "operationType": "DailyBudget Increased",
        "profileId": 4404871489220462,
        "aiGroupName": "Growth-Group-1",
        "amazonCampaignId": 298539385213868,
        "campaignName": "Brand-SP-Auto-US",
        "campaignType": "sponsoredProducts",
        "amazonAdGroupId": null,
        "adGroupName": null,
        "changeField": "dailyBudget",
        "previousValue": "50.0",
        "newValue": "65.0",
        "countryCode": "US",
        "currencyCode": "USD",
        "createdDate": "2024-06-15 14:30:00",
        "changedBy": "AI"
      }
    ],
    "rowCount": 1
  },
  "meta": {
    "limit": 100,
    "truncated": false,
    "effectiveProfileIds": [4404871489220462],
    "hint": "Limit conclusions to this query's scope. Missing fields are not zero, and empty results do not prove that no matching business data exists. Do not present partial or paginated results as complete. Distinguish returned facts from analytical inferences; state limitations or query further when evidence is insufficient."
  },
  "requestId": "a1b2c3d4e5f6"
}
```

**Everything is nested.** `rows` and `rowCount` live under **`data`**; pagination, currency and
hints live under **`meta`**. Only `isError`, `toolName` and `requestId` are top level. Reading
`response.rows` returns nothing - it is `response.data.rows`. `meta` keys are **omitted when
they do not apply** (not set to null). A successful read always has `meta.hint`: any
query-specific warning comes first, followed by the shared interpretation boundary.

The pagination fields differ by mode, and they all live under **`meta`**: **Mode A (real pagination)** gives `meta.page`, `meta.pageSize`, `meta.hasNextPage`; **Mode B (limit-only)** gives `meta.limit`, `meta.truncated` (as shown above). Rows are always `data.rows` and `data.rowCount`.

## ⚠️ `createdDate` Timezone (depends on entity + profileIds count)

**`createdDate` is not always UTC. Its timezone depends on which entity the row belongs to and on how many `profileIds` you passed.** Confirmed by testing (2026-08):

| Entity | profileIds count | `createdDate` timezone | Example |
|---|---|---|---|
| `aiGroup` (SP/SB) | one or many | **UTC** | `2026-08-24 05:58:50` |
| `aiGroup` (SD) | one or many | **downstream DB timezone — undocumented** | `2026-08-24 05:58:50` |
| `campaign` / `adGroup` / `target` / `placement` | **one** | **Store-local** | `2026-08-24 00:01:06` (LA time) |
| `campaign` / `adGroup` / `target` / `placement` | **many** | **UTC** | `2026-08-24 07:01:06` (UTC) |

Verified on one pause record for a US profile (`America/Los_Angeles`, UTC-7 in August):
- `profileIds: [4404871489220462]` → `"2026-08-24 00:01:06"`
- `profileIds: [4404871489220462, 2618208845223116]` → `"2026-08-24 07:01:06"`

Same event, 7 hours apart — exactly the LA daylight-saving offset.

### What you must do about it

1. **Always label the timezone when you show a timestamp.** "2026-08-24 07:01 UTC" or "2026-08-24 00:01 store time". An unlabeled timestamp from this tool is ambiguous by construction, and the ambiguity is a whole business day near midnight.
2. **Never merge or compare a single-profile result with a multi-profile result.** They're on different clocks. If you already pulled one store and then widen the scope, **re-pull** — don't stitch.
3. **Watch for mixed clocks inside one response.** `entities: ["campaign", "aiGroup"]` on a single profile returns store-local campaign rows *and* UTC SP/SB aiGroup rows in the same list — and SD aiGroup rows in the downstream DB's own timezone, which is documented nowhere. Rows are sorted on the raw timestamp string, so a mixed-clock result is **not reliably chronological** — don't present it as an ordered timeline, and don't compute "X happened before Y" across entity types.
4. **Pick the mode deliberately:**
   - The user wants times they can match against their Amazon console → query **one profile at a time**, restrict `entities` to ad entities (`campaign`/`adGroup`/`target`/`placement`), and label the output store-local.
   - The user wants a comparable cross-store timeline → query **multiple profiles**, which puts **ad-entity rows** in UTC, or convert client-side using each row's `countryCode`, and label the output UTC. **Querying more profiles does not normalise managed-group rows**: SP/SB `aiGroup` rows are already UTC regardless, and SD `aiGroup` rows stay in the downstream DB's timezone and are still unplaceable. If the timeline must include SD managed-group history, say those rows could not be put on the same clock.
5. **Don't equate `createdDate` with the `dateStart`/`dateEnd` boundary.** Which zone the request-level filter uses is not documented, so a row can sit near the edge of your requested window in one clock and outside it in another. For boundary-sensitive questions ("what changed yesterday" on a non-UTC store), say results at the edges are approximate.
6. **Don't derive "AI acts at night" style conclusions from raw timestamps** without first pinning down which clock you're in — an hour-of-day pattern computed on UTC rows for a US store is shifted by 7-8 hours.

The MCP layer does no conversion; this is how the log data itself is returned.

| Field | Type | Description |
|---|---|---|
| `isError` | boolean | Top level. Whether the call errored — check this before reading `rows` |
| `toolName` | string | Top level |
| `data.rows` | array[ChangeLogVO] | Log entries, sorted on the **raw timestamp string**. With one clock that is newest-first; across mixed clocks it is **not** a reliable chronology — see platform-notes |
| `data.rowCount` | int | Number of rows returned on this page/call |
| `meta.page` / `meta.pageSize` | int | **Mode A only.** Current page and page size |
| `meta.hasNextPage` | boolean | **Mode A only.** `true` → fetch `page+1` to continue; loop until `false` for the complete set. (Semantically equivalent to Mode B's `truncated`) |
| `meta.limit` | int | **Mode B only.** The `pageSize` cap actually applied |
| `meta.truncated` | boolean | **Mode B only. `true` means more matched than `limit` could return.** You cannot page — steer the user to a single entity (→ Mode A), else split the date range into non-overlapping sub-windows, else add filters as a last resort (flagging the result as partial) |
| `meta.hint` | string | Always present on success. Truncation guidance, when applicable, precedes the shared interpretation boundary |
| `meta.effectiveProfileIds` | array[long] | Profile IDs the query ran against — an echo of your request (unauthorized IDs fail the call outright) |
| `requestId` | string | **Top level.** Trace ID — quote it when reporting a failure to the user. May be absent locally |
| `meta.currency` | string | Optional roll-up of the rows' currencies: a single code if all rows agree, the literal **`"mixed"`** if they don't, absent if no row carries one. **`"mixed"` is not a currency** — fall back to each row's `currencyCode`, and never sum or format amounts across a mixed result |

On error, the response instead follows the shared error envelope described in Platform-Wide Rules above (all errors use a single top-level `errorType`, tool and pipeline alike, e.g. `rate_limited`).

## Getting a Complete Count (handling large result sets rigorously)

There is no server-side `groupBy` for this tool — to answer "how many budget changes did each operator make" or "count of placement adjustments per campaign" **completely and correctly**, first pull the complete row set, then aggregate client-side. How you get the complete set depends on the mode:

**If you can scope to a single non-`aiGroup` entity (Mode A) — preferred:** loop `page` (incrementing each call) while `hasNextPage=true`, collecting rows; raise `pageSize` toward the max (1,000) to cut round trips. Once `hasNextPage=false` you have the complete set — aggregate and you're done. No date-splitting needed.

**Otherwise (Mode B: multi-entity or `aiGroup`-only) — use date-splitting:**
1. Issue the query with your filters and check `truncated`.
2. **If `truncated=false`**: the rows are complete for that window — aggregate client-side and you're done.
3. **If `truncated=true`**: split the date range into two **non-overlapping** sub-windows (bisect at the midpoint, second half starting the day after the first half ends — never share a date), and recursively repeat on each half.
4. Only sum/merge counts across **non-overlapping** sub-windows — overlapping ranges double-count.
5. **If a single day still returns `truncated=true`** on its own (more than the cap — 1,000, or 10,000 for `aiGroup`-only — in one day for your filters), this tool **cannot guarantee a complete count** for that day. Don't report a partial number as exact — tell the user it's a lower bound (e.g. "at least 1,000 changes on 2024-06-15; can't return an exact count for a single day this active") and suggest scoping to a single entity (Mode A) or narrowing by `resourceIds`/`operationType`.

## Examples

**Query last 7 days of AI auto-adjustment records:**
```json
{
  "profileIds": [4404871489220462],
  "dateStart": "2026-07-13",
  "dateEnd": "2026-07-19",
  "changeBy": {"operator": "IN", "values": ["ai"]},
  "pageSize": 100,
  "userContext": "Last 7 days of AI auto-adjustments"
}
```

**All operations on a specific campaign (resolve name to ID first via get_entity_metadata, then):**
```json
{
  "profileIds": [4404871489220462],
  "dateStart": "2026-06-01",
  "dateEnd": "2026-06-30",
  "resourceIds": [{"idEntity": "campaign", "ids": [298539385213868]}],
  "pageSize": 1000,
  "userContext": "Full change history for this campaign"
}
```

**Budget increases made by people (not AI/automation):**
```json
{
  "profileIds": [4404871489220462],
  "dateStart": "2026-06-01",
  "dateEnd": "2026-06-30",
  "entities": ["campaign"],
  "actionType": {"operator": "IN", "values": ["Budget Increased"]},
  "pageSize": 1000,
  "userContext": "Budget increases made by people this month"
}
```
No `changeBy` filter: `manual` is **rejected by the server**, and it never covered changes
recorded under a user's email anyway (see [`field-reference.md`](references/field-reference.md) ->
changeBy). Keep rows whose `changedBy`
is an email or `Manual` (`Amazon Console` is a source, not a person), and whose `changeField` is `dailyBudget` - in AI
managed groups, AI's hourly `currentBudget` rows also land under `Budget Increased`.

## Notes

- **`operationType` and `actionType` are closed enums** — you MUST only use values listed in [`references/field-reference.md`](references/field-reference.md). Never invent, guess, or interpolate values. If unsure whether a value exists, consult the reference table before sending the request. Values are English display strings (e.g. `"DailyBudget Increased"`, `"Campaign Paused"`) — pass them exactly as listed, case-sensitive
- `dateStart`/`dateEnd` request params use `YYYY-MM-DD`; `createdDate` in returned rows is a full timestamp — **but its timezone varies** (SP/SB `aiGroup` = UTC, SD `aiGroup` = the downstream DB's timezone and therefore unknown; ad entities = store-local for one `profileId`, UTC for several). Always label the zone, never merge single- and multi-profile results, and treat a mixed-entity result as not reliably chronological. See "createdDate Timezone" above
- `dateEnd` must be equal to or later than `dateStart`
- Max date span is 90 days, max lookback is 15 months — these are hard limits, not auto-truncation. Split longer windows into multiple calls
- **Pagination has two modes (decided by `entities`)**: a single non-`aiGroup` entity → real pagination (`page` + `pageSize`, loop until `hasNextPage=false`); multi-entity or `aiGroup`-only → limit-only (`pageSize` caps the call, max 1,000 / `aiGroup` 10,000, check `truncated`). For a complete count in limit-only mode, prefer steering to a single entity, otherwise use the non-overlapping date-split procedure above
- When `entities` is not specified, returns operations on all entity types **except `audience`**
- `profileIds` is **required**. Always call `get_user_authorized_context` first. If the user doesn't name a store, pass all authorized `profileIds` — but note this also switches ad-entity timestamps to UTC (see above)
- **Every requested `profileId` must be authorized** — one bad value fails the whole call (`Requested profileIds contain unauthorized values`); nothing is silently dropped
- `pageSize` on this tool is **clamped** silently (over the max → capped, no error). This differs from `get_ads_perf`/`get_entity_metadata`, where an out-of-range `pageSize` is an error
- `changeBy`, `actionType`, and `operationType` must be passed as objects with explicit `operator`/`values` (not bare arrays). **Incomplete filters are rejected with `invalid_params`** (no longer silently ignored): a missing `operator`, or `values` that is `null` / an empty array / all-`null`, all fail — build the full `{"operator": "IN", "values": [...]}` object or omit the filter entirely.
- **`resourceIds` is strictly validated too**: each item must be an object with `idEntity` and an `ids` array of numbers — a missing `idEntity`, a non-numeric ID, or a non-array `ids` returns `invalid_params` (previously such items were silently dropped, e.g. "3 IDs requested, only 2 queried"). **Exception:** an explicit `ids: null` is a *reserved* value meaning "no ID restriction" (different from `[]`, which means the scope genuinely has no results) — it is accepted, not rejected.
- To find a resource by name (campaign name, keyword text, ASIN) rather than ID, resolve it first via `get_entity_metadata`, then pass the ID into `resourceIds`
- No server-side aggregation (`groupBy`) — aggregate client-side after pulling rows, splitting non-overlapping date windows whenever `truncated=true`
- When `profileIds` spans multiple stores, map each row's `profileId` to a `profileName` before describing results
- Amounts in `previousValue`/`newValue` are always local currency — read the row's `currencyCode`, don't assume USD. The optional top-level `currency` may be the literal `"mixed"` on cross-store results; that's a marker, not a currency
- `placementTypes` has exactly 4 confirmed values — don't invent additional ones
- On error, check `errorType` and handle per the guidance above (e.g. `rate_limited` means wait `retryAfterSeconds` before retrying, not that the question is unanswerable)

## Reference Docs

- Shared cross-tool behavior (auth, errors, pagination, dates, currency, decision tree, inference rules): [`references/platform-notes.md`](references/platform-notes.md)
- Field dictionary (parameter enums, ChangeLogVO fields): [`references/field-reference.md`](references/field-reference.md)
- Enum i18n (ZH/EN/JA display labels for changeBy, actionType, operationType, entity — use this when presenting log entries to the user or translating between API values and localized display text): [`references/enum-i18n.md`](references/enum-i18n.md)
- Query examples:
  - [AI bid adjustment records (and how to broaden to all AI ops)](references/example-ai-bid-changes.md)
  - [All bid-change operations on a specific campaign](references/example-campaign-operations.md)
  - [SP budget changes (fine-grained filter)](references/example-user-budget-changes.md)
  - [Pause operations](references/example-pause-operations.md)
  - [Resolving a name to an ID before querying logs](references/example-resolve-name-to-id.md)

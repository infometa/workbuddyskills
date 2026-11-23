# Platform notes - managed-group write tools

Shared behavior for the managed-group write tools (`create_sd_ai_managed_group`,
`save_sp_sb_ai_managed_group`, `edit_sd_ai_managed_group`, `delete_ai_managed_group`,
`save_sp_sb_ai_group_schedule`) and the template read tool (`get_ai_group_template`).
This file ships inside each managed-group skill so it travels with the skill.

## Tool map

| Tool | What it does | Scope |
|---|---|---|
| `create_sd_ai_managed_group` | Create an SD managed group | `amazon_sa_managed_group:write` |
| `save_sp_sb_ai_managed_group` | Create or edit an SP/SB managed group (single or batch) | `amazon_sa_managed_group:write` |
| `edit_sd_ai_managed_group` | Edit SD managed groups (batch by `ids`) | `amazon_sa_managed_group:write` |
| `save_sp_sb_ai_group_schedule` | Create / update / delete SP/SB group schedules | `amazon_sa_managed_group:write` |
| `get_ai_group_template` | Read managed-group templates (list / detail) | `amazon_sa_managed_group:write` |
| `delete_ai_managed_group` | Delete (archive) a group, releasing or migrating campaigns | `amazon_sa_managed_group_delete:write` |

Two things worth noting: `get_ai_group_template` is a **read** operation that sits behind
the **write** scope (a read-only token cannot list templates), and delete has its own
separate scope — a token that can create/edit may still be unable to delete.

**Templates are read-only.** There is no MCP tool that creates, edits, or deletes a
template. `get_ai_group_template` reads them; the write tools *apply* one via `templateId`.
If a user asks to "save these settings as a template", tell them that has to be done in the
platform UI.

## Enforce the constraints yourself - for clear errors and to catch what slips through

When a user acts through the platform UI, the front end blocks invalid input (greys
out fields, hides unsupported options, caps ranges). **Through MCP, none of that UI
guarding runs.** Prod testing (2026-08-13) shows the backend now validates a lot on its
own - enum/type checks, ACOS/ROAS/personality ranges, `*Type`<->value companions, `ids`
size, profile authorization, `remark` length - and **rejects** those bad calls rather
than silently accepting them. That's good, but it isn't a licence to send sloppy input:
some combinations are still accepted unexpectedly or silently ignored (e.g. an
unsupported ad-type action-space switch on the wrong ad type), and a downstream
rejection is a worse experience than a precise up-front message.

Therefore: **treat the constraints in this skill as rules you enforce yourself, before
sending** - both to give the user a clear error and to catch the cases the backend
doesn't.

## Unsupported features -> tell the user, don't send

Some settings don't apply in a given context - a wrong ad type, an unsupported mode, or
a feature not available yet. **Several of these are now hard errors** rather than silent
no-ops, and the error arrives *instead of* any part of your write being applied:

- **SP-only action-space fields sent for an SB group** -> rejected, listing every offending
  field (`X is not supported for sponsoredBrands; remove it or set to 0`).
- **A non-SD group id sent to `edit_sd_ai_managed_group`** -> rejected with a pointer to
  `save_sp_sb_ai_managed_group`.
- **SP-only batch operations on a batch containing SB groups** -> rejected.
- **`optimizeType`, `acos`, or `aiPersonality` on a weekly (`timeType=2`) schedule** ->
  rejected; those are inherited from the parent group.
- **An SP/SB template whose harvest/negative rules are bound to specific campaigns/ad
  groups** (`isSelf=2` with `status=1`) -> rejected, because this tool can't carry those
  bindings: always on template create; on template edit only when `aiAutomation` is not
  passed (with `aiAutomation` the template's rules are ignored - confirm that change with
  the user first).
- **A group whose `campaignType` can't be determined on delete** -> rejected rather than
  guessed.

Others are still accepted-but-ignored. So the rule stands: **if the user asks for something
not supported in their context, tell them plainly and skip that field - never send it
silently and never present it as if it took effect.**

## Auth & scope

- Authenticate via bearer token. Always call `get_user_authorized_context` first to
  get authorized `profileId`s; pass only an authorized one.
- `tenantId` / `userId` / `userName` are injected server-side from the token - never
  pass or fabricate them.
- Writes require `amazon_sa_managed_group:write`. **Delete requires
  `amazon_sa_managed_group_delete:write`** - a token that can create/edit may still not be
  able to delete. See the tool map above.
- **A profileId outside the token's grant is rejected outright** (`profileId X is not
  authorized for the current user`) - nothing partial is applied. Take profile IDs verbatim
  from `get_user_authorized_context`.

## Response envelope

Success:
```json
{ "isError": false, "toolName": "<tool>", "requestId": "a1b2c3d4e5f6",
  "data": { "status": "success", "result": { "aiGroupId": 827136 } } }
```

Failure - **there are two shapes**, distinguished by whether the failure came from the tool
or from the surrounding pipeline:
```json
{ "isError": true, "toolName": "<tool>", "requestId": "a1b2c3d4e5f6",
  "errorType": "invalid_params", "message": "<message>", "recoveryHint": "<hint, if any>" }
```
```json
{ "isError": true, "errorType": "business_error", "service": "Amazon_SA_Service",
  "message": "<downstream message>" }
```

- Check `isError` first, then read the top-level `errorType`. All pipeline failures (`rate_limited`, `token_invalid`, `permission_denied`, `scope_missing`, `business_error`, `timeout`) and parameter/validation failures use `errorType`. A tool's own business failure instead carries a nested `data.error` (+ optional `data.recoveryHint`) — see "Errors" below.
- **The configured write budget is 20 calls/min** per tenant+tool and per user+tool (reads
  get 120); whether limiting is enabled is an environment setting, so treat it as a ceiling
  to plan against rather than something you can count on being off. A serial "write, read
  back, write, read back" loop over many groups can hit it - pace it, and on `rate_limited`
  wait `retryAfterSeconds` rather than retrying immediately.
- `requestId` is your support handle. **Quote it when reporting a failed write to the
  user.**
- When `recoveryHint` is present, use it and relay it to the user.

**Batch results are three-state - don't judge by `isError` alone.** A batch operation
can partially succeed and still come back with `isError:false`:

```json
{ "isError": false, "data": {
    "status": "partial_failure",
    "result": { "success": 1, "fail": 2 },
    "failedItems": [ { "aiGroupId": 1002, "error": "aiStatus is not on" } ] } }
```

`status` is `success` / `partial_failure` / (all-failed ->) `isError:true`. If
`failedItems` names the failures, derive and verify the succeeded set. If it is empty,
re-read every requested id because counts alone cannot identify which items succeeded.
Never present a partial result as full success.

## Errors: prefer the hint, but don't rely on it

The failure shape carries `data.error` and an optional `data.recoveryHint`, and the
batch layer translates some downstream codes into readable messages (e.g. "Budget must
be between 50 and 500", "Operation 'budget' requires: budgetType"). But **not every
error is populated with a useful hint** - some downstream business errors still come
back generic (e.g. `"业务执行错误"`, `"Resource Not Found"`), and parameter values are
validated downstream, not by the tool. So: get the request right the first time by
sticking to the documented fields/enums; relay `recoveryHint` when it's there, and don't
assume it always will be.

## Non-idempotent + 30s timeout

Create and SP/SB save are **non-idempotent** - each call creates/changes state. The
downstream call can take up to ~30s; on timeout the operation may already have
applied. **Always verify with a `get_entity_metadata(profileIds=[...],
entity='aiGroup', userContext='...')` read before retrying** - a blind retry can
create a duplicate group. (`get_entity_metadata` requires `profileIds`, `entity`,
`userContext` on every call.)

## Verify, don't trust the envelope

A `status: success` envelope does not by itself prove the intended state. Some edits
on an AI-running group can be silently skipped downstream. After any write, read the
group back with `get_entity_metadata(profileIds=[...], entity='aiGroup',
userContext='...')` and confirm the fields you set actually took the values you
expected.

### ⚠️ Read-back returns the *currently effective* config - a missing field is not a failure

`get_entity_metadata`'s `aiGroup` response is a projection, not the raw stored record. It is
first trimmed to what the group's `campaignType` supports, then reduced to what is actually
in effect:

- a switch that is **off** drops its dependent fields (turn `bidAdPlaceStatus` off and
  `tosMin`/`tosMax`/`pdpMin`/`pdpMax`/`rosMin`/`rosMax` disappear entirely);
- a rule running in **AI mode** is **omitted from `aiAutomation` altogether**. An empty
  `aiAutomation` is ambiguous by itself: pair it with the effective `aiActionSettings`
  switches to distinguish action spaces that are off from enabled action spaces in AI mode;
- a rule in **Rule mode** keeps its config but drops AI-only parameters.

So verify in this order:

1. Read back the **switch** you set and confirm its value.
2. Only then look for its dependent fields - and only expect them if the switch is on.
3. Treat "field absent under an off switch" as **expected**, never as evidence the write
   failed. Equally, don't diff two read-backs field-by-field and call every disappearance a
   regression: flipping one switch off legitimately removes a whole family of fields.

When you can't confirm a value because it isn't returned, say that plainly ("the switch is
off, so that parameter isn't in effect and isn't reported") rather than guessing at a stored
value or re-sending the write.

For multiple writes against the same object set, execute serially and read back after
each call. Never run dependent writes concurrently. When operation-log read access is
available, also verify the resulting audit entry; `changedBy` is server-derived.

## Naming things in your answer: names first, Amazon ids when asked

Users think in names, not numbers. An internal id is this platform's own primary key - it
means nothing on Amazon and nothing to the person reading your answer.

**Default to names.** Unless the user asked for an identifier, report `campaignName` /
`adGroupName` / `portfolioName` / `aiGroupName` / `asinTitle` and leave ids out entirely -
"Summer Tent SP - Exact spent $1,200 last week", not "campaign 41398 spent $1,200".

**If an id is shown, the name goes with it**: `Summer Tent SP - Exact (ID: 298539385213868)`.
Never a bare number.

**When the user asks for an id, give the Amazon one.** The same object has two different
numbers, and which one you get depends on the tool:

| Source | What its `campaignId` holds |
|---|---|
| `get_ads_perf` | the **Amazon** campaign id |
| `get_operation_log` | the **Amazon** campaign id |
| `get_entity_metadata` | the **internal** id - the Amazon one is the separate `amazonCampaignId` field |

Amazon-side fields per entity: `amazonCampaignId`, `amazonAdGroupId`, `amazonKeywordId`
(keywords and negative keywords), `amazonTargetId` (targets and negative targets),
`amazonAdId` (product ads), `amazonPortfolioId`. **Never present an internal id as "the
campaign ID", and never derive one identifier from the other** - they are unrelated numbers.

**Exports and tables carry both.** For a CSV, a spreadsheet, or any table the user will
reconcile against another system, give a name column **and** an Amazon-id column.

**Previews and confirmations.** A write preview echoes back the **internal** ids you sent.
Translate them to names before showing the user - nobody can meaningfully approve a change
to objects they cannot identify.

### Three exceptions

1. **Managed groups have no Amazon id.** A managed group is this platform's own construct,
   not an Amazon object, so no Amazon-side identifier exists. Report its name, and its
   internal `aiGroupId` when an id is asked for. The **campaigns inside** a managed group are
   ordinary Amazon objects and follow the rule above.
2. **Product ads have no name.** Identify one by **ASIN + SKU**; do not invent a label.
   (`placement` is an enum rather than an object - report the placement label itself.)
3. **A just-created object has only an internal id.** Creation returns local ids; the Amazon
   id appears later, once the object syncs. Report the name, and if an id is asked for give
   the internal one and say plainly that the Amazon id is not available yet. Do not poll for
   it, and do not invent one.

### Getting the name in the first place

`select` is a **strict projection**: ask for ids only and no name comes back. Whenever a
result will be shown to a user, put the name field in `select` as well - or omit `select`
entirely and take the full row.

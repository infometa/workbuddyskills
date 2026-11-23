# Two-phase confirmation

Twelve of the 25 routes can defer a write on the first call. Seven always do so; five do so
only when the payload contains `state: "archived"`. They return a preview plus a
`confirmToken`; the write happens only when you call again with that token.

## Which routes, and when

**Always (every call):**

- `campaign` + `updateBudget`
- `campaign` + `updateAudienceBid` (including 0% and changes to an existing binding)
- `campaign` + `updatePlacementBid` (including 0%)
- `keyword` + `updateBid`
- `target` + `updateBid`
- `productAd` + `archive`
- `portfolio` + `updateBudget`

**Only when the payload contains `state: "archived"`:**

- `campaign` + `updateStatus` (looks in `request.data`)
- `keyword` + `updateStatus` (`request.data`)
- `target` + `updateStatus` (`request.data`)
- `negativeTarget` + `updateStatus` (`request.data`)
- `negativeKeyword` + `updateStatus` (**`request.updates`**)

The other thirteen routes execute immediately. `productAd + updateStatus` cannot reach
`archived` at all. `adGroup + updateStatus` does accept `archived`, but that route still
executes directly; get the user's approval before calling it because archival is irreversible.

Case variants of `archived` (`"Archived"`, `" archived"`) are **rejected up front** with
`invalid_params`. They do not skip confirmation and they do not execute. Send exactly
`archived`.

## The protocol

```
Phase 1: batch_update_ads(entity, action, request, userContext)
         -> isError:false, data.status == "PENDING_CONFIRMATION"
                           data.confirmToken == "<uuid>"
                           data.notice, data.affectedCount, data.details
         Show this to the user. Get an explicit yes.

Phase 2: batch_update_ads(entity, action, request + {confirmToken}, userContext)
         -> the normal write result
```

Rules:

- **Everything except `confirmToken` must be identical.** The token is bound to a
  fingerprint over `entity` + `action` + `request` (with `confirmToken` excluded). Change
  one value - even reordering that changes a value, or "fixing" a field the preview made you
  reconsider - and Phase 2 fails. To change anything, re-run Phase 1.
- `userContext` is **not** part of the fingerprint, so it may differ. Keep it the same
  anyway; the audit log reads better.
- `confirmToken` goes **inside `request`**, not beside it.
- The token is an **opaque UUID with no prefix**. Do not validate its shape, do not parse it,
  do not log it, do not show it to the user.
- **TTL is 5 minutes**, single use, bound to the user who ran Phase 1. Another user's token
  will not work.
- **By default, do not call Phase 2 until the user says yes to the specific preview you
  showed.** If they decline or go quiet, stop - do not call again, and do not re-preview
  hoping for a different answer. If the user has explicitly waived confirmation under the
  rules in SKILL.md, verify the preview yourself (see "Running Phase 2 unattended" below)
  and proceed without waiting for another reply. Either way the `confirmToken` round trip
  still happens - there is no way to skip it.
- Do not run two Phase 2 calls for the same token concurrently.

### When the user changes the scope after seeing the preview

This is the common case, and it is not a token problem to solve - it is a new operation:

- "只改第 2 个" / "去掉那个" / "再加一个" all change `request`, so the old token cannot be
  used for the new scope. Sending Phase 2 with a modified request **burns the token and
  writes nothing**. Do not try it.
- Re-read the current state (time has passed, and the archived guard fails closed), then run
  a **fresh Phase 1** and get a yes to the new preview.
- Say out loud what dropped out of scope - "1001 will not be archived" - rather than letting
  a smaller count speak for itself.
- If the change is ambiguous ("the second one" when the preview held one item), **ask**; do
  not map it onto a row yourself, least of all for an irreversible action.

### When the user defers

"等下 / 我先看看" is neither a yes nor a no. Do not call Phase 2, and do not re-preview to
prompt them. If they come back within the 5-minute TTL with a plain yes and **nothing has
changed**, the original token is still valid. If they come back later, or with any change,
start again from Phase 1. Do not tell them whether a token is still alive - just re-preview
if you need to.

## When the token survives a failure and when it does not

| Phase 2 outcome | Token |
|---|---|
| Fingerprint mismatch (you changed a parameter) | **consumed** - re-run Phase 1 |
| Different user | **consumed** |
| Expired / not found | gone |
| Rejected on top-level `request.profileIds` authorization | **still usable** within the TTL |
| Rejected on a **nested item's** `profileId` | **consumed** - that check runs inside the strategy, after the token is spent |
| Rejected by the archived guard | **still usable** within the TTL |
| Wrong / unregistered route | **still usable** |
| Wrote successfully | consumed |

**Exactly three failures leave the token unspent**: a top-level `request.profileIds`
authorization rejection, an archived-state guard rejection, and an unregistered route.

But "unspent" is only half the test. **Re-sending the same token also requires an identical
`request`**, because the fingerprint covers it. So:

- **Reusable**: the blocker was outside the request and cleared on its own - a permission was
  granted, an object was un-archived, a transient lookup failure passed on retry - and you
  change **nothing** in the payload.
- **Not reusable**: fixing the problem means editing the request. Dropping the unauthorized
  `profileId`, removing the archived id, correcting the route - all change the fingerprint, so
  the old token is dead even though it was never consumed. **Run Phase 1 again**, and get a
  fresh yes for the new (smaller) scope.

**Everything else consumes the token outright** - fingerprint mismatch, a different user, and
(easy to miss) a **nested item's** `profileId` failing authorization, because that check runs
inside the strategy after the token is spent.

Never tell the user "the token is still valid": either you are re-sending an unchanged request
within the TTL, or you are re-previewing.

## Reading the preview

`data.details` shape depends on the route. What matters:

- **`affectedCount` on a conditional route counts only the `archived` items** - not the
  batch. A batch of 1 archive + 20 pauses previews as 1.
- `details.batchItemCount` (whole batch) and `details.otherStatusChanges` (the rest) let you
  report the true scope - **but they exist only on `updateStatus` routes.** Budget, bid and
  `productAd + archive` previews do not carry them. Do not read them unconditionally.
- **Always state the full scope in your own words** before asking for confirmation. The
  user must not be confirming a count that describes part of what will happen.
- **`campaign` preview rows have no `id` key** - they use `campaignId`. Only
  `details.otherStatusChanges[]` entries carry `id`.

### `details.items` - the shape varies by route

`details.items[]` is one entry per previewed row, and **its keys differ per route** - there
is no single schema. Roughly:

| Route | Keys you will see |
|---|---|
| `campaign` + `updateAudienceBid` | `index`, `id`, `profileId`, `campaignType`, `audienceId`, `audienceSegmentType`, `audienceBidPercentage` (requested binding and absolute uplift, not queried current values) |
| `campaign` + `updatePlacementBid` | `index`, `id`, `profileId`, `campaignType`, and whichever placement fields you sent (requested absolute percentages, not queried current values) |
| `campaign` + `updateBudget` | `index`, `campaignId`, `profileId`, `campaignName`, `currentBudget`, `adjustmentType`, `adjustmentAmount`, `projectedBudget` (+ `warnings` only when non-empty) |
| `campaign` + `updateStatus` | `index`, `campaignId`, `profileId`, `campaignName`, `campaignType`, `currentState` (always `"unknown"`), `targetState` |
| `keyword` / `target` + `updateBid` | `id`, `previousBid`, `projectedBid` (+ `campaignType` on target) |
| `keyword` / `target` / `negativeKeyword` / `negativeTarget` + `updateStatus` | `id`, current text / matchType / state as far as the lookup resolved them, `targetState` |
| `productAd` + `archive` | `id`, `targetState` (always `archived`) - built from your request only, no lookup |
| `portfolio` + `updateBudget` | `index`, `id`, `profileId`, `current`, `submitted`, `defaultSources`, `mayBeSkipped` |

**Do not infer which route a preview came from by looking at its keys**, and do not assume a
key is present. You know the route because you sent it - carry that context yourself rather
than re-deriving it from the response.


### Budget preview: `currentBudget` means `dailyBudget`

The budget preview emits a field named `currentBudget`, and its value is the campaign's
**`dailyBudget`**. The `currentBudget` field on a metadata/list row is a *different* number
and is often `0.00`.

So when reconciling a budget preview against metadata, compare
`preview.currentBudget` with the campaign's **`dailyBudget`**. Comparing it against
metadata's `currentBudget` will look like a mismatch when nothing is wrong.

`projectedBudget` is computed from that same `dailyBudget` basis.

### `warnings` is absent when empty

The budget preview omits the `warnings` key entirely when there is nothing to warn about -
it is not an empty array. Treat missing as empty.

### A null field means the lookup failed, not that the value is empty

Preview enrichment reads current text / state / bid from the platform, and **those reads
fail silently** - on error, no match, or a missing field, you get `null` and a server-side
log line, not an error. Unlike the archived guard, the preview does not fail closed.

- Never present a `null` preview field to the user as the current value.
- `projectedBid` will also be `null` for relative bid changes when `previousBid` could not
  be resolved.
- `campaign + updateStatus` previews always show `currentState: "unknown"` - the underlying
  query does not return state at all. Do not report it as the campaign's real state; read
  it with `get_entity_metadata` if the user needs to know.

## Confirmation errors

All four confirmation failures come back as `errorType: business_error`, and the message is
wrapped by the service layer, e.g.
`Service [Amazon_SA_Service] returned an error: Confirmation token expired or not found. Generate a new preview first.`

**Branch on `errorType`, not on message text.** If you must distinguish them, substring-match
on `Confirmation token` / `Request parameters changed` / `Confirmation service unavailable`,
never on a whole sentence.

If the confirmation service itself is unavailable, no token is issued and nothing is
written - fail-closed. Report it and stop; do not try to write without a token.


## Running Phase 2 unattended

Only after the user has explicitly waived confirmation - see the SKILL.md section "When the
user waives confirmation" for what counts as a waiver and what it does not cover.

A waiver removes the approval turn, not the protocol. Phase 1 still returns
`PENDING_CONFIRMATION` with a token, and Phase 2 is still a second call carrying it. Nothing
here lets you write in one call.

Unattended, the preview is checked by you instead of by the user. Before sending Phase 2:

**The preview's scope differs by route - check against the right baseline.**

Always-confirm routes (including `campaign + updateBudget`, `portfolio + updateBudget`,
`keyword + updateBid`, `target + updateBid`, `productAd + archive`, audience and placement
updates) preview the whole request. Conditional routes
(the five `updateStatus` routes) preview **only the `archived` items** while Phase 2 executes
the whole batch, so a batch of 1 archive + 20 pauses correctly previews `1` - comparing that
against `21` would reject every mixed batch.

| Check | Baseline on always-confirm routes | Baseline on conditional routes |
|---|---|---|
| Affected count | every item you sent | only the `archived` items you sent |
| Object identity | exactly the ids you sent | exactly the `archived` ids you sent |
| Rest of the batch | n/a - there is no unpreviewed remainder | `details.batchItemCount` / `details.otherStatusChanges` must reconcile with the non-`archived` items; **absent or not adding up -> stop** |
| Null fields | any `null` other than `campaign + updateStatus`'s `currentState: "unknown"` means the lookup failed -> stop | same |

Any mismatch: stop and ask, waiver or not.

The token rules are unchanged, and unforgiving when nobody is watching the clock: bare UUID,
**5 minutes**, single use, bound to the previewing user, fingerprint over `entity` + `action`
+ `request`. Send Phase 2 in the same turn - do not do other work in between. If the token
expired, re-run Phase 1 and re-check; never reuse a stale token or retry blindly.

State what you did after the write, including how many objects actually changed. A waived
confirmation still leaves a record in the conversation.

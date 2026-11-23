# Identity: internal ids and the discriminator fields

Getting this wrong is the worst failure mode in this skill: the write can land on a
**different, unrelated row** instead of erroring.

## Every id here is an internal platform id

| You need | Get it from | Field |
|---|---|---|
| campaign | `get_entity_metadata(entity='campaign')` | `campaignId` |
| ad group | `get_entity_metadata(entity='adGroup')` | `adGroupId` |
| keyword | `get_entity_metadata(entity='keyword')` | `keywordId` |
| target | `get_entity_metadata(entity='target')` | `targetId` |
| promoted product | `get_entity_metadata(entity='productAd')` | `productAdId` |
| negative keyword | `get_entity_metadata(entity='negativeKeyword')` | `negativeKeywordId` |
| negative target | `get_entity_metadata(entity='negativeTarget')` | `negativeTargetId` |
| portfolio | `get_entity_metadata(entity='portfolio')` | `portfolioId` |
| profile | `get_user_authorized_context` | `profiles[].profileId` |

**Not usable:** anything from `get_ads_perf` or `get_operation_log` (Amazon ids, 15-19
digits), and the metadata rows' own `amazonKeywordId` / `amazonTargetId` / `amazonAdId`.
Those are Amazon-side ids. Passing one fails the positive-long check or resolves nothing.

Portfolio membership is the deliberate exception: portfolio edits use internal
`portfolioId`, while `campaign + addPortfolio` uses the destination's
`amazonPortfolioId`. Do not infer one from the other.

In the write payload the id goes into the field the route names - usually `id`, but
`campaignId` / `adGroupId` on the internal routes. See the per-route write references.

## The discriminator fields are part of the identity

An id alone is not unique. The platform stores these entities across **several physical
tables with independent id spaces**, and the discriminator picks the table:

| Writing | Send with the id | Because |
|---|---|---|
| `keyword` | `matchType` + `campaignType` | `theme` -> theme table, `group` -> target table, `exact`/`phrase`/`broad` -> keyword table |
| `negativeKeyword` | `businessType` + `campaignType` | campaign-level and ad-group-level negatives are two tables |
| `negativeTarget` | `campaignType` | SD and non-SD are two tables - though the write routes accept SP/SB only |
| `target`, `productAd` | `campaignType` | table selection |

**Rules:**

1. **Echo the value metadata returned, verbatim.** Same string, same case.
2. **Never omit one**, even where a route's field table calls it "透传" / optional. Omitting
   it drops a safety filter from the archived-state pre-check, so the batch proceeds with
   less verification.
3. **Never infer or normalise one.** Do not map `"Exact"` to `"exact"`, do not guess
   `businessType` from the ad group id, do not reuse a value across rows.
4. A **wrong** value does not say "wrong matchType" - it surfaces as
   `Batch rejected: unable to resolve owning campaign ...`. If you see that message,
   suspect a discriminator before anything else.

`negativeKeyword`'s `businessType` values are `campaign` and **`adgroup`** - lowercase g,
unlike the `adGroup` entity name.

## Reading the three keyword/negative entities

`keyword`, `negativeKeyword` and `negativeTarget` are entity values of
`get_entity_metadata`. Only `profileIds` is required - you do **not** need to pass a
campaign or ad group filter first, though filtering by `campaignId` / `adGroupId` keeps
result sets small.

**keyword** (11 fields): `keywordId`, `profileId`, `campaignType`, `amazonKeywordId`,
`adGroupId`, `campaignId`, `keywordText`, `matchType`, `keywordState`, `keywordBid`,
`keywordCurrentBid`.

- `matchType`: `exact` / `phrase` / `broad` / `group` / `theme`.
- When `matchType = "group"`, `keywordText` is **not plain text** - it is a JSON string of
  the form `[{"type":"keywordGroupSameAs","value":"..."}]`. Do not show it raw to the user
  and do not substring-match it as a keyword.
- For `updateBid` read **both** `keywordBid` and `keywordCurrentBid`, and use `keywordBid`
  as the base unless `keywordCurrentBid` is a non-zero value you deliberately want to build on.
  **`keywordCurrentBid` is `0` on some whole stores** (see `sparkx-query-entity-metadata`'s
  field reference) — computing a new bid from `0` produces a bid floor, not a change.

**negativeKeyword** (11 fields): `negativeKeywordId`, `profileId`, `campaignType`,
`businessType`, `tableType`, `amazonKeywordId`, `adGroupId`, `campaignId`, `keywordText`,
`matchType`, `negativeKeywordState`.

- `matchType`: `negativeExact` / `negativePhrase`.
- `businessType` is derived from `tableType`; `adGroupId` is meaningless on campaign-level
  rows.

**negativeTarget** (9 fields): `negativeTargetId`, `profileId`, `campaignType`,
`amazonTargetId`, `adGroupId`, `campaignId`, `negativeTargetText`, `negativeTargetType`,
`negativeTargetState`.

- `negativeTargetType`: `asinSameAs` / `asinExpandedFrom` / `asinBrandSameAs`.
- `negativeTargetText` holds the ASIN or brand id.
- There is no `matchType` and no `businessType` on this entity.

## Field-name traps when filtering

- The match column is `matchType` on these three entities but **`targetMatchType`** on the
  `target` entity. Using the wrong one is a hard downstream error (the filter field must be
  in that entity's whitelist), so it fails loudly rather than silently - but it does fail.
- The targeting text column is **`targetText`** on `target` and `negativeTargetText` on
  `negativeTarget`. There is no `targetName`, and `keywordText` does not exist on the
  `target` entity - it belongs to `keyword`.
- `negativeTargetState` (this entity's status) is unrelated to `negativeTargetStatus`,
  which is an AI-managed-group on/off setting. The first is writable through this tool;
  the second is read-only and lives in `edit-ai-group`.
- Unknown filter operators **throw**; they are not ignored. Null filter values are rejected.
- Only the **first** `orderBy` entry is honoured; the rest are dropped silently.

## Metadata read gotchas that affect writes

- **Use `meta.total` for counts and `meta.hasNextPage` to continue paging.**
  **`meta.total` is the exact match count - read it instead of paging to count.** `pageSize`
  defaults to 100; an out-of-range value (`<=0` or `>500`) is an **error, not clamped**.
  `total` is omitted for a few entities (e.g. `asin`); when it is missing, say the count is
  unavailable rather than summing pages.
- **`profileIds` is all-or-nothing** on metadata reads too - an unauthorized id raises
  `Requested profileIds contain unauthorized values` rather than narrowing the result.
- **Do not require a `{field}Text` column to exist.** Translated columns are appended only
  for enum fields registered in the dictionary, and the set of columns is decided from the
  **first row of the page only** - if row 0 lacks a key, no row in that page gets its
  `Text` column. Present values you actually received.
  - Registered here: `keywordState`, `negativeKeywordState`, `negativeTargetState`,
    `matchType`, `negativeTargetType`, `campaignType`.
  - **Not** registered: `businessType`, `tableType` - there is never a `businessTypeText`.
- Responses are English only (`language` is fixed server-side).
- `select` (field projection) saves tokens, but an unrecognised field name is **silently
  dropped**; the only notice is in `meta.hint` (`Unknown select fields ignored: ...`). Read
  `meta.hint` when you use `select`. `select` is applied after pagination, so it cannot
  change `hasNextPage`.

## Bids: read before you write

`keyword + updateBid` and `target + updateBid` **require** `previousBid` in the payload,
but the server does no arithmetic with it and does not verify it - it is forwarded as-is.
So:

1. Read the current bid from metadata (`keywordBid` for keywords, with `keywordCurrentBid`
   only as a cross-check and only when non-zero) immediately before
   the write, **one `profileId` per call**. Multi-profile rows do carry their own `currency`,
   so the currency itself is knowable - but re-reading with exactly one profile before a write
   is a **write-safety rule**: it removes the chance of picking a same-named entity from the
   wrong store, or of carrying an amount across from another store's row. **Do not feed an
   amount taken from a multi-profile result straight into a write** - not as `previousBid`,
   not as a `setTo` amount, and not as the base for a percentage change. The same applies to
   `dailyBudget` before a budget write.
2. A stale or wrong `previousBid` is **not detected**. If time has passed, or if the AI or
   another user may have adjusted bids, re-read rather than reusing a cached value.

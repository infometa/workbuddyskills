# UE routing

Use this reference after `data-integration inspect`.

## Route to UE ingestion

All of these must hold:

- A real `#account_id` or `#distinct_id` source is present.
- A real time column is parseable; no synthetic time is permitted.
- The records are event facts or user-property snapshots rather than aggregates.
- Field-level records can be represented without losing essential meaning.

Classification order:

1. A legal explicit `#type` wins (all eight record types — `track`, `user_set`, `user_setOnce`, `user_add`, `user_unset`, `user_del`, `user_append`, `user_uniq_append`).
2. An event/action field implies `track`.
3. Repeated users across a time series imply `track`; without an event field, propose a normalized file/Sheet name and require review.
4. One row per user with snapshot-like fields implies `user_set`.
5. Rows that mix track and user-profile facts in one file use `mixed` with a `record_type_field`; require explicit review.
6. Low-confidence output is a proposal, never silent approval.

Aggregated metrics, pivot tables, cross-tabs, model outputs, and free-form documents should normally use local analysis. Records without real identity/time are checked against dimension routing next and fall to local analysis only if they are not a stable-entity lookup.

### Time coverage is not native granularity

A parseable time column establishes only when the rows are stamped, not what period each metric
covers. A daily report and a cumulative snapshot both look like one row per user per point in time,
so they satisfy every condition above and are then ingested as per-period events — inflating totals
in a way that stays invisible in ratios, because numerator and denominator scale together.

Native granularity must come from the user, a data dictionary, or a complete period structure in the
data itself. Do not infer it from the file name, the first/last date, the interval between rows, or
the row count; none of those is evidence.

When the data carries numeric columns and any of the following holds, ask the user to state whether
each row's value is the amount that occurred in that period or the total accumulated up to that
point, and do not proceed until they answer:

- Paired start/end time columns (`start_date`/`end_date`, `period_begin`/`period_end`).
- Values for one identity that never decrease over time.
- Column names carrying a to-date sense (`cumulative`, `total`, `ltv`, `累计`, `总`).

An unanswered question, a cumulative snapshot, or overlapping periods route to local analysis
instead.

## Route to dimension table

A dimension / dictionary table describes stable entities (city, product, device): a lookup that maps an entity code to its attributes. It has no row-level identity or event time, so it fails the UE prerequisites above, but it is not local-analysis material either — it belongs in AE as a dimension table bound to a property.

Classification order (UE first, dimension second, local analysis last):

1. Satisfy the UE must-holds above → UE ingestion wins; never route an identity/time-bearing file here.
2. Fail the UE prerequisites **and** match most of these dimension signals → dimension routing:
   - No row-level identity: no `account_id` / `distinct_id` column. A `code` / `id` / `no` key is an entity code, not a user identity.
   - No row-level event time: no `#time` column. If time exists, it is an effective / expiry interval, not an event occurrence.
   - Finite enumeration: few rows, each describing one entity's attributes (code → name / level), not facts accumulating over time.
   - A join key: a column shared with event data (`city_code`, `sku_id`, `device_id`) whose values are descriptive attributes, not measures.
3. Otherwise → local analysis.

See [references/dimension-routing.md](references/dimension-routing.md) for the handoff.

## Route to local analysis

Choose local analysis when:

- The user wants insights, not project ingestion.
- UE identity or time prerequisites are missing.
- Each row is an aggregate rather than a user/event record.
- The rows are a cumulative snapshot, or their native granularity could not be established.
- Conversion would invent semantics or discard important structure.
- The user declines an uncertain mapping or destination.

Explain the reason briefly. Do not frame local analysis as an error.

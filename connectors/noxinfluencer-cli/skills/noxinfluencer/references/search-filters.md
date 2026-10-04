# Search Filter Semantics

For the full parameter list and syntax, run `noxinfluencer schema creator.search`. The single-argument command-path form `noxinfluencer schema 'creator search'` is equivalent.

This reference covers **when to use which filters** — the decision logic, not the syntax.

For a new search, apply topic exclusions and SaaS hide/deduplication directly through `creator search`. Use standalone `creator search-filter` only when a page has already been returned.

## Filter Priority by User Intent

| User intent | Key filters to apply | Why |
|-------------|---------------------|-----|
| Known creator name or handle | `--creator_name`, `--platform` | Match creator identity instead of treating the name as a topic keyword |
| Niche sourcing | `--keywords`, `--platform` | Narrow to relevant content creators |
| Every topic must match | `--keywords`, `--keyword_match all` | Require all supplied topic keywords instead of the default any-keyword union |
| Regional targeting | `--country`, `--follower_countries` | Match campaign geography |
| Budget-constrained | `--follower_min`, `--follower_max` | Size correlates with cost |
| Platform email outreach | `--has_email true` | Only creators with known email signal; platform email can add search `data.items[].id` values as recipient `creator_id` without retrieving visible email |
| Audience fit | `--follower_ages`, `--follower_female_pct_min`, `--follower_language` | Match audience demographics |
| Active creators | `--published_within_days` | Exclude dormant channels |
| Performance floor | `--engagement_rate_min`, `--avg_view_min` | Filter out low-engagement creators |

## Search Result Fields

Each result item includes: `id` (encrypted token), `nickname`, `tags`, `followers`, `country`, `total_videos`, `view_per_followers`, `engagement_rate`, `avg_views`, `language`.

`creator_name` and `keywords` are mutually exclusive. Name search uses the same result pricing and pagination as topic search.

Search responses also include page metadata under `data`: `page_num`, `page_size`, `total_page`, `total_size`, and `search_after`.

The `id` is an encrypted token — use it directly as the positional `<creator_id>` argument in subsequent commands. Do not try to decode it.

## Page Size and Cost

- `creator search` and `creator lookalikes` share returned-result pricing; use `pricing tools --action creator_search` or `--action creator_lookalikes` for the current server-side unit price.
- The default page size is 20 and the maximum page size is 100.
- Charge impact follows the number of returned items, not the requested `page_size`. Prefer targeted pages while refining filters; use larger pages only when the user asks for broad sourcing or bulk follow-up.

## Search Result Deduplication

- Use `exclude_keywords` for unwanted topic/tag matches; do not emulate exclusions by dropping rows after billing.
- Run `creator search-filter-options` to inspect SaaS hide choices. Apply its `search_body_patch` in the same `creator search` request whenever possible.
- Use its standalone `body_patch` with `creator search-filter` only for already returned `data.items[].id` values.
- Use `creator not-interested add` only after explicit approval to mark selected creators as Not interested. `list` audits those marks, and `remove` cancels them so the creators can appear in future searches again.

## Pagination Rules

- For a next-page request, keep the previous search filters exactly the same and send both the next `page_num` and the previous response's `data.search_after`.
- Prefer `--body-file -` for next-page requests and pass one JSON body containing the preserved filters, `page_num`, `page_size`, and `search_after`. This avoids shell globbing/quoting problems with cursor arrays.
- If using flags instead of `--body-file`, shell-quote every bracketed array argument, especially `--search_after`, for example `--search_after '[163.97083,"UCQ-P8lGwkr0Tj4phQB9diDw"]'`.
- Current CLI and server validation require `page_num > 1` when `search_after` is present, so do not try cursor-only paging.
- If `data.search_after` is missing or empty, or the current page is already the last page, tell the user there are no more results.

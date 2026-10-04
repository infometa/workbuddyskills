# analysis filter-value list

List stored candidate values for one event property, user property, user tag, or user cluster whose identifier is already known.

## Purpose

Use this capability when an analysis filter needs an exact stored value but the caller knows only the business wording. Typical examples are checking whether a channel is stored as `iOS`, `ios`, or `Apple`, or narrowing a high-cardinality property with a prefix before constructing a report or ad-hoc filter.

Do not use it to discover property names, calculate value frequencies, enumerate all raw rows, or replace an analysis aggregation. Resolve the property through metadata or compiler clarification first. The result is a candidate-value aid, not proof of frequency or completeness.

## Command

```bash
ae-cli analysis filter-value list \
  --project-id <project_id> \
  --property-name <property_name> \
  --table-type event|user \
  [--event-name <event_name>] \
  [--search-prefix <text>] \
  [--zone-offset <offset>] \
  [--cluster-date-policy LATEST|AUTO|SPECIFIED] \
  [--specified-cluster-date yyyy-MM-dd] \
  [--report-mode true|false]
```

`--event-name` narrows an event-property lookup. `--specified-cluster-date` is required only with `--cluster-date-policy SPECIFIED` and is rejected otherwise. Here “cluster date” means a 用户分群/人群包 snapshot date; it is unrelated to the physical 查询集群 returned by `analysis query-cluster list`.

Output `data.items` contains permission-filtered candidate values. An empty array is successful: no visible candidate matched the selected property and prefix.

## Tag and cluster snapshot semantics

For user tags and user clusters, `LATEST` means the latest available computed result snapshot. It is not a tag definition or configuration release, and it does not require a version list, version ID, draft state, or publish state.

Natural-language routing:

- “查询标签 X 最新版本/最新结果有哪些值” → resolve `X` with `analysis user-tag list`, then call `analysis filter-value list` with the returned exact `tag_name`, `--table-type user`, and `--cluster-date-policy LATEST`.
- “查询分群 X 最新结果的候选值” → resolve `X` with `analysis user-cluster list`, then use the same candidate-value command with `--cluster-date-policy LATEST`.

Do not route either request to a definition-version workflow. `LATEST`, `AUTO`, and `SPECIFIED` select computed data snapshots only.

## Typical workflow

1. Resolve the exact event/property identifier or tag/cluster machine name from the matching metadata or asset list.
2. Call `analysis filter-value list`, using `--search-prefix` when the value space is large.
3. Select only a returned exact value; do not normalize spelling or invent a synonym.
4. Put that value into `report-data run`, `dashboard-report-data run`, or `adhoc run`.
5. Verify the result scope and, when needed, follow the returned synchronous query context into drilldown.

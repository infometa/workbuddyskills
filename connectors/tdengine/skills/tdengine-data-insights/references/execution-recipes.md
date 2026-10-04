# Execution Recipes

Prefer existing panel query results when they match the requested scope. Otherwise retrieve complete attribute history and analyze locally. This skill is read-only: never create, update, or delete a panel or analysis.

## 1. Environment Inventory

1. Page through `list_elements` without a parent to get every root. Its `total`
   is the root count, not the total number of elements in the system.
2. Recursively page through `list_element_children(parent_id)` for every row
   whose `hasChildren` is true. Deduplicate by element ID before counting.
3. Count rows with `hasChildren=false` as leaves only when the requested
   definition of device is a leaf element. Report the definition used.
4. Call `list_element_templates` and count the returned templates.
5. To count monitoring metrics, call `list_element_attributes` for each leaf
   and retain `TDengineMetric` attributes. Report both concrete attribute
   instances and, when useful, unique definitions grouped by template, name,
   value type, and unit. Do not mix tags or static properties into the metric
   count.
6. If every page or branch cannot be covered, label the result incomplete
   instead of extrapolating from the first page.

## 2. Recently Updated Device

1. Establish the candidate leaf population with the inventory traversal.
2. Call `list_element_attributes` and keep the relevant `TDengineMetric`
   attributes for each candidate.
3. Call `get_attribute_value` for those attributes and compare the returned
   data `updatedTime`. Select a device with recent metric data, not merely a
   recently edited element. Claim "most recent" only after scanning the full
   candidate population.
4. Fetch the requested time window with `get_attribute_history`, including all
   pages, and calculate trends and extrema from the returned points.
5. If `enabledLimitsTrait` is true, inspect the attribute `traits` and apply
   only explicitly defined normal lower or upper bounds. State which trait and
   inclusive/exclusive comparison were used. Do not infer bounds from units.

## 3. Recently Updated Panel

1. Call `search_panels` with the keyword omitted and page through all results.
2. Exclude `PANEL_TEMPLATE` rows and rows without a concrete `elementId`.
   Compare `updateTime` and select the newest eligible element panel.
3. Call `get_panel(element_id, panel_id, start_time, end_time)` and interpret
   both `panel_detail` and `query_data`. A panel is one visualization; do not
   describe it as a multi-chart dashboard.
4. If no eligible panel has query data, report that condition instead of
   selecting a template panel as if it contained live measurements.

## 4. Named Panel

1. Call search_panels(keyword) and exclude PANEL_TEMPLATE results.
2. For a result with elementId, call get_panel(element_id, panel_id, start_time, end_time).
3. A null elementId identifies a template-level panel; find a concrete element and use its attributes instead.
4. Treat query_data as evidence. Do not infer measured values from configuration.
5. Normalize with `load_panel_queries()`, then call
   `analyze_panel_queries()`. Treat each entry as a separate SQL result; never
   report only the first entry when `query_count` is greater than one.

## 5. Named Element or Device

1. Use search_elements(keyword) and verify the intended leaf by elementPath.
2. Check search_panels(keyword) or list_panels(element_id), even for a leaf.
3. Reuse a matching element-level panel with get_panel().
4. Otherwise call list_element_attributes(element_id).
5. Keep TDengineMetric attributes; exclude tags and nonnumeric types unless the request concerns state.
6. Retrieve required series with get_attribute_history().
7. Compare total with count and fetch all remaining pages.
8. Normalize, run data_quality_check(), then perform the requested analysis locally.

Use the same time range for all compared series. Read-only calls may run concurrently when supported.

## 6. Named Attribute

1. Call search_attributes(keyword) to discover elementId and attribute ID.
2. Filter by elementPath when multiple devices match.
3. Call get_attribute_history(element_id, attribute_id, start_time, end_time).
4. Fetch all pages and analyze locally.

## 7. Same Attribute Across Devices

1. Resolve the fleet or branch root, then recursively page through
   `list_element_children(parent_id)` until every leaf element is known.
2. Call `list_element_attributes(element_id)` for each leaf and retain the
   exact requested attribute name and its per-element ID.
3. Use `search_attributes(keyword)` only as a global discovery fallback. It
   has no element or branch scope parameter, so filter returned element paths
   against the discovered leaf set before using a result.

- Filter broad scopes by elementName and elementPath.
- Preserve each elementId and attribute ID pair.
- Never assume equivalent names share an ID.
- Fetch histories concurrently where possible and align by timestamp or common bucket.

## 8. Large Fleets

Analyze the complete available population; do not silently sample.

1. Reuse an existing aggregate panel when available.
2. Otherwise recursively page through `list_element_children` to establish the
   complete leaf population, then call `list_element_attributes` per leaf.
3. Filter exact attribute names and data-reference types before retrieving data.
4. Use get_batch_attribute_data only for an explicitly current-state question.
5. For historical analysis, retrieve histories in bounded concurrent batches.
6. If the population cannot be covered within client or service limits, report the limitation and propose a narrower scope.

Do not mutate resources as an analysis shortcut. This skill is strictly read-only.

## 9. Volume and Pagination

| Device family | Typical interval | Seven-day points | Pages at 500 points |
|---|---:|---:|---:|
| Meters, batteries, environmental sensors, transformers, water systems | 10 minutes | about 1,000 | 2-3 |
| Solar and weather sensors | 10 minutes | about 1,000 | 2-3 |
| Wells, vehicles, low-frequency production equipment | 6 hours | about 28 | 1 |

| Point count | Analysis grain |
|---:|---|
| 500 or more | Daily buckets, or a justified finer grain |
| 100-499 | Daily buckets with a coverage caveat |
| 20-99 | Point-level analysis |
| Below 20 | Brief statistics and a sparse-data warning |

Pagination is complete only when accumulated count reaches total or the service indicates no next page.

## 10. Comparison Patterns

For rankings based on average, total, stability, or trend, use complete history rather than current snapshots. Calculate device statistics with calc_stats(), sort on the requested metric, and state whether higher or lower is preferable.

For contribution shares, divide each complete-period total by the fleet total. Guard a zero denominator.

For state distribution, normalize Boolean strings explicitly before calculating true/false rates.

## 11. Recommended Analysis Order

1. load_attribute_history(response)
2. data_quality_check(items)
3. calc_stats(numeric_values)
4. bucket_by(items, chosen_grain)
5. aggregate_buckets(buckets)
6. calc_changes(aggregated)
7. detect_trend(aggregated)
8. detect_anomalies(aggregated, sigma=sigma)
9. detect_periodicity(items), only with enough cycles
10. detect_change_points(aggregated)
11. auto_insights(items, chosen_grain)

Run correlation only when two aligned, nonconstant numeric series exist.

## 12. Tool Selection

| Need | Read-only tool path | Constraint |
|---|---|---|
| Single-metric trend | get_attribute_history, then local aggregation | Raw points only |
| Multi-metric relationship | Multiple get_attribute_history calls, then alignment | Keep one time range |
| Cross-device history | Per-device get_attribute_history | Attribute IDs may differ |
| Current fleet health | get_batch_attribute_data | Snapshot only |
| Current single value | get_attribute_value | No trend evidence |
| Existing panel interpretation | get_panel | Use query_data |
| Event analysis | list_events, then get_event | Respect event scope and status |

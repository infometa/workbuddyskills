# Data Insight Gotchas

Consult this guide before diagnosing missing, truncated, or misleading results.

## 1. Public Tool Contracts

| Tool | Common mistake | Correct handling |
|---|---|---|
| get_attribute_history | Passing relative time such as now-7d | Pass Unix milliseconds from ago_ms() and now_ms() |
| get_attribute_history | Supplying aggregation parameters | It returns raw points; aggregate locally |
| get_attribute_history | Assuming the default page is complete | Compare total and count, then fetch every page |
| get_attribute_history | Reading timestamp instead of updatedTime | Read updatedTime |
| get_batch_attribute_data | Passing element_ids as an array | Pass a comma-separated string |
| get_batch_attribute_data | Omitting attribute_names | Pass a comma-separated name list |
| get_batch_attribute_data | Treating snapshots as history | Use get_attribute_history for trends |
| get_batch_attribute_data | Assuming a shared ID for same-name attributes | Discover the correct per-device attribute |
| list_element_children | Passing element_id | The required parameter is parent_id |
| search_attributes | Passing element_id or another scope parameter | The tool is global and accepts keyword plus pagination only; discover scoped leaves with list_element_children, then inspect each leaf with list_element_attributes |
| get_element_fullpath | Omitting root_element_id | Discover the root first |
| get_panel | Passing only panel_id | Pass both element_id and panel_id |

All workflows in this skill are read-only. Do not invoke resource-creation or mutation tools.

## 2. Panel Results

| Operation | Element-level PANEL | PANEL_TEMPLATE |
|---|---|---|
| search_panels | Returned with elementId | Returned with null elementId |
| list_panels(element_id) | Returned | Not returned |
| get_panel(element_id, panel_id) | Returns definition and query data | Not usable without a concrete element panel |

If only a template-level panel is found, use element attributes and history. Panel titles may differ from user wording, so compare semantics as well as exact text.

Panel query_data commonly contains:

- columnMeta entries shaped as column name, type, and width;
- data rows shaped as timestamp followed by one or more values;
- yaStaticsList with avg, min, max, total, firstTime, and lastTime for non-time-series panels;
- multiple timestamp/value column pairs in a single response.

The outer `query_data` array may also contain multiple independent SQL result
sets. Use `load_panel_queries()` and analyze every entry. Use the singular
`load_panel_query()` only after proving that the response contains at most one
entry; it raises rather than silently discarding later results.

fromText and toText may differ from the actual returned range. Report the observed range. start_time and end_time can override panel defaults.

## 3. Types and Timestamps

| Hazard | Safe handling |
|---|---|
| Boolean values returned as native JSON values or strings | Preserve native Boolean state; compare normalized strings with true |
| Integer values returned as strings | load_attribute_history() converts numeric strings |
| Identical current snapshots | Use history for rankings |
| Different child schemas | Verify each attribute exists |
| All-Boolean devices | Analyze state distribution and transitions |

| Timestamp digits | Unit | Divisor to seconds |
|---:|---|---:|
| 10 | seconds | 1 |
| 13 | milliseconds | 1,000 |
| 16 | microseconds | 1,000,000 |
| 19 | nanoseconds | 1,000,000,000 |

Detect precision from magnitude before conversion. Public attribute-history and panel timestamps are normally milliseconds, while raw TDengine data may use finer precision.

## 4. Response Shapes

- aggregate_buckets() returns a dictionary keyed by bucket, not a list.
- list_element_attributes returns an array of attribute definitions.
- detect_change_points() uses mean/count for mean_shift and stdev/count for variance_shift.
- A batch request across N elements and M names may produce an N by M Cartesian response. Deduplicate by elementId and attribute name.

## 5. Local Python

- Use one local run for all related calculations.
- The packaged script depends only on the Python standard library.
- Guard near-zero denominators for deviation, ratios, and percentage change.
- Prefer absolute difference when percentage change would be unstable.
- Keep raw MCP responses out of reports when they contain unrelated or sensitive fields.

## 6. Correlation

A near-zero correlation can mean independent signals, time lag, nonlinearity, mixed operating regimes, or synthetic data. Check:

1. timestamp alignment and pair count;
2. nonzero variance on both sides;
3. lagged relationships justified by the process;
4. segmentation by operating state;
5. whether the sample size supports the claim.

Encode Boolean state as 0/1 only when that interpretation is meaningful. Correlation on approximately 28 points is low confidence.

## 7. Low-Frequency Data

| Request | Honest adaptation |
|---|---|
| Minute-level state from six-hour samples | Distribution by observed sample |
| Hourly trend from six-hour samples | Six-hour or daily trend |
| Hourly behavior within one day | Describe the three or four observed points |
| P95/P99 from about 28 points | Calculate only with a small-sample caveat |

For equal six-hour intervals, the time-weighted mean reduces to the arithmetic mean.

## 8. Detect Non-Analyzable Cases Early

| Signal | Handling |
|---|---|
| Constant attribute | Report the constant; skip trend and correlation |
| Zero variance in either correlation series | Do not calculate Pearson r |
| Empty history | Fall back to get_attribute_value only for a current snapshot |
| All-Boolean device | Analyze state distribution or change frequency |
| One device in a comparison scope | Switch to temporal analysis |
| Missing source data | Report the gap and recommend checking collection |

## 9. Degradation Matrix

| Situation | Adaptation |
|---|---|
| Current values only | Cross-device distribution and grouping |
| Requested attribute absent | Ask before substituting a semantically related attribute |
| Requested historical period empty | Report it; do not silently change dates |
| Fewer devices than requested TOP N | Return all and state the population size |
| Constant signal | Report its value and skip unsupported statistics |
| Boolean/numeric relationship | Encode Boolean as 0/1 with disclosure |
| Consumption absent but power/flow exists | Integrate over elapsed time |
| Too many devices for complete history within limits | Report scope limitation and propose narrowing |

Never hide a fallback. State what changed, why, and how it affects confidence.

## 10. Business Plausibility

Challenge results that are mathematically valid but operationally surprising:

- very low average speed may include idle or stopped periods;
- extremely low variability may indicate simulated or pre-aggregated data;
- expected physical relationships may be absent because of lag, bad alignment, or synthetic inputs;
- aggregate means may conceal subgroups.

Present these as hypotheses and validation steps, not facts.

## 11. Compound Metrics

- Utilization requires defensible minimum and maximum bounds.
- Setpoint deviation must skip near-zero setpoints or use absolute difference.
- CV is unsuitable when the mean is near zero.
- Discover attribute IDs per element; names alone are not identifiers.
- Resolve phrases such as this month to explicit timestamps and report them.

## 12. Attribute Filtering

Keep source metrics required by the question. Exclude Tag and Varchar attributes from numeric calculations, but retain Boolean attributes for state analysis. Verify units before combining or comparing values.

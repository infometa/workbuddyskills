# Analysis Function Catalog

The functions below are provided by `scripts/analyze_ts.py`. Import only the functions needed for the current analysis. All functions use the normalized history shape returned by `load_attribute_history()` unless stated otherwise.

## Core Utilities

| Function | Purpose | Input -> output |
|---|---|---|
| `ago_ms(days, hours)` | Compute a Unix timestamp in milliseconds relative to now | Integer offsets -> `int` |
| `now_ms()` | Return the current UTC Unix timestamp in milliseconds | None -> `int` |
| `load_attribute_history(data)` | Normalize an attribute-history response | API JSON -> `[{"ts": datetime, "ts_ms": int, "value": float}]`; numeric strings become floats, while Bool and Varchar values remain unchanged |
| `load_panel_queries(data)` | Normalize every panel query result without dropping later SQL results | API JSON -> `[(column_names, rows), ...]` |
| `load_panel_query(data)` | Normalize a panel known to contain zero or one query result | API JSON -> `(column_names, rows)`; raises when multiple results require the plural API |
| `bucket_by(items, bucket)` | Group points by `day`, `hour`, or `weekday` | Normalized items -> `{key: [values]}` |
| `aggregate_buckets(buckets)` | Calculate statistics for each bucket | Buckets -> `{key: stats}` |
| `calc_stats(values)` | Calculate complete descriptive statistics over finite numeric values | mixed values -> `{count, sum, avg, median, max, min, spread, stdev, cv, p25, p75, iqr}` |
| `analyze_panel_queries(queries)` | Analyze every normalized panel result set | normalized queries -> `{query_count, queries}` |

## Trend Analysis

See [Analysis Methodology](analysis-methodology.md#1-time-series-pattern-discovery).

| Function | Purpose | Input -> output |
|---|---|---|
| `calc_changes(agg)` | Period-over-period changes | Aggregates -> `[{from, to, prev, curr, change_pct}]` |
| `moving_average(items, window)` | Moving-average smoothing | Items -> `[{..., ma: float}]` |
| `detect_trend(agg)` | Linear trend, slope, and fit quality | Aggregates -> `{direction, slope, r_squared, total_change_pct, avg_change_pct}` |
| `detect_inflection_points(agg)` | Detect local peaks and valleys | Aggregates -> `[{key, type, value}]` |

## Periodicity and Seasonality

| Function | Purpose | Input -> output |
|---|---|---|
| `overlay_periods(items, period)` | Overlay equivalent positions across periods | Items -> `{hour_or_weekday: [values]}` |
| `has_intraday_coverage(items)` | Verify at least two sufficiently covered daily cycles before periodicity analysis | Items -> `bool` |
| `detect_periodicity(items)` | Detect intraday and workday/weekend patterns after coverage validation | Items -> `{hourly_pattern, peak_hours, valley_hours, workday_vs_weekend}` |

## Anomaly Detection

| Function | Purpose | Input -> output |
|---|---|---|
| `detect_anomalies(agg, metric="avg", sigma=1.0)` | Relative anomaly detection at +/- N sigma | Aggregates -> `[{key, value, deviation, direction}]` |
| `detect_absolute_anomalies(items, low, high)` | Detect violations of physical or business limits | Items and bounds -> `[{ts, ts_ms, value, direction}]` |
| `detect_cluster_anomalies(multi_items, bucket="hour", sigma=2.0)` | Detect simultaneous anomalies across devices | `{name: items}` -> `[{key, anomaly_devices, count, is_cluster}]` |

## Change-Point Detection

| Function | Purpose | Input -> output |
|---|---|---|
| `detect_change_points(agg, metric="avg", min_change_pct=20.0)` | Detect shifts in mean or variability | Aggregates -> `[{split_at, type, before, after, change_pct}]` |

For `mean_shift`, `before` and `after` contain `mean` and `count`. For `variance_shift`, they contain `stdev` and `count`.

## Device Comparison and Grouping

| Function | Purpose | Input -> output |
|---|---|---|
| `compare_series(series, bucket)` | Align and compare multiple series | `{name: items}` -> bucket-aligned comparison |
| `classify_devices(device_stats, metric)` | Classify devices into high, medium, and low groups | `{name: stats}` -> `{high, medium, low}` |
| `benchmark_analysis(device_stats, metric)` | Identify the benchmark and quantify gaps | `{name: stats}` -> `{benchmark, benchmark_value, gaps}` |
| `calc_correlation(items_a, items_b)` | Pearson correlation on aligned points | Two item lists -> `{r, interpretation, n_pairs}` |

## Comparative Calculations

| Function | Purpose | Input -> output |
|---|---|---|
| `calc_compliance_rate(values, low, high)` | Calculate compliance with an accepted range | Values and bounds -> `{total, compliant, rate_pct}` |
| `calc_deviation_rate(values, target)` | Quantify deviation from a target | Values and target -> `{avg_deviation_pct, max_deviation_pct, within_5pct, within_10pct}` |

## Domain Calculations

| Function | Purpose | Input -> output |
|---|---|---|
| `calc_peak_valley_ratio(items)` | Peak-to-valley ratio and load factor | Items -> `{peak_hour, peak_avg, valley_hour, valley_avg, peak_valley_ratio, load_factor}` |
| `calc_efficiency(input_items, output_items)` | Conversion efficiency | Two series -> `{per_bucket, overall_efficiency}` |
| `calc_continuous_compliance(values, low, high)` | Consecutive periods in compliance | Values and bounds -> `{current_streak, max_streak, total_compliant}` |
| `calc_oee(availability, performance, quality)` | Overall equipment effectiveness | Three percentages -> `{oee_pct, availability, performance, quality, bottleneck}` |

## Panel Analysis

| Function | Purpose | Input -> output |
|---|---|---|
| `analyze_panel_data(cols, rows)` | Analyze normalized panel query data | Columns and rows -> `{total_rows, time_range, series, spread_analysis, day_night_comparison}` |

## Time-Series Feature Engineering

| Function | Purpose | Input -> output |
|---|---|---|
| `lag_features(items, lags=[1,3,5])` | Add lagged values for state prediction | Items -> `[{..., lag_1, lag_3, lag_5}]` |
| `rolling_stats(items, windows=[5,10])` | Add rolling means and standard deviations | Items -> `[{..., roll_mean_N, roll_std_N}]` |
| `ewm_features(items, spans=[5,10])` | Add exponentially weighted means | Items -> `[{..., ewm_N}]` |
| `diff_features(items)` | Add first differences and rates of change | Items -> `[{..., diff_1, pct_change}]` |
| `cyclic_encode(items, period)` | Add sine/cosine cycle encodings | Items -> `[{..., cycle_sin, cycle_cos}]` |
| `interaction_features(items_a, items_b)` | Add difference, ratio, and product features | Two lists -> `{key: {a, b, diff, ratio, product}}` |

## Data Quality and Automated Insights

| Function | Purpose | Input -> output |
|---|---|---|
| `data_quality_check(items)` | Diagnose missing data, duplication, irregular sampling, and distribution issues | Items -> `{total, issues, score}` |
| `detect_iqr_outliers(values, factor=1.5)` | Robust outlier detection using IQR | Values -> `{q1, q3, iqr, lower, upper, outliers, count}` |
| `calc_skewness(values)` | Calculate distribution skewness | Values -> `float` |
| `auto_insights(items, bucket)` | Run the standard insight rules | Items -> `[{category, icon, title, detail, severity}]` |

## Markdown Formatters

| Function | Purpose |
|---|---|
| `format_agg_table(agg)` | Aggregated statistics table |
| `format_changes_table(changes)` | Period-over-period change table |
| `format_anomalies_table(anomalies)` | Anomaly table |
| `format_quality_report(quality)` | Data-quality report |
| `format_insights(insights)` | Insight list |
| `format_trend_summary(trend)` | One-line trend summary |
| `format_device_comparison(benchmark)` | Benchmark comparison table |

## Decision-Oriented Formatters

| Function | Parameters |
|---|---|
| `format_decision_brief(question, answer, evidence, confidence, caveats, next_steps)` | Decision, answer, evidence list, confidence, caveats, and next steps |
| `format_anomaly_record(what_changed, since_when, possible_causes, data_quality_ok, immediate_action, next_observation)` | Change, start time, possible causes, quality status, action, and follow-up |
| `format_executive_summary(one_line, supporting_points, caveat, ask)` | One-line answer, supporting points, caveat, and decision request |

## Import Example

```python
import sys

sys.path.insert(0, "skills/tdengine-data-insights/scripts")

from analyze_ts import (
    ago_ms, now_ms, load_attribute_history, load_panel_query,
    bucket_by, aggregate_buckets, calc_stats, calc_changes,
    moving_average, detect_trend, detect_inflection_points,
    overlay_periods, detect_periodicity, detect_anomalies,
    detect_absolute_anomalies, detect_cluster_anomalies,
    detect_change_points, compare_series, classify_devices,
    benchmark_analysis, calc_correlation, calc_compliance_rate,
    calc_deviation_rate, calc_peak_valley_ratio, calc_efficiency,
    calc_continuous_compliance, calc_oee, analyze_panel_data,
    lag_features, rolling_stats, ewm_features, diff_features,
    cyclic_encode, interaction_features, data_quality_check,
    detect_iqr_outliers, calc_skewness, auto_insights,
    format_agg_table, format_changes_table, format_anomalies_table,
    format_quality_report, format_insights, format_trend_summary,
    format_device_comparison, format_decision_brief,
    format_anomaly_record, format_executive_summary,
)
```

# Deep Analysis Methodology

This guide turns industrial time-series data into defensible findings. Run a data-quality check before interpreting patterns, preserve the requested time range, and distinguish observation, association, and causation.

## 1. Time-Series Pattern Discovery

### 1.1 Trends

Use aggregate_buckets() at a meaningful time grain, then:

- calc_changes() for period-over-period rates;
- moving_average() to reduce short-term noise;
- detect_trend() for direction, slope, total change, and R-squared;
- detect_inflection_points() for local peaks and valleys.

Report absolute and percentage changes. A low R-squared means a linear description is weak even when its slope is nonzero.

### 1.2 Periodicity and Seasonality

Use overlay_periods() and detect_periodicity() for intraday peak/valley hours, workday/weekend behavior, shift patterns, and seasonal effects. Require `has_intraday_coverage()` to pass before claiming an intraday pattern; a raw point-count threshold does not prove multiple complete cycles.

### 1.3 Anomalies

- detect_iqr_outliers() is the robust default for an unknown distribution.
- detect_anomalies() is appropriate when a sigma-based relative threshold is justified.
- detect_absolute_anomalies() enforces known physical or business limits.
- detect_cluster_anomalies() distinguishes isolated deviations from fleet-wide events.

Statistical anomalies are investigation candidates, not confirmed faults.

### 1.4 Change Points

Use detect_change_points() for shifts in mean or variability. Validate candidates against maintenance, load, recipe, shift, environment, missing data, sampling changes, and peer-device behavior.

## 2. Cross-Device Comparison

Compare devices only when template, operating regime, unit, time range, and aggregation are compatible. Segment by line, region, model, duty, or shift where relevant.

Use compare_series() to align buckets, classify_devices() for high/medium/low groups, and benchmark_analysis() to quantify peer gaps. A benchmark is observed performance, not proof that every peer can safely reach it.

Use calc_correlation() only after aligning timestamps and confirming both series vary. Always report n_pairs. Detrend shared time trends, inspect lags when process latency is plausible, and never describe correlation as causation.

| Absolute Pearson r | Practical label |
|---:|---|
| below 0.1 | negligible |
| 0.1 to below 0.3 | weak |
| 0.3 to below 0.5 | moderate |
| 0.5 or above | strong |

## 3. Statistical Methods

| Measure | Use | Limitation |
|---|---|---|
| Mean | Central tendency | Sensitive to extremes |
| Median | Robust center | Can hide multimodal behavior |
| Standard deviation | Absolute variability | Scale-dependent |
| Coefficient of variation | Relative variability | Unstable near zero |
| P25/P75 and IQR | Distribution width | Needs adequate samples |
| Minimum/maximum | Extreme conditions | Not representative of normal operation |

Use calc_stats() for a consistent calculation set. Use calc_compliance_rate() for accepted ranges and calc_deviation_rate() for target deviation. Normalize unequal calendar periods and report effect size as well as significance.

## 4. Domain Analysis Angles

### Energy

- peak/valley load and load factor with calc_peak_valley_ratio();
- input/output conversion with calc_efficiency();
- demand peaks, integrated energy, and idle consumption.

### Manufacturing

- availability, performance, quality, and OEE with calc_oee();
- process stability, cycle consistency, setpoint deviation, and bottlenecks;
- comparisons by line, product, recipe, and shift.

### Environmental Monitoring

- compliance rates and consecutive compliant periods;
- exceedance duration and recurrence;
- changes relative to flow, load, weather, or operating state.

### Buildings and Facilities

- occupancy and schedule-related profiles;
- day/night and weekday/weekend baselines;
- simultaneous HVAC, power, temperature, and air-quality changes.

## 5. Limited Data

| Available data | Appropriate analysis |
|---|---|
| At least seven complete days | Trend, anomalies, periodicity, change points |
| One to six days | Descriptive statistics and cautious trend direction |
| 20-99 points | Point-level analysis; avoid fine buckets |
| Fewer than 20 points | Brief statistics and a sparse-data warning |
| Current values only | Cross-device snapshot, distribution, grouping |
| No data | Report the gap and recommend checking collection |

Never manufacture a requested resolution. Six-hour sampling cannot support minute-level conclusions.

## 6. Time-Series Features

- lag_features() supports delayed relationships and state prediction.
- rolling_stats() supports stability monitoring with meaningful-duration windows.
- ewm_features() emphasizes recent observations and gradual drift.
- diff_features() exposes abrupt changes; guard percentage changes near zero.
- cyclic_encode() represents daily, weekly, shift, or seasonal cycles.
- interaction_features() derives difference, ratio, and product from aligned series.

## 7. Data Quality

Run data_quality_check() first.

| Check | Default signal | Severity |
|---|---|---|
| Missing values | above 5% warning; above 10% critical | warning/critical |
| Duplicate timestamps | any | warning |
| Irregular intervals | above 10% irregular | warning |
| IQR outliers | outside 1.5 x IQR | informational/warning |
| High skew | absolute skew above 2 | informational |
| Small sample | fewer than 100 points | informational |

| Method | Strength | Limitation | Use |
|---|---|---|---|
| IQR, factor 1.5 | Robust to extremes | Less informative for strong asymmetry | Unknown distributions |
| Sigma, 2-3 sigma | Tunable | Distorted by extremes | Approximately normal stable signals |
| Absolute limits | Explainable | Requires domain knowledge | Safety or quality limits |

auto_insights() summarizes quality, trend, anomalies, change points, periodicity, variability, and skewness. Review its output against raw evidence.

## 8. Decision Communication

Before analysis, establish the decision, evidence that could change it, available versus desired data, and relevant time/operating context.

- State the answer before the method.
- Quantify uncertainty with ranges.
- Name limitations and alternative explanations.
- Recommend the smallest next step that strengthens the decision.

Use format_decision_brief(), format_anomaly_record(), or format_executive_summary() when appropriate. For a full report, use [Report Structure](report-structure.md).

## 9. Analytical Traps

| Trap | Symptom | Prevention |
|---|---|---|
| Simpson's paradox | Aggregate trend reverses after segmentation | Segment by relevant dimensions |
| Survivorship bias | Only active devices are analyzed | Include failed and offline devices |
| Unequal periods | Calendar totals are compared directly | Normalize to daily rates |
| Spurious time correlation | Two upward trends appear correlated | Detrend first |
| Averaging percentages | Percentages are averaged without weights | Recalculate from counts |
| Causal confusion | Association is described as cause | Control confounders |
| Significance without importance | Tiny effect has low p-value | Report effect size |
| Multiple comparisons | Many tests inflate false positives | Use Bonferroni or Holm correction |

| Cohen's d | Interpretation | Absolute Pearson r | Interpretation |
|---:|---|---:|---|
| 0.2 | small | 0.1 | weak |
| 0.5 | medium | 0.3 | moderate |
| 0.8 | large | 0.5 | strong |

## 10. Derived Metrics

| Requested metric | Required attributes | Calculation |
|---|---|---|
| Energy consumption | Power | Trapezoidal integration of power over time |
| Water consumption | Flow rate | Sum of average adjacent flow times elapsed seconds |
| Conversion efficiency | Input/output energy | output / input * 100%, or calc_efficiency() |
| Utilization | Current value and Min/Max traits | (value - min) / (max - min) * 100% |
| Range | Numeric metric | max - min per bucket |
| Time-weighted mean | Numeric metric | sum(value * elapsed time) / total elapsed time |
| Difference or ratio trend | Two metrics | Align timestamps, then calculate point by point |
| Production share | Production across devices | Sum by group, divide by total |
| Fault rate | Boolean fault signal | true count / total * 100% |
| Downtime rate | Boolean running signal | false count / total * 100% |
| Setpoint deviation | Setpoint and measurement | absolute difference / absolute setpoint; skip near-zero setpoints |
| Availability | Boolean running signal | true count / total * 100% |
| Health index | Coefficient of variation | Map CV below 5% to 100 and above 50% to 0 |

## 11. Industrial Data Patterns

These are discovery hints, not contracts. Verify actual metadata and sampling.

| Device family | Typical interval | Approximate seven-day points | Pagination |
|---|---:|---:|---|
| Meters, batteries, environmental sensors, transformers, water systems | 10 minutes | 1,000 | 2-3 pages |
| Solar and weather sensors | 10 minutes | 1,000 | 2-3 pages |
| Wells, vehicles, low-frequency production equipment | 6 hours | 28 | 1 page |

| Hazard | Example | Safe handling |
|---|---|---|
| Boolean returned as text | true/false strings | Compare explicitly |
| Integer returned as text | numeric string | Convert with float() |
| Identical batch snapshots | Same current value across devices | Use history for rankings |
| Different child schemas | Peers expose different attributes | Verify existence first |
| Same name, different IDs | Per-device attribute IDs | Discover attributes per device |
| Variable response envelope | List or object | Check type before iteration |

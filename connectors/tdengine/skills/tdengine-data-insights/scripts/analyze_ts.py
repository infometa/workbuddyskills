"""Reusable, standard-library time-series analysis utilities.

Supports raw data returned by get_attribute_history and aggregated query data
returned by get_panel. The module can be imported or invoked as a CLI.
"""
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any


# ============================================================
# 1. Time utilities
# ============================================================

def now_ms() -> int:
    """Return the current UTC Unix timestamp in milliseconds."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def ago_ms(days: int = 0, hours: int = 0) -> int:
    """Return the UTC Unix timestamp for the specified offset before now."""
    dt = datetime.now(timezone.utc) - timedelta(days=days, hours=hours)
    return int(dt.timestamp() * 1000)


def ms_to_dt(ms: int) -> datetime:
    """Convert Unix milliseconds to a UTC datetime."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def ms_to_str(ms: int, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format Unix milliseconds as a UTC string."""
    return ms_to_dt(ms).strftime(fmt)


# ============================================================
# 2. Data loading
# ============================================================

def load_attribute_history(data: dict) -> list[dict]:
    """
    Normalize a get_attribute_history response.

    Numeric strings become floats. Boolean and other nonnumeric strings are
    preserved.
    """
    results = []
    for item in data.get("items", []):
        raw = item["value"]
        if isinstance(raw, bool) or raw is None:
            val = raw
        else:
            try:
                val = float(raw)
            except (ValueError, TypeError):
                val = raw  # Preserve Boolean and Varchar values.
        results.append({"ts": ms_to_dt(item["updatedTime"]), "ts_ms": item["updatedTime"], "value": val})
    return results


def load_panel_queries(data: dict) -> list[tuple[list[str], list[list]]]:
    """
    Normalize every get_panel query_data result as column names and rows.
    """
    queries = []
    for query in data.get("query_data", []):
        columns = [col[0] for col in query.get("columnMeta", []) if col]
        queries.append((columns, query.get("data", [])))
    return queries


def load_panel_query(data: dict) -> tuple[list[str], list[list]]:
    """Normalize a panel response only when it contains one query result."""
    queries = load_panel_queries(data)
    if len(queries) > 1:
        raise ValueError("panel contains multiple query results; use load_panel_queries")
    return queries[0] if queries else ([], [])


def is_numeric_value(value: Any) -> bool:
    """Return whether a value is a finite number suitable for statistics."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def numeric_values(values: list[Any]) -> list[float]:
    """Return finite numeric values while excluding Boolean states."""
    return [float(value) for value in values if is_numeric_value(value)]


# ============================================================
# 3. Time bucketing and aggregation
# ============================================================

def bucket_by(items: list[dict], bucket: str = "day") -> dict[str, list[float]]:
    """
    Bucket normalized points by day, hour, or weekday.
    """
    buckets = defaultdict(list)
    for item in items:
        dt = item["ts"]
        if bucket == "day":
            key = dt.strftime("%Y-%m-%d")
        elif bucket == "hour":
            key = dt.strftime("%Y-%m-%d %H:00")
        elif bucket == "weekday":
            key = dt.strftime("%A")  # Monday, Tuesday, ...
        else:
            key = dt.strftime("%Y-%m-%d")
        if is_numeric_value(item.get("value")):
            buckets[key].append(float(item["value"]))
    return dict(sorted(buckets.items()))


def calc_stats(values: list[float]) -> dict[str, float]:
    """Calculate descriptive statistics, including quantiles and IQR."""
    values = numeric_values(values)
    if not values:
        return {"count": 0}
    n = len(values)
    sv = sorted(values)
    result = {
        "count": n,
        "sum": sum(values),
        "avg": statistics.mean(values),
        "median": statistics.median(values),
        "max": max(values),
        "min": min(values),
        "spread": max(values) - min(values),
    }
    if n > 1:
        result["stdev"] = statistics.stdev(values)
        result["cv"] = result["stdev"] / result["avg"] if result["avg"] != 0 else 0
    else:
        result["stdev"] = 0.0
        result["cv"] = 0.0
    # Quantiles and IQR
    if n >= 4:
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        result["p25"] = sv[q1_idx]
        result["p75"] = sv[q3_idx]
        result["iqr"] = result["p75"] - result["p25"]
    return result


def aggregate_buckets(buckets: dict[str, list[float]]) -> dict[str, dict]:
    """Calculate statistics for every bucket."""
    return {key: calc_stats(vals) for key, vals in buckets.items()}


# ============================================================
# 4. Trend and period-over-period analysis
# ============================================================

def calc_changes(agg: dict[str, dict], metric: str = "avg") -> list[dict]:
    """
    Calculate percentage changes between adjacent buckets.
    """
    keys = list(agg.keys())
    changes = []
    for i in range(1, len(keys)):
        prev_val = agg[keys[i - 1]].get(metric, 0)
        curr_val = agg[keys[i]].get(metric, 0)
        pct = ((curr_val - prev_val) / prev_val * 100) if prev_val != 0 else 0
        changes.append({
            "from": keys[i - 1],
            "to": keys[i],
            "prev": round(prev_val, 4),
            "curr": round(curr_val, 4),
            "change_pct": round(pct, 2),
        })
    return changes


# ============================================================
# 5. Anomaly detection
# ============================================================

def detect_anomalies(agg: dict[str, dict], metric: str = "avg", sigma: float = 1.0) -> list[dict]:
    """
    Detect buckets outside mean plus or minus sigma times standard deviation.
    """
    vals = [s[metric] for s in agg.values() if metric in s]
    if len(vals) < 3:
        return []
    mean = statistics.mean(vals)
    std = statistics.stdev(vals)
    threshold_high = mean + sigma * std
    threshold_low = mean - sigma * std
    anomalies = []
    for key, stats in agg.items():
        v = stats.get(metric, 0)
        if v > threshold_high:
            anomalies.append({"key": key, "value": round(v, 4), "deviation": round(v - mean, 4), "direction": "high"})
        elif v < threshold_low:
            anomalies.append({"key": key, "value": round(v, 4), "deviation": round(v - mean, 4), "direction": "low"})
    return anomalies


def detect_absolute_anomalies(items: list[dict], low: float = None, high: float = None) -> list[dict]:
    """
    Detect points outside absolute physical or business limits.
    """
    anomalies = []
    for item in items:
        v = item["value"]
        if high is not None and v > high:
            anomalies.append({"ts": ms_to_str(item["ts_ms"]), "ts_ms": item["ts_ms"], "value": v, "direction": "high"})
        elif low is not None and v < low:
            anomalies.append({"ts": ms_to_str(item["ts_ms"]), "ts_ms": item["ts_ms"], "value": v, "direction": "low"})
    return anomalies


def detect_cluster_anomalies(
    multi_items: dict[str, list[dict]], bucket: str = "hour", sigma: float = 2.0
) -> list[dict]:
    """
    Detect simultaneous anomalies across multiple devices.
    """
    device_anomaly_keys: dict[str, set] = {}
    for name, items in multi_items.items():
        buckets = bucket_by(items, bucket)
        agg = aggregate_buckets(buckets)
        anomalies = detect_anomalies(agg, sigma=sigma)
        device_anomaly_keys[name] = {a["key"] for a in anomalies}

    all_keys = sorted(set(k for ks in device_anomaly_keys.values() for k in ks))
    results = []
    for key in all_keys:
        hit_devices = [name for name, ks in device_anomaly_keys.items() if key in ks]
        results.append({
            "key": key,
            "anomaly_devices": hit_devices,
            "count": len(hit_devices),
            "is_cluster": len(hit_devices) >= max(2, len(multi_items) // 2),
        })
    return [r for r in results if r["count"] > 1]


# ============================================================
# 5b. Trend analysis
# ============================================================

def moving_average(items: list[dict], window: int = 5) -> list[dict]:
    """
    Calculate a simple moving average.
    """
    result = []
    vals = [it["value"] for it in items]
    for i, item in enumerate(items):
        if i < window - 1:
            ma = statistics.mean(vals[: i + 1])
        else:
            ma = statistics.mean(vals[i - window + 1 : i + 1])
        result.append({**item, "ma": round(ma, 4)})
    return result


def detect_trend(agg: dict[str, dict], metric: str = "avg") -> dict:
    """
    Fit a simple linear trend to an aggregated series.
    """
    keys = list(agg.keys())
    vals = [agg[k].get(metric, 0) for k in keys]
    n = len(vals)
    if n < 2:
        return {"direction": "flat", "slope": 0, "r_squared": 0}
    xs = list(range(n))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(vals)
    ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, vals))
    ss_xx = sum((x - x_mean) ** 2 for x in xs)
    ss_yy = sum((y - y_mean) ** 2 for y in vals)
    slope = ss_xy / ss_xx if ss_xx != 0 else 0
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_xx * ss_yy != 0 else 0
    total_change = vals[-1] - vals[0]
    total_change_pct = (total_change / vals[0] * 100) if vals[0] != 0 else 0

    if r_squared < 0.3:
        direction = "flat"
    elif slope > 0:
        direction = "up"
    else:
        direction = "down"

    changes = calc_changes(agg, metric)
    avg_change_pct = statistics.mean([c["change_pct"] for c in changes]) if changes else 0

    return {
        "direction": direction,
        "slope": round(slope, 4),
        "r_squared": round(r_squared, 4),
        "total_change_pct": round(total_change_pct, 2),
        "avg_change_pct": round(avg_change_pct, 2),
        "first_value": round(vals[0], 4),
        "last_value": round(vals[-1], 4),
    }


def detect_inflection_points(agg: dict[str, dict], metric: str = "avg") -> list[dict]:
    """
    Detect local peaks and valleys.
    """
    keys = list(agg.keys())
    vals = [agg[k].get(metric, 0) for k in keys]
    points = []
    for i in range(1, len(vals) - 1):
        if vals[i] > vals[i - 1] and vals[i] > vals[i + 1]:
            points.append({"key": keys[i], "type": "peak", "value": round(vals[i], 4)})
        elif vals[i] < vals[i - 1] and vals[i] < vals[i + 1]:
            points.append({"key": keys[i], "type": "valley", "value": round(vals[i], 4)})
    return points


# ============================================================
# 5c. Periodicity and seasonality
# ============================================================

def overlay_periods(items: list[dict], period: str = "day") -> dict[str, list[float]]:
    """
    Overlay equivalent positions across days, weeks, or months.
    """
    buckets = defaultdict(list)
    for item in items:
        dt = item["ts"]
        if period == "day":
            key = dt.strftime("%H:00")
        elif period == "week":
            key = dt.strftime("%A")
        elif period == "month":
            key = dt.strftime("Day-%d")
        else:
            key = dt.strftime("%H:00")
        buckets[key].append(item["value"])
    return dict(sorted(buckets.items()))


def detect_periodicity(items: list[dict]) -> dict:
    """
    Compare intraday and workday/weekend patterns.
    """
    hourly = defaultdict(list)
    workday_vals = []
    weekend_vals = []
    for item in items:
        if not is_numeric_value(item.get("value")):
            continue
        dt = item["ts"]
        value = float(item["value"])
        hourly[dt.hour].append(value)
        if dt.weekday() < 5:
            workday_vals.append(value)
        else:
            weekend_vals.append(value)

    hourly_stats = {f"{h:02d}:00": calc_stats(vs) for h, vs in sorted(hourly.items())}
    hourly_avgs = {h: s.get("avg", 0) for h, s in hourly_stats.items()}

    if hourly_avgs:
        overall_avg = statistics.mean(hourly_avgs.values())
        peak_hours = [h for h, v in hourly_avgs.items() if v > overall_avg * 1.1]
        valley_hours = [h for h, v in hourly_avgs.items() if v < overall_avg * 0.9]
    else:
        peak_hours, valley_hours = [], []

    result = {
        "hourly_pattern": hourly_stats,
        "peak_hours": peak_hours,
        "valley_hours": valley_hours,
    }
    if workday_vals and weekend_vals:
        result["workday_vs_weekend"] = {
            "workday": calc_stats(workday_vals),
            "weekend": calc_stats(weekend_vals),
        }
    return result


def has_intraday_coverage(items: list[dict], min_coverage: float = 0.8) -> bool:
    """Return whether samples cover at least two usable 24-hour cycles."""
    timestamps = sorted({item["ts"] for item in items if isinstance(item.get("ts"), datetime)})
    if len(timestamps) < 3:
        return False

    intervals = [
        (current - previous).total_seconds()
        for previous, current in zip(timestamps, timestamps[1:])
        if current > previous
    ]
    if not intervals:
        return False
    cadence_seconds = statistics.median(intervals)
    if cadence_seconds <= 0 or cadence_seconds > 2 * 60 * 60:
        return False

    timestamps_by_day = defaultdict(list)
    for timestamp in timestamps:
        timestamps_by_day[timestamp.date()].append(timestamp)
    expected_per_day = 24 * 60 * 60 / cadence_seconds
    return sum(
        1
        for day_timestamps in timestamps_by_day.values()
        if len(day_timestamps) >= expected_per_day * min_coverage
    ) >= 2


# ============================================================
# 5d. Change-point detection
# ============================================================

def detect_change_points(agg: dict[str, dict], metric: str = "avg", min_change_pct: float = 20.0) -> list[dict]:
    """
    Detect the strongest shift in mean or variability.
    """
    keys = list(agg.keys())
    vals = [agg[k].get(metric, 0) for k in keys]
    n = len(vals)
    if n < 4:
        return []

    results = []
    # Mean shift
    best_diff = 0
    best_idx = -1
    for i in range(2, n - 1):
        before_mean = statistics.mean(vals[:i])
        after_mean = statistics.mean(vals[i:])
        diff = abs(after_mean - before_mean)
        if diff > best_diff:
            best_diff = diff
            best_idx = i

    if best_idx > 0:
        before_mean = statistics.mean(vals[:best_idx])
        after_mean = statistics.mean(vals[best_idx:])
        change_pct = abs((after_mean - before_mean) / before_mean * 100) if before_mean != 0 else 0
        if change_pct >= min_change_pct:
            results.append({
                "split_at": keys[best_idx],
                "type": "mean_shift",
                "before": {"avg": round(before_mean, 4), "count": best_idx},
                "after": {"avg": round(after_mean, 4), "count": n - best_idx},
                "change_pct": round(change_pct, 2),
            })

    # Variability shift
    if n >= 6:
        best_var_ratio = 0
        best_var_idx = -1
        for i in range(3, n - 2):
            before_std = statistics.stdev(vals[:i])
            after_std = statistics.stdev(vals[i:])
            ratio = max(after_std, 0.001) / max(before_std, 0.001)
            ratio_diff = abs(ratio - 1)
            if ratio_diff > best_var_ratio:
                best_var_ratio = ratio_diff
                best_var_idx = i

        if best_var_idx > 0 and best_var_ratio > 0.5:
            before_std = statistics.stdev(vals[:best_var_idx])
            after_std = statistics.stdev(vals[best_var_idx:])
            results.append({
                "split_at": keys[best_var_idx],
                "type": "variance_shift",
                "before": {"stdev": round(before_std, 4), "count": best_var_idx},
                "after": {"stdev": round(after_std, 4), "count": n - best_var_idx},
                "change_pct": round(abs(after_std - before_std) / max(before_std, 0.001) * 100, 2),
            })
    return results


# ============================================================
# 5e. Device comparison and grouping
# ============================================================

def classify_devices(
    device_stats: dict[str, dict], metric: str = "avg", groups: int = 3
) -> dict[str, list[str]]:
    """
    Classify devices into high, medium, and low groups.
    """
    scored = sorted(device_stats.items(), key=lambda x: x[1].get(metric, 0), reverse=True)
    n = len(scored)
    if n < 3:
        return {"all": [name for name, _ in scored]}
    cut1 = n // 3
    cut2 = 2 * n // 3
    return {
        "high": [name for name, _ in scored[:cut1]],
        "medium": [name for name, _ in scored[cut1:cut2]],
        "low": [name for name, _ in scored[cut2:]],
    }


def benchmark_analysis(device_stats: dict[str, dict], metric: str = "avg") -> dict:
    """
    Identify the benchmark device and calculate peer gaps.
    """
    if not device_stats:
        return {}
    best_name = max(device_stats, key=lambda n: device_stats[n].get(metric, 0))
    best_val = device_stats[best_name].get(metric, 0)
    gaps = []
    for name, stats in sorted(device_stats.items(), key=lambda x: x[1].get(metric, 0), reverse=True):
        if name == best_name:
            continue
        v = stats.get(metric, 0)
        gap = best_val - v
        gap_pct = (gap / best_val * 100) if best_val != 0 else 0
        gaps.append({"device": name, "value": round(v, 4), "gap": round(gap, 4), "gap_pct": round(gap_pct, 2)})
    return {
        "benchmark": best_name,
        "benchmark_value": round(best_val, 4),
        "gaps": gaps,
    }


def calc_correlation(items_a: list[dict], items_b: list[dict], bucket: str = "hour") -> dict:
    """
    Calculate Pearson correlation after aligning time buckets.
    """
    agg_a = aggregate_buckets(bucket_by(items_a, bucket))
    agg_b = aggregate_buckets(bucket_by(items_b, bucket))
    common_keys = sorted(set(agg_a.keys()) & set(agg_b.keys()))
    if len(common_keys) < 3:
        return {"r": 0, "interpretation": "insufficient data", "n_pairs": len(common_keys)}

    va = [agg_a[k]["avg"] for k in common_keys]
    vb = [agg_b[k]["avg"] for k in common_keys]
    n = len(va)
    mean_a, mean_b = statistics.mean(va), statistics.mean(vb)
    cov = sum((a - mean_a) * (b - mean_b) for a, b in zip(va, vb)) / (n - 1)
    std_a = statistics.stdev(va)
    std_b = statistics.stdev(vb)
    r = cov / (std_a * std_b) if std_a * std_b != 0 else 0

    interp = correlation_label(r)

    return {"r": round(r, 4), "interpretation": interp, "n_pairs": n}


def correlation_label(value: float) -> str:
    """Return the practical Pearson-correlation label used by the methodology."""
    magnitude = abs(value)
    if magnitude >= 0.5:
        strength = "strong"
    elif magnitude >= 0.3:
        strength = "moderate"
    elif magnitude >= 0.1:
        strength = "weak"
    else:
        return "negligible"
    return f"{strength} {'positive' if value > 0 else 'negative'}"


# ============================================================
# 5f. Comparative calculations
# ============================================================

def calc_compliance_rate(values: list[float], low: float = None, high: float = None) -> dict:
    """
    Calculate the percentage of values within inclusive bounds.
    """
    total = len(values)
    if total == 0:
        return {"total": 0, "compliant": 0, "rate_pct": 0}
    compliant = 0
    for v in values:
        ok = True
        if low is not None and v < low:
            ok = False
        if high is not None and v > high:
            ok = False
        if ok:
            compliant += 1
    return {"total": total, "compliant": compliant, "rate_pct": round(compliant / total * 100, 2)}


def calc_deviation_rate(values: list[float], target: float) -> dict:
    """
    Calculate percentage deviations from a target.
    """
    if not values or target == 0:
        return {}
    deviations = [abs(v - target) / abs(target) * 100 for v in values]
    return {
        "avg_deviation_pct": round(statistics.mean(deviations), 2),
        "max_deviation_pct": round(max(deviations), 2),
        "within_5pct": sum(1 for d in deviations if d <= 5),
        "within_10pct": sum(1 for d in deviations if d <= 10),
        "total": len(values),
    }


# ============================================================
# 5g. Domain calculations
# ============================================================

def calc_peak_valley_ratio(items: list[dict]) -> dict:
    """
    Calculate hourly peak-to-valley ratio and load factor.
    """
    hourly = bucket_by(items, "hour")
    if not hourly:
        return {}
    agg = aggregate_buckets(hourly)
    peak_key = max(agg, key=lambda k: agg[k].get("avg", 0))
    valley_key = min(agg, key=lambda k: agg[k].get("avg", 0))
    peak_avg = agg[peak_key]["avg"]
    valley_avg = agg[valley_key]["avg"]
    ratio = peak_avg / valley_avg if valley_avg != 0 else float("inf")
    all_vals = [it["value"] for it in items]
    load_factor = statistics.mean(all_vals) / max(all_vals) if max(all_vals) != 0 else 0
    return {
        "peak_hour": peak_key,
        "peak_avg": round(peak_avg, 4),
        "valley_hour": valley_key,
        "valley_avg": round(valley_avg, 4),
        "peak_valley_ratio": round(ratio, 4),
        "load_factor": round(load_factor, 4),
    }


def calc_efficiency(input_items: list[dict], output_items: list[dict], bucket: str = "day") -> dict:
    """
    Calculate input-to-output conversion efficiency.
    """
    in_agg = aggregate_buckets(bucket_by(input_items, bucket))
    out_agg = aggregate_buckets(bucket_by(output_items, bucket))
    common = sorted(set(in_agg.keys()) & set(out_agg.keys()))
    per_bucket = {}
    efficiencies = []
    for k in common:
        in_v = in_agg[k]["avg"]
        out_v = out_agg[k]["avg"]
        eff = (out_v / in_v * 100) if in_v != 0 else 0
        per_bucket[k] = {"input": round(in_v, 4), "output": round(out_v, 4), "efficiency_pct": round(eff, 2)}
        efficiencies.append(eff)

    overall_eff = calc_stats(efficiencies) if efficiencies else {}
    return {"per_bucket": per_bucket, "overall_efficiency": overall_eff}


def calc_continuous_compliance(values: list[float], low: float = None, high: float = None) -> dict:
    """
    Calculate consecutive compliant periods.
    """
    streaks = []
    current = 0
    for v in values:
        ok = True
        if low is not None and v < low:
            ok = False
        if high is not None and v > high:
            ok = False
        if ok:
            current += 1
        else:
            if current > 0:
                streaks.append(current)
            current = 0
    if current > 0:
        streaks.append(current)
    return {
        "current_streak": current,
        "max_streak": max(streaks) if streaks else 0,
        "total_compliant": sum(streaks),
        "total": len(values),
        "streak_count": len(streaks),
    }


def calc_oee(availability_pct: float, performance_pct: float, quality_pct: float) -> dict:
    """
    Calculate OEE from availability, performance, and quality percentages.
    """
    oee = availability_pct / 100 * performance_pct / 100 * quality_pct / 100 * 100
    bottleneck = min(
        [("availability", availability_pct), ("performance", performance_pct), ("quality", quality_pct)],
        key=lambda x: x[1],
    )[0]
    return {
        "oee_pct": round(oee, 2),
        "availability": round(availability_pct, 2),
        "performance": round(performance_pct, 2),
        "quality": round(quality_pct, 2),
        "bottleneck": bottleneck,
    }


# ============================================================
# 6. Aggregated panel data
# ============================================================

def analyze_panel_data(columns: list[str], rows: list[list]) -> dict:
    """
    Analyze aggregated query data returned by get_panel.
    """
    if not rows or not columns:
        return {"error": "no data"}

    ts_col_idx = None
    candidate_cols = []
    for i, col in enumerate(columns):
        if col.lower() in ("_wstart", "_wend", "ts", "timestamp", "_c0"):
            ts_col_idx = i
        else:
            candidate_cols.append((i, col))

    result = {
        "total_rows": len(rows),
        "columns": columns,
        "time_range": {},
        "series": {},
        "dimensions": {},
    }

    # Observed time range
    timestamps = sorted(
        row[ts_col_idx]
        for row in rows
        if ts_col_idx is not None
        and len(row) > ts_col_idx
        and is_numeric_value(row[ts_col_idx])
    )
    if timestamps:
        result["time_range"] = {
            "start": ms_to_str(timestamps[0]),
            "end": ms_to_str(timestamps[-1]),
            "start_ms": timestamps[0],
            "end_ms": timestamps[-1],
        }

    numeric_cols = []
    for col_idx, col_name in candidate_cols:
        vals = [row[col_idx] for row in rows if len(row) > col_idx and row[col_idx] is not None]
        numeric = numeric_values(vals)
        if numeric:
            numeric_cols.append((col_idx, col_name))
            stats = calc_stats(numeric)
            stats["non_numeric_count"] = len(vals) - len(numeric)
            result["series"][col_name] = stats
            continue

        counts = Counter(str(value) for value in vals)
        result["dimensions"][col_name] = {
            "count": len(vals),
            "distinct_count": len(counts),
            "top_values": [[value, count] for value, count in counts.most_common(10)],
        }

    # Calculate spread when two numeric columns are available.
    if len(numeric_cols) == 2:
        idx_a, name_a = numeric_cols[0]
        idx_b, name_b = numeric_cols[1]
        spreads = []
        high_volatility = []
        for row in rows:
            if len(row) <= max(idx_a, idx_b):
                continue
            va, vb = row[idx_a], row[idx_b]
            if is_numeric_value(va) and is_numeric_value(vb):
                sp = abs(va - vb)
                spreads.append(sp)

        if spreads:
            sp_stats = calc_stats(spreads)
            result["spread_analysis"] = {
                "between": f"{name_a} vs {name_b}",
                "stats": sp_stats,
            }
            # High-volatility periods above mean plus one sigma.
            threshold = sp_stats["avg"] + sp_stats["stdev"]
            for i, row in enumerate(rows):
                if len(row) <= max(idx_a, idx_b):
                    continue
                va, vb = row[idx_a], row[idx_b]
                if is_numeric_value(va) and is_numeric_value(vb):
                    sp = abs(va - vb)
                    if sp > threshold:
                        ts_str = ms_to_str(row[ts_col_idx]) if ts_col_idx is not None else str(i)
                        high_volatility.append({
                            "time": ts_str,
                            name_a: round(va, 4),
                            name_b: round(vb, 4),
                            "spread": round(sp, 4),
                        })
            result["spread_analysis"]["high_volatility_count"] = len(high_volatility)
            result["spread_analysis"]["high_volatility_threshold"] = round(threshold, 4)
            result["spread_analysis"]["high_volatility_samples"] = high_volatility[:10]

    # Day versus night comparison when timestamps are available.
    if ts_col_idx is not None and numeric_cols:
        day_vals = defaultdict(list)
        night_vals = defaultdict(list)
        for row in rows:
            if len(row) <= ts_col_idx or not is_numeric_value(row[ts_col_idx]):
                continue
            hour = ms_to_dt(row[ts_col_idx]).hour
            for col_idx, col_name in numeric_cols:
                if len(row) <= col_idx:
                    continue
                v = row[col_idx]
                if is_numeric_value(v):
                    if 6 <= hour < 18:
                        day_vals[col_name].append(v)
                    else:
                        night_vals[col_name].append(v)
        if day_vals and night_vals:
            result["day_night_comparison"] = {}
            for col_name in [c[1] for c in numeric_cols]:
                result["day_night_comparison"][col_name] = {
                    "day_06_18": calc_stats(day_vals.get(col_name, [])),
                    "night_18_06": calc_stats(night_vals.get(col_name, [])),
                }

    return result


def analyze_panel_queries(queries: list[tuple[list[str], list[list]]]) -> dict:
    """Analyze every normalized result set returned by a panel query."""
    return {
        "query_count": len(queries),
        "queries": [analyze_panel_data(columns, rows) for columns, rows in queries],
    }


# ============================================================
# 7. Multi-series comparison
# ============================================================

def compare_series(series: dict[str, list[dict]], bucket: str = "day") -> dict:
    """
    Compare multiple attribute or device series on aligned buckets.
    """
    all_agg = {}
    for name, items in series.items():
        buckets = bucket_by(items, bucket)
        all_agg[name] = aggregate_buckets(buckets)

    # Align all bucket keys.
    all_keys = sorted(set(k for agg in all_agg.values() for k in agg))
    comparison = {}
    for key in all_keys:
        comparison[key] = {}
        for name, agg in all_agg.items():
            comparison[key][name] = agg.get(key, {"count": 0})

    return {"bucket": bucket, "series_names": list(series.keys()), "data": comparison}


# ============================================================
# 10a. Basic Markdown formatting
# ============================================================

def stats_to_md_row(label: str, stats: dict) -> str:
    """Format statistics as one Markdown table row."""
    return (
        f"| {label} | {stats.get('count', 0)} | {stats.get('avg', 0):.2f} | "
        f"{stats.get('median', 0):.2f} | {stats.get('max', 0):.2f} | {stats.get('min', 0):.2f} | "
        f"{stats.get('stdev', 0):.2f} | {stats.get('spread', 0):.2f} |"
    )


def format_agg_table(agg: dict[str, dict], value_label: str = "Value") -> str:
    """Format aggregated statistics as a Markdown table."""
    lines = [
        "| Period | Count | Mean | Median | Maximum | Minimum | Std dev | Range |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, stats in agg.items():
        lines.append(stats_to_md_row(key, stats))
    return "\n".join(lines)


def format_changes_table(changes: list[dict]) -> str:
    """Format period-over-period changes as a Markdown table."""
    lines = [
        "| From | To | Previous | Current | Change |",
        "|---|---|---:|---:|---:|",
    ]
    for c in changes:
        lines.append(f"| {c['from']} | {c['to']} | {c['prev']:.2f} | {c['curr']:.2f} | {c['change_pct']:+.1f}% |")
    return "\n".join(lines)


def format_anomalies_table(anomalies: list[dict]) -> str:
    """Format anomalies as a Markdown table."""
    if not anomalies:
        return "No anomalous periods detected."
    lines = [
        "| Period | Value | Deviation | Direction |",
        "|---|---:|---:|---|",
    ]
    for a in anomalies:
        direction = "High" if a["direction"] == "high" else "Low"
        lines.append(f"| {a['key']} | {a['value']:.2f} | {a['deviation']:+.2f} | {direction} |")
    return "\n".join(lines)


# ============================================================
# 8. Time-series feature engineering
# ============================================================

def lag_features(items: list[dict], lags: list[int] = None) -> list[dict]:
    """
    Add values from previous steps as lag features.
    """
    if lags is None:
        lags = [1, 3, 5]
    vals = [it["value"] for it in items]
    result = []
    for i, item in enumerate(items):
        row = dict(item)
        for lag in lags:
            row[f"lag_{lag}"] = vals[i - lag] if i >= lag else None
        result.append(row)
    return result


def rolling_stats(items: list[dict], windows: list[int] = None) -> list[dict]:
    """
    Add rolling mean and standard-deviation features.
    """
    if windows is None:
        windows = [5, 10]
    vals = [it["value"] for it in items]
    result = []
    for i, item in enumerate(items):
        row = dict(item)
        for w in windows:
            start = max(0, i - w + 1)
            window_vals = vals[start : i + 1]
            row[f"roll_mean_{w}"] = statistics.mean(window_vals)
            row[f"roll_std_{w}"] = statistics.stdev(window_vals) if len(window_vals) > 1 else 0.0
        result.append(row)
    return result


def ewm_features(items: list[dict], spans: list[int] = None) -> list[dict]:
    """
    Add exponentially weighted means that emphasize recent values.
    """
    if spans is None:
        spans = [5, 10]
    result = []
    ewm_vals = {s: 0.0 for s in spans}
    for i, item in enumerate(items):
        row = dict(item)
        for s in spans:
            alpha = 2.0 / (s + 1)
            if i == 0:
                ewm_vals[s] = item["value"]
            else:
                ewm_vals[s] = alpha * item["value"] + (1 - alpha) * ewm_vals[s]
            row[f"ewm_{s}"] = round(ewm_vals[s], 6)
        result.append(row)
    return result


def diff_features(items: list[dict]) -> list[dict]:
    """
    Add first-difference and percentage-change features.
    """
    vals = [it["value"] for it in items]
    result = []
    for i, item in enumerate(items):
        row = dict(item)
        if i == 0:
            row["diff_1"] = 0.0
            row["pct_change"] = 0.0
        else:
            row["diff_1"] = vals[i] - vals[i - 1]
            row["pct_change"] = (row["diff_1"] / vals[i - 1] * 100) if vals[i - 1] != 0 else 0.0
        result.append(row)
    return result


def cyclic_encode(items: list[dict], period: str = "day") -> list[dict]:
    """
    Add sine/cosine encodings for daily, weekly, or yearly cycles.
    """
    result = []
    for item in items:
        row = dict(item)
        dt = item["ts"]
        if period == "day":
            fraction = (dt.hour * 3600 + dt.minute * 60 + dt.second) / 86400.0
        elif period == "week":
            fraction = dt.weekday() / 7.0
        elif period == "year":
            fraction = dt.timetuple().tm_yday / 365.0
        else:
            fraction = dt.hour / 24.0
        row["cycle_sin"] = round(math.sin(2 * math.pi * fraction), 6)
        row["cycle_cos"] = round(math.cos(2 * math.pi * fraction), 6)
        result.append(row)
    return result


def interaction_features(items_a: list[dict], items_b: list[dict], bucket: str = "hour") -> dict[str, dict]:
    """
    Calculate difference, ratio, and product features for two aligned series.
    """
    agg_a = aggregate_buckets(bucket_by(items_a, bucket))
    agg_b = aggregate_buckets(bucket_by(items_b, bucket))
    common = sorted(set(agg_a.keys()) & set(agg_b.keys()))
    result = {}
    for k in common:
        va = agg_a[k]["avg"]
        vb = agg_b[k]["avg"]
        result[k] = {
            "a": round(va, 4),
            "b": round(vb, 4),
            "diff": round(va - vb, 4),
            "ratio": round(va / (vb + 1e-7), 4),
            "product": round(va * vb, 4),
        }
    return result


# ============================================================
# 9. Data quality and automated insights
# ============================================================

def data_quality_check(items: list[dict]) -> dict:
    """
    Diagnose missing values, duplicates, irregular intervals, outliers, and skew.
    """
    issues = []
    n = len(items)
    if n == 0:
        return {"total": 0, "issues": [{"type": "empty", "severity": "critical", "detail": "No data"}], "score": 0}

    vals = [it["value"] for it in items]

    # 1. Missing values
    null_count = sum(1 for v in vals if v is None)
    if null_count > 0:
        pct = null_count / n * 100
        severity = "critical" if pct > 10 else "warning" if pct > 5 else "info"
        issues.append({"type": "missing_values", "severity": severity,
                        "detail": f"{null_count} missing values ({pct:.1f}%)"})

    # 2. Duplicate timestamps
    ts_set = set()
    dup_count = 0
    for it in items:
        if it["ts_ms"] in ts_set:
            dup_count += 1
        ts_set.add(it["ts_ms"])
    if dup_count > 0:
        issues.append({"type": "duplicate_timestamps", "severity": "warning",
                        "detail": f"{dup_count} duplicate timestamps ({dup_count / n * 100:.1f}%)"})

    # 3. Interval consistency
    if n >= 3:
        intervals = [items[i]["ts_ms"] - items[i - 1]["ts_ms"] for i in range(1, n)]
        intervals = [iv for iv in intervals if iv > 0]
        if intervals:
            median_interval = sorted(intervals)[len(intervals) // 2]
            irregular = sum(1 for iv in intervals if abs(iv - median_interval) > median_interval * 0.5)
            if irregular > len(intervals) * 0.1:
                issues.append({"type": "irregular_intervals", "severity": "warning",
                                "detail": f"{irregular}/{len(intervals)} irregular intervals "
                                           f"(median {median_interval / 1000:.0f}s)"})

    # 4. IQR outliers
    non_null = [v for v in vals if v is not None]
    if len(non_null) >= 4:
        sv = sorted(non_null)
        q1 = sv[len(sv) // 4]
        q3 = sv[3 * len(sv) // 4]
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count = sum(1 for v in non_null if v < lower or v > upper)
        if outlier_count > 0:
            pct = outlier_count / len(non_null) * 100
            severity = "warning" if pct > 5 else "info"
            issues.append({"type": "iqr_outliers", "severity": severity,
                            "detail": f"{outlier_count} IQR outliers ({pct:.1f}%) "
                                       f"outside [{lower:.2f}, {upper:.2f}]"})

    # 5. Skewness
    if len(non_null) >= 10:
        mean = statistics.mean(non_null)
        std = statistics.stdev(non_null)
        if std > 0:
            skew = sum((v - mean) ** 3 for v in non_null) / (len(non_null) * std ** 3)
            if abs(skew) > 2:
                issues.append({"type": "high_skewness", "severity": "info",
                                "detail": f"Skewness is {skew:.2f}; prefer the median over the mean"})

    # 6. Small sample
    if n < 100:
        issues.append({"type": "small_sample", "severity": "info",
                        "detail": f"Only {n} points; statistical confidence is limited"})

    # Data-quality score, 0-100.
    penalties = {"critical": 30, "warning": 10, "info": 2}
    score = max(0, 100 - sum(penalties.get(i["severity"], 0) for i in issues))

    return {"total": n, "issues": issues, "score": score}


def detect_iqr_outliers(values: list[float], factor: float = 1.5) -> dict:
    """
    Detect outliers with the robust IQR method.
    """
    if len(values) < 4:
        return {"count": 0, "outliers": []}
    sv = sorted(values)
    n = len(sv)
    q1 = sv[n // 4]
    q3 = sv[3 * n // 4]
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    outliers = []
    for i, v in enumerate(values):
        if v < lower:
            outliers.append({"index": i, "value": round(v, 4), "direction": "low"})
        elif v > upper:
            outliers.append({"index": i, "value": round(v, 4), "direction": "high"})
    return {
        "q1": round(q1, 4), "q3": round(q3, 4), "iqr": round(iqr, 4),
        "lower": round(lower, 4), "upper": round(upper, 4),
        "outliers": outliers, "count": len(outliers),
    }


def calc_skewness(values: list[float]) -> float:
    """Calculate skewness; absolute values above two indicate high skew."""
    n = len(values)
    if n < 3:
        return 0.0
    mean = statistics.mean(values)
    std = statistics.stdev(values)
    if std == 0:
        return 0.0
    return sum((v - mean) ** 3 for v in values) / (n * std ** 3)


def auto_insights(items: list[dict], bucket: str = "day") -> list[dict]:
    """
    Run the standard insight rules for one time series.
    """
    insights = []
    vals = [it["value"] for it in items]
    non_null = numeric_values(vals)

    if not non_null:
        return [{"category": "data", "icon": "error", "title": "No numeric data", "detail": "No finite numeric values are available", "severity": "critical"}]

    # Data quality
    quality = data_quality_check(items)
    for issue in quality["issues"]:
        insights.append({
            "category": "data_quality", "icon": "🔍",
            "title": issue["type"].replace("_", " ").title(),
            "detail": issue["detail"], "severity": issue["severity"],
        })

    # Trend
    buckets = bucket_by(items, bucket)
    agg = aggregate_buckets(buckets)
    if len(agg) >= 3:
        trend = detect_trend(agg)
        if trend["direction"] != "flat":
            icon = "📈" if trend["direction"] == "up" else "📉"
            insights.append({
                "category": "trend", "icon": icon,
                "title": f"{'Upward' if trend['direction'] == 'up' else 'Downward'} trend",
                "detail": f"Total change {trend['total_change_pct']:+.1f}%, R-squared={trend['r_squared']:.2f}",
                "severity": "info",
            })

    # Anomalous periods
    anomalies = detect_anomalies(agg, sigma=2.0)
    if anomalies:
        insights.append({
            "category": "anomaly", "icon": "⚠️",
            "title": f"{len(anomalies)} anomalous periods (2 sigma)",
            "detail": ", ".join(f"{a['key']}({a['direction']})" for a in anomalies[:5]),
            "severity": "warning",
        })

    # Change points
    cps = detect_change_points(agg)
    for cp in cps:
        insights.append({
            "category": "change_point", "icon": "🔄",
            "title": f"{cp['type'].replace('_', ' ').title()} at {cp['split_at']}",
            "detail": f"Change magnitude {cp['change_pct']:.1f}%",
            "severity": "warning" if cp["change_pct"] > 30 else "info",
        })

    # Periodicity
    if has_intraday_coverage(items):
        period = detect_periodicity(items)
        if period.get("peak_hours"):
            insights.append({
                "category": "periodicity", "icon": "🔁",
                "title": "Intraday periodic pattern",
                "detail": f"Peak periods: {', '.join(period['peak_hours'][:5])}; "
                          f"valleys: {', '.join(period['valley_hours'][:5])}",
                "severity": "info",
            })

    # Volatility
    stats = calc_stats(non_null)
    if stats.get("cv", 0) > 0.5:
        insights.append({
            "category": "volatility", "icon": "📊",
            "title": "High volatility",
            "detail": f"Coefficient of variation is {stats['cv']:.2f}",
            "severity": "info",
        })

    # Skewness
    skew = calc_skewness(non_null)
    if abs(skew) > 2:
        direction = "right-skewed with a high-value tail" if skew > 0 else "left-skewed with a low-value tail"
        insights.append({
            "category": "distribution", "icon": "📐",
            "title": f"Highly skewed distribution: {direction}",
            "detail": f"Skewness={skew:.2f}; mean {stats['avg']:.2f} versus median {stats['median']:.2f}",
            "severity": "info",
        })

    return insights


# ============================================================
# 10. Enhanced Markdown formatting
# ============================================================

def format_quality_report(quality: dict) -> str:
    """Format a data-quality result as Markdown."""
    lines = [f"### Data Quality (score: {quality['score']}/100)\n"]
    lines.append(f"Total points: {quality['total']}\n")
    if not quality["issues"]:
        lines.append("No data-quality issues detected.\n")
    else:
        icon_map = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
        lines.append("| Severity | Issue | Detail |")
        lines.append("|---|---|---|")
        for issue in quality["issues"]:
            icon = icon_map.get(issue["severity"], "⚪")
            lines.append(f"| {icon} {issue['severity']} | {issue['type']} | {issue['detail']} |")
    return "\n".join(lines)


def format_insights(insights: list[dict]) -> str:
    """Format automated insights as Markdown."""
    if not insights:
        return "No significant insights detected."
    lines = ["### Automated Insights\n"]
    for ins in insights:
        lines.append(f"- {ins['icon']} **{ins['title']}**: {ins['detail']}")
    return "\n".join(lines)


def format_trend_summary(trend: dict) -> str:
    """Format a trend as a one-line summary."""
    direction_map = {"up": "upward", "down": "downward", "flat": "flat"}
    d = direction_map.get(trend["direction"], trend["direction"])
    return (f"Trend: {d} | total change: {trend['total_change_pct']:+.1f}% | "
            f"average period change: {trend['avg_change_pct']:+.1f}% | R-squared={trend['r_squared']:.2f}")


def format_device_comparison(benchmark: dict) -> str:
    """Format a benchmark comparison as Markdown."""
    if not benchmark:
        return ""
    lines = [
        "### Device Benchmark\n",
        f"**Benchmark device**: {benchmark['benchmark']} (value: {benchmark['benchmark_value']})\n",
        "| Device | Value | Gap | Gap % |",
        "|---|---:|---:|---:|",
    ]
    for g in benchmark["gaps"]:
        lines.append(f"| {g['device']} | {g['value']} | {g['gap']} | {g['gap_pct']:.1f}% |")
    return "\n".join(lines)


# ============================================================
# 11. Decision-oriented templates
# ============================================================

def format_decision_brief(
    question: str, answer: str, evidence: list[str],
    confidence: str = "medium", caveats: list[str] = None,
    next_steps: list[str] = None,
) -> str:
    """
    Format a concise decision brief.
    """
    lines = [
        "## Decision Brief\n",
        f"**Decision question**: {question}\n",
        f"**Conclusion**: {answer}\n",
        f"**Confidence**: {confidence}\n",
        "### Evidence",
    ]
    for i, e in enumerate(evidence, 1):
        lines.append(f"{i}. {e}")
    if caveats:
        lines.append("\n### Caveats")
        for c in caveats:
            lines.append(f"- ⚠️ {c}")
    if next_steps:
        lines.append("\n### Recommended Next Steps")
        for i, s in enumerate(next_steps, 1):
            lines.append(f"{i}. {s}")
    return "\n".join(lines)


def format_anomaly_record(
    what_changed: str, since_when: str, possible_causes: list[str],
    data_quality_ok: bool = True, immediate_action: str = "",
    next_observation: str = "",
) -> str:
    """
    Format an anomaly record.
    """
    lines = [
        "## Anomaly Record\n",
        f"**What changed**: {what_changed}",
        f"**Since**: {since_when}",
        f"**Data quality**: {'verified' if data_quality_ok else 'questionable'}",
        "\n**Possible causes**:",
    ]
    for c in possible_causes:
        lines.append(f"- {c}")
    if immediate_action:
        lines.append(f"\n**Immediate action**: {immediate_action}")
    if next_observation:
        lines.append(f"**Next observation**: {next_observation}")
    return "\n".join(lines)


def format_executive_summary(
    one_line: str, supporting_points: list[str],
    caveat: str = "", ask: str = "",
) -> str:
    """
    Format an executive summary.
    """
    lines = ["## Executive Summary\n", f"**{one_line}**\n"]
    for p in supporting_points:
        lines.append(f"- {p}")
    if caveat:
        lines.append(f"\n**Caveat**: {caveat}")
    if ask:
        lines.append(f"\n**Decision request**: {ask}")
    return "\n".join(lines)

def main():
    """
    CLI usage:
      python analyze_ts.py <json_file> --type history --bucket day
      python analyze_ts.py <json_file> --type panel
      python analyze_ts.py <json_file> --type history --insights
      python analyze_ts.py <json_file> --type history --quality
    """
    import argparse
    parser = argparse.ArgumentParser(description="TDengine time-series analysis")
    parser.add_argument("file", help="Path to a JSON data file")
    parser.add_argument("--type", choices=["history", "panel"], default="history", help="Input data type")
    parser.add_argument("--bucket", choices=["day", "hour", "weekday"], default="day", help="Aggregation grain")
    parser.add_argument("--sigma", type=float, default=1.0, help="Anomaly threshold in standard deviations")
    parser.add_argument("--insights", action="store_true", help="Run automated insight rules")
    parser.add_argument("--quality", action="store_true", help="Run data-quality checks")
    args = parser.parse_args()

    with open(args.file) as f:
        raw = json.load(f)

    if args.type == "panel":
        result = analyze_panel_queries(load_panel_queries(raw))
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        items = load_attribute_history(raw)
        print(f"Loaded points: {len(items)}, total: {raw.get('total', '?')}")
        if raw.get("total", 0) > raw.get("count", 0):
            print(f"Data is truncated: received {raw['count']}/{raw['total']}; fetch additional pages")

        # Data-quality report
        if args.quality:
            quality = data_quality_check(items)
            print(f"\n{format_quality_report(quality)}")
            return

        # Automated insights
        if args.insights:
            ins = auto_insights(items, args.bucket)
            print(f"\n{format_insights(ins)}")
            return

        # Standard aggregate analysis
        buckets = bucket_by(items, args.bucket)
        agg = aggregate_buckets(buckets)

        print(f"\n===== Aggregated by {args.bucket} =====")
        print(format_agg_table(agg))

        # Trend
        if len(agg) >= 3:
            trend = detect_trend(agg)
            print("\n===== Trend =====")
            print(format_trend_summary(trend))

        changes = calc_changes(agg)
        if changes:
            print("\n===== Period-over-period Changes =====")
            print(format_changes_table(changes))

        anomalies = detect_anomalies(agg, sigma=args.sigma)
        print(f"\n===== Anomalous Periods (>{args.sigma} sigma) =====")
        print(format_anomalies_table(anomalies))


if __name__ == "__main__":
    main()

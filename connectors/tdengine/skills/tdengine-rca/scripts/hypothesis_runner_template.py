"""Template script for RCA hypothesis validation tasks.

Usage:
  python hypothesis_runner_template.py
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd

from analysis_methods import (
    compute_sigma_bounds,
    lagged_correlation,
    rolling_drift,
    simple_granger_like_score,
    zscore_anomaly_mask,
)
from common_io import dump_result_json
from data_prep import (
    coerce_numeric_columns,
    detect_time_column,
    load_timeseries_csv,
    normalize_time_index,
    normalize_timestamp,
    slice_time_window,
)
from plotting import save_window_vs_baseline_plot


def run_analysis() -> dict:
    # Replace these constants in generated subtask code.
    task_id = "HXXX"
    accident_time = normalize_timestamp("2026-01-15T10:00:00Z")
    target_col = "TARGET_METRIC"
    related_cols = ["TARGET_METRIC", "RELATED_X", "RELATED_Y"]

    data_path = "./data_selected_from_tsdb.csv"
    output_dir = Path("./output_images")

    try:
        raw_df = load_timeseries_csv(data_path)
        time_col = detect_time_column(raw_df)
        ts_df = normalize_time_index(raw_df, time_col)
        ts_df = coerce_numeric_columns(ts_df, related_cols)

        window_start = accident_time - timedelta(hours=2)
        window_end = accident_time + timedelta(hours=2)
        baseline_start = accident_time - timedelta(days=7)
        baseline_end = accident_time - timedelta(days=1)

        window_df = slice_time_window(ts_df, window_start, window_end)
        baseline_df = slice_time_window(ts_df, baseline_start, baseline_end)

        if window_df.empty or baseline_df.empty:
            raise ValueError("window or baseline data is empty")

        sigma = compute_sigma_bounds(baseline_df[target_col])
        current_mean = float(window_df[target_col].mean())
        anomaly = current_mean > sigma.upper or current_mean < sigma.lower

        z_anomaly_count = int(
            zscore_anomaly_mask(window_df[target_col], baseline=baseline_df[target_col]).sum()
        )
        drift_df = rolling_drift(
            window_df[target_col], window="30min", baseline=baseline_df[target_col]
        )

        corr_rows = lagged_correlation(window_df[related_cols[1]], window_df[target_col], max_lag=8)
        best_idx = corr_rows["corr"].abs().idxmax()
        best_lag = float(corr_rows.loc[best_idx, "lag"])
        best_lag_corr = float(corr_rows.loc[best_idx, "corr"])

        granger_score = simple_granger_like_score(window_df[related_cols[1]], window_df[target_col], lag=1)

        image_path = save_window_vs_baseline_plot(
            window_series=window_df[target_col],
            baseline_series=baseline_df[target_col],
            title=f"{task_id} {target_col}: incident window vs historical baseline",
            output_dir=output_dir,
            filename=f"{task_id}_{target_col}_window_vs_baseline.png",
        )

        result = {
            "task_id": task_id,
            "hypothesis_supported": bool(anomaly),
            "image_path": image_path,
            "evidence": {
                "target_col": target_col,
                "window_points": len(window_df),
                "baseline_points": len(baseline_df),
                "window_mean": current_mean,
                "baseline_mean": sigma.mean,
                "baseline_std": sigma.std,
                "sigma_upper": sigma.upper,
                "sigma_lower": sigma.lower,
                "zscore_anomaly_count": z_anomaly_count,
                "best_lag": best_lag,
                "best_lag_corr": best_lag_corr,
                "simple_granger_score": granger_score,
                "latest_drift_score": float(drift_df["drift_score"].dropna().iloc[-1]) if not drift_df["drift_score"].dropna().empty else 0.0,
            },
            "conclusion": (
                f"{task_id}: {target_col} incident mean is {current_mean:.4f}; "
                f"the historical three-sigma interval is "
                f"[{sigma.lower:.4f}, {sigma.upper:.4f}]. "
                f"The hypothesis is {'supported' if anomaly else 'not supported'}."
            ),
        }
    except Exception as exc:
        result = {
            "task_id": task_id,
            "hypothesis_supported": False,
            "image_path": None,
            "evidence": {"error": str(exc)},
            "conclusion": f"Analysis failed: {exc}",
        }

    return result


if __name__ == "__main__":
    final_result = run_analysis()
    dump_result_json(final_result, Path("./analysis_result.json"))
    print(final_result)

# RCA Script Templates

This guide describes the reusable Python modules under `../scripts`. The
scripts operate only on data already returned by public MCP tools; do not pass
credentials, tokens, or service URLs to them.

## Included Modules

- `common_io.py`: JSON-safe result serialization and output.
- `data_prep.py`: CSV loading, timestamp detection, time-index normalization,
  UTC normalization, and numeric cleaning.
- `analysis_methods.py`: three-sigma bounds, baseline-relative Z-scores and
  rolling drift, lagged correlation, and lightweight directional scoring.
- `plotting.py`: incident-versus-baseline plots.
- `hypothesis_runner_template.py`: reusable `run_analysis` task template.

The scripts require Python 3 plus `pandas` and `numpy`; charts also require
`matplotlib`.

## Recommended Workflow

1. Copy `hypothesis_runner_template.py` into an isolated working directory.
2. Replace only `task_id`, `accident_time`, `target_col`, `related_cols`, and
   `data_path`.
3. Preserve the cleaning order in `data_prep.py`:
   - load the CSV;
   - detect the timestamp column;
   - normalize, sort, and index by timestamp;
   - normalize the incident timestamp with `normalize_timestamp()` so all
     comparisons use timezone-aware UTC values;
   - convert metric columns with `pd.to_numeric(errors="coerce")`.
4. For peer-equipment comparisons, group by equipment first, then apply
   `compute_sigma_bounds` or `rolling_drift` within each group.
5. Write `analysis_result.json` with `task_id`, `hypothesis_supported`,
   `image_path`, `evidence`, and `conclusion`.

Use a new output directory per run so evidence from separate hypotheses cannot
overwrite each other.

## Example

```python
import pandas as pd

from analysis_methods import compute_sigma_bounds, rolling_drift, zscore_anomaly_mask
from data_prep import (
    coerce_numeric_columns,
    detect_time_column,
    load_timeseries_csv,
    normalize_time_index,
    normalize_timestamp,
    slice_time_window,
)

raw_df = load_timeseries_csv(data_path)
time_col = detect_time_column(raw_df)
ts_df = normalize_time_index(raw_df, time_col)
ts_df = coerce_numeric_columns(ts_df, ["WS", "POWER", "PREPOWER"])

incident_time = normalize_timestamp("2026-01-15T10:00:00Z")
baseline_df = slice_time_window(
    ts_df, incident_time - pd.Timedelta(days=7), incident_time - pd.Timedelta(days=1)
)
incident_df = slice_time_window(
    ts_df, incident_time - pd.Timedelta(hours=2), incident_time + pd.Timedelta(hours=2)
)
sigma = compute_sigma_bounds(baseline_df["POWER"])
anomalies = zscore_anomaly_mask(
    incident_df["POWER"], baseline=baseline_df["POWER"]
)
drift = rolling_drift(
    incident_df["POWER"], baseline=baseline_df["POWER"], window="30min"
)
```

## When to Extend a Template

- For a formal Granger causality test, add `statsmodels` in the task-specific
  script. Do not replace the lightweight default in `analysis_methods.py`.
- For a multi-chart report, add a focused function to `plotting.py`. Keep its
  interface consistent: accept a `Series` or `DataFrame` and return the absolute
  output image path.
- For a domain-specific metric, add a parameterized function to
  `analysis_methods.py`; do not hard-code asset-specific column names.

## Result Interpretation

- Check sample count, cadence, missing values, and units before using a result.
- Record the exact baseline and incident windows in `evidence`.
- A high correlation or lag score supports association only.
- Set `hypothesis_supported` only when the declared threshold is met; otherwise
  use a rejected or inconclusive conclusion supported by measured values.

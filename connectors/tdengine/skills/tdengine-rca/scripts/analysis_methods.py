"""Reusable RCA statistical and causality methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SigmaBounds:
    mean: float
    std: float
    lower: float
    upper: float


def compute_sigma_bounds(series: pd.Series, sigma: float = 3.0) -> SigmaBounds:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        raise ValueError("Series is empty after numeric cleaning")

    mean = float(clean.mean())
    std = float(clean.std(ddof=1))
    return SigmaBounds(mean=mean, std=std, lower=mean - sigma * std, upper=mean + sigma * std)


def zscore_anomaly_mask(
    series: pd.Series,
    threshold: float = 3.0,
    baseline: pd.Series | None = None,
) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce")
    reference = clean if baseline is None else pd.to_numeric(baseline, errors="coerce").dropna()
    std = reference.std(ddof=1)
    if pd.isna(std) or std == 0:
        if reference.empty:
            return pd.Series(False, index=series.index)
        return clean.ne(reference.mean()).fillna(False)
    z = (clean - reference.mean()) / std
    return z.abs() > threshold


def rolling_drift(
    series: pd.Series,
    window: str = "30min",
    baseline_periods: int = 48,
    baseline: pd.Series | None = None,
) -> pd.DataFrame:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        raise ValueError("Series is empty after numeric cleaning")

    rolling_mean = clean.rolling(window=window, min_periods=2).mean()
    rolling_std = clean.rolling(window=window, min_periods=2).std()

    if baseline is None:
        reference = rolling_mean.head(baseline_periods).dropna()
    else:
        reference = pd.to_numeric(baseline, errors="coerce").dropna()
    if reference.empty:
        raise ValueError("Baseline is empty after numeric cleaning")
    baseline_mean = reference.mean()
    baseline_std = reference.std(ddof=1)

    if pd.isna(baseline_std) or baseline_std == 0:
        scale = max(abs(float(baseline_mean)), 1.0)
        drift_score = rolling_mean.apply(
            lambda value: 0.0
            if pd.isna(value) or value == baseline_mean
            else (value - baseline_mean) / scale
        )
    else:
        drift_score = (rolling_mean - baseline_mean) / baseline_std

    return pd.DataFrame(
        {
            "rolling_mean": rolling_mean,
            "rolling_std": rolling_std,
            "drift_score": drift_score,
            "baseline_mean": baseline_mean,
            "baseline_std": baseline_std,
        }
    )


def correlation_matrix(df: pd.DataFrame, columns: Iterable[str], method: str = "pearson") -> pd.DataFrame:
    valid_columns = [c for c in columns if c in df.columns]
    if len(valid_columns) < 2:
        raise ValueError("At least two columns are required for correlation analysis")
    num_df = df[valid_columns].apply(pd.to_numeric, errors="coerce")
    return num_df.corr(method=method)


def lagged_correlation(
    x: pd.Series,
    y: pd.Series,
    max_lag: int = 12,
) -> pd.DataFrame:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    joined = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if joined.empty:
        raise ValueError("No overlapping numeric data for lagged correlation")

    rows: list[dict[str, float]] = []
    for lag in range(-max_lag, max_lag + 1):
        corr = joined["x"].corr(joined["y"].shift(lag))
        rows.append({"lag": float(lag), "corr": float(corr) if pd.notna(corr) else np.nan})
    return pd.DataFrame(rows)


def simple_granger_like_score(cause: pd.Series, effect: pd.Series, lag: int = 1) -> float:
    # Lightweight alternative when statsmodels is unavailable.
    cause = pd.to_numeric(cause, errors="coerce")
    effect = pd.to_numeric(effect, errors="coerce")
    data = pd.concat([cause.rename("cause"), effect.rename("effect")], axis=1).dropna()
    if len(data) < lag + 5:
        return 0.0

    effect_lag = data["effect"].shift(lag)
    cause_lag = data["cause"].shift(lag)
    base = pd.concat([data["effect"], effect_lag], axis=1).dropna()
    aug = pd.concat([data["effect"], effect_lag, cause_lag], axis=1).dropna()
    if len(base) < 5 or len(aug) < 5:
        return 0.0

    base_corr = abs(base.iloc[:, 0].corr(base.iloc[:, 1]))
    aug_corr = abs(aug.iloc[:, 0].corr((aug.iloc[:, 1] + aug.iloc[:, 2]) / 2))
    base_corr = 0.0 if pd.isna(base_corr) else float(base_corr)
    aug_corr = 0.0 if pd.isna(aug_corr) else float(aug_corr)
    return max(0.0, aug_corr - base_corr)

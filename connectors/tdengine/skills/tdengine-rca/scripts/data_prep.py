"""Data preparation helpers for RCA hypothesis scripts."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


def load_timeseries_csv(data_path: str) -> pd.DataFrame:
    # utf-8-sig handles BOM safely in industrial CSV exports.
    return pd.read_csv(data_path, encoding="utf-8-sig", low_memory=False)


def detect_time_column(df: pd.DataFrame) -> str:
    for candidate in ("timestamp", "ts", "time", "datetime"):
        if candidate in df.columns:
            return candidate
    raise ValueError("No supported time column found in dataframe")


def normalize_time_index(df: pd.DataFrame, time_col: str) -> pd.DataFrame:
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)
    df = df.dropna(subset=[time_col])
    df = df.set_index(time_col).sort_index()
    return df


def normalize_timestamp(value: str | pd.Timestamp) -> pd.Timestamp:
    """Return one timezone-aware UTC timestamp for window comparisons."""
    return pd.to_datetime(value, errors="raise", utc=True)


def coerce_numeric_columns(df: pd.DataFrame, required_columns: Iterable[str]) -> pd.DataFrame:
    df = df.copy()
    present = [col for col in required_columns if col in df.columns]
    if not present:
        raise ValueError("None of required columns exists in dataframe")

    for col in present:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=present)
    if df.empty:
        raise ValueError("No valid rows after numeric coercion")
    return df


def slice_time_window(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df.index >= start) & (df.index <= end)].copy()

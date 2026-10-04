"""Reusable plotting helpers for RCA reports."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def configure_matplotlib() -> None:
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def save_window_vs_baseline_plot(
    window_series: pd.Series,
    baseline_series: pd.Series,
    title: str,
    output_dir: str | Path,
    filename: str,
) -> str:
    configure_matplotlib()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    image_path = out_dir / filename

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(window_series.index, window_series.values, label="Incident window", linewidth=2)
    ax.plot(baseline_series.index, baseline_series.values, label="Historical baseline", alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(image_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return str(image_path.resolve())

"""RCA common IO helpers for reusable analysis scripts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AnalysisContext:
    task_id: str
    accident_time: pd.Timestamp
    output_dir: Path


def ensure_output_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def to_serializable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, np.datetime64):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, dict):
        return {k: to_serializable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_serializable(v) for v in value]
    return value


def dump_result_json(result: dict[str, Any], output_file: str | Path) -> None:
    Path(output_file).write_text(
        json.dumps(to_serializable(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

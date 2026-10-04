"""Stable error types and codes used by the MIBAO bootstrap."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MibaoError(Exception):
    """Base exception with a stable machine-readable code."""

    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

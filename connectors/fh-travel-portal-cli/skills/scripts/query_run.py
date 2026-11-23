# -*- coding: utf-8 -*-
"""两条龙共用的发号、跑一步、写 summary、日期归一。不要放业务口径。"""

from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import portal_config

SCRIPTS = Path(__file__).resolve().parent


def configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")


def normalize_date(raw: str) -> str:
    """兼容 2026-09-15 / 2026.9.15 / 9-15 / 9.15（缺省当年）。"""
    raw = raw.strip()
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", raw)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})$", raw)
    if m:
        y = _dt.date.today().year
        mo, d = int(m.group(1)), int(m.group(2))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    raise ValueError(f"日期无法解析: {raw!r}（期望 YYYY-MM-DD 或 M.D）")


class QueryRun:
    def __init__(self, run_id: str = "") -> None:
        self.run_id = portal_config.adopt_run_id(run_id)

    def dir(self) -> Path:
        return portal_config.task_dir(self.run_id)

    def log(self, msg: str) -> None:
        portal_config.task_log(self.run_id, msg)

    def err(self, msg: str) -> None:
        portal_config.task_log(self.run_id, msg, to_stderr=True)

    def run_step(self, title: str, cmd: list[str]) -> tuple[int, str, str]:
        t0 = time.time()
        self.log(f"\n──── [{title}] {' '.join(str(x) for x in cmd[:6])}…")
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=str(SCRIPTS),
            )
        except OSError as exc:
            proc = subprocess.CompletedProcess(cmd, 1, "", str(exc))
        dt = time.time() - t0
        if proc.returncode != 0:
            self.err(f"[失败] {title}（{dt:.1f}s）exit={proc.returncode}")
            if proc.stderr.strip():
                self.err("stderr 尾部: " + proc.stderr.strip()[-600:])
            self.err("不要单独跑城市或拆步脚本；把同一条一条龙原命令再执行一次。")
            raise SystemExit(f"[失败] {title} exit={proc.returncode}")
        self.log(f"[OK] {title}（{dt:.1f}s）")
        return proc.returncode, proc.stdout or "", proc.stderr or ""

    def write_ok(self, shopping: Path, html: Path | None = None, present_dir: str = "", **extra: Any) -> None:
        if html is not None and present_dir:
            dest = Path(present_dir)
            if not dest.is_absolute():
                dest = Path.cwd() / dest
            dest.mkdir(parents=True, exist_ok=True)
            copied = dest / html.name
            shutil.copy2(html, copied)
            html = copied
        payload: dict[str, Any] = {
            "ok": True,
            "shopping": str(shopping.resolve()),
            "runDir": str(self.dir().resolve()),
        }
        if html is not None:
            payload["html"] = str(html.resolve())
        payload.update(extra)
        portal_config.task_summary_path(self.run_id).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def write_fail(self, error: str) -> None:
        if not self.run_id:
            return
        portal_config.task_summary_path(self.run_id).write_text(
            json.dumps(
                {
                    "ok": False,
                    "runDir": str(self.dir().resolve()),
                    "error": (error or "").strip()[:800],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

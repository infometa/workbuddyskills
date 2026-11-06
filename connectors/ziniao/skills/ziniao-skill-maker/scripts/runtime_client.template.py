#!/usr/bin/env python3
"""ZiniaoClient — copy into runtime/ziniao_client.py by scaffold."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def locate_ziniao_cli_argv() -> list[str]:
    """Resolve CLI argv; on Windows bypass .cmd so '&' in URLs is not split."""
    env = (os.environ.get("ZINIAO_CLI_BINARY") or "").strip()
    if env and Path(env).is_file():
        return [env]

    found = shutil.which("ziniao-cli")
    if not found:
        raise RuntimeError("ziniao-cli not found in PATH")
    path = Path(found)
    if path.suffix.lower() in {".cmd", ".bat"}:
        pkg = path.parent / "node_modules" / "@ziniao-open" / "cli"
        exe = pkg / "bin" / "ziniao-cli.exe"
        if exe.is_file():
            return [str(exe)]
        run_js = pkg / "scripts" / "run.js"
        bundled_node = path.parent / "node.exe"
        node_bin = str(bundled_node) if bundled_node.is_file() else shutil.which("node")
        if node_bin and run_js.is_file():
            return [node_bin, str(run_js)]
    return [found]


def poll_until(
    read: Callable[[], T],
    ready: Callable[[T], bool],
    *,
    timeout_ms: int = 6000,
    interval_ms: int = 500,
    raise_on_timeout: bool = False,
) -> T:
    """Poll read() until ready(data) or timeout. Returns the last sample.

    Timeout does not mean success unless raise_on_timeout=True. Callers must
    re-check ready() or let final_gate reject a stale sample.
    """
    deadline = time.perf_counter() + timeout_ms / 1000
    last = read()
    if ready(last):
        return last
    while time.perf_counter() < deadline:
        time.sleep(interval_ms / 1000)
        last = read()
        if ready(last):
            return last
    if raise_on_timeout:
        raise TimeoutError(f"poll_until timed out after {timeout_ms}ms")
    return last


def _cli_payload(resp: Any) -> Any:
    """Unwrap one CLI {ok, data} envelope. jq/raw payloads pass through."""
    if not isinstance(resp, dict):
        return resp
    if resp.get("ok") is False:
        return resp
    inner = resp.get("data", resp)
    if isinstance(inner, dict) and inner.get("ok") is True and "data" in inner:
        return inner.get("data")
    return inner


class ZiniaoClient:
    def __init__(
        self,
        store_id: str,
        cli_argv: list[str] | None = None,
        timeout: int = 120,
        retries: int = 1,
    ) -> None:
        self.store_id = store_id
        self.cli_argv = cli_argv or locate_ziniao_cli_argv()
        self.timeout = timeout
        self.retries = retries
        self.stats: dict[str, Any] = {"calls": 0, "retries": 0, "byCommand": {}}

    def run(self, args: list[str], *, readonly: bool = False) -> dict[str, Any]:
        command = [str(x) for x in args]
        key = " ".join(command[:2]) if len(command) >= 2 else (command[0] if command else "")
        attempts = (self.retries + 1) if readonly else 1
        last = ""
        for attempt in range(attempts):
            proc = subprocess.run(
                [*self.cli_argv, *command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                shell=False,
            )
            self.stats["calls"] += 1
            self.stats["byCommand"][key] = self.stats["byCommand"].get(key, 0) + 1
            if attempt:
                self.stats["retries"] += 1
            raw = (proc.stdout or "").strip()
            err = (proc.stderr or "").strip()
            combined = raw or err
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {}
            if proc.returncode == 0:
                if isinstance(data, dict) and data.get("ok") is False:
                    last = raw or err
                else:
                    if not (isinstance(data, dict) and data.get("ok")):
                        data = {"ok": True, "data": data if data else {"text": combined}, "stdout": combined}
                    return data
            last = combined or proc.stderr
            if attempt + 1 < attempts:
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(last)

    def page_exec(self, script: str) -> Any:
        return self._parse_result(
            self.run(["page", "exec", "--store-id", self.store_id, "--script", script], readonly=True)
        )

    def page_visit(self, url: str, wait_until: str = "load") -> dict[str, Any]:
        return self.run([
            "page", "visit", "--store-id", self.store_id,
            "--url", url, "--wait-until", wait_until,
        ])

    def page_content_jq(self, jq_expr: str) -> Any:
        """--jq filters the ZClaw payload, not the CLI {ok,data} envelope."""
        proc = subprocess.run(
            [*self.cli_argv, "page", "content", "--store-id", self.store_id,
             "--content-format", "structured", "--jq", jq_expr],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=self.timeout, shell=False,
        )
        self.stats["calls"] += 1
        key = "page content"
        self.stats["byCommand"][key] = self.stats["byCommand"].get(key, 0) + 1
        raw = (proc.stdout or "").strip()
        if proc.returncode != 0:
            raise RuntimeError(raw or proc.stderr)
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        if isinstance(parsed, dict) and parsed.get("ok") is False:
            raise RuntimeError(raw)
        return parsed

    def page_screenshot(self, dest: Path, timeout_ms: int = 15000) -> Path:
        resp = self.run([
            "page", "screenshot", "--store-id", self.store_id,
            "--path", str(dest), "--timeout", str(timeout_ms),
        ])
        payload = _cli_payload(resp)
        src = str(dest)
        if isinstance(payload, dict):
            nested = payload.get("data") if isinstance(payload.get("data"), dict) else payload
            src = nested.get("filePath") or nested.get("path") or str(dest)
        src_path = Path(src)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src_path.is_file() and src_path.resolve() != dest.resolve():
            shutil.copy2(src_path, dest)
        if not dest.is_file() or dest.stat().st_size == 0:
            raise RuntimeError(f"screenshot missing or empty: {dest}")
        return dest

    def api(self, method: str, path: str, data: dict | None = None) -> dict[str, Any]:
        args = ["api", method.upper(), path]
        if data is not None:
            args.extend(["--data", json.dumps(data, ensure_ascii=False)])
        return self.run(args)

    @staticmethod
    def _parse_result(resp: dict) -> Any:
        payload = _cli_payload(resp)
        if isinstance(payload, dict) and "result" in payload:
            result = payload["result"]
        elif isinstance(payload, dict) and isinstance(payload.get("data"), dict) and "result" in payload["data"]:
            result = payload["data"]["result"]
        else:
            return payload
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return result
        return result

#!/usr/bin/env python3
"""
WorkBuddy helper for DingTalk Workspace CLI setup diagnostics.

This script does not store credentials and does not complete OAuth by itself.
It checks whether dws is installed, reports version/status, and can start the
standard device flow so WorkBuddy Runtime can render an in-app authorization card.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


DEVICE_URL_RE = re.compile(r"https://login\.dingtalk\.com/oauth2/device/verify\.htm(?:\?user_code=([A-Z0-9-]+))?")
CODE_RE = re.compile(r"authorization code:\s*([A-Z0-9-]+)", re.IGNORECASE)


@dataclass
class CommandResult:
    code: int
    stdout: str
    stderr: str


def run(args: list[str], timeout: Optional[int] = None) -> CommandResult:
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def emit(payload: dict, code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(code)


def find_dws() -> str:
    found = shutil.which("dws")
    return found or ""


def parse_device_output(text: str) -> dict:
    urls = DEVICE_URL_RE.findall(text)
    all_urls = re.findall(r"https://login\.dingtalk\.com/oauth2/device/verify\.htm(?:\?user_code=[A-Z0-9-]+)?", text)
    code_match = CODE_RE.search(text)
    user_code = code_match.group(1) if code_match else ""
    complete_url = ""
    verify_url = "https://login.dingtalk.com/oauth2/device/verify.htm"

    for url in all_urls:
        if "user_code=" in url:
            complete_url = url
        else:
            verify_url = url
    if not user_code:
        for maybe_code in urls:
            if maybe_code:
                user_code = maybe_code
                break
    if not complete_url and user_code:
        complete_url = f"{verify_url}?user_code={user_code}"

    return {
        "verify_url": verify_url,
        "complete_url": complete_url,
        "user_code": user_code,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose dws setup for WorkBuddy")
    parser.add_argument("--start-device-flow", action="store_true", help="Start dws auth login --device and parse initial auth card data")
    parser.add_argument("--timeout", type=int, default=8, help="Timeout seconds for short diagnostic commands")
    args = parser.parse_args()

    dws = find_dws()
    if not dws:
        emit({
            "ok": False,
            "stage": "install_check",
            "reason": "dws_not_found",
            "suggested_command": "npm install -g dingtalk-workspace-cli",
        }, 2)

    version = run([dws, "version", "--format", "json"], timeout=args.timeout)
    status = run([dws, "auth", "status", "--format", "json"], timeout=args.timeout)

    payload = {
        "ok": version.code == 0,
        "dws_path": dws,
        "version_exit_code": version.code,
        "version_stdout": version.stdout.strip(),
        "version_stderr": version.stderr.strip(),
        "auth_status_exit_code": status.code,
        "auth_status_stdout": status.stdout.strip(),
        "auth_status_stderr": status.stderr.strip(),
        "workbuddy_env_recommendation": {
            "DINGTALK_DWS_AGENTCODE": os.environ.get("DINGTALK_DWS_AGENTCODE", "workbuddy"),
            "DWS_CHANNEL": os.environ.get("DWS_CHANNEL", "workbuddy"),
        },
    }

    if args.start_device_flow:
        try:
            login = run([dws, "auth", "login", "--device", "--format", "json"], timeout=args.timeout)
        except subprocess.TimeoutExpired as exc:
            text = ""
            if exc.stdout:
                text += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode(errors="replace")
            if exc.stderr:
                text += "\n" + (exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode(errors="replace"))
            payload["device_flow"] = {
                "status": "polling_timeout_expected",
                "card": parse_device_output(text),
                "raw_excerpt": text[-2000:],
            }
        else:
            text = f"{login.stdout}\n{login.stderr}"
            payload["device_flow"] = {
                "status": "completed_or_failed_quickly",
                "exit_code": login.code,
                "card": parse_device_output(text),
                "raw_excerpt": text[-2000:],
            }

    emit(payload, 0 if payload["ok"] else 1)


if __name__ == "__main__":
    main()

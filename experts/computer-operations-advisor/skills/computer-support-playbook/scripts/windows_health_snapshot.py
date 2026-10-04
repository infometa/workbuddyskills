#!/usr/bin/env python3
"""Read-only Windows health snapshot using Python and built-in PowerShell cmdlets."""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_VERSION = "1.1.0"


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def bytes_to_gib(value: int) -> float:
    return round(value / (1024 ** 3), 2)


def powershell_path() -> str | None:
    return shutil.which("powershell.exe") or shutil.which("powershell")


def run_powershell(command: str, timeout: int = 20) -> tuple[Any | None, str | None]:
    executable = powershell_path()
    if not executable:
        return None, "PowerShell was not found"
    wrapped = (
        "$utf8 = New-Object System.Text.UTF8Encoding($false); "
        "[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8; "
        "$ErrorActionPreference = 'Stop'; "
        "$ProgressPreference = 'SilentlyContinue'; "
        f"$result = & {{ {command} }}; "
        "$result | ConvertTo-Json -Depth 5 -Compress"
    )
    try:
        completed = subprocess.run(
            [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", wrapped],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, f"PowerShell query timed out after {timeout} seconds"
    if completed.returncode != 0:
        error = completed.stderr.strip() or f"PowerShell exited with code {completed.returncode}"
        return None, error
    output = completed.stdout.strip()
    if not output:
        return [], None
    try:
        return json.loads(output), None
    except json.JSONDecodeError as exc:
        return None, f"PowerShell returned invalid JSON: {exc}"


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def memory_snapshot() -> dict[str, Any]:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError()
    used = status.ullTotalPhys - status.ullAvailPhys
    return {
        "total_gib": bytes_to_gib(status.ullTotalPhys),
        "available_gib": bytes_to_gib(status.ullAvailPhys),
        "used_gib": bytes_to_gib(used),
        "used_percent": int(status.dwMemoryLoad),
    }


def disk_snapshot() -> list[dict[str, Any]]:
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    disks: list[dict[str, Any]] = []
    for index in range(26):
        if not mask & (1 << index):
            continue
        drive = f"{chr(65 + index)}:\\"
        try:
            usage = shutil.disk_usage(drive)
        except OSError:
            continue
        used = usage.total - usage.free
        percent = round((used / usage.total) * 100, 1) if usage.total else 0.0
        disks.append(
            {
                "drive": drive,
                "total_gib": bytes_to_gib(usage.total),
                "free_gib": bytes_to_gib(usage.free),
                "used_percent": percent,
            }
        )
    return disks


def uptime_seconds() -> int:
    return int(ctypes.windll.kernel32.GetTickCount64() / 1000)


def add_query(
    report: dict[str, Any],
    key: str,
    command: str,
    timeout: int = 20,
    list_result: bool = False,
    optional: bool = False,
) -> None:
    value, error = run_powershell(command, timeout=timeout)
    if error:
        bucket = "collection_warnings" if optional else "collection_failures"
        report[bucket].append({"section": key, "error": error})
        report["snapshot"][key] = None
    else:
        report["snapshot"][key] = as_list(value) if list_result else value


def build_report(mode: str, include_events: bool, include_software: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "script_version": SCRIPT_VERSION,
        "generated_at": iso_now(),
        "mode": mode,
        "read_only": True,
        "privacy": {
            "collects_file_contents": False,
            "collects_browser_data": False,
            "collects_credentials": False,
            "collects_ip_addresses": False,
            "event_message_text_included": False,
            "events_included": include_events,
            "software_inventory_included": include_software,
            "startup_commands_included": False,
        },
        "snapshot": {},
        "collection_failures": [],
        "collection_warnings": [],
        "interpretation_notes": [
            "This is a point-in-time snapshot, not a diagnosis.",
            "Percentages and device or event counts must be interpreted with symptoms and history.",
            "Empty or failed sections must not be inferred or filled by the assistant.",
        ],
    }

    report["snapshot"]["python_platform"] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "uptime_seconds": uptime_seconds(),
    }
    try:
        report["snapshot"]["memory"] = memory_snapshot()
    except OSError as exc:
        report["collection_failures"].append({"section": "memory", "error": str(exc)})
        report["snapshot"]["memory"] = None
    report["snapshot"]["disks"] = disk_snapshot()

    add_query(
        report,
        "system",
        "Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, SystemType, NumberOfLogicalProcessors",
    )
    add_query(
        report,
        "operating_system",
        "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, LastBootUpTime",
    )
    add_query(
        report,
        "cpu",
        "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, LoadPercentage",
        list_result=True,
    )

    if mode == "full":
        add_query(
            report,
            "network_adapters",
            "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, LinkSpeed | Sort-Object Name",
            list_result=True,
        )
        add_query(
            report,
            "device_errors",
            "Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 } | Select-Object -First 20 Name, Status, ConfigManagerErrorCode",
            list_result=True,
        )
        add_query(
            report,
            "top_processes_by_memory",
            "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name, Id, @{Name='WorkingSetMiB';Expression={[math]::Round($_.WorkingSet64 / 1MB, 1)}}",
            list_result=True,
        )

    if include_software:
        add_query(
            report,
            "startup_apps",
            "Get-CimInstance Win32_StartupCommand | Select-Object Name, Location | Sort-Object Name",
            list_result=True,
        )
        installed_apps_command = (
            "$paths = @('HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
            "'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
            "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'); "
            "Get-ItemProperty $paths -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName } "
            "| Select-Object DisplayName, DisplayVersion, Publisher, InstallDate "
            "| Sort-Object InstallDate -Descending | Select-Object -First 40"
        )
        add_query(
            report,
            "installed_apps",
            installed_apps_command,
            list_result=True,
        )
        add_query(
            report,
            "windows_pua_protection",
            "Get-MpPreference | Select-Object PUAProtection",
            optional=True,
        )

    if include_events:
        event_command = (
            "$start = (Get-Date).AddHours(-24); "
            "Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=$start} -MaxEvents 20 "
            "| Select-Object TimeCreated, Id, LevelDisplayName, ProviderName"
        )
        add_query(
            report,
            "recent_system_errors",
            event_command,
            timeout=30,
            list_result=True,
            optional=True,
        )

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a read-only Windows health snapshot as JSON."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quick", action="store_true", help="Collect core system, memory and disk data.")
    group.add_argument("--full", action="store_true", help="Also collect adapters, device errors and process names.")
    parser.add_argument(
        "--include-events",
        action="store_true",
        help="Include up to 20 System error event headers from the last 24 hours; no message text.",
    )
    parser.add_argument(
        "--include-software",
        action="store_true",
        help="Include startup names, installed app metadata and Windows PUA protection status; no startup commands.",
    )
    parser.add_argument("--save", type=Path, help="Save JSON to this path instead of stdout.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting an existing --save file.")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--version", action="version", version=SCRIPT_VERSION)
    args = parser.parse_args()
    if args.include_events and not args.full:
        parser.error("--include-events requires --full")
    if args.include_software and not args.full:
        parser.error("--include-software requires --full")
    return args


def save_report(destination: Path, text: str, force: bool) -> tuple[bool, str | None]:
    if not destination.parent.exists():
        return False, f"Parent directory does not exist: {destination.parent}"

    payload = text + os.linesep
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            temporary_path = Path(handle.name)
        if force:
            os.replace(temporary_path, destination)
        else:
            os.rename(temporary_path, destination)
        temporary_path = None
    except FileExistsError:
        return False, f"Output file already exists: {destination}. Use --force to overwrite."
    except OSError as exc:
        return False, f"Could not save report to {destination}: {exc}"
    finally:
        if temporary_path and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass
    return True, None


def main() -> int:
    args = parse_args()
    if platform.system() != "Windows":
        error = {"error": "unsupported_platform", "message": "This script supports Windows only."}
        print(json.dumps(error, ensure_ascii=False))
        return 2

    mode = "full" if args.full else "quick"
    report = build_report(
        mode=mode,
        include_events=args.include_events,
        include_software=args.include_software,
    )
    indent = None if args.compact else 2
    text = json.dumps(report, ensure_ascii=False, indent=indent, default=str)

    if args.save:
        destination = args.save.expanduser().resolve()
        saved, error = save_report(destination, text, force=args.force)
        if not saved:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        print(json.dumps({"saved": str(destination), "bytes": destination.stat().st_size}, ensure_ascii=False))
    else:
        print(text)

    return 0 if not report["collection_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

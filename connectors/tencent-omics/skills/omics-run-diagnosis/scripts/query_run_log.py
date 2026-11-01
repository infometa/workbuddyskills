#!/usr/bin/env python3
"""Read-only diagnosis via the installed omics CLI; no private API/auth handling."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit


# Best-effort redaction, not a guarantee arbitrary logs are safe to share.
SECRET_KEYS = {
    "authorization", "cookie", "setcookie", "sessionid", "xsessionid",
    "secretid", "secretkey", "accesstoken", "refreshtoken", "securitytoken",
    "password", "token", "apikey",
}
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
HEADER_RE = re.compile(r"(?im)\b(authorization|cookie|set-cookie)\s*[:=]\s*[^\r\n]+")
ASSIGNMENT_RE = re.compile(
    r"(?i)\b(x[-_]?session[-_]?id|session[-_]?id|secret[-_]?id|secret[-_]?key|"
    r"access[-_]?token|refresh[-_]?token|security[-_]?token|password|api[-_]?key|token)"
    r"\b([\"']?\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;}]+)"
)
COLLECTION_ERROR_KEYS = {
    "StderrError", "StdoutError", "PodEventsError", "NextflowLogError",
    "ExecutionTraceError", "StdoutLogError", "ReportUrlsError",
}


def redact_text(value: str) -> str:
    """Keep diagnostic paths/statuses, removing URL queries and known secrets."""
    # Metadata/Runtime can themselves be JSON-encoded strings.
    if value.lstrip().startswith(("{", "[")):
        try:
            nested = json.loads(value)
        except (ValueError, RecursionError):
            pass
        else:
            return json.dumps(redact(nested), ensure_ascii=False)

    def strip_url(match: re.Match) -> str:
        try:
            parts = urlsplit(match.group(0))
            host = parts.netloc.rsplit("@", 1)[-1]
            return urlunsplit((parts.scheme, host, parts.path,
                               "REDACTED" if parts.query else "", ""))
        except ValueError:
            return "[REDACTED_URL]"

    value = URL_RE.sub(strip_url, value)
    value = HEADER_RE.sub(lambda m: m.group(1) + ": [REDACTED]", value)
    return ASSIGNMENT_RE.sub(lambda m: m.group(1) + m.group(2) + "[REDACTED]", value)


def redact(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if re.sub(r"[^a-z0-9]", "", key.lower()) in SECRET_KEYS
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return redact_text(value) if isinstance(value, str) else value


def evidence_flags(value, path="response"):
    """Collect retrieval errors, separately from the scientific task's errors."""
    errors, truncated = [], []
    if isinstance(value, dict):
        for key, item in value.items():
            child = path + "." + key
            if key in COLLECTION_ERROR_KEYS and item:
                errors.append(child)
            if key.endswith("Truncated") and item is True:
                truncated.append(child)
            child_errors, child_truncated = evidence_flags(item, child)
            errors.extend(child_errors)
            truncated.extend(child_truncated)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child_errors, child_truncated = evidence_flags(item, f"{path}[{index}]")
            errors.extend(child_errors)
            truncated.extend(child_truncated)
    return errors, truncated


def identifier(value: str) -> str:
    value = value.strip()
    if (not value or value.startswith("-")
            or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in value)):
        raise argparse.ArgumentTypeError("标识不能为空、包含空白/控制字符或以 '-' 开头")
    return value


def positive_seconds(value: str) -> float:
    try:
        result = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("超时须为正数") from None
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("超时须为有限正数")
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--run-uuid", type=identifier, help="单任务 RunUuid（omics debug --run）")
    target.add_argument("--run-group-id", type=identifier, help="批次 RunGroupId")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--project", "-p", type=identifier, help="本次查询项目")
    scope.add_argument("--agent-project", action="store_true", help="强制团队项目，忽略 config 项目")
    parser.add_argument("--status", action="store_true", help="查询批次/子任务状态列表，不采集日志")
    parser.add_argument("--job", type=identifier, help="单任务内精确钻取 JobId")
    parser.add_argument("--type", choices=["WDL", "WDL_GRAPH", "NEXTFLOW", "LAMBDA"],
                        help="仅在 CLI 无法识别真实引擎时作为回退")
    parser.add_argument("--with-stdout", action="store_true", help="同时读取 stdout；Lambda 会钻取所有有 JobId 的 calls")
    parser.add_argument("--with-trace", action="store_true", help="读取 Nextflow execution trace")
    parser.add_argument("--omics-cli", help="CLI 可执行文件；优先于 OMICS_CLI_PATH，均未设置时按 PATH 查找 omics")
    parser.add_argument("--timeout", type=positive_seconds, default=120, help="单次 CLI 查询超时秒数（默认 120）")
    parser.add_argument("--print-command", action="store_true", help="仅输出 argv，不启动 CLI 或访问网络")
    args = parser.parse_args(argv)
    if args.omics_cli is None:
        args.omics_cli = os.environ.get("OMICS_CLI_PATH", "omics")
    if args.status:
        if args.run_uuid or args.job or args.type or args.with_stdout or args.with_trace:
            parser.error("--status 仅支持可选 --run-group-id 和项目参数；RunUuid 应使用 debug")
    elif not (args.run_uuid or args.run_group_id):
        parser.error("诊断需要 --run-uuid 或 --run-group-id")
    elif not args.run_uuid and (args.job or args.type or args.with_stdout or args.with_trace):
        parser.error("--job/--type/--with-stdout/--with-trace 仅用于 --run-uuid")
    if not args.omics_cli.strip() or "\x00" in args.omics_cli:
        parser.error("--omics-cli / OMICS_CLI_PATH 不能为空或包含 NUL 字符")
    return args


def build_command(args):
    command = [args.omics_cli, "status" if args.status else "debug"]
    if args.run_group_id:
        command.append(args.run_group_id)
    if args.run_uuid:
        command.extend(["--run", args.run_uuid])
    if args.project:
        command.extend(["--project", args.project])
    elif args.agent_project:
        command.append("--agent-project")
    for flag, value in [("--job", args.job), ("--type", args.type)]:
        if value:
            command.extend([flag, value])
    if args.with_stdout:
        command.append("--with-stdout")
    if args.with_trace:
        command.append("--with-trace")
    return command + ["-o", "json"]


def as_text(value):
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def collect(args):
    command = build_command(args)
    error = None
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=args.timeout, check=False)
        exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code, stdout, stderr = 124, as_text(exc.stdout), as_text(exc.stderr)
        error = "CLI 查询超时；仅保留已经返回的证据"
    except OSError as exc:
        exit_code, stdout, stderr = 127, "", str(exc)
        error = "无法启动 CLI；检查安装与 --omics-cli 路径"

    response = None
    json_received = False
    try:
        response = json.loads(stdout)
        json_received = True
        expected = list if args.status else dict
        # status can serialize a nil Go slice as null for an empty result.
        empty_status = args.status and exit_code == 0 and response is None
        if not isinstance(response, expected) and not empty_status:
            error = error or f"CLI JSON 形态不符：预期 {expected.__name__}"
    except (ValueError, RecursionError):
        error = error or "CLI 未返回有效 JSON；检查 cli_stderr/cli_stdout 和 CLI 版本"

    retrieval_errors, truncated = evidence_flags(response)
    payload = {
        "schema_version": 2,
        "command": command,
        "cli_exit_code": exit_code,
        "response": response,
        "collection": {
            "incomplete": bool(error or exit_code or retrieval_errors or truncated),
            "retrieval_error_fields": retrieval_errors,
            "truncated_fields": truncated,
        },
    }
    if error:
        payload["wrapper_error"] = error
    if stderr.strip():
        payload["cli_stderr"] = stderr.strip()
    if not json_received and stdout.strip():
        payload["cli_stdout"] = stdout.strip()
    # Zero means the query ran, not that the task succeeded or all logs arrived.
    # Preserve CLI failure even when partial JSON contains useful evidence.
    return redact(payload), (exit_code if 0 < exit_code < 256 else 1) if exit_code else int(bool(error))


def main(argv=None):
    args = parse_args(argv)
    if args.print_command:
        payload, exit_code = {"mode": "command_plan", "argv": build_command(args)}, 0
    else:
        payload, exit_code = collect(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

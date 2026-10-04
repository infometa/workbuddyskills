#!/usr/bin/env python3
"""One-shot command entry for the WorkBuddy expert package."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PLUGIN_ROOT / "src"
sys.dont_write_bytecode = True
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mibao_core.expert_runtime import (  # noqa: E402
    execute_expert_request_file,
    safe_error_payload,
)
from mibao_core.runtime_probe import one_shot_runtime_probe  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mibao-expert",
        description="Run a bounded MIBAO expert command without starting a local service.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("probe", help="run the non-product integrity diagnostic")
    execute = subparsers.add_parser(
        "execute",
        help="execute one bounded inventory build or SQLite FTS search request and exit",
    )
    execute.add_argument("--request", type=Path, required=True)
    execute.add_argument("--request-root", type=Path, required=True)
    execute.add_argument(
        "--request-scope",
        choices=("plugin-data", "session-workspace"),
        required=True,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict", newline="\n")
    args = _parser().parse_args(argv)
    if args.command == "probe":
        print(json.dumps(one_shot_runtime_probe(), ensure_ascii=False, sort_keys=True))
        return 0
    try:
        result = execute_expert_request_file(
            args.request,
            request_root=args.request_root,
            request_scope=args.request_scope,
        )
    except Exception as exc:
        print(json.dumps(safe_error_payload(exc), ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deprecated alias for an explicitly reviewed COMMIT; never scans or diffs."""
import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Deprecated: use commit_sources.py directly")
    parser.add_argument("project_dir")
    parser.add_argument("--scan-id", required=True)
    parser.add_argument("--approve-diff-sha256", required=True)
    parser.add_argument("--accept-migrations", action="store_true")
    parser.add_argument("--confirm-empty", action="store_true")
    parser.add_argument("--confirm-missing", action="store_true")
    args = parser.parse_args()
    from commit_sources import main as commit_main

    sys.argv = [
        "commit_sources.py",
        args.project_dir,
        args.scan_id,
        "--approve-diff-sha256",
        args.approve_diff_sha256,
    ]
    if args.accept_migrations:
        sys.argv.append("--accept-migrations")
    if args.confirm_empty:
        sys.argv.append("--confirm-empty")
    if args.confirm_missing:
        sys.argv.append("--confirm-missing")
    commit_main()


if __name__ == "__main__":
    main()

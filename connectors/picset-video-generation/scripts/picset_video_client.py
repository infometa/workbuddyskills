#!/usr/bin/env python3
"""Public WorkBuddy helper commands for Picset AI video creation."""

from __future__ import annotations

import argparse
import json
import sys

from oss_upload import OssUploadError, load_token_from_stdin, upload_file_to_oss


def _upload(args: argparse.Namespace) -> int:
    try:
        result = upload_file_to_oss(load_token_from_stdin(), args.file)
    except OssUploadError as error:
        print(json.dumps({"error": "UPLOAD_FAILED", "message": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Picset AI video creation public client")
    subparsers = parser.add_subparsers(dest="command", required=True)
    upload = subparsers.add_parser("upload", help="Upload a local file using a Picset AI upload token from stdin")
    upload.add_argument("--file", required=True, help="Local image or video path")
    upload.set_defaults(func=_upload)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Encode local UTF-8 SQL files as exact cloudmall_analyze arguments; no network."""
import argparse
import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def bounded(value):
    number = int(value)
    if not 1 <= number <= 1000:
        raise argparse.ArgumentTypeError('must be an integer between 1 and 1000')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*', type=Path)
    parser.add_argument('--batch', action='store_true')
    parser.add_argument('--today', action='store_true')
    parser.add_argument('--max-rows', type=bounded, default=1000)
    parser.add_argument('--max-preview-rows', type=bounded, default=100)
    args = parser.parse_args()
    if args.today:
        print(datetime.now(timezone(timedelta(hours=8), 'Asia/Shanghai')).strftime('%Y%m%d %Z %z'))
        return
    if not 1 <= len(args.files) <= (10 if args.batch else 1):
        parser.error('single requires exactly one SQL file; batch requires 1 to 10')
    queries = []
    try:
        for path in args.files:
            with path.open('rb') as handle:
                raw = handle.read(32769)
            sql = raw.decode('utf-8', errors='strict')
            if not sql.strip() or '\0' in sql or len(raw) > 32768:
                raise ValueError('SQL must be nonempty, without NUL, and at most 32768 UTF-8 bytes')
            queries.append({'sqlBase64': base64.b64encode(raw).decode('ascii'),
                            'maxRows': args.max_rows, 'maxPreviewRows': args.max_preview_rows})
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({'action': 'sql_batch' if args.batch else 'sql_execute',
                      'input': {'sqls': queries} if args.batch else queries[0]}, ensure_ascii=False))


if __name__ == '__main__':
    main()

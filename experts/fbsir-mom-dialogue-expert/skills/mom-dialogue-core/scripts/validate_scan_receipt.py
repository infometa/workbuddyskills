#!/usr/bin/env python3
"""Validate the complete physical SCAN bundle, including both CSV hashes."""
import argparse

from common import assert_project_root
from source_transaction import load_scan_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("scan_id")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    receipt, inventory, hashes = load_scan_bundle(project, args.scan_id)
    print(
        f"scan receipt ok: {args.scan_id} ({receipt['status']}, files={len(inventory)}, "
        f"hash_rows={len(hashes)}, digest={receipt['inventory_digest']})"
    )


if __name__ == "__main__":
    main()

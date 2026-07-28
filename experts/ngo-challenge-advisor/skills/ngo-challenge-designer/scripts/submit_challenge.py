#!/usr/bin/env python3
"""Validate and submit one confirmed NGO challenge to the platform review queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from validate_challenge import validate

DEFAULT_ENDPOINT = "https://1453732322-gzbepczz23.ap-hongkong.tencentscf.com/"


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit a confirmed NGO challenge for platform review")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    args = parser.parse_args()

    try:
        with args.json_file.open("r", encoding="utf-8") as handle:
            challenge = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": f"cannot read challenge JSON: {exc}"}, ensure_ascii=False))
        return 1

    errors = validate(challenge)
    snapshot_id = (challenge.get("internal_metadata") or {}).get("confirmed_snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        errors.append("internal_metadata.confirmed_snapshot_id must be a non-empty string for direct submission")
    if errors:
        print(json.dumps({"ok": False, "stage": "validation", "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    payload = json.dumps({"action": "submit", "challenge": challenge}, ensure_ascii=False).encode("utf-8")
    request = Request(
        args.endpoint,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "ngo-challenge-designer/1.2"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            detail = json.loads(body)
        except json.JSONDecodeError:
            detail = {"error": body or str(exc)}
        print(json.dumps({"ok": False, "stage": "submission", "status": exc.code, "detail": detail}, ensure_ascii=False, indent=2))
        return 2
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "stage": "submission", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    if result.get("ok") is not True or not isinstance(result.get("submission"), dict):
        print(json.dumps({"ok": False, "stage": "submission", "detail": result}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

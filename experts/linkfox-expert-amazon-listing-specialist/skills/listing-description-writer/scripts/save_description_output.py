#!/usr/bin/env python3
"""listing-description-writer 落盘器。

支持 --spec spec.json：用户规格覆盖 Layer B 缺省值（如 charset [1000, 2500]），
平台底线（≤2000）不可放宽。不传 --spec 时行为与历史版本一致。
"""

from __future__ import annotations

import json
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
from listing_spec import check_range, extract_spec_arg  # type: ignore

SLUG = "linkfox-listing-description-writer"
# Layer B 缺省值（历史行为）；可被 --spec 覆盖，平台底线 2000 见 listing_spec
DESC_MAX = 1000

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass


def _read_input(argv: list[str]) -> str:
    if not argv or argv[0] == "-":
        return sys.stdin.read() if not sys.stdin.isatty() else ""
    return open(argv[0], encoding="utf-8").read() if os.path.isfile(argv[0]) else argv[0]


def _validate(payload: dict, spec: dict | None) -> list[str]:
    errors: list[str] = []
    desc = str(payload.get("description") or "")
    if not desc.strip():
        errors.append("缺少 description")
    else:
        payload["char_count"] = len(desc)
        errors.extend(
            check_range(
                len(desc),
                field="description",
                label="description",
                spec=spec,
                max_key="max",
                min_key="min",
                default_max=DESC_MAX,
                default_min=0,
            )
        )
    return errors


def main() -> None:
    argv, spec = extract_spec_arg(sys.argv[1:])
    try:
        payload = json.loads(_read_input(argv))
    except json.JSONDecodeError as e:
        print(f"输入不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(1)

    errors = _validate(payload, spec)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)

    from linkfox_save import save_json_payload  # type: ignore

    # 载荷自描述：UI 的 skill-data-router 按 `kind` 精确路由，没有 kind 的裸 JSON
    # 只能落到 FormattedJsonView 兜底。已有 kind 时不覆盖调用方的值。
    payload.setdefault("kind", "listingDescription")
    payload.setdefault("schema_version", 1)

    save_json_payload(
        SLUG,
        payload,
        summary_lines=[f"已落盘产品描述 {payload.get('char_count')}c，style={payload.get('style', 'narrative')}"],
    )


if __name__ == "__main__":
    main()

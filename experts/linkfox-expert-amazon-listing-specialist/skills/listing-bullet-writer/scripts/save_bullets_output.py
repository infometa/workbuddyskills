#!/usr/bin/env python3
"""listing-bullet-writer 落盘器。

支持 --spec spec.json：用户规格覆盖 Layer B 缺省值（条数/单条区间/合计区间），
平台底线（单条 ≤500、合计 ≤2500）不可放宽。默认合计限制为 255×5=1275；
单条 200 仅是写作建议，不再作为落盘阻断条件。
"""

from __future__ import annotations

import json
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
from listing_spec import check_range, extract_spec_arg, resolve_limit, tag  # type: ignore

SLUG = "linkfox-listing-bullet-writer"
# Layer B 缺省硬上限；Writer 仍以 150–200 为推荐区间，201–255 仅提示。
BULLET_MAX = 255
BULLETS_TOTAL_MAX = 255 * 5
BULLET_COUNT = 5

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
    count, count_layer = resolve_limit(spec, "bullets", "count", BULLET_COUNT)
    bullets = payload.get("bullets")
    if not isinstance(bullets, list) or len(bullets) != count:
        actual = len(bullets) if isinstance(bullets, list) else type(bullets).__name__
        errors.append(f"{tag(count_layer)} bullets 必须是恰好 {count} 条的数组（实际 {actual}）")
    elif not all(isinstance(b, str) and b.strip() for b in bullets):
        errors.append("bullets 每条必须为非空字符串")
    else:
        for idx, bullet in enumerate(bullets, start=1):
            errors.extend(
                check_range(
                    len(bullet),
                    field="bullets",
                    label=f"第 {idx} 条五点",
                    spec=spec,
                    max_key="each_max",
                    min_key="each_min",
                    default_max=BULLET_MAX,
                    default_min=0,
                )
            )
        total = sum(len(bullet) for bullet in bullets)
        payload.setdefault("meta", {})
        if isinstance(payload["meta"], dict):
            payload["meta"]["per_bullet_char"] = [len(bullet) for bullet in bullets]
            payload["meta"]["total_bullet_char"] = total
        errors.extend(
            check_range(
                total,
                field="bullets",
                label="五点合计",
                spec=spec,
                max_key="total_max",
                min_key="total_min",
                default_max=BULLETS_TOTAL_MAX,
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
    payload.setdefault("kind", "listingBullets")
    payload.setdefault("schema_version", 1)

    count = len(payload["bullets"])
    save_json_payload(
        SLUG,
        payload,
        summary_lines=[f"已落盘 {count} 条五点描述，首条: {str(payload['bullets'][0])[:60]}..."],
    )


if __name__ == "__main__":
    main()

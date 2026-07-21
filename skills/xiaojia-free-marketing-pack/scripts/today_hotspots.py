#!/usr/bin/env python3
import argparse
from _common import build_request, get_client_id, get_timeout, open_json, print_json, resolve_content, set_base_url


def main() -> int:
    parser = argparse.ArgumentParser(description="Return today's holiday and hotspot marketing bubbles.")
    parser.add_argument("--content", default="", help="Reserved content input for future matching.")
    parser.add_argument("--content-file", default="", help="Read reserved content from a UTF-8 file.")
    parser.add_argument("--limit", type=int, default=5, help="Number of hotspot bubbles.")
    parser.add_argument("--industry-category", default="", help="Optional industry category filter.")
    parser.add_argument("--base-url", default="", help="Optional JustAI base URL. Persisted for later calls.")
    args = parser.parse_args()

    if args.base_url:
        set_base_url(args.base_url)

    payload = {
        "content": resolve_content(args.content, args.content_file, required=False),
        "limit": args.limit,
    }
    if args.industry_category:
        payload["industry_category"] = args.industry_category

    result = open_json(
        build_request("/openapi/free/today_hotspots", payload, get_client_id()),
        timeout=get_timeout(),
    )
    print_json(result)
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

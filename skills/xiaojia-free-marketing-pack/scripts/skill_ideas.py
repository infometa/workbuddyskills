#!/usr/bin/env python3
import argparse
from _common import build_request, get_client_id, get_timeout, open_json, print_json, resolve_content, set_base_url


def main() -> int:
    parser = argparse.ArgumentParser(description="Return skill idea matches for content.")
    parser.add_argument("--content", default="", help="Input content.")
    parser.add_argument("--content-file", default="", help="Read input content from a UTF-8 file.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of ideas to request.")
    parser.add_argument("--stage", default="", help="Optional skill stage filter.")
    parser.add_argument("--base-url", default="", help="Optional JustAI base URL. Persisted for later calls.")
    args = parser.parse_args()

    if args.base_url:
        set_base_url(args.base_url)

    payload = {
        "content": resolve_content(args.content, args.content_file),
        "top_k": args.top_k,
    }
    if args.stage:
        payload["stage"] = args.stage

    result = open_json(
        build_request("/openapi/free/skill_ideas", payload, get_client_id()),
        timeout=get_timeout(),
    )
    print_json(result)
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

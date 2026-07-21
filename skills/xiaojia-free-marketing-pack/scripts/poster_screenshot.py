#!/usr/bin/env python3
import argparse
from _common import build_request, get_client_id, get_timeout, open_json, print_json, resolve_content, set_base_url


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a poster screenshot or Xiaohongshu note cover from content.")
    parser.add_argument("--content", default="", help="Poster or Xiaohongshu cover content.")
    parser.add_argument("--content-file", default="", help="Read poster or Xiaohongshu cover content from a UTF-8 file.")
    parser.add_argument("--width", type=int, default=300, help="Screenshot width.")
    parser.add_argument("--height", type=int, default=400, help="Screenshot height.")
    parser.add_argument("--template-id", default="", help="Optional note illustration template id.")
    parser.add_argument("--lang", default="zh-CN", help="Rendering language.")
    parser.add_argument("--base-url", default="", help="Optional JustAI base URL. Persisted for later calls.")
    args = parser.parse_args()

    if args.base_url:
        set_base_url(args.base_url)

    payload = {
        "content": resolve_content(args.content, args.content_file),
        "width": args.width,
        "height": args.height,
        "lang": args.lang,
    }
    if args.template_id:
        payload["template_id"] = args.template_id

    result = open_json(
        build_request("/openapi/free/poster_screenshot", payload, get_client_id()),
        timeout=get_timeout(),
    )
    print_json(result)
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

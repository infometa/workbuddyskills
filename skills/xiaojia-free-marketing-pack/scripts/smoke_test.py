#!/usr/bin/env python3
import argparse

from _common import (
    build_request,
    create_client_id,
    get_base_url,
    get_client_id,
    get_pack_version,
    get_source,
    get_timeout,
    open_json,
    print_json,
    save_config,
    set_base_url,
)


def _sample_titles(items: list) -> list[str]:
    titles = []
    for item in items[:3]:
        if isinstance(item, dict):
            title = item.get("name") or item.get("title") or item.get("label")
            if title:
                titles.append(str(title))
    return titles


def _summarize(label: str, payload: dict) -> dict:
    summary = {
        "label": label,
        "status": payload.get("status"),
    }
    if payload.get("client_id"):
        summary["client_id"] = payload.get("client_id")
    for key in ("total", "content_truncated", "content_length", "image_url"):
        if key in payload:
            summary[key] = payload.get(key)

    items = payload.get("ideas") or payload.get("hotspots") or []
    if isinstance(items, list) and items:
        summary["sample_titles"] = _sample_titles(items)
    return summary


def _call(label: str, path: str, payload: dict, client_id: str) -> dict:
    result = open_json(build_request(path, payload, client_id), timeout=get_timeout())
    return _summarize(label, result)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one-command Xiaojia free skill smoke test.")
    parser.add_argument("--base-url", default="", help="Optional JustAI base URL. Persisted before running.")
    parser.add_argument("--skip-poster", action="store_true", help="Skip poster screenshot rendering.")
    parser.add_argument("--force-client-id", action="store_true", help="Create a new local client_id before running.")
    args = parser.parse_args()

    if args.base_url:
        set_base_url(args.base_url)

    client_id = create_client_id() if args.force_client_id else get_client_id()
    save_config(
        {
            "client_id": client_id,
            "source": get_source(),
            "base_url": get_base_url(),
            "timeout": get_timeout(),
            "pack_version": get_pack_version(),
        }
    )

    results = [
        _summarize("init_client", {"status": "ok", "client_id": client_id}),
        _call(
            "skill_ideas",
            "/openapi/free/skill_ideas",
            {
                "content": "Hangzhou coffee shop new opening, Xiaohongshu topic, lunch break discount, photo check-in",
                "top_k": 3,
            },
            client_id,
        ),
        _call(
            "today_hotspots",
            "/openapi/free/today_hotspots",
            {
                "content": "weekend parent-child restaurant campaign",
                "limit": 3,
            },
            client_id,
        ),
    ]

    if not args.skip_poster:
        results.append(
            _call(
                "poster_screenshot",
                "/openapi/free/poster_screenshot",
                {
                    "content": "This weekend, light your life up again",
                    "width": 300,
                    "height": 400,
                },
                client_id,
            )
        )

    ok = all(item.get("status") == "ok" for item in results)
    print_json(
        {
            "status": "ok" if ok else "error",
            "base_url": get_base_url(),
            "results": results,
        }
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

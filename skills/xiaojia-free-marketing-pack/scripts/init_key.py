#!/usr/bin/env python3
import argparse

from _common import (
    CONFIG_PATH,
    CLIENT_ID_ENV_NAME,
    create_client_id,
    get_base_url,
    get_client_id,
    get_pack_version,
    get_source,
    load_config,
    print_json,
    save_config,
    set_base_url,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or show the local Xiaojia free client_id.")
    parser.add_argument("--base-url", default="", help="Optional JustAI base URL. Persisted for later script calls.")
    parser.add_argument("--force", action="store_true", help="Create a new client_id even if one already exists locally.")
    args = parser.parse_args()

    if args.base_url:
        set_base_url(args.base_url)

    if args.force:
        client_id = create_client_id()
        config = load_config()
        config.update(
            {
                "client_id": client_id,
                "source": get_source(),
                "base_url": get_base_url(),
                "pack_version": get_pack_version(),
            }
        )
        save_config(config)
    else:
        get_client_id()
        config = load_config()

    result = {
        "status": "ok",
        "client_id": config.get("client_id") or get_client_id(),
        "source": config.get("source") or get_source(),
        "base_url": get_base_url(),
        "pack_version": config.get("pack_version") or get_pack_version(),
        "config_path": str(CONFIG_PATH),
        "env": CLIENT_ID_ENV_NAME,
    }
    print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

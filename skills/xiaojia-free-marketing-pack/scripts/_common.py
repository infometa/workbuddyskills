#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
import uuid


DEFAULT_BASE_URL = "https://justailab.com"
DEFAULT_TIMEOUT = 120
CLIENT_ID_ENV_NAME = "XIAOJIA_FREE_CLIENT_ID"
BASE_URL_ENV_NAME = "XIAOJIA_FREE_BASE_URL"
TIMEOUT_ENV_NAME = "XIAOJIA_FREE_TIMEOUT"
UNICODE_OUTPUT_ENV_NAME = "XIAOJIA_FREE_UNICODE_OUTPUT"
SOURCE_ENV_NAME = "XIAOJIA_FREE_SOURCE"
PACK_VERSION_ENV_NAME = "XIAOJIA_FREE_PACK_VERSION"
DEFAULT_SOURCE = "codebuddy"
DEFAULT_PACK_VERSION = "0.1.0"
CONFIG_PATH = Path(
    os.environ.get("XIAOJIA_FREE_CONFIG_PATH") or "~/.codebuddy/xiaojia-free-marketing-pack.json"
).expanduser()


def normalize_base_url(value: str = "") -> str:
    return str(value or "").strip().rstrip("/")


def get_base_url() -> str:
    raw_value = normalize_base_url(os.environ.get(BASE_URL_ENV_NAME, ""))
    if not raw_value and CONFIG_PATH.is_file():
        try:
            config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) or {}
            raw_value = normalize_base_url(config_data.get("base_url", ""))
        except (OSError, json.JSONDecodeError):
            raw_value = ""
    return raw_value or DEFAULT_BASE_URL


def set_base_url(base_url: str = "") -> str:
    normalized = normalize_base_url(base_url)
    if not normalized:
        return get_base_url()
    os.environ[BASE_URL_ENV_NAME] = normalized
    config = load_config()
    config["base_url"] = normalized
    save_config(config)
    return normalized


def get_timeout() -> int:
    raw_value = os.environ.get(TIMEOUT_ENV_NAME, "").strip()
    if not raw_value and CONFIG_PATH.is_file():
        try:
            raw_value = str((json.loads(CONFIG_PATH.read_text(encoding="utf-8")) or {}).get("timeout", ""))
        except (OSError, json.JSONDecodeError):
            raw_value = ""
    try:
        return max(int(raw_value or DEFAULT_TIMEOUT), 1)
    except ValueError:
        return DEFAULT_TIMEOUT


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Failed to read local config: {CONFIG_PATH} ({exc})") from exc
    return data if isinstance(data, dict) else {}


def save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_json(data: dict) -> None:
    unicode_output = os.environ.get(UNICODE_OUTPUT_ENV_NAME, "").strip().lower()
    ensure_ascii = unicode_output not in {"1", "true", "yes", "on"}
    print(json.dumps(data, ensure_ascii=ensure_ascii, indent=2))


def get_source() -> str:
    return str(os.environ.get(SOURCE_ENV_NAME, "") or load_config().get("source") or DEFAULT_SOURCE).strip() or DEFAULT_SOURCE


def get_pack_version() -> str:
    return str(
        os.environ.get(PACK_VERSION_ENV_NAME, "") or load_config().get("pack_version") or DEFAULT_PACK_VERSION
    ).strip()


def create_client_id() -> str:
    return f"cb_{uuid.uuid4().hex}"


def get_client_id(auto_create: bool = True) -> str:
    env_value = os.environ.get(CLIENT_ID_ENV_NAME, "").strip()
    if env_value:
        return env_value

    config = load_config()
    config_value = str(config.get("client_id") or "").strip()
    if config_value:
        os.environ[CLIENT_ID_ENV_NAME] = config_value
        return config_value

    if not auto_create:
        raise SystemExit(f"No {CLIENT_ID_ENV_NAME} found. Run init_key.py first.")

    client_id = create_client_id()
    config.update(
        {
            "client_id": client_id,
            "source": get_source(),
            "base_url": get_base_url(),
            "timeout": get_timeout(),
            "pack_version": get_pack_version(),
        }
    )
    save_config(config)
    os.environ[CLIENT_ID_ENV_NAME] = client_id
    return client_id


def build_request(path: str, payload: dict, client_id: str = "") -> urllib.request.Request:
    headers = {
        "Content-Type": "application/json",
        "X-Xiaojia-Source": get_source(),
        "X-Xiaojia-Client-Id": client_id or get_client_id(),
        "X-Xiaojia-Pack-Version": get_pack_version(),
    }
    return urllib.request.Request(
        url=f"{get_base_url()}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )


def open_json(request: urllib.request.Request, timeout: int | None = None) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=timeout or get_timeout()) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(error_body or str(exc), file=sys.stderr)
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        print(body, file=sys.stderr)
        raise SystemExit(1)


def resolve_content(content: str = "", content_file: str = "", required: bool = True) -> str:
    if content and content_file:
        raise SystemExit("--content and --content-file cannot be used together.")
    if content_file:
        try:
            content = Path(content_file).expanduser().read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"Failed to read --content-file: {exc}") from exc
    content = str(content or "").strip()
    if required and not content:
        raise SystemExit("--content or --content-file is required.")
    return content

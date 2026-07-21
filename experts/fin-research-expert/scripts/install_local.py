#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


PACKAGE_NAME = "fin-research-expert"
CONNECTOR_NAME = "tongzhou-fin-research"
EXCLUDED_DOC_ASSET_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".psd", ".sketch", ".webp"}
CONNECTOR_ICON_SUFFIXES = (".svg", ".png")


def _ignore(_dir: str, names: list[str]) -> set[str]:
    ignored = {
        ".git",
        ".gitea",
        ".mypy_cache",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "codex",
        "connectors",
        "inspirations",
        "npm",
        "node_modules",
        "playbooks",
        "dist",
        "tests",
        "workbuddy-expert-audit",
        ".DS_Store",
        ".gitignore",
        ".sms_key",
        ".npm_acc",
        ".mcp.json",
        "export_playbook_cases.py",
        "package_codex_plugin.py",
        "package_layer1_skills.py",
        "package_workbuddy_connector.py",
    }
    ignored.update(name for name in names if name.startswith(".env"))
    if Path(_dir).name == "docs":
        ignored.update(name for name in names if Path(name).suffix.lower() in EXCLUDED_DOC_ASSET_SUFFIXES)
    if "reference-materials" in names:
        ignored.add("reference-materials")
    return ignored.intersection(names)


def install_local(source: Path, marketplace: Path) -> Path:
    source = source.resolve()
    destination = (marketplace.expanduser().resolve() / "plugins" / PACKAGE_NAME)
    if source == destination or source in destination.parents:
        raise SystemExit("destination must not be inside source")
    if not (source / ".codebuddy-plugin" / "plugin.json").exists():
        raise SystemExit(f"not a WorkBuddy expert package: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=_ignore)
    return destination


def install_connector(source: Path, connector_marketplace: Path) -> Path:
    connector_source = source.resolve() / "connectors" / CONNECTOR_NAME
    if not (connector_source / "connector-meta.json").exists():
        raise SystemExit(f"missing local connector source: {connector_source}")
    marketplace = connector_marketplace.expanduser().resolve()
    destination = marketplace / "connectors" / CONNECTOR_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(connector_source, destination)

    # The review bundle keeps icon.svg/icon.png beside connector-meta.json,
    # while WorkBuddy's installed marketplace resolves icons from icons/<source>.*.
    icon_source = next(
        (connector_source / f"icon{suffix}" for suffix in CONNECTOR_ICON_SUFFIXES if (connector_source / f"icon{suffix}").is_file()),
        None,
    )
    if icon_source is None:
        raise SystemExit(f"missing connector icon: {connector_source}/icon.svg or icon.png")
    icons_dir = marketplace / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    for suffix in CONNECTOR_ICON_SUFFIXES:
        stale_icon = icons_dir / f"{CONNECTOR_NAME}{suffix}"
        if stale_icon.exists():
            stale_icon.unlink()
    shutil.copy2(icon_source, icons_dir / f"{CONNECTOR_NAME}{icon_source.suffix.lower()}")
    return destination


def _validate_gateway_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise SystemExit("--gateway-url must be an http(s) URL without embedded credentials")
    return value.rstrip("/")


def configure_local_connector(connector: Path, gateway_url: str) -> None:
    gateway_url = _validate_gateway_url(gateway_url)
    mcp_path = connector / "mcp.json"
    mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
    server = mcp["mcpServers"][CONNECTOR_NAME]
    server["url"] = f"{gateway_url}/mcp/tongzhou-research"
    mcp_path.write_text(json.dumps(mcp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def register_connector(source: Path, connector_marketplace: Path) -> Path:
    catalog_path = connector_marketplace.expanduser().resolve() / ".codebuddy-connector" / "connectors.json"
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        shutil.copy2(catalog_path, catalog_path.with_suffix(f".json.backup-{timestamp}"))
    else:
        catalog = {
            "name": "local-connectors",
            "description": "Locally installed WorkBuddy connectors",
            "owner": "local",
            "auth_injection_rules": {},
            "connectors": [],
        }
    meta = json.loads(
        (source.resolve() / "connectors" / CONNECTOR_NAME / "connector-meta.json").read_text(encoding="utf-8")
    )
    entry = {"id": CONNECTOR_NAME, **meta}
    connectors = catalog.get("connectors")
    if not isinstance(connectors, list):
        raise SystemExit(f"invalid WorkBuddy connector catalog: {catalog_path}")
    catalog["connectors"] = [
        item for item in connectors if not isinstance(item, dict) or item.get("id") != CONNECTOR_NAME
    ] + [entry]
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = catalog_path.with_suffix(".json.installing")
    temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(catalog_path)
    return catalog_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Fin Research Expert into the local WorkBuddy my-experts marketplace.")
    parser.add_argument("--source", default=".", help="Source expert directory.")
    parser.add_argument(
        "--marketplace",
        default=str(Path.home() / ".workbuddy/plugins/marketplaces/my-experts"),
        help="WorkBuddy marketplace directory.",
    )
    parser.add_argument(
        "--skip-connector-registration",
        action="store_true",
        help="Copy connector files without updating the local WorkBuddy connector catalog.",
    )
    parser.add_argument(
        "--connector-marketplace",
        default=str(Path.home() / ".workbuddy/connectors-marketplace"),
        help="WorkBuddy Connector marketplace directory.",
    )
    parser.add_argument(
        "--gateway-url",
        help="Optional Gateway origin override for local Connector validation.",
    )
    args = parser.parse_args()
    source = Path(args.source)
    connector_destination = install_connector(source, Path(args.connector_marketplace))
    if args.gateway_url:
        configure_local_connector(connector_destination, args.gateway_url)
    if not args.skip_connector_registration:
        register_connector(source, Path(args.connector_marketplace))
    destination = install_local(source, Path(args.marketplace))
    _ = connector_destination
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

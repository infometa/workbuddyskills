"""Parse references/asset_inventory.md and read/write manifest.json."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = 2
TOOL_VERSION = "0.2.0"

_MACHINE_BLOCK = re.compile(
    r"<!--\s*machine:(\w+)\s*\n(.*?)\n-->", re.DOTALL
)


def load_inventory(inventory_md: Path) -> Dict[str, Any]:
    """Parse all `<!-- machine:KEY ... -->` JSON blocks from asset_inventory.md."""
    text = inventory_md.read_text(encoding="utf-8")
    out: Dict[str, Any] = {}
    for m in _MACHINE_BLOCK.finditer(text):
        key, body = m.group(1), m.group(2)
        try:
            out[key] = json.loads(body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in inventory section '{key}': {e}") from e
    return out


def sha256_file(path: Path, *, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            h.update(buf)
    return f"sha256:{h.hexdigest()}"


@dataclass
class Manifest:
    tool_version: str = TOOL_VERSION
    schema_version: int = SCHEMA_VERSION
    export_time: str = ""
    source_variant: str = "unknown"
    source_root: str = ""
    source_user_id: Optional[str] = None
    source_user_ids_all: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    asset_inventory: Dict[str, Any] = field(default_factory=dict)
    checksums: Dict[str, str] = field(default_factory=dict)
    # v2 additions for cross-machine migration
    source_os: str = ""
    source_hostname: str = ""
    source_home: str = ""
    source_workbuddy_dir: str = ""
    workspaces: List[Dict[str, Any]] = field(default_factory=list)
    workspaces_package: Optional[str] = None  # filename of accompanying -workspaces.zip

    @classmethod
    def now(cls, **kw) -> "Manifest":
        m = cls(**kw)
        if not m.export_time:
            m.export_time = datetime.now().astimezone().isoformat(timespec="seconds")
        return m

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        data = json.loads(path.read_text(encoding="utf-8"))
        # Accept v1 manifests by filling missing fields
        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def validate_for_import(self) -> None:
        if self.schema_version > SCHEMA_VERSION:
            raise ValueError(
                f"Package schema_version={self.schema_version} is newer than "
                f"tool's supported {SCHEMA_VERSION}. Upgrade the migration tool."
            )

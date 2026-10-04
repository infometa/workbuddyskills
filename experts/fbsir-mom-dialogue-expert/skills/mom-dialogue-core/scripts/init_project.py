#!/usr/bin/env python3
"""Create a marked project and schema-derived ledgers without touching sources."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    MARKER_NAME,
    fail,
    file_sha256,
    initialize_marker,
    iso_now,
    safe_new_project_root,
    safe_project_dir,
    safe_project_path,
    schema_fields,
    schema_path,
    write_csv,
    write_json_atomic,
    write_text_atomic,
)

DIRS = [
    "00_项目看板",
    "01_原始生活资料",
    "02_素材账",
    "02_素材账/scan-runs",
    "02_素材账/ledger-history",
    "03_人物与关系",
    "04_转写与OCR",
    "05_媒体索引",
    "06_事件与生活轨迹",
    "07_问题与回答",
    "08_故事卡",
    "09_心愿与家庭行动",
    "10_大纲与章节",
    "11_隐私与授权",
    "12_版本与检查点",
    "12_版本与检查点/locks",
    "13_导出成果",
]

FILES = {
    "00_项目看板/项目说明.md": "# 项目说明\n\n主叙事妈妈：\n家庭主编：\n项目目标：\n授权来源：\n期望成果：\n隐私边界：\n",
    "00_项目看板/素材地图.md": "# 素材地图\n\n尚未完成首次来源扫描。\n",
    "00_项目看板/当前状态.md": "# 当前状态\n\n状态：已初始化\n已盘点资料：0\n待确认人物：0\n故事卡：0\n权限待确认：0\n",
    "00_项目看板/下一步.md": "# 下一步\n\n推荐动作：登记一个已授权的生活资料目录。\n",
    "00_项目看板/续接胶囊.md": "# 续接胶囊\n\n最近检查点：无\n当前批次：无\n待处理：登记来源并扫描\n",
    "00_项目看板/本轮结果.md": "# 本轮结果\n\n项目结构已创建，尚未读取任何生活资料。\n",
}


def load_catalog() -> tuple[Path, dict]:
    path = Path(__file__).resolve().parents[1] / "schemas" / "schema-catalog.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != "2.0":
        fail(f"unsupported schema catalog: {path}")
    return path, data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    args = parser.parse_args()
    root = safe_new_project_root(args.project_dir)
    if root.exists() and not (root / MARKER_NAME).exists():
        existing = list(root.iterdir())
        if existing:
            fail("refuse to initialize a non-empty unmarked directory")
    if not root.exists():
        root.mkdir(parents=True)
    initialize_marker(root)
    for name in DIRS:
        safe_project_dir(root, name)
    for name, text in FILES.items():
        path = safe_project_path(root, name)
        if not path.exists():
            write_text_atomic(path, text, project_root=root)

    catalog_path, catalog = load_catalog()
    for entry in catalog["ledgers"]:
        path = safe_project_path(root, entry["path"])
        if not path.exists():
            write_csv(path, schema_fields(schema_path(entry["schema"])), [], project_root=root)

    registry = safe_project_path(root, "00_项目看板/source-roots.json")
    if not registry.exists():
        write_json_atomic(registry, {"schema_version": "2.0", "roots": []}, project_root=root)
    schema_state = safe_project_path(root, "00_项目看板/schema-state.json")
    if not schema_state.exists():
        write_json_atomic(
            schema_state,
            {
                "schemaVersion": "2.0",
                "catalogSha256": file_sha256(catalog_path),
                "initializedAt": iso_now(),
                "ledgerCount": len(catalog["ledgers"]),
            },
            project_root=root,
        )
    print(f"initialized project: {root}")


if __name__ == "__main__":
    main()

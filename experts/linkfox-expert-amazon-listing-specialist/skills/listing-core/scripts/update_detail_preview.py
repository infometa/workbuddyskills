#!/usr/bin/env python3
"""把作图链路的 collection-asset-manifest.json 回写进 amazon-detail-preview.json。

与 agent-listing-result-html-skill/scripts/merge-listing-assets.mjs 同一套 asset
归一规则（src/url/image/path/localPath/publicUrl；slot 显式给出或按 type 判 aplus）。
只更新图片区（images / aplusImages / imagesSource），Listing 文案字段一律不动；
manifest 中出现非公开 URL（本地路径 / file://）直接失败——先用 linkfox-file-upload
换公开链接，这与 HTML 合并链路的护栏一致。

用法：
    python3 update_detail_preview.py \
        --preview /abs/.../03-write/amazon-detail-preview.json \
        --asset-manifest /abs/.../collection-asset-manifest.json \
        [--product-index 0] [--append]

默认生成图**替换**原 images（参考竞品图完成历史使命被撤下）；--append 改为追加。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_APLUS_RE = re.compile(r"APLUS|A\+|PLUS", re.IGNORECASE)
_SRC_KEYS = ("src", "url", "image", "path", "localPath", "publicUrl")
_LABEL_KEYS = ("label", "caption", "name")


def _load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [] if value is None else [value]


def _slot_for(item: dict[str, Any]) -> str:
    slot = item.get("slot")
    if isinstance(slot, str) and slot.strip():
        return slot.strip()
    type_hint = str(item.get("type") or item.get("assetType") or item.get("taskType") or "")
    return "aplus" if _APLUS_RE.search(type_hint) else "main"


def normalize_assets(payload: Any) -> list[dict[str, str]]:
    if isinstance(payload, list):
        source: list[Any] = []
        for item in payload:
            if not isinstance(item, dict):
                source.append(item)
                continue
            assets = _ensure_list(item.get("assets"))
            if assets:
                source.extend(assets)
            else:
                source.extend(
                    {"src": src, "type": item.get("type")}
                    for src in _ensure_list(item.get("images"))
                )
    else:
        source = _ensure_list(payload.get("assets") if isinstance(payload, dict) else None)

    out: list[dict[str, str]] = []
    for index, item in enumerate(source):
        if isinstance(item, str):
            item = {"src": item}
        if not isinstance(item, dict):
            continue
        src = next(
            (item[k] for k in _SRC_KEYS if isinstance(item.get(k), str) and item[k].strip()),
            None,
        )
        if not src:
            continue
        label = next(
            (item[k] for k in _LABEL_KEYS if isinstance(item.get(k), str) and item[k].strip()),
            f"素材图 {index + 1}",
        )
        out.append({"src": src.strip(), "alt": label, "slot": _slot_for(item)})
    return out


def update_preview(
    preview_path: str,
    asset_manifest_path: str,
    product_index: int = 0,
    append: bool = False,
) -> dict[str, Any]:
    preview = _load_json(preview_path)
    if not isinstance(preview, dict) or not isinstance(preview.get("products"), list):
        raise ValueError(f"not an amazon-detail-preview envelope: {preview_path}")
    products = preview["products"]
    if not 0 <= product_index < len(products):
        raise ValueError(f"product index {product_index} out of range (0..{len(products) - 1})")

    assets = normalize_assets(_load_json(asset_manifest_path))
    if not assets:
        raise ValueError(f"asset manifest has no usable assets: {asset_manifest_path}")
    non_public = [a["src"] for a in assets if not re.match(r"^https?://", a["src"], re.I)]
    if non_public:
        raise ValueError(
            "asset manifest contains non-public image paths; upload local media with "
            f"linkfox-file-upload before merging. Examples: {', '.join(non_public[:3])}"
        )

    main_images = [{"src": a["src"], "alt": a["alt"]} for a in assets if a["slot"] != "aplus"]
    aplus_images = [{"src": a["src"], "alt": a["alt"]} for a in assets if a["slot"] == "aplus"]

    product = products[product_index]
    if main_images:
        # 参考竞品图不参与保留——append 语义只叠加既有「本品/生成」图
        kept: list[dict[str, Any]] = []
        if append and product.get("imagesSource") != "reference":
            kept = [img for img in _ensure_list(product.get("images")) if isinstance(img, dict)]
        seen = {img.get("src") for img in kept}
        product["images"] = kept + [img for img in main_images if img["src"] not in seen]
        product["imagesSource"] = "generated"
    if aplus_images:
        kept_aplus = [img for img in _ensure_list(product.get("aplusImages")) if isinstance(img, dict)]
        seen_aplus = {img.get("src") for img in kept_aplus}
        product["aplusImages"] = kept_aplus + [
            img for img in aplus_images if img["src"] not in seen_aplus
        ]
    preview["generatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with open(preview_path, "w", encoding="utf-8") as handle:
        json.dump(preview, handle, ensure_ascii=False, indent=2)
    return {
        "preview": str(Path(preview_path).resolve()),
        "main": len(main_images),
        "aplus": len(aplus_images),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", required=True)
    parser.add_argument("--asset-manifest", required=True)
    parser.add_argument("--product-index", type=int, default=0)
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()
    result = update_preview(
        preview_path=args.preview,
        asset_manifest_path=args.asset_manifest,
        product_index=args.product_index,
        append=args.append,
    )
    print(f"Merged detail preview assets: {result['main']} main, {result['aplus']} aplus")
    print(f"JSON artifact: {result['preview']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Concurrent asset downloader for WorkRally batch image generation（MCP 版）.

数据来源是 **MCP 工具 `asset_search` 的返回**（由 Agent 落盘为 JSON），
本脚本只做「按 title 前缀过滤 + 并发 curl 下载」，不发起任何 WorkRally API 调用，
也不需要 workrally CLI 或 API Key。

Usage:
  # 1) Agent 先调 MCP: asset_search(project_id="<PID>", material_type=["image"], page_size=100)
  #    把返回原样写入 /tmp/workrally/assets.json
  # 2) 再跑本脚本：
  python3 download_assets.py /tmp/workrally/assets.json ./out/ CAT01_,CAT02_,AI_TIER

若返回里 asset_details.url 缺失或已过期（签名约 10 小时），
先让 Agent 调 asset_detail(asset_ids=[...])（一次最多 50 个）重新取 URL 再下载。

输入 JSON 结构假设（asset_search 返回）：
    {"assets": [{"title": "...", "asset_details": {"url": "https://..."}}, ...]}
"""
import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path

if len(sys.argv) < 4:
    print("Usage: download_assets.py <assets.json> <out_dir> <prefix1,prefix2,...>")
    sys.exit(1)

assets_path = sys.argv[1]
out_dir = Path(sys.argv[2])
prefixes = [p for p in sys.argv[3].split(",") if p]

out_dir.mkdir(parents=True, exist_ok=True)

with open(assets_path) as f:
    data = json.load(f)

# 兼容顶层就是数组，或包含在 assets / data / list 字段里
if isinstance(data, list):
    assets = data
else:
    assets = data.get("assets") or data.get("data") or data.get("list") or []

items = []
skipped_no_url = []
for a in assets:
    title = (a.get("title") or "").replace(".png", "")
    if not any(title.startswith(p) for p in prefixes):
        continue
    details = a.get("asset_details") or {}
    url = details.get("download_url") or details.get("url") or ""
    if not url:
        skipped_no_url.append(title)
        continue
    items.append((title, url, str(out_dir / f"{title.lower()}.jpg")))


def dl(item):
    name, url, path = item
    subprocess.run(["curl", "-sL", "--fail", "-o", path, url], check=False)
    return path


with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
    list(ex.map(dl, items))

print(f"Downloaded {len(items)} images to {out_dir}")
if skipped_no_url:
    print(f"⚠️ {len(skipped_no_url)} 条无可用 URL（签名可能过期），请先用 asset_detail 重取：")
    for t in skipped_no_url[:10]:
        print("   -", t)

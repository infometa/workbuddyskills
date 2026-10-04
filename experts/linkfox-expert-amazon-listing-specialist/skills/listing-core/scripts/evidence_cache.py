#!/usr/bin/env python3
"""共享证据缓存：跨会话、跨场景复用计费检索结果（Product Detail / SIF / 评论明细等）。

设计见 references/evidence-cache-protocol.md。要点：

- 缓存根 = writable_root()/.listing-cache/evidence/（writable_root 见 linkfox_paths.py：
  $LINKFOX_WORKSPACE → cwd → tmp。跨会话持久取决于 LINKFOX_WORKSPACE 指向持久卷）。
- 条目 = 一个索引 JSON（key 摘要命名），指向真实落盘的原始响应路径；本脚本不复制大响应。
- 负结果（empty/error）同样入缓存：TTL 内不得静默重试同参计费检索（与预算规则一致）。
- lookup 命中时打印 age_hours，调用方必须把数据时点写进产物的 data_confidence。

用法：
  python3 evidence_cache.py store  --type product-detail --key-asin B0X --key-site US \
      --path /abs/saved-response.json [--status ok|empty|error] [--key k=v ...]
  python3 evidence_cache.py lookup --type product-detail --key-asin B0X --key-site US \
      [--key k=v ...] [--ttl-hours N]

lookup 输出单行 JSON：{"hit": bool, "path": str|null, "age_hours": float|null,
"status": "ok|empty|error"|null}。exit code 恒为 0（未命中不是错误）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from linkfox_paths import writable_root  # noqa: E402

# 类型级默认 TTL（小时）。未列出的类型走 DEFAULT_TTL_HOURS。
TTL_HOURS_BY_TYPE = {
    "product-detail": 24,   # 页面事实/评论摘要，日级变化
    "keyword-matrix": 168,  # SIF 30 天窗口数据，周级才有意义变化（matrix 脚本另有自身缓存）
    "reviews-list": 168,    # 评论明细，计费高、变化慢
}
DEFAULT_TTL_HOURS = 24
NEGATIVE_TTL_HOURS = 24  # empty/error 负结果统一 24h，别把失败缓存太久


def _cache_dir() -> str:
    path = os.path.join(writable_root(), ".listing-cache", "evidence")
    os.makedirs(path, exist_ok=True)
    return path


def _digest(kind: str, keys: dict[str, str]) -> str:
    raw = json.dumps({"type": kind, "keys": keys}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _entry_path(kind: str, keys: dict[str, str]) -> str:
    return os.path.join(_cache_dir(), f"{kind}-{_digest(kind, keys)}.json")


def _collect_keys(args: argparse.Namespace) -> dict[str, str]:
    keys: dict[str, str] = {}
    if args.key_asin:
        keys["asin"] = args.key_asin.strip().upper()
    if args.key_site:
        keys["site"] = args.key_site.strip().upper()
    for item in args.key or []:
        if "=" not in item:
            raise SystemExit(f"--key 需要 k=v 形式，收到: {item!r}")
        k, v = item.split("=", 1)
        keys[k.strip()] = v.strip()
    if not keys:
        raise SystemExit("至少提供一个 key（--key-asin / --key-site / --key k=v）")
    return keys


def store_evidence(kind: str, keys: dict[str, str], path: str,
                   status: str = "ok") -> dict[str, object]:
    """库入口：登记证据，供 run_pipeline 在同一进程批量调用。"""
    normalized_path = os.path.abspath(path)
    if status not in {"ok", "empty", "error"}:
        raise ValueError(f"illegal evidence status: {status}")
    if status == "ok" and not os.path.isfile(normalized_path):
        raise ValueError(f"status=ok 但响应文件不存在: {normalized_path}")
    entry = {
        "type": kind,
        "keys": keys,
        "path": normalized_path,
        "status": status,
        "created_at": time.time(),
    }
    entry_path = _entry_path(kind, keys)
    with open(entry_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    return {"stored": True, "entry": entry_path}


def lookup_evidence(kind: str, keys: dict[str, str],
                    ttl_hours: float | None = None) -> dict[str, object]:
    """库入口：查询证据；miss 也是正常结果，不抛异常。"""
    miss: dict[str, object] = {
        "hit": False, "path": None, "age_hours": None, "status": None,
    }
    entry_path = _entry_path(kind, keys)
    if not os.path.isfile(entry_path):
        return miss
    try:
        with open(entry_path, encoding="utf-8") as f:
            entry = json.load(f)
    except (OSError, json.JSONDecodeError):
        return miss
    age_hours = (time.time() - float(entry.get("created_at", 0))) / 3600
    status = entry.get("status", "ok")
    if ttl_hours is not None:
        ttl = ttl_hours
    elif status != "ok":
        ttl = NEGATIVE_TTL_HOURS
    else:
        ttl = TTL_HOURS_BY_TYPE.get(kind, DEFAULT_TTL_HOURS)
    if age_hours > ttl:
        return miss
    path = entry.get("path")
    if status == "ok" and (not path or not os.path.isfile(path)):
        return miss
    return {
        "hit": True,
        "path": path,
        "age_hours": round(age_hours, 2),
        "status": status,
    }


def cmd_store(args: argparse.Namespace) -> None:
    keys = _collect_keys(args)
    try:
        result = store_evidence(args.type, keys, args.path, args.status)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False))


def cmd_lookup(args: argparse.Namespace) -> None:
    keys = _collect_keys(args)
    print(json.dumps(
        lookup_evidence(args.type, keys, args.ttl_hours), ensure_ascii=False,
    ))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--type", required=True,
                       help="证据类型：product-detail / keyword-matrix / reviews-list / 其它")
        p.add_argument("--key-asin", help="ASIN（会归一为大写）")
        p.add_argument("--key-site", help="站点（US/JP/DE…，会归一为大写）")
        p.add_argument("--key", action="append",
                       help="附加 key（k=v，可多次；如 returnAuthorsReviews=true、window=30d）")

    p_store = sub.add_parser("store", help="登记一次检索结果")
    add_common(p_store)
    p_store.add_argument("--path", required=True, help="原始响应落盘绝对路径（Saved full response）")
    p_store.add_argument("--status", choices=("ok", "empty", "error"), default="ok")
    p_store.set_defaults(func=cmd_store)

    p_lookup = sub.add_parser("lookup", help="查询同参缓存")
    add_common(p_lookup)
    p_lookup.add_argument("--ttl-hours", type=float, help="覆盖默认 TTL（小时）")
    p_lookup.set_defaults(func=cmd_lookup)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

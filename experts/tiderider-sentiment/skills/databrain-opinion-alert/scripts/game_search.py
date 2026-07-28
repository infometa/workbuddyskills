#!/usr/bin/env python3
"""
Databrain 游戏 ID 查询脚本。
根据游戏名称关键词查询 unified_edition_id。

用法:
  python game_search.py "Wuthering Waves" "Honkai: Star Rail"

认证:
    DATABRAIN_TOKEN — 认证 token，由服务端环境变量注入
    DATABRAIN_HOST  — 可选；设置后仅用该 host，否则按优先级自动 fallback
"""
import os
import sys
import json
from pathlib import Path
from urllib.parse import urlparse

import httpx

API_PATH = "/api/v1/intelligence_pc/chatbi/search"

_FALLBACK_HOSTS = (
    "https://databrain.intlgame.com",
    "https://databrain.woa.com",
    "https://databrain-global.intlgame.com",
)

_resolved_host: str | None = None


def _load_dotenv() -> None:
    """Load .env from skill root (local dev only; server env vars take priority)."""
    skill_dir = Path(__file__).parent.parent
    env_path = skill_dir / ".env"
    if env_path.is_file():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and os.environ.get(k) is None:
                        os.environ[k] = v


def _is_trusted_host(host: str) -> bool:
    hostname = urlparse(host).hostname or ""
    if hostname in ("databrain.intlgame.com", "databrain.woa.com"):
        return True
    if hostname.startswith("databrain-") and hostname.endswith(".intlgame.com"):
        return True
    return False


def _get_config(
    token: str | None = None,
    host: str | None = None,
) -> tuple[str, list[str]]:
    """Return (token, hosts_to_try)."""
    global _resolved_host
    _load_dotenv()
    token = (token or os.environ.get("DATABRAIN_TOKEN", "")).strip()
    if not token:
        return "", []  # caller handles missing token

    explicit = (host or os.environ.get("DATABRAIN_HOST", "")).strip().rstrip("/")
    if explicit:
        if not _is_trusted_host(explicit):
            return token, []  # invalid host → caller handles
        return token, [explicit]

    if _resolved_host:
        return token, [_resolved_host]

    return token, list(_FALLBACK_HOSTS)


def search_games(
    keywords: list[str],
    *,
    token: str | None = None,
    host: str | None = None,
    top: int = 1,
) -> dict:
    """
    按游戏名关键词查询 unified_edition_id。

    :param keywords: 游戏名称列表
    :param top: 每个关键词返回的最大候选数
    :return: {"games": [...]} 或 {"error": {...}}
    """
    global _resolved_host
    tok, hosts = _get_config(token, host)

    if not tok:
        return {"error": {"code": "CONFIG", "message": "DATABRAIN_TOKEN not set"}}
    if not hosts:
        return {"error": {"code": "CONFIG", "message": "DATABRAIN_HOST is not a trusted domain"}}

    payload = {
        "keywords": keywords,
        "entity_type": "pc,console,mobile",
        "system": "intelligence,dashboard,opinion",
        "top": top,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tok}",
    }

    last_error: Exception | None = None
    for h in hosts:
        try:
            resp = httpx.post(h + API_PATH, headers=headers, json=payload, timeout=30.0)
        except httpx.HTTPError as e:
            last_error = e
            if len(hosts) > 1:
                print(f"[fallback] {h} failed ({e.__class__.__name__}), trying next...", file=sys.stderr)
            continue

        if resp.status_code != 200:
            msg = resp.text.strip()[:500]
            if resp.status_code == 401:
                msg = msg or "Unauthorized: token 无效、过期或无权限"
            last_error = RuntimeError(f"HTTP {resp.status_code}: {msg}")
            if len(hosts) > 1:
                print(f"[fallback] {h} returned {resp.status_code}, trying next...", file=sys.stderr)
            continue

        try:
            body = resp.json()
        except Exception:
            last_error = RuntimeError(f"无法解析响应 JSON: {resp.text[:200]}")
            continue

        if body.get("code") != 0:
            return {"error": {"code": body.get("code"), "message": body.get("msg", "unknown error")}}

        if len(hosts) > 1:
            _resolved_host = h

        games = []
        for entry in body.get("data", []):
            keyword = entry.get("keyword", "")
            hits = entry.get("list", [])
            if hits:
                hit = hits[0]
                games.append({
                    "keyword":       keyword,
                    "game_id":       hit.get("game_id", ""),
                    "game_name":     hit.get("game_name", ""),
                    "entity_name":   hit.get("entity_name", ""),
                    "entity_name_ch": hit.get("entity_name_ch", ""),
                    "release_time":  hit.get("release_time", ""),
                    "match_score":   hit.get("match_score", 0),
                })
            else:
                games.append({"keyword": keyword, "game_id": None, "game_name": None, "error": "no results found"})

        return {"games": games}

    return {"error": {"code": "REQUEST", "message": f"All hosts failed. Last error: {last_error}"}}


def main() -> int:
    if len(sys.argv) < 2:
        print('用法: python game_search.py "Game Name 1" "Game Name 2" ...', file=sys.stderr)
        return 1

    keywords = [arg.strip() for arg in sys.argv[1:]]
    result = search_games(keywords)

    if "error" in result:
        print("Error:", json.dumps(result["error"], ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

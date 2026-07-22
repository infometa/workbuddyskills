#!/usr/bin/env python3
"""
game_search.py — 按游戏名查 unified_edition_id（移植自 databrain-opinion-alert，3.9 兼容）。

用法:
  python scripts/game_search.py "PUBG Mobile"
  python scripts/game_search.py "Wuthering Waves" "Honkai: Star Rail"
  python scripts/game_search.py --self_test

库使用:
  from game_search import search_games, resolve_first_game_id
  result = search_games(["PUBG Mobile"])
  game_id = resolve_first_game_id("PUBG Mobile")  # 直接拿首个匹配的 game_id

认证:
  DATABRAIN_TOKEN — 认证 token，由服务端环境变量注入或 .env 注入
  DATABRAIN_HOST  — 可选；设置后仅用该 host，否则按 fallback 顺序
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx

API_PATH = "/api/v1/intelligence_pc/chatbi/search"

# 优先使用 woa 内网域名（响应稳定、不走 EdgeOne），其他作为 fallback。
_FALLBACK_HOSTS = (
    "https://databrain.woa.com",
    "https://databrain.intlgame.com",
    "https://databrain-global.intlgame.com",
)

_resolved_host: Optional[str] = None


# ---------------------------------------------------------------------------
# Env / host helpers（与 query_executor 完全对齐）
# ---------------------------------------------------------------------------
_DOTENV_LOADED = False


def _load_dotenv() -> None:
    """Load .env from skill root（本地开发用；生产由服务端注入环境变量）.

    Once-only：避免在已 pop env var 的测试场景下被重复回填。
    """
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    env_path = Path(__file__).resolve().parent.parent / ".env"
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
    token: Optional[str] = None,
    host: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """Return (token, hosts_to_try)."""
    global _resolved_host
    _load_dotenv()
    token = (token or os.environ.get("DATABRAIN_TOKEN", "")).strip()
    if not token:
        return "", []  # caller handles missing token

    explicit = (host or os.environ.get("DATABRAIN_HOST", "")).strip().rstrip("/")
    if explicit:
        if not _is_trusted_host(explicit):
            return token, []
        return token, [explicit]

    if _resolved_host:
        return token, [_resolved_host]

    return token, list(_FALLBACK_HOSTS)


# ---------------------------------------------------------------------------
# 主查询
# ---------------------------------------------------------------------------
def search_games(
    keywords: List[str],
    *,
    token: Optional[str] = None,
    host: Optional[str] = None,
    top: int = 1,
) -> dict:
    """
    按游戏名关键词查询 unified_edition_id。

    返回:
      成功: {"games": [{"keyword", "game_id", "game_name", "entity_name",
                        "entity_name_ch", "release_time", "match_score"}, ...]}
      失败: {"error": {"code": "...", "message": "..."}}
    """
    global _resolved_host
    tok, hosts = _get_config(token, host)

    if not tok:
        return {"error": {"code": "CONFIG", "message": "DATABRAIN_TOKEN 未设置"}}
    if not hosts:
        return {"error": {"code": "CONFIG", "message": "DATABRAIN_HOST 不在受信任域名列表"}}

    payload = {
        "keywords": keywords,
        "entity_type": "pc,console,mobile",
        "system": "intelligence,dashboard,opinion",
        "top": int(top),
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tok}",
    }

    last_error: Optional[Exception] = None
    for h in hosts:
        try:
            resp = httpx.post(h + API_PATH, headers=headers, json=payload, timeout=30.0)
        except httpx.HTTPError as e:
            last_error = e
            if len(hosts) > 1:
                print(f"[fallback] {h} failed ({e.__class__.__name__}), trying next...",
                      file=sys.stderr)
            continue

        if resp.status_code != 200:
            msg = resp.text.strip()[:500]
            if resp.status_code == 401:
                msg = msg or "Unauthorized: token 无效、过期或无权限"
            last_error = RuntimeError(f"HTTP {resp.status_code}: {msg}")
            if len(hosts) > 1:
                print(f"[fallback] {h} returned {resp.status_code}, trying next...",
                      file=sys.stderr)
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
                    "keyword":        keyword,
                    "game_id":        hit.get("game_id", ""),
                    "game_name":      hit.get("game_name", ""),
                    "entity_name":    hit.get("entity_name", ""),
                    "entity_name_ch": hit.get("entity_name_ch", ""),
                    "release_time":   hit.get("release_time", ""),
                    "match_score":    hit.get("match_score", 0),
                })
            else:
                games.append({
                    "keyword": keyword, "game_id": None, "game_name": None,
                    "error": "no results found",
                })

        return {"games": games}

    return {"error": {"code": "REQUEST",
                      "message": f"All hosts failed. Last error: {last_error}"}}


def resolve_first_game_id(game_name: str, **kwargs) -> Tuple[Optional[str], Optional[str]]:
    """
    便捷封装：给一个游戏名 → 返回 (game_id, resolved_game_name)。
    未找到时返回 (None, None)；出错时抛 RuntimeError。
    """
    if not game_name or not str(game_name).strip():
        raise ValueError("game_name 不能为空")
    result = search_games([game_name.strip()], **kwargs)
    if "error" in result:
        raise RuntimeError(f"game_search 失败: {result['error']}")
    games = result.get("games") or []
    if not games:
        return None, None
    g = games[0]
    if not g.get("game_id"):
        return None, None
    return g["game_id"], g.get("game_name") or game_name


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--self_test":
        return _self_test()
    if len(sys.argv) < 2:
        print('用法: python scripts/game_search.py "Game Name 1" "Game Name 2" ...',
              file=sys.stderr)
        print('     python scripts/game_search.py --self_test', file=sys.stderr)
        return 1

    keywords = [arg.strip() for arg in sys.argv[1:]]
    result = search_games(keywords)

    if "error" in result:
        print("Error:", json.dumps(result["error"], ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Self test（不联网验证 helper / 边界）
# ---------------------------------------------------------------------------
def _self_test() -> int:
    fails: List[str] = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            fails.append(name)

    print("=== game_search self test ===")

    _check("_is_trusted_host 接受 global",
           _is_trusted_host("https://databrain-global.intlgame.com"))
    _check("_is_trusted_host 接受 woa",
           _is_trusted_host("https://databrain.woa.com"))
    _check("_is_trusted_host 拒绝 evil 子域",
           not _is_trusted_host("https://evil.intlgame.com.evil/"))
    _check("_is_trusted_host 拒绝 http://localhost",
           not _is_trusted_host("http://localhost:8080"))
    _check("_is_trusted_host 拒绝空 host",
           not _is_trusted_host(""))

    # resolve_first_game_id 输入校验
    for bad in ("", "  ", None):
        try:
            resolve_first_game_id(bad)
            _check(f"resolve_first_game_id 拒绝空输入 {bad!r}", False)
        except (ValueError, AttributeError):
            _check(f"resolve_first_game_id 拒绝空输入 {bad!r}", True)

    # _get_config 在无 token 时返回空 token
    # 防御 .env 副作用：标记 dotenv 已加载，避免 pop 后又被回填
    global _DOTENV_LOADED
    saved_loaded = _DOTENV_LOADED
    _DOTENV_LOADED = True
    saved = os.environ.pop("DATABRAIN_TOKEN", None)
    try:
        tok, hosts = _get_config()
        _check("_get_config 无 token 时返回空", tok == "")
    finally:
        if saved is not None:
            os.environ["DATABRAIN_TOKEN"] = saved
        _DOTENV_LOADED = saved_loaded

    # _get_config 显式传 invalid host 时拒绝
    saved_t = os.environ.get("DATABRAIN_TOKEN")
    os.environ["DATABRAIN_TOKEN"] = "fake_token_for_test"
    try:
        tok, hosts = _get_config(host="https://evil.example.com")
        _check("_get_config 拒绝 untrusted host", tok and not hosts)
    finally:
        if saved_t is None:
            os.environ.pop("DATABRAIN_TOKEN", None)
        else:
            os.environ["DATABRAIN_TOKEN"] = saved_t

    print("\n" + "-" * 40)
    if fails:
        print(f"FAIL: {len(fails)}")
        return 1
    print(f"PASS: all game_search tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())

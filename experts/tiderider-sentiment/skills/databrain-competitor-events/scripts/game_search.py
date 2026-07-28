#!/usr/bin/env python3
"""
Databrain 游戏 ID 查询脚本。
根据游戏名称关键词查询 unified_edition_id。

用法:
  python game_search.py "Wuthering Waves" "Honkai: Star Rail"
"""
import os
import sys
import json

import httpx

_DEFAULT_HOST = "https://databrain.intlgame.com"
API_PATH = "/api/v1/intelligence_pc/chatbi/search"


def _load_dotenv() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.abspath(os.path.join(script_dir, ".."))
    plugin_root = os.path.abspath(os.path.join(skill_dir, "..", ".."))
    for base in [plugin_root, skill_dir, os.getcwd(), script_dir]:
        env_path = os.path.join(base, ".env")
        if os.path.isfile(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and os.environ.get(k) is None:
                            os.environ[k] = v


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
    :return: {"results": [...]} 或 {"error": {...}}
    """
    _load_dotenv()

    token = (token or os.environ.get("DATABRAIN_TOKEN", "")).strip()
    if not token:
        return {"error": {"code": "CONFIG", "message": "DATABRAIN_TOKEN not set"}}

    host = (host or os.environ.get("DATABRAIN_INTL_HOST", _DEFAULT_HOST)).strip().rstrip("/")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "keywords": keywords,
        "entity_type": "pc,console,mobile",
        "system": "intelligence,dashboard,opinion",
        "top": top,
    }

    try:
        resp = httpx.post(host + API_PATH, headers=headers, json=payload, timeout=30.0)
    except httpx.HTTPError as e:
        return {"error": {"code": "REQUEST", "message": str(e)}}

    if resp.status_code != 200:
        msg = resp.text.strip()[:500] or ("Unauthorized: token 无效、过期或无权限" if resp.status_code == 401 else "")
        return {"error": {"code": resp.status_code, "message": msg}}

    try:
        body = resp.json()
    except Exception:
        return {"error": {"code": "PARSE", "message": f"无法解析响应 JSON: {resp.text[:200]}"}}

    if body.get("code") != 0:
        return {"error": {"code": body.get("code"), "message": body.get("msg", "unknown error")}}

    # 提取每个 keyword 对应的第一个结果的 game_name + game_id
    games = []
    for entry in body.get("data", []):
        keyword = entry.get("keyword", "")
        hits = entry.get("list", [])
        if hits:
            hit = hits[0]
            games.append({
                "keyword": keyword,
                "game_id": hit.get("game_id", ""),
                "game_name": hit.get("game_name", ""),
                "entity_name": hit.get("entity_name", ""),
                "entity_name_ch": hit.get("entity_name_ch", ""),
                "release_time": hit.get("release_time", ""),
                "match_score": hit.get("match_score", 0),
            })
        else:
            games.append({"keyword": keyword, "game_id": None, "game_name": None, "error": "no results found"})

    return {"games": games}


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

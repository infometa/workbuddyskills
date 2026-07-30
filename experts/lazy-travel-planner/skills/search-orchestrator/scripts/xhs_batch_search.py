#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xhs_batch_search.py · 调用 xiaohongshu-cli 做批量搜索
关键设计：
  - 并发 ≤ 2（xhs CLI 自带反风控，超过 2 容易触发 461/471）
  - 连续错误 >= threshold → 立即降级到 WebSearch
  - 缓存：同一 query 在 30 天内复用 data/.cache/xhs/ 结果
"""
import json, subprocess, hashlib, time, pathlib, os
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "data" / ".cache" / "xhs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_DAYS = 30


def _cache_key(q: str) -> pathlib.Path:
    h = hashlib.md5(q.encode("utf-8")).hexdigest()[:12]
    return CACHE_DIR / f"{h}.json"


def _read_cache(q: str):
    p = _cache_key(q)
    if not p.exists():
        return None
    age = time.time() - p.stat().st_mtime
    if age > CACHE_TTL_DAYS * 86400:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(q: str, data):
    _cache_key(q).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _xhs_search_single(q: str) -> dict:
    """调一次 xhs CLI；返回 {ok, query, notes:[...]} 或 {ok:False, error}"""
    cached = _read_cache(q)
    if cached is not None:
        return {"ok": True, "query": q, "notes": cached.get("notes", []), "from_cache": True}

    if not _xhs_available():
        return {"ok": False, "query": q, "error": "xhs_not_installed"}

    try:
        r = subprocess.run(
            ["xhs", "search", q, "--sort", "popular", "--type", "all", "--json"],
            capture_output=True, text=True, timeout=45
        )
        if r.returncode != 0:
            stderr = (r.stderr or "")[:200]
            if any(c in stderr for c in ("461", "471", "captcha", "验证码")):
                return {"ok": False, "query": q, "error": "rate_limited"}
            return {"ok": False, "query": q, "error": f"xhs_failed: {stderr}"}
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            return {"ok": False, "query": q, "error": "xhs_bad_json"}

        notes = []
        if isinstance(data, dict):
            payload = data.get("data") if data.get("ok") else None
            if isinstance(payload, dict):
                notes = payload.get("items") or payload.get("notes") or []
            elif isinstance(data.get("items"), list):
                notes = data["items"]
        result = {"ok": True, "query": q, "notes": notes}
        _write_cache(q, result)
        return result
    except subprocess.TimeoutExpired:
        return {"ok": False, "query": q, "error": "timeout"}
    except FileNotFoundError:
        return {"ok": False, "query": q, "error": "xhs_not_installed"}


def _xhs_available() -> bool:
    try:
        r = subprocess.run(["xhs", "status", "--json"],
                           capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False


def _websearch_fallback(queries: list) -> list:
    """xhs 不可用时降级；这里返回占位标记，上层 agent 应换用 WebSearch."""
    return [{
        "ok": True, "query": q, "notes": [],
        "fallback": True,
        "_doc": "请上层 agent 用 WebSearch 兜底，并在 confidence 标 yellow"
    } for q in queries]


def xhs_batch_search(queries: list, concurrency: int = 2,
                     error_threshold: int = 3) -> list:
    """主入口：批量跑 xhs search，自动熔断降级"""
    if not _xhs_available():
        print("[xhs_batch_search] ⚠️ xhs CLI 未安装或未登录，降级到 WebSearch")
        return _websearch_fallback(queries)

    results = []
    consecutive_errors = 0
    fallback_pending = []

    with ThreadPoolExecutor(max_workers=max(1, min(concurrency, 2))) as ex:
        futs = {ex.submit(_xhs_search_single, q): q for q in queries}
        for fut in as_completed(futs):
            q = futs[fut]
            r = fut.result()
            if r.get("ok"):
                results.append(r)
                consecutive_errors = 0
            else:
                err = r.get("error", "")
                if err == "rate_limited":
                    consecutive_errors += 1
                else:
                    # 非风控错误也记一笔，但不增加熔断
                    pass
                results.append(r)
                if consecutive_errors >= error_threshold:
                    print(f"[xhs_batch_search] 🚨 连续 {error_threshold} 次风控，全部降级 WebSearch")
                    fallback_pending = [
                        futs[f] for f in futs if not f.done() or not futs[f] in [x.get("query") for x in results if x.get("ok")]
                    ]
                    break
    if fallback_pending:
        results.extend(_websearch_fallback(fallback_pending))
    return results


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", required=True, help="JSON 数组文件")
    a = ap.parse_args()
    qs = json.load(open(a.queries, encoding="utf-8"))
    out = xhs_batch_search(qs)
    print(json.dumps(out, ensure_ascii=False, indent=2))

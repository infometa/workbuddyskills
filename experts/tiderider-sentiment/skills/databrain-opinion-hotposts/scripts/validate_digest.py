#!/usr/bin/env python3
"""
validate_digest.py — 校验 agent 产出的 digest_spec.json（渲染前的护栏）。

schema 见 references/digest_schema.md。校验项：
  - 顶层必填：game_name / digest_time / platforms
  - 每平台必填：display / posts(list)
  - 每帖 8 必选字段齐全：rank/title/author/followers/time/engagement/sentiment/summary/url
  - sentiment ∈ {正面,中性,负面}
  - summary 为字符串或 null（失败兜底）
  - url 为 http(s)（允许空串/缺省，渲染器会跳过）
  - 每平台 posts ≤ top_n（默认 5）
  - 同一平台同事件最多 2 条（按 agent 标注的 _event_id；未标注则跳过该项）

用法：
  python scripts/validate_digest.py --input spec.json --top_n 5
  python scripts/validate_digest.py --self_test

返回：通过 exit 0；不通过打印错误清单 + exit 1（供 agent 据此修正后重渲染）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

_VALID_SENTIMENTS = ("正面", "中性", "负面")
_REQUIRED_POST_FIELDS = (
    "rank", "title", "author", "followers", "time", "engagement", "sentiment", "summary", "url",
)


def validate_spec(spec: dict, *, top_n: int = 5) -> List[str]:
    """返回错误列表；空列表表示通过。"""
    errors: List[str] = []

    if not isinstance(spec, dict):
        return ["顶层必须是 JSON object"]

    for key in ("game_name", "digest_time", "platforms"):
        if key not in spec or spec.get(key) in (None, ""):
            errors.append(f"顶层缺少必填字段: {key}")

    platforms = spec.get("platforms")
    if not isinstance(platforms, list):
        errors.append("platforms 必须是数组")
        return errors

    # summary（可选，但若有需结构合法）
    summary = spec.get("summary")
    if summary is not None and not isinstance(summary, dict):
        errors.append("summary 必须是 object 或省略")
    if isinstance(summary, dict):
        topics = summary.get("topics")
        if topics is not None:
            if not isinstance(topics, list):
                errors.append("summary.topics 必须是数组")
            else:
                for i, t in enumerate(topics):
                    if not (isinstance(t, (list, tuple)) and len(t) == 2):
                        errors.append(f"summary.topics[{i}] 应为 [标签, 帖数] 二元组")

    for pi, p in enumerate(platforms):
        tag = f"platforms[{pi}]"
        if not isinstance(p, dict):
            errors.append(f"{tag} 必须是 object")
            continue
        if not p.get("display"):
            errors.append(f"{tag} 缺少 display")
        posts = p.get("posts")
        if posts is None:
            posts = []
        if not isinstance(posts, list):
            errors.append(f"{tag}.posts 必须是数组")
            continue
        if len(posts) > top_n:
            errors.append(f"{tag}.posts 超过 top_n={top_n}（实际 {len(posts)} 条）")

        # 同事件 ≤ 2（仅当 agent 标注 _event_id 时校验）
        event_count: dict = {}
        for qi, post in enumerate(posts):
            ptag = f"{tag}.posts[{qi}]"
            if not isinstance(post, dict):
                errors.append(f"{ptag} 必须是 object")
                continue
            for f in _REQUIRED_POST_FIELDS:
                if f not in post:
                    errors.append(f"{ptag} 缺少必选字段: {f}")
            # sentiment
            if post.get("sentiment") not in _VALID_SENTIMENTS:
                errors.append(
                    f"{ptag}.sentiment 必须是 正面/中性/负面，实际 {post.get('sentiment')!r}"
                )
            # summary 字符串或 null
            s = post.get("summary", "MISSING")
            if s != "MISSING" and s is not None and not isinstance(s, str):
                errors.append(f"{ptag}.summary 必须是字符串或 null")
            # title 非空
            if not str(post.get("title") or "").strip():
                errors.append(f"{ptag}.title 不能为空")
            # url：允许空/缺省，但若非空必须 http(s)
            url = post.get("url")
            if url and not (isinstance(url, str) and url.startswith(("http://", "https://"))):
                errors.append(f"{ptag}.url 非法（需 http/https 或留空）: {url!r}")
            # rank/engagement/followers 数值
            for numf in ("rank", "engagement", "followers"):
                v = post.get(numf)
                if v is not None and not isinstance(v, (int, float)):
                    errors.append(f"{ptag}.{numf} 应为数值，实际 {v!r}")

            eid = post.get("_event_id")
            if eid:
                event_count[eid] = event_count.get(eid, 0) + 1
        for eid, cnt in event_count.items():
            if cnt > 2:
                errors.append(f"{tag} 同事件 {eid!r} 出现 {cnt} 条（§4.3.3 最多 2 条）")

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="校验 digest_spec.json（渲染前护栏）")
    parser.add_argument("--input", help="digest_spec.json 路径")
    parser.add_argument("--top_n", type=int, default=5, help="每平台允许的最大帖数（默认 5）")
    parser.add_argument("--self_test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    if not args.input:
        parser.error("--input 必传（digest_spec.json 路径）")

    try:
        spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[ERROR] 读取/解析 spec 失败: {e}", file=sys.stderr)
        sys.exit(1)

    errors = validate_spec(spec, top_n=args.top_n)
    if errors:
        print(f"[INVALID] digest_spec 校验未通过（{len(errors)} 项）：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    print("[OK] digest_spec 校验通过")


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
def _valid_spec() -> dict:
    return {
        "game_name": "NIKKE",
        "digest_time": "2026-04-22 09:00",
        "summary": {"sentiment": {"pos": 0.3, "neu": 0.4, "neg": 0.3}, "topics": [["新卡池", 7]]},
        "platforms": [{
            "display": "🔥 Reddit · r/NIKKE",
            "posts": [{
                "rank": 1, "title": "P2W scam", "author": "u/a", "followers": 100,
                "time": "2026-04-22T21:00:00Z", "engagement": 1240,
                "sentiment": "负面", "summary": "吐槽卡池", "url": "https://reddit.com/x",
            }],
        }],
    }


def _self_test() -> int:
    fails: List[str] = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            fails.append(name)

    print("=== validate_digest self test ===")

    _check("合法 spec 通过", validate_spec(_valid_spec()) == [])

    # 缺顶层字段
    s = _valid_spec(); del s["game_name"]
    _check("缺 game_name 报错", any("game_name" in e for e in validate_spec(s)))

    # sentiment 非法
    s = _valid_spec(); s["platforms"][0]["posts"][0]["sentiment"] = "positive"
    _check("非法 sentiment 报错", any("sentiment" in e for e in validate_spec(s)))

    # summary 为 null 合法
    s = _valid_spec(); s["platforms"][0]["posts"][0]["summary"] = None
    _check("summary=null 合法", validate_spec(s) == [])

    # summary 非字符串非 null 报错
    s = _valid_spec(); s["platforms"][0]["posts"][0]["summary"] = 123
    _check("summary 数字报错", any("summary" in e for e in validate_spec(s)))

    # url 非法
    s = _valid_spec(); s["platforms"][0]["posts"][0]["url"] = "javascript:alert(1)"
    _check("非法 url 报错", any("url" in e for e in validate_spec(s)))

    # url 空合法
    s = _valid_spec(); s["platforms"][0]["posts"][0]["url"] = ""
    _check("空 url 合法", validate_spec(s) == [])

    # 缺必选字段
    s = _valid_spec(); del s["platforms"][0]["posts"][0]["engagement"]
    _check("缺 engagement 报错", any("engagement" in e for e in validate_spec(s)))

    # title 空
    s = _valid_spec(); s["platforms"][0]["posts"][0]["title"] = "  "
    _check("空 title 报错", any("title" in e for e in validate_spec(s)))

    # 超 top_n
    s = _valid_spec()
    base = s["platforms"][0]["posts"][0]
    s["platforms"][0]["posts"] = [dict(base, rank=i) for i in range(6)]
    _check("超 top_n=5 报错", any("top_n" in e for e in validate_spec(s, top_n=5)))

    # 同事件 > 2
    s = _valid_spec()
    s["platforms"][0]["posts"] = [dict(base, rank=i, _event_id="E1") for i in range(3)]
    _check("同事件 3 条报错", any("同事件" in e for e in validate_spec(s)))

    # 同事件 2 条合法
    s = _valid_spec()
    s["platforms"][0]["posts"] = [dict(base, rank=i, _event_id="E1") for i in range(2)]
    _check("同事件 2 条合法", validate_spec(s) == [])

    print("\n" + "-" * 40)
    if fails:
        print(f"FAIL: {len(fails)}")
        return 1
    print("PASS: all validate tests")
    return 0


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
dedup.py — 同事件去重的「可选粗筛工具」（标题前缀指纹方案）。

⚠️ 角色说明（架构升级后）：
  本 skill 现采用 agent-driven 架构（见 SKILL.md）：去重的「最终裁断」由 agent
  读 title+snippet 完成（能识别标题党改写 / 中英同事件），因为 LLM 比字符前缀准。
  本模块降级为 **可选粗筛工具**：候选很多时，agent 可先用 fingerprint 做一遍粗分组
  减少逐对比对量，再人工裁断。dedup_posts 保留为参考实现。

规则（来自 §4.3.3，最终由 agent 在 digest_spec 中落实）：
  - 同一平台 Top N 中，相同事件最多保留 2 条
  - 被挤出的位置由下一位候选补齐
  - 推送时标注「同一话题 N 条相关讨论已合并展示 2 条」

fingerprint 算法（零依赖）：
  - 标题（或正文）转小写
  - 去掉标点 / 表情 / 多余空白
  - 保留前 N 个 letter/digit/CJK/假名 字符（默认 30）
  - 该字符串 = 指纹
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

# 标点 + emoji + 控制字符全部拍平为空
_STRIP_RE = re.compile(
    r"[\s\u3000\.,!?;:'\"()\[\]{}<>「」『』、，。！？；：·_\-—~`@#$%^&*+=|\\/]+"
)


def fingerprint(text: str, *, prefix_chars: int = 30) -> str:
    """文本 → 去噪 → 取前 N 字符。空串返回空串。"""
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", str(text)).lower()
    # 保留 letter / digit / cjk，丢弃其他
    cleaned: list[str] = []
    for ch in s:
        if ch.isalnum():
            cleaned.append(ch)
        elif "\u4e00" <= ch <= "\u9fff":  # CJK 统一汉字
            cleaned.append(ch)
        elif "\u3040" <= ch <= "\u30ff":  # 平/片假名
            cleaned.append(ch)
        # 其他全部丢
    return "".join(cleaned)[:prefix_chars]


def dedup_posts(
    posts: list[dict],
    *,
    title_field: str = "title",
    fallback_field: str = "snippet",
    prefix_chars: int = 30,
    keep_per_event: int = 2,
    final_top_n: int = 5,
) -> tuple[list[dict], dict[str, int]]:
    """
    去重并截断到 final_top_n。

    posts: 已按互动量降序排好序的候选列表（建议给 final_top_n * 3 倍候选用于补位）
    返回: (kept_posts, merged_counts)
      kept_posts    : 最终入选 ≤ final_top_n 条，每条多一个 _event_id 字段
      merged_counts : {event_id: 该 event 总共有多少条候选被合并}（仅含 > keep_per_event 的）

    [Why] 候选传足够多（如 top_n × 3），同一事件最多挤掉 keep_per_event 后还能补位到 final_top_n。
    """
    kept: list[dict] = []
    seen_event_count: dict[str, int] = {}
    candidate_event_count: dict[str, int] = {}

    for p in posts:
        # 选指纹源：优先 title，没有用 fallback；都没有用 reviewer 防 None
        src = p.get(title_field) or p.get(fallback_field) or p.get("reviewer", "")
        fp = fingerprint(src, prefix_chars=prefix_chars) or f"__noid_{len(candidate_event_count)}"
        candidate_event_count[fp] = candidate_event_count.get(fp, 0) + 1

        if seen_event_count.get(fp, 0) >= keep_per_event:
            continue  # 该事件已收满 keep_per_event 条
        seen_event_count[fp] = seen_event_count.get(fp, 0) + 1

        out = dict(p)
        out["_event_id"] = fp
        kept.append(out)
        if len(kept) >= final_top_n:
            break

    # 仅返回那些"被合并"的 event（候选数 > keep_per_event）
    merged_counts = {fp: cnt for fp, cnt in candidate_event_count.items()
                     if cnt > keep_per_event}
    return kept, merged_counts


# ---------------------------------------------------------------------------
# CLI / Self test
# ---------------------------------------------------------------------------
def _self_test() -> int:
    fails: list[str] = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            fails.append(name)

    print("=== dedup self test ===")

    # fingerprint
    _check("fingerprint 大小写无关",
           fingerprint("Hello World") == fingerprint("HELLO world"))
    _check("fingerprint 去标点",
           fingerprint("hello, world!") == "helloworld")
    _check("fingerprint 中文保留",
           fingerprint("新卡池出货率太低！！") == "新卡池出货率太低")
    _check("fingerprint 日文保留",
           "ピックアップ" in fingerprint("ピックアップ率"))
    _check("fingerprint 截断到 N 字符",
           len(fingerprint("a" * 100, prefix_chars=10)) == 10)
    _check("fingerprint 空串 → 空",
           fingerprint("") == "" and fingerprint(None) == "")
    _check("fingerprint emoji 丢掉",
           "😀" not in fingerprint("hello 😀 world"))

    # dedup_posts: 6 条 candidates，前 3 条同事件（前 30 字符指纹一致），
    # 应保留 2 条同事件 + 3 条独立 = 5 条；同事件被合并 1 条
    # 注意：清理后 30 字符前缀必须一致才视为同事件
    # 这里前缀 = "p2wscambanneralertagainsamedet"（30 char，前缀完全一致）
    posts = [
        {"title": "P2W scam banner alert again same detail-A", "engagement": 1240},
        {"title": "P2W scam banner alert again same detail-B", "engagement": 980},
        {"title": "P2W scam banner alert again same detail-C", "engagement": 750},
        {"title": "Alice skin showcase video", "engagement": 620},
        {"title": "Story arc theory mother whale", "engagement": 510},
        {"title": "Best team comp guide updated", "engagement": 410},
    ]
    kept, merged = dedup_posts(posts, final_top_n=5, keep_per_event=2)
    titles = [p["title"] for p in kept]
    _check("dedup 同事件最多 2 条",
           sum(1 for t in titles if "p2w scam banner" in t.lower()) <= 2,
           f"got titles={titles}")
    _check("dedup 后裡补位到 final_top_n",
           len(kept) == 5,  # 5 = 2 P2W + Alice + Story + Best team
           f"got len={len(kept)}, titles={titles}")
    _check("dedup 返回 merged_counts 含被合并的事件",
           any(c > 2 for c in merged.values()), f"merged={merged}")

    # 候选数过少时不补位
    kept2, _ = dedup_posts(posts[:2], final_top_n=5, keep_per_event=2)
    _check("dedup 候选不足时按实际数返回", len(kept2) == 2)

    # final_top_n 限制
    posts_unique = [{"title": f"unique title {i}", "engagement": 1000 - i} for i in range(10)]
    kept3, _ = dedup_posts(posts_unique, final_top_n=3, keep_per_event=2)
    _check("dedup final_top_n 限制生效", len(kept3) == 3)

    # _event_id 注入
    _check("dedup 每条注入 _event_id",
           all("_event_id" in p for p in kept))

    print("\n" + "-" * 40)
    if fails:
        print(f"FAIL: {len(fails)}")
        return 1
    print("PASS: all dedup tests")
    return 0


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="同事件去重（标题前缀指纹）")
    parser.add_argument("--self_test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        import sys
        sys.exit(_self_test())
    parser.error("仅支持 --self_test 模式（库使用见 docstring）")


if __name__ == "__main__":
    main()

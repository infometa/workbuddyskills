#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行家话题检索 —— 按职位族 / 职位 / 关键词打分，返回 Top N。

**运行时只走这个脚本，不要直接 Read data/mentors.json**（322 条、389KB，
读进上下文既浪费又容易让模型把相邻条目的字段串错）。

用法：
    # 【推荐】直接从画像读职位族和职位，不用自己传（字段驼峰/下划线都兼容）
    python match_mentors.py --from-profile <rtx> --topn 5
    python match_mentors.py --from-profile <rtx> --need "晋级答辩" --topn 5

    # 手工指定（画像里没有、或用户口头说了自己的族/职位时）
    python match_mentors.py --clan-code TE --position "后台开发" --topn 5

    # 画像缺失时只按关键词兜底
    python match_mentors.py --need "职业规划" --topn 5

    # 查有哪些族 / 某族有哪些职位（用于引导用户自选）
    python match_mentors.py --list-clans
    python match_mentors.py --list-positions TE

输出 JSON：{"ok":true,"query":{...},"total_pool":322,"results":[...]}
每条 result 的 url 必须原样给用户，禁止改写或重新拼接。
"""
import argparse
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "mentors.json"

# 职位名里的常见近义写法，用于「职位不完全同名但其实同一类」的软匹配。
# 只做保守扩展；宁可少匹配，也不要把设计岗算成开发岗。
POSITION_KIN = {
    "后台开发": ["服务端", "后端", "后台"],
    "前端开发": ["前端", "web开发"],
    "客户端开发": ["客户端", "终端开发", "移动开发"],
    "应用开发": ["应用研发"],
    "产品策划": ["产品经理", "产品规划"],
    "产品运营": ["运营"],
    "游戏运营": ["游戏运营", "发行运营"],
    "综合项目管理": ["项目管理", "pmo"],
    "研发项目管理": ["项目管理", "研发管理"],
    "产品体验设计": ["交互设计", "ui", "ux", "体验设计"],
    "学习发展": ["培训", "人才发展", "od"],
    "招聘调配": ["招聘", "hr"],
    "商业分析": ["数据分析", "bi"],
    "技术咨询": ["解决方案", "售前"],
}


def clan_code(raw):
    """从「技术族（TE）」提出 TE。提不出返回 None，绝不猜。"""
    if not raw:
        return None
    m = re.search(r"[（(]([A-Z]{2})[)）]", raw)
    if m:
        return m.group(1)
    for name, code in {"技术族": "TE", "产品/项目族": "PD", "设计族": "DG",
                       "市场族": "MA", "专业族": "SC"}.items():
        if name in raw:
            return code
    return None


def load():
    if not DATA.exists():
        raise SystemExit(json.dumps(
            {"ok": False, "error": f"行家数据文件不存在：{DATA}",
             "hint": "名单未随包分发或路径不对；不要凭记忆编行家，直接告诉用户暂时查不到。"},
            ensure_ascii=False))
    return json.loads(DATA.read_text(encoding="utf-8"))


def read_profile(rtx):
    """从 profile.json 读职位族和职位。

    实测 basic 是驼峰（clanName/positionName），而 schema 文档写的是下划线，
    两种都读一遍，读不到就返回 None——不猜、不用上下文补。
    """
    p = Path.home() / ".workbuddy" / "career-broker" / rtx / "profile.json"
    if not p.exists():
        return None, None, f"没有 {rtx} 的画像文件"
    try:
        basic = json.loads(p.read_text(encoding="utf-8")).get("basic") or {}
    except (json.JSONDecodeError, OSError) as e:
        return None, None, f"画像读取失败：{e}"

    clan_raw = basic.get("clanName") or basic.get("clan_name")
    position = basic.get("positionName") or basic.get("position_name") or basic.get("position")
    if not clan_raw and not position:
        return None, None, "画像里没有职位族和职位字段"
    return clan_code(clan_raw), position, None


def norm(s):
    return re.sub(r"[\s／/\-_（）()]+", "", (s or "").lower())


def position_score(user_pos, topic_pos):
    """职位匹配：完全同名 40 分，近义 26，包含关系 18，同字段片段 10。"""
    if not user_pos or not topic_pos:
        return 0, ""
    u, t = norm(user_pos), norm(topic_pos)
    if u == t:
        return 40, "同职位"
    kin = POSITION_KIN.get(topic_pos, []) + POSITION_KIN.get(user_pos, [])
    for k in kin:
        nk = norm(k)
        if nk and (nk in u or nk in t):
            return 26, "相近职位"
    if u in t or t in u:
        return 18, "职位相关"
    # 中文双字重叠（"产品策划" vs "产品运营" → 产品）
    for n in (3, 2):
        for i in range(len(u) - n + 1):
            if u[i:i + n] in t:
                return 10, "职位部分相关"
    return 0, ""


def need_score(needs, topic):
    """用户诉求关键词命中话题名 / 分类 / 标签 / 大纲。"""
    if not needs:
        return 0, []
    hay = {
        "topic": norm(topic["topic"]),
        "category": norm(topic["category"]),
        "tags": norm(" ".join(topic["tags"])),
        "outline": norm(topic["outline"]),
    }
    score, hit = 0, []
    for kw in needs:
        nk = norm(kw)
        if not nk:
            continue
        if nk in hay["topic"]:
            score += 22
            hit.append(kw)
        elif nk in hay["tags"]:
            score += 18
            hit.append(kw)
        elif nk in hay["category"]:
            score += 14
            hit.append(kw)
        elif nk in hay["outline"]:
            score += 8
            hit.append(kw)
    return min(score, 55), sorted(set(hit))


def rank(topics, clan_code, position, needs, topn):
    scored = []
    for t in topics:
        s, reasons = 0, []

        # 1) 职位族 —— 用户明确要求"族要合适"，所以给最高权重
        if clan_code:
            if t["clan_code"] == clan_code:
                s += 34
                reasons.append("同职位族")
            else:
                s -= 12  # 跨族不排除（有通用话题），但压后

        # 2) 职位
        ps, pr = position_score(position, t["position"])
        s += ps
        if pr:
            reasons.append(pr)

        # 3) 用户诉求关键词
        ns, nhit = need_score(needs, t)
        s += ns
        if nhit:
            reasons.append("诉求匹配：" + "、".join(nhit))

        # 4) 被咨询过的话题略微加权（有人验证过），上限 8 分，不让热度盖过匹配度
        s += min(t["consult_count"], 8)

        if s > 0:
            scored.append((s, t, reasons))

    scored.sort(key=lambda x: (-x[0], -x[1]["consult_count"], x[1]["topic"]))

    out = []
    for s, t, reasons in scored[:topn]:
        out.append({
            "score": s,
            "match_reasons": reasons,
            "mentor_rtx": t["mentor_rtx"],
            "mentor_name": t["mentor_name"],
            "position": t["position"],
            "clan": t["clan"],
            "topic": t["topic"],
            "category": t["category"],
            "tags": t["tags"],
            "outline": t["outline"],
            "credential": t["credential"],
            "hours": t["hours"],
            "consult_count": t["consult_count"],
            "audience": t["audience"],
            "url": t["url"],
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-profile", default=None, metavar="RTX",
                    help="从 ~/.workbuddy/career-broker/<rtx>/profile.json 读职位族和职位")
    ap.add_argument("--clan-code", default=None, help="职位族简码：TE/PD/DG/MA/SC")
    ap.add_argument("--position", default=None, help="用户当前职位，如「后台开发」")
    ap.add_argument("--need", default=None, help="用户诉求关键词，多个用逗号分隔")
    ap.add_argument("--topn", type=int, default=5)
    ap.add_argument("--list-clans", action="store_true")
    ap.add_argument("--list-positions", default=None, metavar="CLAN_CODE")
    args = ap.parse_args()

    data = load()
    topics = data["topics"]

    if args.list_clans:
        agg = {}
        for t in topics:
            key = t["clan"]
            agg.setdefault(key, {"clan": key, "clan_code": t["clan_code"], "topic_count": 0})
            agg[key]["topic_count"] += 1
        print(json.dumps({"ok": True, "clans": sorted(agg.values(), key=lambda x: -x["topic_count"])},
                         ensure_ascii=False, indent=1))
        return 0

    if args.list_positions:
        code = args.list_positions.upper()
        agg = {}
        for t in topics:
            if t["clan_code"] != code:
                continue
            agg[t["position"]] = agg.get(t["position"], 0) + 1
        if not agg:
            print(json.dumps({"ok": False, "error": f"没有职位族 {code} 的话题",
                              "hint": "先跑 --list-clans 看合法族码"}, ensure_ascii=False))
            return 1
        print(json.dumps({"ok": True, "clan_code": code,
                          "positions": [{"position": k, "topic_count": v}
                                        for k, v in sorted(agg.items(), key=lambda x: -x[1])]},
                         ensure_ascii=False, indent=1))
        return 0

    needs = [x.strip() for x in re.split(r"[,，、;；]+", args.need or "") if x.strip()]
    clan = args.clan_code.upper() if args.clan_code else None
    position = args.position
    profile_note = None

    # --from-profile：显式传的参数优先，画像只补空缺
    if args.from_profile:
        p_clan, p_pos, err = read_profile(args.from_profile)
        if err:
            profile_note = err
        clan = clan or p_clan
        position = position or p_pos

    if clan and clan not in set(data["clan_codes"].values()):
        print(json.dumps({"ok": False, "error": f"职位族简码 {clan} 不存在",
                          "valid": sorted(set(data['clan_codes'].values())),
                          "hint": "族码只能来自画像或用户明说，不许猜"}, ensure_ascii=False))
        return 2

    if not (clan or position or needs):
        print(json.dumps({"ok": False, "error": "拿不到职位族/职位/诉求，无法匹配",
                          "profile_note": profile_note,
                          "hint": "先问用户一句「你现在做哪个方向、想聊点什么」，或让他自己选族；不要随机推。"},
                         ensure_ascii=False))
        return 2

    results = rank(topics, clan, position, needs, args.topn)

    print(json.dumps({
        "ok": True,
        "query": {"clan_code": clan, "position": position, "need": needs, "topn": args.topn},
        "profile_note": profile_note,
        "total_pool": len(topics),
        "result_count": len(results),
        "results": results,
        "hint": "url 必须原样输出给用户，禁止改写/拼接/换域名。0 条结果时按 SKILL.md 兜底，不要编行家。",
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

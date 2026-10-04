#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_result_code.py
解析 DNA 结果码 → 结构化 JSON。

测评站现在有 3 个版本，产码段数不同（事实源：http://21.6.92.38:8082/ 各页 calcResult()）：

  初阶员工版 junior.html  → 9 段，尾部 |D:主/辅|V:JR
  中高阶员工版 senior.html → 9 段，尾部 |D:主/辅|V:SR
  管理者版 manager.html   → 13 段，尾部 |SL:主/辅|EF:|FX:|AD:|DG:|R:|K:|N:|V:MG

历史版本（8080 旧站）只有 4 段或 7 段，仍然兼容：
  4 段：DNA|A|S|P
  7 段：DNA|A|S|P|R|K|N

调用：
    python parse_result_code.py "<结果码>"
输出 result.assessment_kind 供上层判断该用哪套解读（junior / senior / manager / legacy）。
"""
import argparse, json, re, sys


ANCHOR_NAMES = {
    "TEC": "技术/职能型", "CHL": "挑战型", "ENT": "创业型", "MGT": "管理型",
    "AUT": "自主/独立型", "SER": "服务/奉献型", "SEC": "安全/稳定型", "LIF": "生活方式型",
}
# 注意：TC = Technical Craft「技术深耕」，与测评站 dimLabel 一致。
# 三个新站点（junior/senior/manager）的 dimLabel 均为 TC:"技术深耕"，已逐一核对。
# 历史版本曾误标为「协作力/Teamwork」，已修正——题目问的是"自己啃文档/研究底层原理"。
STYLE_NAMES = {
    "CR": "创造驱动", "AN": "分析洞察", "CN": "连接影响",
    "TC": "技术深耕", "SY": "系统掌控", "EM": "人文关怀",
}
PSY_NAMES = {"B": "倦怠指数", "O": "开放性", "E": "自我效能感"}

# 性格底色（DISC）—— 员工版专有，来自站点 DISC_META，逐字对齐，不要自己改写
DISC_NAMES = {
    "D": "支配掌控型", "I": "影响社交型", "S": "稳定支持型", "C": "严谨审慎型",
}
DISC_DESC = {
    "D": "事情一紧，倾向于先把结果保住，该拍板就拍板",
    "I": "事情一紧，倾向于把人带动起来，气氛顺了事就顺了",
    "S": "事情一紧，倾向于先顾着别让人扛不住，宁可自己多担一点",
    "C": "事情一紧，倾向于先把情况和后果弄清楚，再决定怎么动",
}

# 领导风格（SLII）—— 管理者版专有，来自站点 SL2_META，逐字对齐
SL_NAMES = {"S1": "指令型", "S2": "教练型", "S3": "支持型", "S4": "授权型"}
SL_DESC = {
    "S1": "定目标、给步骤、盯执行。适合带「热情的初学者（D1）」",
    "S2": "教方法、听想法、带讨论。适合带「憧憬幻灭的学习者（D2）」",
    "S3": "多鼓励、给信任、做后盾。适合带「能干但谨慎的执行者（D3）」",
    "S4": "敢放手、授全权、看结果。适合带「独立自主的完成者（D4）」",
}

# 版本标识 → 测评类型
VERSION_KIND = {"JR": "junior", "SR": "senior", "MG": "manager"}
KIND_LABEL = {
    "junior": "初阶员工版（工龄 5 年以内）",
    "senior": "中高阶员工版（工龄 5 年及以上）",
    "manager": "管理者版",
    "legacy": "旧版（无版本标识）",
}

# 只在遇到 "|XX:" 这种「竖线 + 大写段前缀」时切段，
# 避免 R/K/N 里用户自填内容含 "|" 时被误切。
SEG_SPLIT = re.compile(r"\|(?=[A-Z]{1,3}:)")


def parse_section(section: str, code_len: int = 3) -> dict:
    """
    A:TEC10CHL7ENT5... 或 S:CR4AN3...
    code_len = 3（A 段）/ 2（S 段）；分值可能是多位数
    """
    pattern = rf"([A-Z]{{{code_len}}})(\d+)"
    return {m.group(1): int(m.group(2)) for m in re.finditer(pattern, section)}


def parse_psy(section: str) -> dict:
    """ P:B2.5O4.0E3.5 """
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"([BOE])(\d+\.\d+)", section)}


def parse_pair(section: str, allow: dict, label: str) -> dict | None:
    """
    解析 "主/辅" 型字段：D:D/I 或 SL:S2/S3
    allow 为合法代码表；非法值不静默丢弃，抛错让上层发现。
    """
    if not section:
        return None
    parts = [p.strip() for p in section.split("/") if p.strip()]
    if not parts:
        return None
    bad = [p for p in parts if p not in allow]
    if bad:
        raise ValueError(f"{label} 段出现未知代码 {'/'.join(bad)}（合法值：{'/'.join(allow)}）")
    out = {"main": parts[0], "main_name": allow[parts[0]]}
    if len(parts) > 1:
        out["sub"] = parts[1]
        out["sub_name"] = allow[parts[1]]
    else:
        out["sub"] = None
        out["sub_name"] = None
    return out


def _to_int(val, label):
    """管理者版 EF/FX/AD/DG 都是整数；拿不到就返回 None，不猜。"""
    if val is None or val == "":
        return None
    m = re.search(r"-?\d+", val)
    if not m:
        raise ValueError(f"{label} 段不是数字：{val}")
    return int(m.group(0))


def parse(code: str) -> dict:
    code = (code or "").strip()
    if not code.startswith("DNA:"):
        raise ValueError("结果码必须以 DNA: 开头")

    segs = SEG_SPLIT.split(code)
    bag = {}
    for seg in segs:
        if ":" not in seg:
            continue
        key, _, val = seg.partition(":")
        bag[key.strip()] = val.strip()

    missing = [k for k in ("DNA", "A", "S", "P") if k not in bag]
    if missing:
        raise ValueError(f"结果码缺少必需段：{'/'.join(missing)}（至少要有 DNA / A / S / P）")

    # 三字母代码 - 双字母变体/双字母亚型
    m = re.match(r"([A-Z]{3})-([A-Z]{2})/([A-Z]{2})$", bag["DNA"])
    if not m:
        raise ValueError(f"DNA 代码格式不对: {bag['DNA']}（应该是 XXX-YY/ZZ）")
    main_code, variant, subtype = m.group(1), m.group(2), m.group(3)

    anchors = parse_section(bag["A"], 3)
    styles = parse_section(bag["S"], 2)
    psy = parse_psy(bag["P"])
    if not anchors or not styles:
        raise ValueError("A 段或 S 段没解析出任何得分，检查结果码是否被截断")

    anchors_sorted = sorted(anchors.items(), key=lambda x: -x[1])
    styles_sorted = sorted(styles.items(), key=lambda x: -x[1])

    # 锚点分值上限随题目分布变化（各锚在题库出现次数不同），
    # 所以只给「占全部锚点总分的比例」+ 排名，不给绝对阈值判定。
    anchor_total = sum(anchors.values()) or 1
    style_total = sum(styles.values()) or 1

    # R/K/N —— 用户在测评前画像表单填的，可能为空串
    role = bag.get("R") or None
    skills_raw = bag.get("K") or ""
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    need = bag.get("N") or None

    # ---- 版本与测评类型 ----
    version = bag.get("V") or None
    has_mgr_fields = any(k in bag for k in ("SL", "EF", "FX", "AD", "DG"))
    if version in VERSION_KIND:
        kind = VERSION_KIND[version]
    elif has_mgr_fields:
        kind = "manager"          # 有管理者字段但 V 丢了，按管理者解读
    elif "D" in bag:
        kind = "senior"           # 有 DISC 但无 V：员工版新码，无法区分 JR/SR，取中高阶保守解读
    else:
        kind = "legacy"           # 8080 旧站的 4 段 / 7 段码

    # ---- 性格底色（员工版）----
    disc = parse_pair(bag.get("D"), DISC_NAMES, "D")
    if disc:
        disc["main_desc"] = DISC_DESC.get(disc["main"])
        disc["sub_desc"] = DISC_DESC.get(disc["sub"]) if disc.get("sub") else None
        disc["combo"] = f"{disc['main']}/{disc['sub']}" if disc.get("sub") else disc["main"]

    # ---- 领导风格（管理者版）----
    leadership = None
    if kind == "manager":
        sl = parse_pair(bag.get("SL"), SL_NAMES, "SL")
        if sl:
            sl["main_desc"] = SL_DESC.get(sl["main"])
            sl["sub_desc"] = SL_DESC.get(sl["sub"]) if sl.get("sub") else None
        ef = _to_int(bag.get("EF"), "EF")
        fx = _to_int(bag.get("FX"), "FX")
        ad = _to_int(bag.get("AD"), "AD")
        dg = _to_int(bag.get("DG"), "DG")
        leadership = {
            "style": sl,
            # 站点实际算法：GRADE_W={E:4,G:3,F:1,P:1}，16 题 → 理论区间 16-64
            "effectiveness": {"score": ef, "range": [16, 64]},
            # 站点实际算法：24 - Σ|各风格使用次数-4| → 0-24，越高越均衡
            "flexibility": {"score": fx, "range": [0, 24]},
            "adapt_pct": ad,
            # 4 个诊断情境里判断吻合的个数
            "diagnosis_hit": {"score": dg, "range": [0, 4]},
            # 铁律：这些分数只作定位参照，禁止表述为能力高低/及格线
            "score_is_reference_only": True,
        }
        # 管理者日常消耗更大，倦怠触发阈值下调到 3.0
        burnout_threshold = 3.0
    else:
        burnout_threshold = 3.5

    result = {
        "raw_code": code,
        "assessment_kind": kind,
        "assessment_kind_label": KIND_LABEL[kind],
        "version_tag": version,
        "code_version": "v2_with_rkn" if any(k in bag for k in ("R", "K", "N")) else "v1_core_only",
        "main_code": main_code,
        "variant": variant,
        "subtype": subtype,
        "anchors": [{"code": k, "name": ANCHOR_NAMES.get(k, k), "score": v,
                     "rank": i + 1, "share_pct": round(v / anchor_total * 100, 1)}
                    for i, (k, v) in enumerate(anchors_sorted)],
        "anchors_top3": [k for k, _ in anchors_sorted[:3]],
        "anchor_total": anchor_total,
        "styles": [{"code": k, "name": STYLE_NAMES.get(k, k), "score": v,
                    "rank": i + 1, "share_pct": round(v / style_total * 100, 1)}
                   for i, (k, v) in enumerate(styles_sorted)],
        "styles_top2": [k for k, _ in styles_sorted[:2]],
        "style_total": style_total,
        "psy_state": {k: {"name": PSY_NAMES.get(k), "score": v} for k, v in psy.items()},
        "psy_burnout_alert": psy.get("B", 0) >= burnout_threshold,
        "psy_burnout_threshold": burnout_threshold,
        "disc": disc,
        "leadership": leadership,
        "self_report": {
            "role": role,
            "skills": skills,
            "need": need,
        },
    }

    # 给上层的提示：拿到的码和用户身份可能不匹配时，由 skill 决定怎么说
    notes = []
    if kind == "legacy":
        notes.append("这是旧版结果码（无版本标识），没有性格底色/领导风格部分；"
                     "可正常解读前四段，如需完整画像建议重做最新版测评。")
    if kind in ("junior", "senior") and has_mgr_fields:
        notes.append("码里同时出现员工版与管理者版字段，格式异常，建议用户重新复制。")
    if kind == "manager" and leadership and leadership["style"] is None:
        notes.append("管理者版结果码缺少 SL 段，领导风格模块无法解读，建议重做测评。")
    result["notes"] = notes

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code", help="DNA 结果码")
    args = ap.parse_args()
    try:
        result = parse(args.code)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e),
                          "tips": "员工版：DNA:XXX-YY/ZZ|A:...|S:...|P:...|D:D/I|R:岗位|K:技能|N:诉求|V:JR"
                                  "；管理者版额外含 |SL:S2/S3|EF:52|FX:17|AD:69|DG:3|V:MG"},
                         ensure_ascii=False))
        sys.exit(2)
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pick_assessment.py
根据 recruit-mcp infoDetail 的基础信息，判断该用户应该做哪一版职业DNA测评，并给出唯一正确链接。

为什么要有这个脚本：测评站现在有 3 个版本（初阶员工/中高阶员工/管理者），
链接不能猜、判断规则不能凭印象。把规则写成代码，模型只负责转述结果。

判断规则（依据 infoDetail 真实字段，已 curl 接口核实）：
  1. 管理者 → manager
     判据（任一成立）：managerLevelName 非空 / staffPropertyName 含"管理者"且不含"非"
     注意：staffPropertyName 实际返回的是「非管理者」「管理者」这类值，
     不是接口文档里写的「正式员工/实习生」——文档滞后，以实际返回为准。
  2. 非管理者 + 司龄 enrollAge >= 5 → senior
  3. 非管理者 + 司龄 < 5        → junior
  4. 判据不足（字段缺失）→ unknown，由 skill 引导用户自选，不许瞎猜

enrollAge 是字符串小数年，如 "1.12" 表示 1 年 12 个月？——不是。
实测 inauguralDate=2025-07-04、当前 2026-08，enrollAge="1.12"，
即「1 年又 1.x 个月」的写法不成立，实际是 1.12 年（约 1 年 1.4 个月）。
按十进制年解析即可；无法解析时回退用 inauguralDate 算。

调用：
    python pick_assessment.py --info-json '<infoDetail 的 data 部分 JSON>'
    python pick_assessment.py --manager-level "" --staff-property "非管理者" --enroll-age "6.5"
"""
import argparse, json, re, sys
from datetime import datetime

BASE = "http://21.6.92.38:8082"

# 唯一正确链接表——禁止拼接、禁止改写。改站点时只改这里。
LINKS = {
    "junior":  f"{BASE}/junior.html",
    "senior":  f"{BASE}/senior.html",
    "manager": f"{BASE}/manager.html",
    "entry":   f"{BASE}/",          # 判不出来时给总入口，让用户自己选
}

KIND_LABEL = {
    "junior":  "初阶员工版（工龄 5 年以内）",
    "senior":  "中高阶员工版（工龄 5 年及以上）",
    "manager": "管理者版",
    "unknown": "无法判定",
}

# 结果码里的版本标识，用于回流时校验「做的版本」和「该做的版本」是否一致
EXPECT_VERSION_TAG = {"junior": "JR", "senior": "SR", "manager": "MG"}

SENIOR_YEARS = 5.0


def parse_enroll_age(raw) -> float | None:
    """enrollAge 形如 "1.12" / "6" / "10.5"，按十进制年解析。"""
    if raw is None:
        return None
    m = re.search(r"\d+(?:\.\d+)?", str(raw))
    return float(m.group(0)) if m else None


def years_since(date_str) -> float | None:
    """兜底：用 inauguralDate 算司龄。"""
    if not date_str:
        return None
    s = str(date_str).strip().replace("/", "-")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s, fmt)
            return round((datetime.now() - d).days / 365.25, 2)
        except ValueError:
            continue
    return None


def is_manager(manager_level_name, staff_property_name) -> bool | None:
    """
    返回 True/False，判据完全缺失时返回 None。
    管理职级有值 = 管理者；员工属性明确写「非管理者」= 不是。
    """
    ml = (manager_level_name or "").strip()
    sp = (staff_property_name or "").strip()
    if ml:
        return True
    if sp:
        if "非管理者" in sp:
            return False
        if "管理者" in sp:
            return True
    # 两个字段都空/都不含关键词 → 无法判断
    return None


def decide(manager_level_name=None, staff_property_name=None,
           enroll_age=None, inaugural_date=None) -> dict:
    mgr = is_manager(manager_level_name, staff_property_name)
    yrs = parse_enroll_age(enroll_age)
    if yrs is None:
        yrs = years_since(inaugural_date)

    reasons = []
    if mgr is True:
        kind = "manager"
        reasons.append(f"管理职级={manager_level_name or '(空)'} / 员工属性={staff_property_name or '(空)'} → 承担管理职能")
    elif mgr is False:
        if yrs is None:
            kind = "unknown"
            reasons.append("已确认是非管理者，但司龄字段缺失，无法区分初阶/中高阶")
        elif yrs >= SENIOR_YEARS:
            kind = "senior"
            reasons.append(f"非管理者 + 司龄 {yrs} 年 ≥ {SENIOR_YEARS:g} 年")
        else:
            kind = "junior"
            reasons.append(f"非管理者 + 司龄 {yrs} 年 < {SENIOR_YEARS:g} 年")
    else:
        kind = "unknown"
        reasons.append("管理职级与员工属性都拿不到，无法判断是否带团队")

    out = {
        "kind": kind,
        "kind_label": KIND_LABEL[kind],
        "url": LINKS.get(kind, LINKS["entry"]) if kind != "unknown" else LINKS["entry"],
        "expect_version_tag": EXPECT_VERSION_TAG.get(kind),
        "is_manager": mgr,
        "enroll_years": yrs,
        "reasons": reasons,
        # 判不出来时 skill 必须走引导，不许替用户选
        "need_user_confirm": kind == "unknown",
    }
    if kind == "unknown":
        # 话术口径与 T5 §0.3 一致：先说"读不到"，再问两个问题，最后给对应关系。
        # 不要写成"请提供你的员工属性和司龄"这种表单腔。
        out["fallback_prompt"] = (
            "我这边暂时读不到你的基础信息，你直接告诉我两件事就行："
            "1) 你目前带团队吗？2) 司龄满 5 年了吗？"
            "带团队 → 管理者版；不带团队且满 5 年 → 中高阶员工版；不带团队且不满 5 年 → 初阶员工版。"
        )
    # 边界提醒：司龄贴着 5 年线时，让 skill 主动确认一次
    if kind in ("junior", "senior") and yrs is not None and abs(yrs - SENIOR_YEARS) < 0.5:
        out["borderline_note"] = (
            f"司龄 {yrs} 年正好在 5 年线附近，建议向用户确认一次再给链接。"
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info-json", help="infoDetail 返回的 data 对象（JSON 字符串）")
    ap.add_argument("--manager-level", default=None)
    ap.add_argument("--staff-property", default=None)
    ap.add_argument("--enroll-age", default=None)
    ap.add_argument("--inaugural-date", default=None)
    a = ap.parse_args()

    if a.info_json:
        try:
            info = json.loads(a.info_json)
        except json.JSONDecodeError as e:
            print(json.dumps({"ok": False, "error": f"info-json 不是合法 JSON: {e}"}, ensure_ascii=False))
            sys.exit(2)
        # 容忍传进来的是完整响应（外层可能套 data.data）
        for _ in range(3):
            if isinstance(info, dict) and "data" in info and isinstance(info["data"], dict):
                info = info["data"]
            else:
                break
        res = decide(info.get("managerLevelName"), info.get("staffPropertyName"),
                     info.get("enrollAge"), info.get("inauguralDate"))
    else:
        res = decide(a.manager_level, a.staff_property, a.enroll_age, a.inaugural_date)

    print(json.dumps({"ok": True, "result": res}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

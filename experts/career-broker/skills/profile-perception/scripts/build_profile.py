#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_profile.py (v2)
聚合 raw/ 下数据 → profile.json + profile_summary.md

v2 变化：
- 主数据源：自评 MCP（self_assess_*）
- 三轴：skills / experiences / traits
- 分支：data_path = self_assess | resume_upload | clarify_only
- 历史版本归档：history/profile_v2_<ts>.json
- 上云字段裁剪：cloud_payload.json（按隐私分级）

调用：
    python build_profile.py --staff-id 12345678 [--base-dir ...]

注意：
- traits / skills 的"提炼"需要 LLM 介入。本脚本只做"机械字段拼装"，
  把 self_assess_recent.json 的原文字段直接搬到 experiences.recent_3_periods.objectives.*
  并预留 skills/traits 的 placeholder（标 status:"pending_llm_extract"）。
- 真正的 LLM 提炼由 agent 在对话中触发（参照 skills/profile-perception/references/three-axis-extract-prompt.md），
  把 LLM 输出的 JSON 写回 profile.json 的对应字段。
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = "2.0"


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] 读 {path} 失败: {e}", file=sys.stderr)
        return None


def detect_data_path(self_assess_summary, resume_path: Path) -> str:
    if self_assess_summary and self_assess_summary.get("n_total", 0) > 0:
        return "self_assess"
    if resume_path.exists():
        return "resume_upload"
    return "clarify_only"


def normalize_info_detail_basic(info_detail):
    """把 recruit-mcp infoDetail 返回映射到 profile.basic。只处理当前用户本人信息。"""
    if not info_detail:
        return None
    full_name = info_detail.get("fullName") or ""
    name_en = None
    name_cn = full_name or None
    if "(" in full_name and full_name.endswith(")"):
        name_en = full_name.split("(", 1)[0] or None
        name_cn = full_name.split("(", 1)[1].rstrip(")") or full_name

    return {
        "staff_id": info_detail.get("staffId"),
        "name_cn": name_cn,
        "name_en": name_en,
        "gender": info_detail.get("gender"),
        "dept_path": info_detail.get("departmentFullName") or info_detail.get("departmentName"),
        "dept_id": info_detail.get("departmentId"),
        "department_name": info_detail.get("departmentName"),
        "bg_id": info_detail.get("bgId"),
        "bg_name": info_detail.get("bgShortName"),
        "clan_id": info_detail.get("clanId"),
        "clan_name": info_detail.get("clanName"),
        "genus_id": info_detail.get("genusId"),
        "genus_name": info_detail.get("genusName"),
        "position_id": info_detail.get("positionId"),
        "position": info_detail.get("positionName"),
        "position_name": info_detail.get("positionName"),
        "level": info_detail.get("careerLevelName"),
        "career_level_id": info_detail.get("careerLevelId"),
        "level_sequence": info_detail.get("clanName"),
        "level_channel": info_detail.get("genusName"),
        "staff_property_id": info_detail.get("staffPropertyId"),
        "staff_property_name": info_detail.get("staffPropertyName"),
        "hire_date": info_detail.get("inauguralDate"),
        "tenure_years": info_detail.get("enrollAge"),
        "work_location": info_detail.get("curWorkLocationName"),
        "work_location_id": info_detail.get("curWorkLocation"),
        "avatar_url": info_detail.get("avatarUrl"),
        "_basic_source": "recruit_info_detail",
    }


def build_before_tencent_from_info_detail(info_detail):
    """infoDetail 中的经历多为入司前经历；和自评的司内经历分开存。"""
    if not info_detail:
        return None
    work = info_detail.get("workExperiences") or []
    edu = info_detail.get("eduExperiences") or []
    projects = info_detail.get("projects") or []
    if not (work or edu or projects):
        return None
    return {
        "from_source": "recruit_info_detail",
        "educations": edu,
        "work_experiences": work,
        "project_experiences": projects,
        "note": "infoDetail 中的经历主要用于补充入司前经历；司内经历仍以自评为主干。",
    }


def build_basic(info_detail_basic, self_assess_basic, user_supplied):
    """
    basic 来源优先级：
    1) recruit-mcp infoDetail（当前用户本人可信接口，职位/职级/工作地/员工属性等主来源）
    2) 从自评返回里反推（self_assess_basic 由 fetch_self_assessments.py 写入 raw/basic.json）
    3) 用户在对话中手填（user_supplied 由 agent 把对话中拿到的字段写入 raw/basic_user.json）
    """
    fields = ["staff_id", "name_cn", "name_en", "gender", "dept_path", "dept_id", "department_name",
              "bg_id", "bg_name", "clan_id", "clan_name", "genus_id", "genus_name",
              "position_id", "position", "position_name", "level", "career_level_id",
              "level_sequence", "level_channel", "staff_property_id", "staff_property_name",
              "hire_date", "tenure_years", "work_location", "work_location_id", "avatar_url",
              "manager_rtx", "rtx", "_basic_source"]
    out = {k: None for k in fields}
    for src in (info_detail_basic, self_assess_basic, user_supplied):
        if not src:
            continue
        for k in fields:
            if out.get(k) is None and src.get(k) is not None:
                out[k] = src[k]
    return out


def build_experiences_from_self_assess(raw_dir: Path, summary):
    if not summary:
        return {"recent_3_periods": [], "earlier_summary": None,
                "earlier_periods_meta": [], "before_tencent": None,
                "in_tencent_supplements": {}}

    recent = []
    for f_meta in summary.get("expanded_files", []):
        path = Path(f_meta["path"])
        data = load_json(path)
        if not data:
            continue
        objectives = []
        for dim in data.get("detail", {}).get("dimensions", []):
            for obj in dim.get("objectives", []):
                objectives.append({
                    "type_id": dim.get("typeId"),
                    "type_name": dim.get("typeName"),
                    "index": obj.get("index"),
                    "name": obj.get("oName"),
                    "key_results": obj.get("keyResults"),
                    "outcome": obj.get("outcome"),
                    "high_priority": obj.get("highPriority"),
                    # outcome_metrics / themes 由 LLM 后续填充
                    "outcome_metrics": [],
                    "themes": [],
                })
        recent.append({
            "period_id": data.get("periodId"),
            "period_name": data.get("periodName"),
            "status": data.get("statusKey"),
            "objectives": objectives,
        })

    return {
        "recent_3_periods": recent,
        "earlier_summary": None,           # 由 LLM 填充（agent 拿到本字段为空时触发汇总）
        "earlier_periods_meta": summary.get("earlier_meta", []),
        "before_tencent": None,
        "in_tencent_supplements": {},
    }


def build_skills_placeholder(gongfeng):
    """
    机械抽取的部分先填入：
      - tools：直接搬工蜂 languages_top3
    technical / domain：等 LLM 提炼
    od_self_score 字段已废弃（v2 不再依赖 OD）
    """
    tools = []
    if gongfeng:
        for lang in gongfeng.get("stat", {}).get("languages_top3", []):
            tools.append({"tag": lang, "source": "gongfeng"})
    return {
        "technical": [],     # pending_llm_extract
        "domain": [],        # pending_llm_extract
        "tools": tools,
        "_extract_status": "pending_llm_extract",
    }


def build_traits_placeholder():
    return {
        "business_drive":  None,
        "learning_growth": None,
        "influence":       None,
        "style":           [],
        "summaries":       [],  # 动态软性素质总结：[{title, summary, evidence}]
        "captured_at":     None,
        "captured_by":     None,
        "notes":           [],
        "_extract_status": "pending_llm_extract",
    }


def trait_summary_lines(traits: dict) -> list[str]:
    """渲染“是个怎样的人”：小标题必须是动态总结，不用固定维度名。"""
    if not traits or traits.get("_extract_status") == "pending_llm_extract":
        return ["- 这块还需要后续通过测评或更多经历补充。"]

    lines = []
    for item in traits.get("summaries", []) or []:
        title = item.get("title") or item.get("tag")
        summary = item.get("summary") or item.get("evidence") or ""
        if title:
            lines.append(f"- **{title}**：{summary}".rstrip("："))

    if lines:
        return lines[:3]

    # 兼容旧 schema：优先用 style.tag 作为动态小标题；不要把 business_drive 等固定字段直接展示出来。
    for item in traits.get("style", []) or []:
        title = item.get("tag")
        evidence = item.get("evidence") or ""
        if title:
            lines.append(f"- **{title}**：{evidence}".rstrip("："))

    if lines:
        return lines[:3]

    return ["- 这块还需要后续通过测评或更多经历补充。"]


def render_summary_md(profile):
    b = profile.get("basic", {})
    sk = profile.get("skills", {})
    ex = profile.get("experiences", {})
    tr = profile.get("traits", {})

    L = []
    L.append(f"# {b.get('name_cn') or '-'} · 画像（v2, {datetime.now().strftime('%Y-%m-%d')}）\n")
    L.append("这是我帮你沉淀出的职业画像。\n")

    L.append("## 你是谁")
    identity_parts = [
        b.get('bg_name'),
        b.get('department_name') or b.get('dept_path'),
        b.get('position_name') or b.get('position'),
        b.get('level'),
        f"司龄约 {b.get('tenure_years')} 年" if b.get('tenure_years') else None,
        b.get('work_location'),
    ]
    L.append(" · ".join(str(x) for x in identity_parts if x) or "-")
    L.append("")

    L.append("## 能干什么")
    if sk.get("_extract_status") == "pending_llm_extract":
        L.append("_（待 LLM 三轴提炼，参照 three-axis-extract-prompt.md）_")
    else:
        if sk.get("technical"):
            L.append("**技术能力**：" + " · ".join(t["tag"] for t in sk["technical"][:6]))
        if sk.get("domain"):
            L.append("**领域**：" + " · ".join(t["tag"] for t in sk["domain"][:6]))
    if sk.get("tools"):
        L.append("**工具**：" + " · ".join(t["tag"] for t in sk["tools"][:5]))
    L.append("")

    L.append("## 干过什么")
    if ex.get("recent_3_periods"):
        L.append("几条主线齐推，重点是这些：")
        for idx, p in enumerate(ex["recent_3_periods"], start=1):
            names = " / ".join(o["name"] for o in p["objectives"][:3])
            L.append(f"{idx}. {p['period_name']} — {names}")
    if ex.get("earlier_summary"):
        L.append(f"**更早脉络**：{ex['earlier_summary']}")
    elif ex.get("earlier_periods_meta"):
        more = " / ".join(m["period"] for m in ex["earlier_periods_meta"])
        L.append(f"**更早期**（{len(ex['earlier_periods_meta'])} 期，待 LLM 汇总）：{more}")
    L.append("")

    if ex.get("before_tencent"):
        L.append("**入司前补充**：有可用的工作 / 教育 / 项目经历，可作为背景参考。")
    L.append("")

    L.append("## 是个怎样的人")
    L.extend(trait_summary_lines(tr))
    L.append("")

    L.append("\n---")
    L.append("> 这份画像会作为职业经纪人的后续判断依据。")
    L.append("> 如果你愿意，后面还可以通过测评补充软性素质画像维度。")
    return "\n".join(L)


def cloud_payload(profile):
    """裁剪上云字段：P0 不传、P1 仅传 metric/tag、P2 全传"""
    cloud = json.loads(json.dumps(profile))  # deep copy

    # P0: experiences.recent_3_periods.objectives.outcome / key_results 不上云
    for p in cloud.get("experiences", {}).get("recent_3_periods", []) or []:
        for o in p.get("objectives", []) or []:
            o.pop("outcome", None)
            o.pop("key_results", None)
    # P0: before_tencent.work_experiences[].summary 等原文不上云（保留 company/position/start/end）
    bt = (cloud.get("experiences") or {}).get("before_tencent")
    if bt:
        for w in bt.get("work_experiences", []) or []:
            w.pop("summary", None)
        for p in bt.get("project_experiences", []) or []:
            p.pop("summary", None)

    # P1: skills.*.evidence 仅保留 tag/level/weight
    for cat in ["technical", "domain"]:
        for item in (cloud.get("skills") or {}).get(cat, []) or []:
            item.pop("evidence", None)
    # P1: traits.*.evidence 仅保留 level/scope
    for k in ["business_drive", "learning_growth", "influence"]:
        v = (cloud.get("traits") or {}).get(k)
        if v:
            v.pop("evidence", None)

    cloud["_cloud_safe"] = True
    return cloud


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staff-id", required=True)
    ap.add_argument("--base-dir", default=None,
                    help="默认 ~/.workbuddy/career-broker/<staff_id>/")
    args = ap.parse_args()

    base = Path(args.base_dir) if args.base_dir else (
        Path.home() / ".workbuddy" / "career-broker" / args.staff_id
    )
    raw = base / "raw"
    history = base / "history"
    history.mkdir(parents=True, exist_ok=True)

    info_detail = load_json(raw / "recruit_info_detail.json")  # recruit-mcp infoDetail 当前用户本人信息
    info_detail_basic = normalize_info_detail_basic(info_detail)
    self_assess_basic = load_json(raw / "basic.json")        # 由 fetch_self_assessments.py 写入（自评返回反推）
    user_supplied_basic = load_json(raw / "basic_user.json") # agent 在对话中拿到的 basic 字段
    self_assess_summary = load_json(raw / "self_assess_summary.json")
    tapd = load_json(raw / "tapd.json")
    gongfeng = load_json(raw / "gongfeng.json")
    workbuddy = load_json(raw / "workbuddy.json")
    resume_path = raw / "resume.txt"

    data_path = detect_data_path(self_assess_summary, resume_path)

    n_assess_total = (self_assess_summary or {}).get("n_total", 0)
    n_assess_recent = (self_assess_summary or {}).get("n_expanded", 0)

    basic = build_basic(info_detail_basic, self_assess_basic, user_supplied_basic)

    profile = {
        "schema_version": SCHEMA_VERSION,
        "staff_id": args.staff_id,
        "rtx": basic.get("rtx"),
        "tenure_years": basic.get("tenure_years"),
        "data_path": data_path,
        "n_assess_total": n_assess_total,
        "n_assess_recent": n_assess_recent,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "version": f"v2-{datetime.now().strftime('%Y%m%dT%H%M%S')}",
        "last_updated_by": "auto",
        "partial": (data_path == "clarify_only"),

        "basic": basic,
        "skills": build_skills_placeholder(gongfeng),
        "experiences": build_experiences_from_self_assess(raw, self_assess_summary),
        "traits": build_traits_placeholder(),
        "motivation": None,
        "blockers": None,

        "raw_sources": {
            "self_assess_summary": "raw/self_assess_summary.json" if self_assess_summary else None,
            "recruit_info_detail": "raw/recruit_info_detail.json" if info_detail else None,
            "basic_recruit_info_detail": "raw/recruit_info_detail.json" if info_detail_basic else None,
            "basic_self_assess":   "raw/basic.json" if self_assess_basic else None,
            "basic_user_supplied": "raw/basic_user.json" if user_supplied_basic else None,
            "tapd": "raw/tapd.json" if tapd else None,
            "gongfeng": "raw/gongfeng.json" if gongfeng else None,
            "workbuddy": "raw/workbuddy.json" if workbuddy else None,
            "resume_upload": "raw/resume.txt" if resume_path.exists() else None,
        },
        "cloud_sync": {"synced_at": None, "synced_version": None},
    }

    # infoDetail 中的 work/edu/projects 用来补入司前经历；司内经历仍以自评为主干
    before_tencent = build_before_tencent_from_info_detail(info_detail)
    if before_tencent:
        profile["experiences"]["before_tencent"] = before_tencent

    # 把 in_tencent_supplements 也补上（给 LLM 提炼当 evidence 用）
    if tapd:
        profile["experiences"]["in_tencent_supplements"]["tapd_top"] = tapd.get("items", [])[:10]
    if gongfeng:
        profile["experiences"]["in_tencent_supplements"]["gongfeng_top"] = gongfeng.get("repos", [])[:5]

    # 写 profile.json
    out_json = base / "profile.json"
    out_md = base / "profile_summary.md"
    out_json.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_summary_md(profile), encoding="utf-8")

    # 历史版本归档
    snap = history / f"profile_{profile['version']}.json"
    snap.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")

    # 上云裁剪版本
    cloud = cloud_payload(profile)
    (base / "cloud_payload.json").write_text(
        json.dumps(cloud, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "ok": True,
        "data_path": data_path,
        "n_assess_total": n_assess_total,
        "n_assess_recent": n_assess_recent,
        "profile_json": str(out_json),
        "profile_summary_md": str(out_md),
        "snapshot": str(snap),
        "cloud_payload": str(base / "cloud_payload.json"),
        "next_step": "agent 应根据 schemas 触发 three-axis-extract-prompt 调 LLM 填 skills/experiences.earlier_summary/traits",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

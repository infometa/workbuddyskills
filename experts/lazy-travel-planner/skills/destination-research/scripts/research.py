#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
destination-research/research.py · 目的地调研胶水脚本
1) 调 search-orchestrator
2) 把 candidates 包装成 2-3 个**有差异化主题**的路线选项（这一步更适合让 LLM 做，
   脚本端只输出原始材料 + 模板）
"""
import argparse, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).parent.parent.parent.parent
ORCHESTRATOR = ROOT / "skills" / "search-orchestrator" / "scripts" / "orchestrate.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trip", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    trip = json.loads(pathlib.Path(a.trip).read_text(encoding="utf-8"))
    intent = (trip.get("destination_raw")
              or f"{trip['destination']} {trip.get('duration_days', 3)} 天")

    cache = pathlib.Path(a.output).parent / "00_orchestrator_destination.json"
    r = subprocess.run([
        sys.executable, str(ORCHESTRATOR),
        "--intent", intent,
        "--profile", a.profile,
        "--domain", "destination",
        "--output", str(cache),
    ], capture_output=True, text=True)
    if r.returncode == 2:
        print(r.stdout)
        sys.exit(2)
    if r.returncode != 0:
        print(f"❌ 编排失败: {r.stderr}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(cache.read_text(encoding="utf-8"))
    candidates = data.get("geo_candidates") or []

    # 简单按地理质心 + 名称关键词分主题（v1.0 规则版）
    nature_kw = ("山", "湖", "海", "森林", "公园")
    culture_kw = ("古镇", "博物馆", "故居", "祠", "宫", "寺", "塔")
    niche_kw = ("小众", "秘境", "村")

    nature, culture, niche = [], [], []
    for c in candidates:
        name = c["name"]
        if any(k in name for k in nature_kw): nature.append(c)
        if any(k in name for k in culture_kw): culture.append(c)
        if any(k in name for k in niche_kw): niche.append(c)

    options = []
    if nature:
        options.append({
            "id": "opt-nature",
            "name": "自然风光线",
            "tagline": "看山观湖避人潮",
            "destinations": [c["name"] for c in nature[:5]],
            "evidence_count": {"amap": len(nature)},
            "confidence": "green",
        })
    if culture:
        options.append({
            "id": "opt-culture",
            "name": "文化古韵线",
            "tagline": "古镇老建筑慢节奏",
            "destinations": [c["name"] for c in culture[:5]],
            "evidence_count": {"amap": len(culture)},
            "confidence": "green",
        })
    if niche:
        options.append({
            "id": "opt-niche",
            "name": "小众探秘线",
            "tagline": "避开网红走小路",
            "destinations": [c["name"] for c in niche[:5]],
            "evidence_count": {"amap": len(niche)},
            "confidence": "yellow",
        })
    # 兜底：把所有候选拍成"综合线"
    if not options:
        options.append({
            "id": "opt-default",
            "name": "综合体验线",
            "tagline": "覆盖核心景点",
            "destinations": [c["name"] for c in candidates[:6]],
            "evidence_count": {"amap": len(candidates)},
            "confidence": "green",
        })

    out = {
        "trip_request_id": trip.get("session_id") or "trip-x",
        "options": options[:3],
        "all_candidates": candidates,
        "queried_at": data["metadata"]["queried_at"],
    }
    pathlib.Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "options": len(out["options"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

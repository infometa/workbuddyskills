#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
balance_budget.py · 预算平衡与取舍建议
读 trip + itinerary + transport_plan + hotel_candidates + price_benchmark.json
输出每天细到品类的明细 + 健康度 + 超支取舍方案
"""
import argparse, json, pathlib

ROOT = pathlib.Path(__file__).parent.parent.parent.parent
BENCH_PATH = ROOT / "data" / "price_benchmark.json"


def estimate(trip, itinerary, transport_plan, hotels, bench):
    days = trip["duration_days"]
    party = trip["party_size"]
    tier = (trip.get("budget_tier") or "standard").lower()
    main_city = itinerary.get("main_city") or "成都"
    city_data = bench["cities"].get(main_city, list(bench["cities"].values())[0])

    # 大交通
    transport_long = 0
    for direction in ("outbound", "return"):
        opts = (transport_plan.get(direction) or {}).get("options") or []
        if opts:
            transport_long += opts[0].get("price_ref", 0)
    transport_long *= party

    # 住宿（取首选 hotel × nights）
    nights = max(1, days - 1)
    if isinstance(hotels, list) and hotels:
        per_night = hotels[0].get("price_per_night_ref", 0)
    else:
        # bench 兜底
        rng = city_data["hotel"][tier]
        per_night = (rng[0] + rng[1]) / 2
    accommodation = per_night * nights   # 一间房，多人共住

    # 餐饮 (per person * party * days)
    food_rng = city_data["food"][tier]
    food_per = (food_rng[0] + food_rng[1]) / 2
    food = food_per * days * party

    # 门票（从 itinerary 累加真实票价）
    ticket = 0
    for d in itinerary.get("days") or []:
        for s in d.get("stops") or []:
            ticket += (s.get("poi") or {}).get("ticket_price", 0) or 0
    ticket *= party

    # 市内交通
    intra = city_data.get("transport_intra", {})
    subway = intra.get("subway_avg", 5) * 4 * party * days
    taxi = intra.get("taxi_avg_per_trip", 25) * 1 * party * days
    transport_intra = subway + taxi

    subtotal = transport_long + accommodation + food + ticket + transport_intra
    buffer_amt = round(subtotal * 0.10, 2)
    grand = subtotal + buffer_amt

    breakdown = {
        "transport_long": round(transport_long, 2),
        "accommodation":  round(accommodation, 2),
        "food":           round(food, 2),
        "ticket":         round(ticket, 2),
        "transport_intra": round(transport_intra, 2),
        "buffer":         buffer_amt,
    }

    # ratio check
    target = bench["default_ratio_by_tier"][tier]
    actual_total = subtotal
    ratio = {
        "accommodation": {
            "actual": round(breakdown["accommodation"] / actual_total, 3) if actual_total else 0,
            "target": target["hotel"],
            "verdict": _verdict(breakdown["accommodation"] / actual_total if actual_total else 0, target["hotel"]),
        },
        "food": {
            "actual": round(breakdown["food"] / actual_total, 3) if actual_total else 0,
            "target": target["food"],
            "verdict": _verdict(breakdown["food"] / actual_total if actual_total else 0, target["food"]),
        }
    }

    # vs user budget
    vs_user = None
    user_budget_per_person = trip.get("budget_total_per_person")
    if user_budget_per_person:
        actual_per_person = grand / party
        vs_user = {
            "user_budget_per_person": user_budget_per_person,
            "actual": round(actual_per_person, 2),
            "shortfall": round(actual_per_person - user_budget_per_person, 2),
            "verdict": "over" if actual_per_person > user_budget_per_person * 1.05
                      else ("slightly_over" if actual_per_person > user_budget_per_person else "ok"),
        }

    tradeoffs = _build_tradeoffs(breakdown, vs_user, days)

    return {
        "currency": "CNY",
        "party_size": party,
        "per_person_total": round(grand / party, 2),
        "grand_total": round(grand, 2),
        "breakdown": breakdown,
        "ratio_check": ratio,
        "vs_user_budget": vs_user,
        "tradeoffs": tradeoffs,
    }


def _verdict(actual, target):
    if actual > target * 1.2:
        return "too_high"
    if actual < target * 0.7:
        return "too_low"
    return "ok"


def _build_tradeoffs(breakdown, vs_user, days):
    if not vs_user or vs_user["shortfall"] <= 0:
        return []
    short = vs_user["shortfall"] * 1   # 单人差额
    out = []
    if days >= 4:
        out.append({
            "id": "cut-day",
            "label": f"缩短 1 天（去掉边际效用最低的一天）",
            "savings_per_person": round((breakdown["accommodation"] +
                                          breakdown["food"] / days) /
                                          (breakdown.get("party_size", 2) or 2), 0),
            "impact": "对核心目的地体验影响最小",
        })
    out.append({
        "id": "downgrade-hotel",
        "label": "酒店降一档（如品质 → 标准）",
        "savings_per_person": round(breakdown["accommodation"] * 0.3, 0),
        "impact": "舒适度小幅下降，地段可保持",
    })
    out.append({
        "id": "swap-restaurant",
        "label": "把网红餐厅替换为本地家常",
        "savings_per_person": round(breakdown["food"] * 0.25, 0),
        "impact": "可能错过几个网红，但本地店更地道",
    })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trip", required=True)
    ap.add_argument("--itinerary", required=True)
    ap.add_argument("--transport", required=True)
    ap.add_argument("--hotel", required=True)
    ap.add_argument("--bench", default=str(BENCH_PATH))
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    trip = json.loads(pathlib.Path(a.trip).read_text(encoding="utf-8"))
    itin = json.loads(pathlib.Path(a.itinerary).read_text(encoding="utf-8"))
    trans = json.loads(pathlib.Path(a.transport).read_text(encoding="utf-8"))
    hotel = json.loads(pathlib.Path(a.hotel).read_text(encoding="utf-8"))
    bench = json.loads(pathlib.Path(a.bench).read_text(encoding="utf-8"))

    res = estimate(trip, itin, trans, hotel, bench)
    pathlib.Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.output).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "grand_total": res["grand_total"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

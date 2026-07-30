#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transport-plan/plan_transport.py · 大交通胶水脚本
v1.0 简化版：
  - 推荐高铁/飞机 mode（按距离粗判）
  - 每个 mode 给 2-3 个 stub option 供上层 LLM 调美团/12306 时填充
  - 实际数据获取由 agent 在运行时调对应 MCP 拿到后 merge 进来
"""
import argparse, json, pathlib, math


def haversine_km(a, b):
    R = 6371.0
    lat1, lng1 = math.radians(a[0]), math.radians(a[1])
    lat2, lng2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    return 2 * R * math.asin(math.sqrt(h))


CITY_COORDS = {
    "北京": (39.9042, 116.4074), "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644), "深圳": (22.5431, 114.0579),
    "成都": (30.5728, 104.0668), "杭州": (30.2741, 120.1551),
    "重庆": (29.5630, 106.5516), "西安": (34.3416, 108.9398),
    "厦门": (24.4798, 118.0894), "南京": (32.0603, 118.7969),
    "南昌": (28.6829, 115.8579), "长沙": (28.2282, 112.9388),
    "武汉": (30.5928, 114.3055), "三亚": (18.2528, 109.5119),
    "丽江": (26.8721, 100.2330), "大理": (25.6066, 100.2675),
    "昆明": (24.8801, 102.8329), "拉萨": (29.6500, 91.1402),
    "青岛": (36.0671, 120.3826), "苏州": (31.2989, 120.5853),
}


def recommend_mode(distance_km):
    if distance_km < 800:
        return "high_speed_rail"
    if distance_km < 1500:
        return "either"
    return "flight"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trip", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    trip = json.loads(pathlib.Path(a.trip).read_text(encoding="utf-8"))

    origin = trip.get("origin")
    dest = trip.get("destination")
    if origin in CITY_COORDS and dest in CITY_COORDS:
        d = haversine_km(CITY_COORDS[origin], CITY_COORDS[dest])
    else:
        d = 0
    mode = recommend_mode(d) if d else "high_speed_rail"

    out = {
        "outbound": {
            "mode": mode,
            "distance_km_est": round(d, 0),
            "options": [{
                "rank": 1,
                "depart_station": f"{origin}站",
                "arrive_station": f"{dest}站",
                "depart_time": "TBD",
                "arrive_time": "TBD",
                "duration_min": None,
                "ticket_class": "二等座" if "rail" in mode else "经济舱",
                "price_ref": None,
                "_note": "请由 agent 调美团 / 12306 MCP 填充实际数据",
                "source": "stub",
                "confidence": "gray",
                "book_url": "https://kyfw.12306.cn/" if "rail" in mode else "https://flights.ctrip.com/"
            }],
            "note": "建议提前 7 天订票"
        },
        "return": {
            "mode": mode,
            "options": [{
                "rank": 1,
                "depart_station": f"{dest}站",
                "arrive_station": f"{origin}站",
                "ticket_class": "二等座" if "rail" in mode else "经济舱",
                "price_ref": None,
                "source": "stub",
                "confidence": "gray",
                "book_url": "https://kyfw.12306.cn/"
            }]
        },
        "intra_city": {
            "airport_to_hotel": "建议地铁/出租，约 30-50 元",
            "hotel_to_attraction_default": "市内地铁覆盖广，热门景点打车 25-40 元"
        },
        "queried_at": None,
        "_doc": "v1.0 stub；agent 应在 runtime 调用美团连接器/12306-mcp 获取实际车次/价格后 merge"
    }
    pathlib.Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "mode": mode, "distance_km": round(d, 0)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
高考分数线查询脚本
用法: python fetch_data.py --place 福建 [--year 2024 2023] [--student 历史 物理]
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import date


BASE_URL = "https://gaokao.search.qq.com/skills_data"
TYPE = "score_range"
SOURCE = "open_tB0fU5wP"
DEFAULT_LOOKBACK_YEARS = 6
COMMON_RELEASE_MONTH = 6
COMMON_RELEASE_DAY = 23


def _default_years():
    """Return dynamic lookback years without hard-coding the latest data year."""
    today = date.today()
    current_year = today.year
    latest_candidate = current_year if (today.month, today.day) >= (COMMON_RELEASE_MONTH, COMMON_RELEASE_DAY) else current_year - 1
    return [str(year) for year in range(latest_candidate, latest_candidate - DEFAULT_LOOKBACK_YEARS, -1)]




def _normalize_years(years):
    """Normalize year strings without silently downgrading explicit user years."""
    if not years:
        return _default_years()

    normalized = []
    for year in years:
        try:
            year_int = int(year)
        except (TypeError, ValueError):
            normalized.append(year)
            continue

        normalized.append(str(year_int))

    return list(dict.fromkeys(normalized))



def fetch_data(place: str, year: str, student: str, retry_times: int=1) -> list:
    """从接口获取指定省份的分数线数据，仅读取 lingxi_doc 字段"""
    url = f"{BASE_URL}?type=province_score_line&from={SOURCE}"

    if place:
        url += f"&place={urllib.parse.quote(place)}"
    if year:
        url += f"&year={urllib.parse.quote(year)}"

    if student:
        url += f"&student={urllib.parse.quote(student)}"

    print("access url:", url, file=sys.stderr)

    result = None
    for _ in range(retry_times):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)
                if result.get("status") != 0:
                    # print(json.dumps({"error": f"接口返回异常: {result.get('message', '未知错误')}"}, ensure_ascii=False))
                    continue

                return result.get("data", []).get("地区分数线", [])
        except urllib.error.URLError:
            # print(json.dumps({"error": f"网络请求失败: {str(e)}"}, ensure_ascii=False))
            continue
        except json.JSONDecodeError:
            # print(json.dumps({"error": f"JSON 解析失败: {str(e)}"}, ensure_ascii=False))
            continue

    if result is None:
        print("获取数据失败。", file=sys.stderr)

    return []


def filter_data(records: list, place: str, year: str, student: str, unwanted_keys=None) -> list:
    """过滤掉不需要的字段"""
    if unwanted_keys is None:
        unwanted_keys = []
    filtered = []
    for item in records:
        new_item = {}
        # if student is not None and item["student"] not in student:
            # continue
        for kk, vv in item.items():
            if kk in unwanted_keys:
                continue
            new_item[kk] = vv
        filtered.append(new_item)

    # print(f"根据年份过滤 lingxi_doc 数据，剩余 {len(filtered)} / {len(records)} 条数据。")

    return filtered


DISPLAY_FIELD_ORDER = [
    "分数查询年份",
    "分数线所属地区",
    "考生类别",
    "录取批次",
    "分数",
    "位次",
]


def _year_sort_value(record):
    try:
        return -int(record.get("分数查询年份", 0))
    except (TypeError, ValueError):
        return 0


def normalize_records(records: list) -> list:
    """Deduplicate and sort records so repeated calls expose the same source facts."""
    unique = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        key = json.dumps(record, ensure_ascii=False, sort_keys=True)
        unique[key] = record

    ordered = []
    for record in unique.values():
        normalized = {key: record[key] for key in DISPLAY_FIELD_ORDER if key in record}
        for key in sorted(record.keys()):
            if key not in normalized:
                normalized[key] = record[key]
        ordered.append(normalized)

    return sorted(
        ordered,
        key=lambda item: (
            _year_sort_value(item),
            item.get("分数线所属地区", ""),
            item.get("考生类别", ""),
            item.get("录取批次", ""),
            item.get("分数", ""),
            item.get("位次", ""),
        ),
    )

province_list = [
    "北京",
    "天津",
    "河北",
    "山西",
    "内蒙古",
    "辽宁",
    "吉林",
    "黑龙江",
    "上海",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "广西",
    "海南",
    "重庆",
    "四川",
    "贵州",
    "云南",
    "西藏",
    "陕西",
    "甘肃",
    "青海",
    "宁夏",
    "新疆"
]

luqupici_summary_pro = {
  "普通类": {
    "本科": [
      "本科批",
      "普通类一段",
      "普通类二段",
      "本科一批（A类考生）",
      "本科一批（B类考生）",
      "本科二批（A类考生）",
      "本科二批（B类考生）",
      "部队生源招生本科控制线",
      "本科一批",
      "本科二批",
      "本科一批-单列类",
      "本科二批-单列类",
      "本科提前批",
      "本科提前批-单列类",
      "本科提前批-戏剧影视导演方向",
      "本科提前批-戏剧影视表演方向",
      "本科提前批-服装表演方向",
      "本科提前批-戏剧影视导演方向（单列类）",
      "本科提前批-戏剧影视表演方向（单列类）",
      "本科提前批-服装表演方向（单列类）",
      "本科一批-新疆高中班",
      "本科二批-新疆高中班",
      "本科一批-新疆高中班，单列类",
      "本科二批-新疆高中班，单列类",
      "本科二批C段",
      "本科二批C段-音乐表演（声乐）",
      "本科二批C段-音乐表演（器乐）",
      "本科二批C段-音乐教育（声乐主项）",
      "本科二批C段-音乐教育（器乐主项）",
      "平行录取一段",
      "平行录取二段",
      "本科二段",
      "本科一段",
      "本科一批-单列类（选考外语）",
      "本科二批-单列类（选考外语）",
      "本科提前批-单列类（选考外语）",
      "本科二批C段-航空服务艺术与管理",
      "本科二批C段-广播电视编导及戏剧影视文学",
      "本科二批C段-播音与主持",
      "本科二批C段-书法学",
      "本科二批C段-表演",
      "本科二批C段-舞蹈",
      "本科二批C段-音乐",
      "本科二批C段-美术",
      "三校生本科",
      "本科二批（B类考生）-汉族及区外少数民族考生",
      "本科二批（A类考生）-区内世居两代（含两代）以上少数民族考生",
      "本科一批（B类考生）-汉族及区外少数民族考生",
      "本科一批（A类考生）-区内世居两代（含两代）以上少数民族考生",
      "本科二批-体操武术类",
      "本科二批-足球排球篮球类",
      "本科二批-田径类",
      "本科一批-体操武术类",
      "本科一批-足球排球篮球类",
      "本科一批-田径类",
      "本科二批-航空服务艺术与管理",
      "本科二批-舞蹈",
      "本科二批-播音与主持艺术",
      "本科二批-广播电视编导",
      "本科二批-器乐",
      "本科二批-声乐",
      "本科二批-书法",
      "本科二批-美术",
      "本科一批-航空服务艺术与管理",
      "本科一批-舞蹈",
      "本科一批-播音与主持艺术",
      "本科一批-广播电视编导",
      "本科一批-作曲",
      "本科一批-器乐",
      "本科一批-声乐",
      "本科一批-唐卡",
      "本科一批-书法",
      "本科一批-美术",
      "重点本科（汉族）",
      "普通本科（汉族）",
      "重点本科（少数民族）",
      "普通本科（少数民族）",
      "本科提前批-舞蹈学类、舞蹈专业189",
      "本科批（少数民族）",
      "本科批（汉族）"
    ],
    "专科": [
      "专科批-语数外三科总分",
      "专科批",
      "专科批（独立学院、民办、省属高职除武汉）"
    ],
    "不限": [
      "高本贯通批"
    ]
  }
}


def _build_value_to_keys(summary: dict) -> dict:
    """
    将 luqupici_summary_pro.json 的三层结构展开：
    具体值 -> (大类, 层次)

    例如："本科批" -> ("普通类", "本科")
    """
    mapping = {}
    for cat, levels in summary.items():
        for lv, items in levels.items():
            for item in items:
                mapping[item] = (cat, lv)
    return mapping


def filter_by_luqupici(
    records: list,
    model_luqupici: list,
    luqupici_field: str = "luqupici",
) -> list:
    """
    根据模型检索到的 luqupici 类别，过滤召回数据中不属于该类别的条目。

    参数：
        records         : 召回数据列表，每条是 dict，含 luqupici_field 字段
        model_luqupici  : 模型返回的 luqupici 列表，格式固定为 "大类_层次"
                          如 ["普通类_本科", "艺术类_专科"]
                          层次固定为：本科 / 专科 / 不限
        luqupici_field  : 召回数据中记录批次的字段名，默认 "luqupici"

    返回：
        过滤后的 records 列表
    """
    if not model_luqupici:
        return records

    # 加载召回数据完整值表，展开为：具体值 -> (大类, 层次)
    summary_pro: dict = luqupici_summary_pro
    value_to_keys = _build_value_to_keys(summary_pro)
    # import pdb;pdb.set_trace()
    # 模型返回格式固定为 "大类_层次"，用 rsplit("_", 1) 直接解析
    # 兼容大类名含"/"的情况，如 "预科/民族_本科"
    allowed_keys: set = {
        tuple(item.rsplit("_", 1))
        for item in model_luqupici
        if "_" in item
    }

    # 过滤召回数据
    filtered = []
    for record in records:
        raw_value = record.get(luqupici_field)
        if raw_value is None:
            # 没有该字段，保留
            filtered.append(record)
            continue

        keys = value_to_keys.get(raw_value)
        if keys is None:
            # 该值不在映射表中，无法判断，保留
            filtered.append(record)
            continue

        if keys in allowed_keys:
            filtered.append(record)

    return filtered



def main():
    parser = argparse.ArgumentParser(description="高考地区分数线查询")
    parser.add_argument("--place", default=None, nargs="*", help="省份名称，如：福建、广东")
    parser.add_argument("--year", default=None, nargs="*", help="年份列表，如：2024 2023")
    parser.add_argument("--student", default=None, nargs="*", help="选科列表，如：历史 物理 文科 理科")
    parser.add_argument("--ip", default=None, help="IP地址")
    parser.add_argument("--luqupici", default=None, nargs="*", help="录取批次")

    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"忽略未知参数: {unknown}", file=sys.stderr)

    if args.ip and args.place is None:
        args.place = args.ip

    year_was_provided = args.year is not None and len(args.year) > 0
    args.year = _normalize_years(args.year)

    if not isinstance(args.place, list):
        args.place = [args.place]

    if not isinstance(args.year, list):
        args.year = [args.year]

    if not isinstance(args.student, list):
        args.student = [args.student]

    records = []
    for place_ in args.place:
        if place_ == "全省":
            place_ = None
        for year_ in args.year:
            for student_ in args.student:
                records.extend(fetch_data(place_, year_, student_))

    unwanted_keys = [


        # "item_key", "currentyear", "url", "gaokao", "fenshuxian", "title", "type"
    ]

    filtered = filter_data(records, args.place, args.year, args.student, unwanted_keys)

    if args.luqupici:
        n_records = len(filtered)
        filtered = filter_by_luqupici(filtered, args.luqupici, luqupici_field="录取批次")
        print(f"luqupici 过滤: {len(filtered)}/{n_records}", file=sys.stderr)

    filtered = normalize_records(filtered)
    rnt_data = json.dumps(filtered, ensure_ascii=False, indent=2)

    # 输出结果
    print(rnt_data)


if __name__ == "__main__":
    main()

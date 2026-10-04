"""行业分析计算脚本（沙箱执行）.

负责确定性计算：CAGR 复合增长率、CR5 集中度、市占率分位。
LLM 不得自行计算这些数字，必须调用本脚本。

用法：
    echo '{"market_sizes": [...], "competitor_shares": [...]}' | python3 calculate.py

输入 JSON（stdin）：
    {
      "market_sizes": [
        {"year": "2024", "size": 780},
        {"year": "2023", "size": 610},
        {"year": "2022", "size": 450}
      ],
      "competitor_shares": [
        {"name": "隆基", "share": 23},
        {"name": "晶科", "share": 18},
        {"name": "通威", "share": 15},
        {"name": "TCL中环", "share": 12},
        {"name": "标的", "share": 8.5}
      ]
    }

输出 JSON（stdout）：
    {
      "cagr": {"value": 34.6, "years": 2, "valid": true},
      "cr5": {"value": 76.5, "count": 5, "valid": true},
      "share_percentile": {"rank": 5, "total": 5, "percentile": "Top 100%", "valid": true}
    }
"""

import json
import sys


def calc_cagr(market_sizes: list) -> dict:
    """计算 3 年 CAGR（复合年增长率）.

    CAGR = (末年值 / 首年值)^(1/年数) - 1
    需要至少 2 个年度数据点。
    """
    if not market_sizes or len(market_sizes) < 2:
        return {"value": None, "years": 0, "valid": False, "reason": "数据不足，需至少 2 年"}

    # 按年份排序
    sorted_data = sorted(market_sizes, key=lambda x: x.get("year", 0))
    first = sorted_data[0]
    last = sorted_data[-1]

    first_val = first.get("size")
    last_val = last.get("size")

    if not first_val or not last_val or first_val <= 0:
        return {"value": None, "years": 0, "valid": False, "reason": "数值无效"}

    years = len(sorted_data) - 1
    if years <= 0:
        return {"value": None, "years": 0, "valid": False, "reason": "年数为 0"}

    cagr = (last_val / first_val) ** (1.0 / years) - 1
    return {
        "value": round(cagr * 100, 1),
        "years": years,
        "first_year": first.get("year"),
        "last_year": last.get("year"),
        "valid": True,
    }


def calc_cr5(competitor_shares: list) -> dict:
    """计算 CR5（前 5 名集中度）."""
    if not competitor_shares:
        return {"value": None, "count": 0, "valid": False, "reason": "无竞争者数据"}

    # 按市占率降序
    sorted_comps = sorted(competitor_shares, key=lambda x: x.get("share", 0), reverse=True)
    top5 = sorted_comps[:5]
    cr5 = sum(c.get("share", 0) for c in top5)

    return {
        "value": round(cr5, 1),
        "count": len(top5),
        "top5": [{"name": c.get("name", ""), "share": c.get("share", 0)} for c in top5],
        "valid": True,
    }


def calc_share_percentile(competitor_shares: list, target_name: str = "标的") -> dict:
    """计算本企业市占率分位."""
    if not competitor_shares:
        return {"rank": None, "total": 0, "percentile": None, "valid": False, "reason": "无竞争者数据"}

    sorted_comps = sorted(competitor_shares, key=lambda x: x.get("share", 0), reverse=True)
    total = len(sorted_comps)

    # 找标的企业
    target = None
    for i, c in enumerate(sorted_comps):
        name = c.get("name", "")
        if "标的" in name or target_name in name or c.get("isTarget"):
            target = {"index": i, "share": c.get("share", 0), "name": name}
            break

    if not target:
        return {"rank": None, "total": total, "percentile": None, "valid": False, "reason": "未找到标的企业"}

    rank = target["index"] + 1
    percentile_pct = (rank / total) * 100

    if percentile_pct <= 5:
        percentile = "Top 5%"
    elif percentile_pct <= 10:
        percentile = "Top 10%"
    elif percentile_pct <= 25:
        percentile = "Top 25%"
    elif percentile_pct <= 50:
        percentile = "Top 50%"
    else:
        percentile = "Bottom 50%"

    return {
        "rank": rank,
        "total": total,
        "share": target["share"],
        "percentile": percentile,
        "valid": True,
    }


def main() -> None:
    """主入口：读 stdin JSON → 计算 → 写 stdout JSON."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        print(json.dumps({"error": f"输入 JSON 解析失败: {e}"}))
        sys.exit(1)

    market_sizes = data.get("market_sizes", [])
    competitor_shares = data.get("competitor_shares", [])

    result = {
        "cagr": calc_cagr(market_sizes),
        "cr5": calc_cr5(competitor_shares),
        "share_percentile": calc_share_percentile(competitor_shares),
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

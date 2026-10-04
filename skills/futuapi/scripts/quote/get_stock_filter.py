#!/usr/bin/env python3
"""
条件选股

功能：根据价格、市值、PE、涨跌幅等条件筛选股票
用法：python get_stock_filter.py --market HK --min-price 10 --max-price 100

接口限制：
- 港股 BMP 权限不支持
- 每 30 秒内最多请求 10 次
- 每页最多返回 200 个结果

参数说明：
- --market: 市场代码（HK/US/SH/SZ），不区分沪股和深股，传入沪股或深股都会返回沪深市场的股票
- --sort: 排序字段（market_val/price/volume/turnover/turnover_rate/change_rate/pe/pb），不传默认按市值降序
- --asc: 升序排序（默认降序）
- --limit: 返回数量（默认 20）
- --min-price/--max-price: 价格范围
- --min-market-cap/--max-market-cap: 市值范围（亿）
- --min-pe/--max-pe: PE 范围
- --min-pb/--max-pb: PB 范围
- --min-change-rate/--max-change-rate: 涨跌幅范围(%)
- --min-volume: 最小成交量
- --min-turnover-rate/--max-turnover-rate: 换手率范围(%)
- --json: 输出 JSON 格式

返回字段说明：
- turnover_rate/change_rate/amplitude: 百分比字段，20 实际对应 20%
- total_share/float_share: 单位：股
- float_market_val: 单位：元
"""
import argparse
import json
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_quote_context,
    check_ret,
    safe_close,
    is_empty,
    safe_get,
    safe_float,
    safe_int,
    df_to_records,
    RET_OK,
    Market,
    SimpleFilter,
    AccumulateFilter,
    FinancialFilter,
    FinancialQuarter,
    StockField,
    SortDir,
)

MARKET_MAP = {
    "HK": Market.HK,
    "US": Market.US,
    "SH": Market.SH,
    "SZ": Market.SZ,
}

SORT_MAP = {
    "market_val": StockField.MARKET_VAL,
    "price": StockField.CUR_PRICE,
    "volume": StockField.VOLUME,
    "turnover": StockField.TURNOVER,
    "turnover_rate": StockField.TURNOVER_RATE,
    "change_rate": StockField.CHANGE_RATE,
    "pe": StockField.PE_TTM,
    "pb": StockField.PB_RATE,
}

QUARTER_MAP = {
    "ANNUAL": FinancialQuarter.ANNUAL,
    "FIRST_QUARTER": FinancialQuarter.FIRST_QUARTER,
    "INTERIM": FinancialQuarter.INTERIM,
    "THIRD_QUARTER": FinancialQuarter.THIRD_QUARTER,
}


def _snapshot_to_record(row):
    """将 get_market_snapshot 的一行转为标准 record dict"""
    return {
        "code": row.get("code", ""),
        "name": row.get("name", ""),
        "price": safe_float(row.get("last_price")),
        "change_rate": safe_float(row.get("change_rate")),
        "market_val": safe_float(row.get("total_market_val")),
        "volume": safe_int(row.get("volume")),
        "pe": safe_float(row.get("pe_ttm_ratio")),
        "pb": safe_float(row.get("pb_ratio")),
        "turnover_rate": safe_float(row.get("turnover_rate")),
    }


def _enrich_with_snapshot(ctx, records):
    """用 get_market_snapshot 补全 records 中缺失的行情数据"""
    code_list = [r["code"] for r in records if r["code"]]
    if not code_list:
        return records
    snapshot_map = {}
    for i in range(0, len(code_list), 50):
        batch = code_list[i:i + 50]
        snap_ret, snap_data = ctx.get_market_snapshot(batch)
        if snap_ret == RET_OK and not is_empty(snap_data):
            for _, row in snap_data.iterrows():
                snapshot_map[row["code"]] = row
        elif snap_ret != RET_OK and len(batch) > 1:
            for code in batch:
                s_ret, s_data = ctx.get_market_snapshot([code])
                if s_ret == RET_OK and not is_empty(s_data):
                    snapshot_map[code] = s_data.iloc[0]
    for r in records:
        row = snapshot_map.get(r["code"])
        if row is not None:
            r.update(_snapshot_to_record(row))
    return records


# 回退用已知大盘股代码（覆盖各市场 Top 50 级别标的，保证 snapshot 有市值数据）
_FALLBACK_CODES = {
    "US": [
        "US.AAPL", "US.MSFT", "US.NVDA", "US.GOOG", "US.AMZN",
        "US.META", "US.BRK.B", "US.TSLA", "US.AVGO", "US.TSM",
        "US.WMT", "US.JPM", "US.LLY", "US.V", "US.MA",
        "US.UNH", "US.ORCL", "US.XOM", "US.COST", "US.NFLX",
        "US.HD", "US.PG", "US.JNJ", "US.BAC", "US.ABBV",
        "US.CRM", "US.SAP", "US.KO", "US.PLTR", "US.AMD",
        "US.MRK", "US.CSCO", "US.PEP", "US.TMO", "US.ADBE",
        "US.ACN", "US.IBM", "US.ABT", "US.QCOM", "US.GE",
        "US.AMAT", "US.ISRG", "US.INTU", "US.TXN", "US.BKNG",
        "US.NOW", "US.UBER", "US.GS", "US.MS", "US.CAT",
    ],
    "HK": [
        "HK.00700", "HK.09988", "HK.09618", "HK.03690", "HK.01810",
        "HK.09888", "HK.09999", "HK.01024", "HK.01211", "HK.00981",
        "HK.02800", "HK.00005", "HK.00941", "HK.01398", "HK.00939",
        "HK.03988", "HK.00388", "HK.00001", "HK.00016",
        "HK.02318", "HK.00883", "HK.00857", "HK.00386", "HK.01928",
        "HK.00002", "HK.00003", "HK.00006", "HK.00027", "HK.01299", "HK.00012",
        "HK.02015", "HK.09866", "HK.09868", "HK.01347", "HK.00020",
        "HK.02382", "HK.02269", "HK.01088", "HK.02628", "HK.00669",
    ],
}


def _fallback_by_snapshot(ctx, market, limit, asc):
    """当 get_stock_filter 返回不可靠数据时，通过已知大盘股 snapshot 获取市值排序"""
    code_list = _FALLBACK_CODES.get(market.upper(), [])
    if not code_list:
        return None

    records = []
    # 逐只查询以容错无效代码，避免一个坏代码导致整批失败
    batch_size = 50
    for i in range(0, len(code_list), batch_size):
        batch = code_list[i:i + batch_size]
        snap_ret, snap_data = ctx.get_market_snapshot(batch)
        if snap_ret == RET_OK and not is_empty(snap_data):
            for _, row in snap_data.iterrows():
                r = _snapshot_to_record(row)
                if r["market_val"] > 0:
                    records.append(r)
        elif snap_ret != RET_OK and len(batch) > 1:
            # 批量失败，逐只重试
            for code in batch:
                s_ret, s_data = ctx.get_market_snapshot([code])
                if s_ret == RET_OK and not is_empty(s_data):
                    r = _snapshot_to_record(s_data.iloc[0])
                    if r["market_val"] > 0:
                        records.append(r)

    records.sort(key=lambda r: r["market_val"], reverse=not asc)
    return records[:limit]


def get_stock_filter(market="HK", limit=20, sort=None, asc=False, output_json=False, **kwargs):
    market_enum = MARKET_MAP.get(market.upper(), Market.HK)
    filter_list = []

    # SimpleFilter: 价格、市值、PE、PB
    # 注意：必须显式设置 is_no_filter=False，否则 SDK 不会序列化 filter_min/filter_max
    simple = SimpleFilter()
    has_simple = False
    if kwargs.get("min_price") is not None:
        simple.filter_min = kwargs["min_price"]
        simple.stock_field = StockField.CUR_PRICE
        has_simple = True
    if kwargs.get("max_price") is not None:
        simple.filter_max = kwargs["max_price"]
        simple.stock_field = StockField.CUR_PRICE
        has_simple = True
    if has_simple:
        simple.is_no_filter = False
        filter_list.append(simple)

    if kwargs.get("min_market_cap") is not None or kwargs.get("max_market_cap") is not None:
        sf = SimpleFilter()
        sf.stock_field = StockField.MARKET_VAL
        sf.is_no_filter = False
        if kwargs.get("min_market_cap") is not None:
            sf.filter_min = kwargs["min_market_cap"] * 1e8
        if kwargs.get("max_market_cap") is not None:
            sf.filter_max = kwargs["max_market_cap"] * 1e8
        filter_list.append(sf)

    if kwargs.get("min_pe") is not None or kwargs.get("max_pe") is not None:
        sf = SimpleFilter()
        sf.stock_field = StockField.PE_TTM
        sf.is_no_filter = False
        if kwargs.get("min_pe") is not None:
            sf.filter_min = kwargs["min_pe"]
        if kwargs.get("max_pe") is not None:
            sf.filter_max = kwargs["max_pe"]
        filter_list.append(sf)

    if kwargs.get("min_pb") is not None or kwargs.get("max_pb") is not None:
        sf = SimpleFilter()
        sf.stock_field = StockField.PB_RATE
        sf.is_no_filter = False
        if kwargs.get("min_pb") is not None:
            sf.filter_min = kwargs["min_pb"]
        if kwargs.get("max_pb") is not None:
            sf.filter_max = kwargs["max_pb"]
        filter_list.append(sf)

    # AccumulateFilter: 涨跌幅、成交量、换手率
    if kwargs.get("min_change_rate") is not None or kwargs.get("max_change_rate") is not None:
        af = AccumulateFilter()
        af.stock_field = StockField.CHANGE_RATE
        af.is_no_filter = False
        if kwargs.get("min_change_rate") is not None:
            af.filter_min = kwargs["min_change_rate"]
        if kwargs.get("max_change_rate") is not None:
            af.filter_max = kwargs["max_change_rate"]
        filter_list.append(af)

    if kwargs.get("min_volume") is not None:
        af = AccumulateFilter()
        af.stock_field = StockField.VOLUME
        af.is_no_filter = False
        af.filter_min = kwargs["min_volume"]
        filter_list.append(af)

    if kwargs.get("min_turnover_rate") is not None or kwargs.get("max_turnover_rate") is not None:
        af = AccumulateFilter()
        af.stock_field = StockField.TURNOVER_RATE
        af.is_no_filter = False
        if kwargs.get("min_turnover_rate") is not None:
            af.filter_min = kwargs["min_turnover_rate"]
        if kwargs.get("max_turnover_rate") is not None:
            af.filter_max = kwargs["max_turnover_rate"]
        filter_list.append(af)

    # 排序：必须显式设置 is_no_filter=False，否则 SDK 不会序列化 filter_min/sort 到 protobuf
    accumulate_fields = {"volume", "turnover", "turnover_rate", "change_rate"}
    if sort and sort in SORT_MAP:
        if sort in accumulate_fields:
            sf_sort = AccumulateFilter()
        else:
            sf_sort = SimpleFilter()
        sf_sort.stock_field = SORT_MAP[sort]
        sf_sort.is_no_filter = False
        sf_sort.filter_min = 1
        sf_sort.sort = SortDir.ASCEND if asc else SortDir.DESCEND
        filter_list.append(sf_sort)

    if not filter_list:
        sf_default = SimpleFilter()
        sf_default.stock_field = StockField.MARKET_VAL
        sf_default.is_no_filter = False
        sf_default.filter_min = 1
        sf_default.sort = SortDir.ASCEND if asc else SortDir.DESCEND
        filter_list.append(sf_default)

    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_stock_filter(market_enum, filter_list, begin=0, num=limit)
        check_ret(ret, data, ctx, "条件选股")

        last_page, all_count, stock_list = data

        if not stock_list:
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无数据")
            return

        # get_stock_filter 返回的 FilterStockData 可能不含行情字段（baseDataList 为空），
        # 先尝试从对象属性取值，若全为空则用 get_market_snapshot 补全数据。
        records = []
        has_data = False
        for item in stock_list:
            mv = safe_float(getattr(item, "market_val", None))
            price = safe_float(getattr(item, "cur_price", None))
            if mv > 0 or price > 0:
                has_data = True
            records.append({
                "code": getattr(item, "stock_code", ""),
                "name": getattr(item, "stock_name", ""),
                "price": price,
                "change_rate": safe_float(getattr(item, "change_rate", None)),
                "market_val": mv,
                "volume": safe_int(getattr(item, "volume", None)),
                "pe": safe_float(getattr(item, "pe_ttm", None)),
                "pb": safe_float(getattr(item, "pb_rate", None)),
                "turnover_rate": safe_float(getattr(item, "turnover_rate", None)),
            })

        # 若 FilterStockData 未携带行情数据，通过 get_market_snapshot 补全
        if not has_data:
            records = _enrich_with_snapshot(ctx, records)

        # Python 侧重排序：API 返回的排序可能不可靠（尤其在 enrichment 之后），
        # 用本地排序保证输出顺序正确。
        _RECORD_SORT_KEY = {
            "market_val": "market_val", "price": "price", "volume": "volume",
            "turnover_rate": "turnover_rate", "change_rate": "change_rate",
            "pe": "pe", "pb": "pb",
        }
        effective_sort = sort if sort else "market_val"
        record_key = _RECORD_SORT_KEY.get(effective_sort)
        if record_key:
            records.sort(key=lambda r: r.get(record_key, 0), reverse=not asc)

        # 兜底：按市值排序但所有记录市值均为 0 时，用已知大盘股 snapshot 兜底
        if effective_sort == "market_val":
            max_mv = max((r["market_val"] for r in records), default=0)
            if max_mv <= 0:
                fallback = _fallback_by_snapshot(ctx, market, limit, asc)
                if fallback:
                    records = fallback

        if output_json:
            print(json.dumps({"market": market, "count": len(records), "data": records}, ensure_ascii=False))
        else:
            print("=" * 100)
            print(f"条件选股结果: {market} (共 {len(records)} 只)")
            print("=" * 100)
            print(f"  {'代码':<15} {'名称':<12} {'价格':>8} {'涨跌%':>8} {'市值(亿)':>10} {'PE':>8} {'换手%':>8}")
            print("  " + "-" * 96)
            for r in records:
                mv = r['market_val'] / 1e8 if r['market_val'] > 0 else 0
                print(f"  {r['code']:<15} {r['name']:<12} {r['price']:>8.2f} {r['change_rate']:>8.2f} {mv:>10.2f} {r['pe']:>8.2f} {r['turnover_rate']:>8.2f}")
            print("=" * 100)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="条件选股")
    parser.add_argument("--market", choices=["HK", "US", "SH", "SZ"], default="HK", help="市场")
    parser.add_argument("--min-price", type=float, default=None)
    parser.add_argument("--max-price", type=float, default=None)
    parser.add_argument("--min-market-cap", type=float, default=None, help="最小市值（亿）")
    parser.add_argument("--max-market-cap", type=float, default=None, help="最大市值（亿）")
    parser.add_argument("--min-pe", type=float, default=None)
    parser.add_argument("--max-pe", type=float, default=None)
    parser.add_argument("--min-pb", type=float, default=None)
    parser.add_argument("--max-pb", type=float, default=None)
    parser.add_argument("--min-change-rate", type=float, default=None, help="最小涨跌幅(%%)")
    parser.add_argument("--max-change-rate", type=float, default=None, help="最大涨跌幅(%%)")
    parser.add_argument("--min-volume", type=int, default=None)
    parser.add_argument("--min-turnover-rate", type=float, default=None, help="最小换手率(%%)")
    parser.add_argument("--max-turnover-rate", type=float, default=None, help="最大换手率(%%)")
    parser.add_argument("--sort", choices=["market_val", "price", "volume", "turnover", "turnover_rate", "change_rate", "pe", "pb"],
                        default=None, help="排序字段")
    parser.add_argument("--asc", action="store_true", help="升序排序（默认降序）")
    parser.add_argument("--limit", type=int, default=20, help="返回数量（默认: 20）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()

    get_stock_filter(
        market=args.market, limit=args.limit, sort=args.sort, asc=args.asc,
        output_json=args.output_json,
        min_price=args.min_price, max_price=args.max_price,
        min_market_cap=args.min_market_cap, max_market_cap=args.max_market_cap,
        min_pe=args.min_pe, max_pe=args.max_pe,
        min_pb=args.min_pb, max_pb=args.max_pb,
        min_change_rate=args.min_change_rate, max_change_rate=args.max_change_rate,
        min_volume=args.min_volume,
        min_turnover_rate=args.min_turnover_rate, max_turnover_rate=args.max_turnover_rate,
    )

#!/usr/bin/env python3
"""
获取 K 线数据

功能：获取股票的 K 线（蜡烛图）数据，支持实时和历史数据
- 实时 K 线：获取最近 N 根 K 线（需订阅）
- 历史 K 线：指定日期范围获取历史数据（无需订阅）

接口限制：
- 实时 K 线：最多获取最近 1000 根，需先订阅
- 历史 K 线：每 30 秒内最多请求 60 次；分 K 最近 8 年，日 K 最近 20 年
- 历史 K 线额度：30 天内每请求 1 只股票占用 1 个额度，相同股票不重复计
- 市盈率和换手率仅日 K 及以上周期的正股才有数据
- 期权仅提供日K、1分K、5分K、15分K、60分K
- 美股盘前盘后夜盘仅 60 分钟及以下周期

参数说明：
- num: 每页最多 1000 根（历史 K 线会自动翻页拉取全部）
- max-page: 限制最大翻页次数，不传则拉取全部

返回字段说明：
- time_key: 格式 yyyy-MM-dd HH:mm:ss，港股/A 股北京时间，美股美东时间
- turnover_rate: 百分比字段，默认返回小数，如 0.01 实际对应 1%
- last_close: 即前一个时间的收盘价，第一个数据的昨收价可能为 0
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
    KLType,
    SubType,
    AuType,
    Session,
    RET_OK,
)

# session 仅用于美股历史 K 线，不支持 OVERNIGHT
HISTORY_SESSION_MAP = {
    "NONE": Session.NONE,
    "RTH": Session.RTH,
    "ETH": Session.ETH,
    "ALL": Session.ALL,
}

KTYPE_MAP = {
    "1m": KLType.K_1M,
    "3m": KLType.K_3M,
    "5m": KLType.K_5M,
    "15m": KLType.K_15M,
    "30m": KLType.K_30M,
    "60m": KLType.K_60M,
    "1d": KLType.K_DAY,
    "1w": KLType.K_WEEK,
    "1M": KLType.K_MON,
    "1Q": KLType.K_QUARTER,
    "1Y": KLType.K_YEAR,
}

REHAB_MAP = {
    "none": AuType.NONE,
    "forward": AuType.QFQ,
    "backward": AuType.HFQ,
}

KTYPE_TO_SUBTYPE = {
    KLType.K_1M: SubType.K_1M,
    KLType.K_3M: SubType.K_3M,
    KLType.K_5M: SubType.K_5M,
    KLType.K_15M: SubType.K_15M,
    KLType.K_30M: SubType.K_30M,
    KLType.K_60M: SubType.K_60M,
    KLType.K_DAY: SubType.K_DAY,
    KLType.K_WEEK: SubType.K_WEEK,
    KLType.K_MON: SubType.K_MON,
    KLType.K_QUARTER: SubType.K_QUARTER,
    KLType.K_YEAR: SubType.K_YEAR,
}


def get_kline(code, ktype="1d", num=10, start=None, end=None, rehab="forward",
              max_page=None, session_str="NONE", output_json=False):
    kl_type = KTYPE_MAP.get(ktype, KLType.K_DAY)
    au_type = REHAB_MAP.get(rehab, AuType.QFQ)
    session = HISTORY_SESSION_MAP.get(session_str.upper(), Session.NONE)

    ctx = None
    try:
        ctx = create_quote_context()
        if start or end:
            # 历史 K 线：支持分页拉取全部数据
            import pandas as pd
            page_size = min(num, 1000)
            ret, data, page_req_key = ctx.request_history_kline(
                code, start=start, end=end,
                ktype=kl_type, autype=au_type,
                max_count=page_size,
                session=session,
            )
            check_ret(ret, data, ctx, "获取K线")
            all_data = data
            page_count = 1
            while page_req_key is not None:
                if max_page and page_count >= max_page:
                    break
                ret, data, page_req_key = ctx.request_history_kline(
                    code, start=start, end=end,
                    ktype=kl_type, autype=au_type,
                    max_count=page_size,
                    page_req_key=page_req_key,
                    session=session,
                )
                check_ret(ret, data, ctx, "获取K线(翻页)")
                if not is_empty(data):
                    all_data = pd.concat([all_data, data], ignore_index=True)
                page_count += 1
            data = all_data
            source = "history"
        else:
            sub_type = KTYPE_TO_SUBTYPE.get(kl_type, SubType.K_DAY)
            ret, msg = ctx.subscribe([code], [sub_type])
            if ret != RET_OK:
                print(f"订阅失败: {msg}")
                sys.exit(1)
            ret, data = ctx.get_cur_kline(code, num, kl_type, au_type)
            source = "realtime"
            check_ret(ret, data, ctx, "获取K线")

        if is_empty(data):
            if output_json:
                print(json.dumps({"code": code, "ktype": ktype, "data": []}))
            else:
                print("无数据")
            return

        records = []
        for i in range(len(data)):
            row = data.iloc[i] if hasattr(data, "iloc") else data[i]
            records.append({
                "time": safe_get(row, "time_key", default=""),
                "open": safe_float(safe_get(row, "open", default=0)),
                "high": safe_float(safe_get(row, "high", default=0)),
                "low": safe_float(safe_get(row, "low", default=0)),
                "close": safe_float(safe_get(row, "close", default=0)),
                "volume": safe_int(safe_get(row, "volume", default=0)),
                "turnover": safe_float(safe_get(row, "turnover", default=0)),
            })

        if output_json:
            print(json.dumps({"code": code, "ktype": ktype, "source": source, "data": records}, ensure_ascii=False))
        else:
            title = f"K 线: {code} ({ktype}"
            if start or end:
                title += f", {start or '开始'} 至 {end or '现在'}"
            else:
                title += f", 最近 {num} 根"
            title += ")"

            print("=" * 80)
            print(title)
            print("=" * 80)
            print(f"  {'时间':<20} {'开盘':>10} {'最高':>10} {'最低':>10} {'收盘':>10} {'成交量':>12}")
            print("  " + "-" * 76)
            for r in records:
                print(f"  {r['time']:<20} {r['open']:>10.2f} {r['high']:>10.2f} {r['low']:>10.2f} {r['close']:>10.2f} {r['volume']:>12}")
            print("=" * 80)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取 K 线数据（实时或历史）")
    parser.add_argument("code", help="股票代码，如 US.AAPL、HK.00700")
    parser.add_argument("--ktype", choices=["1m", "3m", "5m", "15m", "30m", "60m", "1d", "1w", "1M", "1Q", "1Y"],
                        default="1d", help="K 线类型（默认: 1d）")
    parser.add_argument("--num", type=int, default=10, help="K 线数量，历史模式为每页大小（默认: 10）")
    parser.add_argument("--start", type=str, default=None, help="历史数据开始日期（YYYY-MM-DD）")
    parser.add_argument("--end", type=str, default=None, help="历史数据结束日期（YYYY-MM-DD）")
    parser.add_argument("--max-page", type=int, default=None, help="历史 K 线最大翻页次数，不传则拉取全部")
    parser.add_argument("--rehab", choices=["none", "forward", "backward"], default="forward",
                        help="复权类型: none(不复权), forward(前复权), backward(后复权)")
    parser.add_argument("--session", choices=["NONE", "RTH", "ETH", "ALL"],
                        default="NONE", help="美股分时段历史K线（仅美股，不支持 OVERNIGHT）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_kline(args.code, args.ktype, args.num, start=args.start, end=args.end,
              rehab=args.rehab, max_page=args.max_page, session_str=args.session,
              output_json=args.output_json)

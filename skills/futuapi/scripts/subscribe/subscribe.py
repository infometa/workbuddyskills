#!/usr/bin/env python3
"""
订阅实时行情数据

功能：订阅股票的指定数据类型（QUOTE/ORDER_BOOK/TICKER/RT_DATA/BROKER/K线等）
用法：python subscribe.py HK.00700 --types QUOTE ORDER_BOOK

接口限制：
- 每只股票订阅一个类型占用 1 个订阅额度（额度由用户等级决定，100~2000）
- 至少订阅一分钟才可反订阅
- 港股 BMP 权限不支持订阅；美股夜盘需 LV1 及以上权限
- SF 权限用户仅限同时订阅 50 只证券的摆盘
- 港股期权期货 LV1 权限不支持订阅逐笔类型

参数说明：
- is_first_push: True 推送断线前最后一条缓存数据，False 等待服务器最新推送
- subscribe_push: True 启用实时回调推送（必须），False 仅通过主动获取方式取数据（节省性能）
- is_detailed_orderbook: 仅港股 SF 权限下订阅 ORDER_BOOK 时使用；美股 LV2 不提供详细明细
- extended_time: 仅用于订阅美股实时 K 线、分时、逐笔
- session: 仅用于订阅美股实时 K 线、分时、逐笔；不支持 OVERNIGHT
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
    parse_subtypes,
    Session,
)

# session 仅支持以下值（订阅不支持 OVERNIGHT）
SESSION_MAP = {
    "NONE": Session.NONE,
    "RTH": Session.RTH,
    "ETH": Session.ETH,
    "ALL": Session.ALL,
}


def subscribe(codes, subtype_names, is_first_push=True, subscribe_push=False,
              extended_time=False, session_str="NONE", output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        subtypes = parse_subtypes(subtype_names)
        session = SESSION_MAP.get(session_str.upper(), Session.NONE)

        ret, msg = ctx.subscribe(
            codes, subtypes,
            is_first_push=is_first_push,
            subscribe_push=subscribe_push,
            extended_time=extended_time,
            session=session,
        )
        check_ret(ret, msg, ctx, "订阅")

        result = {
            "codes": codes,
            "subtypes": [str(s).split(".")[-1] for s in subtypes],
            "is_first_push": is_first_push,
            "subscribe_push": subscribe_push,
            "extended_time": extended_time,
            "session": session_str.upper(),
            "status": "subscribed",
        }

        if output_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("=" * 50)
            print("订阅成功")
            print("=" * 50)
            print(f"  股票: {', '.join(codes)}")
            print(f"  类型: {', '.join(result['subtypes'])}")
            print("=" * 50)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="订阅实时行情数据")
    parser.add_argument("codes", nargs="+", help="股票代码，如 HK.00700 US.AAPL")
    parser.add_argument("--types", nargs="+", required=True,
                        help="订阅类型: QUOTE ORDER_BOOK TICKER RT_DATA BROKER K_DAY K_1M K_5M K_15M K_30M K_60M K_WEEK K_MON")
    parser.add_argument("--no-first-push", action="store_true", help="不立即推送缓存数据")
    parser.add_argument("--push", action="store_true", help="开启推送回调")
    parser.add_argument("--extended-time", action="store_true", help="美股盘前盘后数据")
    parser.add_argument("--session", choices=["NONE", "RTH", "ETH", "ALL"],
                        default="NONE", help="美股交易时段（仅用于美股 K 线/分时/逐笔，不支持 OVERNIGHT）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    subscribe(codes=args.codes, subtype_names=args.types,
              is_first_push=not args.no_first_push, subscribe_push=args.push,
              extended_time=args.extended_time, session_str=args.session,
              output_json=args.output_json)

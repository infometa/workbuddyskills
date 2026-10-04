#!/usr/bin/env python3
"""
接收 K 线推送

功能：订阅股票 K 线并通过 Handler 接收实时推送数据
用法：python push_kline.py HK.00700 --ktype K_1M --duration 300

接口限制：
- 需先订阅对应 K 线类型，受订阅额度限制
- 港股 BMP 权限不支持订阅
"""
import argparse
import json
import time
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_quote_context,
    check_ret,
    safe_close,
    safe_float,
    safe_int,
    SubType,
    Session,
    RET_OK,
)

from futu import CurKlineHandlerBase, RET_ERROR

# session 仅支持以下值（订阅不支持 OVERNIGHT）
SESSION_MAP = {
    "NONE": Session.NONE,
    "RTH": Session.RTH,
    "ETH": Session.ETH,
    "ALL": Session.ALL,
}

KTYPE_SUB_MAP = {
    "K_1M": SubType.K_1M,
    "K_3M": SubType.K_3M,
    "K_5M": SubType.K_5M,
    "K_15M": SubType.K_15M,
    "K_30M": SubType.K_30M,
    "K_60M": SubType.K_60M,
    "K_DAY": SubType.K_DAY,
    "K_WEEK": SubType.K_WEEK,
    "K_MON": SubType.K_MON,
    "K_QUARTER": SubType.K_QUARTER,
    "K_YEAR": SubType.K_YEAR,
}


class KlineHandler(CurKlineHandlerBase):
    """K 线推送回调处理类"""
    def __init__(self, output_json=False):
        super().__init__()
        self.output_json = output_json

    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            if self.output_json:
                print(json.dumps({"error": str(data)}, ensure_ascii=False), flush=True)
            else:
                print(f"推送错误: {data}", flush=True)
            return RET_ERROR, data

        if self.output_json:
            records = []
            for i in range(len(data)):
                row = data.iloc[i] if hasattr(data, "iloc") else data[i]
                records.append({
                    "code": row.get("code", ""),
                    "time_key": row.get("time_key", ""),
                    "open": safe_float(row.get("open", 0)),
                    "high": safe_float(row.get("high", 0)),
                    "low": safe_float(row.get("low", 0)),
                    "close": safe_float(row.get("close", 0)),
                    "volume": safe_int(row.get("volume", 0)),
                })
            print(json.dumps({"type": "KLINE", "data": records}, ensure_ascii=False), flush=True)
        else:
            print(f"\n[K线推送] {time.strftime('%H:%M:%S')}")
            print(data.to_string(index=False))

        return RET_OK, data


def push_kline(codes, ktype="K_1M", duration=300, session_str="NONE", output_json=False):
    sub_type = KTYPE_SUB_MAP.get(ktype.upper(), SubType.K_1M)
    session = SESSION_MAP.get(session_str.upper(), Session.NONE)

    ctx = None
    try:
        ctx = create_quote_context()
        handler = KlineHandler(output_json=output_json)
        ctx.set_handler(handler)

        ret, msg = ctx.subscribe(codes, [sub_type], subscribe_push=True, session=session)
        check_ret(ret, msg, ctx, "订阅K线推送")

        if not output_json:
            print(f"已订阅 {ktype} K线推送: {', '.join(codes)}")
            print(f"等待推送 {duration} 秒...")

        time.sleep(duration)

    except KeyboardInterrupt:
        if not output_json:
            print("\n已停止接收推送")
    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="接收 K 线推送")
    parser.add_argument("codes", nargs="+", help="股票代码，如 HK.00700")
    parser.add_argument("--ktype", choices=["K_1M", "K_3M", "K_5M", "K_15M", "K_30M", "K_60M", "K_DAY", "K_WEEK", "K_MON", "K_QUARTER", "K_YEAR"],
                        default="K_1M", help="K 线类型（默认: K_1M）")
    parser.add_argument("--duration", type=int, default=300, help="持续接收时间（秒，默认: 300）")
    parser.add_argument("--session", choices=["NONE", "RTH", "ETH", "ALL"],
                        default="NONE", help="美股交易时段（仅美股，不支持 OVERNIGHT）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    push_kline(args.codes, args.ktype, args.duration, args.session, args.output_json)

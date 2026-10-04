#!/usr/bin/env python3
"""
接收分时推送

功能：订阅股票分时数据并通过 Handler 接收实时推送
用法：python push_rt_data.py HK.00700 --duration 60

接口限制：
- 需先订阅 RT_DATA 类型，受订阅额度限制
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
    df_to_records,
    SubType,
    Session,
    RET_OK,
)

from futu import RTDataHandlerBase, RET_ERROR

# session 仅支持以下值（订阅不支持 OVERNIGHT）
SESSION_MAP = {
    "NONE": Session.NONE,
    "RTH": Session.RTH,
    "ETH": Session.ETH,
    "ALL": Session.ALL,
}


class RTDataHandler(RTDataHandlerBase):
    """分时推送回调处理类"""
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
            print(json.dumps({"type": "RT_DATA", "data": df_to_records(data)}, ensure_ascii=False), flush=True)
        else:
            print(f"\n[分时推送] {time.strftime('%H:%M:%S')}")
            cols = [c for c in ['code', 'time', 'last_price', 'avg_price', 'volume', 'turnover'] if c in data.columns]
            print(data[cols].tail(5).to_string(index=False))

        return RET_OK, data


def push_rt_data(codes, duration=60, session_str="NONE", output_json=False):
    session = SESSION_MAP.get(session_str.upper(), Session.NONE)
    ctx = None
    try:
        ctx = create_quote_context()
        handler = RTDataHandler(output_json=output_json)
        ctx.set_handler(handler)

        ret, msg = ctx.subscribe(codes, [SubType.RT_DATA], subscribe_push=True, session=session)
        check_ret(ret, msg, ctx, "订阅分时推送")

        if not output_json:
            print(f"已订阅分时推送: {', '.join(codes)}")
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
    parser = argparse.ArgumentParser(description="接收分时推送")
    parser.add_argument("codes", nargs="+", help="股票代码，如 HK.00700")
    parser.add_argument("--duration", type=int, default=60, help="持续接收时间（秒，默认: 60）")
    parser.add_argument("--session", choices=["NONE", "RTH", "ETH", "ALL"],
                        default="NONE", help="美股交易时段（仅美股，不支持 OVERNIGHT）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    push_rt_data(args.codes, args.duration, args.session, args.output_json)

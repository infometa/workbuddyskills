#!/usr/bin/env python3
"""
接收报价推送

功能：订阅股票报价并通过 Handler 接收实时推送数据
用法：python push_quote.py HK.00700 --duration 60

接口限制：
- 需先订阅 QUOTE 类型，受订阅额度限制
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
    RET_OK,
)

from futu import StockQuoteHandlerBase, RET_ERROR


class QuoteHandler(StockQuoteHandlerBase):
    """报价推送回调处理类"""
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
                    "last_price": safe_float(row.get("last_price", 0)),
                    "volume": safe_int(row.get("volume", 0)),
                    "turnover": safe_float(row.get("turnover", 0)),
                    "high_price": safe_float(row.get("high_price", 0)),
                    "low_price": safe_float(row.get("low_price", 0)),
                })
            print(json.dumps({"type": "QUOTE", "data": records}, ensure_ascii=False), flush=True)
        else:
            print(f"\n[报价推送] {time.strftime('%H:%M:%S')}")
            if hasattr(data, "iloc"):
                print(data[['code', 'last_price', 'volume', 'turnover']].to_string(index=False))
            else:
                for row in data:
                    if hasattr(row, "get"):
                        print(f"  {row.get('code', '')}\t{row.get('last_price', '')}\t{row.get('volume', '')}\t{row.get('turnover', '')}")
                    else:
                        print(f"  {row}")

        return RET_OK, data


def push_quote(codes, duration=60, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        handler = QuoteHandler(output_json=output_json)
        ctx.set_handler(handler)

        ret, msg = ctx.subscribe(codes, [SubType.QUOTE], subscribe_push=True)
        check_ret(ret, msg, ctx, "订阅报价推送")

        if not output_json:
            print(f"已订阅报价推送: {', '.join(codes)}")
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
    parser = argparse.ArgumentParser(description="接收报价推送")
    parser.add_argument("codes", nargs="+", help="股票代码，如 HK.00700")
    parser.add_argument("--duration", type=int, default=60, help="持续接收时间（秒，默认: 60）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    push_quote(args.codes, args.duration, args.output_json)

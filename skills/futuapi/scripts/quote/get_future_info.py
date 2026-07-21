#!/usr/bin/env python3
"""
获取期货合约资料

功能：获取期货合约的详细信息
用法：python get_future_info.py HK.MCHmain HK.MCH2501

接口限制：
- 每 30 秒内最多请求 60 次
- 每次最多传入 200 个代码

返回字段说明：
- last_trade_time: 最后交易时间
- owner_code: 标的代码（主连合约对应当月合约代码）
- exchange: 交易所
- contract_size/contract_size_unit: 合约大小与单位
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
    df_to_records,
)


def get_future_info(codes, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_future_info(codes)
        check_ret(ret, data, ctx, "获取期货资料")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无期货资料数据")
            return

        if output_json:
            print(json.dumps({"data": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print("期货合约资料")
            print("=" * 70)
            print(data.to_string(index=False))
            print("=" * 70)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取期货合约资料")
    parser.add_argument("codes", nargs="+", help="期货代码，如 HK.MCHmain HK.MCH2501")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_future_info(args.codes, args.output_json)

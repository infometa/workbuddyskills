#!/usr/bin/env python3
"""
获取全局状态

功能：获取 OpenD 全局状态信息，包括各市场状态、服务器版本、登录状态等
用法：python get_global_state.py

返回字段说明（dict）：
- market_hk/market_us/market_sh/market_sz: 各市场状态
- market_hkfuture/market_usfuture: 期货市场状态
- server_ver: 服务器版本
- qot_logined: 行情是否已登录
- trd_logined: 交易是否已登录
"""
import argparse
import json
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_quote_context,
    safe_close,
    to_jsonable,
    RET_OK,
)


def get_global_state(output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_global_state()
        if ret != RET_OK:
            if output_json:
                print(json.dumps({"error": str(data)}, ensure_ascii=False))
            else:
                print(f"获取全局状态失败: {data}")
            sys.exit(1)

        # data 是 dict，非 DataFrame
        if output_json:
            result = {k: to_jsonable(v) for k, v in data.items()}
            print(json.dumps({"data": result}, ensure_ascii=False))
        else:
            print("=" * 70)
            print("OpenD 全局状态")
            print("=" * 70)
            for key, val in data.items():
                print(f"  {key}: {val}")
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
    parser = argparse.ArgumentParser(description="获取 OpenD 全局状态")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_global_state(args.output_json)

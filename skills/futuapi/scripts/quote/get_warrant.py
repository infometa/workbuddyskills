#!/usr/bin/env python3
"""
获取窝轮列表

功能：获取指定正股的窝轮/牛熊证列表
用法：python get_warrant.py HK.00700

接口限制：
- 每 30 秒内最多请求 60 次
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


def get_warrant(stock_owner, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_warrant(stock_owner=stock_owner)
        # data 是元组: (DataFrame, has_next, total_count)
        if isinstance(data, tuple):
            df, has_next, total_count = data
        else:
            df, has_next, total_count = data, False, 0
        check_ret(ret, df, ctx, "获取窝轮列表")

        if is_empty(df):
            if output_json:
                print(json.dumps({"stock_owner": stock_owner, "data": []}))
            else:
                print("无窝轮数据")
            return

        if output_json:
            result = {"stock_owner": stock_owner, "total_count": total_count, "data": df_to_records(df)}
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"窝轮/牛熊证 - 正股: {stock_owner}（共 {total_count} 条）")
            print("=" * 70)
            cols = [c for c in ['stock', 'name', 'type', 'strike_price',
                                'maturity_time', 'cur_price', 'volume', 'turnover',
                                'implied_volatility', 'premium', 'effective_leverage'] if c in df.columns]
            print(df[cols].to_string(index=False))
            print(f"\n当前显示 {len(df)} / {total_count} 条记录")
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
    parser = argparse.ArgumentParser(description="获取窝轮/牛熊证列表")
    parser.add_argument("stock_owner", help="正股代码，如 HK.00700")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_warrant(args.stock_owner, args.output_json)

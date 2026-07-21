#!/usr/bin/env python3
"""
获取历史 K 线额度

功能：查询历史 K 线额度使用情况
用法：python get_history_kl_quota.py
      python get_history_kl_quota.py --detail

接口限制：
- 每 30 秒内最多请求 60 次

返回字段说明：
- used_quota: 已使用额度
- remain_quota: 剩余额度
- detail_list (--detail): 请求过的股票代码列表
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


def get_history_kl_quota(get_detail=False, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_history_kl_quota(get_detail=get_detail)
        check_ret(ret, data, ctx, "获取 K 线额度")

        if output_json:
            if hasattr(data, 'iloc'):
                print(json.dumps({"data": df_to_records(data)}, ensure_ascii=False))
            else:
                print(json.dumps({"data": data}, ensure_ascii=False))
        else:
            print("=" * 70)
            print("历史 K 线额度")
            print("=" * 70)
            if hasattr(data, 'to_string'):
                print(data.to_string(index=False))
            else:
                print(f"  {data}")
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
    parser = argparse.ArgumentParser(description="获取历史 K 线额度")
    parser.add_argument("--detail", action="store_true", help="是否返回详细的股票列表")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_history_kl_quota(get_detail=args.detail, output_json=args.output_json)

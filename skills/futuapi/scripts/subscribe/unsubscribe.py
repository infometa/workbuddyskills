#!/usr/bin/env python3
"""
取消订阅

功能：取消指定股票的指定数据类型订阅
用法：python unsubscribe.py HK.00700 --types QUOTE ORDER_BOOK
      python unsubscribe.py --all  (取消所有订阅)

接口限制：
- 至少订阅一分钟后才可反订阅
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
)


def unsubscribe(codes=None, subtype_names=None, unsubscribe_all=False, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        if unsubscribe_all:
            ret, msg = ctx.unsubscribe_all()
            check_ret(ret, msg, ctx, "取消所有订阅")
            result = {"status": "all_unsubscribed"}
        else:
            if not codes or not subtype_names:
                print("错误: 需要指定股票代码和订阅类型，或使用 --all 取消所有")
                sys.exit(1)
            subtypes = parse_subtypes(subtype_names)
            ret, msg = ctx.unsubscribe(codes, subtypes)
            check_ret(ret, msg, ctx, "取消订阅")
            result = {
                "codes": codes,
                "subtypes": [str(s).split(".")[-1] for s in subtypes],
                "status": "unsubscribed",
            }

        if output_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("=" * 50)
            if unsubscribe_all:
                print("已取消所有订阅")
            else:
                print("取消订阅成功")
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
    parser = argparse.ArgumentParser(description="取消订阅")
    parser.add_argument("codes", nargs="*", help="股票代码")
    parser.add_argument("--types", nargs="+", default=None, help="订阅类型列表")
    parser.add_argument("--all", action="store_true", dest="unsub_all", help="取消所有订阅")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    unsubscribe(codes=args.codes if args.codes else None,
                subtype_names=args.types,
                unsubscribe_all=args.unsub_all,
                output_json=args.output_json)

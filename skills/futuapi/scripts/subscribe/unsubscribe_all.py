#!/usr/bin/env python3
"""
取消所有订阅

功能：取消当前连接的全部订阅
用法：python unsubscribe_all.py

接口限制：
- 订阅后至少 1 分钟才能反订阅
- 反订阅后需所有连接都反订阅同一标的，额度才会释放
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
    RET_OK,
)


def unsubscribe_all(output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.unsubscribe_all()
        check_ret(ret, data, ctx, "取消所有订阅")

        if output_json:
            print(json.dumps({"result": "ok"}, ensure_ascii=False))
        else:
            print("已取消所有订阅")

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="取消所有订阅")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    unsubscribe_all(args.output_json)

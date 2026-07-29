#!/usr/bin/env python3
"""查询订单支付状态。

Usage:
  python query_order.py <order_id>

调 POST /order/getByAPI 拿订单状态。
输出：JSON 到 stdout。
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import setup_common  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if len(args) != 1:
        print(json.dumps({"error": True, "message": "用法: query_order.py <order_id>"}, ensure_ascii=False))
        return 1
    order_id = args[0]

    try:
        result = setup_common.query_order_real(order_id)
    except RuntimeError as e:
        print(json.dumps({"error": True, "message": str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

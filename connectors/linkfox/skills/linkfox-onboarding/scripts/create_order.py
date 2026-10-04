#!/usr/bin/env python3
"""创建订单并渲染支付二维码。

Usage:
  python create_order.py <plan_id> <pay_method>

pay_method ∈ {wechat, alipay}（需在该套餐 available_methods 内）。
脚本内部调真实下单接口（个人 /order/createByAPI，团队 /order/createTeamOrderByAPI，
按 isTeamUser 自动分流），并内联调 setup_common.render_qr 生成 PNG + ASCII。
输出：JSON 到 stdout。
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import setup_common  # noqa: E402


def _validate_pay_method(plan_id: str, pay_method: str) -> tuple[bool, str]:
    """校验 pay_method 在该套餐 available_methods 内。

    拿用户类型 → 查对应套餐 → 比对。
    Returns:
        (ok, message)
    """
    try:
        user = setup_common.fetch_user_info()
        package_type = 7 if bool(user.get("isTeamUser")) else 1
        packages = setup_common.fetch_packages(package_type)
    except RuntimeError as e:
        return False, f"校验时获取套餐清单失败: {e}"
    for raw_p in packages:
        p = setup_common.normalize_package(raw_p)
        if p is None:
            continue  # 免费版已过滤
        if p["plan_id"] == plan_id:
            methods = p.get("available_methods", [])
            if pay_method in methods:
                return True, ""
            return False, f"套餐 {plan_id} 不支持 {pay_method}，仅支持 {methods}"
    return False, f"未知套餐 plan_id={plan_id}"


def main() -> int:
    args = sys.argv[1:]
    if len(args) != 2:
        print(json.dumps({"error": True, "message": "用法: create_order.py <plan_id> <pay_method>"}, ensure_ascii=False))
        return 1
    plan_id, pay_method = args

    ok, msg = _validate_pay_method(plan_id, pay_method)
    if not ok:
        print(json.dumps({"error": True, "message": msg}, ensure_ascii=False))
        return 1

    try:
        order = setup_common.create_order_real(plan_id, pay_method)
    except (RuntimeError, ValueError) as e:
        print(json.dumps({"error": True, "message": str(e)}, ensure_ascii=False))
        return 1

    # 内联渲染二维码
    qr = setup_common.render_qr(order["qr_content"], setup_common.session_dir())
    order["png_path"] = qr.get("png_path")
    order["ascii_qr"] = qr.get("ascii_qr")
    if qr.get("error"):
        order["qr_render_error"] = qr["error"]

    print(json.dumps(order, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
